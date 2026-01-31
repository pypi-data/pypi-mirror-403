"""
Batch Dispatcher - Automatic Loop Parallelization

Detects loop patterns and automatically dispatches iterations to workers in batches.

Architecture:
1. Detect loop pattern (for i in range(N): ...)
2. Extract loop body as callable
3. Slice iterations into chunks
4. Dispatch chunks to Level 3 executor
5. Collect and merge results

Author: Epochly Development Team
Date: November 17, 2025
"""

import sys
import dis
import types
import inspect
import logging
import os
import tempfile
import threading
from typing import Callable, List, Any, Optional, Tuple, Dict
from concurrent.futures import Future
from dataclasses import dataclass

from ..utils.logger import get_logger
from .executor_adapter import ExecutorAdapter, UnifiedResult

logger = get_logger(__name__)

# Debug instrumentation control (conditional via environment variable)
# Enable with: export EPOCHLY_DEBUG_PARALLELIZATION=1
_DEBUG_PARALLELIZATION = os.environ.get('EPOCHLY_DEBUG_PARALLELIZATION', '').lower() in ('1', 'true', 'yes')
_TRACE_FILE = os.path.join(tempfile.gettempdir(), 'epochly_worker_trace.txt')

# Global persistent pool for batch dispatch (eliminates creation overhead)
# CRITICAL: Initialize lock at module level to prevent race condition
_global_pool = None
_global_pool_lock = threading.Lock()


def _trace_worker_event(pid: int, message: str) -> None:
    """
    Write worker trace event with proper locking (debug mode only).

    Best-effort logging that never fails. Uses file locking on POSIX systems
    for thread-safe concurrent writes.

    Args:
        pid: Worker process ID
        message: Event message to log
    """
    if not _DEBUG_PARALLELIZATION:
        return

    try:
        with open(_TRACE_FILE, 'a') as f:
            # Add file locking on POSIX systems (not available on Windows)
            try:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.write(f"PID {pid}: {message}\n")
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except (ImportError, AttributeError):
                # fcntl not available on Windows - write without locking
                f.write(f"PID {pid}: {message}\n")
    except (IOError, OSError):
        # File I/O failed - silently ignore (debug tracing is best-effort)
        pass


@dataclass
class LoopPattern:
    """
    Detected loop pattern information.

    Attributes:
        code_object: Code object containing the loop
        loop_start_offset: Bytecode offset where loop starts
        loop_end_offset: Bytecode offset where loop ends
        iteration_variable: Name of loop variable (e.g., 'i')
        range_start: Start of range (if detectable)
        range_end: End of range (if detectable)
        range_step: Step of range (default 1)
        is_parallelizable: Whether loop can be safely parallelized
    """
    code_object: object
    loop_start_offset: int
    loop_end_offset: int
    iteration_variable: Optional[str] = None
    range_start: Optional[int] = None
    range_end: Optional[int] = None
    range_step: int = 1
    is_parallelizable: bool = False


