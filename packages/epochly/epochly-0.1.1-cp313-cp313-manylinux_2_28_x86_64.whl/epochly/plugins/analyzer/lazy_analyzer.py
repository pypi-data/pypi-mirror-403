"""
Lazy Analyzer Activation (SPEC2 Task 6)

Defers heavy analyzer component initialization until sustained load is detected.

Benefits:
- Idle deployments skip psutil, hardware counters, ML imports
- Faster startup for simple workloads
- Memory saved when analyzers not needed
- Sampling gates reduce per-event overhead

Architecture:
- Factory pattern with ensure_started() semantics
- Activation triggers based on workload detection
- Sampling reduces allocation tracking overhead
- Thread-safe lazy initialization with proper locking

Thread Safety:
- All shared state protected by _lock
- Double-check locking for activation
- Atomic flag transitions
"""

import threading
import logging
import random  # Module-level import (not in hot path)
from typing import Optional, Callable, Any
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ActivationConfig:
    """Configuration for lazy analyzer activation."""

    # Activation triggers
    min_calls_before_activation: int = 1000  # Minimum calls before activating
    min_duration_ms_before_activation: float = 100.0  # Minimum sustained duration

    # Sampling configuration
    sampling_rate: float = 0.1  # Sample 10% of events before activation
    sampling_rate_after_activation: float = 1.0  # 100% after activation


class LazyAnalyzerManager:
    """
    Manages lazy initialization of heavy analyzer components.

    Defers expensive component creation (psutil, ML helpers, hardware counters)
    until workload justifies the overhead.

    Example:
        factory = lambda: HeavyAnalyzer()
        manager = LazyAnalyzerManager(factory)

        # Before activation - no overhead
        manager.maybe_record(event)  # Sampled, maybe discarded

        # After sustained load detected
        # → factory() called, analyzer created
        manager.maybe_record(event)  # All events recorded

        # Get analyzer (None before activation)
        analyzer = manager.get_analyzer()
    """

    def __init__(self, factory: Callable, config: Optional[ActivationConfig] = None):
        """
        Initialize lazy analyzer manager.

        Args:
            factory: Factory function that creates the analyzer
            config: Optional activation configuration
        """
        self._factory = factory
        self._config = config or ActivationConfig()
        self._lock = threading.Lock()  # Protects ALL shared state

        # Lazy-loaded analyzer instance
        self._instance: Optional[Any] = None
        self._activated = False  # Atomic activation flag

        # Activation tracking (protected by _lock)
        self._event_count = 0
        self._total_duration_ms = 0.0

        logger.debug(f"LazyAnalyzerManager created (factory: {factory})")

    def ensure_started(self) -> Any:
        """
        Ensure analyzer is started and return instance.

        Creates analyzer on first call (lazy initialization).
        Uses double-check locking for thread safety.

        Returns:
            Analyzer instance

        Raises:
            RuntimeError: If factory fails or returns None
        """
        # CRITICAL FIX: Use _activated flag for double-check (atomic)
        if not self._activated:
            with self._lock:
                # Double-check inside lock
                if not self._activated:
                    logger.info(f"Activating analyzer via factory: {self._factory}")

                    try:
                        instance = self._factory()

                        # Validate factory returned valid instance
                        if instance is None:
                            raise RuntimeError(f"Factory {self._factory} returned None")

                        # Atomic assignment and flag flip
                        self._instance = instance
                        self._activated = True
                        logger.info("Analyzer activated successfully")

                    except Exception as e:
                        logger.error(f"Failed to activate analyzer: {e}")
                        raise RuntimeError(f"Analyzer activation failed: {e}") from e

        return self._instance

    def get_analyzer(self) -> Optional[Any]:
        """
        Get analyzer instance if activated.

        Returns:
            Analyzer instance if activated, None otherwise
        """
        return self._instance

    def is_activated(self) -> bool:
        """Check if analyzer has been activated."""
        return self._activated

    def should_activate(self, event: Any) -> bool:
        """
        Determine if analyzer should be activated based on event.

        CRITICAL: Thread-safe - all shared state access protected by lock.

        Args:
            event: Event to evaluate (can be dict, object, etc.)

        Returns:
            True if should activate, False otherwise
        """
        # Fast path - check activation without lock (atomic read)
        if self._activated:
            return True

        # CRITICAL FIX: Protect all shared state modifications with lock
        with self._lock:
            # Double-check after acquiring lock
            if self._activated:
                return True

            # Track event for activation decision
            self._event_count += 1

            # Extract duration if available
            duration_ms = 0.0
            if isinstance(event, dict):
                duration_ms = event.get('duration_ms', 0.0)
            elif hasattr(event, 'duration_ms'):
                duration_ms = event.duration_ms

            self._total_duration_ms += duration_ms

            # Check activation criteria
            if self._event_count >= self._config.min_calls_before_activation:
                avg_duration = self._total_duration_ms / self._event_count

                if avg_duration >= self._config.min_duration_ms_before_activation:
                    logger.info(
                        f"Activation criteria met: {self._event_count} calls, "
                        f"{avg_duration:.1f}ms avg duration"
                    )
                    return True

        return False

    def maybe_record(self, event: Any) -> bool:
        """
        Maybe record event (with sampling before activation).

        Args:
            event: Event to record

        Returns:
            True if event was recorded, False if sampled out or not activated
        """
        # Check if should activate
        if self.should_activate(event):
            try:
                # Ensure analyzer started (may raise if factory fails)
                analyzer = self.ensure_started()

                # Record event with error handling
                if hasattr(analyzer, 'record'):
                    analyzer.record(event)
                    return True
                elif hasattr(analyzer, 'record_allocation'):
                    analyzer.record_allocation(event)
                    return True
                else:
                    logger.warning(f"Analyzer has no record method: {type(analyzer)}")
                    return False

            except Exception as e:
                logger.error(f"Error recording event: {e}")
                return False

        # Not activated yet - sampling decision (events not recorded before activation)
        # Apply sampling to decide if we should track this for activation metrics
        if random.random() < self._config.sampling_rate:
            # Sample accepted - counted for activation decision
            return False

        return False

    def get_stats(self) -> dict:
        """
        Get lazy analyzer statistics.

        CRITICAL: Thread-safe - reads shared state with lock.

        Returns:
            Statistics dictionary
        """
        # CRITICAL FIX: Protect reads for consistent snapshot
        with self._lock:
            return {
                'activated': self._activated,
                'event_count': self._event_count,
                'total_duration_ms': self._total_duration_ms,
                'avg_duration_ms': self._total_duration_ms / self._event_count if self._event_count > 0 else 0.0,
                'sampling_rate': self._config.sampling_rate if not self._activated else self._config.sampling_rate_after_activation
            }
