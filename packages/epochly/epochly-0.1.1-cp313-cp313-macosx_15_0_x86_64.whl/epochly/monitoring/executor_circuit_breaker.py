"""
Circuit Breaker for Executor Auto-Fallback (perf_fixes5.md Finding #3).

Monitors error rates and automatically falls back to more reliable executors
when error thresholds are exceeded.

Author: Epochly Development Team
"""

import time
import threading
import logging
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from collections import deque
from enum import Enum


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Circuit tripped, using fallback
    HALF_OPEN = "half_open"  # Testing if circuit can close


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    error_threshold: float = 0.3  # 30% error rate trips circuit
    min_samples: int = 10  # Minimum samples before checking threshold
    window_seconds: float = 60.0  # Time window for error rate calculation
    recovery_timeout: float = 30.0  # Time before trying to recover (OPEN -> HALF_OPEN)
    half_open_max_attempts: int = 3  # Max test attempts in HALF_OPEN state


class ExecutorCircuitBreaker:
    """
    Circuit breaker for executor error monitoring.

    Tracks error rates in sliding window and trips circuit when
    thresholds exceeded, triggering automatic fallback to more
    reliable executor modes.
    """

    def __init__(self, executor_mode: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker.

        Args:
            executor_mode: Executor mode being monitored ('native', 'sub_interpreter', etc.)
            config: Optional configuration
        """
        self.logger = logging.getLogger(__name__)
        self.executor_mode = executor_mode
        self.config = config or CircuitBreakerConfig()

        self._state = CircuitState.CLOSED
        self._lock = threading.Lock()
        self._samples = deque()  # (timestamp, success: bool)
        self._last_failure_time = 0.0
        self._half_open_attempts = 0
        self._fallback_callback: Optional[Callable] = None

    def set_fallback_callback(self, callback: Callable) -> None:
        """Set callback to invoke when circuit opens."""
        self._fallback_callback = callback

    def record_result(self, success: bool) -> None:
        """
        Record execution result.

        Args:
            success: True if execution succeeded, False if error
        """
        timestamp = time.time()

        with self._lock:
            # Prune old samples
            cutoff = timestamp - self.config.window_seconds
            while self._samples and self._samples[0][0] < cutoff:
                self._samples.popleft()

            # Add new sample
            self._samples.append((timestamp, success))

            if not success:
                self._last_failure_time = timestamp

            # Check if we should trip the circuit
            if self._state == CircuitState.CLOSED:
                if len(self._samples) >= self.config.min_samples:
                    error_rate = self._calculate_error_rate()
                    if error_rate >= self.config.error_threshold:
                        self._trip_circuit()

            elif self._state == CircuitState.HALF_OPEN:
                if success:
                    self._half_open_attempts += 1
                    if self._half_open_attempts >= self.config.half_open_max_attempts:
                        self._close_circuit()
                else:
                    # Failed in HALF_OPEN, reopen circuit
                    self._trip_circuit()

    def _calculate_error_rate(self) -> float:
        """Calculate current error rate."""
        if not self._samples:
            return 0.0

        failures = sum(1 for _, success in self._samples if not success)
        return failures / len(self._samples)

    def _trip_circuit(self) -> None:
        """Trip the circuit (open it)."""
        old_state = self._state
        self._state = CircuitState.OPEN
        self._half_open_attempts = 0

        self.logger.warning(
            f"Circuit breaker OPENED for {self.executor_mode} executor "
            f"(error rate: {self._calculate_error_rate():.1%})"
        )

        # Invoke fallback callback if registered
        if self._fallback_callback:
            try:
                self._fallback_callback(self.executor_mode)
            except Exception as e:
                self.logger.error(f"Fallback callback failed: {e}")

    def _close_circuit(self) -> None:
        """Close the circuit (restore normal operation)."""
        self._state = CircuitState.CLOSED
        self._half_open_attempts = 0
        self.logger.info(f"Circuit breaker CLOSED for {self.executor_mode} executor (recovered)")

    def should_allow_execution(self) -> bool:
        """
        Check if execution should be allowed.

        Returns:
            True if circuit is closed or half-open, False if open
        """
        with self._lock:
            # Check if we should transition to HALF_OPEN
            if self._state == CircuitState.OPEN:
                time_since_failure = time.time() - self._last_failure_time
                if time_since_failure >= self.config.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_attempts = 0
                    self.logger.info(f"Circuit breaker HALF_OPEN for {self.executor_mode}, testing recovery")
                    return True
                return False

            return True

    def get_state(self) -> str:
        """Get current circuit state."""
        with self._lock:
            return self._state.value

    def get_error_rate(self) -> float:
        """Get current error rate."""
        with self._lock:
            return self._calculate_error_rate()

    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._samples.clear()
            self._half_open_attempts = 0
            self.logger.info(f"Circuit breaker RESET for {self.executor_mode}")


class MultiExecutorCircuitBreaker:
    """Manage circuit breakers for multiple executor modes."""

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """Initialize multi-executor circuit breaker."""
        self.config = config or CircuitBreakerConfig()
        self._breakers: Dict[str, ExecutorCircuitBreaker] = {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    def get_breaker(self, executor_mode: str) -> ExecutorCircuitBreaker:
        """Get or create circuit breaker for executor mode."""
        with self._lock:
            if executor_mode not in self._breakers:
                self._breakers[executor_mode] = ExecutorCircuitBreaker(
                    executor_mode, self.config
                )
        return self._breakers[executor_mode]

    def record_result(self, executor_mode: str, success: bool) -> None:
        """Record result for an executor mode."""
        breaker = self.get_breaker(executor_mode)
        breaker.record_result(success)

    def should_allow_execution(self, executor_mode: str) -> bool:
        """Check if execution should be allowed for mode."""
        breaker = self.get_breaker(executor_mode)
        return breaker.should_allow_execution()

    def set_fallback_callback(self, executor_mode: str, callback: Callable) -> None:
        """Set fallback callback for an executor mode."""
        breaker = self.get_breaker(executor_mode)
        breaker.set_fallback_callback(callback)

    def get_all_states(self) -> Dict[str, str]:
        """Get states for all breakers."""
        return {mode: breaker.get_state() for mode, breaker in self._breakers.items()}
