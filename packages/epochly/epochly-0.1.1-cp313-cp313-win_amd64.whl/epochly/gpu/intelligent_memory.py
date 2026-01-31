"""
Intelligent GPU Memory Management

Provides automatic memory management for GPU operations with:
- Pre-execution memory estimation
- Automatic chunking for large allocations
- Transparent CPU fallback with warnings
- Zero code changes required from users

This module maintains Epochly's core principle: transparent overlay for performance.
Users write standard CuPy/NumPy code; Epochly handles memory constraints automatically.

Author: Epochly Development Team
"""

import atexit
import logging
import math
import threading
import warnings
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# Track whether atexit cleanup has been registered
_atexit_registered = False

__all__ = [
    'MemoryEstimator',
    'DecisionEngine',
    'AutoChunker',
    'CPUFallback',
    'CuPyInterceptor',
    'IntelligentGPUMemory',
    'enable_intelligent_memory',
    'disable_intelligent_memory',
    'cleanup_gpu_memory',
    'is_intelligent_memory_enabled',
    'AllocationStrategy',
    'AllocationDecision',
    'is_operation_chunkable',
    'CHUNKABLE_OPERATIONS',
    'NON_CHUNKABLE_OPERATIONS',
    'safe_gpu_operation',
    'enable_oom_safety',
    'disable_oom_safety',
]


class AllocationStrategy(Enum):
    """Strategy for handling memory allocation."""
    GPU_DIRECT = "gpu_direct"       # Fits in GPU, execute directly
    GPU_CHUNKED = "gpu_chunked"     # Too large, chunk across GPU passes
    CPU_FALLBACK = "cpu_fallback"   # Cannot chunk, fall back to CPU


# Operations that can be chunked (embarrassingly parallel)
CHUNKABLE_OPERATIONS = frozenset({
    'zeros', 'ones', 'empty', 'full',
    'random.randn', 'random.rand', 'random.random',
    'random.standard_normal', 'random.uniform',
    'arange', 'linspace',
})

# Operations that cannot be trivially chunked
NON_CHUNKABLE_OPERATIONS = frozenset({
    'matmul', 'dot',
    'fft', 'ifft', 'fft2', 'ifft2',
    'svd', 'eig', 'eigvals',
    'solve', 'inv',
    'sort', 'argsort',
})


def is_operation_chunkable(operation: str) -> bool:
    """
    Determine if an operation can be chunked for large allocations.

    Args:
        operation: Operation name (e.g., 'random.randn', 'matmul')

    Returns:
        True if operation can be chunked, False otherwise
    """
    if operation in CHUNKABLE_OPERATIONS:
        return True
    if operation in NON_CHUNKABLE_OPERATIONS:
        return False
    # Default: assume not chunkable for safety
    return False


class MemoryEstimator:
    """
    Estimates memory requirements for array operations.

    Calculates expected memory usage from shape and dtype before
    allocation to enable intelligent decision making.
    """

    # Bytes per element for common dtypes
    DTYPE_SIZES = {
        np.float64: 8,
        np.float32: 4,
        np.float16: 2,
        np.int64: 8,
        np.int32: 4,
        np.int16: 2,
        np.int8: 1,
        np.uint64: 8,
        np.uint32: 4,
        np.uint16: 2,
        np.uint8: 1,
        np.complex128: 16,
        np.complex64: 8,
        np.bool_: 1,
    }

    def __init__(self, headroom_ratio: float = 0.50):
        """
        Initialize memory estimator.

        Args:
            headroom_ratio: Fraction of memory to keep as safety headroom (default 50%)
        """
        self.headroom_ratio = headroom_ratio

    def estimate_allocation(
        self,
        shape: Tuple[int, ...],
        dtype: np.dtype
    ) -> int:
        """
        Estimate memory required for an array allocation.

        Args:
            shape: Array shape tuple
            dtype: NumPy dtype

        Returns:
            Estimated bytes required
        """
        # Get dtype size
        dtype = np.dtype(dtype)
        element_size = self.DTYPE_SIZES.get(dtype.type, dtype.itemsize)

        # Use numpy for safe overflow handling on large shapes
        total_elements = int(np.prod(shape, dtype=np.int64))

        return total_elements * element_size

    def get_safe_allocation_limit(self, available_memory: int) -> int:
        """
        Get safe allocation limit with headroom.

        Args:
            available_memory: Total available GPU memory in bytes

        Returns:
            Safe allocation limit in bytes
        """
        return int(available_memory * (1.0 - self.headroom_ratio))


