"""
Epochly Memory Foundation - Shared MemoryBlock Definition

This module provides a unified MemoryBlock class used across all memory management
components to ensure type compatibility and consistency. The implementation uses
a rock-solid total ordering that prevents infinite recursion in Red-Black tree
operations.

Author: Epochly Memory Foundation Team
"""

from functools import total_ordering
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

__all__ = ['MemoryBlock']


@total_ordering
class MemoryBlock:
    """
    Unified memory block representation used across the Epochly memory system.
    
    This class provides rock-solid total ordering that prevents infinite recursion
    in Red-Black tree operations. Uses __slots__ for memory efficiency and a 
    canonical _key() method to avoid circular comparison calls.
    
    Attributes:
        offset (int): Starting offset of the memory block
        size (int): Size of the memory block in bytes
        free (bool): Whether the block is free (True) or allocated (False)
    """
    __slots__ = ("offset", "size", "free", "invalid", "_alloc_id", "_is_sentinel")

    def __init__(self, offset: int, size: int, *, free: bool = True):
        """
        Initialize a memory block with dual-tier validation.
        
        Args:
            offset: Starting offset of the memory block
            size: Size of the memory block in bytes
            free: Whether the block is free (True) or allocated (False)
        """
        # Tier-1: allow a single sentinel combination (offset = -1 AND size = 0)
        self.invalid = (offset == -1 and size == 0)
        if not self.invalid:
            if offset < 0:
                raise ValueError(f"Invalid offset: {offset}")
            if size < 0:
                raise ValueError(f"Invalid size: {size}")
            if size == 0:
                # Sentinel / empty block – legal but cannot be allocated.
                self._is_sentinel = True
            else:
                self._is_sentinel = False
        else:
            self._is_sentinel = False
                
        self.offset = offset
        self.size = size
        self.free = free

    def _key(self):
        """
        Canonical key for comparison operations.
        
        The size is added as a tie-breaker so that (10, 128) and (10, 256)
        are different blocks in the tree. This prevents the infinite recursion
        that occurs when comparison operators call each other.
        
        Returns:
            tuple: (offset, size, free) for consistent ordering
        """
        return (self.offset, self.size, self.free)

    def __eq__(self, other):
        """
        Check equality using canonical key comparison.
        
        This implementation never calls any other rich comparison operator,
        preventing the recursion seen in stack traces.
        """
        if not isinstance(other, MemoryBlock):
            return NotImplemented
        return self._key() == other._key()

    def __lt__(self, other):
        """
        Compare blocks using canonical key comparison.
        
        This implementation never calls any other rich comparison operator,
        preventing the recursion seen in stack traces.
        """
        if not isinstance(other, MemoryBlock):
            return NotImplemented
        return self._key() < other._key()

    def __hash__(self):
        """Hash implementation so blocks can be used in dict/set."""
        return hash(self._key())

    def __repr__(self):
        """String representation of the memory block."""
        status = "free" if self.free else "allocated"
        return f"MemoryBlock(offset={self.offset}, size={self.size}, {status})"

    @property
    def end_offset(self) -> int:
        """Calculate the end offset of this block."""
        return self.offset + self.size
    
    def contains_offset(self, offset: int) -> bool:
        """Check if the given offset is within this block."""
        return self.offset <= offset < self.end_offset
    
    def overlaps_with(self, other: 'MemoryBlock') -> bool:
        """Check if this block overlaps with another block."""
        return (self.offset < other.end_offset and
                other.offset < self.end_offset)
    
    def is_adjacent_to(self, other: 'MemoryBlock') -> bool:
        """Check if this block is adjacent to another block."""
        return (self.end_offset == other.offset or
                other.end_offset == self.offset)
    
    def can_merge_with(self, other: 'MemoryBlock') -> bool:
        """Check if this block can be merged with another block."""
        return (self.free and other.free and
                self.is_adjacent_to(other))
    
    # Backward compatibility properties
    @property
    def allocated(self) -> bool:
        """Backward compatibility: allocated is the inverse of free."""
        return not self.free