"""
Epochly Advanced Monitoring

Enhanced monitoring capabilities including distributed tracing, advanced health endpoints,
and comprehensive observability features for production environments.
"""

import asyncio
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import uuid
from collections import deque

from ..utils.logger import get_logger
from ..utils.config import get_config
from .performance_monitor import get_performance_monitor
from .prometheus_exporter import get_prometheus_exporter
from .system_monitor import get_system_monitor

logger = get_logger(__name__)


class TraceLevel(Enum):
    """Trace level for distributed tracing."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class TraceSpan:
    """Distributed tracing span."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "ok"
    service_name: str = "epochly"


@dataclass
class HealthCheckResult:
    """Health check result with detailed information."""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    duration_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ServiceMetrics:
    """Service-level metrics aggregation."""
    service_name: str
    request_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    p99_duration_ms: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class DistributedTracer:
    """
    Distributed tracing implementation for Epochly.
    
    Provides OpenTelemetry-compatible tracing with span collection,
    correlation, and export capabilities.
    """
    
    def __init__(self, service_name: str = "epochly", max_spans: int = 10000):
        """
        Initialize distributed tracer.
        
        Args:
            service_name: Name of the service
            max_spans: Maximum spans to keep in memory
        """
        self.logger = get_logger(__name__)
        self.service_name = service_name
        self.max_spans = max_spans
        
        # Span storage
        self._spans: Dict[str, TraceSpan] = {}
        self._active_spans: Dict[str, TraceSpan] = {}
        self._completed_spans: deque = deque(maxlen=max_spans)
        self._lock = threading.RLock()
        
        # Metrics
        self._trace_metrics = {
            'spans_created': 0,
            'spans_completed': 0,
            'spans_failed': 0,
            'active_traces': 0
        }
    
    def start_span(
        self,
        operation_name: str,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> TraceSpan:
        """
        Start a new trace span.
        
        Args:
            operation_name: Name of the operation
            parent_span_id: Parent span ID for nested spans
            tags: Initial tags for the span
            
        Returns:
            TraceSpan: New trace span
        """
        with self._lock:
            # Generate IDs
            span_id = str(uuid.uuid4())
            trace_id = parent_span_id or str(uuid.uuid4())
            
            # Create span
            span = TraceSpan(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                operation_name=operation_name,
                start_time=datetime.now(),
                tags=tags or {},
                service_name=self.service_name
            )
            
            # Store span
            self._spans[span_id] = span
            self._active_spans[span_id] = span
            
            # Update metrics
            self._trace_metrics['spans_created'] += 1
            self._trace_metrics['active_traces'] = len(self._active_spans)
            
            self.logger.debug(f"Started span {span_id} for operation {operation_name}")
            return span
    
    def finish_span(self, span: TraceSpan, status: str = "ok"):
        """
        Finish a trace span.
        
        Args:
            span: Span to finish
            status: Final status of the span
        """
        with self._lock:
            if span.span_id not in self._active_spans:
                self.logger.warning(f"Attempting to finish inactive span {span.span_id}")
                return
            
            # Update span
            span.end_time = datetime.now()
            span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
            span.status = status
            
            # Move to completed
            del self._active_spans[span.span_id]
            self._completed_spans.append(span)
            
            # Update metrics
            self._trace_metrics['spans_completed'] += 1
            if status != "ok":
                self._trace_metrics['spans_failed'] += 1
            self._trace_metrics['active_traces'] = len(self._active_spans)
            
            self.logger.debug(f"Finished span {span.span_id} with status {status}")
    
    def add_span_tag(self, span: TraceSpan, key: str, value: Any):
        """Add a tag to a span."""
        span.tags[key] = value
    
    def add_span_log(self, span: TraceSpan, message: str, level: TraceLevel = TraceLevel.INFO):
        """Add a log entry to a span."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.value,
            'message': message
        }
        span.logs.append(log_entry)
    
    def get_active_spans(self) -> List[TraceSpan]:
        """Get all active spans."""
        with self._lock:
            return list(self._active_spans.values())
    
    def get_completed_spans(self, limit: int = 100) -> List[TraceSpan]:
        """Get recent completed spans."""
        with self._lock:
            return list(self._completed_spans)[-limit:]
    
    def get_trace_metrics(self) -> Dict[str, Any]:
        """Get tracing metrics."""
        with self._lock:
            return self._trace_metrics.copy()


class AdvancedHealthChecker:
    """
    Advanced health checking with dependency tracking and detailed diagnostics.
    """
    
    def __init__(self):
        """Initialize advanced health checker."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Health checks registry
        self._health_checks: Dict[str, Callable] = {}
        self._health_history: deque = deque(maxlen=100)
        self._dependency_map: Dict[str, List[str]] = {}
        self._lock = threading.RLock()
        
        # Configuration
        self._timeout = self.config.get('monitoring.health_timeout', 10.0)
        self._parallel_checks = self.config.get('monitoring.parallel_health_checks', True)
    
    def register_health_check(
        self,
        name: str,
        check_func: Callable,
        dependencies: Optional[List[str]] = None
    ):
        """
        Register a health check function.
        
        Args:
            name: Name of the health check
            check_func: Function that returns HealthCheckResult
            dependencies: List of dependency service names
        """
        with self._lock:
            self._health_checks[name] = check_func
            self._dependency_map[name] = dependencies or []
            self.logger.debug(f"Registered health check: {name}")
    
    async def run_health_checks(self) -> Dict[str, HealthCheckResult]:
        """
        Run all registered health checks.
        
        Returns:
            Dict mapping check names to results
        """
        results = {}
        
        if self._parallel_checks:
            # Run checks in parallel
            tasks = []
            for name, check_func in self._health_checks.items():
                task = asyncio.create_task(self._run_single_check(name, check_func))
                tasks.append(task)
            
            check_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, (name, _) in enumerate(self._health_checks.items()):
                result = check_results[i]
                if isinstance(result, Exception):
                    results[name] = HealthCheckResult(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check failed: {result}",
                        timestamp=datetime.now(),
                        duration_ms=0.0,
                        details={'error': str(result)}
                    )
                else:
                    results[name] = result
        else:
            # Run checks sequentially
            for name, check_func in self._health_checks.items():
                results[name] = await self._run_single_check(name, check_func)
        
        # Store in history
        with self._lock:
            self._health_history.append({
                'timestamp': datetime.now(),
                'results': results
            })
        
        return results
    
    async def _run_single_check(self, name: str, check_func: Callable) -> HealthCheckResult:
        """Run a single health check with timeout."""
        start_time = time.time()
        
        try:
            # Run with timeout
            result = await asyncio.wait_for(
                self._execute_check(check_func),
                timeout=self._timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if isinstance(result, HealthCheckResult):
                result.duration_ms = duration_ms
                return result
            else:
                # Convert simple result to HealthCheckResult
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                    message="Health check completed",
                    timestamp=datetime.now(),
                    duration_ms=duration_ms
                )
                
        except asyncio.TimeoutError:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self._timeout}s",
                timestamp=datetime.now(),
                duration_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {e}",
                timestamp=datetime.now(),
                duration_ms=(time.time() - start_time) * 1000,
                details={'error': str(e)}
            )
    
    async def _execute_check(self, check_func: Callable):
        """Execute a health check function."""
        if asyncio.iscoroutinefunction(check_func):
            return await check_func()
        else:
            return check_func()
    
    def get_health_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent health check history."""
        with self._lock:
            return list(self._health_history)[-limit:]


class AdvancedMonitoring:
    """
    Advanced monitoring coordinator that integrates distributed tracing,
    enhanced health checks, and comprehensive observability.
    """
    
    def __init__(self):
        """Initialize advanced monitoring."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Component references
        self.performance_monitor = get_performance_monitor()
        self.prometheus_exporter = get_prometheus_exporter()
        self.system_monitor = get_system_monitor()
        
        # Advanced components
        self.tracer = DistributedTracer()
        self.health_checker = AdvancedHealthChecker()
        
        # Service metrics
        self._service_metrics: Dict[str, ServiceMetrics] = {}
        self._lock = threading.RLock()
        
        # Monitoring state
        self._active = False
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Configuration
        self._metrics_interval = self.config.get('monitoring.advanced_interval', 30.0)
        self._trace_export_interval = self.config.get('monitoring.trace_export_interval', 60.0)
        
        # Register default health checks
        self._register_default_health_checks()
    
    async def start(self) -> bool:
        """
        Start advanced monitoring.
        
        Returns:
            bool: True if started successfully
        """
        if self._active:
            self.logger.warning("Advanced monitoring already active")
            return True
        
        try:
            self.logger.info("Starting advanced monitoring")
            
            # Start dependencies
            if not self.performance_monitor.is_active():
                self.performance_monitor.start()
            
            if not self.prometheus_exporter.is_active():
                self.prometheus_exporter.start()
            
            if not self.system_monitor.is_active():
                self.system_monitor.start()
            
            # Start monitoring loop
            self._active = True
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            self.logger.info("Advanced monitoring started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start advanced monitoring: {e}")
            self._active = False
            return False
    
    async def stop(self):
        """Stop advanced monitoring."""
        if not self._active:
            return
        
        try:
            self.logger.info("Stopping advanced monitoring")
            self._active = False
            
            # Cancel monitoring task
            if self._monitoring_task and not self._monitoring_task.done():
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("Advanced monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping advanced monitoring: {e}")
    
    def is_active(self) -> bool:
        """Check if advanced monitoring is active."""
        return self._active
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        self.logger.debug("Advanced monitoring loop started")
        
        while self._active:
            try:
                # Update service metrics
                await self._update_service_metrics()
                
                # Export traces periodically
                await self._export_traces()
                
                # Run health checks
                await self._run_periodic_health_checks()
                
                # Sleep until next interval
                await asyncio.sleep(self._metrics_interval)
                
            except Exception as e:
                self.logger.error(f"Error in advanced monitoring loop: {e}")
                await asyncio.sleep(5.0)  # Prevent tight error loop
        
        self.logger.debug("Advanced monitoring loop stopped")
    
    async def _update_service_metrics(self):
        """Update service-level metrics."""
        try:
            # Get performance metrics
            all_metrics = self.performance_monitor.get_all_metric_names()
            
            for metric_name in all_metrics:
                stats = self.performance_monitor.get_metric_stats(metric_name)
                if stats and stats.count > 0:
                    # Update service metrics
                    service_name = self._extract_service_name(metric_name)
                    
                    with self._lock:
                        if service_name not in self._service_metrics:
                            self._service_metrics[service_name] = ServiceMetrics(service_name)
                        
                        service_metrics = self._service_metrics[service_name]
                        service_metrics.request_count = stats.count
                        service_metrics.avg_duration_ms = stats.mean
                        service_metrics.p95_duration_ms = stats.percentile_95
                        service_metrics.p99_duration_ms = stats.percentile_99
                        service_metrics.last_updated = datetime.now()
                        
        except Exception as e:
            self.logger.debug(f"Error updating service metrics: {e}")
    
    def _extract_service_name(self, metric_name: str) -> str:
        """Extract service name from metric name."""
        # Simple extraction - can be enhanced based on naming conventions
        if not metric_name:
            return 'unknown'
        parts = metric_name.split('_')
        return parts[0] if parts and parts[0] else 'unknown'
    
    async def _export_traces(self):
        """Export completed traces."""
        try:
            completed_spans = self.tracer.get_completed_spans()
            
            if completed_spans:
                # In a real implementation, this would export to a tracing backend
                # Log the trace count
                self.logger.debug(f"Would export {len(completed_spans)} completed spans")
                
        except Exception as e:
            self.logger.debug(f"Error exporting traces: {e}")
    
    async def _run_periodic_health_checks(self):
        """Run periodic health checks."""
        try:
            health_results = await self.health_checker.run_health_checks()
            
            # Log any unhealthy services
            for name, result in health_results.items():
                if result.status != HealthStatus.HEALTHY:
                    self.logger.warning(f"Health check {name} is {result.status.value}: {result.message}")
                    
        except Exception as e:
            self.logger.debug(f"Error running health checks: {e}")
    
    def _register_default_health_checks(self):
        """Register default health checks."""
        self.health_checker.register_health_check(
            'performance_monitor',
            self._check_performance_monitor_health
        )
        
        self.health_checker.register_health_check(
            'prometheus_exporter',
            self._check_prometheus_health
        )
        
        self.health_checker.register_health_check(
            'system_monitor',
            self._check_system_monitor_health
        )
    
    def _check_performance_monitor_health(self) -> HealthCheckResult:
        """Check performance monitor health."""
        try:
            is_active = self.performance_monitor.is_active()
            summary = self.performance_monitor.get_system_summary()
            
            if not is_active:
                return HealthCheckResult(
                    name='performance_monitor',
                    status=HealthStatus.UNHEALTHY,
                    message='Performance monitor is not active',
                    timestamp=datetime.now(),
                    duration_ms=0.0
                )
            
            queue_size = summary.get('queue_size', 0)
            if queue_size > 1000:
                return HealthCheckResult(
                    name='performance_monitor',
                    status=HealthStatus.DEGRADED,
                    message=f'High queue size: {queue_size}',
                    timestamp=datetime.now(),
                    duration_ms=0.0,
                    details=summary
                )
            
            return HealthCheckResult(
                name='performance_monitor',
                status=HealthStatus.HEALTHY,
                message='Performance monitor is healthy',
                timestamp=datetime.now(),
                duration_ms=0.0,
                details=summary
            )
            
        except Exception as e:
            return HealthCheckResult(
                name='performance_monitor',
                status=HealthStatus.UNHEALTHY,
                message=f'Health check failed: {e}',
                timestamp=datetime.now(),
                duration_ms=0.0,
                details={'error': str(e)}
            )
    
    def _check_prometheus_health(self) -> HealthCheckResult:
        """Check Prometheus exporter health."""
        try:
            is_active = self.prometheus_exporter.is_active()
            status_info = self.prometheus_exporter.get_status()
            
            if not is_active:
                return HealthCheckResult(
                    name='prometheus_exporter',
                    status=HealthStatus.UNHEALTHY,
                    message='Prometheus exporter is not active',
                    timestamp=datetime.now(),
                    duration_ms=0.0
                )
            
            return HealthCheckResult(
                name='prometheus_exporter',
                status=HealthStatus.HEALTHY,
                message='Prometheus exporter is healthy',
                timestamp=datetime.now(),
                duration_ms=0.0,
                details=status_info
            )
            
        except Exception as e:
            return HealthCheckResult(
                name='prometheus_exporter',
                status=HealthStatus.UNHEALTHY,
                message=f'Health check failed: {e}',
                timestamp=datetime.now(),
                duration_ms=0.0,
                details={'error': str(e)}
            )
    
    def _check_system_monitor_health(self) -> HealthCheckResult:
        """Check system monitor health."""
        try:
            is_active = self.system_monitor.is_active()
            status_info = self.system_monitor.get_status()
            
            if not is_active:
                return HealthCheckResult(
                    name='system_monitor',
                    status=HealthStatus.UNHEALTHY,
                    message='System monitor is not active',
                    timestamp=datetime.now(),
                    duration_ms=0.0
                )
            
            return HealthCheckResult(
                name='system_monitor',
                status=HealthStatus.HEALTHY,
                message='System monitor is healthy',
                timestamp=datetime.now(),
                duration_ms=0.0,
                details=status_info
            )
            
        except Exception as e:
            return HealthCheckResult(
                name='system_monitor',
                status=HealthStatus.UNHEALTHY,
                message=f'Health check failed: {e}',
                timestamp=datetime.now(),
                duration_ms=0.0,
                details={'error': str(e)}
            )
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status."""
        return {
            'active': self._active,
            'components': {
                'performance_monitor': self.performance_monitor.is_active(),
                'prometheus_exporter': self.prometheus_exporter.is_active(),
                'system_monitor': self.system_monitor.is_active(),
            },
            'tracing': self.tracer.get_trace_metrics(),
            'service_metrics': {
                name: {
                    'request_count': metrics.request_count,
                    'avg_duration_ms': metrics.avg_duration_ms,
                    'p95_duration_ms': metrics.p95_duration_ms,
                    'last_updated': metrics.last_updated.isoformat()
                }
                for name, metrics in self._service_metrics.items()
            },
            'configuration': {
                'metrics_interval': self._metrics_interval,
                'trace_export_interval': self._trace_export_interval,
            }
        }


# Global advanced monitoring instance with thread safety
_advanced_monitoring: Optional[AdvancedMonitoring] = None
_monitoring_lock = threading.RLock()


def get_advanced_monitoring() -> AdvancedMonitoring:
    """Get the global advanced monitoring instance with thread safety."""
    global _advanced_monitoring
    if _advanced_monitoring is None:
        with _monitoring_lock:
            # Double-check locking pattern
            if _advanced_monitoring is None:
                _advanced_monitoring = AdvancedMonitoring()
    return _advanced_monitoring


# Convenience functions for tracing
def start_trace(operation_name: str, **tags) -> TraceSpan:
    """Start a new trace span."""
    monitoring = get_advanced_monitoring()
    return monitoring.tracer.start_span(operation_name, tags=tags)


def finish_trace(span: TraceSpan, status: str = "ok"):
    """Finish a trace span."""
    monitoring = get_advanced_monitoring()
    monitoring.tracer.finish_span(span, status)