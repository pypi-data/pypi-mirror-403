"""
Fast Allocator Adapter (Task 2 Implementation)

Zero-overhead adapter to Cython fast allocator for Level 3 performance.

Performance Improvements:
- 2× throughput improvement (45k → >90k allocs/sec target)
- Eliminates Python-level locks in hot path
- Optional diagnostics (disabled by default)
- Pre-bound methods for fastest dispatch

Architecture:
    Level 3 User Code
        ↓
    FastAllocatorAdapter (this file - minimal overhead)
        ↓
    fast_allocator.pyx (Cython - nogil)
        ↓
    Slab allocator (C-level - lock-free)
"""

import os
from typing import Optional, Dict, Any

from ..utils.logger import get_logger

logger = get_logger(__name__)

def _is_diagnostics_enabled() -> bool:
    """Check if diagnostics are enabled (runtime check)."""
    return os.environ.get('EPOCHLY_MEMORY_DIAGNOSTICS', '0') == '1'


class FastAllocatorAdapter:
    """
    Zero-overhead adapter to Cython fast allocator.

    Uses __slots__ to prevent dict overhead and pre-binds methods
    for fastest possible dispatch.

    Performance:
        - <10μs per allocation (target)
        - >90k allocs/sec throughput (target)
        - Zero Python-level locks
        - Diagnostic overhead only when enabled

    Usage:
        adapter = FastAllocatorAdapter()
        handle = adapter.allocate(1024)
        adapter.deallocate(handle, 1024)

    Diagnostics:
        # Enable via environment variable
        export EPOCHLY_MEMORY_DIAGNOSTICS=1

        adapter = FastAllocatorAdapter()
        handle = adapter.allocate(1024)
        stats = adapter.get_stats()  # Returns diagnostic info
    """

    __slots__ = ('_allocate', '_deallocate', '_diagnostics', '_fast_pool', '_fallback_reason')

    def __init__(self):
        """
        Initialize adapter with pre-bound Cython methods.

        Diagnostic tracking is optional and disabled by default.
        """
        # Try to import Cython fast allocator (use FastMemoryPool API)
        try:
            from .fast_memory_pool import FastMemoryPool

            # Create singleton pool for allocations
            # Use 10MB pool for general allocations
            self._fast_pool = FastMemoryPool(total_size=10 * 1024 * 1024)

            # Pre-bind methods (avoid attribute lookup on every call)
            self._allocate = self._fast_pool.allocate
            self._deallocate = self._fast_pool.deallocate

            # Track that we're on fast path (Task 3 - perf_fixes2.md)
            self._fallback_reason = None

            logger.debug("FastAllocatorAdapter initialized with FastMemoryPool")

        except (ImportError, Exception) as e:
            logger.warning(f"FastMemoryPool unavailable: {e}")

            # Fall back to Python allocator (much slower but functional)
            self._allocate = self._allocate_fallback
            self._deallocate = self._deallocate_fallback
            self._fast_pool = None

            # Track fallback reason for health API (Task 3 - perf_fixes2.md)
            self._fallback_reason = f"FastMemoryPool import failed: {str(e)}"

            logger.warning("Using pure Python fallback allocator (slower)")

        # Optional diagnostics (disabled by default for performance)
        # Check at runtime to allow tests to enable via env var
        if _is_diagnostics_enabled():
            try:
                from ..monitoring.memory_diagnostics import MemoryDiagnostics
                self._diagnostics = MemoryDiagnostics()
                logger.info("Memory diagnostics enabled (adds overhead)")
            except ImportError:
                logger.warning("MemoryDiagnostics unavailable, diagnostics disabled")
                self._diagnostics = None
        else:
            self._diagnostics = None

    def allocate(self, size: int) -> int:
        """
        Allocate memory block.

        Args:
            size: Size in bytes to allocate

        Returns:
            Offset to allocated block

        Raises:
            ValueError: If size <= 0
            MemoryError: If allocation fails

        Performance:
            - <10μs target
            - No Python locks
            - Diagnostics optional (adds ~2μs when enabled)
        """
        # Validate size
        if size <= 0:
            raise ValueError(f"Invalid allocation size: {size}")

        if self._diagnostics:
            return self._diagnostics.track_allocation(self._allocate, size)

        # Fast path: call pool allocate
        block = self._allocate(size)

        if block is None:
            raise MemoryError(f"Could not allocate {size} bytes")

        # Return offset as handle (int)
        return block.offset if hasattr(block, 'offset') else block

    def deallocate(self, handle, size: int) -> None:
        """
        Deallocate memory block.

        Args:
            handle: Handle (int offset) or MemoryBlock returned from allocate()
            size: Size of block (for validation)

        Raises:
            ValueError: If handle/size invalid

        Performance:
            - <5μs target
            - No Python locks
        """
        # Extract offset from handle (supports both int and MemoryBlock)
        if isinstance(handle, int):
            offset = handle
        elif hasattr(handle, 'offset'):
            offset = handle.offset
        else:
            raise TypeError(f"Handle must be int or MemoryBlock, got {type(handle)}")

        # Validate offset
        if offset < 0:
            raise ValueError(f"Invalid offset: {offset}")

        if self._diagnostics:
            self._diagnostics.track_deallocation(offset, size)

        # Fast path: call pool deallocate
        # Note: MemoryPool.deallocate() expects just the block reference (offset)
        self._deallocate(offset)

    def cleanup(self) -> None:
        """
        Cleanup allocator resources.

        Should be called when allocator is no longer needed.
        """
        if self._fast_pool and hasattr(self._fast_pool, 'cleanup'):
            try:
                self._fast_pool.cleanup()
            except Exception as e:
                logger.warning(f"FastMemoryPool cleanup error: {e}")

        self._fast_pool = None

    def get_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get diagnostic statistics (only if enabled).

        Returns:
            Statistics dict if diagnostics enabled, None otherwise
        """
        if self._diagnostics:
            return self._diagnostics.get_stats()
        return None

    def get_shared_memory_stats(self) -> Dict[str, Any]:
        """
        Get SharedMemory usage statistics from underlying FastMemoryPool.

        This method enables SharedMemoryManager to retrieve zero-copy metrics
        for benchmark reporting.

        Returns:
            Dictionary with:
                - total_bytes_allocated: Total bytes allocated across all paths
                - shared_memory_bytes: Bytes allocated via zero-copy mechanisms
                - zero_copy_ratio: Ratio of zero-copy to total allocations
                - zero_copy_allocations: Count of zero-copy allocations
                - copy_allocations: Count of copy-based allocations
        """
        if self._fast_pool and hasattr(self._fast_pool, 'get_shared_memory_stats'):
            return self._fast_pool.get_shared_memory_stats()

        # Fallback if pool not available
        return {
            'total_bytes_allocated': 0,
            'shared_memory_bytes': 0,
            'zero_copy_ratio': 1.0,
            'zero_copy_allocations': 0,
            'copy_allocations': 0
        }

    # ========================================================================
    # Health API (Task 3 - perf_fixes2.md)
    # ========================================================================

    def is_fast_path(self) -> bool:
        """
        Check if Cython fast allocator is active.

        Returns:
            True if using Cython fast allocator, False if on Python fallback

        Example:
            >>> adapter = FastAllocatorAdapter()
            >>> if adapter.is_fast_path():
            ...     print("Using fast Cython allocator")
            ... else:
            ...     print(f"On fallback: {adapter.get_fallback_reason()}")
        """
        return self._fast_pool is not None

    def get_fallback_reason(self) -> Optional[str]:
        """
        Get reason for fallback to Python allocator.

        Returns:
            Human-readable reason string if on fallback, None if on fast path

        Example:
            >>> adapter = FastAllocatorAdapter()
            >>> if not adapter.is_fast_path():
            ...     print(f"Fallback reason: {adapter.get_fallback_reason()}")
        """
        return self._fallback_reason

    def get_health(self) -> 'AllocatorHealth':
        """
        Get comprehensive health snapshot of allocator.

        Returns:
            AllocatorHealth dataclass with current state

        Example:
            >>> adapter = FastAllocatorAdapter()
            >>> health = adapter.get_health()
            >>> if not health.is_healthy():
            ...     logger.warning(f"Allocator unhealthy: {health.fallback_reason}")
        """
        import time
        from .allocator_health import AllocatorHealth

        return AllocatorHealth(
            is_fast_path=self.is_fast_path(),
            fallback_reason=self.get_fallback_reason(),
            pool_name="FastMemoryPool" if self.is_fast_path() else "PythonFallbackPool",
            timestamp=time.time()
        )

    # ========================================================================
    # Fallback Implementation (Pure Python)
    # ========================================================================

    _fallback_pool = None
    _fallback_lock = None

    @classmethod
    def _get_fallback_pool(cls):
        """Get or create fallback pool for pure Python mode."""
        if cls._fallback_pool is None:
            import threading
            from .memory_pool import MemoryPool

            cls._fallback_lock = threading.RLock()
            # Create 10MB fallback pool
            cls._fallback_pool = MemoryPool(total_size=10 * 1024 * 1024)

        return cls._fallback_pool

    def _allocate_fallback(self, size: int) -> int:
        """Pure Python fallback allocator (slow)."""
        pool = self._get_fallback_pool()

        with self._fallback_lock:
            # Use MemoryPool for allocation
            block = pool.allocate(size)

            if block is None:
                raise MemoryError(f"Fallback allocator: Could not allocate {size} bytes")

            # Return offset as handle
            return block.offset if hasattr(block, 'offset') else block

    def _deallocate_fallback(self, handle: int) -> None:
        """Pure Python fallback deallocator."""
        pool = self._get_fallback_pool()

        with self._fallback_lock:
            # Use MemoryPool for deallocation (takes only handle/offset)
            pool.deallocate(handle)
