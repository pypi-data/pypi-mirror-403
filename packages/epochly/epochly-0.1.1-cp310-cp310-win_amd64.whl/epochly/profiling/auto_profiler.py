"""
Epochly Auto-Profiler

Automatically detects hot paths and applies optimizations with zero configuration.
Uses sys.monitoring (Python 3.12+) or sys.settrace for profiling.

Key features:
1. Detects functions/loops consuming >10ms CPU time
2. Automatically applies JIT compilation
3. Integrates with loop transformer for SIMD/memory optimizations
4. ML-guided optimization via adaptive orchestrator
5. Zero configuration - activates when Epochly is enabled

Author: Epochly Development Team
"""

import sys
import time
import logging
import threading
import functools
import inspect
import signal
import types
from typing import Dict, List, Optional, Callable, Any, TYPE_CHECKING
from dataclasses import dataclass
from collections import defaultdict
from enum import Enum, auto
import gc

# Import speedup verifier for runtime speedup validation
from ..jit.speedup_verifier import verify_speedup, SpeedupVerificationResult

logger = logging.getLogger(__name__)


class OptimizationResult(Enum):
    """
    Result of optimization attempt.

    Used to distinguish transient states (DEFERRED, SKIPPED) from
    real failures (FAILED) to prevent false-positive warnings.

    Values:
        SUCCESS: Compilation succeeded, function optimized
        DEFERRED: Not ready yet (JIT initializing, transient state)
        SKIPPED: Pre-filtered (unsuitable for JIT, disabled)
        FAILED: Real error (TypingError, compilation crash)
    """
    SUCCESS = auto()   # Compilation succeeded
    DEFERRED = auto()  # JIT not ready (transient)
    SKIPPED = auto()   # Pre-filtered (unsuitable)
    FAILED = auto()    # Real compilation error


@dataclass
class HotLoopInfo:
    """Information about a detected hot loop."""
    code_object: object  # Code object for the loop
    start_line: int
    cpu_time_ms: float
    iteration_count: int = 0
    optimization_applied: bool = False


def _try_deep_copy(obj: Any) -> tuple[bool, Any]:
    """
    Attempt to deep copy an object for safe verification.

    CRITICAL: This prevents double-execution corruption when verifying JIT functions.
    We need to run compiled version on COPIED arguments so we don't mutate
    the real inputs that will be passed to the original function.

    CRITICAL (Dec 2025): ONLY accepts deep copy, rejects shallow copy.
    Shallow copy creates aliasing for nested mutables (dict with list values, etc.)
    which defeats the purpose of copying. Better to skip verification than get
    false positives from aliased mutations.

    Args:
        obj: Object to copy

    Returns:
        (success: bool, copied_obj: Any) - success=False if copy failed
    """
    try:
        import copy
        return (True, copy.deepcopy(obj))
    except Exception:
        # CRITICAL FIX: Reject shallow copy (aliasing risk for nested mutables)
        # deepcopy failed - verification impossible
        # Better to skip verification than risk false positives
        return (False, obj)


def _results_match(original_result: Any, compiled_result: Any, func_name: str = "") -> bool:
    """
    Compare results from original and JIT-compiled function execution.

    CRITICAL: This is the canary verification that prevents JIT type corruption bugs.
    Uses strict type equality (not isinstance) to catch Numba's silent type changes
    like dict -> numpy.ndarray.

    CRITICAL (Dec 2025): Relaxed for numeric type equivalence (float/float64/int/int64).
    Numba often returns Python float instead of numpy.float64, but these are equivalent.

    Args:
        original_result: Result from original function
        compiled_result: Result from JIT-compiled function
        func_name: Function name for logging (optional)

    Returns:
        True if results match semantically, False otherwise
    """
    # CRITICAL FIX: Handle numeric type equivalence (float/float64/int/int64 are equivalent)
    NUMERIC_TYPE_NAMES = {
        'float', 'float64', 'float32', 'float16',
        'int', 'int64', 'int32', 'int16', 'int8',
        'uint64', 'uint32', 'uint16', 'uint8'
    }

    orig_type_name = type(original_result).__name__
    comp_type_name = type(compiled_result).__name__

    # Both numeric - use value comparison instead of strict type equality
    if orig_type_name in NUMERIC_TYPE_NAMES and comp_type_name in NUMERIC_TYPE_NAMES:
        try:
            diff = abs(float(original_result) - float(compiled_result))
            # Absolute tolerance for values near zero
            if diff < 1e-8:
                return True
            # Relative tolerance for larger values
            if abs(original_result) > 1e-8:
                rel_diff = diff / abs(original_result)
                if rel_diff < 1e-5:
                    return True
                logger.warning(
                    f"JIT canary FAILED for {func_name}: numeric value mismatch - "
                    f"original={original_result}, compiled={compiled_result}, "
                    f"rel_diff={rel_diff:.2e} > 1e-5"
                )
                return False
            # Value is non-zero but diff >= 1e-8
            logger.warning(
                f"JIT canary FAILED for {func_name}: numeric value mismatch - "
                f"original={original_result}, compiled={compiled_result}, "
                f"diff={diff:.2e} >= 1e-8"
            )
            return False
        except (ValueError, TypeError, OverflowError) as e:
            logger.warning(f"JIT canary FAILED for {func_name}: numeric comparison error: {e}")
            return False

    # DICT TYPE EQUIVALENCE (Dec 2025): Handle Numba TypedDict vs Python dict
    # Numba compiles dict-returning functions to return numba.typed.typeddict.Dict
    # These are functionally equivalent for our purposes - check keys/values match
    DICT_LIKE_TYPES = {'dict', 'Dict', 'DictType'}
    if orig_type_name in DICT_LIKE_TYPES or comp_type_name in DICT_LIKE_TYPES:
        # Both must be dict-like (isinstance check handles TypedDict)
        try:
            # Check if both are dict-like (support keys() and __getitem__)
            if hasattr(original_result, 'keys') and hasattr(compiled_result, 'keys'):
                orig_keys = set(original_result.keys())
                comp_keys = set(compiled_result.keys())
                if orig_keys != comp_keys:
                    logger.warning(
                        f"JIT canary FAILED for {func_name}: dict keys mismatch - "
                        f"original={orig_keys}, compiled={comp_keys}"
                    )
                    return False
                # Recursively compare values
                return all(
                    _results_match(original_result[k], compiled_result[k], f"{func_name}[{k}]")
                    for k in orig_keys
                )
        except Exception as e:
            logger.warning(f"JIT canary FAILED for {func_name}: dict comparison error: {e}")
            return False

    # CRITICAL: Strict type equality for non-numerics - catches dict -> ndarray corruption
    if type(original_result) is not type(compiled_result):
        logger.warning(
            f"JIT canary FAILED for {func_name}: type mismatch - "
            f"original={type(original_result).__name__}, "
            f"compiled={type(compiled_result).__name__}"
        )
        return False

    # Handle None
    if original_result is None:
        return compiled_result is None

    # REJECT generators/iterators - single-use, can't verify without consuming
    if inspect.isgenerator(original_result) or inspect.isgeneratorfunction(original_result):
        logger.warning(f"JIT canary REJECTED for {func_name}: generator return type")
        return False

    # Handle numpy arrays with tolerance for floating-point differences
    try:
        import numpy as np
        if isinstance(original_result, np.ndarray):
            if not isinstance(compiled_result, np.ndarray):
                return False
            # Shape and dtype must match exactly
            if original_result.shape != compiled_result.shape:
                logger.warning(
                    f"JIT canary FAILED for {func_name}: shape mismatch - "
                    f"original={original_result.shape}, compiled={compiled_result.shape}"
                )
                return False
            if original_result.dtype != compiled_result.dtype:
                logger.warning(
                    f"JIT canary FAILED for {func_name}: dtype mismatch - "
                    f"original={original_result.dtype}, compiled={compiled_result.dtype}"
                )
                return False
            # Use allclose for numerical comparison with reasonable tolerance
            try:
                return np.allclose(original_result, compiled_result, rtol=1e-5, atol=1e-8, equal_nan=True)
            except TypeError:
                # Non-numeric arrays - use array_equal
                return np.array_equal(original_result, compiled_result)
    except ImportError:
        pass

    # Handle pandas DataFrames
    try:
        import pandas as pd
        if isinstance(original_result, pd.DataFrame):
            if not isinstance(compiled_result, pd.DataFrame):
                return False
            return original_result.equals(compiled_result)
        if isinstance(original_result, pd.Series):
            if not isinstance(compiled_result, pd.Series):
                return False
            return original_result.equals(compiled_result)
    except ImportError:
        pass

    # Handle dictionaries recursively
    if isinstance(original_result, dict):
        if not isinstance(compiled_result, dict):
            return False
        if set(original_result.keys()) != set(compiled_result.keys()):
            logger.warning(
                f"JIT canary FAILED for {func_name}: dict keys mismatch - "
                f"original={set(original_result.keys())}, compiled={set(compiled_result.keys())}"
            )
            return False
        return all(
            _results_match(original_result[k], compiled_result[k], f"{func_name}[{k}]")
            for k in original_result.keys()
        )

    # Handle lists/tuples recursively
    if isinstance(original_result, (list, tuple)):
        if not isinstance(compiled_result, type(original_result)):
            return False
        if len(original_result) != len(compiled_result):
            logger.warning(
                f"JIT canary FAILED for {func_name}: length mismatch - "
                f"original={len(original_result)}, compiled={len(compiled_result)}"
            )
            return False
        return all(
            _results_match(o, c, f"{func_name}[{i}]")
            for i, (o, c) in enumerate(zip(original_result, compiled_result))
        )

    # Handle floats with tolerance
    if isinstance(original_result, float):
        if not isinstance(compiled_result, float):
            return False
        # Use relative tolerance for floating point comparison
        if original_result == 0.0:
            return abs(compiled_result) < 1e-8
        return abs(original_result - compiled_result) / abs(original_result) < 1e-5

    # Default: direct equality
    try:
        return original_result == compiled_result
    except Exception:
        # If comparison fails, assume mismatch
        return False


def _install_wrapper_everywhere(original_func: Callable, wrapper: Callable) -> int:
    """
    Install wrapper in ALL modules that have a reference to the original function.

    CRITICAL FIX (P0.17 - Dec 2025): Solves the local binding bypass problem.

    Problem:
        When a user imports via `from demo_functions import mandelbrot_pure_python`,
        the local binding is created BEFORE Epochly enables. When JITCanaryWrapper
        self-destructs, the existing code only updates the defining module's __globals__,
        not the importing module's namespace. The local binding still points to the
        original function, bypassing the JIT wrapper entirely.

    Solution:
        This function scans ALL loaded modules in sys.modules for references to the
        original function (by object identity) and replaces them with the wrapper.

    Args:
        original_func: The original Python function to replace
        wrapper: The wrapper to install (typically _DisabledAwareWrapper)

    Returns:
        int: Number of locations where wrapper was installed (0 if none found)

    Note:
        - Uses id() for object identity comparison (not equality)
        - Handles None entries in sys.modules gracefully
        - Handles modules without __dict__ gracefully
        - Thread-safe: iterates over list() copy of sys.modules
        - Does NOT handle references captured in closure cells, default arguments,
          or containers (lists, dicts, etc.) - use trampoline for those cases
    """
    import sys

    original_id = id(original_func)
    func_name = getattr(original_func, '__name__', '<unknown>')
    installed_count = 0

    # 1. Install in defining module's __globals__ (original behavior)
    # CRITICAL FIX (Jan 2025): Add identity check to avoid overwriting unrelated bindings
    if hasattr(original_func, '__globals__'):
        func_globals = original_func.__globals__
        if func_name in func_globals:
            current = func_globals.get(func_name)
            if current is original_func or id(current) == original_id:
                func_globals[func_name] = wrapper
                installed_count += 1
                logger.debug(f"Installed wrapper in __globals__ for {func_name}")

    # 2. Scan all loaded modules for references to the original function
    for module_name, module in list(sys.modules.items()):
        # Skip None entries (can happen during import cycles)
        if module is None:
            continue

        # Try to get module's namespace
        try:
            module_dict = vars(module)
            if module_dict is None:
                continue
        except TypeError:
            # Some modules don't support vars() (e.g., built-in modules)
            continue

        # Scan for references to the original function
        for attr_name, attr_value in list(module_dict.items()):
            # Use identity comparison (id) not equality
            if id(attr_value) == original_id:
                try:
                    setattr(module, attr_name, wrapper)
                    installed_count += 1
                    logger.debug(
                        f"Installed wrapper for {attr_name} in {module_name}"
                    )
                except (AttributeError, TypeError):
                    # Some modules have read-only attributes
                    logger.debug(
                        f"Could not install wrapper for {attr_name} in {module_name} (read-only)"
                    )

    logger.debug(
        f"_install_wrapper_everywhere: installed wrapper in {installed_count} locations for {func_name}"
    )

    return installed_count


def _is_epochly_wrapper(obj: Any) -> bool:
    """
    Check if an object is any type of Epochly JIT/GPU wrapper.

    Detects all wrapper types:
    - _DisabledAwareWrapper (post-JIT verified)
    - _GPUDisabledAwareWrapper (post-GPU verified)
    - JITPendingWrapper (awaiting JIT compilation)
    - JITCanaryWrapper (verifying JIT)
    - GPUCanaryWrapper (verifying GPU)
    - Any object with _is_epochly_jit_wrapper or _is_epochly_gpu_wrapper marker

    Args:
        obj: Object to check

    Returns:
        True if this is an Epochly wrapper, False otherwise
    """
    # Check for JIT marker attribute (future-proof detection)
    if getattr(obj, '_is_epochly_jit_wrapper', False):
        return True

    # Check for GPU marker attribute (GPU wrappers use different marker)
    if getattr(obj, '_is_epochly_gpu_wrapper', False):
        return True

    # Check for _original attribute (all wrappers have this)
    if hasattr(obj, '_original'):
        # Additional validation: check class name contains 'Wrapper'
        class_name = type(obj).__name__
        if 'Wrapper' in class_name or 'wrapper' in class_name:
            return True

    return False


def _get_original_from_wrapper(wrapper: Any) -> Optional[Callable]:
    """
    Extract the original function from any Epochly wrapper.

    Args:
        wrapper: An Epochly wrapper object

    Returns:
        The original function, or None if extraction failed
    """
    # All Epochly wrappers store original in _original attribute
    original = getattr(wrapper, '_original', None)
    if original is not None:
        return original

    # Fallback: check _func attribute (some wrappers use this)
    return getattr(wrapper, '_func', None)


def _restore_original_functions_for_gpu_upgrade() -> int:
    """
    Restore original functions by removing ALL Epochly wrappers for GPU re-analysis.

    CRITICAL FIX (Jan 2025 RCA): When upgrading from LEVEL_3 (CPU JIT) to LEVEL_4 (GPU),
    functions wrapped with any Epochly wrapper continue routing to their current
    optimization path, preventing auto_profiler from attempting GPU compilation.

    Root cause traced via integration testing:
    1. Function is JIT-compiled at LEVEL_3
    2. JITCanaryWrapper self-destructs and installs _DisabledAwareWrapper
    3. When upgrading to LEVEL_4, _jit_compiled_code_ids is cleared
    4. BUT the wrapper remains installed in module bindings
    5. Wrapper intercepts all calls and routes to Numba JIT
    6. Auto_profiler never gets a chance to try GPU compilation

    Solution: Comprehensively restore original functions by:
    1. Scanning sys.modules for ALL Epochly wrapper types (by object identity)
    2. Restoring trampolined functions (P0.18 pattern) via _restore_original_code
    3. Checking function __globals__ for wrappers installed there
    4. Using generic wrapper detection for future-proofing

    Handled wrapper types:
    - _DisabledAwareWrapper (post-JIT verified)
    - _GPUDisabledAwareWrapper (post-GPU verified)
    - JITPendingWrapper (awaiting JIT compilation)
    - JITCanaryWrapper (verifying JIT)
    - GPUCanaryWrapper (verifying GPU)
    - Any wrapper with _is_epochly_jit_wrapper or _is_epochly_gpu_wrapper marker

    Thread Safety:
        This function MUST be called during level transitions when the profiler
        lock is held. The caller (EpochlyCore._clear_jit_caches_for_gpu_upgrade)
        is responsible for acquiring profiler._lock before calling this function.
        Uses _trampoline_install_lock for atomic __code__ restoration.

    Returns:
        Number of functions restored
    """
    import sys

    wrapper_count = 0
    trampoline_count = 0
    globals_count = 0
    originals_to_restore = set()  # Use set to avoid duplicates

    # Phase 1: Scan all loaded modules for Epochly wrappers
    # Uses list() to create snapshot for thread-safe iteration
    for module_name, module in list(sys.modules.items()):
        if module is None:
            continue

        try:
            module_dict = vars(module)
            if not module_dict:
                continue
        except TypeError:
            continue

        # Scan for any Epochly wrapper (by object identity, not just name)
        for attr_name, attr_value in list(module_dict.items()):
            # Check if this is any Epochly wrapper
            if _is_epochly_wrapper(attr_value):
                original = _get_original_from_wrapper(attr_value)
                if original is not None:
                    try:
                        setattr(module, attr_name, original)
                        wrapper_count += 1
                        wrapper_type = type(attr_value).__name__

                        # Track for Phase 2 (trampoline restoration)
                        if isinstance(original, types.FunctionType):
                            originals_to_restore.add(original)

                        logger.debug(
                            f"Restored original function for {attr_name} in {module_name} "
                            f"(removed {wrapper_type} for GPU upgrade)"
                        )
                    except (AttributeError, TypeError) as e:
                        logger.debug(
                            f"Could not restore original for {attr_name} in {module_name}: {e}"
                        )

            # Also check for trampolined functions (P0.18 pattern)
            # These have _epochly_orig_code attribute
            elif isinstance(attr_value, types.FunctionType):
                if hasattr(attr_value, '_epochly_orig_code'):
                    originals_to_restore.add(attr_value)

    # Phase 2 & 3: Combined for efficiency
    # Restore trampolines and __globals__ in single pass with lock protection
    with _trampoline_install_lock:
        for original in originals_to_restore:
            # Phase 2: Restore trampolined functions (P0.18 pattern)
            if hasattr(original, '_epochly_orig_code'):
                orig_code, orig_defaults, orig_kwdefaults = original._epochly_orig_code
                original.__code__ = orig_code
                original.__defaults__ = orig_defaults
                original.__kwdefaults__ = orig_kwdefaults
                delattr(original, '_epochly_orig_code')
                trampoline_count += 1
                logger.debug(f"Restored trampoline code for {original.__name__}")

            # Phase 3: Restore wrappers in function __globals__
            # Handle aliased functions by comparing object identity
            if hasattr(original, '__globals__'):
                func_globals = original.__globals__
                original_id = id(original)

                # Scan __globals__ for wrappers pointing to this original
                for name, value in list(func_globals.items()):
                    if _is_epochly_wrapper(value):
                        wrapper_original = _get_original_from_wrapper(value)
                        # Compare by object identity to handle aliases
                        if wrapper_original is not None and id(wrapper_original) == original_id:
                            func_globals[name] = original
                            globals_count += 1
                            wrapper_type = type(value).__name__
                            logger.debug(
                                f"Restored original in __globals__['{name}'] "
                                f"(removed {wrapper_type} for GPU upgrade)"
                            )

    total_restored = wrapper_count + trampoline_count + globals_count
    if total_restored > 0:
        logger.info(
            f"LEVEL_4 GPU upgrade: Restored {wrapper_count} module wrapper(s), "
            f"{trampoline_count} trampoline(s), and {globals_count} __globals__ binding(s) "
            f"for GPU re-analysis"
        )

    return total_restored


def _clone_func(func: types.FunctionType) -> types.FunctionType:
    """
    Create an independent copy of a function with the same behavior.

    CRITICAL for P0.18 trampoline pattern: We need a raw copy of the original
    function to call when Epochly is disabled. The clone has the original
    __code__, so it won't recurse through the trampoline.

    Args:
        func: The function to clone

    Returns:
        A new function object with the same code, globals, name, defaults, and closure

    Note:
        The clone is completely independent - modifying the original's __code__
        will not affect the clone.
    """
    clone = types.FunctionType(
        func.__code__,
        func.__globals__,
        func.__name__,
        func.__defaults__,
        func.__closure__
    )
    clone.__kwdefaults__ = func.__kwdefaults__
    clone.__annotations__ = getattr(func, '__annotations__', {})
    clone.__doc__ = func.__doc__
    clone.__module__ = func.__module__
    clone.__qualname__ = func.__qualname__
    return clone


# Module-level lock for thread-safe trampoline installation
# Protects the multi-attribute update to prevent race conditions
# Use RLock (reentrant lock) because _install_wrapper_with_fallbacks acquires
# this lock, then calls _install_dispatch_trampoline which also acquires it.
# A regular Lock would deadlock; RLock allows same thread to re-acquire.
_trampoline_install_lock = threading.RLock()

# CRITICAL FIX (Jan 2025): Registry for Epochly wrapper __call__ code_ids
# When the profiler sees a wrapper's __call__ method being executed, it sees a
# DIFFERENT code_id than the original function. Without this registry:
#   - Run 1: Original function optimized, code_id added to _jit_compiled_code_ids
#   - Run 2: Wrapper.__call__ executed, DIFFERENT code_id, profiler re-profiles!
#   - This caused Run 2 to be SLOWER than Run 1 (13.7x variance)
#
# Solution: Register wrapper CLASS __call__ code_ids once at module load time.
# Since __call__.__code__ is the same for all instances of a class, registering
# once per class is more efficient than registering per instance.
# Profiler checks this registry in fast-path and skips profiling.
#
# THREAD SAFETY NOTE: Reads in fast-path (`code_id in _wrapper_call_code_ids`)
# happen without lock. This is safe in CPython due to GIL guaranteeing atomic
# set membership checks. Writes are protected by _wrapper_registry_lock.
_wrapper_call_code_ids: set = set()
_wrapper_registry_lock = threading.Lock()


def _register_wrapper_class(wrapper_cls: type) -> None:
    """
    Register a wrapper CLASS's __call__ code_id so the profiler skips all instances.

    CRITICAL for LEVEL_4 consistency: Without this, the profiler sees the wrapper's
    __call__ method as a "new" function and tries to profile/optimize it, causing
    Run 2 to be slower than Run 1.

    This is more efficient than per-instance registration since __call__.__code__
    is the same for all instances of a wrapper class.

    Args:
        wrapper_cls: An Epochly wrapper class with a __call__ method
    """
    if hasattr(wrapper_cls, '__call__'):
        # For classes, __call__ is an unbound method (function)
        call_method = wrapper_cls.__call__
        if hasattr(call_method, '__code__'):
            code_id = id(call_method.__code__)
            registered = False
            with _wrapper_registry_lock:
                if code_id not in _wrapper_call_code_ids:
                    _wrapper_call_code_ids.add(code_id)
                    registered = True
            # Log OUTSIDE lock to prevent lock contention if logging is slow
            if registered and logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"Registered wrapper class __call__ code_id {code_id} for "
                    f"{wrapper_cls.__name__}"
                )


