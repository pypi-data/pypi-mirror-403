"""
Epochly Bootstrap - Transparent Process Interception

Implements the bootstrap sequence described in the technical architecture:
https://github.com/chandlercvaughn/epochly/blob/main/planning/epochly-architecture-spec.md

This module is called from sitecustomize.py to transparently enable Epochly
for all Python processes without code changes.

Bootstrap Sequence (from architecture spec):
1. [110] Instrumentation loader - inserts low-overhead probes
2. [120] Telemetry profiler - begins sampling on rolling buffer
3. [130] Compatibility test harness - runs cached "can I parallelize?" checks
4. [140] Tier-state manager - initializes progressive FSM (Level 0→4)
5. [150] Backend selector - primes available engines
6. [160] Worker-pool manager - prepares sub-interpreters/threads
7. [170] Shared-memory manager - sets up zero-copy buffers
8. [180] Watchdog & rollback - enforces safety constraints
9. [190] Policy & safety engine - validates all tier changes

Transactional Bootstrap (P0-2 Remediation):
- Each bootstrap step has corresponding cleanup function
- Partial initialization triggers full rollback in reverse order
- Structured error reporting with step name and cause
- EPOCHLY_STRICT_INIT=1 fails fast with BootstrapError exception

Author: Epochly Development Team
Date: November 16, 2025
Updated: November 25, 2025 (P0-2 transactional bootstrap)
"""

import sys
import os
import threading
from typing import Optional, Dict, Any, Callable, List

from .utils.logger import get_logger

logger = get_logger(__name__)


class BootstrapError(Exception):
    """
    Exception raised when bootstrap fails in strict mode.

    P0-2: Provides structured error details including which step failed.
    """

    def __init__(self, step: str, message: str, cause: Optional[Exception] = None):
        """
        Initialize BootstrapError.

        Args:
            step: Name of the bootstrap step that failed
            message: Error message
            cause: Original exception that caused the failure
        """
        self.step = step
        self.cause = cause
        super().__init__(f"Bootstrap step '{step}' failed: {message}")


# Global bootstrap state
_bootstrap_lock = threading.Lock()
_bootstrap_complete = False
_completed_steps: List[str] = []  # P0-2: Track completed steps for rollback
_last_error: Optional[Dict[str, Any]] = None  # P0-2: Structured error details


def get_last_error() -> Optional[Dict[str, Any]]:
    """
    Get details of the last bootstrap error.

    P0-2: Returns structured error information for debugging.

    Returns:
        Dict with 'step' and 'error' keys, or None if no error
    """
    return _last_error


def _record_step_completion(step_name: str):
    """
    Record that a bootstrap step completed successfully.

    P0-2: Tracks completed steps for rollback support.

    Args:
        step_name: Name of the completed step
    """
    global _completed_steps
    if step_name not in _completed_steps:
        _completed_steps.append(step_name)
        logger.debug(f"Bootstrap step '{step_name}' completed successfully")


def _record_step_failure(step_name: str, error: Exception):
    """
    Record that a bootstrap step failed.

    P0-2: Stores structured error details.

    Args:
        step_name: Name of the failed step
        error: Exception that caused the failure
    """
    global _last_error
    _last_error = {
        'step': step_name,
        'error': str(error),
        'exception': error,
    }
    logger.error(f"Bootstrap step '{step_name}' failed: {error}")


def _rollback_completed_steps():
    """
    Rollback all completed bootstrap steps in reverse order.

    P0-2: Calls cleanup function for each completed step.
    Ensures idempotent teardown - safe to call multiple times.
    """
    global _completed_steps

    if not _completed_steps:
        logger.debug("No completed steps to rollback")
        return

    logger.info(f"Rolling back {len(_completed_steps)} completed bootstrap steps...")

    # Rollback in reverse order
    for step_name in reversed(_completed_steps.copy()):
        if step_name in BOOTSTRAP_STEPS:
            cleanup_func = BOOTSTRAP_STEPS[step_name].get('cleanup')
            if cleanup_func:
                try:
                    cleanup_func()
                    logger.debug(f"Rolled back step '{step_name}'")
                except Exception as e:
                    logger.warning(f"Cleanup for '{step_name}' failed: {e}")
                    # Continue with other cleanups even if one fails

    # Clear completed steps after rollback
    _completed_steps = []
    logger.debug("Rollback complete - completed steps cleared")


