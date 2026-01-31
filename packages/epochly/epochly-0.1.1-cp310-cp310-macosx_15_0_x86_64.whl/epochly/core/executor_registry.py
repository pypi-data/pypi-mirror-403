"""
Executor Registry - Centralized ProcessPoolExecutor lifecycle management.

CRITICAL PRINCIPLE: Everything must use the registry. No orphans allowed.

This module provides:
1. Centralized registration for all ProcessPoolExecutors
2. Unified cleanup function for deterministic shutdown
3. Orphan auditor that DETECTS (not masks) unregistered processes
4. atexit handler for process exit cleanup

Philosophy:
- Registry cleanup shuts down REGISTERED executors (intended behavior)
- Orphan auditor WARNS about unregistered processes (bug detection)
- We DO NOT silently kill orphans - that would mask bugs

Usage:
    from epochly.core.executor_registry import (
        register_executor,
        unregister_executor,
        shutdown_all_executors,
        audit_orphan_processes,
    )

    # When creating an executor
    executor = ProcessPoolExecutor(max_workers=4)
    register_executor(executor, name="my_feature_pool")

    # When done with an executor
    unregister_executor(executor)
    executor.shutdown()

    # At process exit (automatic via atexit)
    shutdown_all_executors()

    # To check for bugs (unregistered orphans)
    orphans = audit_orphan_processes()
    if orphans:
        logger.warning(f"Found {len(orphans)} orphan processes - investigate!")

CONTRACT:
- Caller MUST call unregister_executor() before manual shutdown
- Executor MUST NOT be shared across processes (registry is per-process)
- Registration IS thread-safe (can be called concurrently)
- Registration MUST happen before first submit()

Author: Epochly Development Team
Date: November 2025
"""

import os
import sys
import time
import atexit
import logging
import threading
import subprocess
import signal
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# =============================================================================
# REGISTRY DATA STRUCTURES
# =============================================================================

# The canonical registry - all executors MUST register here
# Using strong references so executors stay alive until explicit shutdown
_EXECUTOR_REGISTRY: Dict[int, 'RegisteredExecutor'] = {}  # id(executor) -> metadata
_REGISTRY_LOCK = threading.RLock()  # RLock for nested calls

# Rate limiting for orphan audit
_LAST_AUDIT_TIME = 0.0
_MIN_AUDIT_INTERVAL = 30.0  # Don't audit more than once per 30s

# Track statistics
_STATS = {
    'total_registered': 0,
    'total_unregistered': 0,
    'total_shutdown': 0,
    'orphans_detected': 0,
    'shutdown_errors': [],  # Track errors for diagnostics
}


@dataclass
class RegisteredExecutor:
    """Metadata for a registered executor."""
    executor: ProcessPoolExecutor
    name: str
    registered_at: float
    registered_by: str  # Module/function that registered
    max_workers: int
    shutdown_at: Optional[float] = None  # Track shutdown timing


# =============================================================================
# REGISTRATION FUNCTIONS
# =============================================================================

