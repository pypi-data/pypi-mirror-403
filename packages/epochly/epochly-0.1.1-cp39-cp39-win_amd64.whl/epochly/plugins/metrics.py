"""
Epochly Plugin Communication Metrics Collection

Comprehensive metrics collection and monitoring for plugin communication system.
Provides performance monitoring, health checks, and observability features.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict, deque
from enum import Enum

from ..utils.logger import get_logger
from .communication import PluginMessage, MessageType

logger = get_logger(__name__)


class MetricType(Enum):
    """Types of metrics collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class CommunicationMetrics:
    """
    Comprehensive metrics for plugin communication.
    
    Tracks message counts, response times, errors, and throughput.
    """
    
    # Message counters
    message_count: int = 0
    request_count: int = 0
    response_count: int = 0
    notification_count: int = 0
    broadcast_count: int = 0
    error_count: int = 0
    timeout_count: int = 0
    
    # Performance metrics
    response_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    bytes_transferred: int = 0
    
    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    last_message_time: Optional[datetime] = None
    
    # Per-plugin metrics
    plugin_metrics: Dict[str, Dict[str, Any]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))
    
    def record_message(self, message_type: str, duration: Optional[float] = None, 
                      size: int = 0, plugin_id: Optional[str] = None):
        """
        Record a message event.
        
        Args:
            message_type: Type of message
            duration: Response time in seconds
            size: Message size in bytes
            plugin_id: ID of plugin involved
        """
        self.message_count += 1
        self.last_message_time = datetime.now()
        
        # Update type-specific counters
        if message_type == MessageType.REQUEST.value:
            self.request_count += 1
        elif message_type == MessageType.RESPONSE.value:
            self.response_count += 1
        elif message_type == MessageType.NOTIFICATION.value:
            self.notification_count += 1
        elif message_type == MessageType.BROADCAST.value:
            self.broadcast_count += 1
        elif message_type == MessageType.ERROR.value:
            self.error_count += 1
        
        # Record response time
        if duration is not None:
            self.response_times.append(duration)
        
        # Record size
        self.bytes_transferred += size
        
        # Per-plugin metrics
        if plugin_id:
            self.plugin_metrics[plugin_id]['message_count'] += 1
            self.plugin_metrics[plugin_id][f'{message_type}_count'] += 1
            if size > 0:
                self.plugin_metrics[plugin_id]['bytes_transferred'] += size
    
    def record_timeout(self, plugin_id: Optional[str] = None):
        """Record a timeout event."""
        self.timeout_count += 1
        if plugin_id:
            self.plugin_metrics[plugin_id]['timeout_count'] += 1
    
    def record_error(self, plugin_id: Optional[str] = None):
        """Record an error event."""
        self.error_count += 1
        if plugin_id:
            self.plugin_metrics[plugin_id]['error_count'] += 1
    
    def get_average_response_time(self) -> float:
        """Get average response time."""
        return sum(self.response_times) / len(self.response_times) if self.response_times else 0.0
    
    def get_throughput(self, time_window: Optional[float] = None) -> float:
        """
        Get message throughput.
        
        Args:
            time_window: Time window in seconds (None for total uptime)
            
        Returns:
            Messages per second
        """
        if time_window is None:
            uptime = (datetime.now() - self.start_time).total_seconds()
            time_window = uptime if uptime > 0 else 1.0
        
        return self.message_count / time_window if time_window > 0 else 0.0
    
    def get_error_rate(self) -> float:
        """Get error rate as percentage."""
        return (self.error_count / self.message_count * 100) if self.message_count > 0 else 0.0
    
    def get_plugin_stats(self, plugin_id: str) -> Dict[str, Any]:
        """Get statistics for a specific plugin."""
        if plugin_id not in self.plugin_metrics:
            return {}
        
        stats = dict(self.plugin_metrics[plugin_id])
        
        # Calculate derived metrics
        message_count = stats.get('message_count', 0)
        error_count = stats.get('error_count', 0)
        
        stats['error_rate'] = (error_count / message_count * 100) if message_count > 0 else 0.0
        
        return stats
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'message_count': self.message_count,
            'request_count': self.request_count,
            'response_count': self.response_count,
            'notification_count': self.notification_count,
            'broadcast_count': self.broadcast_count,
            'error_count': self.error_count,
            'timeout_count': self.timeout_count,
            'bytes_transferred': self.bytes_transferred,
            'average_response_time': self.get_average_response_time(),
            'throughput': self.get_throughput(),
            'error_rate': self.get_error_rate(),
            'uptime_seconds': uptime,
            'start_time': self.start_time.isoformat(),
            'last_message_time': self.last_message_time.isoformat() if self.last_message_time else None
        }


