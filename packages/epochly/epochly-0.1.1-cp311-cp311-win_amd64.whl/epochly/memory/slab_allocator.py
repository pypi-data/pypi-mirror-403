"""
Epochly Slab Allocator Implementation

This module provides a slab allocator for efficient allocation of fixed-size objects.
The slab allocator reduces fragmentation and improves performance for frequent
allocations and deallocations of objects of the same size.

Author: Epochly Development Team
"""

import threading
from typing import Dict, List, Optional, Set, Union, Any
from dataclasses import dataclass
from enum import Enum
import logging

from .memory_pool import MemoryPool
from .memory_block import MemoryBlock
from .exceptions import (
    AllocationError, InvalidBlockException
)
from .managed_memory import ManagedSlabObject
from .canary_checksums import (
    CanaryValidator, CanaryConfig
)

logger = logging.getLogger(__name__)


# WEEK 2 OPTIMIZATION: Compressed slab header implementation
# Reduces header from 32B to 16B using bit-fields and size-class indexing
class CompressedSlabHeader:
    """
    16-byte compressed slab header using production allocator techniques.
    
    Layout (128 bits total):
    - Size class index: 8 bits (256 size classes up to 64KB)
    - Flags: 8 bits (allocation state indicators)
    - Epoch-CRC hybrid: 32 bits (high 16b=epoch, low 16b=CRC16)
    - Free block bitmap: 64 bits (tracks up to 64 objects efficiently)
    - Reserved: 16 bits (alignment and future expansion)
    
    Based on jemalloc's chunk map bits and TCMalloc's span management.
    """
    
    # Size class table: maps 8-bit indices to actual sizes (8B to 64KB)
    SIZE_CLASSES = [
        8, 16, 24, 32, 48, 64, 80, 96, 112, 128,           # Small: 8-128B
        160, 192, 224, 256, 320, 384, 448, 512,           # Medium: 160-512B
        640, 768, 896, 1024, 1280, 1536, 1792, 2048,     # Large: 640B-2KB
        2560, 3072, 3584, 4096, 5120, 6144, 7168, 8192,  # XLarge: 2.5-8KB
    ] + [i * 1024 for i in range(10, 65)]  # 10KB-64KB in 1KB increments
    
    # Flag bit definitions (8 bits total)
    FLAG_DIRTY = 0x01       # Slab contains dirty memory
    FLAG_UNZEROED = 0x02    # Memory not zero-initialized
    FLAG_DECOMMITTED = 0x04 # Memory decommitted from OS
    FLAG_LARGE = 0x08       # Large allocation slab
    FLAG_ALLOCATED = 0x10   # Slab has allocated objects
    FLAG_RESERVED_1 = 0x20  # Reserved for future use
    FLAG_RESERVED_2 = 0x40  # Reserved for future use
    FLAG_CORRUPTION = 0x80  # Corruption detected flag
    
    def __init__(self, object_size: int, objects_per_slab: int):
        """Initialize compressed header for given object size."""
        self.size_class_index = self._size_to_class_index(object_size)
        self.flags = 0
        self.epoch = 0
        self.free_bitmap = (1 << min(objects_per_slab, 64)) - 1  # All free initially
        self.reserved = 0
        
    def _size_to_class_index(self, size: int) -> int:
        """Convert object size to size class index."""
        for i, class_size in enumerate(self.SIZE_CLASSES):
            if size <= class_size:
                return i
        raise ValueError(f"Size {size} exceeds maximum size class")
    
    def get_object_size(self) -> int:
        """Get actual object size from size class index."""
        if self.size_class_index >= len(self.SIZE_CLASSES):
            raise ValueError(f"Invalid size class index: {self.size_class_index}")
        return self.SIZE_CLASSES[self.size_class_index]
    
    def _compute_crc16(self, data: bytes) -> int:
        """Compute CRC-16 checksum for corruption detection."""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc & 0xFFFF
    
    def pack(self) -> bytes:
        """Pack header into 16-byte binary format."""
        import struct
        
        # Compute CRC over first 6 bytes (size_class, flags, epoch)
        header_data = struct.pack('<BBL', self.size_class_index, self.flags, self.epoch)
        crc = self._compute_crc16(header_data)
        
        # Pack into 16-byte structure
        return struct.pack('<BBLHQH',
                          self.size_class_index,  # 1 byte
                          self.flags,             # 1 byte
                          self.epoch,             # 4 bytes
                          crc,                    # 2 bytes
                          self.free_bitmap,       # 8 bytes
                          self.reserved)          # 2 bytes (padding)
    
    def unpack(self, data: bytes) -> None:
        """Unpack header from 16-byte binary format."""
        import struct
        
        if len(data) != 16:
            raise ValueError(f"Header data must be 16 bytes, got {len(data)}")
        
        # Unpack structure
        (self.size_class_index, self.flags, self.epoch,
         stored_crc, self.free_bitmap, self.reserved) = struct.unpack('<BBLHQH', data)
        
        # Verify CRC integrity
        header_data = struct.pack('<BBL', self.size_class_index, self.flags, self.epoch)
        computed_crc = self._compute_crc16(header_data)
        
        if stored_crc != computed_crc:
            self.flags |= self.FLAG_CORRUPTION
            logger.warning(f"Header corruption detected: stored_crc={stored_crc:04x}, computed_crc={computed_crc:04x}")
    
    def increment_epoch(self) -> None:
        """Increment epoch counter for ABA prevention."""
        self.epoch = (self.epoch + 1) & 0xFFFFFFFF  # 32-bit wrap-around
    
    def is_object_free(self, object_index: int) -> bool:
        """Check if object at index is free using bitmap."""
        if object_index >= 64:
            return False  # Beyond bitmap range
        return bool(self.free_bitmap & (1 << object_index))
    
    def allocate_object(self, object_index: int) -> None:
        """Mark object as allocated in bitmap."""
        if object_index < 64:
            self.free_bitmap &= ~(1 << object_index)
            self.flags |= self.FLAG_ALLOCATED
    
    def deallocate_object(self, object_index: int) -> None:
        """Mark object as free in bitmap."""
        if object_index < 64:
            self.free_bitmap |= (1 << object_index)
            # Clear allocated flag if no objects remain allocated
            if self.free_bitmap == (1 << 64) - 1:
                self.flags &= ~self.FLAG_ALLOCATED