def register_executor(
    executor: ProcessPoolExecutor,
    name: Optional[str] = None,
    registered_by: Optional[str] = None
) -> None:
    """
    Register a ProcessPoolExecutor in the global registry.

    CRITICAL: All executors created by Epochly MUST call this function.
    Unregistered executors will be flagged by audit_orphan_processes().

    Args:
        executor: The ProcessPoolExecutor to register
        name: Human-readable name for logging (default: auto-generated)
        registered_by: Module/function that registered (default: auto-detected)
    """
    # Accept ProcessPoolExecutor OR ForkingProcessExecutor (Epochly's custom executor)
    # ForkingProcessExecutor doesn't inherit from ProcessPoolExecutor but has same interface
    valid_types = (ProcessPoolExecutor,)
    try:
        from epochly.plugins.executor.process_pool import ForkingProcessExecutor
        valid_types = (ProcessPoolExecutor, ForkingProcessExecutor)
    except ImportError:
        pass  # ForkingProcessExecutor not available

    if not isinstance(executor, valid_types):
        raise TypeError(f"Expected ProcessPoolExecutor or ForkingProcessExecutor, got {type(executor).__name__}")

    executor_id = id(executor)

    # Auto-detect caller if not provided
    if registered_by is None:
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller = frame.f_back
            registered_by = f"{caller.f_code.co_filename}:{caller.f_lineno}"

    # Generate name if not provided
    if name is None:
        name = f"executor_{executor_id}"

    # Get max_workers from executor
    max_workers = getattr(executor, '_max_workers', -1)

    with _REGISTRY_LOCK:
        if executor_id in _EXECUTOR_REGISTRY:
            existing = _EXECUTOR_REGISTRY[executor_id]
            logger.debug(f"Executor {name} already registered as {existing.name}")
            return

        _EXECUTOR_REGISTRY[executor_id] = RegisteredExecutor(
            executor=executor,
            name=name,
            registered_at=time.time(),
            registered_by=registered_by,
            max_workers=max_workers,
        )
        _STATS['total_registered'] += 1

        logger.debug(f"Registered executor '{name}' (id={executor_id}, workers={max_workers}, total={len(_EXECUTOR_REGISTRY)})")


def unregister_executor(executor: ProcessPoolExecutor) -> bool:
    """
    Unregister a ProcessPoolExecutor from the global registry.

    Call this BEFORE shutting down an executor to prevent double-shutdown
    during atexit cleanup.

    Args:
        executor: The ProcessPoolExecutor to unregister

    Returns:
        True if executor was found and unregistered, False otherwise
    """
    executor_id = id(executor)

    with _REGISTRY_LOCK:
        if executor_id not in _EXECUTOR_REGISTRY:
            logger.debug(f"Executor {executor_id} not in registry (already unregistered?)")
            return False

        entry = _EXECUTOR_REGISTRY.pop(executor_id)
        _STATS['total_unregistered'] += 1

        logger.debug(f"Unregistered executor '{entry.name}' (remaining={len(_EXECUTOR_REGISTRY)})")
        return True


def get_registered_count() -> int:
    """Return the number of currently registered executors."""
    with _REGISTRY_LOCK:
        return len(_EXECUTOR_REGISTRY)


def get_registry_stats() -> Dict:
    """Return registry statistics."""
    with _REGISTRY_LOCK:
        return {
            **_STATS,
            'currently_registered': len(_EXECUTOR_REGISTRY),
        }


# =============================================================================
# SHUTDOWN FUNCTIONS
# =============================================================================

def _shutdown_executor_with_timeout(
    executor: ProcessPoolExecutor,
    name: str,
    timeout: float,
    cancel_futures: bool = True
) -> bool:
    """
    Shutdown an executor with a hard timeout.

    Args:
        executor: The executor to shutdown
        name: Name for logging
        timeout: Maximum time to wait for shutdown
        cancel_futures: Whether to cancel pending futures

    Returns:
        True if shutdown completed within timeout, False otherwise
    """
    done_event = threading.Event()

    def do_shutdown():
        try:
            # Check if executor supports cancel_futures (ForkingProcessExecutor doesn't)
            import inspect
            try:
                shutdown_sig = inspect.signature(executor.shutdown)
                supports_cancel_futures = 'cancel_futures' in shutdown_sig.parameters
            except (ValueError, TypeError):
                # Could not inspect (e.g., extension types); default to safe call
                supports_cancel_futures = False

            # Python 3.9+ ProcessPoolExecutor supports cancel_futures
            if supports_cancel_futures and sys.version_info >= (3, 9):
                executor.shutdown(wait=True, cancel_futures=cancel_futures)
            else:
                # ForkingProcessExecutor or older Python - just use wait
                executor.shutdown(wait=True)
        except Exception as e:
            logger.warning(f"Error during executor '{name}' shutdown: {e}")
        finally:
            done_event.set()

    thread = threading.Thread(target=do_shutdown, daemon=True)
    thread.start()

    if done_event.wait(timeout):
        return True
    else:
        logger.warning(f"Executor '{name}' shutdown timed out after {timeout}s")
        return False


