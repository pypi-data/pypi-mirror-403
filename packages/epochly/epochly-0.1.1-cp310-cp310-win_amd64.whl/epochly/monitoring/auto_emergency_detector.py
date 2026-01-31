"""
Automatic Emergency Detector for Epochly.

Monitors system health in a background thread and automatically triggers
emergency disable when degradation is detected. This ensures users don't
need to manually detect and respond to system failures.

Safety Requirement (R-SAFE-04): Epochly MUST automatically disable itself
if degradation is detected.

Trigger Conditions:
- Global error rate > 50% (ERROR_RATE_THRESHOLD)
- Memory allocation failures > threshold (MEMORY_FAILURE_THRESHOLD)
- Processing latency > max threshold (LATENCY_THRESHOLD_MS)

Integration:
- Uses EnhancementProgressionManager for error rate monitoring
- Sets EPOCHLY_EMERGENCY_DISABLE=1 environment variable
- Calls emergency_disable_callback for cleanup

Author: Epochly Development Team
Date: January 2026
"""

import logging
import os
import threading
import time
from typing import Callable, Optional, Protocol

logger = logging.getLogger(__name__)

# Environment variable constant for emergency disable flag
EMERGENCY_DISABLE_ENV_VAR = "EPOCHLY_EMERGENCY_DISABLE"


class ErrorRateProvider(Protocol):
    """Protocol for objects that can provide global error rate."""

    def global_error_rate(self) -> float:
        """Return current global error rate (0.0 to 1.0)."""
        ...


