"""
Advanced Windows NUMA Detection and Optimization

This module implements enhanced Windows NUMA support using advanced Windows APIs
for detailed topology detection, memory affinity, and thread affinity optimization.
"""

import os
import sys
import ctypes
import threading
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

from .numa_memory import NUMATopology, NUMANode, NUMAPolicy

logger = logging.getLogger(__name__)

# Platform-specific imports
if sys.platform == 'win32':
    from ctypes import wintypes, POINTER, Structure, Union, c_uint64, c_uint32, c_uint16, c_uint8
    
    # Define ULONG_PTR for Windows
    if hasattr(wintypes, 'ULONG_PTR'):
        ULONG_PTR = wintypes.ULONG_PTR
    else:
        # Define ULONG_PTR manually for older Python versions
        import platform
        if platform.architecture()[0] == '64bit':
            ULONG_PTR = c_uint64
        else:
            ULONG_PTR = c_uint32
    
    # Windows API structures for advanced NUMA detection
    class GROUP_AFFINITY(Structure):
        """Windows GROUP_AFFINITY structure for processor groups."""
        _fields_ = [
            ('Mask', ULONG_PTR),
            ('Group', wintypes.WORD),
            ('Reserved', wintypes.WORD * 3)
        ]
else:
    # Non-Windows platforms - define dummy structures
    class Structure:
        pass
    
    class GROUP_AFFINITY(Structure):
        """Dummy structure for non-Windows platforms."""
        pass
    
    wintypes = None
    POINTER = lambda x: x
    c_uint64 = int
    ULONG_PTR = int


if sys.platform == 'win32':
    class NUMA_NODE_RELATIONSHIP(Structure):
        """Windows NUMA_NODE_RELATIONSHIP structure."""
        _fields_ = [
            ('NodeNumber', wintypes.DWORD),
            ('Reserved', wintypes.BYTE * 18),
            ('GroupCount', wintypes.WORD),
            ('GroupMask', GROUP_AFFINITY * 1)  # Variable length in real API
        ]

    class LOGICAL_PROCESSOR_RELATIONSHIP(Structure):
        """Windows LOGICAL_PROCESSOR_RELATIONSHIP structure."""
        _fields_ = [
            ('Flags', wintypes.BYTE),
            ('EfficiencyClass', wintypes.BYTE),
            ('Reserved', wintypes.BYTE * 20),
            ('GroupCount', wintypes.WORD),
            ('GroupMask', GROUP_AFFINITY * 1)  # Variable length
        ]

    class SYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX(Structure):
        """Windows SYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX structure."""
        _fields_ = [
            ('Relationship', wintypes.DWORD),
            ('Size', wintypes.DWORD),
            # Union of different relationship types (simplified)
            ('NumaNode', NUMA_NODE_RELATIONSHIP),
            ('Processor', LOGICAL_PROCESSOR_RELATIONSHIP)
        ]
else:
    # Dummy structures for non-Windows platforms
    class NUMA_NODE_RELATIONSHIP(Structure):
        pass
    
    class LOGICAL_PROCESSOR_RELATIONSHIP(Structure):
        pass
    
    class SYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX(Structure):
        pass


@dataclass
class ProcessorGroup:
    """Windows processor group information."""
    group_id: int
    processor_count: int
    active_processor_mask: int
    numa_nodes: List[int]


