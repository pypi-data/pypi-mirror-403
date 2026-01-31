"""
Background JIT Compilation Worker (Phase 2.4)

Runs compilation and benchmarking in background thread without blocking callers.

Architecture:
- Queue-based compilation requests
- Background thread processes queue
- Benchmark results stored in artifact store
- Shared memory integration for cross-interpreter access

Performance:
- Queue submission: <1ms (non-blocking)
- Compilation: Async in background
- Benchmarking: Async in background
- Callers never block
"""

import marshal
import time
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
import logging

# MCP-reflect FIX (Jan 2026): Use TYPE_CHECKING for proper type annotation
# without causing circular import issues
if TYPE_CHECKING:
    from .manager import JITManager

from .base import JITBackend
from .artifact_store import JITArtifactStore, CompiledArtifact, CompilationStatus, get_artifact_store

logger = logging.getLogger(__name__)


@dataclass
class CompilationRequest:
    """Request to compile a function."""

    function: Callable
    function_name: str
    backend: JITBackend
    priority: int = 0  # Higher = more urgent
    # P0.13 FIX (Dec 2025): Bypass static call_count filter for auto-profiler/sys.monitoring hot detection
    bypass_call_count: bool = False


class CompilationWorker:
    """
    Background worker for JIT compilation and benchmarking.

    Consumes compilation queue and processes requests asynchronously.
    Stores results in artifact store for non-blocking retrieval.

    P0.8 FIX (Dec 2025): Uses composition instead of Thread inheritance.
    This avoids the threading._limbo KeyError that occurs during rapid
    thread recreation or interpreter shutdown. The KeyError happens when
    a daemon thread's object identity changes between __init__ and
    _bootstrap_inner, causing `del _limbo[self]` to fail.
    """

    def __init__(self,
                 jit_manager: "JITManager",  # MCP-reflect FIX: Proper type annotation
                 artifact_store: Optional[JITArtifactStore] = None,
                 max_queue_size: int = 100,
                 benchmark_workers: int = 2):
        """
        Initialize compilation worker.

        Args:
            jit_manager: Parent JITManager instance
            artifact_store: Artifact store for results (default: global store)
            max_queue_size: Maximum compilation queue depth
            benchmark_workers: Number of threads for async benchmarking (P3)
        """
        self.jit_manager = jit_manager
        self.artifact_store = artifact_store or get_artifact_store()
        self.max_queue_size = max_queue_size

        # Compilation queue (bounded for backpressure)
        self._queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self._running = False
        self._stop_event = threading.Event()

        # P0.8: Internal thread (composition instead of inheritance)
        self._thread: Optional[threading.Thread] = None
        self._thread_lock = threading.Lock()

        # P3 WARMUP OPTIMIZATION (Jan 2026): Separate thread pool for benchmarking
        # This ensures benchmarks don't block the compilation queue.
        # Benchmarks are I/O-bound (timing measurements), so a small pool suffices.
        self._benchmark_executor = ThreadPoolExecutor(
            max_workers=benchmark_workers,
            thread_name_prefix="JIT-Benchmark"
        )

        # Statistics
        self._compiled_count = 0
        self._failed_count = 0
        self._benchmarked_count = 0

    def _is_executor_shutdown(self) -> bool:
        """
        Check if benchmark executor is shutdown without accessing private attributes.

        MCP-reflect FIX (Jan 2026): Avoid using _shutdown private attribute which
        is a CPython implementation detail that could break on version upgrades.
        Instead, try submitting a no-op task to check if executor accepts work.

        Returns:
            True if executor is shutdown and cannot accept work, False otherwise
        """
        try:
            # Try submitting a no-op to check if executor accepts work
            future = self._benchmark_executor.submit(lambda: None)
            future.cancel()  # Cancel immediately - we don't need the result
            return False
        except RuntimeError:
            # RuntimeError is raised when submitting to a shutdown executor
            return True

    def queue_compilation(self, request: CompilationRequest) -> bool:
        """
        Queue function for background compilation (non-blocking).

        Args:
            request: Compilation request

        Returns:
            True if queued, False if queue full
        """
        if not self._running:
            return False

        try:
            # Non-blocking put with immediate timeout
            self._queue.put(request, block=False)

            # Mark as pending in artifact store
            self.artifact_store.mark_compiling(request.function_name, request.backend.value)

            return True

        except queue.Full:
            logger.warning(f"Compilation queue full, dropping request for {request.function_name}")
            return False

    def _run_loop(self) -> None:
        """Background worker main loop (runs in internal thread)."""
        logger.info("Compilation worker started")

        while not self._stop_event.is_set():
            try:
                # Get next compilation request (with timeout for stop check)
                try:
                    request = self._queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                # Process compilation
                self._process_compilation(request)

                self._queue.task_done()

            except Exception as e:
                logger.error(f"Worker error: {e}")

        logger.info("Compilation worker stopped")

    def _process_compilation(self, request: CompilationRequest) -> None:
        """
        Process single compilation request.

        Args:
            request: Compilation request to process
        """
        func_name = request.function_name

        try:
            # Compile the function
            logger.debug(f"Compiling {func_name} with {request.backend.value}")

            compilation_result = self.jit_manager._compile_with_backend(
                request.function, request.backend
            )

            if not compilation_result.is_successful:
                logger.warning(f"Compilation failed for {func_name}")
                self._failed_count += 1
                # P0.14: Cache failed compilation to prevent retries
                # P0.12: Also track by code_id for monitoring callback checks
                with self.jit_manager._lock:
                    self.jit_manager._failed_compilations.add(func_name)
                    # Add code_id so monitoring callbacks can check and return DISABLE
                    if hasattr(request.function, '__code__'):
                        self.jit_manager._failed_code_ids.add(id(request.function.__code__))
                # MCP-reflect FIX: Propagate failure to artifact store
                self.artifact_store.mark_failed(func_name, request.backend.value)
                return

            self._compiled_count += 1

            # Store in JIT manager's compiled_functions dict (primary in-process storage)
            # This is where get_compiled_artifact looks first
            with self.jit_manager._lock:
                self.jit_manager.compiled_functions[func_name] = compilation_result
                # Remove from queue now that it's compiled
                self.jit_manager.compilation_queue.discard(func_name)

            # Try to serialize for artifact store (cross-process sharing)
            # This may fail for Numba CPUDispatcher which doesn't have standard __code__
            code_bytes = b''  # Empty bytes as fallback
            try:
                if hasattr(compilation_result.compiled_function, '__code__'):
                    code_bytes = marshal.dumps(compilation_result.compiled_function.__code__)
            except Exception as e:
                logger.debug(f"Could not serialize {func_name} (expected for Numba): {e}")
                # This is expected for Numba - continue with empty code_bytes
                # The actual compiled function is stored in jit_manager.compiled_functions

            # Create artifact for status tracking
            artifact = CompiledArtifact(
                function_name=func_name,
                code_bytes=code_bytes,
                status=CompilationStatus.BENCHMARKING,
                compiled_at=time.time(),
                backend=request.backend.value
            )

            # Store immediately (compilation complete, benchmark pending)
            self.artifact_store.store(artifact)

            # Now benchmark in background (doesn't block other compilations)
            self._benchmark_async(request.function, compilation_result.compiled_function, func_name)

        except Exception as e:
            logger.error(f"Compilation processing failed for {func_name}: {e}")
            self._failed_count += 1
            # P0.14: Cache failed compilation to prevent retries
            # P0.12: Also track by code_id for monitoring callback checks
            with self.jit_manager._lock:
                self.jit_manager._failed_compilations.add(func_name)
                # Add code_id so monitoring callbacks can check and return DISABLE
                if hasattr(request.function, '__code__'):
                    self.jit_manager._failed_code_ids.add(id(request.function.__code__))
            # MCP-reflect FIX: Propagate failure to artifact store
            self.artifact_store.mark_failed(func_name, request.backend.value)

    def _benchmark_async(self, original_func: Callable, compiled_func: Callable, func_name: str) -> None:
        """
        Benchmark compiled function asynchronously.

        P3 WARMUP OPTIMIZATION (Jan 2026): Submits benchmark work to a separate
        thread pool executor, so benchmarking doesn't block the compilation queue.
        This enables the compilation worker to process subsequent compilations
        while benchmarks run in parallel.

        Args:
            original_func: Original function
            compiled_func: Compiled function
            func_name: Function name
        """
        # P3 FIX: Guard against submitting to shutdown executor
        # This can happen if stop() is called while _process_compilation is running
        # MCP-reflect FIX: Use helper method instead of accessing private _shutdown attribute
        if self._is_executor_shutdown():
            logger.debug(f"Benchmark executor shutdown, skipping benchmark for {func_name}")
            return

        try:
            # Submit benchmark to separate thread pool (non-blocking)
            self._benchmark_executor.submit(
                self._run_benchmark,
                original_func,
                compiled_func,
                func_name
            )
        except RuntimeError as e:
            # Handle race condition where executor shuts down between check and submit
            logger.debug(f"Could not submit benchmark for {func_name}: {e}")

    def _run_benchmark(self, original_func: Callable, compiled_func: Callable, func_name: str) -> None:
        """
        Execute benchmark work (runs in benchmark thread pool).

        P3 WARMUP OPTIMIZATION (Jan 2026): This is the actual benchmark execution,
        moved from _benchmark_async to run in the benchmark thread pool.

        Args:
            original_func: Original function
            compiled_func: Compiled function
            func_name: Function name
        """
        try:
            # Run benchmark (this may take 10-100ms)
            speedup = self.jit_manager._benchmark_compilation(original_func, compiled_func)

            if speedup is not None:
                # Update speedup in jit_manager.compiled_functions (primary storage)
                with self.jit_manager._lock:
                    if func_name in self.jit_manager.compiled_functions:
                        self.jit_manager.compiled_functions[func_name].speedup_ratio = speedup

                # Update artifact store with benchmark results (for status tracking)
                self.artifact_store.update_speedup(func_name, speedup)
                self._benchmarked_count += 1

                logger.info(f"Benchmark complete for {func_name}: {speedup:.2f}x speedup")
            else:
                logger.warning(f"Benchmark failed for {func_name}")

        except Exception as e:
            logger.error(f"Benchmark error for {func_name}: {e}")

    def start(self) -> None:
        """Start background worker.

        P0.8: Creates a new Thread instance each time, avoiding _limbo issues.
        Thread-safe: can be called from multiple threads.

        P0.8.1 FIX (Dec 2025): Reap zombie threads before starting new one.
        Fixes race where is_alive() returns True for thread about to die.

        P3 FIX (Jan 2026): Recreates benchmark executor if previously shutdown.
        This allows the worker to be restarted after stop() is called.
        """
        with self._thread_lock:
            if self._thread is not None:
                if self._thread.is_alive():
                    # Thread still alive, don't start new one
                    return
                # Reap the dead thread (prevents zombie accumulation)
                self._thread.join(timeout=0)

            self._running = True
            self._stop_event.clear()

            # P3 FIX: Recreate benchmark executor if it was shutdown
            # MCP-reflect FIX: Use helper method instead of accessing private _shutdown attribute
            # The check and recreation happen atomically within the _thread_lock
            if self._is_executor_shutdown():
                self._benchmark_executor = ThreadPoolExecutor(
                    max_workers=2,
                    thread_name_prefix="JIT-Benchmark"
                )

            # Create fresh thread for this start
            self._thread = threading.Thread(
                target=self._run_loop,
                daemon=True,
                name="JIT-CompilationWorker"
            )
            self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        """
        Stop background worker gracefully.

        Args:
            timeout: Maximum time to wait for shutdown

        P0.8.2 FIX (Dec 2025): Release lock before join() to avoid deadlock.
        If worker thread tries to log/acquire locks during shutdown, holding
        _thread_lock during join() could cause deadlock.

        P3 WARMUP OPTIMIZATION (Jan 2026): Also shuts down the benchmark executor.
        """
        thread_to_join = None
        with self._thread_lock:
            self._running = False
            self._stop_event.set()
            thread_to_join = self._thread
            self._thread = None

        # Join OUTSIDE the lock to prevent deadlock
        if thread_to_join is not None and thread_to_join.is_alive():
            thread_to_join.join(timeout=timeout)

        # P3: Shut down benchmark executor (wait=True to let pending benchmarks finish)
        self._benchmark_executor.shutdown(wait=True)

    def is_alive(self) -> bool:
        """Check if worker thread is alive."""
        with self._thread_lock:
            return self._thread is not None and self._thread.is_alive()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get worker statistics.

        Returns:
            Dictionary with worker stats
        """
        return {
            'running': self._running,
            'queue_size': self._queue.qsize(),
            'compiled_count': self._compiled_count,
            'failed_count': self._failed_count,
            'benchmarked_count': self._benchmarked_count
        }
