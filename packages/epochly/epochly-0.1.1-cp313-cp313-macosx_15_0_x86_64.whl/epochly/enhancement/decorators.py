"""
Epochly Enhancement Decorators (Task 3 Integration)

Decorators that use precomputed compatibility metadata for zero-overhead
Level 3 routing decisions.

Performance:
- Old: 1ms compatibility check per call (inspect.getsource + regex)
- New: <1μs flag read (precomputed at decoration time)
- Improvement: 1000× faster

Usage:
    from epochly.enhancement.decorators import full_optimize

    @full_optimize
    def my_function(data):
        # This function is analyzed once at decoration time
        # Runtime checks are <1μs
        return process(data)
"""

import functools
import concurrent.futures
from typing import Callable, Any

from .compatibility_analyzer import CompatibilityAnalyzer, CompatibilityFlags
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Singleton analyzer instance
_analyzer = CompatibilityAnalyzer()


def full_optimize(fn: Callable) -> Callable:
    """
    Decorator for full optimization (Level 3).

    Analyzes function compatibility at decoration time and caches results
    on the function object. Runtime execution reads cached flags (<1μs) instead
    of performing expensive source inspection (1ms).

    Args:
        fn: Function to optimize

    Returns:
        Wrapped function with optimization applied

    Example:
        @full_optimize
        def compute(data):
            result = 0
            for item in data:
                result += item ** 2
            return result

        # Compatibility analyzed once at decoration time
        # Each call reads __epochly_flags__ (<1μs overhead)
    """
    # Analyze once at decoration time
    flags = _analyzer.analyze_function(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        """
        Wrapper that uses precomputed compatibility flags.

        Fast path: <1μs flag read + routing decision.
        """
        # Fast path: read precomputed flags (attribute access)
        # No inspect.getsource(), no regex, no AST parsing
        if not flags.level3_safe:
            # Execute in current interpreter (not safe for Level 3)
            return fn(*args, **kwargs)

        # Level 3 execution (if available)
        # Separate import errors from execution errors
        try:
            from ..core.epochly_core import get_epochly_core, EnhancementLevel
        except ImportError as e:
            logger.debug(f"Level 3 core unavailable: {e}")
            return fn(*args, **kwargs)

        try:
            core = get_epochly_core()

            if core.current_level.value >= EnhancementLevel.LEVEL_3_FULL.value:
                # CRITICAL FIX: Trigger lazy Level 3 initialization if deferred during bootstrap
                # Without this call, functions using @full_optimize would silently skip Level 3
                # when initialization was deferred to prevent fork bombs
                if hasattr(core, '_ensure_level3_initialized'):
                    if not core._ensure_level3_initialized():
                        # Lazy init failed or not needed - fall through to local execution
                        logger.debug("Level 3 lazy initialization not ready, using local execution")
                        return fn(*args, **kwargs)

                # Level 3 available - try to use it
                # Note: The executor is _sub_interpreter_executor, not _level3_executor
                if hasattr(core, '_sub_interpreter_executor') and core._sub_interpreter_executor is not None:
                    try:
                        # Submit to sub-interpreter pool (FIXED: use submit_task, not submit)
                        future = core._sub_interpreter_executor.submit_task(fn, args, kwargs)

                        # Await result with timeout to prevent indefinite waits
                        exec_result = future.result(timeout=60.0)

                        # Check for execution errors
                        if not exec_result.success:
                            # Re-raise the error from Level 3 execution (propagate, don't suppress)
                            error_msg = exec_result.error or "Unknown Level 3 execution error"
                            raise RuntimeError(f"Level 3 execution failed: {error_msg}")

                        # Return unwrapped payload (not ExecutionResult metadata)
                        return exec_result.result

                    except RuntimeError as e:
                        # RuntimeError from ExecutionResult failures - check if it's from us
                        if "Level 3 execution failed" in str(e):
                            # This is from exec_result.success=False - propagate it
                            raise
                        # Other RuntimeErrors (e.g., from Future.result()) - fallback
                        func_name = getattr(fn, '__name__', repr(fn))
                        logger.debug(f"Future raised RuntimeError for {func_name}: {e}")
                        # Fall through to local execution

                    except (TimeoutError, concurrent.futures.TimeoutError) as e:
                        # Level 3 executor wedged - fallback
                        func_name = getattr(fn, '__name__', repr(fn))
                        logger.warning(f"Level 3 timeout for {func_name}: {e}")
                        # Fall through to local execution

                    except concurrent.futures.CancelledError as e:
                        # Future was cancelled - fallback
                        func_name = getattr(fn, '__name__', repr(fn))
                        logger.debug(f"Level 3 cancelled for {func_name}: {e}")
                        # Fall through to local execution

        except AttributeError as e:
            # Missing Level 3 infrastructure (e.g., core._sub_interpreter_executor not set)
            func_name = getattr(fn, '__name__', repr(fn))
            logger.debug(f"Level 3 infrastructure unavailable for {func_name}: {e}")

        except RuntimeError as e:
            # Re-raise only execution errors (from exec_result.success=False)
            if "Level 3 execution failed" in str(e):
                raise
            # Infrastructure RuntimeErrors - fallback
            func_name = getattr(fn, '__name__', repr(fn))
            logger.debug(f"Level 3 runtime error for {func_name}: {e}")

        except Exception as e:
            # Catch-all for unexpected infrastructure errors - fallback
            func_name = getattr(fn, '__name__', repr(fn))
            logger.debug(f"Level 3 infrastructure error for {func_name}: {e}")

        # Fallback: execute locally
        return fn(*args, **kwargs)

    # Attach flags to wrapper for introspection
    wrapper.__epochly_flags__ = flags

    logger.debug(
        f"Decorated {fn.__name__}: "
        f"Level3={'✓' if flags.level3_safe else '✗'}, "
        f"complexity={flags.complexity_score}, "
        f"overhead~{flags.estimated_overhead_ns}ns"
    )

    return wrapper


def jit_compile(fn: Callable) -> Callable:
    """
    Decorator for JIT compilation (Level 2).

    Marks function for JIT compilation without Level 3 sub-interpreter routing.

    Args:
        fn: Function to JIT compile

    Returns:
        Wrapped function with JIT applied
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        """Wrapper for JIT compilation."""
        try:
            from ..core.epochly_core import get_epochly_core, EnhancementLevel

            core = get_epochly_core()

            if core.current_level.value >= EnhancementLevel.LEVEL_2_JIT.value:
                # Level 2 available - try JIT
                if hasattr(core, '_jit_manager') and core._jit_manager is not None:
                    # Try to compile and execute
                    compiled_fn = core._jit_manager.compile_function(fn)
                    if compiled_fn is not None:
                        return compiled_fn(*args, **kwargs)

        except Exception as e:
            logger.debug(f"JIT compilation failed for {fn.__name__}: {e}")

        # Fallback: execute original
        return fn(*args, **kwargs)

    return wrapper


def monitor_only(fn: Callable) -> Callable:
    """
    Decorator for monitoring only (Level 0).

    Tracks execution time but applies no optimization.

    Args:
        fn: Function to monitor

    Returns:
        Wrapped function with monitoring
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        """Wrapper for monitoring."""
        import time

        start = time.perf_counter_ns()
        result = fn(*args, **kwargs)
        duration_ns = time.perf_counter_ns() - start

        # Emit metric (if monitoring available)
        try:
            from ..core.epochly_core import get_epochly_core

            core = get_epochly_core()
            if hasattr(core, 'performance_monitor') and core.performance_monitor:
                core.performance_monitor.record_metric(
                    name=f"function.{fn.__name__}.duration_ns",
                    value=duration_ns,
                    context={"function": fn.__name__}
                )
        except Exception:
            pass

        return result

    return wrapper
