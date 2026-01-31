"""
Zero-Copy Buffer Implementation for Sub-Interpreter Communication

This module provides zero-copy buffer functionality for efficient data transfer
between sub-interpreters in the Week 5 multicore parallelization system.

Key Features:
- Zero-copy data transfer between sub-interpreters
- Memory-efficient buffer views and operations
- Integration with shared memory management
- Thread-safe buffer operations
- Support for various data types and serialization formats

Author: Epochly Development Team
"""

import time
import threading
import weakref
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
import pickle

from ...utils.exceptions import EpochlyError


class TransferError(EpochlyError):
    """Exception raised for data transfer related errors."""
    pass


class BufferError(EpochlyError):
    """Exception raised for buffer operation related errors."""
    pass


@dataclass
class BufferView:
    """
    A view into a zero-copy buffer for efficient data access.
    
    Provides a lightweight interface to access buffer data without copying.
    """
    buffer_id: str
    offset: int
    size: int
    data_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    _memory_view: Optional[memoryview] = None
    
    def __post_init__(self):
        """Initialize buffer view after creation."""
        self.created_time = time.time()
        self.access_count = 0
    
    def get_memory_view(self) -> memoryview:
        """
        Get the underlying memory view.
        
        Returns:
            Memory view of the buffer data
            
        Raises:
            BufferError: If memory view is not available
        """
        if self._memory_view is None:
            raise BufferError(f"Memory view not available for buffer {self.buffer_id}")
        
        self.access_count += 1
        return self._memory_view
    
    def set_memory_view(self, memory_view: memoryview) -> None:
        """
        Set the underlying memory view.
        
        Args:
            memory_view: Memory view to associate with this buffer view
        """
        self._memory_view = memory_view
    
    def is_valid(self) -> bool:
        """Check if the buffer view is valid and accessible."""
        return self._memory_view is not None and self.size > 0


