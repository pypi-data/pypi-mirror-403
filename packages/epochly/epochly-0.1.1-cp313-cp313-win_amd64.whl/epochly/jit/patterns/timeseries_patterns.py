"""
Time Series Pattern Detection

Detects rolling/window statistics patterns:
- pandas.rolling operations (mean, std, sum, min, max, var, apply)
- pandas.ewm (exponential weighted moving operations)
- Manual rolling window implementations
- NumPy sliding window views

Author: Epochly Development Team
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from .base import BasePatternInfo, PatternDetector

logger = logging.getLogger(__name__)


@dataclass
class RollingStatsInfo(BasePatternInfo):
    """
    Information about a detected rolling statistics pattern.

    Attributes:
        operation: The aggregation operation ('mean', 'std', 'sum', 'min', 'max',
                   'var', 'apply', 'range')
        window_size: Window size if literal value detected (None if variable)
        min_periods: Minimum periods for valid output (None if not specified)
        is_centered: True if center=True is specified
        is_exponential: True for ewm (exponential weighted) operations
        has_custom_function: True if rolling.apply() with custom function
        is_manual_implementation: True for manual loop-based rolling
        uses_stride_tricks: True for numpy sliding_window_view
        has_window_size: True if any window size is specified
    """
    operation: str = 'unknown'
    window_size: Optional[int] = None
    min_periods: Optional[int] = None
    is_centered: bool = False
    is_exponential: bool = False
    has_custom_function: bool = False
    is_manual_implementation: bool = False
    uses_stride_tricks: bool = False
    has_window_size: bool = False


class RollingStatsDetector(PatternDetector):
    """
    Detects rolling/window statistics patterns.

    Uses regex for pandas rolling/ewm detection, then AST for parameter extraction.

    Detection priority: 25 (moderate - specific but needs context)
    """

    # Operations supported by pandas rolling
    ROLLING_OPERATIONS = frozenset({
        'mean', 'std', 'var', 'sum', 'min', 'max',
        'median', 'quantile', 'count', 'skew', 'kurt',
        'apply', 'aggregate', 'agg'
    })

    # Regex for pandas rolling pattern: .rolling(...).<operation>()
    ROLLING_REGEX = re.compile(
        r'\.rolling\s*\([^)]*\)\s*\.\s*'
        r'(mean|std|var|sum|min|max|median|quantile|count|skew|kurt|apply|aggregate|agg)\s*\(',
        re.IGNORECASE | re.DOTALL
    )

    # Regex for pandas ewm pattern: .ewm(...).<operation>()
    EWM_REGEX = re.compile(
        r'\.ewm\s*\([^)]*\)\s*\.\s*'
        r'(mean|std|var|sum|corr|cov)\s*\(',
        re.IGNORECASE | re.DOTALL
    )

    # Regex for numpy sliding_window_view
    SLIDING_WINDOW_REGEX = re.compile(
        r'\bsliding_window_view\s*\(',
        re.IGNORECASE
    )

    # Regex for extracting window parameter from rolling(...)
    WINDOW_PARAM_REGEX = re.compile(
        r'\.rolling\s*\(\s*(?:window\s*=\s*)?(\d+)',
        re.IGNORECASE
    )

    # Regex for min_periods parameter
    MIN_PERIODS_REGEX = re.compile(
        r'min_periods\s*=\s*(\d+)',
        re.IGNORECASE
    )

    # Regex for center parameter
    CENTER_REGEX = re.compile(
        r'center\s*=\s*True',
        re.IGNORECASE
    )

    @property
    def pattern_name(self) -> str:
        return 'rolling_stats'

    @property
    def detection_priority(self) -> int:
        return 25

    def detect(self, source: str, tree: ast.AST) -> Optional[RollingStatsInfo]:
        """
        Detect rolling statistics patterns in source code.

        Args:
            source: Source code as string
            tree: Parsed AST

        Returns:
            RollingStatsInfo if rolling pattern detected, None otherwise.
        """
        # Check for pandas rolling
        rolling_match = self.ROLLING_REGEX.search(source)
        if rolling_match:
            return self._handle_pandas_rolling(source, tree, rolling_match)

        # Check for pandas ewm
        ewm_match = self.EWM_REGEX.search(source)
        if ewm_match:
            return self._handle_pandas_ewm(source, tree, ewm_match)

        # Check for numpy sliding window view
        if self.SLIDING_WINDOW_REGEX.search(source):
            return self._handle_numpy_sliding_window(source, tree)

        # Check for manual rolling implementation
        manual_result = self._detect_manual_rolling(source, tree)
        if manual_result:
            return manual_result

        return None

    def _handle_pandas_rolling(
        self,
        source: str,
        tree: ast.AST,
        match: re.Match
    ) -> RollingStatsInfo:
        """Handle pandas .rolling().<op>() pattern."""
        operation = match.group(1).lower()

        info = RollingStatsInfo(
            pattern_name='rolling_stats',
            operation=operation,
            confidence=0.9,
            has_window_size=True
        )

        # Extract window size if literal
        window_match = self.WINDOW_PARAM_REGEX.search(source)
        if window_match:
            info.window_size = int(window_match.group(1))

        # Extract min_periods
        min_periods_match = self.MIN_PERIODS_REGEX.search(source)
        if min_periods_match:
            info.min_periods = int(min_periods_match.group(1))

        # Check for center=True
        if self.CENTER_REGEX.search(source):
            info.is_centered = True

        # Check for custom function (apply)
        if operation in ('apply', 'aggregate', 'agg'):
            info.has_custom_function = True

        # Rolling operations are GPU-suitable for large windows
        info.gpu_suitable = True
        info.memory_pattern = 'coalesced'

        return info

    def _handle_pandas_ewm(
        self,
        source: str,
        tree: ast.AST,
        match: re.Match
    ) -> RollingStatsInfo:
        """Handle pandas .ewm().<op>() pattern."""
        operation = match.group(1).lower()

        info = RollingStatsInfo(
            pattern_name='rolling_stats',
            operation=operation,
            is_exponential=True,
            has_window_size=True,  # EWM uses span/alpha instead of window
            confidence=0.9,
            gpu_suitable=True,
            memory_pattern='coalesced'
        )

        return info

    def _handle_numpy_sliding_window(
        self,
        source: str,
        tree: ast.AST
    ) -> RollingStatsInfo:
        """Handle numpy sliding_window_view pattern."""
        info = RollingStatsInfo(
            pattern_name='rolling_stats',
            operation='custom',
            uses_stride_tricks=True,
            has_window_size=True,
            confidence=0.85,
            gpu_suitable=True,
            memory_pattern='strided'
        )

        # Try to detect the operation applied to the windows
        # Look for common aggregations: mean, sum, max, min
        if re.search(r'np\.mean\s*\([^)]*windows', source, re.IGNORECASE):
            info.operation = 'mean'
        elif re.search(r'np\.sum\s*\([^)]*windows', source, re.IGNORECASE):
            info.operation = 'sum'
        elif re.search(r'np\.max\s*\([^)]*windows', source, re.IGNORECASE):
            info.operation = 'max'
        elif re.search(r'np\.min\s*\([^)]*windows', source, re.IGNORECASE):
            info.operation = 'min'

        return info

    def _detect_manual_rolling(
        self,
        source: str,
        tree: ast.AST
    ) -> Optional[RollingStatsInfo]:
        """
        Detect manual rolling window implementations.

        Looks for patterns like:
        - Nested loops with sliding window indexing
        - Loop with sum accumulation over window range
        """
        # Check for nested for loops using AST (more reliable than regex for Python)
        has_nested_loops = False
        has_window_indexing = False
        has_window_in_range = False

        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Check for nested for loops
                for child in ast.walk(node):
                    if isinstance(child, ast.For) and child is not node:
                        has_nested_loops = True
                        # Check if inner loop uses 'window' in range
                        if isinstance(child.iter, ast.Call):
                            if isinstance(child.iter.func, ast.Name):
                                if child.iter.func.id == 'range':
                                    for arg in child.iter.args:
                                        if isinstance(arg, ast.Name) and arg.id == 'window':
                                            has_window_in_range = True

                # Check for subscript with subtraction (data[i-j] pattern)
                for child in ast.walk(node):
                    if isinstance(child, ast.Subscript):
                        if isinstance(child.slice, ast.BinOp):
                            if isinstance(child.slice.op, ast.Sub):
                                has_window_indexing = True

        # Need nested loops with:
        # 1. sliding window indexing (data[i-j] pattern)
        # 2. A window-related variable in range() to avoid false positives on stencil patterns
        #    (stencil has nested loops and subscript subtraction but not for window iteration)
        if has_nested_loops and has_window_indexing and has_window_in_range:
            return RollingStatsInfo(
                pattern_name='rolling_stats',
                operation='custom',
                is_manual_implementation=True,
                has_window_size=True,
                confidence=0.75,
                gpu_suitable=True,
                memory_pattern='coalesced'
            )

        return None
