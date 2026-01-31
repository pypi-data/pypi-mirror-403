"""Epochly configuration module.

This package provides configuration management for Epochly.
ConfigManager is re-exported here for backwards compatibility since
there's both a config.py file and config/ package.
"""

from .api_endpoints import APIEndpoints, get_api_endpoint

# Re-export ConfigManager from the config.py file for backwards compatibility
# This handles the naming conflict between config.py and config/ package
import sys
import os

# Import from the parent's config.py file using absolute import tricks
_config_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.py')
if os.path.exists(_config_file_path):
    import importlib.util
    _spec = importlib.util.spec_from_file_location("epochly._config_module", _config_file_path)
    _config_module = importlib.util.module_from_spec(_spec)
    sys.modules['epochly._config_module'] = _config_module
    try:
        _spec.loader.exec_module(_config_module)
        ConfigManager = _config_module.ConfigManager
        ConfigWizard = getattr(_config_module, 'ConfigWizard', None)
    except Exception as e:
        # If import fails, provide a placeholder
        ConfigManager = None
        ConfigWizard = None
else:
    ConfigManager = None
    ConfigWizard = None

__all__ = ['APIEndpoints', 'get_api_endpoint', 'ConfigManager', 'ConfigWizard']
