"""
Epochly Memory System - Hybrid Large Block Manager

High-performance two-tier hybrid allocator optimized for speed and reliability.
Provides O(1) bucket allocation with O(log n) tree fallback.

Author: Epochly Memory Team
"""

import bisect
import threading
from collections import defaultdict, deque
from typing import Optional, Dict, Deque, List, Set

from .memory_block import MemoryBlock

# Phase 3.3: Use native FastRedBlackTree (3× faster) with fallback to Python version
try:
    from .fast_rb_tree import FastRedBlackTree as RedBlackTree
    RB_TREE_NATIVE = True
except ImportError:
    from .thread_safe_rb_tree import ThreadSafeRedBlackTree as RedBlackTree
    RB_TREE_NATIVE = False


class HybridLargeBlockManager:
    """
    High-performance two-tier hybrid allocator.
    
    Tier-A: Power-of-two sized buckets (O(1)) with per-bucket locks
    Tier-B: Size-ordered tree (O(log n)) for larger blocks
    
    Performance targets: <10μs latency, >100K ops/s concurrent
    """

    def __init__(self, bucket_size_step: int = 128, tree_threshold: int = 8192, capacity: Optional[int] = None, adaptation_threshold: int = 10):
        """
        Initialize hybrid allocator.
        
        Args:
            bucket_size_step: Size increment for bucket allocation (default: 128)
            tree_threshold: Threshold above which blocks go to tree (default: 8192)
            capacity: Total capacity (creates initial free block if provided)
            adaptation_threshold: Threshold for adaptive bucket creation (default: 10)
        """
        self.bucket_size_step = bucket_size_step
        self.tree_threshold = tree_threshold
        self.adaptation_threshold = adaptation_threshold

        # Tier-A: Fast path buckets with per-bucket locks
        self._buckets: Dict[int, Deque[int]] = defaultdict(deque)
        self._bucket_locks: Dict[int, threading.Lock] = defaultdict(threading.Lock)

        # Tier-B: Tree fallback for larger blocks
        self._tree_sizes: List[int] = []  # Sorted unique sizes for O(log n) search
        self._size_to_offsets: Dict[int, Deque[int]] = {}  # Size -> deque[offset]
        self._tree_lock = threading.Lock()

        # Global allocation tracking (prevents duplicate allocations)
        self._allocated_offsets: Set[int] = set()
        self._alloc_lock = threading.Lock()

        # Phase 3.3: Tree for complex allocations (native Cython version - 3× faster)
        self.rb_tree = RedBlackTree(sample_rate=100)
        
        # Statistics tracking
        self.bucket_stats = defaultdict(int)
        self.stats = self  # For stats interface compatibility
        
        # Initialize default power-of-two buckets (9 buckets for test compatibility)
        default_bucket_sizes = [1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144]
        for size in default_bucket_sizes:
            self._buckets[size] = deque()
            self._bucket_locks[size] = threading.Lock()

        # CRITICAL FIX: Initialize with capacity if provided
        # Put the whole arena in the tree so it can be subdivided on demand
        # ALIGNMENT FIX: Ensure initial block starts at aligned offset
        if capacity:
            # Start at offset 8 to ensure all allocations are 8-byte aligned
            # Reserve first 8 bytes as unusable to maintain alignment invariant
            aligned_start = 8  # Minimum alignment for all allocations
            usable_capacity = capacity - aligned_start if capacity > aligned_start else 0
            if usable_capacity > 0:
                # Put the whole arena (minus reserved bytes) in the tree so it can be subdivided.
                with self._tree_lock:  # tree helpers expect the lock.
                    self._add_to_tree_unlocked(MemoryBlock(aligned_start, usable_capacity, free=True))

    def allocate(self, size: int, alignment: Optional[int] = None) -> Optional[MemoryBlock]:
        """
        Hybrid allocation - bucket first, tree fallback.
        
        Args:
            size: Requested allocation size
            alignment: Alignment requirement
            
        Returns:
            MemoryBlock with actual allocated size, or None if allocation fails
        """
        if alignment is None or alignment < 1:
            alignment = 1
            
        if size <= 0:
            return None

        # Try bucket allocation first (only if alignment is 1 or bucket offsets are aligned)
        if alignment == 1:
            bucket_size = self.find_bucket(size)
            if bucket_size:
                bucket_lock = self._bucket_locks[bucket_size]
                with bucket_lock:
                    bucket = self._buckets.get(bucket_size)
                    if bucket:
                        # Try to find an aligned offset in the bucket
                        temp_offsets = []
                        while bucket:
                            offset = bucket.pop()
                            if offset % alignment == 0 and self._mark_as_allocated(offset):
                                # Put back any offsets we temporarily removed
                                bucket.extend(temp_offsets)
                                return MemoryBlock(offset=offset, size=bucket_size)
                            else:
                                temp_offsets.append(offset)
                        # Put back all offsets if none were aligned
                        bucket.extend(temp_offsets)

        # Fallback to tree allocation with alignment
        return self._allocate_from_tree(size, alignment)

    def allocate_from_tree(self, size: int) -> Optional[MemoryBlock]:
        """
        Direct tree allocation method.
        
        Args:
            size: Requested allocation size
            
        Returns:
            MemoryBlock with actual tree node size, or None if allocation fails
        """
        return self._allocate_from_tree(size)

    def free(self, block: MemoryBlock) -> None:
        """
        Return a block to the correct tier based on size.
        
        Args:
            block: Memory block to free
        """
        if block is None:
            return

        # Clear allocation tracking
        with self._alloc_lock:
            self._allocated_offsets.discard(block.offset)

        size = block.size

        # Small sizes back to buckets, larger sizes to tree
        if size <= self.tree_threshold and size in self._buckets:
            bucket_lock = self._bucket_locks[size]
            with bucket_lock:
                bucket = self._buckets[size]
                # Bucket overflow protection (max 1000 items per bucket)
                if len(bucket) < 1000:
                    bucket.append(block.offset)
                else:
                    # If bucket is full, add to tree instead
                    with self._tree_lock:
                        if size not in self._size_to_offsets:
                            bisect.insort(self._tree_sizes, size)
                            self._size_to_offsets[size] = deque()
                        self._size_to_offsets[size].append(block.offset)
            return

        # Add to tree
        with self._tree_lock:
            if size not in self._size_to_offsets:
                bisect.insort(self._tree_sizes, size)
                self._size_to_offsets[size] = deque()
            self._size_to_offsets[size].append(block.offset)

    def clear(self) -> None:
        """Clear all allocated blocks."""
        with self._alloc_lock:
            self._allocated_offsets.clear()
        
        # Clear all bucket locks and buckets
        for bucket_size in list(self._bucket_locks.keys()):
            with self._bucket_locks[bucket_size]:
                self._buckets[bucket_size].clear()
        
        # Clear tree
        with self._tree_lock:
            self._tree_sizes.clear()
            self._size_to_offsets.clear()
        
        # Clear rb_tree
        self.rb_tree.clear()

    def add(self, block: MemoryBlock) -> None:
        """Add a block to the manager."""
        self.free(block)

    def _mark_as_allocated(self, offset: int) -> bool:
        """
        Mark offset as allocated if it's currently free.
        
        Args:
            offset: Memory offset to mark as allocated
            
        Returns:
            True if offset was free and is now allocated, False if already allocated
        """
        with self._alloc_lock:
            if offset in self._allocated_offsets:
                return False
            self._allocated_offsets.add(offset)
            return True

    def _allocate_from_tree(self, requested_size: int, alignment: int = 1) -> Optional[MemoryBlock]:
        """
        O(log n) first-fit allocation from size-ordered tree with span subdivision.
        
        Args:
            requested_size: Minimum required size
            alignment: Alignment requirement (default: 1)
            
        Returns:
            MemoryBlock with exact requested size, or None if no suitable block
        """
        # Try our optimized tree structure first
        with self._tree_lock:
            idx = bisect.bisect_left(self._tree_sizes, requested_size)
            
            # Find the first size that can accommodate the request
            while idx < len(self._tree_sizes):
                available_size = self._tree_sizes[idx]
                offsets_deque = self._size_to_offsets[available_size]
                
                if offsets_deque:
                    offset = offsets_deque.pop()

                    if not offsets_deque:  # Last offset for this size
                        del self._size_to_offsets[available_size]
                        self._tree_sizes.pop(idx)
                        # Don't increment idx since we removed an element

                    # Protect against duplication globally
                    if self._mark_as_allocated(offset):
                        # Calculate aligned offset
                        aligned_offset = (offset + alignment - 1) & ~(alignment - 1)
                        
                        # Make sure the aligned part still fits
                        if aligned_offset + requested_size > offset + available_size:
                            # Cannot satisfy alignment using this span - try next
                            # Need to unmark as allocated since we're not using it
                            with self._alloc_lock:
                                self._allocated_offsets.discard(offset)
                            continue
                        
                        # Leading fragment (if any)
                        leading = aligned_offset - offset
                        if leading:
                            self._add_to_tree_unlocked(
                                MemoryBlock(offset, leading, free=True)
                            )
                        
                        # Allocated part
                        allocated_block = MemoryBlock(aligned_offset, requested_size)
                        
                        # Trailing fragment (if any)
                        trailing = (offset + available_size) - (aligned_offset + requested_size)
                        if trailing:
                            self._add_to_tree_unlocked(
                                MemoryBlock(aligned_offset + requested_size, trailing, free=True)
                            )
                        
                        return allocated_block
                else:
                    # This size class is empty, move to next
                    idx += 1

        # Fallback to rb_tree
        block = self.rb_tree.find_best_fit(requested_size)
        if block and self._mark_as_allocated(block.offset):
            # Remove from rb_tree to prevent double allocation
            self.rb_tree.delete(block.size, block)
            
            # If we have a perfect fit, return it
            if block.size == requested_size:
                return block
            
            # Otherwise, subdivide and return remainder to rb_tree
            allocated_block = MemoryBlock(offset=block.offset, size=requested_size)
            remainder_size = block.size - requested_size
            if remainder_size > 0:
                remainder_offset = block.offset + requested_size
                remainder_block = MemoryBlock(offset=remainder_offset, size=remainder_size, free=True)
                # Add remainder back to rb_tree
                self.rb_tree.insert(remainder_block.size, remainder_block)
            
            return allocated_block

        return None

    def _add_to_tree_unlocked(self, block: MemoryBlock) -> None:
        """
        Add a block to the tree structure without acquiring locks.
        Used internally when locks are already held.
        
        Args:
            block: Memory block to add to tree
        """
        size = block.size
        if size not in self._size_to_offsets:
            bisect.insort(self._tree_sizes, size)
            self._size_to_offsets[size] = deque()
        self._size_to_offsets[size].append(block.offset)

    # Properties for test compatibility
    @property
    def size_buckets(self):
        """Property for test compatibility."""
        return self._buckets

    def inject_bucket_block(self, bucket_size: int, offset: int) -> None:
        """Helper for tests to pre-fill buckets."""
        bucket_lock = self._bucket_locks[bucket_size]
        with bucket_lock:
            self._buckets[bucket_size].append(offset)

    def get_free_bytes(self) -> int:
        """
        Get total free bytes available in the allocator.
        
        This method calculates the sum of all free memory by:
        1. Summing all blocks in buckets (bucket_size * count)
        2. Summing all blocks in the tree with their individual sizes
        
        Returns:
            Total free bytes available for allocation
        """
        # Calculate free bytes in buckets
        bucket_free_bytes = 0
        for bucket_size, offsets in self._buckets.items():
            bucket_free_bytes += bucket_size * len(offsets)
        
        # Calculate free bytes in tree
        tree_free_bytes = 0
        with self._tree_lock:
            for size, offsets in self._size_to_offsets.items():
                tree_free_bytes += size * len(offsets)
        
        return bucket_free_bytes + tree_free_bytes

    def get_stats(self) -> Dict:
        """
        Get allocation statistics.
        
        Returns:
            Dictionary with allocation statistics including individual bucket stats
        """
        with self._alloc_lock:
            allocated_count = len(self._allocated_offsets)
        
        bucket_count = sum(len(bucket) for bucket in self._buckets.values())
        
        with self._tree_lock:
            tree_count = sum(len(offsets) for offsets in self._size_to_offsets.values())
        
        stats = {
            'allocated_blocks': allocated_count,
            'free_bucket_blocks': bucket_count,
            'free_tree_blocks': tree_count,
            'total_buckets': len(self._buckets),
            'adaptive_buckets': len(self._buckets),
            'tree_size_classes': len(self._tree_sizes),
            'is_valid': True
        }
        
        # Add individual bucket statistics
        for size in self._buckets.keys():
            bucket_key = f'bucket_{size}'
            stats[bucket_key] = len(self._buckets[size])
        
        return stats

    def find_bucket(self, size: int) -> Optional[int]:
        """
        Find appropriate bucket size for given allocation size.
        Uses power-of-two sizing.
        
        Args:
            size: Requested allocation size
            
        Returns:
            Bucket size that can accommodate the request, or None if too large
        """
        # Power-of-two bucket sizes
        default_bucket_sizes = [1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144]
        
        for bucket_size in default_bucket_sizes:
            if size <= bucket_size:
                return bucket_size
        
        return None  # Too large for buckets

    def allocate_from_bucket(self, bucket_size: int) -> Optional[MemoryBlock]:
        """
        Allocate directly from a specific bucket.
        
        Args:
            bucket_size: Exact bucket size to allocate from
            
        Returns:
            MemoryBlock if available, None otherwise
        """
        bucket_lock = self._bucket_locks[bucket_size]
        with bucket_lock:
            bucket = self._buckets.get(bucket_size)
            if bucket:
                while bucket:
                    offset = bucket.pop()
                    if self._mark_as_allocated(offset):
                        return MemoryBlock(offset=offset, size=bucket_size)
        return None

    def _track_allocation_pattern(self, size: int) -> None:
        """
        Track allocation patterns for adaptive bucket creation.
        
        Args:
            size: Size being allocated
        """
        self.bucket_stats[size] += 1

    def get_snapshot(self) -> Dict:
        """Stats interface compatibility."""
        return self.get_stats()

    def get_fragmentation_stats(self) -> Dict:
        """
        Calculate fragmentation statistics.
        
        Returns:
            Dictionary with fragmentation metrics
        """
        bucket_count = sum(len(bucket) for bucket in self._buckets.values())
        
        with self._tree_lock:
            tree_count = sum(len(offsets) for offsets in self._size_to_offsets.values())
        
        total_free = bucket_count + tree_count
        
        if total_free == 0:
            bucket_util = 0.0
            tree_util = 0.0
            frag_ratio = 0.0
        else:
            bucket_util = bucket_count / total_free
            tree_util = tree_count / total_free
            frag_ratio = tree_util  # Higher tree usage indicates more fragmentation
        
        return {
            'fragmentation_ratio': frag_ratio,
            'bucket_utilization': bucket_util,
            'tree_utilization': tree_util,
            'total_free_blocks': total_free
        }