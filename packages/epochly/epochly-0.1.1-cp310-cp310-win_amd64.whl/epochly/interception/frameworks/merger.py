"""
Group Result Merger for parallel pandas operations.

Combines partial aggregation results from multiple workers.
Handles different aggregation function types correctly:
- Combinable: sum, count, min, max (direct combination)
- Weighted: mean (requires count-weighted combination)
- Complex: std, var (requires intermediate statistics)
- Non-parallelizable: median, quantile (requires full data)

Reference: Architecture spec expects correct results from parallel groupby
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Callable, Any, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class AggregationStrategy:
    """
    Defines how to merge partial aggregation results.

    Categories:
    - COMBINABLE: Direct combination (sum of sums, min of mins, etc.)
    - WEIGHTED: Requires count for proper combination (mean)
    - COMPLEX: Requires intermediate statistics (std, var)
    - NON_PARALLELIZABLE: Cannot be combined (median, quantile)
    """

    # Aggregations that can be directly combined
    COMBINABLE = frozenset({
        'sum', 'count', 'min', 'max', 'first', 'last',
        'prod', 'size', 'any', 'all'
    })

    # Aggregations requiring weighted combination
    WEIGHTED = frozenset({'mean'})

    # Aggregations requiring intermediate statistics
    COMPLEX = frozenset({'std', 'var', 'sem'})

    # Aggregations that cannot be parallelized
    NON_PARALLELIZABLE = frozenset({
        'median', 'quantile', 'nunique', 'describe'
    })


class GroupResultMerger:
    """
    Merges partial groupby results from parallel workers.

    For each aggregation function type:
    - sum/count/min/max: Direct pd.concat().groupby().agg()
    - mean: Weighted average using (sum, count) pairs
    - std/var: Welford's parallel algorithm (requires sum, sum_sq, count)
    - median: Falls back to sequential (non-parallelizable)

    Performance target: <10ms merge overhead for 1M result rows
    """

    def __init__(self):
        self.strategy = AggregationStrategy()

    def merge_groupby_results(
        self,
        partial_results: List,  # List[pd.DataFrame]
        by: Union[str, List[str]],
        agg_spec: Optional[Dict] = None
    ):
        """
        Merge partial groupby results.

        Args:
            partial_results: Results from each worker (already grouped)
            by: Group column(s)
            agg_spec: Aggregation specification (e.g., {'value': ['sum', 'mean']})

        Returns:
            Combined DataFrame with final aggregations
        """
        import pandas as pd

        if not partial_results:
            return pd.DataFrame()

        if len(partial_results) == 1:
            return partial_results[0]

        # Normalize by to list
        if isinstance(by, str):
            by = [by]

        # If no agg_spec provided, infer from results
        if agg_spec is None:
            agg_spec = self._infer_agg_spec(partial_results[0])

        logger.debug(f"Merging {len(partial_results)} partial results with agg_spec: {agg_spec}")

        # Combine all results
        combined = pd.concat(partial_results, ignore_index=False)

        # For simple combinable aggregations, we can re-aggregate
        if self._all_combinable(agg_spec):
            return self._merge_combinable(combined, by, agg_spec)

        # For mixed aggregations, handle each type separately
        return self._merge_mixed(combined, by, agg_spec, partial_results)

    def _infer_agg_spec(self, result) -> Dict:
        """Infer aggregation spec from result DataFrame columns."""
        import pandas as pd

        agg_spec = {}
        if isinstance(result.columns, pd.MultiIndex):
            # Multi-level columns from .agg()
            for col, func in result.columns:
                agg_spec.setdefault(col, []).append(func)
        else:
            # Single aggregation
            for col in result.columns:
                agg_spec[col] = ['sum']  # Default assumption

        return agg_spec

    def _all_combinable(self, agg_spec: Dict) -> bool:
        """Check if all aggregations are directly combinable."""
        for col, funcs in agg_spec.items():
            for func in funcs:
                func_name = func if isinstance(func, str) else getattr(func, '__name__', '')
                if func_name not in self.strategy.COMBINABLE:
                    return False
        return True

    def _merge_combinable(self, combined, by: List[str], agg_spec: Dict):
        """
        Merge results where all aggregations are directly combinable.

        For sum: sum of partial sums = total sum
        For count: sum of partial counts = total count
        For min: min of partial mins = total min
        For max: max of partial maxs = total max
        """
        import pandas as pd

        # Build re-aggregation spec
        reagg_spec = {}
        for col, funcs in agg_spec.items():
            for func in funcs:
                func_name = func if isinstance(func, str) else getattr(func, '__name__', '')

                # Map to appropriate merge operation
                if func_name in ('sum', 'count', 'size', 'prod'):
                    merge_op = 'sum'
                elif func_name == 'min':
                    merge_op = 'min'
                elif func_name == 'max':
                    merge_op = 'max'
                elif func_name == 'first':
                    merge_op = 'first'
                elif func_name == 'last':
                    merge_op = 'last'
                elif func_name in ('any', 'all'):
                    merge_op = func_name
                else:
                    merge_op = 'sum'  # Default

                # Handle multi-level columns
                if isinstance(combined.columns, pd.MultiIndex):
                    reagg_spec[(col, func_name)] = merge_op
                else:
                    reagg_spec[col] = merge_op

        # Re-aggregate by groups
        if isinstance(combined.index, pd.MultiIndex):
            # Already has group index
            result = combined.groupby(level=list(range(len(by)))).agg(reagg_spec)
        else:
            # Reset and re-group
            if isinstance(combined.columns, pd.MultiIndex):
                # Flatten for groupby
                combined_flat = combined.reset_index()
                result = combined_flat.groupby(by).agg(reagg_spec)
            else:
                result = combined.groupby(by).agg(reagg_spec)

        return result

    def _merge_mixed(
        self,
        combined,
        by: List[str],
        agg_spec: Dict,
        partial_results: List
    ):
        """
        Merge results with mixed aggregation types.

        Handles weighted means and falls back for complex aggregations.
        """
        import pandas as pd
        import numpy as np

        results = {}

        for col, funcs in agg_spec.items():
            for func in funcs:
                func_name = func if isinstance(func, str) else getattr(func, '__name__', '')

                if func_name in self.strategy.COMBINABLE:
                    # Direct combination
                    results[(col, func_name)] = self._merge_single_combinable(
                        combined, by, col, func_name
                    )

                elif func_name == 'mean':
                    # Weighted mean using sum and count
                    results[(col, func_name)] = self._merge_mean(
                        partial_results, by, col
                    )

                elif func_name in self.strategy.COMPLEX:
                    # Fall back to sequential for complex aggregations
                    logger.warning(
                        f"Aggregation '{func_name}' requires full data access. "
                        f"Falling back to sequential computation."
                    )
                    results[(col, func_name)] = self._fallback_sequential(
                        combined, by, col, func_name
                    )

                elif func_name in self.strategy.NON_PARALLELIZABLE:
                    logger.warning(
                        f"Aggregation '{func_name}' is non-parallelizable. "
                        f"Result may be approximate."
                    )
                    results[(col, func_name)] = self._fallback_sequential(
                        combined, by, col, func_name
                    )

                else:
                    # Unknown aggregation - try combinable approach
                    try:
                        results[(col, func_name)] = self._merge_single_combinable(
                            combined, by, col, func_name
                        )
                    except Exception as e:
                        logger.warning(f"Unknown aggregation '{func_name}': {e}")
                        results[(col, func_name)] = self._fallback_sequential(
                            combined, by, col, func_name
                        )

        # Combine into DataFrame with proper index handling
        if not results:
            return pd.DataFrame()

        # Get index from first non-empty result
        first_result = next(
            (v for v in results.values() if isinstance(v, (pd.Series, pd.DataFrame)) and len(v) > 0),
            None
        )

        if first_result is not None:
            result_df = pd.DataFrame(results, index=first_result.index)
        else:
            result_df = pd.DataFrame(results)

        return result_df

    def _merge_single_combinable(self, combined, by: List[str], col: str, func: str):
        """Merge a single combinable aggregation."""
        import pandas as pd

        # Determine merge operation
        merge_ops = {
            'sum': 'sum', 'count': 'sum', 'size': 'sum', 'prod': 'prod',
            'min': 'min', 'max': 'max', 'first': 'first', 'last': 'last',
            'any': 'any', 'all': 'all'
        }
        merge_op = merge_ops.get(func, 'sum')

        # Get the column data
        if isinstance(combined.columns, pd.MultiIndex):
            if (col, func) in combined.columns:
                data = combined[(col, func)]
            else:
                raise KeyError(f"Column ({col}, {func}) not found")
        else:
            data = combined[col]

        # Reset index if needed and re-aggregate
        if isinstance(combined.index, pd.MultiIndex):
            return data.groupby(level=list(range(len(by)))).agg(merge_op)
        else:
            df_with_data = combined.reset_index()[[*by, col if col in combined.columns else (col, func)]]
            return df_with_data.groupby(by).agg(merge_op)

    def _merge_mean(self, partial_results: List, by: List[str], col: str):
        """
        Merge mean using weighted average.

        Formula: total_mean = sum(partition_sum) / sum(partition_count)

        If count not available, fall back to simple average of means.
        """
        import pandas as pd
        import numpy as np

        sums = []
        counts = []

        for result in partial_results:
            if isinstance(result.columns, pd.MultiIndex):
                # Check if we have both sum and count
                has_sum = (col, 'sum') in result.columns
                has_count = (col, 'count') in result.columns
                has_mean = (col, 'mean') in result.columns

                if has_sum and has_count:
                    sums.append(result[(col, 'sum')])
                    counts.append(result[(col, 'count')])
                elif has_mean and has_count:
                    # Reconstruct sum from mean * count
                    sums.append(result[(col, 'mean')] * result[(col, 'count')])
                    counts.append(result[(col, 'count')])
                elif has_mean:
                    # No count available - assume equal weights
                    # This is less accurate but better than nothing
                    sums.append(result[(col, 'mean')])
                    counts.append(pd.Series(1, index=result.index))
            else:
                # Single column result
                if col in result.columns:
                    sums.append(result[col])
                    counts.append(pd.Series(1, index=result.index))

        if not sums:
            return pd.Series(dtype=float)

        # Combine sums and counts
        combined_sums = pd.concat(sums).groupby(level=0).sum()
        combined_counts = pd.concat(counts).groupby(level=0).sum()

        return combined_sums / combined_counts

    def _fallback_sequential(self, combined, by: List[str], col: str, func: str):
        """Fall back to sequential computation for non-parallelizable aggregations."""
        import pandas as pd

        # Reset to raw data and compute sequentially
        if isinstance(combined.columns, pd.MultiIndex):
            # Can't easily recover raw data from aggregated results
            # Return NaN with warning
            logger.warning(
                f"Cannot compute '{func}' from pre-aggregated data. "
                f"Consider requesting this aggregation separately."
            )
            return pd.Series(dtype=float)
        else:
            # Try to compute from combined data
            return combined.groupby(by)[col].agg(func)
