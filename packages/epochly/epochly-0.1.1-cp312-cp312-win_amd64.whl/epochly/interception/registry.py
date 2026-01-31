"""
Interception Registry - Safe Function Mappings

Defines which library functions are safe for Level 3 executor routing.

Each entry specifies:
- Function signature (module.function)
- Safety criteria (Level 3 compatible)
- Argument shaping rules
- Fallback conditions

Author: Epochly Development Team
Date: November 16, 2025
"""

from dataclasses import dataclass, field
from typing import Callable, Optional, Dict, Any, List, TYPE_CHECKING
from enum import Enum

# Avoid importing numpy at module level to prevent circular imports during wrapping
if TYPE_CHECKING:
    import numpy as np


class SafetyLevel(Enum):
    """Safety level for automatic interception."""
    SAFE = "safe"  # Always safe for Level 3
    CONDITIONAL = "conditional"  # Safe under specific conditions
    UNSAFE = "unsafe"  # Never intercept


@dataclass
class FunctionDescriptor:
    """
    Descriptor for a library function that can be intercepted.

    Attributes:
        module: Module name (e.g., 'numpy')
        function: Function name (e.g., 'dot')
        safety_level: Whether safe for Level 3 routing
        min_data_size: Minimum data size for worthwhile routing (bytes)
        conditions: Additional conditions that must be met
        fallback_on_error: Whether to fallback to original on error
    """
    module: str
    function: str
    safety_level: SafetyLevel = SafetyLevel.SAFE
    min_data_size: int = 1_000_000  # 1MB default threshold
    conditions: Optional[Dict[str, Any]] = None
    fallback_on_error: bool = True


