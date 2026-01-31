"""
Epochly Memory Foundation - Hierarchical Lock Manager

This module provides centralized lock management with deadlock prevention
through strict lock ordering hierarchy. Eliminates lock inversion deadlocks
by enforcing proper lock acquisition order.

Author: Epochly Memory Foundation Team
Created: 2025-06-06
Updated: 2025-06-06 - Week 3 Concurrency Fixes
"""

import threading
import time
from contextlib import contextmanager
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from collections import defaultdict
from enum import IntEnum
import logging

logger = logging.getLogger(__name__)


class NullLock:
    """
    No-op lock for when locking is disabled.

    Provides a proper context manager interface without actual locking.
    This is used when the lock manager is disabled, replacing the
    previous unittest.mock.MagicMock usage which violated production code standards.
    """

    def __enter__(self):
        """Enter context - no-op"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - no-op"""
        return False  # Don't suppress exceptions

    def acquire(self, blocking=True, timeout=-1):
        """No-op acquire"""
        return True

    def release(self):
        """No-op release"""
        pass

    def locked(self):
        """Always returns False (no real lock)"""
        return False


class LockLevel(IntEnum):
    """
    Lock hierarchy levels - higher number = acquired first.
    
    This hierarchy prevents deadlocks by ensuring locks are always
    acquired in the same order across all threads.
    """
    GLOBAL = 100      # Global pool lock - highest priority
    BUCKET = 50       # Per-bucket locks - medium priority
    SLAB = 25         # Per-slab locks - lower priority
    COMPONENT = 10    # Component-specific locks - lowest priority


@dataclass
class LockInfo:
    """Information about a hierarchical lock."""
    level: LockLevel
    name: str
    lock: threading.RLock
    
    def __post_init__(self):
        """Validate lock info after initialization."""
        if not isinstance(self.level, LockLevel):
            raise ValueError(f"Invalid lock level: {self.level}")
        if not self.name:
            raise ValueError("Lock name cannot be empty")


@dataclass
class LockStatistics:
    """Statistics for lock usage and contention."""
    
    acquisition_count: int = 0
    total_wait_time: float = 0.0
    max_wait_time: float = 0.0
    contention_count: int = 0
    hold_time: float = 0.0
    max_hold_time: float = 0.0
    hierarchy_violations: int = 0
    
    @property
    def average_wait_time(self) -> float:
        """Calculate average wait time for lock acquisition."""
        if self.acquisition_count == 0:
            return 0.0
        return self.total_wait_time / self.acquisition_count
    
    @property
    def average_hold_time(self) -> float:
        """Calculate average time locks are held."""
        if self.acquisition_count == 0:
            return 0.0
        return self.hold_time / self.acquisition_count
    
    @property
    def contention_ratio(self) -> float:
        """Calculate ratio of contentious acquisitions."""
        if self.acquisition_count == 0:
            return 0.0
        return self.contention_count / self.acquisition_count


