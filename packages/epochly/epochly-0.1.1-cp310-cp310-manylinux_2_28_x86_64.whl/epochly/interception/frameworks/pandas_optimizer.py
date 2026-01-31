"""
Pandas-specific optimization strategies for Epochly Level 3.

Provides parallel implementations for:
- groupby: Split by group keys, aggregate in parallel, merge results
- merge: Hash partition, parallel join, combine results

Architecture Reference: planning/epochly-architecture-spec.md lines 3860-3872
Performance Target: 3x+ speedup for pandas groupby operations

Implementation based on mcp-reflect guidance (Nov 2025):
- Hash-based partitioning keeps same groups together
- Combinable aggregations (sum, count, min, max) merge directly
- Weighted aggregations (mean) use sum/count pairs
- Non-parallelizable aggregations (median) fall back to sequential
"""

from __future__ import annotations

import os
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from dataclasses import dataclass

from .partitioner import DataFramePartitioner, PartitionStrategy
from .merger import GroupResultMerger, AggregationStrategy

logger = logging.getLogger(__name__)


def _register_executor(executor: ProcessPoolExecutor) -> None:
    """
    Register ProcessPoolExecutor in global registry for cleanup.

    This ensures executors created by optimizers are properly shut down
    during pytest session teardown, preventing orphaned processes.
    """
    # Primary: Use centralized executor registry (orphan detection, unified cleanup)
    try:
        from epochly.core.executor_registry import register_executor
        register_executor(executor, name="pandas_optimizer_pool")
        logger.debug(f"Registered ProcessPoolExecutor in centralized registry")
        return
    except ImportError:
        pass  # Centralized registry not available

    # Fallback: Use local SIE registry for backwards compatibility
    try:
        from epochly.plugins.executor.sub_interpreter_executor import (
            _PROCESS_POOL_REGISTRY,
            _POOL_REGISTRY_LOCK
        )
        with _POOL_REGISTRY_LOCK:
            _PROCESS_POOL_REGISTRY.add(executor)
        logger.debug(f"Registered ProcessPoolExecutor in SIE registry (total: {len(_PROCESS_POOL_REGISTRY)})")
    except ImportError:
        pass  # Registry not available, cleanup will use gc fallback


# Worker function must be at module level for pickling
def _worker_groupby(partition_data: bytes, by: List[str], agg_spec: Dict) -> bytes:
    """
    Worker function for parallel groupby.

    Executes groupby on a single partition and returns pickled result.

    Args:
        partition_data: Pickled DataFrame partition
        by: Group columns
        agg_spec: Aggregation specification

    Returns:
        Pickled result DataFrame
    """
    import pickle
    import pandas as pd

    # Unpickle partition
    partition = pickle.loads(partition_data)

    # Execute groupby
    result = partition.groupby(by, observed=True).agg(agg_spec)

    # Pickle result
    return pickle.dumps(result)


def _worker_merge(
    left_data: bytes,
    right_data: bytes,
    on: Optional[List[str]],
    how: str,
    left_on: Optional[List[str]],
    right_on: Optional[List[str]]
) -> bytes:
    """
    Worker function for parallel merge.

    Args:
        left_data: Pickled left DataFrame
        right_data: Pickled right DataFrame
        on: Common columns
        how: Merge type
        left_on: Left join columns
        right_on: Right join columns

    Returns:
        Pickled result DataFrame
    """
    import pickle
    import pandas as pd

    left = pickle.loads(left_data)
    right = pickle.loads(right_data)

    result = pd.merge(
        left, right,
        on=on, how=how,
        left_on=left_on, right_on=right_on
    )

    return pickle.dumps(result)


@dataclass
class ParallelizationDecision:
    """Result of parallelization benefit analysis."""
    should_parallelize: bool
    reason: str
    estimated_speedup: float
    estimated_overhead_ms: float
    num_workers: int


class ParallelizationBenefitEstimator:
    """
    Estimates whether parallelization will provide speedup.

    Accounts for:
    - Process spawn overhead (~20ms per worker)
    - Data serialization overhead (~5ms per MB)
    - Result merging overhead (~2ms per MB)
    - Actual computation time

    Based on empirical measurements from Nov 2025 investigation.
    """

    # Measured overheads (ProcessPoolExecutor on macOS M-series)
    # CRITICAL: These values based on Nov 2025 benchmarks showing pandas
    # processes ~80M rows/sec for simple agg, so parallelization overhead
    # must be < sequential time / 3 to achieve 3x speedup
    PROCESS_SPAWN_MS = 400.0  # Pool creation + worker init (first call)
    SERIALIZATION_OVERHEAD_PER_MB = 10.0  # ms per MB for pickle (roundtrip)
    MERGE_OVERHEAD_PER_MB = 5.0  # ms per MB for result combination
    MIN_SPEEDUP_THRESHOLD = 1.5  # Minimum expected speedup to parallelize

    # Thresholds for parallelization decisions
    # Pandas groupby.agg is ~80M rows/sec, so we need huge data
    # to overcome ~500ms parallelization overhead
    MIN_ROWS = 50_000_000  # 50M rows minimum (sequential ~625ms)
    MIN_DATA_SIZE_MB = 500.0  # 500MB minimum data size

    @classmethod
    def should_parallelize_groupby(
        cls,
        df,  # pd.DataFrame
        by: Union[str, List[str]],
        agg_spec: Dict,
        num_workers: int
    ) -> ParallelizationDecision:
        """
        Decide if groupby parallelization is beneficial.

        Args:
            df: DataFrame to process
            by: Group columns
            agg_spec: Aggregation specification
            num_workers: Available workers

        Returns:
            ParallelizationDecision with recommendation
        """
        # Calculate data characteristics
        num_rows = len(df)
        data_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

        # Quick rejection: too small
        if num_rows < cls.MIN_ROWS:
            return ParallelizationDecision(
                should_parallelize=False,
                reason=f"DataFrame too small ({num_rows} rows < {cls.MIN_ROWS})",
                estimated_speedup=1.0,
                estimated_overhead_ms=0,
                num_workers=0
            )

        if data_size_mb < cls.MIN_DATA_SIZE_MB:
            return ParallelizationDecision(
                should_parallelize=False,
                reason=f"Data too small ({data_size_mb:.1f}MB < {cls.MIN_DATA_SIZE_MB}MB)",
                estimated_speedup=1.0,
                estimated_overhead_ms=0,
                num_workers=0
            )

        # Estimate sequential time (rough heuristic)
        # Groupby typically processes ~1M rows/sec
        estimated_sequential_ms = (num_rows / 1_000_000) * 1000

        # Estimate parallel overhead
        # Serialization: data goes to workers + results come back
        serialization_overhead = data_size_mb * cls.SERIALIZATION_OVERHEAD_PER_MB * 2

        # Result merging
        result_size_mb = data_size_mb * 0.1  # Assume 10% size reduction from aggregation
        merge_overhead = result_size_mb * cls.MERGE_OVERHEAD_PER_MB

        total_overhead_ms = serialization_overhead + merge_overhead

        # Estimate parallel time
        # Ideal parallelization: sequential_time / num_workers
        # With overhead: (sequential_time / num_workers) + overhead
        estimated_parallel_ms = (estimated_sequential_ms / num_workers) + total_overhead_ms

        # Calculate expected speedup
        estimated_speedup = estimated_sequential_ms / max(1, estimated_parallel_ms)

        # Decision
        should_parallelize = estimated_speedup >= cls.MIN_SPEEDUP_THRESHOLD

        if should_parallelize:
            reason = (
                f"Expected {estimated_speedup:.1f}x speedup "
                f"({estimated_sequential_ms:.0f}ms -> {estimated_parallel_ms:.0f}ms)"
            )
        else:
            reason = (
                f"Overhead ({total_overhead_ms:.0f}ms) exceeds benefit "
                f"(estimated {estimated_speedup:.1f}x < {cls.MIN_SPEEDUP_THRESHOLD}x threshold)"
            )

        return ParallelizationDecision(
            should_parallelize=should_parallelize,
            reason=reason,
            estimated_speedup=estimated_speedup,
            estimated_overhead_ms=total_overhead_ms,
            num_workers=num_workers if should_parallelize else 0
        )