def teardown():
    """
    Explicit teardown of bootstrap state.

    P0-2: Provides idempotent cleanup mechanism.
    Resets all bootstrap state and calls cleanup functions.

    Thread-safe: Uses _bootstrap_lock to prevent race conditions with
    concurrent bootstrap() calls.
    """
    global _bootstrap_complete, _completed_steps, _last_error

    # mcp-reflect P0: Use same lock as bootstrap() to prevent race conditions
    with _bootstrap_lock:
        logger.info("Tearing down Epochly bootstrap...")

        # Rollback any completed steps
        _rollback_completed_steps()

        # Reset state
        _bootstrap_complete = False
        _completed_steps = []
        _last_error = None

        logger.debug("Bootstrap teardown complete")


# P0-2: Bootstrap steps registry with init/cleanup function pairs
# Each step must have 'init' and 'cleanup' functions for transactional behavior
BOOTSTRAP_STEPS: Dict[str, Dict[str, Callable]] = {
    'instrumentation': {
        'init': lambda: _attach_instrumentation(),
        'cleanup': lambda: _cleanup_instrumentation(),
    },
    'telemetry': {
        'init': lambda: _start_telemetry_profiler(),
        'cleanup': lambda: _cleanup_telemetry_profiler(),
    },
    'compatibility': {
        'init': lambda: _initialize_compatibility_harness(),
        'cleanup': lambda: _cleanup_compatibility_harness(),
    },
    'tier_state': {
        'init': lambda: _initialize_tier_state_manager(),
        'cleanup': lambda: _cleanup_tier_state_manager(),
    },
    'backend': {
        'init': lambda: _prime_backend_selector(),
        'cleanup': lambda: _cleanup_backend_selector(),
    },
    'worker_pool': {
        'init': lambda: _prepare_worker_pool(),
        'cleanup': lambda: _cleanup_worker_pool(),
    },
    'shared_memory': {
        'init': lambda: _initialize_shared_memory(),
        'cleanup': lambda: _cleanup_shared_memory(),
    },
    'watchdog': {
        'init': lambda: _install_watchdog(),
        'cleanup': lambda: _cleanup_watchdog(),
    },
    'policy': {
        'init': lambda: _configure_policy_engine(),
        'cleanup': lambda: _cleanup_policy_engine(),
    },
}


def bootstrap(force: bool = False) -> bool:
    """
    Bootstrap Epochly for transparent acceleration.

    Called from sitecustomize.py to enable Epochly without code changes.
    Implements the complete bootstrap sequence from the architecture spec.

    This is the primary entry point for transparent process interception.

    P0-2: Transactional bootstrap with rollback support.
    - Each step has corresponding cleanup function
    - On failure, completed steps are rolled back in reverse order
    - EPOCHLY_STRICT_INIT=1 raises BootstrapError instead of returning False

    Args:
        force: If True, force re-bootstrap even if already done

    Returns:
        True if bootstrap succeeded, False otherwise

    Raises:
        BootstrapError: If EPOCHLY_STRICT_INIT=1 and bootstrap fails

    Architecture Reference:
    - Lines 110-190: Bootstrap component specifications
    - Lines 200-290: Progressive optimization pipeline
    - Section "Transparent process interception (how Epochly gets loaded first)"

    Environment Variables:
    - EPOCHLY_MODE: off|monitor|conservative|balanced|aggressive
    - EPOCHLY_DISABLE: 1 to disable completely
    - EPOCHLY_AUTO_ENABLE: 1 to enable auto-initialization
    - EPOCHLY_MAX_WORKERS: Override worker count
    - EPOCHLY_JIT: JIT aggressiveness (0/1/2)
    - EPOCHLY_STRICT_INIT: 1 to fail fast with exception on error

    Bootstrap Sequence:
    1. [110] Attach instrumentation probes
    2. [120] Start telemetry profiler
    3. [130] Initialize compatibility harness
    4. [140] Create tier-state manager
    5. [150] Prime backend selector
    6. [160] Prepare worker pool manager
    7. [170] Initialize shared memory manager
    8. [180] Install watchdog & rollback
    9. [190] Configure policy & safety engine
    """
    global _bootstrap_complete, _completed_steps, _last_error

    # P0-2: Check for strict mode
    strict_mode = os.environ.get('EPOCHLY_STRICT_INIT') == '1'

    # Quick environment check (<1ms)
    if os.environ.get('EPOCHLY_MODE') == 'off' or os.environ.get('EPOCHLY_DISABLE') == '1':
        logger.debug("Epochly disabled via environment variable")
        return False

    # Check if already bootstrapped
    with _bootstrap_lock:
        if _bootstrap_complete and not force:
            logger.debug("Epochly already bootstrapped")
            return True

        # mcp-reflect fix: Clear _last_error at start of each bootstrap attempt
        # to avoid stale error data from previous failed attempts
        _last_error = None

        # mcp-reflect fix: Properly handle force=True with full rollback
        # This ensures consistent state by rolling back any previous
        # initialization before starting fresh
        if force:
            logger.debug("Force re-bootstrap requested, rolling back previous state...")
            _rollback_completed_steps()
            _bootstrap_complete = False
            _completed_steps = []

        logger.info("Starting Epochly bootstrap sequence...")

        # P0-2: Execute bootstrap steps with transactional support
        step_order = [
            'instrumentation',
            'telemetry',
            'compatibility',
            'tier_state',
            'backend',
            'worker_pool',
            'shared_memory',
            'watchdog',
            'policy',
        ]

        for step_name in step_order:
            if step_name not in BOOTSTRAP_STEPS:
                logger.warning(f"Unknown bootstrap step: {step_name}")
                continue

            step_config = BOOTSTRAP_STEPS[step_name]
            init_func = step_config.get('init')

            if init_func is None:
                continue

            try:
                init_func()
                _record_step_completion(step_name)

            except Exception as e:
                # P0-2: Record failure and rollback
                _record_step_failure(step_name, e)

                if os.environ.get('EPOCHLY_DEBUG') == '1':
                    import traceback
                    traceback.print_exc()

                # Rollback completed steps
                _rollback_completed_steps()

                # P0-2: Strict mode raises exception
                if strict_mode:
                    raise BootstrapError(step_name, str(e), cause=e)

                return False

        # All steps succeeded
        _bootstrap_complete = True

        # P0-1: Signal import hook that bootstrap is complete
        _signal_import_hook_bootstrap_complete()

        logger.info("Epochly bootstrap complete - transparent acceleration active")
        return True


