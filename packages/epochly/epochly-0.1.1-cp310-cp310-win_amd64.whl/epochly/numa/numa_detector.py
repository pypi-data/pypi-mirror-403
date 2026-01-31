"""
NUMA Topology Detection (SPEC2 Task 14).

Detects NUMA nodes and provides topology information.
"""

import os
import platform
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class NumaNode:
    """Represents a NUMA node."""
    node_id: int
    cpu_list: List[int]
    memory_total_mb: int
    memory_free_mb: int
    distance_map: Dict[int, int]  # {node_id: distance}


class NumaDetector:
    """
    NUMA topology detector.

    Detects NUMA nodes via platform-specific methods.
    Falls back gracefully on single-NUMA systems.
    """

    def __init__(self):
        """Initialize NUMA detector."""
        self._nodes: Optional[List[NumaNode]] = None
        self._numa_available = False
        self._detect_numa()

    def _detect_numa(self) -> None:
        """Detect NUMA topology."""
        system = platform.system()

        if system == 'Linux':
            self._detect_linux_numa()
        elif system == 'Windows':
            self._detect_windows_numa()
        elif system == 'Darwin':
            # macOS doesn't have NUMA
            self._numa_available = False
            self._nodes = [self._create_single_node()]
            logger.info("macOS detected - no NUMA support")
        else:
            self._numa_available = False
            self._nodes = [self._create_single_node()]
            logger.info(f"Unknown platform {system} - assuming single NUMA node")

    def _detect_linux_numa(self) -> None:
        """Detect NUMA on Linux via sysfs."""
        numa_path = '/sys/devices/system/node'

        if not os.path.exists(numa_path):
            self._numa_available = False
            self._nodes = [self._create_single_node()]
            logger.info("No NUMA sysfs found - single node system")
            return

        try:
            # Find all node directories
            node_dirs = [d for d in os.listdir(numa_path) if d.startswith('node')]

            if not node_dirs:
                self._numa_available = False
                self._nodes = [self._create_single_node()]
                logger.info("No NUMA nodes found - single node system")
                return

            nodes = []
            for node_dir in sorted(node_dirs):
                node_id = int(node_dir.replace('node', ''))
                node_path = os.path.join(numa_path, node_dir)

                # Read CPU list
                cpulist_file = os.path.join(node_path, 'cpulist')
                try:
                    with open(cpulist_file) as f:
                        cpu_list = self._parse_cpu_list(f.read().strip())
                except (IOError, OSError):
                    cpu_list = [node_id]  # Fallback to single CPU

                # Read memory info
                meminfo_file = os.path.join(node_path, 'meminfo')
                try:
                    with open(meminfo_file) as f:
                        memory_total, memory_free = self._parse_meminfo(f.read())
                except (IOError, OSError):
                    memory_total, memory_free = 0, 0  # Fallback

                # Read distance map
                distance_file = os.path.join(node_path, 'distance')
                try:
                    with open(distance_file) as f:
                        distance_map = self._parse_distance(node_id, f.read().strip())
                except (IOError, OSError):
                    distance_map = {node_id: 10}  # Fallback to self-distance

                node = NumaNode(
                    node_id=node_id,
                    cpu_list=cpu_list,
                    memory_total_mb=memory_total,
                    memory_free_mb=memory_free,
                    distance_map=distance_map
                )
                nodes.append(node)

            self._numa_available = len(nodes) > 1
            self._nodes = nodes
            logger.info(f"Detected {len(nodes)} NUMA nodes")

        except Exception as e:
            logger.warning(f"Error detecting NUMA: {e}, falling back to single node")
            self._numa_available = False
            self._nodes = [self._create_single_node()]

    def _detect_windows_numa(self) -> None:
        """Detect NUMA on Windows."""
        try:
            import ctypes
            from ctypes import wintypes

            # Try to detect NUMA nodes via Windows API
            kernel32 = ctypes.windll.kernel32

            # GetNumaHighestNodeNumber
            highest_node = wintypes.ULONG()
            if kernel32.GetNumaHighestNodeNumber(ctypes.byref(highest_node)):
                num_nodes = highest_node.value + 1

                if num_nodes > 1:
                    self._numa_available = True
                    # Create simplified node info (Windows API is complex)
                    cpu_count = os.cpu_count() or 1
                    cpus_per_node = max(1, cpu_count // num_nodes)

                    nodes = []
                    for i in range(num_nodes):
                        start_cpu = i * cpus_per_node
                        end_cpu = min((i + 1) * cpus_per_node, cpu_count)
                        cpu_list = list(range(start_cpu, end_cpu))

                        node = NumaNode(
                            node_id=i,
                            cpu_list=cpu_list,
                            memory_total_mb=0,  # Not easily available
                            memory_free_mb=0,
                            distance_map={i: 10}  # Self-distance
                        )
                        nodes.append(node)

                    self._nodes = nodes
                    logger.info(f"Windows NUMA detected: {num_nodes} nodes")
                else:
                    self._numa_available = False
                    self._nodes = [self._create_single_node()]
                    logger.info("Windows single-node system")
            else:
                raise RuntimeError("GetNumaHighestNodeNumber failed")

        except Exception as e:
            logger.warning(f"Windows NUMA detection failed: {e}")
            self._numa_available = False
            self._nodes = [self._create_single_node()]

    def _create_single_node(self) -> NumaNode:
        """Create a single NUMA node for non-NUMA systems."""
        cpu_count = os.cpu_count() or 1
        return NumaNode(
            node_id=0,
            cpu_list=list(range(cpu_count)),
            memory_total_mb=0,
            memory_free_mb=0,
            distance_map={0: 10}
        )

    def _parse_cpu_list(self, cpulist: str) -> List[int]:
        """Parse Linux cpulist format (e.g., '0-3,8-11')."""
        cpus = []
        for part in cpulist.split(','):
            if '-' in part:
                start, end = part.split('-')
                cpus.extend(range(int(start), int(end) + 1))
            else:
                cpus.append(int(part))
        return cpus

    def _parse_meminfo(self, meminfo: str) -> tuple:
        """Parse Linux NUMA meminfo."""
        total_mb = 0
        free_mb = 0

        for line in meminfo.splitlines():
            if 'MemTotal' in line:
                total_mb = int(line.split()[3]) // 1024  # KB to MB
            elif 'MemFree' in line:
                free_mb = int(line.split()[3]) // 1024

        return total_mb, free_mb

    def _parse_distance(self, node_id: int, distance: str) -> Dict[int, int]:
        """Parse NUMA distance map."""
        distances = [int(d) for d in distance.split()]
        return {i: dist for i, dist in enumerate(distances)}

    def is_numa_available(self) -> bool:
        """Check if NUMA is available."""
        return self._numa_available

    def get_nodes(self) -> List[NumaNode]:
        """Get list of NUMA nodes."""
        return self._nodes or []

    def get_node_count(self) -> int:
        """Get number of NUMA nodes."""
        return len(self._nodes) if self._nodes else 0

    def get_node_for_cpu(self, cpu_id: int) -> Optional[NumaNode]:
        """Get NUMA node containing a CPU."""
        if not self._nodes:
            return None

        for node in self._nodes:
            if cpu_id in node.cpu_list:
                return node

        return None

    def get_local_node(self, cpu_id: int) -> int:
        """Get local NUMA node ID for a CPU."""
        node = self.get_node_for_cpu(cpu_id)
        return node.node_id if node else 0

    def get_distance(self, from_node: int, to_node: int) -> int:
        """Get NUMA distance between two nodes."""
        if not self._nodes or from_node >= len(self._nodes):
            return 10  # Default distance

        return self._nodes[from_node].distance_map.get(to_node, 20)
