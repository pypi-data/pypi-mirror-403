"""
Transparent Interception Metrics Collection for Benchmarking

Tracks transparent interception statistics to validate Epochly's interception
features:
- Interception count per framework (numpy, pandas, sklearn)
- Interception overhead per call (microseconds)
- Routing decisions (optimize vs pass-through)
- Framework detection accuracy and timing

This module provides benchmarking-specific metrics for measuring transparent
interception effectiveness.

Author: Epochly Development Team
Date: November 19, 2025
"""

import threading
from dataclasses import dataclass
from typing import Dict, List
from collections import defaultdict


@dataclass
class InterceptionMetrics:
    """
    Metrics for transparent interception performance.

    Attributes:
        interceptions_by_framework: Count of interceptions per framework
        interception_overhead_us: Per-call overhead in microseconds
        optimized_calls: Number of calls that were optimized
        passthrough_calls: Number of calls passed through without optimization
        framework_detection_time_us: Time to detect framework per call (microseconds)
    """
    interceptions_by_framework: Dict[str, int]
    interception_overhead_us: List[float]
    optimized_calls: int
    passthrough_calls: int
    framework_detection_time_us: List[float]

    @property
    def total_interceptions(self) -> int:
        """
        Total number of intercepted calls across all frameworks.

        Returns:
            Sum of all framework interceptions
        """
        return sum(self.interceptions_by_framework.values())

    @property
    def optimization_rate(self) -> float:
        """
        Fraction of calls that were optimized (vs passed through).

        Returns:
            Ratio of optimized / total calls (0.0 to 1.0)
        """
        total_calls = self.optimized_calls + self.passthrough_calls
        if total_calls == 0:
            return 0.0
        return self.optimized_calls / total_calls

    @property
    def mean_interception_overhead_us(self) -> float:
        """
        Mean overhead per intercepted call.

        Target: <10 microseconds per call

        Returns:
            Average interception overhead in microseconds
        """
        if not self.interception_overhead_us:
            return 0.0
        return sum(self.interception_overhead_us) / len(self.interception_overhead_us)


class InterceptionTracker:
    """
    Track transparent interception metrics during benchmark execution.

    Monitors framework detection, call interception, routing decisions, and
    overhead to validate that Epochly's transparent interception works effectively.

    Usage:
        tracker = InterceptionTracker()
        tracker.start_tracking()

        # Run benchmark (interception events recorded via callbacks)
        # numpy.sum() called:
        #   record_interception("numpy", overhead_us=5.0, detection_time_us=1.0, optimized=True)

        tracker.stop_tracking()
        metrics = tracker.get_metrics()

        print(f"Total interceptions: {metrics.total_interceptions}")
        print(f"Optimization rate: {metrics.optimization_rate:.1%}")
        print(f"Mean overhead: {metrics.mean_interception_overhead_us:.2f}us")

    Integration Points:
        - sys.meta_path hooks: Report interception events
        - InterceptionManager: Track framework detection and routing
        - WorkloadDetector: Determine optimize vs passthrough decisions

    Thread Safety:
        All public methods are thread-safe and use proper locking.
    """

    def __init__(self):
        """Initialize interception tracker."""
        # Framework-specific counters
        self._interceptions: defaultdict = defaultdict(int)

        # Performance data
        self._overhead_samples: List[float] = []
        self._detection_time_samples: List[float] = []

        # Routing decisions
        self._optimized_count: int = 0
        self._passthrough_count: int = 0

        # Thread safety lock for all mutable state
        self._lock = threading.Lock()

    def start_tracking(self) -> None:
        """
        Begin tracking interception metrics.

        Resets all counters and starts new tracking session.

        Thread Safety:
            Safe to call from any thread.
        """
        with self._lock:
            self._reset_counters()

    def stop_tracking(self) -> None:
        """
        Stop tracking and finalize metrics.

        Thread Safety:
            Safe to call from any thread.
        """
        # All data already collected via callbacks
        pass

    def _reset_counters(self) -> None:
        """
        Reset all counters for new tracking session.

        Note: Caller must hold self._lock.
        """
        self._interceptions.clear()
        self._overhead_samples.clear()
        self._detection_time_samples.clear()
        self._optimized_count = 0
        self._passthrough_count = 0

    def record_interception(
        self,
        framework: str,
        overhead_us: float,
        detection_time_us: float,
        optimized: bool
    ) -> None:
        """
        Record interception event.

        Args:
            framework: Framework name (e.g., "numpy", "pandas", "sklearn")
            overhead_us: Interception overhead in microseconds
            detection_time_us: Framework detection time in microseconds
            optimized: Whether call was optimized (True) or passed through (False)

        Thread Safety:
            Safe to call from any thread with proper locking.
            Note: defaultdict[key] += 1 is NOT atomic - it's a read-modify-write
            operation that requires locking.
        """
        with self._lock:
            self._interceptions[framework] += 1
            self._overhead_samples.append(overhead_us)
            self._detection_time_samples.append(detection_time_us)

            if optimized:
                self._optimized_count += 1
            else:
                self._passthrough_count += 1

    def get_metrics(self) -> InterceptionMetrics:
        """
        Compute final interception metrics.

        Returns:
            InterceptionMetrics with statistical summary

        Thread Safety:
            Safe to call while tracking is active. Returns snapshot of current state.
        """
        with self._lock:
            return InterceptionMetrics(
                interceptions_by_framework=dict(self._interceptions),
                interception_overhead_us=self._overhead_samples.copy(),
                optimized_calls=self._optimized_count,
                passthrough_calls=self._passthrough_count,
                framework_detection_time_us=self._detection_time_samples.copy()
            )
