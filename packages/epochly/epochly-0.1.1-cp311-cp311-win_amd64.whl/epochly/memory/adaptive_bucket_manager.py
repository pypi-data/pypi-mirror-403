"""
Adaptive Bucket Manager for Epochly Memory System

This module implements dynamic bucket creation and management for the hybrid
memory allocation system. It provides adaptive bucket sizing based on allocation
patterns and workload characteristics, optimizing memory allocation performance
through intelligent bucket selection and creation.

Author: Epochly Memory System
"""

import threading
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque

from .circuit_breaker import MemoryCircuitBreakerManager


class BucketStrategy(Enum):
    """Bucket creation strategies."""
    POWER_OF_TWO = "power_of_two"
    FIBONACCI = "fibonacci"
    ADAPTIVE = "adaptive"
    WORKLOAD_BASED = "workload_based"


@dataclass
class BucketMetrics:
    """Metrics for a specific bucket size."""
    size: int
    allocation_count: int = 0
    deallocation_count: int = 0
    hit_rate: float = 0.0
    fragmentation_ratio: float = 0.0
    last_access_time: float = 0.0
    average_hold_time: float = 0.0
    peak_usage: int = 0
    current_usage: int = 0


@dataclass
class BucketAllocationPattern:
    """Pattern analysis for allocation requests in bucket management."""
    size: int
    frequency: int
    last_seen: float
    trend: str  # "increasing", "decreasing", "stable"
    variance: float


