"""
Pattern-Aware Kernel Compiler for LEVEL_4 GPU Acceleration.

This module compiles detected loop patterns to actual CuPy CUDA kernels,
replacing Python for-loop execution with true GPU parallelism.

Key features:
1. Map patterns -> CuPy ElementwiseKernel
2. Reduce patterns -> CuPy ReductionKernel
3. Kernel caching with dtype-aware keys
4. Compilation failure tracking (integrated into compilation path)
5. Runtime type inference
6. Non-contiguous array handling
7. Thread-safe with double-checked locking
8. Dtype-specific code generation (e.g., abs for int vs float)

Reference: planning/level4-transparent-gpu-acceleration-design.md
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, Set, Union

import numpy as np

logger = logging.getLogger(__name__)


class KernelCompilationError(Exception):
    """Raised when kernel compilation fails."""
    pass


class UnsupportedOperationError(Exception):
    """Raised when an operation cannot be compiled to a CUDA kernel."""
    pass


class UnsupportedDtypeError(Exception):
    """Raised when a dtype is not supported for kernel compilation."""
    pass


class KernelType(Enum):
    """Type of compiled kernel."""
    ELEMENTWISE = "elementwise"
    REDUCTION = "reduction"


# Supported dtypes for kernel compilation
SUPPORTED_DTYPES = {
    np.float64, np.float32,
    np.int64, np.int32,
    np.uint64, np.uint32,
}

# Float dtypes (for operations that differ between int/float)
FLOAT_DTYPES = {np.float64, np.float32}

# Integer dtypes
INT_DTYPES = {np.int64, np.int32}

# Unsigned integer dtypes
UINT_DTYPES = {np.uint64, np.uint32}


@dataclass
class CompiledKernel:
    """Wrapper for a compiled CuPy kernel with execution interface."""

    kernel: Any  # CuPy ElementwiseKernel or ReductionKernel
    operation: str
    input_dtype: np.dtype
    output_dtype: np.dtype
    kernel_type: KernelType
    compilation_time_ms: float = 0.0

    def execute(self, *args):
        """Execute the kernel on GPU arrays."""
        if self.kernel_type == KernelType.ELEMENTWISE:
            return self._execute_elementwise(*args)
        elif self.kernel_type == KernelType.REDUCTION:
            return self._execute_reduction(*args)
        else:
            raise ValueError(f"Unknown kernel type: {self.kernel_type}")

    def _execute_elementwise(self, *args):
        """Execute an elementwise kernel."""
        # Single-input operations
        if self.operation in ('square', 'negate', 'abs'):
            arr = args[0]
            return self.kernel(arr)
        # Two-input operations
        elif self.operation in ('add', 'multiply'):
            a, b = args[0], args[1]
            return self.kernel(a, b)
        else:
            raise ValueError(f"Unknown operation: {self.operation}")

    def _execute_reduction(self, *args):
        """Execute a reduction kernel."""
        arr = args[0]
        return self.kernel(arr)


class LRUKernelCache:
    """Thread-safe LRU cache for compiled kernels with size limit."""

    def __init__(self, max_size: int = 128):
        """Initialize the cache with a maximum size."""
        self._cache: OrderedDict[str, CompiledKernel] = OrderedDict()
        self._max_size = max_size
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[CompiledKernel]:
        """Get a kernel from cache, moving it to end (most recent)."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return None

    def put(self, key: str, kernel: CompiledKernel) -> None:
        """Add a kernel to cache, evicting oldest if at capacity."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = kernel
            else:
                if len(self._cache) >= self._max_size:
                    oldest_key, _ = self._cache.popitem(last=False)
                    logger.debug(f"Evicted kernel from cache: {oldest_key}")
                self._cache[key] = kernel

    def put_if_absent(self, key: str, kernel: CompiledKernel) -> CompiledKernel:
        """Add kernel only if not present, return existing or new kernel."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            if len(self._cache) >= self._max_size:
                oldest_key, _ = self._cache.popitem(last=False)
                logger.debug(f"Evicted kernel from cache: {oldest_key}")
            self._cache[key] = kernel
            return kernel

    def clear(self) -> None:
        """Clear all cached kernels."""
        with self._lock:
            self._cache.clear()

    @property
    def stats(self) -> Dict[str, Union[int, float]]:
        """Return cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': self._hits / total if total > 0 else 0.0
            }


class PatternKernelCompiler:
    """
    Compiles loop patterns to CuPy CUDA kernels for true GPU parallelism.

    This replaces the Python for-loop execution with actual compiled CUDA
    kernels that leverage GPU parallelism properly.

    Thread-safe implementation with LRU kernel caching and failure tracking.

    Note on ReductionKernel output_dtype:
        CuPy's ReductionKernel uses template type 'T' which is inferred from
        the input array dtype. The output_dtype parameter is validated to
        match input_dtype for reductions. This is standard behavior for
        reductions (e.g., sum of float64 returns float64).
    """

    # Supported map operations and their CUDA code
    # Note: 'abs' has dtype-specific code generated at compile time
    MAP_OPERATIONS = {
        'square': {
            'code': 'out0 = in0 * in0',
            'inputs': 1,
            'name': 'pattern_square',
        },
        'add': {
            'code': 'out0 = in0 + in1',
            'inputs': 2,
            'name': 'pattern_add',
        },
        'multiply': {
            'code': 'out0 = in0 * in1',
            'inputs': 2,
            'name': 'pattern_multiply',
        },
        'negate': {
            'code': 'out0 = -in0',
            'inputs': 1,
            'name': 'pattern_negate',
        },
        'abs': {
            'code': None,  # Dtype-specific, set at compile time
            'inputs': 1,
            'name': 'pattern_abs',
        },
    }

    # Supported reduce operations with dtype-aware identity values
    # Using template type T for dtype flexibility (per CuPy docs)
    REDUCE_OPERATIONS = {
        'sum': {
            'in_params': 'T x',
            'out_params': 'T y',
            'map_expr': 'x',
            'reduce_expr': 'a + b',
            'post_map_expr': 'y = a',
            'identity': '0',
            'name': 'pattern_sum',
        },
        'max': {
            'in_params': 'T x',
            'out_params': 'T y',
            'map_expr': 'x',
            'reduce_expr': 'max(a, b)',
            'post_map_expr': 'y = a',
            'identity': None,  # Dtype-specific, set at compile time
            'name': 'pattern_max',
        },
        'min': {
            'in_params': 'T x',
            'out_params': 'T y',
            'map_expr': 'x',
            'reduce_expr': 'min(a, b)',
            'post_map_expr': 'y = a',
            'identity': None,  # Dtype-specific, set at compile time
            'name': 'pattern_min',
        },
        'prod': {
            'in_params': 'T x',
            'out_params': 'T y',
            'map_expr': 'x',
            'reduce_expr': 'a * b',
            'post_map_expr': 'y = a',
            'identity': '1',
            'name': 'pattern_prod',
        },
    }

    # Dtype-specific identity values for max/min operations
    MAX_IDENTITY = {
        np.float64: '-1.7976931348623157e+308',  # -DBL_MAX
        np.float32: '-3.4028235e+38',             # -FLT_MAX
        np.int64: '-9223372036854775808LL',       # LLONG_MIN
        np.int32: '-2147483648',                  # INT_MIN
        np.uint64: '0ULL',
        np.uint32: '0U',
    }

    MIN_IDENTITY = {
        np.float64: '1.7976931348623157e+308',   # DBL_MAX
        np.float32: '3.4028235e+38',              # FLT_MAX
        np.int64: '9223372036854775807LL',        # LLONG_MAX
        np.int32: '2147483647',                   # INT_MAX
        np.uint64: '18446744073709551615ULL',     # ULLONG_MAX
        np.uint32: '4294967295U',                 # UINT_MAX
    }

    def __init__(self, cache_size: int = 128):
        """Initialize the pattern kernel compiler."""
        self._kernel_cache = LRUKernelCache(max_size=cache_size)
        self._failure_cache: Dict[str, str] = {}
        self._failure_lock = threading.Lock()
        self._cupy_available: Optional[bool] = None
        self._cupy_check_lock = threading.Lock()

    def _check_cupy(self) -> bool:
        """Check if CuPy is available (thread-safe with caching)."""
        if self._cupy_available is None:
            with self._cupy_check_lock:
                if self._cupy_available is None:
                    try:
                        import cupy
                        self._cupy_available = True
                    except ImportError:
                        self._cupy_available = False
                        logger.warning(
                            "CuPy not available - GPU kernels will not work. "
                            "Install with: pip install cupy-cuda12x"
                        )
        return self._cupy_available

    def _validate_dtype(self, dtype: np.dtype) -> None:
        """Validate that dtype is supported for kernel compilation."""
        dtype = np.dtype(dtype)
        if dtype.type not in SUPPORTED_DTYPES:
            raise UnsupportedDtypeError(
                f"Dtype '{dtype}' is not supported. "
                f"Supported dtypes: {[np.dtype(d).name for d in SUPPORTED_DTYPES]}"
            )

    def _is_float_dtype(self, dtype: np.dtype) -> bool:
        """Check if dtype is a floating point type."""
        return np.dtype(dtype).type in FLOAT_DTYPES

    def _is_unsigned_dtype(self, dtype: np.dtype) -> bool:
        """Check if dtype is an unsigned integer type."""
        return np.dtype(dtype).type in UINT_DTYPES

    def get_supported_operations(self) -> Set[str]:
        """Return set of supported map and reduce operations."""
        ops = set(self.MAP_OPERATIONS.keys())
        ops.update(self.REDUCE_OPERATIONS.keys())
        return ops

    def _get_cache_key(
        self,
        pattern_type: str,
        operation: str,
        input_dtype: np.dtype,
        output_dtype: np.dtype
    ) -> str:
        """Generate a cache key for the kernel."""
        return f"{pattern_type}:{operation}:{input_dtype}:{output_dtype}"

    def _get_failure_key(
        self,
        pattern_type: str,
        operation: str,
        input_dtype: np.dtype,
        output_dtype: np.dtype
    ) -> str:
        """Generate a failure cache key (same as cache key for consistency)."""
        return self._get_cache_key(pattern_type, operation, input_dtype, output_dtype)

    def _check_failure_cache(self, failure_key: str) -> Optional[str]:
        """Check if this compilation is known to fail. Returns failure reason or None."""
        with self._failure_lock:
            return self._failure_cache.get(failure_key)

    def _record_failure(self, failure_key: str, reason: str) -> None:
        """Record a compilation failure."""
        with self._failure_lock:
            self._failure_cache[failure_key] = reason
        logger.debug(f"Recorded compilation failure for {failure_key}: {reason}")

    def _dtype_to_cupy_type(self, dtype: np.dtype) -> str:
        """Convert numpy dtype to CuPy type string."""
        dtype = np.dtype(dtype)
        mapping = {
            np.float64: 'float64',
            np.float32: 'float32',
            np.int64: 'int64',
            np.int32: 'int32',
            np.uint64: 'uint64',
            np.uint32: 'uint32',
        }
        cupy_type = mapping.get(dtype.type)
        if cupy_type is None:
            raise UnsupportedDtypeError(f"Cannot convert dtype '{dtype}' to CuPy type")
        return cupy_type

    def _get_identity_for_dtype(self, operation: str, dtype: np.dtype) -> str:
        """Get dtype-appropriate identity value for reduce operations."""
        dtype = np.dtype(dtype)
        if operation == 'max':
            return self.MAX_IDENTITY.get(dtype.type, '-1e308')
        elif operation == 'min':
            return self.MIN_IDENTITY.get(dtype.type, '1e308')
        else:
            # Use operation's default identity
            return self.REDUCE_OPERATIONS[operation]['identity']

    def _get_abs_code_for_dtype(self, dtype: np.dtype) -> str:
        """Get dtype-appropriate abs code.

        For floats: use fabs (CUDA math function)
        For signed ints: use ternary (no abs for long long in CUDA)
        For unsigned: identity (always positive)

        Note: For signed integers, abs(INT_MIN) causes overflow since the
        absolute value cannot be represented in the same signed type. This
        matches numpy behavior which also wraps around for integer abs of
        minimum values.
        """
        dtype = np.dtype(dtype)
        if self._is_float_dtype(dtype):
            return 'out0 = fabs(in0)'
        elif self._is_unsigned_dtype(dtype):
            # Unsigned values are always non-negative
            return 'out0 = in0'
        else:
            # Signed integer: use ternary operator
            return 'out0 = (in0 < 0) ? -in0 : in0'

    def compile_map_pattern(
        self,
        operation: str,
        input_dtype: np.dtype,
        output_dtype: np.dtype
    ) -> CompiledKernel:
        """
        Compile a map pattern to a CuPy ElementwiseKernel.

        Args:
            operation: The map operation ('square', 'add', 'multiply', etc.)
            input_dtype: Input array dtype
            output_dtype: Output array dtype

        Returns:
            CompiledKernel wrapping a CuPy ElementwiseKernel

        Raises:
            RuntimeError: If CuPy is not available
            UnsupportedOperationError: If operation is not supported
            UnsupportedDtypeError: If dtype is not supported
            KernelCompilationError: If kernel compilation fails or previously failed
        """
        if not self._check_cupy():
            raise RuntimeError("CuPy is not available")

        if operation not in self.MAP_OPERATIONS:
            raise UnsupportedOperationError(
                f"Operation '{operation}' is not supported. "
                f"Supported operations: {list(self.MAP_OPERATIONS.keys())}"
            )

        # Validate dtypes
        self._validate_dtype(input_dtype)
        self._validate_dtype(output_dtype)

        cache_key = self._get_cache_key('map', operation, input_dtype, output_dtype)

        # Check kernel cache first (common path - fast return for cached kernels)
        cached = self._kernel_cache.get(cache_key)
        if cached is not None:
            return cached

        # Check failure cache (avoid repeated failed compilations)
        failure_key = self._get_failure_key('map', operation, input_dtype, output_dtype)
        failure_reason = self._check_failure_cache(failure_key)
        if failure_reason is not None:
            raise KernelCompilationError(
                f"Compilation previously failed for map:{operation} "
                f"({input_dtype} -> {output_dtype}): {failure_reason}"
            )

        # Compile kernel outside of lock
        import cupy as cp

        op_info = self.MAP_OPERATIONS[operation]
        cupy_type = self._dtype_to_cupy_type(input_dtype)
        out_type = self._dtype_to_cupy_type(output_dtype)

        # Build input signature
        if op_info['inputs'] == 1:
            in_params = f'{cupy_type} in0'
        else:
            in_params = ', '.join(
                f'{cupy_type} in{i}' for i in range(op_info['inputs'])
            )

        out_params = f'{out_type} out0'

        # Get operation code (dtype-specific for some operations)
        if operation == 'abs':
            code = self._get_abs_code_for_dtype(input_dtype)
        else:
            code = op_info['code']

        try:
            start_time = time.perf_counter()
            kernel = cp.ElementwiseKernel(
                in_params,
                out_params,
                code,
                op_info['name']
            )
            compilation_time_ms = (time.perf_counter() - start_time) * 1000
        except Exception as e:
            # Record failure to avoid repeated attempts
            self._record_failure(failure_key, str(e))
            raise KernelCompilationError(
                f"Failed to compile map kernel '{operation}': {e}"
            ) from e

        compiled = CompiledKernel(
            kernel=kernel,
            operation=operation,
            input_dtype=np.dtype(input_dtype),
            output_dtype=np.dtype(output_dtype),
            kernel_type=KernelType.ELEMENTWISE,
            compilation_time_ms=compilation_time_ms
        )

        # Add to cache using put_if_absent to handle concurrent compilations
        result = self._kernel_cache.put_if_absent(cache_key, compiled)

        logger.debug(
            f"Compiled map kernel: {operation} "
            f"({input_dtype} -> {output_dtype}) in {compilation_time_ms:.2f}ms"
        )

        return result

    def compile_reduce_pattern(
        self,
        operation: str,
        input_dtype: np.dtype,
        output_dtype: Optional[np.dtype] = None
    ) -> CompiledKernel:
        """
        Compile a reduce pattern to a CuPy ReductionKernel.

        Note: CuPy's ReductionKernel uses template type 'T' which is inferred
        from the input array dtype. The output_dtype must match input_dtype
        for standard reductions (sum, max, min, prod).

        Args:
            operation: The reduce operation ('sum', 'max', 'min', 'prod')
            input_dtype: Input array dtype
            output_dtype: Output array dtype (defaults to input_dtype, must match)

        Returns:
            CompiledKernel wrapping a CuPy ReductionKernel

        Raises:
            RuntimeError: If CuPy is not available
            UnsupportedOperationError: If operation is not supported
            UnsupportedDtypeError: If dtype is not supported
            ValueError: If output_dtype doesn't match input_dtype
            KernelCompilationError: If kernel compilation fails or previously failed
        """
        if not self._check_cupy():
            raise RuntimeError("CuPy is not available")

        if operation not in self.REDUCE_OPERATIONS:
            raise UnsupportedOperationError(
                f"Operation '{operation}' is not supported for reduction. "
                f"Supported operations: {list(self.REDUCE_OPERATIONS.keys())}"
            )

        # Validate input dtype
        self._validate_dtype(input_dtype)

        # Default output_dtype to input_dtype (standard reduction behavior)
        if output_dtype is None:
            output_dtype = input_dtype
        else:
            self._validate_dtype(output_dtype)
            # Validate that output_dtype matches input_dtype for template T
            if np.dtype(output_dtype) != np.dtype(input_dtype):
                raise ValueError(
                    f"For reduction operations, output_dtype ({output_dtype}) must match "
                    f"input_dtype ({input_dtype}). CuPy ReductionKernel uses template type 'T' "
                    f"which is inferred from the input array."
                )

        cache_key = self._get_cache_key('reduce', operation, input_dtype, output_dtype)

        # Check kernel cache first (common path - fast return for cached kernels)
        cached = self._kernel_cache.get(cache_key)
        if cached is not None:
            return cached

        # Check failure cache (avoid repeated failed compilations)
        failure_key = self._get_failure_key('reduce', operation, input_dtype, output_dtype)
        failure_reason = self._check_failure_cache(failure_key)
        if failure_reason is not None:
            raise KernelCompilationError(
                f"Compilation previously failed for reduce:{operation} "
                f"({input_dtype} -> {output_dtype}): {failure_reason}"
            )

        # Compile kernel outside of lock
        import cupy as cp

        op_info = self.REDUCE_OPERATIONS[operation]

        # Get dtype-appropriate identity value
        identity = self._get_identity_for_dtype(operation, input_dtype)

        try:
            start_time = time.perf_counter()
            kernel = cp.ReductionKernel(
                op_info['in_params'],
                op_info['out_params'],
                op_info['map_expr'],
                op_info['reduce_expr'],
                op_info['post_map_expr'],
                identity,
                op_info['name']
            )
            compilation_time_ms = (time.perf_counter() - start_time) * 1000
        except Exception as e:
            # Record failure to avoid repeated attempts
            self._record_failure(failure_key, str(e))
            raise KernelCompilationError(
                f"Failed to compile reduce kernel '{operation}': {e}"
            ) from e

        compiled = CompiledKernel(
            kernel=kernel,
            operation=operation,
            input_dtype=np.dtype(input_dtype),
            output_dtype=np.dtype(output_dtype),
            kernel_type=KernelType.REDUCTION,
            compilation_time_ms=compilation_time_ms
        )

        # Add to cache using put_if_absent to handle concurrent compilations
        result = self._kernel_cache.put_if_absent(cache_key, compiled)

        logger.debug(
            f"Compiled reduce kernel: {operation} "
            f"({input_dtype} -> {output_dtype}) in {compilation_time_ms:.2f}ms"
        )

        return result

    def clear_cache(self) -> None:
        """Clear the kernel cache."""
        self._kernel_cache.clear()
        logger.debug("Kernel cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get kernel cache statistics."""
        return self._kernel_cache.stats

    def mark_compilation_failed(self, func_hash: str, reason: str) -> None:
        """
        Mark a function as having failed compilation.

        This prevents repeated compilation attempts for functions
        that are known to fail.

        Args:
            func_hash: Hash identifying the function
            reason: Description of why compilation failed
        """
        with self._failure_lock:
            self._failure_cache[func_hash] = reason
        logger.debug(f"Marked compilation failed for {func_hash}: {reason}")

    def is_known_failure(self, func_hash: str) -> bool:
        """
        Check if a function is known to fail compilation.

        Args:
            func_hash: Hash identifying the function

        Returns:
            True if this function has previously failed compilation
        """
        with self._failure_lock:
            return func_hash in self._failure_cache

    def get_failure_count(self) -> int:
        """Get the number of recorded compilation failures."""
        with self._failure_lock:
            return len(self._failure_cache)

    def clear_failure_cache(self) -> None:
        """Clear the compilation failure cache."""
        with self._failure_lock:
            self._failure_cache.clear()
        logger.debug("Failure cache cleared")

    def infer_dtype(self, arr: Any) -> np.dtype:
        """
        Infer the dtype from an array or value.

        Args:
            arr: Array or value to infer dtype from (numpy or cupy)

        Returns:
            Inferred numpy dtype (defaults to float64 for non-arrays)
        """
        if hasattr(arr, 'dtype'):
            return np.dtype(arr.dtype)
        return np.dtype(np.float64)

    def ensure_contiguous(self, arr: Any) -> Any:
        """
        Ensure array is C-contiguous, copying if necessary.

        Works with both numpy and cupy arrays.
        CUDA kernels require contiguous memory layout for efficient access.

        Args:
            arr: Input array (numpy or cupy)

        Returns:
            C-contiguous array (same array if already contiguous)

        Raises:
            RuntimeError: If array requires contiguity but CuPy is unavailable
        """
        if hasattr(arr, 'flags') and arr.flags['C_CONTIGUOUS']:
            return arr

        # Handle both numpy and cupy arrays
        if hasattr(arr, '__array_interface__'):
            # NumPy array
            return np.ascontiguousarray(arr)
        elif hasattr(arr, '__cuda_array_interface__'):
            # CuPy array - must use CuPy to maintain GPU memory
            if not self._check_cupy():
                raise RuntimeError(
                    "Cannot make CuPy array contiguous: CuPy is not available"
                )
            import cupy as cp
            return cp.ascontiguousarray(arr)

        # Return as-is for unknown array types (may already be contiguous)
        logger.debug(f"Unknown array type {type(arr)}, returning as-is")
        return arr


# Module-level singleton for convenience
_compiler: Optional[PatternKernelCompiler] = None
_compiler_lock = threading.Lock()


def get_compiler() -> PatternKernelCompiler:
    """Get the global PatternKernelCompiler instance (thread-safe singleton)."""
    global _compiler
    if _compiler is None:
        with _compiler_lock:
            if _compiler is None:
                _compiler = PatternKernelCompiler()
    return _compiler
