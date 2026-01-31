"""
Epochly Deployment Configuration Management

This module provides centralized configuration management for the Epochly deployment
infrastructure. It handles environment variable parsing, validation, and runtime
configuration updates as specified in the deployment refinement plan Phase 1.3.

Author: Epochly Development Team
Created: 2025-06-05
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path


@dataclass
class Configuration:
    """
    Centralized configuration for Epochly deployment infrastructure.
    
    This dataclass provides a single source of truth for all configuration
    settings, with runtime environment variable reading and validation.
    
    Attributes:
        config_path: Path to Epochly configuration file
        enabled: Whether Epochly deployment is enabled
        emergency_disable: Emergency killswitch status
        log_level: Logging level for deployment components
        memory_threshold_mb: Memory threshold for emergency controls (MB)
        cpu_threshold_percent: CPU threshold for emergency controls (%)
        backup_retention_days: Number of days to retain backup files
        file_permissions: Default file permissions (octal)
        dir_permissions: Default directory permissions (octal)
        timeout_seconds: Default timeout for operations (seconds)
        max_retries: Maximum number of retries for operations
        container_aware: Whether to use container-aware resource monitoring
    """
    
    # Core deployment settings
    config_path: Optional[str] = None
    enabled: bool = True
    emergency_disable: bool = False
    
    # Logging configuration
    log_level: str = "INFO"
    
    # Resource monitoring thresholds
    memory_threshold_mb: int = 1024
    cpu_threshold_percent: float = 80.0
    
    # File management settings
    backup_retention_days: int = 30
    file_permissions: int = 0o644
    dir_permissions: int = 0o755
    
    # Operation settings
    timeout_seconds: int = 30
    max_retries: int = 3
    
    # Advanced features
    container_aware: bool = True
    
    # Internal state
    _env_vars_loaded: bool = field(default=False, init=False)
    _validation_errors: List[str] = field(default_factory=list, init=False)
    
    def __post_init__(self) -> None:
        """Initialize configuration by loading from environment variables."""
        self.reload_from_env()
    
    def reload_from_env(self) -> None:
        """
        Reload configuration from environment variables at runtime.
        
        This method reads all Epochly-related environment variables and updates
        the configuration accordingly. It provides runtime configuration
        updates as required by the refinement plan.
        """
        self._validation_errors.clear()
        
        # Core deployment settings
        self.config_path = os.environ.get('EPOCHLY_CONFIG_PATH')
        self.enabled = self._parse_bool_env('EPOCHLY_ENABLED', self.enabled)
        self.emergency_disable = self._parse_bool_env('EPOCHLY_EMERGENCY_DISABLE', self.emergency_disable)
        
        # Logging configuration
        self.log_level = os.environ.get('EPOCHLY_LOG_LEVEL', self.log_level).strip().upper()
        
        # Resource monitoring thresholds
        self.memory_threshold_mb = self._parse_int_env(
            'EPOCHLY_MEMORY_THRESHOLD_MB', 
            self.memory_threshold_mb,
            min_value=64,
            max_value=32768
        )
        self.cpu_threshold_percent = self._parse_float_env(
            'EPOCHLY_CPU_THRESHOLD_PERCENT',
            self.cpu_threshold_percent,
            min_value=10.0,
            max_value=100.0
        )
        
        # File management settings
        self.backup_retention_days = self._parse_int_env(
            'EPOCHLY_BACKUP_RETENTION_DAYS',
            self.backup_retention_days,
            min_value=1,
            max_value=365
        )
        self.file_permissions = self._parse_octal_env(
            'EPOCHLY_FILE_PERMISSIONS',
            self.file_permissions
        )
        self.dir_permissions = self._parse_octal_env(
            'EPOCHLY_DIR_PERMISSIONS',
            self.dir_permissions
        )
        
        # Operation settings
        self.timeout_seconds = self._parse_int_env(
            'EPOCHLY_TIMEOUT_SECONDS',
            self.timeout_seconds,
            min_value=1,
            max_value=300
        )
        self.max_retries = self._parse_int_env(
            'EPOCHLY_MAX_RETRIES',
            self.max_retries,
            min_value=0,
            max_value=10
        )
        
        # Advanced features
        self.container_aware = self._parse_bool_env('EPOCHLY_CONTAINER_AWARE', self.container_aware)
        
        self._env_vars_loaded = True
        
        # Validate configuration after loading
        self._validate_configuration()
    
    def _parse_bool_env(self, env_var: str, default: bool) -> bool:
        """
        Parse boolean environment variable with consistent handling.
        
        Supports various boolean representations as specified in the
        refinement plan for consistent boolean parsing.
        
        Args:
            env_var: Environment variable name
            default: Default value if not set or invalid
            
        Returns:
            Parsed boolean value
        """
        value = os.environ.get(env_var)
        if value is None:
            return default
        
        # Normalize to lowercase for comparison
        value_lower = value.lower().strip()
        
        # True values
        if value_lower in ('1', 'true', 'yes', 'on', 'enabled'):
            return True
        
        # False values
        if value_lower in ('0', 'false', 'no', 'off', 'disabled', ''):
            return False
        
        # Invalid value - log warning and use default
        self._validation_errors.append(
            f"Invalid boolean value for {env_var}: '{value}'. Using default: {default}"
        )
        return default
    
    def _parse_int_env(self, env_var: str, default: int, min_value: Optional[int] = None, 
                       max_value: Optional[int] = None) -> int:
        """
        Parse integer environment variable with validation.
        
        Args:
            env_var: Environment variable name
            default: Default value if not set or invalid
            min_value: Minimum allowed value (optional)
            max_value: Maximum allowed value (optional)
            
        Returns:
            Parsed integer value
        """
        value = os.environ.get(env_var)
        if value is None:
            return default
        
        try:
            parsed_value = int(value.strip())
            
            # Validate range if specified
            if min_value is not None and parsed_value < min_value:
                self._validation_errors.append(
                    f"{env_var} value {parsed_value} below minimum {min_value}. Using default: {default}"
                )
                return default
            
            if max_value is not None and parsed_value > max_value:
                self._validation_errors.append(
                    f"{env_var} value {parsed_value} above maximum {max_value}. Using default: {default}"
                )
                return default
            
            return parsed_value
            
        except ValueError:
            self._validation_errors.append(
                f"Invalid integer value for {env_var}: '{value}'. Using default: {default}"
            )
            return default
    
    def _parse_float_env(self, env_var: str, default: float, min_value: Optional[float] = None,
                         max_value: Optional[float] = None) -> float:
        """
        Parse float environment variable with validation.
        
        Args:
            env_var: Environment variable name
            default: Default value if not set or invalid
            min_value: Minimum allowed value (optional)
            max_value: Maximum allowed value (optional)
            
        Returns:
            Parsed float value
        """
        value = os.environ.get(env_var)
        if value is None:
            return default
        
        try:
            parsed_value = float(value.strip())
            
            # Validate range if specified
            if min_value is not None and parsed_value < min_value:
                self._validation_errors.append(
                    f"{env_var} value {parsed_value} below minimum {min_value}. Using default: {default}"
                )
                return default
            
            if max_value is not None and parsed_value > max_value:
                self._validation_errors.append(
                    f"{env_var} value {parsed_value} above maximum {max_value}. Using default: {default}"
                )
                return default
            
            return parsed_value
            
        except ValueError:
            self._validation_errors.append(
                f"Invalid float value for {env_var}: '{value}'. Using default: {default}"
            )
            return default
    
    def _parse_octal_env(self, env_var: str, default: int) -> int:
        """
        Parse octal permission environment variable.
        
        Args:
            env_var: Environment variable name
            default: Default octal value
            
        Returns:
            Parsed octal permission value
        """
        value = os.environ.get(env_var)
        if value is None:
            return default
        
        try:
            # Handle both '0o644' and '644' formats
            value = value.strip()
            if value.startswith('0o') or value.startswith('0O'):
                parsed_value = int(value, 8)
            else:
                parsed_value = int(value, 8)
            
            # Validate reasonable permission range
            if parsed_value < 0o000 or parsed_value > 0o777:
                self._validation_errors.append(
                    f"Invalid permission value for {env_var}: '{value}'. Using default: {oct(default)}"
                )
                return default
            
            return parsed_value
            
        except ValueError:
            self._validation_errors.append(
                f"Invalid octal value for {env_var}: '{value}'. Using default: {oct(default)}"
            )
            return default
    
    def _validate_configuration(self) -> None:
        """
        Validate the complete configuration for consistency and correctness.
        
        This method performs cross-field validation and logs any issues
        found during configuration loading.
        """
        # Validate log level
        valid_log_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if self.log_level not in valid_log_levels:
            self._validation_errors.append(
                f"Invalid log level: '{self.log_level}'. Valid levels: {valid_log_levels}"
            )
            self.log_level = 'INFO'
        
        # Validate config path if specified
        if self.config_path and not Path(self.config_path).parent.exists():
            self._validation_errors.append(
                f"Config path directory does not exist: {Path(self.config_path).parent}"
            )
        
        # Log validation errors if any
        if self._validation_errors:
            logger = logging.getLogger(__name__)
            for error in self._validation_errors:
                logger.warning(f"Configuration validation: {error}")
    
    def is_valid(self) -> bool:
        """
        Check if the configuration is valid.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        return len(self._validation_errors) == 0
    
    def get_validation_errors(self) -> List[str]:
        """
        Get list of validation errors encountered during configuration loading.
        
        Returns:
            List of validation error messages
        """
        return self._validation_errors.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary representation.
        
        Returns:
            Dictionary containing all configuration values
        """
        return {
            'config_path': self.config_path,
            'enabled': self.enabled,
            'emergency_disable': self.emergency_disable,
            'log_level': self.log_level,
            'memory_threshold_mb': self.memory_threshold_mb,
            'cpu_threshold_percent': self.cpu_threshold_percent,
            'backup_retention_days': self.backup_retention_days,
            'file_permissions': oct(self.file_permissions),
            'dir_permissions': oct(self.dir_permissions),
            'timeout_seconds': self.timeout_seconds,
            'max_retries': self.max_retries,
            'container_aware': self.container_aware,
            'env_vars_loaded': self._env_vars_loaded,
            'validation_errors': self._validation_errors
        }
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"Configuration(enabled={self.enabled}, emergency_disable={self.emergency_disable})"
    
    def __repr__(self) -> str:
        """Detailed string representation of configuration."""
        return f"Configuration({self.to_dict()})"


# Global configuration instance
_global_config: Optional[Configuration] = None


def get_config() -> Configuration:
    """
    Get the global configuration instance.
    
    This function provides access to the centralized configuration
    throughout the deployment infrastructure.
    
    Returns:
        Global Configuration instance
    """
    global _global_config
    if _global_config is None:
        _global_config = Configuration()
    return _global_config


def reload_config() -> Configuration:
    """
    Reload the global configuration from environment variables.
    
    This function forces a reload of the configuration from environment
    variables, useful for runtime configuration updates.
    
    Returns:
        Reloaded Configuration instance
    """
    global _global_config
    if _global_config is None:
        _global_config = Configuration()
    else:
        _global_config.reload_from_env()
    return _global_config


def reset_config() -> None:
    """
    Reset the global configuration instance.
    
    This function is primarily used for testing to ensure clean
    configuration state between tests.
    """
    global _global_config
    _global_config = None