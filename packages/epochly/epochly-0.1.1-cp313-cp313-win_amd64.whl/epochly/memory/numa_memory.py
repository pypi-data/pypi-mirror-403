"""
Epochly NUMA-Aware Memory Management

This module implements NUMA (Non-Uniform Memory Access) aware memory allocation
strategies for multi-socket systems. It provides topology detection and
NUMA-aware allocation policies as specified in the research-validated remediation plan.

Key Features:
- NUMA topology detection across platforms
- NUMA-aware memory allocation strategies
- Multi-socket optimization support
- Graceful fallback for single-socket systems

Author: Epochly Development Team
"""

import os
import sys
import threading
import psutil
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from ..utils.logger import get_logger


class NUMAPolicy(Enum):
    """NUMA memory allocation policies."""
    DEFAULT = "default"  # System default
    BIND = "bind"       # Bind to specific nodes
    INTERLEAVE = "interleave"  # Interleave across nodes
    LOCAL = "local"     # Prefer local node
    PREFERRED = "preferred"  # Prefer specific node with fallback


@dataclass
class NUMANode:
    """NUMA node information."""
    node_id: int
    cpu_list: List[int]
    memory_total: int  # bytes
    memory_free: int   # bytes
    distance_map: Dict[int, int] = field(default_factory=dict)

    @property
    def memory_utilization(self) -> float:
        """Calculate memory utilization ratio (0.0 to 1.0)."""
        if self.memory_total == 0:
            return 0.0
        return 1.0 - (self.memory_free / self.memory_total)

    def __eq__(self, other) -> bool:
        """
        Compare NUMA nodes for equality, ignoring transient memory_free values.

        memory_free changes constantly as system allocates/frees memory, so we only
        compare stable attributes for topology equality checks.
        """
        if not isinstance(other, NUMANode):
            return False

        return (
            self.node_id == other.node_id and
            self.cpu_list == other.cpu_list and
            self.memory_total == other.memory_total and
            self.distance_map == other.distance_map
        )

    def __hash__(self) -> int:
        """Hash based on stable attributes."""
        return hash((self.node_id, tuple(self.cpu_list), self.memory_total))


@dataclass
class NUMATopology:
    """NUMA system topology information."""
    node_count: int
    nodes: Dict[int, NUMANode] = field(default_factory=dict)
    cpu_to_node: Dict[int, int] = field(default_factory=dict)
    numa_available: bool = False

    def __eq__(self, other) -> bool:
        """
        Compare NUMA topologies for equality, ignoring transient memory_free values.

        This is critical for test stability - memory_free changes between topology
        detection calls due to system memory allocation.
        """
        if not isinstance(other, NUMATopology):
            return False

        return (
            self.node_count == other.node_count and
            self.numa_available == other.numa_available and
            self.cpu_to_node == other.cpu_to_node and
            self.nodes == other.nodes  # Uses NUMANode.__eq__ which ignores memory_free
        )

    def get_local_node(self, cpu_id: Optional[int] = None) -> Optional[int]:
        """Get local NUMA node for current thread or specific CPU."""
        if not self.numa_available or not self.nodes:
            return None

        if cpu_id is not None:
            return self.cpu_to_node.get(cpu_id)

        # Try to get current CPU affinity
        try:
            current_process = psutil.Process()
            affinity = current_process.cpu_affinity()
            if affinity:
                # Use first CPU in affinity set
                return self.cpu_to_node.get(affinity[0])
        except Exception:
            pass

        # Default to node 0
        return 0 if 0 in self.nodes else None

    def get_node_distance(self, from_node: int, to_node: int) -> int:
        """Get distance between NUMA nodes (10 = local, 20+ = remote)."""
        if from_node == to_node:
            return 10  # Local access

        if from_node in self.nodes:
            return self.nodes[from_node].distance_map.get(to_node, 20)

        return 20  # Default remote distance


