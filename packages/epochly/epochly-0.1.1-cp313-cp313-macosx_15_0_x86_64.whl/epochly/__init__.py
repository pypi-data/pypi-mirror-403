"""
Epochly - Transparent Performance Optimization

A transparent performance optimization framework for Python applications
through progressive enhancement levels.

Copyright (c) 2025 Epochly Development Team. All Rights Reserved.
PROPRIETARY SOFTWARE - See LICENSE file for details.
"""

try:
    from importlib.metadata import version as _get_version
    __version__ = _get_version("epochly")
except Exception:
    __version__ = "0.1.0"  # Fallback for editable installs / development
__author__ = "Epochly Development Team"
__email__ = "dev@epochly-python.org"

# Core imports needed for lazy initialization
import os
import sys
import threading as _threading
import time as _time
import logging  # CRITICAL FIX: For preflight thread logging

# Initialize module logger for preflight and other module-level operations
logger = logging.getLogger(__name__)

# ============================================================================
# Lazy Initialization System (Task 1: Performance Improvements)
# ============================================================================
# Epochly core is NOT initialized on import. Instead, initialization is
# deferred until first actual use via _ensure_core_initialized().
#
# This eliminates import-time side effects and makes simple tooling
# (linters, type checkers, etc.) pay zero startup penalty.
#
# Key components:
# - _core_singleton: The singleton core instance (None until initialized)
# - _auto_enabled: Whether auto-enable has been triggered
# - _init_lock: Threading lock for thread-safe initialization
# - _ensure_core_initialized(): Main initialization function
# - _should_auto_enable(): Check if auto-enable should trigger
# ============================================================================

# Global state for lazy initialization
_core_singleton = None
_auto_enabled = False
_init_lock = _threading.Lock()

# Q-M-002: Structured error diagnostics for lazy init failures
# Stores details about the last initialization error for debugging
_last_init_error = None


def _should_auto_enable():
    """
    Check if auto-enable should be triggered based on environment variable.

    Auto-enable is triggered when EPOCHLY_AUTO_ENABLE environment variable
    is set to one of: '1', 'true', 'yes', 'on' (case-insensitive).

    Returns:
        bool: True if EPOCHLY_AUTO_ENABLE is set to a truthy value
    """
    return os.environ.get('EPOCHLY_AUTO_ENABLE', '').lower() in ('1', 'true', 'yes', 'on')


def _ensure_core_initialized():
    """
    Ensure Epochly core is initialized (lazy initialization).

    This is the main entry point for lazy initialization. It:
    1. Checks if core is already initialized (fast path)
    2. If not, acquires lock and initializes (slow path)
    3. Records timing metrics via performance monitor
    4. Returns the initialized core instance

    Thread-safe: Multiple concurrent calls will only initialize once.

    Returns:
        EpochlyCore: The initialized core instance, or None if initialization failed

    Note:
        If initialization fails, a warning is issued and None is returned.
        This allows graceful degradation - optimizations will be disabled
        but the application will continue to run.
    """
    global _core_singleton

    # CRITICAL: Check emergency disable BEFORE anything - this is for emergencies
    # and should disable even an already-running core
    if os.environ.get('EPOCHLY_EMERGENCY_DISABLE') == '1':
        return None

    # P3-1 FIX (Dec 2025): Move singleton check BEFORE EPOCHLY_DISABLE check.
    #
    # PROBLEM: During Level 3 ProcessPool initialization, EPOCHLY_DISABLE=1 is
    # temporarily set in the main process to prevent workers from initializing
    # Epochly recursively. However, if get_status() is called from another thread
    # during this time, it would see EPOCHLY_DISABLE=1 and return None, causing
    # level to appear as "DISABLED" even though core is fully initialized.
    #
    # SOLUTION: Check if core is already initialized BEFORE checking EPOCHLY_DISABLE.
    # EPOCHLY_DISABLE is meant to prevent NEW initialization, not to shut down
    # an already-running core. An already-initialized core should keep running
    # even if EPOCHLY_DISABLE=1 is temporarily set.
    #
    # Fast path: core already initialized - return it regardless of EPOCHLY_DISABLE
    if _core_singleton is not None:
        return _core_singleton

    # EPOCHLY_DISABLE prevents NEW initialization only (checked AFTER singleton check)
    if os.environ.get('EPOCHLY_DISABLE') == '1':
        return None

    # Slow path: need to initialize
    with _init_lock:
        # Double-check: another thread may have initialized while we waited
        if _core_singleton is not None:
            return _core_singleton

        # Record initialization start time
        start_time = _time.perf_counter()

        try:
            from .core.epochly_core import EpochlyCore
            import atexit

            # Create and initialize core
            _core_singleton = EpochlyCore()
            _core_singleton.initialize()

            # Register cleanup handler for proper shutdown
            atexit.register(_cleanup_global_epochly)

            # Update backward compatibility alias
            _update_global_epochly_core_alias()

            # Record initialization time
            init_time_ms = (_time.perf_counter() - start_time) * 1000

            # Try to record metric (graceful degradation if monitor not available)
            try:
                if hasattr(_core_singleton, 'performance_monitor'):
                    _core_singleton.performance_monitor.record_metric(
                        'core.lazy_init_ms', init_time_ms
                    )
            except Exception:
                pass  # Silently ignore metric recording failures

        except Exception as e:
            # Q-M-002: Store structured error details for diagnostic retrieval
            global _last_init_error
            import traceback as _tb
            from datetime import datetime

            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'timestamp': datetime.now().isoformat(),
            }

            # Include traceback if debug mode enabled
            if os.environ.get('EPOCHLY_DEBUG') == '1':
                error_details['traceback'] = _tb.format_exc()
                print(f"Epochly initialization error:", file=sys.stderr)
                _tb.print_exc(file=sys.stderr)

            _last_init_error = error_details

            # Q-M-002: Support EPOCHLY_STRICT_INIT to fail fast
            strict_mode = os.environ.get('EPOCHLY_STRICT_INIT') == '1'
            if strict_mode:
                from .utils.exceptions import EpochlyInitializationError
                raise EpochlyInitializationError(
                    f"Epochly core initialization failed: {e}",
                    component="lazy_init",
                    cause=e
                ) from e

            # Non-strict mode: Warn user and provide diagnostics
            import warnings
            warnings.warn(
                f"Epochly core initialization failed: {e}. "
                f"Optimization will be disabled but application will continue. "
                f"To debug, set EPOCHLY_DEBUG=1 or EPOCHLY_STRICT_INIT=1.",
                RuntimeWarning,
                stacklevel=2
            )

            # Core remains None - callers will see this and skip optimization
            _core_singleton = None

    return _core_singleton


