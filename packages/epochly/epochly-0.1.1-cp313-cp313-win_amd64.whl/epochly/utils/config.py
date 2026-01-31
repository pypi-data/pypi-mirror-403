"""
Epochly Configuration Management

Centralized configuration system for the Epochly framework.
"""

import os
import json
import threading
from typing import Any, Dict, Optional
from pathlib import Path

from .logger import get_logger
from .exceptions import EpochlyConfigError


class ConfigManager:
    """
    Thread-safe configuration manager for Epochly settings.
    
    Supports hierarchical configuration with environment variable overrides,
    file-based configuration, and runtime updates.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.logger = get_logger(__name__)
        self._config = {}
        self._lock = threading.RLock()
        self._config_file = config_file
        self._defaults = self._get_default_config()
        
        # Load configuration
        self._load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values.
        
        Returns:
            Dictionary of default configuration values
        """
        return {
            # Core settings
            'core': {
                'enabled': True,
                'auto_init': True,
                'enhancement_level': 'auto',  # auto, 0, 1, 2, 3
                'fallback_on_error': True,
            },
            
            # Monitoring settings
            'monitoring': {
                'enabled': True,
                'interval': 1.0,  # seconds
                'metrics_retention': 3600,  # seconds
                'export_prometheus': False,
                'prometheus_port': 8000,
            },
            
            # Threading settings
            'threading': {
                'max_workers': None,  # auto-detect
                'use_subinterpreters': True,
                'thread_pool_size': 4,
                'queue_size': 1000,
            },
            
            # Memory settings
            'memory': {
                'shared_memory_size': 1024 * 1024 * 100,  # 100MB
                'numa_aware': True,
                'zero_copy': None,  # Auto-detect based on system capabilities
                'gc_optimization': True,
            },
            
            # JIT settings
            'jit': {
                'enabled': True,
                'backend': 'auto',  # auto, numba, jax, taichi
                'cache_size': 1000,
                'optimization_level': 2,
            },
            
            # Plugin settings
            'plugins': {
                'enabled': True,
                'auto_load': True,
                'plugin_dirs': ['plugins'],
                'blacklist': [],
            },
            
            # Logging settings
            'logging': {
                'level': 'INFO',
                'file': None,
                'max_size': 10 * 1024 * 1024,  # 10MB
                'backup_count': 5,
                'performance_logging': True,
            },
            
            # Development settings
            'development': {
                'debug_mode': False,
                'profile_enabled': False,
                'trace_enabled': False,
                'test_mode': False,
            }
        }
    
    def _load_config(self):
        """Load configuration from various sources."""
        with self._lock:
            # Start with defaults - need deep copy for nested dicts
            import copy
            self._config = copy.deepcopy(self._defaults)
            
            # Load from file if specified
            if self._config_file:
                self._load_from_file(self._config_file)
            
            # Load from environment variables
            self._load_from_environment()
            
            # Defer zero-copy capability detection until first use
            # This prevents import-time initialization and resource exhaustion during tests
            if self._config['memory']['zero_copy'] is None:
                # Set to None to indicate it needs lazy detection
                self._config['memory']['zero_copy'] = None
            
            self.logger.debug("Configuration loaded successfully")
    
    def _detect_zero_copy_capability(self) -> bool:
        """
        Detect if the system supports zero-copy memory transfers.
        
        Tests SharedMemoryManager functionality to determine if zero-copy
        operations are available and working correctly.
        
        Returns:
            bool: True if zero-copy is supported, False otherwise
        """
        # Check if in test mode or auto-init disabled BEFORE importing
        if (os.environ.get('EPOCHLY_TEST_MODE', '').lower() in ('1', 'true', 'yes', 'on') or
            os.environ.get('EPOCHLY_DISABLE_AUTO_INIT', '').lower() in ('1', 'true', 'yes', 'on')):
            self.logger.debug("Test mode or auto-init disabled - disabling zero-copy capability")
            return False
            
        try:
            # Try to import SharedMemoryManager
            from ..plugins.executor.shared_memory_manager import SharedMemoryManager
            
            # Create a test instance with small memory pool
            test_manager = SharedMemoryManager(pool_size=1024 * 1024)  # 1MB test pool
            
            try:
                # Test basic zero-copy buffer operations
                test_data = b"test_zero_copy_capability"
                buffer = test_manager.create_zero_copy_buffer(
                    data=test_data,
                    data_type='bytes'
                )
                
                # Verify we can read the buffer back - pass the buffer object, not just the ID
                test_manager.read_zero_copy_buffer(buffer)
                
                # Clean up the specific buffer
                test_manager.deallocate_block(buffer.memory_block.block_id)
                
                # If we got here without exceptions, zero-copy is supported
                self.logger.debug("Zero-copy memory transfers are supported")
                return True
                
            finally:
                # Always cleanup the shared memory manager
                test_manager.cleanup()
            
        except ImportError:
            self.logger.debug("SharedMemoryManager not available, zero-copy disabled")
            return False
        except Exception as e:
            self.logger.debug(f"Zero-copy capability test failed: {e}, zero-copy disabled")
            return False
    
    def _load_from_file(self, config_file: str):
        """
        Load configuration from JSON file.
        
        Args:
            config_file: Path to configuration file
        """
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                
                # Merge with existing config
                self._deep_merge(self._config, file_config)
                self.logger.debug(f"Loaded configuration from {config_file}")
            else:
                self.logger.debug(f"Configuration file {config_file} not found, using defaults")
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration from {config_file}: {e}")
            # Don't raise exception - continue with defaults
            # This allows the system to continue even with invalid config files
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        env_prefix = 'EPOCHLY_'
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                # Convert environment variable to config path
                config_key = key[len(env_prefix):].lower()
                parts = config_key.split('_')
                
                # Smart parsing: First part is the section, rest is the key
                # This handles cases like EPOCHLY_CORE_ENHANCEMENT_LEVEL -> ['core', 'enhancement_level']
                if len(parts) > 1:
                    config_path = [parts[0], '_'.join(parts[1:])]
                else:
                    config_path = parts
                
                # Get the current/default value to determine expected type
                try:
                    current_value = self._get_nested_value(self._config, config_path)
                    expected_type = type(current_value) if current_value is not None else None
                except (KeyError, TypeError):
                    expected_type = None
                
                # Convert string value to appropriate type
                converted_value = self._convert_env_value(value, expected_type, config_path)
                
                # Only set if conversion was successful (not None)
                if converted_value is not None:
                    self._set_nested_value(self._config, config_path, converted_value)
                    self.logger.debug(f"Set config from env: {config_key} = {converted_value} (type: {type(converted_value).__name__})")
                else:
                    self.logger.debug(f"Skipping invalid env value: {key} = {value}")
    
    def _get_nested_value(self, config: Dict, path: list) -> Any:
        """
        Get a nested configuration value.
        
        Args:
            config: Configuration dictionary
            path: List of keys representing the path
            
        Returns:
            Value at the path
            
        Raises:
            KeyError: If path doesn't exist
        """
        current = config
        for key in path:
            current = current[key]
        return current
    
    def _convert_env_value(self, value: str, expected_type: Optional[type] = None, config_path: Optional[list] = None) -> Any:
        """
        Convert environment variable string to appropriate type.
        
        Args:
            value: String value from environment
            expected_type: Expected type based on default value
            config_path: Configuration path for validation
            
        Returns:
            Converted value or None if conversion fails for typed values
        """
        # Handle lists (comma-separated values)
        if expected_type == list:
            return [v.strip() for v in value.split(',') if v.strip()]
        
        # Boolean conversion
        lower_value = value.lower()
        if expected_type == bool or lower_value in ('true', 'false', '1', '0', 'yes', 'no', 'on', 'off'):
            if lower_value in ('true', '1', 'yes', 'on'):
                return True
            elif lower_value in ('false', '0', 'no', 'off'):
                return False
            elif expected_type == bool:
                # Invalid boolean value, return None to skip
                return None
        
        # Integer conversion
        if expected_type == int:
            try:
                return int(value)
            except ValueError:
                return None  # Invalid integer
        
        # Float conversion
        if expected_type == float:
            try:
                return float(value)
            except ValueError:
                return None  # Invalid float
        
        # Special case: If expected type is string but value looks numeric,
        # allow conversion for configuration values that can be string or int
        # (like enhancement_level which can be 'auto', 0, 1, 2, 3)
        if expected_type == str:
            # Special validation for known config values
            if config_path == ['core', 'enhancement_level']:
                # Valid values: 'auto', 0, 1, 2, 3
                if value == 'auto':
                    return value
                try:
                    int_val = int(value)
                    if 0 <= int_val <= 3:
                        return int_val
                    else:
                        return None  # Invalid enhancement level
                except ValueError:
                    return None  # Invalid value
            
            # For other string configs, try integer conversion first
            try:
                return int(value)
            except ValueError:
                pass
            
            # Try float conversion
            try:
                return float(value)
            except ValueError:
                pass
        
        # Try auto-detection if no expected type
        if expected_type is None:
            # Try integer
            try:
                return int(value)
            except ValueError:
                pass
            
            # Try float
            try:
                return float(value)
            except ValueError:
                pass
            
            # Try JSON for complex types
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Return as string
        return value
    
    def _deep_merge(self, target: Dict, source: Dict):
        """
        Deep merge source dictionary into target dictionary.
        
        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def _set_nested_value(self, config: Dict, path: list, value: Any):
        """
        Set a nested configuration value.
        
        Args:
            config: Configuration dictionary
            path: List of keys representing the path
            value: Value to set
        """
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[path[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        with self._lock:
            try:
                keys = key.split('.')
                value = self._config
                
                for k in keys:
                    value = value[k]
                
                # Handle lazy detection of zero-copy capability
                if key == 'memory.zero_copy' and value is None:
                    # Perform lazy detection now
                    value = self._detect_zero_copy_capability()
                    # Cache the result
                    self._config['memory']['zero_copy'] = value
                
                return value
                
            except (KeyError, TypeError):
                return default
    
    def set(self, key: str, value: Any):
        """
        Set configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        # Validate key
        if not key or key.startswith('.') or key.endswith('.') or '..' in key:
            raise EpochlyConfigError(f"Invalid configuration key: '{key}'")
        
        with self._lock:
            keys = key.split('.')
            self._set_nested_value(self._config, keys, value)
            self.logger.debug(f"Set config: {key} = {value}")
    
    def update(self, config: Dict[str, Any]):
        """
        Update configuration with dictionary.
        
        Args:
            config: Dictionary of configuration updates
        """
        with self._lock:
            self._deep_merge(self._config, config)
            self.logger.debug(f"Updated configuration with {len(config)} items")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Dictionary containing section configuration
        """
        return self.get(section, {})
    
    def save(self, config_file: Optional[str] = None):
        """
        Save current configuration to file.
        
        Args:
            config_file: Optional file path (uses default if not specified)
        """
        file_path = config_file or self._config_file
        if not file_path:
            raise EpochlyConfigError("No configuration file specified")
        
        try:
            with self._lock:
                config_path = Path(file_path)
                config_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(config_path, 'w') as f:
                    json.dump(self._config, f, indent=2)
                
                self.logger.info(f"Configuration saved to {file_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise EpochlyConfigError(f"Failed to save configuration: {e}")
    
    def reload(self):
        """Reload configuration from all sources."""
        with self._lock:
            self.logger.info("Reloading configuration")
            self._load_config()
    
    def reset(self):
        """Reset configuration to defaults."""
        with self._lock:
            self.logger.info("Resetting configuration to defaults")
            self._config = self._get_default_config()
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get complete configuration dictionary.
        
        Returns:
            Complete configuration dictionary
        """
        with self._lock:
            return self._config.copy()
    
    def export(self) -> Dict[str, Any]:
        """
        Export current configuration.
        
        Returns:
            Complete configuration dictionary
        """
        return self.get_all()
    
    def validate(self) -> bool:
        """
        Validate current configuration.
        
        Returns:
            True if configuration is valid
        """
        try:
            # Validate core settings
            core_config = self.get_section('core')
            if not isinstance(core_config.get('enabled'), bool):
                raise EpochlyConfigError("core.enabled must be boolean")
            
            # Validate monitoring settings
            monitoring_config = self.get_section('monitoring')
            interval = monitoring_config.get('interval')
            if interval is not None and (not isinstance(interval, (int, float)) or interval <= 0):
                raise EpochlyConfigError("monitoring.interval must be positive number")
            
            # Validate threading settings
            threading_config = self.get_section('threading')
            max_workers = threading_config.get('max_workers')
            if max_workers is not None and (not isinstance(max_workers, int) or max_workers <= 0):
                raise EpochlyConfigError("threading.max_workers must be positive integer")
            
            self.logger.debug("Configuration validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False


# Global configuration instance with thread safety
_config_manager = None
_config_lock = threading.RLock()

def get_config() -> ConfigManager:
    """Get the global configuration manager instance with thread safety."""
    global _config_manager
    if _config_manager is None:
        with _config_lock:
            # Double-check locking pattern
            if _config_manager is None:
                config_file = os.environ.get('EPOCHLY_CONFIG_FILE')
                _config_manager = ConfigManager(config_file)
    return _config_manager