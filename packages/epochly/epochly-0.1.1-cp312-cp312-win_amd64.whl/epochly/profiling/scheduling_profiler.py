"""
Scheduling Overhead Profiler - Per-Task Latency Measurement

Provides detailed breakdown of task scheduling overhead:
- Queue time: Time spent waiting in queue before worker pickup
- Serialization time: Time to pickle/cloudpickle function and arguments
- Worker startup time: First-task initialization overhead
- Execution time: Actual task execution
- Result transfer time: Time to return results to main process

Used to identify bottlenecks and guide optimization decisions:
- When to use thread pool vs process pool
- Optimal chunk size to amortize overhead
- When warm worker pools provide benefit

Author: Epochly Development Team
Date: November 26, 2025
"""

from __future__ import annotations

import os
import sys
import time
import threading
import statistics
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ExecutorType(Enum):
    """Executor type for adaptive selection."""
    THREAD = "thread"
    PROCESS = "process"
    SUBINTERPRETER = "subinterpreter"
    WARM_POOL = "warm_pool"


@dataclass
class TaskLatencyBreakdown:
    """Detailed latency breakdown for a single task."""
    task_id: str
    executor_type: ExecutorType

    # Pre-execution phases
    serialization_time_ns: int = 0  # Time to serialize function + args
    queue_time_ns: int = 0          # Time waiting in queue
    worker_startup_ns: int = 0      # Worker initialization (first task only)
    deserialization_time_ns: int = 0  # Time to deserialize in worker

    # Execution
    execution_time_ns: int = 0      # Actual task execution

    # Post-execution phases
    result_serialization_ns: int = 0  # Time to serialize result
    result_transfer_ns: int = 0       # Time to return to main process

    # Metadata
    task_size_bytes: int = 0        # Estimated task payload size
    result_size_bytes: int = 0      # Estimated result size
    worker_id: int = -1             # Which worker processed this
    was_warm_worker: bool = False   # True if worker was already warm

    @property
    def total_overhead_ns(self) -> int:
        """Total scheduling overhead (everything except execution)."""
        return (self.serialization_time_ns + self.queue_time_ns +
                self.worker_startup_ns + self.deserialization_time_ns +
                self.result_serialization_ns + self.result_transfer_ns)

    @property
    def total_time_ns(self) -> int:
        """Total time from submit to result."""
        return self.total_overhead_ns + self.execution_time_ns

    @property
    def overhead_ratio(self) -> float:
        """Ratio of overhead to total time (0.0 = no overhead, 1.0 = all overhead)."""
        total = self.total_time_ns
        if total == 0:
            return 0.0
        return self.total_overhead_ns / total

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'task_id': self.task_id,
            'executor_type': self.executor_type.value,
            'serialization_ms': self.serialization_time_ns / 1_000_000,
            'queue_ms': self.queue_time_ns / 1_000_000,
            'worker_startup_ms': self.worker_startup_ns / 1_000_000,
            'deserialization_ms': self.deserialization_time_ns / 1_000_000,
            'execution_ms': self.execution_time_ns / 1_000_000,
            'result_serialization_ms': self.result_serialization_ns / 1_000_000,
            'result_transfer_ms': self.result_transfer_ns / 1_000_000,
            'total_overhead_ms': self.total_overhead_ns / 1_000_000,
            'total_time_ms': self.total_time_ns / 1_000_000,
            'overhead_ratio': self.overhead_ratio,
            'task_size_bytes': self.task_size_bytes,
            'result_size_bytes': self.result_size_bytes,
            'worker_id': self.worker_id,
            'was_warm_worker': self.was_warm_worker,
        }


