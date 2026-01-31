"""
GPU Executor for Level 4 Enhancement

This module implements GPU-accelerated execution capabilities for Epochly,
providing transparent GPU acceleration through CuPy integration while
maintaining full compatibility with existing executor architecture.

Author: Epochly Development Team
"""

import os
import threading
import time
from typing import Any, Dict, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

from .execution_types import ExecutionRequest, ExecutionResult, ExecutionError
from ..base_plugins import EpochlyExecutor, create_executor_metadata, PluginPriority
from ...gpu.cupy_manager import CuPyManager
from ...gpu.gpu_detector import GPUDetector
from ...gpu.offload_optimizer import GPUOffloadOptimizer, ParallelismContext, OffloadDecision
from ..executor.shared_memory_manager import SharedMemoryManager
from ...utils.exceptions import EpochlyError
from ...jit.cuda_pattern_detector import CUDAPatternDetector, PatternAnalysis
from ...jit.cuda_kernel_compiler import CUDAKernelCompiler, CompiledKernel, CUPY_AVAILABLE
from ...jit.pattern_kernel_compiler import (
    PatternKernelCompiler,
    CompiledKernel as PatternCompiledKernel,
    UnsupportedOperationError,
    get_compiler as get_pattern_compiler,
)
from ...jit.stencil_kernel_compiler import (
    StencilKernelCompiler,
    CompiledStencilKernel,
    StencilCompilationError,
    get_stencil_compiler,
)


def _get_stable_func_id(func: Callable) -> str:
    """
    Get a stable identifier for a function that doesn't change when wrappers are installed.

    CRITICAL FIX (Jan 2025): Using id(func) as cache key caused cache misses when:
    1. GPUCanaryWrapper self-destructs to _GPUDisabledAwareWrapper
    2. Function object in __globals__ changes, but code object remains same
    3. Cache key changes -> re-compilation -> Run 2 slower than Run 1

    Solution: Use id(func.__code__) which is stable across wrapper installations.
    For wrapped functions, recursively extract the original function first.

    Wrapper Unwrapping Priority:
        1. _original (Epochly wrapper attribute - GPUCanaryWrapper, JITCanaryWrapper)
        2. __wrapped__ (functools.wraps standard attribute)
        3. _gpu (GPU-specific wrapper - used for compiled GPU function reference)

    Cache Collision Notes:
        - Functions with identical __code__ objects share cache keys (intentional)
        - Non-function callables with same module.qualname use instance id for uniqueness

    Args:
        func: Function to get stable identifier for

    Returns:
        Stable string identifier based on code object
    """
    import types

    # Recursively unwrap to find the original function (with cycle detection)
    seen = set()
    current = func

    while id(current) not in seen:
        seen.add(id(current))
        unwrapped = False

        # Priority 1: Epochly wrapper attributes (_original)
        # Handles GPUCanaryWrapper, JITCanaryWrapper, _GPUDisabledAwareWrapper, etc.
        if hasattr(current, '_original') and callable(getattr(current, '_original', None)):
            current = current._original
            unwrapped = True
            continue

        # Priority 2: functools.wraps standard (__wrapped__)
        if hasattr(current, '__wrapped__') and callable(current.__wrapped__):
            current = current.__wrapped__
            unwrapped = True
            continue

        # Priority 3: GPU wrapper internal function (_gpu)
        # Note: _gpu points to the compiled GPU function, which may not have __code__
        # if it's a closure/wrapper, so we just use it for its code object if available
        if hasattr(current, '_gpu') and callable(getattr(current, '_gpu', None)):
            gpu_func = current._gpu
            if hasattr(gpu_func, '__code__'):
                return str(id(gpu_func.__code__))
            # If _gpu doesn't have __code__, continue unwrapping

        if not unwrapped:
            break

    # After unwrapping, 'current' is the innermost callable
    original = current

    # Get code object - this is stable even when func object changes
    if hasattr(original, '__code__'):
        return str(id(original.__code__))

    # Fallback for non-function callables: use qualname + module + instance id
    # Instance id ensures unique cache keys for different callable instances
    # with the same qualname (e.g., multiple MyClass() instances)
    module = getattr(func, '__module__', 'unknown')
    qualname = getattr(func, '__qualname__', getattr(func, '__name__', 'unknown'))
    return f"{module}.{qualname}:{id(func)}"


class GPUExecutionMode(Enum):
    """GPU execution modes."""
    AUTO = "auto"                    # Automatic CPU/GPU selection
    FORCE_GPU = "force_gpu"         # Force GPU execution
    FORCE_CPU = "force_cpu"         # Force CPU execution
    HYBRID = "hybrid"               # Split between CPU and GPU


@dataclass
class GPUExecutionRequest(ExecutionRequest):
    """Extended execution request for GPU operations."""
    gpu_mode: GPUExecutionMode = GPUExecutionMode.AUTO
    min_gpu_benefit: float = 1.2    # Minimum speedup to justify GPU
    force_cpu_fallback: bool = True # Allow fallback to CPU on GPU failure
    memory_limit_mb: Optional[int] = None  # GPU memory limit for this operation


@dataclass
class GPUExecutionResult(ExecutionResult):
    """Extended execution result with GPU performance data."""
    executed_on_gpu: bool = False
    gpu_transfer_time: float = 0.0
    gpu_execution_time: float = 0.0
    cpu_fallback_used: bool = False
    tertiary_fallback_used: bool = False  # Inline Python fallback when GPU+CPU fail
    estimated_speedup: float = 1.0
    actual_speedup: float = 1.0
    memory_transfers: int = 0
    metadata: Optional[Dict[str, Any]] = None