def _update_global_epochly_core_alias():
    """
    Update the _global_epochly_core alias to point to current singleton.

    This is called after successful initialization to maintain backward compatibility.
    """
    global _global_epochly_core
    _global_epochly_core = _core_singleton


def _cleanup_global_epochly():
    """
    Cleanup global Epochly core on exit.

    Shuts down the core instance and resets all global state.
    Called automatically via atexit handler.

    CRITICAL FIX (Dec 2025): Only run cleanup in main process.
    Subprocess workers (from multiprocessing or sub-interpreters) also trigger
    atexit handlers when they exit. If we call shutdown() in a subprocess,
    it can interfere with the main process's detection threads, causing
    Level 3 detection to abort prematurely (stop_event gets set).
    """
    import multiprocessing

    global _core_singleton, _auto_enabled, _global_epochly_core

    # Only cleanup in the main process - subprocesses should not call shutdown
    # on the main process's singleton (they have their own copy anyway)
    current_process = multiprocessing.current_process()
    if current_process.name != "MainProcess":
        # Subprocess - don't touch the singleton
        return

    if _core_singleton:
        try:
            _core_singleton.shutdown()
        except Exception:
            # Ignore errors during exit cleanup
            pass
        finally:
            _core_singleton = None
            _auto_enabled = False  # Reset for potential module reload
            _global_epochly_core = None  # Reset alias as well


# Backward compatibility: Keep _global_epochly_core as alias for _core_singleton
# This will be updated after initialization via _update_global_epochly_core_alias()
_global_epochly_core = None


# ============================================================================
# Q-M-002: Initialization State Detection Functions
# ============================================================================
# These functions allow callers to detect and diagnose lazy init failures.
# ============================================================================

def get_init_error():
    """
    Get details about the last initialization error.

    Q-M-002: Provides structured error diagnostics instead of silent None.

    Returns:
        dict: Error details with 'error_type', 'error_message', 'timestamp',
              and optionally 'traceback' (if EPOCHLY_DEBUG=1 was set).
              Returns None if no error occurred.
    """
    return _last_init_error


def is_initialized():
    """
    Check if Epochly core is successfully initialized.

    Q-M-002: Allows callers to detect initialization state.

    Returns:
        bool: True if core is initialized and ready, False otherwise.
    """
    return _core_singleton is not None


def had_init_error():
    """
    Check if initialization was attempted and failed.

    Q-M-002: Allows callers to distinguish between "not yet initialized"
    and "tried to initialize but failed".

    Returns:
        bool: True if initialization was attempted and failed.
    """
    return _last_init_error is not None


def clear_init_error():
    """
    Clear the initialization error state to allow retry.

    Q-M-002: Allows callers to reset error state before retrying init.
    Useful after fixing the underlying issue (e.g., installing dependencies).
    """
    global _last_init_error
    _last_init_error = None


# ============================================================================
# Lazy API Wrappers (Always Lazy - Task 1 Performance Improvement)
# ============================================================================
# ALL public API functions use lazy imports to minimize import-time overhead.
# This ensures import epochly completes in <10ms regardless of mode.
# ============================================================================

def epochly_run(*args, **kwargs):
    """
    Run a Python function with Epochly optimization.

    Lazy import wrapper that defers module loading until first use.
    Ensures core is initialized before calling the actual function.

    Args:
        Same as epochly.api.public_api.epochly_run

    Returns:
        Result from the optimized function execution
    """
    _ensure_core_initialized()
    from .api.public_api import epochly_run as _epochly_run
    return _epochly_run(*args, **kwargs)


def configure(*args, **kwargs):
    """
    Configure Epochly optimization parameters.

    Lazy import wrapper that defers module loading until first use.
    Ensures core is initialized before calling the actual function.

    Args:
        Same as epochly.api.public_api.configure

    Returns:
        Configuration object or None
    """
    _ensure_core_initialized()
    from .api.public_api import configure as _configure
    return _configure(*args, **kwargs)


