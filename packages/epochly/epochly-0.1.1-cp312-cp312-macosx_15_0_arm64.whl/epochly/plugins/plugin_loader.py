"""
Epochly Secure Plugin Loader

This module provides secure plugin loading with entry point compatibility,
security validation, and proper error handling.

Author: Epochly Development Team
"""

import logging
from typing import List, Optional, Set
from types import ModuleType

from .compat import iter_entry_points

# Security configuration
ALLOWED_GROUP = "epochly.plugins"
BLOCKED_PREFIXES = ("_", ".", "__")
REQUIRED_PLUGIN_ATTRIBUTE = "__epochly_plugin__"

logger = logging.getLogger(__name__)


class PluginSecurityError(Exception):
    """Raised when a plugin fails security validation."""
    pass


class PluginLoadError(Exception):
    """Raised when a plugin fails to load properly."""
    pass


def validate_plugin_name(name: str) -> bool:
    """
    Validate plugin name for security.
    
    Args:
        name: Plugin entry point name
        
    Returns:
        True if name is valid, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    
    # Block private/hidden plugins
    for prefix in BLOCKED_PREFIXES:
        if name.startswith(prefix):
            return False
    
    # Basic name validation
    if not name.replace("_", "").replace("-", "").isalnum():
        return False
    
    return True


def validate_plugin_module(module: ModuleType) -> bool:
    """
    Validate loaded plugin module for security.
    
    Args:
        module: Loaded plugin module
        
    Returns:
        True if module is valid, False otherwise
    """
    if not module:
        return False
    
    # Ensure it's actually a module type
    if not isinstance(module, ModuleType):
        return False
    
    # Check for required plugin marker
    if not getattr(module, REQUIRED_PLUGIN_ATTRIBUTE, False):
        module_name = getattr(module, '__name__', 'unknown')
        logger.warning(f"Plugin {module_name} missing {REQUIRED_PLUGIN_ATTRIBUTE} marker")
        return False
    
    # Check module source location for security
    module_file = getattr(module, '__file__', None)
    if module_file:
        # Reject suspicious paths
        suspicious_paths = ['/etc/', '/proc/', '/sys/', '/dev/', '/root/']
        if any(module_file.startswith(path) for path in suspicious_paths):
            logger.warning(f"Plugin {module.__name__} from suspicious location: {module_file}")
            return False
    
    # Additional security checks can be added here
    # - Validate digital signatures
    # - Scan for suspicious imports
    
    return True


def safe_load_plugins(group: Optional[str] = None, name: Optional[str] = None) -> List[ModuleType]:
    """
    Safely load plugins with security validation.
    
    Args:
        group: Entry point group (defaults to ALLOWED_GROUP)
        name: Optional specific plugin name to load
        
    Returns:
        List of validated plugin modules
        
    Raises:
        PluginSecurityError: If security validation fails
        PluginLoadError: If plugin loading fails
    """
    if group is None:
        group = ALLOWED_GROUP
    
    # Security check: only allow approved groups
    if group != ALLOWED_GROUP:
        raise PluginSecurityError(f"Plugin group '{group}' not allowed. Only '{ALLOWED_GROUP}' is permitted.")
    
    plugins = []
    loaded_names: Set[str] = set()
    
    try:
        for entry_point in iter_entry_points(group, name=name):
            try:
                # Validate entry point name
                ep_name = getattr(entry_point, 'name', None)
                if not ep_name or not validate_plugin_name(ep_name):
                    logger.warning(f"Skipping plugin with invalid name: {ep_name}")
                    continue
                
                # Avoid duplicate loading
                if ep_name in loaded_names:
                    logger.debug(f"Plugin {ep_name} already loaded, skipping")
                    continue
                
                logger.debug(f"Loading plugin: {ep_name}")
                
                # Load the plugin module
                try:
                    module = entry_point.load()
                except Exception as e:
                    logger.error(f"Failed to load plugin {ep_name}: {e}")
                    raise PluginLoadError(f"Plugin {ep_name} failed to load: {e}") from e
                
                # Validate the loaded module
                if not validate_plugin_module(module):
                    logger.warning(f"Plugin {ep_name} failed security validation")
                    continue
                
                plugins.append(module)
                loaded_names.add(ep_name)
                logger.info(f"Successfully loaded plugin: {ep_name}")
                
            except (PluginSecurityError, PluginLoadError):
                # Re-raise security and load errors
                raise
            except Exception as e:
                # Log other errors but continue loading
                logger.error(f"Unexpected error loading plugin {getattr(entry_point, 'name', 'unknown')}: {e}")
                continue
                
    except Exception as e:
        if isinstance(e, (PluginSecurityError, PluginLoadError)):
            raise
        logger.error(f"Error discovering plugins in group {group}: {e}")
        raise PluginLoadError(f"Plugin discovery failed: {e}") from e
    
    logger.info(f"Loaded {len(plugins)} plugins from group {group}")
    return plugins


def get_plugin_info(module: ModuleType) -> dict:
    """
    Extract plugin information from a loaded module.
    
    Args:
        module: Loaded plugin module
        
    Returns:
        Dictionary with plugin information
    """
    doc = getattr(module, '__doc__', '') or ''
    return {
        'name': getattr(module, '__name__', 'unknown'),
        'version': getattr(module, '__version__', 'unknown'),
        'description': doc.strip() if doc else 'No description',
        'author': getattr(module, '__author__', 'unknown'),
        'epochly_plugin': getattr(module, REQUIRED_PLUGIN_ATTRIBUTE, False),
        'file': getattr(module, '__file__', 'unknown'),
    }


def list_available_plugins(group: Optional[str] = None) -> List[dict]:
    """
    List available plugins without loading them.
    
    Args:
        group: Entry point group (defaults to ALLOWED_GROUP)
        
    Returns:
        List of plugin information dictionaries
    """
    if group is None:
        group = ALLOWED_GROUP
    
    plugins_info = []
    
    try:
        for entry_point in iter_entry_points(group):
            ep_name = getattr(entry_point, 'name', 'unknown')
            ep_module = getattr(entry_point, 'module', 'unknown')
            ep_attr = getattr(entry_point, 'attr', None)
            
            plugins_info.append({
                'name': ep_name,
                'module': ep_module,
                'attr': ep_attr,
                'group': group,
                'valid_name': validate_plugin_name(ep_name),
            })
    except Exception as e:
        logger.error(f"Error listing plugins in group {group}: {e}")
    
    return plugins_info