"""
Epochly Memory Foundation - mmap-based Memory Pool Implementation

This module provides a memory pool implementation using mmap for deterministic
memory management and zero RSS growth. Based on state-of-the-art allocator
techniques from jemalloc, tcmalloc, and mimalloc.

Key features:
- Direct mmap allocation for large buffers
- madvise(MADV_DONTNEED) for immediate page reclamation
- malloc_trim() integration for arena cleanup
- Per-bucket decay timers for automatic cleanup

Author: Epochly Memory Foundation Team
Created: 2025-07-24
"""

import mmap
import ctypes
import logging
import threading
import time
import sys
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

from .platform_utils import create_anonymous_mmap

logger = logging.getLogger(__name__)


class MmapMemoryPool:
    """
    Memory pool implementation using mmap for deterministic memory management.
    
    This implementation addresses RSS growth issues by using direct mmap
    allocation and madvise for immediate page reclamation, following
    best practices from modern allocators.
    """
    
    def __init__(self, size: int, name: str = "MmapMemoryPool"):
        """
        Initialize mmap-based memory pool.
        
        Args:
            size: Size of memory pool in bytes
            name: Name for logging
        """
        self.size = size
        self.name = name
        self._lock = threading.Lock()
        
        # Create anonymous memory mapping (cross-platform)
        self._fd = -1  # Anonymous mapping
        self._mmap = create_anonymous_mmap(size)
        
        # Track allocations
        self._allocations: Dict[int, int] = {}  # offset -> size
        self._free_blocks: List[tuple[int, int]] = [(0, size)]  # (offset, size)

        # Load libc for madvise and malloc_trim
        try:
            if sys.platform == 'win32':
                # Windows: use msvcrt (ctypes.CDLL(None) fails on Windows Python 3.13+)
                self._libc = ctypes.CDLL('msvcrt')
            else:
                # Unix: None loads libc automatically
                self._libc = ctypes.CDLL(None)
        except Exception:
            self._libc = None
        
        # Define madvise constants (Linux)
        self.MADV_DONTNEED = 4
        self.MADV_FREE = 8  # Linux 4.5+
        
        logger.info(f"Created {name} with {size} bytes using mmap")
    
    def allocate(self, size: int, alignment: int = 8) -> Optional[int]:
        """
        Allocate memory from the pool.
        
        Args:
            size: Size to allocate
            alignment: Alignment requirement
            
        Returns:
            Offset of allocated memory or None if failed
        """
        with self._lock:
            # Find first-fit free block
            for i, (offset, block_size) in enumerate(self._free_blocks):
                # Calculate aligned offset
                aligned_offset = (offset + alignment - 1) & ~(alignment - 1)
                padding = aligned_offset - offset
                
                if aligned_offset + size <= offset + block_size:
                    # Remove this free block
                    self._free_blocks.pop(i)
                    
                    # Add padding back if any
                    if padding > 0:
                        self._free_blocks.append((offset, padding))
                    
                    # Add remainder if any
                    remainder = (offset + block_size) - (aligned_offset + size)
                    if remainder > 0:
                        self._free_blocks.append((aligned_offset + size, remainder))
                    
                    # Track allocation
                    self._allocations[aligned_offset] = size
                    
                    return aligned_offset
            
            return None
    
    def deallocate(self, offset: int) -> None:
        """
        Deallocate memory and immediately release pages to OS.
        
        Args:
            offset: Offset to deallocate
        """
        with self._lock:
            if offset not in self._allocations:
                raise ValueError(f"Invalid offset: {offset}")
            
            size = self._allocations.pop(offset)
            
            # Add back to free list
            self._free_blocks.append((offset, size))
            
            # Immediately advise kernel to release these pages
            self._madvise_dontneed(offset, size)
            
            # Coalesce adjacent free blocks
            self._coalesce_free_blocks()
    
    def _madvise_dontneed(self, offset: int, size: int) -> None:
        """
        Use madvise to tell kernel these pages can be reclaimed.
        
        Args:
            offset: Starting offset
            size: Size of region
        """
        try:
            # Get memory address
            addr = ctypes.c_void_p.from_buffer(self._mmap, offset)
            
            # Call madvise
            result = self._libc.madvise(
                ctypes.c_void_p(addr.value),
                ctypes.c_size_t(size),
                ctypes.c_int(self.MADV_DONTNEED)
            )
            
            if result != 0:
                logger.warning(f"madvise failed with result {result}")
            else:
                logger.debug(f"Released {size} bytes at offset {offset} to OS")
                
        except Exception as e:
            logger.error(f"Error in madvise: {e}")
    
    def _coalesce_free_blocks(self) -> None:
        """Coalesce adjacent free blocks to reduce fragmentation."""
        if len(self._free_blocks) <= 1:
            return
        
        # Sort by offset
        self._free_blocks.sort(key=lambda x: x[0])
        
        # Merge adjacent blocks
        merged = []
        current_offset, current_size = self._free_blocks[0]
        
        for offset, size in self._free_blocks[1:]:
            if current_offset + current_size == offset:
                # Adjacent - merge
                current_size += size
            else:
                # Not adjacent - save current and start new
                merged.append((current_offset, current_size))
                current_offset, current_size = offset, size
        
        merged.append((current_offset, current_size))
        self._free_blocks = merged
    
    def memory_view(self, offset: int, size: int) -> memoryview:
        """Get a memory view for the specified region."""
        if offset < 0 or offset + size > self.size:
            raise ValueError(f"Invalid offset/size: {offset}/{size}")
        
        return memoryview(self._mmap)[offset:offset + size]
    
    def collect(self) -> None:
        """
        Force memory collection similar to modern allocators.
        
        This implements the decay/purge behavior of jemalloc/mimalloc.
        """
        with self._lock:
            # Advise on all free blocks
            for offset, size in self._free_blocks:
                self._madvise_dontneed(offset, size)
            
            # Call malloc_trim to release arenas
            try:
                self._libc.malloc_trim(ctypes.c_int(0))
                logger.debug("Called malloc_trim to release memory")
            except Exception as e:
                logger.warning(f"malloc_trim failed: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            total_free = sum(size for _, size in self._free_blocks)
            fragmentation = len(self._free_blocks) - 1 if self._free_blocks else 0
            
            return {
                "total_size": self.size,
                "allocated": self.size - total_free,
                "free": total_free,
                "allocations": len(self._allocations),
                "free_blocks": len(self._free_blocks),
                "fragmentation": fragmentation,
                "largest_free_block": max((s for _, s in self._free_blocks), default=0)
            }
    
    def cleanup(self) -> None:
        """Clean up mmap and release all resources."""
        try:
            # Close mmap
            if hasattr(self, '_mmap') and self._mmap:
                self._mmap.close()
                self._mmap = None
            
            # Clear tracking
            self._allocations.clear()
            self._free_blocks.clear()
            
            logger.info(f"Cleaned up {self.name}")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Ensure cleanup on deletion."""
        self.cleanup()


@dataclass
class DecayConfig:
    """Configuration for memory decay (similar to jemalloc)."""
    decay_time_ms: int = 10000  # Time before decay starts
    decay_interval_ms: int = 1000  # How often to check for decay
    min_free_size: int = 65536  # Minimum size to decay


class DecayingMemoryPool(MmapMemoryPool):
    """
    Memory pool with automatic decay of unused pages.
    
    This implements jemalloc-style decay where free pages are
    automatically returned to the OS after a timeout.
    """
    
    def __init__(self, size: int, name: str = "DecayingMemoryPool", 
                 decay_config: Optional[DecayConfig] = None):
        """Initialize with decay support."""
        super().__init__(size, name)
        
        self.decay_config = decay_config or DecayConfig()
        self._free_timestamps: Dict[int, float] = {}  # offset -> timestamp
        self._decay_thread = None
        self._stop_decay = threading.Event()
        
        # Start decay thread
        self._start_decay_thread()
    
    def deallocate(self, offset: int) -> None:
        """Deallocate and mark for decay."""
        super().deallocate(offset)
        
        # Mark timestamp for decay
        with self._lock:
            self._free_timestamps[offset] = time.time()
    
    def _start_decay_thread(self) -> None:
        """Start background decay thread."""
        def decay_worker():
            while not self._stop_decay.is_set():
                try:
                    self._decay_free_blocks()
                except Exception as e:
                    logger.error(f"Error in decay thread: {e}")
                
                # Sleep for decay interval
                self._stop_decay.wait(self.decay_config.decay_interval_ms / 1000.0)
        
        self._decay_thread = threading.Thread(target=decay_worker, daemon=True)
        self._decay_thread.start()
        logger.debug("Started decay thread")
    
    def _decay_free_blocks(self) -> None:
        """Decay old free blocks."""
        now = time.time()
        decay_threshold = now - (self.decay_config.decay_time_ms / 1000.0)
        
        with self._lock:
            for offset, size in list(self._free_blocks):
                # Check if this block is old enough to decay
                if offset in self._free_timestamps:
                    if self._free_timestamps[offset] < decay_threshold:
                        if size >= self.decay_config.min_free_size:
                            # Decay this block
                            self._madvise_dontneed(offset, size)
                            del self._free_timestamps[offset]
                            logger.debug(f"Decayed {size} bytes at offset {offset}")
    
    def cleanup(self) -> None:
        """Stop decay thread and cleanup."""
        # Stop decay thread
        if self._decay_thread:
            self._stop_decay.set()
            self._decay_thread.join(timeout=1.0)
        
        # Call parent cleanup
        super().cleanup()