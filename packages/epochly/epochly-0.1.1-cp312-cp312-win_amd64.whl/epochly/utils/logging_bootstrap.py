"""
Epochly Centralized Logging Bootstrap

Provides centralized logging initialization and management for the Epochly framework.
Integrates with DeploymentController to establish consistent logging across all components.

IMPORTANT: This module ONLY configures the isolated 'epochly' logger hierarchy.
It NEVER touches the root logger or user's logging configuration.

Author: Epochly Development Team
"""

import logging
import os
import threading
from typing import Dict, Optional, Any
from pathlib import Path

from .logger import setup_logging, get_logger, _get_epochly_root_logger
from .concurrent_logging import configure_concurrent_logging, add_file_handler, get_listener_handlers


class LoggingBootstrap:
    """
    Centralized logging bootstrap manager for Epochly.
    
    Provides centralized initialization, child logger management,
    and consistent formatting across all Epochly components.
    """
    
    def __init__(self):
        """Initialize the logging bootstrap manager."""
        self._initialized = False
        self._lock = threading.RLock()
        self._child_loggers: Dict[str, logging.Logger] = {}
        self._config = None  # Lazy load to avoid circular import
        self._root_logger: Optional[logging.Logger] = None
        self._concurrent_enabled = False
    
    def _get_config(self):
        """Lazy load config to avoid circular import."""
        if self._config is None:
            from .config import get_config
            self._config = get_config()
        return self._config
        
    def initialize(self, 
                  use_concurrent: bool = True,
                  force_reinit: bool = False) -> bool:
        """
        Initialize centralized logging system.
        
        Args:
            use_concurrent: Whether to use concurrent logging
            force_reinit: Force reinitialization even if already initialized
            
        Returns:
            True if initialization successful, False otherwise
        """
        with self._lock:
            if self._initialized and not force_reinit:
                return True
                
            try:
                # Get logging configuration
                logging_config = self._get_config().get_section('logging')
                
                # Initialize appropriate logging system
                if use_concurrent:
                    self._initialize_concurrent_logging(logging_config)
                else:
                    self._initialize_standard_logging(logging_config)
                
                # Set up structured logging format
                self._setup_structured_format()
                
                # Create root Epochly logger
                self._root_logger = get_logger('epochly')
                self._root_logger.info("Epochly centralized logging initialized")
                
                self._initialized = True
                self._concurrent_enabled = use_concurrent
                
                return True
                
            except Exception as e:
                # Fallback to basic Epochly logging if initialization fails
                # CRITICAL: Never use logging.basicConfig() as it touches root logger
                epochly_logger = logging.getLogger('epochly')
                epochly_logger.propagate = False  # Isolate from root
                if not epochly_logger.handlers:
                    handler = logging.StreamHandler()
                    handler.setFormatter(logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    ))
                    epochly_logger.addHandler(handler)
                    epochly_logger.setLevel(logging.INFO)

                logger = logging.getLogger('epochly.logging_bootstrap')
                logger.error(f"Failed to initialize centralized logging: {e}")
                return False
    
    def _initialize_concurrent_logging(self, config: Dict[str, Any]) -> None:
        """Initialize concurrent logging system."""
        level = getattr(logging, config.get('level', 'INFO').upper())
        
        # Configure concurrent logging
        configure_concurrent_logging(level)
        
        # Add file handler if specified
        log_file = config.get('file')
        if log_file:
            try:
                # Ensure log directory exists
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                add_file_handler(
                    log_file=str(log_path),
                    max_bytes=config.get('max_size', 10 * 1024 * 1024),
                    backup_count=config.get('backup_count', 5),
                    level=level
                )
            except Exception as e:
                # Log error but continue with console logging
                logger = logging.getLogger('epochly.logging_bootstrap')
                logger.warning(f"Failed to setup file logging: {e}")
    
    def _initialize_standard_logging(self, config: Dict[str, Any]) -> None:
        """Initialize standard logging system."""
        setup_logging(
            level=config.get('level', 'INFO'),
            log_file=config.get('file'),
            max_bytes=config.get('max_size', 10 * 1024 * 1024),
            backup_count=config.get('backup_count', 5)
        )
    
    def _setup_structured_format(self) -> None:
        """Setup structured logging format for operational monitoring.

        NOTE: Only configures the isolated 'epochly' logger hierarchy.
        Never touches the root logger or user's logging configuration.

        In concurrent mode, formats the listener's output handlers (not QueueHandler).
        """
        # Define consistent format for all Epochly loggers
        structured_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[%(process)d:%(thread)d] - %(filename)s:%(lineno)d - %(message)s"
        )
        formatter = logging.Formatter(structured_format)

        # In concurrent mode, format the listener's handlers (not the QueueHandler)
        if self._concurrent_enabled:
            listener_handlers = get_listener_handlers()
            for handler in listener_handlers:
                handler.setFormatter(formatter)
        else:
            # Apply format to Epochly logger handlers directly
            epochly_logger = logging.getLogger('epochly')
            for handler in epochly_logger.handlers:
                if not isinstance(handler, logging.NullHandler):
                    handler.setFormatter(formatter)
    
    def get_child_logger(self, name: str, 
                        component: Optional[str] = None,
                        extra_context: Optional[Dict[str, Any]] = None) -> logging.Logger:
        """
        Get or create a child logger with consistent hierarchy.
        
        Args:
            name: Logger name (typically __name__)
            component: Component name for categorization
            extra_context: Additional context for structured logging
            
        Returns:
            Configured child logger instance
        """
        with self._lock:
            # Ensure initialization
            if not self._initialized:
                self.initialize()
            
            # Normalize logger name to Epochly hierarchy
            if not name.startswith('epochly'):
                if name.startswith('epochly'):
                    # Convert epochly.module to epochly.module
                    normalized_name = name.replace('epochly', 'epochly')
                elif '.' in name:
                    # Keep existing hierarchy but ensure epochly prefix
                    normalized_name = f"epochly.{name}"
                else:
                    # Simple name, add epochly prefix
                    normalized_name = f"epochly.{name}"
            else:
                normalized_name = name
            
            # Check cache first
            if normalized_name in self._child_loggers:
                return self._child_loggers[normalized_name]
            
            # Create new child logger
            child_logger = logging.getLogger(normalized_name)
            
            # Add component context if provided
            if component:
                # Add component-specific context
                child_logger = self._add_component_context(child_logger, component, extra_context)
            
            # Cache the logger
            self._child_loggers[normalized_name] = child_logger
            
            return child_logger
    
    def _add_component_context(self, logger: logging.Logger, 
                              component: str,
                              extra_context: Optional[Dict[str, Any]]) -> logging.Logger:
        """Add component-specific context to logger."""
        # Return the logger as-is
        # Future enhancement: could wrap with LoggerAdapter for additional context
        return logger
    
    def get_performance_logger(self, name: str) -> logging.Logger:
        """
        Get a performance-focused logger for metrics and monitoring.
        
        Args:
            name: Logger name
            
        Returns:
            Performance logger instance
        """
        return self.get_child_logger(
            name, 
            component='performance',
            extra_context={'subsystem': 'monitoring'}
        )
    
    def set_log_level(self, level: str, logger_name: Optional[str] = None) -> None:
        """
        Set logging level for specific logger or all Epochly loggers.

        NOTE: Only affects the isolated 'epochly' logger hierarchy.
        Never touches the root logger or user's logging configuration.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            logger_name: Specific logger name, or None for all Epochly loggers
        """
        with self._lock:
            log_level = getattr(logging, level.upper())

            if logger_name:
                # Ensure we only touch epochly loggers
                if not logger_name.startswith('epochly'):
                    logger_name = f'epochly.{logger_name}'
                logger = logging.getLogger(logger_name)
                logger.setLevel(log_level)
            else:
                # Set Epochly root logger level (NOT Python root logger)
                epochly_root = logging.getLogger('epochly')
                epochly_root.setLevel(log_level)

                # Update all cached child loggers
                for child_logger in self._child_loggers.values():
                    child_logger.setLevel(log_level)
    
    def add_operational_context(self, context: Dict[str, Any]) -> None:
        """
        Add operational context for structured logging.
        
        Args:
            context: Context information for operational monitoring
        """
        # Store context for future logger creation
        # This could be enhanced to add context to existing loggers
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get logging system status.

        Returns:
            Dictionary containing Epochly logging system status
        """
        with self._lock:
            epochly_logger = logging.getLogger('epochly')
            return {
                'initialized': self._initialized,
                'concurrent_enabled': self._concurrent_enabled,
                'child_loggers_count': len(self._child_loggers),
                'epochly_logger_level': epochly_logger.level if self._initialized else None,
                'epochly_handlers_count': len(epochly_logger.handlers),
                'propagate': epochly_logger.propagate  # Should always be False
            }
    
    def shutdown(self) -> None:
        """Shutdown logging system gracefully."""
        with self._lock:
            if self._root_logger:
                self._root_logger.info("Shutting down centralized logging")
            
            # Clear cached loggers
            self._child_loggers.clear()
            
            # Stop concurrent logging if enabled
            if self._concurrent_enabled:
                try:
                    from .concurrent_logging import stop_concurrent_logging
                    stop_concurrent_logging()
                except Exception as e:
                    logging.getLogger('epochly.logging_bootstrap').warning(
                        f"Error stopping concurrent logging: {e}"
                    )
            
            self._initialized = False
            self._concurrent_enabled = False
            self._root_logger = None


# Global logging bootstrap instance
_logging_bootstrap: Optional[LoggingBootstrap] = None
_bootstrap_lock = threading.RLock()


def get_logging_bootstrap() -> LoggingBootstrap:
    """Get the global logging bootstrap instance."""
    global _logging_bootstrap
    
    if _logging_bootstrap is None:
        with _bootstrap_lock:
            # Double-check locking pattern
            if _logging_bootstrap is None:
                _logging_bootstrap = LoggingBootstrap()
    
    return _logging_bootstrap


def initialize_centralized_logging(use_concurrent: bool = True,
                                 force_reinit: bool = False) -> bool:
    """
    Initialize centralized logging system.
    
    Args:
        use_concurrent: Whether to use concurrent logging
        force_reinit: Force reinitialization
        
    Returns:
        True if successful, False otherwise
    """
    bootstrap = get_logging_bootstrap()
    return bootstrap.initialize(use_concurrent, force_reinit)


def get_centralized_logger(name: str, 
                          component: Optional[str] = None) -> logging.Logger:
    """
    Get a centralized logger instance.
    
    Args:
        name: Logger name (typically __name__)
        component: Component name for categorization
        
    Returns:
        Configured logger instance
    """
    bootstrap = get_logging_bootstrap()
    return bootstrap.get_child_logger(name, component)
