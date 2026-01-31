"""
GPU Detection Refresh Scheduler (perf_fixes5.md Finding #4).

Periodic refresh to catch hot-plug events and GPU state changes.
"""

import threading
import time
import logging
from typing import Optional, Callable


class GPURefreshScheduler:
    """Scheduled refresh for GPU detection."""

    def __init__(self, refresh_interval: float = 300.0):
        """
        Initialize GPU refresh scheduler.

        Args:
            refresh_interval: Seconds between refreshes (default: 5 minutes)
        """
        self.refresh_interval = refresh_interval
        self.logger = logging.getLogger(__name__)
        self._stop_event = threading.Event()
        self._refresh_thread: Optional[threading.Thread] = None
        self._refresh_callback: Optional[Callable] = None

    def set_refresh_callback(self, callback: Callable) -> None:
        """Set callback to invoke on each refresh."""
        self._refresh_callback = callback

    def start(self) -> None:
        """Start refresh scheduler."""
        if self._refresh_thread and self._refresh_thread.is_alive():
            return

        self._stop_event.clear()
        self._refresh_thread = threading.Thread(
            target=self._refresh_loop,
            daemon=True,
            name="GPU-Refresh-Scheduler"
        )
        self._refresh_thread.start()
        self.logger.info(f"GPU refresh scheduler started (interval: {self.refresh_interval}s)")

    def stop(self) -> None:
        """Stop refresh scheduler."""
        if not self._refresh_thread:
            return

        self._stop_event.set()
        if self._refresh_thread.is_alive():
            self._refresh_thread.join(timeout=2.0)

    def _refresh_loop(self) -> None:
        """Refresh loop."""
        while not self._stop_event.wait(timeout=self.refresh_interval):
            try:
                if self._refresh_callback:
                    self._refresh_callback()
            except Exception as e:
                self.logger.error(f"GPU refresh failed: {e}")
