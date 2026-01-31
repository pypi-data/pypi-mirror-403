"""
Parallelism Metrics Collection for Benchmarking

Tracks parallel execution statistics to validate Epochly's parallelism features:
- Worker pool utilization (configured vs active)
- CPU utilization per worker
- Task distribution and scheduling overhead
- Parallelism degree achieved

This module provides benchmarking-specific metrics separate from general
runtime monitoring (ResourceTracker/InFlightTracker).

Author: Epochly Development Team
Date: November 19, 2025
"""

import threading
import time
import psutil
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ParallelismMetrics:
    """
    Metrics for parallel execution performance.

    Attributes:
        configured_workers: Number of workers configured
        active_workers_peak: Maximum number of workers active simultaneously
        active_workers_mean: Average number of active workers
        cpu_utilization_per_worker: CPU usage % per worker ID
        task_count: Total number of tasks executed
        scheduling_latency_ms: Per-task submit-to-start latency in milliseconds
        execution_duration_sec: Total execution time in seconds
    """
    configured_workers: int
    active_workers_peak: int
    active_workers_mean: float
    cpu_utilization_per_worker: Dict[int, float]
    task_count: int
    scheduling_latency_ms: List[float]
    execution_duration_sec: float

    @property
    def parallelism_degree(self) -> float:
        """
        Actual parallelism achieved (vs configured).

        Returns:
            Float ratio (0.0 to 1.0) of mean_active / configured
            1.0 = perfect utilization, 0.0 = no parallelism
        """
        if self.configured_workers == 0:
            return 0.0
        return self.active_workers_mean / self.configured_workers

    @property
    def scheduling_overhead_ms(self) -> float:
        """
        Mean scheduling latency across all tasks.

        Returns:
            Average time in milliseconds from task submission to task start
        """
        if not self.scheduling_latency_ms:
            return 0.0
        return sum(self.scheduling_latency_ms) / len(self.scheduling_latency_ms)