class ZeroCopyBuffer:
    """
    Zero-copy buffer for efficient data transfer between sub-interpreters.
    
    Provides high-performance data sharing without memory copying overhead.
    """
    
    def __init__(self, buffer_id: str, size: int, data_type: str = "bytes"):
        """
        Initialize zero-copy buffer.
        
        Args:
            buffer_id: Unique identifier for this buffer
            size: Size of the buffer in bytes
            data_type: Type of data stored in buffer
        """
        self.buffer_id = buffer_id
        self.size = size
        self.data_type = data_type
        self.created_time = time.time()
        self.last_accessed = time.time()
        self.access_count = 0
        self.ref_count = 1
        
        # Buffer state
        self._is_allocated = False
        self._is_mapped = False
        self._memory_view: Optional[memoryview] = None
        self._memory_block: Optional[Any] = None  # Reference to SharedMemoryManager block
        self._shared_memory_manager: Optional[Any] = None  # Reference to SharedMemoryManager
        self._lock = threading.RLock()
        
        # Metadata and views
        self.metadata: Dict[str, Any] = {}
        self._views: Dict[str, BufferView] = {}
        
        # Weak reference tracking for cleanup
        self._finalizer = weakref.finalize(self, self._cleanup_buffer)
    
    def allocate(self, shared_memory_manager=None) -> None:
        """
        Allocate the buffer in shared memory.

        Args:
            shared_memory_manager: Optional manager for shared memory operations.
                                 If not provided, creates its own manager.

        Raises:
            BufferError: If allocation fails
        """
        with self._lock:
            if self._is_allocated:
                return

            try:
                # CRITICAL FIX (Jan 2026): Skip SharedMemoryManager on Python 3.13 macOS
                # SharedMemory uses multiprocessing.resource_tracker which has known deadlock
                # issues on Python 3.13 macOS.
                import sys
                is_python313_macos = sys.version_info[:2] == (3, 13) and sys.platform == 'darwin'
                if is_python313_macos and shared_memory_manager is None:
                    raise BufferError(
                        "ZeroCopyBuffer unavailable on Python 3.13 macOS "
                        "(SharedMemory resource_tracker deadlock issues)"
                    )

                # Integrate with SharedMemoryManager for real zero-copy allocation
                if shared_memory_manager is not None:
                    self._shared_memory_manager = shared_memory_manager
                elif self._shared_memory_manager is None:
                    # Import here to avoid circular imports
                    from .shared_memory_manager import SharedMemoryManager
                    self._shared_memory_manager = SharedMemoryManager()
                
                # Allocate a memory block from shared memory
                self._memory_block = self._shared_memory_manager.allocate_block(
                    self.size, 
                    block_type="zero_copy_buffer"
                )
                
                if self._memory_block is None:
                    raise BufferError("Failed to allocate memory block from shared memory")
                
                # Get the actual memory view from shared memory
                if self._shared_memory_manager._shared_memory:
                    offset = self._memory_block.offset
                    self._memory_view = memoryview(
                        self._shared_memory_manager._shared_memory.buf
                    )[offset:offset + self.size]
                    self._is_allocated = True
                    self._is_mapped = True
                else:
                    raise BufferError("Shared memory not initialized")
                
            except Exception as e:
                raise BufferError(f"Failed to allocate buffer {self.buffer_id}: {e}")
    
    def deallocate(self) -> None:
        """
        Deallocate the buffer from shared memory.
        
        Raises:
            BufferError: If deallocation fails
        """
        with self._lock:
            if not self._is_allocated:
                return
            
            try:
                # Release all views first
                self.release_views()
                
                # Clear all views
                for view in self._views.values():
                    view._memory_view = None
                self._views.clear()
                
                # Deallocate from shared memory manager
                if self._memory_block and self._shared_memory_manager:
                    self._shared_memory_manager.deallocate_block(self._memory_block.block_id)
                    self._memory_block = None
                
                # Clear memory view
                self._memory_view = None
                self._is_allocated = False
                self._is_mapped = False
                self._shared_memory_manager = None
                
            except Exception as e:
                raise BufferError(f"Failed to deallocate buffer {self.buffer_id}: {e}")
    
    def create_view(self, view_id: str, offset: int = 0, size: Optional[int] = None) -> BufferView:
        """
        Create a view into the buffer.
        
        Args:
            view_id: Unique identifier for the view
            offset: Offset into the buffer
            size: Size of the view (defaults to remaining buffer size)
            
        Returns:
            Buffer view object
            
        Raises:
            BufferError: If view creation fails
        """
        with self._lock:
            if not self._is_allocated:
                raise BufferError(f"Buffer {self.buffer_id} is not allocated")
            
            if offset < 0 or offset >= self.size:
                raise BufferError(f"Invalid offset {offset} for buffer size {self.size}")
            
            if size is None:
                size = self.size - offset
            
            if offset + size > self.size:
                raise BufferError(f"View extends beyond buffer: {offset + size} > {self.size}")
            
            # Create the view
            view = BufferView(
                buffer_id=self.buffer_id,
                offset=offset,
                size=size,
                data_type=self.data_type,
                metadata={"parent_buffer": self.buffer_id}
            )
            
            # Set memory view if available
            if self._memory_view:
                view.set_memory_view(self._memory_view[offset:offset + size])
            
            self._views[view_id] = view
            return view
    
    def get_view(self, view_id: str) -> Optional[BufferView]:
        """
        Get an existing view by ID.
        
        Args:
            view_id: ID of the view to retrieve
            
        Returns:
            Buffer view if found, None otherwise
        """
        with self._lock:
            return self._views.get(view_id)
    
    def remove_view(self, view_id: str) -> None:
        """
        Remove a view from the buffer.
        
        Args:
            view_id: ID of the view to remove
        """
        with self._lock:
            if view_id in self._views:
                view = self._views[view_id]
                view._memory_view = None
                del self._views[view_id]
    
    def release_views(self) -> None:
        """
        Release all memory views to allow cleanup without warnings.
        """
        with self._lock:
            # Release all created views
            for view in self._views.values():
                if view._memory_view is not None:
                    try:
                        view._memory_view.release()
                    except:
                        pass
                    view._memory_view = None
            
            # Release the main memory view
            if self._memory_view is not None:
                try:
                    self._memory_view.release()
                except:
                    pass
                self._memory_view = None
    
    def write(self, data: bytes, offset: int = 0) -> None:
        """
        Write data to the buffer (alias for write_data).
        
        Args:
            data: Data to write
            offset: Offset in buffer to start writing
            
        Raises:
            BufferError: If write operation fails
        """
        self.write_data(data, offset)
    
    def write_data(self, data: bytes, offset: int = 0) -> None:
        """
        Write data to the buffer.
        
        Args:
            data: Data to write
            offset: Offset in buffer to start writing
            
        Raises:
            BufferError: If write operation fails
        """
        with self._lock:
            if not self._is_allocated or not self._memory_view:
                raise BufferError(f"Buffer {self.buffer_id} is not allocated")
            
            if offset + len(data) > self.size:
                raise BufferError(f"Data too large for buffer: {len(data)} bytes at offset {offset}")
            
            try:
                self._memory_view[offset:offset + len(data)] = data
                self.last_accessed = time.time()
                self.access_count += 1
                
            except Exception as e:
                raise BufferError(f"Failed to write data to buffer {self.buffer_id}: {e}")
    
    def read(self, offset: int = 0, size: Optional[int] = None) -> bytes:
        """
        Read data from the buffer (alias for read_data).
        
        Args:
            offset: Offset in buffer to start reading
            size: Number of bytes to read (defaults to remaining buffer size)
            
        Returns:
            Data read from buffer
            
        Raises:
            BufferError: If read operation fails
        """
        return self.read_data(offset, size)
    
    def read_data(self, offset: int = 0, size: Optional[int] = None) -> bytes:
        """
        Read data from the buffer.
        
        Args:
            offset: Offset in buffer to start reading
            size: Number of bytes to read (defaults to remaining buffer size)
            
        Returns:
            Data read from buffer
            
        Raises:
            BufferError: If read operation fails
        """
        with self._lock:
            if not self._is_allocated or not self._memory_view:
                raise BufferError(f"Buffer {self.buffer_id} is not allocated")
            
            if size is None:
                size = self.size - offset
            
            if offset + size > self.size:
                raise BufferError(f"Read extends beyond buffer: {offset + size} > {self.size}")
            
            try:
                data = bytes(self._memory_view[offset:offset + size])
                self.last_accessed = time.time()
                self.access_count += 1
                return data
                
            except Exception as e:
                raise BufferError(f"Failed to read data from buffer {self.buffer_id}: {e}")
    
    def get_memory_view(self) -> memoryview:
        """
        Get the underlying memory view.
        
        Returns:
            Memory view of the entire buffer
            
        Raises:
            BufferError: If buffer is not allocated
        """
        with self._lock:
            if not self._is_allocated or not self._memory_view:
                raise BufferError(f"Buffer {self.buffer_id} is not allocated")
            
            self.last_accessed = time.time()
            self.access_count += 1
            return self._memory_view
    
    def serialize_object(self, obj: Any, offset: int = 0) -> int:
        """
        Serialize an object into the buffer.
        
        Args:
            obj: Object to serialize
            offset: Offset in buffer to start writing
            
        Returns:
            Number of bytes written
            
        Raises:
            BufferError: If serialization fails
        """
        try:
            serialized_data = pickle.dumps(obj)
            self.write_data(serialized_data, offset)
            return len(serialized_data)
            
        except Exception as e:
            raise BufferError(f"Failed to serialize object to buffer {self.buffer_id}: {e}")
    
    def deserialize_object(self, offset: int = 0, size: Optional[int] = None) -> Any:
        """
        Deserialize an object from the buffer.
        
        Args:
            offset: Offset in buffer to start reading
            size: Number of bytes to read (defaults to remaining buffer size)
            
        Returns:
            Deserialized object
            
        Raises:
            BufferError: If deserialization fails
        """
        try:
            data = self.read_data(offset, size)
            return pickle.loads(data)
            
        except Exception as e:
            raise BufferError(f"Failed to deserialize object from buffer {self.buffer_id}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get buffer statistics.

        Returns:
            Dictionary containing buffer statistics
        """
        with self._lock:
            return {
                "buffer_id": self.buffer_id,
                "size": self.size,
                "data_type": self.data_type,
                "is_allocated": self._is_allocated,
                "is_mapped": self._is_mapped,
                "ref_count": self.ref_count,
                "access_count": self.access_count,
                "view_count": len(self._views),
                "created_time": self.created_time,
                "last_accessed": self.last_accessed,
                "uptime": time.time() - self.created_time,
                "metadata": self.metadata.copy()
            }
    
    def add_reference(self) -> None:
        """Add a reference to this buffer."""
        with self._lock:
            self.ref_count += 1
    
    def remove_reference(self) -> None:
        """Remove a reference from this buffer."""
        with self._lock:
            self.ref_count = max(0, self.ref_count - 1)
    
    @staticmethod
    def _cleanup_buffer():
        """Static cleanup method for finalizer."""
        # This would perform any necessary cleanup
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.deallocate()
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.deallocate()
        except:
            pass  # Ignore errors during cleanup