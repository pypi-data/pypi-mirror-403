"""
In-Flight Work Tracking System

Tracks active work items for graceful shutdown with proper timeout handling.
Required for SIGTERM graceful shutdown guarantee in production environments.

Thread-safe tracking with no race conditions or deadlocks.
"""

import threading
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class WorkItem:
    """Represents an active work item being tracked."""
    task_id: str
    description: str
    start_time: float

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time since work started (in seconds)."""
        return time.time() - self.start_time


class InFlightTracker:
    """
    Thread-safe tracking of active work items for graceful shutdown.

    This class enables graceful shutdown by:
    1. Tracking all active work items with unique IDs
    2. Providing wait_for_completion() to drain work on shutdown
    3. Timeout protection to prevent indefinite waits
    4. Thread-safe concurrent access without deadlocks

    Usage:
        tracker = InFlightTracker()

        # Register work
        task_id = str(uuid.uuid4())
        tracker.register_work(task_id, "Processing batch 123")

        try:
            # Do work
            process_batch(123)
        finally:
            # Always complete, even on error
            tracker.complete_work(task_id)

        # On shutdown
        if tracker.wait_for_completion(timeout=30):
            print("All work drained cleanly")
        else:
            print("Timeout - some work may be incomplete")

    Thread Safety:
        All methods are thread-safe and can be called concurrently
        from multiple workers without coordination.
    """

    def __init__(self):
        """Initialize the in-flight work tracker."""
        self._active_work: Dict[str, WorkItem] = {}
        self._lock = threading.Lock()

    def register_work(self, task_id: str, description: str) -> None:
        """
        Register a new work item as in-flight.

        Args:
            task_id: Unique identifier for this work item
            description: Human-readable description of the work

        Thread Safety:
            Safe to call from multiple threads concurrently.
        """
        with self._lock:
            self._active_work[task_id] = WorkItem(
                task_id=task_id,
                description=description,
                start_time=time.time()
            )

    def complete_work(self, task_id: str) -> None:
        """
        Mark work item as complete and remove from tracking.

        Args:
            task_id: Unique identifier for the completed work

        Thread Safety:
            Safe to call from multiple threads concurrently.
            Idempotent - safe to call multiple times for same task_id.
        """
        with self._lock:
            self._active_work.pop(task_id, None)

    def get_active_work(self) -> List[WorkItem]:
        """
        Get list of currently active work items.

        Returns:
            List of WorkItem objects (snapshot at call time)

        Thread Safety:
            Returns a snapshot. The actual active work may change
            immediately after this call returns.
        """
        with self._lock:
            return list(self._active_work.values())

    def get_active_count(self) -> int:
        """
        Get count of active work items.

        Returns:
            Number of work items currently in flight

        Thread Safety:
            Safe to call from multiple threads concurrently.
        """
        with self._lock:
            return len(self._active_work)

    def wait_for_completion(self, timeout: float = 30.0) -> bool:
        """
        Wait for all in-flight work to complete.

        Polls active work count every 100ms until either:
        - All work completes (returns True)
        - Timeout expires (returns False)

        Args:
            timeout: Maximum time to wait in seconds (default: 30)

        Returns:
            True if all work completed within timeout
            False if timeout expired with work still in flight

        Thread Safety:
            Safe to call from multiple threads, but typically called
            only from shutdown handler.

        Performance:
            Polls every 100ms - balances responsiveness with CPU usage.
            For 30s timeout, performs ~300 checks maximum.
        """
        start_time = time.time()

        while True:
            # Check if all work complete
            with self._lock:
                if len(self._active_work) == 0:
                    return True

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                return False

            # Sleep briefly before next check
            # 100ms balances responsiveness with CPU usage
            time.sleep(0.1)

    def get_status(self) -> Dict[str, any]:
        """
        Get current status summary for monitoring/debugging.

        Returns:
            Dictionary containing:
            - active_count: Number of active work items
            - oldest_task_age: Age of oldest task in seconds (or None)
            - active_tasks: List of task descriptions

        Thread Safety:
            Returns a snapshot. Status may change immediately after return.
        """
        with self._lock:
            active_work = list(self._active_work.values())

        if not active_work:
            return {
                'active_count': 0,
                'oldest_task_age': None,
                'active_tasks': []
            }

        oldest_age = max(item.elapsed_time for item in active_work)

        return {
            'active_count': len(active_work),
            'oldest_task_age': oldest_age,
            'active_tasks': [item.description for item in active_work]
        }
