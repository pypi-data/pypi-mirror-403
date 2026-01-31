"""
Adaptive Threshold Tuning (Phase 4.2)

Auto-tunes routing and JIT compilation thresholds based on allocator telemetry
and real workload patterns.

Architecture:
- Monitors allocator telemetry (size distribution)
- Adjusts routing threshold (sub-interpreter vs JIT decision)
- Adjusts JIT compilation threshold (when to compile)
- Prevents thrashing with smoothing

Performance:
- Updates every N telemetry samples (not every allocation)
- Smoothed updates (exponential moving average)
- Low overhead (<1µs per update)

CRITICAL FIX (Nov 22, 2025):
- Added EPOCHLY_ROUTING_THRESHOLD_BYTES environment variable
- Allows forcing Level 3 for scalar CPU-intensive workloads
- Fixes benchmarking parallelization issue
"""

import os
import time
import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ThresholdConfig:
    """Configuration for adaptive thresholds."""

    # Routing thresholds
    min_routing_threshold: int = 512 * 1024  # 512KB minimum
    max_routing_threshold: int = 10 * 1024 * 1024  # 10MB maximum
    default_routing_threshold: int = 1 * 1024 * 1024  # 1MB default

    # JIT compilation thresholds
    min_jit_threshold: int = 10  # Min function calls before compile
    max_jit_threshold: int = 1000  # Max calls
    default_jit_threshold: int = 100  # Default

    # Update frequency
    update_interval_seconds: float = 60.0  # Update every minute
    smoothing_factor: float = 0.3  # EMA smoothing (0.0-1.0)

    # Sensitivity
    min_pattern_change: float = 0.1  # 10% change required to update


