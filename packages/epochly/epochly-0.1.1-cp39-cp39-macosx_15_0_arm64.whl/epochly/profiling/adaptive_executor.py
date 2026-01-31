"""
Adaptive Executor Selection - Lightweight Executors for Small Tasks

Provides intelligent executor selection based on task characteristics:
- ThreadPoolExecutor for GIL-releasing operations and small tasks
- ProcessPoolExecutor for CPU-bound tasks with significant execution time
- Warm worker pools for pre-initialized process pools with shared state

Key Decision Criteria:
- Task execution time: <10ms = threads, >10ms = processes
- Payload size: <1KB = threads (serialization dominates), >1MB = shared memory
- GIL-releasing: Known GIL-releasing ops = threads
- CPU-bound Python: Always processes (GIL contention)

Author: Epochly Development Team
Date: November 26, 2025
"""

from __future__ import annotations

import os
import sys
import time
import threading
import atexit
from functools import partial
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future, Executor

from ..utils.logger import get_logger
from .scheduling_profiler import (
    SchedulingProfiler, ExecutorType, TaskLatencyBreakdown,
    get_scheduling_profiler
)

logger = get_logger(__name__)


def _register_executor(executor: ProcessPoolExecutor) -> None:
    """
    Register ProcessPoolExecutor in global registry for cleanup.

    This ensures executors created by optimizers are properly shut down
    during pytest session teardown, preventing orphaned processes.
    """
    # Primary: Use centralized executor registry (orphan detection, unified cleanup)
    try:
        from epochly.core.executor_registry import register_executor
        register_executor(executor, name="adaptive_executor_pool")
        logger.debug(f"Registered ProcessPoolExecutor in centralized registry")
        return
    except ImportError:
        pass  # Centralized registry not available

    # Fallback: Use local SIE registry for backwards compatibility
    try:
        from epochly.plugins.executor.sub_interpreter_executor import (
            _PROCESS_POOL_REGISTRY,
            _POOL_REGISTRY_LOCK
        )
        with _POOL_REGISTRY_LOCK:
            _PROCESS_POOL_REGISTRY.add(executor)
        logger.debug(f"Registered ProcessPoolExecutor in SIE registry (total: {len(_PROCESS_POOL_REGISTRY)})")
    except ImportError:
        pass  # Registry not available, cleanup will use gc fallback


def _warm_pool_initializer(modules: List[str], custom_init: Optional[Callable] = None) -> None:
    """
    Module-level initializer for warm worker pools.

    This function is called in each worker process at startup.
    Config is passed via initargs for cross-platform compatibility
    (works with both 'fork' and 'spawn' multiprocessing start methods).

    Args:
        modules: List of module names to pre-import in workers
        custom_init: Optional custom initializer function (must be picklable)
    """
    # Disable Epochly in workers to prevent interception
    os.environ['EPOCHLY_DISABLE'] = '1'
    os.environ['EPOCHLY_DISABLE_INTERCEPTION'] = '1'

    # Pre-import modules
    for module_name in modules:
        try:
            __import__(module_name)
        except ImportError:
            logger.warning(f"WarmWorkerPool: failed to import {module_name}")

    # Run custom initializer if provided (must be a module-level function)
    if custom_init and callable(custom_init):
        try:
            custom_init()
        except Exception as e:
            logger.warning(f"WarmWorkerPool: custom initializer failed: {e}")


# Thresholds for executor selection
SMALL_TASK_EXECUTION_MS = 10.0  # Tasks < 10ms execution use threads
SMALL_PAYLOAD_BYTES = 1024      # Payloads < 1KB use threads
LARGE_PAYLOAD_BYTES = 1024 * 1024  # Payloads > 1MB benefit from shared memory
MIN_PROCESS_BENEFIT_MS = 50.0   # Minimum execution time to benefit from processes


@dataclass
class ExecutorDecision:
    """Decision about which executor to use for a task."""
    executor_type: ExecutorType
    reason: str
    confidence: float  # 0.0 to 1.0
    estimated_overhead_ms: float
    estimated_execution_ms: float
    use_shared_memory: bool = False

    @property
    def estimated_speedup(self) -> float:
        """Estimated speedup from parallelization."""
        if self.executor_type == ExecutorType.THREAD:
            return 1.0  # No speedup, but minimal overhead
        elif self.executor_type == ExecutorType.PROCESS:
            # Factor in overhead
            overhead_ratio = self.estimated_overhead_ms / max(self.estimated_execution_ms, 1.0)
            if overhead_ratio > 0.5:
                return 0.5 / (1.0 + overhead_ratio)  # Overhead dominates
            return 0.8  # Typical process parallelization factor
        return 1.0


