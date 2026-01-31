"""
ProcessPool Memory Monitor and Safety Controls.

Prevents memory saturation when using ProcessPoolExecutor by:
1. Monitoring per-process memory usage
2. Limiting total ProcessPool memory
3. Auto-scaling worker count based on available memory
4. Graceful degradation when memory constrained
5. Fork bomb prevention via worker_initializer integration

Reference: mcp-reflect recommendations (2025-11-23)
Updated: 2025-11-24 - Integrated with lazy Level 3 and fork bomb protection
"""

import os
import sys
import multiprocessing
import psutil
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class MemoryLimits:
    """Memory limits for ProcessPool safety."""

    max_total_memory_bytes: int  # Maximum total memory for all workers
    max_per_worker_bytes: int  # Maximum memory per worker process
    warning_threshold_pct: float = 0.75  # Warn at 75% of limit
    critical_threshold_pct: float = 0.90  # Critical at 90% of limit


class ProcessPoolMemoryMonitor:
    """
    Monitor and control ProcessPool memory usage.

    Prevents system memory saturation by:
    - Tracking per-process memory
    - Auto-scaling worker count
    - Graceful degradation
    """

    def __init__(self, limits: Optional[MemoryLimits] = None):
        """
        Initialize memory monitor.

        Args:
            limits: Memory limits (auto-calculated if None)
        """
        self.limits = limits or self._calculate_safe_limits()
        self.current_workers = 0
        self.peak_memory_per_worker = 0
        self._last_check_memory = 0

    def _calculate_safe_limits(self) -> MemoryLimits:
        """
        Calculate safe memory limits based on system resources.

        Strategy:
        - Never use more than 50% of total system memory
        - Leave headroom for OS and other processes
        - Scale conservatively in containers
        """
        vm = psutil.virtual_memory()
        total_memory = vm.total
        available_memory = vm.available

        # Container detection
        in_container = self._detect_container()

        if in_container:
            # Conservative in containers (30% of total)
            max_pool_memory = int(total_memory * 0.30)
        else:
            # Less conservative on bare metal (50% of available)
            max_pool_memory = int(available_memory * 0.50)

        # Estimate per-worker memory (conservative: 200MB per worker)
        estimated_per_worker = 200 * 1024 * 1024  # 200MB

        return MemoryLimits(
            max_total_memory_bytes=max_pool_memory,
            max_per_worker_bytes=estimated_per_worker
        )

    def _detect_container(self) -> bool:
        """Detect if running in container (Docker, K8s, etc.)."""
        import os

        # Check common container indicators
        if os.path.exists('/.dockerenv'):
            return True

        if os.environ.get('KUBERNETES_SERVICE_HOST'):
            return True

        try:
            with open('/proc/1/cgroup', 'r') as f:
                content = f.read()
                if 'docker' in content or 'kubepods' in content:
                    return True
        except (FileNotFoundError, PermissionError, OSError):
            pass  # Expected on non-Linux or restricted systems

        return False

    def calculate_safe_worker_count(self, desired_workers: int) -> int:
        """
        Calculate safe worker count based on memory limits.

        Args:
            desired_workers: Requested number of workers

        Returns:
            Safe number of workers that won't exceed memory limits
        """
        # Calculate maximum workers based on total memory limit
        max_workers_by_total = self.limits.max_total_memory_bytes // self.limits.max_per_worker_bytes

        # Use peak memory per worker if we have data
        if self.peak_memory_per_worker > 0:
            max_workers_by_peak = self.limits.max_total_memory_bytes // self.peak_memory_per_worker
            max_workers_by_memory = min(max_workers_by_total, max_workers_by_peak)
        else:
            max_workers_by_memory = max_workers_by_total

        # Take minimum of desired and safe count
        safe_count = min(desired_workers, max_workers_by_memory)

        # Always allow at least 1 worker (even if memory tight)
        safe_count = max(1, safe_count)

        if safe_count < desired_workers:
            logger.warning(
                f"ProcessPool worker count reduced: {desired_workers} → {safe_count} "
                f"(memory limit: {self.limits.max_total_memory_bytes / (1024**3):.1f}GB)"
            )

        return safe_count

    def check_memory_usage(self, process_pool) -> Dict[str, Any]:
        """
        Check current memory usage of ProcessPool.

        Args:
            process_pool: ProcessPoolExecutor instance

        Returns:
            Dictionary with memory metrics
        """
        try:
            # Get all worker processes
            current_process = psutil.Process()
            children = current_process.children(recursive=True)

            total_memory = 0
            max_per_worker = 0
            worker_count = 0

            for child in children:
                try:
                    mem_info = child.memory_info()
                    memory_bytes = mem_info.rss  # Resident Set Size

                    total_memory += memory_bytes
                    max_per_worker = max(max_per_worker, memory_bytes)
                    worker_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Update peak tracking
            if max_per_worker > self.peak_memory_per_worker:
                self.peak_memory_per_worker = max_per_worker

            # Calculate thresholds
            warning_threshold = self.limits.max_total_memory_bytes * self.limits.warning_threshold_pct
            critical_threshold = self.limits.max_total_memory_bytes * self.limits.critical_threshold_pct

            # Determine status
            if total_memory >= critical_threshold:
                status = 'CRITICAL'
            elif total_memory >= warning_threshold:
                status = 'WARNING'
            else:
                status = 'OK'

            return {
                'total_memory_mb': total_memory / (1024**2),
                'max_per_worker_mb': max_per_worker / (1024**2),
                'worker_count': worker_count,
                'limit_mb': self.limits.max_total_memory_bytes / (1024**2),
                'usage_pct': (total_memory / self.limits.max_total_memory_bytes) * 100,
                'status': status
            }

        except Exception as e:
            logger.debug(f"Memory check failed: {e}")
            return {'status': 'UNKNOWN', 'error': str(e)}

    def should_scale_down(self, usage_metrics: Dict) -> bool:
        """
        Determine if worker count should be reduced.

        Args:
            usage_metrics: Result from check_memory_usage()

        Returns:
            True if workers should be reduced
        """
        return usage_metrics.get('status') in ['WARNING', 'CRITICAL']

    def get_recommended_worker_count(self, current_workers: int, usage_metrics: Dict) -> int:
        """
        Get recommended worker count based on memory usage.

        Args:
            current_workers: Current number of workers
            usage_metrics: Current memory usage

        Returns:
            Recommended worker count (may be lower than current)
        """
        status = usage_metrics.get('status', 'OK')

        if status == 'CRITICAL':
            # Reduce by 50%
            return max(1, current_workers // 2)

        elif status == 'WARNING':
            # Reduce by 25%
            return max(1, int(current_workers * 0.75))

        else:
            # No reduction needed
            return current_workers


def _get_safe_multiprocessing_context():
    """
    Get the safest multiprocessing context for the current platform.

    Returns:
        Tuple of (context, method_name) where context is a multiprocessing context
        and method_name is 'forkserver', 'spawn', or 'fork'.

    Priority:
    1. forkserver - Fast (5ms) and fork-safe, prevents deadlocks
    2. spawn - Slow (650ms) but always safe
    3. fork - Fast but can cause deadlocks in multi-threaded environments
    """
    import platform

    start_methods = multiprocessing.get_all_start_methods()

    # Windows only supports spawn
    if sys.platform == 'win32' or platform.system() == 'Windows':
        return multiprocessing.get_context('spawn'), 'spawn'

    # Prefer forkserver on Unix (fast and safe)
    if 'forkserver' in start_methods:
        return multiprocessing.get_context('forkserver'), 'forkserver'

    # Fall back to spawn (slow but safe)
    if 'spawn' in start_methods:
        return multiprocessing.get_context('spawn'), 'spawn'

    # Last resort: fork (may cause issues in multi-threaded environments)
    return multiprocessing.get_context('fork'), 'fork'


def create_memory_safe_processpool(
    desired_workers: int,
    use_worker_initializer: bool = True,
    **kwargs
) -> ProcessPoolExecutor:
    """
    Create ProcessPoolExecutor with memory safety controls and fork bomb protection.

    This is the CANONICAL way to create ProcessPool in Epochly. It ensures:
    1. Memory-safe worker count (won't exhaust system memory)
    2. Fork bomb protection via epochly_worker_initializer
    3. Safe multiprocessing context (forkserver preferred)
    4. Proper environment setup for workers

    Args:
        desired_workers: Desired number of workers
        use_worker_initializer: If True, use epochly_worker_initializer (default: True)
                               Set to False ONLY for testing purposes
        **kwargs: Additional ProcessPoolExecutor arguments
                  NOTE: 'initializer' and 'mp_context' will be overridden if not compatible

    Returns:
        ProcessPoolExecutor with safe worker count and fork bomb protection

    Example:
        pool = create_memory_safe_processpool(16)
        future = pool.submit(my_func, arg1, arg2)
        result = future.result()
        pool.shutdown(wait=True)
    """
    # Calculate safe worker count based on memory limits
    monitor = ProcessPoolMemoryMonitor()
    safe_workers = monitor.calculate_safe_worker_count(desired_workers)

    # Phase 2 (Dec 2025): Use forkserver_manager for centralized start method selection
    # This respects forkserver state set during Level 3 initialization
    try:
        from epochly.core.forkserver_manager import get_recommended_start_method
        method = get_recommended_start_method()
        ctx = multiprocessing.get_context(method)
    except ImportError:
        # Fallback to original logic if forkserver_manager not available
        ctx, method = _get_safe_multiprocessing_context()

    # CRITICAL: Set environment variables BEFORE creating pool
    # This ensures workers inherit disabled state and prevents fork bomb
    os.environ['EPOCHLY_DISABLE_INTERCEPTION'] = '1'
    os.environ['EPOCHLY_DISABLE'] = '1'

    # Prepare kwargs for ProcessPoolExecutor
    pool_kwargs = dict(kwargs)
    pool_kwargs['max_workers'] = safe_workers
    pool_kwargs['mp_context'] = ctx

    # Add worker initializer for fork bomb protection
    if use_worker_initializer:
        from .worker_initializer import epochly_worker_initializer
        pool_kwargs['initializer'] = epochly_worker_initializer

    logger.info(
        f"Creating ProcessPool with {safe_workers} workers "
        f"(requested: {desired_workers}, context: {method}, "
        f"memory limit: {monitor.limits.max_total_memory_bytes / (1024**3):.1f}GB)"
    )

    try:
        pool = ProcessPoolExecutor(**pool_kwargs)
        return pool
    finally:
        # CRITICAL FIX (Dec 2025): Clear env vars AFTER pool is created
        # Workers have inherited these at spawn time. Clearing in main process
        # allows subsequent EpochlyCore re-initialization (e.g., in tests).
        os.environ.pop('EPOCHLY_DISABLE', None)
        os.environ.pop('EPOCHLY_DISABLE_INTERCEPTION', None)


# Singleton monitor for global access
_global_monitor: Optional[ProcessPoolMemoryMonitor] = None


def get_memory_monitor() -> ProcessPoolMemoryMonitor:
    """
    Get the global ProcessPoolMemoryMonitor singleton.

    Returns:
        ProcessPoolMemoryMonitor instance
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ProcessPoolMemoryMonitor()
    return _global_monitor