class InterceptionRegistry:
    """
    Registry of functions safe for transparent interception.

    Maintains mappings of library functions that can be automatically
    routed to Level 3 executor.
    """

    def __init__(self):
        """Initialize registry with safe function mappings."""
        self._registry: Dict[str, FunctionDescriptor] = {}
        self._load_default_mappings()

    def _load_default_mappings(self):
        """Load default safe function mappings."""

        # NumPy - Matrix operations
        # DISABLED (Nov 2025): No actual parallel optimizer implemented!
        # Benchmarks showed NumPy interception adds overhead without speedup:
        # - numpy_matmul: 0.97x (slower, not faster)
        # NumPy operations are already C-optimized with internal parallelization
        # via OpenBLAS/MKL - interception just adds IPC overhead.
        #
        # STATUS: Marked UNSAFE until proper chunked parallel optimizer is implemented
        # Target: 3-8x speedup per architecture spec (lines 4306-4310)
        numpy_functions = [
            FunctionDescriptor('numpy', 'dot', SafetyLevel.UNSAFE, min_data_size=100_000),
            FunctionDescriptor('numpy', 'matmul', SafetyLevel.UNSAFE, min_data_size=100_000),
            FunctionDescriptor('numpy', 'tensordot', SafetyLevel.UNSAFE, min_data_size=100_000),

            # Array operations - UNSAFE until proper optimizer
            FunctionDescriptor('numpy', 'sum', SafetyLevel.UNSAFE, min_data_size=1_000_000),
            FunctionDescriptor('numpy', 'mean', SafetyLevel.UNSAFE, min_data_size=1_000_000),
            FunctionDescriptor('numpy', 'std', SafetyLevel.UNSAFE, min_data_size=1_000_000),
            FunctionDescriptor('numpy', 'var', SafetyLevel.UNSAFE, min_data_size=1_000_000),

            # Sorting - UNSAFE until proper optimizer
            FunctionDescriptor('numpy', 'sort', SafetyLevel.UNSAFE, min_data_size=500_000),
            FunctionDescriptor('numpy', 'argsort', SafetyLevel.UNSAFE, min_data_size=500_000),
        ]

        # Pandas - DataFrame operations (conditional on size)
        pandas_functions = [
            FunctionDescriptor('pandas.DataFrame', 'groupby', SafetyLevel.CONDITIONAL,
                             min_data_size=1_000_000,
                             conditions={'min_rows': 10000}),
            FunctionDescriptor('pandas.DataFrame', 'agg', SafetyLevel.CONDITIONAL,
                             min_data_size=500_000),
            FunctionDescriptor('pandas.DataFrame', 'apply', SafetyLevel.CONDITIONAL,
                             min_data_size=500_000),
            FunctionDescriptor('pandas', 'merge', SafetyLevel.SAFE, min_data_size=500_000),
            FunctionDescriptor('pandas', 'concat', SafetyLevel.SAFE, min_data_size=500_000),
        ]

        # scikit-learn - Model training
        # DISABLED (Nov 2025): No actual parallel optimizer implemented!
        # Benchmarks showed sklearn interception adds overhead without speedup:
        # - sklearn_logreg: 0.98x (slower, not faster)
        # sklearn already has built-in parallelization via n_jobs parameter.
        # Interception just adds overhead without additional parallelization.
        #
        # STATUS: Marked UNSAFE until proper optimizer is implemented
        # Strategy: Should configure n_jobs=-1 automatically, not re-parallelize
        # Target: >5x speedup per architecture spec (line 5702)
        sklearn_functions = [
            FunctionDescriptor('sklearn.ensemble.RandomForestClassifier', 'fit',
                             SafetyLevel.UNSAFE, min_data_size=10_000),
            FunctionDescriptor('sklearn.ensemble.RandomForestRegressor', 'fit',
                             SafetyLevel.UNSAFE, min_data_size=10_000),
            FunctionDescriptor('sklearn.model_selection', 'cross_val_score',
                             SafetyLevel.UNSAFE, min_data_size=1_000),
            FunctionDescriptor('sklearn.model_selection', 'GridSearchCV',
                             SafetyLevel.UNSAFE, min_data_size=1_000),
        ]

        # Register all
        for desc in numpy_functions + pandas_functions + sklearn_functions:
            key = f"{desc.module}.{desc.function}"
            self._registry[key] = desc

    def register(self, descriptor: FunctionDescriptor):
        """
        Register a function for interception.

        Args:
            descriptor: Function descriptor with safety criteria
        """
        key = f"{descriptor.module}.{descriptor.function}"
        self._registry[key] = descriptor

    def is_interceptable(self, module: str, function: str) -> bool:
        """
        Check if function is registered for interception.

        Args:
            module: Module name
            function: Function name

        Returns:
            True if function is registered
        """
        key = f"{module}.{function}"
        return key in self._registry

    def get_descriptor(self, module: str, function: str) -> Optional[FunctionDescriptor]:
        """
        Get descriptor for a function.

        Args:
            module: Module name
            function: Function name

        Returns:
            FunctionDescriptor or None if not registered
        """
        key = f"{module}.{function}"
        return self._registry.get(key)

    def should_intercept(self, module: str, function: str, *args, **kwargs) -> bool:
        """
        Determine if function should be intercepted for specific call.

        Checks:
        - Function is registered
        - Safety criteria met
        - Data size threshold exceeded
        - Conditions satisfied

        Args:
            module: Module name
            function: Function name
            *args: Function arguments (for size estimation)
            **kwargs: Function keyword arguments

        Returns:
            True if should intercept this call
        """
        descriptor = self.get_descriptor(module, function)
        if not descriptor:
            return False

        # Check safety level
        if descriptor.safety_level == SafetyLevel.UNSAFE:
            return False

        # Estimate data size
        data_size = self._estimate_data_size(*args, **kwargs)

        # Check threshold
        if data_size < descriptor.min_data_size:
            return False

        # Check conditional criteria
        if descriptor.safety_level == SafetyLevel.CONDITIONAL:
            if not self._check_conditions(descriptor.conditions, *args, **kwargs):
                return False

        return True

    def _estimate_data_size(self, *args, **kwargs) -> int:
        """
        Estimate data size from function arguments.

        CRITICAL FIX (Nov 2025): Check order matters!
        - Pandas DataFrames have both __len__ and memory_usage
        - Must check memory_usage FIRST or DataFrames get wrong estimate
        - A 1M row DataFrame was estimated as 8MB instead of actual 160MB+

        Returns:
            Estimated size in bytes
        """
        total_size = 0

        for arg in args:
            try:
                # FIRST: Pandas DataFrame/Series (has memory_usage method)
                # Must check before __len__ because DataFrames also have __len__
                if hasattr(arg, 'memory_usage'):
                    mem_usage = arg.memory_usage(deep=True)
                    # Handle both DataFrame (returns Series) and Series (returns int)
                    if hasattr(mem_usage, 'sum'):
                        total_size += mem_usage.sum()
                    else:
                        total_size += mem_usage
                # SECOND: NumPy array (has nbytes attribute)
                elif hasattr(arg, 'nbytes'):
                    total_size += arg.nbytes
                # THIRD: List/tuple/other iterables
                elif hasattr(arg, '__len__'):
                    total_size += len(arg) * 8  # Rough estimate
            except Exception:
                pass

        return total_size

    def _check_conditions(self, conditions: Optional[Dict[str, Any]], *args, **kwargs) -> bool:
        """
        Check if conditional criteria are met.

        Args:
            conditions: Condition dict (e.g., {'min_rows': 10000})
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            True if conditions met
        """
        if not conditions:
            return True

        # Check min_rows for DataFrames
        if 'min_rows' in conditions:
            for arg in args:
                if hasattr(arg, 'shape'):  # NumPy or Pandas
                    if arg.shape[0] < conditions['min_rows']:
                        return False

        # Additional condition checks can be added here

        return True

    def get_all_numpy_functions(self) -> List[FunctionDescriptor]:
        """Get all registered NumPy functions."""
        return [d for d in self._registry.values() if d.module.startswith('numpy')]

    def get_all_pandas_functions(self) -> List[FunctionDescriptor]:
        """Get all registered Pandas functions."""
        return [d for d in self._registry.values() if d.module.startswith('pandas')]

    def get_all_sklearn_functions(self) -> List[FunctionDescriptor]:
        """Get all registered sklearn functions."""
        return [d for d in self._registry.values() if d.module.startswith('sklearn')]


# Global registry instance
_global_registry = None


def get_registry() -> InterceptionRegistry:
    """Get the global interception registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = InterceptionRegistry()
    return _global_registry
