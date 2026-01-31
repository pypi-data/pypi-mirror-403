"""
DataFrame Partitioner for parallel pandas operations.

Provides intelligent partitioning strategies that ensure:
1. All rows for the same group key go to the same partition
2. Load is balanced across workers
3. Overhead is minimized for small datasets

Reference: Architecture spec expects 3x+ speedup for pandas groupby
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class PartitionStrategy:
    """Metadata about how DataFrame was partitioned."""
    num_partitions: int
    partition_method: str  # 'hash', 'group', 'none'
    group_columns: List[str]
    estimated_groups_per_partition: int
    total_rows: int
    data_size_mb: float


class DataFramePartitioner:
    """
    Partitions DataFrames for parallel groupby operations.

    Strategy:
    1. Hash group keys to distribute evenly across partitions
    2. Keep all rows for same group in same partition (critical!)
    3. Balance partition sizes for load distribution

    Performance targets:
    - Partitioning overhead: <50ms for 10M rows
    - Load imbalance: <20% variance across partitions
    """

    # Thresholds for parallelization decisions
    MIN_ROWS_FOR_PARALLEL = 100_000  # Minimum rows to consider parallelization
    MIN_PARTITION_SIZE = 10_000  # Minimum rows per partition

    def __init__(self, num_workers: int = None):
        """
        Args:
            num_workers: Number of worker processes (default: cpu_count - 1)
        """
        if num_workers is None:
            num_workers = max(1, os.cpu_count() - 1)
        self.num_workers = num_workers

    def partition_for_groupby(
        self,
        df,  # pd.DataFrame - lazy import
        by: Union[str, List[str]],
        min_partition_size: int = None
    ) -> Tuple[List, PartitionStrategy]:
        """
        Partition DataFrame for parallel groupby.

        CRITICAL: All rows with same group key MUST go to same partition!

        Args:
            df: DataFrame to partition
            by: Group column(s)
            min_partition_size: Minimum rows per partition (default: MIN_PARTITION_SIZE)

        Returns:
            (partitions, strategy_metadata)
        """
        import pandas as pd
        import numpy as np

        if min_partition_size is None:
            min_partition_size = self.MIN_PARTITION_SIZE

        # Normalize by to list
        if isinstance(by, str):
            by = [by]

        # Calculate data size
        data_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        total_rows = len(df)

        # Check if parallelization is worthwhile
        if total_rows < self.MIN_ROWS_FOR_PARALLEL:
            logger.debug(f"DataFrame too small ({total_rows} rows) for parallelization")
            return [df], PartitionStrategy(
                num_partitions=1,
                partition_method='none',
                group_columns=by,
                estimated_groups_per_partition=self._estimate_group_cardinality(df, by),
                total_rows=total_rows,
                data_size_mb=data_size_mb
            )

        # Estimate group cardinality
        group_cardinality = self._estimate_group_cardinality(df, by)

        # Determine optimal partition count
        optimal_partitions = self._calculate_optimal_partitions(
            total_rows, group_cardinality, min_partition_size
        )

        logger.debug(
            f"Partitioning {total_rows} rows with ~{group_cardinality} groups "
            f"into {optimal_partitions} partitions"
        )

        # Choose partitioning method
        if group_cardinality > optimal_partitions * 2:
            # High cardinality - hash partitioning works well
            partitions = self._hash_partition(df, by, optimal_partitions)
            method = 'hash'
        elif group_cardinality < optimal_partitions:
            # Low cardinality - partition by group directly
            partitions = self._group_partition(df, by, optimal_partitions)
            method = 'group'
        else:
            # Medium cardinality - hash partitioning
            partitions = self._hash_partition(df, by, optimal_partitions)
            method = 'hash'

        # Filter empty partitions
        partitions = [p for p in partitions if len(p) > 0]

        strategy = PartitionStrategy(
            num_partitions=len(partitions),
            partition_method=method,
            group_columns=by,
            estimated_groups_per_partition=group_cardinality // max(1, len(partitions)),
            total_rows=total_rows,
            data_size_mb=data_size_mb
        )

        logger.debug(f"Created {len(partitions)} partitions using {method} method")

        return partitions, strategy

    def _estimate_group_cardinality(self, df, by: List[str]) -> int:
        """
        Estimate number of unique groups.

        For large DataFrames, sampling is faster than full nunique().
        """
        import numpy as np

        if len(df) > 1_000_000:
            # Sample 10% for estimation (max 100k rows)
            sample_size = min(100_000, len(df) // 10)
            sample = df.sample(n=sample_size, random_state=42)
            if len(by) == 1:
                estimated = sample[by[0]].nunique()
            else:
                estimated = sample[by].drop_duplicates().shape[0]
            # Scale up with correction factor (sampling underestimates)
            return int(estimated * (len(df) / sample_size) * 0.8)
        else:
            # Small enough for exact count
            if len(by) == 1:
                return df[by[0]].nunique()
            return df[by].drop_duplicates().shape[0]

    def _calculate_optimal_partitions(
        self,
        total_rows: int,
        group_cardinality: int,
        min_partition_size: int
    ) -> int:
        """Calculate optimal number of partitions."""
        # Rule 1: At least 2x chunks per worker for load balancing
        min_partitions = self.num_workers

        # Rule 2: Each partition >= min_partition_size
        max_by_size = total_rows // min_partition_size

        # Rule 3: Don't exceed number of groups (wasteful)
        max_by_groups = max(1, group_cardinality)

        # Rule 4: Target ~100ms processing per partition
        # Assume ~1M rows/sec groupby speed
        target_by_time = max(1, total_rows // 100_000)

        # Combine rules
        optimal = min(max_by_size, max_by_groups, target_by_time)
        optimal = max(min_partitions, optimal)

        # Cap at reasonable maximum
        return min(optimal, self.num_workers * 4)

    def _hash_partition(
        self,
        df,
        by: List[str],
        num_partitions: int
    ) -> List:
        """
        Hash-based partitioning ensuring same groups stay together.
        """
        import pandas as pd

        # Create composite hash of group columns
        if len(by) == 1:
            group_hash = pd.util.hash_pandas_object(df[by[0]], index=False)
        else:
            # Create tuple string for hashing
            group_key = df[by].astype(str).agg('_'.join, axis=1)
            group_hash = pd.util.hash_pandas_object(group_key, index=False)

        # Assign partition IDs
        partition_ids = group_hash % num_partitions

        # Split into partitions
        partitions = []
        for i in range(num_partitions):
            mask = partition_ids == i
            if mask.any():
                partition_df = df.loc[mask].copy()
                partitions.append(partition_df)

        return partitions

    def _group_partition(
        self,
        df,
        by: List[str],
        num_partitions: int
    ) -> List:
        """
        Partition by assigning each unique group to a partition.

        Used when number of groups < number of workers.
        """
        import numpy as np

        # Get unique groups
        if len(by) == 1:
            unique_groups = df[[by[0]]].drop_duplicates().copy()
        else:
            unique_groups = df[by].drop_duplicates().copy()

        # Assign groups to partitions in round-robin
        unique_groups['_partition_id'] = np.arange(len(unique_groups)) % num_partitions

        # Merge back to get partition assignment
        df_with_partition = df.merge(unique_groups, on=by, how='left')

        # Split by partition
        partitions = []
        for i in range(num_partitions):
            mask = df_with_partition['_partition_id'] == i
            if mask.any():
                partition_df = df_with_partition.loc[mask].drop('_partition_id', axis=1).copy()
                partitions.append(partition_df)

        return partitions
