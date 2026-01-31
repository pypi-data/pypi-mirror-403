"""
Epochly Logging Utilities

Centralized logging configuration and utilities for the Epochly framework.

IMPORTANT: Epochly logging is COMPLETELY ISOLATED from user logging.
- Epochly uses its own logger hierarchy (epochly.*)
- Epochly NEVER touches the root logger
- User's logging.disable() and logging configuration are respected
- Set EPOCHLY_LOG_LEVEL to control Epochly's internal logging (default: WARNING)
- Set EPOCHLY_DISABLE_LOGGING=1 to completely silence Epochly logging
"""

import logging
import os
import sys
import threading
from typing import Optional
from logging.handlers import RotatingFileHandler


# Global logger configuration - ONLY for Epochly loggers
_loggers = {}
_epochly_logger_configured = False
_logger_lock = threading.RLock()

# The isolated Epochly root logger
_epochly_root_logger: Optional[logging.Logger] = None


def _get_epochly_root_logger() -> logging.Logger:
    """
    Get the isolated Epochly root logger.

    This logger:
    - Does NOT propagate to the Python root logger
    - Has its own handlers
    - Is completely independent of user logging configuration

    Thread-safe: Uses double-checked locking to prevent duplicate handler attachment.

    Returns:
        The Epochly root logger
    """
    global _epochly_root_logger, _epochly_logger_configured

    # Fast path: already configured
    if _epochly_root_logger is not None:
        return _epochly_root_logger

    # Thread-safe initialization with double-checked locking
    with _logger_lock:
        # Re-check after acquiring lock
        if _epochly_root_logger is not None:
            return _epochly_root_logger

        # Check if logging is completely disabled
        if os.environ.get('EPOCHLY_DISABLE_LOGGING', '').lower() in ('1', 'true', 'yes'):
            # Create a null logger that does nothing
            logger = logging.getLogger('epochly')
            logger.propagate = False
            if not logger.handlers:
                logger.addHandler(logging.NullHandler())
            _epochly_root_logger = logger
            _epochly_logger_configured = True
            return _epochly_root_logger

        # Create the epochly root logger
        logger = logging.getLogger('epochly')

        # CRITICAL: Do NOT propagate to root logger - this isolates us from user config
        logger.propagate = False

        # Get log level from environment (default: WARNING for minimal noise)
        level_str = os.environ.get('EPOCHLY_LOG_LEVEL', 'WARNING').upper()
        level = getattr(logging, level_str, logging.WARNING)
        logger.setLevel(level)

        # Only add handlers if not already configured
        if not logger.handlers:
            # Default format for Epochly logs
            format_string = (
                "%(asctime)s - %(name)s - %(levelname)s - "
                "%(filename)s:%(lineno)d - %(message)s"
            )
            formatter = logging.Formatter(format_string)

            # Console handler to stderr (only if not in Jupyter or if explicitly enabled)
            if not _is_jupyter_environment() or os.environ.get('EPOCHLY_JUPYTER_LOGGING', '').lower() in ('1', 'true', 'yes'):
                console_handler = logging.StreamHandler(sys.stderr)
                console_handler.setFormatter(formatter)
                console_handler.setLevel(level)
                logger.addHandler(console_handler)
            else:
                # In Jupyter without explicit enable, use NullHandler to avoid IOPub flooding
                logger.addHandler(logging.NullHandler())

            # Add file handler if EPOCHLY_LOG_FILE is set
            log_file = os.environ.get('EPOCHLY_LOG_FILE')
            if log_file:
                try:
                    log_dir = os.path.dirname(log_file)
                    if log_dir:
                        os.makedirs(log_dir, mode=0o700, exist_ok=True)

                    file_handler = RotatingFileHandler(
                        log_file,
                        maxBytes=10 * 1024 * 1024,  # 10MB
                        backupCount=5
                    )
                    file_handler.setFormatter(formatter)
                    file_handler.setLevel(logging.DEBUG)  # File gets everything
                    logger.addHandler(file_handler)
                except Exception:
                    pass  # Silently ignore file handler errors

        _epochly_root_logger = logger
        _epochly_logger_configured = True
        return _epochly_root_logger