@dataclass
class SchedulingMetrics:
    """Aggregated scheduling metrics over multiple tasks."""

    # Task counts
    total_tasks: int = 0
    failed_tasks: int = 0

    # Overhead statistics (milliseconds)
    avg_serialization_ms: float = 0.0
    avg_queue_ms: float = 0.0
    avg_worker_startup_ms: float = 0.0
    avg_deserialization_ms: float = 0.0
    avg_execution_ms: float = 0.0
    avg_result_transfer_ms: float = 0.0
    avg_total_overhead_ms: float = 0.0

    # Percentiles
    p50_overhead_ms: float = 0.0
    p95_overhead_ms: float = 0.0
    p99_overhead_ms: float = 0.0

    # Overhead ratio statistics
    avg_overhead_ratio: float = 0.0
    max_overhead_ratio: float = 0.0

    # Worker statistics
    warm_worker_ratio: float = 0.0  # Ratio of tasks handled by warm workers
    cold_start_penalty_ms: float = 0.0  # Average extra overhead for cold starts

    # Size statistics
    avg_task_size_bytes: int = 0
    avg_result_size_bytes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_tasks': self.total_tasks,
            'failed_tasks': self.failed_tasks,
            'avg_serialization_ms': self.avg_serialization_ms,
            'avg_queue_ms': self.avg_queue_ms,
            'avg_worker_startup_ms': self.avg_worker_startup_ms,
            'avg_deserialization_ms': self.avg_deserialization_ms,
            'avg_execution_ms': self.avg_execution_ms,
            'avg_result_transfer_ms': self.avg_result_transfer_ms,
            'avg_total_overhead_ms': self.avg_total_overhead_ms,
            'p50_overhead_ms': self.p50_overhead_ms,
            'p95_overhead_ms': self.p95_overhead_ms,
            'p99_overhead_ms': self.p99_overhead_ms,
            'avg_overhead_ratio': self.avg_overhead_ratio,
            'max_overhead_ratio': self.max_overhead_ratio,
            'warm_worker_ratio': self.warm_worker_ratio,
            'cold_start_penalty_ms': self.cold_start_penalty_ms,
            'avg_task_size_bytes': self.avg_task_size_bytes,
            'avg_result_size_bytes': self.avg_result_size_bytes,
        }


