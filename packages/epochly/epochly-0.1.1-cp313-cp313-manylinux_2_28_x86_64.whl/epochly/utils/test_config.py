"""
Test Configuration Manager for Epochly

Provides a test-specific configuration implementation that extends ConfigManager
for use in test environments without requiring mocks in production code.

This ensures complete separation of test and production code while maintaining
full compatibility with the ConfigManager interface.

Author: Epochly Development Team
"""

from typing import Any, Dict, Optional, List
from .config import ConfigManager


class TestConfigManager(ConfigManager):
    """
    Test-specific configuration manager that provides controlled behavior
    for testing without using mocks in production code.
    """
    __test__ = False  # Tell pytest this is not a test class

    def __init__(self, config_overrides: Optional[Dict[str, Any]] = None):
        """
        Initialize test configuration manager with optional overrides.
        
        Args:
            config_overrides: Dictionary of configuration values to override defaults
        """
        # Initialize with test defaults
        self._test_config = {
            'enhancement_level': 0,  # Start at monitoring only
            'max_workers': 0,
            'shared_memory_size': 0,
            'enable_jit': False,
            'enable_numba': False,
            'enable_gpu': False,
            'telemetry_enabled': False,  # Disable telemetry in tests
            'mode': 'test',
            'debug': True,
            'test_mode': True,  # Explicit test mode flag
            'offline_mode': True,  # No network calls in tests
        }
        
        # Apply any overrides
        if config_overrides:
            self._test_config.update(config_overrides)
        
        # Don't call parent __init__ to avoid file system operations
        self._config = self._test_config
        self._env_vars = {}
        self._config_file = None
        self._initialized = True
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with test-specific behavior.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self._test_config.get(key, default)
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get boolean configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Boolean configuration value
        """
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """
        Get integer configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Integer configuration value
        """
        value = self.get(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """
        Get float configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Float configuration value
        """
        value = self.get(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
    
    def get_list(self, key: str, default: Optional[List] = None) -> List:
        """
        Get list configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            List configuration value
        """
        value = self.get(key, default or [])
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [v.strip() for v in value.split(',') if v.strip()]
        return default or []
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value for testing.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self._test_config[key] = value
    
    def reset(self) -> None:
        """Reset configuration to initial test defaults."""
        self._test_config = {
            'enhancement_level': 0,
            'max_workers': 0,
            'shared_memory_size': 0,
            'enable_jit': False,
            'enable_numba': False,
            'enable_gpu': False,
            'telemetry_enabled': False,
            'mode': 'test',
            'debug': True,
            'test_mode': True,
            'offline_mode': True,
        }
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple configuration values at once.
        
        Args:
            updates: Dictionary of configuration updates
        """
        self._test_config.update(updates)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values for inspection."""
        return self._test_config.copy()
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"TestConfigManager({self._test_config})"