def _is_jupyter_environment() -> bool:
    """Detect if running in Jupyter/IPython environment."""
    try:
        from IPython import get_ipython
        ip = get_ipython()
        if ip is not None:
            # Check for ZMQ-based kernels (Jupyter)
            return ip.__class__.__name__ == 'ZMQInteractiveShell'
    except Exception:
        pass
    return False


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup Epochly-specific logging configuration.

    NOTE: This now ONLY configures the Epochly logger hierarchy.
    It does NOT touch the root logger or user's logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        format_string: Custom format string for log messages

    Returns:
        Configured Epochly root logger instance
    """
    global _epochly_logger_configured

    # Get or create the Epochly root logger
    epochly_logger = _get_epochly_root_logger()

    # Parse the requested level
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Always apply level when explicitly requested (even if already configured)
    epochly_logger.setLevel(log_level)
    for handler in epochly_logger.handlers:
        if not isinstance(handler, logging.NullHandler):
            handler.setLevel(log_level)

    # If already configured and no file handler requested, return early
    if _epochly_logger_configured and not log_file:
        return epochly_logger

    # Add file handler if specified and not already present
    if log_file:
        # Check if file handler already exists
        has_file_handler = any(
            isinstance(h, RotatingFileHandler)
            for h in epochly_logger.handlers
        )

        if not has_file_handler:
            try:
                log_dir = os.path.dirname(log_file)
                if log_dir:
                    os.makedirs(log_dir, mode=0o700, exist_ok=True)

                if format_string is None:
                    format_string = (
                        "%(asctime)s - %(name)s - %(levelname)s - "
                        "%(filename)s:%(lineno)d - %(message)s"
                    )
                formatter = logging.Formatter(format_string)

                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count
                )
                file_handler.setFormatter(formatter)
                file_handler.setLevel(log_level)
                epochly_logger.addHandler(file_handler)

            except (PermissionError, OSError, IOError):
                pass  # Silently ignore - don't pollute user output
            except Exception:
                pass

    _epochly_logger_configured = True
    return epochly_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified name.

    All Epochly loggers are children of the isolated 'epochly' logger,
    which does NOT propagate to the root logger. This ensures:
    - User's logging configuration is never affected
    - logging.disable() from user code is respected
    - Epochly logs can be controlled independently via EPOCHLY_LOG_LEVEL

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance under the 'epochly' hierarchy
    """
    global _loggers

    # Ensure the isolated Epochly root logger is configured
    _get_epochly_root_logger()

    # Return cached logger if available
    if name in _loggers:
        return _loggers[name]

    # Normalize name to be under epochly hierarchy
    if name.startswith('epochly'):
        logger_name = name
    else:
        # Convert module paths like 'epochly.core.manager' to use epochly prefix
        logger_name = f'epochly.{name}' if name else 'epochly'

    # Create logger - it will inherit from epochly root logger
    logger = logging.getLogger(logger_name)

    # Child loggers should NOT propagate beyond the epochly root
    # (The epochly root already has propagate=False)

    _loggers[name] = logger
    return logger


class EpochlyLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds Epochly-specific context to log messages.
    """
    
    def __init__(self, logger: logging.Logger, extra: Optional[dict] = None):
        """
        Initialize the adapter.
        
        Args:
            logger: Base logger instance
            extra: Additional context to include in log messages
        """
        super().__init__(logger, extra or {})
    
    def process(self, msg, kwargs):
        """
        Process log message to add context.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments
            
        Returns:
            Tuple of (message, kwargs)
        """
        # Add Epochly context
        extra = kwargs.get('extra', {})
        if self.extra:
            extra.update(self.extra)
        
        # Add performance context if available
        try:
            import threading
            extra['thread_id'] = threading.get_ident()
        except Exception:
            pass
        
        kwargs['extra'] = extra
        return msg, kwargs


def get_performance_logger(name: str) -> EpochlyLoggerAdapter:
    """
    Get a performance-focused logger with additional context.
    
    Args:
        name: Logger name
        
    Returns:
        EpochlyLoggerAdapter instance with performance context
    """
    base_logger = get_logger(name)
    
    # Add performance-specific context
    extra = {
        'component': 'performance',
        'subsystem': name.split('.')[-1] if '.' in name else name
    }
    
    return EpochlyLoggerAdapter(base_logger, extra)


def log_performance_metric(
    logger: logging.Logger,
    metric_name: str,
    value: float,
    unit: str = "",
    context: Optional[dict] = None
) -> None:
    """
    Log a performance metric in a structured format.
    
    Args:
        logger: Logger instance
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        context: Additional context information
    """
    context = context or {}
    
    metric_data = {
        'metric': metric_name,
        'value': value,
        'unit': unit,
        **context
    }
    
    logger.info(
        f"METRIC: {metric_name}={value}{unit}",
        extra={'metric_data': metric_data}
    )


def log_function_entry_exit(func):
    """
    Decorator to log function entry and exit with timing.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        # Log entry
        logger.debug(f"Entering {func.__name__}")
        start_time = time.perf_counter()
        
        try:
            result = func(*args, **kwargs)
            
            # Log successful exit
            duration = time.perf_counter() - start_time
            logger.debug(f"Exiting {func.__name__} (duration: {duration:.4f}s)")
            
            return result
            
        except Exception as e:
            # Log exception exit
            duration = time.perf_counter() - start_time
            logger.error(
                f"Exception in {func.__name__} after {duration:.4f}s: {e}",
                exc_info=True
            )
            raise
    
    return wrapper


# NOTE: No auto-setup on import!
# Epochly logging is now isolated and configured on-demand when get_logger() is called.
# This ensures user's logging configuration is NEVER affected by importing Epochly.