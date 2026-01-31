"""
Epochly Plugin Manager

This module provides the plugin management system for the Epochly (Epochly) framework.
It enables dynamic loading, registration, and management of plugins that extend Epochly functionality.

Author: Epochly Development Team
"""

import logging
import threading
from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod
import importlib
import importlib.util
import inspect

from ..utils.exceptions import EpochlyError
from ..utils.decorators import singleton, thread_safe
from .plugin_loader import safe_load_plugins, PluginSecurityError, PluginLoadError


class PluginInterface(ABC):
    """Abstract base class for Epochly plugins."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the plugin."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up plugin resources."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass


class PluginRegistry:
    """Registry for managing plugin metadata and instances."""
    
    def __init__(self):
        self._plugins: Dict[str, PluginInterface] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    @thread_safe
    def register(self, plugin: PluginInterface, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a plugin instance."""
        if not isinstance(plugin, PluginInterface):
            raise EpochlyError(f"Plugin must implement PluginInterface: {type(plugin)}")
        
        name = plugin.name
        if name in self._plugins:
            raise EpochlyError(f"Plugin already registered: {name}")
        
        self._plugins[name] = plugin
        self._metadata[name] = metadata or {}
        
        logging.info(f"Registered plugin: {name} v{plugin.version}")
    
    @thread_safe
    def unregister(self, name: str) -> None:
        """Unregister a plugin."""
        if name not in self._plugins:
            raise EpochlyError(f"Plugin not found: {name}")
        
        plugin = self._plugins[name]
        try:
            plugin.cleanup()
        except Exception as e:
            logging.warning(f"Error cleaning up plugin {name}: {e}")
        
        del self._plugins[name]
        del self._metadata[name]
        
        logging.info(f"Unregistered plugin: {name}")
    
    @thread_safe
    def get(self, name: str) -> Optional[PluginInterface]:
        """Get a plugin by name."""
        return self._plugins.get(name)
    
    @thread_safe
    def list_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())
    
    @thread_safe
    def get_metadata(self, name: str) -> Dict[str, Any]:
        """Get plugin metadata."""
        return self._metadata.get(name, {}).copy()


@singleton
class PluginManager:
    """
    Central plugin manager for the Epochly framework.
    
    Manages plugin discovery, loading, registration, and lifecycle.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._registry = PluginRegistry()
        self._hooks: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the plugin manager."""
        if self._initialized:
            return
        
        self.logger.info("Initializing plugin manager")
        self._initialized = True
    
    @thread_safe
    def register_plugin(self, plugin: PluginInterface, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a plugin instance with thread safety."""
        with self._lock:
            try:
                plugin.initialize()
                self._registry.register(plugin, metadata)
                self.logger.info(f"Successfully registered plugin: {plugin.name}")
            except Exception as e:
                self.logger.error(f"Failed to register plugin {plugin.name}: {e}")
                raise EpochlyError(f"Plugin registration failed: {e}")
    
    @thread_safe
    def unregister_plugin(self, name: str) -> None:
        """Unregister a plugin by name with thread safety."""
        with self._lock:
            try:
                self._registry.unregister(name)
                self.logger.info(f"Successfully unregistered plugin: {name}")
            except Exception as e:
                self.logger.error(f"Failed to unregister plugin {name}: {e}")
                raise EpochlyError(f"Plugin unregistration failed: {e}")
    
    def get_plugin(self, name: str) -> Optional[PluginInterface]:
        """Get a plugin by name."""
        return self._registry.get(name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return self._registry.list_plugins()
    
    def get_plugin_metadata(self, name: str) -> Dict[str, Any]:
        """Get plugin metadata."""
        return self._registry.get_metadata(name)
    
    @thread_safe
    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """Register a hook callback."""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        
        if callback not in self._hooks[hook_name]:
            self._hooks[hook_name].append(callback)
            self.logger.debug(f"Registered hook: {hook_name}")
    
    @thread_safe
    def unregister_hook(self, hook_name: str, callback: Callable) -> None:
        """Unregister a hook callback."""
        if hook_name in self._hooks and callback in self._hooks[hook_name]:
            self._hooks[hook_name].remove(callback)
            self.logger.debug(f"Unregistered hook: {hook_name}")
    
    def trigger_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Trigger all callbacks for a hook."""
        results = []
        if hook_name in self._hooks:
            for callback in self._hooks[hook_name]:
                try:
                    result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Hook callback error in {hook_name}: {e}")
        
        return results
    
    def load_plugin_from_module(self, module_path: str, plugin_class_name: str) -> None:
        """Load a plugin from a module path."""
        try:
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, plugin_class_name)
            
            if not issubclass(plugin_class, PluginInterface):
                raise EpochlyError(f"Plugin class must inherit from PluginInterface: {plugin_class}")
            
            plugin_instance = plugin_class()
            self.register_plugin(plugin_instance)
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin from {module_path}: {e}")
            raise EpochlyError(f"Plugin loading failed: {e}")
    
    def discover_plugins(self, group_name: str = "epochly.plugins") -> List[str]:
        """
        Discover plugins using secure entry points mechanism.
        
        Args:
            group_name: Entry point group name for Epochly plugins
            
        Returns:
            List of discovered plugin entry point names
        """
        discovered = []
        
        try:
            # Use the secure plugin loader for discovery
            plugin_modules = safe_load_plugins(group_name)
            
            for module in plugin_modules:
                try:
                    module_name = getattr(module, '__name__', 'unknown')
                    
                    # Look for plugin classes in the module that implement PluginInterface
                    plugin_classes = []
                    for attr_name in dir(module):
                        if not attr_name.startswith('_'):
                            attr = getattr(module, attr_name)
                            if (inspect.isclass(attr) and
                                issubclass(attr, PluginInterface) and
                                attr != PluginInterface):
                                plugin_classes.append(attr)
                    
                    if plugin_classes:
                        discovered.append(module_name)
                        self.logger.info(f"Discovered plugin module via secure loader: {module_name}")
                    else:
                        self.logger.warning(f"Module {module_name} contains no valid plugin classes")
                    
                except Exception as e:
                    module_name = getattr(module, '__name__', 'unknown')
                    self.logger.error(f"Error validating plugin module {module_name}: {e}")
            
        except (PluginSecurityError, PluginLoadError) as e:
            self.logger.error(f"Security/loading error during plugin discovery: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error discovering plugins: {e}")
        
        return discovered
    
    def shutdown(self) -> None:
        """Shutdown the plugin manager and cleanup all plugins."""
        self.logger.info("Shutting down plugin manager")
        
        # Unregister all plugins
        plugin_names = self.list_plugins().copy()
        for name in plugin_names:
            try:
                self.unregister_plugin(name)
            except Exception as e:
                self.logger.error(f"Error during plugin shutdown {name}: {e}")
        
        # Clear hooks
        with self._lock:
            self._hooks.clear()
        
        self._initialized = False
        self.logger.info("Plugin manager shutdown complete")
    
    def load_plugins(self) -> None:
        """Load plugins from default plugin directory."""
        # Initialize the plugin manager
        self.initialize()
        self.logger.info("Plugin loading completed")
    
    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugin names."""
        return self.list_plugins()
    
    def unload_all_plugins(self) -> None:
        """Unload all plugins."""
        self.shutdown()