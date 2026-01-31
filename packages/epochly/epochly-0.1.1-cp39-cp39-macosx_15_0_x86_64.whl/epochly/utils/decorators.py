"""
Epochly Decorator Utilities

Common decorators for the Epochly framework.
"""

import functools
import threading
import time
from typing import Any, Callable, Literal, Optional, TypeVar, Union, cast, overload

from .logger import get_logger, log_performance_metric

F = TypeVar('F', bound=Callable[..., Any])
Scope = Literal["per-callable", "per-instance"]


def singleton(cls):
    """
    Singleton decorator for classes.
    
    Args:
        cls: Class to make singleton
        
    Returns:
        Singleton class
    """
    instances = {}
    lock = threading.Lock()
    
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


@overload
def thread_safe(func: F) -> F: ...

@overload
def thread_safe(*, scope: Scope = "per-callable") -> Callable[[F], F]: ...

def thread_safe(func: Optional[F] = None, *, scope: Scope = "per-callable") -> Union[F, Callable[[F], F]]:
    """
    Thread-safe decorator with configurable locking scope.

    Supports two locking strategies:
    - 'per-callable': Each decorated function has its own lock (default, no contention between functions)
    - 'per-instance': Each instance method has its own lock per instance (requires instance._lock attribute)

    Per perf_fixes.md Task 3: "Replace global RLock with per-function lock...
    Provide optional granularity via decorator parameter scope='per-instance'|'per-callable'"

    Args:
        func: Function to make thread-safe
        scope: Locking scope - "per-callable" (default) or "per-instance"

    Returns:
        Thread-safe function

    Example:
        # Per-callable (default) - each function has its own lock
        @thread_safe
        def my_function():
            ...

        # Per-instance - each instance has its own lock (for instance methods only)
        class MyClass:
            def __init__(self):
                self._lock = threading.RLock()

            @thread_safe(scope='per-instance')
            def my_method(self):
                ...

    Note:
        - Per-instance mode requires instance to define self._lock attribute
        - Per-instance mode is for instance methods only (not staticmethod/classmethod)
        - Raises clear TypeError/AttributeError if used incorrectly
    """
    # Validate scope (type checker will catch invalid literals, but runtime validation for safety)
    if scope not in ("per-callable", "per-instance"):
        raise ValueError(f"Invalid scope: {scope}. Must be 'per-callable' or 'per-instance'")

    def decorator(f: F) -> F:
        # Per-callable: Create lock in closure (each decorated function gets own lock)
        if scope == "per-callable":
            lock = threading.RLock()

            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                with lock:
                    return f(*args, **kwargs)

            return cast(F, wrapper)

        # Per-instance: Use instance._lock attribute
        elif scope == "per-instance":
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                # First argument is 'self' for instance methods
                if not args:
                    raise TypeError(
                        f"Per-instance locking requires instance (self) as first argument. "
                        f"Function {f.__name__} called with no arguments."
                    )

                instance = args[0]

                # Get lock from instance
                if not hasattr(instance, '_lock'):
                    raise AttributeError(
                        f"Per-instance locking requires instance to have '_lock' attribute. "
                        f"Instance {type(instance).__name__} missing _lock. "
                        f"Add: self._lock = threading.RLock() to __init__"
                    )

                instance_lock = instance._lock

                with instance_lock:
                    return f(*args, **kwargs)

            return cast(F, wrapper)

    # Support both @thread_safe and @thread_safe(scope='...')
    if func is not None:
        # Called as @thread_safe (no parentheses)
        return decorator(func)
    else:
        # Called as @thread_safe(scope='...') (with parentheses)
        return decorator


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called on each retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}, retrying in {current_delay}s")
                    
                    if on_retry:
                        on_retry(attempt + 1, e)
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None  # Should never reach here
        
        return cast(F, wrapper)
    return decorator