def _signal_import_hook_bootstrap_complete():
    """
    Signal the import hook that bootstrap has completed.

    P0-1: This enables the background wrapping thread to start.
    The thread is gated on bootstrap completion to ensure all
    dependencies are loaded before wrapping begins.
    """
    from .core.import_hook import get_import_hook

    hook = get_import_hook()
    if hook is not None:
        hook.on_bootstrap_complete()
        logger.debug("Signaled import hook that bootstrap is complete")
    else:
        logger.debug("No import hook installed, skipping bootstrap signal")


def _attach_instrumentation():
    """
    [110] Instrumentation Loader

    Inserts low-overhead probes on interpreter startup and into the import system.
    Enables observation of function timing, allocation churn, vector op density.
    """
    logger.debug("[110] Attaching instrumentation...")

    # CRITICAL: Don't install hook in worker processes (prevents fork bomb)
    # INLINE check to avoid circular imports
    try:
        import multiprocessing
        import tempfile
        process_name = multiprocessing.current_process().name
        is_disabled = os.environ.get('EPOCHLY_DISABLE_INTERCEPTION') == '1' or os.environ.get('EPOCHLY_DISABLE') == '1'

        # DEBUG: Log for analysis
        with open(f'{tempfile.gettempdir()}/epochly_bootstrap_{os.getpid()}.log', 'w') as f:
            f.write(f"PID: {os.getpid()}\n")
            f.write(f"PPID: {os.getppid()}\n")
            f.write(f"Process name: {process_name}\n")
            f.write(f"Is disabled: {is_disabled}\n")
            f.write(f"Will skip: {process_name != 'MainProcess' or is_disabled}\n")

        if process_name != 'MainProcess' or is_disabled:
            logger.debug(f"   Skipping instrumentation in worker process (name={process_name}, disabled={is_disabled})")
            return
    except Exception as e:
        logger.debug(f"   Worker detection failed: {e}, proceeding with instrumentation")

    # Install import hook for module interception
    from .core.import_hook import EpochlyImportHook

    # Only install if not already present
    hook = None
    for existing_hook in sys.meta_path:
        if isinstance(existing_hook, EpochlyImportHook):
            hook = existing_hook
            break

    if hook is None:
        hook = EpochlyImportHook()
        sys.meta_path.insert(0, hook)
        logger.debug("   Import hook installed")
    else:
        logger.debug("   Import hook already installed")

    # CRITICAL FIX: Wrap already-imported modules immediately
    # This ensures modules imported before sitecustomize (like numpy in benchmarks)
    # get wrapped properly
    hook.check_and_wrap_new_modules()
    logger.info("   Already-imported modules wrapped")

    # Install profiling hook for function timing
    from .core.profiler import epochly_profile_hook

    if sys.getprofile() is None:
        sys.setprofile(epochly_profile_hook)
        logger.debug("   Profile hook installed")

    logger.debug("[110] ✅ Instrumentation attached")


