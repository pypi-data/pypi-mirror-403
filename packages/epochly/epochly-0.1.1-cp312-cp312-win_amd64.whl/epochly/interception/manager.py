"""
Interception Manager - Central Routing for Transparent Interception

Provides execute_vector_op() and similar entry points that wrapped library
functions call. Routes to Level 3 executor if beneficial, falls back otherwise.

Author: Epochly Development Team
Date: November 16, 2025
"""

import time
import functools
from typing import Callable, Any, Optional, Tuple, Dict, TYPE_CHECKING

# Lazy imports to avoid circular dependencies
if TYPE_CHECKING:
    from .telemetry import InterceptionTelemetry

from ..utils.logger import get_logger

logger = get_logger(__name__)


class InterceptionManager:
    """
    Central manager for transparent function interception.

    Wrapp library functions call this manager's execute_* methods,
    which decide whether to route to Level 3 or call original function.
    """

    def __init__(self):
        """Initialize interception manager."""
        # Lazy import to avoid circular dependency
        from .telemetry import InterceptionTelemetry
        self._telemetry = InterceptionTelemetry()
        self._original_functions: Dict[str, Callable] = {}

    def execute_vector_op(
        self,
        op_id: str,
        original_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a vector operation (NumPy/Pandas), routing to Level 3 if beneficial.

        Telemetry Note:
        - execution_time tracks Level 3 attempt duration (not including fallback)
        - If Level 3 fails, fallback execution time is NOT included in telemetry
        - This allows measuring Level 3 overhead separately from total operation time

        Args:
            op_id: Operation identifier (e.g., 'numpy.dot')
            original_func: Original unwrapped function
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Result from function execution (Level 3 or sequential fallback)
        """
        # Debug logging (use DEBUG level for high-frequency calls)
        logger.debug(f"execute_vector_op called: op_id={op_id}, args={len(args)}, kwargs={len(kwargs)}")

        # Additional debug for interception investigation
        import os
        if os.environ.get('EPOCHLY_DEBUG_INTERCEPTION') == '1':
            logger.debug(f"InterceptionManager.execute_vector_op: op_id={op_id}")

        start_time = time.perf_counter()

        try:
            # Try Level 3 routing
            if os.environ.get('EPOCHLY_DEBUG_INTERCEPTION') == '1':
                logger.debug(f"  Attempting Level 3 routing...")
            result = self._try_level3_execution(op_id, original_func, *args, **kwargs)

            # Record success (BEFORE return!)
            elapsed = time.perf_counter() - start_time
            self._telemetry.record_interception(
                op_id=op_id,
                routed_to_level3=True,
                execution_time=elapsed,
                success=True
            )

            logger.debug(f"Level 3 routing succeeded for {op_id}")
            return result

        except Exception as e:
            # Fallback to original function
            import os
            if os.environ.get('EPOCHLY_DEBUG_INTERCEPTION') == '1':
                logger.debug(f"  Level 3 routing FAILED: {type(e).__name__}: {e}")
            logger.warning(f"Level 3 routing failed for {op_id}: {type(e).__name__}: {e}, falling back to original")

            # Record fallback (BEFORE executing original!)
            elapsed = time.perf_counter() - start_time
            self._telemetry.record_interception(
                op_id=op_id,
                routed_to_level3=False,
                execution_time=elapsed,
                success=False,
                error=str(e)
            )

            # Execute original function
            if os.environ.get('EPOCHLY_DEBUG_INTERCEPTION') == '1':
                logger.debug(f"  Executing original function...")
            return original_func(*args, **kwargs)

    def _try_level3_execution(
        self,
        op_id: str,
        original_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Attempt to execute via Level 3 executor.

        CRITICAL FIX: Uses OperationDescriptor to avoid pickle errors.
        Instead of sending the wrapped function object (which can't be pickled),
        we send an operation descriptor that workers can reconstruct.

        FRAMEWORK OPTIMIZATION (Nov 2025):
        For framework-specific operations (pandas groupby, merge), routes to
        specialized parallel optimizers instead of generic Level 3 executor.
        This achieves 3x+ speedup for suitable workloads.

        Args:
            op_id: Operation identifier (e.g., 'numpy.dot')
            original_func: Original function (not sent to workers, just for fallback)
            *args: Arguments
            **kwargs: Keyword arguments

        Returns:
            Execution result

        Raises:
            Exception: If Level 3 unavailable or execution fails
        """
        # FRAMEWORK-SPECIFIC ROUTING FIRST (Nov 2025 - CRITICAL FIX)
        # Framework optimizers have their own intelligent thresholds and must be
        # tried BEFORE generic registry gating. Otherwise, custom optimizers like
        # PandasApplyOptimizer (3.78x speedup) are unreachable.
        result = self._try_framework_optimization(op_id, original_func, *args, **kwargs)
        if result is not None:
            return result

        # GENERIC LEVEL 3: Check size threshold before attempting routing
        # This prevents regression on small operations (overhead > benefit)
        # Only applies to operations NOT handled by framework optimizers above
        from .registry import get_registry
        registry = get_registry()

        # Parse op_id to get module and function
        parts = op_id.split('.')
        if len(parts) >= 2:
            module = parts[0]
            function = '.'.join(parts[1:])

            # Check if operation meets size threshold for GENERIC Level 3
            if not registry.should_intercept(module, function, *args, **kwargs):
                # Operation too small for generic Level 3 - overhead would dominate
                raise RuntimeError(f"Operation below size threshold (prevents overhead regression)")

        # Get Epochly core
        from ..core.epochly_core import get_epochly_core, EnhancementLevel

        core = get_epochly_core()

        # Check if core available and initialized
        if not core or not core._initialized:
            raise RuntimeError("EpochlyCore not initialized")

        # Check if Level 3 active
        if core.current_level.value < EnhancementLevel.LEVEL_3_FULL.value:
            raise RuntimeError(f"Level 3 not active (current: {core.current_level.name})")

        # Check if Level 3 executor available
        if not hasattr(core, '_level3_executor') or core._level3_executor is None:
            raise RuntimeError("Level 3 executor not available")

        # CRITICAL: Create picklable operation descriptor instead of sending function
        from .operation_descriptor import create_operation_from_op_id

        operation = create_operation_from_op_id(op_id, args, kwargs)

        # Submit operation descriptor (not function object)
        # The descriptor is picklable and workers can execute it
        # Timeout configurable via environment variable (default 60s)
        import os
        timeout_seconds = float(os.environ.get('EPOCHLY_OPERATION_TIMEOUT', '60.0'))

        future = core._level3_executor.submit_task(operation, (), {})

        # Wait for result with configurable timeout
        exec_result = future.result(timeout=timeout_seconds)

        # Check for execution errors
        if not exec_result.success:
            error_msg = exec_result.error or "Unknown Level 3 execution error"
            raise RuntimeError(f"Level 3 execution failed: {error_msg}")

        # Return unwrapped result
        return exec_result.result

    def _try_framework_optimization(
        self,
        op_id: str,
        original_func: Callable,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """
        Try framework-specific parallel optimization.

        For certain framework operations (pandas groupby, merge), we have
        specialized parallel implementations that achieve significant speedups.

        Args:
            op_id: Operation identifier (e.g., 'pandas.DataFrame.groupby')
            original_func: Original function
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Result from framework optimization, or None if not applicable
        """
        import os
        debug = os.environ.get('EPOCHLY_DEBUG_INTERCEPTION') == '1'

        # Check if this is a pandas operation we can optimize
        if not op_id.startswith('pandas.'):
            return None

        # Parse operation
        op_lower = op_id.lower()

        try:
            # Handle pandas apply operations (custom Python functions - 3x+ speedup!)
            if 'apply' in op_lower:
                return self._optimize_pandas_apply(op_id, args, kwargs, debug)

            # Handle pandas groupby operations (built-in agg - no speedup)
            elif 'groupby' in op_lower:
                return self._optimize_pandas_groupby(op_id, args, kwargs, debug)

            # Handle pandas merge operations (built-in - no speedup)
            elif 'merge' in op_lower:
                return self._optimize_pandas_merge(op_id, args, kwargs, debug)

        except Exception as e:
            if debug:
                logger.debug(f"  Framework optimization failed: {e}, falling back to generic Level 3")
            # Return None to fall back to generic Level 3 execution
            return None

        return None

    def _optimize_pandas_groupby(
        self,
        op_id: str,
        args: tuple,
        kwargs: dict,
        debug: bool = False
    ) -> Optional[Any]:
        """
        Execute pandas groupby with parallel optimization.

        Strategy:
        1. Extract DataFrame and groupby parameters
        2. Check if parallelization is beneficial
        3. Use PandasGroupbyOptimizer for parallel execution

        Args:
            op_id: Operation identifier
            args: Function arguments (df as first arg for methods)
            kwargs: Keyword arguments (may contain 'by', aggregation spec)
            debug: Enable debug logging

        Returns:
            Grouped/aggregated result or None
        """
        from .frameworks import PandasGroupbyOptimizer

        if debug:
            logger.debug(f"  Attempting pandas groupby optimization...")

        # Extract DataFrame - it's typically the first argument or 'self'
        if not args:
            return None

        df = args[0]

        # Verify it's a DataFrame
        try:
            import pandas as pd
            if not isinstance(df, pd.DataFrame):
                if debug:
                    logger.debug(f"  First arg not a DataFrame, skipping optimization")
                return None
        except ImportError:
            return None

        # Extract groupby column(s) from kwargs or second argument
        by = kwargs.get('by')
        if by is None and len(args) > 1:
            by = args[1]

        if by is None:
            if debug:
                logger.debug(f"  No 'by' parameter found, skipping optimization")
            return None

        # Extract aggregation spec if present
        agg_spec = kwargs.get('agg', kwargs.get('aggfunc', kwargs.get('func')))

        # For simple groupby (no agg), we can't parallelize yet
        # Only optimize when we have an aggregation
        if agg_spec is None:
            if debug:
                logger.debug(f"  No aggregation spec, returning GroupBy object (not parallelized)")
            # Return None to let pandas create normal GroupBy object
            return None

        # Create optimizer and execute
        optimizer = PandasGroupbyOptimizer()

        try:
            result = optimizer.optimize_groupby(df, by, agg_spec)

            if debug:
                logger.debug(f"  Pandas groupby optimization successful")

            return result

        finally:
            # Don't shut down executor - keep it warm for subsequent calls
            pass

    def _optimize_pandas_merge(
        self,
        op_id: str,
        args: tuple,
        kwargs: dict,
        debug: bool = False
    ) -> Optional[Any]:
        """
        Execute pandas merge with parallel optimization.

        Strategy:
        1. Extract left and right DataFrames
        2. Check if parallelization is beneficial
        3. Use PandasMergeOptimizer for parallel execution

        Args:
            op_id: Operation identifier
            args: Function arguments (left, right DataFrames)
            kwargs: Keyword arguments (on, how, left_on, right_on)
            debug: Enable debug logging

        Returns:
            Merged DataFrame or None
        """
        from .frameworks import PandasMergeOptimizer

        if debug:
            logger.debug(f"  Attempting pandas merge optimization...")

        # Extract left and right DataFrames
        if len(args) < 2:
            return None

        left = args[0]
        right = args[1]

        # Verify they're DataFrames
        try:
            import pandas as pd
            if not isinstance(left, pd.DataFrame) or not isinstance(right, pd.DataFrame):
                if debug:
                    logger.debug(f"  Args not DataFrames, skipping optimization")
                return None
        except ImportError:
            return None

        # Extract merge parameters
        on = kwargs.get('on')
        how = kwargs.get('how', 'inner')
        left_on = kwargs.get('left_on')
        right_on = kwargs.get('right_on')

        # Create optimizer and execute
        optimizer = PandasMergeOptimizer()

        try:
            result = optimizer.optimize_merge(
                left, right,
                on=on, how=how,
                left_on=left_on, right_on=right_on
            )

            if debug:
                logger.debug(f"  Pandas merge optimization successful")

            return result

        finally:
            # Don't shut down executor - keep it warm for subsequent calls
            pass

    def _optimize_pandas_apply(
        self,
        op_id: str,
        args: tuple,
        kwargs: dict,
        debug: bool = False
    ) -> Optional[Any]:
        """
        Execute pandas apply with parallel optimization.

        CRITICAL: This is where parallelization ACTUALLY provides speedups!

        Custom Python apply functions are GIL-bound. Running them in separate
        processes via ProcessPoolExecutor bypasses the GIL and achieves real
        parallelism with 3-10x speedups.

        Args:
            op_id: Operation identifier
            args: Function arguments (df, func, or GroupBy object)
            kwargs: Keyword arguments
            debug: Enable debug logging

        Returns:
            Apply result or None
        """
        from .frameworks import PandasApplyOptimizer

        if debug:
            logger.debug(f"  Attempting pandas apply optimization (3x+ speedup target)...")

        # Extract DataFrame or GroupBy object
        if not args:
            return None

        first_arg = args[0]

        # Check if this is a GroupBy.apply call
        try:
            import pandas as pd
            from pandas.core.groupby import DataFrameGroupBy, SeriesGroupBy

            if isinstance(first_arg, (DataFrameGroupBy, SeriesGroupBy)):
                # GroupBy.apply(func) call
                groupby_obj = first_arg
                func = args[1] if len(args) > 1 else kwargs.get('func')

                if func is None:
                    if debug:
                        logger.debug(f"  No function provided to apply")
                    return None

                # Get original DataFrame and group keys from GroupBy object
                # CRITICAL FIX (Nov 2025): Use grouper.names not keys
                # groupby_obj.keys returns group values, not column names
                df = groupby_obj.obj
                by = list(groupby_obj.grouper.names)

                # Create optimizer and execute
                optimizer = PandasApplyOptimizer()

                try:
                    result = optimizer.optimize_apply(df, by, func)

                    if debug:
                        logger.debug(f"  Pandas apply optimization successful")

                    return result

                finally:
                    # Don't shut down executor - keep it warm
                    pass

            elif isinstance(first_arg, pd.DataFrame):
                # DataFrame.apply(func) call - not groupby, different optimization
                # For now, return None to use default behavior
                if debug:
                    logger.debug(f"  DataFrame.apply (not GroupBy) - using default")
                return None

        except ImportError:
            return None

        return None

    def is_wrapped(self, module: str, function: str) -> bool:
        """
        Check if a function is wrapped.

        Args:
            module: Module name (e.g., 'numpy')
            function: Function name (e.g., 'dot')

        Returns:
            True if the function is wrapped (registered in _original_functions)
        """
        op_id = f"{module}.{function}"
        return op_id in self._original_functions

    def get_interception_count(self) -> int:
        """
        Get total number of interceptions recorded.

        Returns:
            Total interception count from telemetry
        """
        if hasattr(self._telemetry, 'get_total_count'):
            return self._telemetry.get_total_count()
        # Fallback - count from telemetry data
        if hasattr(self._telemetry, '_interceptions'):
            return len(self._telemetry._interceptions)
        return 0

    def register_original_function(self, op_id: str, func: Callable):
        """
        Register original function for an operation.

        Args:
            op_id: Operation identifier
            func: Original unwrapped function
        """
        self._original_functions[op_id] = func

    def get_original_function(self, op_id: str) -> Optional[Callable]:
        """
        Get original unwrapped function.

        Args:
            op_id: Operation identifier

        Returns:
            Original function or None
        """
        return self._original_functions.get(op_id)

    def get_telemetry(self) -> 'InterceptionTelemetry':
        """Get telemetry instance."""
        return self._telemetry


# Global manager instance
_global_manager = None


def get_interception_manager() -> InterceptionManager:
    """Get the global interception manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = InterceptionManager()
    return _global_manager