class LoopPatternDetector:
    """
    Detects loop patterns in bytecode.

    Analyzes Python bytecode to find loops and determine if they can be parallelized.
    """

    def __init__(self):
        self.logger = logger

    def detect_loops(self, code_object) -> List[LoopPattern]:
        """
        Detect all loops in a code object.

        Args:
            code_object: Code object to analyze

        Returns:
            List of LoopPattern objects
        """
        loops = []

        try:
            # Disassemble bytecode
            instructions = list(dis.get_instructions(code_object))

            # Find FOR_ITER instructions (indicate loop start)
            for i, instr in enumerate(instructions):
                if instr.opname == 'FOR_ITER':
                    loop_pattern = self._analyze_for_loop(instructions, i)
                    if loop_pattern:
                        loops.append(loop_pattern)

            self.logger.debug(f"Detected {len(loops)} loops in {code_object.co_name}")

        except Exception as e:
            self.logger.debug(f"Loop detection failed: {e}")

        return loops

    def _analyze_for_loop(self, instructions: List, for_iter_index: int) -> Optional[LoopPattern]:
        """
        Analyze a for loop starting at FOR_ITER instruction.

        Args:
            instructions: List of bytecode instructions
            for_iter_index: Index of FOR_ITER instruction

        Returns:
            LoopPattern if loop is analyzable, None otherwise
        """
        try:
            for_iter = instructions[for_iter_index]

            # FOR_ITER target is the offset to jump to when loop ends
            loop_end_offset = for_iter.argval
            loop_start_offset = for_iter.offset

            # Check if this is a range() loop by looking backward
            # Pattern: LOAD_GLOBAL range -> CALL_FUNCTION -> GET_ITER -> FOR_ITER
            is_range_loop = False
            range_arg = None

            if for_iter_index >= 3:
                # Look back for range() call
                for j in range(max(0, for_iter_index - 10), for_iter_index):
                    instr = instructions[j]
                    if instr.opname in ('LOAD_GLOBAL', 'LOAD_NAME') and instr.argval == 'range':
                        is_range_loop = True
                        # Try to extract range argument (if it's a constant)
                        # This is simplified - full implementation would need stack simulation
                        break

            pattern = LoopPattern(
                code_object=for_iter.code,  # Will be set by caller
                loop_start_offset=loop_start_offset,
                loop_end_offset=loop_end_offset,
                is_parallelizable=is_range_loop  # Only range loops are easily parallelizable
            )

            return pattern

        except Exception as e:
            self.logger.debug(f"Loop analysis failed: {e}")
            return None


# ============================================================================
# CRITICAL BUG FIX (Nov 22, 2025): Module-level worker functions
# ============================================================================
# These MUST be at module scope to be picklable with spawn start method.
# @staticmethod inside class fails to pickle on macOS/Windows.

def _execute_chunk_worker(loop_func: Callable, start: int, end: int, step: int) -> List[Any]:
    """
    Execute a chunk of loop iterations.

    MODULE-LEVEL: Picklable on all platforms.

    Args:
        loop_func: Loop body function
        start: Chunk start index
        end: Chunk end index
        step: Loop step

    Returns:
        List of results for this chunk
    """
    results = []
    for i in range(start, end, step):
        results.append(loop_func(i))
    return results


def _execute_chunk_cloudpickle_worker(pickled_func: bytes, start: int, end: int, step: int) -> List[Any]:
    """
    Execute chunk with cloudpickle-serialized function.

    MODULE-LEVEL: Picklable with spawn.

    Debug tracing enabled via EPOCHLY_DEBUG_PARALLELIZATION=1 environment variable.
    Trace file location: <tempdir>/epochly_worker_trace.txt

    Args:
        pickled_func: Cloudpickle-serialized loop function
        start: Chunk start index
        end: Chunk end index
        step: Loop step

    Returns:
        List of results for this chunk
    """
    import cloudpickle
    import os

    # Conditional debug tracing (production: no overhead)
    if _DEBUG_PARALLELIZATION:
        pid = os.getpid()
        _trace_worker_event(pid, f"START chunk [{start}:{end}:{step}]")

    # Execute work
    loop_func = cloudpickle.loads(pickled_func)
    results = _execute_chunk_worker(loop_func, start, end, step)

    # Conditional debug tracing (production: no overhead)
    if _DEBUG_PARALLELIZATION:
        _trace_worker_event(pid, f"COMPLETE chunk, {len(results)} results")

    return results