def timeout(seconds: float):
    """
    Timeout decorator for functions.
    
    Args:
        seconds: Timeout in seconds
        
    Returns:
        Decorated function with timeout
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use threading-based timeout for cross-platform compatibility
            import threading
            import queue
            
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            def target():
                try:
                    result = func(*args, **kwargs)
                    result_queue.put(result)
                except Exception as e:
                    exception_queue.put(e)
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=seconds)
            
            if thread.is_alive():
                # Thread is still running, timeout occurred
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
            
            # Check for exceptions
            if not exception_queue.empty():
                raise exception_queue.get()
            
            # Return result
            if not result_queue.empty():
                return result_queue.get()
            
            raise RuntimeError(f"Function {func.__name__} completed but no result available")
        
        return cast(F, wrapper)
    return decorator


def measure_performance(
    log_result: bool = True,
    include_args: bool = False,
    threshold: Optional[float] = None,
    sample_rate: float = 1.0
):
    """
    Performance measurement decorator.

    SPEC2 Task 7: Adds sampling to reduce log churn in hot functions.

    Args:
        log_result: Whether to log the performance result
        include_args: Whether to include function arguments in logs
        threshold: Optional threshold to warn if execution time exceeds it
        sample_rate: SPEC2 Task 7 - Sampling rate (0.0-1.0, default 1.0 = log everything)

    Returns:
        Decorated function with performance measurement
    """
    # Validate sample_rate
    if not 0.0 <= sample_rate <= 1.0:
        raise ValueError(f"sample_rate must be between 0.0 and 1.0, got {sample_rate}")

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time

                # SPEC2 Task 7: Probabilistic sampling to reduce log volume
                should_log = log_result
                if should_log and sample_rate < 1.0:
                    import random
                    should_log = random.random() < sample_rate

                # Log performance metric (with sampling)
                if should_log:
                    context = {'function': func.__name__, 'sample_rate': sample_rate}
                    if include_args:
                        context['args'] = str(args)[:100]  # Truncate long args
                        context['kwargs'] = str(kwargs)[:100]

                    log_performance_metric(
                        logger,
                        f"{func.__name__}_duration",
                        duration,
                        "seconds",
                        context
                    )

                # Check threshold (always check, even if not logging)
                if threshold and duration > threshold:
                    logger.warning(
                        f"Function {func.__name__} exceeded threshold: {duration:.4f}s > {threshold}s"
                    )

                return result

            except Exception as e:
                duration = time.perf_counter() - start_time
                logger.error(f"Function {func.__name__} failed after {duration:.4f}s: {e}")
                raise

        return cast(F, wrapper)
    return decorator


def cache_result(
    max_size: int = 128,
    ttl: Optional[float] = None,
    key_func: Optional[Callable] = None
):
    """
    Result caching decorator with TTL support.
    
    Args:
        max_size: Maximum cache size
        ttl: Time-to-live in seconds (None for no expiration)
        key_func: Optional function to generate cache keys
        
    Returns:
        Decorated function with caching
    """
    def decorator(func: F) -> F:
        cache = {}
        cache_times = {}
        lock = threading.RLock()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = str(args) + str(sorted(kwargs.items()))
            
            with lock:
                current_time = time.time()
                
                # Check if cached result exists and is valid
                if cache_key in cache:
                    if ttl is None or (current_time - cache_times[cache_key]) < ttl:
                        return cache[cache_key]
                    else:
                        # Remove expired entry
                        del cache[cache_key]
                        del cache_times[cache_key]
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                
                # Manage cache size
                if len(cache) >= max_size:
                    # Remove oldest entry
                    oldest_key = min(cache_times.keys(), key=lambda k: cache_times[k])
                    del cache[oldest_key]
                    del cache_times[oldest_key]
                
                cache[cache_key] = result
                cache_times[cache_key] = current_time
                
                return result
        
        # Add cache management methods to wrapper
        def cache_clear():
            cache.clear()
            cache_times.clear()
        
        def cache_info():
            return {
                'size': len(cache),
                'max_size': max_size,
                'ttl': ttl
            }
        
        wrapper.cache_clear = cache_clear  # type: ignore
        wrapper.cache_info = cache_info    # type: ignore
        
        return cast(F, wrapper)
    return decorator


def validate_args(**validators):
    """
    Argument validation decorator.
    
    Args:
        **validators: Keyword arguments mapping parameter names to validation functions
        
    Returns:
        Decorated function with argument validation
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import inspect
            
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate arguments
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValueError(f"Validation failed for parameter '{param_name}' with value: {value}")
            
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    return decorator


def deprecated(reason: str = "", version: str = ""):
    """
    Deprecation warning decorator.
    
    Args:
        reason: Reason for deprecation
        version: Version when deprecated
        
    Returns:
        Decorated function with deprecation warning
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import warnings
            
            message = f"Function {func.__name__} is deprecated"
            if version:
                message += f" since version {version}"
            if reason:
                message += f": {reason}"
            
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    return decorator


def async_to_sync(func: F) -> F:
    """
    Convert async function to sync using asyncio.
    
    Args:
        func: Async function to convert
        
    Returns:
        Sync version of the function
    """
    import asyncio
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(func(*args, **kwargs))
    
    return cast(F, wrapper)


def conditional(condition: Union[bool, Callable]):
    """
    Conditional decorator that only applies if condition is met.
    
    Args:
        condition: Boolean or callable that returns boolean
        
    Returns:
        Decorator that conditionally applies
    """
    def decorator(other_decorator):
        def wrapper(func: F) -> F:
            should_apply = condition() if callable(condition) else condition
            if should_apply:
                return other_decorator(func)
            return func
        return wrapper
    return decorator


# Utility function to combine multiple decorators
def compose_decorators(*decorators):
    """
    Compose multiple decorators into a single decorator.
    
    Args:
        *decorators: Decorators to compose
        
    Returns:
        Composed decorator
    """
    def decorator(func: F) -> F:
        for dec in reversed(decorators):
            func = dec(func)
        return func
    return decorator