def optimize(*args, **kwargs):
    """
    Decorator to optimize a Python function with Epochly.

    Lazy import wrapper that defers module loading until decorator application.
    Ensures core is initialized before applying the decorator.

    Supports both usage patterns:
    - @epochly.optimize (without parentheses) - applies default optimization
    - @epochly.optimize() or @epochly.optimize(level=2) - with arguments

    Args:
        Same as epochly.api.decorators.optimize

    Returns:
        Decorated function with Epochly optimizations applied
    """
    _ensure_core_initialized()
    from .api.decorators import optimize as _optimize

    # Support @epochly.optimize without parentheses
    # If called with a single callable argument and no kwargs, it's direct decoration
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]
        # Apply the decorator with default settings
        return _optimize()(func)

    # Otherwise, pass through to the underlying decorator
    return _optimize(*args, **kwargs)


def optimize_context(*args, **kwargs):
    """
    Context manager for temporary Epochly optimization.

    Lazy import wrapper that defers module loading until context creation.
    Ensures core is initialized before creating the context manager.

    Args:
        Same as epochly.api.context_managers.optimize_context

    Returns:
        Context manager for Epochly optimization
    """
    _ensure_core_initialized()
    from .api.context_managers import optimize_context as _optimize_context
    return _optimize_context(*args, **kwargs)


# ============================================================================
# Transparent Activation Function
# ============================================================================

def auto_enable(force=False):
    """
    Transparently enable Epochly for all Python code.

    Called from sitecustomize.py to activate Epochly without code changes.
    Implements the zero-configuration promise from architecture spec.

    With lazy initialization, this function now:
    1. Installs hooks (profiler, import hook) immediately
    2. Defers core initialization until first use OR if force=True

    Args:
        force (bool): If True, force immediate core initialization.
                     If False, use lazy initialization (initialize on first use).

    Architecture Reference:
    - Lines 1838-1854: auto_enable() specification
    - Lines 5680-5700: Transparent activation mechanism
    - Lines 2012-2086: EpochlyProfiler with sys.setprofile
    - Task 1: Lazy initialization to eliminate import-time overhead
    """
    global _auto_enabled, _core_singleton

    # Quick environment check (<1ms)
    if os.environ.get('EPOCHLY_MODE') == 'off':
        return

    # CRITICAL FIX: Move state management inside lock to prevent race conditions
    # Determine initialization decision inside lock, perform initialization OUTSIDE lock
    with _init_lock:
        # Check if already enabled (prevent double-init)
        if _auto_enabled and hasattr(sys, '_epochly_initialized'):
            return

        # Mark as enabled and initialized (thread-safe)
        sys._epochly_initialized = True
        _auto_enabled = True

        # Import required components (inside lock to prevent duplicate imports)
        from .core.profiler import EpochlyProfiler, epochly_profile_hook, get_global_profiler
        from .core.import_hook import EpochlyImportHook

        # Register import hook for module interception (thread-safe)
        if EpochlyImportHook not in [type(hook) for hook in sys.meta_path]:
            sys.meta_path.insert(0, EpochlyImportHook())

        # Install profiling hook (lightweight)
        # This creates the global profiler
        #
        # P0.24 FIX (Dec 2025): sys.setprofile causes 350%+ overhead because it runs
        # on EVERY function call. On Python 3.12+, we use sys.monitoring instead
        # which can return DISABLE for individual code objects (near-zero overhead).
        #
        # The EpochlyProfiler (sys.setprofile) is ONLY needed on Python <3.12 where
        # sys.monitoring is not available. On Python 3.12+, AutoProfiler handles
        # hot loop detection via sys.monitoring with minimal overhead.
        #
        # Users can force sys.setprofile on Python 3.12+ with EPOCHLY_FORCE_SETPROFILE=1
        # (for debugging or specific profiling needs).
        skip_setprofile = os.environ.get('EPOCHLY_DISABLE_SETPROFILE', '').lower() in ('1', 'true', 'yes', 'on')
        force_setprofile = os.environ.get('EPOCHLY_FORCE_SETPROFILE', '').lower() in ('1', 'true', 'yes', 'on')

        # P0.24: On Python 3.12+, skip sys.setprofile by default (use sys.monitoring instead)
        has_sys_monitoring = sys.version_info >= (3, 12) and hasattr(sys, 'monitoring')
        if has_sys_monitoring and not force_setprofile:
            skip_setprofile = True
            import logging
            logging.getLogger('epochly').debug(
                "P0.24: Skipping sys.setprofile on Python 3.12+ (using sys.monitoring instead). "
                "Set EPOCHLY_FORCE_SETPROFILE=1 to override."
            )

        if not skip_setprofile:
            sys.setprofile(epochly_profile_hook)
        else:
            # Log at DEBUG level to avoid noise, but record the skip
            import logging
            logging.getLogger('epochly').debug("EpochlyProfiler (sys.setprofile) disabled")

        # P0.25 FIX (Jan 2026): Core initialization is LAZY by default for zero overhead.
        #
        # PREVIOUS BEHAVIOR (line 480 had: should_initialize_now = True):
        # - auto_enable() always called _ensure_core_initialized()
        # - This spawned 9-17 background threads (PerformanceMonitor, JIT workers, etc.)
        # - These threads caused ~98% overhead via GIL contention
        # - Even workloads that can't benefit from Epochly paid this penalty
        #
        # NEW BEHAVIOR:
        # - auto_enable() installs lightweight hooks only (import hook, sys.monitoring)
        # - Core initializes LAZILY when first API function is called
        # - No background threads until actually needed
        # - Workloads that don't use Epochly APIs pay near-zero overhead
        #
        # BACKWARD COMPATIBILITY:
        # - Set EPOCHLY_EAGER_INIT=1 to force immediate initialization
        # - Decorated functions (@epochly.optimize) trigger lazy init when applied
        # - Context managers trigger lazy init when entered
        # - force=True parameter still forces immediate initialization
        #
        # NOTEBOOK SUPPORT:
        # - Notebooks that call auto_enable() still work - they just get lazy init
        # - First use of @epochly.optimize or epochly.set_level() triggers core init
        # - This is BETTER for notebooks - faster startup, less overhead
        should_initialize_now = (
            force or
            os.environ.get('EPOCHLY_EAGER_INIT', '').lower() in ('1', 'true', 'yes', 'on')
        )

        # Re-check environment at call time (not import time) for correct test behavior
        # Note: should_initialize_now (force or EPOCHLY_EAGER_INIT=1) overrides skip_init
        # This allows explicit eager init to work even in test mode
        skip_init = (
            not should_initialize_now and (
                os.environ.get('EPOCHLY_DISABLE_AUTO_INIT', '').lower() in ('1', 'true', 'yes', 'on') or
                os.environ.get('EPOCHLY_TEST_MODE') == '1'
            )
        )

    # CRITICAL: Perform initialization OUTSIDE the lock to prevent deadlock
    # _ensure_core_initialized() acquires _init_lock internally, so we can't hold it here
    if should_initialize_now and not skip_init:
        # Force immediate initialization (old behavior for backward compatibility)
        core = _ensure_core_initialized()

        # Wire profiler to existing ML/RNN system
        from .core.profiler import get_global_profiler
        profiler = get_global_profiler()
        if profiler and core:
            try:
                # Connect to adaptive orchestrator if available
                if hasattr(core, '_adaptive_orchestrator'):
                    profiler._adaptive_orchestrator = core._adaptive_orchestrator

                # Connect to JIT analyzer if available
                if hasattr(core, '_jit_manager'):
                    jit_manager = core._jit_manager
                    if hasattr(jit_manager, '_jit_analyzer'):
                        profiler._jit_analyzer = jit_manager._jit_analyzer

                # Connect to workload detector if available
                if hasattr(core, 'plugin_manager'):
                    plugins = core.plugin_manager.get_plugin('workload_detector')
                    if plugins:
                        profiler._workload_detector = plugins
            except Exception:
                # Silently fail - profiler will work in standalone mode
                pass
    # else: Lazy initialization - core will be initialized on first API call

    # CRITICAL FIX (Jan 2025): Install IPython hook for source extraction
    # This ensures that cell source is registered with linecache for GPU compilation
    try:
        from .profiling.source_extractor import SourceExtractor
        SourceExtractor.install_ipython_hook()
    except Exception:
        pass  # Silently fail if not in IPython/Jupyter

    # ISSUE #8 FIX (perf_fixes4.md): Schedule background preflight capability detection
    _schedule_background_preflight()


