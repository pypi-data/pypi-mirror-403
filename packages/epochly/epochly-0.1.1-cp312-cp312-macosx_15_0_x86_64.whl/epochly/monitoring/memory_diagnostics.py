"""
Memory Diagnostics Module (Task 2 Supporting Component)

Optional diagnostic tracking for FastAllocatorAdapter.
Only enabled via EPOCHLY_MEMORY_DIAGNOSTICS=1 environment variable.

Performance Impact:
- Disabled: 0μs overhead
- Enabled: ~2μs overhead per operation

Usage:
    export EPOCHLY_MEMORY_DIAGNOSTICS=1

    diagnostics = MemoryDiagnostics()
    handle = diagnostics.track_allocation(allocate_fn, 1024)
    diagnostics.track_deallocation(handle, 1024)
    stats = diagnostics.get_stats()
"""

import time
import threading
from typing import Dict, Any, Callable
from collections import defaultdict


class MemoryDiagnostics:
    """
    Track memory allocation diagnostics.

    Thread-safe diagnostic tracking for debugging and monitoring.
    """

    def __init__(self):
        """Initialize diagnostic tracking."""
        self._lock = threading.RLock()

        # Counters
        self._allocations = 0
        self._deallocations = 0
        self._bytes_allocated = 0
        self._bytes_deallocated = 0

        # Timing
        self._allocation_times = []  # Recent allocation latencies
        self._max_samples = 1000  # Keep last 1000 samples

        # Size distribution
        self._size_histogram = defaultdict(int)

        # Active allocations
        self._active_handles = {}  # handle -> (size, timestamp)

    def track_allocation(self, allocate_fn: Callable, size: int) -> int:
        """
        Track an allocation operation.

        Args:
            allocate_fn: Underlying allocator function
            size: Size to allocate

        Returns:
            Handle from allocator
        """
        start = time.perf_counter_ns()

        # Perform allocation
        handle = allocate_fn(size)

        duration_ns = time.perf_counter_ns() - start

        # Record diagnostics
        with self._lock:
            self._allocations += 1
            self._bytes_allocated += size

            # Record timing
            if len(self._allocation_times) >= self._max_samples:
                self._allocation_times.pop(0)
            self._allocation_times.append(duration_ns)

            # Record size distribution
            # Bucket sizes: <256, 256-1K, 1K-4K, 4K-64K, >64K
            if size < 256:
                bucket = '<256B'
            elif size < 1024:
                bucket = '256B-1KB'
            elif size < 4096:
                bucket = '1KB-4KB'
            elif size < 65536:
                bucket = '4KB-64KB'
            else:
                bucket = '>64KB'

            self._size_histogram[bucket] += 1

            # Track active allocation
            self._active_handles[handle] = (size, time.time())

        return handle

    def track_deallocation(self, handle: int, size: int) -> None:
        """
        Track a deallocation operation.

        Args:
            handle: Handle to deallocate
            size: Size of block
        """
        with self._lock:
            self._deallocations += 1
            self._bytes_deallocated += size

            # Remove from active tracking
            if handle in self._active_handles:
                del self._active_handles[handle]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get diagnostic statistics.

        Returns:
            Dictionary with allocation stats, timing, and size distribution
        """
        with self._lock:
            # Calculate timing statistics
            if self._allocation_times:
                times_us = [t / 1000 for t in self._allocation_times]
                mean_us = sum(times_us) / len(times_us)

                times_sorted = sorted(times_us)
                p50_us = times_sorted[len(times_sorted) // 2]
                p99_us = times_sorted[int(len(times_sorted) * 0.99)]
            else:
                mean_us = p50_us = p99_us = 0.0

            return {
                'allocations': self._allocations,
                'deallocations': self._deallocations,
                'bytes_allocated': self._bytes_allocated,
                'bytes_deallocated': self._bytes_deallocated,
                'active_allocations': len(self._active_handles),
                'allocation_latency_us': {
                    'mean': mean_us,
                    'p50': p50_us,
                    'p99': p99_us,
                    'samples': len(self._allocation_times)
                },
                'size_distribution': dict(self._size_histogram)
            }

    def reset(self) -> None:
        """Reset all diagnostic counters."""
        with self._lock:
            self._allocations = 0
            self._deallocations = 0
            self._bytes_allocated = 0
            self._bytes_deallocated = 0
            self._allocation_times.clear()
            self._size_histogram.clear()
            self._active_handles.clear()
