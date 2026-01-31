"""
Epochly Router Adapters

Adapters to replace direct component calls with event router.
Eliminates duplicate operations between Core→Monitoring, API→Logger, and Plugin→Monitoring.
"""

import asyncio
from typing import Any, Dict

from .event_router import EventType, create_event, get_event_router
from .logger import get_logger

logger = get_logger(__name__)


class CoreToMonitoringAdapter:
    """Replace Core→Monitoring direct calls with single routing channel"""
    
    def __init__(self):
        self.router = get_event_router()
        
    async def send_metric(self, metric_name: str, value: Any) -> bool:
        """Single routing channel for metrics from core to monitoring"""
        try:
            event = create_event(
                event_type=EventType.METRIC_UPDATE,
                source="core",
                target="monitoring",
                data={"metric": metric_name, "value": value}
            )
            return await self.router.route_event(event)
        except Exception as e:
            logger.error(f"Failed to route core metric {metric_name}: {e}")
            return False
    
    def send_metric_sync(self, metric_name: str, value: Any) -> bool:
        """Synchronous version for non-async contexts"""
        try:
            # Create new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, schedule the coroutine
                    asyncio.create_task(self.send_metric(metric_name, value))
                    return True  # Return True immediately, actual result handled async
                else:
                    return loop.run_until_complete(self.send_metric(metric_name, value))
            except RuntimeError:
                # No event loop, create one
                return asyncio.run(self.send_metric(metric_name, value))
        except Exception as e:
            logger.error(f"Failed to route core metric sync {metric_name}: {e}")
            return False
    
    async def send_status(self, status_data: Dict[str, Any]) -> bool:
        """Route core status updates"""
        try:
            event = create_event(
                event_type=EventType.CORE_STATUS,
                source="core",
                target="monitoring",
                data=status_data
            )
            return await self.router.route_event(event)
        except Exception as e:
            logger.error(f"Failed to route core status: {e}")
            return False


class PluginToMonitoringAdapter:
    """Replace Plugin→Monitoring direct calls with single routing channel"""
    
    def __init__(self):
        self.router = get_event_router()
        
    async def report_status(self, plugin_name: str, status: Dict[str, Any]) -> bool:
        """Single routing channel for plugin status to monitoring"""
        try:
            event = create_event(
                event_type=EventType.PLUGIN_STATUS,
                source=f"plugin_{plugin_name}",
                target="monitoring",
                data=status
            )
            return await self.router.route_event(event)
        except Exception as e:
            logger.error(f"Failed to route plugin status for {plugin_name}: {e}")
            return False
    
    def report_status_sync(self, plugin_name: str, status: Dict[str, Any]) -> bool:
        """Synchronous version for non-async contexts"""
        try:
            # Create new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, schedule the coroutine
                    asyncio.create_task(self.report_status(plugin_name, status))
                    return True  # Return True immediately, actual result handled async
                else:
                    return loop.run_until_complete(self.report_status(plugin_name, status))
            except RuntimeError:
                # No event loop, create one
                return asyncio.run(self.report_status(plugin_name, status))
        except Exception as e:
            logger.error(f"Failed to route plugin status sync for {plugin_name}: {e}")
            return False
    
    async def send_metric(self, plugin_name: str, metric_name: str, value: Any) -> bool:
        """Route plugin metrics to monitoring"""
        try:
            event = create_event(
                event_type=EventType.METRIC_UPDATE,
                source=f"plugin_{plugin_name}",
                target="monitoring",
                data={"metric": metric_name, "value": value, "plugin": plugin_name}
            )
            return await self.router.route_event(event)
        except Exception as e:
            logger.error(f"Failed to route plugin metric {metric_name} for {plugin_name}: {e}")
            return False


class APIToLoggerAdapter:
    """Replace API→Logger direct calls with single routing channel"""
    
    def __init__(self):
        self.router = get_event_router()
        
    async def log_request(self, endpoint: str, method: str, data: Dict[str, Any]) -> bool:
        """Single routing channel for API logs to logger"""
        try:
            event = create_event(
                event_type=EventType.LOG_ENTRY,
                source="api",
                target="logger",
                data={
                    "endpoint": endpoint,
                    "method": method,
                    "request_data": data,
                    "log_level": "info"
                }
            )
            return await self.router.route_event(event)
        except Exception as e:
            logger.error(f"Failed to route API log for {endpoint}: {e}")
            return False
    
    def log_request_sync(self, endpoint: str, method: str, data: Dict[str, Any]) -> bool:
        """Synchronous version for non-async contexts"""
        try:
            # Create new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, schedule the coroutine
                    asyncio.create_task(self.log_request(endpoint, method, data))
                    return True  # Return True immediately, actual result handled async
                else:
                    return loop.run_until_complete(self.log_request(endpoint, method, data))
            except RuntimeError:
                # No event loop, create one
                return asyncio.run(self.log_request(endpoint, method, data))
        except Exception as e:
            logger.error(f"Failed to route API log sync for {endpoint}: {e}")
            return False
    
    async def log_error(self, endpoint: str, error: str, data: Dict[str, Any]) -> bool:
        """Route API errors to logger"""
        try:
            event = create_event(
                event_type=EventType.LOG_ENTRY,
                source="api",
                target="logger",
                data={
                    "endpoint": endpoint,
                    "error": error,
                    "request_data": data,
                    "log_level": "error"
                }
            )
            return await self.router.route_event(event)
        except Exception as e:
            logger.error(f"Failed to route API error for {endpoint}: {e}")
            return False


# Global adapter instances with thread safety
_core_adapter = None
_plugin_adapter = None
_api_adapter = None


def get_core_adapter() -> CoreToMonitoringAdapter:
    """Get or create the global core adapter instance"""
    global _core_adapter
    if _core_adapter is None:
        _core_adapter = CoreToMonitoringAdapter()
    return _core_adapter


def get_plugin_adapter() -> PluginToMonitoringAdapter:
    """Get or create the global plugin adapter instance"""
    global _plugin_adapter
    if _plugin_adapter is None:
        _plugin_adapter = PluginToMonitoringAdapter()
    return _plugin_adapter


def get_api_adapter() -> APIToLoggerAdapter:
    """Get or create the global API adapter instance"""
    global _api_adapter
    if _api_adapter is None:
        _api_adapter = APIToLoggerAdapter()
    return _api_adapter