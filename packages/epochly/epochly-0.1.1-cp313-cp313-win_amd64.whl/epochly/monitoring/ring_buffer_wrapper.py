"""
Lock-free ring buffer for high-performance monitoring.

Provides MPSC (multi-producer, single-consumer) ring buffer for metric
collection with minimal contention. Uses atomic operations where possible,
falls back to Python implementation when native helpers unavailable.

Architecture:
- Producers (multiple threads) push metrics lock-free
- Consumer (single thread) batches and aggregates
- Fixed-size buffer prevents unbounded memory growth
- Streaming quantiles (t-digest) for percentile computation
"""

import threading
import time
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
import logging

# Import atomic primitives for lock-free counters
try:
    from ..memory.atomic_primitives import AtomicCounter
    ATOMIC_AVAILABLE = True
except ImportError:
    ATOMIC_AVAILABLE = False
    AtomicCounter = None


logger = logging.getLogger(__name__)


# Check for native ring buffer (Rust/C extension)
_native_available = False
try:
    from ..native import ring_buffer_native
    _native_available = True
except ImportError:
    ring_buffer_native = None


@dataclass(frozen=True)
class MetricEntry:
    """
    Immutable metric entry for ring buffer.

    Frozen dataclass ensures thread-safe reads without locking.
    """
    metric_type: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class RingBufferConfig:
    """Configuration for ring buffer monitor."""

    capacity: int = 4096  # Must be power of 2
    batch_size: int = 128  # Metrics per batch
    poll_interval_ms: int = 10  # Consumer poll interval
    sampling_rate: float = 1.0  # Probabilistic sampling (1.0 = 100%, 0.1 = 10%)

    def __post_init__(self):
        """Validate configuration."""
        if not self._is_power_of_two(self.capacity):
            raise ValueError(f"Capacity {self.capacity} must be power of 2")

        if self.batch_size > self.capacity:
            raise ValueError(
                f"Batch size {self.batch_size} exceeds capacity {self.capacity}"
            )

        if not (0.0 <= self.sampling_rate <= 1.0):
            raise ValueError(
                f"Sampling rate {self.sampling_rate} must be in [0.0, 1.0]"
            )

    @staticmethod
    def _is_power_of_two(n: int) -> bool:
        """Check if n is power of 2."""
        return n > 0 and (n & (n - 1)) == 0


class TDigest:
    """
    Streaming quantile estimator using t-digest algorithm.

    Provides accurate percentile estimates with bounded memory.
    Reference: Ted Dunning's t-digest paper.
    """

    def __init__(self, compression: float = 100.0):
        """
        Initialize t-digest.

        Args:
            compression: Controls accuracy vs memory tradeoff
                        Higher = more accurate, more memory
        """
        self.compression = compression
        self.centroids: List[Tuple[float, float]] = []  # (mean, weight)
        self.min_value = float('inf')
        self.max_value = float('-inf')
        self.total_weight = 0.0

    def add(self, value: float, weight: float = 1.0):
        """Add value to digest."""
        self.min_value = min(self.min_value, value)
        self.max_value = max(self.max_value, value)
        self.total_weight += weight

        # Add as new centroid
        self.centroids.append((value, weight))

        # Merge if too many centroids
        if len(self.centroids) > self.compression * 2:
            self._compress()

    def quantile(self, q: float) -> float:
        """
        Estimate quantile.

        Args:
            q: Quantile in [0, 1]

        Returns:
            Estimated value at quantile q
        """
        if not self.centroids:
            return 0.0

        if q <= 0:
            return self.min_value
        if q >= 1:
            return self.max_value

        # Sort centroids by mean
        sorted_centroids = sorted(self.centroids, key=lambda c: c[0])

        # Find quantile position
        target_weight = q * self.total_weight
        cumulative_weight = 0.0

        for mean, weight in sorted_centroids:
            cumulative_weight += weight
            if cumulative_weight >= target_weight:
                return mean

        return sorted_centroids[-1][0]

    def _compress(self):
        """Merge centroids to maintain bounded size."""
        if not self.centroids:
            return

        # Sort by mean
        sorted_centroids = sorted(self.centroids, key=lambda c: c[0])

        # Merge adjacent centroids
        compressed = []
        current_mean, current_weight = sorted_centroids[0]

        for mean, weight in sorted_centroids[1:]:
            # Decide whether to merge
            if len(compressed) < self.compression:
                # Merge
                total_weight = current_weight + weight
                current_mean = (
                    (current_mean * current_weight + mean * weight) /
                    total_weight
                )
                current_weight = total_weight
            else:
                # Keep separate
                compressed.append((current_mean, current_weight))
                current_mean = mean
                current_weight = weight

        compressed.append((current_mean, current_weight))
        self.centroids = compressed


