"""
Allocator Health Tracking for Memory Subsystem

This module provides the AllocatorHealth dataclass used by JITManager
to pause compilation when the fast allocator is on fallback path.

Key Features:
- Tracks whether Cython fast allocator is active
- Provides fallback reason for diagnostics
- Serialization support for telemetry

Author: Epochly Development Team
Date: November 14, 2025
Spec: perf_fixes2.md Task 3
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class AllocatorHealth:
    """
    Health status of the memory allocator subsystem.

    Used by JITManager to pause compilations when allocator is on
    slow fallback path to prevent memory pressure.

    Attributes:
        is_fast_path: Whether Cython fast allocator is active
        fallback_reason: Human-readable reason for fallback (if applicable)
        pool_name: Name of the memory pool
        timestamp: Unix timestamp of health check

    Example:
        >>> health = AllocatorHealth(
        ...     is_fast_path=False,
        ...     fallback_reason="Cython module not compiled",
        ...     pool_name="FastMemoryPool",
        ...     timestamp=1234567890.0
        ... )
        >>> if not health.is_fast_path:
        ...     print(f"Allocator on fallback: {health.fallback_reason}")
    """

    is_fast_path: bool
    fallback_reason: Optional[str]
    pool_name: str
    timestamp: float

    def is_healthy(self) -> bool:
        """
        Check if allocator is in optimal state.

        Returns:
            True if fast path is active, False if on fallback
        """
        return self.is_fast_path

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary for telemetry.

        Returns:
            Dictionary representation of allocator health
        """
        return {
            'is_fast_path': self.is_fast_path,
            'fallback_reason': self.fallback_reason,
            'pool_name': self.pool_name,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AllocatorHealth':
        """
        Deserialize from dictionary.

        Args:
            data: Dictionary containing health fields

        Returns:
            AllocatorHealth instance
        """
        return cls(
            is_fast_path=data['is_fast_path'],
            fallback_reason=data.get('fallback_reason'),
            pool_name=data['pool_name'],
            timestamp=data['timestamp']
        )
