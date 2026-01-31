"""
CuPy Integration Manager

This module manages the dynamic switching between NumPy and CuPy for transparent
GPU acceleration. It provides zero-code-change GPU acceleration by intercepting
NumPy operations and transparently offloading suitable workloads to GPU.

Author: Epochly Development Team
"""

import logging
import threading
import time
from typing import Any, Dict, Optional, Callable
from functools import wraps
from contextlib import contextmanager

from .gpu_detector import GPUDetector, GPUInfo, GPUBackend
from .offload_optimizer import GPUOffloadOptimizer
from .gpu_memory_manager import GPUMemoryManager
from ..utils.exceptions import EpochlyError


class CuPyManager:
    """
    Manager for CuPy integration and NumPy/CuPy switching.
    
    This class handles:
    - Dynamic loading of CuPy
    - Transparent NumPy/CuPy operation switching
    - Memory management between CPU and GPU
    - Performance monitoring and optimization
    """
    
    _instance: Optional['CuPyManager'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        """Initialize the CuPy manager."""
        if CuPyManager._instance is not None:
            raise RuntimeError("CuPyManager is a singleton. Use get_instance().")
        
        self._logger = logging.getLogger(__name__)
        self._cupy = None
        self._gpu_info: Optional[GPUInfo] = None
        self._offload_optimizer: Optional[GPUOffloadOptimizer] = None
        self._memory_manager: Optional[GPUMemoryManager] = None
        
        # State management
        self._enabled = False
        self._initialization_attempted = False
        self._initialization_successful = False
        
        # Performance tracking
        self._operation_stats = {
            'gpu_operations': 0,
            'cpu_operations': 0,
            'gpu_time_saved': 0.0,
            'total_gpu_time': 0.0,
            'total_cpu_time': 0.0,
            'memory_transfers': 0,
            'transfer_time': 0.0
        }
        self._stats_lock = threading.Lock()
        
        # Configuration
        self._config = {
            'auto_enable': True,
            'memory_limit_ratio': 0.8,  # Use 80% of GPU memory
            'min_array_size': 10 * 1024 * 1024,  # 10MB minimum
            'enable_caching': True,
            'cache_size_limit': 100 * 1024 * 1024,  # 100MB cache
            'enable_profiling': True
        }
        
    @classmethod
    def get_instance(cls) -> 'CuPyManager':
        """Get the singleton instance of CuPyManager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def initialize(self, force_reinit: bool = False) -> bool:
        """
        Initialize CuPy and GPU resources.
        
        Args:
            force_reinit: Force reinitialization even if already attempted
            
        Returns:
            True if initialization successful
        """
        if self._initialization_attempted and not force_reinit:
            return self._initialization_successful
        
        self._initialization_attempted = True
        
        try:
            # Detect GPU hardware
            self._gpu_info = GPUDetector.get_gpu_info()
            
            if self._gpu_info.backend == GPUBackend.NONE:
                self._logger.info("No GPU detected - CuPy manager will remain disabled")
                return False
            
            # LAZY LOADING: Don't import CuPy during initialization
            # CuPy will be imported on-demand when first GPU operation is requested
            self._cupy = None  # Will be loaded lazily
            
            # Initialize memory manager (lightweight, no CuPy needed)
            memory_limit = int(self._gpu_info.memory_total * self._config['memory_limit_ratio'])
            self._memory_manager = GPUMemoryManager(
                memory_limit=memory_limit,
                enable_caching=self._config['enable_caching']
            )
            
            # Initialize offload optimizer (lightweight, no CuPy needed)
            self._offload_optimizer = GPUOffloadOptimizer(
                gpu_info=self._gpu_info,
                min_array_size=self._config['min_array_size']
            )
            
            # Memory pool setup will be done lazily when CuPy is loaded
            
            self._enabled = True
            self._initialization_successful = True
            
            self._logger.info(f"CuPy manager initialized successfully on {self._gpu_info.device_name} (lazy loading)")
            self._logger.info(f"GPU memory limit: {memory_limit // (1024**3)}GB")
            
            return True
            
        except ImportError:
            self._logger.warning(
                "CuPy dependencies not available - GPU acceleration disabled. "
                "Install with: pip install cupy-cuda12x"
            )
            return False
        except Exception as e:
            self._logger.error(f"CuPy manager initialization failed: {e}")
            return False
    
    def _load_cupy_on_demand(self) -> bool:
        """
        Load CuPy on-demand when first GPU operation is requested.
        
        Returns:
            True if CuPy loaded successfully
        """
        if self._cupy is not None:
            return True  # Already loaded
        
        try:
            self._logger.info("Loading CuPy on-demand for GPU operation")
            import cupy as cp
            self._cupy = cp
            
            # Set up memory pool now that CuPy is loaded
            memory_limit = int(self._gpu_info.memory_total * self._config['memory_limit_ratio'])
            if hasattr(cp, 'get_default_memory_pool'):
                pool = cp.get_default_memory_pool()
                pool.set_limit(size=memory_limit)
                self._logger.debug(f"CuPy memory pool configured: {memory_limit // (1024**3)}GB")
            
            return True
            
        except ImportError:
            self._logger.error("CuPy not available for GPU operations")
            return False
        except Exception as e:
            self._logger.error(f"Failed to load CuPy on-demand: {e}")
            return False
    
    def is_enabled(self) -> bool:
        """Check if CuPy manager is enabled and ready."""
        return self._enabled  # With lazy loading, don't require CuPy to be pre-loaded
    
    def get_gpu_info(self) -> Optional[GPUInfo]:
        """Get GPU information."""
        return self._gpu_info
    
    def should_use_gpu(self, array_size: int, operation: str) -> bool:
        """
        Determine if an operation should use GPU.
        
        Args:
            array_size: Size of arrays involved in bytes
            operation: Type of operation
            
        Returns:
            True if GPU should be used
        """
        if not self.is_enabled():
            return False
        
        if not self._offload_optimizer:
            return False
        
        return self._offload_optimizer.should_offload(array_size, operation)
    
    def numpy_to_cupy(self, array) -> Any:
        """
        Convert NumPy array to CuPy array.

        Args:
            array: NumPy array to convert

        Returns:
            CuPy array
        """
        if not self.is_enabled():
            raise EpochlyError("CuPy manager not enabled")

        # Load CuPy on-demand if not already loaded
        if self._cupy is None:
            if not self._load_cupy_on_demand():
                raise EpochlyError("Failed to load CuPy for GPU operation")

        try:
            start_time = time.time()

            # Handle memory management
            if self._memory_manager:
                self._memory_manager.ensure_memory_available(array.nbytes)

            # Convert to CuPy
            cupy_array = self._cupy.asarray(array)

            # Track transfer time
            transfer_time = time.time() - start_time
            with self._stats_lock:
                self._operation_stats['memory_transfers'] += 1
                self._operation_stats['transfer_time'] += transfer_time

            return cupy_array

        except Exception as e:
            self._logger.error(f"NumPy to CuPy conversion failed: {e}")
            raise EpochlyError(f"GPU conversion failed: {e}")
    
    def cupy_to_numpy(self, array) -> Any:
        """
        Convert CuPy array to NumPy array.

        Args:
            array: CuPy array to convert

        Returns:
            NumPy array
        """
        if not self.is_enabled():
            raise EpochlyError("CuPy manager not enabled")

        # Load CuPy on-demand if not already loaded
        if self._cupy is None:
            if not self._load_cupy_on_demand():
                raise EpochlyError("Failed to load CuPy for GPU operation")

        try:
            start_time = time.time()

            # Convert to NumPy (this triggers GPU to CPU transfer)
            numpy_array = self._cupy.asnumpy(array)

            # Track transfer time
            transfer_time = time.time() - start_time
            with self._stats_lock:
                self._operation_stats['memory_transfers'] += 1
                self._operation_stats['transfer_time'] += transfer_time

            return numpy_array

        except Exception as e:
            self._logger.error(f"CuPy to NumPy conversion failed: {e}")
            raise EpochlyError(f"GPU conversion failed: {e}")
    
    def execute_on_gpu(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute an operation on GPU with performance tracking.

        Args:
            operation: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of operation
        """
        if not self.is_enabled():
            raise EpochlyError("CuPy manager not enabled")

        # Load CuPy on-demand if not already loaded
        if self._cupy is None:
            if not self._load_cupy_on_demand():
                raise EpochlyError("Failed to load CuPy for GPU operation")

        start_time = time.time()

        try:
            # Execute operation
            result = operation(*args, **kwargs)

            # Track performance
            execution_time = time.time() - start_time
            with self._stats_lock:
                self._operation_stats['gpu_operations'] += 1
                self._operation_stats['total_gpu_time'] += execution_time

            return result

        except Exception as e:
            self._logger.error(f"GPU operation failed: {e}")
            # Track failed operation
            with self._stats_lock:
                self._operation_stats['cpu_operations'] += 1
            raise
    
    @contextmanager
    def gpu_context(self):
        """Context manager for GPU operations with automatic cleanup and lazy CuPy loading."""
        if not self.is_enabled():
            yield None
            return
        
        # Load CuPy on-demand when GPU context is first requested
        if self._cupy is None:
            if not self._load_cupy_on_demand():
                yield None
                return
        
        try:
            # Switch to GPU context
            with self._cupy.cuda.Device():
                yield self._cupy
        except Exception as e:
            self._logger.error(f"GPU context error: {e}")
            yield None
        finally:
            # Cleanup GPU memory if needed
            if self._memory_manager:
                self._memory_manager.cleanup_if_needed()
    
    def create_gpu_accelerated_function(self, numpy_func: Callable, 
                                      operation_name: str) -> Callable:
        """
        Create a GPU-accelerated version of a NumPy function.
        
        Args:
            numpy_func: Original NumPy function
            operation_name: Name of the operation for optimization decisions
            
        Returns:
            GPU-accelerated function that falls back to CPU
        """
        @wraps(numpy_func)
        def gpu_accelerated_wrapper(*args, **kwargs):
            # Check if we should use GPU for this operation
            if not self._should_accelerate_call(args, operation_name):
                # Execute on CPU
                start_time = time.time()
                result = numpy_func(*args, **kwargs)
                
                # Track CPU execution
                execution_time = time.time() - start_time
                with self._stats_lock:
                    self._operation_stats['cpu_operations'] += 1
                    self._operation_stats['total_cpu_time'] += execution_time
                
                return result
            
            # Execute on GPU
            try:
                with self.gpu_context() as cp:
                    if cp is None:
                        # Fallback to CPU
                        return numpy_func(*args, **kwargs)
                    
                    # Convert arguments to GPU
                    gpu_args = self._convert_args_to_gpu(args, cp)
                    gpu_kwargs = self._convert_kwargs_to_gpu(kwargs, cp)
                    
                    # Get CuPy equivalent function
                    cupy_func = getattr(cp, numpy_func.__name__)
                    
                    # Execute on GPU
                    gpu_result = self.execute_on_gpu(cupy_func, *gpu_args, **gpu_kwargs)
                    
                    # Convert result back to CPU if needed
                    if self._offload_optimizer and self._offload_optimizer.should_return_to_cpu():
                        return self.cupy_to_numpy(gpu_result)
                    else:
                        return gpu_result
                        
            except Exception as e:
                self._logger.debug(f"GPU execution failed for {operation_name}, falling back to CPU: {e}")
                
                # Fallback to CPU
                start_time = time.time()
                result = numpy_func(*args, **kwargs)
                
                execution_time = time.time() - start_time
                with self._stats_lock:
                    self._operation_stats['cpu_operations'] += 1
                    self._operation_stats['total_cpu_time'] += execution_time
                
                return result
        
        return gpu_accelerated_wrapper
    
    def _should_accelerate_call(self, args: tuple, operation_name: str) -> bool:
        """Determine if a specific function call should be GPU accelerated."""
        if not self.is_enabled():
            return False
        
        # Estimate total data size
        total_size = 0
        for arg in args:
            if hasattr(arg, 'nbytes'):
                total_size += arg.nbytes
            elif hasattr(arg, '__len__'):
                try:
                    import numpy as np
                    arr = np.asarray(arg)
                    total_size += arr.nbytes
                except:
                    continue
        
        return self.should_use_gpu(total_size, operation_name)
    
    def _convert_args_to_gpu(self, args: tuple, cp) -> tuple:
        """Convert positional arguments to GPU arrays."""
        gpu_args = []
        for arg in args:
            if hasattr(arg, 'ndim'):  # NumPy array
                gpu_args.append(cp.asarray(arg))
            else:
                gpu_args.append(arg)
        return tuple(gpu_args)
    
    def _convert_kwargs_to_gpu(self, kwargs: dict, cp) -> dict:
        """Convert keyword arguments to GPU arrays."""
        gpu_kwargs = {}
        for key, value in kwargs.items():
            if hasattr(value, 'ndim'):  # NumPy array
                gpu_kwargs[key] = cp.asarray(value)
            else:
                gpu_kwargs[key] = value
        return gpu_kwargs
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        with self._stats_lock:
            stats = self._operation_stats.copy()
        
        # Calculate derived metrics
        total_ops = stats['gpu_operations'] + stats['cpu_operations']
        if total_ops > 0:
            stats['gpu_operation_ratio'] = stats['gpu_operations'] / total_ops
        else:
            stats['gpu_operation_ratio'] = 0.0
        
        if stats['gpu_operations'] > 0:
            stats['avg_gpu_time'] = stats['total_gpu_time'] / stats['gpu_operations']
        else:
            stats['avg_gpu_time'] = 0.0
        
        if stats['cpu_operations'] > 0:
            stats['avg_cpu_time'] = stats['total_cpu_time'] / stats['cpu_operations']
        else:
            stats['avg_cpu_time'] = 0.0
        
        if stats['memory_transfers'] > 0:
            stats['avg_transfer_time'] = stats['transfer_time'] / stats['memory_transfers']
        else:
            stats['avg_transfer_time'] = 0.0
        
        # Add GPU info
        if self._gpu_info:
            stats['gpu_info'] = {
                'device_name': self._gpu_info.device_name,
                'memory_total_gb': self._gpu_info.memory_total // (1024**3),
                'memory_free_gb': self._gpu_info.memory_free // (1024**3),
                'compute_capability': self._gpu_info.compute_capability
            }
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset performance statistics."""
        with self._stats_lock:
            for key in self._operation_stats:
                if isinstance(self._operation_stats[key], (int, float)):
                    self._operation_stats[key] = 0 if isinstance(self._operation_stats[key], int) else 0.0
    
    def cleanup(self) -> None:
        """Cleanup GPU resources."""
        if self._memory_manager:
            self._memory_manager.cleanup()
        
        if self._cupy and hasattr(self._cupy, 'get_default_memory_pool'):
            try:
                pool = self._cupy.get_default_memory_pool()
                pool.free_all_blocks()
            except:
                pass
        
        self._enabled = False
        self._logger.info("CuPy manager cleanup completed")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass