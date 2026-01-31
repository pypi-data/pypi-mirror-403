"""
Epochly Router Setup

Setup and configuration for the event router system.
Initializes router with proper wiring to eliminate duplicate operations.
"""

import asyncio
from typing import Dict, Any

from .event_router import EventType, get_event_router
from .router_adapters import get_core_adapter, get_plugin_adapter, get_api_adapter
from .integration_handlers import get_monitoring_handler, get_logger_handler, get_api_handler
from .logger import get_logger

logger = get_logger(__name__)


def setup_router_system() -> Dict[str, Any]:
    """
    Initialize router with proper wiring to eliminate duplicate operations.
    
    Returns:
        Dictionary containing router, adapters, and handlers
    """
    try:
        # Create single router instance
        router = get_event_router()
        
        # Create handlers
        monitoring_handler = get_monitoring_handler()
        logger_handler = get_logger_handler()
        api_handler = get_api_handler()
        
        # Register handlers to eliminate duplicates
        router.register_handler(EventType.METRIC_UPDATE, monitoring_handler.handle_metric_update)
        router.register_handler(EventType.PLUGIN_STATUS, monitoring_handler.handle_plugin_status)
        router.register_handler(EventType.CORE_STATUS, monitoring_handler.handle_core_status)
        router.register_handler(EventType.LOG_ENTRY, logger_handler.handle_log_entry)
        router.register_handler(EventType.API_REQUEST, api_handler.handle_api_request)
        
        # Create adapters to replace direct calls
        core_adapter = get_core_adapter()
        plugin_adapter = get_plugin_adapter()
        api_adapter = get_api_adapter()
        
        logger.info("Router system initialized successfully")
        
        return {
            "router": router,
            "adapters": {
                "core": core_adapter,
                "plugin": plugin_adapter,
                "api": api_adapter
            },
            "handlers": {
                "monitoring": monitoring_handler,
                "logger": logger_handler,
                "api": api_handler
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to setup router system: {e}")
        raise


async def verify_router_integration() -> bool:
    """
    Verify the router integration to ensure it works correctly.
    Uses unique test data to avoid duplicate event conflicts.
    
    Returns:
        True if all tests pass, False otherwise
    """
    try:
        # Setup router system
        system = setup_router_system()
        
        # Test Core→Monitoring routing with unique test data
        core_result = await system["adapters"]["core"].send_metric("integration_test_cpu", 85.5)
        if not core_result:
            logger.error("Core→Monitoring routing test failed")
            return False
        
        # Test Plugin→Monitoring routing with unique test data
        plugin_result = await system["adapters"]["plugin"].report_status(
            "integration_test_plugin",
            {"status": "testing", "processed": 2000}
        )
        if not plugin_result:
            logger.error("Plugin→Monitoring routing test failed")
            return False
        
        # Test API→Logger routing with unique test data
        api_result = await system["adapters"]["api"].log_request(
            "/api/v1/integration_test",
            "PUT",
            {"user": "integration_test", "action": "update"}
        )
        if not api_result:
            logger.error("API→Logger routing test failed")
            return False
        
        # Verify metrics were processed
        metrics = system["handlers"]["monitoring"].get_metrics()
        if not metrics:
            logger.error("No metrics found after routing test")
            return False
        
        # Verify logs were processed
        logs = system["handlers"]["logger"].get_recent_logs(10)
        if not logs:
            logger.error("No logs found after routing test")
            return False
        
        logger.info("Router integration test passed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Router integration test failed: {e}")
        return False


def get_router_status() -> Dict[str, Any]:
    """
    Get current status of the router system.
    
    Returns:
        Dictionary containing router system status
    """
    try:
        system = setup_router_system()
        
        # Get metrics from monitoring handler
        monitoring_handler = system["handlers"]["monitoring"]
        metrics = monitoring_handler.get_metrics()
        alerts = monitoring_handler.get_alerts()
        
        # Get logs from logger handler
        logger_handler = system["handlers"]["logger"]
        recent_logs = logger_handler.get_recent_logs(10)
        
        # Get API requests from API handler
        api_handler = system["handlers"]["api"]
        recent_requests = api_handler.get_request_history(10)
        
        return {
            "status": "active",
            "metrics_count": len(metrics),
            "alerts_count": len(alerts),
            "recent_logs_count": len(recent_logs),
            "recent_requests_count": len(recent_requests),
            "handlers_registered": True,
            "adapters_available": True
        }
        
    except Exception as e:
        logger.error(f"Failed to get router status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "handlers_registered": False,
            "adapters_available": False
        }


# Global system instance
_router_system = None


def get_router_system() -> Dict[str, Any]:
    """Get or create the global router system instance"""
    global _router_system
    if _router_system is None:
        _router_system = setup_router_system()
    return _router_system


async def example_integration() -> None:
    """
    Example of replacing direct component calls with router system.
    Demonstrates elimination of duplicate operations.
    """
    try:
        # Setup router system
        system = get_router_system()
        
        logger.info("Starting router integration example")
        
        # Replace direct Core→Monitoring call
        await system["adapters"]["core"].send_metric("cpu_usage", 75.5)
        await system["adapters"]["core"].send_status({"active": True, "load": 0.8})
        
        # Replace direct Plugin→Monitoring call
        await system["adapters"]["plugin"].report_status(
            "data_processor",
            {"status": "active", "processed": 1000}
        )
        await system["adapters"]["plugin"].send_metric(
            "data_processor", 
            "throughput", 
            1000
        )
        
        # Replace direct API→Logger call
        await system["adapters"]["api"].log_request(
            "/api/v1/data",
            "POST",
            {"user": "test", "action": "create"}
        )
        await system["adapters"]["api"].log_error(
            "/api/v1/data",
            "Validation failed",
            {"user": "test", "error": "missing_field"}
        )
        
        # All events routed through single channel without duplication
        logger.info("Router integration example completed successfully")
        
        # Show results
        status = get_router_status()
        logger.info(f"Router system status: {status}")
        
    except Exception as e:
        logger.error(f"Router integration example failed: {e}")


if __name__ == "__main__":
    # Run example integration
    asyncio.run(example_integration())