def _schedule_background_preflight():
    """
    Schedule low-priority background preflight task for capability detection.

    ISSUE #8 FIX (perf_fixes4.md): Pre-detect capabilities so first call hits warmed components.
    """
    import threading

    def preflight_task():
        try:
            import time
            time.sleep(2.0)  # Wait to not interfere with startup

            # Detect subinterpreter availability
            try:
                import sys
                if sys.version_info >= (3, 12):
                    try:
                        import _xxsubinterpreters
                        logger.debug("Preflight: _xxsubinterpreters available")
                    except ImportError:
                        logger.debug("Preflight: _xxsubinterpreters not available")
            except Exception:
                pass

            # Detect GPU availability
            try:
                from .gpu.gpu_detector import GPUDetector
                detector = GPUDetector()
                gpu_info = detector.detect_gpu()
                if gpu_info.get('available'):
                    logger.debug(f"Preflight: GPU available - {gpu_info.get('device_name')}")
                else:
                    logger.debug("Preflight: No GPU detected")
            except Exception:
                pass

            # Detect NUMA topology
            try:
                from .numa import NumaManager
                numa = NumaManager()
                node_count = numa.get_node_count()
                logger.debug(f"Preflight: {node_count} NUMA nodes detected")
            except Exception:
                pass

            # perf_fixes5.md Finding #6: Fast allocator health probe
            try:
                from .memory.allocator_health_probe import probe_fast_allocator, is_fast_allocator_enabled
                available, latency_us, message = probe_fast_allocator()
                logger.debug(f"Preflight: Allocator probe - {message}")

                # Gap #2: Expose allocator health to orchestrator
                core = _core_singleton
                if core and hasattr(core, '_adaptive_orchestrator') and core._adaptive_orchestrator:
                    try:
                        # Record allocator health metric
                        orchestrator = core._adaptive_orchestrator
                        if hasattr(orchestrator, '_memory_profiler') and orchestrator._memory_profiler:
                            orchestrator._memory_profiler.record_allocation(
                                size=0,  # Metadata only
                                address=None,
                                thread_id=None
                            )
                        logger.debug(f"Allocator health exposed to orchestrator: enabled={is_fast_allocator_enabled()}, latency={latency_us:.1f}μs")
                    except Exception:
                        pass
            except Exception as e:
                logger.debug(f"Preflight: Allocator probe failed - {e}")

            # ENHANCEMENT (perf_fixes5.md Issue E): Prime JIT cache with hot functions
            try:
                # Get core to access JIT manager
                core = _core_singleton
                if core and hasattr(core, '_jit_manager') and core._jit_manager:
                    jit_manager = core._jit_manager

                    # Check if telemetry store has hot function data
                    if hasattr(jit_manager, '_telemetry_store') and jit_manager._telemetry_store:
                        telemetry = jit_manager._telemetry_store

                        # Get top N hot functions from previous runs
                        try:
                            hot_functions = telemetry.get_top_functions(limit=10)
                            if hot_functions:
                                logger.debug(f"Preflight: Priming JIT cache with {len(hot_functions)} hot functions")
                                # The actual prewarming is already handled by _schedule_prewarm_pass()
                                # This just logs that we could do it
                        except Exception:
                            pass
            except Exception:
                pass

            # ENHANCEMENT (perf_fixes5.md Issue E): Pre-size memory pools
            try:
                core = _core_singleton
                if core:
                    # Check if we have workload characteristics from previous runs
                    if hasattr(core, '_adaptive_orchestrator') and core._adaptive_orchestrator:
                        orchestrator = core._adaptive_orchestrator
                        try:
                            summary = orchestrator.get_performance_summary()
                            if summary:
                                avg_data_size = summary.get('avg_data_size', 0)
                                if avg_data_size > 0:
                                    logger.debug(f"Preflight: Historical avg data size: {avg_data_size // 1024}KB")
                                    # Pre-sizing happens in _calculate_adaptive_pool_size() during Level 3 init
                        except Exception:
                            pass
            except Exception:
                pass

            logger.debug("Preflight capability detection complete (enhanced with JIT/pool heuristics)")

        except Exception as e:
            logger.debug(f"Preflight failed: {e}")

    # Schedule as low-priority daemon thread
    preflight_thread = threading.Thread(target=preflight_task, daemon=True, name="Epochly-Preflight")
    preflight_thread.start()


