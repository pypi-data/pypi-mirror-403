"""
Epochly Memory Foundation - Fine-Grained Bucket Locking Memory Pool (Phase 3)

This module implements Phase 3 of the lock-free memory pool evolution:
- Per-bucket atomic operations instead of global locking
- Fine-grained locking for improved concurrency
- Maintains compatibility with existing MemoryPool interface

Author: Epochly Memory Foundation Team
Created: 2025-06-07
Phase: 3 - Fine-Grained Bucket Locking
"""

import logging
import threading
import contextlib
import time
from typing import Dict, List, Optional, Any
from sortedcontainers import SortedSet

from .exceptions import AllocationError
from .atomic_primitives import (
    AtomicCounter,
    LockFreeStack,
    LockFreeStatistics,
    PerformanceTimer
)
from .lock_manager import (
    register_bucket_lock
)
from .memory_block import MemoryBlock
from .mmap_memory_pool import MmapMemoryPool, DecayingMemoryPool, DecayConfig

logger = logging.getLogger(__name__)


class MemoryBlockPool:
    """
    Thread-local object pool for MemoryBlock instances to prevent memory leaks.
    
    This pool reuses MemoryBlock objects instead of creating new ones for every
    allocation, significantly reducing memory pressure and GC overhead.
    """
    
    def __init__(self, initial_capacity: int = 100):
        """Initialize the memory block pool."""
        self._pool: List[MemoryBlock] = []
        self._capacity = initial_capacity
        self._high_water_mark = 0
        
        # Pre-allocate some blocks
        for _ in range(min(initial_capacity // 4, 25)):
            self._pool.append(MemoryBlock(offset=0, size=0, free=True))
    
    def acquire(self, offset: int, size: int, free: bool = False) -> MemoryBlock:
        """
        Acquire a MemoryBlock from the pool or create a new one.
        
        Args:
            offset: Block offset
            size: Block size
            free: Whether block is free
            
        Returns:
            MemoryBlock instance
        """
        if self._pool:
            block = self._pool.pop()
            # Reinitialize the block with new values
            block.offset = offset
            block.size = size
            block.free = free
            block.invalid = False
            block._is_sentinel = (size == 0)
            return block
        else:
            # Pool is empty, create a new block
            self._high_water_mark += 1
            return MemoryBlock(offset=offset, size=size, free=free)
    
    def release(self, block: MemoryBlock) -> None:
        """
        Release a MemoryBlock back to the pool for reuse.
        
        Args:
            block: MemoryBlock to release
        """
        if len(self._pool) < self._capacity:
            # Reset block state before returning to pool
            block.invalid = True  # Mark as invalid to catch misuse
            self._pool.append(block)
    
    def clear(self) -> None:
        """Clear the pool, releasing all cached blocks."""
        self._pool.clear()
        self._high_water_mark = 0


# Thread-local storage for block pools
_thread_local = threading.local()


def _get_block_pool() -> MemoryBlockPool:
    """Get or create thread-local MemoryBlock pool."""
    if not hasattr(_thread_local, 'block_pool'):
        _thread_local.block_pool = MemoryBlockPool()
    return _thread_local.block_pool


class AtomicBucket:
    """
    Atomic bucket for fine-grained lock-free allocation.
    
    Each bucket manages a specific size class with its own atomic operations,
    eliminating contention between different size allocations.
    """
    
    def __init__(self, bucket_size: int, bucket_id: str):
        """
        Initialize atomic bucket.
        
        Args:
            bucket_size: Size class this bucket manages
            bucket_id: Unique identifier for this bucket
        """
        self.bucket_size = bucket_size
        self.bucket_id = bucket_id
        
        # Lock-free stack for available blocks
        # Note: Cython types don't support generic subscripting, use unparameterized type
        self.free_blocks = LockFreeStack()
        
        # Atomic counters for bucket statistics
        self.total_blocks = AtomicCounter()
        self.allocated_blocks = AtomicCounter()
        self.allocation_count = AtomicCounter()
        self.deallocation_count = AtomicCounter()
        
        # Per-bucket lock for complex operations (minimal usage)
        self.bucket_lock = register_bucket_lock(bucket_id)
        
        # Performance tracking
        self.allocation_time_ns = AtomicCounter()
        self.contention_count = AtomicCounter()
        
        logger.debug(f"Initialized atomic bucket {bucket_id} for size {bucket_size}")
    
    def add_block(self, offset: int) -> None:
        """
        Add a free block to this bucket atomically.
        
        Args:
            offset: Offset of the free block
        """
        self.free_blocks.push(offset)
        self.total_blocks.increment()
    
    def allocate_block(self) -> Optional[int]:
        """
        Atomically allocate a block from this bucket.
        
        Returns:
            Block offset or None if bucket is empty
        """
        start_time = time.perf_counter_ns()
        
        # Try lock-free allocation first
        offset = self.free_blocks.pop()
        
        if offset is not None:
            self.allocated_blocks.increment()
            self.allocation_count.increment()
            
            # Record timing
            elapsed = time.perf_counter_ns() - start_time
            self.allocation_time_ns.increment(elapsed)
            
            return offset
        
        return None
    
    def deallocate_block(self, offset: int) -> None:
        """
        Atomically deallocate a block back to this bucket.
        
        Args:
            offset: Offset of the block to deallocate
        """
        self.free_blocks.push(offset)
        self.allocated_blocks.decrement()
        self.deallocation_count.increment()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get atomic statistics for this bucket."""
        total_allocs = self.allocation_count.load()
        avg_time = (self.allocation_time_ns.load() / total_allocs) if total_allocs > 0 else 0.0
        
        return {
            'bucket_id': self.bucket_id,
            'bucket_size': self.bucket_size,
            'total_blocks': self.total_blocks.load(),
            'allocated_blocks': self.allocated_blocks.load(),
            'available_blocks': self.total_blocks.load() - self.allocated_blocks.load(),
            'allocation_count': total_allocs,
            'deallocation_count': self.deallocation_count.load(),
            'average_allocation_time_ns': avg_time,
            'contention_count': self.contention_count.load(),
            'utilization_ratio': (self.allocated_blocks.load() / self.total_blocks.load()) 
                               if self.total_blocks.load() > 0 else 0.0
        }
    
    def is_empty(self) -> bool:
        """Check if bucket has no available blocks."""
        return self.free_blocks.is_empty()
    
    def size(self) -> int:
        """Get approximate number of available blocks."""
        return self.free_blocks.size()


class FineGrainedMemoryPool:
    """
    Fine-grained bucket locking memory pool (Phase 3).
    
    Implements per-bucket atomic operations to reduce lock contention
    while maintaining thread safety. Each size class has its own atomic
    bucket with independent locking.
    
    Features:
    - Per-bucket atomic operations
    - Fine-grained locking hierarchy
    - Lock-free statistics collection
    - Backward compatibility with MemoryPool interface
    """
    
    # Size class boundaries for fine-grained buckets
    SMALL_BLOCK_MAX = 256      # 8B to 256B
    MEDIUM_BLOCK_MAX = 4096    # 256B to 4KB
    BUCKET_SIZE_STEP = 8       # 8-byte alignment buckets
    RESERVED_OFFSET = -1       # Reserved offset, never allocated (changed from 0 to avoid collision with valid offsets)
    
    def __init__(self, total_size: int, alignment: int = 8, name: str = "FineGrainedMemoryPool",
                 use_mmap: bool = True, enable_decay: bool = True):
        """
        Initialize fine-grained memory pool.
        
        Args:
            total_size: Total size of memory pool in bytes
            alignment: Default alignment for allocations (default: 8)
            name: Name for logging and identification
            use_mmap: Use mmap-based backing pool for deterministic memory management
            enable_decay: Enable automatic decay of free pages (requires use_mmap)
        """
        if total_size <= 0:
            raise ValueError("Total size must be positive")
        if alignment <= 0 or (alignment & (alignment - 1)) != 0:
            raise ValueError("Alignment must be a positive power of 2")
            
        self._total_size = total_size
        self._default_alignment = alignment
        self._name = name
        self._use_mmap = use_mmap
        
        # Create backing storage
        if use_mmap:
            # Use mmap-based pool for deterministic memory management
            if enable_decay:
                decay_config = DecayConfig(
                    decay_time_ms=10000,  # 10 seconds
                    decay_interval_ms=1000,  # Check every second
                    min_free_size=65536  # Only decay blocks >= 64KB
                )
                self._backing_pool = DecayingMemoryPool(
                    total_size, 
                    f"{name}_mmap",
                    decay_config
                )
            else:
                self._backing_pool = MmapMemoryPool(total_size, f"{name}_mmap")
            logger.info(f"Using mmap backing pool with decay={'enabled' if enable_decay else 'disabled'}")
        else:
            # Fallback to bytearray (original implementation)
            self._buffer = bytearray(total_size)
            self._backing_pool = None
        
        # Initialize atomic buckets for each size class
        self._atomic_buckets: Dict[int, AtomicBucket] = {}
        self._init_atomic_buckets()
        
        # Fallback for large allocations (still uses minimal locking)
        self._large_allocation_lock = threading.RLock()
        # Use pool for initial free block
        initial_block = _get_block_pool().acquire(offset=1, size=total_size - 1, free=True)
        self._free_blocks = SortedSet([initial_block])
        
        # Allocation tracking with atomic operations
        self._allocations: Dict[int, int] = {}  # offset -> size
        self._allocations_lock = threading.RLock()  # Minimal lock for dict operations
        
        # Lock-free global statistics
        self._atomic_stats = LockFreeStatistics()
        
        # Performance timer
        self._timer = PerformanceTimer()
        
        logger.info(f"Initialized {name} with fine-grained bucket locking "
                   f"({len(self._atomic_buckets)} atomic buckets)")
    
    def _init_atomic_buckets(self) -> None:
        """Initialize atomic buckets for each size class."""
        bucket_count = 0
        
        # Small blocks: 8, 16, 24, ..., 256
        for size in range(self.BUCKET_SIZE_STEP, self.SMALL_BLOCK_MAX + 1, self.BUCKET_SIZE_STEP):
            bucket_id = f"small_{size}"
            self._atomic_buckets[size] = AtomicBucket(size, bucket_id)
            bucket_count += 1
        
        # Medium blocks: 264, 272, ..., 4096 (every 8 bytes)
        for size in range(self.SMALL_BLOCK_MAX + self.BUCKET_SIZE_STEP,
                         self.MEDIUM_BLOCK_MAX + 1, self.BUCKET_SIZE_STEP):
            bucket_id = f"medium_{size}"
            self._atomic_buckets[size] = AtomicBucket(size, bucket_id)
            bucket_count += 1
        
        logger.debug(f"Initialized {bucket_count} atomic buckets")
    
    def _get_size_bucket(self, size: int) -> Optional[int]:
        """Get the appropriate size bucket for a given size."""
        if size <= self.SMALL_BLOCK_MAX:
            # Round up to nearest bucket size
            return ((size + self.BUCKET_SIZE_STEP - 1) // self.BUCKET_SIZE_STEP) * self.BUCKET_SIZE_STEP
        elif size <= self.MEDIUM_BLOCK_MAX:
            # Round up to nearest bucket size
            return ((size + self.BUCKET_SIZE_STEP - 1) // self.BUCKET_SIZE_STEP) * self.BUCKET_SIZE_STEP
        else:
            # Large blocks use fallback allocation
            return None
    
    def _populate_bucket_from_large_blocks(self, bucket_size: int) -> bool:
        """
        Populate a bucket by splitting large blocks when bucket is empty.
        
        Args:
            bucket_size: Size of bucket to populate
            
        Returns:
            True if bucket was populated successfully
        """
        with self._large_allocation_lock:
            # Find a suitable large block to split
            for block in self._free_blocks:
                if block.size >= bucket_size * 4:  # Only split if we get at least 4 blocks
                    # Remove the large block
                    self._free_blocks.remove(block)
                    _get_block_pool().release(block)  # Release back to pool
                    
                    # Calculate how many bucket-sized blocks we can create
                    num_blocks = min(block.size // bucket_size, 16)  # Limit to 16 blocks per split
                    
                    # Add blocks to the bucket
                    bucket = self._atomic_buckets[bucket_size]
                    for i in range(num_blocks):
                        offset = block.offset + (i * bucket_size)
                        bucket.add_block(offset)
                    
                    # Add remainder back to large blocks if significant
                    remainder_size = block.size - (num_blocks * bucket_size)
                    if remainder_size >= bucket_size:
                        remainder_offset = block.offset + (num_blocks * bucket_size)
                        remainder_block = _get_block_pool().acquire(offset=remainder_offset, size=remainder_size, free=True)
                        self._free_blocks.add(remainder_block)
                    
                    logger.debug(f"Populated bucket {bucket_size} with {num_blocks} blocks")
                    return True
            
            return False
    
    def allocate(self, size: int, alignment: Optional[int] = None) -> Optional[MemoryBlock]:
        """
        Allocate memory using fine-grained bucket locking.
        
        Args:
            size: Size in bytes to allocate
            alignment: Alignment requirement (default: pool default)
            
        Returns:
            MemoryBlock object if successful, None if allocation failed
            
        Raises:
            AllocationError: If allocation fails due to invalid parameters
        """
        if size <= 0:
            raise AllocationError("Size must be positive")
        
        if alignment is None:
            alignment = self._default_alignment
        
        if alignment <= 0 or (alignment & (alignment - 1)) != 0:
            raise AllocationError("Alignment must be a positive power of 2")
        
        # Start timing
        self._timer.start()
        
        # Try atomic bucket allocation first
        bucket_size = self._get_size_bucket(size)
        if bucket_size is not None and bucket_size in self._atomic_buckets:
            bucket = self._atomic_buckets[bucket_size]
            
            # Try to allocate from bucket
            offset = bucket.allocate_block()
            
            # If bucket is empty, try to populate it
            if offset is None:
                if self._populate_bucket_from_large_blocks(bucket_size):
                    offset = bucket.allocate_block()
            
            if offset is not None:
                # Handle alignment
                aligned_offset = (offset + alignment - 1) & ~(alignment - 1)
                padding = aligned_offset - offset
                
                # For simplicity in Phase 3, we'll use the bucket size allocation
                # even if there's padding (Phase 4 will optimize this)
                
                # Record allocation
                with self._allocations_lock:
                    self._allocations[aligned_offset] = size
                
                # Record statistics
                allocation_time = self._timer.elapsed_ns()
                self._atomic_stats.record_allocation(
                    size=size,
                    is_bucketed=True,
                    padding=padding,
                    time_ns=allocation_time
                )
                
                return _get_block_pool().acquire(offset=aligned_offset, size=size, free=False)
        
        # Fall back to large block allocation with minimal locking
        return self._allocate_large_block(size, alignment)
    
    def _allocate_large_block(self, size: int, alignment: int) -> Optional[MemoryBlock]:
        """Allocate large block using fallback mechanism."""
        with self._large_allocation_lock:
            for block in self._free_blocks:
                aligned_offset = (block.offset + alignment - 1) & ~(alignment - 1)
                padding = aligned_offset - block.offset
                
                if aligned_offset + size <= block.offset + block.size:
                    # Remove block from free list
                    self._free_blocks.remove(block)
                    _get_block_pool().release(block)  # Release back to pool
                    
                    # Add padding back to free list if any
                    if padding > 0:
                        padding_block = _get_block_pool().acquire(offset=block.offset, size=padding, free=True)
                        self._free_blocks.add(padding_block)
                    
                    # Add remainder back to free list if any
                    remainder_size = block.size - padding - size
                    if remainder_size > 0:
                        remainder_offset = aligned_offset + size
                        remainder_block = _get_block_pool().acquire(offset=remainder_offset, size=remainder_size, free=True)
                        self._free_blocks.add(remainder_block)
                    
                    # Record allocation
                    with self._allocations_lock:
                        self._allocations[aligned_offset] = size
                    
                    # Record statistics
                    allocation_time = self._timer.elapsed_ns()
                    self._atomic_stats.record_allocation(
                        size=size,
                        is_bucketed=False,
                        padding=padding,
                        time_ns=allocation_time
                    )
                    
                    return _get_block_pool().acquire(offset=aligned_offset, size=size, free=False)
            
            return None  # Allocation failed
    
    def deallocate(self, offset: int) -> None:
        """
        Deallocate memory using fine-grained bucket operations.
        
        Args:
            offset: Offset returned by allocate()
            
        Raises:
            ValueError: If offset is invalid
        """
        if offset == self.RESERVED_OFFSET:
            raise ValueError(f"Cannot deallocate reserved offset: {offset}")
        
        # Get allocation size
        with self._allocations_lock:
            if offset not in self._allocations:
                raise ValueError(f"Invalid offset: {offset}")
            size = self._allocations.pop(offset)
        
        # Start timing
        self._timer.start()
        
        # Try to return to appropriate bucket
        bucket_size = self._get_size_bucket(size)
        if bucket_size is not None and bucket_size in self._atomic_buckets:
            bucket = self._atomic_buckets[bucket_size]
            bucket.deallocate_block(offset)
        else:
            # Return large block to fallback pool
            with self._large_allocation_lock:
                new_block = _get_block_pool().acquire(offset=offset, size=size, free=True)
                self._free_blocks.add(new_block)
                self._coalesce_free_blocks(new_block)
        
        # Record statistics
        deallocation_time = self._timer.elapsed_ns()
        self._atomic_stats.record_deallocation(size=size, time_ns=deallocation_time)
    
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
        
        try:
            self.deallocate(block.offset)
            return True
        except Exception:
            return False
    
    def _coalesce_free_blocks(self, new_block: MemoryBlock) -> None:
        """Coalesce adjacent free blocks in the large block pool."""
        # Find adjacent blocks and merge them
        to_remove = []
        merged_offset = new_block.offset
        merged_size = new_block.size
        
        for block in self._free_blocks:
            if block == new_block:
                continue
                
            # Check if blocks are adjacent
            if block.offset + block.size == merged_offset:
                # Block is immediately before new block
                merged_offset = block.offset
                merged_size += block.size
                to_remove.append(block)
            elif merged_offset + merged_size == block.offset:
                # Block is immediately after new block
                merged_size += block.size
                to_remove.append(block)
        
        # Remove old blocks and add merged block
        if to_remove:
            block_pool = _get_block_pool()
            self._free_blocks.remove(new_block)
            block_pool.release(new_block)  # Release back to pool
            
            for block in to_remove:
                self._free_blocks.remove(block)
                block_pool.release(block)  # Release back to pool
            
            merged_block = block_pool.acquire(offset=merged_offset, size=merged_size, free=True)
            self._free_blocks.add(merged_block)
    
    def memory_view(self, offset: int, size: int) -> memoryview:
        """Get a memory view for the specified offset and size."""
        if offset < 0 or offset + size > self._total_size:
            raise ValueError(f"Invalid offset/size: {offset}/{size}")
        
        if self._backing_pool:
            # Use mmap backing pool
            return self._backing_pool.memory_view(offset, size)
        else:
            # Use bytearray
            return memoryview(self._buffer)[offset:offset + size]
    
    @contextlib.contextmanager
    def managed_allocate(self, size: int, alignment: Optional[int] = None):
        """Context manager for automatic memory management."""
        offset = self.allocate(size, alignment)
        view = self.memory_view(offset, size)
        try:
            yield view
        finally:
            try:
                self.deallocate(offset)
            except (ValueError, Exception):
                pass  # Already freed or other error - ignore
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory pool statistics."""
        with self._allocations_lock:
            used = sum(size for size in self._allocations.values())
        
        # Get atomic statistics
        stats = self._atomic_stats.get_snapshot()
        
        # Get bucket statistics
        bucket_stats = {}
        total_bucket_allocations = 0
        for size, bucket in self._atomic_buckets.items():
            bucket_stats[f"bucket_{size}"] = bucket.get_statistics()
            total_bucket_allocations += bucket.allocation_count.load()
        
        # Calculate ratios
        total_allocs = stats['total_allocations']
        bucketed_ratio = (stats['bucketed_allocations'] / total_allocs * 100) if total_allocs > 0 else 0
        
        return {
            "total_size": self._total_size,
            "used": used,
            "free": self._total_size - used,
            "allocations": len(self._allocations),
            "total_allocations": stats['total_allocations'],
            "total_deallocations": stats['total_deallocations'],
            "current_allocations": stats['current_allocations'],
            "bytes_allocated": stats['bytes_allocated'],
            "peak_allocations": stats['peak_allocations'],
            "peak_bytes_allocated": stats['peak_bytes_allocated'],
            "bucketed_allocations": stats['bucketed_allocations'],
            "fallback_allocations": stats['fallback_allocations'],
            "bucketed_allocation_ratio": f"{bucketed_ratio:.1f}%",
            "alignment_padding_bytes": stats['alignment_padding_bytes'],
            "free_blocks": len(self._free_blocks),
            "allocation_mode": "fine-grained bucket locking",
            "lock_free_enabled": True,
            "atomic_buckets": len(self._atomic_buckets),
            "bucket_statistics": bucket_stats,
            "average_allocation_time_ns": stats.get('average_allocation_time_ns', 0),
            "average_deallocation_time_ns": stats.get('average_deallocation_time_ns', 0)
        }
    
    def get_fragmentation_info(self) -> Dict[str, Any]:
        """Get detailed fragmentation information."""
        with self._large_allocation_lock:
            if not self._free_blocks:
                largest_free = 0
                total_free = 0
                free_block_count = 0
            else:
                free_sizes = [block.size for block in self._free_blocks]
                largest_free = max(free_sizes)
                total_free = sum(free_sizes)
                free_block_count = len(free_sizes)
        
        # Add bucket fragmentation info
        bucket_fragmentation = {}
        for size, bucket in self._atomic_buckets.items():
            bucket_stats = bucket.get_statistics()
            bucket_fragmentation[f"bucket_{size}"] = {
                "available_blocks": bucket_stats['available_blocks'],
                "utilization_ratio": bucket_stats['utilization_ratio']
            }
        
        # Calculate overall fragmentation
        fragmentation_ratio = 1.0 - (largest_free / total_free) if total_free > 0 else 0.0
        
        return {
            "largest_free_block": largest_free,
            "total_free_space": total_free,
            "free_block_count": free_block_count,
            "fragmentation_ratio": fragmentation_ratio,
            "average_free_block_size": total_free // free_block_count if free_block_count > 0 else 0,
            "bucket_fragmentation": bucket_fragmentation
        }
    
    def collect(self) -> None:
        """
        Force memory collection and return pages to OS.
        
        This implements the Perplexity recommendation to provide
        an explicit collection API similar to tcmalloc/mimalloc.
        """
        if self._backing_pool:
            # Trigger madvise on all free pages
            self._backing_pool.collect()
            logger.debug(f"Triggered memory collection for {self._name}")
    
    def cleanup(self):
        """Explicitly cleanup all resources to prevent memory leaks."""
        # Clear all atomic buckets
        # Note: LockFreeStack doesn't have clear method, but will be GC'd when buckets are cleared
        self._atomic_buckets.clear()
        
        # Release all free blocks back to the pool
        block_pool = _get_block_pool()
        for block in self._free_blocks:
            block_pool.release(block)
        self._free_blocks.clear()
        
        # Clear allocations tracking
        with self._allocations_lock:
            self._allocations.clear()
        
        # Reset statistics
        self._atomic_stats = LockFreeStatistics()
        
        # Clear the thread-local block pool
        block_pool.clear()
        
        # Clean up backing storage
        if self._backing_pool:
            # Force collection before cleanup to return pages to OS
            self._backing_pool.collect()
            self._backing_pool.cleanup()
            self._backing_pool = None
        elif hasattr(self, '_buffer'):
            self._buffer = None
        
        logger.info(f"Cleaned up {self._name}")
    
    def __del__(self):
        """Cleanup when memory pool is destroyed."""
        try:
            # Cleanup all resources
            if hasattr(self, '_atomic_buckets'):
                self.cleanup()
            
            # Force release of backing storage
            if hasattr(self, '_backing_pool') and self._backing_pool:
                try:
                    self._backing_pool.cleanup()
                    self._backing_pool = None
                except Exception:
                    pass
            elif hasattr(self, '_buffer'):
                try:
                    self._buffer = None
                except BufferError:
                    logger.info(f"BufferError during cleanup of {self._name}: "
                               f"active memory views prevent immediate cleanup")
        except Exception as e:
            logger.error(f"Error during {self._name} cleanup: {e}")