class PythonRingBuffer:
    """
    Python fallback implementation of lock-free ring buffer.

    Uses thread-safe queue with bounded capacity.
    Not truly lock-free but provides correct semantics.
    """

    def __init__(self, capacity: int):
        """Initialize ring buffer."""
        self.capacity = capacity
        self._lock = threading.Lock()
        self._buffer: deque = deque(maxlen=capacity)
        self._dropped = 0

    def try_push(self, item: MetricEntry) -> bool:
        """
        Try to push item to buffer.

        Returns:
            True if pushed, False if full
        """
        with self._lock:
            if len(self._buffer) >= self.capacity:
                self._dropped += 1
                return False

            self._buffer.append(item)
            return True

    def pop_batch(self, max_size: int) -> List[MetricEntry]:
        """Pop up to max_size items."""
        with self._lock:
            batch = []
            while self._buffer and len(batch) < max_size:
                batch.append(self._buffer.popleft())
            return batch

    @property
    def dropped_count(self) -> int:
        """Get number of dropped items."""
        with self._lock:
            return self._dropped


class RingBufferMonitor(threading.Thread):
    """
    Lock-free monitoring system using ring buffer.

    Multi-producer, single-consumer pattern:
    - Producers: Multiple threads submit metrics via submit()
    - Consumer: Background thread batches and aggregates

    Features:
    - Lock-free submission (when native buffer available)
    - Streaming quantile computation (t-digest)
    - Fixed memory footprint
    - High throughput (target >90k ops/sec)
    """

    def __init__(self, config: Optional[RingBufferConfig] = None):
        """
        Initialize ring buffer monitor.

        Args:
            config: Optional configuration (uses defaults if None)
        """
        super().__init__(daemon=True, name="RingBufferMonitor")

        self.config = config or RingBufferConfig()

        # Create ring buffer (native or fallback)
        if _native_available:
            self._buffer = ring_buffer_native.create(self.config.capacity)
            logger.info(f"Using native ring buffer (capacity={self.config.capacity})")
        else:
            self._buffer = PythonRingBuffer(self.config.capacity)
            logger.info(
                f"Using Python fallback ring buffer (capacity={self.config.capacity})"
            )

        # Statistics (Phase 2.2: Use AtomicCounter for lock-free fast path)
        if ATOMIC_AVAILABLE and AtomicCounter:
            self._total_attempted = AtomicCounter(0)  # All calls to submit()
            self._submitted = AtomicCounter(0)  # Actually submitted to buffer
            self._processed = AtomicCounter(0)  # Processed by consumer
            self._using_atomic = True
        else:
            self._total_attempted = 0
            self._submitted = 0
            self._processed = 0
            self._using_atomic = False
            self._stats_lock = threading.Lock()

        # Probabilistic sampling (Phase 2.2)
        self._sampling_rate = self.config.sampling_rate

        # Quantile digesters per metric type
        self._digesters: Dict[str, TDigest] = defaultdict(
            lambda: TDigest(compression=100.0)
        )

        # Control
        self._running = False
        self._stop_event = threading.Event()

    @property
    def capacity(self) -> int:
        """Get buffer capacity."""
        return self.config.capacity

    @property
    def batch_size(self) -> int:
        """Get batch size."""
        return self.config.batch_size

    @property
    def dropped_count(self) -> int:
        """Get number of dropped metrics."""
        return self._buffer.dropped_count

    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self._running

    def submit(self, entry: MetricEntry) -> bool:
        """
        Submit metric entry with probabilistic sampling (Phase 2.2).

        Fast path: Always count attempt (atomic, no lock), sample out if below rate
        Slow path: Submit to buffer if sampled in

        Args:
            entry: Metric to submit

        Returns:
            True if counted (even if not buffered), False if monitor not running
        """
        # Phase 2.2: Fast path - always count attempt (lock-free with AtomicCounter)
        if self._using_atomic:
            self._total_attempted.increment()
        else:
            # Fallback: minimal lock just for counter
            with self._stats_lock:
                self._total_attempted += 1

        if not self._running:
            return False

        # Phase 2.2: Probabilistic sampling
        # Short-circuit 0.0 and 1.0 to avoid random() overhead
        s = self._sampling_rate
        if s <= 0.0:
            # Count only, never submit
            return True
        elif s < 1.0:
            # Sample: Use >= to handle random()=0.0 edge case correctly
            if random.random() >= s:
                # Sampled out - fast path exit (counted but not submitted)
                return True

        # Slow path: Actually submit to buffer (sampled in, or sampling_rate >= 1.0)
        success = self._buffer.try_push(entry)

        if success:
            if self._using_atomic:
                self._submitted.increment()
            else:
                with self._stats_lock:
                    self._submitted += 1

        return success

    def start(self):
        """Start monitoring thread."""
        self._running = True
        self._stop_event.clear()
        super().start()

    def stop(self):
        """Stop monitoring thread."""
        self._running = False
        self._stop_event.set()

    def run(self):
        """Consumer thread main loop."""
        poll_interval = self.config.poll_interval_ms / 1000.0

        while not self._stop_event.is_set():
            # Pop batch
            batch = self._buffer.pop_batch(self.config.batch_size)

            if batch:
                self._process_batch(batch)

            # Wait for next poll
            self._stop_event.wait(poll_interval)

        # Process remaining items
        while True:
            batch = self._buffer.pop_batch(self.config.batch_size)
            if not batch:
                break
            self._process_batch(batch)

    def _process_batch(self, batch: List[MetricEntry]):
        """Process batch of metrics."""
        for entry in batch:
            # Update digester
            digester = self._digesters[entry.metric_type]
            digester.add(entry.value)

        # Update processed count
        if self._using_atomic:
            self._processed.increment(len(batch))
        else:
            with self._stats_lock:
                self._processed += len(batch)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get monitoring statistics (Phase 2.2: includes total_attempted).

        Returns:
            Dictionary with total_attempted, submitted, dropped, processed counts
        """
        # Get metric types safely (protect against concurrent modification)
        try:
            metric_types = list(self._digesters.keys())
        except RuntimeError:
            # Dict modified during iteration - retry once
            metric_types = list(self._digesters.keys())

        if self._using_atomic:
            # Load from AtomicCounters (no lock needed)
            return {
                'total_attempted': self._total_attempted.load(),
                'submitted': self._submitted.load(),
                'dropped': self.dropped_count,
                'processed': self._processed.load(),
                'buffer_capacity': self.capacity,
                'metric_types': metric_types,
                'sampling_rate': self._sampling_rate
            }
        else:
            # Fallback: lock for consistency
            with self._stats_lock:
                return {
                    'total_attempted': self._total_attempted,
                    'submitted': self._submitted,
                    'dropped': self.dropped_count,
                    'processed': self._processed,
                    'buffer_capacity': self.capacity,
                    'metric_types': metric_types,
                    'sampling_rate': self._sampling_rate
                }

    def get_quantiles(
        self,
        metric_type: str,
        quantiles: List[float]
    ) -> Optional[List[float]]:
        """
        Get quantile estimates for metric type.

        Args:
            metric_type: Type of metric
            quantiles: List of quantiles in [0, 1]

        Returns:
            List of quantile values, or None if metric not found
        """
        digester = self._digesters.get(metric_type)
        if digester is None:
            return None

        return [digester.quantile(q) for q in quantiles]
