"""
Epochly Workload Detection Analyzer

This module implements the WorkloadDetectionAnalyzer plugin that detects workload patterns
and characteristics for optimal pool selection and multicore distribution.

CRITICAL: This component is essential for Week 4 multicore capabilities, enabling
intelligent workload distribution across sub-interpreters.

MEM-5: Right-size retention buffers based on available RAM to reduce memory footprint.

Author: Epochly Development Team
"""

import os
import time
import threading
import psutil
import inspect
from typing import Dict, Any, List, Optional, Set, Callable
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import re

from ..base_plugins import EpochlyAnalyzer, create_analyzer_metadata, PluginPriority
from ...memory.workload_aware_pool import WorkloadType
from ...utils.exceptions import EpochlyError
from ...monitoring.hardware_counters import HardwareCounterManager, StatisticalSampler

# GPU detection import (optional - gracefully degrades without CuPy)
try:
    from ...gpu.gpu_detector import GPUDetector
except ImportError:
    GPUDetector = None

# PERFORMANCE OPTIMIZATION: Precompiled patterns for framework detection
COMPILED_PATTERNS = {
    'numpy': re.compile(r'\b(numpy|np\.|ndarray|array|vectorize|matmul|linalg)\b', re.IGNORECASE),
    'pandas': re.compile(r'\b(pandas|pd\.|DataFrame|Series|groupby|merge|pivot)\b', re.IGNORECASE),
    'sklearn': re.compile(r'\b(sklearn|fit|predict|transform|GridSearchCV|RandomForest)\b', re.IGNORECASE)
}


def _calculate_buffer_capacity(
    total_ram_bytes: int,
    sample_size_bytes: int,
    min_capacity: int,
    max_capacity: int,
    env_var_name: Optional[str] = None
) -> int:
    """
    Calculate buffer capacity based on available RAM.

    MEM-5 Implementation: Scale buffer size as (total_ram * 0.001 / sample_size),
    clamped to [min_capacity, max_capacity].

    Args:
        total_ram_bytes: Total system RAM in bytes
        sample_size_bytes: Estimated size per sample in bytes
        min_capacity: Minimum buffer capacity
        max_capacity: Maximum buffer capacity
        env_var_name: Optional environment variable override

    Returns:
        Buffer capacity (number of samples)
    """
    # Check for environment variable override first
    if env_var_name and env_var_name in os.environ:
        try:
            override_value = int(os.environ[env_var_name])
            # Still clamp to safe bounds
            return max(min_capacity, min(override_value, max_capacity))
        except (ValueError, TypeError):
            pass  # Fall through to calculated value

    # Calculate capacity: 0.1% of RAM divided by sample size
    # This ensures total buffer memory stays well under 1% of RAM
    ram_fraction = total_ram_bytes * 0.001  # 0.1% of RAM
    calculated_capacity = int(ram_fraction / sample_size_bytes)

    # Clamp to bounds
    return max(min_capacity, min(calculated_capacity, max_capacity))


def _get_memory_pressure() -> float:
    """
    Get current memory pressure as percentage (0.0-100.0).

    Returns:
        Memory pressure percentage
    """
    try:
        vmem = psutil.virtual_memory()
        return vmem.percent
    except Exception:
        return 0.0  # Assume no pressure if can't determine


