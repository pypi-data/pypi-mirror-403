"""
Epochly Integration Handlers

Centralized handlers for processing routed events.
Eliminates duplicate operations by providing single processing points.
"""

import threading
from typing import Any, Dict, List

from .event_router import RouteEvent
from .logger import get_logger

logger = get_logger(__name__)


class MonitoringHandler:
    """Centralized monitoring handler to prevent duplicate metric processing"""
    
    def __init__(self):
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._alerts: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
        self._logger = get_logger(__name__)
        
    async def handle_metric_update(self, event: RouteEvent) -> None:
        """Handle all metric updates through single channel"""
        try:
            metric_name = event.data.get("metric")
            value = event.data.get("value")
            plugin_name = event.data.get("plugin")  # For plugin metrics
            
            if not metric_name:
                self._logger.warning(f"Metric update event missing metric name: {event.event_id}")
                return
            
            # Prevent duplicate metric processing
            with self._lock:
                if plugin_name:
                    metric_key = f"{event.source}_{plugin_name}_{metric_name}"
                else:
                    metric_key = f"{event.source}_{metric_name}"
                
                # Check for duplicate within short time window
                existing_metric = self._metrics.get(metric_key)
                if existing_metric:
                    time_diff = (event.timestamp - existing_metric["timestamp"]).total_seconds()
                    if time_diff < 0.1 and existing_metric["value"] == value:
                        self._logger.debug(f"Duplicate metric ignored: {metric_key}")
                        return
                
                self._metrics[metric_key] = {
                    "value": value,
                    "timestamp": event.timestamp,
                    "source": event.source,
                    "plugin": plugin_name
                }
                
                self._logger.debug(f"Processed metric update: {metric_key} = {value}")
                
        except Exception as e:
            self._logger.error(f"Error handling metric update: {e}")
            
    async def handle_plugin_status(self, event: RouteEvent) -> None:
        """Handle plugin status updates without duplication"""
        try:
            with self._lock:
                # Process plugin status without duplication
                status_key = f"{event.source}_status"
                
                # Check for duplicate status updates
                existing_status = self._metrics.get(status_key)
                if existing_status:
                    time_diff = (event.timestamp - existing_status["timestamp"]).total_seconds()
                    if time_diff < 0.5 and existing_status["data"] == event.data:
                        self._logger.debug(f"Duplicate plugin status ignored: {status_key}")
                        return
                
                self._metrics[status_key] = {
                    "data": event.data,
                    "timestamp": event.timestamp,
                    "source": event.source
                }
                
                self._logger.debug(f"Processed plugin status: {status_key}")
                
        except Exception as e:
            self._logger.error(f"Error handling plugin status: {e}")
    
    async def handle_core_status(self, event: RouteEvent) -> None:
        """Handle core status updates"""
        try:
            with self._lock:
                status_key = f"{event.source}_status"
                
                # Check for duplicate status updates
                existing_status = self._metrics.get(status_key)
                if existing_status:
                    time_diff = (event.timestamp - existing_status["timestamp"]).total_seconds()
                    if time_diff < 0.5 and existing_status["data"] == event.data:
                        self._logger.debug(f"Duplicate core status ignored: {status_key}")
                        return
                
                self._metrics[status_key] = {
                    "data": event.data,
                    "timestamp": event.timestamp,
                    "source": event.source
                }
                
                self._logger.debug(f"Processed core status: {status_key}")
                
        except Exception as e:
            self._logger.error(f"Error handling core status: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        with self._lock:
            return dict(self._metrics)
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current alerts"""
        with self._lock:
            return list(self._alerts)


class LoggerHandler:
    """Centralized logging handler to prevent duplicate log entries"""
    
    def __init__(self):
        self._log_buffer: List[Dict[str, Any]] = []
        self._max_buffer_size = 1000
        self._lock = threading.RLock()
        self._logger = get_logger(__name__)
        
    async def handle_log_entry(self, event: RouteEvent) -> None:
        """Handle all log entries through single channel"""
        try:
            log_entry = {
                "timestamp": event.timestamp,
                "source": event.source,
                "data": event.data,
                "event_id": event.event_id
            }
            
            # Prevent duplicate log entries
            if not self._is_duplicate_log(log_entry):
                with self._lock:
                    self._log_buffer.append(log_entry)
                    
                    # Maintain buffer size
                    if len(self._log_buffer) > self._max_buffer_size:
                        self._log_buffer = self._log_buffer[-self._max_buffer_size:]
                    
                    # Log based on level
                    log_level = event.data.get("log_level", "info")
                    if log_level == "error":
                        self._logger.error(f"API Error: {event.data}")
                    else:
                        self._logger.info(f"API Request: {event.data}")
            else:
                self._logger.debug(f"Duplicate log entry ignored: {event.event_id}")
                
        except Exception as e:
            self._logger.error(f"Error handling log entry: {e}")
            
    def _is_duplicate_log(self, entry: Dict[str, Any]) -> bool:
        """Check for duplicate log entries"""
        try:
            with self._lock:
                # Check last 10 entries for duplicates
                for existing in self._log_buffer[-10:]:
                    if (existing["source"] == entry["source"] and
                        existing["data"] == entry["data"] and
                        (entry["timestamp"] - existing["timestamp"]).total_seconds() < 0.1):
                        return True
            return False
        except Exception:
            return False
    
    def get_recent_logs(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get recent log entries"""
        with self._lock:
            return self._log_buffer[-count:] if self._log_buffer else []


class APIRequestHandler:
    """Handler for API request events"""
    
    def __init__(self):
        self._request_history: List[Dict[str, Any]] = []
        self._max_history_size = 500
        self._lock = threading.RLock()
        self._logger = get_logger(__name__)
        
    async def handle_api_request(self, event: RouteEvent) -> None:
        """Handle API request events"""
        try:
            request_entry = {
                "timestamp": event.timestamp,
                "source": event.source,
                "data": event.data,
                "event_id": event.event_id
            }
            
            with self._lock:
                self._request_history.append(request_entry)
                
                # Maintain history size
                if len(self._request_history) > self._max_history_size:
                    self._request_history = self._request_history[-self._max_history_size:]
                
                self._logger.debug(f"Processed API request: {event.data.get('endpoint', 'unknown')}")
                
        except Exception as e:
            self._logger.error(f"Error handling API request: {e}")
    
    def get_request_history(self, count: int = 100) -> List[Dict[str, Any]]:
        """Get recent API request history"""
        with self._lock:
            return self._request_history[-count:] if self._request_history else []


# Global handler instances
_monitoring_handler = None
_logger_handler = None
_api_handler = None
_handlers_lock = threading.RLock()


def get_monitoring_handler() -> MonitoringHandler:
    """Get or create the global monitoring handler instance"""
    global _monitoring_handler
    if _monitoring_handler is None:
        with _handlers_lock:
            if _monitoring_handler is None:
                _monitoring_handler = MonitoringHandler()
    return _monitoring_handler


def get_logger_handler() -> LoggerHandler:
    """Get or create the global logger handler instance"""
    global _logger_handler
    if _logger_handler is None:
        with _handlers_lock:
            if _logger_handler is None:
                _logger_handler = LoggerHandler()
    return _logger_handler


def get_api_handler() -> APIRequestHandler:
    """Get or create the global API handler instance"""
    global _api_handler
    if _api_handler is None:
        with _handlers_lock:
            if _api_handler is None:
                _api_handler = APIRequestHandler()
    return _api_handler