def _create_signature_preserving_trampoline(
    target_func: types.FunctionType,
    dispatch_callable: Callable
) -> Optional[types.FunctionType]:
    """
    Create a trampoline that exactly preserves the target function's signature.

    CRITICAL FIX (Dec 2025): This avoids using *args/**kwargs which generate
    DICT_MERGE bytecode that Numba doesn't support.

    Architecture:
        1. Extract function signature using inspect.signature()
        2. Generate trampoline code with identical parameter list
        3. Inject __dispatch as a hidden keyword-only parameter
        4. Return trampoline function with matching signature

    Example:
        Input:  def foo(a, b=1): ...
        Output: def _trampoline(a, b, *, __dispatch=<dispatcher>): return __dispatch(a, b)

    The __dispatch parameter is keyword-only with a default, so it's invisible
    to callers who use the original signature.

    Args:
        target_func: Original function whose signature to preserve
        dispatch_callable: Dispatcher to route calls through

    Returns:
        Trampoline function with matching signature, or None if signature
        cannot be extracted (caller should fall back to *args/**kwargs).

    Limitations:
        - Functions with **kwargs will generate DICT_MERGE bytecode in the
          trampoline (Numba incompatible). This is unavoidable since we must
          forward the kwargs.
        - Positional-only parameters require Python 3.8+
        - Functions defined in C extensions cannot be signature-inspected
    """
    try:
        sig = inspect.signature(target_func)
    except (ValueError, TypeError) as e:
        logger.debug(f"Cannot extract signature for {target_func.__name__}: {e}")
        return None

    # Build parameter and call argument strings
    # Track positional-only params separately to add "/" separator
    positional_only_params = []
    regular_params = []
    call_args = []
    has_var_positional = False
    has_var_keyword = False
    has_keyword_only = False
    has_positional_only = False

    for name, param in sig.parameters.items():
        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            positional_only_params.append(name)
            call_args.append(name)
            has_positional_only = True
        elif param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            regular_params.append(name)
            call_args.append(name)
        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
            regular_params.append(f"*{name}")
            call_args.append(f"*{name}")
            has_var_positional = True
        elif param.kind == inspect.Parameter.KEYWORD_ONLY:
            # If no *args, we need to add bare * before first keyword-only param
            if not has_var_positional and not has_keyword_only:
                regular_params.append("*")
            has_keyword_only = True
            regular_params.append(name)
            call_args.append(f"{name}={name}")
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            regular_params.append(f"**{name}")
            call_args.append(f"**{name}")
            has_var_keyword = True

    # Build final params list with "/" separator if needed
    params = []
    if has_positional_only:
        params.extend(positional_only_params)
        params.append("/")
    params.extend(regular_params)

    # Inject __dispatch as keyword-only parameter
    # Position depends on presence of *args, keyword-only params, and **kwargs:
    # - Has *args or keyword-only: append __dispatch (already in keyword-only section)
    # - Has **kwargs only (no *args, no keyword-only): add "*, __dispatch" before **kwargs
    # - No keyword-only params: add "*, __dispatch" at end
    if has_var_keyword:
        # Insert __dispatch before **kwargs
        kwargs_param = params.pop()  # Remove **kwargs
        if not has_var_positional and not has_keyword_only:
            # No *args or keyword-only params, need to add * for __dispatch
            params.append("*")
        params.append("__dispatch")
        params.append(kwargs_param)  # Re-add **kwargs
    elif has_var_positional or has_keyword_only:
        # Already in keyword-only section
        params.append("__dispatch")
    else:
        # Need to add * to make __dispatch keyword-only
        params.append("*")
        params.append("__dispatch")

    param_str = ", ".join(params)
    call_str = ", ".join(call_args)

    # Generate trampoline code
    # Note: __dispatch default value set via namespace, not in code string
    code = f"def _trampoline({param_str}): return __dispatch({call_str})"

    # Create the function in a namespace with __dispatch bound
    namespace = {"__dispatch": dispatch_callable}
    try:
        exec(code, namespace)
    except SyntaxError as e:
        logger.debug(f"Failed to compile trampoline for {target_func.__name__}: {e}")
        return None

    trampoline = namespace["_trampoline"]

    # Preserve original function's defaults
    # NOTE: Intentionally shares default objects with original (Python semantics)
    trampoline.__defaults__ = target_func.__defaults__

    # Preserve keyword-only defaults and add __dispatch
    original_kwdefaults = target_func.__kwdefaults__ or {}
    trampoline.__kwdefaults__ = {**original_kwdefaults, "__dispatch": dispatch_callable}

    logger.debug(
        f"Created signature-preserving trampoline for {target_func.__name__}: "
        f"params=({param_str}), call=({call_str})"
    )

    return trampoline


def _install_dispatch_trampoline(target_func: types.FunctionType, dispatch_callable: Callable) -> bool:
    """
    Mutate a function's __code__ to route ALL calls through a dispatcher.

    CRITICAL FIX (P0.18 - Dec 2025): Superior solution to the local binding bypass problem.

    The trampoline pattern works because it mutates the function OBJECT itself, not
    just module namespace bindings. This means ALL references to the function -
    including local variables, closures, default arguments, and container captures -
    automatically route through the dispatcher.

    How it works:
        1. Save the original __code__, __defaults__, __kwdefaults__ for potential restoration
        2. Create a tiny trampoline function that just calls the dispatcher
        3. Replace target_func's __code__ with the trampoline's __code__

    Why this is superior to sys.modules scanning:
        - Handles local variables: `def foo(): from demo import func; func()`
        - Handles closures: `closure = lambda: func()`
        - Handles default arguments: `def foo(g=func): g()`
        - Handles container captures: `funcs = [func]`, `registry['x'] = func`
        - O(1) instead of O(modules * attrs)

    Closure Support (Jan 2026 Fix):
        Functions with closure variables (free vars) ARE now supported. The key insight
        is that we don't need to USE the free variables - we just need the trampoline's
        code object to DECLARE them. We use CodeType.replace(co_freevars=...) to create
        a trampoline code object with matching free var declarations, which satisfies
        Python's validation while still dispatching to our wrapper.

    Thread Safety:
        This function uses a module-level lock to ensure the multi-attribute
        update (__code__, __defaults__, __kwdefaults__) is atomic. This prevents
        other threads from seeing the function in an inconsistent state.

    Args:
        target_func: The function object to mutate (will be modified in-place)
        dispatch_callable: The dispatcher to route calls through

    Returns:
        True if trampoline was installed successfully, False if the function has
        closures and cannot use the trampoline pattern.

    Warning:
        To avoid infinite recursion, the dispatcher should call a CLONE of the
        original function (via _clone_func), not the target_func itself.
    """
    # Get the original function's free variables (closure variables)
    original_freevars = target_func.__code__.co_freevars

    if original_freevars:
        logger.debug(
            f"Installing trampoline for {target_func.__name__} with "
            f"{len(original_freevars)} free vars: {original_freevars}"
        )

    # CRITICAL FIX (Dec 2025): Use signature-preserving trampoline to avoid DICT_MERGE
    # The old *args/**kwargs trampoline generates DICT_MERGE bytecode (Python 3.9+).
    # Numba doesn't support DICT_MERGE opcode, causing UnsupportedBytecodeError when
    # Numba tries to read func.__code__ for recompilation (e.g., GPU kernels).
    #
    # Solution: Generate a trampoline that matches the function's exact signature.
    # This avoids DICT_MERGE entirely, making the trampoline Numba-compatible.
    _trampoline = _create_signature_preserving_trampoline(target_func, dispatch_callable)

    if _trampoline is None:
        # Fallback to *args/**kwargs trampoline for functions with complex signatures
        # Note: This will still cause DICT_MERGE issues with Numba, but such functions
        # likely aren't Numba-compatible anyway (Numba needs concrete signatures).
        logger.debug(
            f"Falling back to *args/**kwargs trampoline for {target_func.__name__}: "
            f"could not generate signature-preserving code"
        )

        def _trampoline(*args, __dispatch=dispatch_callable, **kwargs):
            return __dispatch(*args, **kwargs)

    # CRITICAL FIX (Jan 2026): Handle functions with closure variables
    # Python requires __code__ replacements to have matching co_freevars count.
    # Solution: Use CodeType.replace to create a code object that DECLARES the same
    # free variables, even though the trampoline doesn't USE them. This satisfies
    # Python's validation while still dispatching to our wrapper.
    if original_freevars:
        trampoline_code = _trampoline.__code__
        # Save these BEFORE creating the new function
        old_defaults = _trampoline.__defaults__
        old_kwdefaults = _trampoline.__kwdefaults__
        old_globals = _trampoline.__globals__
        old_name = _trampoline.__name__

        try:
            # Python 3.8+ has CodeType.replace() for easy code object modification
            if hasattr(trampoline_code, 'replace'):
                new_code = trampoline_code.replace(co_freevars=original_freevars)
            else:
                # Python 3.7 fallback: manual CodeType construction
                # Note: Python 3.7 signature is different - no co_posonlyargcount
                import sys
                if sys.version_info >= (3, 8):
                    # Should not reach here if replace() exists, but just in case
                    new_code = types.CodeType(
                        trampoline_code.co_argcount,
                        trampoline_code.co_posonlyargcount,
                        trampoline_code.co_kwonlyargcount,
                        trampoline_code.co_nlocals,
                        trampoline_code.co_stacksize,
                        trampoline_code.co_flags,
                        trampoline_code.co_code,
                        trampoline_code.co_consts,
                        trampoline_code.co_names,
                        trampoline_code.co_varnames,
                        trampoline_code.co_filename,
                        trampoline_code.co_name,
                        trampoline_code.co_firstlineno,
                        trampoline_code.co_lnotab if hasattr(trampoline_code, 'co_lnotab') else b'',
                        original_freevars,
                        trampoline_code.co_cellvars,
                    )
                else:
                    # Python 3.7: no co_posonlyargcount parameter
                    new_code = types.CodeType(
                        trampoline_code.co_argcount,
                        trampoline_code.co_kwonlyargcount,
                        trampoline_code.co_nlocals,
                        trampoline_code.co_stacksize,
                        trampoline_code.co_flags,
                        trampoline_code.co_code,
                        trampoline_code.co_consts,
                        trampoline_code.co_names,
                        trampoline_code.co_varnames,
                        trampoline_code.co_filename,
                        trampoline_code.co_name,
                        trampoline_code.co_firstlineno,
                        trampoline_code.co_lnotab,
                        original_freevars,
                        trampoline_code.co_cellvars,
                    )

            # Create a new function with the modified code and original closure
            _trampoline = types.FunctionType(
                new_code,
                old_globals,
                old_name,
                old_defaults,
                target_func.__closure__,  # Reuse original's closure cells
            )
            _trampoline.__kwdefaults__ = old_kwdefaults

            logger.debug(
                f"Created closure-compatible trampoline for {target_func.__name__} "
                f"with {len(original_freevars)} free vars"
            )
        except Exception as e:
            logger.warning(
                f"Failed to create closure-compatible trampoline for {target_func.__name__}: {e}. "
                f"Falling back to module scan."
            )
            return False

    # Use lock to ensure atomic multi-attribute update
    with _trampoline_install_lock:
        # Save original code for potential restoration (inside lock for consistency)
        # NOTE: "Last write wins" semantics - if two threads install different dispatchers
        # on the same function, the second dispatcher will be used but the original code
        # is preserved from the first save (hasattr check prevents overwriting).
        # This is intentional: the original code should always be the TRUE original,
        # not an intermediate trampoline.
        if not hasattr(target_func, '_epochly_orig_code'):
            target_func._epochly_orig_code = (
                target_func.__code__,
                target_func.__defaults__,
                target_func.__kwdefaults__
            )

        # Replace target function's code with trampoline code
        # All three attributes must be updated atomically to prevent callers
        # from seeing an inconsistent function state
        target_func.__code__ = _trampoline.__code__
        target_func.__defaults__ = _trampoline.__defaults__
        target_func.__kwdefaults__ = _trampoline.__kwdefaults__

    logger.debug(f"Installed dispatch trampoline for {target_func.__name__}")
    return True


def _restore_original_code(target_func: types.FunctionType) -> bool:
    """
    Restore a function's original __code__ after trampoline installation.

    Thread Safety:
        Uses the same lock as _install_dispatch_trampoline to ensure atomic
        restoration of function attributes.

    Args:
        target_func: The function to restore

    Returns:
        True if restoration succeeded, False if no original code was saved
    """
    with _trampoline_install_lock:
        if not hasattr(target_func, '_epochly_orig_code'):
            return False

        orig_code, orig_defaults, orig_kwdefaults = target_func._epochly_orig_code
        target_func.__code__ = orig_code
        target_func.__defaults__ = orig_defaults
        target_func.__kwdefaults__ = orig_kwdefaults

        delattr(target_func, '_epochly_orig_code')

    logger.debug(f"Restored original code for {target_func.__name__}")
    return True


def _install_wrapper_with_fallbacks(
    original_func: Callable,
    wrapper: Callable,
    use_trampoline: bool = True,
    use_module_scan: bool = True
) -> bool:
    """
    Install a wrapper for a function using the most appropriate mechanism.

    CRITICAL FIX (Jan 2025): Generalizable solution for nested function optimization.

    The Problem:
        Functions defined in local scopes (inside other functions, closures, lambdas)
        cannot be wrapped via the simple `func.__globals__[func.__name__] = wrapper`
        approach because their names aren't in the module's globals.

    The Solution:
        A three-tier fallback strategy that handles all function types:
        1. Fast path: Direct __globals__ assignment (module-level functions)
        2. Trampoline: Patch __code__ in-place (nested functions without closures)
        3. Module scan: Find and replace all references (closures, complex cases)

    Why This Pattern:
        - Works for 100% of Python functions, regardless of definition scope
        - Proven pattern from P0.17/P0.18 JITCanaryWrapper self-destruct code
        - O(1) for most cases (fast path + trampoline), O(modules) worst case

    Args:
        original_func: The original function to wrap
        wrapper: The wrapper callable to install
        use_trampoline: Whether to try trampoline fallback (default True)
        use_module_scan: Whether to try module scanning fallback (default True)

    Returns:
        True if wrapper was successfully installed via at least one mechanism,
        False if all installation methods failed.

    Thread Safety:
        - Fast path: Thread-safe via GIL for dict assignment
        - Trampoline: Uses _trampoline_install_lock for atomic __code__ update
        - Module scan: Thread-safe via list() copy of sys.modules
    """
    func_name = getattr(original_func, '__name__', '<unknown>')
    installed = False

    # Tier 1: Fast path - direct __globals__ assignment
    # Works for: Module-level functions, class methods, decorated functions
    # Time complexity: O(1)
    if hasattr(original_func, '__globals__') and func_name in original_func.__globals__:
        # Verify we're replacing the correct function (avoid overwriting a different one)
        current = original_func.__globals__.get(func_name)
        if current is original_func or id(current) == id(original_func):
            original_func.__globals__[func_name] = wrapper
            installed = True
            logger.debug(f"_install_wrapper_with_fallbacks: installed in __globals__ for {func_name}")

    # Tier 2: Trampoline - patch __code__ in-place
    # Works for: Nested functions, closures, local functions
    # Time complexity: O(1)
    # CRITICAL FIX (Jan 2026): Clone original BEFORE installing trampoline to prevent recursion
    #
    # Thread Safety Design:
    #   - We acquire _trampoline_install_lock HERE (outer scope)
    #   - _install_dispatch_trampoline also acquires the same lock internally
    #   - This works because _trampoline_install_lock is an RLock (reentrant)
    #   - The same thread can acquire an RLock multiple times without deadlock
    #   - This ensures the ENTIRE sequence (clone + trampoline + wrapper update) is atomic
    #
    if use_trampoline and not installed:
        if isinstance(original_func, types.FunctionType):
            # Acquire lock for entire atomic operation: clone + trampoline + wrapper._original update
            # The RLock allows _install_dispatch_trampoline to re-acquire without deadlock
            with _trampoline_install_lock:
                # Step 1: Clone BEFORE any modifications
                # The wrapper holds a reference to original_func. When we patch original_func.__code__
                # to dispatch to wrapper, calling wrapper._original would recurse through the trampoline.
                # By cloning first and updating wrapper._original to the clone, we break the recursion:
                # - Calls to original_func -> trampoline -> wrapper
                # - Wrapper calls clone (has original code, not trampoline) -> success
                original_clone = _clone_func(original_func)

                # Step 2: Install trampoline (re-acquires RLock internally - safe)
                trampoline_success = _install_dispatch_trampoline(original_func, wrapper)

                if trampoline_success:
                    # Step 3: Validate wrapper interface
                    # CRITICAL: Wrapper MUST have _original attribute for this pattern to work.
                    # Without it, the trampoline will dispatch to wrapper, but wrapper will
                    # call the trampolined function, causing infinite recursion.
                    if not hasattr(wrapper, '_original'):
                        # FAIL-SAFE: Restore original code to prevent recursion
                        logger.error(
                            f"_install_wrapper_with_fallbacks: CRITICAL - wrapper for {func_name} "
                            f"missing '_original' attribute. Restoring original code. "
                            f"Wrapper type: {type(wrapper).__name__}"
                        )
                        _restore_original_code(original_func)
                        # Explicitly: installed stays False, Tier 3 will be attempted
                        installed = False
                    else:
                        # Step 4: Update wrapper to use clone (breaks recursion cycle)
                        wrapper._original = original_clone
                        installed = True
                        logger.debug(
                            f"_install_wrapper_with_fallbacks: Tier 2 SUCCESS - trampoline for {func_name} "
                            f"(wrapper._original -> clone @ {id(original_clone):#x})"
                        )
                else:
                    # Trampoline installation failed (e.g., unsupported signature)
                    # installed stays False, Tier 3 will be attempted
                    logger.debug(
                        f"_install_wrapper_with_fallbacks: Tier 2 SKIP - trampoline failed for {func_name}"
                    )

    # Tier 3: Module scan - find and replace all references
    # Works for: Closures, functions in containers, complex import patterns
    # Time complexity: O(modules * attrs) - only used as last resort
    if use_module_scan and not installed:
        scan_count = _install_wrapper_everywhere(original_func, wrapper)
        if scan_count > 0:
            installed = True
            logger.debug(
                f"_install_wrapper_with_fallbacks: installed via module scan in "
                f"{scan_count} location(s) for {func_name}"
            )
        else:
            logger.debug(
                f"_install_wrapper_with_fallbacks: module scan found no references for {func_name}. "
                f"This may be a closure or dynamically-created function that cannot be intercepted."
            )

    if not installed:
        logger.warning(
            f"_install_wrapper_with_fallbacks: ALL installation methods failed for {func_name}. "
            f"Function may not be optimized."
        )

    return installed


class _DisabledAwareWrapper:
    """
    Numba-transparent wrapper that respects epochly_disabled_context() after JIT self-destruct.

    CRITICAL FIX (P0.14 - Dec 2025): JITCanaryWrapper's self-destruct pattern was
    replacing itself with the RAW compiled Numba function, which bypassed the P0.13
    disabled context check. This caused baseline measurements to use JIT-compiled
    speeds instead of pure Python.

    CRITICAL FIX (P0.16 - Dec 2025): The original P0.14 fix broke Numba's nested
    function compilation because Numba couldn't type-infer the wrapper class.
    This version uses __getattr__ to proxy attribute access to the compiled
    function, making the wrapper "transparent" to Numba's type system.

    This wrapper is installed during self-destruct instead of the raw compiled
    function. It checks ep._core_singleton.enabled and routes to:
    - Original Python function when Epochly is disabled (for baseline measurements)
    - Compiled Numba function when Epochly is enabled (for performance)

    For Numba compatibility, it proxies all attribute access (except __call__)
    to the compiled function, so Numba sees the wrapper's type signature as
    matching the compiled Numba dispatcher.

    Author: Epochly Development Team
    Date: December 2025
    """
    # Note: Cannot use __slots__ because we need __getattr__ for Numba transparency

    def __init__(self, original: Callable, compiled: Callable, name: str):
        """
        Initialize disabled-aware wrapper.

        Args:
            original: The original Python function (for baseline measurements)
            compiled: The compiled Numba function (for performance)
            name: Function name for debugging
        """
        # Use object.__setattr__ to avoid triggering __getattr__
        object.__setattr__(self, '_original', original)
        object.__setattr__(self, '_compiled', compiled)
        object.__setattr__(self, '_name', name)
        # Marker attribute for future-proof JIT wrapper detection
        # Used by loop transformation to avoid overwriting JIT wrappers
        object.__setattr__(self, '_is_epochly_jit_wrapper', True)

    def __call__(self, *args, **kwargs):
        """Route to original or compiled based on Epochly enabled state."""
        import epochly as ep
        # P0.23 FIX (Dec 2025): Track routing decisions for diagnostics
        # This helps identify when/why functions route to original instead of compiled
        if ep._core_singleton is not None and not ep._core_singleton.enabled:
            # Log at DEBUG level to avoid flooding - only logs when DEBUG is enabled
            if logger.isEnabledFor(logging.DEBUG):
                reason = getattr(ep._core_singleton, '_disabled_reason', 'unknown')
                logger.debug(
                    f"_DisabledAwareWrapper routing {self._name} to ORIGINAL "
                    f"(enabled=False, reason={reason})"
                )
            return self._original(*args, **kwargs)
        return self._compiled(*args, **kwargs)

    def __getattr__(self, name):
        """
        Proxy attribute access to the compiled function for Numba transparency.

        This makes the wrapper look like a Numba dispatcher to Numba's type
        inference system. Attributes like 'nopython_signatures', 'get_call_template',
        '_type', etc. are forwarded to the compiled function.
        """
        # Proxy to compiled function - this is what makes Numba see our type
        return getattr(self._compiled, name)

    def __repr__(self):
        return f"<_DisabledAwareWrapper for {self._name}>"


