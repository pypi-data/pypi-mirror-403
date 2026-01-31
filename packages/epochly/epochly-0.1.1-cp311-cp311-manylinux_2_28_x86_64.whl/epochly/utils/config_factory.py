"""
Configuration Factory for Epochly

Provides factory methods to create appropriate configuration managers
for different environments (production, test, etc.) without requiring
mocks in production code.

This ensures complete separation of test and production code while
maintaining full compatibility.

Author: Epochly Development Team
"""

import os
from typing import Optional, Any
from .config import ConfigManager
from .test_config import TestConfigManager


class ConfigFactory:
    """
    Factory for creating appropriate configuration managers based on environment.
    
    This factory ensures that test-specific configuration is only used in test
    environments, and production code never imports or references test utilities.
    """
    
    # Singleton instance
    _test_config_override: Optional[Any] = None
    
    @classmethod
    def create_config(cls) -> ConfigManager:
        """
        Create appropriate configuration manager based on environment.
        
        This method checks for test environment indicators and returns
        the appropriate configuration implementation.
        
        Returns:
            ConfigManager: Production or test configuration manager
        """
        # Check if test config has been explicitly set
        if cls._test_config_override is not None:
            return cls._test_config_override
        
        # Check environment indicators
        # Note: We check multiple indicators for flexibility
        if any([
            os.environ.get('EPOCHLY_TEST_MODE') == '1',
            os.environ.get('PYTEST_CURRENT_TEST') is not None,
            os.environ.get('EPOCHLY_TESTING') == 'true',
            # Check if we're running under pytest
            'pytest' in os.environ.get('_', '').lower(),
        ]):
            # Return test configuration
            return TestConfigManager()
        
        # Return production configuration
        return ConfigManager()
    
    @classmethod
    def set_test_config(cls, config: Optional[Any]) -> None:
        """
        Set a specific test configuration override.
        
        This is useful for tests that need specific configuration behavior.
        
        Args:
            config: Test configuration to use, or None to clear override
        """
        cls._test_config_override = config
    
    @classmethod
    def reset(cls) -> None:
        """
        Reset factory to default state.
        
        This clears any test configuration overrides.
        """
        cls._test_config_override = None


def get_config() -> ConfigManager:
    """
    Convenience function to get appropriate configuration.
    
    Returns:
        ConfigManager: Appropriate configuration for current environment
    """
    return ConfigFactory.create_config()