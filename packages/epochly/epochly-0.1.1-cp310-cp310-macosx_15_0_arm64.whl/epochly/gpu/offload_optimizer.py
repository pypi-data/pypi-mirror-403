"""
GPU Offload Optimizer

This module implements intelligent decision-making for GPU offloading,
including cost-benefit analysis, workload size thresholds, and automatic
data movement optimization.

Author: Epochly Development Team
"""

import time
import logging
import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

from .gpu_detector import GPUInfo, GPUDetector


@dataclass(frozen=True)
class ParallelismContext:
    """
    Context describing CPU parallelism capabilities for accurate GPU decision-making.

    When LEVEL_3 (multi-core parallelization) is active, CPU execution estimates
    must account for the speedup from parallelism. Without this context, the
    optimizer would compare GPU execution against single-core CPU estimates,
    leading to incorrect offload decisions.

    Attributes:
        level: Current enhancement level (0-4). Level 3+ enables parallelism.
        available_cores: Number of CPU cores available for parallel execution.
        level3_dispatch_overhead_ms: ProcessPool dispatch overhead in milliseconds.
            Default 100ms based on typical IPC overhead measurements.
    """
    level: int
    available_cores: int
    level3_dispatch_overhead_ms: float = 100.0


class OffloadDecision(Enum):
    """Decision outcomes for GPU offloading."""
    GPU_OFFLOAD = "gpu_offload"
    CPU_EXECUTE = "cpu_execute"
    ADAPTIVE_SPLIT = "adaptive_split"


@dataclass
class OffloadAnalysis:
    """Analysis result for offloading decision."""
    decision: OffloadDecision
    confidence: float  # 0.0 to 1.0
    estimated_speedup: float  # Expected speedup ratio
    estimated_overhead: float  # Transfer overhead in seconds
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationProfile:
    """Profile information for specific operations."""
    operation_name: str
    call_count: int = 0
    total_cpu_time: float = 0.0
    total_gpu_time: float = 0.0
    total_transfer_time: float = 0.0
    average_data_size: float = 0.0
    success_rate: float = 1.0
    last_updated: float = field(default_factory=time.time)


