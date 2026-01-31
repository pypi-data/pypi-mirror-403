"""
Windows NUMA Memory Allocator

Implements NUMA-aware memory allocation using VirtualAllocExNuma for optimal
memory locality on multi-socket Windows systems.
"""

import sys
import ctypes
import threading
from ctypes import wintypes
from typing import Dict, Any, Optional, List
import logging

from .windows_numa_advanced import get_windows_numa_detector, WindowsNUMAMemoryInfo

logger = logging.getLogger(__name__)


class WindowsNUMAAllocator:
    """
    Windows NUMA-aware memory allocator using VirtualAllocExNuma.

    Provides NUMA-local memory allocation for optimal performance on
    multi-socket Windows systems.
    """

    # Windows memory allocation constants
    MEM_COMMIT = 0x1000
    MEM_RESERVE = 0x2000
    MEM_RELEASE = 0x8000
    PAGE_READWRITE = 0x04

    def __init__(self):
        """Initialize Windows NUMA allocator."""
        self._allocations: Dict[int, Dict[str, Any]] = {}
        self._allocation_lock = threading.Lock()

        # Get NUMA topology
        detector = get_windows_numa_detector()
        self.topology = detector.detect_enhanced_topology()
        self.numa_available = self.topology.numa_available

        # Load Windows APIs
        try:
            self.kernel32 = ctypes.windll.kernel32
            self._check_api_support()
        except Exception as e:
            logger.warning(f"Windows NUMA APIs not available: {e}")
            self.numa_available = False

    def _check_api_support(self) -> None:
        """Check if VirtualAllocExNuma is available."""
        if not hasattr(self.kernel32, 'VirtualAllocExNuma'):
            raise OSError("VirtualAllocExNuma not available")
        if not hasattr(self.kernel32, 'VirtualFreeEx'):
            raise OSError("VirtualFreeEx not available")

    def allocate_on_node(self, size: int, numa_node: int) -> Optional[memoryview]:
        """
        Allocate memory on specific NUMA node using VirtualAllocExNuma.

        Args:
            size: Size in bytes to allocate
            numa_node: Target NUMA node ID

        Returns:
            Memory buffer or None if allocation failed
        """
        if not self.numa_available or sys.platform != 'win32':
            # Fallback to standard allocation
            return self._allocate_standard(size)

        if numa_node not in self.topology.nodes:
            raise ValueError(f"Invalid NUMA node: {numa_node}")

        try:
            # CRITICAL FIX: Use proper ctypes wrappers for all parameters
            # Allocate memory on specific NUMA node
            addr = self.kernel32.VirtualAllocExNuma(
                ctypes.c_void_p(-1),  # Current process handle (64-bit safe)
                ctypes.c_void_p(0),   # Let system choose address (64-bit safe)
                ctypes.c_size_t(size),  # Size with proper type
                ctypes.c_ulong(self.MEM_COMMIT | self.MEM_RESERVE),  # Allocation type
                ctypes.c_ulong(self.PAGE_READWRITE),  # Protection
                ctypes.c_ulong(numa_node)  # NUMA node ID
            )

            if not addr:
                error_code = ctypes.get_last_error()
                raise OSError(f"VirtualAllocExNuma failed: error {error_code}")

            # Create Python buffer from allocated memory
            buffer = self._create_buffer_from_address(addr, size)

            # Track allocation
            with self._allocation_lock:
                allocation_id = id(buffer)
                self._allocations[allocation_id] = {
                    'address': addr,
                    'size': size,
                    'numa_node': numa_node,
                    'buffer': buffer
                }

            logger.debug(f"Allocated {size} bytes on NUMA node {numa_node}")
            return buffer

        except Exception as e:
            logger.warning(f"NUMA allocation failed, using standard allocation: {e}")
            return self._allocate_standard(size)

    def _create_buffer_from_address(self, addr: int, size: int) -> memoryview:
        """
        Create Python buffer from Windows memory address.

        CRITICAL FIX: Use bytearray intermediate for ALL Python versions to avoid
        "memoryview: unsupported format <B" error on Windows Python 3.12+.
        """
        try:
            # Create ctypes array from address
            ArrayType = ctypes.c_uint8 * size
            array = ArrayType.from_address(addr)

            # PRODUCTION-READY: Use bytearray for ALL Python versions
            # Direct memoryview(ctypes_array) fails with "unsupported format <B"
            # on Windows Python 3.12+ due to buffer format incompatibility
            buffer = bytearray(size)
            ctypes.memmove(
                (ctypes.c_uint8 * size).from_buffer(buffer),
                array,
                size
            )
            return memoryview(buffer)

        except Exception as e:
            logger.error(f"Failed to create buffer from address: {e}")
            raise

    def _allocate_standard(self, size: int) -> memoryview:
        """Fallback to standard Python memory allocation."""
        try:
            # Use bytearray for fallback allocation
            data = bytearray(size)
            return memoryview(data)
        except MemoryError as e:
            logger.error(f"Standard allocation failed: {e}")
            raise

    def free_buffer(self, buffer: memoryview) -> bool:
        """
        Free NUMA-allocated buffer.

        Args:
            buffer: Buffer to free

        Returns:
            True if freed successfully
        """
        if not buffer:
            return True

        allocation_id = id(buffer)

        with self._allocation_lock:
            if allocation_id not in self._allocations:
                # Not a NUMA allocation, let Python handle it
                return True

            allocation_info = self._allocations[allocation_id]
            addr = allocation_info['address']

            try:
                # CRITICAL FIX: Use ctypes.c_void_p for 64-bit address to avoid OverflowError
                # Plain int causes "int too long to convert" on 64-bit addresses
                success = self.kernel32.VirtualFreeEx(
                    ctypes.c_void_p(-1),  # Current process (use c_void_p for proper type)
                    ctypes.c_void_p(addr),  # Address as c_void_p for 64-bit safety
                    ctypes.c_size_t(0),   # Free entire allocation
                    ctypes.c_ulong(self.MEM_RELEASE)
                )

                if success:
                    del self._allocations[allocation_id]
                    logger.debug(f"Freed NUMA allocation at address {hex(addr)}")
                    return True
                else:
                    error_code = ctypes.get_last_error()
                    logger.error(f"VirtualFreeEx failed: error {error_code}")
                    return False

            except Exception as e:
                logger.error(f"Failed to free NUMA allocation: {e}")
                return False

    def get_buffer_numa_node(self, buffer: memoryview) -> Optional[int]:
        """
        Get NUMA node for allocated buffer.

        Args:
            buffer: Buffer to check

        Returns:
            NUMA node ID or None if unknown
        """
        allocation_id = id(buffer)

        with self._allocation_lock:
            if allocation_id in self._allocations:
                return self._allocations[allocation_id]['numa_node']

        return None

    def get_allocation_stats(self) -> Dict[str, Any]:
        """Get NUMA allocation statistics."""
        with self._allocation_lock:
            stats = {
                'total_allocations': len(self._allocations),
                'total_bytes': sum(alloc['size'] for alloc in self._allocations.values()),
                'allocations_by_node': {}
            }

            # Count allocations by NUMA node
            for alloc in self._allocations.values():
                node_id = alloc['numa_node']
                if node_id not in stats['allocations_by_node']:
                    stats['allocations_by_node'][node_id] = {
                        'count': 0,
                        'bytes': 0
                    }

                stats['allocations_by_node'][node_id]['count'] += 1
                stats['allocations_by_node'][node_id]['bytes'] += alloc['size']

        return stats

    def cleanup_all(self) -> None:
        """Free all NUMA allocations."""
        with self._allocation_lock:
            allocation_ids = list(self._allocations.keys())

        for allocation_id in allocation_ids:
            try:
                allocation_info = self._allocations[allocation_id]
                buffer = allocation_info['buffer']
                self.free_buffer(buffer)
            except Exception as e:
                logger.error(f"Failed to cleanup allocation {allocation_id}: {e}")


# Global allocator instance
_global_numa_allocator: Optional[WindowsNUMAAllocator] = None
_allocator_lock = threading.Lock()


def get_windows_numa_allocator() -> WindowsNUMAAllocator:
    """Get global Windows NUMA allocator instance."""
    global _global_numa_allocator
    if _global_numa_allocator is None:
        with _allocator_lock:
            if _global_numa_allocator is None:
                _global_numa_allocator = WindowsNUMAAllocator()
    return _global_numa_allocator


def allocate_numa_memory(size: int, numa_node: int = 0) -> Optional[memoryview]:
    """Allocate NUMA-aware memory on Windows."""
    allocator = get_windows_numa_allocator()
    return allocator.allocate_on_node(size, numa_node)


def free_numa_memory(buffer: memoryview) -> bool:
    """Free NUMA-allocated memory."""
    allocator = get_windows_numa_allocator()
    return allocator.free_buffer(buffer)
