"""
CUDA Kernel Compiler for Epochly JIT

Compiles detected parallelizable loop patterns into GPU-accelerated operations
using CuPy for reliable cross-platform GPU execution.

Author: Epochly Development Team
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, Any, Tuple, List
import hashlib
import inspect
import re
import numpy as np

# GPU availability check - prefer CuPy for reliability
CUPY_AVAILABLE = False
CUDA_AVAILABLE = False

try:
    import cupy as cp
    CUPY_AVAILABLE = True
    CUDA_AVAILABLE = True
except ImportError:
    cp = None

# Numba CUDA as fallback (currently has issues with CUDA 13.x)
try:
    from numba import cuda as numba_cuda
    NUMBA_CUDA_AVAILABLE = numba_cuda.is_available()
except ImportError:
    numba_cuda = None
    NUMBA_CUDA_AVAILABLE = False

from epochly.jit.cuda_pattern_detector import (
    PatternAnalysis,
    StencilInfo,
    MapInfo,
    ReduceInfo,
    ScanInfo,
    MatMulInfo,
    TransposeInfo,
    GatherInfo,
    ScatterInfo,
    HistogramInfo,
    FilterInfo,
    ConvolutionInfo,
    OuterInfo,
)

# Memory management integration
_memory_manager = None
_memory_manager_init_logged = False
import logging as _logging

def get_memory_manager():
    """Get the GPU memory manager instance (lazy initialization)."""
    global _memory_manager, _memory_manager_init_logged
    if _memory_manager is None:
        try:
            from epochly.gpu import GPUMemoryManager, GPUDetector
            gpu_info = GPUDetector.get_gpu_info()
            if gpu_info.memory_total > 0:
                # Use 80% of GPU memory as limit
                memory_limit = int(gpu_info.memory_total * 0.8)
                _memory_manager = GPUMemoryManager(
                    memory_limit=memory_limit,
                    enable_caching=True
                )
                _logging.getLogger(__name__).debug(
                    f"GPUMemoryManager initialized with {memory_limit / 1e9:.1f}GB limit"
                )
        except Exception as e:
            if not _memory_manager_init_logged:
                _memory_manager_init_logged = True
                _logging.getLogger(__name__).warning(
                    f"GPUMemoryManager initialization failed: {e}. "
                    f"Memory checks will use fallback method."
                )
    return _memory_manager


def _is_array_like(obj) -> bool:
    """Check if object is array-like (numpy or cupy array).

    Uses explicit type checks first for performance, then duck-typing fallback.
    """
    # Check for ndarray types explicitly first
    if isinstance(obj, np.ndarray):
        return True
    if CUPY_AVAILABLE and cp is not None and isinstance(obj, cp.ndarray):
        return True
    # Fallback for duck-typing (custom array-like objects)
    return (
        hasattr(obj, 'ndim') and
        hasattr(obj, 'nbytes') and
        hasattr(obj, 'shape') and
        hasattr(obj, 'dtype')
    )

import sys


def _execute_function_on_gpu(func: Callable, args: tuple, kwargs: dict = None) -> Any:
    """
    Execute a function on GPU by converting numpy arrays to CuPy arrays.

    This is the core dynamic execution mechanism. Instead of parsing expressions
    and generating kernels, we simply:
    1. Convert numpy arrays to CuPy arrays
    2. Call the original function
    3. CuPy intercepts numpy operations and runs them on GPU
    4. Convert results back to numpy

    Args:
        func: The function to execute
        args: Positional arguments (numpy arrays will be converted)
        kwargs: Keyword arguments (numpy arrays will be converted)

    Returns:
        Result with CuPy arrays converted back to numpy
    """
    if not CUPY_AVAILABLE:
        return func(*args, **(kwargs or {}))

    # Convert numpy arrays to CuPy arrays
    gpu_args = []
    for arg in args:
        if isinstance(arg, np.ndarray):
            gpu_args.append(cp.asarray(arg))
        else:
            gpu_args.append(arg)

    gpu_kwargs = {}
    if kwargs:
        for key, val in kwargs.items():
            if isinstance(val, np.ndarray):
                gpu_kwargs[key] = cp.asarray(val)
            else:
                gpu_kwargs[key] = val

    # Execute function - CuPy arrays use GPU operations automatically
    result = func(*gpu_args, **gpu_kwargs)

    # Synchronize GPU
    cp.cuda.Stream.null.synchronize()

    # Convert CuPy arrays back to numpy
    if isinstance(result, cp.ndarray):
        return cp.asnumpy(result)
    elif isinstance(result, tuple):
        return tuple(
            cp.asnumpy(r) if isinstance(r, cp.ndarray) else r
            for r in result
        )
    elif isinstance(result, list):
        return [
            cp.asnumpy(r) if isinstance(r, cp.ndarray) else r
            for r in result
        ]

    return result


# Use typing.Any properly
from typing import Any


@dataclass
class CompiledKernel:
    """Wrapper for a compiled GPU kernel."""

    name: str
    pattern_type: str
    cuda_kernel: Optional[Any] = None
    dimensions: int = 1
    _block_size: Tuple[int, ...] = field(default_factory=lambda: (16, 16))
    _original_func: Optional[Callable] = None
    _stencil_info: Optional[StencilInfo] = None
    _map_info: Optional[MapInfo] = None
    _reduce_info: Optional[ReduceInfo] = None
    _scan_info: Optional[ScanInfo] = None
    _matmul_info: Optional[MatMulInfo] = None
    _transpose_info: Optional[TransposeInfo] = None
    _gather_info: Optional[GatherInfo] = None
    _scatter_info: Optional[ScatterInfo] = None
    _histogram_info: Optional[HistogramInfo] = None
    _filter_info: Optional[FilterInfo] = None
    _convolution_info: Optional[ConvolutionInfo] = None
    _outer_info: Optional[OuterInfo] = None
    _operation_source: Optional[str] = None

    @property
    def is_compiled(self) -> bool:
        """Check if the kernel is successfully compiled."""
        return self.cuda_kernel is not None

    def get_launch_config(self, *grid_dims) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
        """
        Calculate optimal block and grid configuration for launch.

        Args:
            *grid_dims: Dimensions of the problem space (e.g., n, m for 2D)

        Returns:
            Tuple of (blocks_per_grid, threads_per_block)
        """
        if len(grid_dims) == 1:
            # 1D kernel
            n = grid_dims[0]
            threads_per_block = 256
            blocks_per_grid = (n + threads_per_block - 1) // threads_per_block
            return ((blocks_per_grid,), (threads_per_block,))
        elif len(grid_dims) == 2:
            # 2D kernel
            n, m = grid_dims
            threads_x = min(16, n)
            threads_y = min(16, m)
            # Ensure we have at least 8x8 threads
            threads_x = max(8, threads_x)
            threads_y = max(8, threads_y)
            blocks_x = (n + threads_x - 1) // threads_x
            blocks_y = (m + threads_y - 1) // threads_y
            return ((blocks_x, blocks_y), (threads_x, threads_y))
        else:
            raise ValueError(f"Unsupported grid dimensions: {len(grid_dims)}")

    def estimate_memory_usage(self, *grid_dims, dtype=np.float64) -> int:
        """
        Estimate GPU memory usage for the kernel.

        Args:
            *grid_dims: Dimensions of the problem space
            dtype: Data type of arrays

        Returns:
            Estimated memory usage in bytes
        """
        element_size = np.dtype(dtype).itemsize
        total_elements = 1
        for dim in grid_dims:
            total_elements *= dim

        # Estimate based on pattern type
        if self.pattern_type == 'stencil':
            # Stencils typically need input and output arrays
            return 2 * total_elements * element_size
        elif self.pattern_type == 'map':
            # Maps need input and output arrays
            return 2 * total_elements * element_size
        elif self.pattern_type == 'reduce':
            # Reduce needs input array plus temporary reduction array
            return total_elements * element_size + 1024 * element_size
        else:
            return total_elements * element_size

    def _check_gpu_memory(self, args: tuple) -> None:
        """
        Check if GPU has sufficient memory for the operation.

        Uses the GPUMemoryManager for proper memory tracking and cleanup.
        Handles both NumPy and CuPy arrays.

        Args:
            args: Arguments to the kernel (arrays and scalars)

        Raises:
            MemoryError: If GPU memory is insufficient for the operation
        """
        if not CUPY_AVAILABLE:
            return

        # Calculate required memory from input arrays (both numpy and cupy)
        required_bytes = 0
        array_shapes = []
        arr_list = []

        for arg in args:
            if _is_array_like(arg):
                required_bytes += arg.nbytes
                array_shapes.append(arg.shape)
                arr_list.append(arg)

        # Add overhead for GPU copies and temporary arrays (2x for safety)
        required_bytes *= 2

        # Add pattern-specific overhead estimates for intermediate arrays
        if self.pattern_type == 'matmul':
            # matmul(A[m,k], B[k,n]) creates C[m,n] - account for output array
            shapes_2d = [a.shape for a in arr_list if a.ndim == 2]
            if len(shapes_2d) >= 2:
                m, k = shapes_2d[0]
                k2, n = shapes_2d[1]
                # Get dtype from first array (default to float64)
                dtype = arr_list[0].dtype if arr_list else np.float64
                output_size = m * n * np.dtype(dtype).itemsize
                required_bytes += output_size

        elif self.pattern_type == 'outer':
            # outer(a[m], b[n]) creates result[m,n] - account for output array
            shapes_1d = [a for a in arr_list if a.ndim == 1]
            if len(shapes_1d) >= 2:
                m = len(shapes_1d[0])
                n = len(shapes_1d[1])
                dtype = shapes_1d[0].dtype if shapes_1d else np.float64
                output_size = m * n * np.dtype(dtype).itemsize
                required_bytes += output_size

        elif self.pattern_type == 'histogram':
            # histogram creates output bins array
            # Estimate based on typical bin count (256 bins by default)
            required_bytes += 256 * 8  # 256 float64 bins

        elif self.pattern_type == 'convolution':
            # convolution creates output same size as input
            if arr_list:
                required_bytes += arr_list[0].nbytes

        # Try using the GPUMemoryManager first
        memory_manager = get_memory_manager()
        if memory_manager is not None:
            # Use the memory manager's ensure_memory_available method
            if not memory_manager.ensure_memory_available(required_bytes):
                # Memory manager tried cleanup but still not enough
                stats = memory_manager.get_stats()
                raise MemoryError(
                    f"Insufficient GPU memory for {self.pattern_type} kernel. "
                    f"Required: {required_bytes / 1e9:.2f} GB, "
                    f"Available: {stats.free_bytes / 1e9:.2f} GB / {stats.total_bytes / 1e9:.2f} GB total. "
                    f"Array shapes: {array_shapes}. "
                    f"Memory manager attempted cleanup but insufficient memory remains."
                )
            return

        # Fallback: direct GPU memory check if memory manager unavailable
        try:
            device = cp.cuda.Device()
            free_mem = device.mem_info[0]  # Free memory in bytes
            total_mem = device.mem_info[1]  # Total memory in bytes

            # Check if we have enough memory (with 10% safety margin)
            if required_bytes > free_mem * 0.9:
                raise MemoryError(
                    f"Insufficient GPU memory for {self.pattern_type} kernel. "
                    f"Required: {required_bytes / 1e9:.2f} GB, "
                    f"Available: {free_mem / 1e9:.2f} GB / {total_mem / 1e9:.2f} GB total. "
                    f"Array shapes: {array_shapes}"
                )
        except AttributeError:
            # mem_info not available on all CUDA versions
            pass

    def execute(self, *args) -> Any:
        """
        Execute the compiled kernel with the given arguments.

        Args:
            *args: Arguments to pass to the kernel (arrays and scalars)

        Returns:
            Result of the kernel execution (for reduce patterns, returns the scalar)

        Raises:
            RuntimeError: If kernel is not compiled
            MemoryError: If GPU memory is insufficient for the operation
        """
        if not self.is_compiled:
            raise RuntimeError("Kernel is not compiled")

        # Memory check before execution
        if CUPY_AVAILABLE:
            self._check_gpu_memory(args)

        try:
            if self.pattern_type == 'stencil':
                return self._execute_stencil(*args)
            elif self.pattern_type == 'map':
                return self._execute_map(*args)
            elif self.pattern_type == 'reduce':
                # Handle reduce pattern - extract array and n from args
                arr_args = [arg for arg in args if _is_array_like(arg)]
                if not arr_args:
                    raise ValueError("Reduce requires an input array")

                arr = arr_args[0]
                # Use array length as default, allow explicit override only if int
                # and within valid bounds
                n = len(arr)
                for arg in args:
                    if isinstance(arg, int) and not _is_array_like(arg):
                        # Only accept if it's a valid size (positive and <= array length)
                        if 0 < arg <= len(arr):
                            n = arg
                            break
                return self._execute_reduce_impl(arr, n)
            elif self.pattern_type == 'scan':
                return self._execute_scan(*args)
            elif self.pattern_type == 'matmul':
                return self._execute_matmul(*args)
            elif self.pattern_type == 'transpose':
                return self._execute_transpose(*args)
            elif self.pattern_type == 'gather':
                return self._execute_gather(*args)
            elif self.pattern_type == 'scatter':
                return self._execute_scatter(*args)
            elif self.pattern_type == 'histogram':
                return self._execute_histogram(*args)
            elif self.pattern_type == 'filter':
                return self._execute_filter(*args)
            elif self.pattern_type == 'convolution':
                return self._execute_convolution(*args)
            elif self.pattern_type == 'outer':
                return self._execute_outer(*args)
            else:
                raise ValueError(f"Cannot execute pattern type: {self.pattern_type}")

        except cp.cuda.memory.OutOfMemoryError as e:
            # Convert CuPy OOM to Python MemoryError with context
            raise MemoryError(
                f"GPU out of memory during {self.pattern_type} kernel execution: {e}. "
                f"Try reducing array sizes or freeing GPU memory."
            ) from e

    def execute_reduce(self, arr: np.ndarray, n: int) -> float:
        """
        Execute a reduce kernel.

        Args:
            arr: Input array to reduce
            n: Number of elements

        Returns:
            The reduction result
        """
        if not self.is_compiled:
            raise RuntimeError("Kernel is not compiled")

        if self.pattern_type != 'reduce':
            raise ValueError("execute_reduce only works for reduce kernels")

        # Memory check before execution
        if CUPY_AVAILABLE:
            self._check_gpu_memory((arr,))

        try:
            return self._execute_reduce_impl(arr, n)
        except cp.cuda.memory.OutOfMemoryError as e:
            raise MemoryError(
                f"GPU out of memory during reduce kernel execution: {e}"
            ) from e

    def execute_scan(self, arr: np.ndarray, result: np.ndarray, n: int) -> None:
        """
        Execute a scan (prefix sum) kernel.

        Args:
            arr: Input array
            result: Output array
            n: Number of elements

        Raises:
            ValueError: If n is invalid or exceeds array lengths
        """
        if not self.is_compiled:
            raise RuntimeError("Kernel is not compiled")

        if self.pattern_type != 'scan':
            raise ValueError("execute_scan only works for scan kernels")

        # Validate n against input/output lengths
        if not isinstance(n, int) or n <= 0:
            raise ValueError(f"Scan size n must be a positive integer, got: {n}")
        if n > len(arr):
            raise ValueError(
                f"Scan size n ({n}) exceeds input array length ({len(arr)})"
            )
        if n > len(result):
            raise ValueError(
                f"Scan size n ({n}) exceeds output array length ({len(result)})"
            )

        # Memory check before execution
        if CUPY_AVAILABLE:
            self._check_gpu_memory((arr, result))

        try:
            self._execute_scan_impl(arr, result, n)
        except cp.cuda.memory.OutOfMemoryError as e:
            raise MemoryError(
                f"GPU out of memory during scan kernel execution: {e}"
            ) from e

    def _execute_scan(self, *args) -> None:
        """
        Wrapper for scan execution via the generic execute() interface.

        Parses arguments and calls _execute_scan_impl.
        """
        arr_args = [arg for arg in args if _is_array_like(arg)]
        scalar_args = [arg for arg in args if isinstance(arg, (int, float)) and not _is_array_like(arg)]

        if len(arr_args) < 2:
            raise ValueError("Scan requires input and output arrays")

        arr = arr_args[0]
        result = arr_args[1]
        n = scalar_args[0] if scalar_args else len(arr)

        # Validate n against input/output lengths
        if not isinstance(n, int) or n <= 0:
            raise ValueError(f"Scan size n must be a positive integer, got: {n}")
        if n > len(arr):
            raise ValueError(
                f"Scan size n ({n}) exceeds input array length ({len(arr)})"
            )
        if n > len(result):
            raise ValueError(
                f"Scan size n ({n}) exceeds output array length ({len(result)})"
            )

        self._execute_scan_impl(arr, result, n)

    def _execute_stencil(self, *args) -> None:
        """
        Execute a stencil kernel using dynamic GPU execution for correctness.

        ALWAYS uses the original function with CuPy arrays to ensure correct
        computation for any stencil pattern. This guarantees the user's exact
        stencil operation is preserved, regardless of the detected stencil type.

        Falls back to simple averaging stencils ONLY when original function
        is not available (should be rare).

        Args:
            *args: Arguments to pass to the stencil function (arrays and scalars)
        """
        if not CUPY_AVAILABLE:
            raise RuntimeError("CuPy not available for GPU execution")

        # Parse arguments - find input/output arrays and size parameter
        arr_args = [arg for arg in args if _is_array_like(arg)]
        scalar_args = [arg for arg in args if isinstance(arg, (int, float))]

        if len(arr_args) < 2:
            raise ValueError("Stencil requires at least input and output arrays")

        input_arr, output_arr = arr_args[0], arr_args[1]

        # Validate shapes match
        if input_arr.shape != output_arr.shape:
            raise ValueError(
                f"Input and output array shapes must match for stencil. "
                f"Got input: {input_arr.shape}, output: {output_arr.shape}"
            )

        # Validate minimum size for stencil operations (need at least 3 in each dim)
        min_size = 3
        for dim_idx, dim_size in enumerate(input_arr.shape):
            if dim_size < min_size:
                raise ValueError(
                    f"Array dimension {dim_idx} must be at least {min_size} for stencil operations. "
                    f"Got shape: {input_arr.shape}"
                )

        # ALWAYS prefer original function for correctness - this ensures the
        # user's exact stencil operation is preserved
        if self._original_func:
            # Convert arrays for GPU execution
            # - NumPy arrays: convert to CuPy
            # - CuPy arrays: keep as-is (already on GPU)
            # - Scalars: pass through
            gpu_args = []
            for arg in args:
                if isinstance(arg, np.ndarray):
                    gpu_args.append(cp.asarray(arg))
                elif _is_array_like(arg):
                    # Already a GPU array (CuPy), keep as-is
                    gpu_args.append(arg)
                else:
                    gpu_args.append(arg)

            result = self._original_func(*gpu_args)
            cp.cuda.Stream.null.synchronize()

            # Copy results back to NumPy arrays only (CuPy arrays stay on GPU)
            for i, arg in enumerate(args):
                if isinstance(arg, np.ndarray) and isinstance(gpu_args[i], cp.ndarray):
                    arg[:] = cp.asnumpy(gpu_args[i])

            if result is not None and isinstance(result, cp.ndarray):
                return cp.asnumpy(result)
            return result  # Return actual result (including None for in-place operations)

        # No original function available - cannot execute
        raise RuntimeError("Stencil execution requires original function for correctness")

    def _execute_map(self, *args) -> None:
        """
        Execute a map kernel using dynamic GPU execution.

        Instead of pattern-matching on expression strings, this executes the
        ORIGINAL function with CuPy arrays for correct computation of any
        map operation, regardless of complexity.

        Args:
            *args: Arguments to pass to the map function (arrays and scalars)
        """
        if not CUPY_AVAILABLE:
            raise RuntimeError("CuPy not available for GPU execution")

        # If we have the original function, use dynamic execution
        if self._original_func:
            # Convert arrays for GPU execution
            # - NumPy arrays: convert to CuPy
            # - CuPy arrays: keep as-is (already on GPU)
            # - Scalars: pass through
            gpu_args = []
            for arg in args:
                if isinstance(arg, np.ndarray):
                    gpu_args.append(cp.asarray(arg))
                elif _is_array_like(arg):
                    # Already a GPU array (CuPy), keep as-is
                    gpu_args.append(arg)
                else:
                    gpu_args.append(arg)

            # Execute original function with CuPy arrays
            result = self._original_func(*gpu_args)

            # Synchronize GPU
            cp.cuda.Stream.null.synchronize()

            # Copy results back to NumPy arrays only (CuPy arrays stay on GPU)
            for i, arg in enumerate(args):
                if isinstance(arg, np.ndarray) and isinstance(gpu_args[i], cp.ndarray):
                    arg[:] = cp.asnumpy(gpu_args[i])

            # Handle return value if any
            if result is not None and isinstance(result, cp.ndarray):
                return cp.asnumpy(result)
            return

        # Fallback: Use expression-based execution for backward compatibility
        # This path is used when original_func is not available
        self._execute_map_expression_based(*args)

    def _execute_map_expression_based(self, *args) -> None:
        """
        Backward-compatible expression-based map execution.

        This method provides limited pattern-matching for simple map operations
        when the original function is not available. For complex operations,
        the original function should always be used via _execute_map.

        Note: This is a FALLBACK method. Dynamic execution via original_func
        is preferred for correct computation of arbitrary expressions.
        """
        # Extract expression from map_info
        if self._map_info and self._map_info.expr_spec:
            expr_src = self._map_info.expr_spec.src
        else:
            expr_src = None

        # Parse arguments - accept both NumPy and CuPy arrays
        arr_args = [arg for arg in args if _is_array_like(arg)]
        scalar_args = [arg for arg in args if not _is_array_like(arg)]

        if len(arr_args) < 2:
            raise ValueError("Map requires at least input and output arrays")

        result = arr_args[-1]
        inputs = arr_args[:-1]

        # Find n (size) and constants
        n = None
        constants = []
        for s in scalar_args:
            if isinstance(s, int) and n is None:
                n = s
            elif isinstance(s, (int, float)):
                constants.append(s)

        if n is None:
            n = len(result)

        # Transfer inputs to device
        d_inputs = [cp.asarray(inp[:n]) for inp in inputs]

        # Execute based on expression pattern (limited support)
        if len(inputs) == 1:
            d_arr = d_inputs[0]
            if expr_src and ('* c' in expr_src or '* scale' in expr_src) and constants:
                d_result = d_arr * constants[-1]
            elif expr_src and ('+ c' in expr_src or '+ offset' in expr_src) and constants:
                d_result = d_arr + constants[-1]
            elif expr_src and '*' in expr_src:
                d_result = d_arr * d_arr
            else:
                d_result = d_arr
        elif len(inputs) == 2:
            if expr_src and '+' in expr_src:
                d_result = d_inputs[0] + d_inputs[1]
            elif expr_src and '*' in expr_src:
                d_result = d_inputs[0] * d_inputs[1]
            elif expr_src and '-' in expr_src:
                d_result = d_inputs[0] - d_inputs[1]
            elif expr_src and '/' in expr_src:
                d_result = d_inputs[0] / d_inputs[1]
            else:
                d_result = d_inputs[0] * d_inputs[1]
        else:
            d_result = d_inputs[0] * d_inputs[0]

        cp.cuda.Stream.null.synchronize()
        result[:n] = cp.asnumpy(d_result)[:n]

    def _execute_scan_impl(self, arr: np.ndarray, result: np.ndarray, n: int) -> None:
        """Execute a scan (prefix sum) kernel using CuPy."""
        if not CUPY_AVAILABLE:
            # Fallback to NumPy
            if self._scan_info:
                op = self._scan_info.operation
            else:
                op = 'sum'

            if op == 'sum':
                result[:n] = np.cumsum(arr[:n])
            elif op == 'product':
                result[:n] = np.cumprod(arr[:n])
            elif op == 'max':
                result[:n] = np.maximum.accumulate(arr[:n])
            elif op == 'min':
                result[:n] = np.minimum.accumulate(arr[:n])
            else:
                result[:n] = np.cumsum(arr[:n])
            return

        # Use CuPy for GPU-accelerated scan
        d_arr = cp.asarray(arr[:n])

        if self._scan_info:
            op = self._scan_info.operation
        else:
            op = 'sum'

        if op == 'sum':
            d_result = cp.cumsum(d_arr)
        elif op == 'product':
            d_result = cp.cumprod(d_arr)
        elif op == 'max':
            d_result = cp.maximum.accumulate(d_arr)
        elif op == 'min':
            d_result = cp.minimum.accumulate(d_arr)
        else:
            d_result = cp.cumsum(d_arr)

        cp.cuda.Stream.null.synchronize()
        result[:n] = cp.asnumpy(d_result)

    def _execute_reduce_impl(self, arr: np.ndarray, n: int) -> float:
        """
        Execute a reduce kernel using dynamic GPU execution.

        ALWAYS prefers the original function for correctness - this ensures
        the user's exact reduction operation is preserved.

        Falls back to pattern-based transforms ONLY when original function
        is not available.

        Args:
            arr: Input array to reduce
            n: Number of elements

        Returns:
            The reduction result as a float

        Raises:
            ValueError: If n is not a positive integer or exceeds array length
        """
        # Validate n parameter
        if not isinstance(n, int) or n <= 0:
            raise ValueError(f"Reduce size n must be a positive integer, got: {n}")
        if n > len(arr):
            raise ValueError(f"Reduce size n ({n}) exceeds array length ({len(arr)})")

        # ALWAYS prefer original function for correctness
        if self._original_func and CUPY_AVAILABLE:
            # Execute the original function with CuPy arrays via dynamic execution
            result = _execute_function_on_gpu(self._original_func, (arr[:n], n))
            if isinstance(result, (int, float)):
                return float(result)
            elif _is_array_like(result):
                return float(result.flat[0] if hasattr(result, 'flat') else result)

        reduce_op = self._reduce_info.operation if self._reduce_info else 'sum'

        if not CUPY_AVAILABLE:
            # CPU fallback using NumPy
            transformed = self._apply_input_transform_cpu(arr[:n])
            return self._apply_reduction_cpu(transformed, reduce_op)

        # GPU execution using CuPy - pattern-based fallback
        d_arr = cp.asarray(arr[:n])

        # Apply input transformation (for map-reduce patterns)
        d_arr = self._apply_input_transform_gpu(d_arr)

        # Apply reduction operation
        result = self._apply_reduction_gpu(d_arr, reduce_op)

        cp.cuda.Stream.null.synchronize()
        return result

    def _apply_input_transform_cpu(self, arr: np.ndarray) -> np.ndarray:
        """
        Apply input transformation for map-reduce patterns on CPU.

        Args:
            arr: Input array

        Returns:
            Transformed array
        """
        if not self._reduce_info or not self._reduce_info.input_expr:
            return arr

        expr_src = self._reduce_info.input_expr.src

        # Comprehensive transformation mappings
        # Key patterns detected by the pattern detector
        transformations = [
            # Square patterns
            ('arr[i] * arr[i]', lambda a: a * a),
            ('arr[i] ** 2', lambda a: a ** 2),
            ('x * x', lambda a: a * a),
            ('x ** 2', lambda a: a ** 2),
            # Absolute value
            ('abs(', lambda a: np.abs(a)),
            ('np.abs(', lambda a: np.abs(a)),
            # Square root
            ('sqrt(', lambda a: np.sqrt(a)),
            ('np.sqrt(', lambda a: np.sqrt(a)),
            ('** 0.5', lambda a: np.sqrt(a)),
            # Trigonometric
            ('np.sin(', lambda a: np.sin(a)),
            ('np.cos(', lambda a: np.cos(a)),
            ('np.tan(', lambda a: np.tan(a)),
            ('sin(', lambda a: np.sin(a)),
            ('cos(', lambda a: np.cos(a)),
            ('tan(', lambda a: np.tan(a)),
            # Exponential/logarithmic
            ('np.exp(', lambda a: np.exp(a)),
            ('np.log(', lambda a: np.log(a)),
            ('np.log10(', lambda a: np.log10(a)),
            ('np.log2(', lambda a: np.log2(a)),
            ('exp(', lambda a: np.exp(a)),
            ('log(', lambda a: np.log(a)),
            # Cube and higher powers
            ('** 3', lambda a: a ** 3),
            ('** 4', lambda a: a ** 4),
            # Reciprocal
            ('1 /', lambda a: 1 / a),
            ('1.0 /', lambda a: 1.0 / a),
        ]

        # Check each pattern
        for pattern, transform in transformations:
            if pattern in expr_src:
                return transform(arr)

        # Check for multiplication pattern with same array (squaring)
        if '*' in expr_src and expr_src.count('arr[i]') == 2:
            return arr * arr

        return arr

    def _apply_input_transform_gpu(self, d_arr: 'cp.ndarray') -> 'cp.ndarray':
        """
        Apply input transformation for map-reduce patterns on GPU.

        Args:
            d_arr: CuPy array on GPU

        Returns:
            Transformed CuPy array
        """
        if not self._reduce_info or not self._reduce_info.input_expr:
            return d_arr

        expr_src = self._reduce_info.input_expr.src

        # Comprehensive transformation mappings using CuPy
        transformations = [
            # Square patterns
            ('arr[i] * arr[i]', lambda a: a * a),
            ('arr[i] ** 2', lambda a: a ** 2),
            ('x * x', lambda a: a * a),
            ('x ** 2', lambda a: a ** 2),
            # Absolute value
            ('abs(', lambda a: cp.abs(a)),
            ('np.abs(', lambda a: cp.abs(a)),
            # Square root
            ('sqrt(', lambda a: cp.sqrt(a)),
            ('np.sqrt(', lambda a: cp.sqrt(a)),
            ('** 0.5', lambda a: cp.sqrt(a)),
            # Trigonometric
            ('np.sin(', lambda a: cp.sin(a)),
            ('np.cos(', lambda a: cp.cos(a)),
            ('np.tan(', lambda a: cp.tan(a)),
            ('sin(', lambda a: cp.sin(a)),
            ('cos(', lambda a: cp.cos(a)),
            ('tan(', lambda a: cp.tan(a)),
            # Exponential/logarithmic
            ('np.exp(', lambda a: cp.exp(a)),
            ('np.log(', lambda a: cp.log(a)),
            ('np.log10(', lambda a: cp.log10(a)),
            ('np.log2(', lambda a: cp.log2(a)),
            ('exp(', lambda a: cp.exp(a)),
            ('log(', lambda a: cp.log(a)),
            # Cube and higher powers
            ('** 3', lambda a: a ** 3),
            ('** 4', lambda a: a ** 4),
            # Reciprocal
            ('1 /', lambda a: 1 / a),
            ('1.0 /', lambda a: 1.0 / a),
        ]

        # Check each pattern
        for pattern, transform in transformations:
            if pattern in expr_src:
                return transform(d_arr)

        # Check for multiplication pattern with same array (squaring)
        if '*' in expr_src and expr_src.count('arr[i]') == 2:
            return d_arr * d_arr

        return d_arr

    def _apply_reduction_cpu(self, arr: np.ndarray, reduce_op: str) -> float:
        """
        Apply reduction operation on CPU.

        Args:
            arr: Array to reduce
            reduce_op: Reduction operation type

        Returns:
            Reduction result as float
        """
        if reduce_op == 'sum':
            return float(np.sum(arr))
        elif reduce_op == 'max':
            return float(np.max(arr))
        elif reduce_op == 'min':
            return float(np.min(arr))
        elif reduce_op == 'product':
            return float(np.prod(arr))
        elif reduce_op == 'mean':
            return float(np.mean(arr))
        return float(np.sum(arr))

    def _apply_reduction_gpu(self, d_arr: 'cp.ndarray', reduce_op: str) -> float:
        """
        Apply reduction operation on GPU using CuPy.

        Args:
            d_arr: CuPy array on GPU
            reduce_op: Reduction operation type

        Returns:
            Reduction result as float
        """
        if reduce_op == 'sum':
            return float(cp.sum(d_arr))
        elif reduce_op == 'max':
            return float(cp.max(d_arr))
        elif reduce_op == 'min':
            return float(cp.min(d_arr))
        elif reduce_op == 'product':
            return float(cp.prod(d_arr))
        elif reduce_op == 'mean':
            return float(cp.mean(d_arr))
        return float(cp.sum(d_arr))

    def _execute_matmul(self, *args) -> None:
        """
        Execute matrix multiplication C = A @ B using CuPy's cuBLAS backend.

        Signature: matmul(a, b, c) where c is pre-allocated output.
        Handles both NumPy arrays and CuPy arrays (when called from GPU executor).
        """
        if not CUPY_AVAILABLE:
            # Fallback to NumPy
            if len(args) >= 3:
                a, b, c = args[0], args[1], args[2]
                np.matmul(a, b, out=c)
            return

        # Parse arguments - accept both NumPy and CuPy arrays
        arr_args = [arg for arg in args if _is_array_like(arg)]
        if len(arr_args) < 3:
            # Not enough arrays - call original if available
            if self._original_func:
                return self._original_func(*args)
            raise ValueError("matmul requires at least 3 arrays (a, b, c)")

        a, b, c = arr_args[0], arr_args[1], arr_args[2]

        # Check if inputs are already CuPy arrays (use explicit isinstance check)
        a_is_cupy = CUPY_AVAILABLE and cp is not None and isinstance(a, cp.ndarray)
        b_is_cupy = CUPY_AVAILABLE and cp is not None and isinstance(b, cp.ndarray)
        c_is_cupy = CUPY_AVAILABLE and cp is not None and isinstance(c, cp.ndarray)

        # Transfer to GPU if needed (cp.asarray is no-op for CuPy arrays)
        d_a = cp.asarray(a)
        d_b = cp.asarray(b)

        # Execute matmul on GPU using cuBLAS
        d_c = cp.matmul(d_a, d_b)

        # Synchronize
        cp.cuda.Stream.null.synchronize()

        # Copy back to output array
        if c_is_cupy:
            # Output is already on GPU - copy in-place
            c[:] = d_c
        else:
            # Output is NumPy - transfer back to CPU
            c[:] = cp.asnumpy(d_c)

    def _execute_transpose(self, *args) -> None:
        """
        Execute matrix transpose B = A.T using CuPy.

        Signature: transpose(a, b) where b is pre-allocated output.
        Handles both NumPy arrays and CuPy arrays (when called from GPU executor).
        """
        if not CUPY_AVAILABLE:
            # Fallback to NumPy
            if len(args) >= 2:
                a, b = args[0], args[1]
                b[:] = a.T
            return

        # Parse arguments - accept both NumPy and CuPy arrays
        arr_args = [arg for arg in args if _is_array_like(arg)]
        if len(arr_args) < 2:
            if self._original_func:
                return self._original_func(*args)
            raise ValueError("transpose requires at least 2 arrays (input, output)")

        a, b = arr_args[0], arr_args[1]

        # Check if output is already a CuPy array (use explicit isinstance check)
        b_is_cupy = CUPY_AVAILABLE and cp is not None and isinstance(b, cp.ndarray)

        # Transfer to GPU if needed
        d_a = cp.asarray(a)

        # Execute transpose on GPU
        d_b = cp.transpose(d_a)

        # Synchronize
        cp.cuda.Stream.null.synchronize()

        # Copy back to output array
        if b_is_cupy:
            b[:] = d_b
        else:
            b[:] = cp.asnumpy(d_b)

    def _execute_gather(self, *args) -> Any:
        """
        Execute a gather (indexed read) pattern using dynamic GPU execution.

        Gather operations read from indexed locations: result[i] = data[indices[i]]

        This uses the original function with CuPy arrays to ensure correct
        computation for any gather pattern, regardless of complexity.
        """
        if not CUPY_AVAILABLE:
            if self._original_func:
                return self._original_func(*args)
            raise RuntimeError("CuPy not available and no original function for gather")

        if self._original_func:
            return _execute_function_on_gpu(self._original_func, args)

        # Fallback: try to execute using gather_info
        if not self._gather_info:
            raise RuntimeError("No gather_info or original function available")

        # Parse arguments to find data array and indices - accept both NumPy and CuPy arrays
        arr_args = [arg for arg in args if _is_array_like(arg)]
        if len(arr_args) < 2:
            raise ValueError("Gather requires at least data array and indices")

        # Transfer to GPU and execute gather
        d_data = cp.asarray(arr_args[0])
        d_indices = cp.asarray(arr_args[1])

        # Execute gather using fancy indexing
        d_result = d_data[d_indices]

        cp.cuda.Stream.null.synchronize()

        # Copy result back if we have output array
        if len(arr_args) >= 3:
            arr_args[2][:] = cp.asnumpy(d_result)
            return None
        return cp.asnumpy(d_result)

    def _execute_scatter(self, *args) -> Any:
        """
        Execute a scatter (indexed write) pattern using dynamic GPU execution.

        Scatter operations write to indexed locations: result[indices[i]] = data[i]

        This uses the original function with CuPy arrays to ensure correct
        computation for any scatter pattern, regardless of complexity.
        """
        if not CUPY_AVAILABLE:
            if self._original_func:
                return self._original_func(*args)
            raise RuntimeError("CuPy not available and no original function for scatter")

        if self._original_func:
            return _execute_function_on_gpu(self._original_func, args)

        # Fallback: try to execute using scatter_info
        if not self._scatter_info:
            raise RuntimeError("No scatter_info or original function available")

        # Parse arguments to find data array, indices, and output - accept both NumPy and CuPy arrays
        arr_args = [arg for arg in args if _is_array_like(arg)]
        if len(arr_args) < 3:
            raise ValueError("Scatter requires data, indices, and output arrays")

        d_data = cp.asarray(arr_args[0])
        d_indices = cp.asarray(arr_args[1])
        d_output = cp.asarray(arr_args[2])

        # Execute scatter using fancy indexing
        d_output[d_indices] = d_data

        cp.cuda.Stream.null.synchronize()

        # Copy result back
        arr_args[2][:] = cp.asnumpy(d_output)

    def _execute_histogram(self, *args) -> Any:
        """
        Execute a histogram (binning) pattern using dynamic GPU execution.

        Histogram operations count occurrences: bins[data[i]] += 1

        This uses CuPy's histogram function for GPU-accelerated binning.
        """
        if not CUPY_AVAILABLE:
            if self._original_func:
                return self._original_func(*args)
            raise RuntimeError("CuPy not available and no original function for histogram")

        if self._original_func:
            return _execute_function_on_gpu(self._original_func, args)

        # Fallback: try to execute using histogram_info
        if not self._histogram_info:
            raise RuntimeError("No histogram_info or original function available")

        # Parse arguments to find data array and bins - accept both NumPy and CuPy arrays
        arr_args = [arg for arg in args if _is_array_like(arg)]
        scalar_args = [arg for arg in args if isinstance(arg, (int, float)) and not _is_array_like(arg)]

        if len(arr_args) < 1:
            raise ValueError("Histogram requires at least data array")

        d_data = cp.asarray(arr_args[0])

        # Determine number of bins
        n_bins = scalar_args[0] if scalar_args else self._histogram_info.n_bins

        # Execute histogram using CuPy
        hist, bin_edges = cp.histogram(d_data, bins=n_bins)

        cp.cuda.Stream.null.synchronize()

        # Copy result back if we have output array
        if len(arr_args) >= 2:
            arr_args[1][:len(hist)] = cp.asnumpy(hist)
            return None
        return cp.asnumpy(hist)

    def _execute_filter(self, *args) -> Any:
        """
        Execute a filter (conditional selection) pattern using dynamic GPU execution.

        Filter operations select elements matching a condition:
        result = data[condition(data)]

        This uses the original function with CuPy arrays to ensure correct
        computation for any filter condition.
        """
        if not CUPY_AVAILABLE:
            if self._original_func:
                return self._original_func(*args)
            raise RuntimeError("CuPy not available and no original function for filter")

        # Always prefer original function for correct semantics
        if self._original_func:
            return _execute_function_on_gpu(self._original_func, args)

        # Fallback: try to execute using filter_info
        if not self._filter_info or not self._filter_info.condition_expr:
            raise RuntimeError("No filter condition available and no original function")

        # Parse arguments - accept both NumPy and CuPy arrays
        arr_args = [arg for arg in args if _is_array_like(arg)]
        if not arr_args:
            raise ValueError("Filter requires at least data array")

        d_data = cp.asarray(arr_args[0])
        condition_src = self._filter_info.condition_expr.src

        # Use regex for robust condition parsing - only handle simple numeric comparisons
        # Match patterns like "x > 5", "arr[i] <= 3.14", "value != -10", "x > 1e-5"
        match = re.match(
            r'^\s*\w+(?:\[\w+\])?\s*([><=!]+)\s*([-+]?\d*\.?\d*(?:[eE][-+]?\d+)?)\s*$',
            condition_src
        )

        if not match:
            raise RuntimeError(
                f"Cannot parse filter condition '{condition_src}' without original function. "
                f"Only simple numeric comparisons (e.g., 'x > 5') are supported in fallback mode."
            )

        op, value_str = match.groups()
        threshold = float(value_str)

        # Map operators to CuPy functions
        ops = {
            '>': lambda arr, v: arr > v,
            '<': lambda arr, v: arr < v,
            '>=': lambda arr, v: arr >= v,
            '<=': lambda arr, v: arr <= v,
            '==': lambda arr, v: arr == v,
            '!=': lambda arr, v: arr != v,
        }

        if op not in ops:
            raise RuntimeError(f"Unsupported comparison operator: {op}")

        mask = ops[op](d_data, threshold)
        d_result = d_data[mask]

        cp.cuda.Stream.null.synchronize()

        return cp.asnumpy(d_result)

    def _execute_convolution(self, *args) -> Any:
        """
        Execute a convolution (weighted stencil) pattern using dynamic GPU execution.

        Convolution applies weighted kernels: result[i] = sum(data[i+j] * kernel[j])

        This uses the original function with CuPy arrays for correct computation,
        or falls back to CuPy's signal processing functions.
        """
        if not CUPY_AVAILABLE:
            if self._original_func:
                return self._original_func(*args)
            raise RuntimeError("CuPy not available and no original function for convolution")

        if self._original_func:
            return _execute_function_on_gpu(self._original_func, args)

        # Fallback: try to execute using convolution_info and CuPy convolve
        if not self._convolution_info:
            raise RuntimeError("No convolution_info or original function available")

        # Parse arguments to find data and kernel - accept both NumPy and CuPy arrays
        arr_args = [arg for arg in args if _is_array_like(arg)]
        if len(arr_args) < 2:
            raise ValueError("Convolution requires data and kernel arrays")

        d_data = cp.asarray(arr_args[0])
        d_kernel = cp.asarray(arr_args[1])

        # Use CuPy's convolve function for ND arrays
        try:
            from cupyx.scipy.ndimage import convolve
            d_result = convolve(d_data, d_kernel, mode='constant')
        except ImportError:
            # Fallback only works for 1D arrays
            if d_data.ndim > 1:
                raise RuntimeError(
                    f"ND convolution (ndim={d_data.ndim}) requires cupyx.scipy.ndimage. "
                    f"Install with: pip install cupy-cuda12x[scipy] or similar. "
                    f"Only 1D convolution is supported without scipy extension."
                )
            # 1D convolution fallback
            d_result = cp.convolve(d_data.ravel(), d_kernel.ravel(), mode='same')

        cp.cuda.Stream.null.synchronize()

        # Copy result back if we have output array
        if len(arr_args) >= 3:
            arr_args[2][:] = cp.asnumpy(d_result)
            return None
        return cp.asnumpy(d_result)

    def _execute_outer(self, *args) -> Any:
        """
        Execute an outer product pattern using dynamic GPU execution.

        Outer product: result[i,j] = a[i] * b[j] (or other binary operation)

        This uses CuPy's outer function for GPU-accelerated outer products.
        """
        if not CUPY_AVAILABLE:
            if self._original_func:
                return self._original_func(*args)
            raise RuntimeError("CuPy not available and no original function for outer")

        if self._original_func:
            return _execute_function_on_gpu(self._original_func, args)

        # Fallback: try to execute using outer_info
        if not self._outer_info:
            raise RuntimeError("No outer_info or original function available")

        # Parse arguments to find input vectors - accept both NumPy and CuPy arrays
        arr_args = [arg for arg in args if _is_array_like(arg)]
        if len(arr_args) < 2:
            raise ValueError("Outer product requires at least two input vectors")

        d_a = cp.asarray(arr_args[0]).ravel()
        d_b = cp.asarray(arr_args[1]).ravel()

        # Determine operation from outer_info
        op = self._outer_info.operation if self._outer_info else 'multiply'

        if op == 'multiply':
            d_result = cp.outer(d_a, d_b)
        elif op == 'add':
            d_result = cp.add.outer(d_a, d_b)
        elif op == 'subtract':
            d_result = cp.subtract.outer(d_a, d_b)
        elif op == 'divide':
            d_result = cp.divide.outer(d_a, d_b)
        else:
            d_result = cp.outer(d_a, d_b)

        cp.cuda.Stream.null.synchronize()

        # Copy result back if we have output array
        if len(arr_args) >= 3:
            arr_args[2][:] = cp.asnumpy(d_result)
            return None
        return cp.asnumpy(d_result)


class CUDAKernelCompiler:
    """
    Compiles detected loop patterns into GPU-accelerated kernels.

    Uses CuPy for reliable GPU execution across CUDA versions.

    Supports:
    - Stencil patterns (5-point, 9-point, custom)
    - Map patterns (element-wise operations)
    - Reduce patterns (sum, max, min, product)
    - Scan patterns (prefix sum, product, max, min)
    - MatMul patterns (matrix multiplication)
    - Transpose patterns (matrix transpose)
    - Gather patterns (indexed read)
    - Scatter patterns (indexed write)
    - Histogram patterns (binning)
    - Filter patterns (conditional selection)
    - Convolution patterns (weighted stencil)
    - Outer Product patterns (vector outer product)
    """

    def __init__(self):
        """Initialize the kernel compiler."""
        self._cache: Dict[str, CompiledKernel] = {}

    def compile(self, func: Callable, analysis: PatternAnalysis) -> CompiledKernel:
        """
        Compile a function into a GPU kernel based on pattern analysis.

        Args:
            func: The Python function to compile
            analysis: Pattern analysis result from CUDAPatternDetector

        Returns:
            CompiledKernel wrapper for the compiled kernel

        Raises:
            ValueError: If function is not parallelizable or pattern is unknown
        """
        # Check if function is parallelizable
        if not analysis.parallelizable:
            if analysis.has_loop_carried_dependency:
                raise ValueError(
                    f"Function is not parallelizable: has loop-carried dependency. "
                    f"{analysis.rejection_reason}"
                )
            raise ValueError(
                f"Function is not parallelizable: {analysis.rejection_reason}"
            )

        # Check for unknown pattern
        if analysis.pattern_type == 'unknown':
            raise ValueError(
                f"Unknown pattern type cannot be compiled. "
                f"Rejection reason: {analysis.rejection_reason}"
            )

        # Generate cache key
        cache_key = self._generate_cache_key(func, analysis)

        # Check cache
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Compile based on pattern type
        if analysis.pattern_type == 'stencil':
            kernel = self._compile_stencil(func, analysis)
        elif analysis.pattern_type == 'map':
            kernel = self._compile_map(func, analysis)
        elif analysis.pattern_type == 'reduce':
            kernel = self._compile_reduce(func, analysis)
        elif analysis.pattern_type == 'scan':
            kernel = self._compile_scan(func, analysis)
        elif analysis.pattern_type == 'matmul':
            kernel = self._compile_matmul(func, analysis)
        elif analysis.pattern_type == 'transpose':
            kernel = self._compile_transpose(func, analysis)
        elif analysis.pattern_type == 'gather':
            kernel = self._compile_gather(func, analysis)
        elif analysis.pattern_type == 'scatter':
            kernel = self._compile_scatter(func, analysis)
        elif analysis.pattern_type == 'histogram':
            kernel = self._compile_histogram(func, analysis)
        elif analysis.pattern_type == 'filter':
            kernel = self._compile_filter(func, analysis)
        elif analysis.pattern_type == 'convolution':
            kernel = self._compile_convolution(func, analysis)
        elif analysis.pattern_type == 'outer':
            kernel = self._compile_outer(func, analysis)
        else:
            raise ValueError(f"Unknown pattern type: {analysis.pattern_type}")

        # Cache and return
        self._cache[cache_key] = kernel
        return kernel

    def clear_cache(self) -> None:
        """Clear the compiled kernel cache."""
        self._cache.clear()

    def _generate_cache_key(self, func: Callable, analysis: PatternAnalysis) -> str:
        """Generate a unique cache key for a function and analysis."""
        source = inspect.getsource(func)
        key_data = f"{func.__name__}:{analysis.pattern_type}:{source}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _compile_stencil(self, func: Callable, analysis: PatternAnalysis) -> CompiledKernel:
        """Compile a stencil pattern to GPU kernel."""
        stencil_info = analysis.stencil_info

        # Generate kernel function (CuPy-based execution)
        kernel_func = self._generate_stencil_kernel(stencil_info)

        return CompiledKernel(
            name=func.__name__,
            pattern_type='stencil',
            cuda_kernel=kernel_func,
            dimensions=analysis.dimensions,
            _original_func=func,
            _stencil_info=stencil_info,
        )

    def _compile_map(self, func: Callable, analysis: PatternAnalysis) -> CompiledKernel:
        """Compile a map pattern to GPU kernel."""
        map_info = analysis.map_info

        # Generate kernel function
        kernel_func = self._generate_map_kernel(map_info, func)

        return CompiledKernel(
            name=func.__name__,
            pattern_type='map',
            cuda_kernel=kernel_func,
            dimensions=analysis.dimensions,
            _original_func=func,
            _map_info=map_info,
            _operation_source=inspect.getsource(func),
        )

    def _compile_reduce(self, func: Callable, analysis: PatternAnalysis) -> CompiledKernel:
        """Compile a reduce pattern to GPU kernel."""
        reduce_info = analysis.reduce_info

        # Generate kernel function
        kernel_func = self._generate_reduce_kernel(reduce_info)

        return CompiledKernel(
            name=func.__name__,
            pattern_type='reduce',
            cuda_kernel=kernel_func,
            dimensions=1,
            _original_func=func,
            _reduce_info=reduce_info,
        )

    def _compile_scan(self, func: Callable, analysis: PatternAnalysis) -> CompiledKernel:
        """Compile a scan (prefix sum) pattern to GPU kernel."""
        scan_info = analysis.scan_info

        # Generate kernel function
        kernel_func = self._generate_scan_kernel(scan_info)

        return CompiledKernel(
            name=func.__name__,
            pattern_type='scan',
            cuda_kernel=kernel_func,
            dimensions=1,
            _original_func=func,
            _scan_info=scan_info,
        )

    def _compile_matmul(self, func: Callable, analysis: PatternAnalysis) -> CompiledKernel:
        """Compile a matrix multiplication pattern to GPU kernel."""
        return CompiledKernel(
            name=func.__name__,
            pattern_type='matmul',
            cuda_kernel=lambda: None,
            dimensions=2,
            _original_func=func,
            _matmul_info=analysis.matmul_info,
        )

    def _compile_transpose(self, func: Callable, analysis: PatternAnalysis) -> CompiledKernel:
        """Compile a transpose pattern to GPU kernel."""
        return CompiledKernel(
            name=func.__name__,
            pattern_type='transpose',
            cuda_kernel=lambda: None,
            dimensions=2,
            _original_func=func,
            _transpose_info=analysis.transpose_info,
        )

    def _compile_gather(self, func: Callable, analysis: PatternAnalysis) -> CompiledKernel:
        """Compile a gather pattern to GPU kernel."""
        return CompiledKernel(
            name=func.__name__,
            pattern_type='gather',
            cuda_kernel=lambda: None,
            dimensions=1,
            _original_func=func,
            _gather_info=analysis.gather_info,
        )

    def _compile_scatter(self, func: Callable, analysis: PatternAnalysis) -> CompiledKernel:
        """Compile a scatter pattern to GPU kernel."""
        return CompiledKernel(
            name=func.__name__,
            pattern_type='scatter',
            cuda_kernel=lambda: None,
            dimensions=1,
            _original_func=func,
            _scatter_info=analysis.scatter_info,
        )

    def _compile_histogram(self, func: Callable, analysis: PatternAnalysis) -> CompiledKernel:
        """Compile a histogram pattern to GPU kernel."""
        return CompiledKernel(
            name=func.__name__,
            pattern_type='histogram',
            cuda_kernel=lambda: None,
            dimensions=1,
            _original_func=func,
            _histogram_info=analysis.histogram_info,
        )

    def _compile_filter(self, func: Callable, analysis: PatternAnalysis) -> CompiledKernel:
        """Compile a filter pattern to GPU kernel."""
        return CompiledKernel(
            name=func.__name__,
            pattern_type='filter',
            cuda_kernel=lambda: None,
            dimensions=1,
            _original_func=func,
            _filter_info=analysis.filter_info,
        )

    def _compile_convolution(self, func: Callable, analysis: PatternAnalysis) -> CompiledKernel:
        """Compile a convolution pattern to GPU kernel."""
        return CompiledKernel(
            name=func.__name__,
            pattern_type='convolution',
            cuda_kernel=lambda: None,
            dimensions=analysis.convolution_info.dimensions if analysis.convolution_info else 1,
            _original_func=func,
            _convolution_info=analysis.convolution_info,
        )

    def _compile_outer(self, func: Callable, analysis: PatternAnalysis) -> CompiledKernel:
        """Compile an outer product pattern to GPU kernel."""
        return CompiledKernel(
            name=func.__name__,
            pattern_type='outer',
            cuda_kernel=lambda: None,
            dimensions=2,
            _original_func=func,
            _outer_info=analysis.outer_info,
        )

    def _generate_stencil_kernel(self, stencil_info: StencilInfo) -> Callable:
        """
        Generate a GPU kernel function for a stencil pattern.

        Args:
            stencil_info: Information about the stencil pattern

        Returns:
            Kernel function marker (actual execution uses CuPy slicing)
        """
        if not CUPY_AVAILABLE:
            return None

        # Return a marker function - actual execution happens in CompiledKernel
        def stencil_kernel_marker():
            """Marker for stencil kernel - execution uses CuPy array operations."""
            pass

        stencil_kernel_marker.stencil_type = stencil_info.stencil_type
        stencil_kernel_marker.dimensions = stencil_info.dimensions
        return stencil_kernel_marker

    def _generate_map_kernel(self, map_info: MapInfo, original_func: Callable) -> Callable:
        """
        Generate a GPU kernel function for a map pattern.

        Args:
            map_info: Information about the map pattern
            original_func: The original Python function

        Returns:
            Kernel function marker
        """
        if not CUPY_AVAILABLE:
            return None

        # Return a marker function
        def map_kernel_marker():
            """Marker for map kernel - execution uses CuPy array operations."""
            pass

        map_kernel_marker.dimensions = map_info.dimensions
        return map_kernel_marker

    def _generate_reduce_kernel(self, reduce_info: ReduceInfo) -> Callable:
        """
        Generate a GPU kernel function for a reduce pattern.

        Args:
            reduce_info: Information about the reduce pattern

        Returns:
            Kernel function marker
        """
        if not CUPY_AVAILABLE:
            return None

        # Return a marker function
        def reduce_kernel_marker():
            """Marker for reduce kernel - execution uses CuPy reduction functions."""
            pass

        reduce_kernel_marker.operation = reduce_info.operation
        return reduce_kernel_marker

    def _generate_scan_kernel(self, scan_info: ScanInfo) -> Callable:
        """
        Generate a GPU kernel function for a scan pattern.

        Args:
            scan_info: Information about the scan pattern

        Returns:
            Kernel function marker
        """
        if not CUPY_AVAILABLE:
            return None

        # Return a marker function
        def scan_kernel_marker():
            """Marker for scan kernel - execution uses CuPy scan functions."""
            pass

        scan_kernel_marker.operation = scan_info.operation
        return scan_kernel_marker
