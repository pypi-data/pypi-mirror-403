"""
GPU Memory Manager

This module manages GPU memory allocation, deallocation, and caching
for efficient GPU operations with proper memory pressure handling.

Author: Epochly Development Team
"""

import logging
import threading
import time
from typing import Dict, Optional, Set
from dataclasses import dataclass
from collections import defaultdict, OrderedDict
from enum import Enum



class MemoryStrategy(Enum):
    """Memory management strategies."""
    AGGRESSIVE_CACHE = "aggressive_cache"
    CONSERVATIVE_CACHE = "conservative_cache"
    NO_CACHE = "no_cache"
    ADAPTIVE = "adaptive"


@dataclass
class MemoryBlock:
    """Represents a GPU memory block."""
    ptr: int
    size: int
    allocated_time: float
    last_used: float
    ref_count: int = 0
    pinned: bool = False
    # Store the CuPy MemoryPointer to keep the allocation alive
    # Without this, the memory would be freed when memptr goes out of scope
    memptr: object = None  # cupy.cuda.MemoryPointer or similar


@dataclass
class MemoryStats:
    """GPU memory usage statistics."""
    allocated_bytes: int
    cached_bytes: int
    free_bytes: int
    total_bytes: int
    fragmentation_ratio: float
    allocation_count: int
    cache_hits: int
    cache_misses: int