class PandasGroupbyOptimizer:
    """
    Parallel groupby implementation for Epochly Level 3.

    Strategy:
    1. Estimate if parallelization is beneficial
    2. Partition DataFrame by group keys (same groups stay together)
    3. Submit partitions to ProcessPoolExecutor
    4. Merge partial results using appropriate strategy per aggregation

    Performance target: 3x+ speedup for suitable workloads
    """

    def __init__(self, num_workers: int = None):
        """
        Args:
            num_workers: Number of workers (default: cpu_count - 1)
        """
        if num_workers is None:
            num_workers = max(1, os.cpu_count() - 1)
        self.num_workers = num_workers
        self.partitioner = DataFramePartitioner(num_workers)
        self.merger = GroupResultMerger()
        self._executor = None

    def _get_executor(self) -> ProcessPoolExecutor:
        """Get or create ProcessPoolExecutor."""
        if self._executor is None:
            self._executor = ProcessPoolExecutor(max_workers=self.num_workers)
            _register_executor(self._executor)
        return self._executor

    def optimize_groupby(
        self,
        df,  # pd.DataFrame
        by: Union[str, List[str]],
        agg_spec: Dict[str, Union[str, List[str], Callable]]
    ):
        """
        Execute groupby with parallel optimization.

        Args:
            df: DataFrame to process
            by: Group column(s)
            agg_spec: Aggregation specification (e.g., {'value': ['sum', 'mean']})

        Returns:
            Aggregated DataFrame (same format as df.groupby(by).agg(agg_spec))
        """
        import pickle
        import pandas as pd

        # Normalize inputs
        if isinstance(by, str):
            by = [by]
        if isinstance(agg_spec, str):
            agg_spec = {col: [agg_spec] for col in df.columns if col not in by}

        # Check if parallelization is beneficial
        decision = ParallelizationBenefitEstimator.should_parallelize_groupby(
            df, by, agg_spec, self.num_workers
        )

        logger.debug(f"Parallelization decision: {decision.reason}")

        if not decision.should_parallelize:
            # Fall back to sequential pandas
            logger.debug("Using sequential groupby")
            return df.groupby(by, observed=True).agg(agg_spec)

        # Partition DataFrame
        partitions, strategy = self.partitioner.partition_for_groupby(df, by)

        logger.debug(
            f"Created {len(partitions)} partitions "
            f"(method={strategy.partition_method}, ~{strategy.estimated_groups_per_partition} groups/partition)"
        )

        if len(partitions) <= 1:
            # Not enough partitions, fall back to sequential
            return df.groupby(by, observed=True).agg(agg_spec)

        # Prepare for parallel execution
        executor = self._get_executor()

        # Pickle partitions
        partition_data = [pickle.dumps(p) for p in partitions]

        # Submit to workers
        futures = [
            executor.submit(_worker_groupby, pdata, by, agg_spec)
            for pdata in partition_data
        ]

        # Collect results
        partial_results = []
        for future in as_completed(futures):
            try:
                result_data = future.result()
                result = pickle.loads(result_data)
                partial_results.append(result)
            except Exception as e:
                logger.error(f"Worker failed: {e}")
                # Fall back to sequential on any failure
                logger.warning("Falling back to sequential groupby due to worker failure")
                return df.groupby(by, observed=True).agg(agg_spec)

        # Merge results
        try:
            merged = self.merger.merge_groupby_results(partial_results, by, agg_spec)
            return merged
        except Exception as e:
            logger.error(f"Merge failed: {e}")
            # Fall back to sequential on merge failure
            logger.warning("Falling back to sequential groupby due to merge failure")
            return df.groupby(by, observed=True).agg(agg_spec)

    def shutdown(self):
        """Shutdown the executor pool."""
        if self._executor is not None:
            self._executor.shutdown(wait=True)
            self._executor = None


class PandasMergeOptimizer:
    """
    Parallel merge implementation for Epochly Level 3.

    Strategy for hash join:
    1. Partition both DataFrames by join key
    2. Match partitions with same key hash
    3. Execute merge on each partition pair in parallel
    4. Concatenate results

    Note: Only effective for large DataFrames (>1M rows each)
    """

    def __init__(self, num_workers: int = None):
        """
        Args:
            num_workers: Number of workers (default: cpu_count - 1)
        """
        if num_workers is None:
            num_workers = max(1, os.cpu_count() - 1)
        self.num_workers = num_workers
        self.partitioner = DataFramePartitioner(num_workers)
        self._executor = None

    def _get_executor(self) -> ProcessPoolExecutor:
        """Get or create ProcessPoolExecutor."""
        if self._executor is None:
            self._executor = ProcessPoolExecutor(max_workers=self.num_workers)
            _register_executor(self._executor)
        return self._executor

    def optimize_merge(
        self,
        left,  # pd.DataFrame
        right,  # pd.DataFrame
        on: Optional[Union[str, List[str]]] = None,
        how: str = 'inner',
        left_on: Optional[Union[str, List[str]]] = None,
        right_on: Optional[Union[str, List[str]]] = None
    ):
        """
        Execute merge with parallel optimization.

        Args:
            left: Left DataFrame
            right: Right DataFrame
            on: Common join columns
            how: Merge type ('inner', 'left', 'right', 'outer')
            left_on: Left join columns
            right_on: Right join columns

        Returns:
            Merged DataFrame
        """
        import pickle
        import pandas as pd

        # Determine join columns
        if on is not None:
            if isinstance(on, str):
                on = [on]
            left_cols = on
            right_cols = on
        elif left_on is not None and right_on is not None:
            if isinstance(left_on, str):
                left_on = [left_on]
            if isinstance(right_on, str):
                right_on = [right_on]
            left_cols = left_on
            right_cols = right_on
        else:
            # Can't parallelize without explicit join columns
            return pd.merge(left, right, on=on, how=how, left_on=left_on, right_on=right_on)

        # Check if parallelization is beneficial
        total_rows = len(left) + len(right)
        total_size_mb = (
            left.memory_usage(deep=True).sum() +
            right.memory_usage(deep=True).sum()
        ) / (1024 * 1024)

        if total_rows < 200_000 or total_size_mb < 20:
            # Too small for parallelization
            logger.debug("DataFrames too small for parallel merge")
            return pd.merge(left, right, on=on, how=how, left_on=left_on, right_on=right_on)

        # Partition both DataFrames by join key
        left_partitions, _ = self.partitioner.partition_for_groupby(left, left_cols)
        right_partitions, _ = self.partitioner.partition_for_groupby(right, right_cols)

        if len(left_partitions) <= 1 or len(right_partitions) <= 1:
            # Not enough partitions
            return pd.merge(left, right, on=on, how=how, left_on=left_on, right_on=right_on)

        # For hash join, we need to match partitions by hash
        # This is complex for non-inner joins, so we only parallelize inner joins
        if how != 'inner':
            logger.debug(f"Parallel merge only supports 'inner' join, got '{how}'")
            return pd.merge(left, right, on=on, how=how, left_on=left_on, right_on=right_on)

        # Execute parallel merge
        executor = self._get_executor()

        # For inner join, we can merge partition pairs independently
        # (same hash = same key values)
        num_partitions = min(len(left_partitions), len(right_partitions))
        futures = []

        for i in range(num_partitions):
            left_data = pickle.dumps(left_partitions[i] if i < len(left_partitions) else pd.DataFrame())
            right_data = pickle.dumps(right_partitions[i] if i < len(right_partitions) else pd.DataFrame())

            future = executor.submit(
                _worker_merge,
                left_data, right_data,
                on, how, left_on, right_on
            )
            futures.append(future)

        # Collect results
        results = []
        for future in as_completed(futures):
            try:
                result_data = future.result()
                result = pickle.loads(result_data)
                if len(result) > 0:
                    results.append(result)
            except Exception as e:
                logger.error(f"Merge worker failed: {e}")
                # Fall back to sequential
                return pd.merge(left, right, on=on, how=how, left_on=left_on, right_on=right_on)

        if not results:
            return pd.DataFrame()

        # Concatenate results
        return pd.concat(results, ignore_index=True)

    def shutdown(self):
        """Shutdown the executor pool."""
        if self._executor is not None:
            self._executor.shutdown(wait=True)
            self._executor = None


# Worker function for apply - must be at module level for pickling
def _worker_apply(partition_data: bytes, func_bytes: bytes, by: list, column: str) -> bytes:
    """
    Worker function for parallel apply.

    Executes apply on a single partition with a custom Python function.
    This is where parallelization provides real speedups because Python
    functions are GIL-bound in the main process.

    Args:
        partition_data: Pickled DataFrame partition
        func_bytes: Cloudpickled function to apply
        by: Group columns
        column: Column to apply function to (or None for whole group)

    Returns:
        Pickled result Series/DataFrame
    """
    import pickle
    import pandas as pd
    try:
        import cloudpickle
        use_cloudpickle = True
    except ImportError:
        use_cloudpickle = False

    # Unpickle partition (standard pickle for DataFrames)
    partition = pickle.loads(partition_data)
    # Unpickle function (cloudpickle for lambdas/closures)
    if use_cloudpickle:
        func = cloudpickle.loads(func_bytes)
    else:
        func = pickle.loads(func_bytes)

    # Execute groupby.apply
    # FutureWarning fix: include_groups=False excludes grouping columns from operation
    if column:
        result = partition.groupby(by, observed=True)[column].apply(func)
    else:
        result = partition.groupby(by, observed=True).apply(func, include_groups=False)

    # Pickle result
    return pickle.dumps(result)


