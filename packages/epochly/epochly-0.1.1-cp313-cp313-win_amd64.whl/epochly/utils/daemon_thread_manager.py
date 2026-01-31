"""
Daemon Thread Manager - Graceful shutdown for background threads.

Follows the same pattern as _SubinterpManager for reliable cleanup.
"""

import threading
import logging
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ManagedThread:
    """Wrapper for a managed daemon thread."""
    thread: threading.Thread
    stop_event: Optional[threading.Event] = None
    timeout: float = 2.0
    name: str = ""


class DaemonThreadManager:
    """
    Centralized manager for graceful daemon thread shutdown.

    Pattern from sub-interpreter manager:
    - Track all daemon threads
    - Signal shutdown via stop events
    - Join with timeout (don't hang forever)
    - Log warnings for threads that don't stop

    Critical for pytest compatibility where daemon threads cause deadlocks.
    """

    def __init__(self):
        self._threads: List[ManagedThread] = []
        self._lock = threading.Lock()
        self.logger = logger

    def register_thread(
        self,
        thread: threading.Thread,
        stop_event: Optional[threading.Event] = None,
        timeout: float = 2.0
    ) -> None:
        """
        Register a daemon thread for managed shutdown.

        Args:
            thread: The Thread object to manage
            stop_event: Optional Event to signal thread to stop
            timeout: Max seconds to wait for thread during shutdown
        """
        with self._lock:
            managed = ManagedThread(
                thread=thread,
                stop_event=stop_event,
                timeout=timeout,
                name=thread.name or "unnamed"
            )
            self._threads.append(managed)
            self.logger.debug(f"Registered daemon thread: {managed.name}")

    def shutdown_all(self, global_timeout: float = 10.0) -> None:
        """
        Shutdown all registered daemon threads gracefully.

        Args:
            global_timeout: Total time to spend shutting down all threads

        Returns:
            None. Logs warnings for threads that don't stop.
        """
        import time
        start_time = time.time()

        with self._lock:
            threads_copy = list(self._threads)
            self._threads.clear()

        self.logger.info(f"Shutting down {len(threads_copy)} daemon threads")

        for managed in threads_copy:
            # Check global timeout
            elapsed = time.time() - start_time
            if elapsed >= global_timeout:
                self.logger.warning(
                    f"Global shutdown timeout reached. "
                    f"{len([t for t in threads_copy if t.thread.is_alive()])} threads still alive"
                )
                break

            if not managed.thread.is_alive():
                continue

            # Signal stop if event provided
            if managed.stop_event:
                managed.stop_event.set()

            # Wait for thread with per-thread timeout
            remaining = min(managed.timeout, global_timeout - elapsed)
            if remaining > 0:
                managed.thread.join(timeout=remaining)

            # Log if thread didn't stop
            if managed.thread.is_alive():
                self.logger.warning(
                    f"Daemon thread '{managed.name}' did not stop within {managed.timeout}s"
                )

        self.logger.info("Daemon thread shutdown complete")

    def is_empty(self) -> bool:
        """Check if any threads are still registered."""
        with self._lock:
            return len(self._threads) == 0


# Global singleton
_global_manager = None
_manager_lock = threading.Lock()


def get_daemon_thread_manager() -> DaemonThreadManager:
    """Get the global daemon thread manager (singleton)."""
    global _global_manager
    if _global_manager is None:
        with _manager_lock:
            if _global_manager is None:
                _global_manager = DaemonThreadManager()
    return _global_manager