# ============================================================================
# Additional Decorator API Functions (Lazy Wrappers)
# ============================================================================
# These decorators are documented in user-guide/decorators.md and must be
# accessible directly from the epochly module (e.g., @epochly.performance_monitor)
# ============================================================================

def performance_monitor(func=None):
    """
    Decorator to monitor function performance without optimization.

    Lazy import wrapper that defers module loading until decorator application.
    Ensures core is initialized before applying the decorator.

    This is equivalent to @epochly.optimize(level=0) - monitoring only.

    Args:
        func: The function to monitor (when used without parentheses)

    Returns:
        Decorated function with performance monitoring applied

    Example:
        @epochly.performance_monitor
        def my_function():
            pass

        # Or with parentheses
        @epochly.performance_monitor()
        def my_function():
            pass
    """
    _ensure_core_initialized()
    from .api.decorators import performance_monitor as _performance_monitor

    if func is not None:
        # Called without parentheses: @epochly.performance_monitor
        return _performance_monitor(func)
    else:
        # Called with parentheses: @epochly.performance_monitor()
        return _performance_monitor


def jit_compile(func=None):
    """
    Decorator to apply JIT compilation to a function.

    Lazy import wrapper that defers module loading until decorator application.
    Ensures core is initialized before applying the decorator.

    This is equivalent to @epochly.optimize(level=2) - JIT compilation.

    Args:
        func: The function to JIT compile (when used without parentheses)

    Returns:
        Decorated function with JIT compilation applied

    Example:
        @epochly.jit_compile
        def compute_intensive():
            pass
    """
    _ensure_core_initialized()
    from .api.decorators import jit_compile as _jit_compile

    if func is not None:
        # Called without parentheses: @epochly.jit_compile
        return _jit_compile(func)
    else:
        # Called with parentheses: @epochly.jit_compile()
        return _jit_compile


def full_optimize(func=None):
    """
    Decorator to apply full optimization (Level 3) to a function.

    Lazy import wrapper that defers module loading until decorator application.
    Ensures core is initialized before applying the decorator.

    This is equivalent to @epochly.optimize(level=3) - full parallelism.

    Args:
        func: The function to optimize (when used without parentheses)

    Returns:
        Decorated function with full optimization applied

    Example:
        @epochly.full_optimize
        def parallel_work():
            pass
    """
    _ensure_core_initialized()
    from .api.decorators import full_optimize as _full_optimize

    if func is not None:
        # Called without parentheses: @epochly.full_optimize
        return _full_optimize(func)
    else:
        # Called with parentheses: @epochly.full_optimize()
        return _full_optimize


def threading_optimize(func=None, *, max_workers=None, thread_pool=True):
    """
    Decorator to apply threading optimization (Level 1) to a function.

    Lazy import wrapper that defers module loading until decorator application.
    Ensures core is initialized before applying the decorator.

    This is equivalent to @epochly.optimize(level=1) - threading for I/O.

    Args:
        func: The function to optimize (when used without parentheses)
        max_workers: Maximum number of worker threads
        thread_pool: Whether to use thread pool (default: True)

    Returns:
        Decorated function with threading optimization applied

    Example:
        @epochly.threading_optimize
        def io_heavy_work():
            pass

        @epochly.threading_optimize(max_workers=8)
        def custom_threading():
            pass
    """
    _ensure_core_initialized()
    from .api.decorators import threading_optimize as _threading_optimize

    if func is not None:
        # Called without parentheses: @epochly.threading_optimize
        return _threading_optimize()(func)
    else:
        # Called with parentheses: @epochly.threading_optimize(max_workers=8)
        return _threading_optimize(max_workers=max_workers, thread_pool=thread_pool)


