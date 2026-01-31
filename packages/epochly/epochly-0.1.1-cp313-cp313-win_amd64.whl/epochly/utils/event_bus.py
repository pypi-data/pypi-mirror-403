"""
Epochly Event Bus Architecture

Advanced event bus implementation with typed event system, performance monitoring,
and debugging capabilities for decoupled component communication.
"""

# Guard asyncio import for Windows multiprocessing subprocess shutdown scenario.
# When Python is shutting down and a spawned subprocess tries to import this module,
# asyncio may be partially torn down, causing NameError: name 'base_events' is not defined.
try:
    import asyncio
except (ImportError, NameError):
    asyncio = None  # type: ignore[assignment]

import os
import sys
import threading
import time
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic, Union
from uuid import uuid4
import weakref
from collections import defaultdict, deque
from weakref import WeakSet
import inspect
from concurrent.futures import ThreadPoolExecutor

from .logger import get_logger
from .config import get_config

logger = get_logger(__name__)

# Type variables for generic event handling
T = TypeVar('T')
EventHandlerType = Union[Callable[[Any], None], Callable[[Any], asyncio.Future]]


class EventPriority(Enum):
    """Event priority levels for processing order."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EventStatus(Enum):
    """Event processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class EventMetrics:
    """Performance metrics for event processing."""
    total_events: int = 0
    processed_events: int = 0
    failed_events: int = 0
    average_processing_time: float = 0.0
    max_processing_time: float = 0.0
    min_processing_time: float = float('inf')
    queue_size: int = 0
    handler_count: int = 0


@dataclass
class BaseEvent:
    """Base event class with common properties."""
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    priority: EventPriority = EventPriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Processing tracking
    status: EventStatus = EventStatus.PENDING
    processing_start: Optional[datetime] = None
    processing_end: Optional[datetime] = None
    error: Optional[str] = None

    def __lt__(self, other):
        """
        Compare events for priority queue ordering.

        Required for asyncio.PriorityQueue which needs to compare events.
        Events are ordered by priority (lower number = higher priority),
        then by timestamp for events with same priority.

        Handles comparison with non-BaseEvent objects gracefully for testing.
        """
        if not isinstance(other, BaseEvent):
            # WINDOWS FIX: Handle comparison with test mock objects
            # When PriorityQueue has same (priority, timestamp), it compares events
            # On Windows, time.time() resolution is lower, making this more likely
            # NOTE: id() is non-deterministic across processes, but this is in-process only
            # Production queue only contains BaseEvent objects; id() is for test mocks
            # Returning NotImplemented would cause TypeError which breaks PriorityQueue
            return id(self) < id(other)
        # Lower priority number = higher priority (CRITICAL comes before NORMAL)
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value  # Reversed for correct ordering
        # Same priority: older events first
        return self.timestamp < other.timestamp


@dataclass
class TypedEvent(BaseEvent, Generic[T]):
    """Typed event with payload."""
    payload: Optional[T] = None
    event_type: str = ""


class EventHandler(ABC):
    """Abstract base class for event handlers."""

    def __init__(self):
        """Initialize event handler with cleanup callbacks."""
        self._cleanup_callbacks: List[Callable] = []

    @abstractmethod
    async def handle(self, event: BaseEvent) -> bool:
        """
        Handle an event.

        Args:
            event: Event to handle

        Returns:
            bool: True if handled successfully
        """
        pass
    
    @property
    @abstractmethod
    def event_types(self) -> List[str]:
        """List of event types this handler can process."""
        pass
    
    @property
    def priority(self) -> int:
        """Handler priority (higher = processed first)."""
        return 0


