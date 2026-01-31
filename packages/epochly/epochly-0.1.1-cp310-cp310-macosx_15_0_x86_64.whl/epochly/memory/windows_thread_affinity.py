"""
Windows Thread Affinity Management

Implements Windows thread affinity management for NUMA optimization using
SetThreadAffinityMask and related Windows APIs.
"""

import sys
import ctypes
import threading
import time
from ctypes import wintypes
from typing import Dict, Any, Optional, List, Set
import logging

from .windows_numa_advanced import get_windows_numa_detector

logger = logging.getLogger(__name__)


class WindowsThreadAffinityManager:
    """
    Windows thread affinity manager for NUMA optimization.
    
    Provides thread pinning to NUMA nodes using Windows APIs for optimal
    memory locality and performance on multi-socket systems.
    """
    
    def __init__(self):
        """Initialize Windows thread affinity manager."""
        # Get NUMA topology
        detector = get_windows_numa_detector()
        self.topology = detector.detect_enhanced_topology()
        self.numa_available = self.topology.numa_available
        
        # Load Windows APIs
        try:
            self.kernel32 = ctypes.windll.kernel32
            self._check_affinity_apis()
        except Exception as e:
            logger.warning(f"Windows thread affinity APIs not available: {e}")
            self.numa_available = False
        
        # Track thread affinities
        self._thread_affinities: Dict[int, int] = {}  # thread_id -> affinity_mask
        self._affinity_lock = threading.Lock()
    
    def _check_affinity_apis(self) -> None:
        """Check if required thread affinity APIs are available."""
        required_apis = [
            'GetCurrentThread',
            'SetThreadAffinityMask',
            'GetThreadAffinityMask',
            'SetThreadIdealProcessor'
        ]
        
        for api_name in required_apis:
            if not hasattr(self.kernel32, api_name):
                raise OSError(f"Required API not available: {api_name}")
    
    def pin_thread_to_numa_node(self, numa_node: int) -> bool:
        """
        Pin current thread to specific NUMA node.
        
        Args:
            numa_node: Target NUMA node ID
            
        Returns:
            True if pinning successful
        """
        if not self.numa_available or sys.platform != 'win32':
            return False
        
        if numa_node not in self.topology.nodes:
            logger.error(f"Invalid NUMA node: {numa_node}")
            return False
        
        try:
            # Get processor mask for NUMA node
            processor_mask = self._get_numa_node_processor_mask(numa_node)
            if not processor_mask:
                logger.error(f"Could not get processor mask for NUMA node {numa_node}")
                return False
            
            # Set thread affinity
            thread_handle = self.kernel32.GetCurrentThread()
            old_affinity = self.kernel32.SetThreadAffinityMask(thread_handle, processor_mask)
            
            if old_affinity == 0:
                error_code = ctypes.get_last_error()
                logger.error(f"SetThreadAffinityMask failed: error {error_code}")
                return False
            
            # Set ideal processor within the NUMA node
            first_cpu = self._get_first_cpu_in_node(numa_node)
            if first_cpu is not None:
                self.kernel32.SetThreadIdealProcessor(thread_handle, first_cpu)
            
            # Track affinity change
            thread_id = threading.get_ident()
            with self._affinity_lock:
                self._thread_affinities[thread_id] = processor_mask
            
            logger.debug(f"Pinned thread {thread_id} to NUMA node {numa_node}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pin thread to NUMA node {numa_node}: {e}")
            return False
    
    def _get_numa_node_processor_mask(self, numa_node: int) -> Optional[int]:
        """Get processor mask for NUMA node."""
        try:
            # Use GetNumaNodeProcessorMask for processor mask
            processor_mask = wintypes.ULONG_PTR()
            
            if hasattr(self.kernel32, 'GetNumaNodeProcessorMask'):
                success = self.kernel32.GetNumaNodeProcessorMask(
                    numa_node,
                    ctypes.byref(processor_mask)
                )
                
                if success:
                    return processor_mask.value
            
            # Fallback: calculate mask from CPU list in topology
            node = self.topology.nodes.get(numa_node)
            if node and node.cpu_list:
                mask = 0
                for cpu_id in node.cpu_list:
                    if cpu_id < 64:  # Standard processor mask limit
                        mask |= (1 << cpu_id)
                return mask
                
        except Exception as e:
            logger.debug(f"Failed to get processor mask for node {numa_node}: {e}")
        
        return None
    
    def _get_first_cpu_in_node(self, numa_node: int) -> Optional[int]:
        """Get first CPU ID in NUMA node for ideal processor setting."""
        node = self.topology.nodes.get(numa_node)
        if node and node.cpu_list:
            return min(node.cpu_list)
        return None
    
    def get_current_thread_affinity(self) -> Optional[int]:
        """Get current thread affinity mask."""
        if not self.numa_available or sys.platform != 'win32':
            return None
        
        try:
            thread_handle = self.kernel32.GetCurrentThread()
            
            # GetThreadAffinityMask doesn't exist, use workaround
            # Set affinity to itself to get current mask
            current_mask = self.kernel32.SetThreadAffinityMask(thread_handle, -1)
            
            if current_mask != 0:
                # Restore original affinity
                self.kernel32.SetThreadAffinityMask(thread_handle, current_mask)
                return current_mask
                
        except Exception as e:
            logger.debug(f"Failed to get thread affinity: {e}")
        
        return None
    
    def set_thread_affinity(self, affinity_mask: int) -> bool:
        """
        Set thread affinity to specific mask.
        
        Args:
            affinity_mask: Processor affinity mask
            
        Returns:
            True if successful
        """
        if not self.numa_available or sys.platform != 'win32':
            return False
        
        try:
            thread_handle = self.kernel32.GetCurrentThread()
            old_affinity = self.kernel32.SetThreadAffinityMask(thread_handle, affinity_mask)
            
            if old_affinity == 0:
                error_code = ctypes.get_last_error()
                logger.error(f"SetThreadAffinityMask failed: error {error_code}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set thread affinity: {e}")
            return False
    
    def get_current_thread_numa_node(self) -> Optional[int]:
        """Get NUMA node of current thread based on affinity."""
        if not self.numa_available:
            return None
        
        thread_id = threading.get_ident()
        
        with self._affinity_lock:
            if thread_id in self._thread_affinities:
                affinity_mask = self._thread_affinities[thread_id]
                return self._mask_to_numa_node(affinity_mask)
        
        # Try to determine from current affinity
        current_affinity = self.get_current_thread_affinity()
        if current_affinity:
            return self._mask_to_numa_node(current_affinity)
        
        return None
    
    def _mask_to_numa_node(self, affinity_mask: int) -> Optional[int]:
        """Convert affinity mask to NUMA node ID."""
        # Find which NUMA node contains the most CPUs in the mask
        best_node = None
        best_match_count = 0
        
        for node_id, node in self.topology.nodes.items():
            match_count = 0
            for cpu_id in node.cpu_list:
                if cpu_id < 64 and (affinity_mask & (1 << cpu_id)):
                    match_count += 1
            
            if match_count > best_match_count:
                best_match_count = match_count
                best_node = node_id
        
        return best_node
    
    def create_numa_thread_pool_executor(self, workers_per_node: int = 2) -> 'NUMAThreadPoolExecutor':
        """
        Create thread pool executor with NUMA-aware worker pinning.
        
        Args:
            workers_per_node: Number of worker threads per NUMA node
            
        Returns:
            NUMA-aware thread pool executor
        """
        from concurrent.futures import ThreadPoolExecutor
        
        if not self.numa_available:
            # Fallback to standard thread pool
            return ThreadPoolExecutor(max_workers=workers_per_node)
        
        return NUMAThreadPoolExecutor(
            workers_per_node=workers_per_node,
            affinity_manager=self
        )
    
    def get_optimal_numa_node_for_thread(self) -> int:
        """Get optimal NUMA node for current thread based on workload."""
        if not self.numa_available:
            return 0
        
        # Simple strategy: use node with most available memory
        best_node = 0
        best_available = 0
        
        for node_id, node in self.topology.nodes.items():
            if node.memory_free > best_available:
                best_available = node.memory_free
                best_node = node_id
        
        return best_node