class WorkloadCache:
    """LRU cache for workload analysis results."""

    def __init__(self, max_size: int = 512):
        self._cache = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        self._lock = threading.Lock()

    def get_signature(self, code: str, context: Dict[str, Any]) -> str:
        """Generate deterministic signature for workload."""
        # Include relevant context in signature
        sig_parts = [
            code,
            context.get('function_name', ''),
            str(context.get('size', 0))
        ]
        sig_str = '|'.join(sig_parts)
        # Use hash for more compact signature
        return str(hash(sig_str))

    def get_cached_analysis(self, signature: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached analysis result."""
        with self._lock:
            if signature in self._cache:
                self._hits += 1
                # Move to end (LRU behavior)
                result = self._cache.pop(signature)
                self._cache[signature] = result
                return result
            self._misses += 1
            return None

    def cache_analysis(self, signature: str, result: Dict[str, Any]):
        """Cache analysis result with LRU eviction."""
        with self._lock:
            if len(self._cache) >= self._max_size:
                # Remove oldest entry
                oldest = next(iter(self._cache))
                del self._cache[oldest]
            self._cache[signature] = result

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            return {
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': self._hits / total if total > 0 else 0.0,
                'size': len(self._cache)
            }


class WorkloadPattern(Enum):
    """Detected workload patterns for multicore distribution."""
    CPU_INTENSIVE = "cpu_intensive"
    MEMORY_INTENSIVE = "memory_intensive"
    IO_BOUND = "io_bound"
    MIXED = "mixed"
    PARALLEL_FRIENDLY = "parallel_friendly"
    SEQUENTIAL = "sequential"
    GPU_SUITABLE = "gpu_suitable"           # NEW: Suitable for GPU acceleration
    GPU_COMPUTE_INTENSIVE = "gpu_compute_intensive"  # NEW: Heavy compute workload for GPU
    GPU_MEMORY_BOUND = "gpu_memory_bound"   # NEW: Memory bandwidth limited
    # Framework-specific patterns
    NUMPY_VECTORIZED = "numpy_vectorized"   # NumPy array operations
    NUMPY_LINALG = "numpy_linalg"          # Linear algebra operations
    PANDAS_DATAFRAME = "pandas_dataframe"  # DataFrame operations
    PANDAS_GROUPBY = "pandas_groupby"      # GroupBy operations
    SKLEARN_TRAINING = "sklearn_training"  # Model training
    SKLEARN_INFERENCE = "sklearn_inference" # Model inference/prediction


@dataclass
class AllocationEvent:
    """Represents a memory allocation event for pattern analysis."""
    timestamp: float
    size: int
    thread_id: int
    allocation_type: str = "unknown"
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionMetrics:
    """Metrics for a single function execution (Task 1.3)."""
    timestamp: float
    wall_time: float  # Total elapsed time
    cpu_time: float   # CPU time consumed
    io_wait_time: float  # Time waiting for I/O
    memory_pressure: float = 0.0  # Memory pressure at execution time (0-100%)


@dataclass
class WorkloadCharacteristics:
    """Characteristics of detected workload for optimization decisions."""
    pattern: WorkloadPattern
    memory_intensity: float  # 0.0 to 1.0
    cpu_intensity: float     # 0.0 to 1.0
    parallelization_potential: float  # 0.0 to 1.0
    allocation_frequency: float  # allocations per second
    average_allocation_size: int
    thread_count: int
    confidence: float  # 0.0 to 1.0
    # Enhanced hardware characteristics
    l1_cache_miss_rate: float = 0.0  # Hardware counter data
    memory_pressure_indicator: float = 0.0  # Hardware counter data
    computational_intensity: float = 0.0  # Instructions per cycle
    sampling_overhead_us: float = 0.0  # Profiling overhead
    # NEW: GPU acceleration characteristics
    gpu_suitability: float = 0.0  # 0.0 to 1.0 - how suitable for GPU
    gpu_data_size_score: float = 0.0  # Based on typical array sizes
    gpu_operation_score: float = 0.0  # Based on operation types detected
    estimated_gpu_speedup: float = 1.0  # Estimated speedup ratio
    # Framework-specific characteristics
    numpy_array_count: int = 0  # Number of NumPy arrays detected
    numpy_operation_complexity: float = 0.0  # Complexity of NumPy operations
    pandas_dataframe_size: int = 0  # Size of DataFrames in bytes
    pandas_groupby_complexity: float = 0.0  # Complexity of GroupBy operations
    sklearn_model_complexity: float = 0.0  # Model training complexity
    framework_parallelization_score: float = 0.0  # Framework-specific parallel potential


@dataclass
class ThresholdLearningData:
    """Data for adaptive threshold learning."""
    pattern: WorkloadPattern
    predicted_score: float
    actual_performance: float
    threshold_used: float
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)


class AdaptiveThresholdManager:
    """Manages adaptive threshold learning for framework detection accuracy."""

    def __init__(self, learning_rate: float = 0.1, min_samples: int = 10):
        self.learning_rate = learning_rate
        self.min_samples = min_samples
        self.performance_history: Dict[str, List[ThresholdLearningData]] = defaultdict(list)
        self.current_thresholds = {
            'numpy': 0.1,
            'pandas': 0.1,
            'sklearn': 0.1,
            'gpu': 0.6
        }
        self.lock = threading.Lock()

        # PERFORMANCE OPTIMIZATION: Lazy threshold computation
        self._cached_thresholds = {
            'numpy': 0.1,
            'pandas': 0.1,
            'sklearn': 0.1,
            'gpu': 0.6
        }
        self._last_update_time = {}
        self._update_interval = 60.0  # Update at most once per minute
        self._update_scheduled = set()  # Frameworks scheduled for background update

    def record_performance(self, framework: str, predicted_score: float,
                          actual_performance: float, pattern: WorkloadPattern,
                          context: Dict[str, Any] = None):
        """Record performance feedback for threshold adaptation."""
        with self.lock:
            data = ThresholdLearningData(
                pattern=pattern,
                predicted_score=predicted_score,
                actual_performance=actual_performance,
                threshold_used=self.current_thresholds.get(framework, 0.1),
                timestamp=time.time(),
                context=context or {}
            )
            self.performance_history[framework].append(data)

            # Keep recent history (last 100 samples)
            if len(self.performance_history[framework]) > 100:
                self.performance_history[framework] = self.performance_history[framework][-100:]

            # Update threshold if we have enough samples
            if len(self.performance_history[framework]) >= self.min_samples:
                self._update_threshold(framework)

    def _update_threshold(self, framework: str):
        """Update threshold based on performance feedback using simple adaptive algorithm."""
        recent_data = self.performance_history[framework][-self.min_samples:]

        # Calculate success rate at current threshold
        successes = sum(1 for data in recent_data if data.actual_performance > 1.1)  # 10% improvement
        success_rate = successes / len(recent_data) if len(recent_data) > 0 else 0.0

        # Adjust threshold based on success rate
        if success_rate > 0.8:  # Too many false positives
            self.current_thresholds[framework] = min(0.5, self.current_thresholds[framework] + self.learning_rate)
        elif success_rate < 0.4:  # Too many false negatives
            self.current_thresholds[framework] = max(0.05, self.current_thresholds[framework] - self.learning_rate)

    def get_threshold(self, framework: str) -> float:
        """Get threshold with caching and lazy updates."""
        current_time = time.time()
        last_update = self._last_update_time.get(framework, 0)

        # Use cached value if recently updated
        if current_time - last_update < self._update_interval:
            return self._cached_thresholds.get(framework, 0.1)

        # Update threshold in background if needed
        if self._needs_update(framework) and framework not in self._update_scheduled:
            self._schedule_background_update(framework)

        return self._cached_thresholds.get(framework, 0.1)

    def _needs_update(self, framework: str) -> bool:
        """Check if framework threshold needs update."""
        with self.lock:
            history = self.performance_history.get(framework, [])
            return len(history) >= self.min_samples

    def _schedule_background_update(self, framework: str):
        """Schedule threshold update for the given framework.

        Updates are performed synchronously as async scheduling adds complexity
        without significant benefit for the current update frequency.
        """
        # Update synchronously (async not needed for this use case) but mark as updated
        self._update_scheduled.add(framework)
        if len(self.performance_history.get(framework, [])) >= self.min_samples:
            self._update_threshold(framework)
            self._last_update_time[framework] = time.time()
            self._cached_thresholds[framework] = self.current_thresholds[framework]
        self._update_scheduled.discard(framework)

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics for monitoring."""
        with self.lock:
            stats = {}
            for framework, history in self.performance_history.items():
                if history:
                    recent_performance = [d.actual_performance for d in history[-10:]]
                    stats[framework] = {
                        'threshold': self.current_thresholds.get(framework, 0.1),
                        'samples': len(history),
                        'avg_performance': statistics.mean(recent_performance) if recent_performance else 0.0,
                        'success_rate': sum(1 for p in recent_performance if p > 1.1) / len(recent_performance) if recent_performance else 0.0
                    }
            return stats


class WorkloadDetectionAnalyzer(EpochlyAnalyzer):
    """
    Analyzer plugin for detecting workload patterns and characteristics.

    This analyzer is critical for multicore workload distribution, providing
    the intelligence needed to distribute work across sub-interpreters effectively.

    MEM-5: Implements RAM-based buffer scaling to reduce memory footprint.
    """

    def __init__(self):
        metadata = create_analyzer_metadata(
            name="workload_detector",
            version="2.1.0",  # Version bump for MEM-5
            priority=PluginPriority.HIGH,
            capabilities=[
                "workload_pattern_detection",
                "memory_profiling",
                "parallelization_analysis",
                "multicore_distribution",
                "hardware_counter_profiling",
                "statistical_sampling",
                "framework_optimization",
                "numpy_detection",
                "pandas_optimization",
                "sklearn_acceleration",
                "dynamic_buffer_sizing"  # NEW: MEM-5 capability
            ]
        )
        super().__init__("workload_detector", "2.1.0", metadata)

        # MEM-5: Calculate dynamic allocation buffer capacity based on RAM
        try:
            vmem = psutil.virtual_memory()
            allocation_sample_size = 64  # bytes per AllocationEvent (conservative estimate)
            allocation_buffer_capacity = _calculate_buffer_capacity(
                total_ram_bytes=vmem.total,
                sample_size_bytes=allocation_sample_size,
                min_capacity=1000,
                max_capacity=100000,
                env_var_name='EPOCHLY_WORKLOAD_BUFFER_SIZE'
            )
        except Exception:
            # Fallback to safe default
            allocation_buffer_capacity = 10000

        # Analysis state with dynamic buffer sizing
        self._allocation_events: deque = deque(maxlen=allocation_buffer_capacity)
        self._thread_activity: Dict[int, List[float]] = defaultdict(list)
        self._analysis_window = 5.0  # seconds
        self._lock = threading.RLock()

        # MEM-5: Memory pressure monitoring for dynamic shrinking
        self._last_buffer_check = 0.0
        self._buffer_check_interval = 30.0  # Check every 30 seconds
        self._high_memory_pressure_threshold = 85.0  # Shrink at >85% RAM usage

        # Enhanced hardware profiling
        self._hardware_counter_manager: Optional[HardwareCounterManager] = None
        self._statistical_sampler: Optional[StatisticalSampler] = None
        self._hardware_profiling_enabled = False

        # NEW: GPU capability detection
        self._gpu_detector = None
        self._gpu_available = False
        self._gpu_info = None
        self._init_gpu_detection()

        # Pattern detection thresholds
        self._cpu_intensive_threshold = 0.7
        self._memory_intensive_threshold = 0.6
        self._parallel_threshold = 0.5
        self._gpu_suitability_threshold = 0.6  # NEW: GPU suitability threshold

        # NEW: Adaptive threshold management
        self._threshold_manager = AdaptiveThresholdManager()

        # Framework detection state
        self._framework_imports = set()  # Detected framework imports
        self._numpy_available = False
        self._pandas_available = False
        self._sklearn_available = False
        self._framework_activity = defaultdict(list)  # Per-framework operation tracking
        self._init_framework_detection()

        # PERFORMANCE OPTIMIZATION: Fast-path for non-framework workloads
        self._frameworks_in_environment = self._detect_available_frameworks()
        self._fast_path_enabled = True
        self._workload_cache = WorkloadCache(max_size=512)

        # TASK 1.3: Historical execution metrics tracking (perf_fixes3.md Section 5.2)
        # Store rolling averages by function signature for CPU intensity routing
        self._function_execution_history: Dict[str, deque] = {}  # func_sig -> deque of ExecutionMetrics
        self._max_history_per_function = 50  # Keep last 50 executions
        self._min_samples_for_confidence = 5  # Need 5+ samples for confident metrics
        self._execution_stats_lock = threading.RLock()  # Separate lock for execution stats

    # ============================================================================
    # TASK 1.3: Function Execution Tracking (perf_fixes3.md Section 5.2)
    # ============================================================================

    def record_execution(self,
                        func_signature: str,
                        wall_time: float,
                        cpu_time: float,
                        io_wait_time: float,
                        memory_pressure: Optional[float] = None) -> None:
        """
        Record execution metrics for a function signature.

        Per perf_fixes3.md Section 5.2: Track historical duration samples to enable
        metrics-based CPU intensity routing instead of size-only heuristics.

        Args:
            func_signature: Function signature (from generate_function_signature)
            wall_time: Wall clock time in seconds
            cpu_time: CPU time consumed in seconds
            io_wait_time: Time spent waiting for I/O in seconds
            memory_pressure: Memory pressure percentage (0-100), auto-detected if None

        Raises:
            ValueError: If times are negative or invalid
        """
        # Validate inputs
        if wall_time < 0:
            raise ValueError(f"wall_time must be >= 0, got {wall_time}")
        if cpu_time < 0:
            raise ValueError(f"cpu_time must be >= 0, got {cpu_time}")
        if io_wait_time < 0:
            raise ValueError(f"io_wait_time must be >= 0, got {io_wait_time}")

        # Auto-detect memory pressure if not provided
        if memory_pressure is None:
            memory_pressure = _get_memory_pressure()

        # Create metrics record
        metrics = ExecutionMetrics(
            timestamp=time.time(),
            wall_time=wall_time,
            cpu_time=cpu_time,
            io_wait_time=io_wait_time,
            memory_pressure=memory_pressure
        )

        # Store in history (thread-safe)
        with self._execution_stats_lock:
            if func_signature not in self._function_execution_history:
                self._function_execution_history[func_signature] = deque(
                    maxlen=self._max_history_per_function
                )

            self._function_execution_history[func_signature].append(metrics)

    def generate_function_signature(self, func: Callable) -> str:
        """
        Generate deterministic signature for a function.

        Args:
            func: Function object

        Returns:
            String signature including function name and parameter types
        """
        try:
            # Get function signature
            sig = inspect.signature(func)
            func_name = func.__name__

            # Build signature string: "func_name(param1: type1, param2: type2) -> return_type"
            params = []
            for param_name, param in sig.parameters.items():
                if param.annotation != inspect.Parameter.empty:
                    params.append(f"{param_name}: {param.annotation.__name__ if hasattr(param.annotation, '__name__') else str(param.annotation)}")
                else:
                    params.append(param_name)

            param_str = ", ".join(params)

            # Add return annotation if available
            if sig.return_annotation != inspect.Signature.empty:
                return_type = sig.return_annotation.__name__ if hasattr(sig.return_annotation, '__name__') else str(sig.return_annotation)
                return f"{func_name}({param_str}) -> {return_type}"
            else:
                return f"{func_name}({param_str})"

        except Exception:
            # Fallback to simple name
            return func.__name__ if hasattr(func, '__name__') else str(func)

    def get_function_stats(self, func_signature: str) -> Optional[Dict[str, Any]]:
        """
        Get execution statistics for a function signature.

        Args:
            func_signature: Function signature

        Returns:
            Dictionary with execution stats, or None if no data
        """
        with self._execution_stats_lock:
            if func_signature not in self._function_execution_history:
                return None

            history = self._function_execution_history[func_signature]
            if not history:
                return None

            # Calculate statistics from rolling window
            execution_count = len(history)

            # Calculate averages
            avg_wall_time = sum(m.wall_time for m in history) / execution_count
            avg_cpu_time = sum(m.cpu_time for m in history) / execution_count
            avg_io_wait_time = sum(m.io_wait_time for m in history) / execution_count
            avg_memory_pressure = sum(m.memory_pressure for m in history) / execution_count

            # Calculate confidence based on sample count
            confidence = min(execution_count / self._min_samples_for_confidence, 1.0)

            return {
                'execution_count': execution_count,
                'avg_wall_time': avg_wall_time,
                'avg_cpu_time': avg_cpu_time,
                'avg_io_wait_time': avg_io_wait_time,
                'avg_memory_pressure': avg_memory_pressure,
                'confidence': confidence
            }

    def get_cpu_intensity(self, func_signature: str) -> Optional[float]:
        """
        Get CPU intensity metric for a function.

        CPU intensity = cpu_time / wall_time (ratio of CPU usage)
        - High value (>0.8): CPU-bound workload
        - Low value (<0.2): I/O-bound or waiting workload

        Args:
            func_signature: Function signature

        Returns:
            CPU intensity (0.0-1.0), or None if no data
        """
        stats = self.get_function_stats(func_signature)
        if not stats:
            return None

        avg_wall_time = stats['avg_wall_time']
        avg_cpu_time = stats['avg_cpu_time']

        # Handle edge cases
        if avg_wall_time == 0.0:
            return None  # Cannot determine from instant execution

        # Calculate ratio, clamped to [0.0, 1.0]
        ratio = avg_cpu_time / avg_wall_time
        return min(max(ratio, 0.0), 1.0)

    def get_io_wait_ratio(self, func_signature: str) -> Optional[float]:
        """
        Get I/O wait ratio for a function.

        I/O wait ratio = io_wait_time / wall_time
        - High value (>0.8): I/O-bound workload
        - Low value (<0.1): CPU-bound workload

        Args:
            func_signature: Function signature

        Returns:
            I/O wait ratio (0.0-1.0), or None if no data
        """
        stats = self.get_function_stats(func_signature)
        if not stats:
            return None

        avg_wall_time = stats['avg_wall_time']
        avg_io_wait_time = stats['avg_io_wait_time']

        # Handle edge cases
        if avg_wall_time == 0.0:
            return None

        # Calculate ratio, clamped to [0.0, 1.0]
        ratio = avg_io_wait_time / avg_wall_time
        return min(max(ratio, 0.0), 1.0)

    def get_memory_pressure(self) -> float:
        """
        Get current system memory pressure.

        Returns:
            Memory pressure percentage (0.0-100.0)
        """
        return _get_memory_pressure()

    def peek(self, func_signature: str) -> Optional[Dict[str, Any]]:
        """
        Quick lookup of execution metrics without full analysis.

        Args:
            func_signature: Function signature

        Returns:
            Dictionary with metrics, or None if no data
        """
        stats = self.get_function_stats(func_signature)
        if not stats:
            return None

        return {
            'cpu_intensity': self.get_cpu_intensity(func_signature),
            'io_wait_ratio': self.get_io_wait_ratio(func_signature),
            'memory_pressure': stats['avg_memory_pressure'],
            'confidence': stats['confidence'],
            'sample_count': stats['execution_count']
        }

    def _merge_historical_metrics(self,
                                   static_characteristics: WorkloadCharacteristics,
                                   context: Dict[str, Any]) -> WorkloadCharacteristics:
        """
        Merge historical execution metrics with static analysis characteristics.

        Per Task 1.3: Historical data should override static analysis when available
        and confidence is high enough.

        Args:
            static_characteristics: Characteristics from static code analysis
            context: Analysis context (may contain function_name)

        Returns:
            Enhanced characteristics with historical data merged
        """
        # Try to get function signature from context
        func_name = context.get('function_name')
        if not func_name:
            # No function context - return static analysis only
            return static_characteristics

        # Look up historical metrics - try multiple signature formats
        historical_metrics = None

        # 1. Try exact match
        historical_metrics = self.peek(func_name)

        # 2. Try with empty parens
        if not historical_metrics:
            historical_metrics = self.peek(f"{func_name}()")

        # 3. Try fuzzy match - any signature starting with function name
        if not historical_metrics:
            with self._execution_stats_lock:
                for sig in self._function_execution_history.keys():
                    # Match signatures that start with function name
                    if sig.startswith(func_name + "("):
                        historical_metrics = self.peek(sig)
                        if historical_metrics:
                            break

        if not historical_metrics:
            # No historical data - return static analysis only
            return static_characteristics

        # Merge historical metrics with static analysis
        # Weight: 70% historical (if confident) + 30% static
        confidence = historical_metrics.get('confidence', 0.0)

        if confidence < 0.5:
            # Low confidence - prefer static analysis
            weight_historical = 0.3
            weight_static = 0.7
        else:
            # High confidence - prefer historical data
            weight_historical = 0.7
            weight_static = 0.3

        # Get historical values
        hist_cpu_intensity = historical_metrics.get('cpu_intensity', static_characteristics.cpu_intensity)
        hist_io_wait_ratio = historical_metrics.get('io_wait_ratio', 0.0)

        # Merge CPU intensity
        merged_cpu_intensity = (
            static_characteristics.cpu_intensity * weight_static +
            hist_cpu_intensity * weight_historical
        )

        # I/O-bound workloads have complementary relationship: high I/O wait means low CPU
        # Adjust CPU intensity down if historical I/O wait is high
        if hist_io_wait_ratio > 0.5:
            merged_cpu_intensity *= (1.0 - hist_io_wait_ratio * 0.5)

        # Create merged characteristics
        # Use dataclass replace to preserve other fields
        from dataclasses import replace

        merged = replace(
            static_characteristics,
            cpu_intensity=min(merged_cpu_intensity, 1.0),
            confidence=max(static_characteristics.confidence, confidence)
        )

        return merged

    # ============================================================================
    # End of Task 1.3 methods
    # ============================================================================

    def _check_and_adjust_buffers(self) -> None:
        """
        MEM-5: Check memory pressure and adjust buffers if needed.

        Called periodically to shrink buffers under high memory pressure (>85% RAM usage).
        """
        current_time = time.time()

        # Only check periodically
        if current_time - self._last_buffer_check < self._buffer_check_interval:
            return

        self._last_buffer_check = current_time

        # Check memory pressure
        memory_pressure = _get_memory_pressure()

        if memory_pressure > self._high_memory_pressure_threshold:
            # High memory pressure - shrink buffers by 50%
            with self._lock:
                current_capacity = self._allocation_events.maxlen
                new_capacity = max(1000, current_capacity // 2)  # Never go below minimum

                # Create new deque with smaller capacity, preserving recent data
                new_deque = deque(maxlen=new_capacity)
                # Copy most recent events
                for event in list(self._allocation_events)[-new_capacity:]:
                    new_deque.append(event)

                self._allocation_events = new_deque

                self._logger.info(
                    f"MEM-5: Shrunk allocation buffer due to memory pressure "
                    f"({memory_pressure:.1f}%): {current_capacity} -> {new_capacity}"
                )

    def _setup_plugin(self) -> None:
        """Setup workload detection resources with hardware profiling."""
        self._logger.info("Setting up enhanced workload detection analyzer with hardware profiling")
        self._allocation_events.clear()
        self._thread_activity.clear()

        # Initialize hardware profiling components
        try:
            # Initialize HardwareCounterManager for profiling
            self._hardware_counter_manager = HardwareCounterManager(sampling_frequency=10000)
            # Don't create StatisticalSampler as it creates another HardwareCounterManager
            self._statistical_sampler = None

            # Start hardware counter sampling
            self._hardware_counter_manager.start_sampling()
            self._hardware_profiling_enabled = True

            self._logger.info("Hardware profiling enabled with 10kHz sampling")

        except Exception as e:
            self._logger.warning(f"Hardware profiling unavailable, falling back to basic profiling: {e}")
            self._hardware_counter_manager = None
            self._statistical_sampler = None
            self._hardware_profiling_enabled = False

    def record_framework_performance_feedback(self, framework: str, predicted_score: float,
                                             actual_performance: float, pattern: WorkloadPattern,
                                             context: Dict[str, Any] = None):
        """Record performance feedback for adaptive threshold learning."""
        self._threshold_manager.record_performance(
            framework, predicted_score, actual_performance, pattern, context
        )
        self._logger.debug(f"Recorded performance feedback for {framework}: "
                          f"predicted={predicted_score:.3f}, actual={actual_performance:.3f}")

    def get_adaptive_threshold_stats(self) -> Dict[str, Any]:
        """Get statistics about adaptive threshold learning."""
        return self._threshold_manager.get_learning_stats()

    def __del__(self):
        """Ensure hardware counters stopped on garbage collection."""
        try:
            if hasattr(self, '_hardware_counter_manager') and self._hardware_counter_manager:
                self._hardware_counter_manager.stop_sampling()
        except:
            pass  # Best effort during GC

    def _teardown_plugin(self) -> None:
        """Teardown workload detection resources and hardware profiling."""
        self._logger.info("Tearing down enhanced workload detection analyzer")

        # Cleanup hardware profiling
        if self._statistical_sampler:
            self._statistical_sampler.cleanup()
            self._statistical_sampler = None

        if self._hardware_counter_manager:
            self._hardware_counter_manager.cleanup()
            self._hardware_counter_manager = None

        with self._lock:
            self._allocation_events.clear()
            self._thread_activity.clear()
            self._hardware_profiling_enabled = False

    def _init_gpu_detection(self) -> None:
        """Initialize GPU detection capabilities."""
        try:
            if GPUDetector is None:
                # GPU module not available (CuPy dependency missing)
                self._gpu_detector = None
                self._gpu_available = False
                self._gpu_info = None
                self._logger.debug("GPU module not available - GPU detection disabled")
                return

            self._gpu_detector = GPUDetector
            self._gpu_info = self._gpu_detector.get_gpu_info()
            self._gpu_available = self._gpu_detector.is_available()

            if self._gpu_available:
                self._logger.info(f"GPU acceleration available: {self._gpu_info.device_name}")
            else:
                self._logger.debug("No GPU acceleration available")

        except Exception as e:
            self._gpu_detector = None
            self._gpu_available = False
            self._gpu_info = None
            self._logger.warning(f"GPU detection initialization failed: {e}")

    def _init_framework_detection(self) -> None:
        """Initialize framework detection capabilities."""
        try:
            # Check NumPy availability
            try:
                import numpy
                self._numpy_available = True
                self._framework_imports.add('numpy')
                self._logger.debug("NumPy framework detected")
            except ImportError:
                pass

            # Check Pandas availability
            try:
                import pandas
                self._pandas_available = True
                self._framework_imports.add('pandas')
                self._logger.debug("Pandas framework detected")
            except ImportError:
                pass

            # Check scikit-learn availability
            try:
                import sklearn
                self._sklearn_available = True
                self._framework_imports.add('sklearn')
                self._logger.debug("scikit-learn framework detected")
            except ImportError:
                pass

            if self._framework_imports:
                self._logger.info(f"Framework optimization available for: {', '.join(self._framework_imports)}")
            else:
                self._logger.debug("No supported frameworks detected")

        except Exception as e:
            self._logger.warning(f"Framework detection initialization failed: {e}")

    def _detect_available_frameworks(self) -> Set[str]:
        """One-time detection of available frameworks for fast-path optimization"""
        frameworks = set()
        if self._numpy_available:
            frameworks.add('numpy')
        if self._pandas_available:
            frameworks.add('pandas')
        if self._sklearn_available:
            frameworks.add('sklearn')
        return frameworks

    def _contains_framework_indicators(self, code: str) -> bool:
        """Quick check for framework-specific patterns without full analysis"""
        if not self._frameworks_in_environment:
            return False

        # Use simple string checks, not full pattern matching
        code_lower = code.lower()

        # Quick indicators for each framework
        indicators = {
            'numpy': ['np.', 'numpy', 'array(', 'ndarray', 'vectorize', 'matmul'],
            'pandas': ['pd.', 'pandas', 'dataframe', 'series', 'groupby', '.merge('],
            'sklearn': ['sklearn', '.fit(', '.predict(', '.transform(', 'gridsearchcv']
        }

        for framework in self._frameworks_in_environment:
            if framework in indicators:
                if any(indicator in code_lower for indicator in indicators[framework]):
                    return True

        return False

    def analyze_code(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code for workload patterns and optimization opportunities.

        MEM-5: Periodically checks and adjusts buffers based on memory pressure.

        Args:
            code: Source code to analyze
            context: Analysis context and metadata

        Returns:
            Analysis results with workload characteristics
        """
        try:
            # MEM-5: Check and adjust buffers periodically
            self._check_and_adjust_buffers()

            # PERFORMANCE OPTIMIZATION: Check cache first
            cache_key = self._workload_cache.get_signature(code, context)
            cached_result = self._workload_cache.get_cached_analysis(cache_key)
            if cached_result is not None:
                return cached_result

            # FAST PATH: Skip framework detection if no frameworks available
            if self._fast_path_enabled and not self._frameworks_in_environment:
                characteristics = self._analyze_generic_workload(code, context)
            elif self._fast_path_enabled and not self._contains_framework_indicators(code):
                # No framework indicators found - use generic analysis
                characteristics = self._analyze_generic_workload(code, context)
            else:
                # Full analysis with framework detection
                characteristics = self._analyze_code_patterns(code, context)

            # TASK 1.3: Merge historical execution metrics with static analysis
            characteristics = self._merge_historical_metrics(characteristics, context)

            result = {
                "workload_type": characteristics.pattern.value,
                "characteristics": characteristics,
                "optimization_recommendations": self._generate_recommendations(characteristics),
                "multicore_suitability": characteristics.parallelization_potential,
                "confidence": characteristics.confidence
            }

            # Emit workload classification telemetry to AWS/Lens (GAP #3 fix)
            self._emit_workload_classification_telemetry(characteristics)

            # Cache result
            self._workload_cache.cache_analysis(cache_key, result)

            return result

        except Exception as e:
            self._logger.error(f"Code analysis failed: {e}")
            raise EpochlyError(f"Workload analysis failed: {e}")

    def _analyze_generic_workload(self, code: str, context: Dict[str, Any]) -> WorkloadCharacteristics:
        """Fast generic workload analysis without framework detection overhead"""
        # Basic pattern detection without framework-specific analysis
        cpu_indicators = ["for", "while", "range", "calculation", "compute"]
        memory_indicators = ["array", "list", "dict", "allocate", "buffer"]
        parallel_indicators = ["multiprocessing", "threading", "concurrent", "async"]

        code_lower = code.lower()
        cpu_score = sum(1 for ind in cpu_indicators if ind in code_lower)
        memory_score = sum(1 for ind in memory_indicators if ind in code_lower)
        parallel_score = sum(1 for ind in parallel_indicators if ind in code_lower)

        cpu_intensity = min(cpu_score / len(cpu_indicators), 1.0) if len(cpu_indicators) > 0 else 0.0
        memory_intensity = min(memory_score / len(memory_indicators), 1.0) if len(memory_indicators) > 0 else 0.0
        parallelization_potential = min(parallel_score / len(parallel_indicators), 1.0) if len(parallel_indicators) > 0 else 0.0

        # Determine pattern without framework analysis
        if parallelization_potential > 0.6:
            pattern = WorkloadPattern.PARALLEL_FRIENDLY
        elif cpu_intensity > 0.7:
            pattern = WorkloadPattern.CPU_INTENSIVE
        elif memory_intensity > 0.6:
            pattern = WorkloadPattern.MEMORY_INTENSIVE
        else:
            pattern = WorkloadPattern.MIXED

        return WorkloadCharacteristics(
            pattern=pattern,
            memory_intensity=memory_intensity,
            cpu_intensity=cpu_intensity,
            parallelization_potential=parallelization_potential,
            allocation_frequency=0.0,
            average_allocation_size=0,
            thread_count=1,
            confidence=0.7,  # Lower confidence for generic analysis
            # No framework-specific characteristics
            numpy_operation_complexity=0.0,
            pandas_groupby_complexity=0.0,
            sklearn_model_complexity=0.0,
            framework_parallelization_score=0.0
        )

    def _quick_framework_score(self, code: str, framework: str) -> float:
        """Fast pattern scoring using precompiled regex"""
        if framework not in COMPILED_PATTERNS:
            return 0.0

        matches = len(COMPILED_PATTERNS[framework].findall(code))
        # Simple scoring: more matches = higher score
        return min(matches / 10.0, 1.0)

    def analyze_runtime(self, runtime_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze runtime behavior for workload characteristics.

        Args:
            runtime_data: Runtime performance and behavior data

        Returns:
            Runtime analysis results with workload patterns
        """
        try:
            # MEM-5: Check and adjust buffers periodically
            self._check_and_adjust_buffers()

            # Record allocation events
            if "allocation_events" in runtime_data:
                self._record_allocation_events(runtime_data["allocation_events"])

            # Analyze current workload characteristics
            characteristics = self._analyze_runtime_patterns()

            return {
                "current_workload": characteristics.pattern.value,
                "characteristics": characteristics,
                "distribution_strategy": self._recommend_distribution_strategy(characteristics),
                "pool_recommendation": self._recommend_memory_pool(characteristics),
                "analysis_timestamp": time.time()
            }

        except Exception as e:
            self._logger.error(f"Runtime analysis failed: {e}")
            raise EpochlyError(f"Runtime analysis failed: {e}")

    def _analyze_code_patterns(self, code: str, context: Dict[str, Any]) -> WorkloadCharacteristics:
        """Enhanced code analysis for workload patterns with parallelization detection."""
        # Enhanced indicators with parallelization focus
        cpu_indicators = [
            "for", "while", "range", "numpy", "scipy", "math",
            "calculation", "compute", "algorithm", "sum", "prod",
            "dot", "matmul", "fft", "linalg"
        ]

        memory_indicators = [
            "array", "list", "dict", "pandas", "DataFrame",
            "allocate", "buffer", "cache", "append", "extend"
        ]

        parallel_indicators = [
            "multiprocessing", "threading", "concurrent", "async",
            "parallel", "pool", "worker", "chunk", "batch",
            "ProcessPoolExecutor", "ThreadPoolExecutor"
        ]

        # NEW: Detect embarrassingly parallel patterns
        embarrassingly_parallel_indicators = [
            "workload", "benchmark", "intensive", "chunk_workload",
            "map", "apply", "vectorize", "broadcast"
        ]

        # NEW: Detect sequential bottlenecks
        sequential_indicators = [
            "global", "nonlocal", "lock", "mutex", "synchronized",
            "sequential", "ordered", "dependencies"
        ]

        # NEW: GPU-suitable operation indicators
        gpu_operation_indicators = [
            "matmul", "dot", "tensordot", "@",  # Matrix operations
            "fft", "ifft", "rfft",              # FFT operations
            "convolve", "correlate",            # Convolution
            "sum", "mean", "std", "var",        # Reductions
            "sin", "cos", "exp", "log",         # Math functions
            "sqrt", "power", "**",              # Power operations
            "add", "subtract", "multiply",      # Element-wise ops
            "divide", "/", "*", "+", "-",
            "linalg", "linear_algebra",         # Linear algebra
            "array", "asarray", "zeros",        # Array creation
            "ones", "empty", "full"
        ]

        # Framework-specific operation indicators
        numpy_indicators = [
            "numpy", "np.", "ndarray", "array", "matrix", "vectorize",
            "broadcast", "ufunc", "dot", "matmul", "linalg", "fft",
            "sum", "mean", "std", "var", "min", "max", "argmax", "argmin",
            "reshape", "transpose", "concatenate", "stack", "split"
        ]

        pandas_indicators = [
            "pandas", "pd.", "DataFrame", "Series", "groupby", "apply",
            "agg", "transform", "merge", "join", "concat", "pivot",
            "melt", "query", "eval", "rolling", "resample", "sort_values"
        ]

        sklearn_indicators = [
            "sklearn", "fit", "predict", "transform", "score", "cross_val",
            "GridSearchCV", "RandomizedSearchCV", "Pipeline", "FeatureUnion",
            "train_test_split", "classification", "regression", "clustering",
            "preprocessing", "model_selection", "metrics", "ensemble"
        ]

        # Large data indicators
        large_data_indicators = [
            "reshape", "resize", "huge", "large",
            "gigabyte", "GB", "million", "billion",
            "1e6", "1e9", "1024", "megabyte", "MB"
        ]

        # Count indicators with function name analysis
        function_name = context.get('function_name', '')

        cpu_score = sum(1 for indicator in cpu_indicators if indicator in code.lower())
        memory_score = sum(1 for indicator in memory_indicators if indicator in code.lower())
        parallel_score = sum(1 for indicator in parallel_indicators if indicator in code.lower())

        # NEW: GPU scoring
        gpu_op_score = sum(1 for indicator in gpu_operation_indicators
                          if indicator in code.lower() or indicator in function_name.lower())
        large_data_score = sum(1 for indicator in large_data_indicators if indicator in code.lower())

        # NEW: Enhanced parallelization scoring
        embarrassing_parallel_score = sum(1 for indicator in embarrassingly_parallel_indicators
                                         if indicator in code.lower() or indicator in function_name.lower())
        sequential_score = sum(1 for indicator in sequential_indicators if indicator in code.lower())

        # PERFORMANCE OPTIMIZATION: Use fast precompiled pattern scoring
        numpy_score = 0
        pandas_score = 0
        sklearn_score = 0

        # Calculate framework scores (always for static code analysis)
        # Tests verify pattern detection works even without frameworks installed
        numpy_score = self._quick_framework_score(code, 'numpy') * len(numpy_indicators)
        pandas_score = self._quick_framework_score(code, 'pandas') * len(pandas_indicators)
        sklearn_score = self._quick_framework_score(code, 'sklearn') * len(sklearn_indicators)

        # NEW: AST-based loop analysis for chunking potential
        loop_analysis = self._analyze_loops_for_chunking(code)

        # Enhanced scoring with parallelization focus
        cpu_intensity = min(cpu_score / len(cpu_indicators), 1.0) if len(cpu_indicators) > 0 else 0.0
        memory_intensity = min(memory_score / len(memory_indicators), 1.0) if len(memory_indicators) > 0 else 0.0

        # Enhanced parallelization potential calculation
        base_parallel_score = min(parallel_score / len(parallel_indicators), 1.0) if len(parallel_indicators) > 0 else 0.0
        embarrassing_bonus = min(embarrassing_parallel_score * 0.3, 0.7)  # Up to 70% bonus
        sequential_penalty = min(sequential_score * 0.2, 0.5)  # Up to 50% penalty
        loop_bonus = loop_analysis['chunking_potential'] * 0.4  # Up to 40% bonus

        parallelization_potential = min(
            base_parallel_score + embarrassing_bonus + loop_bonus - sequential_penalty,
            1.0
        )

        # NEW: Calculate GPU characteristics
        gpu_operation_score = min(gpu_op_score / len(gpu_operation_indicators), 1.0) if len(gpu_operation_indicators) > 0 else 0.0
        gpu_data_size_score = min(large_data_score / len(large_data_indicators), 1.0) if len(large_data_indicators) > 0 else 0.0
        gpu_suitability = self._calculate_gpu_suitability(gpu_operation_score, gpu_data_size_score, cpu_intensity)
        estimated_gpu_speedup = self._estimate_gpu_speedup_from_static(gpu_operation_score, gpu_data_size_score)

        # NEW: Calculate framework-specific characteristics
        # Allow detection even without frameworks for testing, but mark as lower confidence
        numpy_operation_score = min(numpy_score / max(len(numpy_indicators), 1), 1.0)
        pandas_operation_score = min(pandas_score / max(len(pandas_indicators), 1), 1.0)
        sklearn_operation_score = min(sklearn_score / max(len(sklearn_indicators), 1), 1.0)

        # Reduce confidence if frameworks not available
        framework_confidence_penalty = 1.0
        if not self._numpy_available and numpy_operation_score > 0:
            framework_confidence_penalty *= 0.7
        if not self._pandas_available and pandas_operation_score > 0:
            framework_confidence_penalty *= 0.7
        if not self._sklearn_available and sklearn_operation_score > 0:
            framework_confidence_penalty *= 0.7

        # Framework-specific pattern detection with adaptive thresholds
        framework_pattern = None
        sklearn_threshold = self._threshold_manager.get_threshold('sklearn')
        pandas_threshold = self._threshold_manager.get_threshold('pandas')
        numpy_threshold = self._threshold_manager.get_threshold('numpy')

        # WINDOWS 3.8 FIX: Lower thresholds for static analysis when frameworks not installed
        # Enables pattern detection in test environments without runtime frameworks
        effective_sklearn_threshold = sklearn_threshold if self._sklearn_available else sklearn_threshold * 0.5
        effective_pandas_threshold = pandas_threshold if self._pandas_available else pandas_threshold * 0.5
        effective_numpy_threshold = numpy_threshold if self._numpy_available else numpy_threshold * 0.5

        if sklearn_operation_score > effective_sklearn_threshold:
            if any(indicator in code.lower() for indicator in ["fit", "train", "gridsearchcv", "cross_val"]):
                framework_pattern = WorkloadPattern.SKLEARN_TRAINING
            else:
                framework_pattern = WorkloadPattern.SKLEARN_INFERENCE
        elif pandas_operation_score > effective_pandas_threshold:
            if any(indicator in code.lower() for indicator in ["groupby", "agg", "transform"]):
                framework_pattern = WorkloadPattern.PANDAS_GROUPBY
            else:
                framework_pattern = WorkloadPattern.PANDAS_DATAFRAME
        elif numpy_operation_score > effective_numpy_threshold:
            if any(indicator in code.lower() for indicator in ["linalg", "dot", "matmul", "tensordot"]):
                framework_pattern = WorkloadPattern.NUMPY_LINALG
            else:
                framework_pattern = WorkloadPattern.NUMPY_VECTORIZED

        # NEW: Determine primary pattern with framework preference
        if framework_pattern is not None:
            pattern = framework_pattern
        elif self._gpu_available and gpu_suitability > self._gpu_suitability_threshold:
            if gpu_operation_score > 0.7 and cpu_intensity > 0.6:
                pattern = WorkloadPattern.GPU_COMPUTE_INTENSIVE
            elif gpu_data_size_score > 0.5 and memory_intensity > 0.5:
                pattern = WorkloadPattern.GPU_MEMORY_BOUND
            else:
                pattern = WorkloadPattern.GPU_SUITABLE
        elif embarrassing_parallel_score > 0 or parallelization_potential > 0.6:
            pattern = WorkloadPattern.PARALLEL_FRIENDLY
        elif cpu_intensity > self._cpu_intensive_threshold:
            pattern = WorkloadPattern.CPU_INTENSIVE
        elif memory_intensity > self._memory_intensive_threshold:
            pattern = WorkloadPattern.MEMORY_INTENSIVE
        elif sequential_score > 2:
            pattern = WorkloadPattern.SEQUENTIAL
        else:
            pattern = WorkloadPattern.MIXED

        return WorkloadCharacteristics(
            pattern=pattern,
            memory_intensity=memory_intensity,
            cpu_intensity=cpu_intensity,
            parallelization_potential=max(parallelization_potential, 0.0),
            allocation_frequency=0.0,  # Unknown from static analysis
            average_allocation_size=0,
            thread_count=1,  # Assume single-threaded for static analysis
            confidence=0.8 * framework_confidence_penalty,  # Higher confidence with enhanced analysis, reduced if frameworks missing
            # Hardware characteristics unknown for static analysis
            l1_cache_miss_rate=0.0,
            memory_pressure_indicator=0.0,
            computational_intensity=0.0,
            sampling_overhead_us=0.0,
            # NEW: GPU characteristics from static analysis
            gpu_suitability=gpu_suitability,
            gpu_data_size_score=gpu_data_size_score,
            gpu_operation_score=gpu_operation_score,
            estimated_gpu_speedup=estimated_gpu_speedup,
            # Framework-specific characteristics
            numpy_array_count=numpy_score,  # Use score as proxy for array count
            numpy_operation_complexity=numpy_operation_score,
            pandas_dataframe_size=0,  # Unknown from static analysis
            pandas_groupby_complexity=pandas_operation_score,
            sklearn_model_complexity=sklearn_operation_score,
            framework_parallelization_score=max(numpy_operation_score, pandas_operation_score, sklearn_operation_score)
        )

    def _analyze_runtime_patterns(self) -> WorkloadCharacteristics:
        """Enhanced runtime analysis with hardware counter integration."""
        with self._lock:
            # Get hardware profiling data if available
            hardware_characteristics = self._get_hardware_characteristics()

            if not self._allocation_events:
                # Return hardware-enhanced default characteristics
                base_characteristics = WorkloadCharacteristics(
                    pattern=WorkloadPattern.MIXED,
                    memory_intensity=0.5,
                    cpu_intensity=0.5,
                    parallelization_potential=0.5,
                    allocation_frequency=0.0,
                    average_allocation_size=0,
                    thread_count=1,
                    confidence=0.1 if not hardware_characteristics else 0.3
                )
                # Merge with hardware data
                return self._merge_hardware_characteristics(base_characteristics, hardware_characteristics)

            # Analyze recent events within time window
            current_time = time.time()
            recent_events = [
                event for event in self._allocation_events
                if current_time - event.timestamp <= self._analysis_window
            ]

            if not recent_events:
                return self._get_default_characteristics()

            # Calculate metrics
            allocation_frequency = len(recent_events) / self._analysis_window if self._analysis_window > 0 else 0.0
            average_size = sum(event.size for event in recent_events) / len(recent_events) if len(recent_events) > 0 else 0
            thread_count = len(set(event.thread_id for event in recent_events))

            # Analyze allocation patterns
            memory_intensity = self._calculate_memory_intensity(recent_events)
            cpu_intensity = self._calculate_cpu_intensity(recent_events)
            parallelization_potential = self._calculate_parallelization_potential(recent_events)

            # Determine workload pattern
            pattern = self._determine_workload_pattern(
                memory_intensity, cpu_intensity, parallelization_potential
            )

            base_characteristics = WorkloadCharacteristics(
                pattern=pattern,
                memory_intensity=memory_intensity,
                cpu_intensity=cpu_intensity,
                parallelization_potential=parallelization_potential,
                allocation_frequency=allocation_frequency,
                average_allocation_size=int(average_size),
                thread_count=thread_count,
                confidence=0.8 if not hardware_characteristics else 0.9  # Higher confidence with hardware data
            )

            # Enhanced analysis with hardware counter integration
            return self._merge_hardware_characteristics(base_characteristics, hardware_characteristics)

    def _record_allocation_events(self, events: List[Dict[str, Any]]) -> None:
        """Record allocation events for pattern analysis."""
        with self._lock:
            for event_data in events:
                event = AllocationEvent(
                    timestamp=event_data.get("timestamp", time.time()),
                    size=event_data.get("size", 0),
                    thread_id=event_data.get("thread_id", threading.get_ident()),
                    allocation_type=event_data.get("type", "unknown"),
                    context=event_data.get("context", {})
                )
                self._allocation_events.append(event)

    def _calculate_memory_intensity(self, events: List[AllocationEvent]) -> float:
        """Calculate memory intensity based on allocation patterns."""
        if not events:
            return 0.0

        # Large allocations indicate memory-intensive workload
        large_allocation_threshold = 1024 * 1024  # 1MB
        large_allocations = sum(1 for event in events if event.size > large_allocation_threshold)

        return min(large_allocations / len(events) * 2.0, 1.0)

    def _calculate_cpu_intensity(self, events: List[AllocationEvent]) -> float:
        """Calculate CPU intensity based on allocation frequency."""
        if not events:
            return 0.0

        # High frequency allocations often indicate CPU-intensive work
        frequency = len(events) / self._analysis_window
        high_frequency_threshold = 100  # allocations per second

        return min(frequency / high_frequency_threshold, 1.0)

    def _calculate_parallelization_potential(self, events: List[AllocationEvent]) -> float:
        """Calculate parallelization potential based on thread activity."""
        if not events:
            return 0.0

        thread_count = len(set(event.thread_id for event in events))

        # More threads indicate higher parallelization potential
        if thread_count == 1:
            return 0.2  # Low potential for single-threaded
        elif thread_count <= 4:
            return 0.6  # Medium potential
        else:
            return 0.9  # High potential for many threads

    def _determine_workload_pattern(
        self, memory_intensity: float, cpu_intensity: float, parallelization_potential: float
    ) -> WorkloadPattern:
        """Determine the primary workload pattern with enhanced logic."""
        # Prioritize parallel-friendly detection
        if parallelization_potential > 0.6:  # Lower threshold for better detection
            return WorkloadPattern.PARALLEL_FRIENDLY
        elif parallelization_potential > self._parallel_threshold and (cpu_intensity > 0.4 or memory_intensity > 0.4):
            return WorkloadPattern.PARALLEL_FRIENDLY
        elif memory_intensity > self._memory_intensive_threshold:
            return WorkloadPattern.MEMORY_INTENSIVE
        elif cpu_intensity > self._cpu_intensive_threshold:
            return WorkloadPattern.CPU_INTENSIVE
        elif parallelization_potential < 0.2:  # Very low parallelization potential
            return WorkloadPattern.SEQUENTIAL
        else:
            return WorkloadPattern.MIXED

    def _generate_recommendations(self, characteristics: WorkloadCharacteristics) -> List[str]:
        """Generate optimization recommendations based on workload characteristics."""
        recommendations = []

        if characteristics.parallelization_potential > 0.7:
            recommendations.append("Enable sub-interpreter parallelization")
            recommendations.append("Use multicore workload distribution")

            # Hardware-specific recommendations
            if hasattr(characteristics, 'sampling_overhead_us') and characteristics.sampling_overhead_us < 1.8:
                recommendations.append("Hardware profiling overhead is optimal (<1.8μs target)")

            if hasattr(characteristics, 'l1_cache_miss_rate') and characteristics.l1_cache_miss_rate > 0.1:
                recommendations.append("Consider NUMA-aware memory allocation for cache optimization")

        if characteristics.memory_intensity > 0.7:
            recommendations.append("Use memory-optimized pool configuration")
            recommendations.append("Enable large block allocation strategies")

        if characteristics.cpu_intensity > 0.7:
            recommendations.append("Enable JIT compilation")
            recommendations.append("Use CPU-optimized execution strategies")

        return recommendations

    def _recommend_distribution_strategy(self, characteristics: WorkloadCharacteristics) -> str:
        """Recommend multicore distribution strategy."""
        if characteristics.parallelization_potential > 0.7:
            return "parallel_distribution"
        elif characteristics.cpu_intensity > 0.7:
            return "cpu_optimized_distribution"
        elif characteristics.memory_intensity > 0.7:
            return "memory_aware_distribution"
        else:
            return "balanced_distribution"

    def _emit_workload_classification_telemetry(
        self,
        characteristics: WorkloadCharacteristics
    ) -> None:
        """
        Emit workload classification telemetry to AWS/Lens (non-blocking).

        Per telemetry-audit-findings.md GAP #3: WorkloadManifest detection
        must be transmitted to AWS for Lens Compatibility tab visibility.

        Args:
            characteristics: WorkloadCharacteristics from analysis

        Thread Safety:
            Safe to call from any thread. Uses try/except to ensure
            telemetry failures never affect workload detection functionality.
        """
        try:
            from ...telemetry.routing_events import get_routing_emitter
            emitter = get_routing_emitter()
            if emitter:
                # Build indicators list from characteristics
                indicators = []

                # Add pattern-based indicators
                if characteristics.cpu_intensity > 0.7:
                    indicators.append("high_cpu_intensity")
                if characteristics.memory_intensity > 0.7:
                    indicators.append("high_memory_intensity")
                if characteristics.parallelization_potential > 0.7:
                    indicators.append("high_parallelization_potential")
                if characteristics.gpu_suitability > 0.5:
                    indicators.append("gpu_suitable")

                # Add framework indicators
                if characteristics.numpy_array_count > 0:
                    indicators.append("numpy_detected")
                if characteristics.pandas_dataframe_size > 0:
                    indicators.append("pandas_detected")
                if characteristics.sklearn_model_complexity > 0:
                    indicators.append("sklearn_detected")

                # Map pattern to classification string for Lens compatibility
                classification_map = {
                    WorkloadPattern.CPU_INTENSIVE: "computation",
                    WorkloadPattern.MEMORY_INTENSIVE: "data_processing",
                    WorkloadPattern.IO_BOUND: "web_service",
                    WorkloadPattern.MIXED: "regular_python",
                    WorkloadPattern.PARALLEL_FRIENDLY: "computation",
                    WorkloadPattern.SEQUENTIAL: "regular_python",
                    WorkloadPattern.GPU_SUITABLE: "ml_training",
                    WorkloadPattern.GPU_COMPUTE_INTENSIVE: "ml_training",
                    WorkloadPattern.GPU_MEMORY_BOUND: "ml_training",
                    WorkloadPattern.NUMPY_VECTORIZED: "data_science",
                    WorkloadPattern.NUMPY_LINALG: "data_science",
                    WorkloadPattern.PANDAS_DATAFRAME: "data_science",
                    WorkloadPattern.PANDAS_GROUPBY: "data_science",
                    WorkloadPattern.SKLEARN_TRAINING: "ml_training",
                    WorkloadPattern.SKLEARN_INFERENCE: "llm_inference",
                }
                classification = classification_map.get(
                    characteristics.pattern,
                    "regular_python"
                )

                emitter.emit_workload_classification(
                    classification=classification,
                    confidence=characteristics.confidence,
                    indicators=indicators
                )
                self._logger.debug(
                    f"Workload classification telemetry emitted: "
                    f"{classification} (confidence={characteristics.confidence:.2f})"
                )

        except Exception as e:
            # Telemetry failures must never affect workload detection
            self._logger.debug(f"Failed to emit workload classification telemetry: {e}")

    def _recommend_memory_pool(self, characteristics: WorkloadCharacteristics) -> WorkloadType:
        """Recommend memory pool type based on characteristics."""
        if characteristics.memory_intensity > 0.7:
            return WorkloadType.MEMORY_INTENSIVE
        elif characteristics.cpu_intensity > 0.7:
            return WorkloadType.CPU_BOUND
        elif characteristics.parallelization_potential > 0.7:
            return WorkloadType.MIXED
        else:
            return WorkloadType.MIXED

    def _analyze_loops_for_chunking(self, code: str) -> Dict[str, float]:
        """Analyze loops for chunking potential using AST."""
        try:
            import ast

            tree = ast.parse(code)

            loop_info = {
                'total_loops': 0,
                'chunkable_loops': 0,
                'nested_depth': 0,
                'chunking_potential': 0.0
            }

            class LoopAnalyzer(ast.NodeVisitor):
                def __init__(self):
                    self.depth = 0
                    self.max_depth = 0
                    self.independent_loops = 0
                    self.dependent_loops = 0

                def visit_For(self, node):
                    loop_info['total_loops'] += 1
                    self.depth += 1
                    self.max_depth = max(self.max_depth, self.depth)

                    # Check if loop is potentially chunkable
                    is_chunkable = self._is_loop_chunkable(node)
                    if is_chunkable:
                        loop_info['chunkable_loops'] += 1
                        self.independent_loops += 1
                    else:
                        self.dependent_loops += 1

                    self.generic_visit(node)
                    self.depth -= 1

                def visit_While(self, node):
                    loop_info['total_loops'] += 1
                    # While loops are generally harder to chunk
                    self.dependent_loops += 1
                    self.generic_visit(node)

                def _is_loop_chunkable(self, node):
                    """Check if a for loop is chunkable (independent iterations)."""
                    # Simple heuristics:
                    # 1. range() loops are often chunkable
                    # 2. No break/continue statements
                    # 3. No cross-iteration dependencies

                    if isinstance(node.iter, ast.Call):
                        if (hasattr(node.iter.func, 'id') and
                            node.iter.func.id == 'range'):
                            # range() loops are good candidates
                            return True

                    # Check for break/continue (makes chunking harder)
                    for child in ast.walk(node):
                        if isinstance(child, (ast.Break, ast.Continue)):
                            return False

                    return True

            analyzer = LoopAnalyzer()
            analyzer.visit(tree)

            loop_info['nested_depth'] = analyzer.max_depth

            # Calculate chunking potential
            if loop_info['total_loops'] > 0:
                chunkable_ratio = loop_info['chunkable_loops'] / loop_info['total_loops']
                # Boost for simple loops, reduce for complex nested structures
                depth_factor = max(0.2, 1.0 - (analyzer.max_depth - 1) * 0.3)
                loop_info['chunking_potential'] = chunkable_ratio * depth_factor

            return loop_info

        except Exception:
            # Fallback if AST analysis fails
            return {
                'total_loops': 0,
                'chunkable_loops': 0,
                'nested_depth': 0,
                'chunking_potential': 0.0
            }

    def _get_default_characteristics(self) -> WorkloadCharacteristics:
        """Get default workload characteristics when no data is available."""
        return WorkloadCharacteristics(
            pattern=WorkloadPattern.MIXED,
            memory_intensity=0.5,
            cpu_intensity=0.5,
            parallelization_potential=0.5,
            allocation_frequency=0.0,
            average_allocation_size=0,
            thread_count=1,
            confidence=0.1,
            l1_cache_miss_rate=0.0,
            memory_pressure_indicator=0.0,
            computational_intensity=0.0,
            sampling_overhead_us=0.0,
            # GPU characteristics - default values
            gpu_suitability=0.0,
            gpu_data_size_score=0.0,
            gpu_operation_score=0.0,
            estimated_gpu_speedup=1.0
        )

    def _get_hardware_characteristics(self) -> Optional[Dict[str, Any]]:
        """Get hardware performance characteristics from statistical sampling."""
        if not self._hardware_profiling_enabled or not self._statistical_sampler:
            return None

        try:
            # Get 1-second window of hardware characteristics
            hardware_data = self._statistical_sampler.get_workload_characteristics(window_seconds=1.0)

            self._logger.debug(f"Hardware profiling data: {hardware_data}")
            return hardware_data

        except Exception as e:
            self._logger.warning(f"Failed to get hardware characteristics: {e}")
            return None

    def _merge_hardware_characteristics(self,
                                      base_characteristics: WorkloadCharacteristics,
                                      hardware_data: Optional[Dict[str, Any]]) -> WorkloadCharacteristics:
        """Merge hardware counter data with allocation-based characteristics."""
        if not hardware_data:
            return base_characteristics

        # Extract hardware metrics
        hw_cpu_score = hardware_data.get('cpu_bound_score', 0.0)
        hw_memory_score = hardware_data.get('memory_bound_score', 0.0)
        hw_io_score = hardware_data.get('io_bound_score', 0.0)
        hw_parallel_efficiency = hardware_data.get('parallel_efficiency', 1.0)
        hw_memory_pressure = hardware_data.get('memory_pressure', 0.0)
        hw_computational_intensity = hardware_data.get('computational_intensity', 0.0)
        hw_sampling_overhead = hardware_data.get('sampling_overhead_us', 0.0)

        # Enhanced scoring with hardware validation
        # Weight: 60% allocation analysis + 40% hardware counters
        enhanced_cpu_intensity = (base_characteristics.cpu_intensity * 0.6 + hw_cpu_score * 0.4)
        enhanced_memory_intensity = (base_characteristics.memory_intensity * 0.6 +
                                   max(hw_memory_score, hw_memory_pressure) * 0.4)

        # Parallel efficiency from hardware helps validate parallelization potential
        enhanced_parallel_potential = min(
            base_characteristics.parallelization_potential * hw_parallel_efficiency,
            1.0
        )

        # Re-evaluate pattern with hardware-enhanced data
        enhanced_pattern = self._determine_enhanced_workload_pattern(
            enhanced_memory_intensity, enhanced_cpu_intensity, enhanced_parallel_potential, hw_io_score
        )

        # Calculate enhanced GPU characteristics
        enhanced_gpu_suitability = self._calculate_gpu_suitability(
            base_characteristics.gpu_operation_score,
            base_characteristics.gpu_data_size_score,
            enhanced_cpu_intensity
        )

        return WorkloadCharacteristics(
            pattern=enhanced_pattern,
            memory_intensity=enhanced_memory_intensity,
            cpu_intensity=enhanced_cpu_intensity,
            parallelization_potential=enhanced_parallel_potential,
            allocation_frequency=base_characteristics.allocation_frequency,
            average_allocation_size=base_characteristics.average_allocation_size,
            thread_count=base_characteristics.thread_count,
            confidence=min(base_characteristics.confidence + 0.2, 1.0),  # Higher confidence
            # Hardware-specific characteristics
            l1_cache_miss_rate=hw_memory_score,
            memory_pressure_indicator=hw_memory_pressure,
            computational_intensity=hw_computational_intensity,
            sampling_overhead_us=hw_sampling_overhead,
            # GPU characteristics (enhanced with hardware data)
            gpu_suitability=enhanced_gpu_suitability,
            gpu_data_size_score=base_characteristics.gpu_data_size_score,
            gpu_operation_score=base_characteristics.gpu_operation_score,
            estimated_gpu_speedup=base_characteristics.estimated_gpu_speedup
        )

    def _calculate_gpu_suitability(self, gpu_operation_score: float,
                                 gpu_data_size_score: float,
                                 cpu_intensity: float) -> float:
        """
        Calculate overall GPU suitability score.

        Args:
            gpu_operation_score: Score based on GPU-friendly operations
            gpu_data_size_score: Score based on data size indicators
            cpu_intensity: CPU intensity score

        Returns:
            GPU suitability score (0.0 to 1.0)
        """
        if not self._gpu_available:
            return 0.0

        # Base suitability from operations and data size
        base_score = (gpu_operation_score * 0.6 + gpu_data_size_score * 0.4)

        # Boost for CPU-intensive workloads (they benefit more from GPU)
        cpu_boost = min(cpu_intensity * 0.3, 0.3)

        # Consider GPU capability
        capability_factor = 1.0
        if self._gpu_info and self._gpu_info.compute_capability:
            major = int(self._gpu_info.compute_capability.split('.')[0])
            if major >= 8:      # Ampere or newer
                capability_factor = 1.2
            elif major >= 7:    # Turing/Volta
                capability_factor = 1.1
            elif major >= 6:    # Pascal
                capability_factor = 1.0
            else:               # Older
                capability_factor = 0.8

        return min(1.0, (base_score + cpu_boost) * capability_factor)

    def _estimate_gpu_speedup_from_static(self, gpu_operation_score: float,
                                        gpu_data_size_score: float) -> float:
        """
        Estimate GPU speedup from static code analysis.

        Args:
            gpu_operation_score: Score based on GPU-friendly operations
            gpu_data_size_score: Score based on data size indicators

        Returns:
            Estimated speedup ratio
        """
        if not self._gpu_available or gpu_operation_score == 0:
            return 1.0

        # Base speedup estimates for different operation types
        if gpu_operation_score > 0.8:      # Heavy compute (matmul, fft)
            base_speedup = 15.0
        elif gpu_operation_score > 0.6:    # Moderate compute
            base_speedup = 8.0
        elif gpu_operation_score > 0.3:    # Light compute
            base_speedup = 4.0
        else:
            base_speedup = 2.0

        # Adjust based on data size
        data_size_factor = 1.0 + gpu_data_size_score * 0.5  # Up to 1.5x boost

        return base_speedup * data_size_factor

    def _determine_enhanced_workload_pattern(self, memory_intensity: float,
                                           cpu_intensity: float,
                                           parallelization_potential: float,
                                           io_score: float) -> WorkloadPattern:
        """Determine workload pattern with hardware-enhanced logic."""
        # Enhanced decision tree with hardware validation
        if io_score > 0.7:  # High I/O from context switches
            return WorkloadPattern.IO_BOUND
        elif parallelization_potential > 0.7 and cpu_intensity > 0.5:
            return WorkloadPattern.PARALLEL_FRIENDLY
        elif cpu_intensity > self._cpu_intensive_threshold:
            return WorkloadPattern.CPU_INTENSIVE
        elif memory_intensity > self._memory_intensive_threshold:
            return WorkloadPattern.MEMORY_INTENSIVE
        elif parallelization_potential < 0.2:
            return WorkloadPattern.SEQUENTIAL
        else:
            return WorkloadPattern.MIXED