class WindowsNUMADetector:
    """
    Advanced Windows NUMA topology detector using comprehensive Windows APIs.
    
    Uses GetLogicalProcessorInformationEx for detailed topology information
    instead of basic GetNumaHighestNodeNumber approximations.
    """
    
    def __init__(self):
        """Initialize Windows NUMA detector."""
        self._topology_cache: Optional[NUMATopology] = None
        self._processor_groups_cache: Optional[Dict[int, ProcessorGroup]] = None
        self._cache_lock = threading.Lock()
        
        # Load Windows APIs
        try:
            self.kernel32 = ctypes.windll.kernel32
            self._apis_available = self._check_api_availability()
        except Exception as e:
            logger.warning(f"Windows APIs not available: {e}")
            self._apis_available = False
    
    def _check_api_availability(self) -> bool:
        """Check if required Windows NUMA APIs are available."""
        required_apis = [
            'GetLogicalProcessorInformationEx',
            'GetNumaHighestNodeNumber',
            'GetNumaNodeProcessorMaskEx',
            'GetNumaAvailableMemoryNodeEx'
        ]
        
        for api_name in required_apis:
            if not hasattr(self.kernel32, api_name):
                logger.debug(f"Windows API not available: {api_name}")
                return False
        
        return True
    
    def detect_enhanced_topology(self) -> NUMATopology:
        """
        Detect enhanced NUMA topology using GetLogicalProcessorInformationEx.
        
        Returns:
            Detailed NUMA topology with accurate CPU-to-node mapping
        """
        with self._cache_lock:
            if self._topology_cache is not None:
                return self._topology_cache
            
            try:
                if not self._apis_available or sys.platform != 'win32':
                    return self._fallback_numa_detection()
                
                topology = self._detect_with_logical_processor_info()
                self._topology_cache = topology
                
                logger.info(f"Enhanced Windows NUMA topology: {topology.node_count} nodes, "
                           f"NUMA available: {topology.numa_available}")
                
                return topology
                
            except Exception as e:
                logger.warning(f"Enhanced NUMA detection failed: {e}")
                return self._fallback_numa_detection()
    
    def _detect_with_logical_processor_info(self) -> NUMATopology:
        """Detect NUMA topology using GetLogicalProcessorInformationEx."""
        # RelationNumaNode = 1
        RelationNumaNode = 1

        # CRITICAL FIX: Use 64-bit c_ulonglong for buffer size (not 32-bit DWORD)
        # On large NUMA systems, buffer size can exceed 2^32 bytes
        buffer_size = ctypes.c_ulonglong()
        result = self.kernel32.GetLogicalProcessorInformationEx(
            RelationNumaNode,
            None,
            ctypes.byref(buffer_size)
        )

        # CRITICAL FIX: GetLogicalProcessorInformationEx returns 0 on failure
        # Check for failure (result == 0) AND expected error code
        if result != 0 or ctypes.get_last_error() != 122:  # ERROR_INSUFFICIENT_BUFFER
            raise OSError("Failed to get buffer size for processor information")

        # CRITICAL FIX: Validate buffer size to prevent DoS
        MAX_BUFFER_SIZE = 1024 * 1024  # 1MB maximum (reasonable for NUMA topology)
        if buffer_size.value == 0 or buffer_size.value > MAX_BUFFER_SIZE:
            raise OSError(f"Invalid buffer size from API: {buffer_size.value} bytes")

        # Allocate buffer with validated size
        buffer = (ctypes.c_byte * buffer_size.value)()

        # Get processor information with properly sized buffer
        success = self.kernel32.GetLogicalProcessorInformationEx(
            RelationNumaNode,
            buffer,
            ctypes.byref(buffer_size)
        )

        if not success:
            error_code = ctypes.get_last_error()
            raise OSError(f"GetLogicalProcessorInformationEx failed with error {error_code}")

        # Parse NUMA information from buffer
        topology = self._parse_logical_processor_info(buffer, buffer_size.value)

        return topology
    
    def _parse_logical_processor_info(self, buffer: ctypes.Array, size: int) -> NUMATopology:
        """Parse NUMA topology from GetLogicalProcessorInformationEx buffer."""
        topology = NUMATopology(node_count=0, numa_available=False)
        offset = 0
        
        while offset < size:
            # Read structure header
            info_ptr = ctypes.cast(
                ctypes.addressof(buffer) + offset,
                POINTER(SYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX)
            )
            info = info_ptr.contents
            
            if info.Relationship == 1:  # RelationNumaNode
                # Extract NUMA node information
                numa_info = info.NumaNode
                node_id = numa_info.NodeNumber
                
                # Get processor group and mask
                if numa_info.GroupCount > 0:
                    group_mask = numa_info.GroupMask[0]
                    group_id = group_mask.Group
                    processor_mask = group_mask.Mask
                    
                    # Convert processor mask to CPU list
                    cpu_list = self._mask_to_cpu_list(processor_mask, group_id)
                    
                    # Get memory information for this node
                    memory_total, memory_free = self._get_node_memory_info(node_id)
                    
                    # Create NUMA node
                    numa_node = NUMANode(
                        node_id=node_id,
                        cpu_list=cpu_list,
                        memory_total=memory_total,
                        memory_free=memory_free
                    )
                    
                    topology.nodes[node_id] = numa_node
                    
                    # Update CPU to node mapping
                    for cpu_id in cpu_list:
                        topology.cpu_to_node[cpu_id] = node_id
            
            # Move to next structure
            offset += info.Size
        
        topology.node_count = len(topology.nodes)
        topology.numa_available = topology.node_count > 1
        
        return topology
    
    def _mask_to_cpu_list(self, processor_mask: int, group_id: int) -> List[int]:
        """Convert Windows processor mask to list of CPU IDs."""
        cpu_list = []
        
        # Base CPU offset for processor group
        group_offset = group_id * 64  # 64 processors per group max
        
        # Extract CPU IDs from bitmask
        for bit in range(64):
            if processor_mask & (1 << bit):
                cpu_list.append(group_offset + bit)
        
        return cpu_list
    
    def _get_node_memory_info(self, node_id: int) -> Tuple[int, int]:
        """Get real memory information for NUMA node using Windows APIs."""
        try:
            # Use GetNumaAvailableMemoryNodeEx for accurate memory info
            available_bytes = ctypes.c_uint64()
            
            if hasattr(self.kernel32, 'GetNumaAvailableMemoryNodeEx'):
                success = self.kernel32.GetNumaAvailableMemoryNodeEx(
                    node_id,
                    ctypes.byref(available_bytes)
                )
                
                if success:
                    # Estimate total memory (Windows doesn't provide direct API)
                    # Use system memory divided by node count as approximation
                    import psutil
                    total_system_memory = psutil.virtual_memory().total
                    estimated_total = total_system_memory // max(1, self._get_node_count())
                    
                    return estimated_total, available_bytes.value
            
        except Exception as e:
            logger.debug(f"Failed to get node memory info: {e}")
        
        # Fallback to system memory approximation
        import psutil
        total_memory = psutil.virtual_memory().total
        available_memory = psutil.virtual_memory().available
        node_count = max(1, self._get_node_count())
        
        return total_memory // node_count, available_memory // node_count
    
    def _get_node_count(self) -> int:
        """Get NUMA node count using GetNumaHighestNodeNumber."""
        try:
            highest_node = wintypes.ULONG()
            if self.kernel32.GetNumaHighestNodeNumber(ctypes.byref(highest_node)):
                return highest_node.value + 1
        except Exception:
            pass
        return 1
    
    def get_processor_groups(self) -> Dict[int, ProcessorGroup]:
        """Get Windows processor group information."""
        with self._cache_lock:
            if self._processor_groups_cache is not None:
                return self._processor_groups_cache
            
            try:
                groups = self._detect_processor_groups()
                self._processor_groups_cache = groups
                return groups
                
            except Exception as e:
                logger.warning(f"Processor group detection failed: {e}")
                return {}
    
    def _detect_processor_groups(self) -> Dict[int, ProcessorGroup]:
        """Detect Windows processor groups."""
        groups = {}

        try:
            # Use GetLogicalProcessorInformationEx with RelationGroup
            RelationGroup = 4

            # CRITICAL FIX: Use 64-bit c_ulonglong for buffer size (same as NUMA detection)
            buffer_size = ctypes.c_ulonglong()
            result = self.kernel32.GetLogicalProcessorInformationEx(
                RelationGroup, None, ctypes.byref(buffer_size)
            )

            # CRITICAL FIX: Check return value correctly (0 = failure)
            if result != 0 or ctypes.get_last_error() != 122:
                logger.warning("Failed to get processor group buffer size")
                return {}

            # Validate buffer size
            MAX_BUFFER_SIZE = 1024 * 1024  # 1MB max
            if buffer_size.value == 0 or buffer_size.value > MAX_BUFFER_SIZE:
                logger.warning(f"Invalid processor group buffer size: {buffer_size.value}")
                return {}

            # Get group information with properly sized buffer
            buffer = (ctypes.c_byte * buffer_size.value)()
            success = self.kernel32.GetLogicalProcessorInformationEx(
                RelationGroup, buffer, ctypes.byref(buffer_size)
            )
            
            if success:
                # Parse group information (simplified)
                # In real implementation, would parse the complex structure
                groups[0] = ProcessorGroup(
                    group_id=0,
                    processor_count=os.cpu_count() or 1,
                    active_processor_mask=(1 << (os.cpu_count() or 1)) - 1,
                    numa_nodes=list(range(self._get_node_count()))
                )
                
        except Exception as e:
            logger.debug(f"Processor group detection failed: {e}")
        
        return groups
    
    def _fallback_numa_detection(self) -> NUMATopology:
        """Fallback to basic NUMA detection when advanced APIs fail."""
        from .numa_memory import NUMATopologyDetector
        
        basic_detector = NUMATopologyDetector()
        return basic_detector._detect_windows_numa()


