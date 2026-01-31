"""
Epochly System Monitor

High-level system monitoring and health checks for the Epochly framework.
"""

import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from ..utils.logger import get_logger
from ..utils.config import get_config
from .performance_monitor import get_performance_monitor
from .metrics_collector import get_metrics_collector


class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Container for health check results."""
    name: str
    status: HealthStatus
    message: str
    timestamp: float
    details: Dict[str, Any]


@dataclass
class SystemHealth:
    """Overall system health summary."""
    overall_status: HealthStatus
    timestamp: float
    checks: List[HealthCheck]
    metrics_summary: Dict[str, Any]


class SystemMonitor:
    """
    High-level system monitoring and health assessment.
    
    Coordinates with performance monitor and metrics collector
    to provide comprehensive system health reporting.
    """
    
    def __init__(self):
        """Initialize the system monitor."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Component references
        self.performance_monitor = get_performance_monitor()
        self.metrics_collector = get_metrics_collector()
        
        # Monitoring state
        self._active = False
        self._thread = None
        self._stop_event = threading.Event()
        
        # Configuration
        self._check_interval = self.config.get('monitoring.interval', 30.0)
        self._health_retention = 100  # Keep last 100 health checks
        
        # Health checks registry
        self._health_checks = {}
        self._health_history = []
        self._lock = threading.RLock()
        
        # Health thresholds
        self._thresholds = {
            'cpu_usage': {'warning': 70.0, 'critical': 90.0},
            'memory_usage': {'warning': 80.0, 'critical': 95.0},
            'disk_usage': {'warning': 85.0, 'critical': 95.0},
            'response_time': {'warning': 1.0, 'critical': 5.0},
        }
        
        # Register default health checks
        self._register_default_checks()
    
    def start(self) -> bool:
        """
        Start system monitoring.
        
        Returns:
            bool: True if started successfully
        """
        if self._active:
            self.logger.warning("System monitor already active")
            return True
        
        try:
            self.logger.info("Starting system monitor")
            
            # Ensure dependencies are running
            if not self.performance_monitor.is_active():
                self.performance_monitor.start()
            
            if not self.metrics_collector.is_active():
                self.metrics_collector.start()
            
            # Reset state
            self._stop_event.clear()
            
            # Start monitoring thread
            self._thread = threading.Thread(
                target=self._monitoring_loop,
                name="Epochly-SystemMonitor",
                daemon=True
            )
            self._thread.start()
            
            self._active = True
            self.logger.info("System monitor started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start system monitor: {e}")
            return False
    
    def stop(self):
        """Stop system monitoring."""
        if not self._active:
            return
        
        try:
            self.logger.info("Stopping system monitor")
            
            # Signal stop and wait for thread
            self._stop_event.set()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5.0)
            
            self._active = False
            self.logger.info("System monitor stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping system monitor: {e}")
    
    def is_active(self) -> bool:
        """Check if the monitor is active."""
        return self._active
    
    def _register_default_checks(self):
        """Register default health checks."""
        self.register_health_check('cpu_usage', self._check_cpu_usage)
        self.register_health_check('memory_usage', self._check_memory_usage)
        self.register_health_check('disk_usage', self._check_disk_usage)
        self.register_health_check('performance_monitor', self._check_performance_monitor)
        self.register_health_check('metrics_collector', self._check_metrics_collector)
    
    def register_health_check(self, name: str, check_func: Callable[[], HealthCheck]):
        """
        Register a health check function.
        
        Args:
            name: Name of the health check
            check_func: Function that returns a HealthCheck
        """
        with self._lock:
            self._health_checks[name] = check_func
            self.logger.debug(f"Registered health check: {name}")
    
    def unregister_health_check(self, name: str):
        """
        Unregister a health check.
        
        Args:
            name: Name of the health check to remove
        """
        with self._lock:
            if name in self._health_checks:
                del self._health_checks[name]
                self.logger.debug(f"Unregistered health check: {name}")
    
    def _monitoring_loop(self):
        """Main monitoring loop running in background thread."""
        self.logger.debug("System monitoring loop started")

        while not self._stop_event.is_set():
            try:
                # Check if Python is shutting down - exit immediately
                import sys
                if sys.is_finalizing():
                    break

                # Perform health checks
                health = self._perform_health_checks()

                # Store health result
                self._store_health_result(health)

                # Log health status if not healthy
                if health.overall_status != HealthStatus.HEALTHY:
                    self._log_health_issues(health)

                # Sleep until next check
                self._stop_event.wait(self._check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5.0)  # Prevent tight error loop
        
        self.logger.debug("System monitoring loop stopped")
    
    def _perform_health_checks(self) -> SystemHealth:
        """Perform all registered health checks."""
        timestamp = time.time()
        checks = []
        
        with self._lock:
            for name, check_func in self._health_checks.items():
                try:
                    check_result = check_func()
                    checks.append(check_result)
                except Exception as e:
                    # Create error health check
                    error_check = HealthCheck(
                        name=name,
                        status=HealthStatus.CRITICAL,
                        message=f"Health check failed: {e}",
                        timestamp=timestamp,
                        details={'error': str(e)}
                    )
                    checks.append(error_check)
                    self.logger.error(f"Health check {name} failed: {e}")
        
        # Determine overall status
        overall_status = self._calculate_overall_status(checks)
        
        # Get metrics summary
        metrics_summary = self._get_metrics_summary()
        
        return SystemHealth(
            overall_status=overall_status,
            timestamp=timestamp,
            checks=checks,
            metrics_summary=metrics_summary
        )
    
    def _calculate_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Calculate overall health status from individual checks."""
        if not checks:
            return HealthStatus.UNKNOWN
        
        # If any check is critical, overall is critical
        if any(check.status == HealthStatus.CRITICAL for check in checks):
            return HealthStatus.CRITICAL
        
        # If any check is warning, overall is warning
        if any(check.status == HealthStatus.WARNING for check in checks):
            return HealthStatus.WARNING
        
        # All checks are healthy
        return HealthStatus.HEALTHY
    
    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of key metrics."""
        summary = {}
        
        try:
            # Get recent metrics from performance monitor
            for metric_name in ['cpu_usage', 'memory_usage', 'disk_usage']:
                stats = self.performance_monitor.get_metric_stats(metric_name)
                if stats:
                    summary[metric_name] = {
                        'current': stats.mean,
                        'max': stats.max_value,
                        'count': stats.count
                    }
            
            # Get system metrics from collector
            current_metrics = self.metrics_collector.get_current_metrics()
            if current_metrics:
                summary['system_snapshot'] = {
                    'cpu_percent': current_metrics.cpu_percent,
                    'memory_percent': current_metrics.memory_percent,
                    'process_count': current_metrics.process_count
                }
        
        except Exception as e:
            self.logger.debug(f"Failed to get metrics summary: {e}")
        
        return summary
    
    def _store_health_result(self, health: SystemHealth):
        """Store health check result in history."""
        with self._lock:
            self._health_history.append(health)
            
            # Maintain history size
            if len(self._health_history) > self._health_retention:
                self._health_history.pop(0)
    
    def _log_health_issues(self, health: SystemHealth):
        """Log health issues for non-healthy status."""
        # Skip logging in test mode to prevent spam when monitors aren't started
        import os
        if os.environ.get('EPOCHLY_TEST_MODE') == '1':
            return

        issues = [check for check in health.checks
                 if check.status in (HealthStatus.WARNING, HealthStatus.CRITICAL)]

        for issue in issues:
            if issue.status == HealthStatus.CRITICAL:
                self.logger.error(f"CRITICAL: {issue.name} - {issue.message}")
            else:
                self.logger.warning(f"WARNING: {issue.name} - {issue.message}")
    
    def _check_cpu_usage(self) -> HealthCheck:
        """Check CPU usage health."""
        timestamp = time.time()
        
        try:
            stats = self.performance_monitor.get_metric_stats('cpu_usage')
            if not stats or stats.count == 0:
                return HealthCheck(
                    name='cpu_usage',
                    status=HealthStatus.UNKNOWN,
                    message='No CPU usage data available',
                    timestamp=timestamp,
                    details={}
                )
            
            current_usage = stats.mean
            thresholds = self._thresholds['cpu_usage']
            
            if current_usage >= thresholds['critical']:
                status = HealthStatus.CRITICAL
                message = f"CPU usage critical: {current_usage:.1f}%"
            elif current_usage >= thresholds['warning']:
                status = HealthStatus.WARNING
                message = f"CPU usage high: {current_usage:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage normal: {current_usage:.1f}%"
            
            return HealthCheck(
                name='cpu_usage',
                status=status,
                message=message,
                timestamp=timestamp,
                details={
                    'current': current_usage,
                    'max': stats.max_value,
                    'samples': stats.count
                }
            )
        
        except Exception as e:
            return HealthCheck(
                name='cpu_usage',
                status=HealthStatus.CRITICAL,
                message=f"CPU check failed: {e}",
                timestamp=timestamp,
                details={'error': str(e)}
            )
    
    def _check_memory_usage(self) -> HealthCheck:
        """Check memory usage health."""
        timestamp = time.time()
        
        try:
            stats = self.performance_monitor.get_metric_stats('memory_usage')
            if not stats or stats.count == 0:
                return HealthCheck(
                    name='memory_usage',
                    status=HealthStatus.UNKNOWN,
                    message='No memory usage data available',
                    timestamp=timestamp,
                    details={}
                )
            
            current_usage = stats.mean
            thresholds = self._thresholds['memory_usage']
            
            if current_usage >= thresholds['critical']:
                status = HealthStatus.CRITICAL
                message = f"Memory usage critical: {current_usage:.1f}%"
            elif current_usage >= thresholds['warning']:
                status = HealthStatus.WARNING
                message = f"Memory usage high: {current_usage:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {current_usage:.1f}%"
            
            return HealthCheck(
                name='memory_usage',
                status=status,
                message=message,
                timestamp=timestamp,
                details={
                    'current': current_usage,
                    'max': stats.max_value,
                    'samples': stats.count
                }
            )
        
        except Exception as e:
            return HealthCheck(
                name='memory_usage',
                status=HealthStatus.CRITICAL,
                message=f"Memory check failed: {e}",
                timestamp=timestamp,
                details={'error': str(e)}
            )
    
    def _check_disk_usage(self) -> HealthCheck:
        """Check disk usage health."""
        timestamp = time.time()
        
        try:
            stats = self.performance_monitor.get_metric_stats('disk_usage')
            if not stats or stats.count == 0:
                return HealthCheck(
                    name='disk_usage',
                    status=HealthStatus.UNKNOWN,
                    message='No disk usage data available',
                    timestamp=timestamp,
                    details={}
                )
            
            current_usage = stats.mean
            thresholds = self._thresholds['disk_usage']
            
            if current_usage >= thresholds['critical']:
                status = HealthStatus.CRITICAL
                message = f"Disk usage critical: {current_usage:.1f}%"
            elif current_usage >= thresholds['warning']:
                status = HealthStatus.WARNING
                message = f"Disk usage high: {current_usage:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {current_usage:.1f}%"
            
            return HealthCheck(
                name='disk_usage',
                status=status,
                message=message,
                timestamp=timestamp,
                details={
                    'current': current_usage,
                    'max': stats.max_value,
                    'samples': stats.count
                }
            )
        
        except Exception as e:
            return HealthCheck(
                name='disk_usage',
                status=HealthStatus.CRITICAL,
                message=f"Disk check failed: {e}",
                timestamp=timestamp,
                details={'error': str(e)}
            )
    
    def _check_performance_monitor(self) -> HealthCheck:
        """Check performance monitor health."""
        timestamp = time.time()

        try:
            if not self.performance_monitor.is_active():
                # During shutdown, monitors being inactive is expected, not CRITICAL
                import sys
                if sys.is_finalizing() or self._stop_event.is_set():
                    return HealthCheck(
                        name='performance_monitor',
                        status=HealthStatus.HEALTHY,
                        message='Performance monitor stopped (shutdown)',
                        timestamp=timestamp,
                        details={}
                    )

                return HealthCheck(
                    name='performance_monitor',
                    status=HealthStatus.CRITICAL,
                    message='Performance monitor not active',
                    timestamp=timestamp,
                    details={}
                )
            
            summary = self.performance_monitor.get_system_summary()
            queue_size = summary.get('queue_size', 0)
            
            if queue_size > 1000:
                status = HealthStatus.WARNING
                message = f"Performance monitor queue size high: {queue_size}"
            else:
                status = HealthStatus.HEALTHY
                message = f"Performance monitor healthy (queue: {queue_size})"
            
            return HealthCheck(
                name='performance_monitor',
                status=status,
                message=message,
                timestamp=timestamp,
                details=summary
            )
        
        except Exception as e:
            return HealthCheck(
                name='performance_monitor',
                status=HealthStatus.CRITICAL,
                message=f"Performance monitor check failed: {e}",
                timestamp=timestamp,
                details={'error': str(e)}
            )
    
    def _check_metrics_collector(self) -> HealthCheck:
        """Check metrics collector health."""
        timestamp = time.time()

        try:
            if not self.metrics_collector.is_active():
                # During shutdown, monitors being inactive is expected, not CRITICAL
                import sys
                if sys.is_finalizing() or self._stop_event.is_set():
                    return HealthCheck(
                        name='metrics_collector',
                        status=HealthStatus.HEALTHY,
                        message='Metrics collector stopped (shutdown)',
                        timestamp=timestamp,
                        details={}
                    )

                return HealthCheck(
                    name='metrics_collector',
                    status=HealthStatus.CRITICAL,
                    message='Metrics collector not active',
                    timestamp=timestamp,
                    details={}
                )
            
            status_info = self.metrics_collector.get_status()
            
            return HealthCheck(
                name='metrics_collector',
                status=HealthStatus.HEALTHY,
                message='Metrics collector healthy',
                timestamp=timestamp,
                details=status_info
            )
        
        except Exception as e:
            return HealthCheck(
                name='metrics_collector',
                status=HealthStatus.CRITICAL,
                message=f"Metrics collector check failed: {e}",
                timestamp=timestamp,
                details={'error': str(e)}
            )
    
    def get_current_health(self) -> Optional[SystemHealth]:
        """
        Get current system health status.
        
        Returns:
            SystemHealth or None if no health data available
        """
        with self._lock:
            if self._health_history:
                return self._health_history[-1]
            return None
    
    def get_health_history(self, count: int = 10) -> List[SystemHealth]:
        """
        Get recent health check history.
        
        Args:
            count: Number of recent health checks to return
            
        Returns:
            List of recent SystemHealth objects
        """
        with self._lock:
            return self._health_history[-count:]
    
    def set_threshold(self, metric: str, warning: float, critical: float):
        """
        Set health thresholds for a metric.
        
        Args:
            metric: Metric name
            warning: Warning threshold
            critical: Critical threshold
        """
        self._thresholds[metric] = {
            'warning': warning,
            'critical': critical
        }
        self.logger.debug(f"Set thresholds for {metric}: warning={warning}, critical={critical}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get system monitor status.
        
        Returns:
            Dictionary containing status information
        """
        current_health = self.get_current_health()
        
        return {
            'active': self._active,
            'check_interval': self._check_interval,
            'registered_checks': list(self._health_checks.keys()),
            'health_history_size': len(self._health_history),
            'current_health': current_health.overall_status.value if current_health else None,
            'thresholds': self._thresholds.copy(),
            'performance_monitor_active': self.performance_monitor.is_active(),
            'metrics_collector_active': self.metrics_collector.is_active(),
        }


# Global system monitor instance with thread safety
_system_monitor = None
_monitor_lock = threading.RLock()

def get_system_monitor() -> SystemMonitor:
    """Get the global system monitor instance with thread safety."""
    global _system_monitor
    if _system_monitor is None:
        with _monitor_lock:
            # Double-check locking pattern
            if _system_monitor is None:
                _system_monitor = SystemMonitor()
    return _system_monitor