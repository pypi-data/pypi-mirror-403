"""
Epochly Public API

Main public interface for the Epochly framework.
"""

import functools
import inspect
from typing import Any, Callable, Dict, Optional, TypeVar, Union, cast

from ..core.epochly_core import EpochlyCore, EnhancementLevel, get_epochly_core
from ..utils.logger import get_logger
from ..utils.exceptions import EpochlyError, EpochlyConfigurationError

logger = get_logger(__name__)

F = TypeVar('F', bound=Callable[..., Any])

# Use the singleton from epochly_core instead of creating our own
def _get_epochly_instance() -> EpochlyCore:
    """Get the global Epochly instance from epochly_core."""
    return get_epochly_core()


def epochly_run(
    func: Optional[F] = None,
    *,
    level: Union[EnhancementLevel, int, str] = EnhancementLevel.LEVEL_0_MONITOR,
    config: Optional[Dict[str, Any]] = None,
    auto_optimize: bool = True,
    monitor_performance: bool = True
) -> Union[F, Callable[[F], F]]:
    """
    Main Epochly decorator for optimizing functions.

    Args:
        func: Function to optimize (when used without parentheses)
        level: Enhancement level to apply
        config: Additional configuration options
        auto_optimize: Whether to automatically optimize based on performance
        monitor_performance: Whether to monitor performance metrics

    Returns:
        Decorated function or decorator

    Example:
        @epochly_run
        def my_function():
            pass

        @epochly_run(level=EnhancementLevel.JIT)
        def optimized_function():
            pass
    """
    def decorator(f: F) -> F:
        # Convert level to EnhancementLevel if needed
        if isinstance(level, (int, str)):
            try:
                enhancement_level = EnhancementLevel(level)
            except ValueError:
                raise EpochlyConfigurationError(f"Invalid enhancement level: {level}")
        else:
            enhancement_level = level

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # CRITICAL FIX: Fast path for Level 2 JIT (bypass optimizer after compilation)
                # After first successful JIT compilation, jump directly to compiled function
                # This eliminates ~130ms per-call overhead and enables 90× JIT speedup
                if enhancement_level == EnhancementLevel.LEVEL_2_JIT:
                    compiled_impl = getattr(f, '_epochly_jit_impl', None)
                    if compiled_impl is not None:
                        # Fast path: Execute compiled function directly
                        return compiled_impl(*args, **kwargs)

                # Get Epochly instance at execution time, not decoration time
                epochly = _get_epochly_instance()

                # Check if system is closed and reinitialize if needed
                if getattr(epochly, '_closed', False):
                    # Epochly was shutdown, reinitialize it
                    epochly._closed = False
                    epochly.initialize()

                # LEVEL 3+: Try loop transformation for parallelizable loops
                # CRITICAL: If transformation not possible, execute original with ZERO overhead
                if enhancement_level.value >= EnhancementLevel.LEVEL_3_FULL.value:
                    # ==========================================================================
                    # FAST PATTERN PRE-SCREENING (Architecture Requirement: Zero Overhead)
                    # ==========================================================================
                    # Per epochly-architecture-spec.md: "Unsuitable workloads must NOT be penalized"
                    # This section ensures patterns like inline arithmetic run at baseline speed.
                    # ==========================================================================
                    func_id = id(f)

                    # Check if already marked as non-transformable (fastest path)
                    if hasattr(epochly, '_non_transformable_functions') and func_id in epochly._non_transformable_functions:
                        # Known unsuitable pattern - execute directly with ZERO overhead
                        return f(*args, **kwargs)

                    # Initialize non-transformable cache if needed
                    if not hasattr(epochly, '_non_transformable_functions'):
                        epochly._non_transformable_functions = set()

                    # FAST HEURISTIC 1: Check function signature for known problematic patterns
                    # Functions with no parameters can't be chunked - reject immediately
                    try:
                        sig = inspect.signature(f)
                        if len(sig.parameters) == 0:
                            epochly._non_transformable_functions.add(func_id)
                            return f(*args, **kwargs)
                    except Exception:
                        pass  # Can't get signature, proceed with analysis

                    # FAST HEURISTIC 2: Pattern Suitability Analysis (<1ms)
                    # Detect patterns where parallelization overhead exceeds benefit:
                    # - Inline arithmetic (r += i ** 2)
                    # - Light nested loops
                    # - Trivial operations
                    try:
                        from ..profiling.pattern_suitability_analyzer import is_pattern_suitable_for_parallelization

                        is_suitable, reason = is_pattern_suitable_for_parallelization(f)

                        if not is_suitable:
                            # Pattern not suitable - mark and execute directly with ZERO overhead
                            epochly._non_transformable_functions.add(func_id)
                            logger.debug(f"{f.__name__} pattern unsuitable: {reason}")
                            return f(*args, **kwargs)

                    except ImportError:
                        # Analyzer not available - fall back to standard analysis
                        logger.debug("Pattern suitability analyzer not available")
                    except Exception as e:
                        # Analysis failed - proceed with standard path (conservative)
                        logger.debug(f"Pattern analysis exception: {e}")

                    # ==========================================================================
                    # STANDARD TRANSFORMATION PATH (only for suitable patterns)
                    # ==========================================================================
                    try:
                        from ..profiling.runtime_loop_transformer import RuntimeLoopTransformer

                        # Get or create cached transformer (reuse across calls to maintain batch_dispatcher)
                        if not hasattr(epochly, '_loop_transformer'):
                            # CRITICAL: min_iterations threshold filters tiny workloads where overhead > speedup
                            # Per MCP-Reflect RCA (2025-11-19): Tasks <1000 iterations often have overhead > compute
                            # Production default: 1000 (only substantial loops benefit from parallelization)
                            # For testing/development: Set to 50 via environment variable
                            import os
                            min_iters = int(os.environ.get('EPOCHLY_MIN_ITERATIONS', '1000'))
                            epochly._loop_transformer = RuntimeLoopTransformer(executor=None, min_iterations=min_iters)

                        transformer = epochly._loop_transformer

                        # Check if we've already transformed this function
                        if func_id in transformer._transformed_functions:
                            cached = transformer._transformed_functions[func_id]

                            # If cached value is original function, it's non-transformable
                            if cached is f:
                                # Mark as non-transformable for faster path next time
                                epochly._non_transformable_functions.add(func_id)
                                return f(*args, **kwargs)
                            else:
                                # Successfully transformed - use it
                                return cached(*args, **kwargs)

                        # First call for a suitable pattern - perform detailed analysis
                        analysis = transformer.analyze_function(f)

                        # If not suitable after detailed analysis, mark and execute directly
                        if not analysis or not analysis.get('should_transform', False):
                            epochly._non_transformable_functions.add(func_id)
                            logger.debug(f"{f.__name__} not suitable for transformation, executing with zero overhead")
                            return f(*args, **kwargs)

                        # Attempt transformation
                        transformed = transformer.transform_function(f)

                        if transformed:
                            logger.debug(f"Transformed {f.__name__} for loop parallelization")
                            return transformed(*args, **kwargs)
                        else:
                            # Transformation failed - mark as non-transformable
                            epochly._non_transformable_functions.add(func_id)
                            logger.debug(f"Transformation failed for {f.__name__}, executing directly")
                            return f(*args, **kwargs)

                    except Exception as e:
                        logger.debug(f"Loop transformation exception for {f.__name__}: {e}, executing directly")
                        # Mark as non-transformable and execute directly
                        epochly._non_transformable_functions.add(func_id)
                        return f(*args, **kwargs)

                # Standard Epochly optimization path
                return epochly.optimize_function(
                    f,
                    args,
                    kwargs,
                    level=enhancement_level,
                    config=config or {},
                    auto_optimize=auto_optimize,
                    monitor_performance=monitor_performance
                )
            except Exception as e:
                logger.error(f"Epochly optimization failed for {f.__name__}: {e}")
                # Fallback to original function
                return f(*args, **kwargs)

        # Preserve function metadata and add Epochly-specific attributes
        wrapper._epochly_enhanced = True  # type: ignore[attr-defined]
        wrapper._epochly_level = enhancement_level  # type: ignore[attr-defined]
        wrapper._epochly_original = f  # type: ignore[attr-defined]

        # Initialize JIT fast path attribute (will be set after first successful compilation)
        f._epochly_jit_impl = None  # type: ignore[attr-defined]

        # Preserve original function signature for introspection
        wrapper.__signature__ = inspect.signature(f)  # type: ignore[attr-defined]

        return cast(F, wrapper)

    if func is None:
        # Called with parentheses: @epochly_run(...)
        return decorator
    else:
        # Called without parentheses: @epochly_run
        return decorator(func)


