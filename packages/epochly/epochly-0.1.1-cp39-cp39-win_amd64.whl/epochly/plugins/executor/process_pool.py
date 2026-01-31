"""
High-Performance Process Executor with Shared Memory Support

Per perf_fixes3.md Section 5.4: ForkingProcessExecutor replaces standard ProcessPoolExecutor
for CPU-bound workloads, using shared memory buffers to avoid pickling overhead.

Key Features:
- Pre-forked workers (fork on POSIX, spawn on Windows)
- Shared memory buffer reuse for numpy/pandas payloads
- Task queue with zero-copy handoffs via ShareableList
- Warm pool: workers stay hot, graceful resize
- Instrumentation: serialization time, queue wait, execution duration

Performance Target:
- Serialization time <10% of execution time for large CPU workloads

Author: Epochly Development Team
Created: 2025-11-15
"""

import os
import sys
import time
import threading
import multiprocessing
import logging
from multiprocessing import shared_memory
from concurrent.futures import Future
from typing import Any, Callable, Optional, Dict, List
from dataclasses import dataclass, field
from queue import Queue, Empty
import numpy as np

# Use dill for better pickling support (lambdas, closures, etc.)
try:
    import dill
    pickle = dill
except ImportError:
    import pickle

# Import shared memory manager for buffer management
from .shared_memory_manager import SharedMemoryManager, ZeroCopyBuffer


@dataclass
class TaskDescriptor:
    """Descriptor for a task submitted to worker pool."""
    task_id: str
    func_name: str
    use_shared_memory: bool
    shared_memory_refs: List[str] = field(default_factory=list)
    pickled_args: Optional[bytes] = None
    submit_time: float = field(default_factory=time.time)


