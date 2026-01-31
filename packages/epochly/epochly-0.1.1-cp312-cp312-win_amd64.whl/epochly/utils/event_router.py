"""
Epochly Event Router

Lightweight router to eliminate duplicate cross-component operations.
Provides single routing channel for Core→Monitoring, API→Logger, and Plugin→Monitoring.
"""

import asyncio
import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Centralized event types to prevent duplicates"""
    METRIC_UPDATE = "metric_update"
    LOG_ENTRY = "log_entry"
    PLUGIN_STATUS = "plugin_status"
    API_REQUEST = "api_request"
    MONITORING_ALERT = "monitoring_alert"
    CORE_STATUS = "core_status"


@dataclass
class RouteEvent:
    """Standardized event structure"""
    event_type: EventType
    source: str
    target: str
    data: Dict[str, Any]
    timestamp: datetime
    event_id: str
    processed: bool = False


class EventRouter:
    """Lightweight router to eliminate duplicate cross-component operations"""
    
    def __init__(self):
        self._routes: Dict[EventType, List[Callable]] = {}
        self._event_history: Dict[str, RouteEvent] = {}
        self._deduplication_window = 1.0  # seconds
        self._logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        
    def register_handler(self, event_type: EventType, handler: Callable) -> None:
        """Register single handler per event type to prevent duplicates"""
        with self._lock:
            if event_type not in self._routes:
                self._routes[event_type] = []
            
            # Prevent duplicate handler registration
            handler_id = f"{handler.__module__}.{handler.__name__}"
            existing_handlers = [f"{h.__module__}.{h.__name__}" for h in self._routes[event_type]]
            
            if handler_id not in existing_handlers:
                self._routes[event_type].append(handler)
                self._logger.debug(f"Registered handler {handler_id} for {event_type.value}")
    
    async def route_event(self, event: RouteEvent) -> bool:
        """Route event through single channel with deduplication"""
        # Check for duplicate events
        if self._is_duplicate_event(event):
            self._logger.warning(f"Duplicate event detected: {event.event_id}")
            return False
        
        # Store event for deduplication
        with self._lock:
            self._event_history[event.event_id] = event
        
        # Route to appropriate handlers
        handlers = self._routes.get(event.event_type, [])
        if not handlers:
            self._logger.warning(f"No handlers for event type: {event.event_type.value}")
            return False
        
        # Execute handlers
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                event.processed = True
            except Exception as e:
                self._logger.error(f"Handler error for {event.event_type.value}: {e}")
                
        # Cleanup old events
        await self._cleanup_event_history()
        return True
    
    def _is_duplicate_event(self, event: RouteEvent) -> bool:
        """Check if event is duplicate within time window"""
        with self._lock:
            for event_id, stored_event in self._event_history.items():
                if (event.source == stored_event.source and
                    event.target == stored_event.target and
                    event.event_type == stored_event.event_type and
                    event.data == stored_event.data):
                    
                    time_diff = (event.timestamp - stored_event.timestamp).total_seconds()
                    if time_diff < self._deduplication_window:
                        return True
        return False
    
    async def _cleanup_event_history(self):
        """Remove old events from history"""
        current_time = datetime.now()
        expired_events = []
        
        with self._lock:
            for event_id, event in self._event_history.items():
                if (current_time - event.timestamp).total_seconds() > self._deduplication_window * 2:
                    expired_events.append(event_id)
            
            for event_id in expired_events:
                del self._event_history[event_id]


# Global router instance with thread safety
_router_instance: Optional[EventRouter] = None
_router_lock = threading.RLock()


def get_event_router() -> EventRouter:
    """Get or create the global event router instance"""
    global _router_instance
    if _router_instance is None:
        with _router_lock:
            # Double-check locking pattern
            if _router_instance is None:
                _router_instance = EventRouter()
    return _router_instance


def create_event(event_type: EventType, source: str, target: str, data: Dict[str, Any]) -> RouteEvent:
    """Helper function to create standardized events"""
    return RouteEvent(
        event_type=event_type,
        source=source,
        target=target,
        data=data,
        timestamp=datetime.now(),
        event_id=str(uuid4()),
        processed=False
    )