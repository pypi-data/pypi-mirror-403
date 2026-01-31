"""
Background Alert Worker (SPEC2 Task 4)

Moves drop alerts off the foreground monitoring thread to prevent
blocking. Subprocess calls can block for milliseconds, creating
feedback that worsens drop rates.

Architecture:
- Alert queue with bounded size
- Dedicated worker thread for alert emission
- Bounded retry/backoff on failures
- Structured logging instead of subprocess calls

Performance:
- Monitor loop remains responsive during alerts
- No blocking subprocess calls in critical path
- Graceful degradation under alert storms
"""

import logging
import threading
import time
from queue import Queue, Full, Empty
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert message."""
    level: AlertLevel
    message: str
    context: Dict[str, Any]
    timestamp: float
    retry_count: int = 0


class AlertWorker(threading.Thread):
    """
    Background worker for alert emission.

    Prevents blocking the monitoring critical path by handling
    alerts asynchronously in a dedicated thread.

    Example:
        worker = AlertWorker(max_queue_size=1000)
        worker.start()

        # From monitor loop (non-blocking)
        worker.enqueue_alert(AlertLevel.WARNING, "Queue saturated", {...})

        # Shutdown
        worker.stop()
    """

    def __init__(self, max_queue_size: int = 1000, max_retries: int = 3):
        """
        Initialize alert worker.

        Args:
            max_queue_size: Maximum alerts to queue
            max_retries: Maximum retry attempts per alert
        """
        # FIX: Use daemon=True to prevent hanging shutdown (like monitor thread)
        super().__init__(daemon=True, name="AlertWorker")

        self._alert_queue: Queue = Queue(maxsize=max_queue_size)
        self._max_retries = max_retries
        self._stop_event = threading.Event()
        self._running = False

        # Statistics
        self._alerts_processed = 0
        self._alerts_dropped = 0
        self._alerts_retried = 0

        logger.info(f"AlertWorker initialized (queue: {max_queue_size}, retries: {max_retries})")

    def enqueue_alert(self, level: AlertLevel, message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Enqueue alert for background emission (non-blocking).

        Args:
            level: Alert severity level
            message: Alert message
            context: Optional context dictionary

        Returns:
            True if enqueued, False if queue full
        """
        alert = Alert(
            level=level,
            message=message,
            context=context or {},
            timestamp=time.time()
        )

        try:
            self._alert_queue.put_nowait(alert)
            return True
        except Full:
            self._alerts_dropped += 1
            # Don't log here - would create recursion
            return False

    def run(self) -> None:
        """Background loop for alert emission."""
        self._running = True
        logger.info("AlertWorker started")

        while not self._stop_event.is_set():
            try:
                # Wait for alert with timeout
                alert = self._alert_queue.get(timeout=1.0)

                # Emit alert
                self._emit_alert(alert)
                self._alerts_processed += 1

            except Empty:
                # No alerts - continue waiting
                continue
            except Exception as e:
                logger.error(f"Error in AlertWorker loop: {e}")

        # Process remaining alerts before shutdown
        while not self._alert_queue.empty():
            try:
                alert = self._alert_queue.get_nowait()
                self._emit_alert(alert)
                self._alerts_processed += 1
            except Empty:
                break
            except Exception as e:
                logger.error(f"Error processing shutdown alerts: {e}")

        logger.info(f"AlertWorker stopped (processed: {self._alerts_processed}, "
                   f"dropped: {self._alerts_dropped}, retried: {self._alerts_retried})")
        self._running = False

    def _emit_alert(self, alert: Alert) -> None:
        """
        Emit alert using structured logging (not subprocess).

        Args:
            alert: Alert to emit
        """
        try:
            # Use Python logging instead of subprocess calls
            # This is much faster and doesn't block
            log_method = getattr(logger, alert.level.value)

            # Format message with context
            if alert.context:
                context_str = ", ".join(f"{k}={v}" for k, v in alert.context.items())
                full_message = f"{alert.message} ({context_str})"
            else:
                full_message = alert.message

            # Emit via logging
            log_method(full_message)

        except Exception as e:
            # Retry logic with backoff
            if alert.retry_count < self._max_retries:
                alert.retry_count += 1
                self._alerts_retried += 1

                # Exponential backoff
                backoff = 0.1 * (2 ** alert.retry_count)
                time.sleep(backoff)

                # Re-enqueue for retry
                try:
                    self._alert_queue.put_nowait(alert)
                except Full:
                    # Queue full - drop the retry
                    self._alerts_dropped += 1
            else:
                # Max retries exceeded
                logger.error(f"Alert emission failed after {self._max_retries} retries: {e}")

    def stop(self, timeout: float = 5.0) -> bool:
        """
        Stop alert worker and wait for shutdown.

        Args:
            timeout: Maximum time to wait for shutdown

        Returns:
            True if stopped cleanly, False if timeout
        """
        logger.info("Stopping AlertWorker...")
        self._stop_event.set()

        # Wait for thread to finish
        self.join(timeout=timeout)

        if self.is_alive():
            logger.warning(f"AlertWorker did not stop within {timeout}s")
            return False

        return True

    def get_stats(self) -> Dict[str, Any]:
        """
        Get worker statistics.

        Returns:
            Statistics dictionary
        """
        return {
            'alerts_processed': self._alerts_processed,
            'alerts_dropped': self._alerts_dropped,
            'alerts_retried': self._alerts_retried,
            'queue_size': self._alert_queue.qsize(),
            'running': self._running
        }
