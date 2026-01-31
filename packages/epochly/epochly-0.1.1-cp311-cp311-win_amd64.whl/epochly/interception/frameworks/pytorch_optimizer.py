"""
PyTorch GPU Coordinator for Epochly.

Tier 2 GPU coordination with PyTorch via DLPack protocol.

This module provides SAFE coordination between Epochly's GPU acceleration
and PyTorch's CUDA operations. It does NOT re-parallelize PyTorch ops
(they release GIL internally), but DOES coordinate:
- GPU memory budget awareness
- Zero-copy DLPack tensor sharing with mandatory synchronization
- Mixed workload optimization (NumPy portions)

CRITICAL SAFETY REQUIREMENTS:
- Always call torch.cuda.synchronize() before DLPack transfer
- Ensure tensors are contiguous before export
- Use conservative memory budget (60% of free memory)

Compatible with Python 3.9-3.13, Windows/Linux/Mac.

Author: Epochly Team
License: Apache 2.0
"""

from __future__ import annotations

import sys
import threading
import warnings
from typing import TYPE_CHECKING, Any, Optional, Tuple

if TYPE_CHECKING:
    import cupy
    import torch


class PyTorchGPUCoordinator:
    """
    Tier 2 GPU coordination with PyTorch via DLPack.

    DOES NOT re-parallelize PyTorch ops (they release GIL internally).
    DOES coordinate:
    - GPU memory budget awareness
    - Zero-copy DLPack tensor sharing with mandatory sync
    - Mixed workload optimization (NumPy portions)

    Thread Safety:
        Instance methods are thread-safe for independent tensors.
        Concurrent operations on the same tensor require external sync.

    Example:
        >>> coordinator = PyTorchGPUCoordinator()
        >>> if coordinator.detect_pytorch_active():
        ...     budget = coordinator.coordinate_memory_budget(free_bytes)
        ...     cupy_array = coordinator.safe_tensor_to_cupy(tensor)
    """

    # Conservative memory fraction to leave headroom for PyTorch
    MEMORY_FRACTION: float = 0.6

    def __init__(self) -> None:
        """
        Initialize the PyTorch GPU coordinator.

        Does not import PyTorch or CuPy at initialization time to avoid
        unnecessary dependency loading. Imports are deferred to method calls.
        """
        self._torch: Optional[Any] = None
        self._cupy: Optional[Any] = None
        self._cuda_available: Optional[bool] = None

    def _ensure_torch(self) -> Any:
        """
        Lazily import and return the torch module.

        Returns:
            The torch module.

        Raises:
            ImportError: If PyTorch is not installed.
        """
        if self._torch is None:
            import torch

            self._torch = torch
        return self._torch

    def _ensure_cupy(self) -> Any:
        """
        Lazily import and return the cupy module.

        Returns:
            The cupy module.

        Raises:
            ImportError: If CuPy is not installed.
        """
        if self._cupy is None:
            import cupy

            self._cupy = cupy
        return self._cupy

    def _check_cuda_available(self) -> bool:
        """
        Check if CUDA is available via PyTorch.

        Returns:
            True if CUDA is available, False otherwise.
        """
        if self._cuda_available is None:
            try:
                torch = self._ensure_torch()
                self._cuda_available = torch.cuda.is_available()
            except ImportError:
                self._cuda_available = False
        return self._cuda_available

    def detect_pytorch_active(self) -> bool:
        """
        Check if PyTorch is imported and using CUDA.

        This method checks:
        1. If PyTorch is installed
        2. If CUDA is available via torch.cuda.is_available()

        Returns:
            True if PyTorch is available with CUDA support, False otherwise.

        Example:
            >>> coordinator = PyTorchGPUCoordinator()
            >>> if coordinator.detect_pytorch_active():
            ...     print("PyTorch with CUDA is active")
        """
        return self._check_cuda_available()

    def get_memory_usage(self) -> Tuple[int, int]:
        """
        Return current GPU memory usage from PyTorch.

        Returns:
            Tuple of (allocated_bytes, reserved_bytes):
            - allocated_bytes: Memory actually used by tensors
            - reserved_bytes: Memory reserved by the caching allocator

        When CUDA is not available, returns (0, 0).

        Example:
            >>> coordinator = PyTorchGPUCoordinator()
            >>> allocated, reserved = coordinator.get_memory_usage()
            >>> print(f"Using {allocated / 1e9:.2f} GB of {reserved / 1e9:.2f} GB reserved")
        """
        if not self._check_cuda_available():
            return (0, 0)

        torch = self._ensure_torch()
        allocated = torch.cuda.memory_allocated()
        reserved = torch.cuda.memory_reserved()
        return (int(allocated), int(reserved))

    def coordinate_memory_budget(self, free_bytes: int) -> int:
        """
        Calculate safe CuPy memory budget given available memory.

        Uses a conservative 60% of free memory to leave headroom for
        PyTorch's dynamic allocation needs.

        Args:
            free_bytes: Available free GPU memory in bytes.

        Returns:
            Recommended memory budget for CuPy in bytes.
            Always returns a non-negative integer.

        Example:
            >>> coordinator = PyTorchGPUCoordinator()
            >>> free = 10_000_000_000  # 10 GB free
            >>> budget = coordinator.coordinate_memory_budget(free)
            >>> print(f"Safe to use: {budget / 1e9:.2f} GB")  # 6 GB
        """
        if free_bytes <= 0:
            return 0
        return int(free_bytes * self.MEMORY_FRACTION)

    def safe_tensor_to_cupy(self, tensor: "torch.Tensor") -> "cupy.ndarray":
        """
        Zero-copy transfer from PyTorch tensor to CuPy array.

        CRITICAL SAFETY: This method ALWAYS synchronizes before transfer
        to ensure data integrity. Without sync, async GPU operations
        could result in undefined data.

        Args:
            tensor: A CUDA tensor to convert. Must be on GPU.

        Returns:
            A CuPy array sharing the same GPU memory as the tensor.

        Raises:
            ValueError: If the tensor is not on CUDA device.
            ImportError: If CuPy is not installed.

        Example:
            >>> import torch
            >>> coordinator = PyTorchGPUCoordinator()
            >>> tensor = torch.randn(100, 100, device="cuda")
            >>> cupy_array = coordinator.safe_tensor_to_cupy(tensor)
            >>> assert cupy_array.shape == (100, 100)
        """
        torch = self._ensure_torch()
        cupy = self._ensure_cupy()

        # Validate tensor is on CUDA
        if not tensor.is_cuda:
            raise ValueError(
                "Tensor must be on CUDA device. "
                f"Got tensor on device: {tensor.device}"
            )

        # MANDATORY: Make tensor contiguous if needed
        # Non-contiguous memory cannot be safely shared via DLPack
        if not tensor.is_contiguous():
            tensor = tensor.contiguous()

        # MANDATORY: Synchronize before DLPack transfer
        # This ensures all pending GPU operations are complete
        torch.cuda.synchronize()

        # Use DLPack for zero-copy transfer
        # cupy.from_dlpack is the safe, modern approach
        try:
            # PyTorch 1.10+ supports __dlpack__
            cupy_array = cupy.from_dlpack(tensor)
        except (AttributeError, TypeError):
            # Fallback for older PyTorch versions - may perform copy
            warnings.warn(
                "DLPack not available for PyTorch tensor, falling back to "
                "copy-based transfer. Consider upgrading PyTorch >= 1.10.",
                RuntimeWarning,
                stacklevel=2,
            )
            cupy_array = cupy.asarray(tensor)

        return cupy_array

    def safe_cupy_to_tensor(self, array: "cupy.ndarray") -> "torch.Tensor":
        """
        Zero-copy transfer from CuPy array to PyTorch tensor.

        CRITICAL SAFETY: This method ALWAYS synchronizes the CuPy stream
        before transfer to ensure data integrity. Without sync, async
        GPU operations could result in undefined data.

        Args:
            array: A CuPy array on GPU.

        Returns:
            A PyTorch CUDA tensor sharing the same GPU memory.

        Raises:
            ImportError: If PyTorch is not installed.

        Example:
            >>> import cupy as cp
            >>> coordinator = PyTorchGPUCoordinator()
            >>> array = cp.random.randn(100, 100)
            >>> tensor = coordinator.safe_cupy_to_tensor(array)
            >>> assert tensor.shape == (100, 100)
        """
        torch = self._ensure_torch()
        cupy = self._ensure_cupy()

        # MANDATORY: Make array contiguous if needed
        # Non-contiguous memory cannot be safely shared via DLPack
        if not array.flags.c_contiguous:
            array = cupy.ascontiguousarray(array)

        # MANDATORY: Synchronize CuPy stream before transfer
        # This ensures all pending CuPy operations are complete
        cupy.cuda.Stream.null.synchronize()

        # Use DLPack for zero-copy transfer
        try:
            # CuPy 9.0+ supports __dlpack__
            tensor = torch.from_dlpack(array)
        except (AttributeError, TypeError):
            # Fallback for older CuPy versions - may perform copy
            warnings.warn(
                "DLPack not available for CuPy array, falling back to "
                "copy-based transfer. Consider upgrading CuPy >= 9.0.",
                RuntimeWarning,
                stacklevel=2,
            )
            tensor = torch.as_tensor(array, device="cuda")

        return tensor


# Module-level singleton for convenience (thread-safe)
_coordinator: Optional[PyTorchGPUCoordinator] = None
_coordinator_lock = threading.Lock()


def get_pytorch_coordinator() -> PyTorchGPUCoordinator:
    """
    Get or create the module-level PyTorchGPUCoordinator singleton.

    This function is thread-safe and uses double-checked locking to
    minimize lock contention after initialization.

    Returns:
        The shared PyTorchGPUCoordinator instance.

    Example:
        >>> coordinator = get_pytorch_coordinator()
        >>> if coordinator.detect_pytorch_active():
        ...     # Use coordinator
        ...     pass
    """
    global _coordinator
    if _coordinator is None:
        with _coordinator_lock:
            # Double-check after acquiring lock
            if _coordinator is None:
                _coordinator = PyTorchGPUCoordinator()
    return _coordinator


def is_pytorch_active() -> bool:
    """
    Convenience function to check if PyTorch with CUDA is available.

    Returns:
        True if PyTorch is installed and CUDA is available.

    Example:
        >>> if is_pytorch_active():
        ...     print("PyTorch GPU acceleration available")
    """
    return get_pytorch_coordinator().detect_pytorch_active()
