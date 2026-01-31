"""
Routing Decision Telemetry Events (Task 5.2)

Structured events for all routing decisions per perf_fixes3.md Section 5.8.

Events emitted:
- Fallback executor selection
- Worker scaling operations
- GPU routing decisions
- Memory allocator expansion/shrinkage
- JIT compilation metrics (GAP #1)
- Resource utilization (GAP #2)
- Workload classification (GAP #3)
- Level transitions (GAP #4)

All events sent to AWS via api.epochly.com gateway.

Author: Epochly Development Team
Created: 2025-11-15
Python Compatibility: 3.9, 3.10, 3.11, 3.12, 3.13
"""

from __future__ import annotations

import math
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


logger = logging.getLogger(__name__)


def _sanitize_float(value: Any, fallback: float = 0.0) -> float:
    """Sanitize float value by replacing NaN/Inf/None/invalid with fallback.

    This function is designed to NEVER throw - it always returns a valid float.
    It handles None, NaN, Inf, and non-numeric types gracefully.

    Args:
        value: Value to sanitize (may be None, NaN, Inf, or invalid type)
        fallback: Value to return for invalid inputs (default 0.0)

    Returns:
        Sanitized float value, or fallback if input is invalid

    Example:
        >>> _sanitize_float(float('nan'), 1.0)
        1.0
        >>> _sanitize_float(None, 0.0)
        0.0
        >>> _sanitize_float("invalid", 0.0)
        0.0
    """
    if value is None:
        return fallback
    try:
        v = float(value)
    except (TypeError, ValueError):
        return fallback
    if math.isnan(v) or math.isinf(v):
        return fallback
    return v


def _clamp_percent(value: Optional[float]) -> float:
    """Clamp percentage value to 0-100 range.

    Args:
        value: Percentage value (may be None, negative, or > 100)

    Returns:
        Float clamped to [0.0, 100.0]
    """
    return max(0.0, min(100.0, _sanitize_float(value)))


def _clamp_positive(value: Optional[int]) -> int:
    """Clamp integer value to non-negative.

    Args:
        value: Integer value (may be None or negative)

    Returns:
        Non-negative integer
    """
    if value is None:
        return 0
    return max(0, value)


def _clamp_ratio(value: Optional[float]) -> float:
    """Clamp ratio value to 0-1 range.

    Args:
        value: Ratio value (may be None, negative, or > 1)

    Returns:
        Float clamped to [0.0, 1.0]
    """
    return max(0.0, min(1.0, _sanitize_float(value)))


def _clamp_level(value: Optional[int]) -> int:
    """Clamp enhancement level to 0-4 range.

    Args:
        value: Level value (may be None, negative, or > 4)

    Returns:
        Integer clamped to [0, 4]
    """
    if value is None:
        return 0
    return max(0, min(4, value))


def _truncate_string(value: Optional[str], max_length: int = 256) -> str:
    """Truncate string to maximum length.

    Args:
        value: String to truncate (may be None or exceed max_length)
        max_length: Maximum allowed length (default 256)

    Returns:
        String truncated to max_length, or empty string if None
    """
    if not value:
        return ""
    if len(value) > max_length:
        return value[:max_length]
    return value


@dataclass
class RoutingEvent:
    """Base class for routing decision events."""
    event_type: str
    timestamp: float
    metadata: Dict[str, Any]


