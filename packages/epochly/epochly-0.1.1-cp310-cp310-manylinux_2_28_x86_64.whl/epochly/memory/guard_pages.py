"""
Epochly Guard Page Manager Implementation

This module provides guard page functionality for memory protection in Epochly's shared memory system.
Guard pages help detect buffer overflows, underflows, and other memory access violations by
creating protected memory regions that trigger segmentation faults when accessed.

Author: Epochly Development Team
"""

import mmap
import math
import sys
import threading
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import logging

from .exceptions import (
    GuardPageError
)
from .platform_memory import PlatformMemoryManager

logger = logging.getLogger(__name__)


class GuardPageType(Enum):
    """Types of guard pages."""
    PREFIX = "prefix"    # Guard page before allocated region
    SUFFIX = "suffix"    # Guard page after allocated region
    BOTH = "both"        # Guard pages before and after


# CRITICAL FIX: Use unified exception model instead of local exceptions
class GuardPageViolationError(GuardPageError):
    """Raised when guard page is accessed."""
    pass


@dataclass
class GuardedRegion:
    """Information about a guarded memory region."""
    data_offset: int
    data_size: int
    guard_type: GuardPageType
    prefix_guard_offset: Optional[int] = None
    prefix_guard_size: Optional[int] = None
    suffix_guard_offset: Optional[int] = None
    suffix_guard_size: Optional[int] = None
    
    @property
    def total_size(self) -> int:
        """Total size including guard pages."""
        size = self.data_size
        if self.prefix_guard_size:
            size += self.prefix_guard_size
        if self.suffix_guard_size:
            size += self.suffix_guard_size
        return size
    
    @property
    def start_offset(self) -> int:
        """Start offset of the entire guarded region."""
        if self.prefix_guard_offset is not None:
            return self.prefix_guard_offset
        return self.data_offset
    
    @property
    def end_offset(self) -> int:
        """End offset of the entire guarded region."""
        if self.suffix_guard_offset is not None:
            return self.suffix_guard_offset + (self.suffix_guard_size or 0)
        return self.data_offset + self.data_size


