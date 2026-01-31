"""
Epochly Performance Monitor

Real-time performance monitoring and metrics collection for the Epochly framework.
"""

import time
import threading
import queue
from typing import Dict, Any, Optional, List, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
import statistics

from ..utils.logger import get_logger
from ..utils.config import get_config
from ..utils.decorators import thread_safe


@dataclass
class PerformanceMetric:
    """Container for performance metric data."""
    name: str
    value: float
    unit: str
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """Statistical summary of performance metrics."""
    count: int
    mean: float
    median: float
    min_value: float
    max_value: float
    std_dev: float
    percentile_95: float
    percentile_99: float


class PerformanceMonitor:
    """
    Real-time performance monitoring system for Epochly.

    Collects, aggregates, and reports performance metrics with
    configurable retention and export capabilities.

    IO-8 Enhancement: Surfaces monitoring back-pressure by tracking
    dropped metrics and integrating with platform-native logging.
    """

    def __init__(
        self,
        *,
        queue_size: Optional[int] = None,
        batch_size: Optional[int] = None,
        batch_interval_ms: Optional[int] = None,
        flush_interval: Optional[float] = None
    ):
        """
        Initialize the performance monitor with adaptive batching and drop reporting.

        Per perf_fixes.md Task 4: Configuration knobs exposed via constructor.

        Args:
            queue_size: Maximum queue capacity (default: 10000 from config)
            batch_size: Metrics per batch (default: 100 from config)
            batch_interval_ms: Batch flush interval in ms (default: 100 from config)
            flush_interval: Alias for batch_interval_ms in seconds (optional)
        """
        self.logger = get_logger(__name__)
        self.config = get_config()

        # Monitoring state
        self._active = False
        self._thread = None
        self._stop_event = threading.Event()

        # ========== TASK 5: ADAPTIVE BATCHING IMPROVEMENTS ==========

        # Batching configuration (constructor params override config)
        self._batch_interval_ms = (
            batch_interval_ms
            if batch_interval_ms is not None
            else int(flush_interval * 1000) if flush_interval is not None
            else self.config.get('monitoring.batch_interval_ms', 100)
        )
        self._batch_size = (
            batch_size
            if batch_size is not None
            else self.config.get('monitoring.batch_size', 100)
        )
        self._queue_limit = (
            queue_size
            if queue_size is not None
            else self.config.get('monitoring.queue_limit', 10000)
        )

        # Replace queue.Queue with deque for back-pressure
        # When full, oldest entries are automatically evicted (no blocking)
        self._metrics_queue = deque(maxlen=self._queue_limit)
        self._queue_lock = threading.Lock()  # Protects deque operations
        self._condition = threading.Condition(self._queue_lock)  # For batching

        # ========== IO-8: DROP TRACKING AND ALERTING ==========

        # Track dropped metrics (when queue full)
        self._metrics_dropped = 0
        self._total_metrics_attempted = 0  # Total metrics attempted to record
        self._last_drop_alert = 0  # Last drop count when alert was emitted
        self._drop_alert_interval = self.config.get('monitoring.drop_alert_interval', 100)  # Alert every N drops

        # SPEC2 Task 4: Background alert worker (prevents blocking monitor loop)
        # P2-2 FIX (Dec 2025): Lazy initialization - only create when first alert is emitted
        # This saves 1 daemon thread when alerts are never used
        self._alert_worker = None
        self._alert_worker_initialized = False

        # SPEC2 Task 3: RingBufferMonitor for lock-free high-throughput monitoring
        # P2-2 FIX (Dec 2025): Lazy initialization - only create when explicitly enabled
        # This saves 1 daemon thread in normal operation
        self._ring_buffer_monitor = None
        self._ring_buffer_enabled = self.config.get('monitoring.enable_ring_buffer', False)

        # Platform logger (lazy-loaded)
        self._platform_logger = None

        # ========== ORIGINAL MONITOR STATE (Preserved) ==========

        # SPEC2 Task 8: Use AdaptiveBuffer instead of fixed deques
        try:
            from .adaptive_buffer import AdaptiveBuffer
            # Verify AdaptiveBuffer has required API
            test_buffer = AdaptiveBuffer()
            list(test_buffer)  # Verify __iter__ works
            self._use_adaptive_buffers_history = True
            self._metrics_history_adaptive: Dict[str, AdaptiveBuffer] = {}
            self.logger.info("Adaptive metric buffers enabled for history (dynamic sizing)")
        except (ImportError, Exception) as e:
            self.logger.debug(f"AdaptiveBuffer not available: {e}")
            self._use_adaptive_buffers_history = False
            self._metrics_history_adaptive = None

        self._metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self._aggregated_stats = {}
        self._lock = threading.RLock()

        # Configuration
        self._interval = self.config.get('monitoring.interval', 1.0)
        self._retention_seconds = self.config.get('monitoring.metrics_retention', 3600)
        self._max_queue_size = 10000  # Kept for backward compatibility

        # Callbacks for metric events
        self._metric_callbacks = []
        self._threshold_callbacks = {}

        # ========== TASK 1 PHASE 2: SNAPSHOT EMISSION (perf_fixes2.md) ==========
        # Snapshot callbacks for progressive enhancement feedback loop
        self._snapshot_callbacks: List[Callable] = []
        self._last_snapshot_time = 0.0
        self._last_drop_spike_snapshot = 0.0  # Rate limiting for drop spike snapshots
        self._drop_spike_cooldown = 5.0  # Minimum 5 seconds between drop spike snapshots
        self._baseline_throughput = 1.0  # Will be updated dynamically
        self._allocator = None  # Will be set by EpochlyCore if available

        # ThreadPoolExecutor for non-blocking snapshot emission
        from concurrent.futures import ThreadPoolExecutor
        self._snapshot_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="Snapshot-Emit")

        # Performance thresholds
        self._thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'response_time': 1.0,
            'error_rate': 5.0,
        }

    def start(self) -> bool:
        """
        Start the performance monitoring system.

        Returns:
            bool: True if started successfully
        """
        if self._active:
            self.logger.warning("Performance monitor already active")
            return True

        try:
            self.logger.info("Starting performance monitor")

            # Reset state
            self._stop_event.clear()

            # SPEC2 Task 4: AlertWorker is now lazy-initialized (P2-2 FIX)
            # It will be created and started on first alert via _get_alert_worker()

            # SPEC2 Task 3: RingBufferMonitor - only start if explicitly enabled
            # P2-2 FIX: Saves 1 daemon thread in normal operation
            if self._ring_buffer_enabled and self._ring_buffer_monitor is None:
                try:
                    from .ring_buffer_wrapper import RingBufferMonitor
                    self._ring_buffer_monitor = RingBufferMonitor()
                    self._ring_buffer_monitor.start()
                    self.logger.debug("RingBufferMonitor started (enabled via config)")
                except ImportError as e:
                    self.logger.debug(f"RingBufferMonitor unavailable: {e}")

            # Start monitoring thread as daemon (data loss on exit is acceptable)
            # Expert consensus: daemon=True for non-critical monitoring
            self._thread = threading.Thread(
                target=self._monitoring_loop,
                name="Epochly-PerformanceMonitor",
                daemon=True  # Monitoring data loss acceptable, prevents pytest hang
            )
            self._thread.start()

            self._active = True
            self.logger.info("Performance monitor started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start performance monitor: {e}")
            return False

    def stop(self, reset: bool = True):
        """Stop the performance monitoring system.

        Args:
            reset: Whether to reset all metrics after stopping (default: True)
        """
        if not self._active:
            return

        try:
            self.logger.info("Stopping performance monitor")

            # Flush pending metrics before stopping (ensures stats are up-to-date)
            batch = []
            with self._queue_lock:
                while self._metrics_queue:
                    batch.append(self._metrics_queue.popleft())

            if batch:
                self._process_batch(batch)  # Updates stats internally (line 624)

            # Note: Stats are already up-to-date from _process_batch()
            # No need for redundant _update_aggregated_stats() call

            # Signal stop and wait for thread
            self._stop_event.set()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5.0)

            # SPEC2 Task 4: Stop alert worker
            if self._alert_worker:
                self._alert_worker.stop(timeout=3.0)
                self.logger.debug("AlertWorker stopped")

            # SPEC2 Task 3: Stop ring buffer monitor
            if self._ring_buffer_monitor:
                try:
                    # RingBufferMonitor.stop() doesn't accept timeout
                    self._ring_buffer_monitor.stop()
                    self.logger.debug("RingBufferMonitor stopped")
                except Exception as e:
                    self.logger.debug(f"Error stopping RingBufferMonitor: {e}")

            # TASK 1 PHASE 2: Shutdown snapshot executor
            if hasattr(self, '_snapshot_executor'):
                try:
                    # ThreadPoolExecutor.shutdown() doesn't accept timeout parameter
                    self._snapshot_executor.shutdown(wait=True, cancel_futures=False)
                    self.logger.debug("Snapshot executor shutdown complete")
                except Exception as e:
                    self.logger.debug(f"Error shutting down snapshot executor: {e}")

            self._active = False
            self.logger.info("Performance monitor stopped")

            if reset:
                self.reset_metrics()

        except Exception as e:
            self.logger.error(f"Error stopping performance monitor: {e}")

    def is_active(self) -> bool:
        """Check if the monitor is active."""
        return self._active

    def __del__(self):
        """Ensure thread stops when instance is garbage collected."""
        try:
            if hasattr(self, '_active') and self._active:
                self.stop()
            # Shutdown snapshot executor
            if hasattr(self, '_snapshot_executor'):
                self._snapshot_executor.shutdown(wait=False)
        except:
            pass  # Best effort during GC

    # ========== TASK 1 PHASE 2: SNAPSHOT EMISSION METHODS ==========

    def add_snapshot_callback(self, callback: Callable):
        """
        Register callback to receive LevelHealthSnapshot updates.

        Callbacks are invoked asynchronously (non-blocking) on flush intervals
        and when drop spikes occur. This enables the EnhancementProgressionManager
        to make automatic upgrade/rollback decisions based on real-time metrics.

        Args:
            callback: Function accepting LevelHealthSnapshot
                     Signature: def callback(snapshot: LevelHealthSnapshot) -> None

        Example:
            >>> from epochly.monitoring.performance_monitor import PerformanceMonitor
            >>> monitor = PerformanceMonitor()
            >>> def on_snapshot(snapshot):
            ...     print(f"Level {snapshot.level.name}: throughput={snapshot.throughput_ratio:.2f}")
            >>> monitor.add_snapshot_callback(on_snapshot)
            >>> monitor.start()
        """
        if callback not in self._snapshot_callbacks:
            self._snapshot_callbacks.append(callback)
            callback_name = getattr(callback, '__name__', repr(callback))
            self.logger.debug(f"Snapshot callback registered: {callback_name}")

    def _emit_snapshot(self):
        """
        Emit LevelHealthSnapshot to all registered callbacks.

        Invoked on flush interval and drop spikes. Callbacks run in
        background threads via ThreadPoolExecutor to avoid blocking the
        monitoring loop.

        Snapshot Content:
        - level: Current EnhancementLevel from EpochlyCore
        - throughput_ratio: Current/baseline throughput (>1.0 = improvement)
        - error_rate: Errors per second over recent history
        - allocator_fast_path: Whether Cython allocator is active
        - timestamp: Unix timestamp of snapshot
        - metadata: Additional context (drop_rate, queue_depth)

        Thread Safety: This method can be called from monitoring loop thread
        without blocking. Callbacks execute in separate threads.
        """
        if not self._snapshot_callbacks:
            return  # No callbacks registered

        try:
            # Import here to avoid circular dependency
            from .level_health_snapshot import LevelHealthSnapshot

            # Get current level from core (with fallback)
            try:
                from ..core.epochly_core import EpochlyCore, EnhancementLevel
                core = EpochlyCore.get_instance() if hasattr(EpochlyCore, 'get_instance') else None
                current_level = core.current_level if core else EnhancementLevel.LEVEL_1_THREADING
            except (ImportError, AttributeError):
                # Fallback if EpochlyCore not available
                from ..core.epochly_core import EnhancementLevel
                current_level = EnhancementLevel.LEVEL_1_THREADING

            # Calculate throughput ratio (current vs baseline)
            # Use recent performance from telemetry
            telemetry = self.get_telemetry_metrics()
            current_perf = telemetry.get('queue_utilization', 0.0)
            if current_perf > 0 and self._baseline_throughput > 0:
                throughput_ratio = current_perf / self._baseline_throughput
            else:
                throughput_ratio = 1.0  # Baseline

            # Calculate error rate (errors per second)
            # Look for error metrics in history (thread-safe)
            error_rate = 0.0
            with self._lock:
                if 'errors' in self._metrics_history or 'error_count' in self._metrics_history:
                    error_metrics = self._metrics_history.get('errors', []) or self._metrics_history.get('error_count', [])
                    if error_metrics:
                        # Count errors in last 10 seconds
                        now = time.time()
                        recent_errors = [m for m in error_metrics if now - m.timestamp <= 10.0]
                        error_rate = len(recent_errors) / 10.0  # Errors per second

            # Get allocator status
            allocator_fast_path = True  # Default to healthy
            if self._allocator and hasattr(self._allocator, 'is_fast_path'):
                try:
                    allocator_fast_path = self._allocator.is_fast_path()
                except Exception as e:
                    self.logger.debug(f"Error checking allocator status: {e}")

            # Create snapshot
            snapshot = LevelHealthSnapshot(
                level=current_level,
                throughput_ratio=throughput_ratio,
                error_rate=error_rate,
                allocator_fast_path=allocator_fast_path,
                timestamp=time.time(),
                metadata={
                    'drop_rate': self.get_drop_rate(),
                    'queue_depth': len(self._metrics_queue),
                    'metrics_recorded': self._total_metrics_attempted,
                    'metrics_dropped': self._metrics_dropped
                }
            )

            # Emit resource utilization telemetry to AWS/Lens (GAP #2 fix)
            self._emit_resource_utilization_telemetry(current_level, allocator_fast_path)

            # Emit to callbacks (non-blocking via ThreadPoolExecutor)
            for callback in self._snapshot_callbacks:
                try:
                    # Submit to executor (returns Future, doesn't block)
                    self._snapshot_executor.submit(callback, snapshot)
                except Exception as e:
                    callback_name = getattr(callback, '__name__', repr(callback))
                    self.logger.error(f"Error submitting snapshot to callback {callback_name}: {e}")

            self._last_snapshot_time = time.time()
            self.logger.debug(
                f"Snapshot emitted: level={current_level.name}, "
                f"throughput={throughput_ratio:.2f}, error_rate={error_rate:.3f}"
            )

        except Exception as e:
            self.logger.error(f"Error emitting snapshot: {e}", exc_info=True)

    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "",
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Record a performance metric with adaptive batching and drop tracking (IO-8).

        Performance Improvement:
        - Non-blocking push to deque (no synchronous processing)
        - Automatic eviction when full (back-pressure)
        - Condition notify for batching worker
        - Tracks drop count and emits alerts (IO-8)

        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement
            context: Additional context information
            tags: Metric tags for categorization
        """
        try:
            metric = PerformanceMetric(
                name=name,
                value=value,
                unit=unit,
                timestamp=time.time(),
                context=context or {},
                tags=tags or {}
            )

            # IO-8: Track total attempts
            emit_snapshot = False  # Track if snapshot should be emitted after releasing lock
            with self._queue_lock:
                self._total_metrics_attempted += 1

                # Check if queue is full (will auto-evict oldest)
                queue_was_full = len(self._metrics_queue) == self._metrics_queue.maxlen

                if queue_was_full:
                    self._metrics_dropped += 1  # Track drops for monitoring

                    # IO-8: Alert on drop interval (returns True if snapshot should be emitted)
                    emit_snapshot = self._check_and_emit_drop_alert()

                # Add to deque (non-blocking, auto-evicts if full)
                self._metrics_queue.append(metric)

                # Notify batching worker (wake up to process)
                self._condition.notify()

            # CRITICAL: Emit snapshot AFTER releasing lock (prevent deadlock)
            if emit_snapshot:
                self._emit_snapshot()

            # Check thresholds (lightweight, outside lock)
            self._check_thresholds(metric)

            # Notify callbacks (lightweight, outside lock)
            self._notify_metric_callbacks(metric)

        except Exception as e:
            self.logger.error(f"Failed to record metric {name}: {e}")

    def _check_and_emit_drop_alert(self):
        """
        Check if drop alert should be emitted (IO-8).

        SPEC2 Task 4: Uses AlertWorker for non-blocking emission.
        Falls back to platform logger if AlertWorker unavailable.

        Must be called with _queue_lock held.
        """
        if self._drop_alert_interval == 0:
            return  # Alerts disabled

        # Check if we've hit the alert interval
        drops_since_last_alert = self._metrics_dropped - self._last_drop_alert

        if drops_since_last_alert >= self._drop_alert_interval:
            # CRITICAL FIX: Compute drop rate inline to avoid deadlock
            # (This method is called while holding _queue_lock, can't call get_drop_rate())
            attempted = self._total_metrics_attempted
            drop_rate = (self._metrics_dropped / attempted) if attempted > 0 else 0.0

            # SPEC2 Task 4: Use AlertWorker for non-blocking emission
            # P2-2 FIX: Use lazy getter to initialize AlertWorker on first alert
            alert_worker = self._get_alert_worker()
            if alert_worker:
                # Non-blocking alert via background worker
                context = {
                    'dropped': self._metrics_dropped,
                    'attempted': self._total_metrics_attempted,
                    'drop_rate': f"{drop_rate:.2%}"
                }

                from .alert_worker import AlertLevel
                enqueued = alert_worker.enqueue_alert(
                    AlertLevel.WARNING,
                    f"Metrics queue saturated: {drops_since_last_alert} drops",
                    context
                )

                # Only advance watermark if alert was actually enqueued
                if enqueued:
                    self._last_drop_alert = self._metrics_dropped
            else:
                # Legacy fallback to platform logger (blocking)
                try:
                    self._get_platform_logger().log_metric_drops(
                        self._metrics_dropped,
                        self._total_metrics_attempted,
                        drop_rate
                    )
                    self._last_drop_alert = self._metrics_dropped
                except Exception as e:
                    self.logger.debug(f"Failed to emit drop alert: {e}")

            # TASK 1 PHASE 2: Check if snapshot should be emitted (rate limiting)
            # CRITICAL FIX: Return flag instead of calling _emit_snapshot() here
            # to avoid deadlock (_emit_snapshot needs _lock, but we hold _queue_lock)
            now = time.time()
            if now - self._last_drop_spike_snapshot >= self._drop_spike_cooldown:
                self._last_drop_spike_snapshot = now
                return True  # Signal caller to emit snapshot AFTER releasing lock

        return False  # No snapshot needed

    def _get_platform_logger(self):
        """Get platform logger instance (lazy-loaded)."""
        if self._platform_logger is None:
            from .platform_logger import get_platform_logger
            self._platform_logger = get_platform_logger()
        return self._platform_logger

    def _get_alert_worker(self):
        """
        Get AlertWorker instance (lazy-loaded).

        P2-2 FIX (Dec 2025): Lazy initialization saves 1 daemon thread
        when alerts are never used. Creates and starts AlertWorker on first call.
        """
        if not self._alert_worker_initialized:
            self._alert_worker_initialized = True
            try:
                from .alert_worker import AlertWorker
                self._alert_worker = AlertWorker(max_queue_size=1000)
                self._alert_worker.start()
                self.logger.debug("AlertWorker lazily initialized")
            except ImportError:
                self._alert_worker = None
                self.logger.debug("AlertWorker unavailable - using platform logger")
        return self._alert_worker

    def _monitoring_loop(self):
        """
        Main monitoring loop with adaptive batching (Task 5/6).

        Performance Improvement:
        - Wakes on condition variable or timeout
        - Processes up to batch_size items at once
        - Reduces lock contention via batching
        """
        self.logger.debug("Performance monitoring loop started")

        batch = []
        batch_timeout = self._batch_interval_ms / 1000.0  # Convert to seconds
        last_maintenance = time.time()  # TASK 5 FIX: Track last maintenance time

        while not self._stop_event.is_set():
            try:
                # TASK 5: Batching loop with condition variable
                with self._queue_lock:
                    # Wait for metrics or timeout
                    if not self._metrics_queue:
                        self._condition.wait(timeout=batch_timeout)

                    # Collect batch (up to batch_size items)
                    while self._metrics_queue and len(batch) < self._batch_size:
                        batch.append(self._metrics_queue.popleft())

                # Process batch (outside lock to allow concurrent recording)
                if batch:
                    self._process_batch(batch)
                    batch.clear()

                # TASK 5 FIX: Better maintenance timing (once per second)
                now = time.time()
                if now - last_maintenance >= 1.0:
                    self._cleanup_old_metrics()
                    self._update_aggregated_stats()
                    last_maintenance = now

                # TASK 1 PHASE 2: Emit snapshot on flush interval
                if now - self._last_snapshot_time >= batch_timeout:
                    self._emit_snapshot()

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(0.1)  # Brief pause on error

        self.logger.debug("Performance monitoring loop stopped")

    def _process_batch(self, batch: List[PerformanceMetric]):
        """
        Process a batch of metrics (Task 5/6/8).

        SPEC2 Task 8: Uses AdaptiveBuffer for dynamic sizing if available.

        Args:
            batch: List of metrics to process
        """
        if not batch:
            return

        try:
            # SPEC2 Task 8: Store in AdaptiveBuffer if available
            with self._lock:
                for metric in batch:
                    if self._use_adaptive_buffers_history and self._metrics_history_adaptive is not None:
                        # Use adaptive buffer (uses default BufferConfig)
                        if metric.name not in self._metrics_history_adaptive:
                            from .adaptive_buffer import AdaptiveBuffer
                            self._metrics_history_adaptive[metric.name] = AdaptiveBuffer()
                        self._metrics_history_adaptive[metric.name].append(metric)
                    else:
                        # Fallback to fixed deque
                        self._metrics_history[metric.name].append(metric)

                # Update aggregated stats after storing metrics
                self._update_aggregated_stats()

        except Exception as e:
            self.logger.error(f"Error processing batch: {e}")

    def _process_metrics_queue(self):
        """
        Process all queued metrics (legacy method for compatibility).

        Note: This method is kept for backward compatibility but is no longer
        called from _monitoring_loop() (now uses _process_batch()).
        """
        batch = []

        with self._queue_lock:
            while self._metrics_queue and len(batch) < 100:
                batch.append(self._metrics_queue.popleft())

        # Process batch outside lock
        if batch:
            self._process_batch(batch)

    def _store_metric(self, metric: PerformanceMetric):
        """
        Store metric in history.

        SPEC2 Task 8: Uses AdaptiveBuffer if available.
        """
        with self._lock:
            if self._use_adaptive_buffers_history and self._metrics_history_adaptive is not None:
                if metric.name not in self._metrics_history_adaptive:
                    from .adaptive_buffer import AdaptiveBuffer
                    self._metrics_history_adaptive[metric.name] = AdaptiveBuffer()
                self._metrics_history_adaptive[metric.name].append(metric)
            else:
                self._metrics_history[metric.name].append(metric)

    def _cleanup_old_metrics(self):
        """
        Remove metrics older than retention period.

        SPEC2 Task 8: Handles both AdaptiveBuffer and deque storage.
        """
        cutoff_time = time.time() - self._retention_seconds

        with self._lock:
            # Clean AdaptiveBuffer storage (Critical fix: prevent memory leak)
            if self._use_adaptive_buffers_history and self._metrics_history_adaptive:
                for metric_name, buffer in self._metrics_history_adaptive.items():
                    # AdaptiveBuffer doesn't auto-cleanup old metrics
                    # Must manually filter and rebuild
                    items = list(buffer)
                    retained = [m for m in items if m.timestamp >= cutoff_time]

                    if len(retained) < len(items):
                        # Clear and re-populate with retained metrics
                        buffer.clear()
                        for metric in retained:
                            buffer.append(metric)

            # Clean legacy deque storage
            for metric_name, history in self._metrics_history.items():
                # Remove old metrics from the front of deque
                while history and history[0].timestamp < cutoff_time:
                    history.popleft()

    def _update_aggregated_stats(self):
        """
        Update aggregated statistics for all metrics.

        SPEC2 Task 8: Handles both AdaptiveBuffer and deque storage.
        """
        with self._lock:
            # Update from AdaptiveBuffer storage
            if self._use_adaptive_buffers_history and self._metrics_history_adaptive:
                for metric_name, buffer in self._metrics_history_adaptive.items():
                    items = list(buffer)  # AdaptiveBuffer has __iter__, not get_all()
                    if items:
                        values = [m.value for m in items]
                        self._aggregated_stats[metric_name] = self._calculate_stats(values)

            # Update from legacy deque storage
            for metric_name, history in self._metrics_history.items():
                if history:
                    values = [m.value for m in history]
                    self._aggregated_stats[metric_name] = self._calculate_stats(values)

    def _calculate_stats(self, values: List[float]) -> PerformanceStats:
        """Calculate statistical summary for a list of values."""
        if not values:
            return PerformanceStats(0, 0, 0, 0, 0, 0, 0, 0)

        sorted_values = sorted(values)
        count = len(values)

        return PerformanceStats(
            count=count,
            mean=statistics.mean(values),
            median=statistics.median(values),
            min_value=min(values),
            max_value=max(values),
            std_dev=statistics.stdev(values) if count > 1 else 0,
            percentile_95=sorted_values[int(0.95 * count)] if count > 0 else 0,
            percentile_99=sorted_values[int(0.99 * count)] if count > 0 else 0,
        )

    def _check_thresholds(self, metric: PerformanceMetric):
        """Check if metric exceeds configured thresholds."""
        threshold = self._thresholds.get(metric.name)
        if threshold and metric.value > threshold:
            self.logger.warning(
                f"Metric {metric.name} exceeded threshold: {metric.value} > {threshold}"
            )

            # Notify threshold callbacks
            callbacks = self._threshold_callbacks.get(metric.name, [])
            for callback in callbacks:
                try:
                    callback(metric, threshold)
                except Exception as e:
                    self.logger.error(f"Error in threshold callback: {e}")

    def _notify_metric_callbacks(self, metric: PerformanceMetric):
        """Notify registered metric callbacks."""
        for callback in self._metric_callbacks:
            try:
                callback(metric)
            except Exception as e:
                self.logger.error(f"Error in metric callback: {e}")

    # ========== IO-8: DROP MONITORING PUBLIC API ==========

    def get_drop_count(self) -> int:
        """
        Get the current number of dropped metrics (IO-8).

        Returns:
            Number of metrics dropped due to queue saturation
        """
        with self._queue_lock:
            return self._metrics_dropped

    def reset_drop_count(self):
        """
        Reset the dropped metrics counter (IO-8).

        Useful for resetting after addressing queue saturation.
        """
        with self._queue_lock:
            self._metrics_dropped = 0
            self._last_drop_alert = 0

    def get_total_metrics_attempted(self) -> int:
        """
        Get total number of metrics attempted to record (IO-8).

        Returns:
            Total number of record_metric() calls
        """
        with self._queue_lock:
            return self._total_metrics_attempted

    def get_drop_rate(self) -> float:
        """
        Calculate current drop rate (IO-8).

        Returns:
            Drop rate as a fraction (0.0 - 1.0)
        """
        with self._queue_lock:
            if self._total_metrics_attempted == 0:
                return 0.0
            return self._metrics_dropped / self._total_metrics_attempted

    def get_telemetry_metrics(self) -> Dict[str, Any]:
        """
        Get structured telemetry metrics for dashboards (SPEC2 Task 17).

        Returns metrics that can be exported to Prometheus, CloudWatch, etc.

        Returns:
            Dictionary of telemetry metrics
        """
        # CRITICAL FIX: Acquire locks in correct order to avoid deadlock
        with self._lock:  # Acquire metrics history lock first
            with self._queue_lock:  # Then queue lock
                # Compute drop rate inline (can't call get_drop_rate() - would deadlock)
                attempted = self._total_metrics_attempted
                drop_rate = (self._metrics_dropped / attempted) if attempted > 0 else 0.0

                # Get metrics history count (now safe with _lock held)
                metrics_in_history = sum(len(h) for h in self._metrics_history.values())

                return {
                    # Drop-rate metrics (SPEC2 Task 17)
                    'metrics_dropped': self._metrics_dropped,
                    'metrics_attempted': self._total_metrics_attempted,
                    'drop_rate': drop_rate,

                    # Queue saturation metrics (SPEC2 Task 17)
                    'queue_depth': len(self._metrics_queue),
                    'queue_capacity': self._queue_limit,
                    'queue_utilization': len(self._metrics_queue) / self._queue_limit if self._queue_limit > 0 else 0.0,

                    # Alert worker metrics (SPEC2 Task 4)
                    'alert_worker_stats': self._alert_worker.get_stats() if self._alert_worker else None,

                    # General monitor health
                    'active': self._active,
                    'metrics_in_history': metrics_in_history
                }

    def set_drop_alert_interval(self, interval: int):
        """
        Configure drop alert interval (IO-8).

        Args:
            interval: Alert every N drops (0 to disable)
        """
        with self._queue_lock:
            self._drop_alert_interval = interval
            self.logger.info(f"Drop alert interval set to {interval}")

    # ========== ORIGINAL PUBLIC API (Preserved) ==========

    def get_metric_stats(self, metric_name: str) -> Optional[PerformanceStats]:
        """
        Get statistical summary for a metric.

        Args:
            metric_name: Name of the metric

        Returns:
            PerformanceStats or None if metric not found
        """
        with self._lock:
            return self._aggregated_stats.get(metric_name)

    def get_recent_metrics(
        self,
        metric_name: str,
        count: int = 100
    ) -> List[PerformanceMetric]:
        """
        Get recent metrics for a specific metric name.

        Args:
            metric_name: Name of the metric
            count: Maximum number of recent metrics to return

        Returns:
            List of recent metrics
        """
        with self._lock:
            # Check adaptive buffer storage first (if enabled)
            if self._use_adaptive_buffers_history and self._metrics_history_adaptive:
                if metric_name in self._metrics_history_adaptive:
                    items = list(self._metrics_history_adaptive[metric_name])
                    return items[-count:]

            # Fallback to legacy deque storage
            history = self._metrics_history.get(metric_name, deque())
            return list(history)[-count:]

    def get_all_metric_names(self) -> List[str]:
        """Get list of all metric names being tracked."""
        with self._lock:
            # Combine names from both storages
            names = set(self._metrics_history.keys())
            if self._use_adaptive_buffers_history and self._metrics_history_adaptive:
                names.update(self._metrics_history_adaptive.keys())
            return list(names)

    def add_metric_callback(self, callback: Callable[[PerformanceMetric], None]):
        """
        Add callback to be notified of new metrics.

        Args:
            callback: Function to call with new metrics
        """
        self._metric_callbacks.append(callback)

    def add_threshold_callback(
        self,
        metric_name: str,
        callback: Callable[[PerformanceMetric, float], None]
    ):
        """
        Add callback for threshold violations.

        Args:
            metric_name: Name of metric to monitor
            callback: Function to call when threshold exceeded
        """
        if metric_name not in self._threshold_callbacks:
            self._threshold_callbacks[metric_name] = []
        self._threshold_callbacks[metric_name].append(callback)

    def set_threshold(self, metric_name: str, threshold: float):
        """
        Set threshold for a metric.

        Args:
            metric_name: Name of the metric
            threshold: Threshold value
        """
        self._thresholds[metric_name] = threshold
        self.logger.debug(f"Set threshold for {metric_name}: {threshold}")

    def get_system_summary(self) -> Dict[str, Any]:
        """
        Get summary of system performance (IO-8 enhanced).

        Returns:
            Dictionary containing system performance summary including drop metrics
        """
        # Use len() instead of .qsize() for deque
        # CRITICAL FIX: Compute drop_rate inline to avoid deadlock
        # get_drop_rate() would try to re-acquire _queue_lock (self-deadlock)
        with self._queue_lock:
            queue_size = len(self._metrics_queue)
            metrics_dropped = self._metrics_dropped
            total_attempted = self._total_metrics_attempted
            # Compute drop rate inline (avoid re-entrancy)
            drop_rate = (metrics_dropped / total_attempted) if total_attempted > 0 else 0.0

        with self._lock:
            summary = {
                'active': self._active,
                'metrics_count': len(self._metrics_history),
                'queue_size': queue_size,
                'metrics_dropped': metrics_dropped,  # IO-8
                'total_metrics_attempted': total_attempted,  # IO-8
                'drop_rate': drop_rate,  # IO-8
                'total_metrics': sum(len(h) for h in self._metrics_history.values()),
                'thresholds': self._thresholds.copy(),
                'recent_stats': {}
            }

            # Add recent stats for key metrics
            for metric_name in ['cpu_usage', 'memory_usage', 'response_time']:
                stats = self._aggregated_stats.get(metric_name)
                if stats:
                    summary['recent_stats'][metric_name] = {
                        'mean': stats.mean,
                        'max': stats.max_value,
                        'count': stats.count
                    }

            return summary

    def _emit_resource_utilization_telemetry(self, current_level, allocator_fast_path: bool) -> None:
        """
        Emit resource utilization telemetry to AWS/Lens (non-blocking).

        Per telemetry-audit-findings.md GAP #2: PerformanceMonitor metrics must
        be transmitted to AWS for Lens Infrastructure/Performance tabs.

        Args:
            current_level: Current EnhancementLevel (for GPU detection)
            allocator_fast_path: Whether allocator is in fast path mode

        Thread Safety:
            Safe to call from monitoring loop. Uses try/except to ensure
            telemetry failures never affect monitoring functionality.
        """
        try:
            # Gather system resource metrics
            import psutil

            # CPU and memory metrics
            cpu_percent = psutil.cpu_percent(interval=None)  # Non-blocking
            memory_info = psutil.virtual_memory()
            memory_mb = int(memory_info.used / (1024 * 1024))
            memory_percent = memory_info.percent

            # Pool efficiency (if allocator available)
            pool_efficiency = 1.0 if allocator_fast_path else 0.5

            # Check for GPU metrics (Level 4 only)
            gpu_utilization = None
            gpu_memory_mb = None

            try:
                from ..core.epochly_core import EnhancementLevel
                if current_level.value >= EnhancementLevel.LEVEL_4_GPU.value:
                    try:
                        import pynvml
                        pynvml.nvmlInit()
                        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                        gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        gpu_mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        gpu_utilization = float(gpu_util.gpu)
                        gpu_memory_mb = int(gpu_mem.used / (1024 * 1024))
                    except Exception:
                        pass  # GPU metrics not available
            except ImportError:
                pass

            # Emit to AWS/Lens
            from ..telemetry.routing_events import get_routing_emitter
            emitter = get_routing_emitter()
            if emitter:
                emitter.emit_resource_utilization(
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                    memory_percent=memory_percent,
                    gpu_utilization_percent=gpu_utilization,
                    gpu_memory_mb=gpu_memory_mb,
                    pool_efficiency=pool_efficiency
                )
                self.logger.debug(
                    f"Resource utilization telemetry emitted: "
                    f"CPU={cpu_percent:.1f}%, Memory={memory_mb}MB ({memory_percent:.1f}%)"
                )

        except ImportError:
            # psutil not available - skip telemetry
            self.logger.debug("psutil not available for resource telemetry")
        except Exception as e:
            # Telemetry failures must never affect monitoring
            self.logger.debug(f"Failed to emit resource utilization telemetry: {e}")

    def reset_metrics(self):
        """Clear all stored metrics and statistics (IO-8: preserves drop count)."""
        with self._lock:
            self._metrics_history.clear()
            self._aggregated_stats.clear()

            # Clear adaptive buffer storage if enabled
            if self._use_adaptive_buffers_history and self._metrics_history_adaptive:
                self._metrics_history_adaptive.clear()

        # Clear deque properly (deque has .clear(), not .empty()/.get_nowait())
        with self._queue_lock:
            self._metrics_queue.clear()
            # IO-8: Note - drop counter is NOT reset here
            # Use reset_drop_count() explicitly if needed

        self.logger.info("All metrics reset")


# Global performance monitor instance with thread safety
_performance_monitor = None
_monitor_lock = threading.Lock()

def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        with _monitor_lock:
            if _performance_monitor is None:
                _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def _reset_performance_monitor():
    """
    Reset the global performance monitor singleton for testing.

    CRITICAL: Prevents "threads can only be started once" error across pytest tests.
    - Stops the existing monitor if running
    - Clears the global singleton
    - Next get_performance_monitor() creates fresh instance with new thread

    Use in pytest teardown via EpochlyCore._reset_singleton().
    """
    global _performance_monitor
    with _monitor_lock:
        if _performance_monitor is not None:
            try:
                _performance_monitor.stop()
            except Exception:
                pass
            _performance_monitor = None
