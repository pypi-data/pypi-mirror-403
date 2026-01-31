"""
NumPy GIL-bound operation optimizer for Epochly Level 3.

CRITICAL INSIGHT (Nov 2025 mcp-reflect research):
Standard NumPy operations (dot, matmul, sum, mean) CANNOT benefit from
Epochly parallelization because:
1. They already release the GIL
2. OpenBLAS/MKL provides internal parallelization
3. Pickle/IPC overhead exceeds any potential gain

HOWEVER, GIL-bound NumPy operations CAN benefit:
- np.vectorize() with Python functions: 7x+ speedup achievable
- np.apply_along_axis() with Python functions: parallelizable
- Operations on object arrays with Python methods
- Custom ufuncs written in pure Python

This module provides optimization for these GIL-bound cases.
"""

from __future__ import annotations

import os
import logging
import pickle
from concurrent.futures import ProcessPoolExecutor
from typing import Callable, Any, Optional, List
from dataclasses import dataclass

try:
    import cloudpickle
    HAS_CLOUDPICKLE = True
except ImportError:
    HAS_CLOUDPICKLE = False

logger = logging.getLogger(__name__)


def _register_executor(executor: ProcessPoolExecutor) -> None:
    """
    Register ProcessPoolExecutor in global registry for cleanup.

    This ensures executors created by optimizers are properly shut down
    during pytest session teardown, preventing orphaned processes.
    """
    # Primary: Use centralized executor registry (orphan detection, unified cleanup)
    try:
        from epochly.core.executor_registry import register_executor
        register_executor(executor, name="numpy_optimizer_pool")
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


@dataclass
class VectorizeDecision:
    """Decision about whether to parallelize vectorize operation."""
    should_parallelize: bool
    reason: str
    estimated_speedup: float
    num_workers: int
    estimated_sequential_ms: float
    estimated_parallel_ms: float


# Worker function must be at module level for pickling
def _worker_vectorize(chunk_data: bytes, func_bytes: bytes, use_cloudpickle: bool) -> bytes:
    """
    Worker function for parallel vectorize.

    Args:
        chunk_data: Pickled array chunk
        func_bytes: Pickled Python function
        use_cloudpickle: Whether cloudpickle was used

    Returns:
        Pickled result array
    """
    import numpy as np

    # Unpickle data
    chunk = pickle.loads(chunk_data)

    # Unpickle function
    if use_cloudpickle:
        import cloudpickle
        func = cloudpickle.loads(func_bytes)
    else:
        func = pickle.loads(func_bytes)

    # Execute vectorize
    vectorized = np.vectorize(func)
    result = vectorized(chunk)

    return pickle.dumps(result)


def _worker_apply_along_axis(
    chunk_data: bytes,
    func_bytes: bytes,
    axis: int,
    use_cloudpickle: bool
) -> bytes:
    """
    Worker function for parallel apply_along_axis.

    Args:
        chunk_data: Pickled array chunk
        func_bytes: Pickled Python function
        axis: Axis to apply along
        use_cloudpickle: Whether cloudpickle was used

    Returns:
        Pickled result array
    """
    import numpy as np

    # Unpickle data
    chunk = pickle.loads(chunk_data)

    # Unpickle function
    if use_cloudpickle:
        import cloudpickle
        func = cloudpickle.loads(func_bytes)
    else:
        func = pickle.loads(func_bytes)

    # Execute apply_along_axis
    result = np.apply_along_axis(func, axis, chunk)

    return pickle.dumps(result)