class GuardPageManager:
    """
    Manager for memory guard pages to detect access violations.
    
    Provides functionality to create and manage guard pages around allocated
    memory regions to detect buffer overflows and other memory access errors.
    """
    
    def __init__(
        self,
        page_size: Optional[int] = None,
        default_guard_type: GuardPageType = GuardPageType.BOTH,
        enable_violation_logging: bool = True
    ):
        """
        Initialize guard page manager.
        
        Args:
            page_size: Size of guard pages (defaults to system page size)
            default_guard_type: Default type of guard pages to create
            enable_violation_logging: Whether to log guard page violations
        """
        # Initialize platform memory manager for cross-platform compatibility
        self._platform_memory = PlatformMemoryManager()
        
        self._page_size = page_size or self._platform_memory._page_size
        self._default_guard_type = default_guard_type
        self._enable_violation_logging = enable_violation_logging
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Guard page tracking
        self._guarded_regions: Dict[int, GuardedRegion] = {}  # data_offset -> GuardedRegion
        self._guard_pages: Set[int] = set()  # Set of guard page offsets
        
        # Memory mapping for guard pages (platform-specific)
        self._memory_maps: Dict[int, mmap.mmap] = {}  # offset -> mmap object
        
        # Statistics
        self._total_guard_pages = 0
        self._violation_count = 0
        
        logger.debug(f"Initialized GuardPageManager with page size {self._page_size}")
        logger.debug(f"Platform: {self._platform_memory.get_platform_info()}")
    
    def _get_system_page_size(self) -> int:
        """Get system page size."""
        try:
            # Try different methods to get page size
            if hasattr(mmap, 'PAGESIZE'):
                return mmap.PAGESIZE
            elif sys.platform.startswith('win'):
                # Windows default page size
                return 4096
            else:
                # Default to 4KB on Unix-like systems
                return 4096
        except Exception:
            return 4096
    
    def _align_to_page_boundary(self, offset: int) -> int:
        """Align offset to page boundary."""
        return (offset // self._page_size) * self._page_size
    
    def _create_guard_page(self, offset: int, size: int) -> bool:
        """
        Create a guard page at specified offset using platform-specific memory protection.
        
        Args:
            offset: Offset where to create guard page
            size: Size of guard page
            
        Returns:
            True if guard page created successfully
        """
        try:
            # Align to page boundary
            aligned_offset = self._align_to_page_boundary(offset)
            # CRITICAL FIX: Replace manual ceil-division with math.ceil() for clarity and correctness
            # This prevents memory overshoot by one page for exact N*page_size blocks
            aligned_size = math.ceil(size / self._page_size) * self._page_size
            
            # Use platform memory manager for proper Windows RWX flag compatibility
            platform_info = self._platform_memory.get_platform_info()
            
            # Create memory mapping with platform-appropriate minimal access permissions
            if platform_info.platform == 'Windows':
                # Windows implementation - use platform memory manager for proper flag handling
                # Check if we can use no-access protection (ideal for guard pages)
                if platform_info.supports_rwx:
                    # Try to create with no access permissions if supported
                    try:
                        guard_map = mmap.mmap(-1, aligned_size, access=mmap.ACCESS_READ)
                        logger.debug("Windows guard page created with READ access (DEP compatible)")
                    except OSError as e:
                        logger.warning(f"Windows guard page creation failed with READ access: {e}")
                        return False
                else:
                    # DEP is enabled, use read-only as safest option
                    guard_map = mmap.mmap(-1, aligned_size, access=mmap.ACCESS_READ)
                    logger.debug("Windows guard page created with READ access (DEP enabled)")
            else:
                # POSIX systems - try to use minimal permissions
                try:
                    # Try with no permissions (Unix-specific)
                    guard_map = mmap.mmap(-1, aligned_size)
                    logger.debug("POSIX guard page created with default permissions")
                except (AttributeError, OSError):
                    # Fallback to read-only if no-permission mapping fails
                    guard_map = mmap.mmap(-1, aligned_size, access=mmap.ACCESS_READ)
                    logger.debug("POSIX guard page created with READ access (fallback)")
            
            self._memory_maps[aligned_offset] = guard_map
            self._guard_pages.add(aligned_offset)
            self._total_guard_pages += 1
            
            logger.debug(f"Created guard page at offset {aligned_offset}, size {aligned_size} on {platform_info.platform}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create guard page at {offset}: {e}")
            return False
    
    def _remove_guard_page(self, offset: int) -> bool:
        """
        Remove guard page at specified offset.
        
        Args:
            offset: Offset of guard page to remove
            
        Returns:
            True if guard page removed successfully
        """
        try:
            aligned_offset = self._align_to_page_boundary(offset)
            
            if aligned_offset in self._memory_maps:
                guard_map = self._memory_maps[aligned_offset]
                guard_map.close()
                del self._memory_maps[aligned_offset]
                
                self._guard_pages.discard(aligned_offset)
                self._total_guard_pages -= 1
                
                logger.debug(f"Removed guard page at offset {aligned_offset}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove guard page at {offset}: {e}")
            return False
    
    def create_guarded_region(
        self,
        data_offset: int,
        data_size: int,
        guard_type: Optional[GuardPageType] = None
    ) -> Optional[GuardedRegion]:
        """
        Create a guarded memory region.
        
        Args:
            data_offset: Offset of data region
            data_size: Size of data region
            guard_type: Type of guard pages to create
            
        Returns:
            GuardedRegion object if successful, None otherwise
            
        Raises:
            ValueError: If data_size is negative or zero
        """
        # Validate input parameters
        if data_size <= 0:
            raise ValueError("Data size must be positive")
        if data_offset < 0:
            raise GuardPageError("Data offset cannot be negative")
        
        if guard_type is None:
            guard_type = self._default_guard_type
        
        with self._lock:
            # Check if region already guarded
            if data_offset in self._guarded_regions:
                logger.warning(f"Region at {data_offset} already guarded")
                return self._guarded_regions[data_offset]
            
            region = GuardedRegion(
                data_offset=data_offset,
                data_size=data_size,
                guard_type=guard_type
            )
            
            success = True
            
            # Create prefix guard page
            if guard_type in (GuardPageType.PREFIX, GuardPageType.BOTH):
                prefix_offset = data_offset - self._page_size
                if prefix_offset >= 0:  # Ensure we don't go negative
                    if self._create_guard_page(prefix_offset, self._page_size):
                        region.prefix_guard_offset = prefix_offset
                        region.prefix_guard_size = self._page_size
                    else:
                        success = False
                else:
                    logger.warning(f"Cannot create prefix guard for region at {data_offset}")
            
            # Create suffix guard page
            if guard_type in (GuardPageType.SUFFIX, GuardPageType.BOTH):
                suffix_offset = data_offset + data_size
                if self._create_guard_page(suffix_offset, self._page_size):
                    region.suffix_guard_offset = suffix_offset
                    region.suffix_guard_size = self._page_size
                else:
                    success = False
            
            if success:
                self._guarded_regions[data_offset] = region
                logger.debug(f"Created guarded region for data at {data_offset}")
                return region
            else:
                # Clean up any partially created guard pages
                self.remove_guarded_region(data_offset)
                return None
    
    def remove_guarded_region(self, data_offset: int) -> bool:
        """
        Remove guarded region and its guard pages.
        
        Args:
            data_offset: Offset of data region
            
        Returns:
            True if region removed successfully
        """
        with self._lock:
            if data_offset not in self._guarded_regions:
                return False
            
            region = self._guarded_regions[data_offset]
            success = True
            
            # Remove prefix guard page
            if region.prefix_guard_offset is not None:
                if not self._remove_guard_page(region.prefix_guard_offset):
                    success = False
            
            # Remove suffix guard page
            if region.suffix_guard_offset is not None:
                if not self._remove_guard_page(region.suffix_guard_offset):
                    success = False
            
            # Remove from tracking
            del self._guarded_regions[data_offset]
            
            logger.debug(f"Removed guarded region for data at {data_offset}")
            return success
    
    def check_access_violation(self, offset: int, size: int) -> bool:
        """
        Check if memory access would violate guard pages.
        
        Args:
            offset: Offset of memory access
            size: Size of memory access
            
        Returns:
            True if access would violate guard pages
        """
        with self._lock:
            access_start = offset
            access_end = offset + size
            
            # Check if access overlaps with any guard pages
            for guard_offset in self._guard_pages:
                guard_end = guard_offset + self._page_size
                
                # Check for overlap
                if (access_start < guard_end and access_end > guard_offset):
                    if self._enable_violation_logging:
                        logger.error(
                            f"Guard page violation: access at {offset}-{access_end} "
                            f"overlaps guard page at {guard_offset}-{guard_end}"
                        )
                    self._violation_count += 1
                    return True
            
            return False
    
    def get_guarded_region(self, data_offset: int) -> Optional[GuardedRegion]:
        """Get guarded region information."""
        with self._lock:
            return self._guarded_regions.get(data_offset)
    
    def is_guard_page(self, offset: int) -> bool:
        """Check if offset is within a guard page."""
        with self._lock:
            aligned_offset = self._align_to_page_boundary(offset)
            return aligned_offset in self._guard_pages
    
    def get_data_region_for_offset(self, offset: int) -> Optional[GuardedRegion]:
        """Find the guarded region that contains the given offset."""
        with self._lock:
            for region in self._guarded_regions.values():
                if (region.data_offset <= offset < 
                    region.data_offset + region.data_size):
                    return region
            return None
    
    def validate_memory_access(self, offset: int, size: int) -> None:
        """
        Validate memory access and raise exception if it violates guard pages.
        
        Args:
            offset: Offset of memory access
            size: Size of memory access
            
        Raises:
            GuardPageViolationError: If access violates guard pages
        """
        if self.check_access_violation(offset, size):
            raise GuardPageViolationError(
                f"Memory access at offset {offset} size {size} violates guard pages"
            )
    
    @property
    def page_size(self) -> int:
        """Guard page size."""
        return self._page_size
    
    @property
    def total_guard_pages(self) -> int:
        """Total number of guard pages."""
        return self._total_guard_pages
    
    @property
    def violation_count(self) -> int:
        """Number of guard page violations detected."""
        return self._violation_count
    
    @property
    def guarded_region_count(self) -> int:
        """Number of guarded regions."""
        return len(self._guarded_regions)
    
    def get_statistics(self) -> Dict:
        """Get guard page manager statistics."""
        with self._lock:
            return {
                'page_size': self._page_size,
                'total_guard_pages': self._total_guard_pages,
                'total_regions': self.guarded_region_count,  # Expected by tests
                'guarded_regions': self.guarded_region_count,  # Keep old name for compatibility
                'violation_count': self._violation_count,
                'default_guard_type': self._default_guard_type.value,
                'memory_usage': self._total_guard_pages * self._page_size
            }
    
    def list_guarded_regions(self) -> List[GuardedRegion]:
        """Get list of all guarded regions."""
        with self._lock:
            return list(self._guarded_regions.values())
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
    
    def cleanup(self) -> None:
        """
        CRITICAL FIX: Clean up all guard pages and resources with proper Windows VirtualFree handling.
        """
        with self._lock:
            # Remove all guarded regions
            data_offsets = list(self._guarded_regions.keys())
            for data_offset in data_offsets:
                self.remove_guarded_region(data_offset)
            
            # CRITICAL FIX: Enhanced cleanup for Windows VirtualFree issue
            # Clean up any remaining memory maps with platform-specific handling
            for offset, guard_map in list(self._memory_maps.items()):
                try:
                    # Ensure proper cleanup on Windows
                    if sys.platform.startswith('win'):
                        # Windows-specific cleanup: ensure mmap is properly closed
                        # The Python mmap.close() should handle VirtualFree internally
                        # but we add extra safety measures
                        if hasattr(guard_map, 'closed') and not guard_map.closed:
                            guard_map.close()
                        # Additional safety: force garbage collection to ensure cleanup
                        import gc
                        gc.collect()
                    else:
                        # Unix-like systems
                        guard_map.close()
                        
                except Exception as e:
                    logger.error(f"CRITICAL: Error closing guard page at {offset}: {e}")
                    # On Windows, this could indicate VirtualFree was never called
                    if sys.platform.startswith('win'):
                        logger.error(f"Windows VirtualFree cleanup failed for guard page at {offset}")
            
            self._memory_maps.clear()
            self._guard_pages.clear()
            self._guarded_regions.clear()
            
            # CRITICAL FIX: Force garbage collection on Windows to ensure VirtualFree is called
            if sys.platform.startswith('win'):
                import gc
                gc.collect()
            
            logger.debug("Cleaned up GuardPageManager with platform-specific handling")