class ParallelismTracker:
    """
    Track parallelism metrics during benchmark execution.

    Monitors worker activity, CPU utilization, and task scheduling to validate
    that Epochly's parallel execution features are actually being used.

    Usage:
        tracker = ParallelismTracker(configured_workers=16)
        tracker.start_tracking()

        # Run benchmark (Epochly activates workers, executes tasks)
        # Tracker samples worker activity every 100ms

        tracker.stop_tracking()
        metrics = tracker.get_metrics()

        print(f"Parallelism degree: {metrics.parallelism_degree:.2f}")
        print(f"Peak workers: {metrics.active_workers_peak}")
        print(f"Scheduling overhead: {metrics.scheduling_overhead_ms:.2f}ms")

    Thread Safety:
        All methods are thread-safe. Safe to call record_task_scheduled()
        from multiple worker threads concurrently.

    Integration Points:
        - SubInterpreterExecutor: Reports worker activation/deactivation
        - BatchDispatcher: Reports task scheduling latency
        - Auto-profiler: Tracks parallel function execution
    """

    def __init__(self, configured_workers: int):
        """
        Initialize parallelism tracker.

        Args:
            configured_workers: Number of workers configured in pool
        """
        self.configured_workers = configured_workers

        # Tracking state
        self._active_count_samples: List[int] = []
        self._worker_cpu_usage: Dict[int, List[float]] = {}
        self._task_latencies: List[float] = []
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

        # Background sampling thread
        self._sampling_thread: Optional[threading.Thread] = None
        self._stop_sampling = threading.Event()

        # Thread safety
        self._lock = threading.Lock()

    def start_tracking(self) -> None:
        """
        Begin tracking parallelism metrics.

        Starts background thread that samples worker activity every 100ms.

        Thread Safety:
            Safe to call from any thread.
        """
        with self._lock:
            self._start_time = time.time()
            self._stop_sampling.clear()

            # Reset previous run data
            self._active_count_samples.clear()
            self._worker_cpu_usage.clear()
            self._task_latencies.clear()
            self._end_time = None

            # Start background sampling thread
            self._sampling_thread = threading.Thread(
                target=self._sample_workers,
                daemon=True,
                name="ParallelismTrackerSampler"
            )
            self._sampling_thread.start()

    def stop_tracking(self) -> None:
        """
        Stop tracking and finalize metrics.

        Stops background sampling thread and records end time.

        Thread Safety:
            Safe to call from any thread.
        """
        with self._lock:
            self._end_time = time.time()
            self._stop_sampling.set()

        # Wait for sampling thread to finish (with timeout)
        if self._sampling_thread and self._sampling_thread.is_alive():
            self._sampling_thread.join(timeout=1.0)

    def record_task_scheduled(
        self,
        task_id: int,
        submit_time: float,
        start_time: float
    ) -> None:
        """
        Record task scheduling event.

        Args:
            task_id: Unique task identifier
            submit_time: Time when task was submitted (seconds since epoch)
            start_time: Time when task started executing (seconds since epoch)

        Thread Safety:
            Safe to call from multiple threads concurrently.
        """
        latency_ms = (start_time - submit_time) * 1000
        with self._lock:
            self._task_latencies.append(latency_ms)

    def get_metrics(self) -> ParallelismMetrics:
        """
        Compute final parallelism metrics.

        Returns:
            ParallelismMetrics with statistical summary of parallel execution

        Thread Safety:
            Safe to call while tracking is active. Returns snapshot of current state.
        """
        with self._lock:
            # Compute worker activity statistics
            if self._active_count_samples:
                active_peak = max(self._active_count_samples)
                active_mean = sum(self._active_count_samples) / len(self._active_count_samples)
            else:
                active_peak = 0
                active_mean = 0.0

            # Compute execution duration
            end_time = self._end_time if self._end_time is not None else time.time()
            start_time = self._start_time if self._start_time is not None else 0.0
            duration = end_time - start_time

            # Compute per-worker CPU utilization
            cpu_per_worker = {}
            for worker_id, samples in self._worker_cpu_usage.items():
                if samples:
                    cpu_per_worker[worker_id] = sum(samples) / len(samples)

            return ParallelismMetrics(
                configured_workers=self.configured_workers,
                active_workers_peak=active_peak,
                active_workers_mean=active_mean,
                cpu_utilization_per_worker=cpu_per_worker,
                task_count=len(self._task_latencies),
                scheduling_latency_ms=self._task_latencies.copy(),
                execution_duration_sec=duration
            )

    def _sample_workers(self) -> None:
        """
        Background sampling of worker activity.

        Runs every 100ms to capture worker count snapshots.

        This method queries the Epochly core for actual executor status,
        falling back to process-based heuristics if the core is unavailable.
        """
        while not self._stop_sampling.wait(timeout=0.1):  # 100ms sample interval
            # Sample active worker count from actual executor
            active_workers = self._count_active_workers()

            with self._lock:
                self._active_count_samples.append(active_workers)

    def _count_active_workers(self) -> int:
        """
        Count currently active Epochly workers.

        Queries the Epochly core for actual executor status. Falls back to
        process-based heuristics if the core is not initialized.

        Returns:
            Number of active workers from the actual executor pool
        """
        try:
            # Primary integration: Query Epochly core for executor status
            from ..core.epochly_core import get_core
            core = get_core()

            if core and core._initialized:
                # Try Level 3 executor first (sub-interpreters or fallback)
                if hasattr(core, '_level3_executor') and core._level3_executor:
                    try:
                        executor_info = core._level3_executor.get_executor_info()
                        # Get active workers from executor info
                        if 'active_interpreters' in executor_info:
                            return executor_info['active_interpreters']
                        elif 'workers' in executor_info:
                            return executor_info['workers']
                    except Exception:
                        pass

                # Try Level 1 thread executor as fallback
                if hasattr(core, '_thread_executor') and core._thread_executor:
                    try:
                        executor_status = core._thread_executor.get_status()
                        return executor_status.get('active_workers', 0)
                    except Exception:
                        pass

            # Secondary fallback: Use psutil to count Python processes
            # This is a heuristic for when Epochly core is not available
            try:
                current_process = psutil.Process()
                children = current_process.children(recursive=True)
                python_children = [
                    p for p in children
                    if 'python' in p.name().lower() or 'epochly' in p.name().lower()
                ]
                return len(python_children)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process disappeared or permission denied
                return 0

        except Exception:
            # Final fallback: Return 0 if all methods fail
            return 0

    def set_active_worker_count(self, count: int) -> None:
        """
        Manually set active worker count (for testing or external integration).

        Args:
            count: Number of active workers

        Thread Safety:
            Safe to call from any thread.
        """
        with self._lock:
            self._active_count_samples.append(count)

    def record_worker_cpu_usage(self, worker_id: int, cpu_percent: float) -> None:
        """
        Record CPU usage for specific worker.

        Args:
            worker_id: Worker identifier (0 to configured_workers-1)
            cpu_percent: CPU usage percentage (0.0 to 100.0)

        Thread Safety:
            Safe to call from any thread.
        """
        with self._lock:
            if worker_id not in self._worker_cpu_usage:
                self._worker_cpu_usage[worker_id] = []
            self._worker_cpu_usage[worker_id].append(cpu_percent)
