"""
Level Health Snapshot for Progressive Enhancement Monitoring

This module provides the LevelHealthSnapshot dataclass used by the
EnhancementProgressionManager to make automatic upgrade/rollback decisions
based on real-time performance metrics.

Key Features:
- Captures throughput ratio, error rate, allocator status
- Supports serialization to/from dict for persistence
- Provides health checking with configurable thresholds
- Ordered by timestamp for rolling window analysis

Author: Epochly Development Team
Date: November 14, 2025
Spec: perf_fixes2.md Task 1 Phase 1
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from epochly.core.epochly_core import EnhancementLevel


@dataclass(order=True)
class LevelHealthSnapshot:
    """
    Snapshot of enhancement level health metrics at a point in time.

    Used by EnhancementProgressionManager to make upgrade/rollback decisions
    based on throughput improvements, error rates, and allocator status.

    Ordering is by timestamp (oldest to newest) for rolling window analysis.

    Attributes:
        level: Current enhancement level (LEVEL_0_MONITOR through LEVEL_4_GPU_ACCELERATION)
        throughput_ratio: Current/baseline throughput ratio
                         >1.0 = improvement, <1.0 = regression, 1.0 = baseline
        error_rate: Errors per second (0.0 = no errors)
        allocator_fast_path: Whether Cython fast allocator is active (True = fast, False = fallback)
        timestamp: Unix timestamp when snapshot was taken (used for ordering)
        metadata: Extensible metadata dictionary for additional context (not used in comparison)

    Example:
        >>> from epochly.core.epochly_core import EnhancementLevel
        >>> snapshot = LevelHealthSnapshot(
        ...     level=EnhancementLevel.LEVEL_3_FULL,
        ...     throughput_ratio=1.25,  # 25% improvement
        ...     error_rate=0.001,       # 0.1% error rate
        ...     allocator_fast_path=True,
        ...     timestamp=1234567890.0
        ... )
        >>> snapshot.is_healthy()
        True
        >>> snapshot.is_healthy(min_throughput=1.5)  # Stricter threshold
        False
    """

    level: 'EnhancementLevel'
    throughput_ratio: float
    error_rate: float
    allocator_fast_path: bool
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict, compare=False)

    def __post_init__(self):
        """
        Validate snapshot fields after initialization.

        Raises:
            ValueError: If throughput_ratio or error_rate is negative
        """
        if self.throughput_ratio < 0:
            raise ValueError(
                f"throughput_ratio must be >= 0, got {self.throughput_ratio}"
            )
        if self.error_rate < 0:
            raise ValueError(
                f"error_rate must be >= 0, got {self.error_rate}"
            )

    def is_healthy(
        self,
        min_throughput: float = 1.0,
        max_error_rate: float = 0.01
    ) -> bool:
        """
        Check if snapshot indicates healthy operation within acceptable thresholds.

        A snapshot is considered healthy when:
        1. Throughput ratio meets or exceeds minimum (default: 1.0 = baseline)
        2. Error rate is at or below maximum (default: 0.01 = 1%)
        3. Fast allocator is active (not on fallback path)

        Args:
            min_throughput: Minimum acceptable throughput ratio (default: 1.0)
                          - 1.0 = baseline performance
                          - 1.05 = 5% improvement required
                          - 0.95 = tolerate 5% regression
            max_error_rate: Maximum acceptable error rate (default: 0.01 = 1%)
                          - 0.01 = 1% errors tolerated
                          - 0.005 = 0.5% errors tolerated
                          - 0.0 = zero errors required

        Returns:
            True if all health criteria are met, False otherwise

        Example:
            >>> snapshot = LevelHealthSnapshot(
            ...     level=EnhancementLevel.LEVEL_3_FULL,
            ...     throughput_ratio=1.15,
            ...     error_rate=0.005,
            ...     allocator_fast_path=True,
            ...     timestamp=1000.0
            ... )
            >>> snapshot.is_healthy()  # Default thresholds
            True
            >>> snapshot.is_healthy(min_throughput=1.2)  # Stricter threshold
            False
        """
        return (
            self.throughput_ratio >= min_throughput and
            self.error_rate <= max_error_rate and
            self.allocator_fast_path
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize snapshot to dictionary for persistence or transmission.

        The EnhancementLevel enum is converted to its string name for JSON compatibility.

        Returns:
            Dictionary representation of the snapshot with 'level' as enum name string

        Example:
            >>> snapshot.to_dict()
            {
                'level': 'LEVEL_3_FULL',
                'throughput_ratio': 1.25,
                'error_rate': 0.001,
                'allocator_fast_path': True,
                'timestamp': 1234567890.0,
                'metadata': {}
            }
        """
        data = asdict(self)
        # Convert EnhancementLevel enum to string for serialization
        data['level'] = self.level.name
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LevelHealthSnapshot':
        """
        Deserialize snapshot from dictionary.

        The 'level' field must be an EnhancementLevel enum name string
        (e.g., 'LEVEL_3_FULL') which will be converted to the enum value.

        Args:
            data: Dictionary containing snapshot fields with 'level' as enum name

        Returns:
            LevelHealthSnapshot instance reconstructed from dictionary

        Raises:
            KeyError: If 'level' is not a valid EnhancementLevel enum name

        Example:
            >>> data = {
            ...     'level': 'LEVEL_3_FULL',
            ...     'throughput_ratio': 1.25,
            ...     'error_rate': 0.001,
            ...     'allocator_fast_path': True,
            ...     'timestamp': 1234567890.0
            ... }
            >>> snapshot = LevelHealthSnapshot.from_dict(data)
            >>> snapshot.level
            <EnhancementLevel.LEVEL_3_FULL: 3>
        """
        from ..core.epochly_core import EnhancementLevel

        # Create copy to avoid mutating input
        data = data.copy()

        # Convert level string to enum
        data['level'] = EnhancementLevel[data['level']]

        return cls(**data)