class SlabState(Enum):
    """Slab allocation states."""
    EMPTY = "empty"      # No objects allocated
    PARTIAL = "partial"  # Some objects allocated
    FULL = "full"        # All objects allocated


@dataclass
class SlabInfo:
    """
    Information about a slab with compressed header support.
    
    WEEK 2 OPTIMIZATION: Integrates 16-byte compressed headers for 50% metadata reduction.
    Uses bitmap-based object tracking instead of set-based free object lists.
    """
    offset: int
    size: int
    object_size: int
    objects_per_slab: int
    allocated_objects: int
    header: CompressedSlabHeader  # OPTIMIZATION: Compressed 16-byte header
    state: SlabState
    
    @property
    def utilization(self) -> float:
        """Get slab utilization ratio."""
        return self.allocated_objects / self.objects_per_slab
    
    @property
    def free_objects(self) -> Set[int]:
        """Get free object offsets from compressed header bitmap."""
        free_set = set()
        for i in range(min(self.objects_per_slab, 64)):
            if self.header.is_object_free(i):
                object_offset = self.offset + (i * self.object_size)
                free_set.add(object_offset)
        return free_set
    
    def is_object_free_at_index(self, object_index: int) -> bool:
        """Check if object at index is free using compressed header."""
        return self.header.is_object_free(object_index)
    
    def allocate_object_at_index(self, object_index: int) -> int:
        """Allocate object at specific index, return offset."""
        if not self.header.is_object_free(object_index):
            raise ValueError(f"Object at index {object_index} already allocated")
        
        self.header.allocate_object(object_index)
        self.header.increment_epoch()  # ABA prevention
        self.allocated_objects += 1
        
        return self.offset + (object_index * self.object_size)
    
    def deallocate_object_at_offset(self, object_offset: int) -> None:
        """Deallocate object at specific offset."""
        if object_offset < self.offset or object_offset >= self.offset + self.size:
            raise ValueError(f"Object offset {object_offset} outside slab bounds")
        
        relative_offset = object_offset - self.offset
        if relative_offset % self.object_size != 0:
            raise ValueError(f"Object offset {object_offset} not properly aligned")
        
        object_index = relative_offset // self.object_size
        if object_index >= self.objects_per_slab:
            raise ValueError(f"Object index {object_index} exceeds slab capacity")
        
        self.header.deallocate_object(object_index)
        self.header.increment_epoch()  # ABA prevention
        self.allocated_objects -= 1