def shutdown_all_executors(
    wait: bool = False,
    cancel_futures: bool = True,
    graceful_timeout: float = 5.0
) -> int:
    """
    Shutdown all registered ProcessPoolExecutors.

    This is the canonical cleanup function. Called automatically via atexit,
    and can be called manually for deterministic cleanup.

    Args:
        wait: Whether to wait for pending futures (default: False for fast exit)
        cancel_futures: Whether to cancel pending futures (default: True)
        graceful_timeout: Timeout for graceful shutdown before force-killing

    Returns:
        Number of executors shut down
    """
    with _REGISTRY_LOCK:
        if not _EXECUTOR_REGISTRY:
            logger.debug("No executors to shutdown")
            return 0

        entries = list(_EXECUTOR_REGISTRY.values())
        logger.info(f"Shutting down {len(entries)} registered executor(s)")

    shutdown_count = 0
    errors = []

    for entry in entries:
        try:
            executor = entry.executor
            name = entry.name

            logger.debug(f"Shutting down executor '{name}'")

            # Mark shutdown time
            entry.shutdown_at = time.time()

            if wait:
                # Use timeout-protected shutdown
                success = _shutdown_executor_with_timeout(
                    executor, name, graceful_timeout, cancel_futures
                )
                if not success:
                    # Force-kill workers if timeout exceeded
                    _force_terminate_executor_workers(executor, name)
            else:
                # Quick shutdown without waiting
                # Check if executor supports cancel_futures (ForkingProcessExecutor doesn't)
                import inspect
                try:
                    shutdown_sig = inspect.signature(executor.shutdown)
                    supports_cancel_futures = 'cancel_futures' in shutdown_sig.parameters
                except (ValueError, TypeError):
                    # Could not inspect (e.g., extension types); default to safe call
                    supports_cancel_futures = False

                if supports_cancel_futures and sys.version_info >= (3, 9):
                    executor.shutdown(wait=False, cancel_futures=cancel_futures)
                else:
                    executor.shutdown(wait=False)

            shutdown_count += 1
            logger.debug(f"Executor '{name}' shutdown complete")

        except Exception as e:
            errors.append((entry.name, str(e)))
            logger.warning(f"Error shutting down executor '{entry.name}': {e}")

    # Clear the registry AFTER all shutdown attempts
    with _REGISTRY_LOCK:
        _EXECUTOR_REGISTRY.clear()
        _STATS['total_shutdown'] += shutdown_count
        if errors:
            _STATS['shutdown_errors'].extend(errors)

    logger.info(f"Shutdown complete: {shutdown_count} executor(s)")
    return shutdown_count


def _wait_for_executor_workers(executor: ProcessPoolExecutor, timeout: float) -> List:
    """
    Wait for executor worker processes to terminate.

    Returns list of processes that are still alive after timeout.
    """
    processes_dict = getattr(executor, '_processes', None)
    if not processes_dict:
        return []

    procs = list(processes_dict.values())
    deadline = time.monotonic() + timeout

    # Phase 1: Wait for graceful termination
    while procs and time.monotonic() < deadline:
        still_alive = []
        for p in procs:
            p.join(timeout=0.1)
            if p.is_alive():
                still_alive.append(p)
        procs = still_alive

    return procs


def _force_terminate_executor_workers(executor: ProcessPoolExecutor, name: str) -> None:
    """
    Force-terminate executor workers with escalation (SIGTERM -> SIGKILL).
    """
    processes_dict = getattr(executor, '_processes', None)
    if not processes_dict:
        return

    procs = [p for p in processes_dict.values() if p.is_alive()]
    if not procs:
        return

    # Phase 1: SIGTERM
    logger.warning(f"Force-terminating {len(procs)} workers from '{name}' with SIGTERM")
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass

    # Brief wait for SIGTERM to take effect
    time.sleep(0.5)

    # Phase 2: SIGKILL for stragglers
    still_alive = [p for p in procs if p.is_alive()]
    if still_alive:
        logger.warning(f"Escalating to SIGKILL for {len(still_alive)} stuck workers from '{name}'")
        for p in still_alive:
            try:
                p.kill()
            except Exception:
                pass


