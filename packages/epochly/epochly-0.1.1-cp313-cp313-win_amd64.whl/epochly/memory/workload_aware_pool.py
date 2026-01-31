"""
Epochly Memory Foundation - Workload-Aware Memory Pool

This module implements workload-specific memory pool selection and optimization
based on detected usage patterns and application characteristics.

Author: Epochly Memory Foundation Team
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass

from .memory_pool import MemoryPool
from .memory_block import MemoryBlock
from .fast_memory_pool import FastMemoryPool
from .sharded_memory_pool import ShardedMemoryPool
from .fine_grained_memory_pool import FineGrainedMemoryPool
from .workload_type import WorkloadType
from .exceptions import AllocationError
from .atomic_primitives import AtomicCounter, LockFreeStatistics

# Type checking imports to avoid circular dependencies
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .lock_free_memory_pool import LockFreeMemoryPool

# Type alias for memory pool types
MemoryPoolType = Union[MemoryPool, FastMemoryPool, ShardedMemoryPool, FineGrainedMemoryPool, 'LockFreeMemoryPool']

logger = logging.getLogger(__name__)


@dataclass
class WorkloadCharacteristics:
    """Characteristics of a detected workload."""
    allocation_frequency: float      # Allocations per second
    average_allocation_size: int     # Average size in bytes
    allocation_size_variance: float  # Variance in allocation sizes
    deallocation_pattern: str        # "immediate", "batched", "delayed"
    concurrency_level: int          # Number of concurrent threads
    memory_pressure: float          # Memory usage ratio
    temporal_locality: float        # Reuse pattern score
    spatial_locality: float         # Adjacent access pattern score


class WorkloadDetector:
    """
    Detects workload patterns and characteristics for optimal pool selection.
    
    Analyzes allocation patterns, sizes, timing, and concurrency to classify
    the workload type and recommend appropriate memory pool configurations.
    """
    
    def __init__(self, analysis_window: float = 60.0):
        """
        Initialize workload detector.
        
        Args:
            analysis_window: Time window for pattern analysis in seconds
        """
        self.analysis_window = analysis_window
        
        # Pattern tracking
        self.allocation_times = []
        self.allocation_sizes = []
        self.deallocation_times = []
        self.thread_counts = AtomicCounter()
        self.memory_usage = AtomicCounter()
        
        # Statistics
        self.stats = LockFreeStatistics()
        self._lock = threading.RLock()
        
        # Detection state
        self.last_analysis_time = 0.0
        self.current_workload = WorkloadType.UNKNOWN
        self.confidence_score = 0.0
        
    def record_allocation(self, size: int, thread_id: int) -> None:
        """Record an allocation event for pattern analysis."""
        current_time = time.perf_counter()
        
        with self._lock:
            self.allocation_times.append(current_time)
            self.allocation_sizes.append(size)
            
            # Trim old data outside analysis window
            cutoff_time = current_time - self.analysis_window
            self.allocation_times = [t for t in self.allocation_times if t > cutoff_time]
            self.allocation_sizes = self.allocation_sizes[-len(self.allocation_times):]
            
        self.memory_usage.increment(size)
        self.stats.record_allocation(size=size, is_bucketed=True, padding=0, time_ns=0)
    
    def record_deallocation(self, size: int, thread_id: int) -> None:
        """Record a deallocation event for pattern analysis."""
        current_time = time.perf_counter()
        
        with self._lock:
            self.deallocation_times.append(current_time)
            
            # Trim old data
            cutoff_time = current_time - self.analysis_window
            self.deallocation_times = [t for t in self.deallocation_times if t > cutoff_time]
            
        self.memory_usage.decrement(size)
        self.stats.record_deallocation(size=size, time_ns=0)
    
    def analyze_workload(self) -> WorkloadCharacteristics:
        """Analyze current workload patterns and return characteristics."""
        current_time = time.perf_counter()
        
        with self._lock:
            if not self.allocation_times:
                return WorkloadCharacteristics(
                    allocation_frequency=0.0,
                    average_allocation_size=0,
                    allocation_size_variance=0.0,
                    deallocation_pattern="unknown",
                    concurrency_level=1,
                    memory_pressure=0.0,
                    temporal_locality=0.0,
                    spatial_locality=0.0
                )
            
            # Calculate allocation frequency
            time_span = max(current_time - min(self.allocation_times), 1.0)
            allocation_frequency = len(self.allocation_times) / time_span
            
            # Calculate size statistics
            avg_size = sum(self.allocation_sizes) / len(self.allocation_sizes)
            size_variance = sum((s - avg_size) ** 2 for s in self.allocation_sizes) / len(self.allocation_sizes)
            
            # Analyze deallocation pattern
            deallocation_pattern = self._analyze_deallocation_pattern()
            
            # Estimate concurrency (simplified)
            concurrency_level = max(1, self.thread_counts.load())
            
            # Calculate memory pressure (simplified)
            memory_pressure = min(1.0, self.memory_usage.load() / (1024 * 1024 * 100))  # Assume 100MB baseline
            
            # Calculate locality scores (simplified heuristics)
            temporal_locality = self._calculate_temporal_locality()
            spatial_locality = self._calculate_spatial_locality()
            
            return WorkloadCharacteristics(
                allocation_frequency=allocation_frequency,
                average_allocation_size=int(avg_size),
                allocation_size_variance=size_variance,
                deallocation_pattern=deallocation_pattern,
                concurrency_level=concurrency_level,
                memory_pressure=memory_pressure,
                temporal_locality=temporal_locality,
                spatial_locality=spatial_locality
            )
    
    def _analyze_deallocation_pattern(self) -> str:
        """Analyze deallocation timing patterns."""
        if not self.deallocation_times or not self.allocation_times:
            return "unknown"
        
        # Simple heuristic based on timing
        alloc_dealloc_ratio = len(self.allocation_times) / max(len(self.deallocation_times), 1)
        
        if alloc_dealloc_ratio > 2.0:
            return "delayed"
        elif alloc_dealloc_ratio < 0.8:
            return "immediate"
        else:
            return "batched"
    
    def _calculate_temporal_locality(self) -> float:
        """Calculate temporal locality score (0.0 to 1.0)."""
        if len(self.allocation_sizes) < 2:
            return 0.0
        
        # Simple heuristic: how often similar sizes are allocated close in time
        similar_pairs = 0
        total_pairs = 0
        
        for i in range(len(self.allocation_sizes) - 1):
            for j in range(i + 1, min(i + 10, len(self.allocation_sizes))):  # Look ahead 10 allocations
                total_pairs += 1
                size_diff = abs(self.allocation_sizes[i] - self.allocation_sizes[j])
                if size_diff < self.allocation_sizes[i] * 0.1:  # Within 10% of size
                    similar_pairs += 1
        
        return similar_pairs / max(total_pairs, 1)
    
    def _calculate_spatial_locality(self) -> float:
        """Calculate spatial locality score (0.0 to 1.0)."""
        # Simplified heuristic based on allocation size patterns
        if len(self.allocation_sizes) < 5:
            return 0.0
        
        # Look for patterns in allocation sizes that suggest spatial locality
        pattern_score = 0.0
        window_size = 5
        
        for i in range(len(self.allocation_sizes) - window_size):
            window = self.allocation_sizes[i:i + window_size]
            avg_size = sum(window) / len(window)
            variance = sum((s - avg_size) ** 2 for s in window) / len(window)
            
            # Low variance suggests spatial locality
            if variance < avg_size * 0.1:
                pattern_score += 1.0
        
        return pattern_score / max(len(self.allocation_sizes) - window_size, 1)
    
    def detect_workload_type(self) -> WorkloadType:
        """Detect and classify the current workload type."""
        characteristics = self.analyze_workload()
        
        # Classification rules based on characteristics
        if characteristics.average_allocation_size > 64 * 1024:  # > 64KB
            if characteristics.allocation_frequency > 1000:  # High frequency
                return WorkloadType.NUMPY_HEAVY
            else:
                return WorkloadType.MEMORY_INTENSIVE
        
        elif characteristics.concurrency_level > 4:  # High concurrency
            if characteristics.allocation_frequency > 5000:  # Very high frequency
                return WorkloadType.CPU_BOUND
            else:
                return WorkloadType.MIXED
        
        elif characteristics.allocation_frequency < 100:  # Low frequency
            return WorkloadType.IO_BOUND
        
        elif characteristics.temporal_locality > 0.7:  # High temporal locality
            return WorkloadType.PURE_PYTHON_LOOPS
        
        else:
            return WorkloadType.MIXED


class WorkloadAwareMemoryPool:
    """
    Workload-aware memory pool that automatically selects and configures
    the optimal memory pool implementation based on detected usage patterns.
    """
    
    # Default pool size: 4 MiB
    DEFAULT_TOTAL_SIZE = 4 * 1024 * 1024
    
    def __init__(self, total_size: Optional[int] = None, alignment: int = 8, name: str = "WorkloadAwarePool"):
        """
        Initialize workload-aware memory pool.
        
        Args:
            total_size: Total memory pool size (defaults to 4 MiB if None or <= 0)
            alignment: Memory alignment requirement
            name: Pool name for identification
        """
        # Use default size if total_size is None or invalid
        if total_size is None or total_size <= 0:
            self.total_size = self.DEFAULT_TOTAL_SIZE
        else:
            self.total_size = total_size
            
        self.alignment = alignment
        self.name = name
        
        # Validate that total_size is sufficient for all workload types - warn but don't fail for small test sizes
        min_required_size = len(WorkloadType) * 1024  # Minimum 1KB per workload type
        if self.total_size < min_required_size:
            import logging
            logging.getLogger(__name__).debug(
                "Pool created with only %d bytes (recommended ≥ %d for %d "
                "workload types). Falling back to minimal chunk sizes.",
                self.total_size,
                min_required_size,
                len(WorkloadType)
            )
        
        # Workload detection
        self.detector = WorkloadDetector()
        self.current_workload = WorkloadType.UNKNOWN
        self.last_adaptation_time = 0.0
        self.adaptation_interval = 30.0  # Adapt every 30 seconds
        
        # Pool implementations
        self.pools: Dict[WorkloadType, MemoryPoolType] = {}
        self.current_pool: Optional[MemoryPoolType] = None
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize pools
        self._initialize_pools()
        
        # Start with mixed workload pool
        self.current_pool = self.pools[WorkloadType.MIXED]
        
        logger.info(f"Initialized workload-aware memory pool '{name}' with {total_size} bytes")
    
    def _initialize_pools(self) -> None:
        """Initialize all pool implementations for different workload types."""
        # Use robust division that ensures no pool gets zero size
        num_workload_types = len(WorkloadType)
        base_pool_size = self.total_size // num_workload_types
        remainder = self.total_size % num_workload_types
        
        # Ensure minimum pool size
        min_pool_size = max(base_pool_size, 1024)  # At least 1KB per pool
        
        def get_pool_size(index: int) -> int:
            """Get pool size for workload type at given index, distributing remainder."""
            size = min_pool_size
            if index < remainder:
                size += 1  # Distribute remainder among first few pools
            return size
        
        # Initialize pools for each workload type with proper size distribution
        list(WorkloadType)
        
        try:
            # NumPy-heavy: Fast pool with large buckets
            numpy_size = get_pool_size(0)
            self.pools[WorkloadType.NUMPY_HEAVY] = FastMemoryPool(
                total_size=numpy_size,
                alignment=self.alignment,
                name=f"{self.name}_numpy",
                bucket_size_step=64,  # Larger steps for large allocations
                small_block_max=1024,
                medium_block_max=64 * 1024
            )
        except Exception:
            self.pools[WorkloadType.NUMPY_HEAVY] = MemoryPool(
                total_size=get_pool_size(0),
                alignment=self.alignment,
                name=f"{self.name}_numpy"
            )
        
        # Pure Python loops: Standard pool with fine-grained buckets
        self.pools[WorkloadType.PURE_PYTHON_LOOPS] = MemoryPool(
            total_size=get_pool_size(1),
            alignment=self.alignment,
            name=f"{self.name}_python"
        )
        
        # I/O bound: Simple pool with minimal overhead
        self.pools[WorkloadType.IO_BOUND] = MemoryPool(
            total_size=get_pool_size(2),
            alignment=self.alignment,
            name=f"{self.name}_io"
        )
        
        # Memory intensive: Larger pool for big allocations
        memory_size = max(get_pool_size(3), min_pool_size * 2)  # At least 2x minimum
        self.pools[WorkloadType.MEMORY_INTENSIVE] = MemoryPool(
            total_size=memory_size,
            alignment=self.alignment,
            name=f"{self.name}_memory"
        )
        
        try:
            # CPU bound: Lock-free pool for high concurrency
            self.pools[WorkloadType.CPU_BOUND] = LockFreeMemoryPool(
                total_size=get_pool_size(4),
                alignment=self.alignment,
                name=f"{self.name}_cpu"
            )
        except Exception:
            self.pools[WorkloadType.CPU_BOUND] = MemoryPool(
                total_size=get_pool_size(4),
                alignment=self.alignment,
                name=f"{self.name}_cpu"
            )
        
        try:
            # Mixed: Sharded pool for balanced performance
            self.pools[WorkloadType.MIXED] = ShardedMemoryPool(
                total_size=get_pool_size(5),
                alignment=self.alignment,
                name=f"{self.name}_mixed"
            )
        except Exception:
            self.pools[WorkloadType.MIXED] = MemoryPool(
                total_size=get_pool_size(5),
                alignment=self.alignment,
                name=f"{self.name}_mixed"
            )
        
        # Unknown: Default to standard pool
        self.pools[WorkloadType.UNKNOWN] = self.pools[WorkloadType.MIXED]
    
    def allocate(self, size: int, alignment: Optional[int] = None) -> Optional[MemoryBlock]:
        """
        Allocate memory with workload-aware pool selection.
        
        Args:
            size: Size to allocate
            alignment: Optional alignment override
            
        Returns:
            MemoryBlock object if successful, None if allocation failed
        """
        thread_id = threading.get_ident()
        
        # Record allocation for workload detection
        self.detector.record_allocation(size, thread_id)
        
        # Check if we should adapt the pool
        self._maybe_adapt_pool()
        
        # Allocate from current pool
        with self._lock:
            if self.current_pool is None:
                raise AllocationError("No pool available")
            
            # Use default alignment if none provided
            actual_alignment = alignment if alignment is not None else self.alignment
            result = self.current_pool.allocate(size, actual_alignment)
            
            # Handle mixed return types during transition period
            if isinstance(result, MemoryBlock):
                return result
            elif isinstance(result, int):
                # Legacy pool returning offset - convert to MemoryBlock
                return MemoryBlock(offset=result, size=size)
            else:
                # None or allocation failure
                return None
    
    def deallocate(self, offset: int) -> None:
        """
        Deallocate memory.
        
        Args:
            offset: Offset to deallocate
        """
        thread_id = threading.get_ident()
        
        with self._lock:
            if self.current_pool is None:
                raise ValueError("No pool available")
            
            # Get size for tracking (if available)
            size = 0
            try:
                if hasattr(self.current_pool, '_allocations') and hasattr(self.current_pool, '_allocations'):
                    allocations = getattr(self.current_pool, '_allocations', {})
                    if offset in allocations:
                        size = allocations[offset]
            except (AttributeError, KeyError):
                # Fallback if allocation tracking is not available
                size = 0
            
            self.current_pool.deallocate(offset)
            
            # Record deallocation for workload detection
            self.detector.record_deallocation(size, thread_id)
    
    def free(self, block: MemoryBlock) -> bool:
        """
        Free a memory block using the unified interface.
        
        Args:
            block: MemoryBlock to free
            
        Returns:
            True if successfully freed, False otherwise
        """
        if block is None or block.invalid:
            return False
        
        thread_id = threading.get_ident()
        
        with self._lock:
            if self.current_pool is None:
                return False
            
            try:
                # Check if current pool supports the new free() method
                if hasattr(self.current_pool, 'free') and callable(getattr(self.current_pool, 'free')):
                    # Use type: ignore to handle transition period where not all pools have free() method
                    result = getattr(self.current_pool, 'free')(block)  # type: ignore
                else:
                    # Fallback to legacy deallocate method
                    self.current_pool.deallocate(block.offset)
                    result = True
                
                if result:
                    # Record deallocation for workload detection
                    self.detector.record_deallocation(block.size, thread_id)
                
                return result
            except Exception:
                return False
    
    def _maybe_adapt_pool(self) -> None:
        """Check if pool adaptation is needed and perform it."""
        current_time = time.perf_counter()
        
        if current_time - self.last_adaptation_time < self.adaptation_interval:
            return
        
        # Detect current workload
        detected_workload = self.detector.detect_workload_type()
        
        if detected_workload != self.current_workload:
            with self._lock:
                logger.info(f"Adapting pool from {self.current_workload} to {detected_workload}")
                self.current_workload = detected_workload
                self.current_pool = self.pools[detected_workload]
                self.last_adaptation_time = current_time
    
    def select_pool(self, workload_type: WorkloadType) -> MemoryPoolType:
        """
        Manually select pool for specific workload type.
        
        Args:
            workload_type: Type of workload
            
        Returns:
            Memory pool optimized for the workload
        """
        return self.pools.get(workload_type, self.pools[WorkloadType.MIXED])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all pools."""
        stats = {
            'workload_aware_pool': {
                'current_workload': self.current_workload.value,
                'detector_stats': self.detector.stats.get_snapshot(),
                'workload_characteristics': self.detector.analyze_workload().__dict__
            }
        }
        
        # Add statistics from all pools
        for workload_type, pool in self.pools.items():
            try:
                pool_stats = pool.get_statistics()
                stats[f'pool_{workload_type.value}'] = pool_stats
            except Exception as e:
                stats[f'pool_{workload_type.value}'] = {'error': str(e)}
        
        return stats
    
    def memory_view(self, offset: int, size: int) -> memoryview:
        """Get memory view from current pool."""
        with self._lock:
            if self.current_pool is None:
                raise ValueError("No pool available")
            
            # Check if the current pool supports memory_view
            if hasattr(self.current_pool, 'memory_view') and callable(getattr(self.current_pool, 'memory_view')):
                # Type narrowing: we know it has memory_view method
                return getattr(self.current_pool, 'memory_view')(offset, size)
            else:
                # Fallback for pools that don't support memory_view
                raise NotImplementedError(f"Pool {type(self.current_pool).__name__} does not support memory_view")
    
    def get_current_pool_type(self) -> WorkloadType:
        """Get the currently active pool type."""
        return self.current_workload
    
    def force_pool_selection(self, workload_type: WorkloadType) -> None:
        """Force selection of specific pool type."""
        with self._lock:
            if workload_type in self.pools:
                self.current_workload = workload_type
                self.current_pool = self.pools[workload_type]
                logger.info(f"Forced pool selection to {workload_type.value}")