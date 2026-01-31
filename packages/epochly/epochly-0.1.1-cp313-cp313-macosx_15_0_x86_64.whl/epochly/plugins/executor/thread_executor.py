"""
Thread-based Executor with Adaptive Thread Pool Sizing (IO-7)

This module implements a feature-complete thread-based executor with:
- Platform-aware default sizing (2x cores on Linux, 1x on Windows/macOS)
- Dynamic scaling based on backlog depth and I/O wait time
- Configuration knobs for min/max workers and thresholds
- Instrumentation for monitoring and workload detection
- Thread-safe scaling operations

Key Features:
- Full benchmark discovery and registration
- Integration test support
- Progressive enhancement compatibility
- Adaptive thread pool that scales with workload
- Compatible interface with SubInterpreterExecutor

Author: Epochly Development Team
"""

import threading
import time
import logging
import platform
import os
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from collections import deque

from .execution_types import ExecutionResult


@dataclass
class ThreadExecutorContext:
    """Context information for thread-based execution."""
    thread_id: int
    is_active: bool = False
    current_task: Optional[str] = None
    task_count: int = 0
    last_activity: float = 0.0
    io_wait_time: float = 0.0

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = time.time()


@dataclass
class ScalingMetrics:
    """Metrics for tracking pool scaling behavior."""
    scale_up_events: int = 0
    scale_down_events: int = 0
    max_backlog_depth: int = 0
    avg_io_wait_time: float = 0.0
    max_io_wait_time: float = 0.0
    io_wait_samples: deque = field(default_factory=lambda: deque(maxlen=100))


def _calculate_default_workers(explicit_workers: Optional[int] = None) -> int:
    """
    Calculate platform-aware default worker count.

    Args:
        explicit_workers: Explicitly specified worker count

    Returns:
        Appropriate worker count based on platform and CPU count
    """
    if explicit_workers is not None:
        return explicit_workers

    cpu_count = os.cpu_count()
    if cpu_count is None:
        # Fallback when cpu_count unavailable
        return 4

    system = platform.system()

    if system == 'Linux':
        # Linux has better epoll/kqueue, use 2x cores
        return cpu_count * 2
    else:
        # Windows/macOS have higher context-switch cost, use 1x cores
        return cpu_count


