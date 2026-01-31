"""
Epochly Memory System - Workload-Aware Memory Pool Implementation

This module provides a lightweight workload-aware memory pool that uses the
ThreadSafeRedBlackTree for efficient memory block management. The implementation
is designed to be minimal but functional, providing the necessary interface
for integration with the existing memory pool architecture.

Author: Epochly Memory Foundation Team
"""

import threading
import time
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from .memory_block import MemoryBlock

# Phase 3.3: Use native FastRedBlackTree (3× faster) with fallback to Python version
try:
    from .fast_rb_tree import FastRedBlackTree as RedBlackTree
    RB_TREE_NATIVE = True
except ImportError:
    from .thread_safe_rb_tree import ThreadSafeRedBlackTree as RedBlackTree
    RB_TREE_NATIVE = False
from .block_coalescer import (
    BlockCoalescer, CoalescingPolicy, ImmediateCoalescingPolicy,
    DeferredCoalescingPolicy, ThresholdCoalescingPolicy, AdaptiveCoalescingPolicy,
    CoalescingEvent
)

__all__ = ['WorkloadAwareMemoryPool', 'PoolType']


class PoolType(Enum):
    """Types of memory pools."""
    GENERAL_PURPOSE = "general_purpose"
    HIGH_FREQUENCY = "high_frequency"
    LARGE_OBJECT = "large_object"


