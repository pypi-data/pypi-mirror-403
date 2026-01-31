"""
Epochly Pyston-Lite JIT Backend

Pyston-Lite is a process-wide runtime accelerator for CPython 3.8-3.10.
It is NOT a per-function compiler like Numba - it optimizes ALL Python code
once enabled via pyston_lite.enable().

SUPPORTED PLATFORMS:
- Python 3.7-3.10 ONLY (NOT 3.11+)
- Linux and macOS (check pip availability for specific platforms)
- x86_64 architecture primarily (ARM support may be limited)

PYTHON 3.11+ USERS:
On Python 3.11+, Pyston-Lite is NOT available. However, this is acceptable
because Python 3.11's "Specializing Adaptive Interpreter" (PEP 659) already
provides comparable ~25% speedup over Python 3.10. Users on 3.11+ automatically
benefit from CPython's native optimizations without needing external JIT.

IMPORTANT: pyston_lite 2.3.5 only exposes one function: enable()
There is no per-function compilation API. This module correctly handles
Pyston as a global runtime enabler, not a function compiler.

Author: Epochly Development Team
"""

import logging
import sys
import threading
import importlib.util
from typing import Callable, Optional, List, Any, Dict

from .base import JITCompiler, JITBackend, JITCompilationResult, CompilationStatus

logger = logging.getLogger(__name__)

# Module-level state for global Pyston enablement
_PYSTON_ENABLE_LOCK = threading.Lock()
_PYSTON_ENABLED = False
_pyston_lite = None  # Will hold the module reference when actually imported

# Check Pyston-Lite availability using find_spec (NO IMPORT - avoids side effects)
# IMPORTANT: We use find_spec instead of importing because importing pyston_lite
# can cause conflicts with other JIT compilers like Numba. The actual import
# is deferred until _enable_pyston_once() is called.
#
# NOTE: Do NOT import pyston_lite_autoload - it enables JIT as a side-effect
# at import time, which is undesirable for a library.
if sys.version_info[:2] <= (3, 10):
    PYSTON_AVAILABLE = importlib.util.find_spec("pyston_lite") is not None
    if PYSTON_AVAILABLE:
        logger.debug("Pyston-Lite detected (lazy import pending)")
    else:
        logger.debug("Pyston-Lite not installed")
else:
    PYSTON_AVAILABLE = False
    logger.debug("Pyston-Lite not supported on Python 3.11+")


def _enable_pyston_once() -> bool:
    """
    Enable Pyston-Lite JIT exactly once per process.

    Thread-safe and idempotent. Returns True if Pyston is now enabled,
    False if unavailable or failed.

    IMPORTANT: This is where pyston_lite is actually imported. We use lazy
    importing to avoid conflicts with Numba when pyston_lite is installed
    but not explicitly enabled.
    """
    global _PYSTON_ENABLED, _pyston_lite

    # Fast path: already enabled
    if _PYSTON_ENABLED:
        return True

    # Check availability (determined at module load via find_spec)
    if not PYSTON_AVAILABLE:
        return False

    # Check Python version (Pyston-Lite only supports 3.8-3.10)
    if sys.version_info[:2] > (3, 10):
        logger.debug(f"Pyston-Lite not supported on Python {sys.version_info.major}.{sys.version_info.minor} (max 3.10)")
        return False

    # CRITICAL FIX (Jan 2026): Check for Numba to avoid interpreter-level conflicts
    # Both pyston_lite and Numba modify CPython internals. When pyston_lite.enable()
    # runs, it replaces parts of the interpreter. Numba's C extensions (_typeconv, etc.)
    # assume stock CPython internals. Mixing them causes memory corruption that manifests
    # as segfaults in Numba's type conversion code after many compilations.
    # This check is cheap (dict lookup) and prevents silent corruption.
    numba_loaded = 'numba' in sys.modules or 'numba.core' in sys.modules
    if numba_loaded:
        logger.info(
            "Numba detected in process - disabling pyston_lite to avoid interpreter conflicts. "
            "Numba provides targeted numerical optimization; pyston_lite is not needed."
        )
        return False

    with _PYSTON_ENABLE_LOCK:
        # Double-check inside lock
        if _PYSTON_ENABLED:
            return True

        try:
            # Lazy import: only import pyston_lite when actually enabling
            # This avoids conflicts with Numba when both are installed
            if _pyston_lite is None:
                import pyston_lite as _pyston_lite_module
                _pyston_lite = _pyston_lite_module
                logger.debug("Pyston-Lite module imported")

            # The ONLY stable public API in pyston-lite 2.3.5
            _pyston_lite.enable()
            _PYSTON_ENABLED = True
            logger.info("Pyston-Lite JIT enabled (process-wide runtime acceleration)")
            return True
        except ImportError as e:
            logger.warning(f"Failed to import Pyston-Lite: {e}")
            return False
        except Exception as e:
            logger.warning(f"Failed to enable Pyston-Lite JIT: {e}")
            return False


