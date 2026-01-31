"""
GPU Backend Registry for Multi-Vendor Support

Provides abstraction layer for multiple GPU backends (CUDA, ROCm, oneAPI)
enabling Epochly to work across different GPU vendors.

Key Features:
- Backend enumeration (CUDA, ROCm, oneAPI, CPU fallback)
- Backend detection and capability reporting
- Unified interface across vendors
- Graceful fallback to CPU when GPU unavailable

Author: Epochly Development Team
Date: November 14, 2025
Spec: perf_fixes2.md Task 4
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging
import threading

logger = logging.getLogger(__name__)


class GPUBackendKind(Enum):
    """GPU backend types supported by Epochly"""
    CUDA = "cuda"      # NVIDIA via CuPy
    ROCm = "rocm"      # AMD via ROCm/HIP
    oneAPI = "oneapi"  # Intel via oneAPI
    CPU = "cpu"        # NumPy fallback (no GPU)


@dataclass
class GPUBackendInfo:
    """Information about a detected GPU backend"""
    kind: GPUBackendKind
    version: str
    device_count: int
    memory_gb: float
    compute_capability: Optional[str] = None


class GPUBackend:
    """
    Abstract interface for GPU backends.

    Each backend (CUDA, ROCm, oneAPI) implements this interface
    to provide unified GPU operations across vendors.
    """

    def __init__(self, info: GPUBackendInfo):
        self.info = info
        self.logger = logging.getLogger(f"{__name__}.{info.kind.value}")

    def is_available(self) -> bool:
        """Check if backend is available"""
        raise NotImplementedError

    def to_gpu(self, array) -> Any:
        """
        Transfer array to GPU.

        Args:
            array: NumPy array or array-like to transfer

        Returns:
            GPU array (backend-specific type)

        Raises:
            RuntimeError: If backend unavailable or transfer fails
            MemoryError: If GPU out of memory
        """
        raise NotImplementedError

    def to_cpu(self, array) -> Any:
        """
        Transfer array to CPU.

        Args:
            array: GPU array to transfer

        Returns:
            NumPy array

        Raises:
            RuntimeError: If backend unavailable or transfer fails
        """
        raise NotImplementedError

    def get_memory_info(self) -> Dict[str, float]:
        """
        Get GPU memory information (MB).

        Returns:
            Dictionary with memory statistics:
                - device_free_mb: Free GPU RAM
                - device_total_mb: Total GPU RAM
                - device_used_mb: Used GPU RAM
                - pool_cached_mb: Memory pool cache (if applicable)

        Raises:
            RuntimeError: If backend unavailable
        """
        raise NotImplementedError


class CUDABackend(GPUBackend):
    """NVIDIA CUDA backend via CuPy"""

    def __init__(self, info: GPUBackendInfo):
        super().__init__(info)
        self._cupy = None
        self._init_lock = threading.Lock()  # Thread-safe lazy import

    def is_available(self) -> bool:
        """
        Check if CuPy/CUDA available with actual GPU devices.

        Returns:
            True only if CuPy imports AND is NVIDIA build AND at least one CUDA device exists
        """
        with self._init_lock:
            if self._cupy is not None:
                # Already loaded - reject HIP builds, verify devices exist
                is_hip = getattr(self._cupy.cuda.runtime, 'is_hip', False) or hasattr(self._cupy, 'hip')
                if is_hip:
                    return False
                try:
                    return self._cupy.cuda.runtime.getDeviceCount() > 0
                except Exception:
                    return False

            try:
                import cupy as cp
                # Reject ROCm/HIP builds
                is_hip = getattr(cp.cuda.runtime, 'is_hip', False) or hasattr(cp, 'hip') or 'rocm' in cp.__version__.lower()
                if is_hip:
                    return False

                self._cupy = cp
                # Verify at least one CUDA device exists
                try:
                    return cp.cuda.runtime.getDeviceCount() > 0
                except Exception:
                    return False
            except ImportError:
                return False

    def to_gpu(self, array) -> Any:
        """
        Transfer to GPU via CuPy.

        Args:
            array: NumPy array or array-like

        Returns:
            CuPy array on GPU

        Raises:
            RuntimeError: If CUDA unavailable or transfer fails
            MemoryError: If GPU out of memory
        """
        if not self.is_available():
            raise RuntimeError(
                "CUDA backend not available. Install with: pip install cupy-cuda12x"
            )

        try:
            return self._cupy.asarray(array)
        except Exception as e:
            # Check if OOM error
            if 'out of memory' in str(e).lower() or 'OutOfMemoryError' in str(type(e).__name__):
                mem_info = self.get_memory_info()
                raise MemoryError(
                    f"GPU out of memory. "
                    f"Device: {mem_info.get('device_used_mb', 0):.1f}/{mem_info.get('device_total_mb', 0):.1f} MB used"
                ) from e
            raise RuntimeError(f"GPU transfer failed: {e}") from e

    def to_cpu(self, array) -> Any:
        """
        Transfer to CPU via CuPy.

        Args:
            array: CuPy GPU array

        Returns:
            NumPy array

        Raises:
            RuntimeError: If CUDA unavailable or transfer fails
        """
        if not self.is_available():
            raise RuntimeError("CUDA backend not available")

        try:
            return self._cupy.asnumpy(array)
        except Exception as e:
            raise RuntimeError(f"GPU-to-CPU transfer failed: {e}") from e

    def get_memory_info(self) -> Dict[str, float]:
        """
        Get CUDA memory info (device + pool).

        Returns comprehensive memory statistics for monitoring and
        offload decisions.

        Returns:
            Dictionary with memory statistics (all in MB)
        """
        if not self.is_available():
            return {
                'device_free_mb': 0.0,
                'device_total_mb': 0.0,
                'device_used_mb': 0.0,
                'pool_cached_mb': 0.0
            }

        try:
            # Device memory (actual GPU RAM)
            device = self._cupy.cuda.Device()
            free_bytes, total_bytes = device.mem_info

            # Memory pool (CuPy's allocator cache)
            mempool = self._cupy.get_default_memory_pool()
            pool_bytes = mempool.total_bytes()

            return {
                'device_free_mb': free_bytes / (1024 * 1024),
                'device_total_mb': total_bytes / (1024 * 1024),
                'device_used_mb': (total_bytes - free_bytes) / (1024 * 1024),
                'pool_cached_mb': pool_bytes / (1024 * 1024)
            }
        except Exception as e:
            self.logger.warning(f"Error getting CUDA memory info: {e}")
            return {
                'device_free_mb': 0.0,
                'device_total_mb': 0.0,
                'device_used_mb': 0.0,
                'pool_cached_mb': 0.0
            }


class ROCmBackend(GPUBackend):
    """AMD ROCm backend via CuPy-ROCm or HIP"""

    def __init__(self, info: GPUBackendInfo):
        super().__init__(info)
        self._cupy_rocm = None
        self._init_lock = threading.Lock()  # Thread-safe lazy import

    def is_available(self) -> bool:
        """
        Check if ROCm/HIP available with actual GPU devices.

        Returns:
            True only if CuPy-ROCm imports (HIP build) AND at least one ROCm device exists
        """
        with self._init_lock:
            if self._cupy_rocm is not None:
                # Already loaded - verify it's HIP and has devices
                is_hip = getattr(self._cupy_rocm.cuda.runtime, 'is_hip', False) or hasattr(self._cupy_rocm, 'hip')
                if not is_hip:
                    return False
                try:
                    return self._cupy_rocm.cuda.runtime.getDeviceCount() > 0
                except Exception:
                    return False

            try:
                # Try CuPy built for ROCm
                import cupy as cp
                # Verify it's ROCm/HIP build
                is_hip = getattr(cp.cuda.runtime, 'is_hip', False) or hasattr(cp, 'hip') or 'rocm' in cp.__version__.lower()
                if not is_hip:
                    return False

                self._cupy_rocm = cp
                # Verify at least one ROCm device exists
                try:
                    return cp.cuda.runtime.getDeviceCount() > 0
                except Exception:
                    return False
            except ImportError:
                pass

            return False

    def to_gpu(self, array) -> Any:
        """Transfer to GPU via CuPy-ROCm"""
        if not self.is_available():
            raise RuntimeError(
                "ROCm backend not available. Install with: pip install cupy-rocm"
            )

        try:
            return self._cupy_rocm.asarray(array)
        except Exception as e:
            if 'out of memory' in str(e).lower():
                mem_info = self.get_memory_info()
                raise MemoryError(
                    f"GPU out of memory (ROCm). "
                    f"Used: {mem_info.get('device_used_mb', 0):.1f} MB"
                ) from e
            raise RuntimeError(f"ROCm transfer failed: {e}") from e

    def to_cpu(self, array) -> Any:
        """Transfer to CPU via CuPy-ROCm"""
        if not self.is_available():
            raise RuntimeError("ROCm backend not available")

        try:
            return self._cupy_rocm.asnumpy(array)
        except Exception as e:
            raise RuntimeError(f"ROCm-to-CPU transfer failed: {e}") from e

    def get_memory_info(self) -> Dict[str, float]:
        """Get ROCm memory info"""
        if not self.is_available():
            return {
                'device_free_mb': 0.0,
                'device_total_mb': 0.0,
                'device_used_mb': 0.0,
                'pool_cached_mb': 0.0
            }

        try:
            # ROCm device memory via HIP
            device = self._cupy_rocm.cuda.Device()  # CuPy-ROCm uses cuda API compatibility
            free_bytes, total_bytes = device.mem_info

            # Memory pool
            mempool = self._cupy_rocm.get_default_memory_pool()
            pool_bytes = mempool.total_bytes()

            return {
                'device_free_mb': free_bytes / (1024 * 1024),
                'device_total_mb': total_bytes / (1024 * 1024),
                'device_used_mb': (total_bytes - free_bytes) / (1024 * 1024),
                'pool_cached_mb': pool_bytes / (1024 * 1024)
            }
        except Exception as e:
            self.logger.warning(f"Error getting ROCm memory info: {e}")
            return {
                'device_free_mb': 0.0,
                'device_total_mb': 0.0,
                'device_used_mb': 0.0,
                'pool_cached_mb': 0.0
            }


class oneAPIBackend(GPUBackend):
    """Intel oneAPI backend via dpctl + numba-dpex"""

    def __init__(self, info: GPUBackendInfo):
        super().__init__(info)
        self._dpctl = None
        self._dpnp = None
        self._init_lock = threading.Lock()  # Thread-safe lazy import

    def is_available(self) -> bool:
        """
        Check if oneAPI (dpctl + dpnp) available with actual Intel GPU devices.

        Returns:
            True only if dpctl/dpnp import AND at least one Intel GPU device exists
        """
        with self._init_lock:
            if self._dpctl is not None and self._dpnp is not None:
                # Already loaded - verify GPU devices exist
                try:
                    gpu_devices = [d for d in self._dpctl.get_devices() if d.is_gpu]
                    return len(gpu_devices) > 0
                except Exception:
                    return False

            try:
                import dpctl
                import dpnp  # Data Parallel NumPy (Intel's NumPy for GPUs)

                # Verify at least one Intel GPU device exists
                try:
                    gpu_devices = [d for d in dpctl.get_devices() if d.is_gpu]
                    if len(gpu_devices) == 0:
                        return False
                except Exception:
                    return False

                self._dpctl = dpctl
                self._dpnp = dpnp
                return True
            except ImportError:
                return False

    def to_gpu(self, array) -> Any:
        """Transfer to GPU via dpnp (Intel Data Parallel NumPy)"""
        if not self.is_available():
            raise RuntimeError(
                "oneAPI backend not available. "
                "Install with: pip install dpctl dpnp numba-dpex"
            )

        try:
            # Convert NumPy → dpnp array (Intel GPU)
            return self._dpnp.asarray(array)
        except Exception as e:
            if 'memory' in str(e).lower():
                mem_info = self.get_memory_info()
                raise MemoryError(
                    f"Intel GPU out of memory. "
                    f"Used: {mem_info.get('device_used_mb', 0):.1f} MB"
                ) from e
            raise RuntimeError(f"oneAPI transfer failed: {e}") from e

    def to_cpu(self, array) -> Any:
        """Transfer to CPU via dpnp"""
        if not self.is_available():
            raise RuntimeError("oneAPI backend not available")

        try:
            # dpnp → NumPy conversion
            return self._dpnp.asnumpy(array)
        except Exception as e:
            raise RuntimeError(f"oneAPI-to-CPU transfer failed: {e}") from e

    def get_memory_info(self) -> Dict[str, float]:
        """
        Get Intel GPU memory info via dpctl.

        Note: dpctl/oneAPI Python bindings don't expose free/used memory.
        Total memory is reported via global_mem_size (preferred) or max_mem_alloc_size.
        """
        if not self.is_available():
            return {
                'device_free_mb': 0.0,
                'device_total_mb': 0.0,
                'device_used_mb': 0.0,
                'pool_cached_mb': 0.0
            }

        try:
            # Get GPU devices
            gpu_devices = [d for d in self._dpctl.get_devices() if d.is_gpu]
            if not gpu_devices:
                return {
                    'device_free_mb': 0.0,
                    'device_total_mb': 0.0,
                    'device_used_mb': 0.0,
                    'pool_cached_mb': 0.0
                }

            device = gpu_devices[0]  # First GPU

            # Prefer global_mem_size (more accurate) over max_mem_alloc_size
            if hasattr(device, 'global_mem_size'):
                total_bytes = device.global_mem_size
            else:
                total_bytes = device.max_mem_alloc_size * 4  # Approximation

            return {
                'device_free_mb': 0.0,  # Not exposed by dpctl
                'device_total_mb': total_bytes / (1024 * 1024),
                'device_used_mb': 0.0,  # Not exposed by dpctl
                'pool_cached_mb': 0.0   # dpnp doesn't expose pool stats
            }
        except Exception as e:
            self.logger.warning(f"Error getting oneAPI memory info: {e}")
            return {
                'device_free_mb': 0.0,
                'device_total_mb': 0.0,
                'device_used_mb': 0.0,
                'pool_cached_mb': 0.0
            }


class CPUBackend(GPUBackend):
    """CPU fallback backend via NumPy"""

    def __init__(self, info: GPUBackendInfo):
        super().__init__(info)

    def is_available(self) -> bool:
        """CPU always available"""
        return True

    def to_gpu(self, array) -> Any:
        """No-op for CPU (return NumPy array)"""
        import numpy as np
        return np.asarray(array)

    def to_cpu(self, array) -> Any:
        """No-op for CPU (return NumPy array)"""
        import numpy as np
        return np.asarray(array)

    def get_memory_info(self) -> Dict[str, float]:
        """CPU memory not tracked"""
        return {
            'device_free_mb': 0.0,
            'device_total_mb': 0.0,
            'device_used_mb': 0.0,
            'pool_cached_mb': 0.0
        }


class GPUBackendRegistry:
    """
    Registry and factory for GPU backends.

    Detects available GPU backends and provides unified access.
    """

    @staticmethod
    def detect_available_backends() -> Dict[GPUBackendKind, GPUBackendInfo]:
        """
        Detect all available GPU backends.

        Returns:
            Dict mapping backend kind to detected info
        """
        backends = {}

        # Detect CUDA or ROCm (mutually exclusive - same CuPy import)
        try:
            import cupy as cp

            # Distinguish CUDA vs ROCm build via runtime.is_hip
            is_hip = getattr(cp.cuda.runtime, 'is_hip', False) or hasattr(cp, 'hip') or 'rocm' in cp.__version__.lower()

            try:
                device_count = cp.cuda.runtime.getDeviceCount()
                if device_count > 0:
                    # Get info for first device
                    device = cp.cuda.Device(0)
                    mem_info = device.mem_info
                    total_gb = mem_info[1] / (1024 ** 3)

                    if not is_hip:
                        # NVIDIA CUDA backend
                        # Format compute_capability as "major.minor" (e.g., "8.6")
                        compute_cap = cp.cuda.Device(0).compute_capability
                        if isinstance(compute_cap, tuple) and len(compute_cap) >= 2:
                            compute_cap_str = f"{compute_cap[0]}.{compute_cap[1]}"
                        else:
                            compute_cap_str = str(compute_cap)

                        backends[GPUBackendKind.CUDA] = GPUBackendInfo(
                            kind=GPUBackendKind.CUDA,
                            version=cp.__version__,
                            device_count=device_count,
                            memory_gb=total_gb,
                            compute_capability=compute_cap_str
                        )
                    else:
                        # AMD ROCm backend (via CuPy-ROCm)
                        compute_cap = None
                        if hasattr(device, 'compute_capability'):
                            cap_tuple = device.compute_capability
                            compute_cap = f"gfx{cap_tuple[0]}{cap_tuple[1]}" if isinstance(cap_tuple, tuple) else str(cap_tuple)

                        backends[GPUBackendKind.ROCm] = GPUBackendInfo(
                            kind=GPUBackendKind.ROCm,
                            version=cp.__version__,
                            device_count=device_count,
                            memory_gb=total_gb,
                            compute_capability=compute_cap
                        )
            except Exception as e:
                backend_type = "ROCm" if is_hip else "CUDA"
                logger.debug(f"{backend_type} devices not accessible: {e}")
        except ImportError:
            pass

        # Detect oneAPI (Intel GPUs via dpctl)
        try:
            import dpctl
            import dpnp  # Required for full oneAPI support

            # Get Intel GPU devices
            try:
                gpu_devices = [d for d in dpctl.get_devices() if d.is_gpu]
                if gpu_devices:
                    device = gpu_devices[0]  # First Intel GPU
                    # Use global_mem_size if available, fallback to approximation
                    if hasattr(device, 'global_mem_size'):
                        total_gb = device.global_mem_size / (1024 ** 3)
                    else:
                        total_gb = device.max_mem_alloc_size * 4 / (1024 ** 3)  # Approximation

                    backends[GPUBackendKind.oneAPI] = GPUBackendInfo(
                        kind=GPUBackendKind.oneAPI,
                        version=dpctl.__version__,
                        device_count=len(gpu_devices),
                        memory_gb=total_gb,
                        compute_capability=device.name  # Device name (e.g., "Intel(R) Data Center GPU")
                    )
            except Exception as e:
                logger.debug(f"oneAPI devices not accessible: {e}")
        except ImportError:
            pass

        # CPU fallback always available
        try:
            import numpy as np
            numpy_version = np.__version__
        except ImportError:
            numpy_version = "unknown"

        backends[GPUBackendKind.CPU] = GPUBackendInfo(
            kind=GPUBackendKind.CPU,
            version=numpy_version,
            device_count=1,
            memory_gb=0.0  # Not tracked for CPU
        )

        return backends

    @staticmethod
    def create_backend(kind: GPUBackendKind, info: Optional[GPUBackendInfo] = None) -> GPUBackend:
        """
        Create backend instance.

        Args:
            kind: Backend type to create
            info: Optional backend info (detected if None)

        Returns:
            GPUBackend instance
        """
        if info is None:
            available = GPUBackendRegistry.detect_available_backends()
            info = available.get(kind)
            if info is None:
                # Requested backend not available - fall back to CPU
                logger.info(f"Requested backend {kind.value} not available; falling back to CPU")
                kind = GPUBackendKind.CPU  # CRITICAL FIX: Change kind to CPU
                info = available.get(GPUBackendKind.CPU)
                if info is None:
                    # Create CPU info if detection failed
                    import numpy as np
                    info = GPUBackendInfo(
                        kind=GPUBackendKind.CPU,
                        version=np.__version__,
                        device_count=1,
                        memory_gb=0.0
                    )

        # Create backend based on (possibly updated) kind
        if kind == GPUBackendKind.CUDA:
            return CUDABackend(info)
        elif kind == GPUBackendKind.ROCm:
            return ROCmBackend(info)
        elif kind == GPUBackendKind.oneAPI:
            return oneAPIBackend(info)
        elif kind == GPUBackendKind.CPU:
            return CPUBackend(info)
        else:
            # Unknown backend - should never reach here after fallback logic
            logger.warning(f"Unknown backend {kind}, using CPU fallback")
            return CPUBackend(info)

    @staticmethod
    def get_best_available() -> GPUBackend:
        """
        Get the best available GPU backend.

        Priority: CUDA > ROCm > oneAPI > CPU

        Returns:
            Best available backend instance
        """
        available = GPUBackendRegistry.detect_available_backends()

        # Try in priority order
        for kind in [GPUBackendKind.CUDA, GPUBackendKind.ROCm, GPUBackendKind.oneAPI]:
            if kind in available:
                return GPUBackendRegistry.create_backend(kind, available[kind])

        # Fallback to CPU
        return GPUBackendRegistry.create_backend(GPUBackendKind.CPU, available[GPUBackendKind.CPU])
