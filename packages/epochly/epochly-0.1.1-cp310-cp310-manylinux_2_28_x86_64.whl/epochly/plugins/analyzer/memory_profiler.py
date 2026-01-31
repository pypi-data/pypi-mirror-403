"""
Epochly Memory Profiler

This module implements the MemoryProfiler component that tracks memory allocation
patterns, usage statistics, and fragmentation analysis for optimal pool selection.

Author: Epochly Development Team
"""

import time
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import statistics



class AllocationPattern(Enum):
    """Memory allocation patterns detected by the profiler."""
    SEQUENTIAL = "sequential"
    RANDOM = "random"
    BURST = "burst"
    STEADY = "steady"
    LARGE_BLOCKS = "large_blocks"
    SMALL_FREQUENT = "small_frequent"


@dataclass
class MemoryStats:
    """Memory usage statistics for a time window."""
    total_allocated: int = 0
    total_freed: int = 0
    peak_usage: int = 0
    current_usage: int = 0
    allocation_count: int = 0
    deallocation_count: int = 0
    average_allocation_size: float = 0.0
    fragmentation_ratio: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class AllocationInfo:
    """Information about a memory allocation."""
    size: int
    timestamp: float
    thread_id: int
    address: Optional[int] = None
    freed: bool = False
    free_timestamp: Optional[float] = None


class MemoryProfiler:
    """
    Memory profiler for tracking allocation patterns and usage statistics.
    
    This component provides detailed memory usage analysis to support
    intelligent pool selection and optimization decisions.
    """
    
    def __init__(self, window_size: float = 10.0, max_allocations: int = 50000, sampling_rate: float = 0.1):
        """
        Initialize the memory profiler.

        Args:
            window_size: Time window for statistics calculation (seconds)
            max_allocations: Maximum number of allocations to track
            sampling_rate: SPEC2 Task 9 - Sample rate for allocation tracking (0.0-1.0)
        """
        self._window_size = window_size
        self._max_allocations = max_allocations
        self._sampling_rate = sampling_rate  # SPEC2 Task 9: Probabilistic sampling

        # Allocation tracking
        self._allocations: deque = deque(maxlen=max_allocations)
        self._active_allocations: Dict[int, AllocationInfo] = {}
        self._stats_history: deque = deque(maxlen=1000)

        # SPEC2 Task 9: Sampling statistics
        self._total_allocations = 0
        self._sampled_allocations = 0
        self._large_allocation_threshold = 1024 * 1024  # Always sample >1MB
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Pattern detection
        self._pattern_thresholds = {
            "burst_threshold": 100,  # allocations per second
            "large_block_threshold": 1024 * 1024,  # 1MB
            "small_frequent_threshold": 1024,  # 1KB
            "fragmentation_threshold": 0.3  # 30%
        }
        
        # Current statistics
        self._current_stats = MemoryStats()
        
    def record_allocation(
        self,
        size: int,
        address: Optional[int] = None,
        thread_id: Optional[int] = None
    ) -> None:
        """
        Record a memory allocation event.

        SPEC2 Task 9: Uses probabilistic sampling to reduce overhead.
        - Large allocations (>1MB) always recorded
        - Small allocations sampled at configured rate

        Args:
            size: Size of the allocation in bytes
            address: Memory address (optional)
            thread_id: Thread ID (optional, uses current thread if None)
        """
        # SPEC2 Task 9: Probabilistic sampling (size-biased + rate-limited)
        self._total_allocations += 1

        # Always sample large allocations
        should_sample = size >= self._large_allocation_threshold

        if not should_sample:
            # Probabilistic sampling for small allocations
            import random
            should_sample = random.random() < self._sampling_rate

        if not should_sample:
            # Sampled out - skip recording
            return

        # Sample accepted - record allocation
        self._sampled_allocations += 1

        if thread_id is None:
            thread_id = threading.get_ident()

        allocation = AllocationInfo(
            size=size,
            timestamp=time.time(),
            thread_id=thread_id,
            address=address
        )

        with self._lock:
            self._allocations.append(allocation)
            if address is not None:
                self._active_allocations[address] = allocation

            # Update current statistics
            self._current_stats.total_allocated += size
            self._current_stats.current_usage += size
            self._current_stats.allocation_count += 1
            
            if self._current_stats.current_usage > self._current_stats.peak_usage:
                self._current_stats.peak_usage = self._current_stats.current_usage
    
    def record_deallocation(self, address: int, size: Optional[int] = None) -> None:
        """
        Record a memory deallocation event.
        
        Args:
            address: Memory address being freed
            size: Size of the deallocation (optional, inferred if None)
        """
        with self._lock:
            if address in self._active_allocations:
                allocation = self._active_allocations[address]
                allocation.freed = True
                allocation.free_timestamp = time.time()
                
                freed_size = allocation.size
                del self._active_allocations[address]
            else:
                freed_size = size or 0
            
            # Update current statistics
            self._current_stats.total_freed += freed_size
            self._current_stats.current_usage -= freed_size
            self._current_stats.deallocation_count += 1
    
    def get_current_stats(self) -> MemoryStats:
        """Get current memory usage statistics."""
        with self._lock:
            # Update calculated fields
            if self._current_stats.allocation_count > 0:
                self._current_stats.average_allocation_size = (
                    self._current_stats.total_allocated / self._current_stats.allocation_count
                    if self._current_stats.allocation_count > 0 else 0
                )
            
            self._current_stats.fragmentation_ratio = self._calculate_fragmentation()
            self._current_stats.timestamp = time.time()
            
            return MemoryStats(
                total_allocated=self._current_stats.total_allocated,
                total_freed=self._current_stats.total_freed,
                peak_usage=self._current_stats.peak_usage,
                current_usage=self._current_stats.current_usage,
                allocation_count=self._current_stats.allocation_count,
                deallocation_count=self._current_stats.deallocation_count,
                average_allocation_size=self._current_stats.average_allocation_size,
                fragmentation_ratio=self._current_stats.fragmentation_ratio,
                timestamp=self._current_stats.timestamp
            )
    
    def get_window_stats(self, window_seconds: Optional[float] = None) -> MemoryStats:
        """
        Get memory statistics for a specific time window.
        
        Args:
            window_seconds: Time window in seconds (uses default if None)
            
        Returns:
            Memory statistics for the specified window
        """
        if window_seconds is None:
            window_seconds = self._window_size
            
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        with self._lock:
            # Filter allocations within the window
            window_allocations = [
                alloc for alloc in self._allocations
                if alloc.timestamp >= cutoff_time
            ]
            
            if not window_allocations:
                return MemoryStats(timestamp=current_time)
            
            # Calculate window statistics
            total_allocated = sum(alloc.size for alloc in window_allocations)
            allocation_count = len(window_allocations)
            
            # Calculate deallocations in window
            window_deallocations = [
                alloc for alloc in window_allocations
                if alloc.freed and alloc.free_timestamp and alloc.free_timestamp >= cutoff_time
            ]
            
            total_freed = sum(alloc.size for alloc in window_deallocations)
            deallocation_count = len(window_deallocations)
            
            # Calculate other metrics
            average_size = total_allocated / allocation_count if allocation_count > 0 else 0.0
            current_usage = total_allocated - total_freed
            peak_usage = self._calculate_peak_usage_in_window(window_allocations, cutoff_time)
            fragmentation = self._calculate_fragmentation_in_window(window_allocations)
            
            return MemoryStats(
                total_allocated=total_allocated,
                total_freed=total_freed,
                peak_usage=peak_usage,
                current_usage=current_usage,
                allocation_count=allocation_count,
                deallocation_count=deallocation_count,
                average_allocation_size=average_size,
                fragmentation_ratio=fragmentation,
                timestamp=current_time
            )
    
    def detect_allocation_pattern(self, window_seconds: Optional[float] = None) -> AllocationPattern:
        """
        Detect the current allocation pattern.
        
        Args:
            window_seconds: Time window for pattern detection
            
        Returns:
            Detected allocation pattern
        """
        if window_seconds is None:
            window_seconds = self._window_size
            
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        with self._lock:
            window_allocations = [
                alloc for alloc in self._allocations
                if alloc.timestamp >= cutoff_time
            ]
            
            if not window_allocations:
                return AllocationPattern.STEADY
            
            # Analyze allocation patterns
            allocation_rate = len(window_allocations) / window_seconds
            sizes = [alloc.size for alloc in window_allocations]
            
            # Check for burst pattern
            if allocation_rate > self._pattern_thresholds["burst_threshold"]:
                return AllocationPattern.BURST
            
            # Check for large blocks
            large_blocks = sum(1 for size in sizes if size > self._pattern_thresholds["large_block_threshold"])
            if len(sizes) > 0 and large_blocks / len(sizes) > 0.5:
                return AllocationPattern.LARGE_BLOCKS
            
            # Check for small frequent allocations
            small_allocations = sum(1 for size in sizes if size < self._pattern_thresholds["small_frequent_threshold"])
            if len(sizes) > 0 and small_allocations / len(sizes) > 0.8 and allocation_rate > 10:
                return AllocationPattern.SMALL_FREQUENT
            
            # Check for sequential vs random pattern
            if self._is_sequential_pattern(window_allocations):
                return AllocationPattern.SEQUENTIAL
            elif self._is_random_pattern(window_allocations):
                return AllocationPattern.RANDOM
            else:
                return AllocationPattern.STEADY
    
    def get_allocation_size_distribution(self, window_seconds: Optional[float] = None) -> Dict[str, Any]:
        """
        Get allocation size distribution statistics.
        
        Args:
            window_seconds: Time window for analysis
            
        Returns:
            Size distribution statistics
        """
        if window_seconds is None:
            window_seconds = self._window_size
            
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        with self._lock:
            window_allocations = [
                alloc for alloc in self._allocations
                if alloc.timestamp >= cutoff_time
            ]
            
            if not window_allocations:
                return {"count": 0}
            
            sizes = [alloc.size for alloc in window_allocations]
            
            # Calculate distribution statistics
            return {
                "count": len(sizes),
                "min_size": min(sizes),
                "max_size": max(sizes),
                "mean_size": statistics.mean(sizes),
                "median_size": statistics.median(sizes),
                "std_dev": statistics.stdev(sizes) if len(sizes) > 1 else 0.0,
                "percentiles": {
                    "p25": self._percentile(sizes, 25),
                    "p50": self._percentile(sizes, 50),
                    "p75": self._percentile(sizes, 75),
                    "p90": self._percentile(sizes, 90),
                    "p95": self._percentile(sizes, 95),
                    "p99": self._percentile(sizes, 99)
                },
                "size_buckets": self._calculate_size_buckets(sizes)
            }
    
    def get_thread_activity(self, window_seconds: Optional[float] = None) -> Dict[int, Dict[str, Any]]:
        """
        Get per-thread allocation activity.
        
        Args:
            window_seconds: Time window for analysis
            
        Returns:
            Per-thread activity statistics
        """
        if window_seconds is None:
            window_seconds = self._window_size
            
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        with self._lock:
            window_allocations = [
                alloc for alloc in self._allocations
                if alloc.timestamp >= cutoff_time
            ]
            
            # Group by thread
            thread_activity = defaultdict(list)
            for alloc in window_allocations:
                thread_activity[alloc.thread_id].append(alloc)
            
            # Calculate per-thread statistics
            result = {}
            for thread_id, allocations in thread_activity.items():
                sizes = [alloc.size for alloc in allocations]
                result[thread_id] = {
                    "allocation_count": len(allocations),
                    "total_allocated": sum(sizes),
                    "average_size": statistics.mean(sizes),
                    "allocation_rate": len(allocations) / window_seconds
                }
            
            return result
    
    def reset_stats(self) -> None:
        """Reset all statistics and tracking data."""
        with self._lock:
            self._allocations.clear()
            self._active_allocations.clear()
            self._stats_history.clear()
            self._current_stats = MemoryStats()
    
    def _calculate_fragmentation(self) -> float:
        """Calculate current memory fragmentation ratio."""
        with self._lock:
            if not self._active_allocations:
                return 0.0
            
            # Simple fragmentation calculation based on allocation size variance
            sizes = [alloc.size for alloc in self._active_allocations.values()]
            if len(sizes) < 2:
                return 0.0
            
            mean_size = statistics.mean(sizes)
            variance = statistics.variance(sizes)
            
            # Normalize fragmentation ratio
            return min(variance / (mean_size * mean_size) if mean_size > 0 else 0.0, 1.0)
    
    def _calculate_peak_usage_in_window(
        self, 
        allocations: List[AllocationInfo], 
        cutoff_time: float
    ) -> int:
        """Calculate peak memory usage within a time window."""
        if not allocations:
            return 0
        
        # Sort allocations by timestamp
        events = []
        for alloc in allocations:
            events.append((alloc.timestamp, alloc.size, 'alloc'))
            if alloc.freed and alloc.free_timestamp and alloc.free_timestamp >= cutoff_time:
                events.append((alloc.free_timestamp, -alloc.size, 'free'))
        
        events.sort(key=lambda x: x[0])
        
        # Calculate peak usage
        current_usage = 0
        peak_usage = 0
        
        for timestamp, size_delta, event_type in events:
            current_usage += size_delta
            peak_usage = max(peak_usage, current_usage)
        
        return peak_usage
    
    def _calculate_fragmentation_in_window(self, allocations: List[AllocationInfo]) -> float:
        """Calculate fragmentation ratio for allocations in a window."""
        if len(allocations) < 2:
            return 0.0
        
        sizes = [alloc.size for alloc in allocations]
        mean_size = statistics.mean(sizes)
        variance = statistics.variance(sizes)
        
        return min(variance / (mean_size * mean_size) if mean_size > 0 else 0.0, 1.0)
    
    def _is_sequential_pattern(self, allocations: List[AllocationInfo]) -> bool:
        """Check if allocations follow a sequential pattern."""
        if len(allocations) < 3:
            return False
        
        # Check if allocation sizes are relatively consistent
        sizes = [alloc.size for alloc in allocations]
        mean_size = statistics.mean(sizes)
        std_dev = statistics.stdev(sizes) if len(sizes) > 1 else 0
        
        # Sequential pattern: low variance in size and timing
        size_consistency = (std_dev / mean_size) < 0.2 if mean_size > 0 else False
        
        # Check timing consistency
        timestamps = [alloc.timestamp for alloc in allocations]
        time_diffs = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        # Guard against zero mean (all time_diffs are zero)
        mean_time = statistics.mean(time_diffs) if time_diffs else 0
        time_consistency = (
            (statistics.stdev(time_diffs) / mean_time) < 0.5
            if time_diffs and mean_time != 0
            else False
        )
        
        return size_consistency and time_consistency
    
    def _is_random_pattern(self, allocations: List[AllocationInfo]) -> bool:
        """Check if allocations follow a random pattern."""
        if len(allocations) < 5:
            return False
        
        # Random pattern: high variance in both size and timing
        sizes = [alloc.size for alloc in allocations]
        mean_size = statistics.mean(sizes)
        std_dev = statistics.stdev(sizes) if len(sizes) > 1 else 0
        
        return (std_dev / mean_size) > 0.5 if mean_size > 0 else False
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of a dataset."""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100.0) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _calculate_size_buckets(self, sizes: List[int]) -> Dict[str, int]:
        """Calculate allocation count by size buckets."""
        buckets = {
            "tiny": 0,      # < 1KB
            "small": 0,     # 1KB - 64KB
            "medium": 0,    # 64KB - 1MB
            "large": 0,     # 1MB - 16MB
            "huge": 0       # > 16MB
        }
        
        for size in sizes:
            if size < 1024:
                buckets["tiny"] += 1
            elif size < 64 * 1024:
                buckets["small"] += 1
            elif size < 1024 * 1024:
                buckets["medium"] += 1
            elif size < 16 * 1024 * 1024:
                buckets["large"] += 1
            else:
                buckets["huge"] += 1
        
        return buckets