class WorkloadAwareMemoryPool:
    """
    Lightweight workload-aware memory pool implementation.
    
    This pool uses a ThreadSafeRedBlackTree to manage free blocks and provides
    basic allocation and deallocation functionality. It's designed to be a
    minimal but functional implementation that satisfies the interface
    requirements of the existing memory pool architecture.
    
    Features:
    - Thread-safe operations using the underlying ThreadSafeRedBlackTree
    - Basic allocation and deallocation with best-fit strategy
    - Statistics tracking for monitoring and debugging
    - Graceful degradation for unsupported operations
    """
    
    def __init__(self, pool_size: int = 1024 * 1024, alignment: int = 8,
                 total_size: Optional[int] = None,
                 initial_pool_type: PoolType = PoolType.GENERAL_PURPOSE,
                 coalescing_policy: str = 'immediate',
                 fragmentation_threshold: float = 0.3,
                 track_coalescing_stats: bool = False,
                 coalescing_event_handler: Optional[Callable[[CoalescingEvent], None]] = None):
        """
        Initialize the workload-aware memory pool.
        
        Args:
            pool_size: Total size of the memory pool in bytes (deprecated, use total_size)
            alignment: Memory alignment requirement in bytes
            total_size: Total size of the memory pool in bytes
            initial_pool_type: Initial pool type
            coalescing_policy: Coalescing policy ('immediate', 'deferred', 'threshold', 'adaptive')
            fragmentation_threshold: Threshold for threshold-based coalescing
            track_coalescing_stats: Whether to track detailed coalescing statistics
            coalescing_event_handler: Optional handler for coalescing events
        """
        # Handle both pool_size and total_size for compatibility
        self.total_size = total_size or pool_size
        self.pool_size = self.total_size  # Keep for backward compatibility
        self.alignment = alignment
        self.pool_type = initial_pool_type
        self._lock = threading.RLock()
        
        # Phase 3.3: Use native RB tree (3× faster searches) with fallback
        self._free_blocks = RedBlackTree()
        
        # Track allocated blocks for deallocation
        self._allocated_blocks: Dict[int, MemoryBlock] = {}
        
        # Initialize coalescing
        self._coalescer = BlockCoalescer()
        self._setup_coalescing_policy(coalescing_policy, fragmentation_threshold)
        self._coalescing_event_handler = coalescing_event_handler
        self._track_coalescing_stats = track_coalescing_stats
        
        # Statistics
        self._stats = {
            'total_allocations': 0,
            'total_deallocations': 0,
            'bytes_allocated': 0,
            'bytes_deallocated': 0,
            'peak_usage': 0,
            'current_usage': 0,
            'allocation_failures': 0,
            'free_blocks_count': 1,
            # Coalescing statistics
            'coalescing_operations': 0,
            'blocks_coalesced': 0,
            'coalescing_time_ms': 0,
            'fragmentation_reduction': 0
        }
        
        # Tracking for adaptive policies
        self._last_stats_time = time.time()
        self._recent_allocations = 0
        self._recent_deallocations = 0
        
        # Initialize with one large free block starting at aligned offset
        # Reserve first 8 bytes to ensure all allocations are 8-byte aligned
        aligned_start = 8  # Minimum alignment for all allocations
        usable_size = self.total_size - aligned_start if self.total_size > aligned_start else 0
        if usable_size > 0:
            initial_block = MemoryBlock(offset=aligned_start, size=usable_size, free=True)
            self._free_blocks.insert(usable_size, initial_block)
        
        # Next allocation ID for tracking
        self._next_alloc_id = 1
    
    def _setup_coalescing_policy(self, policy_name: str, fragmentation_threshold: float):
        """Set up the coalescing policy."""
        if policy_name == 'immediate':
            self._coalescing_policy = ImmediateCoalescingPolicy()
        elif policy_name == 'deferred':
            self._coalescing_policy = DeferredCoalescingPolicy()
        elif policy_name == 'threshold':
            self._coalescing_policy = ThresholdCoalescingPolicy(
                fragmentation_threshold=fragmentation_threshold
            )
        elif policy_name == 'adaptive':
            self._coalescing_policy = AdaptiveCoalescingPolicy()
        else:
            # Default to immediate
            self._coalescing_policy = ImmediateCoalescingPolicy()
    
    def allocate(self, size: int) -> Optional[MemoryBlock]:
        """
        Allocate a memory block of the specified size.
        
        Args:
            size: Size of the memory block to allocate
            
        Returns:
            MemoryBlock if allocation successful, None otherwise
        """
        if size <= 0:
            return None
        
        # Align size to alignment boundary
        aligned_size = ((size + self.alignment - 1) // self.alignment) * self.alignment
        
        with self._lock:
            # Find best-fit block
            best_fit = self._free_blocks.find_best_fit(aligned_size)
            if not best_fit:
                self._stats['allocation_failures'] += 1
                return None
            
            # Remove the block from free list
            self._free_blocks.delete(best_fit.size, best_fit)
            
            # Create allocated block
            allocated_block = MemoryBlock(
                offset=best_fit.offset,
                size=aligned_size,
                free=False
            )
            
            # If there's remaining space, add it back to free list
            remaining_size = best_fit.size - aligned_size
            if remaining_size > 0:
                remaining_block = MemoryBlock(
                    offset=best_fit.offset + aligned_size,
                    size=remaining_size,
                    free=True
                )
                self._free_blocks.insert(remaining_size, remaining_block)
            
            # Track the allocation
            alloc_id = self._next_alloc_id
            self._next_alloc_id += 1
            self._allocated_blocks[alloc_id] = allocated_block
            
            # Update statistics
            self._stats['total_allocations'] += 1
            self._stats['bytes_allocated'] += aligned_size
            self._stats['current_usage'] += aligned_size
            self._stats['peak_usage'] = max(
                self._stats['peak_usage'],
                self._stats['current_usage']
            )
            self._recent_allocations += 1
            
            # Store allocation ID in the block for tracking (using setattr for dynamic attribute)
            setattr(allocated_block, '_alloc_id', alloc_id)
            
            return allocated_block
    
    def deallocate(self, block: MemoryBlock) -> bool:
        """
        Free a previously allocated memory block.
        
        Args:
            block: MemoryBlock to free
            
        Returns:
            True if deallocation successful, False otherwise
        """
        if not block or block.free:
            return False
        
        with self._lock:
            # Find the allocation ID
            alloc_id = getattr(block, '_alloc_id', None)
            if alloc_id is None or alloc_id not in self._allocated_blocks:
                return False
            
            # Remove from allocated blocks
            del self._allocated_blocks[alloc_id]
            
            # Mark as free
            block.free = True
            
            # Add back to free list
            self._free_blocks.insert(block.size, block)
            
            # Update statistics
            self._stats['total_deallocations'] += 1
            self._stats['bytes_deallocated'] += block.size
            self._stats['current_usage'] -= block.size
            self._recent_deallocations += 1
            
            # Check if coalescing should occur
            if self._should_coalesce():
                self._perform_coalescing()
            
            return True
    
    def free(self, block: MemoryBlock) -> bool:
        """Alias for deallocate for backward compatibility."""
        return self.deallocate(block)
    
    def _should_coalesce(self) -> bool:
        """Determine if coalescing should occur based on policy."""
        current_time = time.time()
        elapsed = current_time - self._last_stats_time
        
        # Calculate rates
        allocation_rate = self._recent_allocations / max(0.01, elapsed)
        deallocation_rate = self._recent_deallocations / max(0.01, elapsed)
        
        # Get current fragmentation
        fragmentation = self._calculate_fragmentation_ratio()
        free_blocks_count = self._free_blocks.size()
        
        # Check policy
        should_coalesce = self._coalescing_policy.should_coalesce(
            fragmentation_ratio=fragmentation,
            free_blocks_count=free_blocks_count,
            allocation_rate=allocation_rate,
            deallocation_rate=deallocation_rate
        )
        
        # Reset counters if enough time has passed
        if elapsed > 1.0:
            self._recent_allocations = 0
            self._recent_deallocations = 0
            self._last_stats_time = current_time
        
        return should_coalesce
    
    def _perform_coalescing(self):
        """Perform the actual coalescing operation."""
        start_time = time.time()
        initial_fragmentation = self._calculate_fragmentation_ratio()
        initial_blocks = self._free_blocks.size()
        
        # Get all free blocks
        free_blocks = self.get_free_blocks()
        
        # Perform coalescing
        coalesced_blocks = self._coalescer.coalesce(free_blocks)
        
        # Clear and rebuild free blocks tree
        self._free_blocks.clear()
        for block in coalesced_blocks:
            self._free_blocks.insert(block.size, block)
        
        # Calculate metrics
        final_fragmentation = self._calculate_fragmentation_ratio()
        blocks_merged = initial_blocks - len(coalesced_blocks)
        coalescing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Update statistics if tracking
        if self._track_coalescing_stats:
            self._stats['coalescing_operations'] += 1
            self._stats['blocks_coalesced'] += blocks_merged
            self._stats['coalescing_time_ms'] += coalescing_time
            self._stats['fragmentation_reduction'] += (initial_fragmentation - final_fragmentation)
        
        # Update free blocks count
        self._stats['free_blocks_count'] = len(coalesced_blocks)
        
        # Send event if handler is registered
        if self._coalescing_event_handler and blocks_merged > 0:
            event = CoalescingEvent(
                timestamp=time.time(),
                blocks_merged=blocks_merged,
                size_recovered=0  # Could calculate actual size recovered
            )
            self._coalescing_event_handler(event)
        
        # Update adaptive policy if applicable
        if isinstance(self._coalescing_policy, AdaptiveCoalescingPolicy):
            benefit = (initial_fragmentation - final_fragmentation) / max(0.01, initial_fragmentation)
            cost = min(1.0, coalescing_time / 100.0)  # Normalize cost
            self._coalescing_policy.update_feedback(benefit, cost)
        
        # Reset deferred policy timer if applicable
        self._coalescing_policy.reset()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the memory pool.
        
        Returns:
            Dictionary containing various statistics
        """
        with self._lock:
            stats: Dict[str, Any] = self._stats.copy()
            
            # Add tree statistics
            tree_stats = self._free_blocks.get_stats()
            stats['free_blocks_count'] = tree_stats.get('total_blocks', self._free_blocks.size())
            stats['free_block_sizes'] = tree_stats.get('unique_sizes', 0)
            stats['fragmentation_ratio'] = self._calculate_fragmentation_ratio()
            stats['utilization_ratio'] = (
                self._stats['current_usage'] / max(1, self.total_size)
            )
            stats['pool_size'] = self.total_size
            stats['alignment'] = self.alignment
            
            return stats
    
    def _calculate_fragmentation_ratio(self) -> float:
        """
        Calculate the fragmentation ratio of the memory pool.
        
        Returns:
            Fragmentation ratio between 0.0 and 1.0
        """
        if self._free_blocks.size() <= 1:
            return 0.0
        
        # Simple fragmentation metric: number of free blocks / total free space
        total_free_space = self.pool_size - self._stats['current_usage']
        if total_free_space <= 0:
            return 0.0
        
        free_block_count = self._free_blocks.size()
        return min(1.0, free_block_count / max(1, total_free_space / 1024))
    
    def reset(self) -> None:
        """Reset the memory pool to initial state."""
        with self._lock:
            self._free_blocks.clear()
            self._allocated_blocks.clear()
            
            # Reset statistics
            self._stats = {
                'total_allocations': 0,
                'total_deallocations': 0,
                'bytes_allocated': 0,
                'bytes_deallocated': 0,
                'peak_usage': 0,
                'current_usage': 0,
                'allocation_failures': 0,
                'free_blocks_count': 1,
                'coalescing_operations': 0,
                'blocks_coalesced': 0,
                'coalescing_time_ms': 0,
                'fragmentation_reduction': 0
            }
            
            # Reset tracking
            self._recent_allocations = 0
            self._recent_deallocations = 0
            self._last_stats_time = time.time()
            
            # Reinitialize with one large free block starting at offset 1 (reserve 0)
            initial_block = MemoryBlock(offset=1, size=self.total_size-1, free=True)
            self._free_blocks.insert(self.total_size-1, initial_block)
            self._next_alloc_id = 1
    
    def get_free_blocks(self) -> List[MemoryBlock]:
        """
        Get a list of all free blocks.
        
        Returns:
            List of free MemoryBlock instances
        """
        with self._lock:
            free_blocks = []
            size_distribution = self._free_blocks.get_size_distribution()
            
            for size, count in size_distribution.items():
                blocks = self._free_blocks.find_all_exact(size)
                free_blocks.extend(blocks[:count])  # Limit to actual count
            
            return free_blocks
    
    def get_allocated_blocks(self) -> List[MemoryBlock]:
        """
        Get a list of all allocated blocks.
        
        Returns:
            List of allocated MemoryBlock instances
        """
        with self._lock:
            return list(self._allocated_blocks.values())
    
    def supports_aligned_allocation(self) -> bool:
        """Check if the pool supports aligned allocation."""
        return True
    
    def supports_async_operations(self) -> bool:
        """Check if the pool supports async operations."""
        return False  # This is a synchronous implementation
    
    def __len__(self) -> int:
        """Return the number of allocated blocks."""
        with self._lock:
            return len(self._allocated_blocks)
    
    def __bool__(self) -> bool:
        """Return True if there are any allocated blocks."""
        return len(self) > 0
    
    def __repr__(self) -> str:
        """String representation of the memory pool."""
        with self._lock:
            return (
                f"WorkloadAwareMemoryPool("
                f"size={self.total_size}, "
                f"allocated={len(self._allocated_blocks)}, "
                f"free_blocks={self._free_blocks.size()}, "
                f"usage={self._stats['current_usage']}/{self.total_size})"
            )