@dataclass
class ExecutionStats:
    """Statistics for task execution instrumentation."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_serialization_time: float = 0.0
    total_queue_wait_time: float = 0.0
    total_execution_time: float = 0.0
    shared_memory_transfers: int = 0
    pickle_transfers: int = 0
    buffer_reuses: int = 0


@dataclass
class SpikeInstrumentation:
    """
    Instrumentation for detecting and diagnosing performance spikes.

    Added Dec 2025 to diagnose P1-3: 505ms spike (38x variance).
    Enable with: export EPOCHLY_DEBUG_SPIKE_DETECTION=1
    """
    # Task timing (for variance detection)
    task_times_ms: List[float] = field(default_factory=list)
    max_task_time_ms: float = 0.0
    min_task_time_ms: float = float('inf')

    # Worker health events
    worker_deaths_detected: int = 0
    worker_respawns: int = 0
    last_worker_death_time: Optional[float] = None

    # Scale events (correlation with spikes)
    scale_down_events: int = 0
    scale_up_events: int = 0
    last_scale_event_time: Optional[float] = None

    # Spike detection
    spike_count: int = 0  # Tasks >10x median time
    spike_times_ms: List[float] = field(default_factory=list)
    spike_contexts: List[str] = field(default_factory=list)  # Context when spike occurred

    def record_task_time(self, time_ms: float, context: str = ""):
        """Record task execution time and detect spikes."""
        self.task_times_ms.append(time_ms)
        self.max_task_time_ms = max(self.max_task_time_ms, time_ms)
        if time_ms > 0:
            self.min_task_time_ms = min(self.min_task_time_ms, time_ms)

        # Detect spike: >10x median (need at least 3 samples)
        if len(self.task_times_ms) >= 3:
            sorted_times = sorted(self.task_times_ms)
            median = sorted_times[len(sorted_times) // 2]
            if median > 0 and time_ms > median * 10:
                self.spike_count += 1
                self.spike_times_ms.append(time_ms)
                self.spike_contexts.append(context)

    def record_worker_death(self, worker_id: int):
        """Record worker death event."""
        self.worker_deaths_detected += 1
        self.last_worker_death_time = time.time()

    def record_scale_event(self, direction: str, old_count: int, new_count: int):
        """Record scale up/down event."""
        if direction == 'up':
            self.scale_up_events += 1
        else:
            self.scale_down_events += 1
        self.last_scale_event_time = time.time()

    def get_variance_ratio(self) -> float:
        """Calculate variance ratio (max/min)."""
        if self.min_task_time_ms > 0 and self.min_task_time_ms != float('inf'):
            return self.max_task_time_ms / self.min_task_time_ms
        return 0.0


class ForkingProcessExecutor:
    """
    High-performance process executor with shared memory buffer reuse.

    Per perf_fixes3.md Section 5.4: Eliminates pickling overhead for large
    numpy/pandas payloads by using shared memory buffers.

    Usage:
        with ForkingProcessExecutor(max_workers=4) as executor:
            future = executor.submit(compute_func, large_array)
            result = future.result()
    """

    def __init__(self, max_workers: Optional[int] = None,
                 shared_memory_threshold: int = 1024 * 1024):  # 1MB threshold
        """
        Initialize ForkingProcessExecutor.

        Args:
            max_workers: Number of worker processes (default: cpu_count)
            shared_memory_threshold: Size threshold for using shared memory (default: 1MB)
        """
        self.logger = logging.getLogger(__name__)

        # Worker configuration
        self.num_workers = max_workers or multiprocessing.cpu_count()
        self._shared_memory_threshold = shared_memory_threshold

        # Phase 2 (Dec 2025): Use forkserver_manager for centralized start method selection
        # This ensures consistent behavior across all ProcessPool creation paths
        try:
            from epochly.core.forkserver_manager import get_recommended_start_method
            self._context_method = get_recommended_start_method()
            self._mp_context = multiprocessing.get_context(self._context_method)
        except ImportError:
            # Fallback: Platform-specific context selection
            # Use forkserver on POSIX (safer than fork in multi-threaded environments)
            # Use spawn on Windows (only option)
            if sys.platform == 'win32':
                self._context_method = 'spawn'
                self._mp_context = multiprocessing.get_context('spawn')
            else:
                self._context_method = 'forkserver'
                self._mp_context = multiprocessing.get_context('forkserver')

        self.logger.info(f"Initializing ForkingProcessExecutor: {self.num_workers} workers, "
                        f"context={self._context_method}")

        # Shared memory manager for buffer reuse
        self._shared_memory_manager = SharedMemoryManager(
            pool_size=64 * 1024 * 1024  # 64MB pool for shared buffers
        )

        # Worker process pool (pre-forked, stays warm)
        self._workers: List[multiprocessing.Process] = []
        self._task_queue = self._mp_context.Queue()
        self._result_queue = self._mp_context.Queue()

        # Task tracking (thread-safe access required)
        self._pending_futures: Dict[str, Future] = {}
        self._futures_lock = threading.Lock()  # Protect pending_futures dict
        self._next_task_id = 0
        self._task_id_lock = threading.Lock()

        # Buffer lifecycle tracking (Task 3.1 fix for >90 score)
        self._task_buffer_refs: Dict[str, List[str]] = {}  # task_id -> buffer_ids
        self._buffer_lock = threading.Lock()

        # Instrumentation
        self._stats = ExecutionStats()
        self._stats_lock = threading.Lock()

        # Spike detection instrumentation (P1-3: 505ms spike diagnosis)
        # Enable with: export EPOCHLY_DEBUG_SPIKE_DETECTION=1
        self._spike_detection_enabled = os.environ.get('EPOCHLY_DEBUG_SPIKE_DETECTION', '0') == '1'
        self._spike_instrumentation = SpikeInstrumentation()
        self._spike_lock = threading.Lock()  # Protect spike instrumentation

        # Worker health monitoring (P1-3: detect dead workers)
        self._last_worker_health_check = time.time()
        self._worker_health_check_interval = 1.0  # Check every 1 second
        self._dead_workers_detected = 0

        # Lifecycle management
        self._shutdown_event = self._mp_context.Event()
        self._result_collector_thread: Optional[threading.Thread] = None

        # Initialize workers
        self._initialize_workers()

        # Start result collector
        self._start_result_collector()

    def _initialize_workers(self):
        """Create and start worker processes."""
        # NOTE: epochly_worker_initializer is called at the start of _worker_main
        # (Process() doesn't accept initializer - that's for ProcessPoolExecutor)

        for worker_id in range(self.num_workers):
            process = self._mp_context.Process(
                target=_worker_main,
                args=(
                    worker_id,
                    self._task_queue,
                    self._result_queue,
                    self._shutdown_event,
                    self._shared_memory_manager._shm_name  # Pass shared memory name
                ),
                daemon=False
            )
            process.start()
            self._workers.append(process)

        self.logger.info(f"Started {len(self._workers)} worker processes")

    def _start_result_collector(self):
        """Start background thread to collect results from workers."""
        self._result_collector_thread = threading.Thread(
            target=self._collect_results,
            daemon=True,
            name="ForkingProcessExecutor-ResultCollector"
        )
        self._result_collector_thread.start()

    def _check_worker_health(self) -> int:
        """
        Check worker health and detect dead workers.

        P1-3 instrumentation: Dead workers correlate with spawn overhead spikes.
        If a worker dies and is replaced, the new worker takes ~500ms to spawn.

        Returns:
            Number of dead workers detected
        """
        now = time.time()
        if now - self._last_worker_health_check < self._worker_health_check_interval:
            return 0  # Not time to check yet

        self._last_worker_health_check = now
        dead_count = 0

        for i, worker in enumerate(self._workers):
            if not worker.is_alive():
                dead_count += 1
                self._dead_workers_detected += 1

                if self._spike_detection_enabled:
                    with self._spike_lock:
                        self._spike_instrumentation.record_worker_death(i)
                        self.logger.warning(
                            f"[SPIKE_DETECTION] Worker {i} is DEAD! "
                            f"Total dead workers detected: {self._dead_workers_detected}. "
                            f"This correlates with spawn overhead (~500ms spike)."
                        )

        return dead_count

    def _collect_results(self):
        """Collect results from worker processes and resolve futures."""
        # Keep collecting until shutdown AND queue is drained AND all futures resolved
        shutdown_requested = False
        shutdown_start_time = None
        MAX_SHUTDOWN_WAIT = 5.0  # Maximum seconds to wait after shutdown signal before forcing exit

        while True:
            try:
                # P1-3: Check worker health periodically to detect dead workers
                # Dead workers correlate with spawn overhead spikes (~500ms)
                self._check_worker_health()

                # Get result with timeout
                task_id, success, result, exec_time, queue_wait = self._result_queue.get(timeout=0.05)

                # Reset shutdown timer if we got a result (still processing work)
                shutdown_start_time = None

                # Handle worker error messages (init_error, worker_error)
                if task_id in ('init_error', 'worker_error'):
                    self.logger.error(f"Worker error: {result}")
                    # Don't update stats or resolve futures for error messages
                    continue

                # Calculate total task time (execution + queue wait)
                total_task_time_ms = (exec_time + queue_wait) * 1000

                # P1-3: Record task time for spike detection
                if self._spike_detection_enabled:
                    context = f"task={task_id}, exec={exec_time*1000:.1f}ms, queue={queue_wait*1000:.1f}ms"
                    spike_detected = False

                    with self._spike_lock:
                        prev_spike_count = self._spike_instrumentation.spike_count
                        self._spike_instrumentation.record_task_time(total_task_time_ms, context)
                        spike_detected = self._spike_instrumentation.spike_count > prev_spike_count

                    # Log spike immediately when detected
                    if spike_detected:
                        variance_ratio = self._spike_instrumentation.get_variance_ratio()
                        self.logger.warning(
                            f"[SPIKE_DETECTION] SPIKE DETECTED! "
                            f"Task {task_id}: {total_task_time_ms:.1f}ms "
                            f"(exec={exec_time*1000:.1f}ms, queue_wait={queue_wait*1000:.1f}ms). "
                            f"Variance ratio: {variance_ratio:.1f}x. "
                            f"Worker deaths: {self._spike_instrumentation.worker_deaths_detected}, "
                            f"Scale events: up={self._spike_instrumentation.scale_up_events}, "
                            f"down={self._spike_instrumentation.scale_down_events}"
                        )

                # Update statistics
                with self._stats_lock:
                    self._stats.completed_tasks += 1
                    self._stats.total_execution_time += exec_time
                    self._stats.total_queue_wait_time += queue_wait

                    if not success:
                        self._stats.failed_tasks += 1

                # Resolve future (thread-safe)
                future = None
                with self._futures_lock:
                    if task_id in self._pending_futures:
                        future = self._pending_futures.pop(task_id)

                # Release shared memory buffers for this task (Task 3.1 fix)
                self._release_shared_buffers(task_id)

                # Set result outside lock to avoid holding lock during callback
                if future:
                    if success:
                        future.set_result(result)
                    else:
                        future.set_exception(result)

            except Empty:
                # No results available - check worker health while idle
                self._check_worker_health()

                # Check if we should exit
                shutdown_requested = self._shutdown_event.is_set()

                if shutdown_requested:
                    # Track shutdown start time for timeout escape hatch
                    if shutdown_start_time is None:
                        shutdown_start_time = time.time()

                    # CRITICAL FIX (Jan 2026): Timeout escape hatch prevents infinite hang
                    # Without this, the result collector can hang forever if:
                    # - Workers exit before putting results in queue
                    # - Queue appears empty but items are in transit
                    # - Race condition between queue.empty() check and worker puts
                    elapsed = time.time() - shutdown_start_time
                    if elapsed > MAX_SHUTDOWN_WAIT:
                        self.logger.warning(
                            f"Result collector shutdown timeout ({elapsed:.1f}s > {MAX_SHUTDOWN_WAIT}s) - forcing exit"
                        )
                        break

                    # Double-check: queue empty AND no pending futures
                    with self._futures_lock:
                        has_pending = bool(self._pending_futures)

                    if not has_pending and self._result_queue.empty():
                        # Shutdown requested, queue empty, no pending futures - safe to exit
                        break

                # Continue waiting (either not shutdown, or still have pending work)
                continue
            except Exception as e:
                self.logger.error(f"Error collecting results: {e}")
                # On error, check if shutdown and no pending work
                if self._shutdown_event.is_set():
                    with self._futures_lock:
                        if not self._pending_futures:
                            break

    def _generate_task_id(self) -> str:
        """Generate unique task ID."""
        with self._task_id_lock:
            self._next_task_id += 1
            return f"task_{self._next_task_id}"

    def _track_shared_buffers(self, task_id: str, shared_refs: List[Dict[str, Any]]) -> None:
        """Track shared memory buffers for a task (for cleanup after completion)."""
        if not shared_refs:
            return

        buffer_ids = [ref['buffer_id'] for ref in shared_refs if ref.get('buffer_id')]
        if buffer_ids:
            with self._buffer_lock:
                self._task_buffer_refs[task_id] = buffer_ids

    def _release_shared_buffers(self, task_id: str) -> None:
        """Release shared memory buffers for completed task."""
        with self._buffer_lock:
            buffer_ids = self._task_buffer_refs.pop(task_id, None)

        if buffer_ids:
            self._release_buffer_ids(buffer_ids)

    def _release_buffer_ids(self, buffer_ids: List[str]) -> None:
        """Release buffers back to SharedMemoryManager."""
        if not buffer_ids:
            return

        # Check what release method SharedMemoryManager provides
        release_fn = None
        for method_name in ['release_buffer', 'deallocate_buffer', 'free_buffer']:
            if hasattr(self._shared_memory_manager, method_name):
                release_fn = getattr(self._shared_memory_manager, method_name)
                break

        if not release_fn:
            # SharedMemoryManager doesn't have release - buffers freed on cleanup
            self.logger.debug("SharedMemoryManager has no release method - buffers freed on shutdown")
            return

        for buffer_id in buffer_ids:
            try:
                release_fn(buffer_id)
            except Exception as exc:
                self.logger.warning(f"Failed to release buffer {buffer_id}: {exc}")

    def submit(self, fn: Callable, *args, **kwargs) -> Future:
        """
        Submit a task for execution.

        Uses shared memory for large numpy/pandas payloads, pickle for others.

        Args:
            fn: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Future for the task result
        """
        if self._shutdown_event.is_set():
            raise RuntimeError("Executor is shut down")

        # Generate task ID
        task_id = self._generate_task_id()

        # Create future for this task (thread-safe)
        future = Future()
        with self._futures_lock:
            self._pending_futures[task_id] = future

        # Analyze arguments for shared memory optimization
        use_shared_memory, shared_refs, pickled_args, ser_time, reused_buffers = \
            self._marshal_arguments(args, kwargs)

        # Update serialization stats
        with self._stats_lock:
            self._stats.total_tasks += 1
            self._stats.total_serialization_time += ser_time

            if use_shared_memory:
                self._stats.shared_memory_transfers += 1
            else:
                self._stats.pickle_transfers += 1

            # Track buffer reuse (Task 3.1 fix)
            if reused_buffers > 0:
                self._stats.buffer_reuses += reused_buffers

        # Track buffers for this task (for cleanup)
        if shared_refs:
            self._track_shared_buffers(task_id, shared_refs)

        # Pickle the function for forkserver/spawn compatibility
        pickled_func = pickle.dumps(fn, protocol=5)

        # Create task descriptor
        descriptor = TaskDescriptor(
            task_id=task_id,
            func_name=fn.__name__ if hasattr(fn, '__name__') else str(fn),
            use_shared_memory=use_shared_memory,
            shared_memory_refs=shared_refs,
            pickled_args=pickled_args
        )

        # Submit to worker queue (send pickled function, not function object)
        self._task_queue.put((task_id, pickled_func, descriptor))

        return future

    def _marshal_arguments(self, args: tuple, kwargs: dict):
        """
        Marshal arguments for transfer to worker process.

        Uses shared memory for large numpy arrays, pickle for others.
        Task 3.1: Adds fallback when pool exhausted and buffer reuse tracking.

        Returns:
            (use_shared_memory, shared_refs, pickled_args, serialization_time, reused_buffers)
        """
        start = time.perf_counter()

        # Check if any args are large numpy arrays
        def _eligible(value: Any) -> bool:
            return isinstance(value, np.ndarray) and value.nbytes >= self._shared_memory_threshold

        has_large_arrays = any(_eligible(arg) for arg in args)
        reused_buffers = 0

        if has_large_arrays:
            # Use shared memory path - CRITICAL: Replace large arrays with placeholders
            shared_refs = []
            args_list = list(args)
            allocated_buffer_ids: List[str] = []

            try:
                # Create buffers for large arrays and REPLACE with placeholders
                for i, arg in enumerate(args):
                    if not _eligible(arg):
                        continue

                    # Create zero-copy buffer (may fail if pool exhausted)
                    buffer = self._shared_memory_manager.create_zero_copy_buffer(arg)
                    allocated_buffer_ids.append(buffer.buffer_id)

                    # Track buffer reuse (if SharedMemoryManager supports it)
                    if hasattr(buffer, 'reused') and buffer.reused:
                        reused_buffers += 1

                    # Include offset and nbytes for reconstruction
                    buffer_metadata = buffer.metadata.copy()
                    buffer_metadata['offset'] = buffer.memory_block.offset
                    buffer_metadata['nbytes'] = arg.nbytes

                    shared_refs.append({
                        'index': i,
                        'buffer_id': buffer.buffer_id,
                        'metadata': buffer_metadata
                    })

                    # CRITICAL FIX: Replace array with None placeholder to avoid pickling
                    args_list[i] = None

                # Pickle args with placeholders (small payload) using dill
                pickled_args = pickle.dumps((tuple(args_list), kwargs), protocol=5)
                use_shared_memory = True

            except (BufferError, MemoryError, RuntimeError, Exception) as exc:
                # Shared memory pool exhausted - fallback to pickle
                self.logger.warning(
                    f"Shared memory allocation failed, falling back to pickle: {exc}"
                )

                # Release any buffers we did allocate
                self._release_buffer_ids(allocated_buffer_ids)

                # Fallback to full pickle (safe but slower)
                pickled_args = pickle.dumps((args, kwargs), protocol=5)
                shared_refs = []
                use_shared_memory = False
                reused_buffers = 0

        else:
            # Use dill/pickle for everything
            pickled_args = pickle.dumps((args, kwargs), protocol=5)
            shared_refs = []
            use_shared_memory = False

        serialization_time = time.perf_counter() - start

        return use_shared_memory, shared_refs, pickled_args, serialization_time, reused_buffers

    def resize(self, new_worker_count: int):
        """
        Gracefully resize worker pool.

        Args:
            new_worker_count: New number of workers
        """
        current_count = len(self._workers)

        if new_worker_count == current_count:
            return  # No change needed

        # P1-3: Record scale event for spike correlation
        if self._spike_detection_enabled:
            direction = 'up' if new_worker_count > current_count else 'down'
            with self._spike_lock:
                self._spike_instrumentation.record_scale_event(
                    direction, current_count, new_worker_count
                )
            self.logger.info(
                f"[SPIKE_DETECTION] Scale {direction}: {current_count} -> {new_worker_count} workers. "
                f"Scale-up adds ~500ms spawn overhead per new worker."
            )

        if new_worker_count > current_count:
            # Add workers
            for worker_id in range(current_count, new_worker_count):
                process = self._mp_context.Process(
                    target=_worker_main,
                    args=(
                        worker_id,
                        self._task_queue,
                        self._result_queue,
                        self._shutdown_event,
                        self._shared_memory_manager._shm_name
                    ),
                    daemon=False
                )
                process.start()
                self._workers.append(process)

            # UPDATE num_workers to reflect new count
            self.num_workers = new_worker_count

            self.logger.info(f"Scaled up: {current_count} → {new_worker_count} workers")

            # Emit worker scaling telemetry (non-blocking)
            try:
                from epochly.telemetry.routing_events import get_routing_emitter
                emitter = get_routing_emitter()
                if emitter:
                    emitter.emit_worker_scaling(
                        operation='scale_up',
                        old_count=current_count,
                        new_count=new_worker_count,
                        reason='pool_resize',
                        executor_type='process_pool'
                    )
            except Exception:
                pass  # Telemetry failures must not affect pool operations

        else:
            # Remove workers (gracefully - they finish current tasks)
            workers_to_remove = current_count - new_worker_count

            for _ in range(workers_to_remove):
                # Send poison pill to stop one worker
                self._task_queue.put(None)

            # Wait for workers to finish
            removed_count = 0
            for i in range(len(self._workers) - 1, new_worker_count - 1, -1):
                worker = self._workers[i]
                worker.join(timeout=5.0)
                if not worker.is_alive():
                    removed_count += 1

            # Remove stopped workers from list
            self._workers = self._workers[:new_worker_count]

            # UPDATE num_workers to reflect new count
            self.num_workers = new_worker_count

            self.logger.info(f"Scaled down: {current_count} → {new_worker_count} workers "
                           f"({removed_count} stopped gracefully)")

            # Emit worker scaling telemetry (non-blocking)
            try:
                from epochly.telemetry.routing_events import get_routing_emitter
                emitter = get_routing_emitter()
                if emitter:
                    emitter.emit_worker_scaling(
                        operation='scale_down',
                        old_count=current_count,
                        new_count=new_worker_count,
                        reason='pool_resize',
                        executor_type='process_pool'
                    )
            except Exception:
                pass  # Telemetry failures must not affect pool operations

    def get_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics.

        Returns:
            Dictionary with performance metrics
        """
        with self._stats_lock:
            return {
                'total_tasks': self._stats.total_tasks,
                'completed_tasks': self._stats.completed_tasks,
                'failed_tasks': self._stats.failed_tasks,
                'total_serialization_time': self._stats.total_serialization_time,
                'total_queue_wait_time': self._stats.total_queue_wait_time,
                'total_execution_time': self._stats.total_execution_time,
                'serialization_time_ms': self._stats.total_serialization_time * 1000,
                'avg_queue_wait_ms': (self._stats.total_queue_wait_time * 1000 / self._stats.completed_tasks)
                                    if self._stats.completed_tasks > 0 else 0.0,
                'execution_time_ms': self._stats.total_execution_time * 1000,
                'shared_memory_transfers': self._stats.shared_memory_transfers,
                'pickle_transfers': self._stats.pickle_transfers,
                'buffer_reuses': self._stats.buffer_reuses,
                'num_workers': len(self._workers)
            }

    def shutdown(self, wait: bool = True, timeout: Optional[float] = None):
        """
        Shutdown executor and clean up resources.

        Args:
            wait: Wait for pending tasks to complete
            timeout: Maximum time to wait (seconds). Defaults to 10.0 to prevent hangs.
        """
        # CRITICAL FIX (Jan 2026): Default timeout to prevent infinite hangs during exit
        # Without a timeout, worker.join() can block forever if workers don't exit cleanly
        if timeout is None:
            timeout = 10.0  # Reasonable default to allow clean shutdown but prevent hangs

        self.logger.info(f"Shutting down ForkingProcessExecutor (wait={wait}, timeout={timeout})")

        # Signal shutdown FIRST - this triggers the timeout escape hatch in result collector
        self._shutdown_event.set()

        # Send poison pills to all workers (with timeout to avoid blocking)
        for _ in range(len(self._workers)):
            try:
                self._task_queue.put(None, timeout=1.0)
            except Exception:
                pass  # Queue might be full or closed, continue with shutdown

        if wait:
            # Wait for workers to finish with bounded timeout
            start = time.time()
            for worker in self._workers:
                remaining = max(0.1, timeout - (time.time() - start))  # At least 100ms per worker
                worker.join(timeout=remaining)

        # CRITICAL FIX (Jan 2026): Use brief timeout for daemon thread join
        # The result collector is a daemon thread with a 5-second timeout escape hatch.
        # We only need to wait briefly here - if it doesn't exit, it will be killed
        # automatically when the process exits (daemon thread behavior).
        # Long join timeouts here were causing the shutdown hang.
        if self._result_collector_thread and self._result_collector_thread.is_alive():
            self._result_collector_thread.join(timeout=1.0)  # Brief wait only
            # Don't block indefinitely - daemon threads are auto-killed on exit

        # Terminate any remaining workers (with escalation to kill if needed)
        for worker in self._workers:
            if worker.is_alive():
                worker.terminate()
                worker.join(timeout=0.5)
                # Force kill if terminate didn't work (SIGKILL)
                if worker.is_alive():
                    try:
                        import signal
                        os.kill(worker.pid, signal.SIGKILL)
                        worker.join(timeout=0.5)
                    except Exception:
                        pass

        # Clean up shared memory
        try:
            self._shared_memory_manager.cleanup()
        except Exception:
            pass  # Ignore cleanup errors during shutdown

        self.logger.info("ForkingProcessExecutor shut down complete")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown(wait=True)
        return False


