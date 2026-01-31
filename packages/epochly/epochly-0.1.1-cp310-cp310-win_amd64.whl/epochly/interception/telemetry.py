"""
Interception Telemetry - Track Automatic Optimizations

Records which operations were intercepted and routed to Level 3.

Author: Epochly Development Team
Date: November 16, 2025
"""

import time
import threading
from typing import Dict, Any, List, Optional
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class InterceptionEvent:
    """Record of a single interception event."""
    op_id: str
    timestamp: float
    routed_to_level3: bool
    execution_time: float
    success: bool
    error: Optional[str] = None


class InterceptionTelemetry:
    """
    Tracks transparent interception events.

    Provides visibility into:
    - Which operations were intercepted
    - Success/failure rates
    - Performance impact
    - Routing decisions
    """

    def __init__(self):
        """Initialize telemetry tracker."""
        self._lock = threading.Lock()
        self._events: List[InterceptionEvent] = []
        self._stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_calls': 0,
            'level3_routed': 0,
            'level3_success': 0,
            'level3_failed': 0,
            'fallback_used': 0,
            'total_time': 0.0
        })
        self._max_events = 10000  # Ring buffer size

    def record_interception(
        self,
        op_id: str,
        routed_to_level3: bool,
        execution_time: float,
        success: bool,
        error: Optional[str] = None
    ):
        """
        Record an interception event.

        Args:
            op_id: Operation identifier (e.g., 'numpy.dot')
            routed_to_level3: Whether routed to Level 3 executor
            execution_time: Execution time in seconds
            success: Whether execution succeeded
            error: Error message if failed
        """
        event = InterceptionEvent(
            op_id=op_id,
            timestamp=time.time(),
            routed_to_level3=routed_to_level3,
            execution_time=execution_time,
            success=success,
            error=error
        )

        with self._lock:
            # Add to ring buffer
            if len(self._events) >= self._max_events:
                self._events.pop(0)  # Remove oldest
            self._events.append(event)

            # Update stats
            stats = self._stats[op_id]
            stats['total_calls'] += 1
            stats['total_time'] += execution_time

            if routed_to_level3:
                stats['level3_routed'] += 1
                if success:
                    stats['level3_success'] += 1
                else:
                    stats['level3_failed'] += 1
            else:
                stats['fallback_used'] += 1

    def get_stats(self, op_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get interception statistics.

        Args:
            op_id: Specific operation ID, or None for all operations

        Returns:
            Stats dictionary
        """
        with self._lock:
            if op_id:
                return dict(self._stats.get(op_id, {}))
            else:
                return {k: dict(v) for k, v in self._stats.items()}

    def get_recent_events(self, limit: int = 100) -> List[InterceptionEvent]:
        """
        Get recent interception events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        with self._lock:
            return self._events[-limit:]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all interception activity.

        Returns:
            Summary dict with aggregate statistics
        """
        with self._lock:
            total_calls = sum(s['total_calls'] for s in self._stats.values())
            total_level3 = sum(s['level3_routed'] for s in self._stats.values())
            total_success = sum(s['level3_success'] for s in self._stats.values())
            total_fallback = sum(s['fallback_used'] for s in self._stats.values())

            return {
                'total_intercepted_calls': total_calls,
                'level3_routed': total_level3,
                'level3_success_rate': total_success / total_level3 if total_level3 > 0 else 0.0,
                'fallback_rate': total_fallback / total_calls if total_calls > 0 else 0.0,
                'operations_tracked': len(self._stats),
                'recent_events_count': len(self._events)
            }

    def reset(self):
        """Reset all telemetry data."""
        with self._lock:
            self._events.clear()
            self._stats.clear()