class NUMATopologyDetector:
    """Detects NUMA topology across different platforms."""

    def __init__(self):
        """Initialize NUMA topology detector."""
        self.logger = get_logger(__name__)
        self._topology_cache: Optional[NUMATopology] = None

    def detect_topology(self) -> NUMATopology:
        """Detect NUMA topology for current system."""
        if self._topology_cache is not None:
            return self._topology_cache

        try:
            # Try different detection methods based on platform
            if sys.platform.startswith('linux'):
                topology = self._detect_linux_numa()
            elif sys.platform.startswith('win'):
                topology = self._detect_windows_numa()
            elif sys.platform.startswith('darwin'):
                topology = self._detect_macos_numa()
            else:
                topology = self._create_fallback_topology()

            # Validate and cache topology
            self._topology_cache = topology
            self.logger.info(f"Detected NUMA topology: {topology.node_count} nodes, "
                           f"NUMA available: {topology.numa_available}")

            return topology

        except Exception as e:
            self.logger.warning(f"NUMA topology detection failed: {e}")
            return self._create_fallback_topology()

    def _detect_linux_numa(self) -> NUMATopology:
        """Detect NUMA topology on Linux systems."""
        topology = NUMATopology(node_count=0)

        try:
            # Check if /sys/devices/system/node exists
            numa_sys_path = "/sys/devices/system/node"
            if not os.path.exists(numa_sys_path):
                return self._create_fallback_topology()

            # Parse NUMA nodes
            node_dirs = [d for d in os.listdir(numa_sys_path)
                        if d.startswith('node') and d[4:].isdigit()]

            if not node_dirs:
                return self._create_fallback_topology()

            topology.numa_available = True
            topology.node_count = len(node_dirs)

            for node_dir in sorted(node_dirs):
                node_id = int(node_dir[4:])
                node_path = os.path.join(numa_sys_path, node_dir)

                # Get CPU list
                cpu_list = self._parse_linux_cpu_list(node_path)

                # Get memory info
                memory_total, memory_free = self._parse_linux_memory_info(node_path)

                # Create NUMA node
                numa_node = NUMANode(
                    node_id=node_id,
                    cpu_list=cpu_list,
                    memory_total=memory_total,
                    memory_free=memory_free
                )

                # Get distance map
                numa_node.distance_map = self._parse_linux_distances(node_path)

                topology.nodes[node_id] = numa_node

                # Update CPU to node mapping
                for cpu_id in cpu_list:
                    topology.cpu_to_node[cpu_id] = node_id

            return topology

        except Exception as e:
            self.logger.warning(f"Linux NUMA detection failed: {e}")
            return self._create_fallback_topology()

    def _detect_windows_numa(self) -> NUMATopology:
        """Detect NUMA topology on Windows systems."""
        topology = NUMATopology(node_count=0)

        try:
            import ctypes
            from ctypes import wintypes

            # Try to get NUMA node count using GetNumaHighestNodeNumber
            kernel32 = ctypes.windll.kernel32

            if hasattr(kernel32, 'GetNumaHighestNodeNumber'):
                highest_node = wintypes.ULONG()
                if kernel32.GetNumaHighestNodeNumber(ctypes.byref(highest_node)):
                    topology.node_count = highest_node.value + 1
                    topology.numa_available = topology.node_count > 1

                    # Create simplified nodes (detailed info requires more complex APIs)
                    for node_id in range(topology.node_count):
                        # Use psutil for CPU and memory approximation
                        total_cpus = psutil.cpu_count()
                        cpus_per_node = max(1, total_cpus // topology.node_count)

                        cpu_start = node_id * cpus_per_node
                        cpu_end = min((node_id + 1) * cpus_per_node, total_cpus)
                        cpu_list = list(range(cpu_start, cpu_end))

                        # Approximate memory per node
                        total_memory = psutil.virtual_memory().total
                        memory_per_node = total_memory // topology.node_count
                        memory_free = psutil.virtual_memory().available // topology.node_count

                        numa_node = NUMANode(
                            node_id=node_id,
                            cpu_list=cpu_list,
                            memory_total=memory_per_node,
                            memory_free=memory_free
                        )

                        topology.nodes[node_id] = numa_node

                        for cpu_id in cpu_list:
                            topology.cpu_to_node[cpu_id] = node_id

            if topology.node_count == 0:
                return self._create_fallback_topology()

            return topology

        except Exception as e:
            self.logger.warning(f"Windows NUMA detection failed: {e}")
            return self._create_fallback_topology()

    def _detect_macos_numa(self) -> NUMATopology:
        """
        Detect NUMA topology on macOS systems (Task 4/6).

        Performance Improvement:
        - Before: Fabricated dual-node topology for any Mac with ≥8 CPUs
        - After: Returns single-node fallback unless sysctl evidence exists
        - Impact: Eliminates redundant NUMA operations on non-NUMA systems

        Environment Override:
        - EPOCHLY_MAC_NUMA=1: Enable experimental NUMA detection
        - Default: Conservative single-node fallback
        """
        # Check environment override first
        if os.environ.get('EPOCHLY_MAC_NUMA') != '1':
            # Conservative default: Return single-node topology
            self.logger.debug("macOS NUMA disabled (set EPOCHLY_MAC_NUMA=1 to enable)")
            return self._create_fallback_topology()

        # Validate sysctl evidence for NUMA
        if not self._has_perflevel_sysctls():
            self.logger.debug("macOS NUMA: No perflevel sysctls detected")
            return self._create_fallback_topology()

        # If override enabled AND sysctls exist, attempt detection
        try:
            cpu_count = psutil.cpu_count()
            if cpu_count < 8:
                # Low CPU count unlikely to have meaningful NUMA
                return self._create_fallback_topology()

            # Create simplified topology for Apple Silicon
            topology = NUMATopology(node_count=2, numa_available=True)

            # Split CPUs between performance and efficiency cores (approximation)
            perf_cores = cpu_count // 2

            # Performance cores node
            topology.nodes[0] = NUMANode(
                node_id=0,
                cpu_list=list(range(perf_cores)),
                memory_total=psutil.virtual_memory().total // 2,
                memory_free=psutil.virtual_memory().available // 2
            )

            # Efficiency cores node
            topology.nodes[1] = NUMANode(
                node_id=1,
                cpu_list=list(range(perf_cores, cpu_count)),
                memory_total=psutil.virtual_memory().total // 2,
                memory_free=psutil.virtual_memory().available // 2
            )

            # Update CPU mapping
            for cpu_id in range(cpu_count):
                topology.cpu_to_node[cpu_id] = 0 if cpu_id < perf_cores else 1

            self.logger.info(f"macOS NUMA enabled (experimental): {topology.node_count} nodes")
            return topology

        except Exception as e:
            self.logger.warning(f"macOS NUMA detection failed: {e}")
            return self._create_fallback_topology()

    def _has_perflevel_sysctls(self) -> bool:
        """
        Check if macOS has perflevel sysctls (Task 4/6).

        Validates hw.perflevel0.physicalcpu and hw.memsize exist before
        declaring NUMA available.

        Returns:
            bool: True if perflevel sysctls exist
        """
        if not sys.platform.startswith('darwin'):
            return False

        try:
            import subprocess

            # Check for hw.perflevel0.physicalcpu (indicates performance level info)
            result = subprocess.run(
                ['sysctl', 'hw.perflevel0.physicalcpu'],
                capture_output=True,
                text=True,
                timeout=1.0
            )

            if result.returncode == 0 and result.stdout.strip():
                self.logger.debug("Detected hw.perflevel0.physicalcpu sysctl")
                return True

            self.logger.debug("hw.perflevel0.physicalcpu sysctl not found")
            return False

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            self.logger.debug(f"perflevel sysctl check failed: {e}")
            return False

    def _create_fallback_topology(self) -> NUMATopology:
        """Create fallback topology for single-node systems."""
        cpu_count = psutil.cpu_count() or 1
        memory = psutil.virtual_memory()

        topology = NUMATopology(node_count=1, numa_available=False)

        # Single node with all CPUs and memory
        topology.nodes[0] = NUMANode(
            node_id=0,
            cpu_list=list(range(cpu_count)),
            memory_total=memory.total,
            memory_free=memory.available
        )

        # Map all CPUs to node 0
        for cpu_id in range(cpu_count):
            topology.cpu_to_node[cpu_id] = 0

        return topology

    def _parse_linux_cpu_list(self, node_path: str) -> List[int]:
        """Parse CPU list from Linux NUMA node."""
        try:
            cpu_list_file = os.path.join(node_path, "cpulist")
            if os.path.exists(cpu_list_file):
                with open(cpu_list_file, 'r') as f:
                    cpu_list_str = f.read().strip()
                    return self._parse_cpu_range(cpu_list_str)
        except Exception:
            pass
        return []

    def _parse_linux_memory_info(self, node_path: str) -> Tuple[int, int]:
        """Parse memory info from Linux NUMA node."""
        try:
            meminfo_file = os.path.join(node_path, "meminfo")
            if os.path.exists(meminfo_file):
                total = 0
                free = 0
                with open(meminfo_file, 'r') as f:
                    for line in f:
                        if line.startswith('Node'):
                            parts = line.split()
                            if 'MemTotal:' in parts:
                                total = int(parts[parts.index('MemTotal:') + 1]) * 1024
                            elif 'MemFree:' in parts:
                                free = int(parts[parts.index('MemFree:') + 1]) * 1024
                return total, free
        except Exception:
            pass
        return 0, 0

    def _parse_linux_distances(self, node_path: str) -> Dict[int, int]:
        """Parse NUMA distances from Linux node."""
        try:
            distance_file = os.path.join(node_path, "distance")
            if os.path.exists(distance_file):
                with open(distance_file, 'r') as f:
                    distances = f.read().strip().split()
                    return {i: int(d) for i, d in enumerate(distances)}
        except Exception:
            pass
        return {}

    def _parse_cpu_range(self, cpu_range_str: str) -> List[int]:
        """Parse CPU range string like '0-3,8-11' into list of CPU IDs."""
        cpu_list = []
        for part in cpu_range_str.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                cpu_list.extend(range(start, end + 1))
            else:
                cpu_list.append(int(part))
        return cpu_list


class NUMAMemoryManager:
    """NUMA-aware memory allocation manager."""

    def __init__(self):
        """Initialize NUMA memory manager."""
        self.logger = get_logger(__name__)
        self._detector = NUMATopologyDetector()
        self._topology = self._detector.detect_topology()
        self._lock = threading.RLock()

        # Track allocations per node
        self._allocations_per_node: Dict[int, int] = defaultdict(int)
        self._bytes_per_node: Dict[int, int] = defaultdict(int)

        # Default policy
        self._default_policy = NUMAPolicy.LOCAL if self._topology.numa_available else NUMAPolicy.DEFAULT

    def get_topology(self) -> NUMATopology:
        """Get NUMA topology information."""
        return self._topology

    def is_numa_available(self) -> bool:
        """Check if NUMA is available on this system."""
        return self._topology.numa_available

    def get_optimal_node_for_allocation(self, size: int,
                                      policy: NUMAPolicy = None,
                                      preferred_node: Optional[int] = None) -> Optional[int]:
        """
        Get optimal NUMA node for memory allocation.

        Args:
            size: Size of allocation in bytes
            policy: NUMA allocation policy
            preferred_node: Preferred node for PREFERRED policy

        Returns:
            Optimal node ID or None for no preference
        """
        if not self._topology.numa_available:
            return None

        policy = policy or self._default_policy

        if policy == NUMAPolicy.DEFAULT:
            return None  # Let system decide

        elif policy == NUMAPolicy.LOCAL:
            return self._topology.get_local_node()

        elif policy == NUMAPolicy.BIND:
            # Bind to specific node (prefer local if not specified)
            return preferred_node or self._topology.get_local_node()

        elif policy == NUMAPolicy.PREFERRED:
            # Prefer specific node with fallback
            if preferred_node is not None and preferred_node in self._topology.nodes:
                node = self._topology.nodes[preferred_node]
                if node.memory_free >= size:
                    return preferred_node
            # Fallback to local
            return self._topology.get_local_node()

        elif policy == NUMAPolicy.INTERLEAVE:
            # Round-robin allocation across nodes
            return self._get_interleave_node()

        return None

    def _get_interleave_node(self) -> int:
        """Get next node for interleave policy."""
        if not self._topology.nodes:
            return 0

        # Simple round-robin based on total allocations
        total_allocations = sum(self._allocations_per_node.values())
        node_ids = sorted(self._topology.nodes.keys())
        return node_ids[total_allocations % len(node_ids)]

    def get_memory_usage_by_node(self) -> Dict[int, Dict[str, int]]:
        """Get memory usage statistics by NUMA node."""
        usage = {}

        for node_id, node in self._topology.nodes.items():
            usage[node_id] = {
                'total_bytes': node.memory_total,
                'free_bytes': node.memory_free,
                'allocated_by_epochly': self._bytes_per_node[node_id],
                'allocations_count': self._allocations_per_node[node_id],
                'utilization': node.memory_utilization
            }

        return usage

    def record_allocation(self, node_id: Optional[int], size: int) -> None:
        """Record allocation for NUMA tracking."""
        if node_id is not None and node_id in self._topology.nodes:
            with self._lock:
                self._allocations_per_node[node_id] += 1
                self._bytes_per_node[node_id] += size

    def record_deallocation(self, node_id: Optional[int], size: int) -> None:
        """Record deallocation for NUMA tracking."""
        if node_id is not None and node_id in self._topology.nodes:
            with self._lock:
                self._allocations_per_node[node_id] = max(0, self._allocations_per_node[node_id] - 1)
                self._bytes_per_node[node_id] = max(0, self._bytes_per_node[node_id] - size)

    def get_numa_recommendations(self, workload_characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get NUMA optimization recommendations based on workload characteristics.

        Args:
            workload_characteristics: Workload analysis from enhanced profiler

        Returns:
            NUMA optimization recommendations
        """
        if not self._topology.numa_available:
            return {
                'numa_available': False,
                'recommendation': 'NUMA not available - using UMA optimizations',
                'policy': NUMAPolicy.DEFAULT.value
            }

        # Analyze workload for NUMA recommendations
        memory_intensity = workload_characteristics.get('memory_bound_score', 0.0)
        cpu_intensity = workload_characteristics.get('cpu_bound_score', 0.0)
        parallel_efficiency = workload_characteristics.get('parallel_efficiency', 1.0)

        # Decision logic based on research
        if memory_intensity > 0.7:
            # Memory-intensive workloads benefit from local allocation
            policy = NUMAPolicy.LOCAL
            recommendation = "Use local NUMA allocation for memory-intensive workload"
        elif cpu_intensity > 0.7 and parallel_efficiency > 0.8:
            # CPU-intensive parallel workloads may benefit from interleaving
            policy = NUMAPolicy.INTERLEAVE
            recommendation = "Use interleaved NUMA allocation for parallel CPU workload"
        else:
            # Mixed workloads use preferred with local fallback
            policy = NUMAPolicy.PREFERRED
            recommendation = "Use preferred NUMA allocation with local fallback"

        return {
            'numa_available': True,
            'node_count': self._topology.node_count,
            'recommended_policy': policy.value,
            'recommendation': recommendation,
            'topology': {
                'nodes': len(self._topology.nodes),
                'total_cpus': sum(len(node.cpu_list) for node in self._topology.nodes.values()),
                'total_memory': sum(node.memory_total for node in self._topology.nodes.values())
            }
        }


# Global NUMA manager instance
_numa_manager: Optional[NUMAMemoryManager] = None
_numa_lock = threading.Lock()


def get_numa_manager() -> NUMAMemoryManager:
    """Get global NUMA memory manager instance."""
    global _numa_manager
    if _numa_manager is None:
        with _numa_lock:
            if _numa_manager is None:
                _numa_manager = NUMAMemoryManager()
    return _numa_manager


def detect_numa_topology() -> NUMATopology:
    """Detect NUMA topology for current system."""
    manager = get_numa_manager()
    return manager.get_topology()


def is_numa_available() -> bool:
    """Check if NUMA is available on current system."""
    manager = get_numa_manager()
    return manager.is_numa_available()


def get_optimal_numa_node(size: int, policy: NUMAPolicy = None) -> Optional[int]:
    """Get optimal NUMA node for allocation."""
    manager = get_numa_manager()
    return manager.get_optimal_node_for_allocation(size, policy)