@dataclass
class TaskCharacteristics:
    """Characteristics of a task for executor selection."""
    estimated_execution_ms: float = 0.0
    payload_size_bytes: int = 0
    result_size_bytes: int = 0
    is_gil_releasing: bool = False
    is_io_bound: bool = False
    is_cpu_bound: bool = True
    has_shared_state: bool = False
    num_similar_tasks: int = 1  # For batch decisions


class WarmWorkerPool:
    """
    Pre-initialized worker pool with shared state.

    Benefits:
    - Zero startup overhead for subsequent tasks
    - Shared initialization (import heavy modules once)
    - Persistent worker state across tasks
    - Automatic pool sizing based on workload
    - Cross-platform compatible (works with fork and spawn)

    Usage:
        pool = WarmWorkerPool(max_workers=4)
        pool.initialize(['numpy', 'pandas'])  # Pre-import in workers

        future = pool.submit(compute_func, data)
        result = future.result()
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        initializer: Optional[Callable] = None,
        pre_import_modules: Optional[List[str]] = None
    ):
        """
        Initialize warm worker pool.

        Args:
            max_workers: Number of workers (default: cpu_count)
            initializer: Custom worker initialization function (must be picklable/module-level)
            pre_import_modules: Modules to import in workers at startup
        """
        self.max_workers = max_workers or os.cpu_count() or 4
        self._initializer = initializer
        self._pre_import_modules = list(pre_import_modules or [])

        # Pool state
        self._pool: Optional[ProcessPoolExecutor] = None
        self._pool_lock = threading.Lock()
        self._is_initialized = False

        # Statistics
        self._tasks_submitted = 0
        self._warm_tasks = 0  # Tasks that used warm workers
        self._total_startup_time_ns = 0

        # Worker tracking
        self._worker_first_task: Dict[int, bool] = {}

        # Register cleanup
        atexit.register(self._cleanup)

    def _create_pool(self) -> ProcessPoolExecutor:
        """Create and initialize worker pool."""
        # Pass config directly via initargs for cross-platform compatibility
        # This works with both 'fork' and 'spawn' multiprocessing start methods
        pool = ProcessPoolExecutor(
            max_workers=self.max_workers,
            initializer=_warm_pool_initializer,
            initargs=(list(self._pre_import_modules), self._initializer)
        )
        _register_executor(pool)

        logger.info(
            f"Created WarmWorkerPool: {self.max_workers} workers, "
            f"pre-imported {len(self._pre_import_modules)} modules"
        )

        return pool

    def initialize(self, additional_modules: Optional[List[str]] = None) -> None:
        """
        Initialize pool and warm up workers.

        Args:
            additional_modules: Additional modules to pre-import
        """
        if additional_modules:
            for mod in additional_modules:
                if mod not in self._pre_import_modules:
                    self._pre_import_modules.append(mod)

        with self._pool_lock:
            if self._pool is not None:
                return  # Already initialized

            self._pool = self._create_pool()

            # Warm up all workers with a no-op task
            start = time.perf_counter_ns()
            futures = [
                self._pool.submit(_warm_up_worker, i)
                for i in range(self.max_workers)
            ]

            # Wait for all to complete
            for f in futures:
                f.result(timeout=30.0)

            self._total_startup_time_ns = time.perf_counter_ns() - start
            self._is_initialized = True

            logger.info(
                f"WarmWorkerPool initialized: {self.max_workers} workers warmed up in "
                f"{self._total_startup_time_ns / 1_000_000:.1f}ms"
            )

    def submit(self, fn: Callable, *args, **kwargs) -> Future:
        """
        Submit task to warm worker pool.

        Args:
            fn: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Future for the result
        """
        # Lazy initialization
        if not self._is_initialized:
            self.initialize()

        with self._pool_lock:
            self._tasks_submitted += 1
            return self._pool.submit(fn, *args, **kwargs)

    def map(self, fn: Callable, *iterables, timeout: Optional[float] = None,
            chunksize: int = 1) -> List[Any]:
        """
        Map function over iterables using warm workers.

        Args:
            fn: Function to apply
            *iterables: Input iterables
            timeout: Maximum time to wait
            chunksize: Size of chunks for each worker

        Returns:
            List of results
        """
        if not self._is_initialized:
            self.initialize()

        with self._pool_lock:
            return list(self._pool.map(fn, *iterables, timeout=timeout, chunksize=chunksize))

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            'max_workers': self.max_workers,
            'is_initialized': self._is_initialized,
            'tasks_submitted': self._tasks_submitted,
            'startup_time_ms': self._total_startup_time_ns / 1_000_000,
            'pre_imported_modules': list(self._pre_import_modules),
        }

    def resize(self, new_worker_count: int) -> None:
        """Resize pool (recreates with new worker count)."""
        with self._pool_lock:
            if self._pool:
                self._pool.shutdown(wait=True)

            self.max_workers = new_worker_count
            self._pool = None
            self._is_initialized = False

        # Reinitialize with new size
        self.initialize()

    def _cleanup(self) -> None:
        """Clean up pool resources."""
        with self._pool_lock:
            if self._pool:
                try:
                    self._pool.shutdown(wait=False)
                except Exception:
                    pass
                self._pool = None

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the pool."""
        with self._pool_lock:
            if self._pool:
                self._pool.shutdown(wait=wait)
                self._pool = None
                self._is_initialized = False

    def __enter__(self) -> 'WarmWorkerPool':
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.shutdown(wait=True)
        return False