class RoutingEventEmitter:
    """
    Emits routing decision events to AWS telemetry.

    Per Task 5.2: Structured events for observability.
    """

    def __init__(self):
        """Initialize routing event emitter."""
        self.logger = logging.getLogger(__name__)

        # Get telemetry client (lazy import to avoid circular deps)
        self._telemetry_client: Optional[Any] = None
        self._client_initialized = False
        self._telemetry_enabled = False  # Track enabled state separately

    def _ensure_client(self) -> bool:
        """Lazy initialization of telemetry client."""
        if self._client_initialized:
            # Return cached enabled state (fixes disable flag bug)
            return self._telemetry_enabled

        self._client_initialized = True

        try:
            from epochly.compatibility.aws_telemetry_client import AWSSecureTelemetryClient
            self._telemetry_client = AWSSecureTelemetryClient()

            # Cache enabled state
            self._telemetry_enabled = self._telemetry_client.enabled

            if self._telemetry_enabled:
                self.logger.debug("Routing event telemetry enabled (AWS)")
            else:
                self.logger.debug("Telemetry disabled (test mode or no endpoint)")

            return self._telemetry_enabled

        except Exception as e:
            self.logger.debug(f"Telemetry client unavailable: {e}")
            self._telemetry_enabled = False
            return False

    def emit_fallback_selection(self, mode: str, workers: int,
                                workload_type: str, selection_reason: str,
                                workload_size: int = 0,
                                additional_metadata: Optional[Dict] = None):
        """
        Emit fallback executor selection event.

        Args:
            mode: Executor mode ('subinterp', 'gpu', 'async', 'process', 'thread')
            workers: Number of workers allocated (clamped to non-negative)
            workload_type: Type of workload (truncated to 64 chars)
            selection_reason: Why this executor was selected (truncated to 256 chars)
            workload_size: Estimated workload size in bytes (clamped to non-negative)
            additional_metadata: Extra context (reserved keys protected)
        """
        if not self._ensure_client():
            return

        try:
            event = {
                'event_type': 'fallback_selected',
                'timestamp': time.time(),
                'mode': _truncate_string(mode, 32),
                'workers': _clamp_positive(workers),
                'workload_type': _truncate_string(workload_type, 64),
                'selection_reason': _truncate_string(selection_reason, 256),
                'workload_size_bytes': _clamp_positive(workload_size),
            }

            if additional_metadata and isinstance(additional_metadata, dict):
                # Protect reserved keys from being overwritten
                reserved = {'event_type', 'timestamp'}
                safe_metadata = {k: v for k, v in additional_metadata.items()
                                if k not in reserved}
                event.update(safe_metadata)

            self._telemetry_client.send_telemetry(event)
        except Exception as e:
            self.logger.debug(f"Failed to emit fallback selection event: {e}")

    def emit_worker_scaling(self, operation: str, old_count: int,
                           new_count: int, reason: str,
                           executor_type: str = 'unknown'):
        """
        Emit worker scaling event.

        Args:
            operation: 'scale_up' or 'scale_down' (truncated to 32 chars)
            old_count: Previous worker count (clamped to non-negative)
            new_count: New worker count (clamped to non-negative)
            reason: Reason for scaling (truncated to 256 chars)
            executor_type: Type of executor being scaled (truncated to 32 chars)
        """
        if not self._ensure_client():
            return

        try:
            old_clamped = _clamp_positive(old_count)
            new_clamped = _clamp_positive(new_count)
            event = {
                'event_type': 'worker_scaling',
                'timestamp': time.time(),
                'operation': _truncate_string(operation, 32),
                'old_count': old_clamped,
                'new_count': new_clamped,
                'delta': new_clamped - old_clamped,
                'reason': _truncate_string(reason, 256),
                'executor_type': _truncate_string(executor_type, 32)
            }

            self._telemetry_client.send_telemetry(event)
        except Exception as e:
            self.logger.debug(f"Failed to emit worker scaling event: {e}")

    def emit_gpu_routing(self, gpu_activated: bool, reason: str,
                        workload_size: int = 0, gpu_suitability: float = 0.0):
        """
        Emit GPU routing decision event.

        Args:
            gpu_activated: True if GPU was selected
            reason: Why GPU was/wasn't used (truncated to 256 chars)
            workload_size: Workload size (clamped to non-negative)
            gpu_suitability: GPU suitability score 0-1 (clamped to ratio)
        """
        if not self._ensure_client():
            return

        try:
            event = {
                'event_type': 'gpu_routing',
                'timestamp': time.time(),
                'gpu_activated': bool(gpu_activated),
                'reason': _truncate_string(reason, 256),
                'workload_size_bytes': _clamp_positive(workload_size),
                'gpu_suitability_score': _clamp_ratio(gpu_suitability)
            }

            self._telemetry_client.send_telemetry(event)
        except Exception as e:
            self.logger.debug(f"Failed to emit GPU routing event: {e}")

    def emit_allocator_event(self, operation: str, old_size: int,
                            new_size: int, reason: str, pool_type: str = 'shared'):
        """
        Emit memory allocator expansion/shrinkage event.

        Args:
            operation: 'expand' or 'shrink' (truncated to 32 chars)
            old_size: Previous pool size in bytes (clamped to non-negative)
            new_size: New pool size in bytes (clamped to non-negative)
            reason: Reason for resize (truncated to 256 chars)
            pool_type: Type of memory pool (truncated to 32 chars)
        """
        if not self._ensure_client():
            return

        try:
            old_clamped = _clamp_positive(old_size)
            new_clamped = _clamp_positive(new_size)
            event = {
                'event_type': 'allocator_resize',
                'timestamp': time.time(),
                'operation': _truncate_string(operation, 32),
                'old_size_bytes': old_clamped,
                'new_size_bytes': new_clamped,
                'delta_bytes': new_clamped - old_clamped,
                'reason': _truncate_string(reason, 256),
                'pool_type': _truncate_string(pool_type, 32)
            }

            self._telemetry_client.send_telemetry(event)
        except Exception as e:
            self.logger.debug(f"Failed to emit allocator event: {e}")

    def emit_jit_compilation(
        self,
        function_name: str,
        backend: str,
        compilation_time_ms: float,
        speedup_ratio: float,
        hot_loop_detected: bool = False,
        iteration_count: int = 0
    ):
        """
        Emit JIT compilation event for Lens Performance tab.

        Per telemetry-audit-findings.md GAP #1: TelemetryStore metrics
        must be transmitted to AWS for Lens visibility.

        Args:
            function_name: Name of compiled function (truncated to 256 chars)
            backend: JIT backend ('numba', 'pyston', 'native', 'cython')
            compilation_time_ms: Time to compile in milliseconds (sanitized)
            speedup_ratio: Speedup factor (compiled / interpreted) (sanitized)
            hot_loop_detected: Whether a hot loop triggered compilation
            iteration_count: Loop iteration count (if hot loop detected)
        """
        if not self._ensure_client():
            return

        try:
            event = {
                'event_type': 'jit_compilation',
                'timestamp': time.time(),
                'function_name': _truncate_string(function_name),
                'backend': _truncate_string(backend, 32),
                'compilation_time_ms': _sanitize_float(compilation_time_ms),
                'speedup_ratio': _sanitize_float(speedup_ratio, fallback=1.0),
                'hot_loop_detected': bool(hot_loop_detected),
                'iteration_count': _clamp_positive(iteration_count)
            }

            self._telemetry_client.send_telemetry(event)
        except Exception as e:
            self.logger.debug(f"Failed to emit JIT compilation event: {e}")

    def emit_resource_utilization(
        self,
        cpu_percent: float,
        memory_mb: int,
        memory_percent: Optional[float] = None,
        gpu_utilization_percent: Optional[float] = None,
        gpu_memory_mb: Optional[int] = None,
        pool_efficiency: Optional[float] = None
    ):
        """
        Emit resource utilization event for Lens Infrastructure/Performance tabs.

        Per telemetry-audit-findings.md GAP #2: PerformanceMonitor metrics
        must be transmitted to AWS for Lens visibility.

        Args:
            cpu_percent: CPU usage percentage (clamped to 0-100)
            memory_mb: Memory usage in megabytes (clamped to non-negative)
            memory_percent: Memory usage percentage (clamped to 0-100)
            gpu_utilization_percent: GPU utilization percentage (Level 4 only)
            gpu_memory_mb: GPU memory usage in MB (Level 4 only)
            pool_efficiency: Memory pool efficiency ratio (clamped to 0-1)
        """
        if not self._ensure_client():
            return

        try:
            event = {
                'event_type': 'resource_utilization',
                'timestamp': time.time(),
                'cpu_percent': _clamp_percent(cpu_percent),
                'memory_mb': _clamp_positive(memory_mb),
            }

            # Add optional fields only if provided (with sanitization)
            if memory_percent is not None:
                event['memory_percent'] = _clamp_percent(memory_percent)
            if gpu_utilization_percent is not None:
                event['gpu_utilization_percent'] = _clamp_percent(gpu_utilization_percent)
            if gpu_memory_mb is not None:
                event['gpu_memory_mb'] = _clamp_positive(gpu_memory_mb)
            if pool_efficiency is not None:
                event['pool_efficiency'] = _clamp_ratio(pool_efficiency)

            self._telemetry_client.send_telemetry(event)
        except Exception as e:
            self.logger.debug(f"Failed to emit resource utilization event: {e}")

    def emit_workload_classification(
        self,
        classification: str,
        confidence: float,
        indicators: List[str],
        detection_time_us: Optional[int] = None
    ):
        """
        Emit workload classification event for Lens Compatibility tab.

        Per telemetry-audit-findings.md GAP #3: WorkloadManifest detection
        must be transmitted to AWS for Lens visibility.

        Args:
            classification: Workload type ('ml_training', 'llm_inference',
                          'data_science', 'web_service', 'computation', 'regular_python')
            confidence: Classification confidence (clamped to 0-1)
            indicators: List of indicators that triggered classification
            detection_time_us: Detection time in microseconds (non-negative)
        """
        if not self._ensure_client():
            return

        try:
            event = {
                'event_type': 'workload_classification',
                'timestamp': time.time(),
                'classification': _truncate_string(classification, 64),
                'confidence': _clamp_ratio(confidence),
                'indicators': list(indicators) if indicators else [],
            }

            if detection_time_us is not None:
                event['detection_time_us'] = _clamp_positive(detection_time_us)

            self._telemetry_client.send_telemetry(event)
        except Exception as e:
            self.logger.debug(f"Failed to emit workload classification event: {e}")

    def emit_level_transition(
        self,
        from_level: int,
        to_level: int,
        reason: str,
        performance_delta: Optional[float] = None
    ):
        """
        Emit enhancement level transition event for Lens Performance tab.

        Per telemetry-audit-findings.md GAP #4: Level 0-4 transitions
        must be tracked for Lens visibility.

        Args:
            from_level: Previous enhancement level (clamped to 0-4)
            to_level: New enhancement level (clamped to 0-4)
            reason: Reason for level change (truncated to 256 chars)
            performance_delta: Performance change ratio (sanitized, 1.0 fallback)
        """
        if not self._ensure_client():
            return

        try:
            event = {
                'event_type': 'level_transition',
                'timestamp': time.time(),
                'from_level': _clamp_level(from_level),
                'to_level': _clamp_level(to_level),
                'reason': _truncate_string(reason),
            }

            if performance_delta is not None:
                # Use 1.0 fallback for ratio (neutral value = no change)
                event['performance_delta'] = _sanitize_float(performance_delta, fallback=1.0)

            self._telemetry_client.send_telemetry(event)
        except Exception as e:
            self.logger.debug(f"Failed to emit level transition event: {e}")


# Singleton instance for easy access
_global_emitter: Optional[RoutingEventEmitter] = None


def get_routing_emitter() -> RoutingEventEmitter:
    """Get global routing event emitter (singleton)."""
    global _global_emitter
    if _global_emitter is None:
        _global_emitter = RoutingEventEmitter()
    return _global_emitter