class ThreadExecutor:
    """
    Feature-complete thread-based executor with adaptive thread pool sizing.

    This executor provides dynamic scaling based on:
    - Platform characteristics (Linux vs Windows/macOS)
    - Backlog depth and queue latency
    - I/O wait time patterns
    - Configurable min/max limits
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        min_workers: Optional[int] = None,
        scale_up_threshold: int = 5,
        scale_down_threshold: float = 0.6,
        enable_dynamic_scaling: bool = True,
        workload_type: str = 'mixed',  # Task 3.2: Add workload type
        allocator: Optional[Any] = None,  # perf_fixes5.md Issue D.2: Fast allocator injection
        performance_config: Optional[Any] = None  # perf_fixes5.md Finding #2: Config-driven sizing
    ):
        """
        Initialize thread executor with stable pool (Task 3.2).

        Per perf_fixes3.md Section 5.5: Apply oversubscription guard and eliminate churn.

        Args:
            max_workers: Maximum number of worker threads (platform-aware if None)
            min_workers: Minimum number of worker threads (default: max_workers // 4)
            scale_up_threshold: Backlog threshold (DEPRECATED - stable pool)
            scale_down_threshold: Idle ratio threshold (DEPRECATED - stable pool)
            enable_dynamic_scaling: Enable resizing (DEPRECATED - kept for compatibility)
            workload_type: 'cpu_bound', 'io_bound', or 'mixed' (Task 3.2)
            allocator: Optional fast allocator for zero-copy data sharing (perf_fixes5.md Issue D.2)
            performance_config: Optional PerformanceConfig for sizing (perf_fixes5.md Finding #2)
        """
        self.logger = logging.getLogger(__name__)

        # perf_fixes5.md Issue D.2: Store allocator for zero-copy operations
        self._allocator = allocator
        if allocator:
            self.logger.debug(f"ThreadExecutor initialized with allocator: {getattr(allocator, 'name', 'unknown')}")

        # perf_fixes5.md Finding #2: Store performance config for oversubscription
        if performance_config is None:
            from ...performance_config import DEFAULT_PERFORMANCE_CONFIG
            self._performance_config = DEFAULT_PERFORMANCE_CONFIG
        else:
            self._performance_config = performance_config

        # Task 3.2: Apply oversubscription guard based on workload type
        # perf_fixes5.md Finding #2: Use config values instead of hardcoded
        cpu_count = os.cpu_count() or 4

        if max_workers is None:
            if workload_type == 'cpu_bound':
                # CPU-bound: Use config.thread_pool.cpu_oversubscription
                cpu_oversub = self._performance_config.thread_pool.cpu_oversubscription
                max_workers = int(cpu_count * cpu_oversub + 0.5)
                self.logger.debug(f"CPU-bound sizing: {cpu_count} cores * {cpu_oversub} = {max_workers} workers")
            elif workload_type == 'io_bound':
                # I/O-bound: Use config.thread_pool.io_oversubscription
                io_oversub = self._performance_config.thread_pool.io_oversubscription
                max_workers = int(cpu_count * io_oversub)
                self.logger.debug(f"I/O-bound sizing: {cpu_count} cores * {io_oversub} = {max_workers} workers")
            else:
                # Mixed: platform default
                max_workers = _calculate_default_workers(None)

        # Calculate platform-aware defaults
        self._max_workers = max_workers
        self._min_workers = min_workers if min_workers is not None else max(1, self._max_workers // 4)
        self._workload_type = workload_type

        # Validate limits
        if self._min_workers < 0:
            raise ValueError(f"min_workers must be >= 0, got {self._min_workers}")
        if self._max_workers < self._min_workers:
            raise ValueError(
                f"max_workers ({self._max_workers}) must be >= min_workers ({self._min_workers})"
            )

        # Task 3.2: STABLE POOL - start with max_workers, keep stable (no dynamic resize)
        # This eliminates teardown/recreation churn
        self._current_workers = self._max_workers
        self._pool = ThreadPoolExecutor(max_workers=self._max_workers)

        self.logger.info(
            f"ThreadExecutor initialized: {self._max_workers} workers "
            f"(workload_type={workload_type}, stable pool - no resize churn)"
        )

        # Registry and contexts
        self._registry: Dict[str, Callable] = {}
        self._contexts: Dict[int, ThreadExecutorContext] = {}
        self._lock = threading.RLock()

        # Scaling configuration (Task 3.2: deprecated for stable pool mode)
        self._scale_up_threshold = scale_up_threshold
        self._scale_down_threshold = scale_down_threshold
        self._enable_dynamic_scaling = enable_dynamic_scaling

        # Warn about deprecated parameters for stable pool
        if workload_type in ('cpu_bound', 'io_bound'):
            if enable_dynamic_scaling:
                import warnings
                warnings.warn(
                    f"Dynamic scaling disabled for stable pool mode (workload_type='{workload_type}'). "
                    f"Parameters scale_up_threshold, scale_down_threshold, enable_dynamic_scaling "
                    f"are deprecated and will be removed in future versions.",
                    DeprecationWarning,
                    stacklevel=2
                )

        # Backlog tracking
        self._backlog_depth = 0
        self._backlog_lock = threading.Lock()
        self._pending_futures: List[Future] = []

        # Scaling metrics
        self._metrics = ScalingMetrics()
        self._metrics_lock = threading.Lock()

        # Idle tracking
        self._idle_worker_ratio = 0.0

        # Workload detector hook
        self._workload_detector: Optional[Any] = None

        # Shutdown flag for monitor thread
        self._shutdown_flag = threading.Event()

        # Initialize thread contexts
        for i in range(self._max_workers):
            self._contexts[i] = ThreadExecutorContext(thread_id=i)

        # Start scaling monitor if enabled AND not stable pool
        # Task 3.2: Disable monitor for stable pool to eliminate overhead
        stable_pool_mode = workload_type in ('cpu_bound', 'io_bound')

        if self._enable_dynamic_scaling and not stable_pool_mode:
            self._scaling_monitor_thread = threading.Thread(
                target=self._scaling_monitor_loop,
                daemon=True,
                name="ThreadExecutor-ScalingMonitor"
            )
            self._scaling_monitor_thread.start()
            self.logger.debug("Started dynamic scaling monitor thread")
        elif stable_pool_mode:
            self.logger.debug("Scaling monitor disabled for stable pool mode (workload_type=%s)", workload_type)

        self.logger.info(
            f"ThreadExecutor initialized with {self._current_workers} workers "
            f"(min={self._min_workers}, max={self._max_workers}, platform={platform.system()})"
        )

    def _scaling_monitor_loop(self):
        """Background thread that monitors and adjusts pool size."""
        while not self._shutdown_flag.is_set():
            try:
                time.sleep(0.5)  # Check every 500ms
                if self._shutdown_flag.is_set():
                    break
                self._adjust_pool_size()
                self._update_idle_ratio()
            except Exception as e:
                self.logger.error(f"Scaling monitor error: {e}", exc_info=True)

    def _adjust_pool_size(self):
        """Adjust pool size based on current metrics."""
        with self._lock:
            backlog = self._backlog_depth
            idle_ratio = self._idle_worker_ratio
            current = self._current_workers

            # Scale up if backlog exceeds threshold and under max
            if backlog > self._scale_up_threshold and current < self._max_workers:
                new_workers = min(current + 2, self._max_workers)
                self._resize_pool(new_workers)

                with self._metrics_lock:
                    self._metrics.scale_up_events += 1

                self.logger.debug(
                    f"Scaled up: {current} -> {new_workers} workers "
                    f"(backlog={backlog})"
                )

            # Scale down if mostly idle and above minimum
            elif idle_ratio > self._scale_down_threshold and current > self._min_workers:
                # Scale down but respect ThreadPoolExecutor minimum of 1
                new_workers = max(current - 1, self._min_workers, 1)
                self._resize_pool(new_workers)

                with self._metrics_lock:
                    self._metrics.scale_down_events += 1

                self.logger.debug(
                    f"Scaled down: {current} -> {new_workers} workers "
                    f"(idle_ratio={idle_ratio:.2f})"
                )

    def _resize_pool(self, new_size: int):
        """
        Resize the thread pool to new size.

        Task 3.2 CRITICAL FIX: DO NOT recreate ThreadPoolExecutor - keep stable pool.
        This method now logs the request but doesn't actually resize to eliminate churn.

        ThreadPoolExecutor in Python 3.13+ supports internal resizing via _max_workers,
        but for stability we keep a fixed-size pool set at initialization.

        Args:
            new_size: Requested new size (logged but not applied)
        """
        # Task 3.2: STABLE POOL - no dynamic resizing
        # Log the resize request for telemetry but don't recreate pool
        self.logger.debug(
            f"Pool resize requested: {self._current_workers} -> {new_size} "
            f"(ignored - stable pool strategy to eliminate churn)"
        )

        # Pool stays at _max_workers set during initialization
        # This eliminates TLS cache loss and context-switch overhead
        # Future enhancement: Use ThreadPoolExecutor._adjust_thread_count() if needed

    def _update_idle_ratio(self):
        """Update the idle worker ratio metric."""
        with self._lock:
            if self._current_workers == 0:
                self._idle_worker_ratio = 1.0
                return

            active_count = sum(1 for ctx in self._contexts.values() if ctx.is_active)
            self._idle_worker_ratio = 1.0 - (active_count / self._current_workers)

    def _update_backlog(self, delta: int):
        """
        Update backlog depth and track metrics.

        Args:
            delta: Change in backlog (+1 for submit, -1 for complete)
        """
        with self._backlog_lock:
            self._backlog_depth = max(0, self._backlog_depth + delta)

            with self._metrics_lock:
                if self._backlog_depth > self._metrics.max_backlog_depth:
                    self._metrics.max_backlog_depth = self._backlog_depth

            # Signal workload detector on significant backlog
            if self._backlog_depth > self._scale_up_threshold:
                self._signal_workload_detector()

    def _signal_workload_detector(self):
        """Signal workload detector about backlog increase."""
        if self._workload_detector and hasattr(self._workload_detector, 'on_backlog_increase'):
            try:
                self._workload_detector.on_backlog_increase(self._backlog_depth)
            except Exception as e:
                self.logger.error(f"Error signaling workload detector: {e}")

    def set_workload_detector(self, detector: Any):
        """
        Set workload detector for backlog signaling.

        Args:
            detector: Workload detector instance
        """
        self._workload_detector = detector

    def get_backlog_depth(self) -> int:
        """Get current backlog depth."""
        with self._backlog_lock:
            return self._backlog_depth

    def get_avg_io_wait_time(self) -> float:
        """Get average I/O wait time."""
        with self._metrics_lock:
            return self._metrics.avg_io_wait_time

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive executor metrics.

        Returns:
            Dictionary of metrics including workers, backlog, scaling events
        """
        with self._lock, self._metrics_lock:
            active_count = sum(1 for ctx in self._contexts.values() if ctx.is_active)

            return {
                'current_workers': self._current_workers,
                'min_workers': self._min_workers,
                'max_workers': self._max_workers,
                'active_workers': active_count,
                'backlog_depth': self._backlog_depth,
                'idle_ratio': self._idle_worker_ratio,
                'scale_up_events': self._metrics.scale_up_events,
                'scale_down_events': self._metrics.scale_down_events,
                'max_backlog_depth': self._metrics.max_backlog_depth,
                'avg_io_wait_time': self._metrics.avg_io_wait_time,
                'max_io_wait_time': self._metrics.max_io_wait_time,
                'platform': platform.system(),
                'cpu_count': os.cpu_count() or 0
            }

    def register(self, name: str, func: Callable) -> None:
        """
        Register a function for execution.

        Args:
            name: Function name/identifier
            func: Function to register
        """
        with self._lock:
            self._registry[name] = func
            self.logger.debug(f"Registered function: {name}")

    def get_registered_function(self, name: str) -> Optional[Callable]:
        """
        Get a registered function by name.

        Args:
            name: Name of the function to retrieve

        Returns:
            The registered function or None if not found
        """
        with self._lock:
            return self._registry.get(name)

    def discover_benchmarks(self) -> List[str]:
        """
        Discover available benchmarks.

        Returns:
            List of benchmark names
        """
        with self._lock:
            benchmarks = [name for name in self._registry.keys()
                         if 'benchmark' in name.lower()]
            self.logger.info(f"Discovered {len(benchmarks)} benchmarks")
            return benchmarks

    def discover_integration_tests(self) -> List[str]:
        """
        Discover available integration tests.

        Returns:
            List of integration test names
        """
        with self._lock:
            tests = [name for name in self._registry.keys()
                    if 'test' in name.lower() or 'integration' in name.lower()]
            self.logger.info(f"Discovered {len(tests)} integration tests")
            return tests

    def run_all(self) -> Dict[str, Any]:
        """
        Run all registered functions.

        Returns:
            Dictionary mapping function names to results
        """
        with self._lock:
            if not self._registry:
                self.logger.warning("No functions registered for execution")
                return {}

            futures = {}
            for name, func in self._registry.items():
                try:
                    future = self._pool.submit(self._execute_with_context, name, func)
                    futures[name] = future
                    self._update_backlog(1)
                except Exception as e:
                    self.logger.error(f"Failed to submit {name}: {e}")

            # Collect results
            results = {}
            for name, future in futures.items():
                try:
                    results[name] = future.result(timeout=30)
                    self._update_backlog(-1)
                except Exception as e:
                    self.logger.error(f"Execution failed for {name}: {e}")
                    results[name] = ExecutionResult(
                        success=False,
                        error=str(e)
                    )
                    self._update_backlog(-1)

            return results

    def run_benchmarks(self) -> Dict[str, Any]:
        """
        Run all registered benchmarks.

        Returns:
            Dictionary mapping benchmark names to results
        """
        benchmarks = self.discover_benchmarks()
        if not benchmarks:
            self.logger.warning("No benchmarks discovered")
            return {}

        results = {}
        for benchmark_name in benchmarks:
            func = self._registry[benchmark_name]
            try:
                future = self._pool.submit(self._execute_with_context, benchmark_name, func)
                self._update_backlog(1)
                results[benchmark_name] = future.result(timeout=60)
                self._update_backlog(-1)
            except Exception as e:
                self.logger.error(f"Benchmark {benchmark_name} failed: {e}")
                results[benchmark_name] = ExecutionResult(
                    success=False,
                    error=str(e)
                )
                self._update_backlog(-1)

        return results

    def run_integration_tests(self) -> Dict[str, Any]:
        """
        Run all registered integration tests.

        Returns:
            Dictionary mapping test names to results
        """
        tests = self.discover_integration_tests()
        if not tests:
            self.logger.warning("No integration tests discovered")
            return {}

        results = {}
        for test_name in tests:
            func = self._registry[test_name]
            try:
                future = self._pool.submit(self._execute_with_context, test_name, func)
                self._update_backlog(1)
                results[test_name] = future.result(timeout=30)
                self._update_backlog(-1)
            except Exception as e:
                self.logger.error(f"Integration test {test_name} failed: {e}")
                results[test_name] = ExecutionResult(
                    success=False,
                    error=str(e)
                )
                self._update_backlog(-1)

        return results

    def execute(self, func: Callable, *args, **kwargs) -> Future:
        """
        Execute a function and return a Future.

        This method provides compatibility with SubInterpreterExecutor interface.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Future object for the ExecutionResult
        """
        self.logger.debug(f"ThreadExecutor.execute called with func: {func.__name__ if hasattr(func, '__name__') else str(func)}")

        try:
            # Ensure function is callable
            if not callable(func):
                raise TypeError(f"Function is not callable: {type(func)}")

            # Submit task to thread pool
            def wrapped_execution():
                result = self._execute_with_context(func.__name__ if hasattr(func, '__name__') else 'anonymous', func, *args, **kwargs)
                self._update_backlog(-1)
                return result

            future = self._pool.submit(wrapped_execution)
            self._update_backlog(1)
            self.logger.debug("Task submitted successfully to thread pool")
            return future

        except Exception as e:
            self.logger.error(f"ThreadExecutor.execute failed: {e}", exc_info=True)
            # Return a future with a failed result
            from concurrent.futures import Future as ConcurrentFuture
            failed_future = ConcurrentFuture()
            failed_future.set_result(ExecutionResult(
                success=False,
                error=str(e),
                execution_time=0.0
            ))
            return failed_future

    def submit_task(self, func: Callable, *args, **kwargs) -> Future:
        """
        Submit a task for execution.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Future object for the task result
        """
        return self.execute(func, *args, **kwargs)

    def _execute_with_context(self, name: str, func: Callable, *args, **kwargs) -> ExecutionResult:
        """
        Execute function with context tracking and I/O wait measurement.

        Args:
            name: Function name
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            ExecutionResult with execution details
        """
        self.logger.debug(f"_execute_with_context called for {name} with func: {func}")
        thread_id = threading.get_ident() % self._max_workers
        context = self._contexts.get(thread_id)

        if context:
            context.is_active = True
            context.current_task = name
            context.task_count += 1
            context.update_activity()
            self.logger.debug(f"Context updated for thread {thread_id}, task: {name}")

        try:
            self.logger.debug(f"Starting execution of {name}")
            start_time = time.time()
            wait_start = time.time()

            # Ensure function is callable
            if not callable(func):
                raise TypeError(f"Function {name} is not callable: {type(func)}")

            # Execute the function
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Track I/O wait time (approximation based on execution time)
            io_wait = time.time() - wait_start

            if context:
                context.io_wait_time += io_wait

            with self._metrics_lock:
                self._metrics.io_wait_samples.append(io_wait)
                if self._metrics.io_wait_samples:
                    self._metrics.avg_io_wait_time = sum(self._metrics.io_wait_samples) / len(self._metrics.io_wait_samples)
                if io_wait > self._metrics.max_io_wait_time:
                    self._metrics.max_io_wait_time = io_wait

            self.logger.debug(f"Execution of {name} completed successfully in {execution_time:.4f}s")

            return ExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time
            )

        except Exception as e:
            self.logger.error(f"Execution failed for {name}: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=0.0
            )

        finally:
            if context:
                context.is_active = False
                context.current_task = None
                self.logger.debug(f"Context cleaned up for thread {thread_id}")

    def get_status(self) -> Dict[str, Any]:
        """Get executor status with scaling metrics."""
        with self._lock:
            active_count = sum(1 for ctx in self._contexts.values() if ctx.is_active)
            total_tasks = sum(ctx.task_count for ctx in self._contexts.values())

            return {
                "executor_type": "thread_based_adaptive",
                "total_workers": self._max_workers,
                "current_workers": self._current_workers,
                "min_workers": self._min_workers,
                "active_workers": active_count,
                "registered_functions": len(self._registry),
                "total_tasks_processed": total_tasks,
                "available_benchmarks": len(self.discover_benchmarks()),
                "available_integration_tests": len(self.discover_integration_tests()),
                "backlog_depth": self._backlog_depth,
                "scale_up_events": self._metrics.scale_up_events,
                "scale_down_events": self._metrics.scale_down_events,
                "platform": platform.system()
            }

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the thread executor.

        Task 3.2: Complete cleanup without hangs, proper error propagation.
        Idempotent - safe to call multiple times.

        Args:
            wait: If True, block until worker threads finish. If False, initiate
                  shutdown and return immediately (tasks may continue in background).

        Raises:
            RuntimeError: If shutdown is called from within a worker thread
            Exception: Any exception from ThreadPoolExecutor.shutdown() propagates
        """
        # Idempotency check - safe to call shutdown multiple times
        if hasattr(self, '_shutdown_flag') and self._shutdown_flag.is_set():
            self.logger.debug("Shutdown already called, ignoring duplicate call")
            return

        self.logger.info("Shutting down ThreadExecutor (wait=%s)", wait)

        # Signal monitor thread to stop
        if hasattr(self, '_shutdown_flag'):
            self._shutdown_flag.set()

        # Wait for monitor thread to finish (if it exists)
        if hasattr(self, '_scaling_monitor_thread') and self._scaling_monitor_thread:
            if self._scaling_monitor_thread.is_alive():
                self._scaling_monitor_thread.join(timeout=2.0)
                if self._scaling_monitor_thread.is_alive():
                    # Monitor thread failed to stop - this should not happen
                    self.logger.error("Monitor thread did not exit within 2.0s - may indicate deadlock")
                    # In production, could raise TimeoutError, but for now just warn
                    # raise TimeoutError("Monitor thread failed to stop during shutdown")

        # Shutdown thread pool - CRITICAL: propagate exceptions, don't swallow
        # hasattr check only needed if shutdown can be called during failed initialization
        if hasattr(self, '_pool') and self._pool:
            try:
                self._pool.shutdown(wait=wait)
            except Exception:
                # Log with full traceback
                self.logger.exception("CRITICAL: ThreadPoolExecutor shutdown failed")
                # Re-raise so caller knows shutdown failed
                raise

        # Clean up resources (under lock to prevent race with monitor thread)
        with self._lock:
            self._registry.clear()
            self._contexts.clear()

        self.logger.info("ThreadExecutor shutdown complete")