class LockContext:
    """Context manager for lock acquisition with statistics tracking."""
    
    def __init__(self, lock: threading.RLock, stats: LockStatistics, component: str):
        self.lock = lock
        self.stats = stats
        self.component = component
        self.start_time: Optional[float] = None
        self.acquire_time: Optional[float] = None
        self.acquired = False
    
    def __enter__(self):
        """Acquire lock and start timing."""
        self.start_time = time.perf_counter()
        
        # PERFORMANCE FIX: Add timeout to prevent infinite blocking
        timeout = 5.0  # 5 second timeout
        
        # Check if lock is already held (contention detection)
        if not self.lock.acquire(blocking=False):
            # Lock is contended
            self.stats.contention_count += 1
            logger.debug(f"Lock contention detected for {self.component}")
            
            # PERFORMANCE FIX: Use timeout instead of infinite blocking
            acquired = self.lock.acquire(blocking=True, timeout=timeout)
            if not acquired:
                raise RuntimeError(f"Lock acquisition timeout after {timeout}s for {self.component}")
        
        self.acquire_time = time.perf_counter()
        self.acquired = True
        
        # Record acquisition statistics
        wait_time = self.acquire_time - self.start_time
        self.stats.acquisition_count += 1
        self.stats.total_wait_time += wait_time
        self.stats.max_wait_time = max(self.stats.max_wait_time, wait_time)
        
        logger.debug(f"Acquired lock for {self.component} (wait: {wait_time:.6f}s)")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release lock and record hold time."""
        if self.acquired and self.acquire_time:
            release_time = time.perf_counter()
            hold_time = release_time - self.acquire_time
            
            self.stats.hold_time += hold_time
            self.stats.max_hold_time = max(self.stats.max_hold_time, hold_time)
            
            logger.debug(f"Released lock for {self.component} (held: {hold_time:.6f}s)")
            
            self.lock.release()
            self.acquired = False

class HierarchicalLockContext:
    """Context manager for hierarchical lock acquisition with deadlock prevention."""
    
    def __init__(self, lock_info: LockInfo, stats: LockStatistics, manager: 'HierarchicalLockManager'):
        self.lock_info = lock_info
        self.stats = stats
        self.manager = manager
        self.start_time: Optional[float] = None
        self.acquire_time: Optional[float] = None
        self.acquired = False
        # Handle case where thread.ident might be None
        thread_ident = threading.current_thread().ident
        if thread_ident is None:
            raise RuntimeError("Cannot acquire hierarchical lock: thread has no identifier")
        self.thread_id = thread_ident
    
    def __enter__(self):
        """Acquire lock with hierarchy enforcement and timing."""
        self.start_time = time.perf_counter()
        
        # Check lock ordering to prevent deadlocks
        self._validate_lock_hierarchy()
        
        # Check if lock is already held (contention detection)
        if not self.lock_info.lock.acquire(blocking=False):
            # Lock is contended
            self.stats.contention_count += 1
            logger.debug(f"Lock contention detected for {self.lock_info.name}")
            self.lock_info.lock.acquire(blocking=True)
        
        self.acquire_time = time.perf_counter()
        self.acquired = True
        
        # Track acquired lock in manager
        self.manager._track_acquired_lock(self.thread_id, self.lock_info)
        
        # Record acquisition statistics
        wait_time = self.acquire_time - self.start_time
        self.stats.acquisition_count += 1
        self.stats.total_wait_time += wait_time
        self.stats.max_wait_time = max(self.stats.max_wait_time, wait_time)
        
        logger.debug(f"Acquired hierarchical lock {self.lock_info.name} "
                    f"(level {self.lock_info.level}, wait: {wait_time:.6f}s)")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release lock and record hold time."""
        if self.acquired and self.acquire_time:
            release_time = time.perf_counter()
            hold_time = release_time - self.acquire_time
            
            self.stats.hold_time += hold_time
            self.stats.max_hold_time = max(self.stats.max_hold_time, hold_time)
            
            # Untrack lock in manager
            self.manager._untrack_acquired_lock(self.thread_id, self.lock_info)
            
            logger.debug(f"Released hierarchical lock {self.lock_info.name} "
                        f"(held: {hold_time:.6f}s)")
            
            self.lock_info.lock.release()
            self.acquired = False
    
    def _validate_lock_hierarchy(self):
        """Validate that lock acquisition follows hierarchy rules."""
        held_locks = self.manager._get_thread_locks(self.thread_id)
        
        for held_lock in held_locks:
            if held_lock.level < self.lock_info.level:
                self.stats.hierarchy_violations += 1
                error_msg = (
                    f"Lock hierarchy violation: thread {self.thread_id} "
                    f"holding {held_lock.name} (level {held_lock.level}), "
                    f"trying to acquire {self.lock_info.name} (level {self.lock_info.level}). "
                    f"Higher level locks must be acquired first."
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)