class AdaptiveBucketManager:
    """
    Manages dynamic bucket creation and optimization for memory allocation.
    
    This manager analyzes allocation patterns and creates buckets dynamically
    to optimize memory allocation performance. It supports multiple bucket
    creation strategies and adapts to workload characteristics.
    """
    
    def __init__(self, 
                 initial_strategy: BucketStrategy = BucketStrategy.ADAPTIVE,
                 max_buckets: int = 64,
                 min_bucket_size: int = 16,
                 max_bucket_size: int = 1024 * 1024,
                 analysis_window: int = 1000,
                 adaptation_threshold: float = 0.1):
        """
        Initialize the adaptive bucket manager.
        
        Args:
            initial_strategy: Initial bucket creation strategy
            max_buckets: Maximum number of buckets to maintain
            min_bucket_size: Minimum bucket size in bytes
            max_bucket_size: Maximum bucket size in bytes
            analysis_window: Number of allocations to analyze for patterns
            adaptation_threshold: Threshold for triggering bucket adaptations
        """
        self.strategy = initial_strategy
        self.max_buckets = max_buckets
        self.min_bucket_size = min_bucket_size
        self.max_bucket_size = max_bucket_size
        self.analysis_window = analysis_window
        self.adaptation_threshold = adaptation_threshold
        
        # Bucket management
        self.buckets: Dict[int, BucketMetrics] = {}
        self.bucket_lock = threading.RLock()
        
        # Pattern analysis
        self.allocation_history: deque = deque(maxlen=analysis_window)
        self.size_patterns: Dict[int, BucketAllocationPattern] = {}
        self.pattern_lock = threading.Lock()
        
        # Performance tracking
        self.total_allocations = 0
        self.total_hits = 0
        self.total_misses = 0
        self.adaptation_count = 0
        self.last_adaptation_time = time.time()
        
        # Circuit breaker for bucket operations
        self.circuit_breaker = MemoryCircuitBreakerManager()
        
        # Initialize default buckets
        self._initialize_default_buckets()
    
    def _initialize_default_buckets(self) -> None:
        """Initialize default bucket sizes based on strategy."""
        if self.strategy == BucketStrategy.POWER_OF_TWO:
            sizes = self._generate_power_of_two_sizes()
        elif self.strategy == BucketStrategy.FIBONACCI:
            sizes = self._generate_fibonacci_sizes()
        else:
            sizes = self._generate_adaptive_sizes()
        
        with self.bucket_lock:
            for size in sizes:
                if self.min_bucket_size <= size <= self.max_bucket_size:
                    self.buckets[size] = BucketMetrics(size=size)
    
    def _generate_power_of_two_sizes(self) -> List[int]:
        """Generate bucket sizes using power of two strategy."""
        sizes = []
        size = self.min_bucket_size
        while size <= self.max_bucket_size and len(sizes) < self.max_buckets:
            sizes.append(size)
            size *= 2
        return sizes
    
    def _generate_fibonacci_sizes(self) -> List[int]:
        """Generate bucket sizes using Fibonacci sequence."""
        sizes = []
        a, b = self.min_bucket_size, self.min_bucket_size * 2
        
        while a <= self.max_bucket_size and len(sizes) < self.max_buckets:
            sizes.append(a)
            a, b = b, a + b
        
        return sizes
    
    def _generate_adaptive_sizes(self) -> List[int]:
        """Generate initial adaptive bucket sizes."""
        # Common allocation sizes based on typical usage patterns
        common_sizes = [16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]
        return [s for s in common_sizes 
                if self.min_bucket_size <= s <= self.max_bucket_size]
    
    def find_best_bucket(self, size: int) -> Optional[int]:
        """
        Find the best bucket size for the given allocation size.
        
        Args:
            size: Requested allocation size
            
        Returns:
            Best bucket size or None if no suitable bucket exists
        """
        with self.bucket_lock:
            # Find the smallest bucket that can accommodate the size
            suitable_buckets = [bucket_size for bucket_size in self.buckets.keys() 
                              if bucket_size >= size]
            
            if not suitable_buckets:
                return None
            
            # Return the smallest suitable bucket
            return min(suitable_buckets)
    
    def record_allocation(self, requested_size: int, bucket_size: Optional[int]) -> None:
        """
        Record an allocation request for pattern analysis.
        
        Args:
            requested_size: Size that was requested
            bucket_size: Bucket size that was used (None if no bucket was used)
        """
        current_time = time.time()
        
        # Record allocation history
        with self.pattern_lock:
            self.allocation_history.append((requested_size, bucket_size, current_time))
            self.total_allocations += 1
            
            if bucket_size is not None:
                self.total_hits += 1
                # Update bucket metrics
                with self.bucket_lock:
                    if bucket_size in self.buckets:
                        bucket = self.buckets[bucket_size]
                        bucket.allocation_count += 1
                        bucket.last_access_time = current_time
                        bucket.current_usage += 1
                        bucket.peak_usage = max(bucket.peak_usage, bucket.current_usage)
                        bucket.hit_rate = bucket.allocation_count / max(1, bucket.allocation_count + bucket.deallocation_count)
            else:
                self.total_misses += 1
            
            # Update size patterns
            if requested_size not in self.size_patterns:
                self.size_patterns[requested_size] = BucketAllocationPattern(
                    size=requested_size,
                    frequency=1,
                    last_seen=current_time,
                    trend="stable",
                    variance=0.0
                )
            else:
                pattern = self.size_patterns[requested_size]
                pattern.frequency += 1
                pattern.last_seen = current_time
        
        # Trigger adaptation if needed
        if self._should_adapt():
            self._adapt_buckets()
    
    def record_deallocation(self, bucket_size: int, hold_time: float) -> None:
        """
        Record a deallocation for metrics tracking.
        
        Args:
            bucket_size: Size of the bucket being deallocated
            hold_time: How long the allocation was held
        """
        with self.bucket_lock:
            if bucket_size in self.buckets:
                bucket = self.buckets[bucket_size]
                bucket.deallocation_count += 1
                bucket.current_usage = max(0, bucket.current_usage - 1)
                
                # Update average hold time
                if bucket.average_hold_time == 0:
                    bucket.average_hold_time = hold_time
                else:
                    bucket.average_hold_time = (bucket.average_hold_time * 0.9 + hold_time * 0.1)
    
    def _should_adapt(self) -> bool:
        """Check if bucket adaptation should be triggered."""
        current_time = time.time()
        
        # Adapt every 1000 allocations or every 60 seconds
        if (self.total_allocations % 1000 == 0 or 
            current_time - self.last_adaptation_time > 60):
            return True
        
        # Adapt if hit rate is below threshold
        if self.total_allocations > 100:
            hit_rate = self.total_hits / self.total_allocations
            if hit_rate < (1.0 - self.adaptation_threshold):
                return True
        
        return False
    
    def _adapt_buckets(self) -> None:
        """Adapt bucket sizes based on allocation patterns."""
        try:
            # Use circuit breaker to protect bucket adaptation
            try:
                self.circuit_breaker.get_breaker("bucket_adaptation").call(
                    self._perform_adaptation
                )
            except Exception:
                # Silently handle adaptation failures - circuit breaker will track them
                pass
        except Exception as e:
            # Log error but don't fail the allocation
            # Use logger from utils since this class doesn't have self.logger
            from ..utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Bucket adaptation failed: {e}")
    
    def _perform_adaptation(self) -> None:
        """Perform the actual bucket adaptation."""
        current_time = time.time()

        with self.pattern_lock:
            # Update adaptation metrics under lock to prevent races
            self.last_adaptation_time = current_time
            self.adaptation_count += 1
            # Analyze recent allocation patterns
            recent_allocations = [req for req, _, timestamp in self.allocation_history 
                                if current_time - timestamp < 300]  # Last 5 minutes
            
            if not recent_allocations:
                return
            
            # Find frequently requested sizes that don't have good buckets
            size_frequency = defaultdict(int)
            for size in recent_allocations:
                size_frequency[size] += 1
            
            # Sort by frequency
            frequent_sizes = sorted(size_frequency.items(), key=lambda x: x[1], reverse=True)
            
            # Consider adding buckets for frequent sizes
            candidates_to_add = []
            for size, frequency in frequent_sizes[:10]:  # Top 10 frequent sizes
                if frequency >= 5:  # Minimum frequency threshold
                    best_bucket = self.find_best_bucket(size)
                    if best_bucket is None or best_bucket > size * 1.5:
                        # No good bucket exists, consider adding one
                        optimal_size = self._calculate_optimal_bucket_size(size)
                        # Note: Duplicates and existing buckets handled under lock below
                        candidates_to_add.append((optimal_size, frequency))
            
            # Collect telemetry events to emit outside lock
            telemetry_events = []

            # Add new buckets if we have space
            with self.bucket_lock:
                candidates_to_add.sort(key=lambda x: x[1], reverse=True)  # Sort by frequency

                for bucket_size, _ in candidates_to_add:
                    if len(self.buckets) >= self.max_buckets:
                        # Remove least used bucket first, don't emit inside lock
                        shrink_event = self._remove_least_used_bucket(emit_telemetry=False)
                        if shrink_event:
                            telemetry_events.append(shrink_event)

                    if len(self.buckets) < self.max_buckets:
                        # Re-check under lock (handles races + duplicate candidates)
                        if bucket_size in self.buckets:
                            continue
                        # Enforce bucket size bounds (same as _initialize_default_buckets)
                        if not (self.min_bucket_size <= bucket_size <= self.max_bucket_size):
                            continue
                        old_total = sum(b.size for b in self.buckets.values())
                        self.buckets[bucket_size] = BucketMetrics(size=bucket_size)
                        new_total = sum(b.size for b in self.buckets.values())
                        # Capture event to emit outside lock (consistent with shrink pattern)
                        expand_event = ('expand', old_total, new_total, f'bucket_added_size_{bucket_size}')
                        telemetry_events.append(expand_event)

            # Update pattern trends
            self._update_pattern_trends()

        # Emit telemetry outside of locks (non-blocking)
        for event in telemetry_events:
            self._emit_allocator_telemetry(*event)
    
    def _calculate_optimal_bucket_size(self, requested_size: int) -> int:
        """Calculate optimal bucket size for a requested size."""
        # Round up to next power of 2 or use a more sophisticated algorithm
        if self.strategy == BucketStrategy.POWER_OF_TWO:
            size = 1
            while size < requested_size:
                size *= 2
            return min(size, self.max_bucket_size)
        else:
            # Use a more adaptive approach
            # Round up to nearest multiple of 16 for small sizes
            if requested_size <= 256:
                return ((requested_size + 15) // 16) * 16
            # Round up to nearest multiple of 64 for medium sizes
            elif requested_size <= 4096:
                return ((requested_size + 63) // 64) * 64
            # Round up to nearest multiple of 256 for large sizes
            else:
                return ((requested_size + 255) // 256) * 256
    
    def _remove_least_used_bucket(self, emit_telemetry: bool = True) -> Optional[Tuple[str, int, int, str]]:
        """
        Remove the least used bucket to make space for new ones.

        Args:
            emit_telemetry: If True, emit telemetry event immediately.
                           If False, return the event tuple for caller to emit later.
                           Use False when called from within a lock context.

        Returns:
            Tuple[str, int, int, str] of (operation, old_size, new_size, reason)
            if bucket removed, None otherwise.

        Note:
            Uses RLock (reentrant) so safe to call from within bucket_lock context.
        """
        shrink_event = None

        with self.bucket_lock:
            if not self.buckets:
                return None

            # Find bucket with lowest hit rate and recent usage
            current_time = time.time()
            worst_bucket = None
            worst_score = float('inf')

            for bucket_size, metrics in self.buckets.items():
                # Calculate a score based on hit rate, recent usage, and current usage
                age_factor = max(0.1, 1.0 - (current_time - metrics.last_access_time) / 3600)  # 1 hour decay
                usage_factor = max(0.1, metrics.hit_rate)
                current_usage_factor = 1.0 if metrics.current_usage > 0 else 0.5

                score = usage_factor * age_factor * current_usage_factor

                if score < worst_score:
                    worst_score = score
                    worst_bucket = bucket_size

            if worst_bucket is not None:
                old_total = sum(b.size for b in self.buckets.values())
                del self.buckets[worst_bucket]
                new_total = sum(b.size for b in self.buckets.values())
                # Capture event to emit outside lock
                shrink_event = ('shrink', old_total, new_total, f'bucket_removed_size_{worst_bucket}')

        # Emit telemetry outside of lock (non-blocking) only if requested
        if emit_telemetry and shrink_event:
            self._emit_allocator_telemetry(*shrink_event)

        return shrink_event
    
    def _update_pattern_trends(self) -> None:
        """Update allocation pattern trends."""
        current_time = time.time()
        
        for size, pattern in self.size_patterns.items():
            # Calculate trend based on recent frequency changes
            recent_count = sum(1 for req_size, _, timestamp in self.allocation_history
                             if req_size == size and current_time - timestamp < 300)
            
            older_count = sum(1 for req_size, _, timestamp in self.allocation_history
                            if req_size == size and 300 <= current_time - timestamp < 600)
            
            if older_count > 0:
                trend_ratio = recent_count / older_count
                if trend_ratio > 1.2:
                    pattern.trend = "increasing"
                elif trend_ratio < 0.8:
                    pattern.trend = "decreasing"
                else:
                    pattern.trend = "stable"
    
    def get_bucket_statistics(self) -> Dict:
        """Get comprehensive bucket statistics."""
        with self.bucket_lock:
            stats = {
                "total_buckets": len(self.buckets),
                "total_allocations": self.total_allocations,
                "total_hits": self.total_hits,
                "total_misses": self.total_misses,
                "hit_rate": self.total_hits / max(1, self.total_allocations),
                "adaptation_count": self.adaptation_count,
                "strategy": self.strategy.value,
                "buckets": {}
            }
            
            for bucket_size, metrics in self.buckets.items():
                stats["buckets"][bucket_size] = {
                    "size": metrics.size,
                    "allocation_count": metrics.allocation_count,
                    "deallocation_count": metrics.deallocation_count,
                    "hit_rate": metrics.hit_rate,
                    "current_usage": metrics.current_usage,
                    "peak_usage": metrics.peak_usage,
                    "average_hold_time": metrics.average_hold_time,
                    "fragmentation_ratio": metrics.fragmentation_ratio
                }
            
            return stats
    
    def optimize_buckets(self) -> None:
        """Manually trigger bucket optimization."""
        self._adapt_buckets()
    
    def reset_statistics(self) -> None:
        """Reset all statistics and metrics."""
        with self.bucket_lock:
            for metrics in self.buckets.values():
                metrics.allocation_count = 0
                metrics.deallocation_count = 0
                metrics.hit_rate = 0.0
                metrics.current_usage = 0
                metrics.peak_usage = 0
                metrics.average_hold_time = 0.0
        
        with self.pattern_lock:
            self.allocation_history.clear()
            self.size_patterns.clear()
            self.total_allocations = 0
            self.total_hits = 0
            self.total_misses = 0
            self.adaptation_count = 0

    def _emit_allocator_telemetry(
        self, operation: str, old_size: int, new_size: int, reason: str
    ) -> None:
        """
        Emit allocator telemetry event (non-blocking).

        Args:
            operation: 'expand' or 'shrink'
            old_size: Previous total bucket capacity
            new_size: New total bucket capacity
            reason: Reason for the change
        """
        try:
            from epochly.telemetry.routing_events import get_routing_emitter
            emitter = get_routing_emitter()
            if emitter:
                emitter.emit_allocator_event(
                    operation=operation,
                    old_size=old_size,
                    new_size=new_size,
                    reason=reason,
                    pool_type='adaptive_bucket'
                )
        except Exception:
            pass  # Telemetry failures must not affect allocator operations