"""
Allocator-aware memory metrics for Epochly memory subsystem.

This module provides accurate memory tracking that accounts for Python's
memory allocator behavior and mmap-based allocations.
"""

import os
import gc
import psutil
import tracemalloc
from typing import Dict, Tuple, Any
from dataclasses import dataclass


@dataclass
class MemoryMetrics:
    """Comprehensive memory metrics including allocator-aware tracking."""
    # Process-level metrics
    rss_bytes: int = 0  # Resident Set Size
    vms_bytes: int = 0  # Virtual Memory Size
    uss_bytes: int = 0  # Unique Set Size (Linux only)
    pss_bytes: int = 0  # Proportional Set Size (Linux only)
    
    # Python allocator metrics
    python_allocated: int = 0  # Total bytes allocated by Python
    python_objects: int = 0    # Number of Python objects
    
    # Memory pool metrics
    pool_allocated: int = 0    # Bytes allocated from pools
    pool_used: int = 0         # Bytes actually in use
    pool_overhead: int = 0     # Overhead for management structures
    
    # mmap metrics
    mmap_allocated: int = 0    # Total mmap allocations
    mmap_resident: int = 0     # mmap pages in memory
    mmap_returned: int = 0     # Pages returned via madvise
    
    def to_mb(self) -> Dict[str, float]:
        """Convert all metrics to MB for readability."""
        return {
            'rss_mb': self.rss_bytes / 1024 / 1024,
            'vms_mb': self.vms_bytes / 1024 / 1024,
            'uss_mb': self.uss_bytes / 1024 / 1024,
            'pss_mb': self.pss_bytes / 1024 / 1024,
            'python_allocated_mb': self.python_allocated / 1024 / 1024,
            'python_objects': self.python_objects,
            'pool_allocated_mb': self.pool_allocated / 1024 / 1024,
            'pool_used_mb': self.pool_used / 1024 / 1024,
            'pool_overhead_mb': self.pool_overhead / 1024 / 1024,
            'mmap_allocated_mb': self.mmap_allocated / 1024 / 1024,
            'mmap_resident_mb': self.mmap_resident / 1024 / 1024,
            'mmap_returned_mb': self.mmap_returned / 1024 / 1024,
        }