class JITPendingWrapper:
    """
    Non-blocking wrapper for functions awaiting JIT compilation.

    CRITICAL FIX (Dec 2025): Eliminates 13+ second blocking during JIT compilation.

    Instead of blocking iteration 3 waiting for Numba compilation, this wrapper:
    1. Queues compilation in background (returns immediately)
    2. On each call, checks if compilation completed
    3. Uses original function while waiting
    4. Once compiled, installs JITCanaryWrapper for verification

    CRITICAL FIX (Dec 2025 - P0.17): When Numba compiles outer functions that call
    inner functions wrapped by JITPendingWrapper, Numba needs to access type-inference
    attributes (nopython_signatures, get_call_template, etc.). Without these, Numba
    falls back to object mode with no speedup. This wrapper now:
    - Detects Numba type-inference attribute requests
    - Triggers synchronous compilation if needed
    - Returns attributes from the compiled Numba dispatcher

    This enables iteration 3 to run at normal speed (~4ms) instead of
    blocking for 13+ seconds waiting for Numba.

    Author: Epochly Development Team
    Date: December 2025
    """

    # Numba-specific attributes that indicate type inference is happening.
    # When these are requested and compilation is pending, we must compile
    # synchronously so Numba can properly type-infer nested function calls.
    _NUMBA_TYPE_INFERENCE_ATTRS = frozenset({
        'nopython_signatures',
        'signatures',
        'get_call_template',
        'typeof_pyval',
        'py_func',
        'overloads',
        'get_function_type',
        '_type',
        'targetdescr',
        'typingctx',
        'targetctx',
    })

    def __init__(
        self,
        original_func: Callable,
        func_name: str,
        jit_manager,
        code_object,
        on_compiled_callback: Optional[Callable[[bool], None]] = None
    ):
        """
        Initialize pending compilation wrapper.

        Args:
            original_func: The original Python function
            func_name: Function name for logging
            jit_manager: JIT manager for checking compilation status
            code_object: Code object for tracking
            on_compiled_callback: Callback when compilation completes
        """
        self._original = original_func
        self._func_name = func_name
        self._jit_manager = jit_manager
        self._code_object = code_object
        self._on_compiled_callback = on_compiled_callback

        # State tracking
        self._compilation_complete = False
        self._compiled_func = None
        self._check_lock = threading.Lock()
        self._promoted_to_canary = False
        self._sync_compile_attempted = False  # Prevent repeated sync compile attempts

        # Preserve function metadata
        functools.update_wrapper(self, original_func)

        # Marker attribute for future-proof JIT wrapper detection
        # Set AFTER update_wrapper to prevent accidental overwrite from __dict__ copy
        self._is_epochly_jit_wrapper = True

        logger.debug(f"JITPendingWrapper installed for {func_name} (background compilation)")

    def __call__(self, *args, **kwargs) -> Any:
        """
        Execute function, checking for compilation completion.

        Thread-safety: Uses double-checked locking with lock protection for
        both compilation status check AND promotion to canary wrapper.

        Returns:
            Function result from original (while pending) or canary wrapper (once compiled)
        """
        # P0.13 FIX: Respect epochly_disabled_context by using original function
        # when Epochly is disabled. This ensures accurate baseline measurements.
        import epochly as ep
        if ep._core_singleton is not None and not ep._core_singleton.enabled:
            return self._original(*args, **kwargs)

        # Fast path: already promoted to canary (single-read pattern for thread safety)
        if self._promoted_to_canary:
            compiled = self._compiled_func  # Single read to avoid race
            if compiled is not None:
                return compiled(*args, **kwargs)

        # Check if compilation completed (non-blocking, with lock protection)
        if not self._compilation_complete:
            with self._check_lock:
                if not self._compilation_complete:
                    compiled = self._jit_manager.get_compiled_artifact(self._original)

                    if compiled is not self._original and compiled is not None:
                        # Compilation finished successfully!
                        self._compiled_func = compiled
                        self._compilation_complete = True
                        logger.debug(
                            f"Background compilation complete for {self._func_name}, "
                            f"promoting to JITCanaryWrapper for verification"
                        )

                        # Notify callback
                        if self._on_compiled_callback:
                            try:
                                self._on_compiled_callback(True)
                            except Exception as e:
                                logger.debug(f"Compilation callback error: {e}")

                    # Check for compilation failure (not just pending)
                    elif hasattr(self._jit_manager, 'is_compilation_failed'):
                        if self._jit_manager.is_compilation_failed(self._original):
                            # Compilation failed permanently - stop polling
                            self._compilation_complete = True
                            logger.debug(f"Compilation failed for {self._func_name}")
                            if self._on_compiled_callback:
                                try:
                                    self._on_compiled_callback(False)
                                except Exception as e:
                                    logger.debug(f"Compilation callback error: {e}")

        # If compiled, create and use canary wrapper (with lock to prevent race)
        if self._compilation_complete and self._compiled_func is not None:
            with self._check_lock:  # FIX: Protect promotion logic from race condition
                if not self._promoted_to_canary:
                    # P0.23 FIX (Dec 2025): Create verification callback to track canary result
                    # Without this callback, the profiler is not notified when the canary
                    # verifies (or fails), which can cause inconsistent JIT behavior.
                    # The callback ensures proper tracking after canary self-destructs.
                    #
                    # IMPORTANT: Capture values (not self) to avoid reference cycles.
                    # The closure should only hold immutable values.
                    code_id = id(self._code_object) if self._code_object else None
                    func_name = self._func_name  # Capture string value, not self

                    def on_canary_verified(use_compiled: bool, code_id=code_id, func_name=func_name):
                        """Callback when canary verification completes.

                        Note: code_id and func_name are bound as default args to avoid
                        closure captures and make the captured values explicit.
                        """
                        if code_id is None:
                            return

                        # Check for interpreter shutdown - avoid noisy errors during exit
                        import sys
                        if sys.is_finalizing():
                            return

                        # Access profiler via import to avoid circular reference
                        try:
                            # Guard against reentrant import deadlock (Python 3.13 macOS)
                            epochly_core_module = sys.modules.get('epochly.core.epochly_core')
                            if epochly_core_module is None or not hasattr(epochly_core_module, 'get_epochly_core'):
                                return  # Module not fully loaded - skip

                            from ..core.epochly_core import get_epochly_core
                            core = get_epochly_core()
                            if core and hasattr(core, '_auto_profiler') and core._auto_profiler:
                                profiler = core._auto_profiler
                                if use_compiled:
                                    with profiler._lock:
                                        profiler._jit_compiled_code_ids.add(code_id)
                                    logger.debug(f"Canary verified for {func_name}: using compiled")
                                else:
                                    profiler._mark_permanent_failure(code_id, func_name)
                                    logger.debug(f"Canary verification failed for {func_name}: marked as permanent failure")
                        except ImportError:
                            # Expected during shutdown - core module not available
                            logger.debug(f"Canary callback skipped for {func_name}: epochly_core not available")
                        except Exception:
                            # Unexpected error - log with traceback for debugging
                            logger.warning(f"Unexpected canary callback error for {func_name}", exc_info=True)

                    # P0.25 FIX: Get pre-measured speedup from JIT manager to skip
                    # redundant verification in canary (eliminates 1-2s overhead)
                    known_speedup = None
                    try:
                        if hasattr(self._jit_manager, 'compiled_functions'):
                            with self._jit_manager._lock:
                                if self._func_name in self._jit_manager.compiled_functions:
                                    result = self._jit_manager.compiled_functions[self._func_name]
                                    if result.speedup_ratio is not None:
                                        known_speedup = result.speedup_ratio
                                        logger.debug(
                                            f"Using pre-measured speedup {known_speedup:.2f}x for "
                                            f"{self._func_name} canary verification"
                                        )
                    except (KeyError, AttributeError) as e:
                        # Expected errors when speedup not available
                        logger.debug(f"Could not get pre-measured speedup: {e}")
                    except Exception as e:
                        # Unexpected error - log with traceback for debugging
                        logger.warning(f"Unexpected error getting pre-measured speedup: {e}", exc_info=True)

                    # Create canary wrapper on first access after compilation
                    canary = JITCanaryWrapper(
                        self._original,
                        self._compiled_func,
                        self._func_name,
                        on_verified_callback=on_canary_verified,  # P0.23: Add callback
                        known_speedup_ratio=known_speedup  # P0.25: Skip redundant verification
                    )

                    # Replace self in globals with canary wrapper
                    # FIX: Verify globals[name] is self before replacing (aliasing protection)
                    if hasattr(self._original, '__globals__'):
                        globals_dict = self._original.__globals__
                        if (self._func_name in globals_dict and
                                globals_dict[self._func_name] is self):
                            try:
                                globals_dict[self._func_name] = canary
                                self._promoted_to_canary = True
                                logger.debug(f"Promoted {self._func_name} from PendingWrapper to CanaryWrapper")
                            except Exception as e:
                                logger.debug(f"Failed to promote to canary: {e}")
                        else:
                            # Aliasing detected - don't replace wrong function
                            logger.debug(
                                f"Cannot promote {self._func_name}: globals entry is not self "
                                f"(aliasing or already replaced)"
                            )
                            self._promoted_to_canary = True  # Prevent repeated attempts

                    return canary(*args, **kwargs)

        # Still pending - run original
        return self._original(*args, **kwargs)

    def __getattr__(self, name: str):
        """
        Proxy attribute access to the compiled function for Numba transparency.

        CRITICAL FIX (P0.16 - Dec 2025): When Numba compiles outer functions that
        call inner functions wrapped by JITPendingWrapper, it needs to access
        Numba-specific attributes like `nopython_signatures`, `_type`, and
        `get_call_template` to determine how to compile the call site.

        Without this proxy, Numba falls back to object mode which:
        - Disables parallelization (no prange)
        - Disables caching
        - Results in slower execution

        CRITICAL FIX (P0.17 - Dec 2025): If compilation is pending and Numba-specific
        attributes are requested, we MUST trigger synchronous compilation. Otherwise
        Numba will fall back to object mode for the outer function.

        This method makes JITPendingWrapper "transparent" to Numba's type system
        by forwarding attribute lookups to the underlying compiled function.
        """
        # If compilation is complete, proxy to compiled function
        if self._compilation_complete and self._compiled_func is not None:
            return getattr(self._compiled_func, name)

        # P0.17 FIX: If Numba is requesting type-inference attributes and compilation
        # is not yet complete, we must trigger synchronous compilation NOW.
        # This allows nested function compilation to work properly.
        if name in self._NUMBA_TYPE_INFERENCE_ATTRS:
            # Thread-safe synchronous compilation trigger
            compiled_func = self._trigger_sync_compilation()
            if compiled_func is not None:
                return getattr(compiled_func, name)
            # If sync compilation failed or returned None, fall through to original
            # which will raise AttributeError for Numba attributes

        # For non-Numba attributes, or if sync compilation failed,
        # proxy to original function (for introspection)
        return getattr(self._original, name)

    def _trigger_sync_compilation(self) -> Optional[Callable]:
        """
        Trigger synchronous compilation when Numba needs type-inference attributes.

        Thread-safe: Uses lock to ensure only one sync compilation attempt.
        Idempotent: Returns cached result if already compiled.

        Returns:
            Compiled function if successful, None if failed or unavailable.
        """
        # Fast path: already compiled
        if self._compilation_complete and self._compiled_func is not None:
            return self._compiled_func

        with self._check_lock:
            # Double-check inside lock
            if self._compilation_complete and self._compiled_func is not None:
                return self._compiled_func

            # Prevent repeated sync compilation attempts
            if self._sync_compile_attempted:
                return self._compiled_func  # May be None if previous attempt failed

            self._sync_compile_attempted = True

            # Check if compilation already failed for this function.
            # Note: We set _sync_compile_attempted=True BEFORE this check intentionally.
            # This ensures failed compilations aren't retried repeatedly, matching the
            # behavior in __call__ where we mark _compilation_complete=True on failure.
            if hasattr(self._jit_manager, 'is_compilation_failed'):
                if self._jit_manager.is_compilation_failed(self._original):
                    logger.debug(
                        f"Sync compilation skipped for {self._func_name}: "
                        f"compilation already failed"
                    )
                    return None

            logger.debug(
                f"P0.17 FIX: Numba type inference triggered synchronous compilation "
                f"for {self._func_name}"
            )

            try:
                # First check if background compilation already completed
                compiled = self._jit_manager.get_compiled_artifact(self._original)
                if compiled is not self._original and compiled is not None:
                    self._compiled_func = compiled
                    self._compilation_complete = True
                    logger.debug(f"Background compilation already complete for {self._func_name}")
                    return self._compiled_func

                # Background compilation not complete - trigger synchronous compilation
                # Use compile_function_auto with bypass_call_count=True since auto-profiler
                # already identified this as hot, and skip_benchmark=True for speed
                if hasattr(self._jit_manager, 'compile_function_auto'):
                    compiled = self._jit_manager.compile_function_auto(
                        self._original,
                        bypass_call_count=True,
                        skip_benchmark=True
                    )
                    if compiled is not self._original and compiled is not None:
                        self._compiled_func = compiled
                        self._compilation_complete = True
                        logger.debug(
                            f"Synchronous compilation successful for {self._func_name} "
                            f"(triggered by Numba type inference)"
                        )

                        # Notify callback
                        if self._on_compiled_callback:
                            try:
                                self._on_compiled_callback(True)
                            except Exception as e:
                                logger.debug(f"Compilation callback error: {e}")

                        return self._compiled_func
                    else:
                        logger.debug(
                            f"Synchronous compilation returned original for {self._func_name} "
                            f"(function may not be JIT-suitable)"
                        )
                else:
                    logger.warning(
                        f"JIT manager lacks compile_function_auto method - "
                        f"cannot trigger sync compilation for {self._func_name}"
                    )

            except Exception as e:
                logger.warning(
                    f"Synchronous compilation failed for {self._func_name}: {e}"
                )

        return self._compiled_func

    def __repr__(self) -> str:
        status = "compiled" if self._compilation_complete else "pending"
        return f"<JITPendingWrapper({self._func_name}, status={status})>"


class JITCanaryWrapper:
    """
    Lazy verification wrapper for JIT-compiled functions.

    CRITICAL: This class implements the "canary in the coal mine" pattern for JIT safety.
    Instead of blindly replacing functions with compiled versions, we wrap them and verify
    on the FIRST ACTUAL CALL that the compiled version produces identical output.

    Why lazy verification?
    - At compile time, we don't have real user arguments
    - Synthetic test inputs often miss edge cases (like dict returns)
    - Real arguments from actual usage are the best test

    Behavior:
    1. First call: Run BOTH original and compiled, compare results
    2. If match: Promote to compiled-only mode, log success
    3. If mismatch: Revert to original-only mode, log warning with details
    4. Subsequent calls: Use whichever version was selected

    Thread Safety:
    - Uses threading.Lock to ensure exactly one verification occurs
    - Multiple threads may hit first call simultaneously - only one verifies

    Author: Epochly Development Team
    Date: December 2025
    """

    def __init__(self, original_func: Callable, compiled_func: Callable, func_name: str = "",
                 on_verified_callback: Optional[Callable[[bool], None]] = None,
                 known_speedup_ratio: Optional[float] = None):
        """
        Initialize canary wrapper.

        Args:
            original_func: The original Python function
            compiled_func: The JIT-compiled version
            func_name: Function name for logging
            on_verified_callback: Optional callback(use_compiled: bool) called after verification
            known_speedup_ratio: Pre-measured speedup ratio from JIT manager's compilation benchmark.
                                 If >= 1.2x, the canary trusts this measurement and skips its own
                                 speedup verification (saving ~1s for large arrays). Correctness
                                 verification (comparing compiled vs original output) still runs
                                 regardless of this value. None means no pre-measured data is available.
        """
        self._original = original_func
        self._compiled = compiled_func
        self._func_name = func_name or getattr(original_func, '__name__', 'unknown')
        self._on_verified_callback = on_verified_callback
        self._known_speedup_ratio = known_speedup_ratio

        # Verification state
        self._verified = False
        self._use_compiled = False  # Start pessimistic - use original until verified
        self._verification_lock = threading.Lock()

        # Preserve function metadata for transparency
        functools.update_wrapper(self, original_func)

        # Marker attribute for future-proof JIT wrapper detection
        # Set AFTER update_wrapper to prevent accidental overwrite from __dict__ copy
        self._is_epochly_jit_wrapper = True

    def __call__(self, *args, **kwargs) -> Any:
        """
        Execute function with lazy verification on first call.

        CRITICAL FIX (Dec 2025): Executes original on REAL args and compiled on COPIES.
        This prevents double-mutation and side-effect corruption during verification.

        Returns:
            Function result (from original or compiled, depending on verification state)
        """
        # P0.13 FIX: Respect epochly_disabled_context by using original function
        # when Epochly is disabled. This ensures accurate baseline measurements.
        import epochly as ep
        if ep._core_singleton is not None and not ep._core_singleton.enabled:
            return self._original(*args, **kwargs)

        # Fast path: already verified
        if self._verified:
            if self._use_compiled:
                return self._compiled(*args, **kwargs)
            else:
                return self._original(*args, **kwargs)

        # Slow path: first call - perform verification
        with self._verification_lock:
            # Double-check after acquiring lock (another thread may have verified)
            if self._verified:
                if self._use_compiled:
                    return self._compiled(*args, **kwargs)
                else:
                    return self._original(*args, **kwargs)

            # CRITICAL: Single-pass copy to avoid race conditions
            # We copy each argument exactly ONCE - if any copy fails, skip verification
            args_copy = []
            kwargs_copy = {}
            all_copyable = True

            # Copy positional arguments
            for arg in args:
                success, copied = _try_deep_copy(arg)
                if not success:
                    all_copyable = False
                    break
                args_copy.append(copied)

            # Copy keyword arguments (only if args succeeded)
            if all_copyable:
                for k, v in kwargs.items():
                    success, copied = _try_deep_copy(v)
                    if not success:
                        all_copyable = False
                        break
                    kwargs_copy[k] = copied

            if not all_copyable:
                # Can't safely verify - arguments contain uncopyable objects
                # (locks, file handles, etc.) or copy operation failed.
                # Fall back to original forever. This is expected for functions
                # handling complex objects - use DEBUG level.
                logger.debug(
                    f"JIT canary skipped for {self._func_name}: "
                    f"arguments not copyable (contains locks/files/etc), using original"
                )
                self._verified = True
                self._use_compiled = False

                # CRITICAL FIX: Self-destruct - replace wrapper with original
                if hasattr(self._original, '__globals__') and self._func_name in self._original.__globals__:
                    self._original.__globals__[self._func_name] = self._original
                    logger.debug(f"Self-destruct: Replaced wrapper with original (args not copyable)")

                # Notify callback
                if self._on_verified_callback:
                    try:
                        self._on_verified_callback(False)
                    except Exception:
                        pass
                return self._original(*args, **kwargs)

            # Convert to proper types for function call
            args_copy = tuple(args_copy)

            # Perform canary verification with copied args
            try:
                # CRITICAL: Run compiled on COPIES first (dry-run, result not returned)
                # This ensures we don't mutate real inputs
                try:
                    compiled_result = self._compiled(*args_copy, **kwargs_copy)
                except Exception as e:
                    # Compiled version threw exception - revert to original
                    # Check if this is an EXPECTED failure (e.g., Numba can't compile
                    # functions that call other non-compiled functions)
                    error_msg = str(e)
                    error_type = type(e).__name__
                    is_expected_failure = (
                        error_type == "TypingError" and (
                            "Untyped global name" in error_msg or
                            "Unknown attribute" in error_msg or
                            "Cannot determine Numba type" in error_msg or
                            "Unsupported array dtype" in error_msg
                        )
                    ) or (
                        error_type == "UnsupportedError"
                    ) or (
                        error_type == "LoweringError"
                    )

                    # Use DEBUG for expected failures, WARNING for unexpected ones
                    if is_expected_failure:
                        logger.debug(
                            f"JIT canary skipped for {self._func_name}: "
                            f"{error_type} (expected - function not suitable for JIT)"
                        )
                    else:
                        logger.warning(
                            f"JIT canary FAILED for {self._func_name}: "
                            f"compiled version raised {error_type}: {e}"
                        )
                    self._verified = True
                    self._use_compiled = False

                    # CRITICAL FIX: Self-destruct - replace wrapper with original
                    if hasattr(self._original, '__globals__') and self._func_name in self._original.__globals__:
                        self._original.__globals__[self._func_name] = self._original
                        logger.debug(f"Self-destruct: Replaced wrapper with original (compiled raised exception)")

                    # Notify callback
                    if self._on_verified_callback:
                        try:
                            self._on_verified_callback(False)
                        except Exception as e:
                            logger.error(f"Verification callback failed: {e}")
                    # Return original result on REAL args (user-visible call)
                    return self._original(*args, **kwargs)

                # Run original on REAL args (this is the user-visible call)
                original_result = self._original(*args, **kwargs)

                # Compare results
                if _results_match(original_result, compiled_result, self._func_name):
                    # Results match - now verify speedup before promoting
                    # CRITICAL FIX (Dec 2025): speedup_verifier.py was NOT integrated
                    # This caused 0.0x "speedup" for tiny workloads (1.3ms baseline)
                    # where JIT overhead made compiled version SLOWER

                    # P0.25 FIX (Dec 2025): Skip redundant speedup verification if JIT manager
                    # already benchmarked and found high speedup (>= 1.2x). This eliminates
                    # 1-2 seconds of overhead on Run 1 for large array operations where the
                    # original function takes hundreds of ms per call.
                    #
                    # MIN_TRUSTED_SPEEDUP_RATIO = 1.2: Below this threshold, measurement noise
                    # could cause false positives, so we re-verify. Above it, the speedup is
                    # significant enough to trust the JIT manager's benchmark.
                    MIN_TRUSTED_SPEEDUP_RATIO = 1.2
                    if self._known_speedup_ratio is not None and self._known_speedup_ratio >= MIN_TRUSTED_SPEEDUP_RATIO:
                        # JIT manager already verified speedup - trust it
                        logger.debug(
                            f"JIT canary PASSED for {self._func_name}: "
                            f"using pre-verified speedup ({self._known_speedup_ratio:.2f}x)"
                        )
                        use_compiled = True
                        speedup_for_log = self._known_speedup_ratio
                    else:
                        # No pre-verified speedup or it's marginal - run verification
                        # Verify compiled version actually provides speedup
                        # Use args_copy for verification (already copied above)
                        speedup_result = verify_speedup(
                            self._original,
                            self._compiled,
                            test_args=args_copy,
                            test_kwargs=kwargs_copy,
                            num_trials=5,  # Quick check, fewer trials
                            min_speedup=1.10  # Require 10% speedup minimum
                        )
                        use_compiled = speedup_result.use_compiled
                        speedup_for_log = speedup_result.speedup_ratio

                    if use_compiled:
                        # SUCCESS: Speedup verified, promote to compiled version
                        logger.debug(
                            f"JIT canary PASSED for {self._func_name}: "
                            f"promoting to compiled version ({speedup_for_log:.2f}x speedup)"
                        )
                        self._verified = True
                        self._use_compiled = True

                        # CRITICAL FIX (P0.14 + P0.17 + P0.18): Self-destruct with trampoline dispatch
                        # P0.14: Uses _DisabledAwareWrapper to preserve epochly_disabled_context() checks
                        # P0.17: Updates module namespace bindings for explicit imports
                        # P0.18: Uses trampoline pattern to handle ALL references (locals, closures, defaults)
                        #
                        # The trampoline pattern mutates the original function's __code__ so that
                        # ALL references to the function (including local variables, closures,
                        # default arguments, and container captures) route through the dispatcher.

                        # Clone the original BEFORE installing trampoline (to avoid recursion)
                        raw_original = _clone_func(self._original) if isinstance(self._original, types.FunctionType) else self._original

                        # NOTE (Dec 2025): Signature-preserving trampolines now work with Numba.
                        # The trampoline preserves the exact function signature, avoiding DICT_MERGE
                        # bytecode that Numba doesn't support. No special handling needed.

                        # Create disabled-aware wrapper with the CLONE (not the trampolined original)
                        wrapper = _DisabledAwareWrapper(
                            raw_original, self._compiled, self._func_name
                        )

                        # P0.18: Install trampoline on original function (handles all references)
                        trampoline_installed = False
                        if isinstance(self._original, types.FunctionType):
                            trampoline_installed = _install_dispatch_trampoline(self._original, wrapper)
                            if trampoline_installed:
                                logger.debug(f"Self-destruct: Installed trampoline for {self._func_name}")
                            else:
                                # Function has closures, trampoline cannot be installed
                                logger.debug(
                                    f"Self-destruct: Cannot install trampoline for {self._func_name} "
                                    f"(has closure variables), using module namespace only"
                                )
                        else:
                            # Fallback for non-FunctionType (e.g., built-in functions)
                            logger.debug(
                                f"Self-destruct: Cannot install trampoline on {type(self._original).__name__}, "
                                f"using module binding only"
                            )

                        # P0.17: Also update module namespace bindings (for explicit module.func access)
                        # This is always needed, even if trampoline was installed (for module.func patterns)
                        _install_wrapper_everywhere(self._original, wrapper)
                        logger.debug(f"Self-destruct: Installed disabled-aware wrapper everywhere for {self._func_name}")

                        # Notify callback
                        if self._on_verified_callback:
                            try:
                                self._on_verified_callback(True)
                            except Exception as e:
                                logger.error(f"Verification callback failed: {e}")
                        return original_result  # Return original result (already computed)
                    else:
                        # SPEEDUP VERIFICATION FAILED: Compiled is not faster (or marginally faster)
                        # This is the critical fix for tiny workloads showing 0.0x speedup
                        logger.info(
                            f"JIT speedup verification FAILED for {self._func_name}: "
                            f"{speedup_result.reason} - reverting to original"
                        )
                        self._verified = True
                        self._use_compiled = False

                        # Self-destruct - replace wrapper with original in ALL locations
                        # P0.17: Use _install_wrapper_everywhere to update all local bindings
                        # P0.18: Restore original code if trampoline was installed (defensive)
                        if isinstance(self._original, types.FunctionType):
                            _restore_original_code(self._original)
                        _install_wrapper_everywhere(self._original, self._original)
                        logger.debug(f"Self-destruct: Replaced wrapper with original everywhere (speedup insufficient)")

                        # Notify callback (False = don't use compiled)
                        if self._on_verified_callback:
                            try:
                                self._on_verified_callback(False)
                            except Exception as e:
                                logger.error(f"Verification callback failed: {e}")
                        return original_result
                else:
                    # FAILURE: Revert to original
                    logger.warning(
                        f"JIT canary FAILED for {self._func_name}: "
                        f"output mismatch detected, reverting to original"
                    )
                    self._verified = True
                    self._use_compiled = False

                    # CRITICAL FIX: Self-destruct - replace wrapper with original function in ALL locations
                    # This prevents Numba from seeing wrapper object in subsequent compilations
                    # P0.17: Use _install_wrapper_everywhere to update all local bindings
                    # P0.18: Restore original code if trampoline was installed (defensive)
                    if isinstance(self._original, types.FunctionType):
                        _restore_original_code(self._original)
                    _install_wrapper_everywhere(self._original, self._original)
                    logger.debug(f"Self-destruct: Replaced wrapper with original function everywhere for {self._func_name}")

                    # Notify callback
                    if self._on_verified_callback:
                        try:
                            self._on_verified_callback(False)
                        except Exception as e:
                            logger.error(f"Verification callback failed: {e}")
                    return original_result  # Return original result (already computed)

            except Exception as e:
                # Original function threw exception - let it propagate
                # (this is expected behavior, not a verification failure)
                logger.debug(f"Original function {self._func_name} raised: {e}")
                raise

    @property
    def is_verified(self) -> bool:
        """Check if verification has been performed."""
        return self._verified

    @property
    def is_using_compiled(self) -> bool:
        """Check if currently using compiled version."""
        return self._verified and self._use_compiled

    def get_original(self) -> Callable:
        """Get the original function (for testing/debugging)."""
        return self._original

    def get_compiled(self) -> Callable:
        """Get the compiled function (for testing/debugging)."""
        return self._compiled


