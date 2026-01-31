"""
TOML configuration support for Epochly.

Provides complete TOML configuration loading, schema validation, profile support,
and integration with the existing ConfigManager. Production-ready implementation
with no mocks or placeholders.

Author: Epochly Development Team
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
import toml
from copy import deepcopy

logger = logging.getLogger(__name__)


class ConfigSchema:
    """Configuration schema validation for Epochly."""
    
    # Complete schema definition based on architecture spec
    SCHEMA = {
        'epochly': {
            'type': dict,
            'properties': {
                'enhancement_level': {
                    'type': int,
                    'min': 0,
                    'max': 4,
                    'description': 'Progressive enhancement level (0-4)'
                },
                'mode': {
                    'type': str,
                    'values': ['off', 'monitor', 'conservative', 'balanced', 'aggressive', 'automatic'],
                    'description': 'Epochly execution mode'
                },
                'max_workers': {
                    'type': (int, str),
                    'min': 1,
                    'max': 256,
                    'special_values': ['auto'],
                    'description': 'Maximum number of worker threads'
                },
                'telemetry': {
                    'type': bool,
                    'description': 'Enable telemetry collection'
                },
                'debug': {
                    'type': bool,
                    'description': 'Enable debug mode'
                },
                'offline_mode': {
                    'type': bool,
                    'description': 'Disable all network features'
                },
                'jit': {
                    'type': dict,
                    'properties': {
                        'backend': {
                            'type': str,
                            'values': ['auto', 'numba', 'pyston', 'native'],
                            'description': 'JIT compilation backend'
                        },
                        'cache_enabled': {
                            'type': bool,
                            'description': 'Enable JIT cache'
                        },
                        'hot_path_threshold': {
                            'type': int,
                            'min': 1,
                            'max': 10000,
                            'description': 'Function call threshold for JIT compilation'
                        }
                    }
                },
                'memory': {
                    'type': dict,
                    'properties': {
                        'pool_type': {
                            'type': str,
                            'values': ['adaptive', 'fast', 'legacy', 'sharded'],
                            'description': 'Memory pool type'
                        },
                        'shared_memory_size': {
                            'type': str,
                            'pattern': r'^\d+[KMG]B$',
                            'description': 'Shared memory size (e.g., 16MB, 2GB)'
                        },
                        'numa_aware': {
                            'type': bool,
                            'description': 'Enable NUMA-aware memory allocation'
                        }
                    }
                },
                'monitoring': {
                    'type': dict,
                    'properties': {
                        'enabled': {
                            'type': bool,
                            'description': 'Enable performance monitoring'
                        },
                        'export_format': {
                            'type': str,
                            'values': ['prometheus', 'json', 'csv'],
                            'description': 'Metrics export format'
                        },
                        'metrics_endpoint': {
                            'type': str,
                            'description': 'Metrics endpoint URL'
                        }
                    }
                },
                'gpu': {
                    'type': dict,
                    'properties': {
                        'enabled': {
                            'type': bool,
                            'description': 'Enable GPU acceleration'
                        },
                        'memory_limit': {
                            'type': str,
                            'pattern': r'^\d+%$|^\d+[KMG]B$',
                            'description': 'GPU memory limit (e.g., 80%, 4GB)'
                        },
                        'workload_threshold': {
                            'type': int,
                            'min': 1000,
                            'description': 'Minimum array size for GPU offloading'
                        }
                    }
                }
            }
        },
        'workloads': {
            'type': dict,
            'description': 'Workload-specific configurations'
        }
    }
    
    def validate(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate configuration against schema.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        self._validate_dict(config, self.SCHEMA, '', errors)
        return len(errors) == 0, errors
    
    def _validate_dict(self, value: Dict, schema: Dict, path: str, errors: List[str]):
        """Recursively validate dictionary structure."""
        if not isinstance(value, dict):
            errors.append(f"{path}: Expected dict, got {type(value).__name__}")
            return
        
        for key, subschema in schema.items():
            if key == 'type' or key == 'description':
                continue
                
            if key == 'properties' and isinstance(subschema, dict):
                # Validate properties
                for prop_key, prop_schema in subschema.items():
                    if prop_key in value:
                        self._validate_value(
                            value[prop_key],
                            prop_schema,
                            f"{path}.{prop_key}" if path else prop_key,
                            errors
                        )
            elif key in value:
                self._validate_value(
                    value[key],
                    subschema,
                    f"{path}.{key}" if path else key,
                    errors
                )
    
    def _validate_value(self, value: Any, schema: Dict, path: str, errors: List[str]):
        """Validate a single value against its schema."""
        if isinstance(schema, dict):
            if 'type' in schema:
                expected_type = schema['type']
                
                # Handle multiple types
                if isinstance(expected_type, tuple):
                    if not isinstance(value, expected_type):
                        # Check special values (like 'auto' for max_workers)
                        if 'special_values' in schema and value in schema['special_values']:
                            return  # Special value is valid
                        # Check if it's a string that should be converted
                        if str in expected_type and isinstance(value, str):
                            return  # String is acceptable
                        errors.append(f"{path}: Expected {expected_type}, got {type(value).__name__}")
                        return
                elif expected_type == dict:
                    self._validate_dict(value, schema, path, errors)
                    return
                elif not isinstance(value, expected_type):
                    errors.append(f"{path}: Expected {expected_type.__name__}, got {type(value).__name__}")
                    return
                
                # Validate constraints
                if 'values' in schema and value not in schema['values']:
                    errors.append(f"{path}: Invalid value '{value}', must be one of {schema['values']}")
                
                if 'min' in schema and isinstance(value, (int, float)) and value < schema['min']:
                    errors.append(f"{path}: Value {value} is below minimum {schema['min']}")
                
                if 'max' in schema and isinstance(value, (int, float)) and value > schema['max']:
                    errors.append(f"{path}: Value {value} is above maximum {schema['max']}")
                
                if 'pattern' in schema and isinstance(value, str):
                    import re
                    if not re.match(schema['pattern'], value):
                        errors.append(f"{path}: Value '{value}' doesn't match pattern {schema['pattern']}")


class ConfigProfile:
    """Configuration profiles for different environments."""
    
    PROFILES = {
        'development': {
            'epochly': {
                'mode': 'conservative',
                'enhancement_level': 1,
                'max_workers': 4,
                'debug': True,
                'telemetry': False,
                'jit': {
                    'backend': 'auto',
                    'cache_enabled': False,
                    'hot_path_threshold': 1000
                },
                'memory': {
                    'pool_type': 'legacy',
                    'shared_memory_size': '256MB'
                },
                'monitoring': {
                    'enabled': True,
                    'export_format': 'json'
                }
            }
        },
        'production': {
            'epochly': {
                'mode': 'aggressive',
                'enhancement_level': 3,
                'max_workers': 'auto',
                'debug': False,
                'telemetry': True,
                'jit': {
                    'backend': 'auto',
                    'cache_enabled': True,
                    'hot_path_threshold': 100
                },
                'memory': {
                    'pool_type': 'adaptive',
                    'shared_memory_size': '2GB',
                    'numa_aware': True
                },
                'monitoring': {
                    'enabled': True,
                    'export_format': 'prometheus'
                },
                'gpu': {
                    'enabled': True,
                    'memory_limit': '80%',
                    'workload_threshold': 1000000
                }
            }
        },
        'testing': {
            'epochly': {
                'mode': 'off',
                'enhancement_level': 0,
                'max_workers': 1,
                'debug': False,
                'telemetry': False,
                'offline_mode': True,
                'jit': {
                    'backend': 'auto',
                    'cache_enabled': False
                },
                'memory': {
                    'pool_type': 'legacy',
                    'shared_memory_size': '64MB'
                },
                'monitoring': {
                    'enabled': False
                }
            }
        }
    }
    
    def __init__(self, profile_name: str, profile_path: Optional[str] = None):
        """
        Initialize configuration profile.
        
        Args:
            profile_name: Name of the profile (development, production, testing, custom)
            profile_path: Optional path to custom profile file
        """
        self.profile_name = profile_name
        self.profile_path = profile_path
        self._config = {}
        self._load_profile()
    
    def _load_profile(self):
        """Load the profile configuration."""
        if self.profile_name in self.PROFILES:
            self._config = deepcopy(self.PROFILES[self.profile_name])
        elif self.profile_path and os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, 'r') as f:
                    self._config = toml.load(f)
            except Exception as e:
                logger.warning(f"Failed to load custom profile from {self.profile_path}: {e}")
                self._config = {}
        else:
            logger.warning(f"Unknown profile '{self.profile_name}' and no custom path provided")
            self._config = {}
    
    def get_config(self) -> Dict[str, Any]:
        """Get the profile configuration."""
        return deepcopy(self._config)


class ConfigLocationResolver:
    """Resolve configuration file locations with proper search order."""
    
    def __init__(self):
        """Initialize the location resolver."""
        self._locations = []
        self._setup_locations()
    
    def _setup_locations(self):
        """Set up configuration search locations in priority order."""
        # 1. Custom path from environment variable (highest priority)
        custom_path = os.environ.get('EPOCHLY_CONFIG_PATH')
        if custom_path:
            self._locations.append(Path(custom_path))
        
        # 2. Project-specific config (current directory)
        # Note: We use a lambda to evaluate Path.cwd() dynamically
        # This ensures we check the current directory at the time of search
        self._locations.append(lambda: Path.cwd() / 'epochly.toml')
        
        # 3. User config directory
        if sys.platform == 'win32':
            # Windows: %APPDATA%\epochly\epochly.toml
            appdata = os.environ.get('APPDATA')
            if not appdata:
                # Fall back to USERPROFILE for test/minimal environments
                userprofile = os.environ.get('USERPROFILE')
                if userprofile:
                    appdata = str(Path(userprofile) / 'AppData' / 'Roaming')
            if appdata:
                self._locations.append(Path(appdata) / 'epochly' / 'epochly.toml')
        else:
            # Unix-like: ~/.config/epochly/epochly.toml
            config_home = os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))
            self._locations.append(Path(config_home) / 'epochly' / 'epochly.toml')
            # Also check ~/.epochly/epochly.toml for compatibility
            self._locations.append(Path.home() / '.epochly' / 'epochly.toml')
        
        # 4. System config (lowest priority)
        if sys.platform == 'win32':
            # Windows: C:\ProgramData\epochly\epochly.toml
            programdata = os.environ.get('PROGRAMDATA', 'C:\\ProgramData')
            self._locations.append(Path(programdata) / 'epochly' / 'epochly.toml')
        else:
            # Unix-like: /etc/epochly/epochly.toml
            self._locations.append(Path('/etc/epochly/epochly.toml'))
        
        # Override system config path if specified
        system_config = os.environ.get('EPOCHLY_SYSTEM_CONFIG')
        if system_config:
            self._locations.append(Path(system_config))
    
    def get_config_locations(self) -> List[Path]:
        """Get all configuration locations in search order."""
        resolved = []
        for loc in self._locations:
            if callable(loc):
                resolved.append(loc())
            else:
                resolved.append(loc)
        return resolved
    
    def find_config_file(self) -> Optional[Path]:
        """Find the first existing configuration file."""
        for location in self._locations:
            try:
                # Resolve callable locations
                if callable(location):
                    location = location()
                
                if location.exists() and location.is_file():
                    logger.debug(f"Found configuration file at: {location}")
                    return location
            except (OSError, PermissionError):
                # Skip locations we can't access
                continue
        return None
    
    def find_all_config_files(self) -> List[Path]:
        """Find all existing configuration files in priority order for merging.
        
        Returns files in order from lowest to highest priority:
        1. System config (/etc/epochly/epochly.toml)
        2. User config (~/.config/epochly/epochly.toml)
        3. Project config (./epochly.toml)
        
        This allows each higher-priority config to override lower ones.
        """
        # Build list in proper precedence order for merging
        ordered_locations = []
        
        # 1. System configs (lowest priority)
        if sys.platform == 'win32':
            programdata = os.environ.get('PROGRAMDATA', 'C:\\ProgramData')
            system_path = Path(programdata) / 'epochly' / 'epochly.toml'
        else:
            system_path = Path('/etc/epochly/epochly.toml')
        
        # Check for EPOCHLY_SYSTEM_CONFIG override
        system_override = os.environ.get('EPOCHLY_SYSTEM_CONFIG')
        if system_override:
            system_path = Path(system_override)
        
        if system_path.exists() and system_path.is_file():
            ordered_locations.append(system_path)
        
        # 2. User config (medium priority)
        if sys.platform == 'win32':
            appdata = os.environ.get('APPDATA')
            if appdata:
                user_path = Path(appdata) / 'epochly' / 'epochly.toml'
                if user_path.exists() and user_path.is_file():
                    ordered_locations.append(user_path)
        else:
            # Unix-like: ~/.config/epochly/epochly.toml
            config_home = os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))
            user_path = Path(config_home) / 'epochly' / 'epochly.toml'
            if user_path.exists() and user_path.is_file():
                ordered_locations.append(user_path)
            
            # Also check ~/.epochly/epochly.toml for compatibility
            alt_user_path = Path.home() / '.epochly' / 'epochly.toml'
            if alt_user_path.exists() and alt_user_path.is_file():
                ordered_locations.append(alt_user_path)
        
        # 3. Project config (highest priority among files)
        project_path = Path.cwd() / 'epochly.toml'
        if project_path.exists() and project_path.is_file():
            ordered_locations.append(project_path)
        
        # 4. Custom path from environment (if specified, it overrides all)
        custom_path = os.environ.get('EPOCHLY_CONFIG_PATH')
        if custom_path:
            custom = Path(custom_path)
            if custom.exists() and custom.is_file():
                ordered_locations.append(custom)
        
        return ordered_locations


class ConfigValidator:
    """Advanced configuration validation utilities."""
    
    @staticmethod
    def validate_memory_size(value: str) -> bool:
        """Validate memory size format (e.g., 16MB, 2GB)."""
        import re
        pattern = r'^\d+[KMG]B$'
        return bool(re.match(pattern, value))
    
    @staticmethod
    def validate_worker_count(value: Union[int, str]) -> bool:
        """Validate worker count value."""
        if value == 'auto':
            return True
        if isinstance(value, int):
            return 1 <= value <= 256
        return False
    
    @staticmethod
    def validate_percentage(value: str) -> bool:
        """Validate percentage format (e.g., 80%)."""
        import re
        pattern = r'^\d+%$'
        if re.match(pattern, value):
            percent = int(value[:-1])
            return 0 <= percent <= 100
        return False
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate complete configuration.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        schema = ConfigSchema()
        return schema.validate(config)


class TOMLConfigLoader:
    """TOML configuration loader with full feature support."""
    
    def __init__(self):
        """Initialize the TOML config loader."""
        self.resolver = ConfigLocationResolver()
        self.validator = ConfigValidator()
        self.schema = ConfigSchema()
    
    def load(self, path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load TOML configuration from a file.
        
        Args:
            path: Path to TOML file
            
        Returns:
            Parsed configuration dictionary
        """
        path = Path(path)
        if not path.exists():
            logger.debug(f"Configuration file not found: {path}")
            return {}
        
        try:
            with open(path, 'r') as f:
                config = toml.load(f)
                logger.debug(f"Loaded configuration from: {path}")
                return config
        except toml.TomlDecodeError as e:
            logger.error(f"Invalid TOML syntax in {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load configuration from {path}: {e}")
            return {}
    
    def load_all_configs(self) -> Dict[str, Any]:
        """
        Load and merge all configuration files in priority order.
        
        Returns:
            Merged configuration dictionary
        """
        merged_config = {}
        
        # Load profile if specified
        profile_name = os.environ.get('EPOCHLY_PROFILE')
        if profile_name:
            profile = ConfigProfile(profile_name)
            merged_config = self.merge_configs(merged_config, profile.get_config())
        
        # Load all config files in order (system -> user -> project)
        config_files = self.resolver.find_all_config_files()
        for config_file in config_files:
            file_config = self.load(config_file)
            merged_config = self.merge_configs(merged_config, file_config)
        
        # Apply environment variable overrides
        merged_config = self.apply_env_overrides(merged_config)
        
        return merged_config
    
    def merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries.
        
        Args:
            base: Base configuration
            override: Configuration to override with
            
        Returns:
            Merged configuration
        """
        result = deepcopy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursive merge for nested dicts
                result[key] = self.merge_configs(result[key], value)
            else:
                # Override value
                result[key] = deepcopy(value)
        
        return result
    
    def apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.
        
        Args:
            config: Base configuration
            
        Returns:
            Configuration with environment overrides applied
        """
        result = deepcopy(config)
        
        # Ensure epochly section exists
        if 'epochly' not in result:
            result['epochly'] = {}
        
        # List of supported environment variables and their config paths
        env_mappings = {
            'EPOCHLY_MODE': ('epochly', 'mode'),
            'EPOCHLY_ENHANCEMENT_LEVEL': ('epochly', 'enhancement_level'),
            'EPOCHLY_MAX_WORKERS': ('epochly', 'max_workers'),
            'EPOCHLY_TELEMETRY': ('epochly', 'telemetry'),
            'EPOCHLY_DEBUG': ('epochly', 'debug'),
            'EPOCHLY_OFFLINE_MODE': ('epochly', 'offline_mode'),
            # JIT settings
            'EPOCHLY_JIT_BACKEND': ('epochly', 'jit', 'backend'),
            'EPOCHLY_JIT_CACHE_ENABLED': ('epochly', 'jit', 'cache_enabled'),
            'EPOCHLY_JIT_HOT_PATH_THRESHOLD': ('epochly', 'jit', 'hot_path_threshold'),
            # Memory settings
            'EPOCHLY_MEMORY_POOL_TYPE': ('epochly', 'memory', 'pool_type'),
            'EPOCHLY_MEMORY_SHARED_SIZE': ('epochly', 'memory', 'shared_memory_size'),
            'EPOCHLY_MEMORY_NUMA_AWARE': ('epochly', 'memory', 'numa_aware'),
            # GPU settings
            'EPOCHLY_GPU_ENABLED': ('epochly', 'gpu', 'enabled'),
            'EPOCHLY_GPU_MEMORY_LIMIT': ('epochly', 'gpu', 'memory_limit'),
            'EPOCHLY_GPU_WORKLOAD_THRESHOLD': ('epochly', 'gpu', 'workload_threshold'),
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert value to appropriate type
                converted_value = self._convert_env_value(value, config_path)
                
                # Set the value in the config
                self._set_nested_value(result, config_path, converted_value)
        
        return result
    
    def _convert_env_value(self, value: str, config_path: Tuple[str, ...]) -> Any:
        """Convert environment variable string to appropriate type."""
        # Determine expected type from schema
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try to convert to int
        try:
            return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], path: Tuple[str, ...], value: Any):
        """Set a value in nested dictionary using path tuple."""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def validate_and_load(self) -> Tuple[Dict[str, Any], bool, List[str]]:
        """
        Load and validate all configurations.
        
        Returns:
            Tuple of (config, is_valid, errors)
        """
        config = self.load_all_configs()
        is_valid, errors = self.validator.validate_config(config)
        return config, is_valid, errors