def force_emergency_shutdown() -> None:
    """
    Emergency shutdown that doesn't wait.

    Call this when process must exit immediately (SIGTERM handler, etc).
    Does not wait for graceful termination - immediately terminates all workers.
    """
    logger.critical("EMERGENCY SHUTDOWN initiated")

    with _REGISTRY_LOCK:
        executors = list(_EXECUTOR_REGISTRY.values())
        _EXECUTOR_REGISTRY.clear()

    # Don't wait - just terminate everything
    for entry in executors:
        try:
            _force_terminate_executor_workers(entry.executor, entry.name)
        except Exception:
            pass

    logger.critical(f"EMERGENCY SHUTDOWN completed: {len(executors)} executor(s)")


# =============================================================================
# ORPHAN DETECTION (AUDIT, NOT KILL)
# =============================================================================

@dataclass
class OrphanProcess:
    """Information about a potentially orphaned process."""
    pid: int
    ppid: int
    command: str
    reason: str


def _get_registered_worker_pids() -> Set[int]:
    """Get PIDs of all registered executor workers."""
    pids = set()

    with _REGISTRY_LOCK:
        for entry in _EXECUTOR_REGISTRY.values():
            executor = entry.executor
            processes_dict = getattr(executor, '_processes', None)
            if processes_dict:
                for worker in processes_dict.values():
                    if hasattr(worker, 'pid') and worker.pid:
                        pids.add(worker.pid)

    return pids