class _GPUDisabledAwareWrapper:
    """
    GPU wrapper that respects epochly_disabled_context().

    Similar to _DisabledAwareWrapper but for GPU-compiled functions.
    When Epochly is disabled (e.g., during baseline measurements),
    this wrapper routes to the original Python function instead of the GPU version.

    Author: Epochly Development Team
    Date: December 2025
    """

    def __init__(self, original: Callable, gpu_func: Callable, name: str):
        """
        Initialize GPU disabled-aware wrapper.

        Args:
            original: Original Python function
            gpu_func: GPU-compiled version
            name: Function name for logging
        """
        self._original = original
        self._gpu = gpu_func
        self._name = name

        # Preserve function metadata
        functools.update_wrapper(self, original)

        # Marker attribute for wrapper detection
        self._is_epochly_gpu_wrapper = True

        # NOTE: Wrapper code_id registration moved to class-level (more efficient)
        # See _register_epochly_wrapper_classes() called after class definitions

    def __call__(self, *args, **kwargs) -> Any:
        """Execute function, respecting disabled context."""
        import epochly as ep
        if ep._core_singleton is not None and not ep._core_singleton.enabled:
            return self._original(*args, **kwargs)
        return self._gpu(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to GPU function for type inference compatibility."""
        return getattr(self._gpu, name)

    def __repr__(self):
        return f"<_GPUDisabledAwareWrapper for {self._name}>"


class GPUCanaryWrapper:
    """
    Lazy verification wrapper for GPU-compiled functions.

    CRITICAL: Implements the "canary in the coal mine" pattern for GPU safety.
    Instead of blindly replacing functions with GPU versions, we wrap them and verify
    on the FIRST ACTUAL CALL that the GPU version produces identical output AND
    provides meaningful speedup (GPU has kernel launch overhead that may make it
    slower than CPU for small workloads).

    This is the GPU counterpart to JITCanaryWrapper, enabling transparent LEVEL_4
    acceleration without requiring any user code changes.

    Behavior:
    1. First call: Run BOTH original (CPU) and GPU-compiled, compare results
    2. If match AND speedup verified: Promote to GPU-only mode
    3. If mismatch OR no speedup: Revert to original
    4. Subsequent calls: Use whichever version was selected

    Thread Safety:
    - Uses threading.Lock to ensure exactly one verification occurs
    - Multiple threads may hit first call simultaneously - only one verifies

    Author: Epochly Development Team
    Date: December 2025
    """

    # Minimum speedup threshold for GPU promotion (GPU has kernel launch overhead)
    MIN_GPU_SPEEDUP = 1.2

    def __init__(
        self,
        original_func: Callable,
        gpu_func: Callable,
        func_name: str = "",
        on_verified_callback: Optional[Callable[[bool], None]] = None,
        known_speedup_ratio: Optional[float] = None
    ):
        """
        Initialize GPU canary wrapper.

        Args:
            original_func: The original Python function
            gpu_func: The GPU-compiled version
            func_name: Function name for logging
            on_verified_callback: Optional callback(use_gpu: bool) called after verification.
                                  True if GPU acceleration is active, False otherwise.
            known_speedup_ratio: Pre-measured speedup ratio. If >= MIN_GPU_SPEEDUP (1.2x),
                                 skip speedup verification and trust the pre-measured value.
                                 Correctness verification still runs regardless.
        """
        self._original = original_func
        self._gpu = gpu_func
        self._func_name = func_name or getattr(original_func, '__name__', 'unknown')
        self._on_verified_callback = on_verified_callback
        self._known_speedup_ratio = known_speedup_ratio

        # Verification state
        self._verified = False
        self._use_gpu = False
        self._verification_lock = threading.Lock()

        # Preserve function metadata for transparency
        functools.update_wrapper(self, original_func)

        # Marker attribute for wrapper detection
        self._is_epochly_gpu_wrapper = True

    def __call__(self, *args, **kwargs) -> Any:
        """
        Execute function with lazy verification on first call.

        Returns:
            Function result (from original or GPU, depending on verification state)
        """
        # Respect epochly_disabled_context
        import epochly as ep
        if ep._core_singleton is not None and not ep._core_singleton.enabled:
            return self._original(*args, **kwargs)

        # Fast path: already verified
        if self._verified:
            if self._use_gpu:
                return self._gpu(*args, **kwargs)
            else:
                return self._original(*args, **kwargs)

        # Slow path: first call - perform verification
        with self._verification_lock:
            # Double-check after acquiring lock
            if self._verified:
                if self._use_gpu:
                    return self._gpu(*args, **kwargs)
                else:
                    return self._original(*args, **kwargs)

            # Copy arguments for safe GPU verification
            args_copy = []
            kwargs_copy = {}
            all_copyable = True

            for arg in args:
                success, copied = _try_deep_copy(arg)
                if not success:
                    all_copyable = False
                    break
                args_copy.append(copied)

            if all_copyable:
                for k, v in kwargs.items():
                    success, copied = _try_deep_copy(v)
                    if not success:
                        all_copyable = False
                        break
                    kwargs_copy[k] = copied

            if not all_copyable:
                # Can't safely verify - fall back to original
                logger.debug(
                    f"GPU canary skipped for {self._func_name}: "
                    f"arguments not copyable, using original"
                )
                self._verified = True
                self._use_gpu = False
                self._self_destruct_to_original()
                self._notify_callback(False)
                return self._original(*args, **kwargs)

            args_copy = tuple(args_copy)

            # Perform GPU canary verification
            try:
                # Run GPU on COPIES first - handle OOM specifically
                try:
                    gpu_result = self._gpu(*args_copy, **kwargs_copy)
                except MemoryError as e:
                    # GPU out of memory - revert to CPU
                    logger.warning(
                        f"GPU canary FAILED for {self._func_name}: "
                        f"GPU out of memory, reverting to CPU"
                    )
                    self._verified = True
                    self._use_gpu = False
                    self._self_destruct_to_original()
                    self._notify_callback(False)
                    return self._original(*args, **kwargs)
                except RuntimeError as e:
                    # Check for CUDA OOM in RuntimeError
                    if 'out of memory' in str(e).lower() or 'cuda' in str(e).lower():
                        logger.warning(
                            f"GPU canary FAILED for {self._func_name}: "
                            f"GPU error (possible OOM): {e}"
                        )
                        self._verified = True
                        self._use_gpu = False
                        self._self_destruct_to_original()
                        self._notify_callback(False)
                        return self._original(*args, **kwargs)
                    raise  # Re-raise if not OOM-related
                except Exception as e:
                    # GPU version threw other exception - revert to original
                    logger.debug(
                        f"GPU canary FAILED for {self._func_name}: "
                        f"GPU version raised {type(e).__name__}: {e}"
                    )
                    self._verified = True
                    self._use_gpu = False
                    self._self_destruct_to_original()
                    self._notify_callback(False)
                    return self._original(*args, **kwargs)

                # Run original on REAL args (user-visible call)
                original_result = self._original(*args, **kwargs)

                # Compare results for correctness
                if not _results_match(original_result, gpu_result, self._func_name):
                    # FAILURE: Results don't match - revert to original
                    logger.warning(
                        f"GPU canary FAILED for {self._func_name}: "
                        f"output mismatch detected, reverting to original"
                    )
                    self._verified = True
                    self._use_gpu = False
                    self._self_destruct_to_original()
                    self._notify_callback(False)
                    return original_result

                # Results match - now verify speedup
                # TIMING CONSISTENCY (Dec 2025): Skip speedup verification if we have
                # pre-measured speedup >= MIN_GPU_SPEEDUP, similar to P0.25 for CPU JIT.
                if self._known_speedup_ratio is not None and self._known_speedup_ratio >= self.MIN_GPU_SPEEDUP:
                    # Trust pre-measured speedup
                    use_gpu = True
                    speedup_for_log = self._known_speedup_ratio
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(
                            f"GPU canary using pre-verified speedup for {self._func_name}: "
                            f"{self._known_speedup_ratio:.2f}x"
                        )
                else:
                    # No pre-verified speedup - run verification
                    # GPU needs higher speedup threshold due to kernel launch overhead
                    speedup_result = verify_speedup(
                        self._original,
                        self._gpu,
                        test_args=args_copy,
                        test_kwargs=kwargs_copy,
                        num_trials=3,  # Fewer trials for GPU (compilation already done)
                        min_speedup=self.MIN_GPU_SPEEDUP
                    )
                    use_gpu = speedup_result.use_compiled
                    speedup_for_log = speedup_result.speedup_ratio

                if use_gpu:
                    # SUCCESS: Speedup verified - promote to GPU
                    if logger.isEnabledFor(logging.INFO):
                        logger.info(
                            f"GPU canary PASSED for {self._func_name}: "
                            f"promoting to GPU ({speedup_for_log:.2f}x speedup)"
                        )
                    self._verified = True
                    self._use_gpu = True

                    # Install disabled-aware wrapper (inside lock for safety)
                    if hasattr(self._original, '__globals__') and self._func_name in self._original.__globals__:
                        self._original.__globals__[self._func_name] = _GPUDisabledAwareWrapper(
                            self._original, self._gpu, self._func_name
                        )
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f"GPU self-destruct: Installed disabled-aware wrapper for {self._func_name}")

                    self._notify_callback(True)
                    return original_result
                else:
                    # SPEEDUP VERIFICATION FAILED: GPU is not faster
                    if logger.isEnabledFor(logging.INFO):
                        logger.info(
                            f"GPU speedup verification FAILED for {self._func_name}: "
                            f"{speedup_result.reason} - reverting to original"
                        )
                    self._verified = True
                    self._use_gpu = False
                    self._self_destruct_to_original()
                    self._notify_callback(False)
                    return original_result

            except Exception as e:
                # Original function threw exception - let it propagate
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Original function {self._func_name} raised: {e}")
                raise

    def _self_destruct_to_original(self):
        """Replace this wrapper with the original function in globals.

        Note: Called inside verification lock for thread safety.
        """
        if hasattr(self._original, '__globals__') and self._func_name in self._original.__globals__:
            self._original.__globals__[self._func_name] = self._original
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"GPU self-destruct: Replaced wrapper with original for {self._func_name}")

    def _notify_callback(self, use_gpu: bool):
        """Notify verification callback if set.

        Args:
            use_gpu: True if GPU acceleration is now active, False otherwise
        """
        if self._on_verified_callback:
            try:
                self._on_verified_callback(use_gpu)
            except Exception as e:
                logger.error(f"GPU verification callback failed: {e}")

    def __repr__(self) -> str:
        """String representation for debugging."""
        status = "verified" if self._verified else "pending"
        mode = "GPU" if self._use_gpu else "original"
        return f"<GPUCanaryWrapper({self._func_name}, status={status}, using={mode})>"

    @property
    def is_verified(self) -> bool:
        """Check if verification has been performed."""
        return self._verified

    @property
    def is_using_gpu(self) -> bool:
        """Check if currently using GPU version."""
        return self._verified and self._use_gpu

    def get_original(self) -> Callable:
        """Get the original function (for testing/debugging)."""
        return self._original

    def get_gpu(self) -> Callable:
        """Get the GPU function (for testing/debugging)."""
        return self._gpu


# =============================================================================
# CRITICAL FIX (Jan 2025): Register all Epochly wrapper class __call__ code_ids
# This MUST happen after all wrapper classes are defined, before AutoProfiler.
# The profiler's fast-path checks _wrapper_call_code_ids to skip profiling
# wrapper infrastructure, preventing the "Run 2 > Run 1" variance bug.
# =============================================================================
def _register_epochly_wrapper_classes() -> None:
    """
    Register all Epochly wrapper classes' __call__ code_ids.

    Called once at module load time. More efficient than per-instance registration
    since __call__.__code__ is the same for all instances of a class.
    """
    wrapper_classes = [
        _DisabledAwareWrapper,
        JITPendingWrapper,
        JITCanaryWrapper,
        _GPUDisabledAwareWrapper,
        GPUCanaryWrapper,
    ]
    for wrapper_cls in wrapper_classes:
        _register_wrapper_class(wrapper_cls)


# Execute registration at module load time
_register_epochly_wrapper_classes()


class AutoProfiler:
    """
    Automatic Performance Profiler and Optimizer.

    Zero-config profiling that:
    1. Detects functions consuming >10ms CPU time
    2. Analyzes loop patterns and memory access
    3. Predicts speedup with ML model
    4. Automatically compiles with JIT
    5. Automatically slices data for parallel execution

    Zero configuration required - activates automatically when Epochly is enabled.
    """

    def __init__(self, cpu_threshold_ms: float = 10.0, module_allowlist: List[str] = None,
                 module_denylist: List[str] = None, sampling_only: bool = False):
        """
        Initialize auto-profiler.

        Args:
            cpu_threshold_ms: CPU time threshold for hot loop detection (milliseconds)
            module_allowlist: Only profile these modules (None = all modules)
            module_denylist: Never profile these modules
            sampling_only: Use sampling mode (cheap timer check before enabling)
        """
        self.cpu_threshold_ms = cpu_threshold_ms
        self._hot_loops: Dict[int, HotLoopInfo] = {}
        self._loop_timings: Dict[int, List[float]] = defaultdict(list)
        self._enabled = False
        self._lock = threading.RLock()

        # Scoping configuration (Performance fix: Nov 22, 2025)
        self._module_allowlist = set(module_allowlist) if module_allowlist else None
        self._module_denylist = set(module_denylist) if module_denylist else {
            'logging', 'threading', 'queue', 'collections', 'weakref',
            'site-packages', 'importlib', '_bootstrap'
            # NOTE: Don't use 'epochly' here - too broad (matches user project dirs)
            # /src/epochly/ is already in system_indicators for Epochly source filtering
        }
        self._sampling_only = sampling_only

        # Function extraction cache (Performance fix: avoid gc.get_referrers)
        self._code_to_function_cache = {}  # code_id -> function
        self._cache_lock = threading.Lock()

        # Save existing trace function for chaining
        self._previous_trace = None

        # Detect profiling backend
        self._use_sys_monitoring = sys.version_info >= (3, 12)

        # Track the actual profiling backend being used for accurate logging
        # Possible values: "sys.monitoring", "sampling", "sys.settrace", "disabled"
        self._profiling_backend = "unknown"

        # Function call stack for tracking loop context
        self._call_stack: List[tuple] = []

        # Issue 1 fix: Thread-safe function timing storage
        self._thread_local_data = threading.local()

        # Neural orchestrator integration
        self._adaptive_orchestrator = None
        self._jit_analyzer = None
        self._use_ml_guidance = False

        # Loop transformer integration
        self._loop_transformer = None
        self._use_anticipatory_transformation = False
        self._hot_code_ids = set()
        self._transforming_functions = set()

        # P0.12 FIX (Dec 2025): Reference to JIT manager for failed compilation checks
        # When background compilation fails, jit_manager._failed_code_ids is updated.
        # We need to check this in monitoring callbacks to return DISABLE.
        self._jit_manager_ref = None  # Set via set_jit_manager()

        # CRITICAL FIX (Dec 2025): Track JIT-compiled code objects for monitoring bypass
        # When a function is JIT compiled, we MUST stop monitoring it to avoid overhead
        # Without this, sys.monitoring adds 30x overhead even to compiled functions!
        # NOTE: This set serves dual purpose - contains BOTH:
        #   1. Successfully JIT-compiled functions (use compiled version)
        #   2. Permanently failed functions (use original, never retry)
        # Both cases require sys.monitoring.DISABLE to stop hot detection
        self._jit_compiled_code_ids = set()  # code_id -> monitoring disabled

        # CRITICAL FIX (Dec 2025): Track permanent compilation failures
        # Functions that fail JIT compilation should NEVER be retried
        # Otherwise we enter an infinite loop: detect hot -> compile -> fail -> detect hot again
        # NOTE: Functions in this set are ALSO added to _jit_compiled_code_ids above
        # to disable monitoring (the semantic is "don't optimize this function anymore")
        self._compilation_failures_permanent = set()  # code_id -> permanently blacklisted

        # AGGREGATE HOT DETECTION (Dec 2025): Track cumulative time across multiple calls
        # This enables detection of functions that are called many times but each call is fast
        # Example: compute_features() called 64x at 1.5ms each = 96ms total = HOT!
        self._aggregate_time_ns: Dict[int, int] = defaultdict(int)  # code_id -> cumulative time in ns
        self._aggregate_call_count: Dict[int, int] = defaultdict(int)  # code_id -> call count
        self._aggregate_window_start_ns: Dict[int, int] = {}  # code_id -> window start time
        self._aggregate_threshold_ms: float = 50.0  # Trigger optimization if aggregate >50ms
        self._aggregate_window_ms: float = 1000.0  # Reset window every 1 second
        self._aggregate_min_calls: int = 3  # Minimum calls before considering aggregate

        # P0.6 FIX (Dec 2025): Cache analyzed code objects to prevent repeated analysis
        # analyze_function() is EXPENSIVE: inspect.getsource + ast.parse + tree walk
        # Without this cache, EVERY function call triggers analysis (10x slowdown!)
        # Functions are cached regardless of analysis result (transformable or not)
        #
        # BOUNDED CACHE (Dec 2025): Prevent unbounded memory growth in long-running processes
        # When cache exceeds limit, we clear it (simple but effective for code_ids)
        # Re-analysis cost is amortized over many operations
        self._analyzed_code_ids: set = set()  # code_id -> already analyzed, skip
        self._analyzed_code_ids_max_size = 10000  # Max 10k entries before clearing

        # P0.7 FIX (Dec 2025): Track non-transformable functions to disable monitoring
        # Functions analyzed and found UNSUITABLE for transformation are added here.
        # In _monitoring_py_start(), we return sys.monitoring.DISABLE for these functions
        # to eliminate the 50% monitoring overhead for functions that will never be transformed.
        # BOUNDED CACHE: Same strategy as _analyzed_code_ids
        self._non_transformable_code_ids: set = set()  # code_id -> analyzed, not transformable
        self._non_transformable_code_ids_max_size = 10000  # Max 10k entries before clearing

        # P0.11 FIX (Dec 2025): Cache system code IDs to avoid repeated string comparisons
        # _is_system_code() does 5+ string contains checks per call. By caching the result
        # per code_id, we turn subsequent checks into O(1) set lookups.
        self._system_code_ids: set = set()  # code_id -> known system code

        # CRITICAL FIX: Prevent recursive optimization during benchmarking
        self._optimization_in_progress = threading.local()

        # PYTHON 3.9 PERFORMANCE FIX (Dec 2025): Auto-disable sys.settrace after warmup
        # sys.settrace has inherent per-call overhead (~0.1ms) that accumulates significantly.
        # Once hot paths are detected and JIT is triggered, continued profiling only adds overhead.
        # After N consecutive fast-path skips (no new hot functions found), disable tracing entirely.
        # This is critical for Python 3.9 where sys.settrace overhead dominates warmup time.
        self._trace_skip_counter = 0  # Count consecutive fast-path skips
        self._trace_skip_threshold = 50  # After 50 skips with hot paths, disable tracing ASAP
        self._trace_auto_disabled = False  # True once tracing is auto-disabled

        # PYTHON 3.9 SAMPLING PROFILER (Dec 2025): Low-overhead alternative to sys.settrace
        # sys.settrace has 7-10x overhead that cannot be eliminated (VM callback cost).
        # Sampling-based profiling has <5% overhead by sampling stack every 10ms.
        # This is the recommended approach per PEP 669 research and profiling best practices.
        self._sampling_enabled = False  # True when sampling is active
        self._sampling_interval_sec = 0.01  # 10ms sampling interval (100 samples/sec)
        self._sampling_function_counts: Dict[int, int] = {}  # code_id -> sample count
        self._sampling_function_time: Dict[int, float] = {}  # code_id -> estimated CPU time
        self._sampling_total_samples = 0  # Total samples taken
        self._sampling_hot_threshold = 5  # samples before considering hot (50ms at 10ms interval)
        self._old_signal_handler = None  # Store old SIGPROF handler
        self._sampling_pending_hot: list = []  # Queue of (code, code_id, time, count) tuples for deferred processing
        self._sampling_processing_lock = threading.Lock()  # Lock for processing queue (NOT used in signal handler)
        self._sampling_processor_thread: Optional[threading.Thread] = None  # Background thread for processing queue
        self._sampling_processor_stop = threading.Event()  # Stop signal for processor thread

        # Lazy logger initialization
        self._logger = None

    @property
    def logger(self):
        """Lazy logger to avoid initialization overhead."""
        if self._logger is None:
            self._logger = logging.getLogger(__name__)
        return self._logger

    def _get_thread_function_times(self):
        """Get thread-local function timing storage (Issue 1 fix: thread safety)."""
        if not hasattr(self._thread_local_data, 'function_times'):
            self._thread_local_data.function_times = defaultdict(list)
        return self._thread_local_data.function_times

    def enable(self):
        """
        Enable automatic profiling (AUTOMATIC per architecture spec).

        Installs profiling hooks by default for "it just works" hot path detection.
        Performance is minimal through sampling, scoping, and caching.

        Can opt-out with EPOCHLY_AUTO_PROFILING_ENABLED=0 if needed.
        """
        with self._lock:
            if self._enabled:
                return

            # Check for explicit DISABLE (opt-out)
            import os
            if os.environ.get('EPOCHLY_AUTO_PROFILING_ENABLED') == '0':
                # Allow opt-out if explicitly disabled
                self._profiling_backend = "disabled"
                return

            # CRITICAL: Save existing trace function
            self._previous_trace = sys.gettrace()

            # Check for trace conflicts
            if not self._use_sys_monitoring and self._previous_trace is not None:
                if self.logger.isEnabledFor(logging.WARNING):
                    self.logger.warning(
                        "Existing trace function detected - auto-profiling disabled to avoid conflicts"
                    )
                self._profiling_backend = "disabled"
                return

            try:
                if self._use_sys_monitoring:
                    self._enable_sys_monitoring()
                else:
                    self._enable_sys_settrace()

                # Check if profiling was actually enabled (defensive: only known backends)
                # Valid backends: "sys.monitoring", "sampling", "sys.settrace"
                # Invalid/disabled: "disabled", "unknown", or anything else
                valid_backends = {"sys.monitoring", "sampling", "sys.settrace"}
                if self._profiling_backend in valid_backends:
                    self._enabled = True
                    # Only log if logging enabled (guard INFO logs)
                    if self.logger.isEnabledFor(logging.INFO):
                        self.logger.info(
                            f"AutoProfiler enabled ({self._profiling_backend})"
                        )
                else:
                    # Profiling not active (sampling failed, non-main thread, etc.)
                    self._enabled = False
                    if self.logger.isEnabledFor(logging.WARNING):
                        self.logger.warning(
                            f"AutoProfiler initialization complete but hot-path detection disabled "
                            f"(backend={self._profiling_backend}, sys.settrace avoided for performance)"
                        )

            except Exception as e:
                if self.logger.isEnabledFor(logging.ERROR):
                    self.logger.error(f"Failed to enable AutoProfiler: {e}")
                self._enabled = False
                if self._previous_trace:
                    sys.settrace(self._previous_trace)

    def disable(self):
        """Disable automatic profiling and restore previous trace function."""
        with self._lock:  # Thread-safe disable
            if not self._enabled:
                return

            try:
                if self._use_sys_monitoring:
                    self._disable_sys_monitoring()
                else:
                    self._disable_sys_settrace()

                # Disable sampling profiler if it was enabled (Python 3.9-3.11 on Unix)
                # This is separate from sys.settrace - sampling can be active while settrace is not
                if self._sampling_enabled:
                    self._disable_sampling_profiler()

                # Restore previous trace function
                if self._previous_trace:
                    sys.settrace(self._previous_trace)
                    logger.debug("Restored previous trace function")

                self._enabled = False
                self._profiling_backend = "disabled"
                logger.debug("AutoProfiler disabled")

            except Exception as e:
                logger.error(f"Failed to disable AutoProfiler: {e}")

    def _enable_sys_monitoring(self):
        """
        Enable sys.monitoring for low-overhead profiling (Python 3.12+).

        sys.monitoring is the modern profiling API that replaces sys.settrace.
        It's event-based, fast, and doesn't require per-line tracing.
        """
        try:
            import sys
            if not hasattr(sys, 'monitoring'):
                logger.warning("sys.monitoring not available, falling back to sys.settrace")
                self._use_sys_monitoring = False
                self._enable_sys_settrace()
                return

            # Use COVERAGE_ID (0) for auto-profiler (JIT manager uses PROFILER_ID (2))
            # Tool IDs must be 0-5 (reserved), pick one not used by JIT
            self._monitoring_tool_id = sys.monitoring.COVERAGE_ID
            sys.monitoring.use_tool_id(self._monitoring_tool_id, "epochly_auto_profiler")

            # Register callbacks for function events
            sys.monitoring.register_callback(
                self._monitoring_tool_id,
                sys.monitoring.events.PY_START,
                self._monitoring_py_start
            )
            sys.monitoring.register_callback(
                self._monitoring_tool_id,
                sys.monitoring.events.PY_RETURN,
                self._monitoring_py_return
            )

            # Enable monitoring for both PY_START and PY_RETURN events
            sys.monitoring.set_events(
                self._monitoring_tool_id,
                sys.monitoring.events.PY_START | sys.monitoring.events.PY_RETURN
            )

            self._profiling_backend = "sys.monitoring"
            logger.debug(f"sys.monitoring enabled (tool_id={self._monitoring_tool_id})")

        except Exception as e:
            logger.warning(f"Failed to enable sys.monitoring: {e}")
            # Fall back to settrace (which will use sampling on Unix)
            self._use_sys_monitoring = False
            self._enable_sys_settrace()

    def _enable_sys_settrace(self):
        """
        Enable profiling for Python <3.12 using SAMPLING (not sys.settrace).

        PYTHON 3.9 FIX (Dec 2025): sys.settrace has inherent 7-10x overhead that
        cannot be eliminated (VM callback cost per function call). Instead, we use
        signal-based sampling which has <5% overhead.

        Sampling approach:
        - Use SIGPROF signal with setitimer to sample every 10ms
        - In signal handler, capture stack and count function occurrences
        - When function appears frequently (5+ samples), mark as hot
        - This matches the approach used by py-spy, scalene, and other profilers

        Falls back to sys.settrace if signals unavailable (Windows).
        """
        import threading
        import platform

        # Only enable on main thread
        if threading.current_thread() is not threading.main_thread():
            logger.debug("Profiling only available on main thread, skipping")
            self._profiling_backend = "disabled"
            return

        # PYTHON 3.9-3.11 ARCHITECTURE (Dec 2025 - mcp-reflect validated):
        # On Unix: Use sampling ONLY. Do NOT fall back to sys.settrace (7-10x overhead).
        # On Windows: Use sys.settrace as only option (signals unavailable).
        # JIT function replacement uses monkey-patching, NOT call interception.

        is_unix = hasattr(signal, 'SIGPROF') and hasattr(signal, 'setitimer') and platform.system() != 'Windows'

        if is_unix:
            # Unix: sampling-only path (no settrace fallback)
            try:
                self._enable_sampling_profiler()
                logger.debug("Sampling profiler enabled for Python <3.12 on Unix (<5% overhead)")
                return
            except Exception as e:
                # CRITICAL: Do NOT fall back to sys.settrace on Unix
                # Accept no hot-path detection rather than 7-10x overhead regression
                logger.warning(f"Sampling profiler failed on Unix: {e}")
                logger.warning("Hot-path detection disabled for this session (avoiding sys.settrace overhead)")
                # Note: _sampling_enabled is False by default and _enable_sampling_profiler()
                # only sets it True at the END on success. So if we're here, it was never set True.
                # We explicitly set False for clarity and to handle any edge cases.
                self._sampling_enabled = False
                self._profiling_backend = "disabled"
                return
        else:
            # Windows: sys.settrace is the only option (no signals)
            sys.settrace(self._trace_callback_optimized)
            self._profiling_backend = "sys.settrace"
            logger.debug("Using sys.settrace on Windows (sampling unavailable, higher overhead expected)")

    def _enable_sampling_profiler(self):
        """
        Enable signal-based sampling profiler (<5% overhead vs 7-10x for sys.settrace).

        Uses SIGPROF signal which fires based on CPU time consumed.
        This is the same approach used by py-spy, scalene, and other low-overhead profilers.

        If initialization fails partway through, this method performs cleanup:
        - Restores the previous SIGPROF handler
        - Cancels the ITIMER_PROF timer
        This prevents resource leaks on partial initialization failure.
        """
        old_handler = None
        timer_started = False

        try:
            # Step 1: Store old handler and install new one
            old_handler = signal.signal(signal.SIGPROF, self._sampling_signal_handler)
            self._old_signal_handler = old_handler

            # Step 2: Start periodic sampling (10ms interval = 100 samples/sec)
            # ITIMER_PROF counts CPU time, so only fires when process is running
            signal.setitimer(signal.ITIMER_PROF, self._sampling_interval_sec, self._sampling_interval_sec)
            timer_started = True

            # Step 3: Start background thread to process pending hot functions
            # This thread safely processes the queue from the main process
            self._sampling_processor_stop.clear()
            self._sampling_processor_thread = threading.Thread(
                target=self._sampling_processor_loop,
                name="EpochlySamplingProcessor",
                daemon=True
            )
            self._sampling_processor_thread.start()

            # All steps succeeded - mark as enabled
            self._sampling_enabled = True
            self._profiling_backend = "sampling"
            logger.debug(f"Sampling profiler enabled (interval={self._sampling_interval_sec*1000}ms, <5% overhead)")

        except Exception as e:
            # Cleanup on partial failure to prevent resource leaks
            logger.debug(f"Sampling profiler initialization failed: {e}, performing cleanup")

            # Cancel timer if it was started
            if timer_started:
                try:
                    signal.setitimer(signal.ITIMER_PROF, 0, 0)
                except Exception:
                    pass  # Best effort cleanup

            # Restore old signal handler if we installed ours
            if old_handler is not None:
                try:
                    signal.signal(signal.SIGPROF, old_handler)
                except Exception:
                    pass  # Best effort cleanup

            # Re-raise to let caller handle the failure
            raise

    def _sampling_processor_loop(self):
        """
        Background thread that processes pending hot functions from the sampling queue.

        Runs until stopped, checking the queue every 50ms and processing any
        hot functions that the signal handler has discovered.
        """
        while not self._sampling_processor_stop.is_set():
            try:
                # Process any pending hot functions
                self._process_sampling_pending_hot()

                # Sleep briefly before checking again (50ms = 20 checks/sec)
                # This is a good balance between responsiveness and CPU usage
                self._sampling_processor_stop.wait(0.05)
            except Exception as e:
                logger.debug(f"Error in sampling processor loop: {e}")
                # Continue running even on errors
                self._sampling_processor_stop.wait(0.1)

    def _sampling_signal_handler(self, signum, frame):
        """
        SIGPROF handler - samples current stack and counts function occurrences.

        Called every 10ms of CPU time. Captures the call stack and counts how often
        each function appears. Functions appearing frequently are queued for optimization.

        SAFETY: Signal handlers must be FAST and NON-BLOCKING. We ONLY do:
        - Frame walking (cheap)
        - Dictionary updates (atomic in CPython due to GIL)
        - List appends (atomic in CPython)
        - NO I/O, NO locks, NO complex allocations, NO function calls that use locks
        """
        if not self._sampling_enabled:
            return

        try:
            self._sampling_total_samples += 1

            # Walk the stack and count function occurrences
            current_frame = frame
            while current_frame is not None:
                code = current_frame.f_code
                filename = code.co_filename

                # Skip system code (same filter as sys.settrace path)
                if not self._is_system_code(filename):
                    code_id = id(code)

                    # Increment sample count (dict access is atomic under GIL)
                    self._sampling_function_counts[code_id] = self._sampling_function_counts.get(code_id, 0) + 1

                    # Estimate CPU time (each sample = ~10ms of CPU time)
                    self._sampling_function_time[code_id] = (
                        self._sampling_function_counts[code_id] * self._sampling_interval_sec * 1000
                    )

                    # Check if this function is now hot
                    count = self._sampling_function_counts[code_id]
                    if count >= self._sampling_hot_threshold:
                        # Check if already queued (simple set lookup, no locks)
                        if code_id not in self._hot_code_ids and code_id not in self._analyzed_code_ids:
                            # Mark as analyzed to prevent re-queuing
                            self._analyzed_code_ids.add(code_id)
                            estimated_time_ms = self._sampling_function_time[code_id]

                            # Queue for deferred processing - list.append is atomic under GIL
                            # DO NOT call any functions that use locks from here!
                            self._sampling_pending_hot.append((code, code_id, estimated_time_ms, count))

                current_frame = current_frame.f_back

        except Exception:
            # Never crash in signal handler
            pass

    def _process_sampling_pending_hot(self):
        """
        Process pending hot functions from sampling profiler.

        MUST be called from main thread, NOT from signal handler.
        This is where we safely do lock acquisition, JIT triggering, etc.
        """
        if not self._sampling_pending_hot:
            return

        # Atomically swap out the pending list to avoid signal handler conflicts
        with self._sampling_processing_lock:
            pending = self._sampling_pending_hot
            self._sampling_pending_hot = []

        for code, code_id, estimated_time_ms, sample_count in pending:
            try:
                # Create HotLoopInfo for optimization
                hot_loop = HotLoopInfo(
                    code_object=code,
                    start_line=code.co_firstlineno,
                    cpu_time_ms=estimated_time_ms,
                    iteration_count=sample_count
                )

                loop_id = f"{code.co_filename}:{code.co_name}:{code.co_firstlineno}"
                with self._lock:
                    self._hot_loops[loop_id] = hot_loop

                logger.debug(f"Processing sampled hot function: {code.co_name} (samples={sample_count}, est_time={estimated_time_ms}ms)")

                # Trigger optimization (this schedules background JIT compilation)
                result = self._trigger_optimization(hot_loop)

                # P0.14 FIX (Dec 2025): Only disable sampling after SUCCESSFUL compilation queue
                # Previously, sampling was disabled after ANY hot function processing, including
                # when JIT wasn't ready yet (DEFERRED). This caused a race condition:
                # 1. Module-level code detected as "hot" during import
                # 2. JIT not ready yet, optimization DEFERRED
                # 3. Sampling disabled anyway
                # 4. JIT becomes ready 400ms later, but sampling is OFF
                # 5. User functions never get detected or compiled
                #
                # Fix: Only disable sampling when compilation was actually SUCCESS (queued)
                # Keep sampling enabled when:
                # - DEFERRED: JIT not ready yet, need to retry
                # - FAILED: Want to try other functions
                # - SKIPPED: Function unsuitable, but others might be suitable
                if result == OptimizationResult.SUCCESS:
                    # Mark as hot so we don't re-process this function
                    with self._lock:
                        self._hot_code_ids.add(code_id)

                    if not self._trace_auto_disabled and self._sampling_enabled:
                        self._disable_sampling_profiler()
                        self._trace_auto_disabled = True
                        logger.debug(f"Auto-disabled sampling profiler after successful JIT queue")
                elif result == OptimizationResult.DEFERRED:
                    # P0.14 FIX: Allow re-detection when JIT becomes ready
                    # Remove from _analyzed_code_ids so the signal handler can queue it again
                    # Don't add to _hot_code_ids (we haven't actually processed it)
                    with self._lock:
                        self._analyzed_code_ids.discard(code_id)
                    logger.debug(f"Deferred {code.co_name}: will retry when JIT ready")

            except Exception as e:
                logger.debug(f"Error processing sampled hot function: {e}")

    def _disable_sampling_profiler(self):
        """Disable the sampling profiler and stop the processor thread."""
        try:
            if self._sampling_enabled:
                # Stop the timer first
                signal.setitimer(signal.ITIMER_PROF, 0, 0)

                # Mark as disabled (signal handler will exit early)
                self._sampling_enabled = False

                # Restore old signal handler
                if self._old_signal_handler is not None:
                    signal.signal(signal.SIGPROF, self._old_signal_handler)

                # Stop the processor thread
                if self._sampling_processor_thread is not None:
                    self._sampling_processor_stop.set()
                    # Don't wait for thread - it's a daemon and will exit on its own

                # Process any remaining pending hot functions one last time
                self._process_sampling_pending_hot()

                logger.debug("Sampling profiler disabled")
        except Exception as e:
            logger.debug(f"Error disabling sampling profiler: {e}")

    def _trace_callback_optimized(self, frame, event, arg):
        """
        Optimized sys.settrace callback with minimal overhead.

        Only processes 'call' and 'return' events for user code.
        Skips all system code, stdlib, and Epochly internals.

        PYTHON 3.9 PERFORMANCE: Auto-disables after warmup to eliminate sys.settrace overhead.
        """
        try:
            # FAST PATH 0: If tracing was auto-disabled, do nothing
            # This check must be first to minimize overhead after warmup
            if self._trace_auto_disabled:
                return None

            # FAST PATH: Only handle call/return (ignore line, exception, etc.)
            if event not in ('call', 'return'):
                return None

            code = frame.f_code
            code_id = id(code)

            # FAST PATH 1: Skip JIT-compiled functions (critical for Python 3.9 performance)
            # Once a function is JIT-compiled, no need to keep profiling it
            # CRITICAL FIX (Jan 2025): Also skip Epochly wrapper __call__ methods
            # Without this check, profiler sees wrapper's __call__ as "new" and re-profiles,
            # causing Run 2 to be SLOWER than Run 1 (13.7x variance bug)
            if code_id in self._jit_compiled_code_ids or code_id in _wrapper_call_code_ids:
                # Track skips for auto-disable when we have hot paths
                if self._hot_code_ids:
                    self._trace_skip_counter += 1
                    if self._trace_skip_counter >= self._trace_skip_threshold:
                        self._trace_auto_disabled = True
                        sys.settrace(None)
                        logger.debug(f"Auto-disabled sys.settrace after {self._trace_skip_counter} skips (hot paths compiled)")
                return None

            # FAST PATH 2: Skip functions already detected as hot (pending JIT)
            # Once detected and submitted for JIT, stop profiling to reduce overhead
            # This is critical for Python 3.9 warmup performance
            if code_id in self._hot_code_ids:
                # Track skips for auto-disable
                self._trace_skip_counter += 1
                if self._trace_skip_counter >= self._trace_skip_threshold:
                    self._trace_auto_disabled = True
                    sys.settrace(None)
                    logger.debug(f"Auto-disabled sys.settrace after {self._trace_skip_counter} skips (hot paths pending JIT)")
                return None

            filename = code.co_filename

            # FAST PATH: Skip system code immediately
            if self._is_system_code(filename):
                return None

            # FAST PATH: Skip if optimization in progress
            if self._is_optimization_in_progress():
                return None

            # Reset skip counter - we found a function to profile
            self._trace_skip_counter = 0

            # Delegate to existing callback
            return self._trace_callback(frame, event, arg)

        except Exception:
            return None  # Never let trace callback crash user code

    def _disable_sys_monitoring(self):
        """Disable sys.monitoring and unregister callbacks."""
        try:
            if hasattr(sys, 'monitoring') and hasattr(self, '_monitoring_tool_id'):
                # Disable all monitoring events for this tool
                sys.monitoring.set_events(self._monitoring_tool_id, 0)

                # Unregister callbacks
                sys.monitoring.register_callback(
                    self._monitoring_tool_id,
                    sys.monitoring.events.PY_START,
                    None
                )
                sys.monitoring.register_callback(
                    self._monitoring_tool_id,
                    sys.monitoring.events.PY_RETURN,
                    None
                )

                # Free tool ID
                sys.monitoring.free_tool_id(self._monitoring_tool_id)

                logger.debug(f"sys.monitoring disabled (tool_id={self._monitoring_tool_id})")
        except Exception as e:
            logger.warning(f"Failed to disable sys.monitoring: {e}")
            # Fall back to settrace cleanup
            self._disable_sys_settrace()

    def _disable_sys_settrace(self):
        """
        Disable sys.settrace.

        CRITICAL: Also disable on threading module.
        """
        sys.settrace(None)
        logger.debug("Disabled sys.settrace profiling")

    def _monitoring_py_start(self, code, instruction_offset):
        """
        sys.monitoring callback for PY_START event (function entry).

        Implements EAGER anticipatory transformation:
        - Analyzes function for parallelizable loops on first call
        - Transforms immediately if loops detected
        - Enables first-call speedup for single-shot scripts

        Args:
            code: Code object
            instruction_offset: Bytecode offset

        Returns:
            sys.monitoring.DISABLE for system code, JIT-compiled code, or when disabled
        """
        try:
            # P0.9 FIX (Dec 2025): Early exit when profiler is disabled
            # This eliminates ALL monitoring overhead when inside epochly_disabled_context()
            # Without this check, callbacks still run expensive logic even when disabled
            if not self._enabled:
                return sys.monitoring.DISABLE

            # P0.25 FIX (Jan 2026): FAST PATH FIRST - O(1) set lookups BEFORE optimization check
            # The previous ordering checked _is_optimization_in_progress() first, which returned
            # None and prevented DISABLE from being returned for known non-transformable code.
            # This caused ongoing overhead for code that should have been disabled immediately.
            code_id = id(code)

            # P0.7 FIX (Dec 2025): Skip NON-TRANSFORMABLE code - HIGHEST PRIORITY
            # This is the most common case after warmup - check it FIRST
            if code_id in self._non_transformable_code_ids:
                return sys.monitoring.DISABLE

            # CRITICAL FIX (Dec 2025): Skip ALREADY JIT-compiled code
            # CRITICAL FIX (Jan 2025): Also skip Epochly wrapper __call__ methods
            if code_id in self._jit_compiled_code_ids or code_id in _wrapper_call_code_ids:
                return sys.monitoring.DISABLE

            # P0.11 FIX: Check CACHED system code IDs (O(1) lookup)
            if code_id in self._system_code_ids:
                return sys.monitoring.DISABLE

            # CRITICAL: Skip if optimization in progress (prevent recursion)
            # This check is moved AFTER fast-path checks so known code IDs still return DISABLE
            if self._is_optimization_in_progress():
                return sys.monitoring.DISABLE  # P0.25: Return DISABLE, not None

            # P0.12 FIX (Dec 2025): Skip code where JIT compilation FAILED
            # Background compilation failures are tracked in jit_manager._failed_code_ids
            # Checking this prevents continued monitoring overhead for functions that
            # were analyzed as "should transform" but failed actual JIT compilation
            if self._jit_manager_ref is not None:
                if hasattr(self._jit_manager_ref, '_failed_code_ids'):
                    if code_id in self._jit_manager_ref._failed_code_ids:
                        # Also add to our local set to avoid repeated jit_manager checks
                        self._non_transformable_code_ids.add(code_id)
                        return sys.monitoring.DISABLE

            # Only now do the expensive string-based system code check (first time only)
            # Note: P0.25 moved _system_code_ids cache check earlier in fast path
            if self._is_system_code(code):
                # Cache this code_id as system code for future O(1) lookups
                if len(self._system_code_ids) < 10000:  # Bounded cache
                    self._system_code_ids.add(code_id)
                return sys.monitoring.DISABLE

            # P0.21 FIX (Dec 2025): Skip module-level code (<module>)
            # Module-level code:
            # 1. Runs once at import (not a hot loop candidate)
            # 2. Can't be JIT compiled (uses STORE_NAME, STORE_GLOBAL opcodes)
            # 3. Attempting to compile causes warnings and wastes cycles
            # Without this fix: set_level(3) causes 148% overhead vs EPOCHLY_LEVEL=3
            if code.co_name == '<module>':
                if len(self._system_code_ids) < 10000:
                    self._system_code_ids.add(code_id)
                return sys.monitoring.DISABLE

            # EAGER TRANSFORMATION: Transform on first call if loops detected
            if self._use_anticipatory_transformation and self._loop_transformer:
                try:
                    # P0.6 FIX: Skip already-analyzed code objects (cache hit = O(1))
                    # analyze_function() is EXPENSIVE: inspect.getsource + ast.parse
                    # Without this check, every call triggers analysis (10x slowdown!)
                    if code_id in self._analyzed_code_ids:
                        # Already analyzed this code - skip expensive re-analysis
                        pass  # Fall through to timing measurement below
                    else:
                        func = self._extract_function_from_code(code)

                        # P0.17 FIX (Dec 2025): Skip Epochly's own dynamically-created code
                        # Dataclass-generated functions have co_filename='<string>' which
                        # bypasses the normal system code check. We detect them by __module__.
                        if func and hasattr(func, '__module__') and func.__module__:
                            if func.__module__.startswith('epochly'):
                                # Add to system_code_ids for future O(1) lookups
                                if len(self._system_code_ids) < 10000:
                                    self._system_code_ids.add(code_id)
                                return sys.monitoring.DISABLE

                        # Initialize analysis to None for safety
                        analysis = None

                        if func and not hasattr(func, '_epochly_transformed'):
                            # Quick check: Does function have parallelizable loops?
                            analysis = self._loop_transformer.analyze_function(func)

                        # P0.6: Mark as analyzed REGARDLESS of result (even None)
                        # This prevents re-analysis of non-transformable functions
                        # BOUNDED: Clear cache if it grows too large (prevents memory leak)
                        if len(self._analyzed_code_ids) >= self._analyzed_code_ids_max_size:
                            self._analyzed_code_ids.clear()
                        self._analyzed_code_ids.add(code_id)

                        # P0.7: Track non-transformable functions to disable monitoring
                        is_transformable = analysis and analysis.get('should_transform', False)

                        # P0.23 FIX (Dec 2025): Check for method calls EARLY
                        # Functions with method calls (like random_state.binomial()) cannot be JIT compiled.
                        # Previously, this was only checked in apply_optimization (after hot detection).
                        # This caused monitoring overhead for 50+ calls before hot threshold was reached!
                        # Now we check it during initial analysis and disable monitoring immediately.
                        has_method_calls = analysis and analysis.get('has_method_calls_in_loop', False)
                        if has_method_calls:
                            is_transformable = False  # Override - method calls make it unsuitable
                            logger.debug(
                                f"P0.23: Function {code.co_name} has method calls in loop - "
                                f"marking as non-transformable to disable monitoring"
                            )

                        if not is_transformable:
                            # Function is NOT transformable - mark for DISABLE
                            # Next call to _monitoring_py_start will return DISABLE immediately
                            # This eliminates 50% of monitoring overhead
                            if len(self._non_transformable_code_ids) >= self._non_transformable_code_ids_max_size:
                                self._non_transformable_code_ids.clear()
                            self._non_transformable_code_ids.add(code_id)

                        if is_transformable:
                            func_id = id(func)

                            # Race protection: Check if another thread is transforming
                            should_transform = False
                            with self._lock:
                                if func_id not in self._transforming_functions:
                                    self._transforming_functions.add(func_id)
                                    should_transform = True

                            if should_transform:
                                try:
                                    # =============================================================
                                    # CRITICAL FIX (Dec 2025): Disable EAGER transformation for Level 3
                                    # =============================================================
                                    # Eager transformation happens BEFORE we have timing data.
                                    # At Level 3, this routes functions to ProcessPool which has
                                    # ~50-200ms IPC overhead per dispatch.
                                    #
                                    # PROBLEM: Transforming 89ms workloads for ProcessPool causes 20x regression!
                                    #          (89ms work + 1700ms overhead = 1789ms total)
                                    #
                                    # SOLUTION: Only allow eager transformation at Level 2 (JIT only).
                                    # For Level 3+, wait for timing-based hot loop detection which
                                    # can apply workload size thresholds.
                                    #
                                    # Level 2 JIT: Eager is safe (JIT has low overhead)
                                    # Level 3 ProcessPool: NO eager (wait for timing data)
                                    should_transform_eager = False
                                    try:
                                        # Guard against reentrant import deadlock (Python 3.13 macOS)
                                        # Note: sys is already imported at module level - do NOT import here
                                        # as it creates a local variable that shadows the global, causing
                                        # UnboundLocalError for all earlier sys.monitoring references!
                                        epochly_core_module = sys.modules.get('epochly.core.epochly_core')
                                        if epochly_core_module is None or not hasattr(epochly_core_module, 'get_epochly_core'):
                                            core = None  # Module not fully loaded - skip eager transformation
                                        else:
                                            from ..core.epochly_core import get_epochly_core, EnhancementLevel
                                            core = get_epochly_core()
                                        if core and hasattr(core, 'current_level'):
                                            current_level_value = core.current_level.value if hasattr(core.current_level, 'value') else 0

                                            # Only allow eager transformation at Level 2 (JIT)
                                            # At Level 3+, DISABLE eager to prevent ProcessPool dispatch
                                            # for small/unsuitable workloads
                                            if current_level_value == EnhancementLevel.LEVEL_2_JIT.value:
                                                should_transform_eager = True
                                                logger.debug(
                                                    f"Level 2 JIT: Enabling eager transformation for {func.__name__}"
                                                )
                                            elif current_level_value >= EnhancementLevel.LEVEL_3_FULL.value:
                                                # Level 3+: DISABLE eager transformation!
                                                # ProcessPool dispatch needs timing data to avoid regressions.
                                                # Hot loop detection in _monitoring_py_return will handle it.
                                                logger.debug(
                                                    f"Level 3+: Disabling eager transformation for {func.__name__} "
                                                    f"(ProcessPool needs timing data to avoid overhead regression)"
                                                )
                                                should_transform_eager = False
                                            else:
                                                # Level 0/1: No transformation
                                                should_transform_eager = False
                                    except Exception as e:
                                        logger.debug(f"Could not check enhancement level: {e}")
                                        # Default to NO eager transformation if level check fails
                                        should_transform_eager = False

                                    if not should_transform_eager:
                                        # Skip eager transformation - let timing-based detection handle it
                                        with self._lock:
                                            self._transforming_functions.discard(func_id)
                                        # P0.24 FIX (Dec 2025): MUST record timing BEFORE returning!
                                        # Without timing data, hot function detection can't trigger.
                                        # This was the root cause of Level 3 notebooks showing 0x speedup.
                                        function_times = self._get_thread_function_times()
                                        function_times[code_id].append(time.perf_counter_ns())
                                        return  # Exit early (but timing is recorded)

                                    # Transform BEFORE execution (eager mode) - Level 2 JIT only
                                    transformed = self._loop_transformer.transform_function(func)

                                    if transformed and transformed != func:
                                        # Thread-safe replacement in globals
                                        with self._lock:
                                            if hasattr(func, '__globals__') and func.__name__ in func.__globals__:
                                                current = func.__globals__[func.__name__]
                                                if not hasattr(current, '_epochly_transformed'):
                                                    func.__globals__[func.__name__] = transformed
                                                    logger.debug(f"PY_START: Eager transformation applied to {func.__name__}")

                                finally:
                                    # Release transformation lock
                                    with self._lock:
                                        self._transforming_functions.discard(func_id)

                except Exception as e:
                    logger.debug(f"Eager transformation failed: {e}")
                    pass  # Silent fallback

            # Record start time for profiling (MCP-Reflect Optimization 3: use perf_counter_ns)
            code_id = id(code)
            # Issue 1 fix: Use thread-local timing storage
            function_times = self._get_thread_function_times()
            function_times[code_id].append(time.perf_counter_ns())

        except Exception:
            return None

    def _monitoring_py_return(self, code, instruction_offset, retval):
        """
        sys.monitoring callback for PY_RETURN events.

        Detects hot functions by measuring execution time.

        Args:
            code: Code object
            instruction_offset: Bytecode offset
            retval: Return value

        Returns:
            sys.monitoring.DISABLE for JIT-compiled code or when disabled, None otherwise
        """
        try:
            # P0.9 FIX (Dec 2025): Early exit when profiler is disabled
            # This eliminates ALL monitoring overhead when inside epochly_disabled_context()
            if not self._enabled:
                return sys.monitoring.DISABLE

            # CRITICAL FIX: Skip if optimization already in progress (prevent recursive execution)
            if self._is_optimization_in_progress():
                return None

            # P0.11 FIX (Dec 2025): Reorder checks - CHEAP SET LOOKUPS BEFORE EXPENSIVE STRING OPS
            # The original order did _is_system_code() (5+ string comparisons) on EVERY callback
            # BEFORE the O(1) set lookups. This caused massive overhead for library calls.
            # New order: code_id lookups first, then _is_system_code() only if needed.
            code_id = id(code)

            # CRITICAL FIX (Dec 2025): Skip ALREADY JIT-compiled code
            # CRITICAL FIX (Jan 2025): Also skip Epochly wrapper __call__ methods
            if code_id in self._jit_compiled_code_ids or code_id in _wrapper_call_code_ids:
                return sys.monitoring.DISABLE

            # CRITICAL FIX (Dec 2025): Skip permanent compilation failures
            if code_id in self._compilation_failures_permanent:
                return sys.monitoring.DISABLE

            # P0.10 FIX (Dec 2025): Skip NON-TRANSFORMABLE code
            if code_id in self._non_transformable_code_ids:
                return sys.monitoring.DISABLE

            # P0.12 FIX (Dec 2025): Skip code where JIT compilation FAILED
            if self._jit_manager_ref is not None:
                if hasattr(self._jit_manager_ref, '_failed_code_ids'):
                    if code_id in self._jit_manager_ref._failed_code_ids:
                        # Also add to our local set to avoid repeated jit_manager checks
                        self._non_transformable_code_ids.add(code_id)
                        return sys.monitoring.DISABLE

            # P0.11 FIX: Check CACHED system code IDs before expensive string operations
            if code_id in self._system_code_ids:
                return sys.monitoring.DISABLE

            # Only now do the expensive string-based system code check (first time only)
            is_system = self._is_system_code(code)
            if is_system:
                # Cache this code_id as system code for future O(1) lookups
                if len(self._system_code_ids) < 10000:  # Bounded cache
                    self._system_code_ids.add(code_id)
                return sys.monitoring.DISABLE

            # Get function entry time from call stack
            # Issue 1 fix: Use thread-local timing storage
            function_times = self._get_thread_function_times()
            if code_id not in function_times or not function_times[code_id]:
                # No entry time recorded - this shouldn't happen in monitoring mode
                # Record entry time for next call (MCP-Reflect Optimization 3: use perf_counter_ns)
                function_times[code_id].append(time.perf_counter_ns())
                return None

            # Pop entry time and calculate CPU time (MCP-Reflect Optimization 3: nanoseconds)
            start_time_ns = function_times[code_id].pop()
            elapsed_ns = time.perf_counter_ns() - start_time_ns
            cpu_time_ms = elapsed_ns / 1_000_000.0

            # AGGREGATE HOT DETECTION (Dec 2025): Track cumulative time across multiple calls
            # This catches functions called many times but each call is fast (e.g., 64x @ 1.5ms = 96ms)
            current_time_ns = time.perf_counter_ns()

            # Check if we need to reset the aggregate window (every _aggregate_window_ms)
            if code_id in self._aggregate_window_start_ns:
                window_elapsed_ms = (current_time_ns - self._aggregate_window_start_ns[code_id]) / 1_000_000.0
                if window_elapsed_ms > self._aggregate_window_ms:
                    # Reset window - start fresh aggregate tracking
                    self._aggregate_time_ns[code_id] = 0
                    self._aggregate_call_count[code_id] = 0
                    self._aggregate_window_start_ns[code_id] = current_time_ns
            else:
                # First call - initialize window
                self._aggregate_window_start_ns[code_id] = current_time_ns

            # Accumulate time and count
            self._aggregate_time_ns[code_id] += elapsed_ns
            self._aggregate_call_count[code_id] += 1

            # Check for aggregate hot detection
            aggregate_time_ms = self._aggregate_time_ns[code_id] / 1_000_000.0
            aggregate_calls = self._aggregate_call_count[code_id]
            is_aggregate_hot = (
                aggregate_calls >= self._aggregate_min_calls and
                aggregate_time_ms >= self._aggregate_threshold_ms
            )

            # Check if function exceeds hot threshold (single-call OR aggregate)
            if cpu_time_ms >= self.cpu_threshold_ms or is_aggregate_hot:
                # Determine detection type and relevant time/count for optimization
                if is_aggregate_hot and cpu_time_ms < self.cpu_threshold_ms:
                    # Aggregate detection: use cumulative stats
                    effective_time_ms = aggregate_time_ms
                    effective_count = aggregate_calls
                    detection_type = "aggregate"
                else:
                    # Single-call detection: use single-call time
                    effective_time_ms = cpu_time_ms
                    effective_count = 1
                    detection_type = "single-call"

                # MCP-Reflect Optimization 4: DEBUG instead of INFO in hot path (but still detect!)
                if logger.isEnabledFor(logging.DEBUG):
                    if detection_type == "aggregate":
                        logger.debug(f"Hot function detected (AGGREGATE): {code.co_name} "
                                   f"({aggregate_calls} calls, {aggregate_time_ms:.2f}ms total) in {code.co_filename}")
                    else:
                        logger.debug(f"Hot function detected: {code.co_name} ({cpu_time_ms:.2f}ms CPU) in {code.co_filename}")

                # Create HotLoopInfo for this function
                loop_id = self._compute_loop_id(code, code.co_firstlineno)

                # P0.7 CRITICAL FIX (Dec 2025): Check if already optimized BEFORE creating new HotLoopInfo
                # Without this check, a NEW HotLoopInfo replaces the old one on every call,
                # losing the optimization_applied=True flag and re-triggering optimization!
                # This caused 1341ms+ overhead per warmup call in genomics notebook.
                with self._lock:
                    existing = self._hot_loops.get(loop_id)
                    if existing and existing.optimization_applied:
                        # Already optimized - DO NOT re-trigger
                        # Just update stats if needed and exit early
                        existing.cpu_time_ms = max(existing.cpu_time_ms, effective_time_ms)
                        existing.iteration_count += effective_count
                        # Skip optimization - already done
                        return

                hot_loop = HotLoopInfo(
                    code_object=code,
                    start_line=code.co_firstlineno,
                    cpu_time_ms=effective_time_ms,
                    iteration_count=effective_count
                )

                with self._lock:
                    self._hot_loops[loop_id] = hot_loop
                    # Mark as hot for anticipatory transformation on next call
                    self._hot_code_ids.add(code_id)

                # PYTHON 3.9 CRITICAL: Immediately disable sys.settrace once hot path is detected
                # Continued profiling only adds overhead - JIT compilation happens in background anyway.
                # This is THE fix for the 9+ second verification overhead in Python 3.9.
                # Python 3.12+ uses sys.monitoring which has much lower overhead.
                if sys.version_info < (3, 12) and not self._trace_auto_disabled:
                    self._trace_auto_disabled = True
                    sys.settrace(None)
                    logger.debug(f"Auto-disabled sys.settrace immediately after hot path detection (code_id={code_id})")

                # Reset aggregate tracking after triggering optimization
                # This prevents re-triggering for the same function
                self._aggregate_time_ns[code_id] = 0
                self._aggregate_call_count[code_id] = 0

                # Issue 3 fix: Release lock before heavy optimization work
                self._trigger_optimization(hot_loop)

        except Exception as e:
            logger.debug(f"Error in _monitoring_py_return: {e}")
            return None

    def _trace_callback(self, frame, event, arg):
        """
        sys.settrace callback for profiling.

        Tracks function calls and returns to measure CPU time.
        Detects hot loops by measuring function execution time.

        Args:
            frame: Current stack frame
            event: Event type ('call', 'return', 'line', etc.)
            arg: Event-specific argument

        Returns:
            Trace function for local tracing or None
        """
        try:
            # CRITICAL FIX: Skip if optimization already in progress (prevent recursive execution)
            if self._is_optimization_in_progress():
                return None

            if event == 'call':
                # Track function entry time
                code = frame.f_code
                # Skip system/library code to avoid overhead
                # P0.12 fix: Use _is_system_code() for consistent filtering across backends
                if self._is_system_code(code):
                    return None

                start_time = time.perf_counter()
                self._call_stack.append((code, start_time, frame.f_lineno))

            elif event == 'return':
                # Calculate function CPU time
                if not self._call_stack:
                    return None

                code, start_time, start_line = self._call_stack.pop()
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                code_id = id(code)

                # AGGREGATE HOT DETECTION (Dec 2025): Track cumulative time across multiple calls
                current_time_ns = time.perf_counter_ns()
                elapsed_ns = int(elapsed_ms * 1_000_000)

                # Check if we need to reset the aggregate window
                if code_id in self._aggregate_window_start_ns:
                    window_elapsed_ms = (current_time_ns - self._aggregate_window_start_ns[code_id]) / 1_000_000.0
                    if window_elapsed_ms > self._aggregate_window_ms:
                        self._aggregate_time_ns[code_id] = 0
                        self._aggregate_call_count[code_id] = 0
                        self._aggregate_window_start_ns[code_id] = current_time_ns
                else:
                    self._aggregate_window_start_ns[code_id] = current_time_ns

                # Accumulate time and count
                self._aggregate_time_ns[code_id] += elapsed_ns
                self._aggregate_call_count[code_id] += 1

                # Check for aggregate hot detection
                aggregate_time_ms = self._aggregate_time_ns[code_id] / 1_000_000.0
                aggregate_calls = self._aggregate_call_count[code_id]
                is_aggregate_hot = (
                    aggregate_calls >= self._aggregate_min_calls and
                    aggregate_time_ms >= self._aggregate_threshold_ms
                )

                # Check if this function/loop exceeds threshold (single-call OR aggregate)
                if elapsed_ms >= self.cpu_threshold_ms or is_aggregate_hot:
                    with self._lock:
                        loop_id = self._compute_loop_id(code, start_line)

                        # Record timing
                        self._loop_timings[loop_id].append(elapsed_ms)

                        # Determine if we should trigger optimization
                        should_trigger = False
                        effective_time_ms = elapsed_ms
                        effective_count = 1
                        detection_type = "single-call"

                        if is_aggregate_hot and elapsed_ms < self.cpu_threshold_ms:
                            # Aggregate detection: trigger immediately
                            should_trigger = True
                            effective_time_ms = aggregate_time_ms
                            effective_count = aggregate_calls
                            detection_type = "aggregate"
                        elif len(self._loop_timings[loop_id]) >= 3:
                            # Single-call: check if consistently hot (3+ measurements)
                            avg_time = sum(self._loop_timings[loop_id]) / len(self._loop_timings[loop_id])
                            if avg_time >= self.cpu_threshold_ms:
                                should_trigger = True
                                effective_time_ms = avg_time
                                effective_count = len(self._loop_timings[loop_id])

                        if should_trigger:
                            # P0.7 CRITICAL FIX (Dec 2025): Check if already optimized
                            # Same fix as in _monitoring_py_return - don't re-trigger
                            existing = self._hot_loops.get(loop_id)
                            if existing and existing.optimization_applied:
                                # Already optimized - just update stats and skip
                                existing.cpu_time_ms = max(existing.cpu_time_ms, effective_time_ms)
                                existing.iteration_count += effective_count
                                # Continue to next iteration (don't re-trigger)
                                return self._trace_callback

                            # Mark as hot loop
                            hot_loop = HotLoopInfo(
                                code_object=code,
                                start_line=start_line,
                                cpu_time_ms=effective_time_ms,
                                iteration_count=effective_count
                            )
                            self._hot_loops[loop_id] = hot_loop
                            # CRITICAL FIX (Jan 2025): Add to _hot_code_ids for consistency with
                            # _monitoring_py_return (line 3448). Without this, the fast-path check
                            # at line 2995 fails and profiling continues with overhead.
                            self._hot_code_ids.add(code_id)

                            if detection_type == "aggregate":
                                logger.debug(f"Hot loop detected (AGGREGATE): {code.co_name} at line {start_line} "
                                          f"({aggregate_calls} calls, {aggregate_time_ms:.2f}ms total)")
                            else:
                                logger.debug(f"Hot loop detected: {code.co_name} at line {start_line} "
                                          f"({effective_time_ms:.2f}ms avg CPU time)")

                            # Reset aggregate tracking after triggering
                            self._aggregate_time_ns[code_id] = 0
                            self._aggregate_call_count[code_id] = 0

                            # Trigger optimization (async to avoid blocking)
                            self._trigger_optimization(hot_loop)

        except Exception as e:
            logger.debug(f"Error in trace callback: {e}")

        return self._trace_callback

    def _should_profile_module(self, module_name: str) -> bool:
        """
        Check if module should be profiled based on allow/deny lists.

        Performance fix (Nov 22, 2025): Implements module scoping.

        Args:
            module_name: Module name or filename

        Returns:
            True if should profile, False if should skip
        """
        # Check allowlist first (if configured)
        if self._module_allowlist is not None:
            return any(allowed in module_name for allowed in self._module_allowlist)

        # Check denylist
        if self._module_denylist:
            return not any(denied in module_name for denied in self._module_denylist)

        # No restrictions
        return True

    def set_module_allowlist(self, modules: List[str]):
        """Set modules to profile (all others skipped)."""
        self._module_allowlist = set(modules)

    def set_module_denylist(self, modules: List[str]):
        """Set modules to never profile."""
        self._module_denylist = set(modules)

    def _is_system_code(self, code_or_filename) -> bool:
        """
        Check if code is from system/library (not user code).

        Args:
            code_or_filename: Code object OR filename string

        Returns:
            True if system code, False if user code
        """
        # Handle both code object and filename string
        if isinstance(code_or_filename, str):
            filename = code_or_filename
        else:
            filename = code_or_filename.co_filename

        # Module scoping (Performance fix: Nov 22, 2025)
        if not self._should_profile_module(filename):
            return True  # Filtered by allow/deny list

        # System code indicators
        # NOTE (Dec 2025): Do NOT include '<string>' here!
        # Dynamically-defined functions (notebooks, exec(), interactive) have
        # filename '<string>' or '<stdin>' and ARE user code that SHOULD be optimized.
        # This was the root cause of notebooks showing no speedup.
        system_indicators = [
            '/lib/python',
            '/site-packages/',
            '/src/epochly/',  # Skip Epochly source
            '<frozen',
            'importlib',
        ]
        return any(indicator in filename for indicator in system_indicators)

    def _is_optimization_in_progress(self) -> bool:
        """
        Check if optimization is currently in progress for this thread.

        CRITICAL: Prevents recursive optimization during benchmarking.

        Returns:
            True if optimization active, False otherwise
        """
        return getattr(self._optimization_in_progress, 'active', False)

    def _set_optimization_in_progress(self, active: bool):
        """
        Set optimization in progress flag for this thread.

        Args:
            active: True to mark optimization active, False to clear
        """
        self._optimization_in_progress.active = active

    def _mark_permanent_failure(self, code_id: int, func_name: str = ""):
        """
        Mark a function as permanently failed (never retry compilation).

        CRITICAL: This prevents infinite retry loops where the system:
        1. Detects function as hot
        2. Tries to compile
        3. Compilation fails
        4. Reverts to original
        5. Monitoring still active → detects hot AGAIN
        6. Repeats infinitely

        Args:
            code_id: Code object ID to blacklist
            func_name: Function name for logging
        """
        with self._lock:
            self._compilation_failures_permanent.add(code_id)
            # CRITICAL: Also add to jit_compiled_code_ids to disable monitoring
            # This stops the hot detection loop
            self._jit_compiled_code_ids.add(code_id)
            # Use DEBUG level - blacklisting is expected behavior for unsuitable functions
            logger.debug(
                f"Blacklisted {func_name or 'function'} "
                f"(code_id {code_id}) - not suitable for JIT compilation"
            )

    def _proactively_compile_inner_functions(
        self, func: Callable, jit_analyzer: Any, core: Any
    ) -> int:
        """
        Proactively compile inner functions called by an unsuitable wrapper.

        CRITICAL FIX (Dec 2025): When a function like run_workload() is unsuitable
        because it returns a dict, the inner compute functions (compute_rolling_rms,
        compute_rolling_variance) may still be excellent JIT candidates.

        This method:
        1. Extracts user-defined functions called by func
        2. Analyzes each for JIT suitability
        3. Proactively compiles suitable ones
        4. Replaces them in their namespace with JIT-compiled versions

        Args:
            func: The unsuitable wrapper function
            jit_analyzer: JIT analyzer instance
            core: Epochly core instance

        Returns:
            Number of inner functions successfully compiled
        """
        compiled_count = 0

        if not hasattr(func, '__globals__'):
            return compiled_count

        # Track functions being compiled to prevent re-entrancy
        compiling_key = f"_proactive_compiling_{id(func)}"
        if getattr(self, compiling_key, False):
            logger.debug(f"Already proactively compiling for {func.__name__}, skipping")
            return compiled_count

        try:
            setattr(self, compiling_key, True)

            # Use the analyzer's method to extract called user functions
            called_functions = jit_analyzer._extract_called_user_functions(func)

            if not called_functions:
                logger.debug(f"No inner user-defined functions found in {func.__name__}")
                return compiled_count

            logger.debug(f"Found {len(called_functions)} inner function(s) in {func.__name__}: "
                       f"{list(called_functions.keys())}")

            # Import JITSuitability for comparison
            from ..plugins.analyzer.jit_analyzer import JITSuitability

            for inner_name, inner_func in called_functions.items():
                if inner_func is None:
                    continue

                # Skip functions without __code__ (builtins, C extensions)
                if not hasattr(inner_func, '__code__'):
                    logger.debug(f"Skipping {inner_name}: no __code__ attribute (builtin/C extension)")
                    continue

                inner_code_id = id(inner_func.__code__)

                # Skip if already compiled or blacklisted
                with self._lock:
                    if inner_code_id in self._jit_compiled_code_ids:
                        logger.debug(f"Inner function {inner_name} already compiled")
                        continue
                    if inner_code_id in self._compilation_failures_permanent:
                        logger.debug(f"Inner function {inner_name} permanently blacklisted")
                        continue

                # Verify we can replace in the caller's namespace
                # The function must be in the caller's globals under its name
                caller_globals = func.__globals__
                if inner_name not in caller_globals or caller_globals.get(inner_name) is not inner_func:
                    # Check inner function's own globals as fallback
                    if not (hasattr(inner_func, '__globals__') and
                            inner_name in inner_func.__globals__ and
                            inner_func.__globals__.get(inner_name) is inner_func):
                        logger.debug(f"Skipping {inner_name}: cannot find correct binding to replace "
                                    f"(may be aliased, closure, or method)")
                        continue

                # Analyze inner function
                try:
                    # P0.18 FIX (Dec 2025): Check loop transformer BEFORE jit_analyzer
                    # The loop transformer has comprehensive method call detection (P0.13)
                    # that catches patterns like random_state.binomial() which jit_analyzer misses
                    if self._loop_transformer:
                        loop_analysis = self._loop_transformer.analyze_function(inner_func)

                        # P0.19 FIX (Dec 2025): When analysis fails (returns None), be CONSERVATIVE
                        # For REPL/notebook code we often can't get source, so skip JIT
                        if loop_analysis is None:
                            logger.debug(
                                f"P0.19: Skipping {inner_name} - "
                                f"loop analysis returned None (source unavailable)"
                            )
                            self._compilation_failures_permanent.add(inner_code_id)
                            continue

                        if loop_analysis.get('has_method_calls_in_loop', False):
                            logger.debug(
                                f"P0.18: Skipping {inner_name} - "
                                f"loop transformer detected non-JIT-compatible method calls: "
                                f"{loop_analysis.get('method_call_names', [])}"
                            )
                            # Add to permanent failures to prevent retries
                            self._compilation_failures_permanent.add(inner_code_id)
                            continue

                    inner_characteristics = jit_analyzer.analyze_function(inner_func)
                    inner_suitability = inner_characteristics.jit_suitability

                    logger.debug(f"Inner function {inner_name}: suitability={inner_suitability.value}")

                    # Check if suitable for JIT
                    if inner_suitability not in [JITSuitability.EXCELLENT, JITSuitability.GOOD]:
                        logger.debug(f"Skipping {inner_name}: suitability={inner_suitability.value}")
                        continue

                    # CRITICAL FIX (Dec 2025): Queue inner function compilation NON-BLOCKING
                    # Previously: compile_function_auto() blocked for 5+ seconds during Numba compilation
                    # Now: queue_compilation() returns immediately, install JITPendingWrapper
                    # This eliminates the WARMUP_0 spike (5090ms → ~0ms blocking)
                    logger.debug(f"Queueing proactive compilation for inner function {inner_name}...")

                    # Queue compilation in background (non-blocking)
                    compilation_queued = core._jit_manager.queue_compilation(
                        inner_func,
                        bypass_call_count=True
                    )

                    if compilation_queued:
                        # Create callback for when compilation completes
                        def make_callback(profiler_self, code_id, fname):
                            def on_compiled(success: bool):
                                with profiler_self._lock:
                                    if success:
                                        profiler_self._jit_compiled_code_ids.add(code_id)
                                        logger.debug(f"Proactive inner JIT compiled for {fname}")
                                    else:
                                        profiler_self._mark_permanent_failure(code_id, fname)
                            return on_compiled

                        # Install JITPendingWrapper - uses original while compilation happens
                        pending_wrapper = JITPendingWrapper(
                            inner_func,
                            inner_name,
                            core._jit_manager,
                            inner_func.__code__,
                            on_compiled_callback=make_callback(self, inner_code_id, inner_name)
                        )

                        # Replace in the correct namespace (prefer caller's globals)
                        replaced = False
                        if inner_name in caller_globals and caller_globals.get(inner_name) is inner_func:
                            caller_globals[inner_name] = pending_wrapper
                            replaced = True
                            logger.debug(f"Queued proactive compilation for {inner_name} (replaced in caller's globals)")
                        elif hasattr(inner_func, '__globals__') and inner_name in inner_func.__globals__:
                            inner_func.__globals__[inner_name] = pending_wrapper
                            replaced = True
                            logger.debug(f"Queued proactive compilation for {inner_name} (replaced in own globals)")

                        if replaced:
                            compiled_count += 1
                    else:
                        # Compilation not queued - may already be compiled
                        existing = core._jit_manager.get_compiled_artifact(inner_func)
                        if existing is not inner_func:
                            # Already compiled - install canary directly
                            def make_callback(profiler_self, code_id, fname):
                                def on_verified(use_compiled: bool):
                                    with profiler_self._lock:
                                        if use_compiled:
                                            profiler_self._jit_compiled_code_ids.add(code_id)
                                            logger.debug(f"Proactive JIT verified for {fname}")
                                        else:
                                            profiler_self._mark_permanent_failure(code_id, fname)
                                return on_verified

                            canary = JITCanaryWrapper(
                                inner_func, existing, inner_name,
                                on_verified_callback=make_callback(self, inner_code_id, inner_name)
                            )

                            # CRITICAL FIX (Jan 2025): Use _install_wrapper_with_fallbacks for nested functions
                            # First try caller_globals (preferred), then use unified fallbacks
                            replaced = False
                            if inner_name in caller_globals and caller_globals.get(inner_name) is inner_func:
                                caller_globals[inner_name] = canary
                                replaced = True
                                logger.debug(f"Proactively installed canary for {inner_name} (already compiled)")
                            else:
                                # Use unified installation with fallbacks for nested functions
                                replaced = _install_wrapper_with_fallbacks(inner_func, canary)
                                if replaced:
                                    logger.debug(f"Proactively installed canary for {inner_name} via fallbacks (already compiled)")

                            if replaced:
                                compiled_count += 1

                except Exception as e:
                    logger.warning(f"Failed to analyze/compile inner function {inner_name}: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error in proactive inner function compilation: {e}")
        finally:
            # Clear re-entrancy guard
            setattr(self, compiling_key, False)

        return compiled_count

    def get_hot_loops(self) -> List[Dict]:
        """
        Get all detected hot loops.

        Returns:
            List of dictionaries with hot loop information
        """
        with self._lock:
            return [
                {
                    'code_object': info.code_object,
                    'start_line': info.start_line,
                    'cpu_time_ms': info.cpu_time_ms,
                    'iteration_count': info.iteration_count,
                    'optimization_applied': info.optimization_applied,
                    'code_name': info.code_object.co_name,
                    'filename': info.code_object.co_filename,
                }
                for info in self._hot_loops.values()
            ]

    def is_hot_loop(self, code_object, line_number: int) -> bool:
        """
        Check if specific loop is marked as hot.

        Args:
            code_object: Code object containing the loop
            line_number: Line number of the loop

        Returns:
            True if loop exceeds threshold
        """
        loop_id = self._compute_loop_id(code_object, line_number)
        return loop_id in self._hot_loops

    def _compute_loop_id(self, code_object, line_number: int) -> int:
        """
        Compute unique identifier for a loop.

        Args:
            code_object: Code object
            line_number: Line number

        Returns:
            Unique loop identifier (hash)
        """
        return hash((id(code_object), line_number))

    def apply_optimization(self, hot_loop: HotLoopInfo) -> OptimizationResult:
        """
        Apply automatic optimization to a hot loop.

        Performance fix (Nov 22, 2025): Guards logging and short-circuits when already optimized.
        Enhancement #1 (Dec 2025): Returns OptimizationResult enum to distinguish deferral from failure.

        Args:
            hot_loop: HotLoopInfo object

        Returns:
            OptimizationResult indicating outcome:
            - SUCCESS: Compilation succeeded
            - DEFERRED: JIT not ready (transient state)
            - SKIPPED: Pre-filtered as unsuitable
            - FAILED: Real compilation error
        """
        # Short-circuit BEFORE any logging (Performance fix)
        if hot_loop.optimization_applied:
            return OptimizationResult.SUCCESS  # Already optimized, skip all work

        # Guard DEBUG logging (Performance fix)
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("apply_optimization called for %s", hot_loop.code_object.co_name)

        try:
            # P0.22 FIX (Dec 2025): Get code_id early for monitoring disable on ALL paths
            # When optimization is SKIPPED for any reason (method calls, not suitable, etc.),
            # we must still disable monitoring to prevent continued overhead.
            # Without this, monitoring callbacks run on every function call even after
            # optimization was already attempted and skipped, causing 4-5x slowdowns!
            code_id = id(hot_loop.code_object)

            logger.debug(f"Attempting optimization for {hot_loop.code_object.co_name}...")

            # CRITICAL FIX: Check JIT readiness FIRST (before extracting function)
            # This prevents false-positive warnings during Level 1→2 transition
            logger.debug("Step 1: Checking JIT readiness...")
            try:
                # Guard against reentrant import deadlock (Python 3.13 macOS)
                # If epochly.core.epochly_core is not fully imported yet, defer
                import sys
                epochly_core_module = sys.modules.get('epochly.core.epochly_core')
                if epochly_core_module is None or not hasattr(epochly_core_module, 'get_epochly_core'):
                    # Module not fully loaded - defer to avoid import deadlock
                    return OptimizationResult.DEFERRED

                from ..core.epochly_core import get_epochly_core
                core = get_epochly_core()

                if not core:
                    logger.debug("Epochly core not available (deferring)")
                    return OptimizationResult.DEFERRED

                # Fix #2: Check JIT readiness flag BEFORE attempting access
                # During Level 1 → Level 2 transition, functions can be detected hot
                # BEFORE _jit_manager is initialized, causing WARNING logs
                # Enhancement #1 (Dec 2025): Return DEFERRED instead of False to prevent false-positive warnings
                if not getattr(core, '_jit_ready', False):
                    logger.debug(f"JIT not ready yet, deferring optimization of {hot_loop.code_object.co_name}")
                    return OptimizationResult.DEFERRED

                if not hasattr(core, '_jit_manager'):
                    logger.debug("Core has no _jit_manager attribute (deferring)")
                    return OptimizationResult.DEFERRED

                if not core._jit_manager:
                    logger.debug("JIT manager is None (deferring)")
                    return OptimizationResult.DEFERRED

                logger.debug(f"JIT manager available: {core._jit_manager}")

            except Exception as e:
                import traceback
                logger.error(f"Error checking JIT readiness: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return OptimizationResult.FAILED

            # Step 2: Extract actual function from code object (after JIT readiness check)
            logger.debug("Step 2: Extracting function from code object...")
            func = self._extract_function_from_code(hot_loop.code_object)

            if not func:
                logger.warning(f"Could not extract function from code object {hot_loop.code_object.co_name}")
                return OptimizationResult.FAILED

            # P0.17 FIX (Dec 2025): Skip Epochly's own dynamically-created code
            if hasattr(func, '__module__') and func.__module__:
                if func.__module__.startswith('epochly'):
                    logger.debug(f"P0.17: Skipping Epochly internal function: {func.__name__}")
                    hot_loop.optimization_applied = True
                    # P0.22 FIX: Disable monitoring to prevent continued overhead
                    self._jit_compiled_code_ids.add(code_id)
                    return OptimizationResult.SKIPPED

            logger.debug(f"Extracted function: {func.__name__}")

            # ===== P0.14 FIX (Dec 2025): CHECK LOOP TRANSFORMER BEFORE JIT COMPILATION =====
            # The loop transformer has comprehensive method call detection (P0.13) that
            # identifies JIT-incompatible patterns like random_state.binomial().
            # The JIT analyzer doesn't catch these, so check loop transformer FIRST.
            if self._loop_transformer:
                loop_analysis = self._loop_transformer.analyze_function(func)

                # P0.19 FIX (Dec 2025): When analysis fails (returns None), be CONSERVATIVE
                # For REPL/notebook code we often can't get source code, so analysis returns None.
                # Previously: None meant "proceed with JIT" - this is WRONG!
                # The cost of NOT JITing a suitable function = use original Python (acceptable)
                # The cost of ATTEMPTING to JIT an unsuitable function = massive overhead:
                #   - Background compilation time
                #   - JITPendingWrapper polling overhead on every call
                #   - Compilation failure messages and retries
                # CONSERVATIVE APPROACH: If we can't analyze it, don't JIT it.
                if loop_analysis is None:
                    logger.debug(
                        f"P0.19: SKIPPING JIT for {func.__name__} - "
                        f"loop analysis returned None (source unavailable for REPL/notebook code)"
                    )
                    hot_loop.optimization_applied = True
                    # P0.22 FIX: Disable monitoring to prevent continued overhead
                    self._jit_compiled_code_ids.add(code_id)
                    return OptimizationResult.SKIPPED

                if loop_analysis.get('has_method_calls_in_loop', False):
                    logger.debug(
                        f"P0.14: SKIPPING JIT for {func.__name__} - "
                        f"loop transformer detected non-JIT-compatible method calls: "
                        f"{loop_analysis.get('method_call_names', [])}"
                    )
                    hot_loop.optimization_applied = True
                    # P0.22 FIX: Disable monitoring to prevent continued overhead
                    self._jit_compiled_code_ids.add(code_id)
                    return OptimizationResult.SKIPPED
                if not loop_analysis.get('should_transform', True):
                    logger.debug(
                        f"P0.14: SKIPPING JIT for {func.__name__} - "
                        f"loop transformer says should_transform=False"
                    )
                    hot_loop.optimization_applied = True
                    # P0.22 FIX: Disable monitoring to prevent continued overhead
                    self._jit_compiled_code_ids.add(code_id)
                    return OptimizationResult.SKIPPED
            # ===== END P0.14 FIX =====

            # ===== CRITICAL FIX (Dec 2025): PRE-ANALYZE BEFORE COMPILATION =====
            # Step 3: Analyze function for JIT suitability FIRST
            # This prevents TypingError crashes when functions call user-defined functions
            # (e.g., compute_all_pairwise calling compute_pairwise_metrics in notebooks)
            logger.debug(f"Pre-analyzing {func.__name__} for JIT suitability...")

            try:
                # Get analyzer from JIT manager
                jit_analyzer = core._jit_manager.jit_analyzer
                if jit_analyzer:
                    # Analyze function characteristics
                    characteristics = jit_analyzer.analyze_function(func)
                    logger.debug(f"Analysis result for {func.__name__}: "
                                f"suitability={characteristics.jit_suitability.value}, "
                                f"issues={characteristics.compatibility_issues}")

                    # Import JITSuitability for comparison
                    from ..plugins.analyzer.jit_analyzer import JITSuitability

                    # Check suitability BEFORE attempting compilation
                    # Enhancement #1 (Dec 2025): Return SKIPPED for unsuitable functions
                    # Compare by enum value to handle both real enums and mocks
                    suitability_value = getattr(characteristics.jit_suitability, 'value', characteristics.jit_suitability)
                    if isinstance(suitability_value, str):
                        # String comparison for mocks or value extraction
                        is_suitable = suitability_value.upper() in ['EXCELLENT', 'GOOD']
                    else:
                        # Direct enum comparison
                        is_suitable = characteristics.jit_suitability in [JITSuitability.EXCELLENT, JITSuitability.GOOD]

                    if not is_suitable:
                        logger.debug(f"SKIPPING compilation of {func.__name__}: "
                                    f"suitability={suitability_value}")
                        if characteristics.compatibility_issues:
                            logger.debug(f"Compatibility issues: {characteristics.compatibility_issues}")

                        # ===== CRITICAL FIX (Dec 2025): PROACTIVE INNER FUNCTION COMPILATION =====
                        # When a function is unsuitable (e.g., returns dict), check if it calls
                        # inner functions that ARE suitable and proactively compile those.
                        # This enables acceleration even when wrapper functions can't be JIT-compiled.
                        inner_compiled = self._proactively_compile_inner_functions(
                            func, jit_analyzer, core
                        )
                        if inner_compiled > 0:
                            logger.debug(f"Proactively compiled {inner_compiled} inner function(s) called by {func.__name__}")
                        # ===== END CRITICAL FIX =====

                        # Mark as processed to avoid re-analysis
                        hot_loop.optimization_applied = True
                        # P0.22 FIX: Disable monitoring to prevent continued overhead
                        self._jit_compiled_code_ids.add(code_id)
                        return OptimizationResult.SKIPPED  # Not suitable - don't compile
                else:
                    logger.warning("JIT analyzer not available - proceeding without pre-analysis")

            except Exception as e:
                logger.warning(f"Pre-analysis failed for {func.__name__}: {e} - proceeding with compilation")
            # ===== END CRITICAL FIX =====

            # ===== LEVEL_4 GPU PATH (Dec 2025): Transparent GPU Acceleration =====
            # Before falling back to CPU JIT, check if LEVEL_4 (GPU) is active and if
            # this function has parallelizable patterns (stencil, map, reduce).
            # This implements transparent GPU acceleration - no user code changes required.
            #
            # TIMING CONSISTENCY (Dec 2025): GPU compilation happens here during warmup,
            # similar to CPU JIT, so Run 1 of timed execution uses the compiled GPU kernel.
            try:
                from ..core.epochly_core import EnhancementLevel

                # Check if LEVEL_4 GPU is active
                if (core.current_level.value >= EnhancementLevel.LEVEL_4_GPU.value and
                    hasattr(core, '_level4_gpu_executor') and
                    core._level4_gpu_executor is not None):

                    gpu_executor = core._level4_gpu_executor

                    # Check if GPU is available and enabled
                    if getattr(gpu_executor, '_enabled', False):
                        logger.debug(f"LEVEL_4 active: Attempting GPU compilation for {func.__name__}...")

                        # Try to compile function for GPU (pattern detection + kernel compilation)
                        # This uses CUDAPatternDetector to find stencil/map/reduce patterns
                        # and CUDAKernelCompiler to compile them to GPU kernels
                        gpu_func = gpu_executor._try_jit_compile(func)

                        if gpu_func is not None:
                            # GPU compilation succeeded! Install GPUCanaryWrapper
                            # CRITICAL FIX (Jan 2025): Use _install_wrapper_with_fallbacks for nested functions
                            logger.info(f"GPU compilation succeeded for {func.__name__}, installing GPUCanaryWrapper")

                            original_code_id = id(hot_loop.code_object)

                            def make_gpu_callback(profiler_self, code_id_val, fname, loop_id_val):
                                def on_gpu_verified(use_gpu: bool):
                                    with profiler_self._lock:
                                        if use_gpu:
                                            # GPU verification succeeded - nothing to do
                                            # code_id already in _jit_compiled_code_ids (added at line 4253)
                                            if logger.isEnabledFor(logging.DEBUG):
                                                logger.debug(f"GPU canary verified! {fname} now using GPU acceleration")
                                        else:
                                            # GPU verification failed - enable CPU JIT fallback
                                            # CRITICAL FIX (Jan 2025): Remove from ALL tracking sets to allow
                                            # the function to be re-detected and re-optimized with CPU JIT.
                                            #
                                            # Must remove from:
                                            # 1. _jit_compiled_code_ids - allows profiler fast-path to NOT skip
                                            # 2. _hot_code_ids - allows re-detection as hot path
                                            # 3. Reset hot_loop.optimization_applied - allows re-optimization
                                            profiler_self._jit_compiled_code_ids.discard(code_id_val)
                                            profiler_self._hot_code_ids.discard(code_id_val)

                                            # Reset hot_loop to allow CPU JIT re-optimization
                                            existing_loop = profiler_self._hot_loops.get(loop_id_val)
                                            if existing_loop:
                                                existing_loop.optimization_applied = False

                                            if logger.isEnabledFor(logging.DEBUG):
                                                logger.debug(f"GPU canary failed for {fname}, reset for CPU JIT fallback")
                                return on_gpu_verified

                            # Compute loop_id for callback (needed for CPU JIT fallback)
                            loop_id_for_callback = self._compute_loop_id(hot_loop.code_object, hot_loop.start_line)

                            gpu_canary = GPUCanaryWrapper(
                                original_func=func,
                                gpu_func=gpu_func,
                                func_name=func.__name__,
                                on_verified_callback=make_gpu_callback(self, original_code_id, func.__name__, loop_id_for_callback),
                                known_speedup_ratio=None  # Let canary verify speedup on first call
                            )

                            # Use unified installation with fallbacks for nested functions
                            if _install_wrapper_with_fallbacks(func, gpu_canary):
                                hot_loop.optimization_applied = True

                                # CRITICAL FIX (Jan 2025): Add code_id IMMEDIATELY to prevent Run 2 variance
                                # Previous behavior: Wait for GPUCanaryWrapper callback to add code_id.
                                # This caused Run 2 to be SLOWER than Run 1 because:
                                # 1. Callback only fires AFTER first call verification
                                # 2. Until callback fires, code_id is NOT in _jit_compiled_code_ids
                                # 3. Profiler keeps profiling this function on Run 2
                                # 4. Profiling overhead causes Run 2 > Run 1 variance
                                #
                                # Fix: Add code_id IMMEDIATELY, same as JITPendingWrapper (line 4387).
                                # If GPU verification fails, the callback will NOT mark permanent failure,
                                # allowing the function to be re-detected for CPU JIT fallback.
                                self._jit_compiled_code_ids.add(original_code_id)

                                # CRITICAL FIX (Jan 2025): Disable tracing IMMEDIATELY after GPU wrapper install
                                # to eliminate Run 2 overhead. The trace callback has overhead even when
                                # returning early (fast-path). By disabling tracing immediately after
                                # optimization, Run 2 becomes as fast as Run 3+.
                                #
                                # AGGRESSIVE MODE: For GPU workloads, disable trace immediately after
                                # the FIRST GPU optimization succeeds. GPU kernels are so expensive that
                                # the primary hot function dominates - secondary functions are negligible.
                                # This trades potential optimization of secondary functions for Run 2 performance.
                                if not self._trace_auto_disabled:
                                    self._trace_auto_disabled = True
                                    sys.settrace(None)
                                    logger.debug(
                                        f"AGGRESSIVE trace disable after GPU wrapper install for {func.__name__}"
                                    )

                                if logger.isEnabledFor(logging.DEBUG):
                                    logger.debug(f"GPUCanaryWrapper installed for {func.__name__} "
                                               f"({hot_loop.cpu_time_ms:.2f}ms CPU time)")
                                return OptimizationResult.SUCCESS
                            else:
                                if logger.isEnabledFor(logging.DEBUG):
                                    logger.debug(f"Cannot install GPU wrapper for {func.__name__}: all installation methods failed")
                        else:
                            # GPU compilation failed (not parallelizable)
                            # CRITICAL FIX (Jan 2025 RCA): Use SYNCHRONOUS JIT, not background JIT!
                            # Background JIT installs JITPendingWrapper that runs pure Python on first call
                            # For 1500x1500 grids, this takes MINUTES. Synchronous JIT blocks once but
                            # all subsequent calls are fast. User-requested fix: "Level 4 GPU failure
                            # should fall back to level 3, not single-core Python"
                            logger.info(
                                f"LEVEL_4: GPU compilation returned None for '{func.__name__}', "
                                f"falling back to SYNCHRONOUS CPU JIT (avoiding pure Python first call)"
                            )

                            # Use synchronous JIT compilation (blocks but avoids pure Python)
                            compiled_func = core._jit_manager.compile_function_auto(
                                func, bypass_call_count=True, skip_benchmark=True
                            )

                            if compiled_func is not None and compiled_func is not func:
                                # Successfully compiled - install JITCanaryWrapper for verification
                                # CRITICAL FIX (Jan 2025): Use _install_wrapper_with_fallbacks for nested functions
                                original_code_id = id(hot_loop.code_object)

                                def on_sync_jit_verified(use_compiled: bool):
                                    if use_compiled:
                                        self._jit_compiled_code_ids.add(original_code_id)
                                        logger.debug(f"Sync JIT verified for {func.__name__}")
                                    else:
                                        self._mark_permanent_failure(original_code_id, func.__name__)

                                from epochly.profiling.jit_canary_wrapper import JITCanaryWrapper
                                canary_wrapper = JITCanaryWrapper(
                                    func, compiled_func, func.__name__,
                                    on_verified_callback=on_sync_jit_verified
                                )

                                # Use unified installation with fallbacks for nested functions
                                if _install_wrapper_with_fallbacks(func, canary_wrapper):
                                    hot_loop.optimization_applied = True

                                    # Add code_id immediately (same pattern as GPU wrapper)
                                    self._jit_compiled_code_ids.add(original_code_id)

                                    # CRITICAL FIX (Jan 2025): Disable tracing IMMEDIATELY
                                    # AGGRESSIVE MODE for LEVEL_4 fallback
                                    if not self._trace_auto_disabled:
                                        self._trace_auto_disabled = True
                                        sys.settrace(None)
                                        logger.debug(
                                            f"AGGRESSIVE trace disable after sync JIT install for {func.__name__}"
                                        )

                                    logger.info(f"LEVEL_4 GPU fallback: Installed synchronous Numba JIT for {func.__name__}")
                                    return OptimizationResult.SUCCESS
                            else:
                                # Synchronous JIT also failed - fall through to background JIT
                                # (shouldn't normally happen but provides robustness)
                                logger.warning(
                                    f"LEVEL_4: Both GPU and synchronous JIT failed for '{func.__name__}', "
                                    f"falling back to background JIT (may be slow on first call)"
                                )
                    else:
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f"GPU executor not enabled, skipping GPU path for {func.__name__}")

            except Exception as e:
                # GPU path failed - fall through to CPU JIT (log with exception type for debugging)
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"GPU path check failed for {func.__name__}: {type(e).__name__}: {e}")
            # ===== END LEVEL_4 GPU PATH =====

            # Step 4: Queue background compilation (NON-BLOCKING)
            # CRITICAL FIX (Dec 2025): Eliminates 13+ second blocking during JIT compilation
            # Instead of blocking iteration 3 waiting for Numba, we:
            # 1. Queue compilation in background (returns immediately)
            # 2. Install JITPendingWrapper that uses original while compilation happens
            # 3. Once compiled, JITPendingWrapper promotes to JITCanaryWrapper for verification
            logger.debug(f"Queueing {func.__name__} for background JIT compilation (non-blocking)...")

            # Queue compilation in background thread (Phase 2.4 non-blocking API)
            # P0.13 FIX (Dec 2025): Auto-profiler has ALREADY proven this function is hot
            # through runtime profiling. Bypass static call_count filter (FILTER 5) which
            # uses static analysis that returns call_count=0 for notebook/REPL functions.
            compilation_queued = core._jit_manager.queue_compilation(func, bypass_call_count=True)

            if not compilation_queued:
                # Could not queue (e.g., already compiled, or JIT disabled)
                # Check if already compiled
                existing_compiled = core._jit_manager.get_compiled_artifact(func)
                if existing_compiled is not func:
                    # Already compiled - install canary wrapper directly
                    # CRITICAL FIX (Jan 2025): Use _install_wrapper_with_fallbacks for nested functions
                    logger.debug(f"{func.__name__} already compiled, installing canary wrapper")
                    original_code_id = id(hot_loop.code_object)

                    def on_verification_complete(use_compiled: bool):
                        if use_compiled:
                            self._jit_compiled_code_ids.add(original_code_id)
                            logger.debug(f"Canary verified! Marked code_id {original_code_id} as JIT-compiled")
                        else:
                            self._mark_permanent_failure(original_code_id, func.__name__)

                    canary_wrapper = JITCanaryWrapper(
                        func, existing_compiled, func.__name__,
                        on_verified_callback=on_verification_complete
                    )

                    # Use unified installation with fallbacks for nested functions
                    if _install_wrapper_with_fallbacks(func, canary_wrapper):
                        hot_loop.optimization_applied = True

                        # Add code_id immediately
                        self._jit_compiled_code_ids.add(original_code_id)

                        # CRITICAL FIX (Jan 2025): Disable tracing IMMEDIATELY
                        # AGGRESSIVE MODE: Disable after first optimization
                        if not self._trace_auto_disabled:
                            self._trace_auto_disabled = True
                            sys.settrace(None)
                            logger.debug(
                                f"AGGRESSIVE trace disable after canary wrapper install for {func.__name__}"
                            )

                        return OptimizationResult.SUCCESS
                else:
                    logger.debug(f"Could not queue {func.__name__} for compilation - JIT unavailable or disabled")
                    hot_loop.optimization_applied = True
                    # P0.22 FIX: Disable monitoring to prevent continued overhead
                    self._jit_compiled_code_ids.add(code_id)
                    return OptimizationResult.SKIPPED

            # Step 5: Install JITPendingWrapper immediately (NON-BLOCKING)
            # This wrapper uses the original function while compilation happens in background
            # CRITICAL FIX (Jan 2025): Use _install_wrapper_with_fallbacks to handle
            # nested functions, closures, and functions not in module globals.
            logger.debug(f"Installing JITPendingWrapper for {func.__name__} (compilation queued)")

            # Create callback to register JIT-compiled code ONLY after verification passes
            original_code_id = id(hot_loop.code_object)

            def on_compilation_complete(compiled_success: bool):
                """
                Callback invoked when background compilation completes.
                Note: Actual verification happens in JITCanaryWrapper after promotion.
                """
                if compiled_success:
                    logger.debug(f"Background compilation complete for {func.__name__}")
                else:
                    # Compilation failed - mark permanent failure
                    self._mark_permanent_failure(original_code_id, func.__name__)

            pending_wrapper = JITPendingWrapper(
                original_func=func,
                func_name=func.__name__,
                jit_manager=core._jit_manager,
                code_object=hot_loop.code_object,
                on_compiled_callback=on_compilation_complete
            )

            # Use unified installation with fallbacks for nested functions
            if _install_wrapper_with_fallbacks(func, pending_wrapper):
                hot_loop.optimization_applied = True

                # P0.8 FIX: Disable monitoring for this function IMMEDIATELY
                # Without this, monitoring continues on every call even though
                # JITPendingWrapper is already installed, causing massive overhead
                self._jit_compiled_code_ids.add(original_code_id)

                # CRITICAL FIX (Jan 2025): Disable tracing IMMEDIATELY after wrapper install
                # to eliminate Run 2 overhead from trace callback overhead.
                # AGGRESSIVE MODE: Disable after first optimization
                if not self._trace_auto_disabled:
                    self._trace_auto_disabled = True
                    sys.settrace(None)
                    logger.debug(
                        f"AGGRESSIVE trace disable after JITPendingWrapper install for {func.__name__}"
                    )

                logger.debug(f"Non-blocking JIT queued for {func.__name__} "
                           f"({hot_loop.cpu_time_ms:.2f}ms CPU time) - iteration continues immediately")
                return OptimizationResult.DEFERRED  # Compilation in progress
            else:
                logger.warning(f"Cannot install wrapper for {func.__name__}: all installation methods failed")
                return OptimizationResult.FAILED

        except Exception as e:
            import traceback
            logger.error(f"Failed to apply optimization: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return OptimizationResult.FAILED

    def _extract_function_from_code(self, code_object) -> Optional[Callable]:
        """
        Extract actual function object from code object with caching.

        Performance fix (Nov 22, 2025): Cache results to avoid expensive
        gc.get_referrers() on every call (100x speedup for cached lookups).

        Args:
            code_object: Code object

        Returns:
            Function object or None if not found
        """
        code_id = id(code_object)

        # Fast path: check cache (simple dict lookup)
        if code_id in self._code_to_function_cache:
            return self._code_to_function_cache[code_id]

        # Slow path: use gc.get_referrers (expensive!)
        try:
            referrers = gc.get_referrers(code_object)

            # Look for function objects
            for referrer in referrers:
                if isinstance(referrer, type(lambda: None)):  # Function type
                    if referrer.__code__ is code_object:
                        # Cache for future lookups
                        with self._cache_lock:
                            self._code_to_function_cache[code_id] = referrer
                        return referrer

            # Not found - cache None to avoid repeated expensive searches
            with self._cache_lock:
                self._code_to_function_cache[code_id] = None

            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug("Could not find function for code object %s", code_object.co_name)
            return None

        except Exception as e:
            if self.logger.isEnabledFor(logging.ERROR):
                self.logger.error("Error extracting function from code: %s", e)
            return None

    def _trigger_optimization(self, hot_loop: HotLoopInfo) -> 'OptimizationResult':
        """
        Trigger optimization for a hot loop.

        CRITICAL: Sets optimization_in_progress flag to prevent recursive execution.

        If adaptive orchestrator is connected, query ML predictor for decision.
        Otherwise use simple rule-based optimization.

        Args:
            hot_loop: Information about detected hot loop

        Returns:
            OptimizationResult indicating the outcome (SUCCESS, DEFERRED, SKIPPED, FAILED)
        """
        try:
            # CRITICAL FIX: Set flag to prevent recursive optimization
            if self._is_optimization_in_progress():
                logger.debug(f"Optimization already in progress, skipping {hot_loop.code_object.co_name}")
                return OptimizationResult.DEFERRED

            self._set_optimization_in_progress(True)
            try:
                # ML-guided optimization if orchestrator available
                if self._use_ml_guidance and self._adaptive_orchestrator:
                    try:
                        # Notify orchestrator of hot path detection
                        # Signature: (function_name, cpu_time_ms, code_object, hot_loop_info)
                        prediction = self._adaptive_orchestrator.on_hot_path_detected(
                            hot_loop.code_object.co_name,  # function_name
                            hot_loop.cpu_time_ms,          # cpu_time_ms
                            hot_loop.code_object,          # code_object
                            hot_loop                       # hot_loop_info (entire object)
                        )

                        if prediction:
                            logger.debug(
                                f"LSTM recommends optimizing {hot_loop.code_object.co_name} "
                                f"(predicted speedup: {prediction.get('predicted_speedup', 'N/A')}x, "
                                f"confidence: {prediction.get('confidence', 'N/A')})"
                            )

                    except AttributeError:
                        # on_hot_path_detected not implemented yet - fall back to rule-based
                        logger.debug("Orchestrator.on_hot_path_detected() not available, using rule-based optimization")
                    except Exception as e:
                        # ML prediction failed - fall back to rule-based
                        logger.warning(f"ML prediction failed: {e}, falling back to rule-based optimization")

                # Proceed with optimization (either ML-recommended or rule-based)
                # Enhancement #1 (Dec 2025): Handle OptimizationResult enum to prevent false-positive warnings
                result = self.apply_optimization(hot_loop)

                func_name = hot_loop.code_object.co_name

                if result == OptimizationResult.SUCCESS:
                    logger.info(f"Successfully optimized {func_name}")

                elif result == OptimizationResult.DEFERRED:
                    # Expected during initialization - not a warning (prevents false positives during Level 1→2 transition)
                    logger.debug(f"Deferred optimization of {func_name} (JIT initializing)")

                elif result == OptimizationResult.SKIPPED:
                    # Pre-filtered - informational only
                    logger.debug(f"Skipped optimization of {func_name} (unsuitable for JIT)")

                else:  # FAILED
                    # Real issue - warn
                    logger.warning(f"Failed to optimize {func_name}")

                # =====================================================================
                # LEVEL 3+ LOOP TRANSFORMATION (Dec 2025 - Gap Fix)
                # =====================================================================
                # At Level 3+, we have two orthogonal optimizations:
                #   1. JIT compilation (faster per-iteration) - handled above
                #   2. Loop parallelization (multiple cores) - handled HERE
                #
                # The gap being fixed:
                # - Eager transformation was DISABLED at Level 3+ (overhead regression)
                # - But timing-validated hot detection (>10ms) proves the workload is
                #   substantial enough to benefit from parallelization
                # - So we trigger loop transformation HERE, after timing validation
                #
                # This gives Level 3 the best of both worlds:
                # - JIT for per-iteration speedup (if suitable)
                # - Loop parallelization for multi-core speedup (if suitable)
                #
                # Note: JIT and loop transformation are orthogonal - both can succeed
                # independently on the same function for multiplicative speedup.
                # =====================================================================
                if self._use_anticipatory_transformation and self._loop_transformer:
                    try:
                        # Guard against reentrant import deadlock (Python 3.13 macOS)
                        # If epochly.core.epochly_core is not fully imported yet, skip
                        import sys
                        epochly_core_module = sys.modules.get('epochly.core.epochly_core')
                        if epochly_core_module is None or not hasattr(epochly_core_module, 'get_epochly_core'):
                            # Module not fully loaded - skip to avoid import deadlock
                            return

                        from ..core.epochly_core import get_epochly_core, EnhancementLevel
                        core = get_epochly_core()

                        if core and hasattr(core, 'current_level'):
                            current_level_value = core.current_level.value if hasattr(core.current_level, 'value') else 0

                            # Only apply at Level 3+ (where eager was disabled)
                            # Level 2 already has eager transformation in _monitoring_py_start
                            if current_level_value >= EnhancementLevel.LEVEL_3_FULL.value:
                                # Extract function from code object
                                func = self._extract_function_from_code(hot_loop.code_object)

                                # P0.17 FIX (Dec 2025): Skip Epochly's own dynamically-created code
                                if func and hasattr(func, '__module__') and func.__module__:
                                    if func.__module__.startswith('epochly'):
                                        logger.debug(f"P0.17: Skipping Epochly internal: {func.__name__}")
                                        return  # Skip this function

                                if func and not hasattr(func, '_epochly_transformed'):
                                    func_id = id(func)

                                    # Race protection: Check if another thread is transforming
                                    # (coordinates with eager transform in _monitoring_py_start)
                                    should_transform = False
                                    with self._lock:
                                        if func_id not in self._transforming_functions:
                                            self._transforming_functions.add(func_id)
                                            should_transform = True

                                    if not should_transform:
                                        logger.debug(
                                            f"Skipping {func_name}: another thread is transforming"
                                        )
                                    else:
                                        try:
                                            # Analyze for parallelizable loops
                                            analysis = self._loop_transformer.analyze_function(func)

                                            if analysis and analysis.get('should_transform', False):
                                                # Transform the function
                                                logger.debug(
                                                    f"Level 3+ timing-validated loop transformation for {func_name} "
                                                    f"(CPU time: {hot_loop.cpu_time_ms:.2f}ms)"
                                                )

                                                transformed = self._loop_transformer.transform_function(func)

                                                if transformed and transformed != func:
                                                    # Thread-safe replacement in globals
                                                    with self._lock:
                                                        if hasattr(func, '__globals__') and func.__name__ in func.__globals__:
                                                            current = func.__globals__[func.__name__]
                                                            # CRITICAL: Don't overwrite JIT or GPU wrappers!
                                                            # JITPendingWrapper/JITCanaryWrapper handle their own lifecycle.
                                                            # GPUCanaryWrapper/_GPUDisabledAwareWrapper handle GPU lifecycle.
                                                            # Overwriting them would break JIT/GPU optimization.
                                                            # Future-proof: check marker attributes for wrapper types
                                                            is_jit_wrapper = (
                                                                isinstance(current, (JITPendingWrapper, JITCanaryWrapper)) or
                                                                getattr(current, '_is_epochly_jit_wrapper', False)
                                                            )
                                                            is_gpu_wrapper = (
                                                                isinstance(current, (GPUCanaryWrapper, _GPUDisabledAwareWrapper)) or
                                                                getattr(current, '_is_epochly_gpu_wrapper', False)
                                                            )
                                                            if not hasattr(current, '_epochly_transformed') and not is_jit_wrapper and not is_gpu_wrapper:
                                                                func.__globals__[func.__name__] = transformed
                                                                logger.info(
                                                                    f"Level 3+ loop transformation applied to {func_name} "
                                                                    f"(timing-validated: {hot_loop.cpu_time_ms:.2f}ms)"
                                                                )
                                                            elif is_jit_wrapper:
                                                                if logger.isEnabledFor(logging.DEBUG):
                                                                    logger.debug(
                                                                        f"Skipping loop transform replacement for {func_name}: "
                                                                        f"JIT wrapper already installed"
                                                                    )
                                                            elif is_gpu_wrapper:
                                                                if logger.isEnabledFor(logging.DEBUG):
                                                                    logger.debug(
                                                                        f"Skipping loop transform replacement for {func_name}: "
                                                                        f"GPU wrapper already installed"
                                                                    )
                                                else:
                                                    logger.debug(
                                                        f"Loop transformation not applicable for {func_name}"
                                                    )
                                            else:
                                                logger.debug(
                                                    f"Function {func_name} not suitable for loop transformation "
                                                    f"(analysis: {analysis})"
                                                )
                                        finally:
                                            # Release transformation lock
                                            with self._lock:
                                                self._transforming_functions.discard(func_id)

                    except Exception as e:
                        # Log warning for unexpected failures with exception context for debugging
                        logger.warning(f"Level 3+ loop transformation failed for {func_name}: {e}", exc_info=True)

                return result

            finally:
                # CRITICAL: Always clear flag when done
                self._set_optimization_in_progress(False)

        except Exception as e:
            logger.error(f"Exception in _trigger_optimization: {e}", exc_info=True)
            # Ensure flag is cleared even on exception
            self._set_optimization_in_progress(False)
            return OptimizationResult.FAILED

    def set_orchestrator(self, orchestrator, jit_analyzer=None):
        """
        Connect to adaptive orchestrator for ML-guided optimization.

        When connected, the auto-profiler will:
        1. Notify orchestrator of hot paths
        2. Query LSTM predictor for optimization decisions
        3. Use ML predictions instead of simple thresholds
        4. Feed back results for online learning

        Args:
            orchestrator: AdaptiveOrchestrator instance
            jit_analyzer: Optional JITAnalyzer for coordination
        """
        with self._lock:
            self._adaptive_orchestrator = orchestrator
            self._jit_analyzer = jit_analyzer
            self._use_ml_guidance = True
            logger.debug("AutoProfiler connected to adaptive orchestrator (ML-guided optimization enabled)")

    def disconnect_orchestrator(self):
        """
        Disconnect from ML orchestrator and revert to rule-based optimization.

        Used for testing and debugging to compare ML-guided vs rule-based performance.
        """
        with self._lock:
            self._adaptive_orchestrator = None
            self._jit_analyzer = None
            self._use_ml_guidance = False
        logger.debug("AutoProfiler disconnected from orchestrator (reverted to rule-based optimization)")

    def report_optimization_result(self, optimization_result):
        """
        Report optimization results back to ML orchestrator for learning.

        Args:
            optimization_result: Dictionary containing optimization metrics:
                - code_object: Code object that was optimized
                - success: Whether optimization succeeded
                - speedup: Measured speedup (if available)
                - cpu_time_before_ms: CPU time before optimization
                - cpu_time_after_ms: CPU time after optimization
        """
        if not self._use_ml_guidance or not self._adaptive_orchestrator:
            logger.debug("No orchestrator connected - optimization result not reported")
            return

        try:
            self._adaptive_orchestrator.on_optimization_result(optimization_result)
            logger.debug(f"Reported optimization result to orchestrator: "
                       f"success={optimization_result.get('success', False)}, "
                       f"speedup={optimization_result.get('speedup', 'N/A')}")
        except Exception as e:
            logger.error(f"Failed to report optimization result: {e}", exc_info=True)

    def set_loop_transformer(self, loop_transformer):
        """
        Connect loop transformer for anticipatory transformation.

        When connected, the auto-profiler will mark hot code objects,
        and the loop transformer will apply SIMD/memory optimizations
        on next execution using __code__ replacement.

        Args:
            loop_transformer: LoopTransformer instance
        """
        with self._lock:
            self._loop_transformer = loop_transformer
            self._use_anticipatory_transformation = True

            # CRITICAL FIX (Dec 2025): Wire permanent failure callback
            # When loop extraction fails (source unavailable), disable monitoring
            # to prevent 200+ retry attempts causing 5.7x slowdown
            if hasattr(loop_transformer, '_on_permanent_failure'):
                loop_transformer._on_permanent_failure = self._mark_permanent_failure

            logger.debug("AutoProfiler connected to loop transformer (anticipatory transformation enabled)")

    def set_jit_manager(self, jit_manager):
        """
        P0.12 FIX (Dec 2025): Connect JIT manager for failed compilation checks.

        When background compilation fails, jit_manager._failed_code_ids is updated.
        The monitoring callbacks check this to return DISABLE for failed functions,
        preventing continued timing overhead for functions that will never be optimized.

        Args:
            jit_manager: JITManager instance
        """
        with self._lock:
            self._jit_manager_ref = jit_manager
            logger.debug("AutoProfiler connected to JIT manager (failed code checks enabled)")


# Global auto-profiler instance
_auto_profiler: Optional[AutoProfiler] = None


def get_auto_profiler() -> Optional[AutoProfiler]:
    """Get global auto-profiler instance."""
    return _auto_profiler


def set_auto_profiler(profiler: AutoProfiler):
    """Set global auto-profiler instance."""
    global _auto_profiler
    _auto_profiler = profiler


def initialize_auto_profiler(cpu_threshold_ms: float = 10.0) -> AutoProfiler:
    """
    Initialize and return a new AutoProfiler instance.

    This is the factory function called by EpochlyCore during initialization.

    Args:
        cpu_threshold_ms: CPU time threshold for hot loop detection (default: 10ms)

    Returns:
        AutoProfiler instance (not yet enabled - caller must call .enable())
    """
    profiler = AutoProfiler(cpu_threshold_ms=cpu_threshold_ms)

    # Set as global instance
    set_auto_profiler(profiler)

    logger.debug(f"AutoProfiler created with {cpu_threshold_ms}ms threshold")
    return profiler