class HierarchicalLockManager:
    """
    Lock manager that enforces strict ordering to prevent deadlocks.
    
    Provides centralized lock management with hierarchy enforcement,
    deadlock prevention, and comprehensive statistics tracking.
    """
    
    def __init__(self):
        """Initialize the hierarchical lock manager."""
        self._locks: Dict[str, LockInfo] = {}
        self._stats: Dict[str, LockStatistics] = defaultdict(LockStatistics)
        self._thread_locks: Dict[int, List[LockInfo]] = {}
        self._manager_lock = threading.RLock()
        self._enabled = True
        
        logger.info("Hierarchical lock manager initialized")
    
    def register_lock(self, name: str, level: LockLevel) -> threading.RLock:
        """
        Register a new lock with hierarchy level.
        
        Args:
            name: Unique name for the lock
            level: Hierarchy level for deadlock prevention
            
        Returns:
            The RLock instance for the registered lock
            
        Raises:
            ValueError: If lock name already exists or level is invalid
        """
        with self._manager_lock:
            if name in self._locks:
                return self._locks[name].lock
                
            lock = threading.RLock()
            lock_info = LockInfo(level, name, lock)
            self._locks[name] = lock_info
            self._stats[name] = LockStatistics()
            
            logger.debug(f"Registered hierarchical lock: {name} (level {level})")
            return lock
    
    def unregister_lock(self, name: str) -> None:
        """
        Unregister a lock from hierarchy management.
        
        Args:
            name: Name of the lock to unregister
        """
        with self._manager_lock:
            if name in self._locks:
                lock_info = self._locks[name]
                
                # Ensure lock is not held before removing
                try:
                    if lock_info.lock.acquire(blocking=False):
                        lock_info.lock.release()
                        del self._locks[name]
                        del self._stats[name]
                        logger.debug(f"Unregistered hierarchical lock: {name}")
                    else:
                        logger.warning(f"Cannot unregister {name}: lock is held")
                except Exception as e:
                    logger.error(f"Error unregistering {name}: {e}")
    
    @contextmanager
    def acquire(self, name: str):
        """
        Acquire a lock with hierarchy enforcement.
        
        Args:
            name: Name of the lock to acquire
            
        Yields:
            HierarchicalLockContext: Context manager for the lock
            
        Raises:
            ValueError: If lock is not registered
            RuntimeError: If lock hierarchy would be violated
        """
        if not self._enabled:
            # If disabled, provide a no-op context manager
            null_lock = NullLock()
            yield null_lock
            return
        
        with self._manager_lock:
            if name not in self._locks:
                raise ValueError(f"Lock {name} not registered")
            
            lock_info = self._locks[name]
            stats = self._stats[name]
        
        with HierarchicalLockContext(lock_info, stats, self) as context:
            yield context
    
    def _track_acquired_lock(self, thread_id: int, lock_info: LockInfo) -> None:
        """Track a lock acquired by a thread."""
        with self._manager_lock:
            if thread_id not in self._thread_locks:
                self._thread_locks[thread_id] = []
            self._thread_locks[thread_id].append(lock_info)
    
    def _untrack_acquired_lock(self, thread_id: int, lock_info: LockInfo) -> None:
        """Untrack a lock released by a thread."""
        with self._manager_lock:
            if thread_id in self._thread_locks:
                try:
                    self._thread_locks[thread_id].remove(lock_info)
                    if not self._thread_locks[thread_id]:
                        del self._thread_locks[thread_id]
                except ValueError:
                    logger.warning(f"Lock {lock_info.name} not found in thread {thread_id} tracking")
    
    def _get_thread_locks(self, thread_id: int) -> List[LockInfo]:
        """Get locks currently held by a thread."""
        with self._manager_lock:
            return self._thread_locks.get(thread_id, []).copy()
    
    def get_statistics(self, lock_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get lock statistics for a specific lock or all locks.
        
        Args:
            lock_name: Specific lock name, or None for all locks
            
        Returns:
            Dictionary containing lock statistics
        """
        with self._manager_lock:
            if lock_name:
                if lock_name not in self._stats:
                    return {}
                
                stats = self._stats[lock_name]
                lock_info = self._locks[lock_name]
                return {
                    'lock_name': lock_name,
                    'level': lock_info.level.name,
                    'acquisition_count': stats.acquisition_count,
                    'total_wait_time': stats.total_wait_time,
                    'average_wait_time': stats.average_wait_time,
                    'max_wait_time': stats.max_wait_time,
                    'contention_count': stats.contention_count,
                    'contention_ratio': stats.contention_ratio,
                    'total_hold_time': stats.hold_time,
                    'average_hold_time': stats.average_hold_time,
                    'max_hold_time': stats.max_hold_time,
                    'hierarchy_violations': stats.hierarchy_violations
                }
            else:
                # Return statistics for all locks
                result = {}
                for name, stats in self._stats.items():
                    lock_info = self._locks[name]
                    result[name] = {
                        'level': lock_info.level.name,
                        'acquisition_count': stats.acquisition_count,
                        'total_wait_time': stats.total_wait_time,
                        'average_wait_time': stats.average_wait_time,
                        'max_wait_time': stats.max_wait_time,
                        'contention_count': stats.contention_count,
                        'contention_ratio': stats.contention_ratio,
                        'total_hold_time': stats.hold_time,
                        'average_hold_time': stats.average_hold_time,
                        'max_hold_time': stats.max_hold_time,
                        'hierarchy_violations': stats.hierarchy_violations
                    }
                return result
    
    def get_hierarchy_summary(self) -> Dict[str, Any]:
        """
        Get a summary of lock hierarchy and violations.
        
        Returns:
            Dictionary with hierarchy analysis
        """
        with self._manager_lock:
            total_violations = sum(stats.hierarchy_violations for stats in self._stats.values())
            total_acquisitions = sum(stats.acquisition_count for stats in self._stats.values())
            
            # Group locks by level
            locks_by_level = defaultdict(list)
            for name, lock_info in self._locks.items():
                locks_by_level[lock_info.level.name].append(name)
            
            # Find most problematic lock
            most_violations = 0
            most_problematic_lock = None
            for name, stats in self._stats.items():
                if stats.hierarchy_violations > most_violations:
                    most_violations = stats.hierarchy_violations
                    most_problematic_lock = name
            
            return {
                'total_hierarchy_violations': total_violations,
                'total_acquisitions': total_acquisitions,
                'violation_ratio': total_violations / total_acquisitions if total_acquisitions > 0 else 0.0,
                'locks_by_level': dict(locks_by_level),
                'most_problematic_lock': most_problematic_lock,
                'most_violations': most_violations,
                'active_threads': len(self._thread_locks),
                'registered_locks': list(self._locks.keys())
            }
    
    def reset_statistics(self, lock_name: Optional[str] = None) -> None:
        """
        Reset lock statistics for a specific lock or all locks.
        
        Args:
            lock_name: Specific lock name, or None for all locks
        """
        with self._manager_lock:
            if lock_name:
                if lock_name in self._stats:
                    self._stats[lock_name] = LockStatistics()
                    logger.debug(f"Reset statistics for hierarchical lock {lock_name}")
            else:
                for name in self._stats:
                    self._stats[name] = LockStatistics()
                logger.debug("Reset statistics for all hierarchical locks")
    
    def enable(self) -> None:
        """Enable hierarchical lock management."""
        self._enabled = True
        logger.info("Hierarchical lock manager enabled")
    
    def disable(self) -> None:
        """Disable hierarchical lock management (for testing/debugging)."""
        self._enabled = False
        logger.info("Hierarchical lock manager disabled")
    
    @property
    def is_enabled(self) -> bool:
        """Check if hierarchical lock manager is enabled."""
        return self._enabled
    
    def cleanup(self) -> None:
        """Clean up hierarchical lock manager resources."""
        with self._manager_lock:
            # Clear all locks and statistics
            self._locks.clear()
            self._stats.clear()
            self._thread_locks.clear()
            logger.info("Hierarchical lock manager cleaned up")

class LockManager:
    """
    Unified lock manager for memory foundation components.
    
    Provides centralized lock management with statistics tracking,
    contention monitoring, and performance analysis.
    """
    
    def __init__(self):
        """Initialize the lock manager."""
        self._locks: Dict[str, threading.RLock] = {}
        self._stats: Dict[str, LockStatistics] = defaultdict(LockStatistics)
        self._manager_lock = threading.RLock()
        self._enabled = True
        
        logger.info("Unified lock manager initialized")
    
    def register_component(self, component: str) -> None:
        """
        Register a component for lock management.
        
        Args:
            component: Name of the component to register
        """
        with self._manager_lock:
            if component not in self._locks:
                self._locks[component] = threading.RLock()
                self._stats[component] = LockStatistics()
                logger.debug(f"Registered component: {component}")
    
    def unregister_component(self, component: str) -> None:
        """
        Unregister a component from lock management.
        
        Args:
            component: Name of the component to unregister
        """
        with self._manager_lock:
            if component in self._locks:
                # Ensure lock is not held before removing
                lock = self._locks[component]
                try:
                    if lock.acquire(blocking=False):
                        lock.release()
                        del self._locks[component]
                        del self._stats[component]
                        logger.debug(f"Unregistered component: {component}")
                    else:
                        logger.warning(f"Cannot unregister {component}: lock is held")
                except Exception as e:
                    logger.error(f"Error unregistering {component}: {e}")
    
    @contextmanager
    def acquire(self, component: str):
        """
        Acquire a lock for the specified component.
        
        Args:
            component: Name of the component requesting the lock
            
        Yields:
            LockContext: Context manager for the lock
            
        Raises:
            ValueError: If component is not registered
        """
        if not self._enabled:
            # If disabled, provide a no-op context manager
            yield LockContext(threading.RLock(), LockStatistics(), component)
            return
        
        with self._manager_lock:
            if component not in self._locks:
                self.register_component(component)
        
        lock = self._locks[component]
        stats = self._stats[component]
        
        with LockContext(lock, stats, component) as context:
            yield context
    
    def get_statistics(self, component: Optional[str] = None) -> Dict[str, Any]:
        """
        Get lock statistics for a component or all components.
        
        Args:
            component: Specific component name, or None for all components
            
        Returns:
            Dictionary containing lock statistics
        """
        with self._manager_lock:
            if component:
                if component not in self._stats:
                    return {}
                
                stats = self._stats[component]
                return {
                    'component': component,
                    'acquisition_count': stats.acquisition_count,
                    'total_wait_time': stats.total_wait_time,
                    'average_wait_time': stats.average_wait_time,
                    'max_wait_time': stats.max_wait_time,
                    'contention_count': stats.contention_count,
                    'contention_ratio': stats.contention_ratio,
                    'total_hold_time': stats.hold_time,
                    'average_hold_time': stats.average_hold_time,
                    'max_hold_time': stats.max_hold_time
                }
            else:
                # Return statistics for all components
                result = {}
                for comp_name, stats in self._stats.items():
                    result[comp_name] = {
                        'acquisition_count': stats.acquisition_count,
                        'total_wait_time': stats.total_wait_time,
                        'average_wait_time': stats.average_wait_time,
                        'max_wait_time': stats.max_wait_time,
                        'contention_count': stats.contention_count,
                        'contention_ratio': stats.contention_ratio,
                        'total_hold_time': stats.hold_time,
                        'average_hold_time': stats.average_hold_time,
                        'max_hold_time': stats.max_hold_time
                    }
                return result
    
    def get_contention_summary(self) -> Dict[str, Any]:
        """
        Get a summary of lock contention across all components.
        
        Returns:
            Dictionary with contention analysis
        """
        with self._manager_lock:
            total_acquisitions = sum(stats.acquisition_count for stats in self._stats.values())
            total_contentions = sum(stats.contention_count for stats in self._stats.values())
            total_wait_time = sum(stats.total_wait_time for stats in self._stats.values())
            
            # Find most contentious component
            most_contentious = None
            highest_contention_ratio = 0.0
            
            for component, stats in self._stats.items():
                if stats.contention_ratio > highest_contention_ratio:
                    highest_contention_ratio = stats.contention_ratio
                    most_contentious = component
            
            return {
                'total_acquisitions': total_acquisitions,
                'total_contentions': total_contentions,
                'overall_contention_ratio': total_contentions / total_acquisitions if total_acquisitions > 0 else 0.0,
                'total_wait_time': total_wait_time,
                'average_wait_time': total_wait_time / total_acquisitions if total_acquisitions > 0 else 0.0,
                'most_contentious_component': most_contentious,
                'highest_contention_ratio': highest_contention_ratio,
                'registered_components': list(self._locks.keys())
            }
    
    def reset_statistics(self, component: Optional[str] = None) -> None:
        """
        Reset lock statistics for a component or all components.
        
        Args:
            component: Specific component name, or None for all components
        """
        with self._manager_lock:
            if component:
                if component in self._stats:
                    self._stats[component] = LockStatistics()
                    logger.debug(f"Reset statistics for {component}")
            else:
                for comp_name in self._stats:
                    self._stats[comp_name] = LockStatistics()
                logger.debug("Reset statistics for all components")
    
    def enable(self) -> None:
        """Enable lock management."""
        self._enabled = True
        logger.info("Lock manager enabled")
    
    def disable(self) -> None:
        """Disable lock management (for testing/debugging)."""
        self._enabled = False
        logger.info("Lock manager disabled")
    
    @property
    def is_enabled(self) -> bool:
        """Check if lock manager is enabled."""
        return self._enabled
    
    def cleanup(self) -> None:
        """Clean up lock manager resources."""
        with self._manager_lock:
            # Clear all locks and statistics
            self._locks.clear()
            self._stats.clear()
            logger.info("Lock manager cleaned up")


# Global lock manager instance
_global_lock_manager: Optional[LockManager] = None


def get_lock_manager() -> LockManager:
    """
    Get the global lock manager instance.
    
    Returns:
        Global LockManager instance
    """
    global _global_lock_manager
    if _global_lock_manager is None:
        _global_lock_manager = LockManager()
    return _global_lock_manager


def reset_lock_manager() -> None:
    """Reset the global lock manager (for testing)."""
    global _global_lock_manager
    if _global_lock_manager:
        _global_lock_manager.cleanup()
    _global_lock_manager = None
# Global hierarchical lock manager instance
_global_hierarchical_lock_manager: Optional[HierarchicalLockManager] = None


def get_hierarchical_lock_manager() -> HierarchicalLockManager:
    """
    Get the global hierarchical lock manager instance.
    
    Returns:
        Global HierarchicalLockManager instance
    """
    global _global_hierarchical_lock_manager
    if _global_hierarchical_lock_manager is None:
        _global_hierarchical_lock_manager = HierarchicalLockManager()
    return _global_hierarchical_lock_manager


def reset_hierarchical_lock_manager() -> None:
    """Reset the global hierarchical lock manager (for testing)."""
    global _global_hierarchical_lock_manager
    if _global_hierarchical_lock_manager:
        _global_hierarchical_lock_manager.cleanup()
    _global_hierarchical_lock_manager = None


# Convenience functions for per-bucket locks
def register_bucket_lock(bucket_id: str) -> threading.RLock:
    """
    Register a per-bucket lock with proper hierarchy level.
    
    Args:
        bucket_id: Unique identifier for the bucket
        
    Returns:
        The RLock instance for the bucket
    """
    manager = get_hierarchical_lock_manager()
    lock_name = f"bucket_{bucket_id}"
    return manager.register_lock(lock_name, LockLevel.BUCKET)


def acquire_bucket_lock(bucket_id: str):
    """
    Acquire a per-bucket lock with hierarchy enforcement.
    
    Args:
        bucket_id: Unique identifier for the bucket
        
    Returns:
        Context manager for the bucket lock
    """
    manager = get_hierarchical_lock_manager()
    lock_name = f"bucket_{bucket_id}"
    return manager.acquire(lock_name)


def register_slab_lock(slab_id: str) -> threading.RLock:
    """
    Register a per-slab lock with proper hierarchy level.
    
    Args:
        slab_id: Unique identifier for the slab
        
    Returns:
        The RLock instance for the slab
    """
    manager = get_hierarchical_lock_manager()
    lock_name = f"slab_{slab_id}"
    return manager.register_lock(lock_name, LockLevel.SLAB)


def acquire_slab_lock(slab_id: str):
    """
    Acquire a per-slab lock with hierarchy enforcement.
    
    Args:
        slab_id: Unique identifier for the slab
        
    Returns:
        Context manager for the slab lock
    """
    manager = get_hierarchical_lock_manager()
    lock_name = f"slab_{slab_id}"
    return manager.acquire(lock_name)


def register_global_lock(lock_name: str) -> threading.RLock:
    """
    Register a global lock with highest hierarchy level.
    
    Args:
        lock_name: Unique name for the global lock
        
    Returns:
        The RLock instance for the global lock
    """
    manager = get_hierarchical_lock_manager()
    return manager.register_lock(lock_name, LockLevel.GLOBAL)


def acquire_global_lock(lock_name: str):
    """
    Acquire a global lock with hierarchy enforcement.
    
    Args:
        lock_name: Name of the global lock
        
    Returns:
        Context manager for the global lock
    """
    manager = get_hierarchical_lock_manager()
    return manager.acquire(lock_name)