def _worker_main(worker_id: int, task_queue, result_queue, shutdown_event, shm_name: str):
    """
    Worker process main loop.

    Args:
        worker_id: Worker process ID
        task_queue: Queue of tasks to execute
        result_queue: Queue for results
        shutdown_event: Event signaling shutdown
        shm_name: Shared memory segment name for buffer access
    """
    import sys
    import os
    import traceback

    # CRITICAL: Call worker initializer FIRST to disable Epochly in workers
    # This prevents recursive interception when executing operations
    from epochly.plugins.executor.worker_initializer import epochly_worker_initializer
    epochly_worker_initializer()

    # Setup process (disable buffering for debugging)
    sys.stdout.flush()
    sys.stderr.flush()

    # Attach to shared memory using safe connect that unregisters from resource_tracker
    # CRITICAL FIX: Workers must use safe_connect_shared_memory to prevent resource_tracker
    # KeyError on exit when parent process has already cleaned up the segment
    from epochly.utils.shm_cleanup import safe_connect_shared_memory
    shm = None
    try:
        shm = safe_connect_shared_memory(shm_name)
    except Exception as e:
        # Can't access shared memory - send error and return
        try:
            result_queue.put(('init_error', False,
                            Exception(f"Worker {worker_id} failed to attach to shared memory: {e}"),
                            0.0, 0.0))
        except:
            pass
        return

    # Worker loop with guaranteed cleanup
    try:
        while not shutdown_event.is_set():
            try:
                # Get task with timeout
                item = task_queue.get(timeout=0.1)

                if item is None:
                    # Poison pill - shutdown gracefully
                    break

                task_id, pickled_func, descriptor = item

                # Track queue wait time
                queue_wait = time.time() - descriptor.submit_time

                # Unpickle function
                try:
                    import dill
                    pickle_module = dill
                except ImportError:
                    import pickle
                    pickle_module = pickle

                try:
                    func = pickle_module.loads(pickled_func)

                    # Unmarshal arguments
                    if descriptor.use_shared_memory and descriptor.shared_memory_refs:
                        # Reconstruct from shared memory
                        args, kwargs = _unmarshal_from_shared_memory(
                            descriptor.pickled_args,
                            descriptor.shared_memory_refs,
                            shm
                        )
                    else:
                        # Standard pickle/dill
                        args, kwargs = pickle_module.loads(descriptor.pickled_args)

                    # Execute function
                    start_exec = time.perf_counter()
                    result = func(*args, **kwargs)
                    exec_time = time.perf_counter() - start_exec

                    # Return result
                    result_queue.put((task_id, True, result, exec_time, queue_wait))

                except Exception as e:
                    # Return original exception (preserve type for proper propagation)
                    exec_time = 0.0
                    result_queue.put((task_id, False, e, exec_time, queue_wait))

            except Empty:
                # No tasks, continue waiting
                continue
            except Exception as e:
                # Critical worker error - try to report and exit
                try:
                    tb_str = traceback.format_exc()
                    error_msg = f"Worker {worker_id} fatal error: {e}\n{tb_str}"
                    result_queue.put(('worker_error', False, Exception(error_msg), 0.0, 0.0))
                except:
                    pass
                break

    finally:
        # Guaranteed cleanup regardless of how loop exits
        if shm:
            try:
                shm.close()
            except:
                pass


