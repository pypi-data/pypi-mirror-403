"""
Latency Percentile Tracking for Executor Monitoring (perf_fixes5.md Finding #3).

Provides sliding-window latency tracking with p50, p95, p99 percentiles
for executor performance monitoring and circuit breaker decisions.

Author: Epochly Development Team
"""

import time
import threading
from collections import deque
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import statistics


@dataclass
class LatencyMetrics:
    """Latency metrics for an executor."""
    p50: float  # Median latency (ms)
    p95: float  # 95th percentile (ms)
    p99: float  # 99th percentile (ms)
    mean: float  # Average latency (ms)
    count: int  # Sample count
    min: float  # Minimum latency (ms)
    max: float  # Maximum latency (ms)


class SlidingWindowLatencyTracker:
    """
    Track latency metrics in a sliding time window.

    Features:
    - Configurable window size (default: 60 seconds)
    - Automatic old sample pruning
    - Thread-safe operations
    - Percentile calculations (p50, p95, p99)
    - Low overhead (<1μs per record)
    """

    def __init__(self, window_seconds: float = 60.0, max_samples: int = 10000):
        """
        Initialize latency tracker.

        Args:
            window_seconds: Time window for metrics (default: 60s)
            max_samples: Maximum samples to retain (prevents unbounded growth)
        """
        self._window_seconds = window_seconds
        self._max_samples = max_samples
        self._samples: deque = deque(maxlen=max_samples)  # (timestamp, latency_ns)
        self._lock = threading.Lock()

    def record_latency(self, latency_ns: int) -> None:
        """
        Record a latency sample.

        Args:
            latency_ns: Latency in nanoseconds
        """
        timestamp = time.time()
        with self._lock:
            self._samples.append((timestamp, latency_ns))

    def get_metrics(self) -> Optional[LatencyMetrics]:
        """
        Get current latency metrics for the sliding window.

        Returns:
            LatencyMetrics with p50, p95, p99, or None if no samples
        """
        with self._lock:
            # Prune old samples outside window
            cutoff_time = time.time() - self._window_seconds
            while self._samples and self._samples[0][0] < cutoff_time:
                self._samples.popleft()

            if not self._samples:
                return None

            # Extract latencies in milliseconds
            latencies_ms = [lat_ns / 1_000_000 for _, lat_ns in self._samples]

            # Sort for percentile calculation
            sorted_latencies = sorted(latencies_ms)
            count = len(sorted_latencies)

            # Calculate percentiles
            p50_idx = int(count * 0.50)
            p95_idx = int(count * 0.95)
            p99_idx = int(count * 0.99)

            return LatencyMetrics(
                p50=sorted_latencies[p50_idx] if p50_idx < count else sorted_latencies[-1],
                p95=sorted_latencies[p95_idx] if p95_idx < count else sorted_latencies[-1],
                p99=sorted_latencies[p99_idx] if p99_idx < count else sorted_latencies[-1],
                mean=statistics.mean(latencies_ms),
                count=count,
                min=sorted_latencies[0],
                max=sorted_latencies[-1]
            )

    def clear(self) -> None:
        """Clear all samples."""
        with self._lock:
            self._samples.clear()


class ExecutorLatencyMonitor:
    """
    Monitor latency for multiple executor modes.

    Tracks separate metrics for:
    - native (compiled pool)
    - sub_interpreter (Python sub-interpreters)
    - process (ProcessPoolExecutor)
    - thread (ThreadPoolExecutor)
    """

    def __init__(self, window_seconds: float = 60.0):
        """
        Initialize executor latency monitor.

        Args:
            window_seconds: Sliding window size
        """
        self._trackers: Dict[str, SlidingWindowLatencyTracker] = {}
        self._lock = threading.Lock()
        self._window_seconds = window_seconds

    def record_latency(self, executor_mode: str, latency_ns: int) -> None:
        """
        Record latency for an executor mode.

        Args:
            executor_mode: 'native', 'sub_interpreter', 'process', 'thread'
            latency_ns: Latency in nanoseconds
        """
        with self._lock:
            if executor_mode not in self._trackers:
                self._trackers[executor_mode] = SlidingWindowLatencyTracker(
                    window_seconds=self._window_seconds
                )

        self._trackers[executor_mode].record_latency(latency_ns)

    def get_metrics(self, executor_mode: str) -> Optional[LatencyMetrics]:
        """
        Get latency metrics for an executor mode.

        Args:
            executor_mode: Executor mode to query

        Returns:
            LatencyMetrics or None if no data
        """
        tracker = self._trackers.get(executor_mode)
        if tracker:
            return tracker.get_metrics()
        return None

    def get_all_metrics(self) -> Dict[str, LatencyMetrics]:
        """
        Get metrics for all executor modes.

        Returns:
            Dict mapping executor_mode to LatencyMetrics
        """
        result = {}
        for mode, tracker in self._trackers.items():
            metrics = tracker.get_metrics()
            if metrics:
                result[mode] = metrics
        return result

    def clear(self, executor_mode: Optional[str] = None) -> None:
        """
        Clear metrics.

        Args:
            executor_mode: Specific mode to clear, or None for all
        """
        if executor_mode:
            tracker = self._trackers.get(executor_mode)
            if tracker:
                tracker.clear()
        else:
            for tracker in self._trackers.values():
                tracker.clear()