def audit_orphan_processes(force: bool = False) -> List[OrphanProcess]:
    """
    Detect potential orphan processes related to Epochly.

    CRITICAL: This function DETECTS and LOGS orphans - it does NOT kill them.
    Killing orphans silently would mask bugs. We want to KNOW about them.

    Args:
        force: If True, bypass rate limiting

    Returns:
        List of OrphanProcess entries for investigation
    """
    global _LAST_AUDIT_TIME

    # Rate limiting to prevent log spam during rapid executor churn
    now = time.time()
    if not force and (now - _LAST_AUDIT_TIME) < _MIN_AUDIT_INTERVAL:
        logger.debug(f"Skipping audit (last run {now - _LAST_AUDIT_TIME:.1f}s ago)")
        return []

    _LAST_AUDIT_TIME = now

    orphans = []
    our_pid = os.getpid()

    # Get PIDs of registered executor workers - these are NOT orphans
    registered_pids = _get_registered_worker_pids()

    # Patterns that indicate Epochly-related processes
    patterns = [
        'multiprocessing.forkserver',
        'multiprocessing.spawn',
        'multiprocessing.resource_tracker',
        'epochly',
    ]

    try:
        result = subprocess.run(
            ['ps', '-eo', 'pid,ppid,command'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            logger.warning("Failed to run ps command for orphan audit")
            return orphans

        for line in result.stdout.strip().split('\n')[1:]:  # Skip header
            parts = line.split(None, 2)
            if len(parts) < 3:
                continue

            try:
                pid = int(parts[0])
                ppid = int(parts[1])
                command = parts[2]
            except (ValueError, IndexError):
                continue

            # Skip our own process
            if pid == our_pid or pid == os.getppid():
                continue

            # Skip registered executor workers - they are NOT orphans
            if pid in registered_pids:
                continue

            # Check if it matches our patterns
            if not any(p in command.lower() for p in patterns):
                continue

            # Check if it's orphaned
            reason = None

            if ppid == 1:
                reason = "orphaned (PPID=1)"
            elif not _process_exists(ppid):
                reason = f"parent {ppid} dead"

            if reason:
                orphans.append(OrphanProcess(
                    pid=pid,
                    ppid=ppid,
                    command=command,
                    reason=reason
                ))

    except Exception as e:
        logger.warning(f"Error during orphan audit: {e}")

    if orphans:
        # Update stats under lock for thread-safety
        with _REGISTRY_LOCK:
            _STATS['orphans_detected'] += len(orphans)
        logger.warning(
            f"ORPHAN AUDIT: Found {len(orphans)} potential orphan(s). "
            "This may indicate a bug - investigate! PIDs: "
            f"{[o.pid for o in orphans]}"
        )

    return orphans


def _process_exists(pid: int) -> bool:
    """Check if a process exists."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


# =============================================================================
# HEALTH MONITORING & METRICS
# =============================================================================

def get_health_status() -> Dict[str, Any]:
    """
    Get health status of registry and executors.

    Returns:
        Dict with health information including:
        - healthy: Overall health status
        - registered_count: Number of registered executors
        - unhealthy_executors: List of executors that failed health check
        - statistics: Registry statistics
    """
    with _REGISTRY_LOCK:
        health = {
            'healthy': True,
            'registered_count': len(_EXECUTOR_REGISTRY),
            'unhealthy_executors': [],
            'statistics': get_registry_stats()
        }

        # Check each executor (lightweight - just check if it has processes)
        for executor_id, entry in _EXECUTOR_REGISTRY.items():
            try:
                # Check if executor is still functional
                executor = entry.executor
                # Check if _shutdown is set (executor was shut down externally)
                if getattr(executor, '_shutdown_thread', None) is not None:
                    if not executor._shutdown_thread.is_alive():
                        # Executor was shut down
                        health['healthy'] = False
                        health['unhealthy_executors'].append({
                            'id': executor_id,
                            'name': entry.name,
                            'error': 'Executor was shut down externally'
                        })
            except Exception as e:
                health['healthy'] = False
                health['unhealthy_executors'].append({
                    'id': executor_id,
                    'name': entry.name,
                    'error': str(e)
                })

        return health


def export_metrics() -> Dict[str, float]:
    """
    Export metrics for monitoring systems (Prometheus, etc).

    Returns:
        Dict of metric name -> value
    """
    with _REGISTRY_LOCK:
        return {
            'epochly_executors_registered': float(len(_EXECUTOR_REGISTRY)),
            'epochly_executors_total_registered': float(_STATS['total_registered']),
            'epochly_executors_total_unregistered': float(_STATS['total_unregistered']),
            'epochly_executors_total_shutdown': float(_STATS['total_shutdown']),
            'epochly_orphans_detected_total': float(_STATS['orphans_detected']),
            'epochly_shutdown_errors_total': float(len(_STATS['shutdown_errors'])),
        }


# =============================================================================
# ATEXIT HANDLER
# =============================================================================

_atexit_registered = False


def _atexit_cleanup() -> None:
    """
    Cleanup handler called at process exit.

    Shuts down all registered executors to prevent:
    1. Python 3.13+ non-daemon manager thread blocking exit
    2. Orphaned worker processes
    3. Resource leaks
    """
    try:
        # Run audit first (for logging only) - force to bypass rate limit at exit
        orphans = audit_orphan_processes(force=True)
        if orphans:
            print(f"[epochly] WARNING: {len(orphans)} orphan process(es) detected at exit", flush=True)

        # Shutdown all registered executors
        count = shutdown_all_executors(wait=False, cancel_futures=True)
        if count > 0:
            print(f"[epochly] Shutdown {count} executor(s) at exit", flush=True)

    except Exception as e:
        print(f"[epochly] Error in atexit cleanup: {e}", flush=True)


def ensure_atexit_registered() -> None:
    """Ensure the atexit handler is registered (idempotent)."""
    global _atexit_registered
    if not _atexit_registered:
        atexit.register(_atexit_cleanup)
        _atexit_registered = True
        logger.debug("Registered atexit cleanup handler")


# Auto-register atexit handler on module import
ensure_atexit_registered()


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    'register_executor',
    'unregister_executor',
    'shutdown_all_executors',
    'audit_orphan_processes',
    'get_registered_count',
    'get_registry_stats',
    'get_health_status',
    'export_metrics',
    'force_emergency_shutdown',
    'RegisteredExecutor',
    'OrphanProcess',
    # Internal but exposed for testing
    '_EXECUTOR_REGISTRY',
    '_REGISTRY_LOCK',
    '_STATS',
]
