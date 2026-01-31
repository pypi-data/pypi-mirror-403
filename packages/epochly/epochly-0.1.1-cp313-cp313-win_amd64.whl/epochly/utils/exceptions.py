"""
Epochly Exception Classes

Custom exception classes for the Epochly framework.
"""

from typing import Optional, Dict, Any, Callable, TypeVar
import functools

# Type variable for generic function decoration
F = TypeVar('F', bound=Callable[..., Any])


class EpochlyError(Exception):
    """Base exception class for all Epochly-related errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize Epochly error.
        
        Args:
            message: Error message
            error_code: Optional error code for categorization
            context: Optional context information
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
    
    def __str__(self) -> str:
        """String representation of the error."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'context': self.context
        }


class EpochlyConfigError(EpochlyError):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs: Any) -> None:
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_key: Configuration key that caused the error
            **kwargs: Additional arguments passed to EpochlyError
        """
        super().__init__(message, **kwargs)
        self.config_key = config_key
        if config_key:
            self.context['config_key'] = config_key


class EpochlyCompatibilityError(EpochlyError):
    """Exception raised for compatibility-related errors."""
    
    def __init__(self, message: str, requirement: Optional[str] = None, current: Optional[str] = None, **kwargs: Any) -> None:
        """
        Initialize compatibility error.
        
        Args:
            message: Error message
            requirement: Required version/feature
            current: Current version/feature
            **kwargs: Additional arguments passed to EpochlyError
        """
        super().__init__(message, **kwargs)
        self.requirement = requirement
        self.current = current
        if requirement:
            self.context['requirement'] = requirement
        if current:
            self.context['current'] = current


class EpochlyInitializationError(EpochlyError):
    """Exception raised during Epochly system initialization."""

    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        cause: Optional[Exception] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize initialization error.

        Args:
            message: Error message
            component: Component that failed to initialize
            cause: Original exception that caused the initialization failure
            **kwargs: Additional arguments passed to EpochlyError
        """
        super().__init__(message, **kwargs)
        self.component = component
        self.cause = cause
        if component:
            self.context['component'] = component
        if cause:
            self.context['cause_type'] = type(cause).__name__
            self.context['cause_message'] = str(cause)


class EpochlyPluginError(EpochlyError):
    """Exception raised for plugin-related errors."""
    
    def __init__(self, message: str, plugin_name: Optional[str] = None, **kwargs: Any) -> None:
        """
        Initialize plugin error.
        
        Args:
            message: Error message
            plugin_name: Name of the plugin that caused the error
            **kwargs: Additional arguments passed to EpochlyError
        """
        super().__init__(message, **kwargs)
        self.plugin_name = plugin_name
        if plugin_name:
            self.context['plugin_name'] = plugin_name


class EpochlyPerformanceError(EpochlyError):
    """Exception raised for performance-related errors."""
    
    def __init__(self, message: str, metric: Optional[str] = None, threshold: Optional[float] = None, actual: Optional[float] = None, **kwargs: Any) -> None:
        """
        Initialize performance error.
        
        Args:
            message: Error message
            metric: Performance metric name
            threshold: Expected threshold
            actual: Actual measured value
            **kwargs: Additional arguments passed to EpochlyError
        """
        super().__init__(message, **kwargs)
        self.metric = metric
        self.threshold = threshold
        self.actual = actual
        if metric:
            self.context['metric'] = metric
        if threshold is not None:
            self.context['threshold'] = threshold
        if actual is not None:
            self.context['actual'] = actual


class EpochlyMemoryError(EpochlyError):
    """Exception raised for memory-related errors."""
    
    def __init__(self, message: str, requested_size: Optional[int] = None, available_size: Optional[int] = None, **kwargs: Any) -> None:
        """
        Initialize memory error.
        
        Args:
            message: Error message
            requested_size: Requested memory size in bytes
            available_size: Available memory size in bytes
            **kwargs: Additional arguments passed to EpochlyError
        """
        super().__init__(message, **kwargs)
        self.requested_size = requested_size
        self.available_size = available_size
        if requested_size is not None:
            self.context['requested_size'] = requested_size
        if available_size is not None:
            self.context['available_size'] = available_size


class EpochlyThreadingError(EpochlyError):
    """Exception raised for threading-related errors."""
    
    def __init__(self, message: str, thread_id: Optional[int] = None, **kwargs: Any) -> None:
        """
        Initialize threading error.
        
        Args:
            message: Error message
            thread_id: Thread ID that caused the error
            **kwargs: Additional arguments passed to EpochlyError
        """
        super().__init__(message, **kwargs)
        self.thread_id = thread_id
        if thread_id is not None:
            self.context['thread_id'] = thread_id


class EpochlyJITError(EpochlyError):
    """Exception raised for JIT compilation errors."""
    
    def __init__(self, message: str, backend: Optional[str] = None, function_name: Optional[str] = None, **kwargs: Any) -> None:
        """
        Initialize JIT error.
        
        Args:
            message: Error message
            backend: JIT backend that failed
            function_name: Function that failed to compile
            **kwargs: Additional arguments passed to EpochlyError
        """
        super().__init__(message, **kwargs)
        self.backend = backend
        self.function_name = function_name
        if backend:
            self.context['backend'] = backend
        if function_name:
            self.context['function_name'] = function_name


class EpochlyOptimizationError(EpochlyError):
    """Exception raised for optimization-related errors."""
    
    def __init__(self, message: str, optimization_type: Optional[str] = None, **kwargs: Any) -> None:
        """
        Initialize optimization error.
        
        Args:
            message: Error message
            optimization_type: Type of optimization that failed
            **kwargs: Additional arguments passed to EpochlyError
        """
        super().__init__(message, **kwargs)
        self.optimization_type = optimization_type
        if optimization_type:
            self.context['optimization_type'] = optimization_type


# Exception hierarchy for easy catching
EPOCHLY_EXCEPTIONS = (
    EpochlyError,
    EpochlyConfigError,
    EpochlyCompatibilityError,
    EpochlyInitializationError,
    EpochlyPluginError,
    EpochlyPerformanceError,
    EpochlyMemoryError,
    EpochlyThreadingError,
    EpochlyJITError,
    EpochlyOptimizationError,
)


def handle_epochly_exception(func: F) -> F:
    """
    Decorator to handle Epochly exceptions gracefully.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function that handles Epochly exceptions
    """
    from .logger import get_logger
    
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except EPOCHLY_EXCEPTIONS as e:
            logger = get_logger(func.__module__)
            logger.error(f"Epochly exception in {func.__name__}: {e}")
            
            # Re-raise the exception for proper handling upstream
            raise
        except Exception as e:
            logger = get_logger(func.__module__)
            logger.error(f"Unexpected exception in {func.__name__}: {e}", exc_info=True)
            
            # Wrap unexpected exceptions in EpochlyError
            raise EpochlyError(f"Unexpected error in {func.__name__}: {e}") from e
    
    return wrapper  # type: ignore[return-value]


def create_error_context(**kwargs: Any) -> Dict[str, Any]:
    """
    Create error context dictionary.
    
    Args:
        **kwargs: Context key-value pairs
        
    Returns:
        Dictionary containing error context
    """
    import sys
    import traceback
    
    context = kwargs.copy()
    
    # Add system context
    context.update({
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'platform': sys.platform,
    })
    
    # Add stack trace if available
    if sys.exc_info()[0] is not None:
        context['traceback'] = traceback.format_exc()
    
    return context
# Alias for backward compatibility
EpochlyConfigurationError = EpochlyConfigError