"""
Runtime Loop Transformation Metrics Collection for Benchmarking

Tracks runtime loop transformation statistics to validate Epochly's loop
transformation features:
- Loop detection (for-loops, while-loops, nested loops)
- Transformation success/failure rates
- Transformation overhead (AST analysis + code generation)
- Speedup achieved per transformed loop

This module provides benchmarking-specific metrics for measuring runtime
loop transformation effectiveness.

Author: Epochly Development Team
Date: November 19, 2025
"""

import threading
from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class LoopType(Enum):
    """Types of loops that can be detected and transformed."""
    FOR_LOOP = "for"
    WHILE_LOOP = "while"
    NESTED_LOOP = "nested"


@dataclass
class LoopTransformMetrics:
    """
    Metrics for runtime loop transformation.

    Attributes:
        loops_detected: Count of loops detected per type
        loops_transformed: Count of loops successfully transformed per type
        loops_skipped: Count of loops skipped (not transformable) per type
        transformation_time_ms: Per-loop transformation overhead (milliseconds)
        speedup_per_loop: Measured speedup for each transformed loop
    """
    loops_detected: Dict[LoopType, int]
    loops_transformed: Dict[LoopType, int]
    loops_skipped: Dict[LoopType, int]
    transformation_time_ms: List[float]
    speedup_per_loop: List[float]

    @property
    def transformation_rate(self) -> float:
        """
        Fraction of detected loops successfully transformed.

        Returns:
            Ratio of transformed / detected (0.0 to 1.0)
        """
        total_detected = sum(self.loops_detected.values())
        total_transformed = sum(self.loops_transformed.values())

        if total_detected == 0:
            return 0.0

        return total_transformed / total_detected

    @property
    def mean_transformation_time_ms(self) -> float:
        """
        Mean overhead for transforming a loop.

        Target: <10ms per loop

        Returns:
            Average transformation time in milliseconds
        """
        if not self.transformation_time_ms:
            return 0.0
        return sum(self.transformation_time_ms) / len(self.transformation_time_ms)

    @property
    def mean_speedup(self) -> float:
        """
        Mean speedup achieved across all transformed loops.

        Returns:
            Average speedup ratio (1.0 = no improvement)
        """
        if not self.speedup_per_loop:
            return 1.0  # No speedup = 1.0x
        return sum(self.speedup_per_loop) / len(self.speedup_per_loop)


class LoopTransformTracker:
    """
    Track runtime loop transformation metrics during benchmark execution.

    Monitors loop detection, transformation success/failure, and performance
    to validate that Epochly's RuntimeLoopTransformer is working effectively.

    Usage:
        tracker = LoopTransformTracker()
        tracker.start_tracking()

        # Run benchmark (loop transform events recorded via callbacks)
        # Loop detected:    record_loop_detected(LoopType.FOR_LOOP)
        # Loop transformed: record_loop_transformed(LoopType.FOR_LOOP, 2.5, 4.2)
        # Loop skipped:     record_loop_skipped(LoopType.FOR_LOOP, "contains_break")

        tracker.stop_tracking()
        metrics = tracker.get_metrics()

        print(f"Transformation rate: {metrics.transformation_rate:.1%}")
        print(f"Mean speedup: {metrics.mean_speedup:.2f}x")

    Integration Points:
        - RuntimeLoopTransformer: Reports loop detection and transformation events
        - Auto-profiler: Triggers transformation on hot path detection
        - BatchDispatcher: Provides speedup measurements

    Thread Safety:
        All public methods are thread-safe and use proper locking.
    """

    def __init__(self):
        """Initialize loop transformation tracker."""
        # Loop counters per type
        self._detected: Dict[LoopType, int] = {t: 0 for t in LoopType}
        self._transformed: Dict[LoopType, int] = {t: 0 for t in LoopType}
        self._skipped: Dict[LoopType, int] = {t: 0 for t in LoopType}

        # Performance data
        self._transform_times: List[float] = []
        self._speedups: List[float] = []

        # Thread safety lock for all mutable state
        self._lock = threading.Lock()

    def start_tracking(self) -> None:
        """
        Begin tracking loop transformation metrics.

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
        self._detected = {t: 0 for t in LoopType}
        self._transformed = {t: 0 for t in LoopType}
        self._skipped = {t: 0 for t in LoopType}
        self._transform_times.clear()
        self._speedups.clear()

    def record_loop_detected(self, loop_type: LoopType) -> None:
        """
        Record loop detection event.

        Args:
            loop_type: Type of loop detected

        Thread Safety:
            Safe to call from any thread with proper locking.
            Note: dict[key] += 1 is NOT atomic - it's a read-modify-write
            operation that requires locking.
        """
        with self._lock:
            self._detected[loop_type] += 1

    def record_loop_transformed(
        self,
        loop_type: LoopType,
        transform_time_ms: float,
        speedup: float
    ) -> None:
        """
        Record successful loop transformation.

        Args:
            loop_type: Type of loop transformed
            transform_time_ms: Time taken to transform (milliseconds)
            speedup: Speedup achieved (transformed_time / original_time)

        Thread Safety:
            Safe to call from any thread with proper locking.
        """
        with self._lock:
            self._transformed[loop_type] += 1
            self._transform_times.append(transform_time_ms)
            self._speedups.append(speedup)

    def record_loop_skipped(self, loop_type: LoopType, reason: str) -> None:
        """
        Record loop skipped (not transformable).

        Args:
            loop_type: Type of loop skipped
            reason: Reason for skipping (e.g., "contains_break", "unbounded")

        Thread Safety:
            Safe to call from any thread with proper locking.
        """
        with self._lock:
            self._skipped[loop_type] += 1

    def get_metrics(self) -> LoopTransformMetrics:
        """
        Compute final loop transformation metrics.

        Returns:
            LoopTransformMetrics with statistical summary

        Thread Safety:
            Safe to call while tracking is active. Returns snapshot of current state.
        """
        with self._lock:
            return LoopTransformMetrics(
                loops_detected=self._detected.copy(),
                loops_transformed=self._transformed.copy(),
                loops_skipped=self._skipped.copy(),
                transformation_time_ms=self._transform_times.copy(),
                speedup_per_loop=self._speedups.copy()
            )
