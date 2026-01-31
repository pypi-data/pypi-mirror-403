"""
NUMA-aware Scheduling Manager (SPEC2 Task 14).

Routes tasks to interpreters on optimal NUMA nodes.
"""

import os
import logging
from typing import Optional, List, Dict
from .numa_detector import NumaDetector, NumaNode


logger = logging.getLogger(__name__)


class NumaManager:
    """
    NUMA-aware task scheduler.

    Binds sub-interpreters to NUMA nodes and routes tasks
    to minimize memory latency.
    """

    def __init__(self):
        """Initialize NUMA manager."""
        self._detector = NumaDetector()
        self._numa_available = self._detector.is_numa_available()
        self._nodes = self._detector.get_nodes()

        # Map interpreter_id -> numa_node_id
        self._interpreter_node_map: Dict[int, int] = {}

        # Track task characteristics
        self._task_memory_profile: Dict[str, int] = {}  # task_name -> preferred_node

        if self._numa_available:
            logger.info(f"NUMA manager initialized with {len(self._nodes)} nodes")
        else:
            logger.info("NUMA manager initialized (single-node fallback)")

    def assign_interpreter_to_node(self, interpreter_id: int, node_id: Optional[int] = None) -> int:
        """
        Assign an interpreter to a NUMA node.

        Args:
            interpreter_id: Interpreter ID to assign
            node_id: Optional specific node ID, or auto-assign if None

        Returns:
            Assigned NUMA node ID
        """
        if not self._numa_available:
            self._interpreter_node_map[interpreter_id] = 0
            return 0

        if node_id is None:
            # Auto-assign: round-robin across nodes
            node_id = interpreter_id % len(self._nodes)

        # Validate node ID
        if node_id >= len(self._nodes):
            logger.warning(f"Invalid node ID {node_id}, using node 0")
            node_id = 0

        self._interpreter_node_map[interpreter_id] = node_id
        logger.debug(f"Assigned interpreter {interpreter_id} to NUMA node {node_id}")

        return node_id

    def select_node(self, task_memory_profile: Optional[Dict] = None) -> int:
        """
        Select optimal NUMA node for a task.

        Args:
            task_memory_profile: Dict with memory characteristics
                - 'size': Memory size in bytes
                - 'node_preference': Preferred node ID (optional)

        Returns:
            Selected NUMA node ID
        """
        if not self._numa_available:
            return 0

        # Use explicit preference if provided
        if task_memory_profile and 'node_preference' in task_memory_profile:
            node_id = task_memory_profile['node_preference']
            if 0 <= node_id < len(self._nodes):
                return node_id

        # Select node with most free memory
        best_node = 0
        max_free = 0

        for node in self._nodes:
            if node.memory_free_mb > max_free:
                max_free = node.memory_free_mb
                best_node = node.node_id

        return best_node

    def get_interpreter_node(self, interpreter_id: int) -> int:
        """Get NUMA node for an interpreter."""
        return self._interpreter_node_map.get(interpreter_id, 0)

    def get_optimal_interpreter(self, task_name: str, available_interpreters: List[int]) -> int:
        """
        Get optimal interpreter for a task based on NUMA locality.

        Args:
            task_name: Task identifier
            available_interpreters: List of available interpreter IDs

        Returns:
            Optimal interpreter ID
        """
        if not self._numa_available or not available_interpreters:
            return available_interpreters[0] if available_interpreters else 0

        # Check if task has node preference
        preferred_node = self._task_memory_profile.get(task_name, None)

        if preferred_node is not None:
            # Find interpreter on preferred node
            for interp_id in available_interpreters:
                if self.get_interpreter_node(interp_id) == preferred_node:
                    logger.debug(f"Selected interpreter {interp_id} on preferred node {preferred_node}")
                    return interp_id

        # Fallback: return first available
        return available_interpreters[0]

    def record_task_memory_profile(self, task_name: str, node_id: int) -> None:
        """
        Record task's preferred NUMA node based on memory access patterns.

        Args:
            task_name: Task identifier
            node_id: NUMA node where task performed well
        """
        self._task_memory_profile[task_name] = node_id
        logger.debug(f"Recorded memory profile: task '{task_name}' prefers node {node_id}")

    def get_node_info(self, node_id: int) -> Optional[NumaNode]:
        """Get information about a NUMA node."""
        if 0 <= node_id < len(self._nodes):
            return self._nodes[node_id]
        return None

    def is_available(self) -> bool:
        """Check if NUMA is available."""
        return self._numa_available

    def get_node_count(self) -> int:
        """Get number of NUMA nodes."""
        return len(self._nodes)

    def get_topology(self) -> Dict:
        """
        Get NUMA topology information.

        Returns:
            Dict with topology details
        """
        return {
            'numa_available': self._numa_available,
            'node_count': len(self._nodes),
            'nodes': [
                {
                    'node_id': node.node_id,
                    'cpu_count': len(node.cpu_list),
                    'cpu_list': node.cpu_list,
                    'memory_total_mb': node.memory_total_mb,
                    'memory_free_mb': node.memory_free_mb,
                    'distances': node.distance_map
                }
                for node in self._nodes
            ],
            'interpreter_assignments': dict(self._interpreter_node_map)
        }