class NumpyGILOptimizer:
    """
    Parallel optimizer for GIL-bound NumPy operations.

    Standard NumPy ops (matmul, sum, etc.) are NOT optimized here because
    they release the GIL and use internal parallelization.

    This optimizer handles:
    - np.vectorize() with Python functions
    - np.apply_along_axis() with Python functions

    Strategy:
    1. Check if operation is truly GIL-bound (Python function)
    2. Check if data is large enough (overhead threshold)
    3. Split array into chunks
    4. Process chunks in parallel via ProcessPoolExecutor
    5. Concatenate results
    """

    # Thresholds for GIL-bound operation parallelization
    MIN_ELEMENTS = 1_000_000  # 1M elements minimum
    MIN_ARRAY_BYTES = 10_000_000  # 10MB minimum
    MIN_ESTIMATED_TIME_MS = 500  # 500ms estimated sequential time

    def __init__(self, num_workers: int = None):
        """
        Args:
            num_workers: Number of workers (default: cpu_count - 1)
        """
        if num_workers is None:
            num_workers = max(1, os.cpu_count() - 1)
        self.num_workers = num_workers
        self._executor = None

    def _get_executor(self) -> ProcessPoolExecutor:
        """Get or create ProcessPoolExecutor."""
        if self._executor is None:
            self._executor = ProcessPoolExecutor(max_workers=self.num_workers)
            _register_executor(self._executor)
        return self._executor

    def is_python_callable(self, func: Callable) -> bool:
        """
        Check if function is pure Python (GIL-bound).

        C extensions and numpy ufuncs release the GIL.
        Only pure Python functions are GIL-bound.
        """
        # Check for C function
        if hasattr(func, '__code__'):
            # Has Python bytecode - it's pure Python
            return True

        # Check for numpy ufunc
        try:
            import numpy as np
            if isinstance(func, np.ufunc):
                return False  # numpy ufuncs release GIL
        except ImportError:
            pass

        # Check for built-in C functions
        if isinstance(func, type(len)):  # Built-in function type
            return False

        # Check for lambda (pure Python)
        if hasattr(func, '__name__') and func.__name__ == '<lambda>':
            return True

        # Default: assume Python if we can't determine
        return True

    def should_parallelize_vectorize(
        self,
        arr,  # np.ndarray
        func: Callable
    ) -> VectorizeDecision:
        """
        Decide if vectorize parallelization is beneficial.

        Args:
            arr: Input array
            func: Python function to vectorize

        Returns:
            VectorizeDecision
        """
        import numpy as np

        # Check if function is Python (GIL-bound)
        if not self.is_python_callable(func):
            return VectorizeDecision(
                should_parallelize=False,
                reason="Function is not pure Python (releases GIL)",
                estimated_speedup=1.0,
                num_workers=0,
                estimated_sequential_ms=0,
                estimated_parallel_ms=0
            )

        # Check array size
        if arr.size < self.MIN_ELEMENTS:
            return VectorizeDecision(
                should_parallelize=False,
                reason=f"Array too small ({arr.size} < {self.MIN_ELEMENTS} elements)",
                estimated_speedup=1.0,
                num_workers=0,
                estimated_sequential_ms=0,
                estimated_parallel_ms=0
            )

        if arr.nbytes < self.MIN_ARRAY_BYTES:
            return VectorizeDecision(
                should_parallelize=False,
                reason=f"Array too small ({arr.nbytes / 1e6:.1f}MB < {self.MIN_ARRAY_BYTES / 1e6:.1f}MB)",
                estimated_speedup=1.0,
                num_workers=0,
                estimated_sequential_ms=0,
                estimated_parallel_ms=0
            )

        # Estimate sequential time
        # Assume ~0.001ms per element for Python function call overhead
        estimated_sequential_ms = arr.size * 0.001

        if estimated_sequential_ms < self.MIN_ESTIMATED_TIME_MS:
            return VectorizeDecision(
                should_parallelize=False,
                reason=f"Estimated time too short ({estimated_sequential_ms:.0f}ms < {self.MIN_ESTIMATED_TIME_MS}ms)",
                estimated_speedup=1.0,
                num_workers=0,
                estimated_sequential_ms=estimated_sequential_ms,
                estimated_parallel_ms=0
            )

        # Calculate expected speedup
        # Overhead: ~50ms IPC + pickle time (~1ms/MB)
        pickle_overhead_ms = arr.nbytes / 1e6 * 2  # pickle + unpickle
        ipc_overhead_ms = 50 * self.num_workers
        total_overhead_ms = pickle_overhead_ms + ipc_overhead_ms

        # Parallel execution time
        parallel_exec_ms = estimated_sequential_ms / self.num_workers
        estimated_parallel_ms = parallel_exec_ms + total_overhead_ms

        estimated_speedup = estimated_sequential_ms / estimated_parallel_ms

        if estimated_speedup < 1.5:
            return VectorizeDecision(
                should_parallelize=False,
                reason=f"Insufficient speedup ({estimated_speedup:.2f}x < 1.5x)",
                estimated_speedup=estimated_speedup,
                num_workers=self.num_workers,
                estimated_sequential_ms=estimated_sequential_ms,
                estimated_parallel_ms=estimated_parallel_ms
            )

        return VectorizeDecision(
            should_parallelize=True,
            reason=f"Expected {estimated_speedup:.1f}x speedup with {self.num_workers} workers",
            estimated_speedup=estimated_speedup,
            num_workers=self.num_workers,
            estimated_sequential_ms=estimated_sequential_ms,
            estimated_parallel_ms=estimated_parallel_ms
        )

    def optimize_vectorize(
        self,
        arr,  # np.ndarray
        func: Callable
    ) -> Any:
        """
        Execute np.vectorize in parallel.

        Args:
            arr: Input array
            func: Python function to vectorize

        Returns:
            Result array (same shape as input)
        """
        import numpy as np

        # Check if parallelization is beneficial
        decision = self.should_parallelize_vectorize(arr, func)

        if not decision.should_parallelize:
            logger.debug(f"Falling back to sequential vectorize: {decision.reason}")
            return np.vectorize(func)(arr)

        logger.debug(f"Parallel vectorize: {decision.reason}")

        # Serialize function
        use_cloudpickle = HAS_CLOUDPICKLE
        if use_cloudpickle:
            func_bytes = cloudpickle.dumps(func)
        else:
            func_bytes = pickle.dumps(func)

        # Split array into chunks
        flat = arr.ravel()
        chunk_size = len(flat) // self.num_workers
        chunks = []
        for i in range(self.num_workers):
            start = i * chunk_size
            end = start + chunk_size if i < self.num_workers - 1 else len(flat)
            chunks.append(flat[start:end])

        # Submit to workers
        executor = self._get_executor()
        futures = []
        for chunk in chunks:
            chunk_bytes = pickle.dumps(chunk)
            future = executor.submit(
                _worker_vectorize,
                chunk_bytes,
                func_bytes,
                use_cloudpickle
            )
            futures.append(future)

        # Collect results
        results = []
        for future in futures:
            result_bytes = future.result()
            results.append(pickle.loads(result_bytes))

        # Concatenate and reshape
        flat_result = np.concatenate(results)
        return flat_result.reshape(arr.shape)

    def optimize_apply_along_axis(
        self,
        func: Callable,
        axis: int,
        arr  # np.ndarray
    ) -> Any:
        """
        Execute np.apply_along_axis in parallel.

        Strategy: Split array along axis perpendicular to application axis,
        process chunks in parallel, concatenate results.

        Args:
            func: Python function to apply
            axis: Axis to apply along
            arr: Input array

        Returns:
            Result array
        """
        import numpy as np

        # Check if function is Python
        if not self.is_python_callable(func):
            logger.debug("Falling back to sequential apply_along_axis: function releases GIL")
            return np.apply_along_axis(func, axis, arr)

        # Check array size
        if arr.nbytes < self.MIN_ARRAY_BYTES:
            logger.debug(f"Falling back to sequential: array too small ({arr.nbytes / 1e6:.1f}MB)")
            return np.apply_along_axis(func, axis, arr)

        # Serialize function
        use_cloudpickle = HAS_CLOUDPICKLE
        if use_cloudpickle:
            func_bytes = cloudpickle.dumps(func)
        else:
            func_bytes = pickle.dumps(func)

        # Split array perpendicular to application axis
        # E.g., if axis=1, split along axis=0
        split_axis = 0 if axis != 0 else 1
        if arr.ndim < 2:
            # 1D array - can't split perpendicular
            logger.debug("Falling back to sequential: 1D array")
            return np.apply_along_axis(func, axis, arr)

        chunks = np.array_split(arr, self.num_workers, axis=split_axis)

        # Submit to workers
        executor = self._get_executor()
        futures = []
        for chunk in chunks:
            chunk_bytes = pickle.dumps(chunk)
            future = executor.submit(
                _worker_apply_along_axis,
                chunk_bytes,
                func_bytes,
                axis,
                use_cloudpickle
            )
            futures.append(future)

        # Collect results
        results = []
        for future in futures:
            result_bytes = future.result()
            results.append(pickle.loads(result_bytes))

        # Concatenate along split axis
        return np.concatenate(results, axis=split_axis)

    def shutdown(self):
        """Shutdown the executor."""
        if self._executor is not None:
            self._executor.shutdown(wait=False)
            self._executor = None


def should_parallelize_numpy_gil_op(operation: str, arr, func: Callable = None) -> bool:
    """
    Quick check if NumPy operation should be parallelized.

    Args:
        operation: Operation name ('vectorize', 'apply_along_axis')
        arr: Input array
        func: Python function (if applicable)

    Returns:
        True if parallelization is beneficial
    """
    optimizer = NumpyGILOptimizer()

    if operation == 'vectorize':
        decision = optimizer.should_parallelize_vectorize(arr, func)
        return decision.should_parallelize

    # For other operations, use basic size check
    try:
        import numpy as np
        if arr.nbytes < 10_000_000:  # 10MB threshold
            return False
        if func and not optimizer.is_python_callable(func):
            return False
        return True
    except Exception:
        return False