@dataclass
class AllocationDecision:
    """Result of memory allocation decision."""
    strategy: AllocationStrategy
    chunk_size: int = 0
    chunk_count: int = 1
    message: str = ""


class DecisionEngine:
    """
    Decides how to handle memory allocations based on available resources.

    Implements tiered fallback:
    1. GPU direct - if allocation fits with headroom
    2. GPU chunked - if operation is chunkable
    3. CPU fallback - if operation cannot be chunked
    """

    def __init__(self, headroom_ratio: float = 0.50):
        """
        Initialize decision engine.

        Args:
            headroom_ratio: Fraction of memory to keep as safety headroom
        """
        self.headroom_ratio = headroom_ratio
        self.estimator = MemoryEstimator(headroom_ratio)

    def decide(
        self,
        requested_bytes: int,
        available_bytes: int,
        is_chunkable: bool = True
    ) -> AllocationDecision:
        """
        Decide allocation strategy based on memory requirements.

        Args:
            requested_bytes: Memory required for allocation
            available_bytes: Available GPU memory
            is_chunkable: Whether the operation can be chunked

        Returns:
            AllocationDecision with strategy and parameters
        """
        safe_limit = self.estimator.get_safe_allocation_limit(available_bytes)

        # Case 1: Fits in GPU with headroom
        if requested_bytes <= safe_limit:
            return AllocationDecision(
                strategy=AllocationStrategy.GPU_DIRECT,
                message="Allocation fits in GPU memory"
            )

        # Case 2: Too large but chunkable
        if is_chunkable:
            chunk_size = safe_limit
            chunk_count = math.ceil(requested_bytes / chunk_size)

            return AllocationDecision(
                strategy=AllocationStrategy.GPU_CHUNKED,
                chunk_size=chunk_size,
                chunk_count=chunk_count,
                message=f"Chunking into {chunk_count} GPU passes"
            )

        # Case 3: Too large and not chunkable - CPU fallback
        return AllocationDecision(
            strategy=AllocationStrategy.CPU_FALLBACK,
            message="Operation not chunkable, falling back to CPU"
        )


