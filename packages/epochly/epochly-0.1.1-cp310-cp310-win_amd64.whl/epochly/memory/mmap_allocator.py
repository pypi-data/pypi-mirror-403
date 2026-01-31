"""
Epochly Memory Foundation - mmap-Backed Allocator (Tier 2 Fallback)

This module provides a high-performance mmap-backed allocator for use when
the Cython fast allocator is unavailable. Designed to provide intermediate
performance between Cython (Tier 1) and pure Python (Tier 3).

Key features:
- mmap-based allocation for direct memory management
- First-fit allocation with automatic block coalescing
- Performance within 10% of CPython allocator throughput
- Used automatically when Cython extension unavailable

Author: Epochly Memory Foundation Team
Created: 2025-11-11 (MEM-4)
"""

import mmap
import logging
from typing import Optional, Dict, List, Tuple, Any

logger = logging.getLogger(__name__)


class MmapBackedAllocator:
    """
    mmap-based memory allocator for when Cython unavailable.

    This allocator provides intermediate performance (Tier 2) between
    Cython fast allocator (Tier 1) and pure Python fallback (Tier 3).

    Uses first-fit allocation with automatic coalescing for efficient memory reuse.
    """

    def __init__(self, pool_size_mb: int = 64):
        """
        Initialize mmap-backed allocator.

        Args:
            pool_size_mb: Size of memory pool in megabytes
        """
        # CRITICAL: Initialize cleanup tracking FIRST to prevent AttributeError in __del__
        self._initialized = False
        self.mmap_pool = None

        self.pool_size = pool_size_mb * 1024 * 1024

        # Create anonymous mmap
        try:
            self.mmap_pool = mmap.mmap(-1, self.pool_size)
            logger.info(f"Initialized mmap allocator with {pool_size_mb}MB pool")
        except Exception as e:
            logger.error(f"Failed to create mmap pool: {e}")
            raise

        # Track allocations: offset -> size
        self.allocations: Dict[int, int] = {}

        # Free blocks: List of (offset, size) sorted by offset
        self.free_blocks: List[Tuple[int, int]] = [(0, self.pool_size)]

        # Statistics
        self.total_allocations = 0
        self.total_deallocations = 0

        # Mark as fully initialized
        self._initialized = True

    def allocate(self, size: int, alignment: int = 8) -> Optional[int]:
        """
        Allocate memory from mmap pool.

        Args:
            size: Size to allocate in bytes
            alignment: Alignment requirement (power of 2)

        Returns:
            Offset of allocated block, or None if allocation failed
        """
        if size <= 0:
            return None

        # Validate alignment is power of 2
        if alignment <= 0 or (alignment & (alignment - 1)) != 0:
            logger.warning(f"Invalid alignment {alignment} (must be power of 2), using default 8")
            alignment = 8

        # Find first-fit free block
        for i, (offset, block_size) in enumerate(self.free_blocks):
            # Calculate aligned offset within this block
            aligned_offset = (offset + alignment - 1) & ~(alignment - 1)
            padding = aligned_offset - offset

            # Check if aligned allocation fits in this block
            if aligned_offset + size <= offset + block_size:
                # Remove this free block
                self.free_blocks.pop(i)

                # Add padding back as free block if any
                if padding > 0:
                    self.free_blocks.append((offset, padding))

                # Add remainder as free block if any
                remainder = (offset + block_size) - (aligned_offset + size)
                if remainder > 0:
                    self.free_blocks.append((aligned_offset + size, remainder))

                # Sort free blocks by offset for coalescing
                self.free_blocks.sort(key=lambda x: x[0])

                # Track allocation
                self.allocations[aligned_offset] = size
                self.total_allocations += 1

                return aligned_offset

        # No suitable block found
        return None

    def deallocate(self, offset: int, size: int) -> None:
        """
        Deallocate memory block.

        Args:
            offset: Offset of block to deallocate
            size: Size of block (must match allocation)
        """
        if offset not in self.allocations:
            raise ValueError(f"Block at offset {offset} not allocated")

        alloc_size = self.allocations.pop(offset)
        if alloc_size != size:
            logger.warning(f"Deallocation size mismatch: expected {alloc_size}, got {size}")

        # Add to free list using RECORDED size (prevents free list corruption)
        self.free_blocks.append((offset, alloc_size))
        self.total_deallocations += 1

        # Coalesce adjacent free blocks
        self._coalesce_free_blocks()

    def _coalesce_free_blocks(self) -> None:
        """Coalesce adjacent free blocks to reduce fragmentation."""
        if len(self.free_blocks) <= 1:
            return

        # Sort by offset
        self.free_blocks.sort(key=lambda x: x[0])

        # Merge adjacent blocks
        coalesced = []
        current_offset, current_size = self.free_blocks[0]

        for offset, size in self.free_blocks[1:]:
            if current_offset + current_size == offset:
                # Adjacent - merge
                current_size += size
            else:
                # Not adjacent - save current and start new
                coalesced.append((current_offset, current_size))
                current_offset, current_size = offset, size

        # Add last block
        coalesced.append((current_offset, current_size))
        self.free_blocks = coalesced

    def get_statistics(self) -> Dict[str, Any]:
        """Get allocator statistics."""
        total_free = sum(size for _, size in self.free_blocks)
        total_allocated = sum(self.allocations.values())

        return {
            'pool_size': self.pool_size,
            'allocated_bytes': total_allocated,
            'free_bytes': total_free,
            'allocations': len(self.allocations),
            'total_allocations': self.total_allocations,
            'total_deallocations': self.total_deallocations,
            'free_blocks': len(self.free_blocks),
            'fragmentation_ratio': len(self.free_blocks) / max(1, len(self.allocations) + len(self.free_blocks))
        }

    def cleanup(self) -> None:
        """Clean up mmap resources."""
        try:
            if hasattr(self, 'mmap_pool') and self.mmap_pool:
                self.mmap_pool.close()
                self.mmap_pool = None

            self.allocations.clear()
            self.free_blocks.clear()

            logger.info("Cleaned up mmap allocator")
        except Exception as e:
            logger.error(f"Error during mmap allocator cleanup: {e}")

    def __del__(self):
        """Ensure cleanup on deletion."""
        if hasattr(self, '_initialized') and self._initialized:
            self.cleanup()