class CommunicationHealthCheck:
    """
    Health check integration for plugin communication.
    
    Monitors communication health and provides status information.
    """
    
    def __init__(self, communication, check_interval: float = 30.0):
        """
        Initialize health check.
        
        Args:
            communication: EventBusPluginCommunication instance
            check_interval: Health check interval in seconds
        """
        self.communication = communication
        self.check_interval = check_interval
        self.logger = get_logger(f"{__name__}.health")
        self.last_health_check = datetime.now()
        self._health_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
        # Health status
        self.is_healthy = True
        self.last_error: Optional[str] = None
        self.consecutive_failures = 0
        self.max_failures = 3
    
    async def start_monitoring(self):
        """Start periodic health monitoring."""
        if self._health_task and not self._health_task.done():
            return
        
        self._health_task = asyncio.create_task(self._periodic_health_check())
        self.logger.info("Started health monitoring")
    
    async def stop_monitoring(self):
        """Stop health monitoring."""
        self._shutdown = True
        
        if self._health_task and not self._health_task.done():
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Stopped health monitoring")
    
    async def _periodic_health_check(self):
        """Perform periodic health checks."""
        try:
            while not self._shutdown:
                await self.check_health()
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.logger.error(f"Error in periodic health check: {e}")
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Perform health check.
        
        Returns:
            Health status information
        """
        try:
            # Send ping message to self
            start_time = time.time()
            
            # Create a simple ping message
            ping_message = PluginMessage(
                message_type=MessageType.NOTIFICATION,
                recipient_id=self.communication.plugin_id,
                action="health_ping",
                payload={"timestamp": start_time}
            )
            
            # Send the message
            success = await self.communication.send_message(ping_message)
            response_time = time.time() - start_time
            
            if success:
                self.is_healthy = True
                self.consecutive_failures = 0
                self.last_error = None
                
                status = {
                    "status": "healthy",
                    "response_time": response_time,
                    "last_check": datetime.now().isoformat(),
                    "consecutive_failures": self.consecutive_failures
                }
            else:
                self._record_failure("Failed to send ping message")
                status = {
                    "status": "unhealthy",
                    "error": "Failed to send ping message",
                    "last_check": datetime.now().isoformat(),
                    "consecutive_failures": self.consecutive_failures
                }
            
            self.last_health_check = datetime.now()
            return status
            
        except Exception as e:
            self._record_failure(str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
                "consecutive_failures": self.consecutive_failures
            }
    
    def _record_failure(self, error: str):
        """Record a health check failure."""
        self.consecutive_failures += 1
        self.last_error = error
        
        if self.consecutive_failures >= self.max_failures:
            self.is_healthy = False
            self.logger.warning(f"Health check failed {self.consecutive_failures} times: {error}")


class MetricsCollector:
    """
    Central metrics collector for plugin communication.
    
    Aggregates metrics from multiple sources and provides reporting.
    """
    
    def __init__(self):
        self.metrics = CommunicationMetrics()
        self.logger = get_logger(f"{__name__}.collector")
        self._observers: List[Callable[[Dict[str, Any]], None]] = []
    
    def add_observer(self, observer: Callable[[Dict[str, Any]], None]):
        """Add a metrics observer."""
        self._observers.append(observer)
    
    def remove_observer(self, observer: Callable[[Dict[str, Any]], None]):
        """Remove a metrics observer."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def record_message_sent(self, message: PluginMessage, size: int = 0):
        """Record a message being sent."""
        self.metrics.record_message(
            message_type=message.message_type.value,
            size=size,
            plugin_id=message.sender_id
        )
        self._notify_observers()
    
    def record_message_received(self, message: PluginMessage, size: int = 0):
        """Record a message being received."""
        self.metrics.record_message(
            message_type=message.message_type.value,
            size=size,
            plugin_id=message.recipient_id
        )
        self._notify_observers()
    
    def record_request_response(self, duration: float, plugin_id: Optional[str] = None):
        """Record a request-response cycle."""
        self.metrics.record_message(
            message_type=MessageType.RESPONSE.value,
            duration=duration,
            plugin_id=plugin_id
        )
        self._notify_observers()
    
    def record_timeout(self, plugin_id: Optional[str] = None):
        """Record a timeout event."""
        self.metrics.record_timeout(plugin_id)
        self._notify_observers()
    
    def record_error(self, plugin_id: Optional[str] = None):
        """Record an error event."""
        self.metrics.record_error(plugin_id)
        self._notify_observers()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        return self.metrics.to_dict()
    
    def get_plugin_metrics(self, plugin_id: str) -> Dict[str, Any]:
        """Get metrics for a specific plugin."""
        return self.metrics.get_plugin_stats(plugin_id)
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.metrics = CommunicationMetrics()
        self.logger.info("Metrics reset")
        self._notify_observers()
    
    def _notify_observers(self):
        """Notify all observers of metrics update."""
        try:
            metrics_data = self.get_metrics_summary()
            for observer in self._observers:
                try:
                    observer(metrics_data)
                except Exception as e:
                    self.logger.error(f"Error notifying metrics observer: {e}")
        except Exception as e:
            self.logger.error(f"Error in metrics notification: {e}")


# Global metrics collector instance
_global_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _global_metrics_collector
    
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    
    return _global_metrics_collector


def reset_global_metrics():
    """Reset global metrics collector."""
    global _global_metrics_collector
    _global_metrics_collector = None