class EventBus:
    """
    Advanced event bus with typed events, performance monitoring, and debugging.
    
    Features:
    - Typed event system for type safety
    - Priority-based event processing
    - Performance monitoring and metrics
    - Event replay and debugging capabilities
    - Weak reference handlers to prevent memory leaks
    - Async and sync handler support
    """

    @staticmethod
    def _event_identifier(event: Any) -> str:
        """Return a safe identifier string for logging potentially malformed events."""
        # Prefer explicit event_id attribute when available
        event_id = getattr(event, "event_id", None)
        if event_id:
            return str(event_id)

        # Fall back to common alternative identifiers used in tests
        alt_id = getattr(event, "id", None)
        if alt_id:
            return str(alt_id)

        # Final fallback: use object identity to produce a stable-ish identifier
        return f"{type(event).__name__}@0x{id(event):x}"

    def __init__(
        self,
        max_queue_size: int = 10000,
        max_history: int = 1000,
        stop_timeouts: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize event bus with configurable shutdown behavior.

        Args:
            max_queue_size: Maximum number of events that can be queued before
                backpressure is applied. Default: 10,000 events. Increase for
                high-throughput workloads.

            max_history: Maximum number of events to retain in history for
                debugging and replay. Default: 1,000 events. Set to 0 to
                disable history tracking.

            stop_timeouts: Custom shutdown timeout configuration (optional).
                Controls how long the event bus waits for graceful shutdown
                operations before proceeding. Useful for testing or tuning
                shutdown behavior in production.

                Production defaults (seconds):
                    'sentinel': 1.0 - Timeout for sending sentinel values to
                                      signal workers to stop
                    'processor_cancel': 5.0 - Timeout for main event processor
                                              task cancellation
                    'worker_cancel': 5.0 - Timeout for worker task cancellation
                    'flush': 10.0 - Timeout for flushing all handlers to
                                    completion
                    'drain': 5.0 - Timeout for draining remaining queued events

                Example - Fast test timeouts (Windows 3.8 compatible):
                    stop_timeouts = {
                        'sentinel': 0.5,
                        'processor_cancel': 1.0,
                        'worker_cancel': 1.0,
                        'flush': 2.0,
                        'drain': 1.0,
                    }

                Example - Extended timeouts for heavy I/O handlers:
                    stop_timeouts = {
                        'flush': 30.0,  # Allow 30s for handlers to complete
                        'drain': 15.0,  # Allow 15s for queue drain
                    }

                Note: On Windows 3.8, timer resolution is ~15.6ms. Use timeouts
                      ≥500ms for reliable behavior. Linux/Mac support faster
                      timeouts (≥200ms).
        """
        self.logger = get_logger(__name__)
        self.config = get_config()

        # Event processing
        self._handlers: Dict[str, List[weakref.ReferenceType]] = defaultdict(list)
        # Strong reference table to prevent handler garbage collection
        self._strong_handlers: Dict[str, List[Union[EventHandler, Callable]]] = defaultdict(list)
        # NOTE: The queue MUST NOT be created here because __init__ is usually
        # executed outside the running event loop (e.g. in a pytest fixture).
        # The queue will be created lazily in start() when the correct event loop is running.
        self._event_queue: Optional[asyncio.PriorityQueue] = None
        self._max_queue_size = max_queue_size
        self._processing = False
        self._processor_task: Optional[asyncio.Task] = None
        # Use WeakSet to prevent memory leaks from task references
        self._handler_tasks: WeakSet = WeakSet()
        self._handler_tasks_lock = None  # Will be created in start()
        self._workers: List[asyncio.Task] = []

        # Thread pool for sync handler execution to prevent event loop blocking
        self._thread_pool: Optional[ThreadPoolExecutor] = None

        # Event history and debugging
        self._event_history: deque = deque(maxlen=max_history)
        self._replay_enabled = False
        self._debug_mode = False

        # Performance monitoring
        self._metrics = EventMetrics()
        self._processing_times: deque = deque(maxlen=100)
        self._lock = threading.RLock()

        # Configuration
        self._batch_size = self.config.get('event_bus.batch_size', 10)
        self._processing_timeout = self.config.get('event_bus.timeout', 30.0)
        self._enable_metrics = self.config.get('event_bus.enable_metrics', True)
        # Dynamic idle timeout to prevent CPU-melting polling
        self._idle_timeout = max(0.02, min(1.0, 10.0 / self._batch_size))

        # PRODUCTION HARDENING: Race condition prevention for flush operations
        self._generation = 0  # Monotonic counter to detect new events during flush

        # PRODUCTION HARDENING: Active handler counter for O(1) flush checks
        self._active_handler_count = 0
        self._active_handler_lock = threading.Lock()

        # PRODUCTION HARDENING: Started flag for proper lifecycle management
        self._started = False

        # Configurable shutdown timeouts to support faster tests and custom tuning
        default_timeouts = {
            'sentinel': 1.0,
            'processor_cancel': 5.0,
            'worker_cancel': 5.0,
            'flush': 10.0,
            'drain': 5.0,
        }
        if stop_timeouts:
            default_timeouts.update(stop_timeouts)
        self._stop_timeouts = default_timeouts
    
    async def start(self) -> bool:
        """
        Start the event bus processing.
        
        Returns:
            bool: True if started successfully
        """
        # Prevent duplicate processors
        if self._processor_task and not self._processor_task.done():
            self.logger.warning("Event bus already running")
            return True
        
        try:
            self.logger.info("Starting event bus")
            self._processing = True
            
            # Initialize handler tasks lock
            if self._handler_tasks_lock is None:
                self._handler_tasks_lock = asyncio.Lock()
            
            # PRODUCTION HARDENING: Initialize thread pool with bounded workers and proper naming
            if self._thread_pool is None:
                max_workers = min(32, os.cpu_count() or 4)  # Bounded to prevent container resource exhaustion
                self._thread_pool = ThreadPoolExecutor(
                    max_workers=max_workers,
                    thread_name_prefix="epochly-ebus"
                )
                self.logger.info(f"[THREAD_POOL] Initialized with {max_workers} workers")
            
            # Create bounded queue to prevent memory exhaustion
            if self._event_queue is None:
                self._event_queue = asyncio.PriorityQueue(maxsize=self._max_queue_size)
            
            # Start event processor
            self._processor_task = asyncio.create_task(self._process_events())
            
            # CRITICAL FIX: Set started flag to enable flush() operations
            self._started = True
            
            self.logger.info("Event bus started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start event bus: {e}")
            self._processing = False
            return False
    
    async def stop(self):
        """Stop the event bus processing with proper shutdown order."""
        if not self._processing:
            return
        
        try:
            self.logger.info("Stopping event bus")
            self._processing = False
            
            # PRODUCTION HARDENING: Sentinel-based worker termination
            # 1. First stop accepting new events by sending sentinel values
            if self._event_queue is not None:
                # Send sentinel values to signal workers to stop
                for _ in range(len(self._workers) + 1):  # +1 for main processor
                    try:
                        sentinel = (float('inf'), time.time(), None)  # Special sentinel event
                        await asyncio.wait_for(
                            self._event_queue.put(sentinel),
                            timeout=self._stop_timeouts['sentinel'],
                        )
                    except asyncio.TimeoutError:
                        self.logger.warning("Failed to send sentinel: timeout")
                    except Exception as e:
                        self.logger.warning(f"Failed to send sentinel: {e}")
            
            # 2. Cancel processor task with timeout
            if self._processor_task and not self._processor_task.done():
                self._processor_task.cancel()
                try:
                    await asyncio.wait_for(
                        self._processor_task,
                        timeout=self._stop_timeouts['processor_cancel'],
                    )
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    self.logger.warning("Processor task cancellation timed out")
            
            # 3. Cancel all worker tasks with timeout
            if self._workers:
                for worker in self._workers:
                    if not worker.done():
                        worker.cancel()

                # Use asyncio.wait() instead of gather() + wait_for()
                # This properly handles stubborn tasks that ignore cancellation
                try:
                    done, pending = await asyncio.wait(
                        self._workers,
                        timeout=self._stop_timeouts['worker_cancel'],
                        return_when=asyncio.ALL_COMPLETED
                    )
                    if pending:
                        self.logger.warning(f"Worker task cancellation timed out - {len(pending)} workers still running")
                        # Abandon pending workers - they'll be cleaned up when event loop closes
                        for task in pending:
                            task.cancel()
                except Exception as e:
                    self.logger.warning(f"Error cancelling workers: {e}")
            
            # 4. Wait for remaining handler tasks to complete BEFORE draining queue
            try:
                await asyncio.wait_for(
                    self.flush(),
                    timeout=self._stop_timeouts['flush'],
                )
            except asyncio.TimeoutError:
                self.logger.warning("Flush operation timed out during shutdown")
            
            # 5. Process remaining events with timeout
            try:
                await asyncio.wait_for(
                    self._drain_queue(),
                    timeout=self._stop_timeouts['drain'],
                )
            except asyncio.TimeoutError:
                self.logger.warning("Queue drain timed out during shutdown")
            
            # 6. Finally shutdown thread pool with proper cleanup
            if self._thread_pool is not None:
                # Python 3.8 doesn't support cancel_futures parameter (added in 3.9)
                import sys
                if sys.version_info >= (3, 9):
                    self._thread_pool.shutdown(wait=True, cancel_futures=True)
                else:
                    self._thread_pool.shutdown(wait=True)
                self._thread_pool = None
            
            # Mark as stopped
            self._started = False
            
            self.logger.info("Event bus stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping event bus: {e}")
    
    def is_running(self) -> bool:
        """Check if event bus is running."""
        return self._processing
    
    def subscribe(self, event_type: str, handler: Union[EventHandler, Callable]) -> bool:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: Type of event to handle
            handler: Handler function or EventHandler instance
            
        Returns:
            bool: True if subscribed successfully
        """
        try:
            with self._lock:
                # Use weak reference to prevent memory leaks
                if isinstance(handler, EventHandler):
                    weak_ref = weakref.ref(handler)
                else:
                    weak_ref = weakref.ref(handler)
                
                self._handlers[event_type].append(weak_ref)
                
                # Also maintain strong reference to prevent garbage collection
                self._strong_handlers[event_type].append(handler)
                self._metrics.handler_count += 1
                
                self.logger.debug(f"Subscribed handler to {event_type}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to subscribe handler: {e}")
            return False
    
    def unsubscribe(self, event_type: str, handler: Union[EventHandler, Callable]) -> bool:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: Type of event
            handler: Handler to remove
            
        Returns:
            bool: True if unsubscribed successfully
        """
        try:
            with self._lock:
                handlers = self._handlers.get(event_type, [])
                
                # Find and remove handler
                for i, weak_ref in enumerate(handlers):
                    if weak_ref() is handler:
                        handlers.pop(i)
                        self._strong_handlers[event_type].remove(handler)
                        self._metrics.handler_count -= 1
                        self.logger.debug(f"Unsubscribed handler from {event_type}")

                        # Execute cleanup callbacks if handler has them
                        if hasattr(handler, '_cleanup_callbacks'):
                            for callback in handler._cleanup_callbacks:
                                try:
                                    callback()
                                except Exception as e:
                                    self.logger.warning(f"Cleanup callback failed for handler: {e}")

                        return True

                return False
                
        except Exception as e:
            self.logger.error(f"Failed to unsubscribe handler: {e}")
            return False
    
    async def publish(self, event: BaseEvent) -> bool:
        """
        Publish an event to the bus.

        Args:
            event: Event to publish

        Returns:
            bool: True if published successfully
        """
        self.logger.info(f"[EVENT_BUS] Publishing event: {type(event).__name__} (id: {self._event_identifier(event)})")

        try:
            # RACE CONDITION FIX: Capture atomic reference to queue
            # Prevents race between None-check and queue operations during shutdown
            queue = self._event_queue

            if not self._processing or queue is None:
                self.logger.error("Event bus not running, cannot publish event")
                return False

            # Log before queuing (use local queue reference)
            self.logger.info(f"[EVENT_BUS] Event queue exists, current size: {queue.qsize()}")

            # Add to queue with priority
            priority_value = -event.priority.value  # Negative for max-heap behavior
            queue_item = (priority_value, time.time(), event)

            # PRODUCTION HARDENING: Add backpressure handling for bounded queue
            try:
                # Try non-blocking put first
                queue.put_nowait(queue_item)
            except asyncio.QueueFull:
                # Queue is full, apply backpressure by waiting briefly
                self.logger.warning(f"[EVENT_BUS] Queue full ({queue.qsize()}/{self._max_queue_size}), applying backpressure")
                await asyncio.sleep(0.01)  # Brief backpressure delay
                # Try blocking put with timeout
                await asyncio.wait_for(queue.put(queue_item), timeout=1.0)

            # PRODUCTION HARDENING: Increment generation counter for race condition detection
            with self._lock:
                self._generation += 1
                self._metrics.total_events += 1
                self._metrics.queue_size = queue.qsize()

            # Log after queuing
            self.logger.debug(f"[EVENT_BUS] Event queued successfully: {type(event).__name__}, new queue size: {queue.qsize()}")

            if self._debug_mode:
                self.logger.debug(f"Published event {self._event_identifier(event)} of type {getattr(event, 'event_type', 'unknown')}")

            return True

        except asyncio.TimeoutError:
            self.logger.error(f"[EVENT_BUS] Timeout publishing event {self._event_identifier(event)} - queue backpressure exceeded")
            return False
        except Exception as e:
            self.logger.error(f"Failed to publish event: {e}")
            return False
    
    async def publish_typed(self, event_type: str, payload: Any, **kwargs) -> bool:
        """
        Publish a typed event.
        
        Args:
            event_type: Type of event
            payload: Event payload
            **kwargs: Additional event properties
            
        Returns:
            bool: True if published successfully
        """
        event = TypedEvent(
            event_type=event_type,
            payload=payload,
            **kwargs
        )
        return await self.publish(event)
    
    async def flush(self, timeout: float = 5.0) -> bool:
        """
        Wait for all pending events to be processed completely.
        
        This method blocks until every event that has been published
        is actually processed by handlers, not just queued.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if all events processed within timeout
        """
        # PRODUCTION HARDENING: Check if event bus was properly started
        if not self._started:
            raise RuntimeError("Cannot flush event bus before calling start()")
        
        if not self._processing or self._event_queue is None:
            self.logger.debug("[EVENT_BUS] Not processing or no queue, flush complete")
            return True
        
        self.logger.info(f"[EVENT_BUS] Starting flush with timeout {timeout}s")
        
        try:
            # PRODUCTION HARDENING: Capture generation at start to detect race conditions
            with self._lock:
                local_generation = self._generation
            
            # Create a processor task if one doesn't exist
            if self._processor_task is None or self._processor_task.done():
                self.logger.info("[EVENT_BUS] Event processor started")
                self._processor_task = asyncio.create_task(self._process_events())
            
            # Wait for the queue to be completely drained (all events processed)
            await asyncio.wait_for(self._event_queue.join(), timeout)
            
            # PRODUCTION HARDENING: Verify no new events were published during flush
            with self._lock:
                if self._generation != local_generation:
                    self.logger.warning(f"[EVENT_BUS] Race condition detected: generation changed from {local_generation} to {self._generation} during flush")
                    return False
            
            self.logger.info("[EVENT_BUS] Flush completed successfully")
            return True
                
        except asyncio.TimeoutError:
            self.logger.warning(f"[EVENT_BUS] Flush timeout after {timeout}s, queue size: {self._event_queue.qsize()}")
            return False
        except Exception as e:
            self.logger.error(f"[EVENT_BUS] Error during flush: {e}")
            return False
    
    async def _process_events(self):
        """Main event processing loop with comprehensive error handling and recovery."""
        self.logger.info("[EVENT_BUS] Event processor started")
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self._processing:
            try:
                events = []
                self.logger.debug(f"[EVENT_BUS] Starting batch collection (batch_size={self._batch_size})")
                
                # First, fill from queue without blocking
                for _ in range(self._batch_size):
                    try:
                        if self._event_queue is None:
                            self.logger.warning("[EVENT_BUS] Event queue is None, breaking batch collection")
                            break
                        
                        queue_item = self._event_queue.get_nowait()
                        _, _, event = queue_item
                        
                        # PRODUCTION HARDENING: Handle sentinel values for graceful shutdown
                        if event is None:  # Sentinel value
                            self.logger.info("[EVENT_BUS] Received sentinel value, stopping processor")
                            if self._event_queue is not None:
                                self._event_queue.task_done()
                            self._processing = False
                            return
                        
                        events.append(event)
                        self.logger.debug(f"[EVENT_BUS] Got immediate event: {self._event_identifier(event)}")
                    except asyncio.QueueEmpty:
                        break
                    except Exception as e:
                        self.logger.error(f"[EVENT_BUS] Error getting immediate event: {e}")
                        break
                
                # If we still need events, wait briefly for additional events
                if len(events) < self._batch_size and self._event_queue is not None:
                    # PRODUCTION HARDENING: Fix CPU-melting timeout logic
                    # Use intelligent timeout that scales with idle timeout but caps at reasonable limit
                    additional_timeout = min(self._idle_timeout, 0.25)  # Cap at 250ms max
                    try:
                        self.logger.debug(f"[EVENT_BUS] Waiting for additional events (have {len(events)}, want {self._batch_size}, timeout={additional_timeout}s)")
                        queue_item = await asyncio.wait_for(
                            self._event_queue.get(),
                            timeout=additional_timeout
                        )
                        _, _, event = queue_item
                        
                        # PRODUCTION HARDENING: Handle sentinel values for graceful shutdown
                        if event is None:  # Sentinel value
                            self.logger.info("[EVENT_BUS] Received sentinel value during wait, stopping processor")
                            if self._event_queue is not None:
                                self._event_queue.task_done()
                            self._processing = False
                            return
                        
                        events.append(event)
                        self.logger.debug(f"[EVENT_BUS] Got waited event: {self._event_identifier(event)}")
                    except asyncio.TimeoutError:
                        self.logger.debug(f"[EVENT_BUS] Timeout after {additional_timeout}s, processing {len(events)} collected events")
                    except Exception as e:
                        self.logger.error(f"[EVENT_BUS] Error waiting for additional events: {e}")
                
                # Process collected events
                if events:
                    self.logger.info(f"[EVENT_BUS] Processing batch of {len(events)} events")
                    try:
                        await self._process_event_batch(events)
                        # PRODUCTION HARDENING: Reset error counter on successful batch processing
                        consecutive_errors = 0
                        self.logger.debug("[EVENT_BUS] Batch processed successfully, consecutive_errors reset to 0")
                    except Exception as e:
                        self.logger.error(f"[EVENT_BUS] Error processing event batch: {e}")
                        consecutive_errors += 1
                        self.logger.warning(f"[EVENT_BUS] Consecutive errors: {consecutive_errors}/{max_consecutive_errors}")
                        # Mark events as failed if batch processing fails
                        for event in events:
                            try:
                                event.status = EventStatus.FAILED
                                event.error = f"Batch processing error: {str(e)}"
                            except AttributeError:
                                pass  # SlotEvent or malformed event
                            if self._event_queue is not None:
                                self._event_queue.task_done()
                else:
                    self.logger.debug("[EVENT_BUS] No events to process, sleeping briefly")
                    # Only sleep when truly idle to prevent CPU spinning
                    await asyncio.sleep(self._idle_timeout)

                # Check for too many consecutive errors
                if consecutive_errors >= max_consecutive_errors:
                    self.logger.critical(f"[EVENT_BUS] Too many consecutive errors ({consecutive_errors}), stopping processor")
                    self._processing = False
                    self._started = False  # CRITICAL: Sync state flags to prevent cleanup hang
                    break
                
            except asyncio.CancelledError:
                self.logger.info("[EVENT_BUS] Event processor cancelled")
                break
            except Exception as e:
                consecutive_errors += 1
                self.logger.error(f"[EVENT_BUS] Critical error in event processor: {e}")
                
                # Check for too many consecutive errors
                if consecutive_errors >= max_consecutive_errors:
                    self.logger.critical(f"[EVENT_BUS] Too many consecutive errors ({consecutive_errors}), stopping processor")
                    self._processing = False
                    self._started = False  # CRITICAL: Sync state flags to prevent cleanup hang
                    break

                # Exponential backoff for error recovery
                error_sleep = min(10.0, 1.0 * (2 ** min(consecutive_errors - 1, 4)))
                self.logger.info(f"[EVENT_BUS] Sleeping {error_sleep}s for error recovery")
                
                try:
                    await asyncio.sleep(error_sleep)
                except RuntimeError:
                    # Event loop is closed, exit gracefully
                    self.logger.info("[EVENT_BUS] Event loop closed during error recovery, exiting")
                    break
        
        self.logger.info("[EVENT_BUS] Event processor stopped")
    
    async def _process_event_batch(self, events: List[BaseEvent]):
        """Process a batch of events."""
        self.logger.info(f"[EVENT_BUS] Processing batch of {len(events)} events")
        for i, event in enumerate(events):
            try:
                self.logger.debug(f"[EVENT_BUS] Processing event {i+1}/{len(events)}: {self._event_identifier(event)}")
                await self._process_single_event(event)
                self.logger.debug(f"[COMPLETED] Event {i+1}/{len(events)}: {self._event_identifier(event)}")
            except Exception as e:
                self.logger.error(f"[ERROR] Error processing event {self._event_identifier(event)}: {e}")
                # CRITICAL FIX: Wrap attribute setting to prevent deadlock
                # If event is SlotEvent with __slots__ = (), setting attributes will fail
                try:
                    event.status = EventStatus.FAILED
                    event.error = str(e)
                except AttributeError:
                    self.logger.debug(f"Cannot set error status on {type(event).__name__}")
            finally:
                # CRITICAL: Mark task as done after processing completes (success or failure)
                # This enables queue.join() to work properly in flush()
                if self._event_queue is not None:
                    self._event_queue.task_done()
                    self.logger.debug(f"[TASK_DONE] Marked task done for event {self._event_identifier(event)}")
        self.logger.info(f"[BATCH_COMPLETE] Completed batch processing of {len(events)} events")
    
    async def _invoke_handler(self, handler: Union[EventHandler, Callable], event: BaseEvent) -> bool:
        """
        Invoke a single handler for an event with proper task tracking and thread pool execution for sync handlers.
        
        Args:
            handler: Handler to invoke
            event: Event to process
            
        Returns:
            bool: True if handled successfully
        """
        self.logger.debug(f"[INVOKE_HANDLER] Starting handler invocation for {type(handler).__name__}")
        try:
            if isinstance(handler, EventHandler):
                self.logger.debug("[INVOKE_HANDLER] Calling EventHandler.handle() method")
                result = await handler.handle(event)
                self.logger.debug(f"[INVOKE_HANDLER] EventHandler.handle() returned: {result}")
            else:
                # Regular function handler - handle both sync and async
                if inspect.iscoroutinefunction(handler):
                    # Async handler - await it
                    self.logger.debug("[INVOKE_HANDLER] Calling async function handler")
                    result = await handler(event)
                    self.logger.debug(f"[INVOKE_HANDLER] Async function handler returned: {result}")
                else:
                    # Sync handler - execute in thread pool to prevent event loop blocking
                    self.logger.debug("[INVOKE_HANDLER] Calling sync function handler via thread pool")
                    if self._thread_pool is not None:
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(self._thread_pool, handler, event)
                        self.logger.debug(f"[INVOKE_HANDLER] Thread pool execution returned: {result}")
                    else:
                        # Fallback if thread pool not available
                        self.logger.debug("[INVOKE_HANDLER] Thread pool not available, calling sync handler directly")
                        result = handler(event)
                        self.logger.debug(f"[INVOKE_HANDLER] Direct sync handler call returned: {result}")
                    
                    # Check if result is awaitable (shouldn't be from thread pool, but safety check)
                    if inspect.isawaitable(result):
                        self.logger.debug("[INVOKE_HANDLER] Result is awaitable, awaiting it")
                        result = await result
            
            final_result = result is not False  # Consider None as success
            self.logger.debug(f"[INVOKE_HANDLER] Final result: {final_result} (original: {result})")
            return final_result
            
        except Exception as e:
            self.logger.error(f"[INVOKE_HANDLER] Handler error for event {self._event_identifier(event)}: {e}")
            return False
        finally:
            # Remove this task from the tracking set with proper concurrency protection
            current_task = asyncio.current_task()
            if current_task:
                if self._handler_tasks_lock is not None:
                    async with self._handler_tasks_lock:
                        self._handler_tasks.discard(current_task)
                else:
                    self._handler_tasks.discard(current_task)
                self.logger.debug("[INVOKE_HANDLER] Removed task from tracking set")
    
    async def _process_single_event(self, event: BaseEvent):
        """Process a single event."""
        start_time = time.time()
        # CRITICAL FIX: Wrap attribute setting to handle SlotEvents
        try:
            event.status = EventStatus.PROCESSING
            event.processing_start = datetime.now()
        except AttributeError:
            self.logger.debug(f"Cannot set status attributes on {type(event).__name__}")

        try:
            # Get event type with robust string conversion
            event_type_attr = getattr(event, 'event_type', None)
            if event_type_attr:
                event_type = str(event_type_attr)
            else:
                event_type = type(event).__name__
            
            # Debug logging
            self.logger.debug(f"Processing event type: {event_type!r}, event: {event}")
            self.logger.debug(f"Available handler types: {list(self._handlers.keys())}")
            self.logger.debug(f"Strong handler types: {list(self._strong_handlers.keys())}")
            
            # Get handlers for this event type
            handlers = self._get_active_handlers(event_type)
            
            self.logger.debug(f"Found {len(handlers)} handlers for event type: {event_type!r}")
            
            if not handlers:
                self.logger.warning(f"No handlers for event type: {event_type}")
                try:
                    event.status = EventStatus.COMPLETED
                except AttributeError:
                    pass  # SlotEvent
                return
            
            # Execute handlers as tasks and track them
            success_count = 0
            handler_tasks = []
            
            self.logger.debug(f"[HANDLER_INVOKE] Creating tasks for {len(handlers)} handlers")
            for i, handler in enumerate(handlers):
                self.logger.debug(f"[HANDLER_INVOKE] Creating task {i+1}/{len(handlers)} for handler: {type(handler).__name__}")
                # Create task for each handler
                task = asyncio.create_task(self._invoke_handler(handler, event))
                
                # PRODUCTION HARDENING: Add cleanup callback to prevent memory leaks
                def cleanup_task(t, task_ref=task):
                    """Cleanup callback to remove task from tracking set when done."""
                    try:
                        if self._handler_tasks_lock is not None:
                            # Can't use async in callback, so use discard which is thread-safe for WeakSet
                            self._handler_tasks.discard(task_ref)
                        else:
                            self._handler_tasks.discard(task_ref)
                        self.logger.debug("[CLEANUP] Removed completed task from tracking set")
                    except Exception as e:
                        self.logger.debug(f"[CLEANUP] Error removing task from tracking set: {e}")
                
                task.add_done_callback(cleanup_task)
                handler_tasks.append(task)
                
                # Add to tracking set with proper concurrency protection
                if self._handler_tasks_lock is not None:
                    async with self._handler_tasks_lock:
                        self._handler_tasks.add(task)
                else:
                    self._handler_tasks.add(task)
                self.logger.debug("[HANDLER_INVOKE] Task created and added to tracking set with cleanup callback")
            
            # Wait for all handler tasks to complete
            if handler_tasks:
                self.logger.debug(f"[HANDLER_INVOKE] Waiting for {len(handler_tasks)} handler tasks to complete")
                results = await asyncio.gather(*handler_tasks, return_exceptions=True)
                self.logger.debug(f"[HANDLER_INVOKE] Handler tasks completed, processing {len(results)} results")
                for i, result in enumerate(results):
                    self.logger.debug(f"[HANDLER_INVOKE] Result {i+1}/{len(results)}: {result} (type: {type(result).__name__})")
                    if not isinstance(result, Exception) and result is not False:
                        success_count += 1
                        self.logger.debug(f"[HANDLER_INVOKE] Handler {i+1} succeeded, success_count now: {success_count}")
                    else:
                        self.logger.debug(f"[HANDLER_INVOKE] Handler {i+1} failed or returned False")
            else:
                self.logger.warning("[HANDLER_INVOKE] No handler tasks created!")
            
            # Update event status
            if success_count > 0:
                try:
                    event.status = EventStatus.COMPLETED
                except AttributeError:
                    pass  # SlotEvent
                with self._lock:
                    self._metrics.processed_events += 1
            else:
                try:
                    event.status = EventStatus.FAILED
                except AttributeError:
                    pass  # SlotEvent
                with self._lock:
                    self._metrics.failed_events += 1

        except Exception as e:
            try:
                event.status = EventStatus.FAILED
                event.error = str(e)
            except AttributeError:
                pass  # SlotEvent
            with self._lock:
                self._metrics.failed_events += 1

        finally:
            # Update timing metrics
            end_time = time.time()
            processing_time = end_time - start_time
            try:
                event.processing_end = datetime.now()
            except AttributeError:
                pass  # SlotEvent
            
            if self._enable_metrics:
                self._update_timing_metrics(processing_time)
            
            # Store in history
            if self._replay_enabled:
                self._event_history.append(event)
            
            # Update queue size metric
            with self._lock:
                self._metrics.queue_size = self._event_queue.qsize() if self._event_queue else 0
    
    @staticmethod
    def _normalise(evt_type: Union[str, type]) -> str:
        """
        Turn either a class or a string into the canonical string representation
        that is used as key inside the bus.
        """
        return evt_type.__name__ if isinstance(evt_type, type) else str(evt_type)
    
    def _get_active_handlers(self, event_type: str) -> List[Union[EventHandler, Callable]]:
        """Get active handlers for an event type, cleaning up dead references."""
        active_handlers = []
        
        with self._lock:
            # Debug logging
            self.logger.debug(f"[HANDLER_LOOKUP] Looking for handlers of type: {event_type!r}")
            self.logger.debug(f"[HANDLER_LOOKUP] Available handler types: {list(self._handlers.keys())}")
            self.logger.debug(f"[HANDLER_LOOKUP] Strong handler types: {list(self._strong_handlers.keys())}")
            
            # First try direct lookup
            handlers = self._handlers.get(event_type, [])
            alive_handlers = []
            
            self.logger.debug(f"[HANDLER_LOOKUP] Direct lookup found {len(handlers)} weak references for {event_type!r}")
            
            for weak_ref in handlers:
                handler = weak_ref()
                if handler is not None:
                    active_handlers.append(handler)
                    alive_handlers.append(weak_ref)
                else:
                    # Dead reference, will be cleaned up
                    self._metrics.handler_count -= 1
            
            # Update handlers list with only alive references
            self._handlers[event_type] = alive_handlers

            # PATTERN MATCHING: Check if any registered types are regex patterns that match this event
            for registered_type, handler_refs in list(self._handlers.items()):
                if registered_type == event_type:  # Skip already processed exact match
                    continue

                # Try regex pattern matching
                try:
                    if re.match(registered_type, event_type):
                        for weak_ref in handler_refs:
                            handler = weak_ref()
                            if handler is not None and handler not in active_handlers:
                                active_handlers.append(handler)
                                self.logger.debug(f"[HANDLER_LOOKUP] Pattern '{registered_type}' matched '{event_type}'")
                except re.error:
                    # Not a valid regex, skip pattern matching for this type
                    pass

            # Also check EventHandler instances that might handle this event type
            wanted = self._normalise(event_type)

            for registered_type, handler_refs in list(self._handlers.items()):
                if registered_type == event_type:  # Skip already processed
                    continue
                    
                for weak_ref in handler_refs[:]:  # Copy to avoid modification during iteration
                    handler = weak_ref()
                    if handler is None:
                        handler_refs.remove(weak_ref)
                        self._metrics.handler_count -= 1
                        continue
                    
                    if isinstance(handler, EventHandler):
                        # Compare after normalising both sides
                        if any(self._normalise(t) == wanted for t in handler.event_types):
                            if handler not in active_handlers:  # Avoid duplicates
                                active_handlers.append(handler)
        
        return active_handlers
    
    def _update_timing_metrics(self, processing_time: float):
        """Update timing metrics."""
        with self._lock:
            self._processing_times.append(processing_time)
            
            # Update metrics
            if self._processing_times:
                self._metrics.average_processing_time = sum(self._processing_times) / len(self._processing_times)
                self._metrics.max_processing_time = max(self._processing_times)
                self._metrics.min_processing_time = min(self._processing_times)
    
    async def _drain_queue(self):
        """Process remaining events in queue."""
        if self._event_queue is None:
            return
            
        remaining_events = []
        
        while not self._event_queue.empty():
            try:
                queue_item = self._event_queue.get_nowait()
                _, _, event = queue_item
                # Skip sentinel values (None events)
                if event is not None:
                    remaining_events.append(event)
            except asyncio.QueueEmpty:
                break
        
        if remaining_events:
            self.logger.info(f"Processing {len(remaining_events)} remaining events")
            await self._process_event_batch(remaining_events)
    
    def get_metrics(self) -> EventMetrics:
        """Get current event bus metrics."""
        with self._lock:
            return EventMetrics(
                total_events=self._metrics.total_events,
                processed_events=self._metrics.processed_events,
                failed_events=self._metrics.failed_events,
                average_processing_time=self._metrics.average_processing_time,
                max_processing_time=self._metrics.max_processing_time,
                min_processing_time=self._metrics.min_processing_time if self._metrics.min_processing_time != float('inf') else 0.0,
                queue_size=self._metrics.queue_size,
                handler_count=self._metrics.handler_count
            )
    
    def get_event_history(self, count: int = 100) -> List[BaseEvent]:
        """Get recent event history."""
        return list(self._event_history)[-count:]
    
    def enable_replay(self, enabled: bool = True):
        """Enable or disable event replay capability."""
        self._replay_enabled = enabled
        self.logger.debug(f"Event replay {'enabled' if enabled else 'disabled'}")
    
    def enable_debug(self, enabled: bool = True):
        """Enable or disable debug mode."""
        self._debug_mode = enabled
        self.logger.debug(f"Debug mode {'enabled' if enabled else 'disabled'}")
    
    def debug_state(self) -> Dict[str, Any]:
        """Get detailed debug state information."""
        return {
            "running": self._processing,
            "queue_exists": self._event_queue is not None,
            "queue_size": self._event_queue.qsize() if self._event_queue else 0,
            "processor_task": self._processor_task is not None,
            "processor_done": self._processor_task.done() if self._processor_task else None,
            "handlers_count": sum(len(handlers) for handlers in self._handlers.values()),
            "strong_handlers_count": sum(len(handlers) for handlers in self._strong_handlers.values()),
            "metrics": {
                "total_events": self._metrics.total_events,
                "processed_events": self._metrics.processed_events,
                "failed_events": self._metrics.failed_events,
                "queue_size": self._metrics.queue_size
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get event bus status information."""
        metrics = self.get_metrics()
        
        return {
            'running': self._processing,
            'metrics': {
                'total_events': metrics.total_events,
                'processed_events': metrics.processed_events,
                'failed_events': metrics.failed_events,
                'success_rate': (metrics.processed_events / max(metrics.total_events, 1)) * 100,
                'average_processing_time': metrics.average_processing_time,
                'queue_size': metrics.queue_size,
                'handler_count': metrics.handler_count
            },
            'configuration': {
                'batch_size': self._batch_size,
                'processing_timeout': self._processing_timeout,
                'replay_enabled': self._replay_enabled,
                'debug_mode': self._debug_mode,
                'enable_metrics': self._enable_metrics
            }
        }

    def shutdown(self, timeout: float = 5.0) -> bool:
        """
        Synchronous shutdown of event bus for use in non-async contexts (e.g., pytest fixtures).

        This method properly cleans up all resources including worker threads and thread pool
        to prevent interpreter hangs during shutdown (especially on Windows).

        Args:
            timeout: Maximum time to wait for shutdown in seconds

        Returns:
            bool: True if shutdown completed successfully
        """
        if not self._processing and self._thread_pool is None:
            # Already shut down
            return True

        try:
            # Get or create event loop for shutdown
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.stop())
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)
            else:
                # Running loop exists, use it
                asyncio.create_task(self.stop())

            return True
        except Exception as e:
            self.logger.error(f"Error during synchronous shutdown: {e}")
            # Force thread pool shutdown even if async stop failed
            if self._thread_pool is not None:
                import sys
                if sys.version_info >= (3, 9):
                    self._thread_pool.shutdown(wait=True, cancel_futures=True)
                else:
                    self._thread_pool.shutdown(wait=True)
                self._thread_pool = None
            return False

    def wait_until_idle(self, timeout: float = 1.0) -> bool:
        """
        Synchronous wait for all pending events to be processed.

        This provides a deterministic barrier for tests to ensure events are
        processed before assertions run.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            bool: True if all events processed within timeout
        """
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, create a new one for this operation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        asyncio.wait_for(self.flush(timeout), timeout)
                    )
                    return result
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)
            else:
                # Running loop exists, schedule flush
                future = asyncio.create_task(self.flush(timeout))
                # Can't wait synchronously in running loop, return immediately
                return True
        except asyncio.TimeoutError:
            self.logger.warning(f"wait_until_idle timed out after {timeout}s")
            return False
        except Exception as e:
            self.logger.error(f"Error in wait_until_idle: {e}")
            return False


# Global event bus instance with thread safety
_event_bus: Optional[EventBus] = None
_bus_lock = threading.RLock()


def get_event_bus() -> EventBus:
    """Get the global event bus instance with thread safety."""
    global _event_bus
    if _event_bus is None:
        with _bus_lock:
            # Double-check locking pattern
            if _event_bus is None:
                _event_bus = EventBus()
    return _event_bus


# Convenience functions for common operations
async def publish_event(event_type: str, payload: Any, **kwargs) -> bool:
    """Convenience function to publish a typed event."""
    bus = get_event_bus()
    return await bus.publish_typed(event_type, payload, **kwargs)


def subscribe_to_event(event_type: str, handler: Union[EventHandler, Callable]) -> bool:
    """Convenience function to subscribe to an event type."""
    bus = get_event_bus()
    return bus.subscribe(event_type, handler)