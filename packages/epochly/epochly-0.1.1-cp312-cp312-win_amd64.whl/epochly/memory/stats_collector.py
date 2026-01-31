"""
Epochly Memory Foundation - Unified Statistics Collection

This module provides centralized statistics collection for all memory components,
replacing scattered counter logic with a unified, observable system.

Author: Epochly Memory Foundation Team
Created: 2025-06-06
"""

import threading
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from collections import deque
import statistics
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricSnapshot:
    """Snapshot of a metric at a specific point in time."""
    
    timestamp: float
    value: Union[int, float]
    
    def __post_init__(self):
        """Validate metric snapshot data."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("Metric value must be numeric")
        if self.timestamp <= 0:
            raise ValueError("Timestamp must be positive")


class HistogramMetric:
    """
    Histogram metric for tracking value distributions.
    
    Maintains a sliding window of values for percentile calculations.
    """
    
    def __init__(self, max_samples: int = 10000):
        """
        Initialize histogram metric.
        
        Args:
            max_samples: Maximum number of samples to retain
        """
        self.max_samples = max_samples
        self._values: deque = deque(maxlen=max_samples)
        self._lock = threading.RLock()
        self._total_count = 0
        self._sum = 0.0
    
    def record(self, value: Union[int, float]) -> None:
        """
        Record a new value in the histogram.
        
        Args:
            value: Value to record
        """
        with self._lock:
            self._values.append(value)
            self._total_count += 1
            self._sum += value
    
    def get_percentiles(self, percentiles: Optional[List[float]] = None) -> Dict[str, float]:
        """
        Calculate percentiles for recorded values.
        
        Args:
            percentiles: List of percentiles to calculate (0-100)
            
        Returns:
            Dictionary mapping percentile names to values
        """
        if percentiles is None:
            percentiles = [50, 95, 99]
        
        with self._lock:
            if not self._values:
                return {f"p{p}": 0.0 for p in percentiles}
            
            sorted_values = sorted(self._values)
            result = {}
            
            for p in percentiles:
                if p < 0 or p > 100:
                    continue
                
                if p == 0:
                    result[f"p{p}"] = sorted_values[0]
                elif p == 100:
                    result[f"p{p}"] = sorted_values[-1]
                else:
                    index = int((p / 100.0) * (len(sorted_values) - 1))
                    result[f"p{p}"] = sorted_values[index]
            
            return result
    
    def get_statistics(self) -> Dict[str, float]:
        """
        Get comprehensive statistics for the histogram.
        
        Returns:
            Dictionary with count, sum, mean, min, max, and percentiles
        """
        with self._lock:
            if not self._values:
                return {
                    'count': 0,
                    'sum': 0.0,
                    'mean': 0.0,
                    'min': 0.0,
                    'max': 0.0,
                    'stddev': 0.0
                }
            
            values_list = list(self._values)
            return {
                'count': len(values_list),
                'total_count': self._total_count,
                'sum': self._sum,
                'mean': statistics.mean(values_list),
                'min': min(values_list),
                'max': max(values_list),
                'stddev': statistics.stdev(values_list) if len(values_list) > 1 else 0.0
            }
    
    def reset(self) -> None:
        """Reset the histogram."""
        with self._lock:
            self._values.clear()
            self._total_count = 0
            self._sum = 0.0


class CounterMetric:
    """
    Counter metric for tracking cumulative values.
    
    Thread-safe counter with optional rate calculation.
    """
    
    def __init__(self):
        """Initialize counter metric."""
        self._value = 0
        self._lock = threading.RLock()
        # PERFORMANCE FIX: Use nanosecond precision timing
        self._last_reset_ns = time.perf_counter_ns()
    
    def increment(self, value: Union[int, float] = 1) -> None:
        """
        Increment the counter.
        
        Args:
            value: Amount to increment by
        """
        with self._lock:
            self._value += value
    
    def decrement(self, value: Union[int, float] = 1) -> None:
        """
        Decrement the counter.
        
        Args:
            value: Amount to decrement by
        """
        with self._lock:
            self._value -= value
    
    def get_value(self) -> Union[int, float]:
        """Get current counter value."""
        with self._lock:
            return self._value
    
    def get_rate(self) -> float:
        """
        Get rate of change since last reset.
        
        Returns:
            Rate per second
        """
        with self._lock:
            # PERFORMANCE FIX: Use nanosecond precision timing
            elapsed_ns = time.perf_counter_ns() - self._last_reset_ns
            elapsed_seconds = elapsed_ns / 1_000_000_000.0
            if elapsed_seconds <= 0:
                return 0.0
            return self._value / elapsed_seconds
    
    def reset(self) -> Union[int, float]:
        """
        Reset counter and return previous value.
        
        Returns:
            Previous counter value
        """
        with self._lock:
            old_value = self._value
            self._value = 0
            # PERFORMANCE FIX: Use nanosecond precision timing
            self._last_reset_ns = time.perf_counter_ns()
            return old_value


class StatsCollector:
    """
    Unified statistics collector for memory foundation components.
    
    Provides centralized collection of counters, histograms, and gauges
    with thread-safe operations and comprehensive reporting.
    
    PERFORMANCE OPTIMIZATION: Uses nanosecond precision timing and sampling
    to reduce overhead for high-frequency operations.
    """
    
    def __init__(self, name: str = "memory_foundation", sampling_rate: float = 1.0):
        """
        Initialize statistics collector.
        
        Args:
            name: Name of the collector instance
            sampling_rate: Fraction of events to sample (0.0-1.0, default 1.0 = all events)
        """
        self.name = name
        self._counters: Dict[str, CounterMetric] = {}
        self._histograms: Dict[str, HistogramMetric] = {}
        self._gauges: Dict[str, float] = {}
        self._lock = threading.RLock()
        
        # PERFORMANCE FIX: Use nanosecond precision timing for sub-microsecond accuracy
        self._start_time_ns = time.perf_counter_ns()
        
        # PERFORMANCE OPTIMIZATION: Sampling to reduce overhead
        self._sampling_rate = max(0.0, min(1.0, sampling_rate))
        self._sample_counter = 0
        
        logger.info(f"Statistics collector '{name}' initialized with sampling rate {sampling_rate}")
    
    def _should_sample(self) -> bool:
        """
        Determine if current event should be sampled.
        
        Uses deterministic sampling based on counter to ensure consistent
        sampling rate across all operations.
        
        Returns:
            True if event should be recorded, False otherwise
        """
        if self._sampling_rate >= 1.0:
            return True
        
        if self._sampling_rate <= 0.0:
            return False
            
        self._sample_counter += 1
        # Use modulo for deterministic sampling (e.g., 1:32 ratio = sample every 32nd event)
        sample_interval = int(1.0 / self._sampling_rate)
        return (self._sample_counter % sample_interval) == 0
    
    def increment_counter(self, metric: str, value: Union[int, float] = 1) -> None:
        """
        Increment a counter metric.
        
        Args:
            metric: Name of the counter metric
            value: Amount to increment by
        """
        # PERFORMANCE OPTIMIZATION: Apply sampling to reduce overhead
        if not self._should_sample():
            return
            
        with self._lock:
            if metric not in self._counters:
                self._counters[metric] = CounterMetric()
            self._counters[metric].increment(value)
    
    def decrement_counter(self, metric: str, value: Union[int, float] = 1) -> None:
        """
        Decrement a counter metric.
        
        Args:
            metric: Name of the counter metric
            value: Amount to decrement by
        """
        # PERFORMANCE OPTIMIZATION: Apply sampling to reduce overhead
        if not self._should_sample():
            return
            
        with self._lock:
            if metric not in self._counters:
                self._counters[metric] = CounterMetric()
            self._counters[metric].decrement(value)
    
    def record_histogram(self, metric: str, value: Union[int, float]) -> None:
        """
        Record a value in a histogram metric.
        
        Args:
            metric: Name of the histogram metric
            value: Value to record
        """
        # PERFORMANCE OPTIMIZATION: Apply sampling to reduce overhead
        if not self._should_sample():
            return
            
        with self._lock:
            if metric not in self._histograms:
                self._histograms[metric] = HistogramMetric()
            self._histograms[metric].record(value)
    
    def set_gauge(self, metric: str, value: Union[int, float]) -> None:
        """
        Set a gauge metric value.
        
        Args:
            metric: Name of the gauge metric
            value: Value to set
        """
        with self._lock:
            self._gauges[metric] = float(value)
    
    def record_latency(self, operation: str, duration: float) -> None:
        """
        Record operation latency.
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
        """
        self.record_histogram(f"{operation}_latency", duration)
        self.increment_counter(f"{operation}_count")
    
    def record_throughput(self, operation: str, count: int = 1) -> None:
        """
        Record operation throughput.
        
        Args:
            operation: Name of the operation
            count: Number of operations completed
        """
        self.increment_counter(f"{operation}_throughput", count)
    
    def record_error(self, operation: str, error_type: str = "generic") -> None:
        """
        Record an error occurrence.
        
        Args:
            operation: Name of the operation that failed
            error_type: Type of error that occurred
        """
        self.increment_counter(f"{operation}_errors")
        self.increment_counter(f"{operation}_errors_{error_type}")
    
    def get_counter(self, metric: str) -> Union[int, float]:
        """
        Get current value of a counter metric.
        
        Args:
            metric: Name of the counter metric
            
        Returns:
            Current counter value
        """
        with self._lock:
            if metric not in self._counters:
                return 0
            return self._counters[metric].get_value()
    
    def get_counter_rate(self, metric: str) -> float:
        """
        Get rate of change for a counter metric.
        
        Args:
            metric: Name of the counter metric
            
        Returns:
            Rate per second
        """
        with self._lock:
            if metric not in self._counters:
                return 0.0
            return self._counters[metric].get_rate()
    
    def get_histogram_percentiles(self, metric: str, percentiles: Optional[List[float]] = None) -> Dict[str, float]:
        """
        Get percentiles for a histogram metric.
        
        Args:
            metric: Name of the histogram metric
            percentiles: List of percentiles to calculate
            
        Returns:
            Dictionary mapping percentile names to values
        """
        with self._lock:
            if metric not in self._histograms:
                return {}
            return self._histograms[metric].get_percentiles(percentiles)
    
    def get_histogram_statistics(self, metric: str) -> Dict[str, float]:
        """
        Get comprehensive statistics for a histogram metric.
        
        Args:
            metric: Name of the histogram metric
            
        Returns:
            Dictionary with histogram statistics
        """
        with self._lock:
            if metric not in self._histograms:
                return {}
            return self._histograms[metric].get_statistics()
    
    def get_gauge(self, metric: str) -> float:
        """
        Get current value of a gauge metric.
        
        Args:
            metric: Name of the gauge metric
            
        Returns:
            Current gauge value
        """
        with self._lock:
            return self._gauges.get(metric, 0.0)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics and their current values.
        
        Returns:
            Dictionary containing all metrics
        """
        with self._lock:
            # PERFORMANCE FIX: Use nanosecond precision timing
            uptime_ns = time.perf_counter_ns() - self._start_time_ns
            uptime_seconds = uptime_ns / 1_000_000_000.0
            
            result = {
                'collector_name': self.name,
                'uptime_seconds': uptime_seconds,
                'sampling_rate': self._sampling_rate,
                'counters': {},
                'histograms': {},
                'gauges': dict(self._gauges)
            }
            
            # Collect counter metrics
            for name, counter in self._counters.items():
                result['counters'][name] = {
                    'value': counter.get_value(),
                    'rate': counter.get_rate()
                }
            
            # Collect histogram metrics
            for name, histogram in self._histograms.items():
                stats = histogram.get_statistics()
                percentiles = histogram.get_percentiles([50, 95, 99])
                result['histograms'][name] = {**stats, **percentiles}
            
            return result
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of key metrics.
        
        Returns:
            Dictionary with metric summary
        """
        with self._lock:
            # PERFORMANCE FIX: Use nanosecond precision timing
            uptime_ns = time.perf_counter_ns() - self._start_time_ns
            uptime_seconds = uptime_ns / 1_000_000_000.0
            
            # Calculate total operations
            total_ops = sum(
                counter.get_value() 
                for name, counter in self._counters.items() 
                if name.endswith('_count')
            )
            
            # Calculate total errors
            total_errors = sum(
                counter.get_value() 
                for name, counter in self._counters.items() 
                if '_errors' in name and not name.endswith('_errors_generic')
            )
            
            # Calculate average latency across all operations
            avg_latencies = []
            for name, histogram in self._histograms.items():
                if name.endswith('_latency'):
                    stats = histogram.get_statistics()
                    if stats.get('count', 0) > 0:
                        avg_latencies.append(stats['mean'])
            
            overall_avg_latency = statistics.mean(avg_latencies) if avg_latencies else 0.0
            
            return {
                'collector_name': self.name,
                'uptime_seconds': uptime_seconds,
                'sampling_rate': self._sampling_rate,
                'total_operations': total_ops,
                'total_errors': total_errors,
                'error_rate': total_errors / total_ops if total_ops > 0 else 0.0,
                'operations_per_second': total_ops / uptime_seconds if uptime_seconds > 0 else 0.0,
                'average_latency_seconds': overall_avg_latency,
                'active_counters': len(self._counters),
                'active_histograms': len(self._histograms),
                'active_gauges': len(self._gauges)
            }
    
    def reset_all_metrics(self) -> None:
        """Reset all metrics to their initial state."""
        with self._lock:
            for counter in self._counters.values():
                counter.reset()
            for histogram in self._histograms.values():
                histogram.reset()
            self._gauges.clear()
            # PERFORMANCE FIX: Use nanosecond precision timing
            self._start_time_ns = time.perf_counter_ns()
            self._sample_counter = 0
            logger.info(f"All metrics reset for collector '{self.name}'")
    
    def reset_metric(self, metric: str) -> bool:
        """
        Reset a specific metric.
        
        Args:
            metric: Name of the metric to reset
            
        Returns:
            True if metric was found and reset, False otherwise
        """
        with self._lock:
            if metric in self._counters:
                self._counters[metric].reset()
                return True
            elif metric in self._histograms:
                self._histograms[metric].reset()
                return True
            elif metric in self._gauges:
                del self._gauges[metric]
                return True
            return False
    
    def cleanup(self) -> None:
        """Clean up collector resources."""
        with self._lock:
            self._counters.clear()
            self._histograms.clear()
            self._gauges.clear()
            logger.info(f"Statistics collector '{self.name}' cleaned up")


# Global statistics collector instance
_global_stats_collector: Optional[StatsCollector] = None


def get_stats_collector() -> StatsCollector:
    """
    Get the global statistics collector instance.
    
    Returns:
        Global StatsCollector instance
    """
    global _global_stats_collector
    if _global_stats_collector is None:
        _global_stats_collector = StatsCollector("global_memory_foundation")
    return _global_stats_collector


def reset_stats_collector() -> None:
    """Reset the global statistics collector (for testing)."""
    global _global_stats_collector
    if _global_stats_collector:
        _global_stats_collector.cleanup()
    _global_stats_collector = None