class NUMAThreadPoolExecutor:
    """Thread pool executor with NUMA-aware worker pinning."""
    
    def __init__(self, workers_per_node: int, affinity_manager: WindowsThreadAffinityManager):
        """Initialize NUMA-aware thread pool executor."""
        self.workers_per_node = workers_per_node
        self.affinity_manager = affinity_manager
        self.topology = affinity_manager.topology
        
        # Calculate total workers
        total_workers = workers_per_node * self.topology.node_count
        
        # Create thread pool
        from concurrent.futures import ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(
            max_workers=total_workers,
            thread_name_prefix="NUMAWorker"
        )
        
        # Track worker assignments
        self._worker_nodes: Dict[str, int] = {}
        self._assignment_lock = threading.Lock()
    
    def submit(self, fn, *args, **kwargs):
        """Submit task with NUMA-aware worker selection."""
        # Determine optimal NUMA node for task
        numa_node = self._select_numa_node_for_task(fn, args, kwargs)
        
        # Wrap function to set affinity
        def numa_aware_wrapper():
            # Pin worker thread to NUMA node
            thread_name = threading.current_thread().name
            
            with self._assignment_lock:
                if thread_name not in self._worker_nodes:
                    self._worker_nodes[thread_name] = numa_node
                    self.affinity_manager.pin_thread_to_numa_node(numa_node)
            
            # Execute original function
            return fn(*args, **kwargs)
        
        return self.executor.submit(numa_aware_wrapper)
    
    def _select_numa_node_for_task(self, fn, args, kwargs) -> int:
        """Select optimal NUMA node for task based on data locality."""
        # Simple strategy: round-robin across NUMA nodes
        # More sophisticated version could analyze data locations
        
        with self._assignment_lock:
            worker_count = len(self._worker_nodes)
            return worker_count % self.topology.node_count
    
    def shutdown(self, wait: bool = True):
        """Shutdown NUMA-aware thread pool."""
        self.executor.shutdown(wait=wait)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# Global affinity manager instance
_global_affinity_manager: Optional[WindowsThreadAffinityManager] = None
_manager_lock = threading.Lock()


def get_windows_thread_affinity_manager() -> WindowsThreadAffinityManager:
    """Get global Windows thread affinity manager."""
    global _global_affinity_manager
    if _global_affinity_manager is None:
        with _manager_lock:
            if _global_affinity_manager is None:
                _global_affinity_manager = WindowsThreadAffinityManager()
    return _global_affinity_manager


def pin_current_thread_to_numa_node(numa_node: int) -> bool:
    """Pin current thread to NUMA node."""
    manager = get_windows_thread_affinity_manager()
    return manager.pin_thread_to_numa_node(numa_node)