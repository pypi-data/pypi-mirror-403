"""
Epochly Memory Foundation - Remote Deallocation Infrastructure

This module implements lock-free remote deallocation queues to eliminate race conditions
in cross-thread memory deallocation scenarios. Based on ULTRATHINK analysis recommendations.

Key Features:
- Lock-free Treiber stack for remote deallocation requests
- Reference counting and epoch-based lifetime management
- O(1) remote deallocation with no global locks
- Batch draining for optimal performance

Author: Epochly Memory Foundation Team
Created: 2025-06-07
Updated: 2025-06-07 - Race condition remediation implementation
"""

import threading
import time
from typing import Optional, List, Callable
from dataclasses import dataclass

from .atomic_primitives import AtomicCounter, LockFreeStack
import logging

logger = logging.getLogger(__name__)


@dataclass
class RemoteFreeNode:
    """Node for remote deallocation queue."""
    offset: int
    size: int = 0  # Optional size tracking for metrics
    timestamp: float = 0.0  # For debugging and metrics
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class RemoteDeallocationQueue:
    """
    Lock-free queue for cross-thread deallocation requests.
    
    Uses Treiber stack algorithm for O(1) push/pop operations without locks.
    Provides batch draining capabilities for optimal performance.
    """
    
    def __init__(self, owner_name: str = "Unknown"):
        """
        Initialize remote deallocation queue.
        
        Args:
            owner_name: Name of the owning pool for debugging
        """
        self.owner_name = owner_name
        # Note: LockFreeStack is a Cython class that doesn't support generic subscript
        self._queue = LockFreeStack()
        
        # Metrics
        self.total_pushes = AtomicCounter()
        self.total_pops = AtomicCounter()
        self.batch_drains = AtomicCounter()
        self.max_queue_depth = AtomicCounter()
        
        # Performance tracking
        self._last_drain_time = time.time()
        
    def push_remote_free(self, offset: int, size: int = 0) -> None:
        """
        Push a remote deallocation request onto the queue.
        
        This is called by foreign threads to request deallocation.
        O(1) operation with no locks.
        
        Args:
            offset: Local offset to deallocate
            size: Size of allocation (optional, for metrics)
        """
        node = RemoteFreeNode(offset=offset, size=size)
        self._queue.push(node)
        
        # Update metrics
        self.total_pushes.increment()
        current_size = self._queue.size()
        
        # Update max depth if needed
        while True:
            current_max = self.max_queue_depth.load()
            if current_size <= current_max:
                break
            if self.max_queue_depth.compare_and_swap(current_max, current_size):
                break
        
        logger.debug(f"RemoteQueue {self.owner_name}: pushed offset {offset}, queue size: {current_size}")
    
    def drain_batch(self, max_items: int = 128, 
                   deallocate_func: Optional[Callable[[int], None]] = None) -> List[RemoteFreeNode]:
        """
        Drain a batch of remote deallocation requests.
        
        This is called by the owner thread to process pending deallocations.
        Processes up to max_items in a single batch for efficiency.
        
        Args:
            max_items: Maximum number of items to drain in one batch
            deallocate_func: Optional function to call for each deallocation
            
        Returns:
            List of drained nodes
        """
        drained_nodes = []
        items_processed = 0
        
        while items_processed < max_items:
            node = self._queue.pop()
            if node is None:
                break  # Queue is empty
            
            drained_nodes.append(node)
            items_processed += 1
            
            # Call deallocation function if provided
            if deallocate_func:
                try:
                    deallocate_func(node.offset)
                except Exception as e:
                    logger.error(f"RemoteQueue {self.owner_name}: deallocation error for offset {node.offset}: {e}")
            
            self.total_pops.increment()
        
        if items_processed > 0:
            self.batch_drains.increment()
            self._last_drain_time = time.time()
            logger.debug(f"RemoteQueue {self.owner_name}: drained {items_processed} items")
        
        return drained_nodes
    
    def force_drain_all(self, deallocate_func: Optional[Callable[[int], None]] = None) -> int:
        """
        Force drain all pending items (used during shutdown).
        
        Args:
            deallocate_func: Function to call for each deallocation
            
        Returns:
            Number of items drained
        """
        total_drained = 0
        
        while True:
            batch = self.drain_batch(max_items=256, deallocate_func=deallocate_func)
            if not batch:
                break
            total_drained += len(batch)
        
        logger.info(f"RemoteQueue {self.owner_name}: force drained {total_drained} items")
        return total_drained
    
    def get_queue_depth(self) -> int:
        """Get current queue depth."""
        return self._queue.size()
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.is_empty()
    
    def should_drain(self, threshold: int = 32, time_threshold: float = 0.1) -> bool:
        """
        Check if queue should be drained based on heuristics.
        
        Args:
            threshold: Queue depth threshold for immediate draining
            time_threshold: Time threshold in seconds since last drain
            
        Returns:
            True if queue should be drained
        """
        current_depth = self.get_queue_depth()
        time_since_drain = time.time() - self._last_drain_time
        
        return (current_depth >= threshold or 
                (current_depth > 0 and time_since_drain >= time_threshold))
    
    def get_statistics(self) -> dict:
        """Get queue statistics."""
        return {
            'owner_name': self.owner_name,
            'current_depth': self.get_queue_depth(),
            'total_pushes': self.total_pushes.load(),
            'total_pops': self.total_pops.load(),
            'batch_drains': self.batch_drains.load(),
            'max_queue_depth': self.max_queue_depth.load(),
            'time_since_last_drain': time.time() - self._last_drain_time,
            'is_empty': self.is_empty()
        }