class BatchDispatcher:
    """
    Dispatches loop iterations in batches to parallel workers.

    Takes a detected loop pattern and:
    1. Slices iterations into chunks
    2. Dispatches chunks to workers
    3. Collects and merges results
    """

    def __init__(self, executor=None):
        """
        Initialize batch dispatcher.

        Args:
            executor: Level 3 executor (SubInterpreterExecutor or ProcessPoolExecutor)
        """
        # Wrap executor in adapter for unified API
        if executor and not isinstance(executor, ExecutorAdapter):
            self.executor = ExecutorAdapter(executor)
        else:
            self.executor = executor
        self.logger = logger

    def dispatch_loop(
        self,
        loop_func: Callable,
        start: int,
        end: int,
        step: int = 1,
        bound_locals: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Dispatch loop iterations in batches to parallel workers.

        Priority order:
        1. Level 3 pre-warmed ForkingProcessExecutor (best - no startup overhead)
        2. Persistent global Pool (good - reuses processes)
        3. Sequential execution (fallback)

        Args:
            loop_func: Loop body as callable function (takes iteration index)
            start: Loop start index
            end: Loop end index
            step: Loop step (default 1, must be positive for parallel execution)
            bound_locals: Optional dict of local variables to bind into loop_func's scope

        Returns:
            List of results from all iterations
        """
        # Issue 4 fix: Bind locals ONCE at start so all paths work (including sequential fallback)
        if bound_locals:
            loop_func = self._bind_loop_context(loop_func, bound_locals)
            # Clear bound_locals so backends don't try to bind again
            bound_locals = None

        # CRITICAL: Validate step before parallel dispatch
        # Negative steps require complex chunk boundary handling and are not yet supported
        if step == 0:
            raise ValueError("step cannot be zero")

        if step < 0:
            # Negative step ranges not supported for parallel execution
            # Fallback to sequential execution to ensure correctness
            # Note: loop_func is already bound above, so this will work
            self.logger.debug(
                f"Negative step ({step}) not supported for parallel dispatch; "
                f"falling back to sequential execution"
            )
            return [loop_func(i) for i in range(start, end, step)]
        # PRIORITY 1: Try Level 3's pre-warmed executor (zero startup overhead)
        try:
            from ..core.epochly_core import get_epochly_core
            core = get_epochly_core()

            # Trigger lazy Level 3 initialization if deferred
            if hasattr(core, '_ensure_level3_initialized'):
                core._ensure_level3_initialized()

            if core and hasattr(core, '_sub_interpreter_executor') and core._sub_interpreter_executor:
                # Level 3 has pre-warmed workers - use them!
                result = self._dispatch_with_level3_executor(core._sub_interpreter_executor, loop_func, start, end, step, bound_locals)
                if result is not None:
                    self.logger.info(f"Used Level 3 pre-warmed executor (zero overhead)")
                    return result
        except Exception as e:
            self.logger.debug(f"Level 3 executor not available: {e}")

        # PRIORITY 2: Try custom executor if provided
        if self.executor and self.executor.is_available():
            result = self._dispatch_with_executor(loop_func, start, end, step, bound_locals)
            if result is not None:
                return result

        # PRIORITY 3: Use persistent global Pool (eliminates creation overhead)
        result = self._dispatch_with_multiprocessing(loop_func, start, end, step, bound_locals)
        if result is not None:
            return result

        # Final fallback: Sequential execution
        self.logger.debug("No executor available, running sequentially")
        return [loop_func(i) for i in range(start, end, step)]

    def _dispatch_with_level3_executor(
        self,
        level3_executor,
        loop_func: Callable,
        start: int,
        end: int,
        step: int,
        bound_locals: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Any]]:
        """
        Dispatch using Level 3's pre-warmed executor.

        Benefits:
        - Workers already running (zero startup overhead)
        - Shared memory already allocated
        - Process reuse across multiple dispatches

        CRITICAL (Dec 2025): Added minimum-work threshold to prevent catastrophic
        regressions on small workloads. ProcessPool IPC overhead (~50-200ms per
        dispatch) can be 20x worse than sequential for sub-100ms workloads.

        Returns:
            List of results or None if dispatch failed (triggers fallback)
        """
        try:
            import math
            import os

            # Calculate total iterations FIRST (needed for threshold check)
            if step == 0:
                raise ValueError("step cannot be zero")
            total_iterations = math.ceil(abs(end - start) / abs(step))

            # =================================================================
            # CRITICAL FIX (Dec 2025): Minimum-work threshold for Level 3
            # =================================================================
            # ProcessPool dispatch has significant IPC/serialization overhead.
            # Dispatching small workloads causes catastrophic performance regressions:
            # - 89ms workload -> 1796ms with ProcessPool (20x slower!)
            # Solution: Only use Level 3 for substantial workloads.
            #
            # Get threshold from config or environment variable
            min_iterations = 100  # Default
            try:
                env_min_iters = os.environ.get('EPOCHLY_LEVEL3_MIN_ITERATIONS')
                if env_min_iters is not None:
                    min_iterations = int(env_min_iters)
                else:
                    from ..performance_config import DEFAULT_PERFORMANCE_CONFIG
                    min_iterations = DEFAULT_PERFORMANCE_CONFIG.process_pool.level3_min_iterations
            except Exception:
                pass  # Use default

            if total_iterations < min_iterations:
                self.logger.debug(
                    f"Skipping Level 3 ProcessPool dispatch: {total_iterations} iterations "
                    f"< {min_iterations} threshold (use EPOCHLY_LEVEL3_MIN_ITERATIONS to override)"
                )
                return None  # Trigger fallback to sequential or JIT-only

            # =================================================================
            # CRITICAL FIX (Dec 2025): Work-time threshold for Level 3
            # =================================================================
            # Even if iteration count passes, we must verify the WORK TIME
            # justifies ProcessPool overhead (~1700ms IPC cost).
            # Solution: Microbenchmark 1-3 iterations to estimate total work time.
            #
            # Get work-time threshold from config or environment variable
            min_work_ms = 2000.0  # Default: 2 seconds minimum work
            try:
                env_min_work = os.environ.get('EPOCHLY_LEVEL3_MIN_WORK_MS')
                if env_min_work is not None:
                    min_work_ms = float(env_min_work)
                else:
                    from ..performance_config import DEFAULT_PERFORMANCE_CONFIG
                    min_work_ms = DEFAULT_PERFORMANCE_CONFIG.process_pool.level3_min_work_ms
            except Exception:
                pass  # Use default

            # Estimate per-iteration work time via microbenchmark
            # Run 1-3 sample iterations to measure timing
            import time
            sample_count = min(3, total_iterations)
            sample_start_time = time.perf_counter()
            try:
                for sample_i in range(start, start + sample_count * step, step):
                    # Execute sample iteration (result discarded)
                    loop_func(sample_i)
                sample_end_time = time.perf_counter()
                sample_duration_ms = (sample_end_time - sample_start_time) * 1000.0
                per_iter_ms = sample_duration_ms / sample_count if sample_count > 0 else 0.0
                estimated_work_ms = per_iter_ms * total_iterations

                if estimated_work_ms < min_work_ms:
                    self.logger.debug(
                        f"Skipping Level 3 ProcessPool dispatch: estimated work time "
                        f"{estimated_work_ms:.1f}ms < {min_work_ms:.1f}ms threshold "
                        f"(per-iter: {per_iter_ms:.3f}ms, iters: {total_iterations}, "
                        f"use EPOCHLY_LEVEL3_MIN_WORK_MS to override)"
                    )
                    return None  # Trigger fallback to sequential or JIT-only

                self.logger.debug(
                    f"Level 3 work-time check passed: {estimated_work_ms:.1f}ms >= {min_work_ms:.1f}ms "
                    f"(per-iter: {per_iter_ms:.3f}ms)"
                )
            except Exception as e:
                # If microbenchmark fails, log and proceed cautiously
                # (better to try Level 3 than silently fail)
                self.logger.debug(f"Work-time estimation failed ({e}), proceeding with Level 3")

            # Bind locals into function if needed
            if bound_locals:
                loop_func = self._bind_loop_context(loop_func, bound_locals)

            # Get worker count from executor
            if hasattr(level3_executor, '_pool'):
                pool = level3_executor._pool
                if hasattr(pool, '_max_workers'):
                    num_workers = pool._max_workers
                elif hasattr(pool, '_processes') and pool._processes:
                    num_workers = len(pool._processes)
                else:
                    num_workers = 4  # Default
            else:
                num_workers = 4

            # Calculate chunks with adaptive strategy to minimize overhead
            # CRITICAL: Excessive chunking (512 chunks) creates 100% overhead for small tasks
            # Strategy: Use fewer, larger chunks to amortize IPC/pickle overhead
            num_chunks = self._calculate_optimal_chunks(num_workers, total_iterations)

            # Use ceil to ensure actual chunk count never exceeds desired num_chunks
            chunk_size = math.ceil(total_iterations / num_chunks)

            self.logger.info(f"Dispatching {total_iterations} iterations using Level 3 executor "
                           f"({num_workers} workers, {num_chunks} chunks of ~{chunk_size})")

            # Create chunks
            futures = []
            for chunk_start in range(start, end, chunk_size * step):
                chunk_end = min(chunk_start + chunk_size * step, end)

                # Submit via Level 3 executor
                # Note: execute() takes (func, *args)
                future = level3_executor.execute(
                    self._execute_chunk,
                    loop_func,
                    chunk_start,
                    chunk_end,
                    step
                )
                futures.append(future)

            # Collect results
            all_results = []
            for future in futures:
                result = future.result()
                # Handle ExecutionResult wrapper
                if hasattr(result, 'result'):
                    chunk_results = result.result
                else:
                    chunk_results = result

                if isinstance(chunk_results, list):
                    all_results.extend(chunk_results)
                else:
                    all_results.append(chunk_results)

            self.logger.info(f"Level 3 dispatch: {len(all_results)} results from {len(futures)} chunks")
            return all_results

        except Exception as e:
            self.logger.debug(f"Level 3 executor dispatch failed: {e}")
            return None

    def _dispatch_with_executor(
        self,
        loop_func: Callable,
        start: int,
        end: int,
        step: int,
        bound_locals: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Any]]:
        """
        Dispatch using Epochly executor (SubInterpreterPool or ProcessPool).

        Returns:
            List of results or None if dispatch failed
        """
        try:
            import math

            # Bind locals into function if needed
            if bound_locals:
                loop_func = self._bind_loop_context(loop_func, bound_locals)

            # Calculate chunk size (use ceil to avoid truncating remainder)
            if step == 0:
                raise ValueError("step cannot be zero")
            total_iterations = math.ceil(abs(end - start) / abs(step))
            num_workers = self._get_worker_count()

            # Use adaptive chunking to minimize overhead
            num_chunks = self._calculate_optimal_chunks(num_workers, total_iterations)
            chunk_size = math.ceil(total_iterations / num_chunks)

            self.logger.debug(f"Dispatching {total_iterations} iterations in {num_chunks} chunks of ~{chunk_size}")

            # Create chunks and submit
            futures = []
            for chunk_start in range(start, end, chunk_size * step):
                chunk_end = min(chunk_start + chunk_size * step, end)

                # Submit chunk via adapter (unified API)
                future = self.executor.submit(
                    self._execute_chunk,
                    loop_func,
                    chunk_start,
                    chunk_end,
                    step
                )
                futures.append(future)

            # Collect results via adapter
            all_results = []
            for i, future in enumerate(futures):
                unified_result = self.executor.get_result(future)

                if not unified_result.success:
                    self.logger.warning(f"Chunk {i} failed: {unified_result.error}")
                    continue

                # Extract chunk results
                chunk_results = unified_result.value

                if isinstance(chunk_results, list):
                    all_results.extend(chunk_results)
                else:
                    all_results.append(chunk_results)

            self.logger.debug(f"Collected {len(all_results)} results from {len(futures)} chunks")
            return all_results

        except Exception as e:
            self.logger.debug(f"Executor dispatch failed: {e}")
            return None  # Allow fallback to multiprocessing

    @staticmethod
    def _execute_chunk(loop_func: Callable, start: int, end: int, step: int) -> List[Any]:
        """
        Execute a chunk of loop iterations.

        Args:
            loop_func: Loop body function
            start: Chunk start index
            end: Chunk end index
            step: Loop step

        Returns:
            List of results for this chunk
        """
        results = []
        for i in range(start, end, step):
            results.append(loop_func(i))
        return results

    @staticmethod
    def _bind_loop_context(loop_func: Callable, bound_locals: Optional[Dict[str, Any]]) -> Callable:
        """Bind captured locals into function's globals for serialization."""
        if not bound_locals:
            return loop_func

        import types
        merged_globals = dict(loop_func.__globals__)
        merged_globals.update(bound_locals)

        return types.FunctionType(
            loop_func.__code__,
            merged_globals,
            loop_func.__name__,
            loop_func.__defaults__,
            loop_func.__closure__
        )

    def _get_worker_count(self) -> int:
        """Get number of available workers."""
        if hasattr(self.executor, 'get_worker_count'):
            return self.executor.get_worker_count()
        elif hasattr(self.executor, '_max_workers'):
            return self.executor._max_workers
        else:
            import os
            return os.cpu_count() or 4

    def _get_optimal_start_method(self) -> str:
        """
        Determine optimal multiprocessing start method for current platform.

        Per deep RCA (2025-11-19):
        - macOS spawn (default): 2.8× overhead + strict importability requirements
        - macOS fork (opt-in): Fast but requires vetted workloads
        - Linux fork (default): Best performance

        Strategy:
        - Linux: Use fork (default, best performance)
        - macOS: Use fork for compute-only workloads (bypasses spawn overhead)
        - Windows: Use spawn (only option)
        - Override: Respect EPOCHLY_MP_START environment variable

        Returns:
            Start method name ('fork', 'spawn', or 'forkserver')
        """
        import sys
        import os

        # Check for explicit override
        override = os.environ.get('EPOCHLY_MP_START', '').lower()
        if override in ('fork', 'spawn', 'forkserver'):
            self.logger.info(f"Using multiprocessing start method: {override} (from EPOCHLY_MP_START)")
            return override

        # Platform-specific defaults
        if sys.platform == 'darwin':
            # macOS: Default to spawn (safe) but allow fork opt-in for vetted workloads
            # Per RCA: spawn has 2.8× overhead but is safe with GUI/Cocoa frameworks
            # Fork eliminates overhead but risks deadlocks with multi-threaded code
            #
            # PRODUCTION DEFAULT: spawn (safe by default)
            # OPT-IN: Set EPOCHLY_MP_START=fork for pure compute workloads
            self.logger.info("Using multiprocessing start method: spawn (macOS safe default)")
            self.logger.info("TIP: Set EPOCHLY_MP_START=fork for 2.8× speedup on compute-only workloads")
            return 'spawn'
        elif sys.platform.startswith('linux'):
            # Linux: fork is default and best
            return 'fork'
        else:
            # Windows and others: spawn only
            return 'spawn'

    def _calculate_optimal_chunks(self, num_workers: int, total_iterations: int) -> int:
        """
        Calculate optimal chunk count to minimize overhead while maintaining load balance.

        Strategy based on MCP-Reflect RCA (2025-11-19):
        - PROBLEM: 32× oversubscription (512 chunks) creates 100% overhead for small tasks
        - SOLUTION: Use fewer, larger chunks to amortize IPC/pickle overhead
        - TARGET: Overhead <5% of total execution time

        Chunk sizing strategy:
        - Tiny workloads (<=1 iter): 1 chunk (no parallelization benefit)
        - Small workloads (<1000 iter): 4-8 chunks (large chunks, minimal overhead)
        - Medium workloads (1000-10000 iter): num_workers chunks (balance)
        - Large workloads (>10000 iter): num_workers * 2 chunks (better load balancing)

        Args:
            num_workers: Number of worker processes (auto-sanitized if 0/None)
            total_iterations: Total number of loop iterations

        Returns:
            Optimal number of chunks to minimize overhead (always <= total_iterations)
        """
        import math

        # Sanitize num_workers (handle 0/None from mis-configured adapters)
        if not num_workers or num_workers < 1:
            import os
            num_workers = os.cpu_count() or 4

        # Fast-path: No benefit to chunking tiny loops
        if total_iterations <= 1:
            return 1

        # Determine desired chunk count based on workload size
        if total_iterations < 100:
            # Very small: 2-4 chunks
            desired_chunks = min(4, max(2, num_workers // 4))
        elif total_iterations < 1000:
            # Small: 4-8 chunks (minimize overhead over perfect load balance)
            desired_chunks = min(8, max(4, num_workers // 2))
        elif total_iterations < 10000:
            # Medium: 1 chunk per worker (balance overhead and distribution)
            desired_chunks = num_workers
        else:
            # Large: 2× workers (moderate oversubscription for load balancing)
            desired_chunks = num_workers * 2

        # CRITICAL: Clamp chunk count to never exceed total_iterations
        # Without this, floor division in chunk_size causes over-chunking
        # E.g., 100 iters / 8 desired = 12 chunk_size → ceil(100/12) = 9 actual chunks
        return max(1, min(total_iterations, desired_chunks))

    def _dispatch_with_multiprocessing(
        self,
        loop_func: Callable,
        start: int,
        end: int,
        step: int,
        bound_locals: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Any]]:
        """
        Dispatch using stdlib multiprocessing.Pool as fallback.

        Uses a persistent global pool to eliminate process creation overhead (~40-80ms).
        CRITICAL: Uses cloudpickle to serialize dynamically-created loop functions.

        Returns:
            List of results or None if multiprocessing failed
        """
        try:
            from multiprocessing import get_context, cpu_count
            import math
            import cloudpickle
            import sys
            import os

            global _global_pool, _global_pool_lock

            num_workers = cpu_count() or 4

            # CRITICAL: Determine optimal start method for this platform
            # macOS spawn (default) has 2.8× overhead and strict importability requirements
            # Use fork when safe to eliminate overhead and enable dynamic function pickling
            start_method = self._get_optimal_start_method()

            # Calculate total iterations (use ceil to avoid truncating remainder)
            if step == 0:
                raise ValueError("step cannot be zero")
            total_iterations = math.ceil(abs(end - start) / abs(step))

            # Only use multiprocessing for substantial workloads
            if total_iterations < 100:
                return None  # Too small, use sequential

            # Calculate chunks with adaptive strategy
            num_chunks = self._calculate_optimal_chunks(num_workers, total_iterations)
            chunk_size = math.ceil(total_iterations / num_chunks)

            # CRITICAL FIX: Serialize both function and bound locals using cloudpickle
            # Standard pickle cannot handle dynamically-created functions from exec()
            # Bind locals into function BEFORE serialization
            if bound_locals:
                loop_func = self._bind_loop_context(loop_func, bound_locals)
            
            # This was causing silent worker crashes and sequential fallback
            payload = cloudpickle.dumps(loop_func)

            # Create chunks with pre-pickled function+locals
            chunks = []
            for chunk_start in range(start, end, chunk_size * step):
                chunk_end = min(chunk_start + chunk_size * step, end)
                chunks.append((payload, chunk_start, chunk_end, step))

            # Get or create persistent pool using module-level lock
            with _global_pool_lock:
                if _global_pool is None:
                    # Create persistent pool with optimal start method for platform
                    # CRITICAL: Use fork on macOS to bypass spawn overhead (2.8×) and pickling issues
                    ctx = get_context(start_method)
                    _global_pool = ctx.Pool(processes=num_workers)
                    self.logger.info(f"Created persistent multiprocessing.Pool with {num_workers} workers (method={start_method})")

                    # Register cleanup on exit
                    import atexit
                    def cleanup_pool():
                        global _global_pool
                        if _global_pool:
                            _global_pool.close()
                            _global_pool.join()
                            _global_pool = None
                    atexit.register(cleanup_pool)

                pool = _global_pool

            self.logger.info(f"Using persistent multiprocessing.Pool for {len(chunks)} chunks")

            # Execute chunks in parallel using cloudpickle-serialized function
            # CRITICAL FIX: Use module-level function (picklable with spawn)

            # Conditional debug logging (production: no overhead)
            if _DEBUG_PARALLELIZATION or logger.isEnabledFor(logging.DEBUG):
                pool_state = getattr(pool, '_state', 'unknown')
                first_chunk_range = f"[{chunks[0][1]}:{chunks[0][2]}:{chunks[0][3]}]" if chunks else 'NO_CHUNKS'
                logger.debug(
                    f"pool.starmap dispatch: workers={num_workers}, chunks={len(chunks)}, "
                    f"first_chunk={first_chunk_range}, method={start_method}"
                )

            chunk_results = pool.starmap(_execute_chunk_cloudpickle_worker, chunks)

            # Conditional debug logging (production: no overhead)
            if _DEBUG_PARALLELIZATION or logger.isEnabledFor(logging.DEBUG):
                total_results = sum(len(c) if isinstance(c, list) else 1 for c in chunk_results)
                first_result = chunk_results[0] if chunk_results else None
                first_len = len(first_result) if isinstance(first_result, list) else 'N/A'
                logger.debug(
                    f"pool.starmap complete: {len(chunk_results)} chunks, "
                    f"{total_results} total results, first_chunk_len={first_len}"
                )

            # Flatten results
            all_results = []
            for chunk in chunk_results:
                if isinstance(chunk, list):
                    all_results.extend(chunk)
                else:
                    all_results.append(chunk)

            self.logger.info(f"Batch dispatch via multiprocessing.Pool: {len(all_results)} results")
            return all_results

        except Exception as e:
            # Log dispatch failures at WARNING (actionable operational errors)
            self.logger.warning(
                f"multiprocessing.Pool dispatch failed: {type(e).__name__}: {e}",
                exc_info=True  # Include traceback for debugging
            )
            return None

    @staticmethod
    def _execute_chunk_cloudpickle(pickled_func: bytes, start: int, end: int, step: int) -> List[Any]:
        """
        Execute chunk with cloudpickle-serialized function (already has locals bound).

        CRITICAL: This allows dynamically-created functions (from exec()) to be executed
        in worker processes on macOS where multiprocessing uses 'spawn' method.

        Args:
            pickled_func: Cloudpickle-serialized loop function (with captured locals already bound)
            start: Chunk start index
            end: Chunk end index
            step: Loop step

        Returns:
            List of results for this chunk
        """
        import cloudpickle

        # Unpickle function (locals already bound before serialization)
        loop_func = cloudpickle.loads(pickled_func)

        # Execute chunk
        results = []
        for i in range(start, end, step):
            results.append(loop_func(i))
        return results


def create_batch_dispatcher(executor=None):
    """
    Create a batch dispatcher with the given executor.

    Args:
        executor: Level 3 executor or None for auto-detection

    Returns:
        BatchDispatcher instance
    """
    if executor is None:
        # Try to get Level 3 executor from core
        try:
            from ..core.epochly_core import get_epochly_core
            core = get_epochly_core()

            # Trigger lazy Level 3 initialization if deferred
            if hasattr(core, '_ensure_level3_initialized'):
                core._ensure_level3_initialized()

            if core and hasattr(core, '_sub_interpreter_executor') and core._sub_interpreter_executor:
                executor = core._sub_interpreter_executor
                logger.debug("Using Level 3 executor for batch dispatch")
        except:
            pass

    return BatchDispatcher(executor=executor)