def configure(
    enhancement_level: Union[EnhancementLevel, int, str] = EnhancementLevel.LEVEL_0_MONITOR,
    force: bool = False,
    **kwargs
) -> None:
    """
    Configure global Epochly settings.

    Args:
        enhancement_level: Default enhancement level
        force: If True, bypass progression validation (for CLI/explicit level setting)
        **kwargs: Additional configuration options
    """
    try:
        epochly = _get_epochly_instance()

        # Convert level if needed
        if isinstance(enhancement_level, (int, str)):
            enhancement_level = EnhancementLevel(enhancement_level)

        epochly.configure(enhancement_level=enhancement_level, force=force, **kwargs)
        logger.info(f"Epochly configured with level {enhancement_level}")

    except Exception as e:
        logger.error(f"Failed to configure Epochly: {e}")
        raise EpochlyConfigurationError(f"Configuration failed: {e}")


def get_status() -> Dict[str, Any]:
    """
    Get current Epochly status and statistics.

    Returns:
        Dictionary containing status information
    """
    try:
        epochly = _get_epochly_instance()
        return epochly.get_status()
    except Exception as e:
        logger.error(f"Failed to get Epochly status: {e}")
        return {
            "error": str(e),
            "active": False,
            "enhancement_level": "unknown"
        }