class SchedulingProfiler:
    """
    Comprehensive per-task latency profiler.

    Measures scheduling overhead at each phase:
    1. Serialization: Pickling function and arguments
    2. Queueing: Waiting for worker availability
    3. Worker startup: Cold start initialization (first task)
    4. Deserialization: Unpickling in worker
    5. Execution: Actual task work
    6. Result transfer: Returning result to main process

    Usage:
        profiler = SchedulingProfiler()

        with profiler.profile_task("task-1", ExecutorType.PROCESS) as ctx:
            # Record serialization
            ctx.record_serialization(start_ns, end_ns, payload_size)

            # Submit task
            future = executor.submit(func, *args)
            ctx.record_submit_time()

            # Wait for result
            result = future.result()
            ctx.record_completion_time()

        # Get metrics
        metrics = profiler.get_metrics()
        print(f"Average overhead: {metrics.avg_total_overhead_ms:.2f}ms")
    """

    def __init__(self, max_history: int = 10000, window_seconds: float = 300.0):
        """
        Initialize profiler.

        Args:
            max_history: Maximum number of task records to retain
            window_seconds: Time window for metrics (default: 5 minutes)
        """
        self._max_history = max_history
        self._window_seconds = window_seconds

        # Task history (thread-safe access)
        self._history: deque = deque(maxlen=max_history)
        self._lock = threading.Lock()

        # Worker tracking for warm/cold detection
        self._worker_first_task: Dict[int, float] = {}  # worker_id -> first task timestamp

        # Active profiling contexts
        self._active_contexts: Dict[str, 'TaskProfilingContext'] = {}

        # Running statistics
        self._total_tasks = 0
        self._failed_tasks = 0

    def profile_task(self, task_id: str, executor_type: ExecutorType) -> 'TaskProfilingContext':
        """
        Create profiling context for a task.

        Args:
            task_id: Unique task identifier
            executor_type: Type of executor being used

        Returns:
            TaskProfilingContext for recording measurements
        """
        ctx = TaskProfilingContext(self, task_id, executor_type)

        with self._lock:
            self._active_contexts[task_id] = ctx

        return ctx

    def _record_task_completion(self, breakdown: TaskLatencyBreakdown, success: bool = True) -> None:
        """Record task completion (internal)."""
        timestamp = time.time()

        with self._lock:
            self._history.append((timestamp, breakdown))
            self._total_tasks += 1

            if not success:
                self._failed_tasks += 1

            # Track worker warm status
            if breakdown.worker_id >= 0:
                if breakdown.worker_id not in self._worker_first_task:
                    self._worker_first_task[breakdown.worker_id] = timestamp
                    breakdown.was_warm_worker = False
                else:
                    breakdown.was_warm_worker = True

            # Remove from active
            self._active_contexts.pop(breakdown.task_id, None)

    def get_metrics(self) -> SchedulingMetrics:
        """
        Calculate aggregated scheduling metrics.

        Returns:
            SchedulingMetrics with averages, percentiles, and ratios
        """
        with self._lock:
            # Filter to window
            cutoff_time = time.time() - self._window_seconds
            recent = [(ts, bd) for ts, bd in self._history if ts >= cutoff_time]

            if not recent:
                return SchedulingMetrics()

            breakdowns = [bd for _, bd in recent]

            # Calculate averages
            metrics = SchedulingMetrics(
                total_tasks=len(breakdowns),
                failed_tasks=self._failed_tasks,
            )

            # Aggregate statistics
            ser_times = [bd.serialization_time_ns / 1_000_000 for bd in breakdowns]
            queue_times = [bd.queue_time_ns / 1_000_000 for bd in breakdowns]
            startup_times = [bd.worker_startup_ns / 1_000_000 for bd in breakdowns]
            deser_times = [bd.deserialization_time_ns / 1_000_000 for bd in breakdowns]
            exec_times = [bd.execution_time_ns / 1_000_000 for bd in breakdowns]
            result_times = [bd.result_transfer_ns / 1_000_000 for bd in breakdowns]
            overhead_times = [bd.total_overhead_ns / 1_000_000 for bd in breakdowns]
            overhead_ratios = [bd.overhead_ratio for bd in breakdowns]

            metrics.avg_serialization_ms = statistics.mean(ser_times)
            metrics.avg_queue_ms = statistics.mean(queue_times)
            metrics.avg_worker_startup_ms = statistics.mean(startup_times)
            metrics.avg_deserialization_ms = statistics.mean(deser_times)
            metrics.avg_execution_ms = statistics.mean(exec_times)
            metrics.avg_result_transfer_ms = statistics.mean(result_times)
            metrics.avg_total_overhead_ms = statistics.mean(overhead_times)

            # Percentiles
            sorted_overhead = sorted(overhead_times)
            n = len(sorted_overhead)
            metrics.p50_overhead_ms = sorted_overhead[n // 2]
            metrics.p95_overhead_ms = sorted_overhead[int(n * 0.95)]
            metrics.p99_overhead_ms = sorted_overhead[int(n * 0.99)]

            # Overhead ratio
            metrics.avg_overhead_ratio = statistics.mean(overhead_ratios)
            metrics.max_overhead_ratio = max(overhead_ratios)

            # Warm worker statistics
            warm_count = sum(1 for bd in breakdowns if bd.was_warm_worker)
            metrics.warm_worker_ratio = warm_count / len(breakdowns)

            # Cold start penalty
            cold_overheads = [bd.total_overhead_ns for bd in breakdowns if not bd.was_warm_worker]
            warm_overheads = [bd.total_overhead_ns for bd in breakdowns if bd.was_warm_worker]

            if cold_overheads and warm_overheads:
                avg_cold = statistics.mean(cold_overheads) / 1_000_000
                avg_warm = statistics.mean(warm_overheads) / 1_000_000
                metrics.cold_start_penalty_ms = avg_cold - avg_warm

            # Size statistics
            task_sizes = [bd.task_size_bytes for bd in breakdowns if bd.task_size_bytes > 0]
            result_sizes = [bd.result_size_bytes for bd in breakdowns if bd.result_size_bytes > 0]

            if task_sizes:
                metrics.avg_task_size_bytes = int(statistics.mean(task_sizes))
            if result_sizes:
                metrics.avg_result_size_bytes = int(statistics.mean(result_sizes))

            return metrics

    def get_task_breakdown(self, task_id: str) -> Optional[TaskLatencyBreakdown]:
        """Get breakdown for a specific task."""
        with self._lock:
            for _, breakdown in self._history:
                if breakdown.task_id == task_id:
                    return breakdown
        return None

    def get_recent_breakdowns(self, count: int = 100) -> List[TaskLatencyBreakdown]:
        """Get most recent task breakdowns."""
        with self._lock:
            recent = list(self._history)[-count:]
            return [bd for _, bd in recent]

    def get_overhead_histogram(self, bucket_count: int = 20) -> Dict[str, Any]:
        """
        Get histogram of overhead times for visualization.

        Returns:
            Dict with bucket boundaries and counts
        """
        with self._lock:
            cutoff_time = time.time() - self._window_seconds
            recent = [bd for ts, bd in self._history if ts >= cutoff_time]

            if not recent:
                return {'buckets': [], 'counts': [], 'unit': 'ms'}

            overhead_ms = [bd.total_overhead_ns / 1_000_000 for bd in recent]
            min_val = min(overhead_ms)
            max_val = max(overhead_ms)

            bucket_size = (max_val - min_val) / bucket_count if max_val > min_val else 1.0
            buckets = [min_val + i * bucket_size for i in range(bucket_count + 1)]
            counts = [0] * bucket_count

            for val in overhead_ms:
                bucket_idx = min(int((val - min_val) / bucket_size), bucket_count - 1)
                counts[bucket_idx] += 1

            return {
                'buckets': buckets,
                'counts': counts,
                'unit': 'ms',
                'min': min_val,
                'max': max_val,
                'mean': statistics.mean(overhead_ms),
            }

    def suggest_optimizations(self) -> List[str]:
        """
        Suggest optimizations based on profiling data.

        Returns:
            List of optimization suggestions
        """
        metrics = self.get_metrics()
        suggestions = []

        if metrics.total_tasks < 10:
            return ["Insufficient data for optimization suggestions (need >= 10 tasks)"]

        # High serialization overhead
        if metrics.avg_serialization_ms > metrics.avg_execution_ms * 0.2:
            suggestions.append(
                f"HIGH SERIALIZATION OVERHEAD: {metrics.avg_serialization_ms:.1f}ms "
                f"(>{20}% of execution). Consider using shared memory for large payloads "
                "or switching to ThreadPoolExecutor for shared-state access."
            )

        # High queue time
        if metrics.avg_queue_ms > 10:
            suggestions.append(
                f"HIGH QUEUE TIME: {metrics.avg_queue_ms:.1f}ms average. "
                "Consider increasing worker count or using adaptive chunking "
                "to reduce queue contention."
            )

        # Cold start penalty
        if metrics.cold_start_penalty_ms > 50:
            suggestions.append(
                f"COLD START PENALTY: {metrics.cold_start_penalty_ms:.1f}ms extra overhead. "
                "Use warm worker pools or persistent process pools to eliminate startup cost."
            )

        # High overall overhead ratio
        if metrics.avg_overhead_ratio > 0.5:
            suggestions.append(
                f"OVERHEAD DOMINATES: {metrics.avg_overhead_ratio*100:.1f}% of time is overhead. "
                "Tasks may be too small for process parallelization. Consider:\n"
                "  - Batch small tasks into larger chunks\n"
                "  - Use ThreadPoolExecutor for GIL-releasing work\n"
                "  - Inline execution for tasks <10ms"
            )

        # Low warm worker ratio
        if metrics.warm_worker_ratio < 0.8 and metrics.total_tasks > 100:
            suggestions.append(
                f"LOW WARM WORKER RATIO: {metrics.warm_worker_ratio*100:.1f}% warm. "
                "Workers are being recycled too often. Keep worker pools persistent."
            )

        if not suggestions:
            suggestions.append(
                f"GOOD: Overhead ratio {metrics.avg_overhead_ratio*100:.1f}% is acceptable. "
                "No critical optimizations needed."
            )

        return suggestions

    def clear(self) -> None:
        """Clear all profiling data."""
        with self._lock:
            self._history.clear()
            self._worker_first_task.clear()
            self._active_contexts.clear()
            self._total_tasks = 0
            self._failed_tasks = 0


class TaskProfilingContext:
    """
    Context manager for profiling a single task.

    Records timestamps at each phase of task execution.
    """

    def __init__(self, profiler: SchedulingProfiler, task_id: str, executor_type: ExecutorType):
        self._profiler = profiler
        self._breakdown = TaskLatencyBreakdown(task_id=task_id, executor_type=executor_type)

        # Timestamps
        self._start_time_ns: int = 0
        self._submit_time_ns: int = 0
        self._pickup_time_ns: int = 0
        self._exec_start_ns: int = 0
        self._exec_end_ns: int = 0
        self._complete_time_ns: int = 0

    def __enter__(self) -> 'TaskProfilingContext':
        self._start_time_ns = time.perf_counter_ns()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._complete_time_ns = time.perf_counter_ns()

        # Calculate result transfer time
        if self._exec_end_ns and self._complete_time_ns:
            self._breakdown.result_transfer_ns = self._complete_time_ns - self._exec_end_ns

        # Record completion
        success = exc_type is None
        self._profiler._record_task_completion(self._breakdown, success)

        return False  # Don't suppress exceptions

    def record_serialization(self, start_ns: int, end_ns: int, payload_size: int = 0) -> None:
        """Record serialization phase."""
        self._breakdown.serialization_time_ns = end_ns - start_ns
        self._breakdown.task_size_bytes = payload_size

    def record_submit_time(self) -> None:
        """Record when task was submitted to queue."""
        self._submit_time_ns = time.perf_counter_ns()

    def record_worker_pickup(self, worker_id: int = -1) -> None:
        """Record when worker picked up task."""
        self._pickup_time_ns = time.perf_counter_ns()

        # Calculate queue time
        if self._submit_time_ns:
            self._breakdown.queue_time_ns = self._pickup_time_ns - self._submit_time_ns

        self._breakdown.worker_id = worker_id

    def record_worker_startup(self, startup_ns: int) -> None:
        """Record worker initialization time (first task only)."""
        self._breakdown.worker_startup_ns = startup_ns

    def record_deserialization(self, deser_ns: int) -> None:
        """Record deserialization time in worker."""
        self._breakdown.deserialization_time_ns = deser_ns

    def record_execution_start(self) -> None:
        """Record when actual execution started."""
        self._exec_start_ns = time.perf_counter_ns()

    def record_execution_end(self, result_size: int = 0) -> None:
        """Record when execution completed."""
        self._exec_end_ns = time.perf_counter_ns()

        if self._exec_start_ns:
            self._breakdown.execution_time_ns = self._exec_end_ns - self._exec_start_ns

        self._breakdown.result_size_bytes = result_size

    def record_result_serialization(self, ser_ns: int) -> None:
        """Record result serialization time."""
        self._breakdown.result_serialization_ns = ser_ns

    def get_breakdown(self) -> TaskLatencyBreakdown:
        """Get current breakdown (may be incomplete if still profiling)."""
        return self._breakdown


# Utility function for profiling executor submit
def profile_executor_submit(
    profiler: SchedulingProfiler,
    executor,
    func: Callable,
    *args,
    executor_type: ExecutorType = ExecutorType.PROCESS,
    task_id: Optional[str] = None,
    **kwargs
) -> Tuple[Future, TaskProfilingContext]:
    """
    Profile a task submission to an executor.

    Args:
        profiler: SchedulingProfiler instance
        executor: ProcessPoolExecutor or ThreadPoolExecutor
        func: Function to execute
        *args: Function arguments
        executor_type: Type of executor
        task_id: Optional task ID (auto-generated if not provided)
        **kwargs: Function keyword arguments

    Returns:
        (future, context) tuple
    """
    import uuid

    if task_id is None:
        task_id = f"task-{uuid.uuid4().hex[:8]}"

    ctx = profiler.profile_task(task_id, executor_type)

    # Measure serialization
    ser_start = time.perf_counter_ns()
    try:
        import cloudpickle
        pickled = cloudpickle.dumps((func, args, kwargs))
        payload_size = len(pickled)
    except Exception:
        payload_size = 0
    ser_end = time.perf_counter_ns()

    ctx.record_serialization(ser_start, ser_end, payload_size)

    # Submit to executor
    ctx.record_submit_time()
    future = executor.submit(func, *args, **kwargs)

    return future, ctx


# Global profiler instance
_global_profiler: Optional[SchedulingProfiler] = None
_profiler_lock = threading.Lock()


def get_scheduling_profiler() -> SchedulingProfiler:
    """Get or create global scheduling profiler."""
    global _global_profiler

    with _profiler_lock:
        if _global_profiler is None:
            _global_profiler = SchedulingProfiler()
        return _global_profiler


def reset_scheduling_profiler() -> None:
    """Reset global scheduling profiler."""
    global _global_profiler

    with _profiler_lock:
        if _global_profiler:
            _global_profiler.clear()
        _global_profiler = None