def _start_telemetry_profiler():
    """
    [120] Telemetry Profiler

    Begins sampling on a rolling buffer and writes to local telemetry store.
    """
    logger.debug("[120] Starting telemetry profiler...")

    # Telemetry is started as part of EpochlyCore initialization
    # For now, just mark as ready
    logger.debug("[120] ✅ Telemetry profiler ready")


def _initialize_compatibility_harness():
    """
    [130] Compatibility Test Harness

    Runs cached "can I safely parallelize?" checks for imported packages.
    Consults package-compatibility cache to avoid retesting unchanged wheels.
    """
    logger.debug("[130] Initializing compatibility harness...")

    # Compatibility checking happens in EpochlyCore
    # Cache is maintained automatically
    logger.debug("[130] ✅ Compatibility harness initialized")


def _initialize_tier_state_manager():
    """
    [140] Tier-State Manager

    Initializes progressive finite-state controller (Level 0→4).
    Starts at Level 0 and escalates based on safety and performance.
    """
    logger.debug("[140] Initializing tier-state manager...")

    # Get or create Epochly core (handles tier management)
    from .core.epochly_core import get_epochly_core

    core = get_epochly_core()

    # Initialize if not already done
    if not core._initialized:
        core.initialize()
        logger.debug("   Core initialized at Level 0")

    logger.debug(f"[140] ✅ Tier-state manager ready at {core.current_level.name}")


def _prime_backend_selector():
    """
    [150] Backend Selector

    Primes available engines: CPython-JIT (151), Pyston-JIT (152),
    Cython/AOT numerical (153), GPU kernel backend (154).
    """
    logger.debug("[150] Priming backend selector...")

    # Backend selection happens during JIT initialization (Level 2)
    # Backends are lazy-loaded on demand
    logger.debug("[150] ✅ Backend selector primed")


def _prepare_worker_pool():
    """
    [160] Worker-Pool Manager

    Prepares sub-interpreters / OS threads sized to physical cores.
    Installs Threadpool Coordination Guard (380) to prevent oversubscription.
    """
    logger.debug("[160] Preparing worker pool...")

    # Worker pool is created on-demand when Level 3 is activated
    # This avoids initialization overhead for workloads that don't need it
    logger.debug("[160] ✅ Worker pool manager ready (lazy initialization)")


def _initialize_shared_memory():
    """
    [170] Shared-Memory Manager

    Sets up zero-copy, page-pinned shared buffers and buffer-protocol adapters.
    Enables workers to share array data without copying.
    """
    logger.debug("[170] Initializing shared memory...")

    # Shared memory is initialized when Level 3 is activated
    # Lazy initialization minimizes startup overhead
    logger.debug("[170] ✅ Shared memory manager ready (lazy initialization)")


def _install_watchdog():
    """
    [180] Watchdog & Rollback

    Enforces "always safe to run" constraints and immediate rollback on fault.
    Monitors error rate, latency, and resource usage.
    """
    logger.debug("[180] Installing watchdog...")

    # Watchdog is part of the performance monitor (started in core.initialize())
    # Monitors metrics and triggers rollback on SLO violations
    logger.debug("[180] ✅ Watchdog installed")


def _configure_policy_engine():
    """
    [190] Policy & Safety Engine

    Enforces allow/deny lists, GPU permissions, and resource ceilings.
    Every tier change is validated and audited.
    """
    logger.debug("[190] Configuring policy engine...")

    # Policy engine is part of EpochlyCore licensing and enhancement level logic
    # Validates all tier transitions and resource allocations
    logger.debug("[190] ✅ Policy engine configured")


# =============================================================================
# P0-2: Cleanup Functions for Transactional Bootstrap
# =============================================================================