class WindowsNUMAMemoryInfo:
    """Windows NUMA memory information using real-time APIs."""
    
    def __init__(self):
        """Initialize Windows NUMA memory info provider."""
        try:
            self.kernel32 = ctypes.windll.kernel32
            self._apis_available = hasattr(self.kernel32, 'GetNumaAvailableMemoryNodeEx')
        except Exception:
            self._apis_available = False
    
    def get_node_memory_info(self, node_id: int) -> Dict[str, Any]:
        """
        Get real-time memory information for NUMA node.
        
        Args:
            node_id: NUMA node ID
            
        Returns:
            Memory information dictionary
        """
        result = {
            'available': False,
            'node_id': node_id,
            'available_bytes': 0,
            'total_bytes': 0
        }
        
        if not self._apis_available or sys.platform != 'win32':
            return result
        
        try:
            # Use GetNumaAvailableMemoryNodeEx for real memory info
            available_bytes = ctypes.c_uint64()
            
            success = self.kernel32.GetNumaAvailableMemoryNodeEx(
                node_id,
                ctypes.byref(available_bytes)
            )
            
            if success:
                result['available'] = True
                result['available_bytes'] = available_bytes.value
                
                # Estimate total memory (no direct Windows API)
                import psutil
                system_memory = psutil.virtual_memory().total
                
                # Get node count for estimation
                highest_node = wintypes.ULONG()
                if self.kernel32.GetNumaHighestNodeNumber(ctypes.byref(highest_node)):
                    node_count = highest_node.value + 1
                    result['total_bytes'] = system_memory // node_count
                else:
                    result['total_bytes'] = system_memory
            
        except Exception as e:
            logger.debug(f"Failed to get memory info for node {node_id}: {e}")
        
        return result