class GPUExecutor(EpochlyExecutor):
    """
    GPU-accelerated executor for Level 4 enhancement.

    This executor provides transparent GPU acceleration for suitable workloads
    while maintaining full compatibility with the existing executor interface.
    It automatically determines when to use GPU vs CPU execution and handles
    graceful fallback scenarios.
    """

    # Default ProcessPool dispatch overhead for LEVEL_3 parallelism estimates.
    # Based on typical IPC overhead: warm pool ~10ms, cold start ~100ms.
    # Conservative 50ms default for typical mixed workload scenarios.
    DEFAULT_DISPATCH_OVERHEAD_MS = 50.0

    def __init__(self):
        """Initialize the GPU executor."""
        metadata = create_executor_metadata(
            priority=PluginPriority.HIGH,
            capabilities=[
                "gpu_acceleration",
                "cupy_integration", 
                "automatic_offloading",
                "transparent_fallback",
                "performance_monitoring",
                "memory_optimization"
            ]
        )
        super().__init__("gpu_executor", "1.0.0", metadata)
        
        # GPU management components
        self._cupy_manager: Optional[CuPyManager] = None
        self._gpu_detector: Optional[GPUDetector] = None
        self._offload_optimizer: Optional[GPUOffloadOptimizer] = None
        self._shared_memory_manager: Optional[SharedMemoryManager] = None

        # JIT compilation components for loop acceleration
        self._pattern_detector: Optional[CUDAPatternDetector] = None
        self._kernel_compiler: Optional[CUDAKernelCompiler] = None
        self._jit_kernel_cache: Dict[str, CompiledKernel] = {}

        # Pattern-Aware Kernel Compiler for LEVEL_4 true GPU parallelism
        # This compiles map/reduce patterns to actual CuPy ElementwiseKernel/ReductionKernel
        # instead of running Python for-loops with CuPy arrays
        self._pattern_kernel_compiler: Optional[PatternKernelCompiler] = None
        self._pattern_kernel_cache: Dict[str, PatternCompiledKernel] = {}

        # Stencil Kernel Compiler for LEVEL_4 stencil pattern acceleration
        # This compiles 2D stencil patterns to CuPy RawKernel CUDA kernels
        # providing 100-1000x speedup over Python loops with CuPy arrays
        self._stencil_kernel_compiler: Optional[StencilKernelCompiler] = None
        self._stencil_kernel_cache: Dict[str, CompiledStencilKernel] = {}

        # CuPy builtin wrapper cache for LEVEL_4 pattern compilation
        # Stores plain callable wrappers (NOT PatternCompiledKernel) for patterns
        # like scan, histogram, filter, gather, scatter
        self._cupy_builtin_cache: Dict[str, Callable] = {}

        # Execution state
        self._enabled = False
        self._gpu_available = False
        self._gpu_info = None
        
        # Performance tracking
        self._execution_stats = {
            'total_requests': 0,
            'gpu_executions': 0,
            'cpu_executions': 0,
            'fallback_executions': 0,
            'tertiary_fallback_executions': 0,
            'total_gpu_time': 0.0,
            'total_cpu_time': 0.0,
            'total_transfer_time': 0.0,
            'total_speedup_achieved': 0.0
        }
        self._stats_lock = threading.Lock()
        
        # Thread pool for CPU fallback
        self._cpu_executor: Optional[ThreadPoolExecutor] = None
        
        # Configuration
        self._config = {
            'enable_auto_offload': True,
            'gpu_memory_limit_ratio': 0.8,
            'max_concurrent_gpu_ops': 4,
            'cpu_fallback_timeout': 30.0,
            'performance_monitoring': True,
            'aggressive_caching': False
        }
    
    def _setup_plugin(self) -> None:
        """Setup GPU executor components."""
        self._logger.info("Setting up GPU executor for Level 4 enhancement")
        
        try:
            # Initialize GPU detection
            self._gpu_detector = GPUDetector()
            self._gpu_available = self._gpu_detector.is_available()
            self._gpu_info = self._gpu_detector.get_gpu_info()
            
            if not self._gpu_available:
                self._logger.info("No GPU available - GPU executor will operate in CPU-only mode")
                self._enabled = False
                return
            
            # Initialize CuPy manager
            self._cupy_manager = CuPyManager.get_instance()
            if not self._cupy_manager.initialize():
                self._logger.warning("CuPy manager initialization failed - falling back to CPU-only mode")
                self._enabled = False
                return
            
            # Initialize offload optimizer
            self._offload_optimizer = GPUOffloadOptimizer(
                gpu_info=self._gpu_info,
                min_array_size=10 * 1024 * 1024  # 10MB minimum as per Phase 11 spec
            )
            
            # Initialize shared memory manager for zero-copy operations
            self._shared_memory_manager = SharedMemoryManager()
            
            # Initialize CPU fallback executor
            self._cpu_executor = ThreadPoolExecutor(
                max_workers=4,
                thread_name_prefix="Epochly-GPU-Fallback"
            )

            # Initialize JIT compilation components for loop acceleration
            self._pattern_detector = CUDAPatternDetector()
            self._kernel_compiler = CUDAKernelCompiler()

            # Initialize Pattern-Aware Kernel Compiler for LEVEL_4 true GPU parallelism
            # This provides 5-10x speedup by compiling to actual CUDA kernels
            # instead of running Python for-loops with CuPy arrays
            self._pattern_kernel_compiler = PatternKernelCompiler()

            # Initialize Stencil Kernel Compiler for LEVEL_4 stencil acceleration
            # This compiles 2D stencil patterns (neighbor access) to CuPy RawKernel
            # providing 100-1000x speedup over Python for-loops with CuPy arrays
            self._stencil_kernel_compiler = get_stencil_compiler()

            self._enabled = True

            self._logger.info("GPU executor initialized successfully")
            self._logger.info("JIT pattern detector and kernel compiler initialized")
            self._logger.info(
                f"Pattern-Aware Kernel Compiler initialized with operations: "
                f"{self._pattern_kernel_compiler.get_supported_operations()}"
            )
            self._logger.info("Stencil Kernel Compiler initialized for 2D stencil pattern acceleration")
            self._logger.info(f"GPU: {self._gpu_info.device_name}")
            self._logger.info(f"GPU Memory: {self._gpu_info.memory_total // (1024**3)}GB total, "
                            f"{self._gpu_info.memory_free // (1024**3)}GB free")
            
        except Exception as e:
            self._logger.error(f"GPU executor setup failed: {e}")
            self._enabled = False
    
    def _teardown_plugin(self) -> None:
        """Teardown GPU executor components."""
        self._logger.info("Tearing down GPU executor")
        
        # Shutdown CPU executor
        if self._cpu_executor:
            self._cpu_executor.shutdown(wait=True)
            self._cpu_executor = None
        
        # Cleanup GPU manager
        if self._cupy_manager:
            self._cupy_manager.cleanup()
        
        self._enabled = False
    
    def execute_function(self, request: Union[ExecutionRequest, GPUExecutionRequest]) -> ExecutionResult:
        """
        Execute a function with GPU acceleration when beneficial.
        
        Args:
            request: Execution request with function and parameters
            
        Returns:
            Execution result with performance data
        """
        start_time = time.time()
        
        # Convert to GPU request if needed
        if not isinstance(request, GPUExecutionRequest):
            gpu_request = GPUExecutionRequest(
                func=request.func,
                args=request.args,
                kwargs=request.kwargs,
                gpu_mode=getattr(request, 'gpu_mode', GPUExecutionMode.AUTO)
            )
        else:
            gpu_request = request
        
        # Track request
        with self._stats_lock:
            self._execution_stats['total_requests'] += 1

        # Initialize strategy before try block to prevent UnboundLocalError
        # if _determine_execution_strategy raises an exception
        strategy = "cpu"

        try:
            # Determine execution strategy
            strategy = self._determine_execution_strategy(gpu_request)
            
            if strategy == "gpu" and self._enabled:
                result = self._execute_on_gpu(gpu_request)
            elif strategy == "hybrid" and self._enabled:
                result = self._execute_hybrid(gpu_request)
            else:
                result = self._execute_on_cpu(gpu_request)
            
            # Calculate total execution time
            total_time = time.time() - start_time
            result.execution_time = total_time
            
            return result
            
        except Exception as e:
            self._logger.error(f"GPU execution failed: {e}")
            
            # Fallback to CPU if enabled
            if gpu_request.force_cpu_fallback and strategy != "cpu":
                self._logger.info("Attempting CPU fallback after GPU execution failure")
                
                try:
                    result = self._execute_on_cpu(gpu_request)
                    result.cpu_fallback_used = True
                    
                    with self._stats_lock:
                        self._execution_stats['fallback_executions'] += 1
                    
                    return result
                    
                except Exception as fallback_error:
                    self._logger.error(f"CPU fallback also failed: {fallback_error}")

                    # Tertiary fallback: Execute inline Python as last resort
                    self._logger.warning(
                        f"Both GPU and CPU failed, attempting tertiary fallback "
                        f"(inline Python execution) for {gpu_request.func.__name__}"
                    )

                    try:
                        tertiary_start = time.time()
                        tertiary_result = gpu_request.func(
                            *gpu_request.args, **gpu_request.kwargs
                        )
                        tertiary_time = time.time() - tertiary_start

                        with self._stats_lock:
                            self._execution_stats['tertiary_fallback_executions'] += 1
                            self._execution_stats['total_cpu_time'] += tertiary_time

                        return GPUExecutionResult(
                            result=tertiary_result,
                            success=True,
                            executed_on_gpu=False,
                            cpu_fallback_used=False,
                            tertiary_fallback_used=True,
                            execution_time=tertiary_time
                        )

                    except Exception as tertiary_error:
                        self._logger.error(f"Tertiary fallback also failed: {tertiary_error}")
                        raise ExecutionError(
                            f"All execution paths failed (GPU, CPU, tertiary): "
                            f"GPU error: {e}, CPU error: {fallback_error}, "
                            f"Tertiary error: {tertiary_error}"
                        )
            else:
                raise ExecutionError(f"GPU execution failed: {e}")

    def execute(self, func: Callable, *args, timeout: Optional[float] = None, **kwargs) -> Any:
        """
        Execute a function with GPU acceleration (EpochlyCore API).

        This method provides the interface expected by EpochlyCore for Level 4
        GPU acceleration. It wraps the function in an ExecutionRequest and
        delegates to execute_function.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            timeout: Optional timeout in seconds (not currently used for GPU)
            **kwargs: Keyword arguments for the function

        Returns:
            The function result value
        """
        request = GPUExecutionRequest(
            func=func,
            args=args,
            kwargs=kwargs,
            gpu_mode=GPUExecutionMode.AUTO
        )
        result = self.execute_function(request)
        return result.result

    def submit(self, func: Callable, *args, **kwargs) -> Any:
        """
        Submit a function for GPU-accelerated execution (EpochlyCore API).

        This method provides the interface expected by EpochlyCore.submit_task()
        for Level 4 GPU acceleration. Currently executes synchronously but
        returns the result directly for compatibility.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The function result value
        """
        # For now, execute synchronously - async GPU execution can be added later
        return self.execute(func, *args, **kwargs)

    def _determine_execution_strategy(self, request: GPUExecutionRequest) -> str:
        """
        Determine the optimal execution strategy for a request.

        Uses JIT-aware offload decision: for custom functions, first checks if they
        can be JIT-compiled to GPU kernels. If yes, uses pattern-type-specific
        speedup estimates instead of the conservative 2.0x default.

        Args:
            request: GPU execution request

        Returns:
            Execution strategy: "gpu", "cpu", or "hybrid"
        """
        # Check forced modes first
        if request.gpu_mode == GPUExecutionMode.FORCE_GPU:
            return "gpu"
        elif request.gpu_mode == GPUExecutionMode.FORCE_CPU:
            return "cpu"
        elif request.gpu_mode == GPUExecutionMode.HYBRID:
            return "hybrid"

        # Auto mode - analyze the request
        if not self._enabled or not self._offload_optimizer:
            return "cpu"

        # Estimate data size
        data_size = self._estimate_data_size(request.args, request.kwargs)

        # Get function name for operation analysis
        func_name = getattr(request.func, '__name__', str(request.func))

        # JIT-AWARE OFFLOAD DECISION: Check if function can be JIT-compiled BEFORE
        # making offload decision. This fixes the issue where custom functions
        # default to 2.0x speedup (losing to 7.2x parallel CPU) even when they
        # could be JIT-compiled to efficient GPU stencil/matmul kernels.
        jit_operation_name = self._get_jit_operation_name(request.func)
        if jit_operation_name:
            func_name = jit_operation_name
            self._logger.debug(f"JIT pattern detected: using '{jit_operation_name}' for offload decision")

        # Get parallelism context for accurate GPU vs parallel-CPU comparison
        # This ensures we compare GPU time against LEVEL_3 parallelized CPU time,
        # not single-core CPU time (which would incorrectly favor GPU)
        parallelism_ctx = self._get_parallelism_context()

        # Analyze offload opportunity with graceful degradation to CPU on errors.
        # Offload analysis is advisory, not mission-critical - if it fails,
        # we should run on CPU rather than fail the entire request.
        try:
            analysis = self._offload_optimizer.analyze_offload_opportunity(
                data_size, func_name, parallelism_context=parallelism_ctx
            )

            # Check if GPU is beneficial based on decision and min_gpu_benefit threshold
            if analysis.decision == OffloadDecision.GPU_OFFLOAD:
                if analysis.estimated_speedup >= request.min_gpu_benefit:
                    return "gpu"
        except Exception as e:
            # Graceful degradation: if offload analysis fails, default to CPU
            self._logger.debug(f"Offload analysis failed, defaulting to CPU: {e}")

        return "cpu"

    def _get_jit_operation_name(self, func: Callable) -> Optional[str]:
        """
        Check if a function can be JIT-compiled and return its operation name.

        Analyzes the function using the pattern detector. If parallelizable with
        high confidence (>0.7), returns a standardized operation name that maps
        to appropriate speedup estimates in the offload optimizer.

        Pattern type to operation name mapping:
        - stencil -> 'stencil' (uses convolve-like speedups: ~6x)
        - matmul  -> 'matmul' (uses matmul speedups: ~15x)
        - reduce  -> 'sum' (uses reduction speedups: ~4x)
        - map     -> 'elementwise' (uses element-wise speedups: ~3x)
        - scan    -> 'cumsum' (uses scan speedups: ~4x)

        Args:
            func: Function to analyze

        Returns:
            Operation name for offload decision, or None if not JIT-compilable
        """
        if not self._pattern_detector:
            return None

        func_name = getattr(func, '__name__', 'unknown')

        try:
            # Analyze function for parallelizable patterns
            analysis = self._pattern_detector.analyze(func)

            if not analysis.parallelizable or analysis.confidence < 0.7:
                return None

            # Map pattern type to operation name for speedup estimation.
            # These map to entries in the offload optimizer's _base_speedup_estimates.
            # Stencils use dedicated 'stencil' entry (10x GPU speedup) added in the optimizer.
            pattern_to_operation = {
                'stencil': 'stencil',     # Stencil patterns: high arithmetic intensity, ~10x GPU speedup
                'matmul': 'matmul',       # Matrix multiplication: ~15x GPU speedup
                'reduce': 'sum',          # Reduction patterns: ~4x GPU speedup
                'map': 'multiply',        # Element-wise map: ~3x GPU speedup
                'scan': 'cumsum',         # Scan patterns: ~5x GPU speedup
                'transpose': 'transpose', # Transpose: ~2x GPU speedup (memory-bound)
            }

            operation_name = pattern_to_operation.get(analysis.pattern_type)
            if operation_name:
                self._logger.debug(
                    f"JIT analysis for {func_name}: pattern={analysis.pattern_type}, "
                    f"confidence={analysis.confidence:.2f}, operation={operation_name}"
                )
            return operation_name

        except Exception as e:
            self._logger.debug(f"JIT pattern detection failed for {func_name}: {e}")
            return None

    def _get_parallelism_context(self) -> Optional[ParallelismContext]:
        """
        Get the current CPU parallelism context for accurate offload decisions.

        Returns ParallelismContext describing the current enhancement level and
        available CPU cores. This enables the offload optimizer to compare GPU
        execution time against parallelized CPU execution time (not single-core).

        Returns:
            ParallelismContext if LEVEL_3+ is active, None otherwise
        """
        try:
            # Import lazily to avoid circular imports
            from ...core.epochly_core import get_epochly_core

            core = get_epochly_core()
            if core is None or not hasattr(core, 'current_level'):
                return None

            current_level = core.current_level
            level_value = current_level.value if hasattr(current_level, 'value') else int(current_level)

            # Only create parallelism context for LEVEL_3+ (multi-core parallelization)
            if level_value >= 3:
                available_cores = os.cpu_count() or 1

                return ParallelismContext(
                    level=level_value,
                    available_cores=available_cores,
                    level3_dispatch_overhead_ms=self.DEFAULT_DISPATCH_OVERHEAD_MS
                )

            return None

        except Exception as e:
            # Don't fail offload decisions due to context retrieval errors
            self._logger.debug(f"Could not get parallelism context: {e}")
            return None
    
    def _execute_on_gpu(self, request: GPUExecutionRequest) -> GPUExecutionResult:
        """Execute function on GPU with CuPy acceleration."""
        start_time = time.time()
        transfer_start = time.time()
        
        try:
            with self._cupy_manager.gpu_context() as cp:
                if cp is None:
                    raise EpochlyError("GPU context not available")
                
                # Convert arguments to GPU
                gpu_args = self._convert_args_to_gpu(request.args)
                gpu_kwargs = self._convert_kwargs_to_gpu(request.kwargs)
                
                transfer_time = time.time() - transfer_start
                
                # Execute on GPU
                exec_start = time.time()
                
                # Try to find CuPy equivalent of the function
                gpu_func = self._get_gpu_function(request.func, cp)
                if gpu_func is None:
                    raise EpochlyError(f"No GPU implementation available for {request.func}")
                
                gpu_result = gpu_func(*gpu_args, **gpu_kwargs)
                
                exec_time = time.time() - exec_start
                
                # Convert result back to CPU if needed
                result_transfer_start = time.time()
                if self._offload_optimizer.should_return_to_cpu():
                    final_result = self._cupy_manager.cupy_to_numpy(gpu_result)
                else:
                    final_result = gpu_result
                
                result_transfer_time = time.time() - result_transfer_start
                total_transfer_time = transfer_time + result_transfer_time
                
                # Track performance
                with self._stats_lock:
                    self._execution_stats['gpu_executions'] += 1
                    self._execution_stats['total_gpu_time'] += exec_time
                    self._execution_stats['total_transfer_time'] += total_transfer_time

                # Calculate speedup estimate
                estimated_cpu_time = self._estimate_cpu_execution_time(request)
                actual_speedup = estimated_cpu_time / (exec_time + total_transfer_time) if exec_time > 0 else 1.0

                # Record performance for adaptive learning (wire up the learning system)
                data_size = self._estimate_data_size(request.args, request.kwargs)
                operation_name = getattr(request.func, '__name__', 'unknown')
                self._offload_optimizer.record_operation_performance(
                    operation=operation_name,
                    data_size=data_size,
                    gpu_time=exec_time,
                    cpu_time=estimated_cpu_time,
                    transfer_time=total_transfer_time,
                    success=True
                )
                
                return GPUExecutionResult(
                    result=final_result,
                    success=True,
                    execution_time=time.time() - start_time,
                    executed_on_gpu=True,
                    gpu_transfer_time=total_transfer_time,
                    gpu_execution_time=exec_time,
                    actual_speedup=actual_speedup,
                    memory_transfers=2,  # To GPU and back to CPU
                    metadata={
                        'gpu_device': self._gpu_info.device_name if self._gpu_info else 'unknown',
                        'data_size_mb': self._estimate_data_size(request.args, request.kwargs) / (1024**2)
                    }
                )
                
        except Exception as e:
            # Record failed execution for adaptive learning
            # Guard: optimizer may be None in CPU-only mode (no GPU or CuPy init failed)
            if self._offload_optimizer:
                try:
                    data_size = self._estimate_data_size(request.args, request.kwargs)
                    operation_name = getattr(request.func, '__name__', 'unknown')
                    self._offload_optimizer.record_operation_performance(
                        operation=operation_name,
                        data_size=data_size,
                        gpu_time=0.0,
                        cpu_time=None,
                        transfer_time=0.0,
                        success=False
                    )
                except Exception:
                    pass  # Don't fail on recording failure
            self._logger.error(f"GPU execution failed: {e}")
            raise ExecutionError(f"GPU execution failed: {e}")
    
    def _execute_on_cpu(self, request: GPUExecutionRequest) -> GPUExecutionResult:
        """Execute function on CPU with performance tracking."""
        start_time = time.time()

        try:
            # Execute on CPU
            result = request.func(*request.args, **request.kwargs)

            exec_time = time.time() - start_time

            # Track performance
            with self._stats_lock:
                self._execution_stats['cpu_executions'] += 1
                self._execution_stats['total_cpu_time'] += exec_time

            # Record CPU execution time for adaptive learning (if optimizer available)
            # This helps the optimizer learn actual CPU performance
            # Guard: optimizer may be None in CPU-only mode (no GPU or CuPy init failed)
            if self._offload_optimizer:
                data_size = self._estimate_data_size(request.args, request.kwargs)
                operation_name = getattr(request.func, '__name__', 'unknown')
                self._offload_optimizer.record_operation_performance(
                    operation=operation_name,
                    data_size=data_size,
                    gpu_time=None,
                    cpu_time=exec_time,
                    transfer_time=None,
                    success=True
                )

            return GPUExecutionResult(
                result=result,
                success=True,
                execution_time=exec_time,
                executed_on_gpu=False,
                actual_speedup=1.0,
                metadata={'execution_mode': 'cpu'}
            )

        except Exception as e:
            self._logger.error(f"CPU execution failed: {e}")
            raise ExecutionError(f"CPU execution failed: {e}")
    
    def _execute_hybrid(self, request: GPUExecutionRequest) -> GPUExecutionResult:
        """Execute function using hybrid CPU/GPU approach."""
        # Hybrid execution falls back to strategy determination
        # In future versions, this could implement workload splitting
        strategy = "gpu" if self._enabled else "cpu"
        
        if strategy == "gpu":
            return self._execute_on_gpu(request)
        else:
            return self._execute_on_cpu(request)
    
    def _convert_args_to_gpu(self, args: tuple) -> tuple:
        """Convert positional arguments to GPU arrays."""
        if not self._cupy_manager:
            return args
        
        gpu_args = []
        for arg in args:
            if hasattr(arg, 'ndim'):  # NumPy array
                gpu_args.append(self._cupy_manager.numpy_to_cupy(arg))
            else:
                gpu_args.append(arg)
        return tuple(gpu_args)
    
    def _convert_kwargs_to_gpu(self, kwargs: dict) -> dict:
        """Convert keyword arguments to GPU arrays."""
        if not self._cupy_manager:
            return kwargs
        
        gpu_kwargs = {}
        for key, value in kwargs.items():
            if hasattr(value, 'ndim'):  # NumPy array
                gpu_kwargs[key] = self._cupy_manager.numpy_to_cupy(value)
            else:
                gpu_kwargs[key] = value
        return gpu_kwargs
    
    def _get_gpu_function(self, func: Callable, cp) -> Optional[Callable]:
        """Get CuPy equivalent of a function or JIT-compile it."""
        func_name = getattr(func, '__name__', None)

        # Comprehensive CuPy function mapping for transparent GPU acceleration
        # Covers: linear algebra, FFT, reductions, sorting, math functions
        function_mappings = {
            # Matrix multiplication / Linear algebra basics
            'matrix_multiply': cp.dot,
            'large_matrix_multiply': cp.dot,
            'matrix_mult': cp.dot,
            'matmul': cp.matmul,
            'dot_product': cp.dot,
            'vector_dot': cp.dot,
            'dot': cp.dot,
            'tensordot': cp.tensordot,
            'einsum': cp.einsum,
            'inner': cp.inner,
            'outer': cp.outer,

            # Linear algebra decompositions (cuSOLVER)
            # Note: CuPy only supports eigh/eigvalsh (Hermitian), not general eig/eigvals
            'svd': cp.linalg.svd,
            'qr': cp.linalg.qr,
            'cholesky': cp.linalg.cholesky,
            'eigh': cp.linalg.eigh,
            'eigvalsh': cp.linalg.eigvalsh,

            # Linear algebra solvers
            'solve': cp.linalg.solve,
            'lstsq': cp.linalg.lstsq,
            'inv': cp.linalg.inv,
            'pinv': cp.linalg.pinv,
            'norm': cp.linalg.norm,

            # FFT operations (cuFFT)
            'fft': cp.fft.fft,
            'ifft': cp.fft.ifft,
            'fft2': cp.fft.fft2,
            'ifft2': cp.fft.ifft2,
            'fftn': cp.fft.fftn,
            'ifftn': cp.fft.ifftn,
            'rfft': cp.fft.rfft,
            'irfft': cp.fft.irfft,
            'rfft2': cp.fft.rfft2,
            'irfft2': cp.fft.irfft2,
            'rfftn': cp.fft.rfftn,
            'irfftn': cp.fft.irfftn,
            'fftshift': cp.fft.fftshift,
            'ifftshift': cp.fft.ifftshift,
            'fftfreq': cp.fft.fftfreq,
            'fft_transform': cp.fft.fft,
            'ifft_transform': cp.fft.ifft,

            # Reductions
            'array_sum': cp.sum,
            'array_mean': cp.mean,
            'sum': cp.sum,
            'prod': cp.prod,
            'mean': cp.mean,
            'std': cp.std,
            'var': cp.var,
            'max': cp.max,
            'min': cp.min,
            'argmax': cp.argmax,
            'argmin': cp.argmin,
            'cumsum': cp.cumsum,
            'cumprod': cp.cumprod,

            # Array manipulation
            'transpose': cp.transpose,
            'reshape': cp.reshape,
            'reshape_array': cp.reshape,
            'concatenate': cp.concatenate,
            'concatenate_arrays': cp.concatenate,
            'stack': cp.stack,
            'hstack': cp.hstack,
            'vstack': cp.vstack,
            'dstack': cp.dstack,
            'split': cp.split,
            'hsplit': cp.hsplit,
            'vsplit': cp.vsplit,
            'ravel': cp.ravel,
            'flatten': lambda x: x.flatten(),
            'squeeze': cp.squeeze,
            'expand_dims': cp.expand_dims,
            'swapaxes': cp.swapaxes,
            'moveaxis': cp.moveaxis,
            'rollaxis': cp.rollaxis,

            # Sorting and searching
            'sort': cp.sort,
            'argsort': cp.argsort,
            'partition': cp.partition,
            'argpartition': cp.argpartition,
            'searchsorted': cp.searchsorted,
            'where': cp.where,
            'nonzero': cp.nonzero,

            # Mathematical functions
            'sin': cp.sin,
            'cos': cp.cos,
            'tan': cp.tan,
            'arcsin': cp.arcsin,
            'arccos': cp.arccos,
            'arctan': cp.arctan,
            'arctan2': cp.arctan2,
            'sinh': cp.sinh,
            'cosh': cp.cosh,
            'tanh': cp.tanh,
            'exp': cp.exp,
            'expm1': cp.expm1,
            'log': cp.log,
            'log10': cp.log10,
            'log2': cp.log2,
            'log1p': cp.log1p,
            'sqrt': cp.sqrt,
            'cbrt': cp.cbrt,
            'square': cp.square,
            'power': cp.power,
            'abs': cp.abs,
            'absolute': cp.absolute,
            'sign': cp.sign,
            'floor': cp.floor,
            'ceil': cp.ceil,
            'round': cp.round,
            'trunc': cp.trunc,
            'maximum': cp.maximum,
            'minimum': cp.minimum,
            'clip': cp.clip,

            # Statistics
            'corrcoef': cp.corrcoef,
            'cov': cp.cov,
            'histogram': cp.histogram,
            'bincount': cp.bincount,
            'percentile': cp.percentile,
            'quantile': cp.quantile,
            'median': cp.median,

            # Array creation (for completeness)
            'zeros': cp.zeros,
            'ones': cp.ones,
            'empty': cp.empty,
            'full': cp.full,
            'zeros_like': cp.zeros_like,
            'ones_like': cp.ones_like,
            'empty_like': cp.empty_like,
            'full_like': cp.full_like,
            'arange': cp.arange,
            'linspace': cp.linspace,
            'logspace': cp.logspace,
            'eye': cp.eye,
            'identity': cp.identity,
            'diag': cp.diag,
            'diagflat': cp.diagflat,

            # Additional Linear Algebra (CuPy docs section 5.3.9)
            'vdot': cp.vdot,
            'kron': cp.kron,
            'matrix_power': cp.linalg.matrix_power,
            'det': cp.linalg.det,
            'matrix_rank': cp.linalg.matrix_rank,
            'slogdet': cp.linalg.slogdet,
            'trace': cp.trace,
            'tensorsolve': cp.linalg.tensorsolve,
            'tensorinv': cp.linalg.tensorinv,
            # Note: eigvalsh already defined above in decompositions section

            # Additional Array Creation (CuPy docs section 5.3.1)
            'tri': cp.tri,
            'tril': cp.tril,
            'triu': cp.triu,
            'meshgrid': cp.meshgrid,
            'asanyarray': cp.asanyarray,
            'ascontiguousarray': cp.ascontiguousarray,
            'asfortranarray': cp.asfortranarray,
            'copy': cp.copy,
            'fromfile': cp.fromfile,
            'asarray': cp.asarray,

            # Additional Array Manipulation (CuPy docs section 5.3.2)
            'copyto': cp.copyto,
            'shape': cp.shape,
            'broadcast_to': cp.broadcast_to,
            'broadcast_arrays': cp.broadcast_arrays,
            'require': cp.require,
            'column_stack': cp.column_stack,
            'array_split': cp.array_split,
            'dsplit': cp.dsplit,
            'tile': cp.tile,
            'repeat': cp.repeat,
            'append': cp.append,
            'resize': cp.resize,
            'unique': cp.unique,
            'trim_zeros': cp.trim_zeros,
            'flip': cp.flip,
            'fliplr': cp.fliplr,
            'flipud': cp.flipud,
            'roll': cp.roll,
            'rot90': cp.rot90,

            # Indexing Operations (CuPy docs section 5.3.7)
            'indices': cp.indices,
            'ix_': cp.ix_,
            'ravel_multi_index': cp.ravel_multi_index,
            'unravel_index': cp.unravel_index,
            'diag_indices': cp.diag_indices,
            'diag_indices_from': cp.diag_indices_from,
            'take': cp.take,
            'take_along_axis': cp.take_along_axis,
            'choose': cp.choose,
            'compress': cp.compress,
            'diagonal': cp.diagonal,
            'select': cp.select,
            'place': cp.place,
            'put': cp.put,
            'putmask': cp.putmask,
            'fill_diagonal': cp.fill_diagonal,

            # Additional Mathematical Functions (CuPy docs section 5.3.11)
            'arcsinh': cp.arcsinh,
            'arccosh': cp.arccosh,
            'arctanh': cp.arctanh,
            'deg2rad': cp.deg2rad,
            'rad2deg': cp.rad2deg,
            'degrees': cp.degrees,
            'radians': cp.radians,
            'hypot': cp.hypot,
            'reciprocal': cp.reciprocal,
            'positive': cp.positive,
            'negative': cp.negative,
            'real': cp.real,
            'imag': cp.imag,
            'conj': cp.conj,
            'conjugate': cp.conjugate,
            'angle': cp.angle,
            'mod': cp.mod,
            'fmod': cp.fmod,
            'remainder': cp.remainder,
            'divmod': cp.divmod,
            'modf': cp.modf,
            'rint': cp.rint,
            'fix': cp.fix,
            'around': cp.around,
            'ptp': cp.ptp,
            'unwrap': cp.unwrap,
            'diff': cp.diff,
            'gradient': cp.gradient,
            'ediff1d': cp.ediff1d,
            'cross': cp.cross,
            'trapz': cp.trapz,
            'sinc': cp.sinc,
            'signbit': cp.signbit,
            'copysign': cp.copysign,
            'frexp': cp.frexp,
            'ldexp': cp.ldexp,
            'nextafter': cp.nextafter,
            # Note: CuPy doesn't have spacing
            'lcm': cp.lcm,
            'gcd': cp.gcd,
            'add': cp.add,
            'subtract': cp.subtract,
            'multiply': cp.multiply,
            'divide': cp.divide,
            'true_divide': cp.true_divide,
            'floor_divide': cp.floor_divide,
            'float_power': cp.float_power,

            # NaN-safe Functions (CuPy docs)
            'nansum': cp.nansum,
            'nanprod': cp.nanprod,
            'nancumsum': cp.nancumsum,
            'nancumprod': cp.nancumprod,
            'nanmean': cp.nanmean,
            'nanstd': cp.nanstd,
            'nanvar': cp.nanvar,
            'nanmax': cp.nanmax,
            'nanmin': cp.nanmin,
            'nanargmax': cp.nanargmax,
            'nanargmin': cp.nanargmin,
            # Note: CuPy doesn't have nanpercentile/nanquantile
            'nanmedian': cp.nanmedian,

            # Logic Functions (CuPy docs section 5.3.10)
            'all': cp.all,
            'any': cp.any,
            'isnan': cp.isnan,
            'isinf': cp.isinf,
            'isfinite': cp.isfinite,
            'isneginf': cp.isneginf,
            'isposinf': cp.isposinf,
            'iscomplex': cp.iscomplex,
            'isreal': cp.isreal,
            'allclose': cp.allclose,
            'isclose': cp.isclose,
            'array_equal': cp.array_equal,
            'logical_and': cp.logical_and,
            'logical_or': cp.logical_or,
            'logical_not': cp.logical_not,
            'logical_xor': cp.logical_xor,
            'greater': cp.greater,
            'greater_equal': cp.greater_equal,
            'less': cp.less,
            'less_equal': cp.less_equal,
            'equal': cp.equal,
            'not_equal': cp.not_equal,

            # Additional FFT (CuPy docs section 5.3.5)
            'hfft': cp.fft.hfft,
            'ihfft': cp.fft.ihfft,
            'rfftfreq': cp.fft.rfftfreq,

            # Set Operations (CuPy docs section 5.3.16)
            'in1d': cp.in1d,
            'isin': cp.isin,
            'intersect1d': cp.intersect1d,
            'setdiff1d': cp.setdiff1d,
            'setxor1d': cp.setxor1d,
            'union1d': cp.union1d,

            # Binary Operations (CuPy docs section 5.3.3)
            'bitwise_and': cp.bitwise_and,
            'bitwise_or': cp.bitwise_or,
            'bitwise_xor': cp.bitwise_xor,
            'invert': cp.invert,
            'left_shift': cp.left_shift,
            'right_shift': cp.right_shift,
            'packbits': cp.packbits,
            'unpackbits': cp.unpackbits,

            # Additional Statistics (CuPy docs section 5.3.18)
            'average': cp.average,
            'count_nonzero': cp.count_nonzero,
            'histogram2d': cp.histogram2d,
            'histogramdd': cp.histogramdd,
            'digitize': cp.digitize,

            # Functional Programming (CuPy docs section 5.3.6)
            'apply_along_axis': cp.apply_along_axis,
            'piecewise': cp.piecewise,
            'vectorize': cp.vectorize,
        }

        # Check direct function mapping first
        if func_name in function_mappings:
            return function_mappings[func_name]

        # Check if CuPy has direct equivalent
        if func_name and hasattr(cp, func_name):
            return getattr(cp, func_name)

        # Handle NumPy module functions
        if hasattr(func, '__module__') and func.__module__ == 'numpy':
            if hasattr(cp, func_name):
                return getattr(cp, func_name)

        # Handle NumPy submodule functions (numpy.linalg, numpy.fft)
        if hasattr(func, '__module__'):
            module = func.__module__
            if module.startswith('numpy.linalg') and hasattr(cp.linalg, func_name):
                return getattr(cp.linalg, func_name)
            elif module.startswith('numpy.fft') and hasattr(cp.fft, func_name):
                return getattr(cp.fft, func_name)
            elif module.startswith('numpy.random') and hasattr(cp.random, func_name):
                return getattr(cp.random, func_name)

        # Try JIT compilation for Python loops (matmul, stencil, map, reduce patterns)
        jit_wrapper = self._try_jit_compile(func)
        if jit_wrapper is not None:
            self._logger.info(f"JIT compiled {func_name} for GPU acceleration")
            return jit_wrapper

        # Create GPU-accelerated wrapper for custom functions
        return self._cupy_manager.create_gpu_accelerated_function(func, func_name or 'unknown')

    def _try_jit_compile(self, func: Callable) -> Optional[Callable]:
        """
        Attempt to JIT compile a function for GPU execution.

        Analyzes the function for parallelizable loop patterns (stencil, map, reduce)
        and compiles them to GPU-accelerated kernels.

        LEVEL_4 Enhancement: For map and reduce patterns, uses PatternKernelCompiler
        to compile to actual CuPy ElementwiseKernel/ReductionKernel for true GPU
        parallelism (5-10x speedup over Python for-loops with CuPy arrays).

        IMPORTANT: Stencil patterns skip JIT compilation because the kernel executor
        only handles simple averaging patterns, not complex computations. For stencils,
        returning None causes fallback to create_gpu_accelerated_function() which runs
        the actual function with CuPy arrays for correct GPU execution.

        Args:
            func: Python function to analyze and potentially compile

        Returns:
            GPU-accelerated wrapper function if compilation succeeds, None otherwise
        """
        if not self._pattern_detector or not self._kernel_compiler:
            return None

        if not CUPY_AVAILABLE:
            return None

        func_name = getattr(func, '__name__', 'unknown')

        # CRITICAL FIX (Jan 2025): Use stable function ID for cache keys
        # Using id(func) caused cache misses when GPUCanaryWrapper self-destructed
        # to _GPUDisabledAwareWrapper (different object → different id → cache miss)
        # This caused Run 2 to be SLOWER than Run 1 (re-compilation instead of cache hit)
        stable_id = _get_stable_func_id(func)

        # Check CuPy builtin wrapper cache first (LEVEL_4 scan/histogram/filter/etc.)
        # These are plain callable wrappers, NOT PatternCompiledKernel objects
        builtin_cache_key = f"builtin:{func_name}:{stable_id}"
        if builtin_cache_key in self._cupy_builtin_cache:
            return self._cupy_builtin_cache[builtin_cache_key]

        # Check pattern kernel cache (LEVEL_4 map/reduce compiled kernels)
        # These are PatternCompiledKernel objects with .execute() method
        pattern_cache_key = f"pattern:{func_name}:{stable_id}"
        if pattern_cache_key in self._pattern_kernel_cache:
            kernel = self._pattern_kernel_cache[pattern_cache_key]
            return self._create_pattern_kernel_wrapper(kernel, func_name)

        # Check stencil kernel cache (LEVEL_4 stencil patterns)
        stencil_cache_key = f"stencil:{func_name}:{stable_id}"
        if stencil_cache_key in self._stencil_kernel_cache:
            kernel = self._stencil_kernel_cache[stencil_cache_key]
            return self._create_stencil_kernel_wrapper(kernel, func_name)

        # Check legacy JIT kernel cache
        cache_key = f"{func_name}:{stable_id}"
        if cache_key in self._jit_kernel_cache:
            kernel = self._jit_kernel_cache[cache_key]
            return self._create_kernel_wrapper(kernel)

        try:
            # Analyze function for parallelizable patterns
            analysis = self._pattern_detector.analyze(func)

            if not analysis.parallelizable:
                self._logger.debug(f"Function {func_name} not parallelizable: {analysis.rejection_reason}")

                # LEVEL_4 Enhancement: Try recursive function analysis
                # When outer function is rejected due to external function calls,
                # analyze inner functions for GPU-acceleratable patterns
                recursive_wrapper = self._try_recursive_jit_compile(
                    func, analysis.rejection_reason, func_name
                )
                if recursive_wrapper is not None:
                    return recursive_wrapper

                return None

            # LEVEL_4: Try Stencil Kernel Compilation for stencil patterns
            # This compiles 2D stencil patterns to CuPy RawKernel CUDA kernels for
            # true GPU parallelism instead of Python for-loops with CuPy arrays.
            # Provides 100-1000x speedup over sequential Python execution.
            if analysis.pattern_type == 'stencil' and self._stencil_kernel_compiler:
                stencil_wrapper = self._try_stencil_kernel_compile(
                    func, analysis, func_name, stencil_cache_key
                )
                if stencil_wrapper is not None:
                    return stencil_wrapper
                # If stencil compilation fails, fall through to CPU JIT fallback
                # CRITICAL: Changed from debug to warning (Jan 2025 RCA) to make
                # GPU fallbacks visible. This helps diagnose why Level 4 times
                # match Level 3 (indicates GPU compilation is failing silently).
                self._logger.warning(
                    f"LEVEL_4 GPU: Stencil pattern '{func_name}' compilation failed, "
                    f"falling back to CPU JIT. Performance will match Level 3."
                )
                return None

            # LEVEL_4: Try Pattern-Aware Kernel Compilation for map/reduce patterns
            # This compiles to actual CuPy ElementwiseKernel/ReductionKernel for
            # true GPU parallelism instead of Python for-loops with CuPy arrays
            if analysis.pattern_type in ('map', 'reduce') and self._pattern_kernel_compiler:
                pattern_wrapper = self._try_pattern_kernel_compile(
                    func, analysis, func_name, pattern_cache_key
                )
                if pattern_wrapper is not None:
                    return pattern_wrapper

            # LEVEL_4: Handle additional detected patterns using CuPy built-ins
            # These patterns are detected by cuda_pattern_detector and compiled to
            # optimized CuPy operations for true GPU parallelism
            if analysis.pattern_type in ('scan', 'histogram', 'filter', 'gather', 'scatter'):
                cupy_wrapper = self._try_cupy_builtin_compile(
                    func, analysis, func_name, builtin_cache_key
                )
                if cupy_wrapper is not None:
                    return cupy_wrapper

            # Fallback: Compile to legacy GPU kernel (for matmul, transpose, etc.)
            kernel = self._kernel_compiler.compile(func, analysis)

            if not kernel.is_compiled:
                self._logger.debug(f"Failed to compile kernel for {func_name}")
                return None

            # Cache the compiled kernel
            self._jit_kernel_cache[cache_key] = kernel

            self._logger.info(
                f"JIT compiled {func_name}: pattern={analysis.pattern_type}, "
                f"confidence={analysis.confidence:.2f}"
            )

            return self._create_kernel_wrapper(kernel)

        except Exception as e:
            self._logger.debug(f"JIT compilation failed for {func_name}: {e}")
            return None

    def _try_pattern_kernel_compile(
        self,
        func: Callable,
        analysis: PatternAnalysis,
        func_name: str,
        cache_key: str
    ) -> Optional[Callable]:
        """
        Try to compile a map/reduce pattern to a CuPy kernel using PatternKernelCompiler.

        This is the LEVEL_4 enhancement that provides 5-10x speedup by compiling
        detected patterns to actual CuPy ElementwiseKernel/ReductionKernel instead
        of running Python for-loops with CuPy arrays.

        Args:
            func: The function to compile
            analysis: Pattern analysis results
            func_name: Name of the function for logging
            cache_key: Cache key for storing the compiled kernel

        Returns:
            GPU-accelerated wrapper function if compilation succeeds, None otherwise
        """
        import cupy as cp
        import numpy as np

        try:
            # Detect the specific operation from the function name or analysis
            operation = self._detect_operation_from_function(func, analysis)

            if operation is None:
                self._logger.debug(
                    f"Could not detect operation for {func_name}, "
                    f"pattern={analysis.pattern_type}"
                )
                return None

            # Check if operation is supported
            if operation not in self._pattern_kernel_compiler.get_supported_operations():
                self._logger.debug(
                    f"Operation '{operation}' not supported by PatternKernelCompiler"
                )
                return None

            # Compile the pattern to a CuPy kernel
            if analysis.pattern_type == 'map':
                compiled_kernel = self._pattern_kernel_compiler.compile_map_pattern(
                    operation=operation,
                    input_dtype=np.float64,  # Default, will be inferred at runtime
                    output_dtype=np.float64
                )
            elif analysis.pattern_type == 'reduce':
                compiled_kernel = self._pattern_kernel_compiler.compile_reduce_pattern(
                    operation=operation,
                    input_dtype=np.float64,
                    output_dtype=np.float64
                )
            else:
                return None

            # Cache the compiled kernel
            self._pattern_kernel_cache[cache_key] = compiled_kernel

            self._logger.info(
                f"LEVEL_4: Compiled {func_name} to CuPy {compiled_kernel.kernel_type} kernel "
                f"(pattern={analysis.pattern_type}, operation={operation})"
            )

            return self._create_pattern_kernel_wrapper(compiled_kernel, func_name)

        except UnsupportedOperationError as e:
            self._logger.debug(f"PatternKernelCompiler: {e}")
            return None
        except Exception as e:
            self._logger.debug(f"Pattern kernel compilation failed for {func_name}: {e}")
            return None

    def _try_cupy_builtin_compile(
        self,
        func: Callable,
        analysis: PatternAnalysis,
        func_name: str,
        cache_key: str
    ) -> Optional[Callable]:
        """
        Compile detected patterns to CuPy built-in operations.

        This handles patterns that map directly to optimized CuPy functions:
        - scan → cp.cumsum / cp.cumprod
        - histogram → cp.bincount / cp.histogram
        - filter → boolean masking (arr[mask])
        - gather → cp.take / cp.take_along_axis
        - scatter → cp.add.at / cupyx.scatter_add

        Args:
            func: The function to compile
            analysis: Pattern analysis results
            func_name: Name of the function for logging
            cache_key: Cache key for storing the compiled wrapper

        Returns:
            GPU-accelerated wrapper function if compilation succeeds, None otherwise
        """
        import cupy as cp
        import numpy as np

        try:
            pattern = analysis.pattern_type

            if pattern == 'scan':
                return self._compile_scan_pattern(func, analysis, func_name, cache_key)
            elif pattern == 'histogram':
                return self._compile_histogram_pattern(func, analysis, func_name, cache_key)
            elif pattern == 'filter':
                return self._compile_filter_pattern(func, analysis, func_name, cache_key)
            elif pattern == 'gather':
                return self._compile_gather_pattern(func, analysis, func_name, cache_key)
            elif pattern == 'scatter':
                return self._compile_scatter_pattern(func, analysis, func_name, cache_key)
            else:
                return None

        except Exception as e:
            self._logger.debug(f"CuPy builtin compilation failed for {func_name}: {e}")
            return None

    def _extract_scan_operation(self, func: Callable) -> str:
        """
        Extract scan accumulation operation from function AST.

        Analyzes the user function to find the augmented assignment operator
        (e.g., `acc += val` or `acc *= val`) to determine cumsum vs cumprod.

        Returns: 'sum' for cumsum, 'prod' for cumprod
        """
        import ast
        import inspect

        try:
            source = inspect.getsource(func)
            import textwrap
            source = textwrap.dedent(source)
            tree = ast.parse(source)
        except Exception:
            return 'sum'  # Default to cumsum

        class ScanOpVisitor(ast.NodeVisitor):
            def __init__(self):
                self.op = 'sum'  # Default

            def visit_AugAssign(self, node):
                # Detect *= for product, += for sum
                if isinstance(node.op, ast.Mult):
                    self.op = 'prod'
                elif isinstance(node.op, ast.Add):
                    self.op = 'sum'
                self.generic_visit(node)

        visitor = ScanOpVisitor()
        visitor.visit(tree)
        return visitor.op

    def _compile_scan_pattern(
        self, func: Callable, analysis: PatternAnalysis, func_name: str, cache_key: str
    ) -> Optional[Callable]:
        """Compile scan (prefix-sum) pattern to cp.cumsum/cp.cumprod with AST-extracted op."""
        import cupy as cp
        import numpy as np

        # Extract accumulation operation from function's AST
        scan_op = self._extract_scan_operation(func)
        is_product = (scan_op == 'prod')

        def scan_wrapper(arr, *args):
            arr_gpu = cp.asarray(arr)
            if is_product:
                result_gpu = cp.cumprod(arr_gpu)
            else:
                result_gpu = cp.cumsum(arr_gpu)
            return cp.asnumpy(result_gpu)

        self._cupy_builtin_cache[cache_key] = scan_wrapper
        self._logger.info(
            f"LEVEL_4: Compiled {func_name} to cp.{'cumprod' if is_product else 'cumsum'} "
            f"(pattern=scan, op={scan_op})"
        )
        return scan_wrapper

    def _compile_histogram_pattern(
        self, func: Callable, analysis: PatternAnalysis, func_name: str, cache_key: str
    ) -> Optional[Callable]:
        """Compile histogram pattern to cp.bincount or cp.histogram."""
        import cupy as cp
        import numpy as np

        def histogram_wrapper(data, num_bins, *args):
            data_gpu = cp.asarray(data)
            # Use bincount for all integer types (int8/16/32/64, uint8/16/32/64)
            if cp.issubdtype(data_gpu.dtype, cp.integer):
                result_gpu = cp.bincount(data_gpu, minlength=int(num_bins))
            else:
                # For float data, use histogram
                result_gpu, _ = cp.histogram(data_gpu, bins=int(num_bins))
            return cp.asnumpy(result_gpu)

        self._cupy_builtin_cache[cache_key] = histogram_wrapper
        self._logger.info(
            f"LEVEL_4: Compiled {func_name} to cp.bincount/cp.histogram (pattern=histogram)"
        )
        return histogram_wrapper

    def _extract_filter_condition(self, func: Callable) -> Optional[str]:
        """
        Extract filter comparison operator from function AST.

        Analyzes the user function to find the comparison operator used in
        if-conditions inside loops (e.g., `if x > threshold`, `if val != 0`).

        Returns: Operator string ('>', '<', '>=', '<=', '==', '!=') or None
        """
        import ast
        import inspect

        try:
            source = inspect.getsource(func)
            # Dedent to handle methods
            import textwrap
            source = textwrap.dedent(source)
            tree = ast.parse(source)
        except Exception:
            return None

        class FilterConditionVisitor(ast.NodeVisitor):
            def __init__(self):
                self.op = None

            def visit_If(self, node):
                if isinstance(node.test, ast.Compare) and len(node.test.ops) == 1:
                    op_map = {
                        ast.Gt: '>',
                        ast.Lt: '<',
                        ast.GtE: '>=',
                        ast.LtE: '<=',
                        ast.Eq: '==',
                        ast.NotEq: '!='
                    }
                    self.op = op_map.get(type(node.test.ops[0]))
                self.generic_visit(node)

        visitor = FilterConditionVisitor()
        visitor.visit(tree)
        return visitor.op

    def _compile_filter_pattern(
        self, func: Callable, analysis: PatternAnalysis, func_name: str, cache_key: str
    ) -> Optional[Callable]:
        """Compile filter/compact pattern to boolean masking with AST-extracted condition."""
        import cupy as cp
        import numpy as np

        # Extract the actual comparison operator from the function's AST
        extracted_op = self._extract_filter_condition(func)
        if extracted_op is None:
            extracted_op = '>'  # Default fallback

        def filter_wrapper(arr, threshold=0, *args):
            arr_gpu = cp.asarray(arr)
            # Apply the extracted comparison operation
            if extracted_op == '>':
                mask = arr_gpu > threshold
            elif extracted_op == '<':
                mask = arr_gpu < threshold
            elif extracted_op == '>=':
                mask = arr_gpu >= threshold
            elif extracted_op == '<=':
                mask = arr_gpu <= threshold
            elif extracted_op == '==':
                mask = arr_gpu == threshold
            elif extracted_op == '!=':
                mask = arr_gpu != threshold
            else:
                mask = arr_gpu > threshold  # Fallback
            result_gpu = arr_gpu[mask]
            return cp.asnumpy(result_gpu)

        self._cupy_builtin_cache[cache_key] = filter_wrapper
        self._logger.info(
            f"LEVEL_4: Compiled {func_name} to boolean masking (pattern=filter, op={extracted_op})"
        )
        return filter_wrapper

    def _compile_gather_pattern(
        self, func: Callable, analysis: PatternAnalysis, func_name: str, cache_key: str
    ) -> Optional[Callable]:
        """Compile gather pattern to cp.take."""
        import cupy as cp
        import numpy as np

        def gather_wrapper(data, indices, *args):
            data_gpu = cp.asarray(data)
            indices_gpu = cp.asarray(indices)
            result_gpu = cp.take(data_gpu, indices_gpu)
            return cp.asnumpy(result_gpu)

        self._cupy_builtin_cache[cache_key] = gather_wrapper
        self._logger.info(f"LEVEL_4: Compiled {func_name} to cp.take (pattern=gather)")
        return gather_wrapper

    def _extract_scatter_operation(self, func: Callable) -> str:
        """
        Extract scatter accumulation operation from function AST.

        Analyzes the user function to find the augmented assignment operator
        in array subscript operations (e.g., `out[idx] += val` or `out[idx] = val`).

        Returns: 'add' for cp.add.at, 'multiply' for cp.multiply.at, 'assign' for direct
        """
        import ast
        import inspect

        try:
            source = inspect.getsource(func)
            import textwrap
            source = textwrap.dedent(source)
            tree = ast.parse(source)
        except Exception:
            return 'add'  # Default to add.at

        class ScatterOpVisitor(ast.NodeVisitor):
            def __init__(self):
                self.op = 'add'  # Default

            def visit_AugAssign(self, node):
                # Check if target is subscript (array indexing)
                if isinstance(node.target, ast.Subscript):
                    if isinstance(node.op, ast.Mult):
                        self.op = 'multiply'
                    elif isinstance(node.op, ast.Add):
                        self.op = 'add'
                self.generic_visit(node)

            def visit_Assign(self, node):
                # Check for direct assignment to subscript
                for target in node.targets:
                    if isinstance(target, ast.Subscript):
                        self.op = 'assign'
                        break
                self.generic_visit(node)

        visitor = ScatterOpVisitor()
        visitor.visit(tree)
        return visitor.op

    def _compile_scatter_pattern(
        self, func: Callable, analysis: PatternAnalysis, func_name: str, cache_key: str
    ) -> Optional[Callable]:
        """Compile scatter pattern with AST-extracted operation."""
        import cupy as cp
        import numpy as np

        # Extract scatter operation from function's AST
        scatter_op = self._extract_scatter_operation(func)

        def scatter_wrapper(data, indices, out_size, *args):
            data_gpu = cp.asarray(data)
            indices_gpu = cp.asarray(indices)
            result_gpu = cp.zeros(int(out_size), dtype=data_gpu.dtype)

            if scatter_op == 'add':
                cp.add.at(result_gpu, indices_gpu, data_gpu)
            elif scatter_op == 'multiply':
                result_gpu[:] = 1.0  # Initialize to 1 for multiplication
                cp.multiply.at(result_gpu, indices_gpu, data_gpu)
            else:  # 'assign'
                # Direct assignment - last write wins
                result_gpu[indices_gpu] = data_gpu

            return cp.asnumpy(result_gpu)

        self._cupy_builtin_cache[cache_key] = scatter_wrapper
        op_desc = f"cp.{scatter_op}.at" if scatter_op != 'assign' else "advanced indexing"
        self._logger.info(
            f"LEVEL_4: Compiled {func_name} to {op_desc} (pattern=scatter, op={scatter_op})"
        )
        return scatter_wrapper

    def _try_stencil_kernel_compile(
        self,
        func: Callable,
        analysis: PatternAnalysis,
        func_name: str,
        cache_key: str
    ) -> Optional[Callable]:
        """
        Try to compile a stencil pattern to a CuPy RawKernel using StencilKernelCompiler.

        This is the LEVEL_4 enhancement that provides 100-1000x speedup by compiling
        2D stencil patterns (neighbor access loops) to CuPy RawKernel CUDA kernels
        instead of running Python for-loops with CuPy arrays.

        Args:
            func: The function to compile
            analysis: Pattern analysis results
            func_name: Name of the function for logging
            cache_key: Cache key for storing the compiled kernel

        Returns:
            GPU-accelerated wrapper function if compilation succeeds, None otherwise
        """
        import cupy as cp
        import numpy as np

        try:
            # GENERIC APPROACH: Compile directly from function's Python AST
            # This supports ANY user-defined stencil, not just predefined patterns
            compiled_kernel = self._stencil_kernel_compiler.compile_from_function(
                func=func,
                dtype=np.float64,
                block_size=(16, 16)
            )

            if compiled_kernel is not None:
                # Generic compilation succeeded
                self._stencil_kernel_cache[cache_key] = compiled_kernel
                self._logger.info(
                    f"LEVEL_4: Compiled {func_name} to CuPy RawKernel using generic AST-to-CUDA "
                    f"(compilation_time={compiled_kernel.compilation_time_ms:.2f}ms)"
                )
                return self._create_stencil_kernel_wrapper(compiled_kernel, func_name)

            # Generic compilation failed - DO NOT use function-name based fallbacks
            # The architecture requires pattern detection from AST, not function names.
            # If generic compilation fails, let CPU handle it.
            self._logger.debug(
                f"Generic AST compilation failed for {func_name}, "
                f"returning None (no function-name heuristic fallbacks)"
            )
            return None

        except StencilCompilationError as e:
            # Changed from debug to warning (Jan 2025 RCA) for visibility
            self._logger.warning(f"LEVEL_4 GPU: StencilKernelCompiler error for '{func_name}': {e}")
            return None
        except Exception as e:
            # Changed from debug to warning (Jan 2025 RCA) for visibility
            self._logger.warning(f"LEVEL_4 GPU: Stencil kernel compilation failed for '{func_name}': {e}")
            return None

    def _try_recursive_jit_compile(
        self,
        func: Callable,
        rejection_reason: Optional[str],
        func_name: str
    ) -> Optional[Callable]:
        """
        Try recursive function analysis when outer function is rejected.

        LEVEL_4 Enhancement: When outer function is rejected due to external
        function calls in loops, analyze those inner functions for GPU patterns.
        If inner functions are GPU-acceleratable, create a modified outer
        function that uses GPU-accelerated versions.

        Example:
            def run_spatial_iterations(F, iterations=10):
                for _ in range(iterations):
                    F = spatial_feature_step(F, gamma, beta, alpha)  # Stencil
                return F

            Without recursive: rejected due to external function call
            With recursive: spatial_feature_step compiled to GPU, 178x speedup

        Args:
            func: The rejected outer function
            rejection_reason: Why outer function was rejected
            func_name: Name of the function for logging

        Returns:
            GPU-accelerated wrapper if inner functions found, None otherwise
        """
        # Only attempt recursive analysis for external function call rejections
        if rejection_reason is None or 'External function call' not in rejection_reason:
            return None

        try:
            from ...jit.recursive_function_analyzer import (
                get_recursive_analyzer,
                create_gpu_accelerated_version,
            )

            # Analyze recursively for GPU-acceleratable inner functions
            analyzer = get_recursive_analyzer(max_depth=3)
            result = analyzer.analyze_recursively(func)

            if not result.has_gpu_candidates:
                self._logger.debug(
                    f"Recursive analysis found no GPU candidates in {func_name}"
                )
                return None

            # Log the candidates found
            for candidate in result.gpu_candidates:
                self._logger.info(
                    f"LEVEL_4 Recursive: Found GPU candidate '{candidate.function_name}' "
                    f"(pattern={candidate.pattern_type}, confidence={candidate.confidence:.2f})"
                )

            # Create GPU-accelerated version using closure substitution
            accelerated_func = create_gpu_accelerated_version(
                func,
                result.gpu_candidates
            )

            if accelerated_func is func:
                # No substitutions were made
                self._logger.debug(
                    f"Could not create GPU substitutions for {func_name}"
                )
                return None

            self._logger.info(
                f"LEVEL_4 Recursive: Created GPU-accelerated version of {func_name} "
                f"with {len(result.gpu_candidates)} inner function(s) accelerated"
            )

            # Mark as recursively accelerated
            accelerated_func._level4_recursive = True

            return accelerated_func

        except ImportError as e:
            self._logger.debug(f"Recursive analyzer not available: {e}")
            return None
        except Exception as e:
            self._logger.debug(f"Recursive JIT compilation failed for {func_name}: {e}")
            return None

    def _detect_operation_from_function(
        self,
        func: Callable,
        analysis: PatternAnalysis
    ) -> Optional[str]:
        """
        Detect the specific operation (square, sum, etc.) from a function.

        Uses function name heuristics and analysis info to determine the operation.

        Args:
            func: The function to analyze
            analysis: Pattern analysis results

        Returns:
            Operation name string if detected, None otherwise
        """
        func_name = getattr(func, '__name__', '').lower()

        # Map pattern operations (single-input element-wise)
        map_operations = {
            'square': ['square', 'sq', 'pow2', 'x2'],
            'negate': ['negate', 'neg', 'minus'],
            'abs': ['abs', 'absolute', 'fabs'],
        }

        # Map pattern operations (two-input element-wise)
        binary_operations = {
            'add': ['add', 'plus', 'sum_elementwise'],
            'multiply': ['multiply', 'mul', 'times', 'prod_elementwise'],
        }

        # Reduce pattern operations
        reduce_operations = {
            'sum': ['sum', 'total', 'accumulate'],
            'max': ['max', 'maximum'],
            'min': ['min', 'minimum'],
            'prod': ['prod', 'product'],
        }

        # Check against all operation types based on pattern type
        if analysis.pattern_type == 'map':
            for op, keywords in map_operations.items():
                if any(kw in func_name for kw in keywords):
                    return op
            for op, keywords in binary_operations.items():
                if any(kw in func_name for kw in keywords):
                    return op
            # Default to 'square' for generic map patterns (most common)
            if 'map' in func_name or analysis.pattern_type == 'map':
                return 'square'

        elif analysis.pattern_type == 'reduce':
            for op, keywords in reduce_operations.items():
                if any(kw in func_name for kw in keywords):
                    return op
            # Default to 'sum' for generic reduce patterns
            return 'sum'

        return None

    def _create_pattern_kernel_wrapper(
        self,
        kernel: PatternCompiledKernel,
        func_name: str
    ) -> Callable:
        """
        Create a callable wrapper for a PatternKernelCompiler-compiled kernel.

        Args:
            kernel: Compiled CuPy kernel from PatternKernelCompiler
            func_name: Original function name for the wrapper

        Returns:
            Wrapper function that executes the compiled CuPy kernel
        """
        import cupy as cp

        def pattern_kernel_wrapper(*args, **kwargs):
            """Execute the LEVEL_4 compiled CuPy kernel."""
            # Convert numpy arrays to CuPy arrays
            gpu_args = []
            for arg in args:
                if hasattr(arg, 'dtype') and hasattr(arg, 'shape'):
                    # Array-like: convert to CuPy
                    gpu_args.append(cp.asarray(arg))
                else:
                    # Scalar: pass through
                    gpu_args.append(arg)

            # Execute the kernel
            gpu_result = kernel.execute(*gpu_args)

            # Convert result back to numpy
            if hasattr(gpu_result, 'get'):
                return gpu_result.get()
            return gpu_result

        pattern_kernel_wrapper.__name__ = f"level4_gpu_{func_name}"
        pattern_kernel_wrapper._pattern_kernel = kernel
        pattern_kernel_wrapper._level4_accelerated = True
        return pattern_kernel_wrapper

    def _create_stencil_kernel_wrapper(
        self,
        kernel: CompiledStencilKernel,
        func_name: str
    ) -> Callable:
        """
        Create a callable wrapper for a StencilKernelCompiler-compiled kernel.

        Args:
            kernel: Compiled CuPy RawKernel stencil from StencilKernelCompiler
            func_name: Original function name for the wrapper

        Returns:
            Wrapper function that executes the compiled CUDA stencil kernel
        """
        import cupy as cp
        import numpy as np

        # Extract parameter names from the CUDA kernel code
        # The kernel has parameters: F_in, F_out, n_rows, n_cols, then scalar params
        # Parse from cuda_code to get parameter names
        cuda_code = kernel.cuda_code
        param_names = []
        if 'const double' in cuda_code or 'const float' in cuda_code:
            # Find parameter declarations after n_cols
            import re
            # Match parameter names from kernel signature
            match = re.search(r'\)\s*\{', cuda_code)
            if match:
                sig_end = match.start()
                sig_start = cuda_code.rfind('(', 0, sig_end)
                signature = cuda_code[sig_start+1:sig_end]
                # Extract scalar parameter names (after n_cols)
                parts = signature.split(',')
                for part in parts[4:]:  # Skip F_in, F_out, n_rows, n_cols
                    part = part.strip()
                    if part:
                        # Extract name from "const double name" or "const float name"
                        name_match = re.search(r'(\w+)\s*$', part)
                        if name_match:
                            param_names.append(name_match.group(1))

        def stencil_kernel_wrapper(F: np.ndarray, *args) -> np.ndarray:
            """
            Execute the LEVEL_4 compiled CuPy RawKernel stencil.

            This is a GENERIC wrapper that works with ANY user-defined stencil function.
            It dynamically handles scalar parameters based on the compiled kernel.

            Args:
                F: Input 2D array (n_rows x n_cols)
                *args: Scalar parameters matching the original function signature

            Returns:
                Output 2D array with stencil applied
            """
            # Convert to CuPy array if needed
            F_gpu = cp.asarray(F)

            # Allocate output
            F_out_gpu = cp.empty_like(F_gpu)

            # Get dimensions
            n_rows, n_cols = F.shape
            block_x, block_y = kernel.config.block_size
            grid_x = (n_cols + block_x - 1) // block_x
            grid_y = (n_rows + block_y - 1) // block_y

            # Build kernel arguments: F_in, F_out, n_rows, n_cols, then scalar params
            kernel_args = [F_gpu, F_out_gpu, np.int32(n_rows), np.int32(n_cols)]
            for arg in args:
                kernel_args.append(np.float64(arg))

            # Launch kernel
            kernel.kernel(
                (grid_x, grid_y),          # Grid dimensions
                (block_x, block_y),         # Block dimensions
                tuple(kernel_args)
            )

            # Return as numpy
            return cp.asnumpy(F_out_gpu)

        stencil_kernel_wrapper.__name__ = f"level4_stencil_{func_name}"
        stencil_kernel_wrapper._stencil_kernel = kernel
        stencil_kernel_wrapper._level4_stencil = True
        stencil_kernel_wrapper._param_names = param_names
        return stencil_kernel_wrapper

    def _create_kernel_wrapper(self, kernel: CompiledKernel) -> Callable:
        """
        Create a callable wrapper for a compiled kernel.

        Args:
            kernel: Compiled GPU kernel

        Returns:
            Wrapper function that executes the kernel
        """
        def kernel_wrapper(*args, **kwargs):
            """Execute the compiled GPU kernel."""
            if kernel.pattern_type == 'reduce':
                # Reduce patterns return a scalar
                arr = args[0]
                n = args[1] if len(args) > 1 else len(arr)
                return kernel.execute_reduce(arr, n)
            elif kernel.pattern_type == 'matmul':
                # Matmul patterns: (a, b, c) where c is output
                kernel.execute(*args)
                if len(args) >= 3:
                    return args[2]  # Return c (the result matrix)
                return args[0]
            elif kernel.pattern_type == 'transpose':
                # Transpose patterns: (input, output)
                kernel.execute(*args)
                if len(args) >= 2:
                    return args[1]  # Return output
                return args[0]
            else:
                # Stencil and map patterns modify arrays in-place
                kernel.execute(*args)
                # Return the output array (second positional arg for stencil/map)
                if len(args) >= 2:
                    return args[1]
                return args[0]

        kernel_wrapper.__name__ = f"gpu_{kernel.name}"
        kernel_wrapper._compiled_kernel = kernel
        return kernel_wrapper

    def get_jit_stats(self) -> Dict[str, Any]:
        """
        Get statistics about JIT-compiled kernels.

        Returns:
            Dictionary with JIT compilation statistics
        """
        stats = {
            'cached_kernels': len(self._jit_kernel_cache),
            'kernels_by_type': {},
            'kernel_details': []
        }

        for cache_key, kernel in self._jit_kernel_cache.items():
            pattern_type = kernel.pattern_type
            stats['kernels_by_type'][pattern_type] = stats['kernels_by_type'].get(pattern_type, 0) + 1
            stats['kernel_details'].append({
                'name': kernel.name,
                'pattern_type': pattern_type,
                'dimensions': kernel.dimensions
            })

        return stats

    def clear_jit_cache(self) -> None:
        """Clear the JIT kernel cache including detector and compiler caches."""
        self._jit_kernel_cache.clear()
        if self._kernel_compiler:
            self._kernel_compiler.clear_cache()
        if self._pattern_detector:
            self._pattern_detector.clear_cache()
        self._logger.info("JIT kernel cache cleared")
    
    def _estimate_data_size(self, args: tuple, kwargs: dict) -> int:
        """Estimate total data size involved in the operation."""
        total_size = 0
        
        # Estimate from positional arguments
        for arg in args:
            if hasattr(arg, 'nbytes'):
                total_size += arg.nbytes
            elif hasattr(arg, '__len__'):
                try:
                    import numpy as np
                    arr = np.asarray(arg)
                    total_size += arr.nbytes
                except Exception:
                    continue
        
        # Estimate from keyword arguments
        for value in kwargs.values():
            if hasattr(value, 'nbytes'):
                total_size += value.nbytes
            elif hasattr(value, '__len__'):
                try:
                    import numpy as np
                    arr = np.asarray(value)
                    total_size += arr.nbytes
                except Exception:
                    continue
        
        return total_size
    
    def _estimate_cpu_execution_time(self, request: GPUExecutionRequest) -> float:
        """Estimate how long this operation would take on CPU."""
        # Simple estimation based on data size and operation type
        data_size = self._estimate_data_size(request.args, request.kwargs)
        
        # Base estimate: 1 GB/second processing rate
        base_time = data_size / (1024**3)  # GB
        
        # Adjust based on function complexity
        func_name = getattr(request.func, '__name__', '').lower()
        
        # For lambda functions, try to inspect the code
        if func_name == '<lambda>':
            # Try to analyze the lambda's code
            import inspect
            try:
                source = inspect.getsource(request.func)
                # Look for operations in the source
                if 'matmul' in source or 'dot' in source:
                    complexity_factor = 10.0
                elif 'fft' in source or 'ifft' in source:
                    complexity_factor = 5.0
                elif 'sum' in source or 'mean' in source:
                    complexity_factor = 1.0
                else:
                    complexity_factor = 2.0
            except Exception:
                # If we can't inspect, use default
                complexity_factor = 2.0
        else:
            # Named functions
            if any(op in func_name for op in ['matmul', 'dot']):
                complexity_factor = 10.0  # Matrix operations are expensive
            elif any(op in func_name for op in ['fft', 'ifft']):
                complexity_factor = 5.0   # FFT is moderately expensive
            elif any(op in func_name for op in ['sum', 'mean']):
                complexity_factor = 1.0   # Reductions are simple
            else:
                complexity_factor = 2.0   # Default moderate complexity
        
        return base_time * complexity_factor
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get execution performance statistics."""
        with self._stats_lock:
            stats = self._execution_stats.copy()
        
        # Calculate derived metrics
        if stats['total_requests'] > 0:
            stats['gpu_usage_ratio'] = stats['gpu_executions'] / stats['total_requests']
            stats['fallback_ratio'] = stats['fallback_executions'] / stats['total_requests']
        else:
            stats['gpu_usage_ratio'] = 0.0
            stats['fallback_ratio'] = 0.0
        
        if stats['gpu_executions'] > 0:
            stats['avg_gpu_time'] = stats['total_gpu_time'] / stats['gpu_executions']
        else:
            stats['avg_gpu_time'] = 0.0
        
        if stats['cpu_executions'] > 0:
            stats['avg_cpu_time'] = stats['total_cpu_time'] / stats['cpu_executions']
        else:
            stats['avg_cpu_time'] = 0.0
        
        # Add GPU information
        stats['gpu_available'] = self._gpu_available
        stats['gpu_enabled'] = self._enabled
        
        if self._gpu_info:
            stats['gpu_info'] = {
                'device_name': self._gpu_info.device_name,
                'memory_total_gb': self._gpu_info.memory_total // (1024**3),
                'compute_capability': self._gpu_info.compute_capability
            }
        
        # Add CuPy manager stats if available
        if self._cupy_manager:
            cupy_stats = self._cupy_manager.get_performance_stats()
            stats['cupy_stats'] = cupy_stats
        
        return stats
    
    def is_gpu_available(self) -> bool:
        """Check if GPU acceleration is available."""
        return self._gpu_available and self._enabled
    
    def get_gpu_info(self) -> Optional[Dict[str, Any]]:
        """Get GPU hardware information."""
        if self._gpu_info:
            return {
                'device_name': self._gpu_info.device_name,
                'memory_total': self._gpu_info.memory_total,
                'memory_free': self._gpu_info.memory_free,
                'compute_capability': self._gpu_info.compute_capability,
                'cuda_version': self._gpu_info.cuda_version,
                'driver_version': self._gpu_info.driver_version
            }
        return None
    
    def update_config(self, config_updates: Dict[str, Any]) -> None:
        """Update executor configuration."""
        for key, value in config_updates.items():
            if key in self._config:
                self._config[key] = value
                self._logger.info(f"Updated GPU executor config: {key} = {value}")
            else:
                self._logger.warning(f"Unknown config key: {key}")
    
    def reset_stats(self) -> None:
        """Reset performance statistics."""
        with self._stats_lock:
            for key in self._execution_stats:
                if isinstance(self._execution_stats[key], (int, float)):
                    self._execution_stats[key] = 0 if isinstance(self._execution_stats[key], int) else 0.0
    
    def execute_optimized(self, code: str, optimization_plan: Dict[str, Any]) -> Any:
        """
        Execute optimized code according to the optimization plan.
        
        This method implements the abstract method from EpochlyExecutor base class.
        For GPU executor, this translates the optimization plan into a GPU execution request.
        
        Args:
            code: Optimized code to execute
            optimization_plan: Optimization strategy and parameters
            
        Returns:
            Execution result
        """
        # Extract execution parameters from optimization plan
        gpu_mode = optimization_plan.get('gpu_mode', GPUExecutionMode.AUTO)
        min_gpu_benefit = optimization_plan.get('min_gpu_benefit', 1.2)
        force_cpu_fallback = optimization_plan.get('force_cpu_fallback', True)
        
        # Extract function and arguments from the plan
        func = optimization_plan.get('function')
        args = optimization_plan.get('args', ())
        kwargs = optimization_plan.get('kwargs', {})
        
        if not func:
            # If no function provided, try to compile and execute the code string
            # This is a simplified implementation - in production, you'd use exec or compile
            namespace = {}
            exec(code, namespace)
            # Assume the code defines a function named 'optimized_function'
            func = namespace.get('optimized_function')
            if not func:
                raise ExecutionError("No executable function found in optimized code")
        
        # Create GPU execution request
        request = GPUExecutionRequest(
            func=func,
            args=args,
            kwargs=kwargs,
            gpu_mode=gpu_mode,
            min_gpu_benefit=min_gpu_benefit,
            force_cpu_fallback=force_cpu_fallback
        )
        
        # Execute using GPU executor logic
        result = self.execute_function(request)
        
        # Return the actual result value
        return result.result if hasattr(result, 'result') else result
    
    def supports_optimization(self, optimization_type: str) -> bool:
        """
        Check if executor supports a specific optimization type.
        
        This method implements the abstract method from EpochlyExecutor base class.
        
        Args:
            optimization_type: Type of optimization to check
            
        Returns:
            True if supported, False otherwise
        """
        # List of optimization types supported by GPU executor
        supported_types = {
            'gpu_acceleration',
            'cuda_kernels',
            'cupy_arrays',
            'tensor_operations',
            'matrix_multiplication',
            'parallel_computation',
            'vectorized_operations',
            'memory_coalescing',
            'gpu_memory_optimization',
            'hybrid_cpu_gpu',
            'auto_offloading',
            'transparent_gpu'
        }
        
        # Check if the optimization type is supported
        return optimization_type.lower() in supported_types