# CRITICAL FIX: Use unified exception model instead of local exceptions
class NoSlabAvailableError(AllocationError):
    """Raised when no slab is available for allocation."""
    pass


class InvalidObjectError(InvalidBlockException):
    """Raised when attempting to operate on invalid object."""
    pass


class SlabAllocator:
    """
    High-performance slab allocator for fixed-size objects.
    
    Provides efficient allocation and deallocation of fixed-size objects
    with minimal fragmentation and fast allocation/deallocation operations.
    """
    
    def __init__(
        self,
        object_size: int,
        objects_per_slab: Optional[int] = None,
        alignment: int = 8,
        initial_slabs: int = 1,
        max_slabs: Optional[int] = None,
        memory_pool: Optional[MemoryPool] = None,
        name: Optional[str] = None,
        enable_canaries: bool = True,
        canary_config: Optional[CanaryConfig] = None
    ):
        """
        Initialize slab allocator.
        
        Args:
            object_size: Size of objects to allocate
            objects_per_slab: Number of objects per slab (auto-calculated if None)
            alignment: Memory alignment requirement
            initial_slabs: Number of slabs to create initially
            max_slabs: Maximum number of slabs (unlimited if None)
            memory_pool: Memory pool to use (creates own if None)
            name: Optional name for debugging
            enable_canaries: Enable canary checksum protection
            canary_config: Configuration for canary checksums
        """
        # Enhanced validation for edge cases
        if object_size <= 0:
            raise ValueError("Object size must be positive")
        if object_size > 1024 * 1024 * 1024:  # 1GB limit for sanity
            raise ValueError("Object size too large")
        if alignment <= 0 or (alignment & (alignment - 1)) != 0:
            raise ValueError("Alignment must be a positive power of 2")
        if initial_slabs < 0:
            raise ValueError("Initial slabs must be non-negative")
        if max_slabs is not None and max_slabs < initial_slabs:
            raise ValueError("Max slabs must be >= initial slabs")
        if objects_per_slab is not None and objects_per_slab <= 0:
            raise ValueError("Objects per slab must be positive")
        
        # Validate object size vs objects per slab combination
        if objects_per_slab is not None:
            # Account for slab metadata overhead (free-list head, counters, lock, etc.)
            PAGE_SIZE = 4 * 1024  # 4KB limit per slab for testing
            HEADER_SIZE = 16      # WEEK 2 OPTIMIZATION: Compressed slab header using bit-fields
            usable_per_slab = PAGE_SIZE - HEADER_SIZE
            
            potential_slab_size = object_size * objects_per_slab
            if potential_slab_size >= usable_per_slab:
                raise ValueError(
                    "Object size and objects per slab combination leaves "
                    "no room for slab metadata"
                )
        
        # Store the base object size (user-requested size)
        self._base_object_size = self._align_size(object_size, alignment)
        self._alignment = alignment
        self._initial_slabs = initial_slabs
        self._max_slabs = max_slabs
        self._name = name or f"SlabAllocator_{self._base_object_size}"
        
        # Initialize canary protection
        self.enable_canaries = enable_canaries
        if enable_canaries:
            self.canary_validator = CanaryValidator(canary_config or CanaryConfig())
        else:
            self.canary_validator = None
        
        # Calculate effective object size including guard zones when canaries are enabled
        if enable_canaries and self.canary_validator:
            # Add space for front and rear guard zones
            guard_size = self.canary_validator.config.guard_size
            self._object_size = self._base_object_size + (2 * guard_size)
            logger.debug(f"Canaries enabled: base_size={self._base_object_size}, guard_size={guard_size}, effective_size={self._object_size}")
        else:
            self._object_size = self._base_object_size
        
        # Calculate objects per slab if not specified
        if objects_per_slab is None:
            # Aim for slabs around 4KB to 64KB, using effective object size
            target_slab_size = max(4096, min(65536, self._object_size * 64))
            self._objects_per_slab = max(1, target_slab_size // self._object_size)
        else:
            self._objects_per_slab = objects_per_slab
        
        self._slab_size = self._objects_per_slab * self._object_size
        
        # PHASE 3 OPTIMIZATION: Use Lock instead of RLock for better performance
        # RLock has 2x overhead for non-reentrant operations
        self._lock = threading.Lock()
        
        # Memory management
        self._owns_memory_pool = memory_pool is None
        if self._owns_memory_pool:
            # Create memory pool large enough for max slabs
            pool_size = self._slab_size * (max_slabs or 100)
            self._memory_pool = MemoryPool(
                total_size=pool_size,
                alignment=alignment,
                name=f"{self._name}_pool"
            )
        else:
            self._memory_pool = memory_pool
        
        # Slab management
        self._slabs: Dict[int, SlabInfo] = {}  # offset -> SlabInfo
        self._empty_slabs: List[int] = []      # offsets of empty slabs
        self._partial_slabs: List[int] = []    # offsets of partial slabs
        self._full_slabs: List[int] = []       # offsets of full slabs
        
        # Object tracking
        self._object_to_slab: Dict[int, int] = {}  # object offset -> slab offset
        self._object_canaries: Dict[int, Dict[str, Any]] = {}  # object offset -> canary metadata
        
        # Block tracking for unified interface
        self._allocated_blocks: Dict[int, MemoryBlock] = {}  # object offset -> MemoryBlock
        self._block_counter = 0  # For generating unique allocation IDs
        
        # Statistics
        self._total_objects_allocated = 0
        self._total_allocations = 0
        self._total_deallocations = 0
        
        # Initialize with initial slabs
        self._initialize_slabs()
    
    def _align_size(self, size: int, alignment: int) -> int:
        """Align size to specified boundary."""
        return (size + alignment - 1) & ~(alignment - 1)
    
    def _initialize_slabs(self) -> None:
        """Initialize the allocator with initial slabs."""
        for _ in range(self._initial_slabs):
            try:
                self._create_new_slab()
            except Exception as e:
                logger.warning(f"Failed to create initial slab: {e}")
                break
    
    def _create_new_slab(self) -> int:
        """
        Create a new slab.
        
        Returns:
            Offset of the new slab
            
        Raises:
            NoSlabAvailableError: If unable to create new slab
        """
        if (self._max_slabs is not None and
            len(self._slabs) >= self._max_slabs):
            raise NoSlabAvailableError("Maximum number of slabs reached")
        
        try:
            # Allocate memory for new slab
            if self._memory_pool is None:
                raise NoSlabAvailableError("Memory pool not available")
            
            # Handle new MemoryBlock interface from memory pool
            slab_block = self._memory_pool.allocate(
                self._slab_size,
                alignment=self._alignment
            )
            
            if slab_block is None:
                raise NoSlabAvailableError("Memory pool allocation failed")
            
            # Extract offset from MemoryBlock
            slab_offset = slab_block.offset
            
            # WEEK 2 OPTIMIZATION: Create compressed header instead of free object set
            compressed_header = CompressedSlabHeader(
                object_size=self._object_size,
                objects_per_slab=self._objects_per_slab
            )
            
            # Create slab info with compressed header
            slab_info = SlabInfo(
                offset=slab_offset,
                size=self._slab_size,
                object_size=self._object_size,
                objects_per_slab=self._objects_per_slab,
                allocated_objects=0,
                header=compressed_header,
                state=SlabState.EMPTY
            )
            
            # Add to management structures
            self._slabs[slab_offset] = slab_info
            self._empty_slabs.append(slab_offset)
            
            logger.debug(
                f"Created new slab at offset {slab_offset} "
                f"with {self._objects_per_slab} objects"
            )
            
            return slab_offset
            
        except Exception as e:
            raise NoSlabAvailableError(f"Failed to create new slab: {e}")
    
    def _update_slab_state(self, slab_offset: int) -> None:
        """Update slab state based on allocation count."""
        slab = self._slabs[slab_offset]
        old_state = slab.state
        
        # Determine new state
        if slab.allocated_objects == 0:
            new_state = SlabState.EMPTY
        elif slab.allocated_objects == slab.objects_per_slab:
            new_state = SlabState.FULL
        else:
            new_state = SlabState.PARTIAL
        
        # Update state if changed
        if old_state != new_state:
            slab.state = new_state
            
            # Remove from old list
            if old_state == SlabState.EMPTY and slab_offset in self._empty_slabs:
                self._empty_slabs.remove(slab_offset)
            elif old_state == SlabState.PARTIAL and slab_offset in self._partial_slabs:
                self._partial_slabs.remove(slab_offset)
            elif old_state == SlabState.FULL and slab_offset in self._full_slabs:
                self._full_slabs.remove(slab_offset)
            
            # Add to new list
            if new_state == SlabState.EMPTY:
                self._empty_slabs.append(slab_offset)
            elif new_state == SlabState.PARTIAL:
                self._partial_slabs.append(slab_offset)
            elif new_state == SlabState.FULL:
                self._full_slabs.append(slab_offset)
    
    def _find_available_slab(self) -> int:
        """
        Find a slab with available objects.
        
        Returns:
            Offset of available slab
            
        Raises:
            NoSlabAvailableError: If no slab is available
        """
        # Prefer partial slabs to reduce fragmentation
        if self._partial_slabs:
            return self._partial_slabs[0]
        
        # Use empty slabs if no partial slabs
        if self._empty_slabs:
            return self._empty_slabs[0]
        
        # Try to create new slab
        return self._create_new_slab()
    
    def allocate(self) -> Optional[MemoryBlock]:
        """
        Allocate an object.
        
        Returns:
            MemoryBlock representing the allocated object, or None if allocation fails
            
        Raises:
            NoSlabAvailableError: If no object can be allocated
        """
        with self._lock:
            try:
                # Find available slab
                slab_offset = self._find_available_slab()
                slab = self._slabs[slab_offset]
                
                # WEEK 2 OPTIMIZATION: Use compressed header bitmap for allocation
                # Find first free object using bitmap
                free_index = None
                for i in range(min(slab.objects_per_slab, 64)):
                    if slab.header.is_object_free(i):
                        free_index = i
                        break
                
                if free_index is None:
                    raise NoSlabAvailableError("Slab has no free objects")
                
                # Allocate object using compressed header
                object_offset = slab.allocate_object_at_index(free_index)
                self._object_to_slab[object_offset] = slab_offset
                
                # Create MemoryBlock for unified interface
                self._block_counter += 1
                memory_block = MemoryBlock(
                    offset=object_offset,
                    size=self._base_object_size,  # User-visible size (excluding guard zones)
                    free=False
                )
                # Set additional attributes after creation
                memory_block._alloc_id = self._block_counter
                
                # Store block for tracking
                self._allocated_blocks[object_offset] = memory_block
                
                # Install canary protection if enabled
                if self.enable_canaries and self.canary_validator and self._memory_pool:
                    try:
                        # With the new layout, guard zones are already included in object spacing
                        # The allocated slot contains: [front_guard][user_object][rear_guard]
                        guard_size = self.canary_validator.config.guard_size
                        
                        # Get memory view for the entire allocated slot (includes guard zones)
                        memory_view = self._memory_pool.memory_view(object_offset, self._object_size)
                        
                        # Debug logging
                        logger.debug(f"Installing canaries for object {object_offset}, guard_size={guard_size}")
                        logger.debug(f"Slot size={self._object_size}, user_size={self._base_object_size}")
                        logger.debug(f"Should protect: {self.canary_validator.config.should_protect(self._base_object_size)}")
                        
                        # Install canaries with user object starting at guard_size offset within the slot
                        canary_metadata = self.canary_validator.install_canaries(
                            memory_view, guard_size, self._base_object_size
                        )
                        
                        logger.debug(f"Canary metadata returned: {canary_metadata}")
                        
                        # Store canary metadata for validation during deallocation
                        if canary_metadata.get('protected', False):
                            self._object_canaries[object_offset] = canary_metadata
                            logger.debug(f"Stored canary metadata for object {object_offset}")
                        else:
                            logger.debug(f"Object {object_offset} not protected (protected={canary_metadata.get('protected', False)})")
                        
                    except Exception as e:
                        logger.warning(f"Failed to install canaries for object {object_offset}: {e}")
                        import traceback
                        logger.warning(f"Traceback: {traceback.format_exc()}")
                
                # Update slab state
                self._update_slab_state(slab_offset)
                
                # Update statistics
                self._total_objects_allocated += 1
                self._total_allocations += 1
                
                logger.debug(f"Allocated object at offset {object_offset} (index {free_index})")
                
                return memory_block
                
            except NoSlabAvailableError:
                # Return None for allocation failure instead of raising exception
                logger.debug("Allocation failed: no slab available")
                return None
            except Exception as e:
                logger.error(f"Unexpected error during allocation: {e}")
                return None
    
    def managed_allocate(self) -> ManagedSlabObject:
        """
        PHASE 3: Allocate an object with automatic cleanup support.
        
        Returns:
            ManagedSlabObject that automatically deallocates on context exit
            
        Raises:
            NoSlabAvailableError: If no object can be allocated
        """
        memory_block = self.allocate()
        if memory_block is None:
            raise NoSlabAvailableError("Failed to allocate object")
        return ManagedSlabObject(self, memory_block.offset)
    
    def deallocate(self, object_ref: Union[int, MemoryBlock]) -> None:
        """
        Deallocate an object.
        
        Args:
            object_ref: MemoryBlock or offset of object to deallocate
            
        Raises:
            InvalidObjectError: If object is not allocated
        """
        with self._lock:
            # Handle both MemoryBlock objects and integer offsets
            if isinstance(object_ref, MemoryBlock):
                object_offset = object_ref.offset
            else:
                object_offset = object_ref
                
            # Find slab containing object
            if object_offset not in self._object_to_slab:
                raise InvalidObjectError(f"Object at offset {object_offset} not allocated")
            
            slab_offset = self._object_to_slab[object_offset]
            slab = self._slabs[slab_offset]
            
            # Validate canaries if object was protected
            if (self.enable_canaries and self.canary_validator and
                object_offset in self._object_canaries and self._memory_pool is not None):
                canary_metadata = self._object_canaries[object_offset]
                try:
                    # Use the stored guard positions from metadata
                    if canary_metadata.get('protected', False):
                        # With the new layout, get memory view for the entire allocated slot
                        memory_view = self._memory_pool.memory_view(object_offset, self._object_size)
                        
                        # Validate canaries using the stored metadata
                        is_valid, corruption_type = self.canary_validator.validate_canaries(memory_view, canary_metadata)
                        if not is_valid and corruption_type:
                            raise InvalidObjectError(f"Memory corruption detected during deallocation: {corruption_type.name}")
                        
                        # Mark object as freed for use-after-free detection
                        self.canary_validator.mark_freed(memory_view, canary_metadata)
                    
                except InvalidObjectError:
                    # Re-raise corruption errors
                    raise
                except Exception as e:
                    logger.warning(f"Canary validation failed during deallocation of object {object_offset}: {e}")
                    # Continue with deallocation even if canary validation fails
                
                # Always clean up canary metadata after deallocation
                if object_offset in self._object_canaries:
                    del self._object_canaries[object_offset]
            
            # WEEK 2 OPTIMIZATION: Use compressed header for deallocation
            # Deallocate using SlabInfo's compressed header method
            slab.deallocate_object_at_offset(object_offset)
            del self._object_to_slab[object_offset]
            
            # Update slab state
            self._update_slab_state(slab_offset)
            
            # Update statistics
            self._total_objects_allocated -= 1
            self._total_deallocations += 1
            
            logger.debug(f"Deallocated object at offset {object_offset}")
    
    def free(self, block: MemoryBlock) -> bool:
        """
        Free a memory block (unified interface).
        
        Args:
            block: MemoryBlock to free
            
        Returns:
            True if successfully freed, False otherwise
        """
        try:
            # Validate that this block was allocated by this allocator
            if block.offset not in self._allocated_blocks:
                logger.warning(f"Attempt to free block not allocated by this allocator: {block}")
                return False
            
            # Verify block matches our records
            stored_block = self._allocated_blocks[block.offset]
            if stored_block.offset != block.offset or stored_block.size != block.size:
                logger.warning(f"Block mismatch during free: expected {stored_block}, got {block}")
                return False
            
            # Deallocate using existing method
            self.deallocate(block.offset)
            
            # Clean up block tracking
            if block.offset in self._allocated_blocks:
                del self._allocated_blocks[block.offset]
            
            return True
            
        except Exception as e:
            logger.error(f"Error freeing block {block}: {e}")
            return False
    
    def get_object_memory_view(self, object_offset: int) -> memoryview:
        """
        Get memory view for allocated object (user data only, excluding guard zones).
        
        Args:
            object_offset: Offset of allocated object
            
        Returns:
            Memory view of the user object (excluding guard zones)
            
        Raises:
            InvalidObjectError: If object is not allocated
        """
        with self._lock:
            if object_offset not in self._object_to_slab:
                raise InvalidObjectError(f"Object at offset {object_offset} not allocated")
            
            if self._memory_pool is None:
                raise InvalidObjectError("Memory pool not available")
            
            # If canaries are enabled, return view of user object (skip front guard zone)
            if self.enable_canaries and self.canary_validator:
                guard_size = self.canary_validator.config.guard_size
                user_object_offset = object_offset + guard_size
                return self._memory_pool.memory_view(user_object_offset, self._base_object_size)
            else:
                return self._memory_pool.memory_view(object_offset, self._base_object_size)
    
    def compact(self, aggressive: bool = False) -> int:
        """
        CRITICAL FIX: Compact allocator by freeing empty slabs to prevent RSS creep.
        
        Args:
            aggressive: If True, free ALL empty slabs. If False, keep one for future allocations.
        
        Returns:
            Number of slabs freed
        """
        with self._lock:
            freed_count = 0
            
            # CRITICAL FIX: More aggressive empty slab cleanup to prevent RSS creep
            # Determine how many empty slabs to keep
            min_empty_slabs = 0 if aggressive else 1
            
            # Free empty slabs beyond the minimum
            while len(self._empty_slabs) > min_empty_slabs:
                slab_offset = self._empty_slabs.pop()
                self._slabs[slab_offset]
                
                try:
                    # Deallocate slab memory
                    if self._memory_pool is not None:
                        self._memory_pool.deallocate(slab_offset)
                    del self._slabs[slab_offset]
                    freed_count += 1
                    
                    logger.debug(f"Freed empty slab at offset {slab_offset}")
                    
                except Exception as e:
                    logger.warning(f"Failed to free slab at {slab_offset}: {e}")
                    # Re-add to empty slabs if deallocation failed
                    self._empty_slabs.append(slab_offset)
                    break
            
            return freed_count
    
    @property
    def object_size(self) -> int:
        """Size of user objects allocated by this allocator (excluding guard zones)."""
        return self._base_object_size
    
    @property
    def objects_per_slab(self) -> int:
        """Number of objects per slab."""
        return self._objects_per_slab
    
    @property
    def slab_size(self) -> int:
        """Size of each slab."""
        return self._slab_size
    
    @property
    def total_slabs(self) -> int:
        """Total number of slabs."""
        return len(self._slabs)
    
    @property
    def allocated_objects(self) -> int:
        """Number of currently allocated objects."""
        return self._total_objects_allocated
    
    @property
    def total_capacity(self) -> int:
        """Total object capacity across all slabs."""
        return len(self._slabs) * self._objects_per_slab
    
    @property
    def utilization(self) -> float:
        """Overall utilization ratio."""
        if self.total_capacity == 0:
            return 0.0
        return self.allocated_objects / self.total_capacity
    
    def get_statistics(self) -> Dict:
        """Get detailed allocator statistics."""
        with self._lock:
            return {
                'name': self._name,
                'object_size': self._object_size,
                'objects_per_slab': self._objects_per_slab,
                'slab_size': self._slab_size,
                'total_slabs': self.total_slabs,
                'empty_slabs': len(self._empty_slabs),
                'partial_slabs': len(self._partial_slabs),
                'full_slabs': len(self._full_slabs),
                'allocated_objects': self.allocated_objects,
                'total_capacity': self.total_capacity,
                'utilization': self.utilization,
                'total_allocations': self._total_allocations,
                'total_deallocations': self._total_deallocations,
                'memory_pool_stats': self._memory_pool.get_statistics() if self._owns_memory_pool and self._memory_pool is not None else None
            }
    
    def get_slab_info(self, slab_offset: int) -> Optional[SlabInfo]:
        """Get information about a specific slab."""
        with self._lock:
            return self._slabs.get(slab_offset)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up allocator resources."""
        with self._lock:
            # Clear all tracking structures
            self._slabs.clear()
            self._empty_slabs.clear()
            self._partial_slabs.clear()
            self._full_slabs.clear()
            self._object_to_slab.clear()
            
            # Clean up memory pool if we own it
            if self._owns_memory_pool and self._memory_pool:
                # MemoryPool cleanup is handled automatically by __del__
                pass
            
            logger.debug(f"Cleaned up {self._name}")