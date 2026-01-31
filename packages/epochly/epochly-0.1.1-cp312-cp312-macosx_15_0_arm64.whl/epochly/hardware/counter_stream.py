"""
Hardware Counter Streaming Pipeline (SPEC2 Task 15).

Batches perf/eBPF events and feeds summaries to orchestrator.
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque


logger = logging.getLogger(__name__)


@dataclass
class CounterSample:
    """Single hardware counter sample."""
    timestamp: float
    counter_name: str
    value: int
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CounterSummary:
    """Batched counter summary."""
    counter_name: str
    sample_count: int
    total_value: int
    min_value: int
    max_value: int
    mean_value: float
    start_time: float
    end_time: float

    @property
    def duration(self) -> float:
        """Get summary duration in seconds."""
        return self.end_time - self.start_time

    @property
    def rate(self) -> float:
        """Get events per second."""
        if self.duration > 0:
            return self.total_value / self.duration
        return 0.0


class HardwareCounterStream:
    """
    Hardware counter streaming pipeline.

    Collects perf/eBPF events in batches and produces summaries.
    Integrates with HardwareCounterManager and orchestrator.
    """

    def __init__(
        self,
        max_batch_size: int = 1000,
        batch_interval_seconds: float = 1.0,
        max_queue_size: int = 10000
    ):
        """
        Initialize counter stream.

        Args:
            max_batch_size: Maximum samples per batch
            batch_interval_seconds: Maximum time between batches
            max_queue_size: Maximum queue size for samples
        """
        self._max_batch_size = max_batch_size
        self._batch_interval = batch_interval_seconds
        self._max_queue_size = max_queue_size

        # Sample queue (thread-safe)
        self._sample_queue: deque = deque(maxlen=max_queue_size)
        self._queue_lock = threading.Lock()

        # Summary callbacks
        self._summary_callbacks: List = []
        self._callback_lock = threading.Lock()

        # Worker thread
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False

        # Statistics
        self._total_samples_received = 0
        self._total_samples_processed = 0
        self._total_summaries_emitted = 0
        self._samples_dropped = 0

    def start(self) -> None:
        """Start the streaming worker."""
        if self._running:
            logger.warning("Counter stream already running")
            return

        self._stop_event.clear()
        self._running = True

        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name="CounterStreamWorker",
            daemon=True
        )
        self._worker_thread.start()
        logger.info("Hardware counter stream started")

    def stop(self, timeout: float = 5.0) -> None:
        """
        Stop the streaming worker.

        Args:
            timeout: Maximum wait time for worker shutdown
        """
        if not self._running:
            return

        self._stop_event.set()
        self._running = False

        if self._worker_thread:
            self._worker_thread.join(timeout=timeout)
            self._worker_thread = None

        logger.info("Hardware counter stream stopped")

    def add_sample(self, counter_name: str, value: int, context: Optional[Dict] = None) -> bool:
        """
        Add a counter sample to the stream.

        Args:
            counter_name: Name of the hardware counter
            value: Counter value
            context: Optional context metadata

        Returns:
            True if sample was queued, False if dropped
        """
        sample = CounterSample(
            timestamp=time.time(),
            counter_name=counter_name,
            value=value,
            context=context or {}
        )

        with self._queue_lock:
            self._total_samples_received += 1

            # Check if queue is full
            if len(self._sample_queue) >= self._max_queue_size:
                self._samples_dropped += 1
                return False

            self._sample_queue.append(sample)

        return True

    def register_summary_callback(self, callback) -> None:
        """
        Register a callback for counter summaries.

        Callback signature: callback(summary: CounterSummary) -> None
        """
        with self._callback_lock:
            self._summary_callbacks.append(callback)

    def _worker_loop(self) -> None:
        """Worker loop that processes batches."""
        last_batch_time = time.monotonic()

        while not self._stop_event.is_set():
            current_time = time.monotonic()
            elapsed = current_time - last_batch_time

            # Check if we should process a batch
            should_process = False

            with self._queue_lock:
                queue_size = len(self._sample_queue)

                if queue_size >= self._max_batch_size:
                    should_process = True
                elif queue_size > 0 and elapsed >= self._batch_interval:
                    should_process = True

            if should_process:
                self._process_batch()
                last_batch_time = current_time
            else:
                # Wait on stop event instead of sleep for responsive shutdown
                self._stop_event.wait(0.01)

        # Process remaining samples on shutdown
        self._process_batch()

    def _process_batch(self) -> None:
        """Process a batch of samples into summaries."""
        # Dequeue batch
        with self._queue_lock:
            if not self._sample_queue:
                return

            batch_size = min(len(self._sample_queue), self._max_batch_size)
            batch = [self._sample_queue.popleft() for _ in range(batch_size)]

        if not batch:
            return

        # Group samples by counter name
        counter_groups: Dict[str, List[CounterSample]] = {}
        for sample in batch:
            if sample.counter_name not in counter_groups:
                counter_groups[sample.counter_name] = []
            counter_groups[sample.counter_name].append(sample)

        # Create summaries
        summaries = []
        for counter_name, samples in counter_groups.items():
            summary = self._create_summary(counter_name, samples)
            summaries.append(summary)

        # Update statistics
        self._total_samples_processed += len(batch)
        self._total_summaries_emitted += len(summaries)

        # Emit summaries to callbacks
        with self._callback_lock:
            for callback in self._summary_callbacks:
                try:
                    for summary in summaries:
                        callback(summary)
                except Exception as e:
                    logger.error(f"Error in summary callback: {e}")

    def _create_summary(self, counter_name: str, samples: List[CounterSample]) -> CounterSummary:
        """Create a summary from a list of samples."""
        if not samples:
            raise ValueError("Cannot create summary from empty sample list")

        values = [s.value for s in samples]
        total = sum(values)

        return CounterSummary(
            counter_name=counter_name,
            sample_count=len(samples),
            total_value=total,
            min_value=min(values),
            max_value=max(values),
            mean_value=total / len(samples),
            start_time=samples[0].timestamp,
            end_time=samples[-1].timestamp
        )

    def get_stats(self) -> Dict:
        """Get stream statistics."""
        with self._queue_lock:
            queue_size = len(self._sample_queue)

        return {
            'running': self._running,
            'queue_size': queue_size,
            'max_queue_size': self._max_queue_size,
            'total_samples_received': self._total_samples_received,
            'total_samples_processed': self._total_samples_processed,
            'total_summaries_emitted': self._total_summaries_emitted,
            'samples_dropped': self._samples_dropped,
            'drop_rate': self._samples_dropped / max(1, self._total_samples_received)
        }


# Integration with HardwareCounterManager
class StreamingCounterManager:
    """
    Extended HardwareCounterManager with streaming support.

    Wraps HardwareCounterManager and feeds data to stream.
    """

    def __init__(self, hardware_counter_manager=None):
        """
        Initialize streaming counter manager.

        Args:
            hardware_counter_manager: Existing HardwareCounterManager instance
        """
        self._counter_manager = hardware_counter_manager
        self._stream = HardwareCounterStream()
        self._stream.start()

    def poll(self) -> Dict:
        """
        Poll counters and feed to stream.

        Returns:
            Dict of current counter values
        """
        if not self._counter_manager:
            return {}

        # Get current counter values
        try:
            counters = self._counter_manager.read_counters()

            # Feed to stream
            for counter_name, value in counters.items():
                self._stream.add_sample(counter_name, value)

            return counters

        except Exception as e:
            logger.error(f"Error polling counters: {e}")
            return {}

    def register_orchestrator_callback(self, orchestrator) -> None:
        """
        Register orchestrator to receive counter summaries.

        Args:
            orchestrator: Orchestrator instance with update_counters method
        """
        def callback(summary: CounterSummary):
            try:
                orchestrator.update_counters({
                    'counter': summary.counter_name,
                    'value': summary.mean_value,
                    'rate': summary.rate,
                    'samples': summary.sample_count
                })
            except Exception as e:
                logger.error(f"Error updating orchestrator: {e}")

        self._stream.register_summary_callback(callback)

    def shutdown(self, timeout: float = 5.0) -> None:
        """Shutdown the streaming manager."""
        self._stream.stop(timeout=timeout)

    def get_stats(self) -> Dict:
        """Get stream statistics."""
        return self._stream.get_stats()