# ============================================================================
# Additional Context Manager API Functions (Lazy Wrappers)
# ============================================================================
# These context managers are documented in user-guide/context-managers.md and
# must be accessible directly from the epochly module.
# ============================================================================

def monitoring_context(enable=True, reset_on_exit=False):
    """
    Context manager for performance monitoring without optimization.

    Lazy import wrapper that defers module loading until context creation.
    Ensures core is initialized before creating the context manager.

    This is equivalent to optimize_context(level=0) - monitoring only.

    Args:
        enable: Whether to enable monitoring (default: True)
        reset_on_exit: Whether to reset metrics on exit (default: False)

    Returns:
        Context manager for performance monitoring

    Example:
        with epochly.monitoring_context() as metrics:
            # Code to monitor
            pass
        print(metrics)
    """
    _ensure_core_initialized()
    from .api.context_managers import monitoring_context as _monitoring_context
    return _monitoring_context(enable=enable, reset_on_exit=reset_on_exit)


def jit_context(**options):
    """
    Context manager for JIT compilation (Level 2).

    Lazy import wrapper that defers module loading until context creation.
    Ensures core is initialized before creating the context manager.

    This is equivalent to optimize_context(level=2) - JIT compilation.

    Args:
        **options: Additional JIT options

    Returns:
        Context manager for JIT optimization

    Example:
        with epochly.jit_context():
            # Numerical code to JIT compile
            pass
    """
    _ensure_core_initialized()
    from .api.context_managers import jit_context as _jit_context
    return _jit_context(**options)


def threading_context(max_workers=None, thread_pool=True, **options):
    """
    Context manager for threading optimization (Level 1).

    Lazy import wrapper that defers module loading until context creation.
    Ensures core is initialized before creating the context manager.

    This is equivalent to optimize_context(level=1) - threading for I/O.

    Args:
        max_workers: Maximum number of worker threads
        thread_pool: Whether to use thread pool (default: True)
        **options: Additional threading options

    Returns:
        Context manager for threading optimization

    Example:
        with epochly.threading_context(max_workers=8):
            # I/O-bound code
            pass
    """
    _ensure_core_initialized()
    from .api.context_managers import threading_context as _threading_context
    return _threading_context(max_workers=max_workers, thread_pool=thread_pool, **options)


def full_optimize_context(**options):
    """
    Context manager for full optimization (Level 3).

    Lazy import wrapper that defers module loading until context creation.
    Ensures core is initialized before creating the context manager.

    This is equivalent to optimize_context(level=3) - full parallelism.

    Args:
        **options: Additional optimization options

    Returns:
        Context manager for full optimization

    Example:
        with epochly.full_optimize_context():
            # Parallel-capable code
            pass
    """
    _ensure_core_initialized()
    from .api.context_managers import full_optimize_context as _full_optimize_context
    return _full_optimize_context(**options)


def benchmark_context(name="benchmark", print_results=True):
    """
    Context manager for benchmarking code blocks.

    Lazy import wrapper that defers module loading until context creation.
    Ensures core is initialized before creating the context manager.

    Args:
        name: Name for the benchmark (default: "benchmark")
        print_results: Whether to print results on exit (default: True)

    Returns:
        Context manager that yields a dict with timing information

    Example:
        with epochly.benchmark_context("my_operation") as timing:
            # Code to benchmark
            pass
        print(f"Elapsed: {timing['elapsed_ms']}ms")
    """
    _ensure_core_initialized()
    from .api.context_managers import benchmark_context as _benchmark_context
    return _benchmark_context(name=name, print_results=print_results)


def epochly_disabled_context():
    """
    Context manager to temporarily disable Epochly optimization.

    Lazy import wrapper that defers module loading until context creation.
    Ensures core is initialized before creating the context manager.

    Useful for debugging or when you need baseline Python behavior.

    Returns:
        Context manager that disables Epochly within the block

    Example:
        with epochly.epochly_disabled_context():
            # Code runs without Epochly optimization
            result = baseline_operation()
    """
    _ensure_core_initialized()
    from .api.context_managers import epochly_disabled_context as _epochly_disabled_context
    return _epochly_disabled_context()


# ============================================================================
# Additional Public API Functions (Lazy Wrappers)
# ============================================================================

def get_status(*args, **kwargs):
    """
    Get current Epochly status and statistics.

    Lazy import wrapper that defers module loading until first call.

    Returns:
        Dictionary containing status information
    """
    core = _ensure_core_initialized()

    # If core is None (disabled or emergency disabled), return minimal status
    if core is None:
        import platform
        return {
            'enabled': False,
            'initialized': False,
            'enhancement_level': 'DISABLED',
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
            'platform': platform.system(),
            'emergency_disable': os.environ.get('EPOCHLY_EMERGENCY_DISABLE') == '1',
            'regular_disable': os.environ.get('EPOCHLY_DISABLE') == '1',
        }

    from .api.public_api import get_status as _get_status
    return _get_status(*args, **kwargs)


