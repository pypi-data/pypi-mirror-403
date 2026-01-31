"""
Epochly configuration management system.

Provides ConfigManager for managing configuration and ConfigWizard for interactive setup.
Integrated with TOML configuration support for comprehensive configuration management.

Author: Epochly Development Team
"""

import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

# Cache CPU count at module load to prevent race conditions in VMs
# where CPU count can change dynamically
_CACHED_CPU_COUNT = os.cpu_count() or 1

# Import TOML configuration support
try:
    from epochly.config_toml.toml_config import TOMLConfigLoader, ConfigValidator
    TOML_SUPPORT = True
except ImportError:
    TOML_SUPPORT = False
    logger.warning("TOML configuration support not available")


class ConfigManager:
    """Manages Epochly configuration across different scopes."""
    
    # Valid configuration keys and their types/validators
    CONFIG_SCHEMA = {
        'mode': {
            'type': str,
            'values': ['off', 'monitor', 'conservative', 'balanced', 'aggressive'],
            'default': 'balanced',
            'description': 'Epochly execution mode'
        },
        'enhancement_level': {
            'type': int,
            'min': 0,
            'max': 4,
            'default': 1,
            'description': 'Epochly enhancement level (0=monitor, 1=threading, 2=JIT, 3=full, 4=GPU)'
        },
        'max_workers': {
            'type': int,
            'min': 1,
            'max': 256,
            'default': 8,
            'description': 'Maximum number of worker threads'
        },
        'telemetry': {
            'type': bool,
            'default': True,
            'description': 'Enable telemetry collection'
        },
        'jit_enabled': {
            'type': bool,
            'default': True,
            'description': 'Enable JIT compilation'
        },
        'cache_size': {
            'type': int,
            'min': 0,
            'max': 10240,
            'default': 512,
            'description': 'Cache size in MB'
        },
        'log_level': {
            'type': str,
            'values': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            'default': 'INFO',
            'description': 'Logging level'
        },
        'auto_optimize': {
            'type': bool,
            'default': True,
            'description': 'Enable automatic optimization'
        },
        'memory_limit': {
            'type': int,
            'min': 100,
            'max': 102400,
            'default': 4096,
            'description': 'Memory limit in MB'
        },
        'profile_enabled': {
            'type': bool,
            'default': False,
            'description': 'Enable profiling'
        },
        'gpu_enabled': {
            'type': bool,
            'default': True,
            'description': 'Enable GPU acceleration if available'
        }
    }
    
    def __init__(self):
        """Initialize the configuration manager."""
        self.config_paths = self._get_config_paths()
        self._ensure_config_dirs()
        
        # Initialize TOML support if available
        self.toml_loader = None
        self.toml_config = {}
        if TOML_SUPPORT:
            self.toml_loader = TOMLConfigLoader()
            self._load_toml_config()
    
    def _get_config_paths(self) -> Dict[str, Path]:
        """Get paths for different configuration scopes."""
        paths = {}
        
        # Check if EPOCHLY_CONFIG_DIR is set for testing/isolation
        config_dir_override = os.environ.get('EPOCHLY_CONFIG_DIR')
        if config_dir_override:
            # Use the override directory for all scopes
            base_dir = Path(config_dir_override)
            paths['system'] = base_dir / 'system_config.yaml'
            paths['global'] = base_dir / 'config.yaml'
            paths['local'] = base_dir / 'local_config.yaml'
        else:
            # System-wide config
            if sys.platform == 'win32':
                paths['system'] = Path(os.environ.get('PROGRAMDATA', 'C:/ProgramData')) / 'Epochly' / 'config.yaml'
            else:
                paths['system'] = Path('/etc/epochly/config.yaml')
            
            # Global user config
            paths['global'] = Path.home() / '.epochly' / 'config.yaml'
            
            # Local project config
            paths['local'] = Path.cwd() / '.epochly' / 'config.yaml'
        
        return paths
    
    def _ensure_config_dirs(self):
        """Ensure configuration directories exist."""
        for scope in ['global', 'local']:
            config_dir = self.config_paths[scope].parent
            if not config_dir.exists():
                try:
                    config_dir.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    logger.warning(f"Cannot create config directory: {config_dir}")
    
    def ensure_config_dir(self) -> bool:
        """Public method to ensure config directories exist."""
        self._ensure_config_dirs()
        return True
    
    def _load_config_file(self, path: Path) -> Dict[str, Any]:
        """Load configuration from a YAML file."""
        if not path.exists():
            return {}
        
        try:
            with open(path, 'r') as f:
                config = yaml.safe_load(f) or {}
                return config
        except Exception as e:
            logger.error(f"Error loading config from {path}: {e}")
            return {}
    
    def _save_config_file(self, path: Path, config: Dict[str, Any]):
        """Save configuration to a YAML file."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                yaml.safe_dump(config, f, default_flow_style=False, sort_keys=True)
        except Exception as e:
            logger.error(f"Error saving config to {path}: {e}")
            raise
    
    def _load_toml_config(self):
        """Load TOML configuration if available."""
        if self.toml_loader:
            try:
                # Ensure TOML loader uses current working directory
                # This is important for tests and when running from different directories
                self.toml_config = self.toml_loader.load_all_configs()
                if self.toml_config:
                    logger.debug(f"Loaded TOML configuration: {list(self.toml_config.keys())}")
            except Exception as e:
                logger.warning(f"Failed to load TOML configuration: {e}")
                self.toml_config = {}
    
    def _apply_resource_caps(self, key: str, value: Any) -> Any:
        """Apply resource-based caps to configuration values.

        Prevents over-subscription of system resources by capping
        thread/worker counts to available CPU cores.

        Args:
            key: Configuration key name
            value: Configuration value to potentially cap

        Returns:
            Capped value if applicable, original value otherwise
        """
        # Define which keys need CPU-based capping
        CPU_CAPPED_KEYS = {'max_workers', 'max_cores', 'thread_pool_size'}

        if key in CPU_CAPPED_KEYS and isinstance(value, int):
            # Use cached CPU count to prevent race conditions in VMs
            capped_value = min(value, _CACHED_CPU_COUNT)
            if capped_value != value:
                logger.debug(
                    f"Capping {key} from {value} to {capped_value} "
                    f"(available CPUs: {_CACHED_CPU_COUNT})"
                )
            return capped_value

        return value

    def get_all_config(self, scope: str = 'effective') -> Dict[str, Any]:
        """Get all configuration values for a specific scope.

        Precedence order (lowest to highest):
        1. Defaults
        2. TOML configuration (includes profiles, system, user, project configs)
        3. YAML configuration files (legacy support)
        4. Environment variables
        """
        if scope == 'effective':
            # Merge all scopes with proper precedence
            config = {}
            
            # 1. Start with defaults
            for key, schema in self.CONFIG_SCHEMA.items():
                config[key] = schema['default']
            
            # 2. Apply TOML configuration (this includes profiles and all TOML files)
            # The TOML loader handles its own precedence internally
            if self.toml_loader:
                # Reload TOML config to pick up any changes in CWD
                self._load_toml_config()
                
                if self.toml_config and 'epochly' in self.toml_config:
                    epochly_section = self.toml_config['epochly']
                    
                    # Handle direct mapping of known fields
                    for key, value in epochly_section.items():
                        # Handle nested configurations like jit and memory
                        if key == 'jit' and isinstance(value, dict):
                            # Map jit.cache_enabled to jit_enabled if present
                            if 'cache_enabled' in value:
                                config['jit_enabled'] = value['cache_enabled']
                        elif key == 'memory' and isinstance(value, dict):
                            # Map memory.limit to memory_limit if present
                            if 'limit' in value:
                                try:
                                    # Convert memory sizes like "8192MB" to integer
                                    mem_str = str(value['limit'])
                                    if mem_str.endswith('MB'):
                                        config['memory_limit'] = int(mem_str[:-2])
                                    elif mem_str.endswith('GB'):
                                        config['memory_limit'] = int(mem_str[:-2]) * 1024
                                    else:
                                        config['memory_limit'] = int(mem_str)
                                except (ValueError, TypeError):
                                    pass
                        elif key == 'debug':
                            # Map debug field to log_level if appropriate
                            if value:
                                # If debug is True and log_level isn't already DEBUG
                                if config.get('log_level') != 'DEBUG':
                                    config['log_level'] = 'DEBUG'
                        elif key == 'gpu' and isinstance(value, dict):
                            # Map gpu.enabled to gpu_enabled
                            if 'enabled' in value:
                                config['gpu_enabled'] = value['enabled']
                        elif key == 'monitoring' and isinstance(value, dict):
                            # Map monitoring.enabled to profile_enabled
                            if 'enabled' in value:
                                config['profile_enabled'] = value['enabled']
                        elif key in self.CONFIG_SCHEMA:
                            # Direct mapping for known fields
                            # Special handling for max_workers which can be 'auto' or int
                            if key == 'max_workers':
                                if value == 'auto':
                                    # Map 'auto' to actual CPU count for display
                                    # This preserves 'auto' in config but shows actual value
                                    config[key] = os.cpu_count() or 8
                                elif isinstance(value, str):
                                    # Try to convert string to int
                                    try:
                                        config[key] = int(value)
                                    except ValueError:
                                        # Keep default if conversion fails
                                        pass
                                else:
                                    # Validate the value before applying
                                    is_valid, _ = self.validate_config(key, value)
                                    if is_valid:
                                        config[key] = self._apply_resource_caps(key, value)
                            else:
                                # Validate the value before applying
                                is_valid, _ = self.validate_config(key, value)
                                if is_valid:
                                    config[key] = self._apply_resource_caps(key, value)
            
            # 3. Apply YAML configs (for backward compatibility)
            # Only apply if they exist and don't override TOML config unnecessarily
            # System YAML config
            system_config = self._load_config_file(self.config_paths['system'])
            for key, value in system_config.items():
                if key in self.CONFIG_SCHEMA:
                    is_valid, _ = self.validate_config(key, value)
                    if is_valid:
                        config[key] = self._apply_resource_caps(key, value)

            # Global/User YAML config
            global_config = self._load_config_file(self.config_paths['global'])
            for key, value in global_config.items():
                if key in self.CONFIG_SCHEMA:
                    is_valid, _ = self.validate_config(key, value)
                    if is_valid:
                        config[key] = self._apply_resource_caps(key, value)

            # Local/Project YAML config
            local_config = self._load_config_file(self.config_paths['local'])
            for key, value in local_config.items():
                if key in self.CONFIG_SCHEMA:
                    is_valid, _ = self.validate_config(key, value)
                    if is_valid:
                        config[key] = self._apply_resource_caps(key, value)
            
            # 4. Apply environment variables (highest precedence)
            for key in self.CONFIG_SCHEMA:
                env_var = f"EPOCHLY_{key.upper()}"
                if env_var in os.environ:
                    value = os.environ[env_var]
                    # Convert to appropriate type
                    schema = self.CONFIG_SCHEMA[key]
                    if schema['type'] == bool:
                        config[key] = value.lower() in ('true', '1', 'yes', 'on')
                    elif schema['type'] == int:
                        try:
                            int_value = int(value)
                            config[key] = self._apply_resource_caps(key, int_value)
                        except ValueError:
                            pass
                    else:
                        config[key] = value
            
            return config
        
        elif scope in ('system', 'global', 'local'):
            return self._load_config_file(self.config_paths[scope])
        
        else:
            return {}
    
    def get_config(self, key: str, scope: str = 'effective') -> Optional[Any]:
        """Get a specific configuration value."""
        if key not in self.CONFIG_SCHEMA:
            return None
        
        config = self.get_all_config(scope)
        return config.get(key)
    
    def set_config(self, key: str, value: Any, scope: str = 'user'):
        """Set a configuration value."""
        if key not in self.CONFIG_SCHEMA:
            raise ValueError(f"Invalid configuration key: {key}")

        # Validate value
        is_valid, error = self._validate_value(key, value)
        if not is_valid:
            raise ValueError(error)

        # PYTHON 3.11 FIX: Explicit type conversion after validation
        # _validate_value() converts locally but doesn't return the converted value
        # Python 3.11 has stricter YAML serialization that preserves string types
        schema = self.CONFIG_SCHEMA[key]
        if schema['type'] == int:
            value = int(value)
        elif schema['type'] == bool:
            if isinstance(value, str):
                value = value.lower() in ('true', '1', 'yes', 'on')
            else:
                value = bool(value)
        elif schema['type'] == str:
            value = str(value)

        # ARCHITECTURE: Store uncapped value to preserve user intent and portability
        # Resource capping is applied at READ time in get_config() for scope='effective'
        # This allows configs to be portable across different hardware
        CPU_CAPPED_KEYS = {'max_workers', 'max_cores', 'thread_pool_size'}
        if key in CPU_CAPPED_KEYS and isinstance(value, int) and value > _CACHED_CPU_COUNT:
            logger.debug(
                f"Note: {key}={value} will be capped to {_CACHED_CPU_COUNT} at runtime "
                f"(available CPUs: {_CACHED_CPU_COUNT})"
            )

        # Map 'user' scope to 'global'
        if scope == 'user':
            scope = 'global'

        if scope not in ('global', 'local', 'system'):
            raise ValueError(f"Invalid scope: {scope}")

        # Load existing config
        config_path = self.config_paths[scope]
        config = self._load_config_file(config_path)

        # Store UNCAPPED value to preserve user intent
        config[key] = value

        # Save config
        self._save_config_file(config_path, config)

        return True
    
    def _validate_value(self, key: str, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate a configuration value."""
        if key not in self.CONFIG_SCHEMA:
            return False, f"Unknown configuration key: {key}"
        
        schema = self.CONFIG_SCHEMA[key]
        
        # Type check
        if not isinstance(value, schema['type']):
            # Try to convert
            try:
                if schema['type'] == bool:
                    if isinstance(value, str):
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        value = bool(value)
                elif schema['type'] == int:
                    value = int(value)
                elif schema['type'] == str:
                    value = str(value)
            except (ValueError, TypeError):
                return False, f"Invalid type for {key}: expected {schema['type'].__name__}"
        
        # Value range/options check
        if 'values' in schema:
            if value not in schema['values']:
                return False, f"Invalid value for {key}: must be one of {schema['values']}"
        
        if schema['type'] == int:
            if 'min' in schema and value < schema['min']:
                return False, f"Value for {key} too small: minimum is {schema['min']}"
            if 'max' in schema and value > schema['max']:
                return False, f"Value for {key} too large: maximum is {schema['max']}"
        
        return True, None
    
    def validate_config(self, key: str, value: Any) -> Tuple[bool, Optional[str]]:
        """Public validation method."""
        return self._validate_value(key, value)
    
    def reset_config(self, scope: str = 'global') -> bool:
        """Reset configuration to defaults."""
        if scope == 'global':
            config_path = self.config_paths['global']
        elif scope == 'local':
            config_path = self.config_paths['local']
        else:
            raise ValueError(f"Cannot reset {scope} configuration")
        
        # Remove the config file
        if config_path.exists():
            try:
                config_path.unlink()
                return True
            except Exception as e:
                logger.error(f"Error resetting config: {e}")
                return False
        
        return True
    
    def export_config(self, format: str = 'yaml') -> str:
        """Export configuration to string."""
        config = self.get_all_config('effective')
        
        if format == 'yaml':
            import io
            stream = io.StringIO()
            yaml.safe_dump(config, stream, default_flow_style=False, sort_keys=True)
            return stream.getvalue()
        
        elif format == 'json':
            return json.dumps(config, indent=2, sort_keys=True)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def import_config(self, data: str, format: str = 'yaml', scope: str = 'global'):
        """Import configuration from string or file."""
        try:
            # Check if data is a file path
            if os.path.exists(data):
                path = Path(data)
                with open(path, 'r') as f:
                    file_content = f.read()
                
                # Determine format from file extension
                if path.suffix == '.toml':
                    if TOML_SUPPORT:
                        import toml
                        config = toml.loads(file_content)
                        # Extract epochly section if it exists
                        if 'epochly' in config:
                            config = config['epochly']
                    else:
                        raise ValueError("TOML support not available. Install 'toml' package.")
                elif path.suffix in ('.yaml', '.yml'):
                    config = yaml.safe_load(file_content)
                elif path.suffix == '.json':
                    config = json.loads(file_content)
                else:
                    raise ValueError(f"Unsupported file format: {path.suffix}")
            else:
                # Parse as string
                if format == 'yaml':
                    config = yaml.safe_load(data)
                elif format == 'json':
                    config = json.loads(data)
                elif format == 'toml':
                    if TOML_SUPPORT:
                        import toml
                        config = toml.loads(data)
                        if 'epochly' in config:
                            config = config['epochly']
                    else:
                        raise ValueError("TOML support not available.")
                else:
                    raise ValueError(f"Unsupported format: {format}")
            
            # Validate all keys and values
            for key, value in config.items():
                is_valid, error = self._validate_value(key, value)
                if not is_valid:
                    raise ValueError(f"Invalid config: {error}")
            
            # Save to appropriate scope
            if scope == 'global':
                config_path = self.config_paths['global']
            elif scope == 'local':
                config_path = self.config_paths['local']
            else:
                raise ValueError(f"Invalid scope: {scope}")
            
            self._save_config_file(config_path, config)
            return True
            
        except Exception as e:
            logger.error(f"Error importing config: {e}")
            raise
    
    def apply_config(self, config: Dict[str, Any], scope: str = 'global'):
        """Apply a configuration dictionary."""
        for key, value in config.items():
            self.set_config(key, value, scope)
        return True