class AdaptiveThresholdAdjuster:
    """
    Adjusts routing and JIT thresholds based on allocator telemetry.

    Uses exponential moving average for smoothing and prevents thrashing.
    """

    def __init__(self, config: Optional[ThresholdConfig] = None):
        """
        Initialize adaptive threshold adjuster.

        Args:
            config: Optional configuration (uses defaults if None)
        """
        self.config = config or ThresholdConfig()

        # Current thresholds
        self._routing_threshold = self.config.default_routing_threshold
        self._jit_threshold = self.config.default_jit_threshold

        # Smoothing state
        self._bucketed_ratio_ema = 0.5  # Start at 50%
        self._allocation_rate_ema = 0.0  # Allocations per second

        # Update tracking
        self._last_update_time = time.time()
        self._last_telemetry: Optional[Dict[str, Any]] = None

        # CRITICAL FIX (Nov 22, 2025): Routing threshold override
        # Allows forcing Level 3 for benchmarking/CPU-intensive scalar workloads
        self._routing_override: Optional[int] = None
        env_override = os.getenv("EPOCHLY_ROUTING_THRESHOLD_BYTES")
        if env_override is not None:
            try:
                override_value = max(0, int(env_override))
                self._routing_override = override_value
                # Lock thresholds to override
                self.config.min_routing_threshold = override_value
                self.config.max_routing_threshold = override_value
                self.config.default_routing_threshold = override_value
                self._routing_threshold = override_value
                logger.info(
                    f"Routing threshold override: {override_value} bytes (from EPOCHLY_ROUTING_THRESHOLD_BYTES)"
                )
            except ValueError:
                logger.warning(
                    f"Invalid EPOCHLY_ROUTING_THRESHOLD_BYTES={env_override}. Using defaults."
                )

        # Thread safety
        self._lock = threading.Lock()

    def update_from_telemetry(self, telemetry: Dict[str, Any], force: bool = False) -> None:
        """
        Update thresholds based on allocator telemetry.

        Args:
            telemetry: Telemetry dict from FastMemoryPool.get_sampled_stats()
            force: Force update even if interval hasn't elapsed (for testing)
        """
        with self._lock:
            # Check if enough time elapsed since last update
            now = time.time()

            # Allow first update immediately (last_update_time = 0)
            if self._last_update_time > 0 and not force:
                if now - self._last_update_time < self.config.update_interval_seconds:
                    # Too soon, skip update to prevent thrashing
                    return

            # Calculate bucketed allocation ratio
            total_allocs = telemetry.get('total_allocations', 0)
            bucketed_allocs = telemetry.get('bucketed_allocations', 0)

            if total_allocs > 0:
                current_bucketed_ratio = bucketed_allocs / total_allocs
            else:
                current_bucketed_ratio = 0.5  # Default

            # Smooth with exponential moving average
            alpha = self.config.smoothing_factor
            self._bucketed_ratio_ema = (
                alpha * current_bucketed_ratio +
                (1 - alpha) * self._bucketed_ratio_ema
            )

            # Calculate allocation rate (if we have previous telemetry)
            if self._last_telemetry:
                prev_allocs = self._last_telemetry.get('total_allocations', 0)
                time_delta = now - self._last_update_time
                if time_delta > 0:
                    alloc_rate = (total_allocs - prev_allocs) / time_delta
                    self._allocation_rate_ema = (
                        alpha * alloc_rate +
                        (1 - alpha) * self._allocation_rate_ema
                    )

            # Adjust routing threshold based on bucketed ratio
            # CRITICAL FIX: Respect override if set
            if self._routing_override is None:
                # Normal adaptive adjustment
                base_threshold = self.config.default_routing_threshold

                if self._bucketed_ratio_ema > 0.7:
                    # Mostly small allocations - increase threshold
                    adjustment_factor = 1.0 + (self._bucketed_ratio_ema - 0.7) * 2.0
                elif self._bucketed_ratio_ema < 0.3:
                    # Mostly large allocations - decrease threshold
                    adjustment_factor = 0.5 + self._bucketed_ratio_ema
                else:
                    # Balanced - minor adjustment
                    adjustment_factor = 1.0

                new_routing_threshold = int(base_threshold * adjustment_factor)

                # Clamp to bounds
                new_routing_threshold = max(
                    self.config.min_routing_threshold,
                    min(new_routing_threshold, self.config.max_routing_threshold)
                )

                # Check if change is significant enough
                threshold_change_ratio = abs(new_routing_threshold - self._routing_threshold) / self._routing_threshold
                if threshold_change_ratio >= self.config.min_pattern_change:
                    self._routing_threshold = new_routing_threshold
                    logger.info(f"Routing threshold adjusted to {new_routing_threshold} bytes "
                               f"(bucketed ratio: {self._bucketed_ratio_ema:.2%})")
            else:
                # Keep override sticky (don't let adaptive updates change it)
                self._routing_threshold = self._routing_override

            # Adjust JIT threshold based on allocation rate
            # High allocation rate → compile more aggressively (lower threshold)
            # Low allocation rate → compile less (higher threshold)
            if self._allocation_rate_ema > 1000:  # >1k allocs/sec
                jit_factor = 0.5  # Compile earlier
            elif self._allocation_rate_ema > 100:  # >100 allocs/sec
                jit_factor = 0.8
            else:
                jit_factor = 1.2  # Compile later

            new_jit_threshold = int(self.config.default_jit_threshold * jit_factor)
            new_jit_threshold = max(
                self.config.min_jit_threshold,
                min(new_jit_threshold, self.config.max_jit_threshold)
            )

            jit_change_ratio = abs(new_jit_threshold - self._jit_threshold) / self._jit_threshold if self._jit_threshold > 0 else 1.0
            if jit_change_ratio >= self.config.min_pattern_change:
                self._jit_threshold = new_jit_threshold
                logger.debug(f"JIT threshold adjusted to {new_jit_threshold} calls "
                            f"(alloc rate: {self._allocation_rate_ema:.0f}/sec)")

            # Store telemetry for next delta calculation
            self._last_telemetry = telemetry
            self._last_update_time = now

    def get_routing_threshold(self) -> int:
        """
        Get current routing threshold (bytes).

        Returns:
            Threshold in bytes for sub-interpreter vs JIT routing
        """
        with self._lock:
            return self._routing_threshold

    def get_jit_threshold(self) -> int:
        """
        Get current JIT compilation threshold (function calls).

        Returns:
            Number of calls before JIT compilation triggers
        """
        with self._lock:
            return self._jit_threshold

    def get_stats(self) -> Dict[str, Any]:
        """
        Get adjuster statistics.

        Returns:
            Dictionary with current thresholds and EMA values
        """
        with self._lock:
            return {
                'routing_threshold_bytes': self._routing_threshold,
                'jit_threshold_calls': self._jit_threshold,
                'bucketed_ratio_ema': self._bucketed_ratio_ema,
                'allocation_rate_ema': self._allocation_rate_ema,
                'last_update_time': self._last_update_time
            }


# Global adjuster (singleton)
_global_adjuster: Optional[AdaptiveThresholdAdjuster] = None
_adjuster_lock = threading.Lock()


def get_threshold_adjuster() -> AdaptiveThresholdAdjuster:
    """
    Get global adaptive threshold adjuster (singleton).

    Returns:
        AdaptiveThresholdAdjuster instance
    """
    global _global_adjuster

    if _global_adjuster is None:
        with _adjuster_lock:
            if _global_adjuster is None:
                _global_adjuster = AdaptiveThresholdAdjuster()

    return _global_adjuster
