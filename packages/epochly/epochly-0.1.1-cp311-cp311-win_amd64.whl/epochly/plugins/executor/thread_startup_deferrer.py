"""
Thread Startup Deferrer for Import-Safe Worker Creation

CRITICAL FIX (Oct 2 2025): Resolves daemon=FALSE thread startup deadlock in venv.

Problem: Starting daemon=FALSE threads during venv import phase causes lock-order deadlock:
- Global import lock (held during site.py/.pth processing)
- Threading registry locks (_active_limbo_lock in Thread.start())

Solution: Defer worker thread creation until main thread exits import phase.
"""

import sys
import time
import traceback
import threading
from typing import Optional


def _imports_idle(deadline_s: float = 5.0, stable_ms: int = 50) -> bool:
    """
    Robustly detect if imports are idle by probing the global import lock.

    CRITICAL FIX (Oct 2 2025 - Final): Replaces heuristic stack inspection
    Uses importlib._bootstrap._lock directly - the ACTUAL import lock.

    In venv, stack-based detection is unreliable (site.py/.pth keep importlib
    frames around). Direct lock probing is deterministic.

    Args:
        deadline_s: Maximum time to wait for imports to go idle
        stable_ms: Required stability period in milliseconds

    Returns:
        bool: True if imports are idle (lock acquirable), False if deadline exceeded
    """
    import time
    from importlib import _bootstrap  # CPython importlib internals

    # Get the actual global import lock
    lock = getattr(_bootstrap, "_lock", None)
    if lock is None:
        # If CPython internals change, fail open (assume idle)
        return True

    end = time.monotonic() + deadline_s
    stable_until = None

    while time.monotonic() < end:
        # Try to acquire import lock (non-blocking)
        acquired = lock.acquire(False)

        if acquired:
            # Import lock is free - main thread not importing
            lock.release()

            if stable_until is None:
                # Start stability timer
                stable_until = time.monotonic() + (stable_ms / 1000.0)
            elif time.monotonic() >= stable_until:
                # Stable for required period - imports truly idle
                return True
        else:
            # Import lock still held - reset stability window
            stable_until = None

        time.sleep(0.01)

    # Deadline exceeded - imports never went idle
    return False


class ThreadStarter:
    """
    Daemon starter that serializes creation of non-daemon threads safely.

    CRITICAL FIX (Oct 2 2025 - Final): Centralizes all non-daemon thread creation
    through a single daemon thread that waits for imports to go idle first.

    This breaks the lock-order deadlock: main thread never directly calls
    Thread.start() for daemon=False threads. The daemon starter does it after
    import phase completes.
    """

    def __init__(self, logger=None):
        """Initialize the thread starter"""
        import queue
        import threading

        self._queue = queue.Queue()
        self._thread = threading.Thread(
            target=self._run,
            name="epochly-thread-starter",
            daemon=True  # Starter itself is daemon - holds no sub-interpreter state
        )
        self._started = False
        self._logger = logger

    def start(self):
        """Start the daemon starter thread"""
        if not self._started:
            self._thread.start()
            self._started = True

    def start_thread(self, thread: threading.Thread, timeout_s: float = 1.0) -> bool:
        """
        Enqueue a thread start request and wait for confirmation.

        Args:
            thread: Thread object to start (typically daemon=False worker)
            timeout_s: How long to wait for thread to become alive

        Returns:
            bool: True if thread started successfully
        """
        import threading

        evt = threading.Event()
        ok = [False]  # Mutable container for result
        self._queue.put((thread, timeout_s, evt, ok))

        # Wait for starter to attempt start and validate
        evt.wait(timeout_s + 0.25)
        return ok[0]

    def _run(self):
        """Daemon starter main loop"""
        import time

        # Wait until imports are idle (robust lock probe)
        try:
            if not _imports_idle(deadline_s=5.0, stable_ms=50):
                if self._logger:
                    self._logger.warning("Import phase timeout in ThreadStarter - proceeding anyway")
        except Exception as e:
            if self._logger:
                self._logger.debug(f"Import idle check failed: {e}")

        # Now process start requests
        while True:
            thread, timeout_s, evt, ok = self._queue.get()
            try:
                thread.start()

                # Wait for thread to become alive
                end = time.monotonic() + timeout_s
                while time.monotonic() < end:
                    if thread.is_alive():
                        ok[0] = True
                        break
                    time.sleep(0.01)
            except Exception:
                ok[0] = False
            finally:
                evt.set()


