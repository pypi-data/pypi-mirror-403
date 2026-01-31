"""
Accelerator Plugin Registry (SPEC2 Task 16).

Manages plugin lifecycle and task dispatch.
"""

import logging
import threading
from typing import Dict, Optional, Any, List
from .plugin_interface import AcceleratorPlugin, PluginError, PluginStatus


logger = logging.getLogger(__name__)


class AcceleratorRegistry:
    """
    Registry for accelerator plugins.

    Manages plugin registration, lifecycle, and task dispatch.
    """

    def __init__(self):
        """Initialize registry."""
        self._plugins: Dict[str, AcceleratorPlugin] = {}
        self._lock = threading.RLock()
        self._initialized = False

    def register(self, plugin: AcceleratorPlugin, auto_initialize: bool = True) -> bool:
        """
        Register a new plugin.

        Args:
            plugin: Plugin instance to register
            auto_initialize: Automatically initialize plugin

        Returns:
            True if registration successful

        Raises:
            ValueError: If plugin name already registered
            PluginError: If plugin initialization fails
        """
        with self._lock:
            if plugin.name in self._plugins:
                raise ValueError(f"Plugin '{plugin.name}' already registered")

            # Initialize if requested
            if auto_initialize:
                try:
                    if not plugin.initialize():
                        raise PluginError(f"Plugin '{plugin.name}' initialization returned False")
                except Exception as e:
                    raise PluginError(f"Plugin '{plugin.name}' initialization failed: {e}") from e

            self._plugins[plugin.name] = plugin
            logger.info(f"Registered plugin '{plugin.name}' ({plugin.capabilities.language.value})")
            return True

    def unregister(self, plugin_name: str) -> bool:
        """
        Unregister and shutdown a plugin.

        Args:
            plugin_name: Name of plugin to unregister

        Returns:
            True if unregistered successfully
        """
        with self._lock:
            if plugin_name not in self._plugins:
                logger.warning(f"Plugin '{plugin_name}' not registered")
                return False

            plugin = self._plugins[plugin_name]

            try:
                plugin.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down plugin '{plugin_name}': {e}")

            del self._plugins[plugin_name]
            logger.info(f"Unregistered plugin '{plugin_name}'")
            return True

    def get_plugin(self, plugin_name: str) -> Optional[AcceleratorPlugin]:
        """
        Get plugin by name.

        Args:
            plugin_name: Plugin name

        Returns:
            Plugin instance or None if not found
        """
        with self._lock:
            return self._plugins.get(plugin_name)

    def list_plugins(self) -> List[str]:
        """
        Get list of registered plugin names.

        Returns:
            List of plugin names
        """
        with self._lock:
            return list(self._plugins.keys())

    def dispatch(self, task_data: Any, plugin_name: Optional[str] = None) -> Any:
        """
        Dispatch task to a plugin.

        Args:
            task_data: Task data to execute
            plugin_name: Optional specific plugin name, or select automatically

        Returns:
            Task result

        Raises:
            PluginError: If dispatch fails
        """
        with self._lock:
            # Select plugin
            if plugin_name:
                plugin = self._plugins.get(plugin_name)
                if not plugin:
                    raise PluginError(f"Plugin '{plugin_name}' not found")
            else:
                plugin = self._select_plugin(task_data)
                if not plugin:
                    raise PluginError("No suitable plugin found")

            # Validate task data
            if not plugin.validate_task_data(task_data):
                raise PluginError(f"Task data validation failed for plugin '{plugin.name}'")

            # Execute
            try:
                result = plugin.execute(task_data)
                return result
            except PluginError as e:
                # Plugin raised PluginError - fallback to Python
                logger.error(f"Plugin '{plugin.name}' raised PluginError: {e}, falling back")
                return self._fallback_to_python(task_data)
            except Exception as e:
                # Unexpected error - fallback to Python
                logger.error(f"Plugin '{plugin.name}' execution failed: {e}, falling back")
                return self._fallback_to_python(task_data)

    def _select_plugin(self, task_data: Any) -> Optional[AcceleratorPlugin]:
        """
        Select optimal plugin for a task.

        Args:
            task_data: Task data

        Returns:
            Selected plugin or None
        """
        # Simple selection: return first ready plugin
        for plugin in self._plugins.values():
            if plugin.get_status() == PluginStatus.READY:
                return plugin

        return None

    def _fallback_to_python(self, task_data: Any) -> Any:
        """
        Fallback to Python execution.

        Args:
            task_data: Task data

        Returns:
            Execution result
        """
        logger.warning("Falling back to Python execution")

        # If task_data is callable, execute it
        if callable(task_data):
            return task_data()

        # Otherwise, just return the data
        return task_data

    def health_check_all(self) -> Dict[str, Any]:
        """
        Health check all plugins.

        Returns:
            Dict with health status for all plugins
        """
        with self._lock:
            health_status = {}
            for name, plugin in self._plugins.items():
                try:
                    health_status[name] = plugin.health_check()
                except Exception as e:
                    health_status[name] = {
                        'name': name,
                        'status': 'error',
                        'error': str(e)
                    }

            return {
                'total_plugins': len(self._plugins),
                'plugins': health_status
            }

    def shutdown_all(self) -> None:
        """Shutdown all plugins."""
        with self._lock:
            for name in list(self._plugins.keys()):
                try:
                    self.unregister(name)
                except Exception as e:
                    logger.error(f"Error during shutdown of plugin '{name}': {e}")