def _warm_up_worker(worker_id: int) -> int:
    """No-op function to warm up worker process."""
    return worker_id


class AdaptiveExecutorSelector:
    """
    Intelligently selects executor type based on task characteristics.

    Uses historical profiling data and task analysis to minimize overhead:
    - Small/fast tasks: ThreadPoolExecutor (minimal overhead)
    - Large CPU-bound tasks: ProcessPoolExecutor (true parallelism)
    - Repeated tasks: WarmWorkerPool (pre-initialized)

    Learning:
    - Tracks execution history per task signature
    - Adjusts thresholds based on measured performance
    - Provides recommendations for optimization
    """

    # Known GIL-releasing operations (safe for threads)
    GIL_RELEASING_MODULES: Set[str] = {
        'numpy', 'scipy', 'pandas', 'sklearn', 'torch', 'tensorflow',
        'numba', 'cython', 'opencv', 'pillow', 'cv2'
    }

    def __init__(
        self,
        profiler: Optional[SchedulingProfiler] = None,
        thread_executor: Optional[ThreadPoolExecutor] = None,
        process_executor: Optional[ProcessPoolExecutor] = None,
        warm_pool: Optional[WarmWorkerPool] = None
    ):
        """
        Initialize adaptive selector.

        Args:
            profiler: SchedulingProfiler for historical data
            thread_executor: Pre-created ThreadPoolExecutor
            process_executor: Pre-created ProcessPoolExecutor
            warm_pool: Pre-initialized WarmWorkerPool
        """
        self._profiler = profiler or get_scheduling_profiler()

        # Executors (lazy initialization)
        self._thread_executor = thread_executor
        self._process_executor = process_executor
        self._warm_pool = warm_pool

        # Locks for lazy init (all executors need thread-safe creation)
        self._thread_lock = threading.Lock()
        self._process_lock = threading.Lock()
        self._warm_pool_lock = threading.Lock()

        # Task history for learning
        self._task_history: Dict[str, List[float]] = {}  # signature -> [execution_times]
        self._history_lock = threading.Lock()

        # Thresholds (can be tuned based on profiling)
        self.small_task_threshold_ms = SMALL_TASK_EXECUTION_MS
        self.small_payload_threshold = SMALL_PAYLOAD_BYTES
        self.large_payload_threshold = LARGE_PAYLOAD_BYTES

    def analyze_task(self, func: Callable, args: tuple, kwargs: dict) -> TaskCharacteristics:
        """
        Analyze task characteristics for executor selection.

        Args:
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            TaskCharacteristics with estimated properties
        """
        chars = TaskCharacteristics()

        # Estimate payload size
        try:
            import cloudpickle
            pickled = cloudpickle.dumps((func, args, kwargs))
            chars.payload_size_bytes = len(pickled)
        except Exception:
            chars.payload_size_bytes = 0

        # Check if function uses GIL-releasing modules
        func_module = getattr(func, '__module__', '') or ''
        for gil_mod in self.GIL_RELEASING_MODULES:
            if gil_mod in func_module:
                chars.is_gil_releasing = True
                break

        # Check function signature for hints
        func_name = getattr(func, '__name__', str(func))

        # Heuristics for IO-bound vs CPU-bound
        io_hints = ['read', 'write', 'fetch', 'download', 'upload', 'request', 'socket']
        cpu_hints = ['compute', 'calculate', 'process', 'transform', 'analyze']

        func_name_lower = func_name.lower()
        chars.is_io_bound = any(h in func_name_lower for h in io_hints)
        chars.is_cpu_bound = any(h in func_name_lower for h in cpu_hints) or not chars.is_io_bound

        # Look up historical execution time
        task_sig = self._get_task_signature(func)
        with self._history_lock:
            if task_sig in self._task_history:
                exec_times = self._task_history[task_sig]
                if exec_times:
                    import statistics
                    chars.estimated_execution_ms = statistics.median(exec_times)

        return chars

    def decide_executor(self, chars: TaskCharacteristics) -> ExecutorDecision:
        """
        Decide which executor to use for a task.

        Args:
            chars: Task characteristics

        Returns:
            ExecutorDecision with recommended executor and reasoning
        """
        # Small payloads with fast execution = threads
        if (chars.payload_size_bytes < self.small_payload_threshold and
            chars.estimated_execution_ms < self.small_task_threshold_ms):
            return ExecutorDecision(
                executor_type=ExecutorType.THREAD,
                reason="Small payload and fast execution - threads minimize overhead",
                confidence=0.9,
                estimated_overhead_ms=0.1,  # Thread overhead ~0.1ms
                estimated_execution_ms=chars.estimated_execution_ms,
            )

        # GIL-releasing operations = threads (NumPy, pandas, etc.)
        if chars.is_gil_releasing and not chars.is_cpu_bound:
            return ExecutorDecision(
                executor_type=ExecutorType.THREAD,
                reason="GIL-releasing operation - threads provide parallelism without IPC overhead",
                confidence=0.85,
                estimated_overhead_ms=0.1,
                estimated_execution_ms=chars.estimated_execution_ms,
            )

        # IO-bound = threads
        if chars.is_io_bound:
            return ExecutorDecision(
                executor_type=ExecutorType.THREAD,
                reason="IO-bound operation - threads avoid process overhead",
                confidence=0.8,
                estimated_overhead_ms=0.1,
                estimated_execution_ms=chars.estimated_execution_ms,
            )

        # Large payloads with significant execution = warm pool with shared memory
        if (chars.payload_size_bytes > self.large_payload_threshold and
            chars.estimated_execution_ms > MIN_PROCESS_BENEFIT_MS):
            return ExecutorDecision(
                executor_type=ExecutorType.WARM_POOL,
                reason="Large payload and long execution - warm pool with shared memory",
                confidence=0.85,
                estimated_overhead_ms=5.0,  # Warm pool + shared memory
                estimated_execution_ms=chars.estimated_execution_ms,
                use_shared_memory=True,
            )

        # CPU-bound Python with significant execution = processes
        if chars.is_cpu_bound and chars.estimated_execution_ms > MIN_PROCESS_BENEFIT_MS:
            return ExecutorDecision(
                executor_type=ExecutorType.PROCESS,
                reason="CPU-bound Python - processes bypass GIL",
                confidence=0.8,
                estimated_overhead_ms=20.0,  # Process spawn + serialization
                estimated_execution_ms=chars.estimated_execution_ms,
            )

        # Default: threads for low overhead
        return ExecutorDecision(
            executor_type=ExecutorType.THREAD,
            reason="Default to threads for minimal overhead",
            confidence=0.6,
            estimated_overhead_ms=0.1,
            estimated_execution_ms=chars.estimated_execution_ms,
        )

    def get_executor(self, executor_type: ExecutorType) -> Executor:
        """
        Get executor instance by type.

        Args:
            executor_type: Type of executor needed

        Returns:
            Executor instance
        """
        if executor_type == ExecutorType.THREAD:
            return self._get_thread_executor()
        elif executor_type == ExecutorType.PROCESS:
            return self._get_process_executor()
        elif executor_type == ExecutorType.WARM_POOL:
            return self._get_warm_pool()
        else:
            return self._get_thread_executor()  # Default

    def submit(
        self,
        func: Callable,
        *args,
        force_executor: Optional[ExecutorType] = None,
        **kwargs
    ) -> Tuple[Future, ExecutorDecision]:
        """
        Submit task with adaptive executor selection.

        Args:
            func: Function to execute
            *args: Positional arguments
            force_executor: Force specific executor type
            **kwargs: Keyword arguments

        Returns:
            (future, decision) tuple
        """
        if force_executor:
            decision = ExecutorDecision(
                executor_type=force_executor,
                reason="Forced executor type",
                confidence=1.0,
                estimated_overhead_ms=0.0,
                estimated_execution_ms=0.0,
            )
        else:
            chars = self.analyze_task(func, args, kwargs)
            decision = self.decide_executor(chars)

        executor = self.get_executor(decision.executor_type)
        future = executor.submit(func, *args, **kwargs)

        return future, decision

    def record_execution(self, func: Callable, execution_time_ms: float) -> None:
        """
        Record execution time for learning.

        Args:
            func: Function that was executed
            execution_time_ms: Measured execution time
        """
        task_sig = self._get_task_signature(func)

        with self._history_lock:
            if task_sig not in self._task_history:
                self._task_history[task_sig] = []

            self._task_history[task_sig].append(execution_time_ms)

            # Keep only recent history
            if len(self._task_history[task_sig]) > 100:
                self._task_history[task_sig] = self._task_history[task_sig][-100:]

    def _get_task_signature(self, func: Callable) -> str:
        """Get unique signature for a function."""
        return f"{func.__module__}.{func.__qualname__}"

    def _get_thread_executor(self) -> ThreadPoolExecutor:
        """Get or create thread executor."""
        if self._thread_executor is None:
            with self._thread_lock:
                if self._thread_executor is None:
                    self._thread_executor = ThreadPoolExecutor(
                        max_workers=os.cpu_count() or 4,
                        thread_name_prefix="epochly-adaptive-"
                    )
        return self._thread_executor

    def _get_process_executor(self) -> ProcessPoolExecutor:
        """Get or create process executor."""
        if self._process_executor is None:
            with self._process_lock:
                if self._process_executor is None:
                    self._process_executor = ProcessPoolExecutor(
                        max_workers=os.cpu_count() or 4
                    )
                    _register_executor(self._process_executor)
        return self._process_executor

    def _get_warm_pool(self) -> WarmWorkerPool:
        """Get or create warm worker pool (thread-safe)."""
        if self._warm_pool is None:
            with self._warm_pool_lock:
                if self._warm_pool is None:
                    self._warm_pool = WarmWorkerPool(
                        max_workers=os.cpu_count() or 4,
                        pre_import_modules=['numpy', 'pandas']
                    )
                    self._warm_pool.initialize()
        return self._warm_pool

    def get_stats(self) -> Dict[str, Any]:
        """Get selector statistics."""
        with self._history_lock:
            return {
                'tracked_tasks': len(self._task_history),
                'small_task_threshold_ms': self.small_task_threshold_ms,
                'small_payload_threshold': self.small_payload_threshold,
                'large_payload_threshold': self.large_payload_threshold,
            }

    def shutdown(self) -> None:
        """Shutdown all managed executors and reset references."""
        if self._thread_executor:
            self._thread_executor.shutdown(wait=False)
            self._thread_executor = None
        if self._process_executor:
            self._process_executor.shutdown(wait=False)
            self._process_executor = None
        if self._warm_pool:
            self._warm_pool.shutdown(wait=False)
            self._warm_pool = None


# Global adaptive selector
_global_selector: Optional[AdaptiveExecutorSelector] = None
_selector_lock = threading.Lock()


def get_adaptive_selector() -> AdaptiveExecutorSelector:
    """Get or create global adaptive selector."""
    global _global_selector

    with _selector_lock:
        if _global_selector is None:
            _global_selector = AdaptiveExecutorSelector()
        return _global_selector