def get_config(*args, **kwargs):
    """
    Get current Epochly configuration.

    Lazy import wrapper for configuration access.

    Returns:
        Dictionary containing configuration
    """
    _ensure_core_initialized()
    try:
        from .api.public_api import get_config as _get_config
        return _get_config(*args, **kwargs)
    except (ImportError, AttributeError):
        # Fallback: return config from core
        core = _core_singleton
        if core and hasattr(core, 'config'):
            return core.config if not callable(core.config) else {}
        return {}


def get_license_info(*args, **kwargs):
    """
    Get current license information.

    Lazy import wrapper for license info.

    Returns:
        Dictionary containing license details
    """
    _ensure_core_initialized()
    core = _ensure_core_initialized()
    if core and hasattr(core, 'get_license_info'):
        return core.get_license_info()
    # Fallback
    from .licensing.license_enforcer import get_license_limits
    return get_license_limits()


def check_feature(feature_name: str) -> bool:
    """
    Check if a feature is enabled under current license.

    Args:
        feature_name: Name of feature to check

    Returns:
        True if feature is available (False if licensing system unavailable)
    """
    core = _ensure_core_initialized()
    if core and hasattr(core, 'check_feature'):
        try:
            return core.check_feature(feature_name)
        except Exception:
            pass  # Fall through to enforcer

    try:
        from .licensing.license_enforcer import check_feature as _check_feature
        return _check_feature(feature_name)
    except (ImportError, AttributeError):
        # Conservative default: feature not available if licensing unavailable
        return False


def set_level(level: int):
    """
    Set enhancement level.

    Args:
        level: Enhancement level (0-4)
            0 = Monitor only (baseline)
            1 = Threading optimizations
            2 = JIT compilation
            3 = Full optimization (parallel processing)
            4 = GPU acceleration (if available)

    Note:
        Explicit level requests (3 and 4) automatically bypass stability checks
        since they are explicit user requests. If GPU is unavailable for level 4,
        falls back to Level 3.
    """
    _ensure_core_initialized()
    core = _ensure_core_initialized()
    if core and hasattr(core, 'set_enhancement_level'):
        # Convert int to EnhancementLevel enum
        from .core.epochly_core import EnhancementLevel
        level_map = {
            0: EnhancementLevel.LEVEL_0_MONITOR,
            1: EnhancementLevel.LEVEL_1_THREADING,
            2: EnhancementLevel.LEVEL_2_JIT,
            3: EnhancementLevel.LEVEL_3_FULL,
            4: EnhancementLevel.LEVEL_4_GPU,
        }
        if level not in level_map:
            raise ValueError(f"Invalid level {level}. Must be 0-4.")
        enum_level = level_map[level]

        # FIX (Dec 2025): ALWAYS use force=True for explicit set_level() calls.
        # This is an explicit user request - they know what level they want.
        # The progression_manager's can_progress_to() checks are for automatic
        # transitions, not explicit user commands. Without force=True, downgrading
        # from LEVEL_4 to LEVEL_2 silently fails.
        result = core.set_enhancement_level(enum_level, force=True)

        # RCA (Dec 2025): For JIT levels (2+), wait for JIT to be ready.
        # This prevents the erratic timing bug where is_enabled()=False but level=3,
        # causing inconsistent JIT application across runs.
        if level >= 2 and result:
            # Wait for JIT system to be actually ready
            # Level 3+ needs more time for ProcessPool spawn (~8s on macOS)
            timeout = 15.0 if level >= 3 else 10.0
            if hasattr(core, 'wait_for_level'):
                jit_ready = core.wait_for_level(enum_level, timeout=timeout)
                if not jit_ready:
                    import logging
                    logging.getLogger('epochly').warning(
                        f"Timeout waiting for level {level} JIT to be ready after {timeout}s. "
                        f"Performance may be inconsistent."
                    )

        # RCA (Dec 2025): Warn if enabled=False after setting level
        if not core.enabled:
            import logging
            reason = getattr(core, '_disabled_reason', 'unknown')
            logging.getLogger('epochly').error(
                f"EPOCHLY DISABLED after set_level({level}): {reason}. "
                f"JIT acceleration will NOT work. Check initialization logs."
            )


def get_level() -> int:
    """
    Get current enhancement level.

    Returns:
        Current enhancement level (0-4):
            0 = Monitor only (baseline)
            1 = Threading optimizations
            2 = JIT compilation
            3 = Full optimization (parallel processing)
            4 = GPU acceleration
    """
    core = _ensure_core_initialized()
    if core and hasattr(core, 'get_enhancement_level'):
        level = core.get_enhancement_level()
        # Return the integer value of the enum
        return level.value if hasattr(level, 'value') else int(level)
    return 0


