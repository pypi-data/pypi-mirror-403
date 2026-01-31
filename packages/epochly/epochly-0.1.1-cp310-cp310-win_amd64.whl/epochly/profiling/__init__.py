"""
Epochly Auto-Profiling System

Implements automatic profiling for hot loop detection and JIT compilation
without requiring code changes from users (zero-configuration promise).

Product Vision (epochly-architecture-spec.md:179):
> "The profiler marks any loop or function exceeding 10 ms CPU, slices data,
> dispatches to workers and wraps with numba.njit"

Architecture:
1. sys.monitoring for Python 3.12+ (low overhead)
2. sys.settrace fallback for Python 3.8-3.11
3. Hot loop detection (>10ms CPU time threshold)
4. Automatic JIT compilation with numba.njit
5. Automatic data slicing for parallel dispatch

Author: Epochly Development Team
Date: November 17, 2025
"""

from .auto_profiler import AutoProfiler, HotLoopInfo
from .loop_detector import LoopDetector, LoopStatistics
from .executor_adapter import ExecutorAdapter, UnifiedResult, create_executor_adapter
from .batch_dispatcher import BatchDispatcher, create_batch_dispatcher
from .scheduling_profiler import (
    SchedulingProfiler,
    TaskLatencyBreakdown,
    SchedulingMetrics,
    ExecutorType,
    TaskProfilingContext,
    get_scheduling_profiler,
    reset_scheduling_profiler,
    profile_executor_submit,
)
from .adaptive_executor import (
    AdaptiveExecutorSelector,
    WarmWorkerPool,
    TaskCharacteristics,
    ExecutorDecision,
    get_adaptive_selector,
)

# Import extensions to enable advanced features
try:
    from . import batch_dispatcher_extension
except ImportError:
    pass

try:
    from . import runtime_loop_transformer_while_support
except ImportError:
    pass

__all__ = [
    # Auto-profiling
    'AutoProfiler',
    'HotLoopInfo',
    'LoopDetector',
    'LoopStatistics',
    # Executor adaptation
    'ExecutorAdapter',
    'UnifiedResult',
    'create_executor_adapter',
    # Batch dispatch
    'BatchDispatcher',
    'create_batch_dispatcher',
    # Scheduling profiler (November 2025)
    'SchedulingProfiler',
    'TaskLatencyBreakdown',
    'SchedulingMetrics',
    'ExecutorType',
    'TaskProfilingContext',
    'get_scheduling_profiler',
    'reset_scheduling_profiler',
    'profile_executor_submit',
    # Adaptive executor (November 2025)
    'AdaptiveExecutorSelector',
    'WarmWorkerPool',
    'TaskCharacteristics',
    'ExecutorDecision',
    'get_adaptive_selector',
]