"""
Epochly API Context Managers

Context managers for the Epochly framework API.
"""

import contextlib
from typing import Any, Dict, Optional, Generator
from ..core.epochly_core import get_epochly_core, EnhancementLevel


@contextlib.contextmanager
def optimize_context(
    level: EnhancementLevel = EnhancementLevel.LEVEL_1_THREADING,
    monitor_performance: bool = True,
    **options
) -> Generator[None, None, None]:
    """
    Context manager for optimized code execution.
    
    Args:
        level: Enhancement level to apply
        monitor_performance: Whether to monitor performance
        **options: Additional optimization options
        
    Yields:
        None
        
    Example:
        with optimize_context(EnhancementLevel.LEVEL_2_JIT):
            # Code here will be optimized with JIT compilation
            result = expensive_computation()
    """
    epochly_core = get_epochly_core()
    
    # Store original state
    original_level = epochly_core.current_level
    original_enabled = epochly_core.enabled
    
    try:
        # Apply optimization settings
        epochly_core.current_level = level
        epochly_core.enabled = True
        
        if monitor_performance and epochly_core.performance_monitor:
            epochly_core.performance_monitor.start()

        yield
        
    finally:
        # Restore original state
        epochly_core.current_level = original_level
        epochly_core.enabled = original_enabled


@contextlib.contextmanager
def monitoring_context(
    enable: bool = True,
    reset_on_exit: bool = False
) -> Generator[Dict[str, Any], None, None]:
    """
    Context manager for performance monitoring.
    
    Args:
        enable: Whether to enable monitoring
        reset_on_exit: Whether to reset metrics on exit
        
    Yields:
        Dict containing performance metrics
        
    Example:
        with monitoring_context() as metrics:
            # Code here will be monitored
            expensive_function()
            print(f"Metrics: {metrics}")
    """
    epochly_core = get_epochly_core()
    
    # Store original monitoring state
    was_monitoring = epochly_core.performance_monitor.is_active() if epochly_core.performance_monitor else False
    
    try:
        if enable and epochly_core.performance_monitor:
            epochly_core.performance_monitor.start()

        # Create metrics container that updates in real-time
        metrics = {}

        yield metrics

        # Update metrics before exit
        if epochly_core.performance_monitor:
            metrics.update(epochly_core.performance_monitor.get_system_summary())

    finally:
        # Restore original monitoring state
        if not was_monitoring and epochly_core.performance_monitor:
            epochly_core.performance_monitor.stop()

        # Reset metrics if requested
        if reset_on_exit and epochly_core.performance_monitor:
            epochly_core.performance_monitor.reset_metrics()


@contextlib.contextmanager
def jit_context(**options) -> Generator[None, None, None]:
    """
    Context manager for JIT compilation.
    
    Args:
        **options: JIT compilation options
        
    Yields:
        None
        
    Example:
        with jit_context():
            # Code here will use JIT compilation
            result = compute_intensive_task()
    """
    with optimize_context(
        level=EnhancementLevel.LEVEL_2_JIT,
        monitor_performance=True,
        **options
    ):
        yield


@contextlib.contextmanager
def threading_context(
    max_workers: Optional[int] = None,
    thread_pool: bool = True,
    **options
) -> Generator[None, None, None]:
    """
    Context manager for threading optimization.
    
    Args:
        max_workers: Maximum number of worker threads
        thread_pool: Whether to use thread pool
        **options: Additional threading options
        
    Yields:
        None
        
    Example:
        with threading_context(max_workers=4):
            # Code here will use threading optimization
            parallel_task()
    """
    with optimize_context(
        level=EnhancementLevel.LEVEL_1_THREADING,
        monitor_performance=True,
        max_workers=max_workers,
        thread_pool=thread_pool,
        **options
    ):
        yield


@contextlib.contextmanager
def full_optimize_context(**options) -> Generator[None, None, None]:
    """
    Context manager for full Epochly optimization.
    
    Args:
        **options: Optimization options
        
    Yields:
        None
        
    Example:
        with full_optimize_context():
            # Code here will use all available optimizations
            result = complex_computation()
    """
    with optimize_context(
        level=EnhancementLevel.LEVEL_3_FULL,
        monitor_performance=True,
        **options
    ):
        yield


@contextlib.contextmanager
def benchmark_context(
    name: str = "benchmark",
    print_results: bool = True
) -> Generator[Dict[str, Any], None, None]:
    """
    Context manager for benchmarking code execution.
    
    Args:
        name: Name of the benchmark
        print_results: Whether to print results on exit
        
    Yields:
        Dict containing benchmark results
        
    Example:
        with benchmark_context("my_function") as results:
            my_expensive_function()
            # Results will be automatically collected
    """
    import time
    
    epochly_core = get_epochly_core()
    
    # Initialize results container
    results = {
        'name': name,
        'start_time': None,
        'end_time': None,
        'duration': None,
        'metrics': {}
    }
    
    try:
        # Enable monitoring
        if epochly_core.performance_monitor:
            epochly_core.performance_monitor.start()

        # Record start time
        results['start_time'] = time.time()

        yield results

    finally:
        # Record end time and calculate duration
        results['end_time'] = time.time()
        results['duration'] = results['end_time'] - results['start_time']

        # Collect performance metrics
        if epochly_core.performance_monitor:
            results['metrics'] = epochly_core.performance_monitor.get_system_summary()
        
        # Print results if requested
        if print_results:
            print(f"Benchmark '{name}': {results['duration']:.4f}s")
            if results['metrics']:
                print(f"Metrics: {results['metrics']}")


@contextlib.contextmanager
def epochly_disabled_context() -> Generator[None, None, None]:
    """
    Context manager to temporarily disable Epochly optimizations.

    This context manager DOES NOT trigger Epochly initialization if Epochly
    hasn't been initialized yet. This allows running baseline measurements
    without any Epochly overhead or log noise.

    Yields:
        None

    Example:
        with epochly_disabled_context():
            # Code here will run without Epochly optimizations
            unoptimized_function()
    """
    import epochly as ep

    # Check if Epochly core is already initialized
    # CRITICAL: Do NOT call get_epochly_core() here as that triggers initialization
    if ep._core_singleton is None:
        # Core not initialized - just yield, nothing to disable
        yield
        return

    epochly_core = ep._core_singleton

    # Store original state
    original_enabled = epochly_core.enabled
    original_auto_profiler_enabled = False

    # Also disable auto-profiler to prevent sys.monitoring overhead
    # NOTE: AutoProfiler uses _enabled (underscore) not enabled
    if hasattr(epochly_core, '_auto_profiler') and epochly_core._auto_profiler is not None:
        original_auto_profiler_enabled = epochly_core._auto_profiler._enabled

    try:
        # Disable Epochly
        epochly_core.enabled = False

        # Disable auto-profiler to prevent JIT compilation during disabled context
        if hasattr(epochly_core, '_auto_profiler') and epochly_core._auto_profiler is not None:
            epochly_core._auto_profiler._enabled = False

        yield

    finally:
        # Restore original state
        epochly_core.enabled = original_enabled

        # Restore auto-profiler state
        if hasattr(epochly_core, '_auto_profiler') and epochly_core._auto_profiler is not None:
            epochly_core._auto_profiler._enabled = original_auto_profiler_enabled