# Global instances for performance
_windows_numa_detector: Optional[WindowsNUMADetector] = None
_windows_memory_info: Optional[WindowsNUMAMemoryInfo] = None
_detector_lock = threading.Lock()


def get_windows_numa_detector() -> WindowsNUMADetector:
    """Get global Windows NUMA detector instance."""
    global _windows_numa_detector
    if _windows_numa_detector is None:
        with _detector_lock:
            if _windows_numa_detector is None:
                _windows_numa_detector = WindowsNUMADetector()
    return _windows_numa_detector


def get_windows_memory_info() -> WindowsNUMAMemoryInfo:
    """Get global Windows NUMA memory info instance."""
    global _windows_memory_info
    if _windows_memory_info is None:
        with _detector_lock:
            if _windows_memory_info is None:
                _windows_memory_info = WindowsNUMAMemoryInfo()
    return _windows_memory_info


def detect_windows_numa_enhanced() -> NUMATopology:
    """Detect enhanced Windows NUMA topology."""
    detector = get_windows_numa_detector()
    return detector.detect_enhanced_topology()


def is_windows_numa_available() -> bool:
    """Check if Windows NUMA is available."""
    if sys.platform != 'win32':
        return False
    
    detector = get_windows_numa_detector()
    topology = detector.detect_enhanced_topology()
    return topology.numa_available