class AutoChunker:
    """
    Automatically chunks large array operations across multiple GPU passes.

    For embarrassingly parallel operations (random, zeros, etc.), splits
    the work into GPU-sized chunks and reassembles transparently.
    """

    def __init__(self, max_chunk_bytes: int):
        """
        Initialize auto-chunker.

        Args:
            max_chunk_bytes: Maximum bytes per chunk (50% of GPU memory)
        """
        self.max_chunk_bytes = max_chunk_bytes
        self.estimator = MemoryEstimator()

    def compute_chunks(
        self,
        shape: Tuple[int, ...],
        dtype: np.dtype
    ) -> List[Tuple[int, ...]]:
        """
        Compute chunk shapes for a large allocation.

        Chunks along the first axis (rows) to preserve contiguity.

        Args:
            shape: Original array shape
            dtype: Array dtype

        Returns:
            List of chunk shapes
        """
        total_bytes = self.estimator.estimate_allocation(shape, dtype)

        if total_bytes <= self.max_chunk_bytes:
            return [shape]

        # Calculate bytes per row
        row_shape = shape[1:] if len(shape) > 1 else (1,)
        bytes_per_row = self.estimator.estimate_allocation((1,) + row_shape, dtype)

        # Calculate rows per chunk
        rows_per_chunk = max(1, self.max_chunk_bytes // bytes_per_row)
        total_rows = shape[0]

        chunks = []
        remaining_rows = total_rows

        while remaining_rows > 0:
            chunk_rows = min(rows_per_chunk, remaining_rows)
            chunk_shape = (chunk_rows,) + shape[1:]
            chunks.append(chunk_shape)
            remaining_rows -= chunk_rows

        return chunks

    def get_result_dtype(
        self,
        shape: Tuple[int, ...],
        dtype: np.dtype
    ) -> np.dtype:
        """Get the result dtype for a chunked operation."""
        return np.dtype(dtype)

    def reassemble(
        self,
        chunk_results: List[np.ndarray],
        original_shape: Tuple[int, ...],
        dtype: np.dtype
    ) -> np.ndarray:
        """
        Reassemble chunk results into final array.

        Args:
            chunk_results: List of chunk arrays
            original_shape: Expected final shape
            dtype: Expected dtype

        Returns:
            Reassembled array with original shape
        """
        if len(chunk_results) == 1:
            return chunk_results[0]

        # Concatenate along first axis
        result = np.concatenate(chunk_results, axis=0)

        # Verify shape
        if result.shape != original_shape:
            raise ValueError(
                f"Reassembled shape {result.shape} does not match "
                f"expected shape {original_shape}"
            )

        return result


class CPUFallback:
    """
    Handles transparent CPU fallback for operations that cannot fit in GPU.

    Logs warnings to inform users while maintaining transparent operation.
    """

    def __init__(self):
        """Initialize CPU fallback handler."""
        self.logger = logging.getLogger(__name__)

    def execute_on_cpu(
        self,
        operation: str,
        shape: Tuple[int, ...],
        dtype: np.dtype,
        requested_bytes: Optional[int] = None,
        available_bytes: Optional[int] = None,
        **kwargs
    ) -> np.ndarray:
        """
        Execute an operation on CPU with appropriate warnings.

        Args:
            operation: Operation name
            shape: Array shape
            dtype: Array dtype
            requested_bytes: Requested allocation size
            available_bytes: Available GPU memory
            **kwargs: Additional operation arguments

        Returns:
            NumPy array (CPU)
        """
        # Build warning message with memory info
        msg_parts = [f"GPU memory insufficient for {operation} {shape}"]
        if requested_bytes and available_bytes:
            requested_gb = requested_bytes / (1024**3)
            available_gb = available_bytes / (1024**3)
            msg_parts.append(f"- requested {requested_gb:.2f}GB, available {available_gb:.2f}GB")
        msg_parts.append("- falling back to CPU")

        warning_msg = " ".join(msg_parts)

        # Both log AND visible warning (as per requirements)
        self.logger.warning(warning_msg)
        warnings.warn(warning_msg, ResourceWarning, stacklevel=4)

        # Execute on CPU
        dtype = np.dtype(dtype)

        if operation == 'zeros':
            return np.zeros(shape, dtype=dtype)
        elif operation == 'ones':
            return np.ones(shape, dtype=dtype)
        elif operation == 'empty':
            return np.empty(shape, dtype=dtype)
        elif operation == 'full':
            fill_value = kwargs.get('fill_value', 0)
            return np.full(shape, fill_value, dtype=dtype)
        elif operation in ('random.randn', 'random.standard_normal'):
            return np.random.randn(*shape).astype(dtype)
        elif operation in ('random.rand', 'random.random', 'random.uniform'):
            return np.random.rand(*shape).astype(dtype)
        else:
            raise ValueError(f"Unknown operation: {operation}")


class CuPyInterceptor:
    """
    Intercepts CuPy array creation operations for intelligent memory management.

    Provides transparent interception at the allocation level, enabling
    automatic chunking and CPU fallback without user code changes.
    """

    def __init__(self, available_memory: int):
        """
        Initialize CuPy interceptor.

        Args:
            available_memory: Available GPU memory in bytes
        """
        self.available_memory = available_memory
        self.headroom_ratio = 0.50
        self.decision_engine = DecisionEngine(self.headroom_ratio)
        self.estimator = MemoryEstimator(self.headroom_ratio)
        self.cpu_fallback = CPUFallback()

        # Lazy CuPy import
        self._cp = None

    def _get_cupy(self):
        """Lazy import CuPy."""
        if self._cp is None:
            import cupy as cp
            self._cp = cp
        return self._cp

    def _execute_operation(
        self,
        operation: str,
        shape: Tuple[int, ...],
        dtype: np.dtype,
        **kwargs
    ) -> Any:
        """
        Execute an operation with intelligent memory handling.

        Args:
            operation: Operation name
            shape: Array shape
            dtype: Array dtype
            **kwargs: Additional arguments

        Returns:
            CuPy or NumPy array depending on strategy
        """
        dtype = np.dtype(dtype)
        requested_bytes = self.estimator.estimate_allocation(shape, dtype)
        is_chunkable = is_operation_chunkable(operation)

        decision = self.decision_engine.decide(
            requested_bytes,
            self.available_memory,
            is_chunkable
        )

        if decision.strategy == AllocationStrategy.GPU_DIRECT:
            return self._execute_on_gpu(operation, shape, dtype, **kwargs)

        elif decision.strategy == AllocationStrategy.GPU_CHUNKED:
            return self._execute_chunked(operation, shape, dtype, decision, **kwargs)

        else:  # CPU_FALLBACK
            return self.cpu_fallback.execute_on_cpu(
                operation, shape, dtype,
                requested_bytes=requested_bytes,
                available_bytes=self.available_memory,
                **kwargs
            )

    def _execute_on_gpu(
        self,
        operation: str,
        shape: Tuple[int, ...],
        dtype: np.dtype,
        **kwargs
    ) -> Any:
        """Execute operation directly on GPU."""
        cp = self._get_cupy()

        if operation == 'zeros':
            return cp.zeros(shape, dtype=dtype)
        elif operation == 'ones':
            return cp.ones(shape, dtype=dtype)
        elif operation == 'empty':
            return cp.empty(shape, dtype=dtype)
        elif operation == 'full':
            fill_value = kwargs.get('fill_value', 0)
            return cp.full(shape, fill_value, dtype=dtype)
        elif operation in ('random.randn', 'random.standard_normal'):
            return cp.random.randn(*shape).astype(dtype)
        elif operation in ('random.rand', 'random.random', 'random.uniform'):
            return cp.random.rand(*shape).astype(dtype)
        else:
            raise ValueError(f"Unknown GPU operation: {operation}")

    def _execute_chunked(
        self,
        operation: str,
        shape: Tuple[int, ...],
        dtype: np.dtype,
        decision: AllocationDecision,
        **kwargs
    ) -> Any:
        """
        Execute operation in chunks on GPU.

        Note: Returns numpy array (CPU) since the full result is too large for GPU.
        This is intentional - if chunking was needed, the result won't fit on GPU anyway.

        If OOM occurs during chunk allocation, falls back to CPU entirely.
        """
        cp = self._get_cupy()

        chunker = AutoChunker(decision.chunk_size)
        chunk_shapes = chunker.compute_chunks(shape, dtype)

        logger.info(
            f"Chunking {operation} into {len(chunk_shapes)} GPU passes "
            f"(total {decision.chunk_count} chunks estimated)"
        )

        chunk_results = []
        try:
            for i, chunk_shape in enumerate(chunk_shapes):
                logger.debug(f"Processing chunk {i+1}/{len(chunk_shapes)}: shape {chunk_shape}")
                try:
                    chunk = self._execute_on_gpu(operation, chunk_shape, dtype, **kwargs)
                    try:
                        # Move to CPU immediately to free GPU memory for next chunk
                        chunk_results.append(cp.asnumpy(chunk))
                    finally:
                        del chunk
                        cp.get_default_memory_pool().free_all_blocks()
                except Exception as e:
                    # Check if this is an OOM error
                    error_str = str(e).lower()
                    error_type = type(e).__name__
                    is_oom = (
                        'out of memory' in error_str or
                        'outofmemoryerror' in error_type.lower() or
                        'cuda' in error_str and 'memory' in error_str or
                        'allocat' in error_str and 'failed' in error_str
                    )

                    if is_oom:
                        # OOM during chunking - fall back to CPU entirely
                        logger.warning(
                            f"GPU OOM during chunk {i+1}/{len(chunk_shapes)} of {operation} "
                            f"- falling back to CPU for entire operation"
                        )
                        warnings.warn(
                            f"GPU memory exhausted during chunked {operation}, "
                            f"falling back to CPU",
                            ResourceWarning,
                            stacklevel=5
                        )
                        # Clean up partial results
                        chunk_results.clear()
                        cp.get_default_memory_pool().free_all_blocks()

                        # Fall back to CPU for entire operation
                        return self.cpu_fallback.execute_on_cpu(
                            operation, shape, dtype,
                            requested_bytes=self.estimator.estimate_allocation(shape, dtype),
                            available_bytes=self.available_memory,
                            **kwargs
                        )
                    else:
                        # Non-OOM error - re-raise
                        raise

            # Reassemble on CPU - result stays on CPU since it's too large for GPU
            result = chunker.reassemble(chunk_results, shape, dtype)

            # Return numpy array - DO NOT move back to GPU
            # The whole point of chunking is the result is too large for GPU memory
            logger.info(
                f"Chunked operation complete: {shape} array created on CPU "
                f"(too large for GPU memory)"
            )
            return result
        except Exception:
            # Clean up any partial results on error
            chunk_results.clear()
            cp.get_default_memory_pool().free_all_blocks()
            raise

    def zeros(self, shape: Tuple[int, ...], dtype: np.dtype = np.float64) -> Any:
        """Create zeros array with intelligent memory management."""
        return self._execute_operation('zeros', shape, dtype)

    def ones(self, shape: Tuple[int, ...], dtype: np.dtype = np.float64) -> Any:
        """Create ones array with intelligent memory management."""
        return self._execute_operation('ones', shape, dtype)

    def empty(self, shape: Tuple[int, ...], dtype: np.dtype = np.float64) -> Any:
        """Create empty array with intelligent memory management."""
        return self._execute_operation('empty', shape, dtype)

    def random_randn(self, shape: Tuple[int, ...], dtype: np.dtype = np.float64) -> Any:
        """Create random normal array with intelligent memory management."""
        return self._execute_operation('random.randn', shape, dtype)

    def random_rand(self, shape: Tuple[int, ...], dtype: np.dtype = np.float64) -> Any:
        """Create random uniform array with intelligent memory management."""
        return self._execute_operation('random.rand', shape, dtype)

    def matmul(
        self,
        a: np.ndarray,
        b: np.ndarray,
        is_chunkable: bool = False
    ) -> np.ndarray:
        """
        Matrix multiplication with intelligent memory handling.

        Note: matmul is not chunkable by default due to algorithmic constraints.
        Falls back to CPU if GPU memory is insufficient.
        """
        # Estimate result memory
        result_shape = (a.shape[0], b.shape[1])
        dtype = np.result_type(a, b)
        requested_bytes = self.estimator.estimate_allocation(result_shape, dtype)

        # Also need memory for inputs if not already on GPU
        total_bytes = requested_bytes + a.nbytes + b.nbytes

        decision = self.decision_engine.decide(
            total_bytes,
            self.available_memory,
            is_chunkable
        )

        if decision.strategy == AllocationStrategy.GPU_DIRECT:
            cp = self._get_cupy()
            return cp.matmul(cp.asarray(a), cp.asarray(b))

        # CPU fallback for large matmul
        logger.warning(
            f"GPU memory insufficient for matmul {a.shape} x {b.shape} "
            f"- falling back to CPU"
        )
        return np.matmul(a, b)


class IntelligentGPUMemory:
    """
    High-level interface for intelligent GPU memory management.

    Provides drop-in replacements for common CuPy operations with
    automatic memory management.
    """

    def __init__(self):
        """Initialize intelligent GPU memory manager."""
        self._interceptor = None
        self._available_memory = None

    def _get_interceptor(self) -> CuPyInterceptor:
        """Get or create interceptor with current GPU memory info."""
        if self._interceptor is None:
            try:
                import cupy as cp
                # Get available memory
                free_mem, total_mem = cp.cuda.Device().mem_info
                self._available_memory = free_mem
                self._interceptor = CuPyInterceptor(free_mem)
            except Exception as e:
                logger.error(f"Failed to initialize GPU memory interceptor: {e}")
                raise

        return self._interceptor

    def zeros(self, shape: Tuple[int, ...], dtype: np.dtype = np.float64) -> Any:
        """Create zeros array with intelligent memory management."""
        return self._get_interceptor().zeros(shape, dtype)

    def ones(self, shape: Tuple[int, ...], dtype: np.dtype = np.float64) -> Any:
        """Create ones array with intelligent memory management."""
        return self._get_interceptor().ones(shape, dtype)

    def random_randn(self, shape: Tuple[int, ...], dtype: np.dtype = np.float64) -> Any:
        """Create random normal array with intelligent memory management."""
        return self._get_interceptor().random_randn(shape, dtype)


# Module-level storage for original CuPy functions to avoid recursion
_original_cp_zeros = None
_original_cp_ones = None
_original_cp_randn = None
_original_cp_empty = None
_original_cp_rand = None
_original_cp_random = None
_intelligent_memory_enabled = False
_enable_lock = threading.Lock()


def enable_intelligent_memory():
    """
    Enable intelligent GPU memory management globally.

    This patches CuPy's array creation functions to use intelligent
    memory management transparently. Users can continue to use standard
    CuPy code without modifications.

    Patched functions:
    - cp.zeros, cp.ones, cp.empty, cp.full
    - cp.random.randn, cp.random.rand, cp.random.random
    - cp.random.standard_normal, cp.random.uniform

    Thread-safe: Uses lock to prevent concurrent enable/disable races.
    """
    global _original_cp_zeros, _original_cp_ones, _original_cp_randn
    global _original_cp_empty, _original_cp_rand, _original_cp_random
    global _intelligent_memory_enabled

    with _enable_lock:
        if _intelligent_memory_enabled:
            logger.debug("Intelligent memory management already enabled")
            return

        try:
            import cupy as cp

            # Store original functions BEFORE patching
            _original_cp_zeros = cp.zeros
            _original_cp_ones = cp.ones
            _original_cp_randn = cp.random.randn
            _original_cp_empty = cp.empty
            _original_cp_rand = cp.random.rand
            _original_cp_random = getattr(cp.random, 'random', None)

            # Get available memory
            free_mem, total_mem = cp.cuda.Device().mem_info

            # Create interceptor that uses original functions internally
            interceptor = _CuPyInterceptorWithOriginals(
                free_mem,
                _original_cp_zeros,
                _original_cp_ones,
                _original_cp_randn,
                _original_cp_empty,
                _original_cp_rand
            )

            # Create wrapper functions for array creation
            def smart_zeros(shape, dtype=cp.float64, **kwargs):
                if isinstance(shape, int):
                    shape = (shape,)
                return interceptor.zeros(shape, dtype)

            def smart_ones(shape, dtype=cp.float64, **kwargs):
                if isinstance(shape, int):
                    shape = (shape,)
                return interceptor.ones(shape, dtype)

            def smart_empty(shape, dtype=cp.float64, **kwargs):
                if isinstance(shape, int):
                    shape = (shape,)
                return interceptor.empty(shape, dtype)

            # Create wrapper functions for random operations
            def smart_randn(*shape, dtype=cp.float64):
                if len(shape) == 1 and isinstance(shape[0], (tuple, list)):
                    shape = tuple(shape[0])
                return interceptor.random_randn(shape, dtype)

            def smart_rand(*shape, dtype=cp.float64):
                if len(shape) == 1 and isinstance(shape[0], (tuple, list)):
                    shape = tuple(shape[0])
                return interceptor.random_rand(shape, dtype)

            # Patch CuPy array creation
            cp.zeros = smart_zeros
            cp.ones = smart_ones
            cp.empty = smart_empty

            # Patch CuPy random operations (these are the common OOM culprits)
            cp.random.randn = smart_randn
            cp.random.rand = smart_rand

            _intelligent_memory_enabled = True

            # Register atexit handler for cleanup (only once)
            global _atexit_registered
            if not _atexit_registered:
                atexit.register(cleanup_gpu_memory)
                _atexit_registered = True
                logger.debug("Registered GPU memory cleanup for atexit")

            logger.info(
                f"Intelligent GPU memory management enabled "
                f"(available: {free_mem / (1024**3):.2f}GB, "
                f"patched: zeros, ones, empty, random.randn, random.rand)"
            )

            # Also enable OOM safety for operations we can't intercept at creation
            enable_oom_safety()

        except Exception as e:
            logger.warning(f"Failed to enable intelligent memory management: {e}")


def disable_intelligent_memory():
    """
    Disable intelligent GPU memory management and restore original CuPy functions.

    Thread-safe: Uses lock to prevent concurrent enable/disable races.
    """
    global _original_cp_zeros, _original_cp_ones, _original_cp_randn
    global _original_cp_empty, _original_cp_rand, _original_cp_random
    global _intelligent_memory_enabled

    with _enable_lock:
        if not _intelligent_memory_enabled:
            logger.debug("Intelligent memory management already disabled")
            return

        try:
            import cupy as cp

            # Restore original array creation functions
            if _original_cp_zeros is not None:
                cp.zeros = _original_cp_zeros
            if _original_cp_ones is not None:
                cp.ones = _original_cp_ones
            if _original_cp_empty is not None:
                cp.empty = _original_cp_empty

            # Restore original random functions
            if _original_cp_randn is not None:
                cp.random.randn = _original_cp_randn
            if _original_cp_rand is not None:
                cp.random.rand = _original_cp_rand

            # Clear stored references
            _original_cp_zeros = None
            _original_cp_ones = None
            _original_cp_randn = None
            _original_cp_empty = None
            _original_cp_rand = None
            _original_cp_random = None

            _intelligent_memory_enabled = False

            # Also disable OOM safety
            disable_oom_safety()

            logger.info("Intelligent GPU memory management disabled")

        except Exception as e:
            logger.warning(f"Failed to disable intelligent memory management: {e}")


def cleanup_gpu_memory():
    """
    Clean up GPU memory on exit.

    This function is registered with atexit to ensure GPU memory is properly
    released when a script or notebook finishes. It:
    - Disables intelligent memory management
    - Frees all CuPy memory pools
    - Releases GPU memory back to the system

    Can also be called manually to force cleanup at any time.
    """
    global _intelligent_memory_enabled

    try:
        # Disable intelligent memory if enabled
        if _intelligent_memory_enabled:
            disable_intelligent_memory()

        # Free CuPy memory pools
        try:
            import cupy as cp
            # Free all blocks in the default memory pool
            pool = cp.get_default_memory_pool()
            pool.free_all_blocks()

            # Also free pinned memory pool if it exists
            pinned_pool = cp.get_default_pinned_memory_pool()
            pinned_pool.free_all_blocks()

            # Force garbage collection
            import gc
            gc.collect()

            # Synchronize device to ensure all operations complete
            cp.cuda.Device().synchronize()

            logger.debug("GPU memory cleanup completed successfully")
        except ImportError:
            pass  # CuPy not installed
        except Exception as e:
            logger.debug(f"GPU memory cleanup warning: {e}")

    except Exception as e:
        # Don't raise during atexit - just log
        logger.debug(f"GPU cleanup error (non-fatal): {e}")


def is_intelligent_memory_enabled() -> bool:
    """
    Check if intelligent memory management is currently enabled.

    Returns:
        True if enabled, False otherwise
    """
    return _intelligent_memory_enabled


class _CuPyInterceptorWithOriginals(CuPyInterceptor):
    """
    CuPy interceptor that uses stored original functions to avoid recursion.
    """

    def __init__(
        self,
        available_memory: int,
        original_zeros,
        original_ones,
        original_randn,
        original_empty=None,
        original_rand=None
    ):
        super().__init__(available_memory)
        self._original_zeros = original_zeros
        self._original_ones = original_ones
        self._original_randn = original_randn
        self._original_empty = original_empty
        self._original_rand = original_rand

    def _execute_on_gpu(
        self,
        operation: str,
        shape: Tuple[int, ...],
        dtype: np.dtype,
        **kwargs
    ) -> Any:
        """Execute operation directly on GPU using original functions."""
        cp = self._get_cupy()

        if operation == 'zeros':
            return self._original_zeros(shape, dtype=dtype)
        elif operation == 'ones':
            return self._original_ones(shape, dtype=dtype)
        elif operation == 'empty':
            if self._original_empty is not None:
                return self._original_empty(shape, dtype=dtype)
            return cp.empty(shape, dtype=dtype)
        elif operation == 'full':
            fill_value = kwargs.get('fill_value', 0)
            return cp.full(shape, fill_value, dtype=dtype)
        elif operation in ('random.randn', 'random.standard_normal'):
            return self._original_randn(*shape).astype(dtype)
        elif operation in ('random.rand', 'random.random', 'random.uniform'):
            if self._original_rand is not None:
                return self._original_rand(*shape).astype(dtype)
            return cp.random.rand(*shape).astype(dtype)
        else:
            raise ValueError(f"Unknown GPU operation: {operation}")


def safe_gpu_operation(func):
    """
    Decorator that catches GPU OutOfMemoryError and falls back to CPU.

    This is a safety net for any GPU operations that slip through the
    intelligent memory management interception. When OOM occurs:
    1. Frees GPU memory
    2. Issues a warning
    3. Converts inputs to numpy and retries on CPU

    Usage:
        @safe_gpu_operation
        def my_gpu_function(x, y):
            return cp.some_operation(x, y)

    Or wrap inline:
        result = safe_gpu_operation(lambda: cp.random.randn(huge_size))()
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            error_type = type(e).__name__

            # Check if this is a GPU memory error
            is_oom = (
                'out of memory' in error_str or
                'outofmemoryerror' in error_type.lower() or
                'cuda' in error_str and 'memory' in error_str or
                'allocat' in error_str and 'failed' in error_str
            )

            # Check if this is a CUDA library loading error
            # (e.g., libcublas.so.12: cannot open shared object file)
            is_cuda_library_error = (
                'cannot open shared object file' in error_str or
                'libcublas' in error_str or
                'libcudnn' in error_str or
                'libcufft' in error_str or
                'libcusparse' in error_str or
                'libcurand' in error_str or
                'libcusolver' in error_str or
                'libnvrtc' in error_str
            )

            should_fallback = is_oom or is_cuda_library_error

            if not should_fallback:
                raise

            # GPU error detected - fall back to CPU
            error_kind = "GPU memory exhausted" if is_oom else "CUDA library unavailable"
            func_name = func.__name__ if hasattr(func, '__name__') else 'anonymous'

            logger.warning(
                f"{error_kind} in {func_name}: {e} - falling back to CPU"
            )
            warnings.warn(
                f"{error_kind}, falling back to CPU for {func_name}",
                ResourceWarning,
                stacklevel=3
            )

            # Try to free GPU memory
            try:
                import cupy as cp
                cp.get_default_memory_pool().free_all_blocks()
            except Exception:
                pass

            # Convert any cupy arrays in args/kwargs to numpy
            def to_numpy(obj):
                try:
                    import cupy as cp
                    if isinstance(obj, cp.ndarray):
                        return cp.asnumpy(obj)
                except ImportError:
                    pass
                return obj

            numpy_args = tuple(to_numpy(arg) for arg in args)
            numpy_kwargs = {k: to_numpy(v) for k, v in kwargs.items()}

            # Retry with numpy
            # This may fail if the function strictly requires cupy
            # In that case, we tried our best and let the error propagate
            return func(*numpy_args, **numpy_kwargs)

    return wrapper


# Store original cumsum for patching
_original_cp_cumsum = None


def _create_safe_cumsum_wrapper(original_cumsum):
    """Create a safe cumsum wrapper that handles OOM."""

    def safe_cumsum(a, axis=None, dtype=None, out=None):
        """
        Safe cumsum that catches OOM and falls back to CPU.
        """
        try:
            return original_cumsum(a, axis=axis, dtype=dtype, out=out)
        except Exception as e:
            error_str = str(e).lower()
            error_type = type(e).__name__

            is_oom = (
                'out of memory' in error_str or
                'outofmemoryerror' in error_type.lower()
            )

            if not is_oom:
                raise

            logger.warning(f"GPU OutOfMemoryError in cumsum: {e} - falling back to CPU")
            warnings.warn(
                f"GPU memory exhausted during cumsum, falling back to CPU",
                ResourceWarning,
                stacklevel=2
            )

            # Free GPU memory
            try:
                import cupy as cp
                cp.get_default_memory_pool().free_all_blocks()
            except Exception:
                pass

            # Convert to numpy and compute on CPU
            try:
                import cupy as cp
                if isinstance(a, cp.ndarray):
                    a_np = cp.asnumpy(a)
                else:
                    a_np = np.asarray(a)

                result = np.cumsum(a_np, axis=axis, dtype=dtype, out=None)
                return result
            except Exception as cpu_e:
                logger.error(f"CPU fallback also failed: {cpu_e}")
                raise

    return safe_cumsum


def enable_oom_safety():
    """
    Enable global OOM safety handlers for common GPU operations.

    This provides a safety net for operations that slip through the
    intelligent memory management. When OOM occurs, operations fall
    back to CPU automatically with a warning.

    Patched operations:
    - cp.cumsum (commonly used after large random allocations)

    Note: This is automatically called by enable_intelligent_memory().
    """
    global _original_cp_cumsum

    try:
        import cupy as cp

        # Patch cumsum if not already patched
        if _original_cp_cumsum is None:
            _original_cp_cumsum = cp.cumsum
            cp.cumsum = _create_safe_cumsum_wrapper(_original_cp_cumsum)
            logger.debug("OOM safety enabled for cp.cumsum")

    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Failed to enable OOM safety: {e}")


def disable_oom_safety():
    """
    Disable OOM safety handlers and restore original functions.
    """
    global _original_cp_cumsum

    try:
        import cupy as cp

        if _original_cp_cumsum is not None:
            cp.cumsum = _original_cp_cumsum
            _original_cp_cumsum = None
            logger.debug("OOM safety disabled for cp.cumsum")

    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Failed to disable OOM safety: {e}")