def _unmarshal_from_shared_memory(pickled_args: bytes, shared_refs: List[Dict],
                                   shm: shared_memory.SharedMemory):
    """
    Reconstruct arguments from shared memory buffers.

    Args:
        pickled_args: Pickled version of args/kwargs (with placeholders for arrays)
        shared_refs: List of shared memory buffer references
        shm: Shared memory segment

    Returns:
        (args, kwargs) tuple with arrays reconstructed from shared memory
    """
    # Use dill for unpickling (same as marshaling)
    try:
        import dill
        pickle_module = dill
    except ImportError:
        import pickle
        pickle_module = pickle

    # Unpickle base args/kwargs
    args, kwargs = pickle_module.loads(pickled_args)

    # Reconstruct numpy arrays from shared memory
    args_list = list(args)

    for ref in shared_refs:
        index = ref['index']
        metadata = ref['metadata']

        # Get shape, dtype, and buffer location
        shape = metadata['shape']
        dtype = np.dtype(metadata['dtype'])
        offset = metadata.get('offset', 0)
        nbytes = metadata.get('nbytes', 0)

        # Create numpy array view from shared memory then copy for safety
        # CRITICAL: .copy() prevents dangling references if buffer is reused
        buffer_view = memoryview(shm.buf)[offset:offset + nbytes]
        shared_array = np.ndarray(shape, dtype=dtype, buffer=buffer_view)

        # Copy to worker's memory (safe from buffer reuse)
        # This is one copy, vs the previous two copies (tobytes + frombuffer)
        # Performance: Still better than double-copy, and memory-safe
        reconstructed_array = shared_array.copy()

        # Replace in args list
        args_list[index] = reconstructed_array

    return tuple(args_list), kwargs


if __name__ == '__main__':
    # Quick test
    print("ForkingProcessExecutor module loaded")
