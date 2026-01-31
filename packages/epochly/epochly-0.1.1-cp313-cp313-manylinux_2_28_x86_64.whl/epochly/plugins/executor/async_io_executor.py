"""
Async I/O Executor for Task 4.1

Per perf_fixes3.md: Integrate asyncio proactor for I/O workload overlap.

Enables concurrent I/O operations to overlap rather than execute sequentially,
achieving 2× throughput for I/O-bound workloads.

Author: Epochly Development Team
Created: 2025-11-15
"""

import asyncio
import threading
import time
import logging
from functools import partial
from typing import Any, Callable, Optional, Dict, List
from concurrent.futures import Future
from dataclasses import dataclass
from queue import Queue, Empty


@dataclass
class AsyncExecutionStats:
    """Statistics for async I/O execution."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_execution_time: float = 0.0
    total_wait_time: float = 0.0
    concurrent_tasks_peak: int = 0
    event_loop_overhead: float = 0.0


class AsyncIOExecutor:
    """
    Async I/O executor for concurrent I/O operations.

    Runs asyncio event loop in dedicated thread, enabling I/O overlap
    for network requests, file operations, etc.

    Compatible with concurrent.futures.Executor interface.
    """

    def __init__(self, max_concurrent: int = 100):
        """
        Initialize async I/O executor.

        Args:
            max_concurrent: Maximum concurrent I/O operations
        """
        self.logger = logging.getLogger(__name__)
        self.max_concurrent = max_concurrent

        # Event loop management
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()

        # Concurrency limiting (mcp-reflect: enforce max_concurrent)
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._concurrent_tasks = 0
        self._concurrent_lock = threading.Lock()

        # Task tracking
        self._pending_futures: Dict[str, Future] = {}
        self._futures_lock = threading.Lock()
        self._next_task_id = 0
        self._task_id_lock = threading.Lock()

        # Statistics
        self._stats = AsyncExecutionStats()
        self._stats_lock = threading.Lock()

        # Start event loop
        self._start_event_loop()

    def _start_event_loop(self):
        """Start asyncio event loop in dedicated thread."""
        def run_loop():
            # Create new event loop for this thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            self.logger.debug("Async I/O event loop started")

            # Run forever (mcp-reflect recommendation)
            self._loop.run_forever()

            # Shutdown: cancel outstanding tasks
            pending = asyncio.all_tasks(self._loop)
            for task in pending:
                task.cancel()

            # Wait for cancellations to complete (with timeout)
            if pending:
                try:
                    shutdown_task = asyncio.gather(*pending, return_exceptions=True)
                    self._loop.run_until_complete(
                        asyncio.wait_for(shutdown_task, timeout=10.0)
                    )
                except (asyncio.TimeoutError, Exception) as e:
                    self.logger.warning(f"Shutdown timeout or error: {e}")
                    pass

            # Cleanup
            self._loop.close()
            self.logger.debug("Async I/O event loop stopped")

        self._loop_thread = threading.Thread(
            target=run_loop,
            daemon=True,
            name="AsyncIOExecutor-EventLoop"
        )
        self._loop_thread.start()

        # Wait for loop to be ready
        timeout = 2.0
        start = time.time()
        while self._loop is None and (time.time() - start) < timeout:
            time.sleep(0.01)

        if self._loop is None:
            raise RuntimeError("Failed to start async event loop")

        # Create semaphore for concurrency limiting
        async def create_semaphore():
            self._semaphore = asyncio.Semaphore(self.max_concurrent)

        asyncio.run_coroutine_threadsafe(create_semaphore(), self._loop).result(timeout=2.0)

        self.logger.info(f"AsyncIOExecutor initialized with max_concurrent={self.max_concurrent}")

    # Event loop main no longer needed with run_forever() approach
    # Loop runs until stop() is called

    def _generate_task_id(self) -> str:
        """Generate unique task ID."""
        with self._task_id_lock:
            self._next_task_id += 1
            return f"async_task_{self._next_task_id}"

    def submit(self, fn: Callable, *args, **kwargs) -> Future:
        """
        Submit a task for async execution.

        For sync functions, wraps in executor.run_in_executor().
        For async functions, schedules as coroutine.

        Args:
            fn: Function to execute (sync or async)
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Future for result
        """
        if self._shutdown_event.is_set():
            raise RuntimeError("Executor is shut down")

        task_id = self._generate_task_id()

        # Create future for result
        future = Future()
        with self._futures_lock:
            self._pending_futures[task_id] = future

        # Update stats
        with self._stats_lock:
            self._stats.total_tasks += 1

        # Schedule on event loop (with error handling for scheduling failures)
        try:
            if asyncio.iscoroutinefunction(fn):
                # Async function - schedule directly
                asyncio.run_coroutine_threadsafe(
                    self._execute_async(task_id, fn, args, kwargs),
                    self._loop
                )
            else:
                # Sync function - run in thread pool executor
                asyncio.run_coroutine_threadsafe(
                    self._execute_sync(task_id, fn, args, kwargs),
                    self._loop
                )
        except RuntimeError as e:
            # Event loop closed or not running - clean up and raise
            with self._futures_lock:
                future = self._pending_futures.pop(task_id, None)
            if future:
                future.set_exception(e)
            raise

        return future

    async def _execute_async(self, task_id: str, fn: Callable, args: tuple, kwargs: dict):
        """Execute async function with concurrency limiting."""
        # Enforce max_concurrent limit
        async with self._semaphore:
            # Track concurrent tasks
            with self._concurrent_lock:
                self._concurrent_tasks += 1
                if self._concurrent_tasks > self._stats.concurrent_tasks_peak:
                    self._stats.concurrent_tasks_peak = self._concurrent_tasks

            try:
                start = time.perf_counter()
                result = await fn(*args, **kwargs)
                exec_time = time.perf_counter() - start

                # Update stats
                with self._stats_lock:
                    self._stats.completed_tasks += 1
                    self._stats.total_execution_time += exec_time

                # Resolve future
                self._resolve_future(task_id, True, result)

            except (Exception, BaseException) as e:
                # Task failed (catch BaseException for CancelledError)
                with self._stats_lock:
                    self._stats.failed_tasks += 1

                self._resolve_future(task_id, False, e)

            finally:
                # Decrement concurrent task count
                with self._concurrent_lock:
                    self._concurrent_tasks -= 1

    async def _execute_sync(self, task_id: str, fn: Callable, args: tuple, kwargs: dict):
        """Execute sync function in thread pool with concurrency limiting."""
        # Enforce max_concurrent limit
        async with self._semaphore:
            # Track concurrent tasks
            with self._concurrent_lock:
                self._concurrent_tasks += 1
                if self._concurrent_tasks > self._stats.concurrent_tasks_peak:
                    self._stats.concurrent_tasks_peak = self._concurrent_tasks

            try:
                start = time.perf_counter()

                # Run sync function in thread pool (doesn't block event loop)
                # Compatible with Python 3.9-3.13
                # Use partial to properly handle args/kwargs
                result = await self._loop.run_in_executor(
                    None,
                    partial(fn, *args, **kwargs)
                )

                exec_time = time.perf_counter() - start

                # Update stats
                with self._stats_lock:
                    self._stats.completed_tasks += 1
                    self._stats.total_execution_time += exec_time

                # Resolve future
                self._resolve_future(task_id, True, result)

            except (Exception, BaseException) as e:
                # Task failed (catch BaseException for CancelledError)
                with self._stats_lock:
                    self._stats.failed_tasks += 1

                self._resolve_future(task_id, False, e)

            finally:
                # Decrement concurrent task count
                with self._concurrent_lock:
                    self._concurrent_tasks -= 1

    def _resolve_future(self, task_id: str, success: bool, result: Any):
        """Resolve a pending future."""
        with self._futures_lock:
            future = self._pending_futures.pop(task_id, None)

        if future:
            if success:
                future.set_result(result)
            else:
                future.set_exception(result)

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        with self._stats_lock:
            return {
                'total_tasks': self._stats.total_tasks,
                'completed_tasks': self._stats.completed_tasks,
                'failed_tasks': self._stats.failed_tasks,
                'total_execution_time': self._stats.total_execution_time,
                'avg_execution_time': (
                    self._stats.total_execution_time / self._stats.completed_tasks
                    if self._stats.completed_tasks > 0 else 0.0
                ),
                'concurrent_tasks_peak': self._stats.concurrent_tasks_peak
            }

    def shutdown(self, wait: bool = True):
        """
        Shutdown async executor.

        Args:
            wait: Whether to wait for pending tasks
        """
        self.logger.info("Shutting down AsyncIOExecutor")

        # Signal shutdown
        self._shutdown_event.set()

        if wait:
            # Wait for pending futures
            timeout_per_future = 5.0
            with self._futures_lock:
                pending = list(self._pending_futures.values())

            for future in pending:
                try:
                    future.result(timeout=timeout_per_future)
                except Exception:
                    pass

        # Stop event loop gracefully
        if self._loop:
            # Cancel the main loop task
            try:
                if self._loop.is_running():
                    self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception:
                pass

        # Wait for loop thread
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=5.0)

        self.logger.info("AsyncIOExecutor shutdown complete")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown(wait=True)
        return False


if __name__ == '__main__':
    print("AsyncIOExecutor module loaded")