class GPUOffloadOptimizer:
    """
    Intelligent optimizer for GPU offloading decisions.

    This class analyzes workloads and makes intelligent decisions about
    when to offload operations to GPU based on:
    - Operation characteristics
    - Data size and transfer costs
    - Historical performance data
    - Current system state
    """

    # GPU must be at least 20% faster to account for estimation uncertainty.
    # Value 0.83 = 1/1.2, meaning GPU time must be <83% of CPU time.
    GPU_SAFETY_MARGIN = 0.83

    def __init__(self, gpu_info: GPUInfo, min_array_size: int = 10 * 1024 * 1024):
        """
        Initialize the offload optimizer.
        
        Args:
            gpu_info: Information about available GPU
            min_array_size: Minimum array size to consider for GPU (bytes)
        """
        self._gpu_info = gpu_info
        self._min_array_size = min_array_size
        self._logger = logging.getLogger(__name__)
        
        # Performance profiles for different operations
        self._operation_profiles: Dict[str, OperationProfile] = {}
        self._profiles_lock = threading.RLock()
        
        # Recent performance history for adaptive decisions
        self._performance_history: deque = deque(maxlen=1000)
        self._history_lock = threading.RLock()
        
        # Configuration parameters
        self._config = {
            'transfer_bandwidth_gbps': 12.0,  # PCIe bandwidth estimate
            'gpu_overhead_ms': 0.1,           # GPU kernel launch overhead
            'memory_threshold_ratio': 0.9,    # Don't use if GPU >90% full
            'adaptive_threshold': 0.8,        # Confidence threshold for adaptive decisions
            'learning_rate': 0.1,             # Learning rate for profile updates
            'profile_decay_hours': 24.0,      # Decay old profiles after 24h
        }
        
        # Operation-specific speedup estimates (these will be refined by learning)
        self._base_speedup_estimates = {
            'matmul': 15.0,
            'dot': 12.0,
            'tensordot': 10.0,
            'stencil': 10.0,      # JIT-compiled stencil patterns: high arithmetic intensity
            'fft': 8.0,
            'ifft': 8.0,
            'convolve': 6.0,
            'correlate': 6.0,
            'cumsum': 5.0,        # Scan/prefix sum patterns
            'cumprod': 5.0,       # Product scan patterns
            'sum': 4.0,
            'mean': 4.0,
            'std': 4.0,
            'var': 4.0,
            'add': 3.0,
            'subtract': 3.0,
            'multiply': 3.0,
            'divide': 3.0,
            'power': 3.5,
            'sqrt': 3.0,
            'sin': 2.5,
            'cos': 2.5,
            'exp': 2.5,
            'log': 2.5,
            'sort': 2.0,
            'argsort': 2.0,
        }

        # Parallelism efficiency factors for LEVEL_3 CPU parallelization.
        # These represent the fraction of ideal speedup achieved on multi-core CPU.
        # Example: 0.85 means 85% parallel efficiency (8 cores -> 6.8x speedup).
        # Based on empirical measurements from planning/EXECUTOR_SELECTION_ARCHITECTURE_THESIS.md
        self._parallelism_factors = {
            'matmul': 0.85,       # Highly parallelizable, cache-friendly
            'dot': 0.80,         # Good parallelism, some reduction overhead
            'tensordot': 0.80,   # Similar to dot product
            'stencil': 0.60,     # Cache conflicts due to neighbor access patterns
            'fft': 0.70,         # Parallelizable but communication-heavy
            'ifft': 0.70,        # Same as FFT
            'convolve': 0.75,    # Good data parallelism
            'correlate': 0.75,   # Similar to convolve
            'cumsum': 0.55,      # Scan has inherent serial dependency
            'cumprod': 0.55,     # Same as cumsum
            'sum': 0.65,         # Reduction overhead limits scaling
            'mean': 0.65,        # Same as sum
            'std': 0.60,         # Multiple passes, some serial dependencies
            'var': 0.60,         # Same as std
            'elementwise': 0.90, # Embarrassingly parallel
            'add': 0.90,         # Elementwise
            'subtract': 0.90,    # Elementwise
            'multiply': 0.90,    # Elementwise
            'divide': 0.90,      # Elementwise
            'power': 0.85,       # Elementwise but more compute
            'sqrt': 0.90,        # Elementwise
            'sin': 0.85,         # Transcendental, compute-bound
            'cos': 0.85,         # Transcendental, compute-bound
            'exp': 0.85,         # Transcendental, compute-bound
            'log': 0.85,         # Transcendental, compute-bound
            'sort': 0.50,        # Notoriously hard to parallelize efficiently
            'argsort': 0.50,     # Same as sort
        }

        # Initialize detector for current state checks
        self._detector = GPUDetector()
    
    def should_offload(self, data_size: int, operation: str,
                      additional_context: Optional[Dict[str, Any]] = None,
                      parallelism_context: Optional['ParallelismContext'] = None) -> bool:
        """
        Determine if an operation should be offloaded to GPU.

        Args:
            data_size: Total size of data involved in bytes
            operation: Name of the operation
            additional_context: Additional context for decision making
            parallelism_context: CPU parallelism context for accurate comparison.
                When provided, CPU execution estimates account for LEVEL_3
                parallelization speedup.

        Returns:
            True if operation should be offloaded to GPU
        """
        analysis = self.analyze_offload_opportunity(
            data_size, operation, additional_context, parallelism_context
        )
        return analysis.decision == OffloadDecision.GPU_OFFLOAD
    
    def analyze_offload_opportunity(self, data_size: int, operation: str,
                                  additional_context: Optional[Dict[str, Any]] = None,
                                  parallelism_context: Optional['ParallelismContext'] = None) -> OffloadAnalysis:
        """
        Perform comprehensive analysis of GPU offloading opportunity.

        Args:
            data_size: Total size of data involved in bytes
            operation: Name of the operation
            additional_context: Additional context for decision making
            parallelism_context: CPU parallelism context for accurate comparison.
                When provided, CPU execution estimates account for LEVEL_3
                parallelization speedup, ensuring fair GPU vs parallel-CPU comparison.

        Returns:
            OffloadAnalysis with decision and reasoning
        """
        if additional_context is None:
            additional_context = {}
        
        # Quick checks for obvious decisions
        if data_size < self._min_array_size:
            return OffloadAnalysis(
                decision=OffloadDecision.CPU_EXECUTE,
                confidence=0.9,
                estimated_speedup=1.0,
                estimated_overhead=0.0,
                reasoning=f"Data size {data_size // 1024}KB below minimum threshold {self._min_array_size // 1024}KB"
            )
        
        # Check GPU memory availability
        current_gpu_info = self._detector.get_gpu_info()
        memory_usage_ratio = 1.0 - (current_gpu_info.memory_free / current_gpu_info.memory_total)
        
        if memory_usage_ratio > self._config['memory_threshold_ratio']:
            return OffloadAnalysis(
                decision=OffloadDecision.CPU_EXECUTE,
                confidence=0.8,
                estimated_speedup=1.0,
                estimated_overhead=0.0,
                reasoning=f"GPU memory usage {memory_usage_ratio:.1%} exceeds threshold"
            )
        
        # Check if we have enough memory for the operation (need 2x for temporary arrays)
        required_memory = data_size * 2
        if current_gpu_info.memory_free < required_memory:
            return OffloadAnalysis(
                decision=OffloadDecision.CPU_EXECUTE,
                confidence=0.9,
                estimated_speedup=1.0,
                estimated_overhead=0.0,
                reasoning=f"Insufficient GPU memory: need {required_memory // (1024**2)}MB, have {current_gpu_info.memory_free // (1024**2)}MB"
            )
        
        # Get operation profile for historical performance
        operation_profile = self._get_operation_profile(operation)

        # Estimate transfer overhead
        transfer_overhead = self._estimate_transfer_overhead(data_size)

        # Estimate GPU speedup (vs single-core)
        estimated_speedup = self._estimate_gpu_speedup(operation, data_size, operation_profile)

        # Get single-core CPU estimate for GPU time calculation
        single_core_estimate = self._estimate_cpu_execution_time(operation, data_size, None)

        # Get parallelism-aware CPU estimate (already includes dispatch overhead)
        cpu_time_estimate = self._estimate_cpu_execution_time(
            operation, data_size, parallelism_context
        )

        # DIRECT TIME COMPARISON (critical for parallelism-aware decisions)
        # GPU total time = single_core / speedup + transfer_overhead
        # CPU total time = cpu_time_estimate (parallelized if context provided)
        gpu_total_time = (single_core_estimate / estimated_speedup) + transfer_overhead
        cpu_total_time = cpu_time_estimate

        # Build parallelism-aware reasoning suffix
        parallelism_info = ""
        if parallelism_context and parallelism_context.level >= 3:
            parallelism_info = f" (vs {parallelism_context.available_cores}-core LEVEL_3 parallel CPU)"

        # Make decision based on actual time comparison using safety margin
        if gpu_total_time < cpu_total_time * self.GPU_SAFETY_MARGIN:
            # GPU is significantly faster
            time_ratio = cpu_total_time / gpu_total_time
            confidence = min(0.9, time_ratio / 2.0)
            return OffloadAnalysis(
                decision=OffloadDecision.GPU_OFFLOAD,
                confidence=confidence,
                estimated_speedup=estimated_speedup,
                estimated_overhead=transfer_overhead,
                reasoning=f"GPU total {gpu_total_time*1000:.1f}ms < CPU total {cpu_total_time*1000:.1f}ms (speedup {time_ratio:.1f}x){parallelism_info}",
                metadata={
                    'operation_profile': operation_profile,
                    'data_size_mb': data_size / (1024**2),
                    'memory_usage_ratio': memory_usage_ratio,
                    'parallelism_context': parallelism_context,
                    'gpu_total_time_ms': gpu_total_time * 1000,
                    'cpu_total_time_ms': cpu_total_time * 1000
                }
            )
        elif gpu_total_time < cpu_total_time:
            # GPU is marginally faster - use adaptive decision
            if operation_profile and operation_profile.success_rate > self._config['adaptive_threshold']:
                return OffloadAnalysis(
                    decision=OffloadDecision.GPU_OFFLOAD,
                    confidence=0.6,
                    estimated_speedup=estimated_speedup,
                    estimated_overhead=transfer_overhead,
                    reasoning=f"Marginal GPU benefit ({gpu_total_time*1000:.1f}ms vs {cpu_total_time*1000:.1f}ms) but good historical success{parallelism_info}"
                )
            else:
                return OffloadAnalysis(
                    decision=OffloadDecision.CPU_EXECUTE,
                    confidence=0.7,
                    estimated_speedup=estimated_speedup,
                    estimated_overhead=transfer_overhead,
                    reasoning=f"Marginal GPU benefit ({gpu_total_time*1000:.1f}ms vs {cpu_total_time*1000:.1f}ms) with uncertain history{parallelism_info}"
                )
        else:
            # CPU is faster
            time_ratio = gpu_total_time / cpu_total_time
            return OffloadAnalysis(
                decision=OffloadDecision.CPU_EXECUTE,
                confidence=0.8,
                estimated_speedup=estimated_speedup,
                estimated_overhead=transfer_overhead,
                reasoning=f"CPU total {cpu_total_time*1000:.1f}ms < GPU total {gpu_total_time*1000:.1f}ms (GPU {time_ratio:.1f}x slower){parallelism_info}"
            )
    
    def should_return_to_cpu(self, result_size: Optional[int] = None) -> bool:
        """
        Determine if GPU results should be transferred back to CPU.
        
        Args:
            result_size: Size of result data in bytes
            
        Returns:
            True if result should be transferred to CPU
        """
        # Always return to CPU for NumPy compatibility to maintain NumPy compatibility
        # In the future, this could be more intelligent based on downstream operations
        return True
    
    def record_operation_performance(self, operation: str, data_size: int,
                                   cpu_time: Optional[float] = None,
                                   gpu_time: Optional[float] = None,
                                   transfer_time: Optional[float] = None,
                                   success: bool = True) -> None:
        """
        Record performance data for an operation to improve future decisions.
        
        Args:
            operation: Name of the operation
            data_size: Size of data processed
            cpu_time: Time taken on CPU (if executed on CPU)
            gpu_time: Time taken on GPU (if executed on GPU)
            transfer_time: Time taken for data transfers
            success: Whether the operation succeeded
        """
        with self._profiles_lock:
            if operation not in self._operation_profiles:
                self._operation_profiles[operation] = OperationProfile(operation_name=operation)
            
            profile = self._operation_profiles[operation]
            
            # Update profile with exponential moving average
            lr = self._config['learning_rate']
            
            profile.call_count += 1
            
            if cpu_time is not None:
                if profile.total_cpu_time == 0:
                    profile.total_cpu_time = cpu_time
                else:
                    profile.total_cpu_time = profile.total_cpu_time * (1 - lr) + cpu_time * lr
            
            if gpu_time is not None:
                if profile.total_gpu_time == 0:
                    profile.total_gpu_time = gpu_time
                else:
                    profile.total_gpu_time = profile.total_gpu_time * (1 - lr) + gpu_time * lr
            
            if transfer_time is not None:
                if profile.total_transfer_time == 0:
                    profile.total_transfer_time = transfer_time
                else:
                    profile.total_transfer_time = profile.total_transfer_time * (1 - lr) + transfer_time * lr
            
            # Update average data size
            if profile.average_data_size == 0:
                profile.average_data_size = data_size
            else:
                profile.average_data_size = profile.average_data_size * (1 - lr) + data_size * lr
            
            # Update success rate
            if success:
                profile.success_rate = profile.success_rate * (1 - lr) + 1.0 * lr
            else:
                profile.success_rate = profile.success_rate * (1 - lr) + 0.0 * lr
            
            profile.last_updated = time.time()
        
        # Record in performance history
        with self._history_lock:
            self._performance_history.append({
                'timestamp': time.time(),
                'operation': operation,
                'data_size': data_size,
                'cpu_time': cpu_time,
                'gpu_time': gpu_time,
                'transfer_time': transfer_time,
                'success': success
            })
    
    def _get_operation_profile(self, operation: str) -> Optional[OperationProfile]:
        """Get the performance profile for an operation."""
        with self._profiles_lock:
            profile = self._operation_profiles.get(operation)
            
            # Check if profile is stale
            if profile and (time.time() - profile.last_updated) > (self._config['profile_decay_hours'] * 3600):
                # Profile is stale, reduce its influence
                profile.success_rate *= 0.5
                profile.call_count = max(1, profile.call_count // 2)
            
            return profile
    
    def _estimate_transfer_overhead(self, data_size: int) -> float:
        """
        Estimate the overhead of transferring data to/from GPU.
        
        Args:
            data_size: Size of data in bytes
            
        Returns:
            Estimated transfer time in seconds
        """
        # Bidirectional transfer (to GPU and back to CPU)
        total_transfer = data_size * 2
        
        # Convert to GB and calculate transfer time
        transfer_gb = total_transfer / (1024**3)
        transfer_time = transfer_gb / self._config['transfer_bandwidth_gbps']
        
        # Add GPU kernel launch overhead
        overhead = self._config['gpu_overhead_ms'] / 1000.0
        
        return transfer_time + overhead
    
    def _estimate_gpu_speedup(self, operation: str, data_size: int, 
                            profile: Optional[OperationProfile]) -> float:
        """
        Estimate the speedup from GPU execution.
        
        Args:
            operation: Name of the operation
            data_size: Size of data in bytes
            profile: Historical performance profile
            
        Returns:
            Estimated speedup ratio
        """
        # Start with base estimate
        base_speedup = self._base_speedup_estimates.get(operation.lower(), 2.0)
        
        # Adjust based on data size (larger data generally benefits more)
        size_mb = data_size / (1024**2)
        if size_mb > 1000:      # >1GB
            size_factor = 1.3
        elif size_mb > 100:     # 100MB-1GB
            size_factor = 1.1
        elif size_mb > 50:      # 50-100MB
            size_factor = 1.0
        else:                   # 10-50MB
            size_factor = 0.8
        
        # Use historical data if available
        if profile and profile.total_gpu_time > 0 and profile.total_cpu_time > 0:
            historical_speedup = profile.total_cpu_time / profile.total_gpu_time
            # Blend base estimate with historical data
            estimated_speedup = (base_speedup * 0.3 + historical_speedup * 0.7) * size_factor
        else:
            estimated_speedup = base_speedup * size_factor
        
        # Account for GPU compute capability
        if self._gpu_info.compute_capability:
            major, minor = map(int, self._gpu_info.compute_capability.split('.'))
            if major >= 8:      # Ampere or newer
                compute_factor = 1.2
            elif major >= 7:    # Turing/Volta
                compute_factor = 1.1
            elif major >= 6:    # Pascal
                compute_factor = 1.0
            else:               # Older architectures
                compute_factor = 0.8
            
            estimated_speedup *= compute_factor
        
        return max(1.0, estimated_speedup)  # Never estimate worse than CPU
    
    def _estimate_cpu_execution_time(self, operation: str, data_size: int,
                                     parallelism_context: Optional['ParallelismContext'] = None) -> float:
        """
        Estimate CPU execution time for baseline comparison.

        When parallelism_context is provided and indicates LEVEL_3 or higher,
        the estimate accounts for multi-core CPU parallelization speedup.
        This ensures fair comparison: GPU vs parallelized CPU, not GPU vs single-core.

        Args:
            operation: Name of the operation
            data_size: Size of data in bytes
            parallelism_context: CPU parallelism context. If provided and level >= 3,
                estimate will be reduced by the parallelism speedup factor.

        Returns:
            Estimated CPU execution time in seconds
        """
        # Base complexity factors for single-core execution
        complexity_factors = {
            'matmul': 1e-6,      # O(n^3) operations
            'dot': 5e-7,         # O(n^2) operations
            'fft': 1e-7,         # O(n log n) operations
            'sum': 1e-8,         # O(n) operations
            'elementwise': 5e-9,  # Simple O(n) operations
        }

        # Categorize operation
        op_lower = operation.lower()
        if op_lower in ['matmul', 'dot', 'tensordot']:
            factor = complexity_factors['matmul']
            op_category = op_lower if op_lower in self._parallelism_factors else 'matmul'
        elif op_lower in ['fft', 'ifft']:
            factor = complexity_factors['fft']
            op_category = 'fft'
        elif op_lower in ['sum', 'mean', 'std', 'var']:
            factor = complexity_factors['sum']
            op_category = op_lower if op_lower in self._parallelism_factors else 'sum'
        else:
            factor = complexity_factors['elementwise']
            op_category = op_lower if op_lower in self._parallelism_factors else 'elementwise'

        # Calculate single-core estimate
        single_core_estimate = data_size * factor

        # Apply parallelism speedup if context indicates LEVEL_3+
        if parallelism_context and parallelism_context.level >= 3 and parallelism_context.available_cores > 1:
            # Get parallelism efficiency for this operation
            efficiency = self._parallelism_factors.get(op_category, 0.70)

            # Calculate effective speedup: cores * efficiency
            # Example: 8 cores * 0.85 efficiency = 6.8x speedup
            # Guard against division by zero with max(1.0, ...)
            effective_speedup = max(1.0, parallelism_context.available_cores * efficiency)

            # Apply ProcessPool dispatch overhead (convert ms to seconds)
            # This overhead is fixed per operation, so for fast operations it dominates
            # Guard against negative values
            dispatch_overhead = max(0.0, parallelism_context.level3_dispatch_overhead_ms / 1000.0)

            # Parallelized time = single_core / speedup + dispatch_overhead
            parallel_estimate = (single_core_estimate / effective_speedup) + dispatch_overhead

            # Don't return worse than single-core (if dispatch overhead dominates)
            return min(single_core_estimate, parallel_estimate)

        return single_core_estimate
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance profiles and recent history."""
        with self._profiles_lock:
            profiles_summary = {}
            for op_name, profile in self._operation_profiles.items():
                avg_cpu_time = profile.total_cpu_time if profile.call_count > 0 else 0
                avg_gpu_time = profile.total_gpu_time if profile.call_count > 0 else 0
                
                profiles_summary[op_name] = {
                    'call_count': profile.call_count,
                    'avg_cpu_time': avg_cpu_time,
                    'avg_gpu_time': avg_gpu_time,
                    'avg_transfer_time': profile.total_transfer_time,
                    'success_rate': profile.success_rate,
                    'avg_data_size_mb': profile.average_data_size / (1024**2),
                    'estimated_speedup': avg_cpu_time / avg_gpu_time if avg_gpu_time > 0 else 0
                }
        
        with self._history_lock:
            recent_operations = len(self._performance_history)
            gpu_operations = sum(1 for h in self._performance_history if h.get('gpu_time'))
            successful_operations = sum(1 for h in self._performance_history if h.get('success', True))
        
        return {
            'operation_profiles': profiles_summary,
            'recent_stats': {
                'total_operations': recent_operations,
                'gpu_operations': gpu_operations,
                'success_rate': successful_operations / max(1, recent_operations),
                'gpu_usage_rate': gpu_operations / max(1, recent_operations)
            },
            'config': self._config.copy()
        }
    
    def update_config(self, config_updates: Dict[str, Any]) -> None:
        """Update optimizer configuration."""
        for key, value in config_updates.items():
            if key in self._config:
                self._config[key] = value
                self._logger.info(f"Updated optimizer config: {key} = {value}")
            else:
                self._logger.warning(f"Unknown config key: {key}")
    
    def cleanup_stale_profiles(self) -> None:
        """Remove stale performance profiles."""
        current_time = time.time()
        decay_threshold = self._config['profile_decay_hours'] * 3600 * 2  # 2x decay time
        
        with self._profiles_lock:
            stale_operations = [
                op for op, profile in self._operation_profiles.items()
                if (current_time - profile.last_updated) > decay_threshold
            ]
            
            for op in stale_operations:
                del self._operation_profiles[op]
                self._logger.debug(f"Removed stale profile for operation: {op}")
        
        if stale_operations:
            self._logger.info(f"Cleaned up {len(stale_operations)} stale operation profiles")