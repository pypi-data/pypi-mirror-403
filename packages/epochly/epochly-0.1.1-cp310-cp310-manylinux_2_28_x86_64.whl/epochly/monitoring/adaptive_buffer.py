"""
Adaptive Metric Buffer (SPEC2 Task 8)

Dynamically adjusts buffer size based on metric cardinality and update frequency.

Benefits:
- Memory footprint adapts to workload
- High-cardinality metrics get larger buffers
- Low-cardinality metrics release memory
- Maintains reporting fidelity

Architecture:
- Monitors update rate per metric
- Scales buffer size within bounds
- Periodic rebalancing
- Thread-safe resizing
"""

import threading
import time
from collections import deque
from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class BufferConfig:
    """Configuration for adaptive buffer."""

    min_capacity: int = 100  # Minimum buffer size
    max_capacity: int = 10000  # Maximum buffer size
    initial_capacity: int = 1000  # Starting size

    # Thresholds for scaling
    high_rate_threshold: float = 100.0  # Updates/sec to scale up
    low_rate_threshold: float = 1.0  # Updates/sec to scale down

    # Rebalancing
    rebalance_interval_seconds: float = 60.0  # How often to rebalance


class AdaptiveBuffer:
    """
    Dynamically-sized buffer that adapts to metric update frequency.

    Scales buffer capacity based on observed cardinality and update rate.

    Example:
        buffer = AdaptiveBuffer()

        # Add samples
        for value in values:
            buffer.append(value)

        # Buffer auto-adjusts capacity based on rate
        # Get current data
        data = list(buffer)
    """

    def __init__(self, config: Optional[BufferConfig] = None):
        """
        Initialize adaptive buffer.

        Args:
            config: Optional buffer configuration
        """
        self._config = config or BufferConfig()
        self._lock = threading.Lock()

        # Dynamic buffer
        self._capacity = self._config.initial_capacity
        self._buffer = deque(maxlen=self._capacity)

        # Rate tracking
        self._last_append_time = time.time()
        self._append_count = 0
        self._last_rebalance = time.time()

        # Statistics
        self._total_appends = 0
        self._resize_count = 0

    def append(self, sample: Any) -> None:
        """
        Append sample to buffer.

        Args:
            sample: Sample to append
        """
        with self._lock:
            self._buffer.append(sample)
            self._append_count += 1
            self._total_appends += 1

            # Check if need to rebalance
            now = time.time()
            if now - self._last_rebalance >= self._config.rebalance_interval_seconds:
                self._maybe_adjust_capacity(now)

    def _maybe_adjust_capacity(self, now: float) -> None:
        """
        Adjust buffer capacity based on observed rate.

        Must be called with _lock held.

        Args:
            now: Current timestamp
        """
        # Calculate update rate
        time_window = now - self._last_rebalance
        if time_window == 0:
            return

        observed_rate = self._append_count / time_window

        # Determine new capacity
        new_capacity = self._capacity

        if observed_rate > self._config.high_rate_threshold:
            # High rate - scale up
            new_capacity = min(self._config.max_capacity, int(self._capacity * 1.5))

        elif observed_rate < self._config.low_rate_threshold:
            # Low rate - scale down
            new_capacity = max(self._config.min_capacity, int(self._capacity * 0.75))

        # Apply capacity change if significant
        if new_capacity != self._capacity:
            self._resize_buffer(new_capacity)

        # Reset tracking
        self._append_count = 0
        self._last_rebalance = now

    def _resize_buffer(self, new_capacity: int) -> None:
        """
        Resize buffer to new capacity.

        Must be called with _lock held.

        Args:
            new_capacity: New buffer capacity
        """
        if new_capacity == self._capacity:
            return

        # Create new buffer with new capacity
        new_buffer = deque(self._buffer, maxlen=new_capacity)

        self._buffer = new_buffer
        self._capacity = new_capacity
        self._resize_count += 1

    def __iter__(self):
        """Iterate over buffer contents."""
        with self._lock:
            return iter(list(self._buffer))

    def __len__(self) -> int:
        """Get current buffer size."""
        with self._lock:
            return len(self._buffer)

    def get_capacity(self) -> int:
        """Get current buffer capacity."""
        return self._capacity

    def get_stats(self) -> dict:
        """
        Get buffer statistics.

        Returns:
            Statistics dictionary
        """
        with self._lock:
            return {
                'capacity': self._capacity,
                'size': len(self._buffer),
                'utilization': len(self._buffer) / self._capacity if self._capacity > 0 else 0.0,
                'total_appends': self._total_appends,
                'resize_count': self._resize_count,
                'min_capacity': self._config.min_capacity,
                'max_capacity': self._config.max_capacity
            }

    def clear(self) -> None:
        """Clear buffer contents."""
        with self._lock:
            self._buffer.clear()
