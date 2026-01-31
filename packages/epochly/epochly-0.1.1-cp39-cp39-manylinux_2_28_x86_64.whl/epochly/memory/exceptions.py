"""
Epochly Memory Foundation Exception Classes

This module provides a unified error model for the Epochly memory foundation components.
All memory-related exceptions inherit from MemoryFoundationError to provide
consistent error handling across the memory management system.

Author: Epochly Development Team
"""

from typing import Optional


class MemoryFoundationError(Exception):
    """Base exception for memory foundation errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code


class AllocationError(MemoryFoundationError):
    """Memory allocation failures."""
    
    def __init__(self, message: str, size: Optional[int] = None, alignment: Optional[int] = None):
        super().__init__(message, "ALLOCATION_FAILED")
        self.size = size
        self.alignment = alignment


class DeallocationError(MemoryFoundationError):
    """Memory deallocation failures."""
    
    def __init__(self, message: str, offset: Optional[int] = None):
        super().__init__(message, "DEALLOCATION_FAILED")
        self.offset = offset


class PermissionError(MemoryFoundationError):
    """Access control violations."""
    
    def __init__(self, message: str, principal: Optional[str] = None, region_id: Optional[str] = None):
        super().__init__(message, "PERMISSION_DENIED")
        self.principal = principal
        self.region_id = region_id


class GuardPageError(MemoryFoundationError):
    """Guard page violations."""
    
    def __init__(self, message: str, region_id: Optional[str] = None):
        super().__init__(message, "GUARD_PAGE_VIOLATION")
        self.region_id = region_id


class InvalidRegionError(MemoryFoundationError):
    """Invalid memory region errors."""
    
    def __init__(self, message: str, offset: Optional[int] = None, size: Optional[int] = None):
        super().__init__(message, "INVALID_REGION")
        self.offset = offset
        self.size = size


class PoolExhaustedException(AllocationError):
    """Raised when memory pool is exhausted."""
    
    def __init__(self, message: str, pool_name: Optional[str] = None):
        super().__init__(message)
        self.error_code = "POOL_EXHAUSTED"
        self.pool_name = pool_name


class InvalidBlockException(MemoryFoundationError):
    """Raised when attempting to operate on invalid memory block."""
    
    def __init__(self, message: str, offset: Optional[int] = None):
        super().__init__(message, "INVALID_BLOCK")
        self.offset = offset


class AccessDeniedError(PermissionError):
    """Raised when access is denied."""
    pass


class SlabAllocationError(AllocationError):
    """Slab-specific allocation errors."""
    
    def __init__(self, message: str, object_size: Optional[int] = None):
        super().__init__(message)
        self.error_code = "SLAB_ALLOCATION_FAILED"
        self.object_size = object_size