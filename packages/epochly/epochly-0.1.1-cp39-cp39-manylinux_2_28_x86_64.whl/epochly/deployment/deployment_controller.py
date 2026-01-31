"""
Epochly Deployment Controller

Manages controlled deployment and activation of Epochly across different environments.
Provides mechanisms for selective activation, deployment strategies, and runtime control.

Author: Epochly Development Team
"""

import os
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict

from ..utils.logger import get_logger
from ..utils.logging_bootstrap import get_logging_bootstrap, initialize_centralized_logging
from .config import get_config


class DeploymentMode(Enum):
    """Deployment modes for controlled rollout."""
    MONITOR = "monitor"           # Monitor-only mode, no optimizations
    CONSERVATIVE = "conservative" # Safe optimizations only
    BALANCED = "balanced"        # Moderate optimizations
    AGGRESSIVE = "aggressive"    # All optimizations enabled


class ActivationStrategy(Enum):
    """Activation strategies for deployment."""
    GLOBAL = "global"            # Activate for all processes
    ALLOWLIST = "allowlist"      # Only activate for allowlisted items
    DENYLIST = "denylist"        # Activate except for denylisted items
    PERCENTAGE = "percentage"    # Activate for percentage of processes


@dataclass
class DeploymentConfig:
    """Configuration for deployment settings."""
    enabled: bool = True
    mode: DeploymentMode = DeploymentMode.CONSERVATIVE
    strategy: ActivationStrategy = ActivationStrategy.GLOBAL
    percentage: float = 100.0
    allowlist: Optional[List[str]] = None
    denylist: Optional[List[str]] = None
    emergency_disable: bool = False
    
    def __post_init__(self):
        if self.allowlist is None:
            self.allowlist = []
        if self.denylist is None:
            self.denylist = []