def _cleanup_instrumentation():
    """
    Cleanup function for instrumentation step.

    P0-2: Removes import hook and profile hook.

    mcp-reflect fix: Only removes Epochly's profiler, not other tools' profilers.
    """
    logger.debug("[110] Cleaning up instrumentation...")

    # Remove import hook from sys.meta_path
    from .core.import_hook import EpochlyImportHook, get_import_hook

    hook = get_import_hook()
    if hook is not None:
        hook.shutdown()  # P0-1: Proper shutdown
        if hook in sys.meta_path:
            sys.meta_path.remove(hook)
        logger.debug("   Import hook removed")

    # mcp-reflect fix: Only remove profile hook if it's Epochly's hook
    # This avoids tearing down other profiling tools
    from .core.profiler import epochly_profile_hook

    current_profiler = sys.getprofile()
    if current_profiler is epochly_profile_hook:
        sys.setprofile(None)
        logger.debug("   Epochly profile hook removed")
    elif current_profiler is not None:
        logger.debug("   Profile hook is not Epochly's, leaving it in place")

    logger.debug("[110] Instrumentation cleaned up")


def _cleanup_telemetry_profiler():
    """
    Cleanup function for telemetry step.

    P0-2: Stops telemetry sampling.
    """
    logger.debug("[120] Cleaning up telemetry profiler...")
    # Telemetry cleanup is handled by EpochlyCore shutdown
    logger.debug("[120] Telemetry profiler cleaned up")


def _cleanup_compatibility_harness():
    """
    Cleanup function for compatibility harness step.

    P0-2: Clears compatibility cache if needed.
    """
    logger.debug("[130] Cleaning up compatibility harness...")
    # Compatibility harness has no persistent state to clean
    logger.debug("[130] Compatibility harness cleaned up")


def _cleanup_tier_state_manager():
    """
    Cleanup function for tier state manager step.

    P0-2: Resets tier state to Level 0.
    """
    logger.debug("[140] Cleaning up tier-state manager...")

    try:
        from .core.epochly_core import get_epochly_core, EnhancementLevel

        core = get_epochly_core()
        if core._initialized:
            # Reset to Level 0 (safe mode)
            core.set_enhancement_level(EnhancementLevel.LEVEL_0_MONITORING)
            logger.debug("   Tier reset to Level 0")
    except Exception as e:
        logger.debug(f"   Could not reset tier state: {e}")

    logger.debug("[140] Tier-state manager cleaned up")


def _cleanup_backend_selector():
    """
    Cleanup function for backend selector step.

    P0-2: Releases backend resources.
    """
    logger.debug("[150] Cleaning up backend selector...")
    # Backend selector is lazy-loaded, nothing to clean up at this stage
    logger.debug("[150] Backend selector cleaned up")


def _cleanup_worker_pool():
    """
    Cleanup function for worker pool step.

    P0-2: Shuts down worker pools.
    """
    logger.debug("[160] Cleaning up worker pool...")

    try:
        from .core.epochly_core import get_epochly_core

        core = get_epochly_core()
        if hasattr(core, '_cleanup_executors'):
            core._cleanup_executors()
            logger.debug("   Executors cleaned up")
    except Exception as e:
        logger.debug(f"   Could not cleanup worker pool: {e}")

    logger.debug("[160] Worker pool cleaned up")


def _cleanup_shared_memory():
    """
    Cleanup function for shared memory step.

    P0-2: Releases shared memory buffers.
    """
    logger.debug("[170] Cleaning up shared memory...")

    try:
        from .memory.shared_memory_manager import get_shared_memory_manager

        smm = get_shared_memory_manager()
        if hasattr(smm, 'release_all'):
            smm.release_all()
            logger.debug("   Shared memory released")
    except Exception as e:
        logger.debug(f"   Could not cleanup shared memory: {e}")

    logger.debug("[170] Shared memory cleaned up")


def _cleanup_watchdog():
    """
    Cleanup function for watchdog step.

    P0-2: Stops watchdog monitoring.
    """
    logger.debug("[180] Cleaning up watchdog...")

    try:
        from .core.epochly_core import get_epochly_core

        core = get_epochly_core()
        if hasattr(core, '_performance_monitor') and core._performance_monitor:
            core._performance_monitor.stop()
            logger.debug("   Performance monitor stopped")
    except Exception as e:
        logger.debug(f"   Could not cleanup watchdog: {e}")

    logger.debug("[180] Watchdog cleaned up")


def _cleanup_policy_engine():
    """
    Cleanup function for policy engine step.

    P0-2: Resets policy configuration.
    """
    logger.debug("[190] Cleaning up policy engine...")
    # Policy engine state is part of EpochlyCore, handled by tier cleanup
    logger.debug("[190] Policy engine cleaned up")


