"""
Epochly Plugin Communication System - Advanced Features Module

This module provides advanced communication features including priority message queues,
dead letter queues, and sophisticated message routing capabilities.

Author: Epochly Development Team
Version: 1.0.0
"""

import asyncio
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import logging
from collections import defaultdict

from .communication import PluginMessage


class MessagePriority(Enum):
    """Message priority levels for queue processing."""
    CRITICAL = 0    # Highest priority - system critical messages
    HIGH = 1        # High priority - important operations
    NORMAL = 2      # Normal priority - standard operations
    LOW = 3         # Low priority - background tasks
    BULK = 4        # Lowest priority - bulk operations


@dataclass
class PriorityMessage:
    """Message wrapper with priority and metadata."""
    message: PluginMessage
    priority: MessagePriority
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other: 'PriorityMessage') -> bool:
        """Compare messages for priority queue ordering."""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.timestamp < other.timestamp


class PriorityMessageQueue:
    """
    Advanced message queue with priority-based processing.
    
    Supports multiple priority levels with fair scheduling and
    starvation prevention for lower priority messages.
    """
    
    def __init__(self, 
                 max_size: int = 10000,
                 starvation_threshold: int = 100,
                 low_priority_boost_interval: float = 30.0):
        """
        Initialize priority message queue.
        
        Args:
            max_size: Maximum total messages across all priorities
            starvation_threshold: Max high-priority messages before boosting low-priority
            low_priority_boost_interval: Seconds before boosting low-priority messages
        """
        self.max_size = max_size
        self.starvation_threshold = starvation_threshold
        self.low_priority_boost_interval = low_priority_boost_interval
        
        # Separate queues for each priority level
        self.queues: Dict[MessagePriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in MessagePriority
        }
        
        # Metrics and monitoring
        self.total_messages = 0
        self.high_priority_processed = 0
        self.last_low_priority_time = time.time()
        self.priority_stats: Dict[MessagePriority, int] = defaultdict(int)
        
        # Control flags
        self._shutdown = False
        self._processing_task: Optional[asyncio.Task] = None
        
        # Message handlers
        self.message_handlers: List[Callable[[PriorityMessage], None]] = []
    
    async def put(self, 
                  message: PluginMessage, 
                  priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """
        Add message to priority queue.
        
        Args:
            message: Plugin message to queue
            priority: Message priority level
            
        Returns:
            True if message was queued, False if queue is full
        """
        if self.total_messages >= self.max_size:
            return False
        
        priority_message = PriorityMessage(message=message, priority=priority)
        
        try:
            await self.queues[priority].put(priority_message)
            self.total_messages += 1
            self.priority_stats[priority] += 1
            return True
        except asyncio.QueueFull:
            return False
    
    async def get(self, timeout: Optional[float] = None) -> Optional[PriorityMessage]:
        """
        Get next message based on priority and starvation prevention.
        
        Args:
            timeout: Maximum time to wait for message
            
        Returns:
            Next priority message or None if timeout
        """
        start_time = time.time()
        
        while not self._shutdown:
            # Check for starvation prevention
            should_boost_low_priority = (
                self.high_priority_processed >= self.starvation_threshold or
                time.time() - self.last_low_priority_time >= self.low_priority_boost_interval
            )
            
            # Determine queue processing order
            if should_boost_low_priority:
                queue_order = [MessagePriority.LOW, MessagePriority.BULK, 
                              MessagePriority.CRITICAL, MessagePriority.HIGH, MessagePriority.NORMAL]
                self.high_priority_processed = 0
                self.last_low_priority_time = time.time()
            else:
                queue_order = [MessagePriority.CRITICAL, MessagePriority.HIGH, 
                              MessagePriority.NORMAL, MessagePriority.LOW, MessagePriority.BULK]
            
            # Try to get message from queues in order
            for priority in queue_order:
                try:
                    message = self.queues[priority].get_nowait()
                    self.total_messages -= 1
                    
                    if priority in [MessagePriority.CRITICAL, MessagePriority.HIGH]:
                        self.high_priority_processed += 1
                    
                    return message
                except asyncio.QueueEmpty:
                    continue
            
            # Check timeout
            if timeout is not None and time.time() - start_time >= timeout:
                return None
            
            # Wait briefly before checking again
            await asyncio.sleep(0.01)
        
        return None
    
    def add_message_handler(self, handler: Callable[[PriorityMessage], None]) -> None:
        """Add message handler for processing."""
        self.message_handlers.append(handler)
    
    def remove_message_handler(self, handler: Callable[[PriorityMessage], None]) -> None:
        """Remove message handler."""
        if handler in self.message_handlers:
            self.message_handlers.remove(handler)
    
    async def process_messages(self) -> None:
        """Background task to process messages with handlers."""
        while not self._shutdown:
            try:
                message = await self.get(timeout=1.0)
                if message:
                    for handler in self.message_handlers:
                        try:
                            handler(message)
                        except Exception as e:
                            logging.error(f"Message handler error: {e}")
            except Exception as e:
                logging.error(f"Message processing error: {e}")
    
    def start_processing(self) -> None:
        """Start background message processing."""
        if self._processing_task is None or self._processing_task.done():
            self._processing_task = asyncio.create_task(self.process_messages())
    
    async def stop_processing(self) -> None:
        """Stop background message processing."""
        self._shutdown = True
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        queue_sizes = {
            priority.name: self.queues[priority].qsize() 
            for priority in MessagePriority
        }
        
        return {
            "total_messages": self.total_messages,
            "queue_sizes": queue_sizes,
            "priority_stats": dict(self.priority_stats),
            "high_priority_processed": self.high_priority_processed,
            "last_low_priority_time": self.last_low_priority_time,
            "starvation_prevention_active": (
                self.high_priority_processed >= self.starvation_threshold
            )
        }
    
    def clear(self) -> None:
        """Clear all messages from all queues."""
        for queue in self.queues.values():
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
        
        self.total_messages = 0
        self.high_priority_processed = 0
        self.priority_stats.clear()


@dataclass
class FailedMessage:
    """Failed message with error information."""
    message: PluginMessage
    error: Exception
    timestamp: datetime
    retry_count: int = 0
    original_priority: Optional[MessagePriority] = None


class DeadLetterQueue:
    """
    Dead letter queue for handling failed message processing.
    
    Stores messages that failed processing for later analysis,
    retry, or manual intervention.
    """
    
    def __init__(self, 
                 max_size: int = 1000,
                 retention_period: timedelta = timedelta(days=7),
                 auto_cleanup: bool = True):
        """
        Initialize dead letter queue.
        
        Args:
            max_size: Maximum number of failed messages to store
            retention_period: How long to keep failed messages
            auto_cleanup: Whether to automatically clean up old messages
        """
        self.max_size = max_size
        self.retention_period = retention_period
        self.auto_cleanup = auto_cleanup
        
        self.messages: List[FailedMessage] = []
        self.error_stats: Dict[str, int] = defaultdict(int)
        self.last_cleanup = datetime.now()
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown = False
    
    def add_failed_message(self, 
                          message: PluginMessage, 
                          error: Exception,
                          retry_count: int = 0,
                          original_priority: Optional[MessagePriority] = None) -> None:
        """
        Add failed message to dead letter queue.
        
        Args:
            message: Failed plugin message
            error: Exception that caused failure
            retry_count: Number of retry attempts
            original_priority: Original message priority
        """
        # Remove oldest if at capacity
        if len(self.messages) >= self.max_size:
            self.messages.pop(0)
        
        failed_message = FailedMessage(
            message=message,
            error=error,
            timestamp=datetime.now(),
            retry_count=retry_count,
            original_priority=original_priority
        )
        
        self.messages.append(failed_message)
        self.error_stats[type(error).__name__] += 1
        
        # Trigger cleanup if needed
        if self.auto_cleanup:
            self._maybe_cleanup()
    
    def get_failed_messages(self, 
                           since: Optional[datetime] = None,
                           error_type: Optional[str] = None,
                           limit: Optional[int] = None) -> List[FailedMessage]:
        """
        Get failed messages with optional filtering.
        
        Args:
            since: Only return messages after this timestamp
            error_type: Only return messages with this error type
            limit: Maximum number of messages to return
            
        Returns:
            List of failed messages matching criteria
        """
        filtered_messages = self.messages.copy()
        
        if since:
            filtered_messages = [
                msg for msg in filtered_messages 
                if msg.timestamp >= since
            ]
        
        if error_type:
            filtered_messages = [
                msg for msg in filtered_messages 
                if type(msg.error).__name__ == error_type
            ]
        
        if limit:
            filtered_messages = filtered_messages[-limit:]
        
        return filtered_messages
    
    def get_retry_candidates(self, 
                           max_retry_count: int = 3,
                           min_age: timedelta = timedelta(minutes=5)) -> List[FailedMessage]:
        """
        Get messages that are candidates for retry.
        
        Args:
            max_retry_count: Maximum retries before giving up
            min_age: Minimum age before considering for retry
            
        Returns:
            List of messages suitable for retry
        """
        cutoff_time = datetime.now() - min_age
        
        return [
            msg for msg in self.messages
            if (msg.retry_count < max_retry_count and 
                msg.timestamp <= cutoff_time)
        ]
    
    def remove_message(self, failed_message: FailedMessage) -> bool:
        """
        Remove specific failed message from queue.
        
        Args:
            failed_message: Message to remove
            
        Returns:
            True if message was removed, False if not found
        """
        try:
            self.messages.remove(failed_message)
            return True
        except ValueError:
            return False
    
    def _maybe_cleanup(self) -> None:
        """Perform cleanup if needed."""
        now = datetime.now()
        if now - self.last_cleanup >= timedelta(hours=1):
            self._cleanup_old_messages()
            self.last_cleanup = now
    
    def _cleanup_old_messages(self) -> None:
        """Remove messages older than retention period."""
        cutoff_time = datetime.now() - self.retention_period
        
        original_count = len(self.messages)
        self.messages = [
            msg for msg in self.messages 
            if msg.timestamp >= cutoff_time
        ]
        
        cleaned_count = original_count - len(self.messages)
        if cleaned_count > 0:
            logging.info(f"Cleaned up {cleaned_count} old failed messages")
    
    async def start_auto_cleanup(self) -> None:
        """Start automatic cleanup task."""
        if self.auto_cleanup and (self._cleanup_task is None or self._cleanup_task.done()):
            self._cleanup_task = asyncio.create_task(self._auto_cleanup_loop())
    
    async def stop_auto_cleanup(self) -> None:
        """Stop automatic cleanup task."""
        self._shutdown = True
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _auto_cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while not self._shutdown:
            try:
                self._cleanup_old_messages()
                await asyncio.sleep(3600)  # Cleanup every hour
            except Exception as e:
                logging.error(f"Auto cleanup error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute on error
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dead letter queue statistics."""
        return {
            "total_messages": len(self.messages),
            "error_stats": dict(self.error_stats),
            "oldest_message": (
                self.messages[0].timestamp.isoformat() 
                if self.messages else None
            ),
            "newest_message": (
                self.messages[-1].timestamp.isoformat() 
                if self.messages else None
            ),
            "retry_candidates": len(self.get_retry_candidates()),
            "retention_period_days": self.retention_period.days
        }
    
    def clear(self) -> None:
        """Clear all failed messages."""
        self.messages.clear()
        self.error_stats.clear()


# Global instances for shared usage
_priority_queue: Optional[PriorityMessageQueue] = None
_dead_letter_queue: Optional[DeadLetterQueue] = None


def get_priority_queue() -> PriorityMessageQueue:
    """Get global priority message queue instance."""
    global _priority_queue
    if _priority_queue is None:
        _priority_queue = PriorityMessageQueue()
    return _priority_queue


def get_dead_letter_queue() -> DeadLetterQueue:
    """Get global dead letter queue instance."""
    global _dead_letter_queue
    if _dead_letter_queue is None:
        _dead_letter_queue = DeadLetterQueue()
    return _dead_letter_queue


def reset_global_queues() -> None:
    """Reset global queue instances (for testing)."""
    global _priority_queue, _dead_letter_queue
    _priority_queue = None
    _dead_letter_queue = None