class AllocatorMetricsCollector:
    """Collects allocator-aware memory metrics."""
    
    def __init__(self):
        """Initialize the metrics collector."""
        self.process = psutil.Process(os.getpid())
        self._tracemalloc_started = False
        
        # Start tracemalloc if not already running
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            self._tracemalloc_started = True
    
    def collect_metrics(self, pool=None) -> MemoryMetrics:
        """
        Collect comprehensive memory metrics.
        
        Args:
            pool: Optional memory pool to collect metrics from
            
        Returns:
            MemoryMetrics object with current measurements
        """
        metrics = MemoryMetrics()
        
        # Collect process-level metrics
        mem_info = self.process.memory_info()
        metrics.rss_bytes = mem_info.rss
        metrics.vms_bytes = mem_info.vms
        
        # Collect USS/PSS on Linux
        if hasattr(self.process, "memory_full_info"):
            try:
                full_info = self.process.memory_full_info()
                metrics.uss_bytes = full_info.uss
                metrics.pss_bytes = getattr(full_info, 'pss', 0)
            except (AttributeError, OSError):
                pass  # Not available on this platform
        
        # Collect Python allocator metrics
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            metrics.python_allocated = current
        
        # Count Python objects (skip in tests for performance)
        if os.environ.get('EPOCHLY_TEST_MODE') != '1':
            gc.collect()  # Ensure accurate count
            metrics.python_objects = len(gc.get_objects())
        else:
            metrics.python_objects = 0  # Skip expensive operation in tests
        
        # Collect pool-specific metrics if provided
        if pool:
            self._collect_pool_metrics(pool, metrics)
        
        return metrics
    
    def _collect_pool_metrics(self, pool: Any, metrics: MemoryMetrics) -> None:
        """Collect metrics from a memory pool."""
        # Get pool statistics
        if hasattr(pool, 'get_statistics'):
            stats = pool.get_statistics()
            metrics.pool_allocated = stats.get('total_size', 0)
            metrics.pool_used = stats.get('used', 0)
            metrics.pool_overhead = metrics.pool_allocated - metrics.pool_used
        
        # Get mmap-specific metrics if available
        if hasattr(pool, '_backing_pool'):
            backing = pool._backing_pool
            if hasattr(backing, 'get_mmap_stats'):
                mmap_stats = backing.get_mmap_stats()
                metrics.mmap_allocated = mmap_stats.get('total_allocated', 0)
                metrics.mmap_resident = mmap_stats.get('resident_pages', 0) * 4096  # Assume 4KB pages
                metrics.mmap_returned = mmap_stats.get('returned_pages', 0) * 4096
            elif hasattr(backing, '_mmap') and backing._mmap:
                # Basic mmap info
                metrics.mmap_allocated = len(backing._mmap)
    
    def compare_metrics(self, before: MemoryMetrics, after: MemoryMetrics) -> Dict[str, float]:
        """
        Compare two metric snapshots and return the differences.
        
        Returns:
            Dictionary of metric differences in MB
        """
        return {
            'rss_growth_mb': (after.rss_bytes - before.rss_bytes) / 1024 / 1024,
            'vms_growth_mb': (after.vms_bytes - before.vms_bytes) / 1024 / 1024,
            'uss_growth_mb': (after.uss_bytes - before.uss_bytes) / 1024 / 1024,
            'pss_growth_mb': (after.pss_bytes - before.pss_bytes) / 1024 / 1024,
            'python_allocated_growth_mb': (after.python_allocated - before.python_allocated) / 1024 / 1024,
            'python_objects_growth': after.python_objects - before.python_objects,
            'pool_used_growth_mb': (after.pool_used - before.pool_used) / 1024 / 1024,
            'mmap_resident_growth_mb': (after.mmap_resident - before.mmap_resident) / 1024 / 1024,
        }
    
    def get_tracemalloc_top(self, limit: int = 10) -> list:
        """Get top memory allocations from tracemalloc."""
        if not tracemalloc.is_tracing():
            return []
        
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('traceback')
        
        results = []
        for index, stat in enumerate(top_stats[:limit], 1):
            frame = stat.traceback[0]
            results.append({
                'size_mb': stat.size / 1024 / 1024,
                'count': stat.count,
                'average': stat.size / stat.count if stat.count > 0 else 0,
                'file': frame.filename,
                'line': frame.lineno
            })
        
        return results
    
    def check_memory_leak(self, 
                         before: MemoryMetrics, 
                         after: MemoryMetrics,
                         threshold_mb: float = 5.0) -> Tuple[bool, str]:
        """
        Check if memory leak occurred between two measurements.
        
        Args:
            before: Metrics before operation
            after: Metrics after operation
            threshold_mb: Maximum allowed growth in MB
            
        Returns:
            Tuple of (has_leak, explanation)
        """
        diffs = self.compare_metrics(before, after)
        
        # Check various leak indicators
        issues = []
        
        # Check RSS growth
        if diffs['rss_growth_mb'] > threshold_mb:
            issues.append(f"RSS grew by {diffs['rss_growth_mb']:.2f} MB")
        
        # Check Python allocator
        if diffs['python_allocated_growth_mb'] > threshold_mb / 2:
            issues.append(f"Python allocated {diffs['python_allocated_growth_mb']:.2f} MB")
        
        # Check object proliferation
        if diffs['python_objects_growth'] > 10000:
            issues.append(f"Created {diffs['python_objects_growth']} new objects")
        
        # Check USS growth (more accurate than RSS)
        if diffs['uss_growth_mb'] > threshold_mb and diffs['uss_growth_mb'] > 0:
            issues.append(f"USS grew by {diffs['uss_growth_mb']:.2f} MB")
        
        has_leak = len(issues) > 0
        explanation = "; ".join(issues) if has_leak else "No memory leak detected"
        
        return has_leak, explanation
    
    def cleanup(self):
        """Clean up resources."""
        if self._tracemalloc_started:
            tracemalloc.stop()


def track_memory_operation(func):
    """
    Decorator to track memory usage of a function.
    
    Usage:
        @track_memory_operation
        def my_memory_intensive_function():
            # ... do something ...
    """
    def wrapper(*args, **kwargs):
        collector = AllocatorMetricsCollector()
        
        # Collect before metrics
        gc.collect()
        before = collector.collect_metrics()
        
        # Run the function
        result = func(*args, **kwargs)
        
        # Collect after metrics
        gc.collect()
        after = collector.collect_metrics()
        
        # Report differences
        diffs = collector.compare_metrics(before, after)
        print(f"\nMemory impact of {func.__name__}:")
        for key, value in diffs.items():
            if abs(value) > 0.01:  # Only show significant changes
                print(f"  {key}: {value:+.2f}")
        
        # Check for leak
        has_leak, explanation = collector.check_memory_leak(before, after)
        if has_leak:
            print(f"  WARNING: Possible memory leak - {explanation}")
        
        collector.cleanup()
        return result
    
    return wrapper