class AutoEmergencyDetector:
    """
    Automatically detect system degradation and trigger emergency disable.

    Monitors:
    - Global error rate across all enhancement levels
    - Memory allocation failures
    - Processing latency exceeding thresholds

    Thread Safety: All public methods are thread-safe.
    """

    # Default thresholds (can be overridden via constructor)
    DEFAULT_ERROR_RATE_THRESHOLD = 0.50  # 50% error rate
    DEFAULT_MEMORY_FAILURE_THRESHOLD = 10  # 10 allocation failures
    DEFAULT_LATENCY_THRESHOLD_MS = 5000.0  # 5 seconds max latency
    DEFAULT_CHECK_INTERVAL = 5.0  # Check every 5 seconds

    def __init__(
        self,
        progression_manager: ErrorRateProvider,
        emergency_disable_callback: Callable[[], None],
        error_rate_threshold: float = DEFAULT_ERROR_RATE_THRESHOLD,
        memory_failure_threshold: int = DEFAULT_MEMORY_FAILURE_THRESHOLD,
        latency_threshold_ms: float = DEFAULT_LATENCY_THRESHOLD_MS,
        check_interval: float = DEFAULT_CHECK_INTERVAL,
    ):
        """
        Initialize the AutoEmergencyDetector.

        Args:
            progression_manager: Object providing global_error_rate() method
            emergency_disable_callback: Function to call when emergency triggered
            error_rate_threshold: Error rate threshold (0.0-1.0) to trigger emergency
            memory_failure_threshold: Number of memory failures to trigger emergency
            latency_threshold_ms: Max latency in ms before triggering emergency
            check_interval: Seconds between health checks
        """
        self._progression = progression_manager
        self._emergency_callback = emergency_disable_callback
        self._error_rate_threshold = error_rate_threshold
        self._memory_failure_threshold = memory_failure_threshold
        self._latency_threshold_ms = latency_threshold_ms
        self._check_interval = check_interval

        # State tracking
        self._memory_failures = 0
        self._max_latency_ms = 0.0
        self._lock = threading.Lock()

        # Thread management - use Event for fast wakeup on stop
        self._running = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """
        Start background monitoring thread.

        Idempotent: Safe to call multiple times.
        """
        with self._lock:
            if self._running:
                return  # Already running

            self._running = True
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="epochly-emergency-detector"
            )
            self._thread.start()
            logger.info("AutoEmergencyDetector started")

    def stop(self) -> None:
        """
        Stop background monitoring.

        Blocks until thread terminates (with timeout).
        Thread-safe: Uses lock for _running flag.
        """
        with self._lock:
            self._running = False
        self._stop_event.set()  # Wake up sleeping thread immediately
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
            logger.info("AutoEmergencyDetector stopped")

    def record_memory_failure(self) -> None:
        """
        Record a memory allocation failure.

        Thread-safe: Can be called from any thread.
        """
        with self._lock:
            self._memory_failures += 1
            logger.debug(f"Memory failure recorded: {self._memory_failures} total")

    def record_latency(self, latency_ms: float) -> None:
        """
        Record processing latency.

        Args:
            latency_ms: Latency in milliseconds

        Thread-safe: Can be called from any thread.
        """
        with self._lock:
            self._max_latency_ms = max(self._max_latency_ms, latency_ms)

    def _monitor_loop(self) -> None:
        """
        Background monitoring loop.

        Checks health conditions periodically and triggers emergency
        disable if any threshold is exceeded.

        Thread-safe: Uses stop_event for authoritative signal.
        """
        logger.debug("AutoEmergencyDetector monitor loop started")

        while not self._stop_event.is_set():
            try:
                if self._should_emergency_disable():
                    self._trigger_emergency_disable()
                    break  # Stop monitoring after emergency disable
            except Exception as e:
                # Never crash the monitoring thread
                logger.error(f"Error in emergency detector: {e}", exc_info=True)

            # Use event wait instead of sleep for fast wakeup on stop
            self._stop_event.wait(timeout=self._check_interval)

        logger.debug("AutoEmergencyDetector monitor loop ended")

    def _should_emergency_disable(self) -> bool:
        """
        Check if emergency disable conditions are met.

        Returns:
            True if any threshold is exceeded
        """
        # Check error rate
        try:
            error_rate = self._progression.global_error_rate()
            if error_rate > self._error_rate_threshold:
                logger.warning(
                    f"High error rate detected: {error_rate:.1%} > "
                    f"{self._error_rate_threshold:.1%}"
                )
                return True
        except Exception as e:
            logger.debug(f"Could not get error rate: {e}")

        # Check memory failures
        with self._lock:
            if self._memory_failures > self._memory_failure_threshold:
                logger.warning(
                    f"Memory failure threshold exceeded: {self._memory_failures} > "
                    f"{self._memory_failure_threshold}"
                )
                return True

            # Check latency
            if self._max_latency_ms > self._latency_threshold_ms:
                logger.warning(
                    f"Latency threshold exceeded: {self._max_latency_ms:.0f}ms > "
                    f"{self._latency_threshold_ms:.0f}ms"
                )
                return True

        return False

    def _trigger_emergency_disable(self) -> None:
        """
        Trigger emergency disable.

        Sets environment variable and calls callback.
        Catches all callback exceptions to ensure robustness.
        """
        logger.critical("EMERGENCY: Auto-triggering emergency disable")

        # Set environment variable first (always succeeds)
        os.environ[EMERGENCY_DISABLE_ENV_VAR] = "1"

        # Stop monitoring
        self._running = False

        # Call callback (catch exceptions)
        try:
            self._emergency_callback()
        except Exception as e:
            logger.error(f"Emergency callback failed: {e}", exc_info=True)
            # Continue anyway - env var is set

    def get_stats(self) -> dict:
        """
        Get current detector statistics.

        Returns:
            Dictionary with current state
        """
        with self._lock:
            return {
                'running': self._running,
                'memory_failures': self._memory_failures,
                'max_latency_ms': self._max_latency_ms,
                'error_rate_threshold': self._error_rate_threshold,
                'memory_failure_threshold': self._memory_failure_threshold,
                'latency_threshold_ms': self._latency_threshold_ms,
            }