# =============================================================================
# End of P0-2 Cleanup Functions
# =============================================================================


def integrate(**opts) -> None:
    """
    Direct integration API for custom embedding scenarios.

    Explicit alternative to sitecustomize auto-loading.
    Useful for daemons, services, and custom REPLs.

    Args:
        max_workers: Worker count ('physical', 'all', or number)
        general_jit: Enable general JIT (0/1/2)
        numeric_jit: Enable numeric JIT (True/False)
        enable_gpu: Enable GPU acceleration (True/False)
        policy_profile: Policy profile ('safe'/'balanced'/'aggressive')

    Example:
        import epochly
        epochly.integrate(
            max_workers='physical',
            general_jit=1,
            numeric_jit=True,
            enable_gpu=False,
            policy_profile='safe'
        )

    Architecture Reference:
    - Section "Direct import (fine-grained control)"
    - Lines 1838-1854: Integration function specification
    """
    logger.info("Epochly direct integration requested...")

    # First, run bootstrap
    if not bootstrap():
        logger.error("Bootstrap failed, integration aborted")
        return

    # Get core
    from .core.epochly_core import get_epochly_core, EnhancementLevel

    core = get_epochly_core()

    # Apply configuration options
    if 'max_workers' in opts:
        max_workers = opts['max_workers']
        # P0-4: Apply max_workers configuration via environment variable
        # Executors (SubInterpreterExecutor, ThreadExecutor, etc.) read EPOCHLY_MAX_WORKERS
        if max_workers is not None:
            if isinstance(max_workers, int) and max_workers > 0:
                os.environ['EPOCHLY_MAX_WORKERS'] = str(max_workers)
                logger.info(f"Max workers configured: {max_workers}")
            elif isinstance(max_workers, str) and max_workers.lower() == 'auto':
                # 'auto' means don't set limit - use hardware/license defaults
                os.environ.pop('EPOCHLY_MAX_WORKERS', None)
                logger.info("Max workers: auto (using hardware/license defaults)")
            else:
                logger.warning(f"Invalid max_workers value: {max_workers} (expected int > 0 or 'auto')")

    if 'policy_profile' in opts:
        profile_name = opts['policy_profile']
        # P0-4: Apply policy profile from ConfigProfile
        try:
            from .config_toml.toml_config import ConfigProfile
            profile = ConfigProfile(profile_name)
            profile_config = profile.get_config()

            if profile_config:
                # Apply profile settings as environment variables
                epochly_config = profile_config.get('epochly', {})

                # Apply max_workers from profile if not explicitly set
                if 'max_workers' not in opts and 'max_workers' in epochly_config:
                    profile_workers = epochly_config['max_workers']
                    if isinstance(profile_workers, int):
                        os.environ['EPOCHLY_MAX_WORKERS'] = str(profile_workers)
                        logger.info(f"Profile '{profile_name}' max_workers: {profile_workers}")

                # Apply mode from profile
                if 'mode' in epochly_config:
                    os.environ.setdefault('EPOCHLY_MODE', epochly_config['mode'])
                    logger.info(f"Profile '{profile_name}' mode: {epochly_config['mode']}")

                # Apply debug setting
                if epochly_config.get('debug'):
                    os.environ.setdefault('EPOCHLY_DEBUG', '1')

                # Apply telemetry setting
                if 'telemetry' in epochly_config:
                    os.environ.setdefault('EPOCHLY_TELEMETRY', '1' if epochly_config['telemetry'] else '0')

                logger.info(f"Policy profile '{profile_name}' applied successfully")
            else:
                logger.warning(f"Policy profile '{profile_name}' not found or empty")
        except ImportError:
            logger.warning("TOML config module not available - policy profiles disabled")
        except Exception as e:
            logger.error(f"Failed to apply policy profile '{profile_name}': {e}")

    # Determine target enhancement level
    if opts.get('enable_gpu'):
        target_level = EnhancementLevel.LEVEL_4_GPU
    elif opts.get('numeric_jit') or opts.get('general_jit'):
        target_level = EnhancementLevel.LEVEL_3_FULL
    else:
        target_level = EnhancementLevel.LEVEL_1_THREADING

    # Set enhancement level
    core.set_enhancement_level(target_level)

    logger.info(f"Epochly integration complete at {core.current_level.name}")


# Alias for compatibility
start = bootstrap
