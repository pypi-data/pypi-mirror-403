"""
Epochly Plugin Communication Protocols

Event-driven communication system for Epochly plugins using the existing event bus.
Provides standardized messaging patterns for inter-plugin communication.
"""

# Guard asyncio import for Windows multiprocessing subprocess shutdown scenario.
# When Python is shutting down and a spawned subprocess tries to import this module,
# asyncio may be partially torn down, causing NameError: name 'base_events' is not defined.
# This pattern gracefully handles the shutdown case.
try:
    import asyncio
except (ImportError, NameError):
    # During interpreter shutdown, asyncio may be unavailable
    asyncio = None  # type: ignore[assignment]

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from uuid import uuid4

from ..utils.event_bus import (
    BaseEvent, TypedEvent, EventHandler, EventPriority, 
    get_event_bus
)
from ..utils.logger import get_logger
from .base_plugins import PluginType

logger = get_logger(__name__)


class MessageType(Enum):
    """Types of plugin messages."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    ERROR = "error"


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = EventPriority.LOW
    NORMAL = EventPriority.NORMAL
    HIGH = EventPriority.HIGH
    CRITICAL = EventPriority.CRITICAL


@dataclass
class PluginMessage:
    """Standard plugin message structure."""
    message_id: str = field(default_factory=lambda: str(uuid4()))
    message_type: MessageType = MessageType.NOTIFICATION
    sender_id: str = ""
    recipient_id: Optional[str] = None  # None for broadcast
    plugin_type: Optional[PluginType] = None
    action: str = ""
    payload: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None  # For request/response correlation
    timeout: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            'message_id': self.message_id,
            'message_type': self.message_type.value,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'plugin_type': self.plugin_type.value if self.plugin_type else None,
            'action': self.action,
            'payload': self.payload,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'timeout': self.timeout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMessage':
        """Create message from dictionary."""
        return cls(
            message_id=data.get('message_id', str(uuid4())),
            message_type=MessageType(data.get('message_type', 'notification')),
            sender_id=data.get('sender_id', ''),
            recipient_id=data.get('recipient_id'),
            plugin_type=PluginType(data['plugin_type']) if data.get('plugin_type') else None,
            action=data.get('action', ''),
            payload=data.get('payload'),
            metadata=data.get('metadata', {}),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.now(),
            correlation_id=data.get('correlation_id'),
            timeout=data.get('timeout')
        )


@dataclass
class PluginMessageEvent(TypedEvent[PluginMessage]):
    """Event wrapper for plugin messages."""
    event_type: str = "plugin_message"
    
    def __post_init__(self):
        if self.payload:
            self.source = self.payload.sender_id
            # Map message priority to event priority
            if hasattr(self.payload, 'metadata') and 'priority' in self.payload.metadata:
                priority_str = self.payload.metadata['priority']
                if isinstance(priority_str, str):
                    try:
                        self.priority = EventPriority[priority_str.upper()]
                    except KeyError:
                        self.priority = EventPriority.NORMAL
                elif isinstance(priority_str, MessagePriority):
                    self.priority = priority_str.value


class PluginCommunicationProtocol(ABC):
    """Abstract base class for plugin communication protocols."""
    
    @abstractmethod
    async def send_message(self, message: PluginMessage) -> bool:
        """Send a message to another plugin."""
        pass
    
    @abstractmethod
    async def send_request(self, recipient_id: str, action: str, payload: Any, 
                          timeout: float = 30.0) -> Optional[PluginMessage]:
        """Send a request and wait for response."""
        pass
    
    @abstractmethod
    async def send_notification(self, recipient_id: Optional[str], action: str, 
                               payload: Any) -> bool:
        """Send a notification (no response expected)."""
        pass
    
    @abstractmethod
    async def broadcast_message(self, action: str, payload: Any, 
                               plugin_type: Optional[PluginType] = None) -> bool:
        """Broadcast a message to all plugins or specific plugin type."""
        pass
    
    @abstractmethod
    def subscribe_to_messages(self, handler: Callable[[PluginMessage], None]) -> bool:
        """Subscribe to incoming messages."""
        pass


class EventBusPluginCommunication(PluginCommunicationProtocol):
    """
    Plugin communication implementation using the existing event bus.
    
    Provides standardized messaging patterns for inter-plugin communication
    while leveraging the robust event bus infrastructure.
    """
    
    def __init__(self, plugin_id: str, plugin_type: PluginType):
        """
        Initialize plugin communication.
        
        Args:
            plugin_id: Unique identifier for this plugin
            plugin_type: Type of this plugin
        """
        self.plugin_id = plugin_id
        self.plugin_type = plugin_type
        self.logger = get_logger(f"{__name__}.{plugin_id}")
        self.event_bus = get_event_bus()
        
        # Request/response tracking
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._request_timeout_tasks: Dict[str, asyncio.Task] = {}
        
        # Message handlers
        self._message_handlers: List[Callable[[PluginMessage], None]] = []
        
        # Subscribe to plugin messages
        self._setup_message_handling()
    
    def _setup_message_handling(self):
        """Set up event bus subscription for plugin messages."""
        handler = PluginMessageHandler(self)
        success = self.event_bus.subscribe("plugin_message", handler)
        if success:
            self.logger.debug(f"Subscribed to plugin messages for {self.plugin_id}")
        else:
            self.logger.error(f"Failed to subscribe to plugin messages for {self.plugin_id}")
    
    async def send_message(self, message: PluginMessage) -> bool:
        """
        Send a message via the event bus.
        
        Args:
            message: Message to send
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Set sender information
            message.sender_id = self.plugin_id
            
            # Create event wrapper
            event = PluginMessageEvent(payload=message)
            
            # Publish to event bus
            success = await self.event_bus.publish(event)
            
            if success:
                self.logger.debug(f"Sent message {message.message_id} to {message.recipient_id or 'broadcast'}")
            else:
                self.logger.error(f"Failed to send message {message.message_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False
    
    async def send_request(self, recipient_id: str, action: str, payload: Any,
                          timeout: float = 30.0) -> Optional[PluginMessage]:
        """
        Send a request and wait for response.
        
        Args:
            recipient_id: ID of recipient plugin
            action: Action to perform
            payload: Request payload
            timeout: Response timeout in seconds
            
        Returns:
            Response message or None if timeout/error
        """
        try:
            # Create request message with guaranteed correlation_id
            correlation_id = str(uuid4())
            message = PluginMessage(
                message_type=MessageType.REQUEST,
                recipient_id=recipient_id,
                action=action,
                payload=payload,
                timeout=timeout,
                correlation_id=correlation_id
            )
            
            # Set up response future
            response_future = asyncio.Future()
            self._pending_requests[correlation_id] = response_future
            
            # Set up timeout task
            timeout_task = asyncio.create_task(self._handle_request_timeout(correlation_id, timeout))
            self._request_timeout_tasks[correlation_id] = timeout_task
            
            # Send request
            success = await self.send_message(message)
            if not success:
                self._cleanup_request(correlation_id)
                return None
            
            try:
                # Wait for response
                response = await response_future
                self._cleanup_request(correlation_id)
                return response
                
            except asyncio.TimeoutError:
                self.logger.warning(f"Request {correlation_id} timed out after {timeout}s")
                self._cleanup_request(correlation_id)
                return None
                
        except Exception as e:
            self.logger.error(f"Error sending request: {e}")
            return None
    
    async def send_notification(self, recipient_id: Optional[str], action: str, 
                               payload: Any) -> bool:
        """
        Send a notification (no response expected).
        
        Args:
            recipient_id: ID of recipient plugin (None for broadcast)
            action: Action/event type
            payload: Notification payload
            
        Returns:
            bool: True if sent successfully
        """
        message = PluginMessage(
            message_type=MessageType.NOTIFICATION,
            recipient_id=recipient_id,
            action=action,
            payload=payload
        )
        
        return await self.send_message(message)
    
    async def broadcast_message(self, action: str, payload: Any, 
                               plugin_type: Optional[PluginType] = None) -> bool:
        """
        Broadcast a message to all plugins or specific plugin type.
        
        Args:
            action: Action/event type
            payload: Message payload
            plugin_type: Target plugin type (None for all)
            
        Returns:
            bool: True if sent successfully
        """
        message = PluginMessage(
            message_type=MessageType.BROADCAST,
            recipient_id=None,  # Broadcast
            plugin_type=plugin_type,
            action=action,
            payload=payload
        )
        
        return await self.send_message(message)
    
    def subscribe_to_messages(self, handler: Callable[[PluginMessage], None]) -> bool:
        """
        Subscribe to incoming messages.
        
        Args:
            handler: Function to handle incoming messages
            
        Returns:
            bool: True if subscribed successfully
        """
        try:
            self._message_handlers.append(handler)
            self.logger.debug(f"Added message handler for {self.plugin_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error subscribing to messages: {e}")
            return False
    
    async def _handle_request_timeout(self, correlation_id: str, timeout: float):
        """Handle request timeout."""
        try:
            await asyncio.sleep(timeout)
            
            # Check if request is still pending
            if correlation_id in self._pending_requests:
                future = self._pending_requests[correlation_id]
                if not future.done():
                    future.set_exception(asyncio.TimeoutError())
                    
        except asyncio.CancelledError:
            # Timeout task was cancelled (normal response received)
            pass
        except Exception as e:
            self.logger.error(f"Error in timeout handler: {e}")
    
    def _cleanup_request(self, correlation_id: str):
        """Clean up request tracking."""
        # Cancel timeout task
        if correlation_id in self._request_timeout_tasks:
            task = self._request_timeout_tasks.pop(correlation_id)
            if not task.done():
                task.cancel()
        
        # Remove pending request
        self._pending_requests.pop(correlation_id, None)
    
    async def _handle_incoming_message(self, message: PluginMessage):
        """Handle incoming message from event bus."""
        try:
            # Check if message is for this plugin
            if message.recipient_id and message.recipient_id != self.plugin_id:
                return
            
            # Check plugin type filter for broadcasts
            if (message.message_type == MessageType.BROADCAST and 
                message.plugin_type and 
                message.plugin_type != self.plugin_type):
                return
            
            # Handle response messages
            if (message.message_type == MessageType.RESPONSE and 
                message.correlation_id and 
                message.correlation_id in self._pending_requests):
                
                future = self._pending_requests[message.correlation_id]
                if not future.done():
                    future.set_result(message)
                return
            
            # Handle other message types
            for handler in self._message_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                except Exception as e:
                    self.logger.error(f"Error in message handler: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error handling incoming message: {e}")
    
    async def send_response(self, request_message: PluginMessage, payload: Any, 
                           success: bool = True) -> bool:
        """
        Send a response to a request message.
        
        Args:
            request_message: Original request message
            payload: Response payload
            success: Whether the request was successful
            
        Returns:
            bool: True if sent successfully
        """
        if not request_message.correlation_id:
            self.logger.error("Cannot send response: request has no correlation_id")
            return False
        
        response = PluginMessage(
            message_type=MessageType.RESPONSE,
            recipient_id=request_message.sender_id,
            action=f"{request_message.action}_response",
            payload=payload,
            correlation_id=request_message.correlation_id,
            metadata={'success': success}
        )
        
        return await self.send_message(response)


class PluginMessageHandler(EventHandler):
    """Event handler for plugin messages."""

    def __init__(self, communication: EventBusPluginCommunication):
        super().__init__()
        self.communication = communication
        self.logger = get_logger(f"{__name__}.handler")
    
    async def handle(self, event: BaseEvent) -> bool:
        """Handle plugin message events."""
        try:
            if isinstance(event, PluginMessageEvent) and event.payload:
                await self.communication._handle_incoming_message(event.payload)
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error handling plugin message event: {e}")
            return False
    
    @property
    def event_types(self) -> List[str]:
        """Event types this handler processes."""
        return ["plugin_message"]


# Convenience functions for plugin communication
async def send_plugin_notification(sender_id: str, recipient_id: Optional[str], 
                                  action: str, payload: Any) -> bool:
    """
    Convenience function to send a plugin notification.
    
    Args:
        sender_id: ID of sending plugin
        recipient_id: ID of recipient plugin (None for broadcast)
        action: Action/event type
        payload: Notification payload
        
    Returns:
        bool: True if sent successfully
    """
    message = PluginMessage(
        message_type=MessageType.NOTIFICATION,
        sender_id=sender_id,
        recipient_id=recipient_id,
        action=action,
        payload=payload
    )
    
    event = PluginMessageEvent(payload=message)
    event_bus = get_event_bus()
    return await event_bus.publish(event)


async def broadcast_plugin_message(sender_id: str, action: str, payload: Any, 
                                  plugin_type: Optional[PluginType] = None) -> bool:
    """
    Convenience function to broadcast a plugin message.
    
    Args:
        sender_id: ID of sending plugin
        action: Action/event type
        payload: Message payload
        plugin_type: Target plugin type (None for all)
        
    Returns:
        bool: True if sent successfully
    """
    message = PluginMessage(
        message_type=MessageType.BROADCAST,
        sender_id=sender_id,
        recipient_id=None,
        plugin_type=plugin_type,
        action=action,
        payload=payload
    )
    
    event = PluginMessageEvent(payload=message)
    event_bus = get_event_bus()
    return await event_bus.publish(event)