class DeploymentController:
    """
    Controls Epochly deployment and activation across different environments.
    
    Provides mechanisms for:
    - Selective activation based on various strategies
    - Deployment mode control (monitor, conservative, balanced, aggressive)
    - Emergency controls for production safety
    - Configuration management and persistence
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize deployment controller.
        
        Args:
            config_path: Optional path to configuration file
        """
        # Initialize centralized logging first
        self._logging_bootstrap = get_logging_bootstrap()
        self._initialize_centralized_logging()
        
        self.logger = get_logger(__name__)
        self._lock = threading.RLock()
        self._global_config = get_config()
        self._config_path = config_path or self._get_default_config_path()
        self._config = self._load_config()
        self._process_id = os.getpid()
        self._shutdown_event = threading.Event()
        self._shutdown_complete = threading.Event()
        self._background_threads: List[threading.Thread] = []
        self._accepting_new_background = True
        
    def _initialize_centralized_logging(self) -> None:
        """Initialize centralized logging system for Epochly deployment."""
        try:
            # Initialize centralized logging with concurrent support
            success = initialize_centralized_logging(use_concurrent=True)
            if success:
                # Get centralized logger for deployment component
                self._centralized_logger = self._logging_bootstrap.get_child_logger(
                    __name__,
                    component='deployment'
                )
                self._centralized_logger.info("Centralized logging initialized for deployment controller")
            else:
                # Fallback to standard logging if centralized fails
                import logging
                logging.basicConfig(level=logging.INFO)
                logger = logging.getLogger(__name__)
                logger.warning("Failed to initialize centralized logging, using fallback")
        except Exception as e:
            # Ensure we have some form of logging even if centralized fails
            import logging
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(__name__)
            logger.error(f"Error initializing centralized logging: {e}")
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        # Try multiple locations in order of preference
        locations = [
            self._global_config.config_path,
            os.path.join(os.getcwd(), '.epochly.conf'),
            os.path.join(os.path.expanduser('~'), '.epochly', 'config.json'),
            '/etc/epochly/config.json'
        ]
        
        for location in locations:
            if location and os.path.exists(location):
                return location
                
        # Return user config path as default
        return os.path.join(os.path.expanduser('~'), '.epochly', 'config.json')
    
    def _load_config(self) -> DeploymentConfig:
        """Load deployment configuration from file."""
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r') as f:
                    data = json.load(f)
                    
                # Convert string enums back to enum objects
                if 'mode' in data:
                    data['mode'] = DeploymentMode(data['mode'])
                if 'strategy' in data:
                    data['strategy'] = ActivationStrategy(data['strategy'])
                    
                return DeploymentConfig(**data)
            else:
                self.logger.debug(f"Config file not found: {self._config_path}")
                return DeploymentConfig()
                
        except Exception as e:
            self.logger.warning(f"Failed to load config from {self._config_path}: {e}")
            return DeploymentConfig()
    
    def _save_config(self) -> None:
        """Save current configuration to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            
            # Convert config to dict with enum values as strings
            config_dict = asdict(self._config)
            config_dict['mode'] = self._config.mode.value
            config_dict['strategy'] = self._config.strategy.value
            
            with open(self._config_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save config to {self._config_path}: {e}")
    
    def should_activate(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if Epochly should be activated for the current context.
        
        Args:
            context: Optional context information (script path, module name, etc.)
            
        Returns:
            True if Epochly should be activated, False otherwise
        """
        with self._lock:
            # Check emergency disable first
            if self._config.emergency_disable or self.check_emergency_killswitch():
                return False
                
            # Check if globally disabled
            if not self._config.enabled:
                return False
                
            # Check environment variable override
            if self._global_config.enabled is not None:
                return self._global_config.enabled
            
            # Apply activation strategy
            return self._apply_activation_strategy(context)
    
    def _apply_activation_strategy(self, context: Optional[Dict[str, Any]]) -> bool:
        """Apply the configured activation strategy."""
        if self._config.strategy == ActivationStrategy.GLOBAL:
            return True
            
        elif self._config.strategy == ActivationStrategy.PERCENTAGE:
            # Use process ID for deterministic percentage-based activation
            return (self._process_id % 100) < self._config.percentage
            
        elif self._config.strategy == ActivationStrategy.ALLOWLIST:
            if not context:
                return False
            return self._check_allowlist(context)
            
        elif self._config.strategy == ActivationStrategy.DENYLIST:
            if not context:
                return True
            return not self._check_denylist(context)
            
        return False
    
    def _check_allowlist(self, context: Dict[str, Any]) -> bool:
        """Check if context matches allowlist patterns."""
        script_path = context.get('script_path', '')
        module_name = context.get('module_name', '')
        
        for pattern in self._config.allowlist or []:
            if self._matches_pattern(pattern, script_path, module_name):
                return True
        return False
    
    def _check_denylist(self, context: Dict[str, Any]) -> bool:
        """Check if context matches denylist patterns."""
        script_path = context.get('script_path', '')
        module_name = context.get('module_name', '')
        
        for pattern in self._config.denylist or []:
            if self._matches_pattern(pattern, script_path, module_name):
                return True
        return False
    
    def _matches_pattern(self, pattern: str, script_path: str, module_name: str) -> bool:
        """Check if pattern matches script path or module name."""
        import fnmatch
        
        # Check exact matches first
        if pattern == script_path or pattern == module_name:
            return True
            
        # Check wildcard patterns
        if fnmatch.fnmatch(script_path, pattern):
            return True
        if fnmatch.fnmatch(module_name, pattern):
            return True
            
        # Check if pattern matches basename
        if fnmatch.fnmatch(os.path.basename(script_path), pattern):
            return True
            
        return False
    
    def get_current_mode(self) -> DeploymentMode:
        """Get current deployment mode."""
        with self._lock:
            return self._config.mode
    
    def set_mode(self, mode: DeploymentMode) -> None:
        """Set deployment mode."""
        with self._lock:
            self._config.mode = mode
            self._save_config()
            self.logger.info(f"Deployment mode set to: {mode.value}")
    
    def get_activation_level(self) -> float:
        """Get current activation level (0.0 to 1.0)."""
        with self._lock:
            if self._config.strategy == ActivationStrategy.PERCENTAGE:
                return self._config.percentage / 100.0
            elif self._config.enabled and not self._config.emergency_disable:
                return 1.0
            else:
                return 0.0
    
    def set_percentage(self, percentage: float) -> None:
        """Set activation percentage for percentage-based strategy."""
        if not 0.0 <= percentage <= 100.0:
            raise ValueError("Percentage must be between 0.0 and 100.0")
            
        with self._lock:
            self._config.percentage = percentage
            self._save_config()
            self.logger.info(f"Activation percentage set to: {percentage}%")
    
    def add_to_allowlist(self, pattern: str) -> None:
        """Add pattern to allowlist."""
        with self._lock:
            allowlist = self._config.allowlist or []
            if pattern not in allowlist:
                allowlist.append(pattern)
                self._config.allowlist = allowlist
                self._save_config()
                self.logger.info(f"Added to allowlist: {pattern}")
    
    def remove_from_allowlist(self, pattern: str) -> None:
        """Remove pattern from allowlist."""
        with self._lock:
            allowlist = self._config.allowlist or []
            if pattern in allowlist:
                allowlist.remove(pattern)
                self._config.allowlist = allowlist
                self._save_config()
                self.logger.info(f"Removed from allowlist: {pattern}")
    
    def add_to_denylist(self, pattern: str) -> None:
        """Add pattern to denylist."""
        with self._lock:
            denylist = self._config.denylist or []
            if pattern not in denylist:
                denylist.append(pattern)
                self._config.denylist = denylist
                self._save_config()
                self.logger.info(f"Added to denylist: {pattern}")
    
    def remove_from_denylist(self, pattern: str) -> None:
        """Remove pattern from denylist."""
        with self._lock:
            denylist = self._config.denylist or []
            if pattern in denylist:
                denylist.remove(pattern)
                self._config.denylist = denylist
                self._save_config()
                self.logger.info(f"Removed from denylist: {pattern}")
    
    def check_emergency_killswitch(self) -> bool:
        """Check for emergency killswitch activation."""
        # Check for killswitch file
        killswitch_paths = [
            '/tmp/epochly.kill',
            os.path.join(os.path.expanduser('~'), '.epochly', 'kill'),
            'epochly.kill'
        ]
        
        for path in killswitch_paths:
            if os.path.exists(path):
                self.logger.warning(f"Emergency killswitch detected: {path}")
                return True
        
        # Check environment variable
        if self._global_config.emergency_disable:
            self.logger.warning("Emergency killswitch detected via environment variable")
            return True
            
        return False
    
    def emergency_disable(self) -> None:
        """Activate emergency disable."""
        with self._lock:
            self._config.emergency_disable = True
            self._save_config()
            
            # Also create killswitch file
            try:
                killswitch_path = os.path.join(os.path.expanduser('~'), '.epochly', 'kill')
                os.makedirs(os.path.dirname(killswitch_path), exist_ok=True)
                Path(killswitch_path).touch()
                self.logger.critical("Emergency disable activated")
            except Exception as e:
                self.logger.error(f"Failed to create killswitch file: {e}")
    
    def clear_emergency_disable(self) -> None:
        """Clear emergency disable state."""
        with self._lock:
            self._config.emergency_disable = False
            self._save_config()
            
            # Remove killswitch files
            killswitch_paths = [
                '/tmp/epochly.kill',
                os.path.join(os.path.expanduser('~'), '.epochly', 'kill'),
                'epochly.kill'
            ]
            
            for path in killswitch_paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                        self.logger.info(f"Removed killswitch file: {path}")
                except Exception as e:
                    self.logger.warning(f"Failed to remove killswitch file {path}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current deployment status."""
        with self._lock:
            return {
                'enabled': self._config.enabled,
                'mode': self._config.mode.value,
                'strategy': self._config.strategy.value,
                'percentage': self._config.percentage,
                'allowlist_count': len(self._config.allowlist or []),
                'denylist_count': len(self._config.denylist or []),
                'emergency_disable': self._config.emergency_disable,
                'killswitch_active': self.check_emergency_killswitch(),
                'config_path': self._config_path
            }
    
    def load_global_config(self) -> Dict[str, Any]:
        """Load global configuration settings."""
        try:
            global_config_path = '/etc/epochly/global.conf'
            if os.path.exists(global_config_path):
                with open(global_config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.debug(f"Failed to load global config: {e}")
        
        return {}
    
    def register_background_thread(self, thread: threading.Thread) -> None:
        """
        Register a background thread for proper shutdown management.
        Must be called after the thread has been started.
        
        Args:
            thread: Thread to register for shutdown coordination
            
        Raises:
            RuntimeError: If called while shutdown is in progress
        """
        with self._lock:
            if not self._accepting_new_background:
                raise RuntimeError("Cannot register new background thread while shutdown in progress")
            self._background_threads.append(thread)
            self.logger.debug(f"Registered background thread: {thread.name}")
    
    def shutdown(self, timeout: float = 5.0) -> None:
        """
        Gracefully shutdown deployment controller and all managed threads.
        
        This method implements production-grade thread safety patterns:
        - Prevents new thread registration during shutdown
        - Avoids self-join deadlocks
        - Provides final unlimited wait for stubborn threads
        - Makes shutdown idempotent
        
        Args:
            timeout: Maximum time to wait for threads to join (seconds)
        """
        # Fast-path - already shut down
        if self._shutdown_complete.is_set():
            return
        
        self.logger.info("Shutting down deployment controller")
        
        # Signal shutdown to all threads
        self._shutdown_event.set()
        
        # Stop accepting new background threads
        with self._lock:
            self._accepting_new_background = False
            threads_to_join = list(self._background_threads)
        
        # Get current thread to avoid self-join deadlock
        current_thread = threading.current_thread()
        
        # First pass: join with timeout
        for thread in threads_to_join:
            if thread is current_thread:
                # Joining yourself would deadlock
                self.logger.debug(f"Skipping self-join for thread: {thread.name}")
                continue
            
            if not thread.is_alive():
                continue
            
            try:
                self.logger.debug(f"Joining thread: {thread.name} (timeout={timeout}s)")
                thread.join(timeout=timeout)
                if thread.is_alive():
                    self.logger.warning(f"Thread {thread.name} did not shutdown within {timeout}s")
                else:
                    self.logger.debug(f"Thread {thread.name} shutdown successfully")
            except Exception as e:
                self.logger.error(f"Error joining thread {thread.name}: {e}")
        
        # Second pass: unlimited wait for stubborn threads
        for thread in threads_to_join:
            if thread is not current_thread and thread.is_alive():
                self.logger.debug(f"Final wait for stubborn thread: {thread.name}")
                try:
                    thread.join()  # Unlimited wait
                    self.logger.debug(f"Stubborn thread {thread.name} finally joined")
                except Exception as e:
                    self.logger.error(f"Error in final join for thread {thread.name}: {e}")
        
        # Clear thread list so repeated shutdown does nothing
        with self._lock:
            self._background_threads.clear()
        
        # Shutdown centralized logging
        try:
            if hasattr(self, '_logging_bootstrap'):
                self._logging_bootstrap.shutdown()
        except Exception as e:
            self.logger.warning(f"Error shutting down centralized logging: {e}")
        
        # Mark shutdown as complete
        self._shutdown_complete.set()
        self.logger.info("Deployment controller shutdown complete")
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self._shutdown_event.is_set()
    
    def is_shutdown_complete(self) -> bool:
        """Check if shutdown has completed."""
        return self._shutdown_complete.is_set()
    
    def wait_for_shutdown_complete(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for shutdown to complete.
        
        Args:
            timeout: Maximum time to wait (None for unlimited)
            
        Returns:
            True if shutdown completed, False if timeout occurred
        """
        return self._shutdown_complete.wait(timeout)