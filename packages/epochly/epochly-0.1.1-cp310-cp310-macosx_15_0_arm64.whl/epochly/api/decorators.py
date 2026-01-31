"""
Epochly API Decorators

Decorators for the Epochly framework API.
"""

import functools
from typing import Any, Callable, TypeVar, Union, Optional
from ..core.epochly_core import get_epochly_core, EnhancementLevel

F = TypeVar('F', bound=Callable[..., Any])


def optimize(
    level: Union[EnhancementLevel, int, None] = None,  # P0.26 FIX: None = use system level
    monitor_performance: bool = True,
    **options
) -> Callable[[F], F]:
    """
    Decorator to optimize function execution using Epochly.

    Args:
        level: Enhancement level to apply. If None, uses current system level
               (respects EPOCHLY_LEVEL environment variable).
        monitor_performance: Whether to monitor performance
        **options: Additional optimization options

    Returns:
        Decorated function with Epochly optimizations

    P0.26 FIX (Jan 2026): Changed default from LEVEL_1_THREADING to None.
    Previously, decorator always used Level 1 regardless of EPOCHLY_LEVEL env var.
    Now decorator respects the system-wide level setting when no explicit level given.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            epochly_core = get_epochly_core()

            # P0.26 FIX: Determine effective level
            # If level is None, use the system's current level
            effective_level = level
            if effective_level is None:
                effective_level = epochly_core.current_level
            elif isinstance(effective_level, int):
                effective_level = EnhancementLevel(effective_level)

            # Use Epochly core to optimize function execution
            return epochly_core.optimize_function(
                func, args, kwargs,
                level=effective_level,  # CRITICAL: Pass effective level
                monitor_performance=monitor_performance,
                **options
            )
        
        # Add Epochly metadata
        wrapper._epochly_enhanced = True  # type: ignore
        wrapper._epochly_level = level  # type: ignore
        wrapper._epochly_original = func  # type: ignore
        
        return wrapper  # type: ignore
    
    return decorator


def performance_monitor(func: F) -> F:
    """
    Decorator to add performance monitoring to a function.
    
    Args:
        func: Function to monitor
        
    Returns:
        Decorated function with performance monitoring
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        epochly_core = get_epochly_core()
        
        # Enable monitoring if not already enabled
        epochly_core.enable_monitoring(True)
        
        # Execute function with monitoring
        return epochly_core.optimize_function(
            func, args, kwargs,
            monitor_performance=True
        )
    
    # Add Epochly metadata
    wrapper._epochly_monitored = True  # type: ignore
    wrapper._epochly_original = func  # type: ignore
    
    return wrapper  # type: ignore


def jit_compile(func: F) -> F:
    """
    Decorator to enable JIT compilation for a function.
    
    Args:
        func: Function to JIT compile
        
    Returns:
        Decorated function with JIT compilation
    """
    return optimize(
        level=EnhancementLevel.LEVEL_2_JIT,
        monitor_performance=True
    )(func)


def full_optimize(func: F) -> F:
    """
    Decorator to apply full Epochly optimization to a function.
    
    Args:
        func: Function to fully optimize
        
    Returns:
        Decorated function with full optimization
    """
    return optimize(
        level=EnhancementLevel.LEVEL_3_FULL,
        monitor_performance=True
    )(func)


def threading_optimize(
    max_workers: Optional[int] = None,
    thread_pool: bool = True
) -> Callable[[F], F]:
    """
    Decorator to optimize function with threading.
    
    Args:
        max_workers: Maximum number of worker threads
        thread_pool: Whether to use thread pool
        
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        return optimize(
            level=EnhancementLevel.LEVEL_1_THREADING,
            monitor_performance=True,
            max_workers=max_workers,
            thread_pool=thread_pool
        )(func)
    
    return decorator