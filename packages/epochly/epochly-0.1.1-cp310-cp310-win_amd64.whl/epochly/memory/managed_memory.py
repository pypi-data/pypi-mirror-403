"""
Epochly Managed Memory Implementation

This module provides context manager support for automatic memory cleanup.
Implements the managed memory view pattern for safe resource management.

Author: Epochly Development Team
"""

from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from .memory_pool import MemoryPool
    from .slab_allocator import SlabAllocator

logger = logging.getLogger(__name__)


class ManagedMemoryView:
    """
    PHASE 3: Context manager for automatic memory view cleanup.
    
    Provides automatic deallocation of memory views when exiting context.
    Ensures proper resource cleanup even in exception scenarios.
    """
    
    def __init__(self, pool: 'MemoryPool', offset: int, view: memoryview):
        """
        Initialize managed memory view.
        
        Args:
            pool: Memory pool that allocated the view
            offset: Offset of the allocated memory
            view: Memory view to manage
        """
        self.pool = pool
        self.offset = offset
        self.view = view
        self._released = False
    
    def __enter__(self) -> memoryview:
        """Context manager entry."""
        return self.view
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with automatic cleanup."""
        self.release()
    
    def release(self) -> None:
        """Manually release the memory view."""
        if not self._released and self.pool is not None:
            try:
                self.pool.deallocate(self.offset)
                self._released = True
                logger.debug("Released managed memory view")
            except Exception as e:
                logger.warning(f"Failed to release managed memory view: {e}")
    
    def __del__(self):
        """Destructor with cleanup."""
        self.release()


class ManagedSlabObject:
    """
    PHASE 3: Context manager for automatic slab object cleanup.
    
    Provides automatic deallocation of slab objects when exiting context.
    Ensures proper resource cleanup for fixed-size object allocations.
    """
    
    def __init__(self, allocator: 'SlabAllocator', object_offset: int):
        """
        Initialize managed slab object.
        
        Args:
            allocator: Slab allocator that allocated the object
            object_offset: Offset of the allocated object
        """
        self.allocator = allocator
        self.object_offset = object_offset
        self._released = False
    
    def __enter__(self) -> int:
        """Context manager entry."""
        return self.object_offset
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with automatic cleanup."""
        self.release()
    
    def get_memory_view(self) -> memoryview:
        """Get memory view for the allocated object."""
        if self._released:
            raise RuntimeError("Object has been released")
        return self.allocator.get_object_memory_view(self.object_offset)
    
    def release(self) -> None:
        """Manually release the slab object."""
        if not self._released and self.allocator is not None:
            try:
                self.allocator.deallocate(self.object_offset)
                self._released = True
                logger.debug(f"Released managed slab object at offset {self.object_offset}")
            except Exception as e:
                logger.warning(f"Failed to release managed slab object: {e}")
    
    def __del__(self):
        """Destructor with cleanup."""
        self.release()