"""
Epochly Adaptive Orchestrator

This module implements the AdaptiveOrchestrator component that coordinates
dynamic pool switching, optimization decisions, and real-time adaptation
based on workload analysis and performance feedback.

COORD-9: Demand-driven orchestrator activation - gates start_monitoring() behind
explicit triggers (counter spike, hot loop) instead of unconditional Level 2 start.

Author: Epochly Development Team
"""

import time
import threading
from typing import Dict, Any, List, Optional, Tuple, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import statistics
from collections import deque, defaultdict

from .workload_detector import WorkloadDetectionAnalyzer, WorkloadPattern
from .memory_profiler import MemoryProfiler, MemoryStats
from .pool_selector import MemoryPoolSelector, PoolRecommendation, SelectionCriteria, PoolScore
from .jit_analyzer import JITAnalyzer, HotPathCandidate
from .workload_strategy import WorkloadStrategy, PoolSelectionStrategy


class AdaptationTrigger(Enum):
    """Triggers for pool adaptation."""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    WORKLOAD_CHANGE = "workload_change"
    MEMORY_PRESSURE = "memory_pressure"
    FRAGMENTATION_THRESHOLD = "fragmentation_threshold"
    PERIODIC_OPTIMIZATION = "periodic_optimization"
    MANUAL_TRIGGER = "manual_trigger"
    JIT_HOT_PATH_DETECTED = "jit_hot_path_detected"
    JIT_PERFORMANCE_OPPORTUNITY = "jit_performance_opportunity"


class OrchestratorState(Enum):
    """Orchestrator lifecycle states (COORD-9)."""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"


@dataclass
class AdaptationEvent:
    """Event that triggered an adaptation."""
    trigger: AdaptationTrigger
    timestamp: float
    old_pool: Optional[PoolRecommendation]
    new_pool: PoolRecommendation
    performance_before: float
    performance_after: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationConfig:
    """Configuration for the adaptive orchestrator."""
    adaptation_threshold: float = 0.15  # 15% performance change threshold
    monitoring_interval: float = 5.0    # Monitor every 5 seconds
    min_adaptation_interval: float = 30.0  # Minimum 30s between adaptations
    performance_window: float = 60.0    # 60s window for performance calculation
    fragmentation_threshold: float = 0.3  # 30% fragmentation threshold
    enable_predictive_adaptation: bool = True
    enable_learning: bool = True
    max_adaptation_history: int = 1000

    # JIT compilation coordination settings
    enable_jit_coordination: bool = True
    jit_hot_path_threshold: float = 70.0  # Score threshold for JIT hot path detection
    min_jit_benefit_threshold: float = 1.2  # Minimum 20% speedup expected
    jit_analysis_interval: float = 10.0   # JIT analysis every 10 seconds
    max_concurrent_compilations: int = 2  # Limit concurrent JIT compilations

    # COORD-9: Lazy activation settings
    idle_timeout: Optional[float] = None  # Auto-stop after N seconds idle (None = never)
    activation_trigger_threshold: float = 1.5  # Spike magnitude threshold