class ConfigWizard:
    """Interactive configuration wizard for Epochly."""
    
    def __init__(self):
        """Initialize the configuration wizard."""
        self.config_manager = ConfigManager()
    
    def run(self) -> Dict[str, Any]:
        """Run the interactive configuration wizard."""
        print("\n" + "="*60)
        print("       Epochly Configuration Wizard")
        print("="*60)
        print("\nThis wizard will help you configure Epochly for optimal performance.")
        print("Press Enter to accept the default value shown in brackets.\n")
        
        config = {}
        
        # Mode selection
        print("1. Execution Mode")
        print("-" * 40)
        print("Epochly can run in different modes:")
        print("  - off: Disable Epochly completely")
        print("  - monitor: Monitor only, no optimization")
        print("  - conservative: Safe optimizations only")
        print("  - balanced: Balanced performance/safety (recommended)")
        print("  - aggressive: Maximum performance")
        
        mode = self._prompt_choice(
            "Select mode",
            ['off', 'monitor', 'conservative', 'balanced', 'aggressive'],
            default='balanced'
        )
        config['mode'] = mode
        
        # Worker configuration
        print("\n2. Parallelization")
        print("-" * 40)
        cpu_count = os.cpu_count() or 4
        default_workers = min(cpu_count * 2, 16)
        
        max_workers = self._prompt_int(
            f"Maximum worker threads (1-256)",
            min_val=1,
            max_val=256,
            default=default_workers
        )
        config['max_workers'] = max_workers
        
        # Memory configuration
        print("\n3. Memory Management")
        print("-" * 40)
        
        memory_limit = self._prompt_int(
            "Memory limit in MB (100-102400)",
            min_val=100,
            max_val=102400,
            default=4096
        )
        config['memory_limit'] = memory_limit
        
        cache_size = self._prompt_int(
            "Cache size in MB (0-10240)",
            min_val=0,
            max_val=10240,
            default=512
        )
        config['cache_size'] = cache_size
        
        # Features
        print("\n4. Features")
        print("-" * 40)
        
        config['jit_enabled'] = self._prompt_bool(
            "Enable JIT compilation",
            default=True
        )
        
        config['auto_optimize'] = self._prompt_bool(
            "Enable automatic optimization",
            default=True
        )
        
        config['gpu_enabled'] = self._prompt_bool(
            "Enable GPU acceleration (if available)",
            default=True
        )
        
        # Monitoring
        print("\n5. Monitoring & Debugging")
        print("-" * 40)
        
        config['telemetry'] = self._prompt_bool(
            "Enable telemetry collection",
            default=True
        )
        
        config['profile_enabled'] = self._prompt_bool(
            "Enable profiling",
            default=False
        )
        
        log_level = self._prompt_choice(
            "Log level",
            ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default='INFO'
        )
        config['log_level'] = log_level
        
        # Summary
        print("\n" + "="*60)
        print("Configuration Summary:")
        print("-" * 40)
        for key, value in config.items():
            print(f"  {key:20s}: {value}")
        print("="*60)
        
        # Confirm
        if self._prompt_bool("\nApply this configuration", default=True):
            return config
        else:
            print("Configuration cancelled.")
            return {}
    
    def _prompt_choice(self, prompt: str, choices: List[str], default: str) -> str:
        """Prompt for a choice from a list."""
        choices_str = ', '.join(choices)
        while True:
            value = input(f"{prompt} [{choices_str}] (default: {default}): ").strip()
            if not value:
                return default
            if value in choices:
                return value
            print(f"Invalid choice. Please select from: {choices_str}")
    
    def _prompt_int(self, prompt: str, min_val: int, max_val: int, default: int) -> int:
        """Prompt for an integer value."""
        while True:
            value = input(f"{prompt} (default: {default}): ").strip()
            if not value:
                return default
            try:
                int_val = int(value)
                if min_val <= int_val <= max_val:
                    return int_val
                print(f"Value must be between {min_val} and {max_val}")
            except ValueError:
                print("Please enter a valid integer")
    
    def _prompt_bool(self, prompt: str, default: bool) -> bool:
        """Prompt for a boolean value."""
        default_str = "yes" if default else "no"
        while True:
            value = input(f"{prompt} [yes/no] (default: {default_str}): ").strip().lower()
            if not value:
                return default
            if value in ('yes', 'y', 'true', '1'):
                return True
            if value in ('no', 'n', 'false', '0'):
                return False
            print("Please enter yes or no")