class PandasApplyOptimizer:
    """
    Parallel apply implementation for custom Python functions.

    CRITICAL: This is where parallelization ACTUALLY helps!

    Unlike built-in aggregations (sum, mean, max) which are C-optimized,
    custom Python functions are GIL-bound. Running them in separate processes
    via ProcessPoolExecutor bypasses the GIL and achieves real parallelism.

    Strategy:
    1. Partition DataFrame by group keys (same groups stay together)
    2. Submit partitions to ProcessPoolExecutor
    3. Each worker runs groupby.apply with the custom function
    4. Concatenate results (no complex merging needed)

    Performance target: 3-10x speedup for suitable workloads
    """

    # Thresholds for apply parallelization - MUCH lower than built-in agg
    # because custom Python functions are slow (GIL-bound)
    MIN_ROWS = 100_000  # 100K rows
    MIN_GROUPS = 10  # Need enough groups to parallelize
    MIN_ESTIMATED_SEQUENTIAL_MS = 500  # Need at least 500ms sequential time

    def __init__(self, num_workers: int = None):
        """
        Args:
            num_workers: Number of workers (default: cpu_count - 1)
        """
        if num_workers is None:
            num_workers = max(1, os.cpu_count() - 1)
        self.num_workers = num_workers
        self.partitioner = DataFramePartitioner(num_workers)
        self._executor = None

    def _get_executor(self) -> ProcessPoolExecutor:
        """Get or create ProcessPoolExecutor."""
        if self._executor is None:
            self._executor = ProcessPoolExecutor(max_workers=self.num_workers)
            _register_executor(self._executor)
        return self._executor

    def should_parallelize_apply(
        self,
        df,  # pd.DataFrame
        by: Union[str, List[str]],
        func: Callable
    ) -> ParallelizationDecision:
        """
        Decide if apply parallelization is beneficial.

        For custom Python functions, thresholds are MUCH lower than built-in
        aggregations because:
        1. Python functions are slow (GIL-bound, ~10-100x slower than C)
        2. Parallelization overhead is amortized across slow compute
        3. Real speedups are achievable

        Args:
            df: DataFrame to process
            by: Group column(s)
            func: Custom function to apply

        Returns:
            ParallelizationDecision
        """
        num_rows = len(df)

        # Quick rejection: too small
        if num_rows < self.MIN_ROWS:
            return ParallelizationDecision(
                should_parallelize=False,
                reason=f"DataFrame too small ({num_rows} rows < {self.MIN_ROWS})",
                estimated_speedup=1.0,
                estimated_overhead_ms=0,
                num_workers=0
            )

        # Estimate number of groups
        if isinstance(by, str):
            by = [by]
        if len(by) == 1:
            n_groups = df[by[0]].nunique()
        else:
            n_groups = df[by].drop_duplicates().shape[0]

        if n_groups < self.MIN_GROUPS:
            return ParallelizationDecision(
                should_parallelize=False,
                reason=f"Too few groups ({n_groups} < {self.MIN_GROUPS})",
                estimated_speedup=1.0,
                estimated_overhead_ms=0,
                num_workers=0
            )

        # Estimate sequential time (custom Python is ~1000x slower than C)
        # Assume ~10K rows/sec for Python functions
        estimated_sequential_ms = (num_rows / 10_000) * 1000

        if estimated_sequential_ms < self.MIN_ESTIMATED_SEQUENTIAL_MS:
            return ParallelizationDecision(
                should_parallelize=False,
                reason=f"Estimated time too short ({estimated_sequential_ms:.0f}ms < {self.MIN_ESTIMATED_SEQUENTIAL_MS}ms)",
                estimated_speedup=1.0,
                estimated_overhead_ms=0,
                num_workers=0
            )

        # Estimate parallel overhead (lower than built-in agg because compute dominates)
        data_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        overhead_ms = 200 + (data_size_mb * 5)  # Pool + serialization

        # Estimate parallel time
        effective_workers = min(self.num_workers, n_groups)
        estimated_parallel_ms = (estimated_sequential_ms / effective_workers) + overhead_ms

        # Calculate expected speedup
        estimated_speedup = estimated_sequential_ms / max(1, estimated_parallel_ms)

        should_parallelize = estimated_speedup >= 1.5

        if should_parallelize:
            reason = (
                f"Expected {estimated_speedup:.1f}x speedup with {effective_workers} workers "
                f"({estimated_sequential_ms:.0f}ms -> {estimated_parallel_ms:.0f}ms)"
            )
        else:
            reason = f"Estimated {estimated_speedup:.1f}x < 1.5x threshold"

        return ParallelizationDecision(
            should_parallelize=should_parallelize,
            reason=reason,
            estimated_speedup=estimated_speedup,
            estimated_overhead_ms=overhead_ms,
            num_workers=effective_workers if should_parallelize else 0
        )

    def optimize_apply(
        self,
        df,  # pd.DataFrame
        by: Union[str, List[str]],
        func: Callable,
        column: Optional[str] = None
    ):
        """
        Execute groupby.apply with parallel optimization.

        Args:
            df: DataFrame to process
            by: Group column(s)
            func: Custom function to apply
            column: Optional column to apply to (None = apply to whole group)

        Returns:
            Result Series/DataFrame (same format as df.groupby(by)[column].apply(func))
        """
        import pickle
        import pandas as pd

        # Normalize inputs
        if isinstance(by, str):
            by = [by]

        # Check if parallelization is beneficial
        decision = self.should_parallelize_apply(df, by, func)

        logger.debug(f"Apply parallelization decision: {decision.reason}")

        if not decision.should_parallelize:
            # Fall back to sequential pandas
            logger.debug("Using sequential apply")
            if column:
                return df.groupby(by, observed=True)[column].apply(func)
            else:
                return df.groupby(by, observed=True).apply(func)

        # Partition DataFrame
        partitions, strategy = self.partitioner.partition_for_groupby(df, by)

        logger.debug(
            f"Created {len(partitions)} partitions for apply "
            f"(method={strategy.partition_method})"
        )

        if len(partitions) <= 1:
            # Not enough partitions, fall back to sequential
            if column:
                return df.groupby(by, observed=True)[column].apply(func)
            else:
                return df.groupby(by, observed=True).apply(func)

        # Prepare for parallel execution
        executor = self._get_executor()

        # Pickle partitions and function
        # Use cloudpickle for function (supports lambdas, closures, local functions)
        partition_data = [pickle.dumps(p) for p in partitions]
        try:
            import cloudpickle
            func_bytes = cloudpickle.dumps(func)
        except ImportError:
            func_bytes = pickle.dumps(func)

        # Submit to workers
        futures = [
            executor.submit(_worker_apply, pdata, func_bytes, by, column)
            for pdata in partition_data
        ]

        # Collect results
        partial_results = []
        for future in as_completed(futures):
            try:
                result_data = future.result()
                result = pickle.loads(result_data)
                partial_results.append(result)
            except Exception as e:
                logger.error(f"Apply worker failed: {e}")
                # Fall back to sequential on any failure
                logger.warning("Falling back to sequential apply due to worker failure")
                if column:
                    return df.groupby(by, observed=True)[column].apply(func)
                else:
                    return df.groupby(by, observed=True).apply(func)

        # Merge results - just concat since each group is in one partition
        try:
            merged = pd.concat(partial_results)
            # Sort by index to match pandas behavior
            merged = merged.sort_index()
            return merged
        except Exception as e:
            logger.error(f"Apply merge failed: {e}")
            # Fall back to sequential on merge failure
            logger.warning("Falling back to sequential apply due to merge failure")
            if column:
                return df.groupby(by, observed=True)[column].apply(func)
            else:
                return df.groupby(by, observed=True).apply(func)

    def shutdown(self):
        """Shutdown the executor pool."""
        if self._executor is not None:
            self._executor.shutdown(wait=True)
            self._executor = None


# Convenience function for external use
def should_parallelize_pandas_op(
    df,
    operation: str,
    **kwargs
) -> ParallelizationDecision:
    """
    Decide if a pandas operation should be parallelized.

    Args:
        df: DataFrame
        operation: Operation name ('groupby', 'merge', 'apply')
        **kwargs: Operation-specific arguments

    Returns:
        ParallelizationDecision
    """
    num_workers = max(1, os.cpu_count() - 1)

    if operation == 'groupby':
        return ParallelizationBenefitEstimator.should_parallelize_groupby(
            df,
            kwargs.get('by', []),
            kwargs.get('agg', {}),
            num_workers
        )
    else:
        # Default: check basic thresholds
        num_rows = len(df)
        data_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

        should = num_rows >= 100_000 and data_size_mb >= 10

        return ParallelizationDecision(
            should_parallelize=should,
            reason=f"{'Meets' if should else 'Below'} size thresholds",
            estimated_speedup=2.0 if should else 1.0,
            estimated_overhead_ms=50 if should else 0,
            num_workers=num_workers if should else 0
        )