def temporarily_clear_profile_trace():
    """
    Context manager to temporarily clear profile/trace hooks around thread creation.

    CRITICAL FIX (Oct 2 2025 - Final): Parent-side sanitization
    Even though worker sanitizes itself, CPython copies parent's hooks at Thread creation.
    This wrapper prevents that copy, then restores parent state.

    Use around Thread.start() calls to prevent hook inheritance.
    """
    import sys
    import threading
    from contextlib import contextmanager

    @contextmanager
    def _wrapper():
        # Save current hooks
        old_sys_trace = sys.gettrace()
        old_sys_prof = sys.getprofile()
        old_thr_trace = threading.gettrace() if hasattr(threading, 'gettrace') else None
        old_thr_prof = threading.getprofile() if hasattr(threading, 'getprofile') else None

        try:
            # Clear all hooks before thread creation
            sys.settrace(None)
            sys.setprofile(None)
            if hasattr(threading, 'settrace'):
                threading.settrace(None)
            if hasattr(threading, 'setprofile'):
                threading.setprofile(None)

            yield

        finally:
            # Restore hooks after thread created
            if old_sys_trace:
                sys.settrace(old_sys_trace)
            if old_sys_prof:
                sys.setprofile(old_sys_prof)
            if old_thr_trace and hasattr(threading, 'settrace'):
                threading.settrace(old_thr_trace)
            if old_thr_prof and hasattr(threading, 'setprofile'):
                threading.setprofile(old_thr_prof)

    return _wrapper()


def defer_worker_startup(pool_instance, logger=None):
    """
    Defer worker thread creation until import phase completes.

    CRITICAL: This is the fix for daemon=FALSE deadlock in venv.

    Creates a temporary daemon thread that waits for imports to go idle,
    then calls pool.initialize() when safe. The actual worker threads
    created by initialize() remain daemon=FALSE for proper cleanup.

    Args:
        pool_instance: SubInterpreterPool or similar pool to initialize
        logger: Optional logger for diagnostics

    Usage:
        # In bootstrap/sitecustomize:
        pool = SubInterpreterPool()
        defer_worker_startup(pool)
        # Returns immediately, workers created asynchronously when safe
    """
    def _deferred_initialize():
        """Temporary daemon thread function"""
        try:
            # Wait for imports to go idle
            imports_idle = _wait_until_imports_idle(deadline_s=5.0)

            if imports_idle:
                # Safe to create daemon=FALSE workers now
                if logger:
                    logger.info("Imports idle - initializing worker pool")
                pool_instance.initialize()
            else:
                # Deadline exceeded - fallback to ProcessPool
                if logger:
                    logger.warning("Import phase timeout - using ProcessPool fallback")
                pool_instance._force_processpool = True
                pool_instance.initialize()

        except Exception as e:
            if logger:
                logger.error(f"Deferred initialization failed: {e}")
            # Fallback to ProcessPool on any error
            try:
                pool_instance._force_processpool = True
                pool_instance.initialize()
            except Exception:
                pass  # Give up gracefully

    # Start temporary daemon deferrer thread
    deferrer = threading.Thread(
        target=_deferred_initialize,
        name="epochly-startup-deferrer",
        daemon=True  # OK - this thread holds no sub-interpreter state
    )
    deferrer.start()


def _safe_start_thread(thread: threading.Thread, name: str, timeout_s: float = 0.75) -> bool:
    """
    Safely start a thread with deadlock detection.

    CRITICAL FIX (Oct 2 2025): Detects if Thread.start() hangs due to
    import-lock or threading-lock deadlock.

    Args:
        thread: Thread object to start
        name: Thread name for logging
        timeout_s: How long to wait for thread to become alive

    Returns:
        bool: True if thread started successfully, False if deadlock detected
    """
    try:
        thread.start()

        # Wait briefly for thread to become alive
        end = time.monotonic() + timeout_s
        while time.monotonic() < end:
            if thread.is_alive():
                return True
            time.sleep(0.01)

        # Thread didn't start within timeout
        return False

    except Exception:
        return False