class AdaptiveOrchestrator:
    """
    Adaptive orchestrator for dynamic memory pool optimization.

    This component coordinates all analyzer components to provide intelligent,
    real-time adaptation of memory pool configurations based on workload
    characteristics and performance feedback.

    COORD-9: Implements demand-driven activation - orchestrator stays idle until
    explicit triggers (counter spike, hot loop) request activation.
    """

    def __init__(
        self,
        config: Optional[OrchestrationConfig] = None,
        performance_callback: Optional[Callable[[], float]] = None,
        jit_manager: Optional[Any] = None,
        always_on: bool = False,
        sampling_rate: float = 0.01,  # NEW: 1% sampling (1 in 100)
        batch_size: int = 100,  # NEW: Batch size for analysis
        # P2-2 FIX (Dec 2025): Default to False - background thread starts lazily on first event
        enable_background_processing: bool = False  # Background thread (lazy-initialized)
    ):
        """
        Initialize the adaptive orchestrator.

        Args:
            config: Orchestration configuration
            performance_callback: Function to get current performance metrics
            jit_manager: Optional JIT manager for compilation coordination
            always_on: If True, auto-start monitoring (backward compatibility)
            sampling_rate: Probability of analyzing each allocation (0.01 = 1%)
            batch_size: Number of events to batch before analysis
            enable_background_processing: Use background thread for analysis
        """
        self._config = config or OrchestrationConfig()
        self._performance_callback = performance_callback
        self._always_on = always_on

        # Performance optimizations (Nov 22, 2025)
        self._sampling_rate = sampling_rate
        self._batch_size = batch_size
        self._enable_background_processing = enable_background_processing
        self._large_allocation_threshold = 1024 * 1024  # Always sample >1MB

        # Sampling statistics
        self._samples_analyzed = 0
        self._samples_skipped = 0
        self._large_allocations_analyzed = 0

        # Batch processing
        self._batch_queue: deque = deque(maxlen=10000)  # Prevent unbounded growth
        self._batch_lock = threading.Lock()
        self._batch_processed_count = 0
        self._events_processed = 0

        # Background thread for async analysis
        self._background_thread: Optional[threading.Thread] = None
        self._background_queue: deque = deque(maxlen=10000)  # Prevent OOM under extreme load
        self._background_lock = threading.Lock()
        self._stop_background = threading.Event()
        self._queue_capacity_warning_threshold = 8000  # Warn at 80% capacity

        # Logging
        import logging
        self._logger = logging.getLogger(__name__)

        # Component instances
        self._workload_detector = WorkloadDetectionAnalyzer()
        self._memory_profiler = MemoryProfiler()
        self._pool_selector = MemoryPoolSelector()
        self._jit_analyzer = JITAnalyzer() if self._config.enable_jit_coordination else None
        self._jit_manager = jit_manager
        self._pool_strategy = PoolSelectionStrategy()

        # State management
        self._current_pool = PoolRecommendation.GENERAL_PURPOSE
        self._last_adaptation_time = 0.0
        self._last_periodic_optimization = 0.0
        self._monitoring_active = False
        self._adaptation_history: deque = deque(maxlen=self._config.max_adaptation_history)

        # COORD-9: Orchestrator state tracking
        self._state = OrchestratorState.IDLE
        self._last_trigger_time = 0.0
        self._activation_triggers: Dict[str, List[Callable]] = defaultdict(list)

        # JIT coordination state
        self._last_jit_analysis_time = 0.0
        self._active_compilations: Set[str] = set()
        self._jit_performance_gains: Dict[str, float] = {}
        self._function_compilation_history: Dict[str, List[float]] = defaultdict(list)

        # Performance tracking
        self._performance_history: deque = deque(maxlen=1000)
        self._baseline_performance: Optional[float] = None

        # Thread safety
        self._lock = threading.RLock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()

        # Learning and prediction
        self._adaptation_patterns: Dict[str, List[float]] = defaultdict(list)
        self._prediction_cache: Dict[str, Tuple[float, Any]] = {}

        # ML-based enhancement with graceful fallback
        self._ml_predictor = self._initialize_ml_predictor()
        self._rl_scheduler = self._initialize_rl_scheduler()
        self._ml_enabled = self._ml_predictor is not None

        # Resource metrics for ML prediction
        self._resource_metrics_history: deque = deque(maxlen=100)

        # Callbacks for pool changes
        self._pool_change_callbacks: List[Callable[[PoolRecommendation, PoolRecommendation], None]] = []

        # Callbacks for GPU availability changes (perf_fixes5.md Issue C)
        self._gpu_callbacks: List[Callable[[bool], None]] = []

        # P2-2 FIX (Dec 2025): Background thread is now lazy-initialized
        # Thread starts when first event is queued, not at orchestrator creation
        # This saves 1 daemon thread when allocations are never recorded
        self._background_thread_started = False

        # COORD-9: Auto-start if always_on mode
        if self._always_on:
            self.force_start()

    def _start_background_thread(self):
        """Start background thread for async batch processing."""
        self._background_thread = threading.Thread(
            target=self._background_processing_loop,
            daemon=True,
            name="Epochly-Orchestrator-Background"
        )
        self._background_thread.start()
        self._logger.debug("Background analysis thread started")

    def _background_processing_loop(self):
        """Background thread loop for processing batched events."""
        while not self._stop_background.is_set():
            try:
                # Wait for events or timeout
                if self._stop_background.wait(timeout=0.1):
                    break

                # Process any queued batches
                self._process_background_queue()

            except Exception as e:
                self._logger.error(f"Background processing error: {e}")

        self._logger.debug("Background analysis thread stopped")

    def _process_background_queue(self):
        """Process queued events in background thread."""
        batch_to_process = []

        with self._background_lock:
            if len(self._background_queue) >= self._batch_size:
                # Extract batch efficiently (list comprehension)
                batch_size = min(self._batch_size, len(self._background_queue))
                batch_to_process = [
                    self._background_queue.popleft()
                    for _ in range(batch_size)
                ]

        if batch_to_process:
            # Process batch (expensive ML analysis happens here, not on hot path)
            # Counters are updated inside _analyze_batch
            self._analyze_batch(batch_to_process)

    def _analyze_batch(self, events: List[Dict[str, Any]]):
        """Analyze a batch of allocation events."""
        if not events:
            return

        try:
            # Aggregate event data
            total_size = sum(e.get('size', 0) for e in events)
            avg_size = total_size / len(events) if events else 0

            # Call memory profiler for batch
            for event in events:
                self._memory_profiler.record_allocation(
                    event.get('size'),
                    event.get('address'),
                    event.get('thread_id')
                )

            # Analyze workload patterns for batch
            self._workload_detector.analyze_runtime({"allocation_events": events})

            # Update counters
            self._batch_processed_count += 1
            self._events_processed += len(events)

        except Exception as e:
            self._logger.debug(f"Batch analysis error: {e}")

    # COORD-9: Demand-driven activation API

    def ensure_started(self) -> None:
        """
        Ensure orchestrator is running (idempotent).

        Start monitoring if not already active. Safe to call multiple times.
        Provides <500ms activation latency.
        """
        with self._lock:
            if self._state in [OrchestratorState.RUNNING, OrchestratorState.STARTING]:
                return  # Already active

            self._state = OrchestratorState.STARTING
            self._last_trigger_time = time.time()

        # Delegate to start_monitoring for actual activation
        self.start_monitoring()

        with self._lock:
            self._state = OrchestratorState.RUNNING

    def ensure_stopped(self) -> None:
        """
        Ensure orchestrator is stopped (idempotent).

        Stop monitoring if active. Safe to call multiple times.
        """
        with self._lock:
            if self._state in [OrchestratorState.IDLE, OrchestratorState.STOPPING]:
                return  # Already inactive

            self._state = OrchestratorState.STOPPING

        # Delegate to stop_monitoring for actual deactivation
        self.stop_monitoring()

        with self._lock:
            self._state = OrchestratorState.IDLE

    def is_running(self) -> bool:
        """
        Check if orchestrator is currently active.

        Returns:
            True if monitoring is active, False otherwise
        """
        with self._lock:
            return self._state == OrchestratorState.RUNNING and self._monitoring_active

    def get_state(self) -> str:
        """
        Get current orchestrator state.

        Returns:
            Current state as string (idle/starting/running/stopping)
        """
        with self._lock:
            return self._state.value

    def force_start(self) -> None:
        """
        Force orchestrator activation unconditionally.

        Manual override for operators requiring full-time orchestration.
        """
        self._logger.info("Force starting orchestrator (manual override)")
        self.ensure_started()

    def force_stop(self) -> None:
        """
        Force orchestrator deactivation unconditionally.

        Manual override for controlled shutdown.
        """
        self._logger.info("Force stopping orchestrator (manual override)")
        self.ensure_stopped()

    # COORD-9: Subscription-based trigger API

    def on_counter_spike_detected(
        self,
        counter_type: str,
        spike_magnitude: float,
        baseline: float,
        current: float
    ) -> None:
        """
        Callback when hardware counter spike is detected.

        Activates orchestrator if spike exceeds threshold.

        Args:
            counter_type: Type of counter (l1_cache_misses, etc.)
            spike_magnitude: Magnitude of spike (current/baseline ratio)
            baseline: Baseline counter value
            current: Current counter value
        """
        if spike_magnitude >= self._config.activation_trigger_threshold:
            self._logger.info(
                f"Counter spike detected: {counter_type} "
                f"{spike_magnitude:.2f}x (baseline={baseline}, current={current}) - activating orchestrator"
            )
            self.ensure_started()

            # Invoke registered callbacks
            for callback in self._activation_triggers.get("counter_spike", []):
                try:
                    callback()
                except Exception as e:
                    self._logger.error(f"Error in counter spike callback: {e}")

    def on_hot_loop_detected(
        self,
        function_name: str,
        iteration_count: int,
        execution_time_ns: int
    ) -> None:
        """
        Callback when profiler detects hot loop.

        Activates orchestrator to coordinate optimization.

        Args:
            function_name: Name of function with hot loop
            iteration_count: Number of loop iterations
            execution_time_ns: Total execution time in nanoseconds
        """
        self._logger.info(
            f"Hot loop detected: {function_name} "
            f"({iteration_count} iterations, {execution_time_ns/1e9:.3f}s) - activating orchestrator"
        )
        self.ensure_started()

        # Invoke registered callbacks
        for callback in self._activation_triggers.get("hot_loop", []):
            try:
                callback()
            except Exception as e:
                self._logger.error(f"Error in hot loop callback: {e}")

    def on_workload_change_detected(
        self,
        old_pattern: WorkloadPattern,
        new_pattern: WorkloadPattern,
        confidence: float
    ) -> None:
        """
        Callback when workload pattern changes significantly.

        Activates orchestrator to adapt pool configuration.

        Args:
            old_pattern: Previous workload pattern
            new_pattern: New workload pattern
            confidence: Confidence in pattern detection (0.0-1.0)
        """
        if confidence >= 0.7:  # High confidence threshold
            self._logger.info(
                f"Workload change detected: {old_pattern.value} -> {new_pattern.value} "
                f"(confidence={confidence:.2f}) - activating orchestrator"
            )
            self.ensure_started()

            # Invoke registered callbacks
            for callback in self._activation_triggers.get("workload_change", []):
                try:
                    callback()
                except Exception as e:
                    self._logger.error(f"Error in workload change callback: {e}")

    def register_activation_trigger(
        self,
        trigger_type: str,
        callback: Callable[[], None]
    ) -> None:
        """
        Register callback for activation triggers.

        Args:
            trigger_type: Type of trigger (counter_spike, hot_loop, workload_change)
            callback: Callback function to invoke on trigger
        """
        with self._lock:
            self._activation_triggers[trigger_type].append(callback)

    def unregister_activation_trigger(
        self,
        trigger_type: str,
        callback: Callable[[], None]
    ) -> None:
        """
        Unregister activation trigger callback.

        Args:
            trigger_type: Type of trigger
            callback: Callback to remove
        """
        with self._lock:
            if callback in self._activation_triggers[trigger_type]:
                self._activation_triggers[trigger_type].remove(callback)

    # Original monitoring methods (preserved for backward compatibility)

    def start_monitoring(self) -> None:
        """Start continuous monitoring and adaptation."""
        with self._lock:
            if self._monitoring_active:
                return

            self._monitoring_active = True
            self._stop_monitoring.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="Epochly-AdaptiveOrchestrator"
            )
            self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop continuous monitoring and background processing."""
        with self._lock:
            if not self._monitoring_active:
                # Still stop background thread if it's running
                if self._background_thread and self._background_thread.is_alive():
                    self._stop_background.set()
                    self._background_thread.join(timeout=1.0)
                return

            self._monitoring_active = False
            self._stop_monitoring.set()

            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=5.0)

            # Stop background processing thread
            if self._background_thread and self._background_thread.is_alive():
                self._stop_background.set()
                self._background_thread.join(timeout=1.0)

    def record_allocation(
        self,
        size: int,
        address: Optional[int] = None,
        thread_id: Optional[int] = None
    ) -> None:
        """
        Record a memory allocation for analysis (optimized with sampling and batching).

        Performance optimizations (Nov 22, 2025):
        - Sampling: Only analyzes 1% of allocations (configurable)
        - Batching: Accumulates events for bulk analysis
        - Background: Processes batches asynchronously

        Expected overhead: <1μs (vs 389μs without optimizations)
        """
        # OPTIMIZATION 1: Sampling - skip most allocations
        import random

        is_large_allocation = size >= self._large_allocation_threshold
        should_sample = (random.random() < self._sampling_rate) or is_large_allocation

        if not should_sample:
            self._samples_skipped += 1
            return  # Fast path: just return, no analysis

        # Track sampling stats
        self._samples_analyzed += 1
        if is_large_allocation:
            self._large_allocations_analyzed += 1

        # OPTIMIZATION 2 & 3: Batch and queue for background processing
        allocation_event = {
            "timestamp": time.time(),
            "size": size,
            "address": address,
            "thread_id": thread_id or threading.get_ident(),
            "type": "allocation"
        }

        if self._enable_background_processing:
            # P2-2 FIX (Dec 2025): Lazy thread initialization on first queue operation
            if not self._background_thread_started:
                self._start_background_thread()
                self._background_thread_started = True

            # Add to background queue (fast: just append to deque)
            with self._background_lock:
                queue_size = len(self._background_queue)

                # Warn if queue approaching capacity
                if queue_size > self._queue_capacity_warning_threshold:
                    self._logger.warning(
                        f"Background queue near capacity: {queue_size}/10000 "
                        f"(analysis thread may be falling behind)"
                    )

                self._background_queue.append(allocation_event)

        else:
            # Synchronous mode: add to batch queue
            with self._batch_lock:
                self._batch_queue.append(allocation_event)

                # Process batch if threshold reached
                if len(self._batch_queue) >= self._batch_size:
                    batch = list(self._batch_queue)
                    self._batch_queue.clear()
                    # Process immediately (blocking)
                    self._analyze_batch(batch)

    def record_deallocation(self, address: int, size: Optional[int] = None) -> None:
        """Record a memory deallocation for analysis."""
        self._memory_profiler.record_deallocation(address, size)

    def record_function_call(
        self,
        func: Callable,
        execution_time_ns: int,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a function call for JIT analysis."""
        if not self._config.enable_jit_coordination or not self._jit_analyzer:
            return

        try:
            # Profile the function call with JIT analyzer
            self._jit_analyzer.profile_function_call(func, execution_time_ns)

            # Analyze function characteristics with context if provided
            if context:
                self._jit_analyzer.analyze_function(func, context)

            # Analyze function characteristics if not already done
            func_name = getattr(func, '__name__', str(func))
            if not self._jit_analyzer.get_function_characteristics(func_name):
                self._jit_analyzer.analyze_function(func, context)

        except Exception as e:
            self._logger.debug(f"Error recording function call for JIT analysis: {e}")

    def record_hot_loop(
        self,
        func: Callable,
        loop_instruction: str,
        loop_offset: int,
        iteration_count: int,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record detection of a hot loop for optimization.

        This integrates with JIT compilation to prioritize hot loops.

        Args:
            func: Function code object containing the loop
            loop_instruction: Bytecode instruction name (FOR_ITER, JUMP_BACKWARD)
            loop_offset: Bytecode offset of the loop
            iteration_count: Number of iterations detected
            context: Additional context (function name, etc.)
        """
        if not self._config.enable_jit_coordination or not self._jit_analyzer:
            return

        try:
            func_name = context.get('name', str(func)) if context else str(func)

            # Mark function as having hot loops for JIT prioritization
            # JIT compiler will prioritize functions with hot loops
            if hasattr(self._jit_analyzer, 'mark_hot_loop_function'):
                self._jit_analyzer.mark_hot_loop_function(
                    func_name,
                    iteration_count=iteration_count
                )

            # Alternative: directly register for profiling if method exists
            if hasattr(self._jit_analyzer, 'register_function_for_profiling'):
                self._jit_analyzer.register_function_for_profiling(func)

        except Exception as e:
            # Don't let recording failures break the profiler
            pass

    def record_performance_metric(self, metric: float) -> None:
        """Record a performance metric for adaptation decisions."""
        with self._lock:
            self._performance_history.append((time.time(), metric))

            # Establish baseline if not set
            if self._baseline_performance is None and len(self._performance_history) >= 10:
                recent_metrics = [m for _, m in list(self._performance_history)[-10:]]
                self._baseline_performance = statistics.mean(recent_metrics)

    def trigger_adaptation(
        self,
        trigger: AdaptationTrigger = AdaptationTrigger.MANUAL_TRIGGER
    ) -> Optional[PoolRecommendation]:
        """
        Manually trigger pool adaptation.

        Args:
            trigger: Reason for triggering adaptation

        Returns:
            New pool recommendation if adaptation occurred
        """
        return self._evaluate_and_adapt(trigger)

    def get_current_recommendation(self) -> PoolRecommendation:
        """Get the current pool recommendation."""
        with self._lock:
            return self._current_pool

    def get_adaptation_history(self) -> List[AdaptationEvent]:
        """Get the history of adaptation events."""
        with self._lock:
            return list(self._adaptation_history)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary and statistics."""
        with self._lock:
            if not self._performance_history:
                base_summary = {"status": "no_data"}
            else:
                recent_metrics = [m for _, m in list(self._performance_history)[-20:]]

                base_summary = {
                    "current_pool": self._current_pool.value,
                    "baseline_performance": self._baseline_performance,
                    "recent_average": statistics.mean(recent_metrics),
                    "recent_std_dev": statistics.stdev(recent_metrics) if len(recent_metrics) > 1 else 0.0,
                    "adaptation_count": len(self._adaptation_history),
                    "monitoring_active": self._monitoring_active,
                    "orchestrator_state": self._state.value  # COORD-9
                }

            # Add JIT statistics if JIT coordination is enabled
            if self._config.enable_jit_coordination:
                base_summary["jit_statistics"] = self.get_jit_statistics()

            # Add ML statistics if ML is enabled
            if self._ml_enabled and self._ml_predictor:
                base_summary["ml_statistics"] = self._get_ml_statistics()

            # Add queue health metrics (mcp-reflect recommendation)
            base_summary["queue_health"] = {
                "background_queue_size": len(self._background_queue),
                "background_queue_capacity": 10000,
                "background_queue_utilization": len(self._background_queue) / 10000,
                "batch_queue_size": len(self._batch_queue),
                "batches_processed": self._batch_processed_count,
                "events_processed": self._events_processed,
                "samples_analyzed": self._samples_analyzed,
                "samples_skipped": self._samples_skipped,
                "sampling_rate_configured": self._sampling_rate,
                "sampling_rate_actual": (
                    self._samples_analyzed /
                    (self._samples_analyzed + self._samples_skipped)
                    if (self._samples_analyzed + self._samples_skipped) > 0 else 0
                ),
                "large_allocations_analyzed": self._large_allocations_analyzed
            }

            return base_summary

    def predict_optimal_pool(
        self,
        lookahead_seconds: float = 60.0
    ) -> Optional[PoolRecommendation]:
        """
        Predict optimal pool for future workload.

        Args:
            lookahead_seconds: How far ahead to predict

        Returns:
            Predicted optimal pool recommendation
        """
        if not self._config.enable_predictive_adaptation:
            return None

        # Get current workload characteristics
        runtime_analysis = self._workload_detector.analyze_runtime({})
        current_pattern = WorkloadPattern(runtime_analysis.get("current_workload", "mixed"))
        current_stats = self._memory_profiler.get_current_stats()

        # Use cached prediction if recent
        cache_key = f"{current_pattern.value}_{current_stats.allocation_count}"
        if cache_key in self._prediction_cache:
            cache_time, prediction = self._prediction_cache[cache_key]
            if time.time() - cache_time < 30.0:  # 30s cache validity
                return prediction

        # Predict future workload characteristics
        predicted_characteristics = self._predict_workload_evolution(
            current_pattern, lookahead_seconds
        )

        if predicted_characteristics:
            # Get recommendation for predicted workload
            criteria = SelectionCriteria(
                workload_pattern=predicted_characteristics["pattern"],
                allocation_pattern=predicted_characteristics["allocation_pattern"],
                memory_stats=current_stats,
                thread_count=predicted_characteristics.get("thread_count", 1)
            )

            recommendation = self._pool_selector.get_best_recommendation(criteria)

            # Cache the prediction
            self._prediction_cache[cache_key] = (time.time(), recommendation.pool_type)

            return recommendation.pool_type

        return None

    def add_pool_change_callback(
        self,
        callback: Callable[[PoolRecommendation, PoolRecommendation], None]
    ) -> None:
        """Add a callback for pool change notifications."""
        self._pool_change_callbacks.append(callback)

    def remove_pool_change_callback(
        self,
        callback: Callable[[PoolRecommendation, PoolRecommendation], None]
    ) -> None:
        """Remove a pool change callback."""
        if callback in self._pool_change_callbacks:
            self._pool_change_callbacks.remove(callback)

    def add_gpu_callback(self, callback: Callable[[bool], None]) -> None:
        """
        Add a callback for GPU availability change notifications.

        Implements perf_fixes5.md Issue C: GPU availability changes should be
        surfaced to the adaptive orchestrator.

        Args:
            callback: Function to call when GPU availability changes.
                     Receives one argument: available (bool)

        Example:
            def on_gpu_change(available: bool):
                if not available:
                    logger.warning("GPU unavailable - disabling Level 4")

            orchestrator.add_gpu_callback(on_gpu_change)
        """
        with self._lock:
            if callback not in self._gpu_callbacks:
                self._gpu_callbacks.append(callback)
                self._logger.debug(f"Registered GPU callback: {callback.__name__ if hasattr(callback, '__name__') else 'anonymous'}")

    def remove_gpu_callback(self, callback: Callable[[bool], None]) -> None:
        """
        Remove a GPU availability callback.

        Args:
            callback: Callback function to remove
        """
        with self._lock:
            if callback in self._gpu_callbacks:
                self._gpu_callbacks.remove(callback)
                self._logger.debug(f"Removed GPU callback: {callback.__name__ if hasattr(callback, '__name__') else 'anonymous'}")

    def notify_gpu_availability_change(self, available: bool) -> None:
        """
        Notify registered callbacks of GPU availability change.

        This method should be called by the GPU detector or Level 4 system
        when GPU availability changes (e.g., GPU memory exhaustion, driver failure).

        Args:
            available: True if GPU is available, False otherwise
        """
        with self._lock:
            callbacks = list(self._gpu_callbacks)  # Copy to avoid modification during iteration

        self._logger.info(f"GPU availability changed: {available}, notifying {len(callbacks)} callbacks")

        # Invoke callbacks outside lock to prevent deadlock
        for callback in callbacks:
            try:
                callback(available)
            except Exception as e:
                self._logger.error(f"GPU callback {callback} raised exception: {e}")
                # Continue to next callback (don't let one failure stop others)

    def get_framework_optimization_strategy(self, characteristics: Any) -> Dict[str, Any]:
        """
        Get framework-specific optimization strategy based on workload characteristics.

        This method provides cross-cutting framework optimizations that work
        across all enhancement levels (0-4) without requiring GPU availability.

        Args:
            characteristics: WorkloadCharacteristics from workload detector

        Returns:
            Dict containing framework optimization strategy
        """
        strategy = {
            "framework_detected": None,
            "optimization_type": "none",
            "parallelization_strategy": "default",
            "estimated_improvement": 1.0,
            "memory_optimization": False,
            "jit_compatibility": True
        }

        try:
            # Import here to avoid circular imports
            from .workload_detector import WorkloadPattern

            # NumPy optimizations
            if characteristics.pattern in [WorkloadPattern.NUMPY_VECTORIZED, WorkloadPattern.NUMPY_LINALG]:
                strategy.update({
                    "framework_detected": "numpy",
                    "optimization_type": "vectorization" if characteristics.pattern == WorkloadPattern.NUMPY_VECTORIZED else "linear_algebra",
                    "parallelization_strategy": "array_chunking",
                    "estimated_improvement": 2.0 + characteristics.numpy_operation_complexity,
                    "memory_optimization": True,
                    "jit_compatibility": True
                })

            # Pandas optimizations
            elif characteristics.pattern in [WorkloadPattern.PANDAS_DATAFRAME, WorkloadPattern.PANDAS_GROUPBY]:
                strategy.update({
                    "framework_detected": "pandas",
                    "optimization_type": "groupby_parallel" if characteristics.pattern == WorkloadPattern.PANDAS_GROUPBY else "dataframe_chunking",
                    "parallelization_strategy": "row_partitioning",
                    "estimated_improvement": 1.5 + characteristics.pandas_groupby_complexity,
                    "memory_optimization": True,
                    "jit_compatibility": False  # Pandas operations don't JIT well
                })

            # scikit-learn optimizations
            elif characteristics.pattern in [WorkloadPattern.SKLEARN_TRAINING, WorkloadPattern.SKLEARN_INFERENCE]:
                strategy.update({
                    "framework_detected": "sklearn",
                    "optimization_type": "model_parallel" if characteristics.pattern == WorkloadPattern.SKLEARN_TRAINING else "batch_inference",
                    "parallelization_strategy": "model_parallelism",
                    "estimated_improvement": 1.8 + characteristics.sklearn_model_complexity,
                    "memory_optimization": False,
                    "jit_compatibility": True  # sklearn can benefit from JIT in some cases
                })

            # Add framework-specific metadata
            if strategy["framework_detected"]:
                strategy["framework_characteristics"] = {
                    "numpy_complexity": characteristics.numpy_operation_complexity,
                    "pandas_complexity": characteristics.pandas_groupby_complexity,
                    "sklearn_complexity": characteristics.sklearn_model_complexity,
                    "parallelization_score": characteristics.framework_parallelization_score
                }

                self._logger.debug(f"Framework optimization strategy: {strategy['framework_detected']} - {strategy['optimization_type']}")

            return strategy

        except Exception as e:
            self._logger.warning(f"Framework optimization strategy failed: {e}")
            return strategy

    def _monitoring_loop(self) -> None:
        """Main monitoring loop for continuous adaptation."""
        while not self._stop_monitoring.wait(self._config.monitoring_interval):
            try:
                # COORD-9: Check idle timeout
                if self._should_auto_stop():
                    self._logger.info("Idle timeout reached - auto-stopping orchestrator")
                    self.ensure_stopped()
                    break

                # Check for adaptation triggers
                self._check_adaptation_triggers()

                # Update performance metrics if callback available
                if self._performance_callback:
                    current_performance = self._performance_callback()
                    self.record_performance_metric(current_performance)

                # JIT hot path analysis
                if self._config.enable_jit_coordination and self._should_perform_jit_analysis():
                    self._analyze_jit_opportunities()

                # Periodic optimization check
                if self._should_perform_periodic_optimization():
                    self._evaluate_and_adapt(AdaptationTrigger.PERIODIC_OPTIMIZATION)

            except Exception as e:
                # Log error but continue monitoring
                # Skip logging in test mode to prevent spam (similar to system_monitor)
                import os
                if os.environ.get('EPOCHLY_TEST_MODE') != '1':
                    self._logger.error(f"Error in monitoring loop: {e}")

    def _should_auto_stop(self) -> bool:
        """Check if orchestrator should auto-stop due to idle timeout (COORD-9)."""
        if self._config.idle_timeout is None:
            return False  # No idle timeout configured

        if self._always_on:
            return False  # Always-on mode never auto-stops

        # Check if idle timeout elapsed since last trigger
        idle_duration = time.time() - self._last_trigger_time
        return idle_duration >= self._config.idle_timeout

    def _check_adaptation_triggers(self) -> None:
        """Check for conditions that should trigger adaptation."""
        current_time = time.time()

        # Skip if too soon since last adaptation
        if current_time - self._last_adaptation_time < self._config.min_adaptation_interval:
            return

        # Check performance degradation
        if self._detect_performance_degradation():
            self._evaluate_and_adapt(AdaptationTrigger.PERFORMANCE_DEGRADATION)
            return

        # Check workload pattern change
        if self._detect_workload_change():
            self._evaluate_and_adapt(AdaptationTrigger.WORKLOAD_CHANGE)
            return

        # Check memory pressure
        if self._detect_memory_pressure():
            self._evaluate_and_adapt(AdaptationTrigger.MEMORY_PRESSURE)
            return

        # Check fragmentation threshold
        if self._detect_fragmentation_threshold():
            self._evaluate_and_adapt(AdaptationTrigger.FRAGMENTATION_THRESHOLD)
            return

        # Check JIT hot path opportunities
        if self._config.enable_jit_coordination and self._detect_jit_opportunities():
            self._evaluate_and_adapt(AdaptationTrigger.JIT_HOT_PATH_DETECTED)
            return

    def _evaluate_and_adapt(self, trigger: AdaptationTrigger) -> Optional[PoolRecommendation]:
        """Evaluate current state and adapt pool if beneficial."""
        with self._lock:
            current_time = time.time()

            # Get current workload and memory characteristics
            runtime_analysis = self._workload_detector.analyze_runtime({})
            workload_pattern = WorkloadPattern(runtime_analysis.get("current_workload", "mixed"))
            allocation_pattern = self._memory_profiler.detect_allocation_pattern()
            memory_stats = self._memory_profiler.get_current_stats()

            # Create selection criteria
            criteria = SelectionCriteria(
                workload_pattern=workload_pattern,
                allocation_pattern=allocation_pattern,
                memory_stats=memory_stats,
                thread_count=self._estimate_thread_count()
            )

            # Get workload characteristics for ML enhancement
            workload_characteristics = self._workload_detector._analyze_runtime_patterns()

            # Try ML-enhanced recommendation first
            ml_recommendation = self._get_ml_enhanced_recommendation(memory_stats, workload_characteristics)

            if ml_recommendation:
                self._logger.debug(f"Using ML-enhanced recommendation: {ml_recommendation}")
                best_recommendation = ml_recommendation
            else:
                # Fall back to rule-based pool selection
                recommendations = self._pool_selector.recommend_pool(criteria)

                if not recommendations:
                    return None

                best_recommendation = recommendations[0]
                self._logger.debug(f"Using rule-based recommendation: {best_recommendation}")

            # Check if adaptation is beneficial
            if not self._is_adaptation_beneficial(best_recommendation, trigger):
                return None

            # Record adaptation event
            current_performance = self._get_current_performance()
            adaptation_event = AdaptationEvent(
                trigger=trigger,
                timestamp=current_time,
                old_pool=self._current_pool,
                new_pool=best_recommendation.pool_type,
                performance_before=current_performance,
                metadata={
                    "workload_pattern": workload_pattern.value,
                    "allocation_pattern": allocation_pattern.value,
                    "confidence": best_recommendation.confidence,
                    "reasoning": best_recommendation.reasoning
                }
            )

            # Update state
            old_pool = self._current_pool
            self._current_pool = best_recommendation.pool_type
            self._last_adaptation_time = current_time
            self._adaptation_history.append(adaptation_event)

            # Notify callbacks
            for callback in self._pool_change_callbacks:
                try:
                    callback(old_pool, self._current_pool)
                except Exception as e:
                    self._logger.error(f"Error in pool change callback: {e}")

            # Learn from adaptation if enabled
            if self._config.enable_learning:
                self._learn_from_adaptation(adaptation_event)

            return self._current_pool

    def _detect_performance_degradation(self) -> bool:
        """Detect if performance has degraded significantly."""
        if not self._performance_history or self._baseline_performance is None:
            return False

        # Avoid division by zero
        if self._baseline_performance <= 0:
            return False

        # Get recent performance metrics
        recent_window = time.time() - self._config.performance_window
        recent_metrics = [
            metric for timestamp, metric in self._performance_history
            if timestamp >= recent_window
        ]

        if len(recent_metrics) < 5:
            return False

        current_avg = statistics.mean(recent_metrics)
        degradation = (self._baseline_performance - current_avg) / self._baseline_performance

        return degradation > self._config.adaptation_threshold

    def _detect_workload_change(self) -> bool:
        """Detect significant workload pattern changes using pattern analysis."""
        try:
            # Get current workload analysis
            runtime_analysis = self._workload_detector.analyze_runtime({})
            current_pattern = runtime_analysis.get("current_workload", "mixed")
            current_characteristics = runtime_analysis.get("characteristics")

            if not current_characteristics:
                return False

            # Get current memory statistics
            current_stats = self._memory_profiler.get_current_stats()

            # Compare with historical patterns (last 10 analyses)
            if not hasattr(self, '_pattern_history'):
                self._pattern_history = []

            # Store current pattern
            pattern_snapshot = {
                'timestamp': time.time(),
                'pattern': current_pattern,
                'parallelization_potential': current_characteristics.parallelization_potential,
                'cpu_intensity': current_characteristics.cpu_intensity,
                'memory_intensity': current_characteristics.memory_intensity,
                'allocation_frequency': current_stats.allocation_count / max(1, time.time() - getattr(self, '_start_time', time.time())),
                'thread_count': current_characteristics.thread_count
            }

            self._pattern_history.append(pattern_snapshot)

            # Keep only recent history
            if len(self._pattern_history) > 10:
                self._pattern_history = self._pattern_history[-10:]

            # Need at least 3 patterns for comparison
            if len(self._pattern_history) < 3:
                return False

            # Analyze pattern stability
            recent_patterns = [p['pattern'] for p in self._pattern_history[-5:]]
            older_patterns = [p['pattern'] for p in self._pattern_history[-10:-5]] if len(self._pattern_history) >= 10 else []

            # Check for pattern shift
            if older_patterns:
                recent_dominant = max(set(recent_patterns), key=recent_patterns.count)
                older_dominant = max(set(older_patterns), key=older_patterns.count)

                if recent_dominant != older_dominant:
                    self._logger.info(f"Workload pattern shift detected: {older_dominant} -> {recent_dominant}")
                    return True

            # Check for significant characteristic changes
            recent_data = self._pattern_history[-3:]
            older_data = self._pattern_history[-6:-3] if len(self._pattern_history) >= 6 else []

            if older_data:
                # Calculate average characteristics for recent vs older periods
                recent_parallel = sum(p['parallelization_potential'] for p in recent_data) / len(recent_data)
                older_parallel = sum(p['parallelization_potential'] for p in older_data) / len(older_data)

                recent_cpu = sum(p['cpu_intensity'] for p in recent_data) / len(recent_data)
                older_cpu = sum(p['cpu_intensity'] for p in older_data) / len(older_data)

                recent_memory = sum(p['memory_intensity'] for p in recent_data) / len(recent_data)
                older_memory = sum(p['memory_intensity'] for p in older_data) / len(older_data)

                # Check for significant changes (>30% change in key characteristics)
                parallel_change = abs(recent_parallel - older_parallel)
                cpu_change = abs(recent_cpu - older_cpu)
                memory_change = abs(recent_memory - older_memory)

                if parallel_change > 0.3 or cpu_change > 0.3 or memory_change > 0.3:
                    self._logger.info(f"Workload characteristics changed significantly: "
                                    f"parallel:{parallel_change:.2f}, cpu:{cpu_change:.2f}, memory:{memory_change:.2f}")
                    return True

            return False

        except Exception as e:
            self._logger.error(f"Error detecting workload change: {e}")
            return False

    def _detect_memory_pressure(self) -> bool:
        """Detect memory pressure conditions."""
        stats = self._memory_profiler.get_current_stats()

        # Check if current usage is high relative to peak
        if stats.peak_usage > 0:
            usage_ratio = stats.current_usage / stats.peak_usage
            return usage_ratio > 0.8  # 80% of peak usage

        return False

    def _detect_fragmentation_threshold(self) -> bool:
        """Detect if fragmentation exceeds threshold."""
        stats = self._memory_profiler.get_current_stats()
        return stats.fragmentation_ratio > self._config.fragmentation_threshold

    def _should_perform_periodic_optimization(self) -> bool:
        """Check if periodic optimization should be performed."""
        # Perform optimization every 10 minutes if no recent adaptations
        return (time.time() - self._last_adaptation_time) > 600.0

    def _is_adaptation_beneficial(
        self,
        recommendation: PoolScore,
        trigger: AdaptationTrigger
    ) -> bool:
        """Determine if adaptation would be beneficial."""
        # Don't adapt to the same pool
        if recommendation.pool_type == self._current_pool:
            return False

        # Require minimum confidence for adaptation
        if recommendation.confidence < 0.6:
            return False

        # For performance degradation, be more aggressive
        if trigger == AdaptationTrigger.PERFORMANCE_DEGRADATION:
            return recommendation.score > 0.5

        # For other triggers, require higher score improvement
        current_characteristics = self._pool_selector.get_pool_characteristics(self._current_pool)
        current_score = current_characteristics.get("performance_multiplier", 1.0)

        return recommendation.performance_estimate > current_score * 1.1  # 10% improvement

    def _get_current_performance(self) -> float:
        """Get current performance metric."""
        if self._performance_callback:
            return self._performance_callback()
        elif self._performance_history:
            return self._performance_history[-1][1]
        else:
            return 0.0

    def _estimate_thread_count(self) -> int:
        """Estimate current thread count from allocation patterns."""
        thread_activity = self._memory_profiler.get_thread_activity()
        return len(thread_activity) if thread_activity else 1

    def _predict_workload_evolution(
        self,
        current_pattern: WorkloadPattern,
        lookahead_seconds: float
    ) -> Optional[Dict[str, Any]]:
        """Predict how workload will evolve."""
        # Simplified prediction - in practice, this would use ML models
        # or more sophisticated pattern analysis

        # Assume workload characteristics remain similar
        return {
            "pattern": current_pattern,
            "allocation_pattern": self._memory_profiler.detect_allocation_pattern(),
            "thread_count": self._estimate_thread_count()
        }

    def _should_perform_jit_analysis(self) -> bool:
        """Check if JIT analysis should be performed."""
        current_time = time.time()
        return (current_time - self._last_jit_analysis_time) >= self._config.jit_analysis_interval

    def _analyze_jit_opportunities(self) -> None:
        """Analyze current workload for JIT compilation opportunities."""
        if not self._jit_analyzer or not self._jit_manager:
            return

        try:
            with self._lock:
                self._last_jit_analysis_time = time.time()

                # Get hot path candidates from JIT analyzer
                candidates = self._jit_analyzer.get_hot_path_candidates(
                    min_score=self._config.jit_hot_path_threshold
                )

                # Process high-priority candidates
                for candidate in candidates:
                    if self._should_compile_candidate(candidate):
                        self._initiate_jit_compilation(candidate)

        except Exception as e:
            self._logger.debug(f"Error in JIT opportunity analysis: {e}")

    def _detect_jit_opportunities(self) -> bool:
        """Detect if there are significant JIT compilation opportunities."""
        if not self._jit_analyzer:
            return False

        try:
            # Get current hot path candidates
            candidates = self._jit_analyzer.get_hot_path_candidates(
                min_score=self._config.jit_hot_path_threshold
            )

            # Check if any high-value candidates exist
            high_value_candidates = [
                c for c in candidates
                if c.should_compile and c.characteristics.estimated_speedup >= self._config.min_jit_benefit_threshold
            ]

            return len(high_value_candidates) > 0

        except Exception:
            return False

    def _should_compile_candidate(self, candidate: HotPathCandidate) -> bool:
        """Determine if a JIT candidate should be compiled."""
        func_name = candidate.function_name

        # Check if already being compiled
        if func_name in self._active_compilations:
            return False

        # Check concurrent compilation limit
        if len(self._active_compilations) >= self._config.max_concurrent_compilations:
            return False

        # Check minimum benefit threshold
        if candidate.characteristics.estimated_speedup < self._config.min_jit_benefit_threshold:
            return False

        # Check if compilation is actually beneficial based on call frequency
        if candidate.characteristics.call_count < candidate.characteristics.break_even_calls:
            return False

        return True

    def _initiate_jit_compilation(self, candidate: HotPathCandidate) -> None:
        """Initiate JIT compilation for a candidate function."""
        if not self._jit_manager:
            return

        func_name = candidate.function_name

        try:
            with self._lock:
                self._active_compilations.add(func_name)

            # This would integrate with the actual JIT manager
            # Simulate compilation process for testing
            self._logger.info(f"Initiating JIT compilation for {func_name} "
                  f"(score: {candidate.hot_path_score:.1f}, "
                  f"expected speedup: {candidate.characteristics.estimated_speedup:.2f}x)")

            # Record compilation attempt
            self._function_compilation_history[func_name].append(time.time())

        except Exception as e:
            self._logger.error(f"Error initiating JIT compilation for {func_name}: {e}")
            with self._lock:
                self._active_compilations.discard(func_name)

    def record_jit_performance_gain(self, func_name: str, speedup_ratio: float) -> None:
        """Record performance gain from JIT compilation."""
        with self._lock:
            self._jit_performance_gains[func_name] = speedup_ratio
            self._active_compilations.discard(func_name)

        # If significant performance gain, consider triggering adaptation
        if speedup_ratio >= self._config.min_jit_benefit_threshold:
            self.trigger_adaptation(AdaptationTrigger.JIT_PERFORMANCE_OPPORTUNITY)

    def get_jit_statistics(self) -> Dict[str, Any]:
        """Get JIT coordination statistics."""
        with self._lock:
            return {
                "jit_coordination_enabled": self._config.enable_jit_coordination,
                "active_compilations": len(self._active_compilations),
                "compiled_functions": len(self._jit_performance_gains),
                "average_speedup": (
                    sum(self._jit_performance_gains.values()) / len(self._jit_performance_gains)
                    if self._jit_performance_gains else 0.0
                ),
                "total_compilation_attempts": sum(
                    len(history) for history in self._function_compilation_history.values()
                ),
                "hot_path_threshold": self._config.jit_hot_path_threshold,
                "min_benefit_threshold": self._config.min_jit_benefit_threshold
            }

    def _learn_from_adaptation(self, event: AdaptationEvent) -> None:
        """Learn from adaptation outcomes to improve future decisions."""
        # Record adaptation pattern for learning
        pattern_key = f"{event.trigger.value}_{event.old_pool.value if event.old_pool else 'none'}_{event.new_pool.value}"

        # Traditional rule-based learning
        if event.performance_after and event.performance_before:
            # Avoid division by zero - check for non-zero performance_before
            if event.performance_before > 0:
                improvement = (event.performance_after - event.performance_before) / event.performance_before
                self._adaptation_patterns[pattern_key].append(improvement)
            else:
                # If performance_before is 0, can't calculate improvement ratio
                return

            # ML-enhanced learning with graceful fallback
            self._update_ml_with_outcome(
                event.new_pool,
                event.performance_before,
                event.performance_after
            )

            # Keep only recent learning data
            if len(self._adaptation_patterns[pattern_key]) > 100:
                self._adaptation_patterns[pattern_key] = self._adaptation_patterns[pattern_key][-100:]

    def _initialize_ml_predictor(self):
        """Initialize ML predictor with LSTM-RNN as primary, fallback to lightweight linear model."""
        try:
            # First try to use the proper LSTM predictor from ml module
            from ...ml.performance_predictors import LSTMResourcePredictor

            self._logger.info("Initializing LSTM-RNN neural orchestrator for adaptive optimization")
            return LSTMResourcePredictor(
                sequence_length=10,
                hidden_size=32,
                learning_rate=0.001
            )

        except ImportError as e:
            self._logger.info(f"LSTM predictor unavailable ({e}), falling back to lightweight linear model")
            try:
                # Fall back to lightweight linear model when full LSTM unavailable
                import numpy as np
                return LightweightMLPredictor()

            except ImportError:
                self._logger.info("NumPy unavailable, ML prediction disabled - using rule-based optimization only")
                return None

        except Exception as e:
            self._logger.warning(f"ML predictor initialization failed: {e} - using rule-based optimization")
            return None

    def _initialize_rl_scheduler(self):
        """Initialize RL scheduler with graceful fallback."""
        try:
            # Only initialize if ML predictor is available
            if self._ml_predictor:
                return LightweightRLScheduler()
            return None

        except Exception as e:
            self._logger.warning(f"RL scheduler initialization failed: {e} - using rule-based scheduling")
            return None

    def _get_ml_enhanced_recommendation(self,
                                      current_stats: 'MemoryStats',
                                      workload_characteristics: 'WorkloadCharacteristics') -> Optional[PoolScore]:
        """Get ML-enhanced pool recommendation with rule-based fallback."""
        if not self._ml_enabled or not self._ml_predictor:
            return None  # Fall back to rule-based selection

        try:
            # Convert current state to ML features
            resource_metrics = self._convert_to_resource_metrics(current_stats, workload_characteristics)
            self._resource_metrics_history.append(resource_metrics)

            # Need sufficient history for ML prediction
            if len(self._resource_metrics_history) < 5:
                return None  # Not enough data, use rules

            # Get ML prediction for memory bandwidth saturation
            prediction_result = self._ml_predictor.predict_memory_bandwidth_saturation(
                list(self._resource_metrics_history)[-10:]  # Last 10 samples
            )

            # Convert ML prediction to pool recommendation
            if prediction_result and prediction_result.confidence > 0.6:
                return self._ml_prediction_to_pool_recommendation(prediction_result, workload_characteristics)

            return None  # Low confidence, fall back to rules

        except Exception as e:
            self._logger.debug(f"ML recommendation failed: {e}")
            return None  # Fall back to rule-based selection

    def _convert_to_resource_metrics(self, stats: 'MemoryStats', characteristics: 'WorkloadCharacteristics') -> 'ResourceMetrics':
        """Convert Epochly stats to ML ResourceMetrics format."""
        from dataclasses import dataclass

        @dataclass
        class ResourceMetrics:
            timestamp: float
            memory_pressure_indicator: float
            cpu_utilization: float
            cache_miss_rate: float
            context_switch_rate: float
            allocation_rate: float
            thread_count: int

        # Convert Epochly metrics to ML format with reasonable approximations
        current_time = time.time()

        # Estimate bandwidth utilization from allocation patterns
        bandwidth_util = min(stats.allocation_count / 1000.0, 1.0) if hasattr(stats, 'allocation_count') else 0.5

        # Use workload characteristics for CPU and cache estimates
        cpu_util = characteristics.cpu_intensity
        cache_miss_rate = getattr(characteristics, 'l1_cache_miss_rate', 0.0)

        # Estimate allocation rate
        alloc_rate = characteristics.allocation_frequency * characteristics.average_allocation_size

        return ResourceMetrics(
            timestamp=current_time,
            memory_pressure_indicator=bandwidth_util,
            cpu_utilization=cpu_util,
            cache_miss_rate=cache_miss_rate,
            context_switch_rate=0.0,  # Not available in current metrics
            allocation_rate=alloc_rate,
            thread_count=characteristics.thread_count
        )

    def _ml_prediction_to_pool_recommendation(self,
                                            prediction_result,
                                            characteristics: 'WorkloadCharacteristics') -> PoolScore:
        """Convert ML prediction to pool recommendation using workload strategies."""
        # Determine workload strategy based on saturation and characteristics
        strategy = self._determine_workload_strategy(prediction_result, characteristics)

        # Get pool configuration for the strategy
        pool_config = self._pool_strategy.get_pool_for_strategy(strategy)

        # Create PoolScore with the recommended pool type
        return PoolScore(
            pool_type=pool_config.pool_type,
            score=prediction_result.confidence * pool_config.expected_benefit,
            confidence=prediction_result.confidence,
            reasoning=[f"ML prediction: {pool_config.rationale}"],
            performance_estimate=pool_config.expected_benefit,
            memory_efficiency=0.85  # Conservative estimate
        )

    def _determine_workload_strategy(self, prediction_result, characteristics) -> WorkloadStrategy:
        """Determine the workload strategy based on ML prediction and characteristics."""
        # First check for framework-specific patterns
        framework_strategy = self._detect_framework_strategy(characteristics)
        if framework_strategy:
            return framework_strategy

        # High saturation predicted - use memory-optimized strategies
        if prediction_result.predicted_value > 0.7:
            if characteristics.memory_intensity > 0.7:
                return WorkloadStrategy.MEMORY_INTENSIVE
            else:
                return WorkloadStrategy.LARGE_BLOCK_OPTIMIZED

        # Low saturation - can use performance-optimized strategies
        elif prediction_result.predicted_value < 0.3:
            if characteristics.parallelization_potential > 0.7:
                return WorkloadStrategy.LOW_LATENCY
            else:
                return WorkloadStrategy.GENERAL_PURPOSE

        # Medium saturation - balanced approach
        else:
            return WorkloadStrategy.BALANCED

    def _detect_framework_strategy(self, characteristics) -> Optional[WorkloadStrategy]:
        """Detect framework-specific workload patterns and return appropriate strategy."""
        # Check for NumPy patterns
        if hasattr(characteristics, 'pattern') and characteristics.pattern in [
            WorkloadPattern.NUMPY_VECTORIZED,
            WorkloadPattern.NUMPY_LINALG
        ]:
            return WorkloadStrategy.NUMPY_OPTIMIZED

        # Check for Pandas patterns
        if hasattr(characteristics, 'pattern') and characteristics.pattern in [
            WorkloadPattern.PANDAS_DATAFRAME,
            WorkloadPattern.PANDAS_GROUPBY
        ]:
            return WorkloadStrategy.PANDAS_OPTIMIZED

        # Check for scikit-learn patterns
        if hasattr(characteristics, 'pattern') and characteristics.pattern in [
            WorkloadPattern.SKLEARN_TRAINING,
            WorkloadPattern.SKLEARN_INFERENCE
        ]:
            return WorkloadStrategy.SKLEARN_OPTIMIZED

        # Check by complexity scores
        if hasattr(characteristics, 'numpy_operation_complexity') and characteristics.numpy_operation_complexity > 0.7:
            return WorkloadStrategy.NUMPY_OPTIMIZED

        if hasattr(characteristics, 'pandas_groupby_complexity') and characteristics.pandas_groupby_complexity > 0.7:
            return WorkloadStrategy.PANDAS_OPTIMIZED

        if hasattr(characteristics, 'sklearn_model_complexity') and characteristics.sklearn_model_complexity > 0.7:
            return WorkloadStrategy.SKLEARN_OPTIMIZED

        return None

    def _update_ml_with_outcome(self,
                               recommendation: PoolRecommendation,
                               performance_before: float,
                               performance_after: float) -> None:
        """Update ML models with adaptation outcome."""
        if not self._ml_enabled or not self._ml_predictor:
            return

        try:
            # Calculate actual memory bandwidth saturation from performance change
            performance_ratio = performance_after / performance_before if performance_before > 0 else 1.0

            # Estimate saturation level from performance (inverse relationship)
            actual_saturation = max(0.0, min(1.0, 2.0 - performance_ratio))

            # Provide feedback to ML predictor
            if len(self._resource_metrics_history) >= 5:
                recent_metrics = list(self._resource_metrics_history)[-5:]
                self._ml_predictor.update_with_outcome(recent_metrics, actual_saturation)

        except Exception as e:
            self._logger.debug(f"ML outcome update failed: {e}")

    def _get_ml_statistics(self) -> Dict[str, Any]:
        """Get ML system statistics for monitoring."""
        try:
            ml_stats = {
                "ml_enabled": self._ml_enabled,
                "predictor_available": self._ml_predictor is not None,
                "rl_scheduler_available": self._rl_scheduler is not None,
                "resource_metrics_history_size": len(self._resource_metrics_history),
            }

            # Add predictor-specific statistics
            if self._ml_predictor and hasattr(self._ml_predictor, 'prediction_accuracy'):
                ml_stats.update({
                    "prediction_accuracy_samples": len(self._ml_predictor.prediction_accuracy),
                    "average_prediction_accuracy": (
                        self._ml_predictor.np.mean(self._ml_predictor.prediction_accuracy)
                        if self._ml_predictor.prediction_accuracy else 0.0
                    ),
                    "model_learning_rate": getattr(self._ml_predictor, 'learning_rate', 0.0)
                })

            # Add RL scheduler statistics
            if self._rl_scheduler and hasattr(self._rl_scheduler, 'q_values'):
                ml_stats.update({
                    "q_table_states": len(self._rl_scheduler.q_values),
                    "exploration_rate": getattr(self._rl_scheduler, 'epsilon', 0.0),
                    "strategy_performance_tracked": len(getattr(self._rl_scheduler, 'strategy_performance', {}))
                })

            return ml_stats

        except Exception as e:
            self._logger.debug(f"Failed to get ML statistics: {e}")
            return {"ml_enabled": False, "error": str(e)}

    def export_learning_data(self) -> Dict[str, Any]:
        """Export learning data for persistence or analysis."""
        return {
            "timestamp": time.time(),
            "adaptation_history": [
                {
                    "trigger": event.trigger.value,
                    "timestamp": event.timestamp,
                    "old_pool": event.old_pool.value if event.old_pool else None,
                    "new_pool": event.new_pool.value,
                    "performance_before": event.performance_before,
                    "performance_after": event.performance_after,
                    "metadata": event.metadata
                }
                for event in self._adaptation_history
            ],
            "config": {
                "adaptation_threshold": self._config.adaptation_threshold,
                "monitoring_interval": self._config.monitoring_interval,
                "enable_predictive_adaptation": self._config.enable_predictive_adaptation,
                "enable_learning": self._config.enable_learning
            }
        }

    def import_learning_data(self, data: Dict[str, Any]) -> None:
        """Import learning data from persistence."""
        if "adaptation_history" in data:
            self._adaptation_history.clear()
            for event_data in data["adaptation_history"]:
                event = AdaptationEvent(
                    trigger=AdaptationTrigger(event_data["trigger"]),
                    timestamp=event_data["timestamp"],
                    old_pool=PoolRecommendation(event_data["old_pool"]) if event_data["old_pool"] else None,
                    new_pool=PoolRecommendation(event_data["new_pool"]),
                    performance_before=event_data["performance_before"],
                    performance_after=event_data.get("performance_after"),
                    metadata=event_data.get("metadata", {})
                )
                self._adaptation_history.append(event)

    def on_hot_path_detected(
        self,
        function_name: str,
        cpu_time_ms: float,
        code_object: Any,
        hot_loop_info: Any
    ) -> Dict[str, Any]:
        """
        Handle hot path detection from AutoProfiler.

        Queries LSTM predictor to decide optimization strategy.

        Args:
            function_name: Name of the hot function
            cpu_time_ms: CPU time spent in function
            code_object: Python code object
            hot_loop_info: HotLoopInfo from AutoProfiler

        Returns:
            Dict with optimization recommendation:
            {
                'optimize_recommended': bool,
                'predicted_speedup': float,
                'confidence': float,
                'use_jit': bool,
                'use_batch_dispatch': bool,
                'recommended_workers': int
            }
        """
        try:
            # Extract features for LSTM prediction
            features = self._extract_features_from_hot_loop(
                function_name, cpu_time_ms, code_object, hot_loop_info
            )

            # Query LSTM predictor if available
            if self._ml_predictor and hasattr(self._ml_predictor, 'predict_from_features'):
                try:
                    # Use LSTM to predict optimization benefit from hot-loop features
                    # Fix #3 (Dec 2025): Use predict_from_features for feature dict input
                    # (not predict_memory_bandwidth_saturation which expects List[ResourceMetrics])
                    prediction_result = self._ml_predictor.predict_from_features(features)
                    saturation_prob = prediction_result.predicted_value
                    confidence = prediction_result.confidence

                    # REFINEMENT #5: Reject low-confidence predictions (likely fallbacks)
                    if confidence < 0.4:
                        self._logger.debug(
                            f"ML confidence too low ({confidence:.2f}), using rule-based for {function_name}"
                        )
                        raise ValueError("Low-confidence prediction - use rule-based")

                    # Convert saturation probability to speedup prediction
                    # Lower saturation = higher speedup potential
                    predicted_speedup = 1.0 + (1.0 - saturation_prob) * 4.0  # 1-5× range

                    # Make recommendation based on prediction (only for high-confidence results)
                    optimize_recommended = (
                        confidence > 0.6 and  # Reasonable confidence
                        predicted_speedup > 1.2  # At least 20% speedup
                    )

                    recommendation = {
                        'optimize_recommended': optimize_recommended,
                        'predicted_speedup': predicted_speedup,
                        'confidence': confidence,
                        'use_jit': predicted_speedup > 1.2,
                        'use_batch_dispatch': predicted_speedup > 2.0 and cpu_time_ms > 50.0,
                        'recommended_workers': min(8, max(2, int(predicted_speedup)))
                    }

                    self._logger.debug(
                        f"LSTM prediction for {function_name}: "
                        f"speedup={predicted_speedup:.2f}x, confidence={confidence:.2f}, "
                        f"recommend={'optimize' if optimize_recommended else 'skip'}"
                    )

                    return recommendation

                except Exception as e:
                    self._logger.warning(f"LSTM prediction failed: {e}, using rule-based")

            # Fallback: Rule-based recommendation
            return self._rule_based_recommendation(cpu_time_ms)

        except Exception as e:
            self._logger.error(f"Hot path handling failed: {e}")
            # Safe fallback: recommend optimization
            return {'optimize_recommended': True}

    def _extract_features_from_hot_loop(
        self,
        function_name: str,
        cpu_time_ms: float,
        code_object: Any,
        hot_loop_info: Any
    ) -> Dict[str, float]:
        """
        Extract features from hot loop for LSTM prediction.

        Returns:
            Feature dict for LSTM input
        """
        return {
            'cpu_time_ms': cpu_time_ms,
            'iteration_count': getattr(hot_loop_info, 'iteration_count', 1),
            'code_size': len(code_object.co_code) if hasattr(code_object, 'co_code') else 0,
            'function_complexity': len(code_object.co_names) if hasattr(code_object, 'co_names') else 0
        }

    def _rule_based_recommendation(self, cpu_time_ms: float) -> Dict[str, Any]:
        """
        Rule-based optimization recommendation (fallback when LSTM unavailable).

        Args:
            cpu_time_ms: CPU time in milliseconds

        Returns:
            Recommendation dict
        """
        # Simple rule: Optimize if >10ms
        if cpu_time_ms > 10.0:
            return {
                'optimize_recommended': True,
                'predicted_speedup': 2.0,  # Conservative estimate
                'confidence': 0.5,  # Low confidence (rule-based)
                'use_jit': True,
                'use_batch_dispatch': cpu_time_ms > 100.0,  # Only for substantial workloads
                'recommended_workers': 4
            }
        else:
            return {
                'optimize_recommended': False,
                'predicted_speedup': 1.0,
                'confidence': 0.8,
                'use_jit': False,
                'use_batch_dispatch': False,
                'recommended_workers': 0
            }

    def on_optimization_result(self, result: Dict[str, Any]) -> None:
        """
        Receive optimization result feedback for online learning.

        Updates LSTM weights based on actual vs predicted performance.

        Args:
            result: Dict with:
                - function_name: str
                - predicted_speedup: float
                - actual_speedup: float
                - prediction_error: float
        """
        try:
            if self._ml_predictor and hasattr(self._ml_predictor, 'update'):
                # Feed back to LSTM for online learning
                self._ml_predictor.update(
                    predicted=result.get('predicted_speedup', 1.0),
                    actual=result.get('actual_speedup', 1.0),
                    error=result.get('prediction_error', 0.0)
                )

                self._logger.debug(
                    f"LSTM learning: {result['function_name']} "
                    f"predicted={result['predicted_speedup']:.2f}x, "
                    f"actual={result['actual_speedup']:.2f}x"
                )

        except Exception as e:
            self._logger.warning(f"Failed to update LSTM: {e}")

    def emergency_stop(self) -> None:
        """Emergency stop of orchestrator and cleanup."""
        self.stop_monitoring()
        with self._lock:
            self._active_compilations.clear()
            self._monitoring_active = False

    def _trim_history(self) -> None:
        """Trim adaptation history to configured maximum."""
        # The deque automatically maintains the max size, so this is a no-op
        # unless we need to trim based on age or other criteria
        pass


class LightweightMLPredictor:
    """Lightweight ML predictor using numpy-only implementation."""

    def __init__(self):
        import numpy as np
        self.np = np

        # Simple linear model weights (much lighter than full LSTM)
        self.weights = self.np.random.normal(0, 0.1, 6)  # 6 features
        self.bias = 0.0
        self.learning_rate = 0.01

        # Prediction history for confidence calculation
        self.prediction_accuracy = []

    def predict_memory_bandwidth_saturation(self, metrics_list):
        """Predict memory bandwidth saturation using linear model."""
        if len(metrics_list) < 3:
            return self._default_prediction()

        try:
            # Convert metrics to feature vector
            features = self._metrics_to_features(metrics_list[-3:])  # Use last 3 samples

            # Linear prediction
            prediction = self.np.dot(features, self.weights) + self.bias
            prediction = 1.0 / (1.0 + self.np.exp(-prediction))  # Sigmoid

            # Calculate confidence from prediction history
            confidence = self._calculate_confidence()

            from dataclasses import dataclass

            @dataclass
            class PredictionResult:
                predicted_value: float
                confidence: float
                timestamp: float

            return PredictionResult(
                predicted_value=float(prediction),
                confidence=confidence,
                timestamp=time.time()
            )

        except Exception:
            return self._default_prediction()

    def _metrics_to_features(self, metrics_list):
        """Convert metrics to feature vector."""
        # Average the metrics
        avg_bandwidth = self.np.mean([m.memory_pressure_indicator for m in metrics_list])
        avg_cpu = self.np.mean([m.cpu_utilization for m in metrics_list])
        avg_cache = self.np.mean([m.cache_miss_rate for m in metrics_list])
        avg_allocation = self.np.mean([m.allocation_rate for m in metrics_list])
        avg_threads = self.np.mean([m.thread_count for m in metrics_list])

        # Trend (simple derivative)
        if len(metrics_list) >= 2:
            trend = metrics_list[-1].memory_pressure_indicator - metrics_list[-2].memory_pressure_indicator
        else:
            trend = 0.0

        return self.np.array([avg_bandwidth, avg_cpu, avg_cache, avg_allocation/1e6, avg_threads/10.0, trend])

    def _calculate_confidence(self):
        """Calculate prediction confidence."""
        if len(self.prediction_accuracy) < 3:
            return 0.5  # Default confidence

        recent_accuracy = self.prediction_accuracy[-10:]  # Last 10 predictions
        return min(0.95, self.np.mean(recent_accuracy))

    def _default_prediction(self):
        """Default prediction when ML fails."""
        from dataclasses import dataclass

        @dataclass
        class PredictionResult:
            predicted_value: float
            confidence: float
            timestamp: float

        return PredictionResult(
            predicted_value=0.5,  # Conservative estimate
            confidence=0.2,       # Low confidence
            timestamp=time.time()
        )

    def update_with_outcome(self, metrics_list, actual_saturation):
        """Update model with actual outcome."""
        try:
            features = self._metrics_to_features(metrics_list[-3:])

            # Simple gradient descent update
            prediction = self.np.dot(features, self.weights) + self.bias
            prediction = 1.0 / (1.0 + self.np.exp(-prediction))

            error = actual_saturation - prediction

            # Update weights
            self.weights += self.learning_rate * error * features
            self.bias += self.learning_rate * error

            # Track accuracy
            accuracy = 1.0 - abs(error)
            self.prediction_accuracy.append(accuracy)

            # Keep only recent accuracy data
            if len(self.prediction_accuracy) > 100:
                self.prediction_accuracy = self.prediction_accuracy[-100:]

        except Exception:
            pass  # Fail silently


class LightweightRLScheduler:
    """Lightweight RL scheduler for strategy selection."""

    def __init__(self):
        import numpy as np
        self.np = np

        # Simple Q-table using dictionaries
        self.q_values = {}
        self.learning_rate = 0.1
        self.epsilon = 0.1  # Exploration rate

        # Performance tracking
        self.strategy_performance = {}

    def select_strategy(self, workload_state):
        """Select strategy using epsilon-greedy."""
        state_key = self._state_to_key(workload_state)

        # Epsilon-greedy selection
        if self.np.random.random() < self.epsilon:
            # Explore: random strategy
            strategies = ["general", "memory_intensive", "low_latency", "large_block"]
            return self.np.random.choice(strategies)
        else:
            # Exploit: best known strategy
            if state_key in self.q_values:
                return max(self.q_values[state_key], key=self.q_values[state_key].get)
            else:
                return "general"  # Default

    def _state_to_key(self, workload_state):
        """Convert workload state to discrete key."""
        # Simple state discretization
        cpu_bucket = int(workload_state.cpu_utilization * 10)
        mem_bucket = int(workload_state.memory_pressure_indicator * 10)
        return f"{cpu_bucket}_{mem_bucket}"

    def update_with_reward(self, state_key, strategy, reward):
        """Update Q-values with reward."""
        if state_key not in self.q_values:
            self.q_values[state_key] = {}

        if strategy not in self.q_values[state_key]:
            self.q_values[state_key][strategy] = 0.0

        # Simple Q-learning update
        old_q = self.q_values[state_key][strategy]
        self.q_values[state_key][strategy] = old_q + self.learning_rate * (reward - old_q)
