"""
GPU Detection and Capability Assessment

This module handles detection of GPU availability, CUDA capability assessment,
and hardware information gathering for GPU acceleration decisions.

Author: Epochly Development Team
"""

import logging
import threading
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class GPUBackend(Enum):
    """Available GPU backends."""
    NONE = "none"
    CUPY = "cupy" 
    CUDA = "cuda"
    OPENCL = "opencl"


@dataclass
class GPUInfo:
    """Information about available GPU resources."""
    backend: GPUBackend
    device_count: int
    memory_total: int  # in bytes
    memory_free: int   # in bytes
    compute_capability: Optional[str] = None
    device_name: Optional[str] = None
    cuda_version: Optional[str] = None
    driver_version: Optional[str] = None
    supports_unified_memory: bool = False


class GPUDetector:
    """
    Detector for GPU availability and capabilities.
    
    This class provides static methods for detecting GPU hardware
    and assessing suitability for acceleration.
    """
    
    _detection_cache: Optional[GPUInfo] = None
    _detection_lock = threading.Lock()
    _logger = logging.getLogger(__name__)
    
    @classmethod
    def is_available(cls) -> bool:
        """
        Check if GPU acceleration is available.
        
        Returns:
            True if GPU acceleration is available
        """
        info = cls.get_gpu_info()
        return info.backend != GPUBackend.NONE and info.device_count > 0
    
    @classmethod
    def get_gpu_info(cls) -> GPUInfo:
        """
        Get comprehensive GPU information.
        
        Returns:
            GPUInfo object with hardware details
        """
        with cls._detection_lock:
            if cls._detection_cache is None:
                cls._detection_cache = cls._detect_gpu_hardware()
            return cls._detection_cache
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the detection cache to force re-detection."""
        with cls._detection_lock:
            cls._detection_cache = None
    
    @classmethod
    def _detect_gpu_hardware(cls) -> GPUInfo:
        """Detect available GPU hardware and capabilities using fast detection first."""
        # Try FAST detection first using pynvml (nvidia-ml-py) - <25ms typical
        pynvml_info = cls._detect_pynvml_fast()
        if pynvml_info.backend != GPUBackend.NONE:
            return pynvml_info
        
        # Try direct CUDA detection (fallback)
        cuda_info = cls._detect_cuda_direct()
        if cuda_info.backend != GPUBackend.NONE:
            return cuda_info
        
        # CuPy detection as last resort (SLOW - only for comprehensive info)
        # NOTE: This is intentionally last due to 9+ second import overhead
        cupy_info = cls._detect_cupy()
        if cupy_info.backend != GPUBackend.NONE:
            return cupy_info
        
        # No GPU available
        return GPUInfo(
            backend=GPUBackend.NONE,
            device_count=0,
            memory_total=0,
            memory_free=0
        )
    
    @classmethod
    def _detect_pynvml_fast(cls) -> GPUInfo:
        """Fast GPU detection using pynvml (nvidia-ml-py) - target <25ms."""
        try:
            import pynvml
            
            # Initialize NVIDIA management library
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            
            if device_count == 0:
                pynvml.nvmlShutdown()
                return cls._get_no_gpu_info()
            
            # Get information for first device (fast)
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            device_name = pynvml.nvmlDeviceGetName(handle)
            
            # Get compute capability
            major, minor = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
            
            # Get CUDA/driver versions
            cuda_version = pynvml.nvmlSystemGetCudaDriverVersion()
            driver_version = pynvml.nvmlSystemGetDriverVersion()
            
            # Cleanup
            pynvml.nvmlShutdown()
            
            # Decode device name if bytes
            if isinstance(device_name, bytes):
                device_name = device_name.decode('utf-8')
            
            cls._logger.info(f"Fast GPU detected via pynvml: {device_name}, {device_count} devices, "
                           f"{memory_info.total // 1024**3}GB total memory")
            
            return GPUInfo(
                backend=GPUBackend.CUPY,  # Will use CuPy when actually needed
                device_count=device_count,
                memory_total=memory_info.total,
                memory_free=memory_info.free,
                compute_capability=f"{major}.{minor}",
                device_name=device_name,
                cuda_version=str(cuda_version),
                driver_version=str(driver_version),
                supports_unified_memory=major >= 6  # Unified memory available on SM 6.0+
            )
            
        except ImportError:
            cls._logger.debug("pynvml (nvidia-ml-py) not available for fast GPU detection")
            return cls._get_no_gpu_info()
        except Exception as e:
            cls._logger.debug(f"Fast pynvml GPU detection failed: {e}")
            return cls._get_no_gpu_info()
    
    @classmethod
    def _detect_cupy(cls) -> GPUInfo:
        """Detect CuPy availability and GPU information."""
        try:
            import cupy as cp
            
            # Check if CUDA is available
            if not cp.cuda.is_available():
                cls._logger.debug("CUDA not available for CuPy")
                return cls._get_no_gpu_info()
            
            # Get device information
            device_count = cp.cuda.runtime.getDeviceCount()
            if device_count == 0:
                cls._logger.debug("No CUDA devices found")
                return cls._get_no_gpu_info()
            
            # Get information for the current device
            device_id = cp.cuda.Device().id
            meminfo = cp.cuda.runtime.memGetInfo()
            memory_free = meminfo[0]  # free memory
            memory_total = meminfo[1]  # total memory
            
            # Get device properties
            props = cp.cuda.runtime.getDeviceProperties(device_id)
            device_name = props['name'].decode('utf-8')
            compute_capability = f"{props['major']}.{props['minor']}"
            
            # Get CUDA version information
            cuda_version = f"{cp.cuda.runtime.runtimeGetVersion()}"
            driver_version = f"{cp.cuda.runtime.driverGetVersion()}"
            
            # Check for unified memory support (compute capability >= 6.0)
            supports_unified_memory = (props['major'] >= 6)
            
            cls._logger.info(f"CuPy GPU detected: {device_name}, {device_count} devices, "
                           f"{memory_total // (1024**3)}GB total memory")
            
            return GPUInfo(
                backend=GPUBackend.CUPY,
                device_count=device_count,
                memory_total=memory_total,
                memory_free=memory_free,
                compute_capability=compute_capability,
                device_name=device_name,
                cuda_version=cuda_version,
                driver_version=driver_version,
                supports_unified_memory=supports_unified_memory
            )
            
        except ImportError:
            cls._logger.debug("CuPy not available (not installed)")
            return cls._get_no_gpu_info()
        except Exception as e:
            cls._logger.debug(f"CuPy detection failed: {e}")
            return cls._get_no_gpu_info()
    
    @classmethod
    def _detect_cuda_direct(cls) -> GPUInfo:
        """Direct CUDA detection without CuPy."""
        try:
            # Try pynvml for direct CUDA detection
            import pynvml
            
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            
            if device_count == 0:
                return cls._get_no_gpu_info()
            
            # Get information for first device
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            device_name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
            
            # Get compute capability
            major, minor = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
            compute_capability = f"{major}.{minor}"
            
            cls._logger.info(f"Direct CUDA GPU detected: {device_name}, {device_count} devices")
            
            return GPUInfo(
                backend=GPUBackend.CUDA,
                device_count=device_count,
                memory_total=memory_info.total,
                memory_free=memory_info.free,
                compute_capability=compute_capability,
                device_name=device_name,
                supports_unified_memory=(major >= 6)
            )
            
        except ImportError:
            cls._logger.debug("pynvml not available for direct CUDA detection")
            return cls._get_no_gpu_info()
        except Exception as e:
            cls._logger.debug(f"Direct CUDA detection failed: {e}")
            return cls._get_no_gpu_info()
    
    @classmethod
    def _get_no_gpu_info(cls) -> GPUInfo:
        """Return GPUInfo indicating no GPU available."""
        return GPUInfo(
            backend=GPUBackend.NONE,
            device_count=0,
            memory_total=0,
            memory_free=0
        )
    
    @classmethod
    def get_recommended_memory_limit(cls) -> int:
        """
        Get recommended GPU memory limit (80% of total).
        
        Returns:
            Recommended memory limit in bytes
        """
        info = cls.get_gpu_info()
        if info.backend == GPUBackend.NONE:
            return 0
        return int(info.memory_total * 0.8)
    
    @classmethod
    def is_operation_suitable_for_gpu(cls, operation_type: str, data_size: int) -> bool:
        """
        Determine if an operation is suitable for GPU acceleration.
        
        Args:
            operation_type: Type of operation (e.g., 'matmul', 'fft', 'elementwise')
            data_size: Size of data in bytes
            
        Returns:
            True if operation should be accelerated on GPU
        """
        if not cls.is_available():
            return False
        
        info = cls.get_gpu_info()
        
        # Minimum data size threshold (10MB as per Phase 11 spec)
        MIN_DATA_SIZE = 10 * 1024 * 1024  # 10MB
        if data_size < MIN_DATA_SIZE:
            return False
        
        # Check if we have enough free memory (need at least 2x data size for operations)
        if info.memory_free < data_size * 2:
            return False
        
        # Operations that benefit from GPU acceleration
        gpu_friendly_ops = {
            'matmul', 'dot', 'tensordot',       # Linear algebra
            'fft', 'ifft',                      # Fast Fourier Transform
            'convolve', 'correlate',            # Convolution operations  
            'sum', 'mean', 'std', 'var',        # Reductions
            'add', 'subtract', 'multiply',      # Element-wise operations
            'divide', 'power', 'sqrt',
            'sin', 'cos', 'exp', 'log',         # Mathematical functions
            'sort', 'argsort',                  # Sorting
            'unique', 'where',                  # Array operations
        }
        
        return operation_type.lower() in gpu_friendly_ops
    
    @classmethod
    def estimate_gpu_benefit(cls, operation_type: str, data_size: int) -> float:
        """
        Estimate potential speedup from GPU acceleration.
        
        Args:
            operation_type: Type of operation
            data_size: Size of data in bytes
            
        Returns:
            Estimated speedup ratio (1.0 = no benefit, 2.0 = 2x speedup)
        """
        if not cls.is_operation_suitable_for_gpu(operation_type, data_size):
            return 1.0
        
        # Speedup estimates based on operation type and data size
        base_speedups = {
            'matmul': 15.0,         # Matrix multiplication excellent on GPU
            'dot': 12.0,            # Dot product very good
            'fft': 8.0,             # FFT good acceleration
            'convolve': 6.0,        # Convolution good
            'sum': 4.0,             # Reductions moderate
            'elementwise': 3.0,     # Element-wise operations moderate
        }
        
        # Get base speedup for operation category
        op_category = cls._categorize_operation(operation_type)
        base_speedup = base_speedups.get(op_category, 2.0)
        
        # Scale based on data size (larger data = better GPU utilization)
        size_mb = data_size / (1024 * 1024)
        if size_mb > 100:       # >100MB
            size_factor = 1.2
        elif size_mb > 50:      # 50-100MB
            size_factor = 1.1
        else:                   # 10-50MB
            size_factor = 1.0
        
        return base_speedup * size_factor
    
    @classmethod
    def _categorize_operation(cls, operation_type: str) -> str:
        """Categorize operation type for speedup estimation."""
        op = operation_type.lower()
        
        if op in ['matmul', 'dot', 'tensordot']:
            return 'matmul'
        elif op in ['fft', 'ifft']:
            return 'fft'
        elif op in ['convolve', 'correlate']:
            return 'convolve'
        elif op in ['sum', 'mean', 'std', 'var', 'min', 'max']:
            return 'sum'
        else:
            return 'elementwise'