class PystonJIT(JITCompiler):
    """
    Pyston-Lite runtime accelerator integration.

    IMPORTANT: Pyston-Lite is NOT a per-function compiler like Numba.
    It's a process-wide runtime accelerator. "Compiling" a function with
    Pyston simply means:
    1. Ensure pyston_lite.enable() has been called once
    2. Return the ORIGINAL function (no wrapper)

    The Pyston runtime will automatically optimize hot code paths.
    Creating wrappers would be harmful (adds overhead, breaks introspection).

    Supports Python 3.8-3.10 only (pyston-lite 2.3.5 limitation).
    """

    def __init__(self, enable_caching: bool = True, **pyston_options):
        """
        Initialize Pyston JIT backend.

        Args:
            enable_caching: Whether to cache "compilation" results (for API consistency)
            **pyston_options: Stored for reporting but NOT applied (pyston-lite 2.3.5
                            has no Python API for tuning options)
        """
        super().__init__(JITBackend.PYSTON, enable_caching)

        # Store options for reporting only - pyston-lite 2.3.5 does not expose
        # any configuration API (no set_optimization_level, no env var support)
        self.pyston_options = {
            'optimization_level': 2,
            'shared_cache': True,
            'specialize': True,
            'inline': True,
            'debug': False,
            **pyston_options
        }

        # Performance tracking
        self.registered_functions = 0

        if not PYSTON_AVAILABLE:
            logger.warning("Pyston-Lite not available - PystonJIT backend will be disabled")
        elif sys.version_info[:2] > (3, 10):
            logger.warning(f"Pyston-Lite only supports Python 3.8-3.10 (current: {sys.version_info.major}.{sys.version_info.minor})")
        else:
            # Enable Pyston on initialization (it's process-wide anyway)
            enabled = _enable_pyston_once()
            if enabled:
                logger.info(
                    "Pyston-Lite JIT enabled. Note: This is a process-wide runtime accelerator, "
                    "not a per-function compiler. All Python code benefits automatically."
                )

    def is_available(self) -> bool:
        """Check if Pyston-Lite is available and applicable for current Python version."""
        return PYSTON_AVAILABLE and sys.version_info[:2] <= (3, 10)

    def _compile_function_impl(self, func: Callable, source_hash: str) -> JITCompilationResult:
        """
        "Compile" function with Pyston-Lite.

        In reality, this just ensures Pyston is enabled and returns the ORIGINAL
        function. Pyston-Lite is a runtime accelerator - there's no per-function
        compilation. Creating wrappers would add overhead without benefit.

        Args:
            func: Function to "compile"
            source_hash: Hash of function source code

        Returns:
            JITCompilationResult with the original function
        """
        func_name = getattr(func, '__name__', str(func))
        warnings = []

        # Check availability
        if not PYSTON_AVAILABLE:
            return JITCompilationResult(
                backend=self.backend,
                status=CompilationStatus.UNAVAILABLE,
                compilation_time_ms=0.0,
                function_name=func_name,
                source_hash=source_hash,
                error_message="Pyston-Lite not installed"
            )

        # Check Python version
        if sys.version_info[:2] > (3, 10):
            return JITCompilationResult(
                backend=self.backend,
                status=CompilationStatus.UNAVAILABLE,
                compilation_time_ms=0.0,
                function_name=func_name,
                source_hash=source_hash,
                error_message=f"Pyston-Lite only supports Python 3.8-3.10 (current: {sys.version_info.major}.{sys.version_info.minor})"
            )

        try:
            # Ensure Pyston is enabled (idempotent)
            if not _enable_pyston_once():
                return JITCompilationResult(
                    backend=self.backend,
                    status=CompilationStatus.FAILED,
                    compilation_time_ms=0.0,
                    function_name=func_name,
                    source_hash=source_hash,
                    error_message="Pyston-Lite available but failed to enable()"
                )

            # Check function compatibility (for warnings only)
            compatibility_issues = self._check_compatibility(func)
            if compatibility_issues:
                warnings.extend(compatibility_issues)

            # Return the ORIGINAL function - no wrapper!
            # Pyston-Lite is interpreter-level; wrapping would add overhead
            # and interfere with optimization heuristics.
            self.registered_functions += 1

            return JITCompilationResult(
                backend=self.backend,
                status=CompilationStatus.COMPILED,
                compilation_time_ms=0.0,  # No actual compilation - just runtime enable
                function_name=func_name,
                source_hash=source_hash,
                compiled_function=func,  # ORIGINAL function, not a wrapper
                compilation_warnings=warnings + [
                    "Pyston-Lite is process-wide; returning original function (no wrapper)"
                ]
            )

        except Exception as e:
            return JITCompilationResult(
                backend=self.backend,
                status=CompilationStatus.FAILED,
                compilation_time_ms=0.0,
                function_name=func_name,
                source_hash=source_hash,
                error_message=str(e),
                error_type=type(e).__name__
            )

    def _check_compatibility(self, func: Callable) -> List[str]:
        """
        Check function compatibility with Pyston-Lite.

        These are informational warnings only - Pyston-Lite will still
        attempt to optimize all code.

        Args:
            func: Function to check

        Returns:
            List of compatibility warnings
        """
        warnings = []

        try:
            import inspect
            source = inspect.getsource(func)

            # Patterns that may limit Pyston optimization
            potential_issues = [
                ('ctypes', "ctypes usage may limit optimization"),
                ('__import__', "Dynamic imports may not optimize well"),
                ('exec(', "exec() may limit optimization"),
                ('eval(', "eval() may limit optimization"),
            ]

            for pattern, warning in potential_issues:
                if pattern in source:
                    warnings.append(warning)

            # Very dynamic code
            if source.count('getattr') > 5 or source.count('setattr') > 5:
                warnings.append("Highly dynamic code may limit optimization")

        except (OSError, TypeError):
            # Can't get source (e.g., notebook/REPL) - that's fine
            pass

        return warnings

    def get_pyston_statistics(self) -> dict:
        """
        Get Pyston-specific statistics.

        Returns:
            Dictionary with Pyston status and metrics
        """
        base_stats = self.get_statistics()

        pyston_stats = {
            'registered_functions': self.registered_functions,
            'pyston_enabled': _PYSTON_ENABLED,
            'pyston_available': PYSTON_AVAILABLE,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'python_supported': sys.version_info[:2] <= (3, 10),
            'pyston_options': self.pyston_options,
            'note': "Pyston-Lite is process-wide; per-function options are not supported"
        }

        base_stats.update(pyston_stats)
        return base_stats

    def set_optimization_level(self, level: int) -> None:
        """
        Set Pyston optimization level (NO-OP in pyston-lite 2.3.5).

        Args:
            level: Optimization level (0-3) - stored but NOT applied
        """
        self.pyston_options['optimization_level'] = max(0, min(3, level))
        logger.info(
            f"Requested Pyston optimization level={level}, but pyston-lite 2.3.5 "
            "does not expose a supported optimization-level API; this is a no-op."
        )

    def enable_shared_cache(self, enable: bool = True) -> None:
        """
        Enable or disable shared code cache (NO-OP in pyston-lite 2.3.5).

        Args:
            enable: Whether to enable shared cache - stored but NOT applied
        """
        self.pyston_options['shared_cache'] = enable
        logger.info(
            f"Requested shared_cache={enable}, but pyston-lite 2.3.5 "
            "does not support this via Python API; this is a no-op."
        )

    def enable_debug_mode(self, enable: bool = True) -> None:
        """
        Enable or disable debug mode (NO-OP in pyston-lite 2.3.5).

        Args:
            enable: Whether to enable debug mode - stored but NOT applied
        """
        self.pyston_options['debug'] = enable
        logger.info(
            f"Requested debug={enable}, but pyston-lite 2.3.5 "
            "does not support this via Python API; this is a no-op."
        )

    def clear_cache(self) -> None:
        """Clear Pyston code cache (limited support in pyston-lite 2.3.5)."""
        # pyston-lite 2.3.5 does not expose a "clear JIT cache" API
        # Clear only Epochly's own tracking
        super().clear_cache()
        logger.debug("Cleared Epochly's Pyston tracking (pyston-lite cache is managed by runtime)")

    def get_optimization_status(self) -> Dict[str, Any]:
        """
        Get current optimization status.

        Returns:
            Dictionary with Pyston status information
        """
        return {
            'available': PYSTON_AVAILABLE,
            'enabled': _PYSTON_ENABLED,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
            'python_supported': sys.version_info[:2] <= (3, 10),
            'pyston_options': dict(self.pyston_options),
            'note': (
                "Pyston-Lite is a process-wide JIT. Epochly does not compile per-function "
                "callables; 'compile' ensures pyston_lite.enable() was called and returns "
                "the original function."
            ),
        }

    def __del__(self):
        """Cleanup Pyston resources."""
        try:
            super().__del__()
            # Pyston cleanup is handled automatically by the runtime
        except Exception:
            pass