class PoolLifetimeManager:
    """
    Manages pool lifetime with reference counting and epoch-based safety.
    
    Ensures that pools are not destroyed while remote operations are in flight.
    Implements the epoch-based lifetime management from the ULTRATHINK analysis.
    """
    
    def __init__(self, pool_id: str):
        """
        Initialize lifetime manager.
        
        Args:
            pool_id: Unique identifier for the pool
        """
        self.pool_id = pool_id
        self.active_remote_ops = AtomicCounter()
        self.is_shutting_down = False
        self.shutdown_lock = threading.Lock()
        self.destruction_callbacks: List[Callable[[], None]] = []
        
    def begin_remote_operation(self) -> bool:
        """
        Begin a remote operation (increment reference count).
        
        Returns:
            True if operation can proceed, False if pool is shutting down
        """
        with self.shutdown_lock:
            if self.is_shutting_down:
                return False
            self.active_remote_ops.increment()
            return True
    
    def end_remote_operation(self) -> None:
        """End a remote operation (decrement reference count)."""
        self.active_remote_ops.decrement()
    
    def add_destruction_callback(self, callback: Callable[[], None]) -> None:
        """Add callback to be called during destruction."""
        self.destruction_callbacks.append(callback)
    
    def initiate_shutdown(self, timeout: float = 5.0) -> bool:
        """
        Initiate shutdown and wait for all remote operations to complete.
        
        Args:
            timeout: Maximum time to wait for operations to complete
            
        Returns:
            True if shutdown completed successfully
        """
        with self.shutdown_lock:
            if self.is_shutting_down:
                return True
            
            self.is_shutting_down = True
            logger.info(f"PoolLifetimeManager {self.pool_id}: initiating shutdown")
        
        # Wait for active operations to complete
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.active_remote_ops.load() == 0:
                logger.info(f"PoolLifetimeManager {self.pool_id}: all remote operations completed")
                
                # Call destruction callbacks
                for callback in self.destruction_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        logger.error(f"PoolLifetimeManager {self.pool_id}: destruction callback error: {e}")
                
                return True
            
            time.sleep(0.001)  # 1ms sleep
        
        # Timeout reached
        remaining_ops = self.active_remote_ops.load()
        logger.warning(f"PoolLifetimeManager {self.pool_id}: shutdown timeout, {remaining_ops} operations still active")
        return False
    
    def get_statistics(self) -> dict:
        """Get lifetime manager statistics."""
        return {
            'pool_id': self.pool_id,
            'active_remote_ops': self.active_remote_ops.load(),
            'is_shutting_down': self.is_shutting_down,
            'destruction_callbacks': len(self.destruction_callbacks)
        }


class RemoteDeallocationContext:
    """
    Context manager for safe remote operations with automatic cleanup.
    
    Ensures proper reference counting and cleanup even if exceptions occur.
    """
    
    def __init__(self, lifetime_manager: PoolLifetimeManager):
        """
        Initialize context manager.
        
        Args:
            lifetime_manager: Pool lifetime manager
        """
        self.lifetime_manager = lifetime_manager
        self.operation_started = False
    
    def __enter__(self) -> bool:
        """
        Enter context and begin remote operation.
        
        Returns:
            True if operation can proceed
        """
        self.operation_started = self.lifetime_manager.begin_remote_operation()
        return self.operation_started
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and end remote operation."""
        if self.operation_started:
            self.lifetime_manager.end_remote_operation()