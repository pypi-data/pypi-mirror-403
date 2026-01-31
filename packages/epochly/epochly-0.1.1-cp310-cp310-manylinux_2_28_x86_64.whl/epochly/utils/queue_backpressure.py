"""
Adaptive Queue Backpressure (perf_fixes5.md Finding #2).

Prevents latency collapse under overload with bounded queues
and rejection policies.
"""

import threading
import time
import logging
from typing import Any, Optional
from queue import Queue, Full
from dataclasses import dataclass


@dataclass
class BackpressureConfig:
    """Configuration for queue backpressure."""
    max_queue_size: int = 1000
    rejection_policy: str = "block"  # 'block', 'drop_oldest', 'reject'
    latency_threshold_ms: float = 100.0  # Trigger backpressure above this


class BackpressureQueue:
    """Queue with adaptive backpressure."""

    def __init__(self, config: Optional[BackpressureConfig] = None):
        self.config = config or BackpressureConfig()
        self._queue = Queue(maxsize=self.config.max_queue_size)
        self._logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self._enqueue_times = {}  # track enqueue times for latency
        self._drop_count = 0

    def put(self, item: Any, timeout: Optional[float] = None) -> bool:
        """
        Put item with backpressure handling.

        Returns:
            True if item enqueued, False if rejected
        """
        try:
            if self.config.rejection_policy == "block":
                self._queue.put(item, timeout=timeout)
                self._enqueue_times[id(item)] = time.time()
                return True

            elif self.config.rejection_policy == "drop_oldest":
                try:
                    self._queue.put_nowait(item)
                    self._enqueue_times[id(item)] = time.time()
                    return True
                except Full:
                    # Drop oldest item and add new one
                    try:
                        oldest = self._queue.get_nowait()
                        self._enqueue_times.pop(id(oldest), None)
                        self._queue.put_nowait(item)
                        self._enqueue_times[id(item)] = time.time()
                        with self._lock:
                            self._drop_count += 1
                        return True
                    except Exception:
                        return False

            elif self.config.rejection_policy == "reject":
                try:
                    self._queue.put_nowait(item)
                    self._enqueue_times[id(item)] = time.time()
                    return True
                except Full:
                    return False

        except Exception as e:
            self._logger.error(f"Queue put failed: {e}")
            return False

    def get(self, timeout: Optional[float] = None) -> Optional[Any]:
        """Get item from queue."""
        item = self._queue.get(timeout=timeout)
        self._enqueue_times.pop(id(item), None)
        return item

    def qsize(self) -> int:
        """Get approximate queue size."""
        return self._queue.qsize()

    def get_drop_count(self) -> int:
        """Get count of dropped items."""
        with self._lock:
            return self._drop_count
