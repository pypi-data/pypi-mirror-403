"""
Framework-specific optimization strategies for Epochly Level 3.

This module provides intelligent parallelization for framework operations:
- pandas: groupby, merge, apply optimizations (3-5x speedup for GIL-bound)
- numpy: GIL-bound ops only (vectorize, apply_along_axis with Python funcs)
- sklearn: auto-configure n_jobs=-1 (no interception, uses native parallelization)
- pytorch: GPU coordination via DLPack with mandatory synchronization (Tier 2)
- tensorflow: Detection-only (Tier 1) - too risky for automatic coordination

Architecture Reference: planning/epochly-architecture-spec.md lines 3860-3872
Expected: 3x+ speedup for pandas groupby operations
         7x+ speedup for numpy.vectorize with large Python functions

CRITICAL INSIGHT (Nov 2025 mcp-reflect research):
- Standard NumPy/sklearn ops CANNOT benefit from re-parallelization (already optimized)
- GIL-bound NumPy ops (vectorize, apply_along_axis with Python funcs) CAN benefit
- sklearn should auto-configure n_jobs=-1 instead of intercepting operations
- PyTorch DLPack is SAFE with mandatory sync gates (Jan 2026)
- TensorFlow is DETECT-ONLY - too risky for automatic coordination (Jan 2026)
"""

from .pandas_optimizer import (
    PandasGroupbyOptimizer,
    PandasMergeOptimizer,
    PandasApplyOptimizer,
    should_parallelize_pandas_op,
)
from .partitioner import DataFramePartitioner, PartitionStrategy
from .merger import GroupResultMerger, AggregationStrategy
from .numpy_optimizer import (
    NumpyGILOptimizer,
    VectorizeDecision,
    should_parallelize_numpy_gil_op,
)
from .sklearn_optimizer import (
    SklearnAutoConfigurator,
    auto_configure_sklearn,
    get_sklearn_configurator,
    NJOBS_SUPPORTED_ESTIMATORS,
)
from .pytorch_optimizer import (
    PyTorchGPUCoordinator,
    get_pytorch_coordinator,
    is_pytorch_active,
)
from .tensorflow_optimizer import (
    TensorFlowDetector,
    get_tensorflow_detector,
    is_tensorflow_active,
)

__all__ = [
    # Pandas optimizers
    'PandasGroupbyOptimizer',
    'PandasMergeOptimizer',
    'PandasApplyOptimizer',
    'should_parallelize_pandas_op',
    # Pandas helpers
    'DataFramePartitioner',
    'PartitionStrategy',
    'GroupResultMerger',
    'AggregationStrategy',
    # NumPy GIL-bound optimizer (Nov 2025)
    'NumpyGILOptimizer',
    'VectorizeDecision',
    'should_parallelize_numpy_gil_op',
    # sklearn auto-configurator (Nov 2025)
    'SklearnAutoConfigurator',
    'auto_configure_sklearn',
    'get_sklearn_configurator',
    'NJOBS_SUPPORTED_ESTIMATORS',
    # PyTorch GPU coordinator (Jan 2026)
    'PyTorchGPUCoordinator',
    'get_pytorch_coordinator',
    'is_pytorch_active',
    # TensorFlow detector (Jan 2026)
    'TensorFlowDetector',
    'get_tensorflow_detector',
    'is_tensorflow_active',
]