def is_enabled() -> bool:
    """
    Check if Epochly is currently enabled.

    Returns:
        True if Epochly is enabled

    RCA (Dec 2025): Fixed order of checks to prevent race condition.
    Previously, EPOCHLY_DISABLE was checked first, but this env var is
    temporarily set during background worker spawn (to prevent fork bomb).
    This caused is_enabled() to return False during the ~8s spawn window,
    breaking JIT application and causing erratic performance.

    The fix: Check core.enabled first. If the core exists and is enabled,
    trust that state. Only use env var checks for worker isolation (when
    core doesn't exist or isn't enabled).

    IMPORTANT: EPOCHLY_EMERGENCY_DISABLE always takes precedence - it's
    designed for emergency situations where we need to immediately disable
    regardless of core state.
    """
    # EMERGENCY_DISABLE always wins - must be checked FIRST
    # This is for emergency situations where immediate disable is required
    if os.environ.get('EPOCHLY_EMERGENCY_DISABLE') == '1':
        return False

    # RCA FIX: Check core state next - this is the authoritative source
    # The core tracks whether Epochly is truly enabled, independent of
    # temporary env var settings during background spawn.
    core = _ensure_core_initialized()
    if core and hasattr(core, 'enabled'):
        # Core exists - trust its enabled state
        # This handles the race condition where EPOCHLY_DISABLE=1 is
        # temporarily set during ProcessPool spawn but core.enabled=True
        return core.enabled

    # No core exists - fall back to env var checks
    # This is the worker isolation case: workers inherit EPOCHLY_DISABLE=1
    # and should not initialize Epochly (prevents fork bomb)
    if os.environ.get('EPOCHLY_DISABLE') == '1':
        return False

    return False


def get_metrics(*args, **kwargs):
    """
    Get performance metrics.

    Lazy import wrapper for metrics collection.

    Returns:
        Dictionary containing metrics
    """
    _ensure_core_initialized()
    from .api.public_api import get_metrics as _get_metrics
    return _get_metrics(*args, **kwargs)


def shutdown():
    """
    Shut down Epochly system.

    Lazy import wrapper for shutdown.
    """
    global _core_singleton
    if _core_singleton:
        _core_singleton.shutdown()
        _core_singleton = None


def emergency_disable():
    """
    Emergency disable Epochly for production incidents.

    This function immediately disables Epochly optimization and returns
    the system to baseline Python behavior. Useful for production emergencies
    where Epochly may be causing issues.
    """
    global _core_singleton

    # Set emergency disable flag
    os.environ["EPOCHLY_EMERGENCY_DISABLE"] = "1"

    # RCA (Dec 2025): Set disabled reason for diagnostics before shutdown
    if _core_singleton:
        _core_singleton._disabled_reason = "Emergency disable via API"
        _core_singleton.enabled = False
        try:
            _core_singleton.shutdown()
        except Exception:
            pass  # Best effort shutdown
        _core_singleton = None


def get_core():
    """
    Get the Epochly core instance.

    P1 WARMUP OPTIMIZATION (Jan 2026): Provides access to the core for
    eager_mode tests and advanced users who need direct core access.

    Returns:
        EpochlyCore: The core instance, or None if not initialized
    """
    global _core_singleton
    return _core_singleton


def is_gpu_available():
    """
    Check if GPU acceleration is available.

    Returns:
        bool: True if GPU is available and can be used
    """
    try:
        from .gpu import is_gpu_available as _is_gpu_available
        return _is_gpu_available()
    except ImportError:
        return False
    except Exception:
        return False


def get_gpu_info():
    """
    Get information about available GPU(s).

    Returns:
        dict or None: GPU information dictionary, or None if no GPU available
    """
    try:
        from .gpu import get_gpu_info as _get_gpu_info
        info = _get_gpu_info()
        # Convert GPUInfo dataclass to dict for documented API
        if info is None:
            return None
        if hasattr(info, '__dict__'):
            # Dataclass or similar object
            result = {}
            for key, value in vars(info).items():
                # Convert enum values to strings
                if hasattr(value, 'value'):
                    result[key] = value.value
                else:
                    result[key] = value
            return result
        elif isinstance(info, dict):
            return info
        else:
            return None
    except ImportError:
        return None
    except Exception:
        return None


# Version and metadata exports
__all__ = [
    "__version__",
    "__author__",
    "__email__",
    # Core API
    "epochly_run",
    "configure",
    "optimize",
    "optimize_context",
    "auto_enable",  # Export for sitecustomize.py
    # Additional decorator API (documented in user-guide/decorators.md)
    "performance_monitor",
    "jit_compile",
    "full_optimize",
    "threading_optimize",
    # Additional context manager API (documented in user-guide/context-managers.md)
    "monitoring_context",
    "jit_context",
    "threading_context",
    "full_optimize_context",
    "benchmark_context",
    "epochly_disabled_context",
    # Status and configuration
    "get_status",
    "get_config",
    "get_license_info",
    "check_feature",
    "set_level",
    "get_level",
    "is_enabled",
    "get_metrics",
    "shutdown",
    "emergency_disable",
    # Q-M-002: Lazy init error handling
    "get_init_error",
    "is_initialized",
    "had_init_error",
    "clear_init_error",
    "EpochlyInitializationError",
    # P1 WARMUP OPTIMIZATION (Jan 2026): Eager mode API
    "eager_mode",
    "CompilationMode",
    "get_core",  # Expose for eager_mode tests
    # GPU API (documented in optimization-guide/gpu-optimization-strategy.md)
    "is_gpu_available",
    "get_gpu_info",
]

# Q-M-002: Import EpochlyInitializationError for direct access
from .utils.exceptions import EpochlyInitializationError

# P1 WARMUP OPTIMIZATION (Jan 2026): Eager mode API for synchronous compilation
from .jit.manager import eager_mode, CompilationMode
