"""
Epochly Memory Management Module

This module provides the memory management foundation for Epochly's zero-copy shared memory system.
It includes memory pools, slab allocators, guard pages, and access control mechanisms.

Author: Epochly Development Team
"""

from .memory_pool import MemoryPool
from .slab_allocator import SlabAllocator
from .guard_pages import GuardPageManager
from .access_control import AccessController

# CRITICAL FIX: Export unified exception classes for proper error handling
from .exceptions import (
    MemoryFoundationError,
    AllocationError,
    DeallocationError,
    InvalidBlockException,
    PoolExhaustedException,
    PermissionError,
    GuardPageError
)

__all__ = [
    # Core memory management classes
    'MemoryPool',
    'SlabAllocator',
    'GuardPageManager',
    'AccessController',
    
    # Unified exception classes
    'MemoryFoundationError',
    'AllocationError',
    'DeallocationError',
    'InvalidBlockException',
    'PoolExhaustedException',
    'PermissionError',
    'GuardPageError'
]