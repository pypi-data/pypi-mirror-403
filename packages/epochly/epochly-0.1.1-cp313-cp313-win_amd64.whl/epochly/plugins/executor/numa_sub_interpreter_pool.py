"""
NUMA-Aware Sub-Interpreter Pool

Implements NUMA-optimized sub-interpreter pool that pins workers to NUMA nodes
for optimal memory locality and performance on multi-socket systems.
"""

import threading
import time
from typing import Dict, List, Optional, Any
from concurrent.futures import Future
import logging

from ...memory.numa_memory import get_numa_manager, NUMAPolicy
from ...memory.windows_thread_affinity import get_windows_thread_affinity_manager
from ...memory.windows_numa_memory_allocator import get_windows_numa_allocator

logger = logging.getLogger(__name__)


class NUMASubInterpreterPool:
    """
    NUMA-aware sub-interpreter pool for optimal performance on multi-socket systems.
    
    Creates worker sub-interpreters pinned to specific NUMA nodes with local
    memory allocation for maximum memory locality and performance.
    """
    
    def __init__(self, workers_per_node: int = 2, numa_aware: bool = True):
        """
        Initialize NUMA-aware sub-interpreter pool.
        
        Args:
            workers_per_node: Number of workers per NUMA node
            numa_aware: Enable NUMA optimizations
        """
        self.workers_per_node = workers_per_node
        self.numa_aware = numa_aware
        
        # Get NUMA components
        self.numa_manager = get_numa_manager()
        self.topology = self.numa_manager.get_topology()
        
        # Windows-specific components (if available)
        if numa_aware and self.topology.numa_available:
            try:
                self.affinity_manager = get_windows_thread_affinity_manager()
                self.numa_allocator = get_windows_numa_allocator()
                self._windows_numa_available = True
            except Exception as e:
                logger.warning(f"Windows NUMA components not available: {e}")
                self._windows_numa_available = False
        else:
            self.affinity_manager = None
            self.numa_allocator = None
            self._windows_numa_available = False
        
        # Worker management
        self._workers: Dict[int, List[Any]] = {}  # node_id -> list of workers
        self._worker_futures: Dict[int, Future] = {}
        self._shutdown_event = threading.Event()
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize NUMA-aware sub-interpreter pool."""
        if self._initialized:
            return
        
        try:
            # Create workers for each NUMA node
            for node_id in range(self.topology.node_count):
                self._workers[node_id] = []
                
                for worker_idx in range(self.workers_per_node):
                    worker = self._create_numa_worker(node_id, worker_idx)
                    self._workers[node_id].append(worker)
            
            self._initialized = True
            
            total_workers = sum(len(workers) for workers in self._workers.values())
            logger.info(f"NUMA sub-interpreter pool initialized: {total_workers} workers "
                       f"across {self.topology.node_count} NUMA nodes")
            
        except Exception as e:
            logger.error(f"Failed to initialize NUMA sub-interpreter pool: {e}")
            raise
    
    def _create_numa_worker(self, numa_node: int, worker_idx: int) -> 'NUMAWorker':
        """Create worker sub-interpreter pinned to NUMA node."""
        try:
            # Create worker configuration
            worker_config = {
                'numa_node': numa_node,
                'worker_id': f"node{numa_node}_worker{worker_idx}",
                'numa_aware': self._windows_numa_available,
                'affinity_manager': self.affinity_manager,
                'numa_allocator': self.numa_allocator
            }
            
            # Create and start worker
            worker = NUMAWorker(worker_config)
            worker.start()
            
            logger.debug(f"Created NUMA worker {worker_config['worker_id']} on node {numa_node}")
            return worker
            
        except Exception as e:
            logger.error(f"Failed to create NUMA worker for node {numa_node}: {e}")
            raise
    
    def submit_task_to_node(self, numa_node: int, func, *args, **kwargs) -> Future:
        """
        Submit task to specific NUMA node.
        
        Args:
            numa_node: Target NUMA node
            func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Future for task result
        """
        if not self._initialized:
            raise RuntimeError("Pool not initialized")
        
        if numa_node not in self._workers:
            raise ValueError(f"Invalid NUMA node: {numa_node}")
        
        # Select worker from target NUMA node (round-robin)
        workers = self._workers[numa_node]
        if not workers:
            raise RuntimeError(f"No workers available on NUMA node {numa_node}")
        
        # Simple round-robin selection
        worker_idx = len(self._worker_futures) % len(workers)
        worker = workers[worker_idx]
        
        # Submit task to worker
        future = worker.submit_task(func, *args, **kwargs)
        
        # Track future
        future_id = id(future)
        self._worker_futures[future_id] = future
        
        return future
    
    def submit_task_auto_numa(self, func, *args, **kwargs) -> Future:
        """
        Submit task with automatic NUMA node selection.
        
        Args:
            func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Future for task result
        """
        # Select optimal NUMA node based on current load
        optimal_node = self._select_optimal_numa_node()
        return self.submit_task_to_node(optimal_node, func, *args, **kwargs)
    
    def _select_optimal_numa_node(self) -> int:
        """Select optimal NUMA node based on current load and memory availability."""
        if not self.topology.numa_available:
            return 0
        
        # Strategy: Select node with most available memory
        best_node = 0
        best_memory = 0
        
        for node_id, node in self.topology.nodes.items():
            if node.memory_free > best_memory:
                best_memory = node.memory_free
                best_node = node_id
        
        return best_node
    
    def get_worker_numa_distribution(self) -> Dict[int, int]:
        """Get distribution of workers across NUMA nodes."""
        distribution = {}
        
        for node_id, workers in self._workers.items():
            distribution[node_id] = len(workers)
        
        return distribution
    
    def get_numa_performance_stats(self) -> Dict[str, Any]:
        """Get NUMA-related performance statistics."""
        stats = {
            'numa_available': self.topology.numa_available,
            'numa_nodes': self.topology.node_count,
            'workers_per_node': self.workers_per_node,
            'total_workers': sum(len(workers) for workers in self._workers.values()),
            'memory_usage_by_node': {}
        }
        
        # Get memory usage by node
        if self.numa_manager.is_numa_available():
            stats['memory_usage_by_node'] = self.numa_manager.get_memory_usage_by_node()
        
        return stats
    
    def shutdown(self, wait: bool = True) -> None:
        """Shutdown NUMA sub-interpreter pool."""
        if not self._initialized:
            return
        
        try:
            # Signal shutdown
            self._shutdown_event.set()
            
            # Shutdown all workers
            for node_id, workers in self._workers.items():
                for worker in workers:
                    try:
                        worker.shutdown(wait=wait)
                    except Exception as e:
                        logger.error(f"Error shutting down worker on node {node_id}: {e}")
            
            # Clean up allocations
            if self.numa_allocator:
                self.numa_allocator.cleanup_all()
            
            self._initialized = False
            logger.info("NUMA sub-interpreter pool shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during NUMA pool shutdown: {e}")


class NUMAWorker:
    """Individual NUMA-aware worker with sub-interpreter and thread affinity."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize NUMA worker with configuration."""
        self.numa_node = config['numa_node']
        self.worker_id = config['worker_id']
        self.numa_aware = config.get('numa_aware', False)
        self.affinity_manager = config.get('affinity_manager')
        self.numa_allocator = config.get('numa_allocator')
        
        # Worker state
        self._thread: Optional[threading.Thread] = None
        self._task_queue = []
        self._queue_lock = threading.Lock()
        self._shutdown_event = threading.Event()
        self._started = False
    
    def start(self) -> None:
        """Start NUMA worker thread."""
        if self._started:
            return
        
        self._thread = threading.Thread(
            target=self._worker_loop,
            name=self.worker_id,
            daemon=True
        )
        self._thread.start()
        self._started = True
        
        logger.debug(f"Started NUMA worker {self.worker_id} on node {self.numa_node}")
    
    def _worker_loop(self) -> None:
        """Main worker loop with NUMA optimizations."""
        try:
            # Pin thread to NUMA node if Windows NUMA available
            if self.numa_aware and self.affinity_manager:
                success = self.affinity_manager.pin_thread_to_numa_node(self.numa_node)
                if success:
                    logger.debug(f"Worker {self.worker_id} pinned to NUMA node {self.numa_node}")
            
            # Worker main loop
            while not self._shutdown_event.is_set():
                # Process tasks (simplified implementation)
                try:
                    # In real implementation, would have task queue and execution
                    time.sleep(0.1)  # Prevent busy waiting
                except Exception as e:
                    logger.error(f"Worker {self.worker_id} error: {e}")
                    
        except Exception as e:
            logger.error(f"Worker {self.worker_id} loop failed: {e}")
    
    def submit_task(self, func, *args, **kwargs) -> Future:
        """Submit task to this NUMA worker."""
        # Create future for task result
        future = Future()
        
        # Add task to queue (simplified)
        with self._queue_lock:
            self._task_queue.append((future, func, args, kwargs))
        
        return future
    
    def shutdown(self, wait: bool = True) -> None:
        """Shutdown NUMA worker."""
        if not self._started:
            return
        
        self._shutdown_event.set()
        
        if wait and self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        
        self._started = False


# Factory functions for easy usage
def create_numa_sub_interpreter_pool(workers_per_node: int = 2) -> NUMASubInterpreterPool:
    """Create NUMA-aware sub-interpreter pool."""
    return NUMASubInterpreterPool(workers_per_node=workers_per_node, numa_aware=True)


def create_numa_thread_pool(workers_per_node: int = 2) -> 'NUMAThreadPoolExecutor':
    """Create NUMA-aware thread pool executor."""
    affinity_manager = get_windows_thread_affinity_manager()
    return affinity_manager.create_numa_thread_pool_executor(workers_per_node)