def enable_monitoring(enable: bool = True) -> None:
    """
    Enable or disable performance monitoring.

    Args:
        enable: Whether to enable monitoring
    """
    try:
        epochly = _get_epochly_instance()
        epochly.enable_monitoring(enable)
        logger.info(f"Epochly monitoring {'enabled' if enable else 'disabled'}")
    except Exception as e:
        logger.error(f"Failed to toggle monitoring: {e}")
        raise EpochlyError(f"Monitoring toggle failed: {e}")


def get_metrics() -> Dict[str, Any]:
    """
    Get performance metrics.

    Returns:
        Dictionary containing performance metrics
    """
    try:
        epochly = _get_epochly_instance()
        return epochly.get_metrics()
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return {"error": str(e)}


def reset_metrics() -> None:
    """Reset all performance metrics."""
    try:
        epochly = _get_epochly_instance()
        epochly.reset_metrics()
        logger.info("Epochly metrics reset")
    except Exception as e:
        logger.error(f"Failed to reset metrics: {e}")
        raise EpochlyError(f"Metrics reset failed: {e}")


def is_function_enhanced(func: Callable) -> bool:
    """
    Check if a function is Epochly-enhanced.

    Args:
        func: Function to check

    Returns:
        True if function is Epochly-enhanced
    """
    return hasattr(func, '_epochly_enhanced') and func._epochly_enhanced


def get_function_level(func: Callable) -> Optional[EnhancementLevel]:
    """
    Get the enhancement level of a function.

    Args:
        func: Function to check

    Returns:
        Enhancement level or None if not enhanced
    """
    if is_function_enhanced(func):
        return getattr(func, '_epochly_level', None)
    return None


def get_original_function(func: Callable) -> Callable:
    """
    Get the original unenhanced function.

    Args:
        func: Enhanced function

    Returns:
        Original function or the same function if not enhanced
    """
    if is_function_enhanced(func):
        return getattr(func, '_epochly_original', func)
    return func


def shutdown() -> None:
    """Shutdown Epochly and cleanup resources."""
    try:
        epochly_instance = get_epochly_core()
        epochly_instance.shutdown()
        logger.info("Epochly shutdown complete")
    except Exception as e:
        logger.error(f"Error during Epochly shutdown: {e}")
        raise EpochlyError(f"Shutdown failed: {e}")


# Convenience aliases
optimize = epochly_run  # Alias for epochly_run
run = epochly_run      # Shorter alias