class GPUMemoryManager:
    """
    Manages GPU memory allocation with caching and pressure handling.
    
    This class provides:
    - Memory pool management
    - Caching of frequently used arrays
    - Memory pressure detection and cleanup
    - Fragmentation monitoring
    - Pinned memory support for fast transfers
    """
    
    def __init__(self, memory_limit: int, enable_caching: bool = True):
        """
        Initialize GPU memory manager.
        
        Args:
            memory_limit: Maximum GPU memory to use in bytes
            enable_caching: Whether to enable memory caching
        """
        self._memory_limit = memory_limit
        self._enable_caching = enable_caching
        self._logger = logging.getLogger(__name__)
        
        # Memory tracking
        self._allocated_blocks: Dict[int, MemoryBlock] = {}
        self._cached_blocks: OrderedDict[int, MemoryBlock] = OrderedDict()
        self._free_blocks: Dict[int, Set[int]] = defaultdict(set)  # size -> set of ptrs
        
        # Statistics
        self._stats = MemoryStats(
            allocated_bytes=0,
            cached_bytes=0,
            free_bytes=memory_limit,
            total_bytes=memory_limit,
            fragmentation_ratio=0.0,
            allocation_count=0,
            cache_hits=0,
            cache_misses=0
        )
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Configuration
        self._config = {
            'cache_size_ratio': 0.3,        # Use 30% of memory for cache
            'cleanup_threshold': 0.9,       # Cleanup when 90% full
            'fragmentation_threshold': 0.3,  # Defrag when 30% fragmented
            'block_size_alignment': 256,    # Align allocations to 256 bytes
            'max_cached_blocks': 1000,      # Maximum number of cached blocks
            'cache_timeout_hours': 2.0,     # Remove cached blocks after 2 hours
        }
        
        # Lazy CuPy integration - will be initialized when first needed
        self._cupy = None
        self._memory_pool = None
        self._cupy_initialized = False
        
        # Strategy
        self._strategy = MemoryStrategy.ADAPTIVE
        
        # Cleanup thread
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        self._start_cleanup_thread()
    
    def _ensure_cupy_integration(self) -> bool:
        """Ensure CuPy memory pool integration is initialized (lazy loading)."""
        if self._cupy_initialized:
            return self._cupy is not None

        try:
            import cupy as cp
            self._cupy = cp

            # Get the default memory pool
            if hasattr(cp, 'get_default_memory_pool'):
                self._memory_pool = cp.get_default_memory_pool()

                # Set memory limit
                self._memory_pool.set_limit(size=self._memory_limit)

                self._logger.info(f"CuPy memory pool initialized with {self._memory_limit // (1024**3)}GB limit")

            self._cupy_initialized = True
            return True

        except ImportError:
            self._logger.debug("CuPy not available for memory pool integration")
            self._cupy_initialized = True
            return False
        except Exception as e:
            self._logger.warning(f"CuPy memory pool initialization failed: {e}")
            self._cupy_initialized = True
            return False
    
    def allocate(self, size: int, align_to: Optional[int] = None) -> Optional[int]:
        """
        Allocate GPU memory block.

        Args:
            size: Size in bytes to allocate
            align_to: Alignment requirement (defaults to config alignment)

        Returns:
            Pointer to allocated memory or None if allocation failed
        """
        # Ensure CuPy integration is initialized (lazy loading)
        if not self._cupy_initialized:
            cupy_available = self._ensure_cupy_integration()
            if not cupy_available:
                self._logger.error("Cannot allocate GPU memory: CuPy not available")
                return None

        if align_to is None:
            align_to = self._config['block_size_alignment']

        # Align size
        aligned_size = ((size + align_to - 1) // align_to) * align_to

        with self._lock:
            # Check if we have room for this allocation
            if self._stats.allocated_bytes + aligned_size > self._memory_limit:
                # Try cleanup first
                self._cleanup_if_needed()
                
                # Check again after cleanup
                if self._stats.allocated_bytes + aligned_size > self._memory_limit:
                    self._logger.warning(f"GPU memory allocation failed: need {aligned_size // (1024**2)}MB, "
                                       f"have {(self._memory_limit - self._stats.allocated_bytes) // (1024**2)}MB")
                    return None
            
            # Try to find a cached block first
            if self._enable_caching:
                cached_ptr = self._find_cached_block(aligned_size)
                if cached_ptr:
                    return cached_ptr
            
            # Allocate new block
            try:
                if self._memory_pool:
                    # Use CuPy memory pool
                    memptr = self._memory_pool.malloc(aligned_size)
                    ptr = memptr.ptr
                else:
                    # GPU memory pool not initialized - this indicates a bug
                    # Raise error instead of using dangerous placeholder
                    raise RuntimeError(
                        "GPU memory pool not initialized. "
                        "GPUMemoryManager must be initialized with working CuPy before allocating memory. "
                        "Use GPUDetector to verify GPU availability before creating GPUMemoryManager."
                    )

                # Track the allocation - store memptr to keep allocation alive!
                # P0 FIX (mcp-reflect): Without storing memptr, the CuPy MemoryPointer
                # would be freed immediately when memptr goes out of scope, causing
                # use-after-free issues.
                block = MemoryBlock(
                    ptr=ptr,
                    size=aligned_size,
                    allocated_time=time.time(),
                    last_used=time.time(),
                    memptr=memptr  # Keep allocation alive
                )
                
                self._allocated_blocks[ptr] = block
                self._stats.allocated_bytes += aligned_size
                self._stats.free_bytes -= aligned_size
                self._stats.allocation_count += 1
                
                self._logger.debug(f"Allocated {aligned_size // 1024}KB GPU memory at {hex(ptr)}")
                
                return ptr
                
            except Exception as e:
                self._logger.error(f"GPU memory allocation failed: {e}")
                return None
    
    def deallocate(self, ptr: int) -> bool:
        """
        Deallocate GPU memory block.
        
        Args:
            ptr: Pointer to memory block
            
        Returns:
            True if deallocation successful
        """
        with self._lock:
            if ptr not in self._allocated_blocks:
                self._logger.warning(f"Attempted to deallocate unknown pointer {hex(ptr)}")
                return False
            
            block = self._allocated_blocks[ptr]
            
            # Check if block should be cached
            if self._should_cache_block(block):
                return self._move_to_cache(ptr)
            else:
                return self._free_block(ptr)
    
    def ensure_memory_available(self, required_size: int) -> bool:
        """
        Ensure sufficient GPU memory is available for allocation.
        
        Args:
            required_size: Required memory size in bytes
            
        Returns:
            True if sufficient memory is available
        """
        with self._lock:
            available = self._memory_limit - self._stats.allocated_bytes
            
            if available >= required_size:
                return True
            
            # Try cleanup
            self._cleanup_if_needed()
            
            # Check again
            available = self._memory_limit - self._stats.allocated_bytes
            return available >= required_size
    
    def _find_cached_block(self, size: int) -> Optional[int]:
        """Find a cached block of sufficient size."""
        # Look for exact size match first
        for ptr, block in self._cached_blocks.items():
            if block.size == size:
                # Move from cache to allocated
                del self._cached_blocks[ptr]
                self._allocated_blocks[ptr] = block
                
                self._stats.cached_bytes -= block.size
                self._stats.allocated_bytes += block.size
                self._stats.cache_hits += 1
                
                block.last_used = time.time()
                block.ref_count += 1
                
                self._logger.debug(f"Cache hit: reusing {size // 1024}KB block at {hex(ptr)}")
                return ptr
        
        # Look for larger block that can be split
        for ptr, block in self._cached_blocks.items():
            if block.size >= size and block.size <= size * 2:  # Don't waste too much space
                # Move from cache to allocated
                del self._cached_blocks[ptr]

                # P0 FIX (mcp-reflect): Subtract ORIGINAL size from cached_bytes,
                # not the new size. Previously this caused stats drift.
                original_size = block.size
                self._stats.cached_bytes -= original_size

                # Resize the block (conceptually - actual memory stays the same)
                block.size = size  # Use only what we need
                self._allocated_blocks[ptr] = block

                self._stats.allocated_bytes += block.size
                self._stats.cache_hits += 1

                block.last_used = time.time()
                block.ref_count += 1

                self._logger.debug(f"Cache hit: reusing larger block {original_size // 1024}KB for {size // 1024}KB")
                return ptr
        
        # No suitable cached block found
        self._stats.cache_misses += 1
        return None
    
    def _should_cache_block(self, block: MemoryBlock) -> bool:
        """Determine if a block should be cached rather than freed."""
        if not self._enable_caching:
            return False
        
        # Don't cache if we're near memory limit
        cache_usage = self._stats.cached_bytes / self._memory_limit
        if cache_usage > self._config['cache_size_ratio']:
            return False
        
        # Don't cache very large blocks
        if block.size > self._memory_limit * 0.1:  # Larger than 10% of total memory
            return False
        
        # Don't cache if we have too many cached blocks
        if len(self._cached_blocks) >= self._config['max_cached_blocks']:
            return False
        
        # Cache blocks that were used recently or frequently
        age_hours = (time.time() - block.allocated_time) / 3600
        if age_hours < 1.0 or block.ref_count > 2:
            return True
        
        return False
    
    def _move_to_cache(self, ptr: int) -> bool:
        """Move an allocated block to cache."""
        if ptr not in self._allocated_blocks:
            return False
        
        block = self._allocated_blocks[ptr]
        del self._allocated_blocks[ptr]
        
        # Add to cache (most recently used at end)
        self._cached_blocks[ptr] = block
        
        # Update statistics
        self._stats.allocated_bytes -= block.size
        self._stats.cached_bytes += block.size
        
        self._logger.debug(f"Cached {block.size // 1024}KB block at {hex(ptr)}")
        return True
    
    def _free_block(self, ptr: int) -> bool:
        """Actually free a memory block."""
        if ptr not in self._allocated_blocks:
            return False
        
        block = self._allocated_blocks[ptr]
        del self._allocated_blocks[ptr]
        
        try:
            # Free through CuPy if available
            if self._memory_pool:
                # CuPy handles the actual deallocation
                pass
            
            # Update statistics
            self._stats.allocated_bytes -= block.size
            self._stats.free_bytes += block.size
            
            self._logger.debug(f"Freed {block.size // 1024}KB GPU memory at {hex(ptr)}")
            return True
            
        except Exception as e:
            self._logger.error(f"GPU memory deallocation failed: {e}")
            return False
    
    def _cleanup_if_needed(self) -> None:
        """Perform cleanup if memory usage is high."""
        usage_ratio = self._stats.allocated_bytes / self._memory_limit
        
        if usage_ratio > self._config['cleanup_threshold']:
            self._logger.info(f"GPU memory usage {usage_ratio:.1%} exceeds threshold, performing cleanup")
            self._cleanup_cache()
    
    def _cleanup_cache(self) -> None:
        """Clean up cached memory blocks."""
        current_time = time.time()
        timeout_seconds = self._config['cache_timeout_hours'] * 3600
        
        # Remove old cached blocks
        expired_ptrs = []
        for ptr, block in self._cached_blocks.items():
            if (current_time - block.last_used) > timeout_seconds:
                expired_ptrs.append(ptr)
        
        for ptr in expired_ptrs:
            block = self._cached_blocks[ptr]
            del self._cached_blocks[ptr]
            self._free_block_memory(ptr, block.size)
            self._stats.cached_bytes -= block.size
            self._stats.free_bytes += block.size
        
        if expired_ptrs:
            self._logger.info(f"Cleaned up {len(expired_ptrs)} expired cached blocks")
        
        # If still under pressure, remove least recently used blocks
        while (self._stats.cached_bytes > self._memory_limit * self._config['cache_size_ratio'] * 0.5 
               and self._cached_blocks):
            # Remove oldest cached block (first in OrderedDict)
            ptr, block = self._cached_blocks.popitem(last=False)
            self._free_block_memory(ptr, block.size)
            self._stats.cached_bytes -= block.size
            self._stats.free_bytes += block.size
    
    def _free_block_memory(self, ptr: int, size: int) -> None:
        """Actually free the memory for a block."""
        try:
            if self._memory_pool:
                # CuPy memory pool handles this automatically
                pass
        except Exception as e:
            self._logger.error(f"Error freeing memory block {hex(ptr)}: {e}")
    
    def get_stats(self) -> MemoryStats:
        """Get current memory statistics."""
        with self._lock:
            # Update fragmentation ratio
            if self._stats.total_bytes > 0:
                used_ratio = self._stats.allocated_bytes / self._stats.total_bytes
                # Simple fragmentation estimate
                self._stats.fragmentation_ratio = max(0, min(1, used_ratio * (len(self._allocated_blocks) / 100)))
            
            return MemoryStats(
                allocated_bytes=self._stats.allocated_bytes,
                cached_bytes=self._stats.cached_bytes,
                free_bytes=self._stats.free_bytes,
                total_bytes=self._stats.total_bytes,
                fragmentation_ratio=self._stats.fragmentation_ratio,
                allocation_count=self._stats.allocation_count,
                cache_hits=self._stats.cache_hits,
                cache_misses=self._stats.cache_misses
            )
    
    def get_memory_pressure(self) -> float:
        """
        Get current memory pressure (0.0 = no pressure, 1.0 = full).
        
        Returns:
            Memory pressure ratio
        """
        with self._lock:
            total_used = self._stats.allocated_bytes + self._stats.cached_bytes
            return total_used / self._memory_limit
    
    def cleanup(self) -> None:
        """Cleanup all memory and stop background threads."""
        # Stop cleanup thread
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=5.0)
        
        with self._lock:
            # Free all cached blocks
            for ptr, block in self._cached_blocks.items():
                self._free_block_memory(ptr, block.size)
            self._cached_blocks.clear()
            
            # Clear allocated blocks tracking (actual memory freed by CuPy)
            self._allocated_blocks.clear()
            
            # Reset statistics
            self._stats.allocated_bytes = 0
            self._stats.cached_bytes = 0
            self._stats.free_bytes = self._memory_limit
        
        if self._memory_pool:
            try:
                self._memory_pool.free_all_blocks()
            except:
                pass
        
        self._logger.info("GPU memory manager cleanup completed")
    
    def _start_cleanup_thread(self) -> None:
        """Start background cleanup thread."""
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="Epochly-GPUMemoryCleanup"
        )
        self._cleanup_thread.start()
    
    def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while not self._stop_cleanup.wait(60.0):  # Check every minute
            try:
                pressure = self.get_memory_pressure()
                if pressure > 0.7:  # If memory pressure is high
                    with self._lock:
                        self._cleanup_cache()
            except Exception as e:
                self._logger.error(f"Error in cleanup loop: {e}")
    
    def force_cleanup(self) -> None:
        """Force immediate cleanup of cached blocks."""
        with self._lock:
            self._cleanup_cache()
    
    def set_strategy(self, strategy: MemoryStrategy) -> None:
        """Set memory management strategy."""
        self._strategy = strategy
        
        if strategy == MemoryStrategy.NO_CACHE:
            self._enable_caching = False
            self.force_cleanup()
        elif strategy == MemoryStrategy.AGGRESSIVE_CACHE:
            self._enable_caching = True
            self._config['cache_size_ratio'] = 0.5
        elif strategy == MemoryStrategy.CONSERVATIVE_CACHE:
            self._enable_caching = True
            self._config['cache_size_ratio'] = 0.2
        elif strategy == MemoryStrategy.ADAPTIVE:
            self._enable_caching = True
            self._config['cache_size_ratio'] = 0.3
        
        self._logger.info(f"Memory management strategy set to {strategy.value}")
    
    def _update_fragmentation_ratio(self) -> None:
        """Update fragmentation ratio estimate based on current allocations."""
        if self._stats.total_bytes > 0:
            used_ratio = self._stats.allocated_bytes / self._stats.total_bytes
            # Estimate fragmentation based on number of blocks vs memory used
            # More blocks = more fragmented (simplified heuristic)
            self._stats.fragmentation_ratio = max(0, min(1, used_ratio * (len(self._allocated_blocks) / 100)))

    def cleanup_if_needed(self) -> None:
        """Clean up GPU memory if usage is high."""
        with self._lock:
            # Check if cleanup is needed
            current_usage = self._stats.allocated_bytes + self._stats.cached_bytes
            if current_usage > self._memory_limit * self._config['cleanup_threshold']:
                self._logger.debug("GPU memory cleanup triggered")
                self._cleanup_cache()

                # P1 FIX (mcp-reflect): Update fragmentation ratio BEFORE checking
                # threshold, since it's only computed in get_stats() otherwise
                self._update_fragmentation_ratio()

                # Check fragmentation and defragment if needed
                if self._stats.fragmentation_ratio > self._config['fragmentation_threshold']:
                    self._defragment_memory()

    def _defragment_memory(self) -> None:
        """
        Defragment GPU memory by coalescing free blocks.

        This method consolidates fragmented free memory regions to reduce
        fragmentation and improve allocation efficiency for large blocks.

        Note: CuPy's memory pool handles most fragmentation internally,
        so this primarily manages our tracking structures and triggers
        CuPy's internal compaction when available.

        Thread-safe: Uses RLock which allows re-entrant locking.
        """
        # P1 FIX (mcp-reflect): Explicitly acquire lock for thread safety
        # even though caller may already hold it. RLock is re-entrant.
        with self._lock:
            if not self._memory_pool:
                return

            try:
                # CuPy memory pool handles compaction internally
                # We can trigger a free_all_blocks followed by re-allocation hints
                # However, this is aggressive - only do when fragmentation is severe

                if self._stats.fragmentation_ratio > 0.5:  # Severe fragmentation
                    self._logger.info(f"Defragmenting GPU memory (fragmentation: {self._stats.fragmentation_ratio:.1%})")

                    # Free all cached blocks to give memory pool room to compact
                    cached_sizes = []
                    for ptr, block in list(self._cached_blocks.items()):
                        cached_sizes.append(block.size)
                        self._free_block_memory(ptr, block.size)
                        self._stats.cached_bytes -= block.size
                        self._stats.free_bytes += block.size
                    self._cached_blocks.clear()

                    # Ask CuPy to compact if available
                    if hasattr(self._memory_pool, 'free_all_blocks'):
                        # This releases unused blocks back to CUDA
                        self._memory_pool.free_all_blocks()

                    # Update fragmentation estimate after cleanup
                    if self._stats.total_bytes > 0:
                        used_ratio = self._stats.allocated_bytes / self._stats.total_bytes
                        self._stats.fragmentation_ratio = max(0, min(1, used_ratio * (len(self._allocated_blocks) / 100)))

                    self._logger.info(f"Defragmentation complete (new fragmentation: {self._stats.fragmentation_ratio:.1%})")
                else:
                    # Mild fragmentation - just clean oldest cached blocks
                    cleanup_count = 0
                    while self._cached_blocks and cleanup_count < 10:
                        ptr, block = self._cached_blocks.popitem(last=False)
                        self._free_block_memory(ptr, block.size)
                        self._stats.cached_bytes -= block.size
                        self._stats.free_bytes += block.size
                        cleanup_count += 1

                    if cleanup_count > 0:
                        self._logger.debug(f"Mild defragmentation: freed {cleanup_count} cached blocks")

            except Exception as e:
                self._logger.warning(f"Memory defragmentation failed: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass