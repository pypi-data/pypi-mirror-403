"""
Epochly Metrics Collector

System metrics collection for CPU, memory, and other system resources.
"""

import sys
import time
import threading
import psutil
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..utils.logger import get_logger
from ..utils.config import get_config
from .performance_monitor import get_performance_monitor


# Use slots=True only for Python 3.10+ (PEP 681)
_dataclass_kwargs = {'slots': True} if sys.version_info >= (3, 10) else {}


@dataclass(**_dataclass_kwargs)
class SystemMetrics:
    """Container for system metrics snapshot."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available: int
    memory_used: int
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    load_average: Optional[List[float]] = None


class MetricsCollector:
    """
    System metrics collector for Epochly monitoring.
    
    Collects CPU, memory, disk, network, and process metrics
    and forwards them to the performance monitor.
    """
    
    def __init__(self):
        """Initialize the metrics collector."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.performance_monitor = get_performance_monitor()
        
        # Collection state
        self._active = False
        self._thread = None
        self._stop_event = threading.Event()
        
        # Configuration
        self._interval = self.config.get('monitoring.interval', 1.0)
        self._collect_network = True
        self._collect_disk = True
        self._collect_processes = True

        # Derived sampling configuration
        self._psutil_check_interval = self._coerce_positive(
            self.config.get('monitoring.psutil_check_interval', 30.0),
            minimum=0.05,
        )
        process_refresh_default = max(self._interval, 1.0)
        self._process_refresh_interval = max(
            self._coerce_positive(
                self.config.get(
                    'monitoring.process_refresh_interval',
                    process_refresh_default,
                ),
                minimum=0.05,
            ),
            self._interval,
        )

        # Baseline metrics for delta calculations
        self._last_network_stats = None
        self._last_cpu_times = None

        # Process-specific monitoring
        self._current_process = psutil.Process()
        self._monitor_current_process = True
        self._last_process_count = 0
        self._last_process_count_time = 0.0

        # Cached capability checks
        self._psutil_available = None
        self._psutil_check_timestamp = 0.0
    
    def start(self) -> bool:
        """
        Start metrics collection.
        
        Returns:
            bool: True if started successfully
        """
        if self._active:
            self.logger.warning("Metrics collector already active")
            return True
        
        try:
            self.logger.info("Starting metrics collector")
            
            # Verify psutil availability
            if not self._check_psutil_availability(force=True):
                self.logger.error("psutil not available or insufficient permissions")
                return False
            
            # Initialize baseline metrics
            self._initialize_baselines()
            
            # Reset state
            self._stop_event.clear()
            
            # Start collection thread
            self._thread = threading.Thread(
                target=self._collection_loop,
                name="Epochly-MetricsCollector",
                daemon=True
            )
            self._thread.start()
            
            self._active = True
            self.logger.info("Metrics collector started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start metrics collector: {e}")
            return False
    
    def stop(self):
        """Stop metrics collection."""
        if not self._active:
            return
        
        try:
            self.logger.info("Stopping metrics collector")
            
            # Signal stop and wait for thread
            self._stop_event.set()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5.0)
            
            self._active = False
            self.logger.info("Metrics collector stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping metrics collector: {e}")
    
    def is_active(self) -> bool:
        """Check if the collector is active."""
        return self._active
    
    def _coerce_positive(self, value, minimum: float) -> float:
        try:
            coerced = float(value)
        except (TypeError, ValueError):
            return minimum
        return max(coerced, minimum)

    def _check_psutil_availability(self, force: bool = False) -> bool:
        """Check if psutil is available and has necessary permissions."""
        now = time.monotonic()
        if (
            not force
            and self._psutil_available is not None
            and (now - self._psutil_check_timestamp) < self._psutil_check_interval
        ):
            return self._psutil_available

        try:
            # Test basic psutil functions
            psutil.cpu_percent(interval=None)
            psutil.virtual_memory()
            psutil.disk_usage('/')
            available = True
        except Exception as e:
            self.logger.error(f"psutil availability check failed: {e}")
            available = False

        self._psutil_available = available
        self._psutil_check_timestamp = now
        return available
    
    def _initialize_baselines(self):
        """Initialize baseline metrics for delta calculations."""
        try:
            # Initialize network stats
            if self._collect_network:
                self._last_network_stats = psutil.net_io_counters()
            
            # Initialize CPU times
            self._last_cpu_times = psutil.cpu_times()
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize baselines: {e}")
    
    def _collection_loop(self):
        """Main collection loop running in background thread."""
        self.logger.debug("Metrics collection loop started")
        
        while not self._stop_event.is_set():
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                
                # Record metrics with performance monitor
                self._record_metrics(metrics)
                
                # Collect process-specific metrics if enabled
                if self._monitor_current_process:
                    self._collect_process_metrics()
                
                # Sleep until next interval
                self._stop_event.wait(self._interval)
                
            except Exception as e:
                self.logger.error(f"Error in collection loop: {e}")
                time.sleep(1.0)  # Prevent tight error loop
        
        self.logger.debug("Metrics collection loop stopped")
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        timestamp = time.time()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available = memory.available
        memory_used = memory.used
        
        # Disk metrics
        disk_usage_percent = 0.0
        if self._collect_disk:
            try:
                disk = psutil.disk_usage('/')
                if hasattr(disk, 'percent') and disk.percent is not None:
                    disk_usage_percent = float(disk.percent)
                elif disk.total > 0:
                    disk_usage_percent = (disk.used / disk.total) * 100
                else:
                    disk_usage_percent = 0.0  # Prevent division by zero
            except Exception as e:
                self.logger.debug(f"Failed to collect disk metrics: {e}")
        
        # Network metrics
        network_bytes_sent = 0
        network_bytes_recv = 0
        if self._collect_network:
            try:
                net_io = psutil.net_io_counters()
                if net_io:
                    network_bytes_sent = net_io.bytes_sent
                    network_bytes_recv = net_io.bytes_recv
            except Exception as e:
                self.logger.debug(f"Failed to collect network metrics: {e}")
        
        # Process count
        process_count = self._get_process_count()
        
        # Load average (Unix-like systems only)
        load_average = None
        try:
            if hasattr(psutil, 'getloadavg'):
                load_average = list(psutil.getloadavg())
        except Exception:
            pass  # Not available on Windows
        
        return SystemMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available=memory_available,
            memory_used=memory_used,
            disk_usage_percent=disk_usage_percent,
            network_bytes_sent=network_bytes_sent,
            network_bytes_recv=network_bytes_recv,
            process_count=process_count,
            load_average=load_average
        )
    
    def _record_metrics(self, metrics: SystemMetrics):
        """Record metrics with the performance monitor."""
        try:
            # Record CPU metrics
            self.performance_monitor.record_metric(
                'cpu_usage',
                metrics.cpu_percent,
                'percent',
                {'timestamp': metrics.timestamp}
            )
            
            # Record memory metrics
            self.performance_monitor.record_metric(
                'memory_usage',
                metrics.memory_percent,
                'percent',
                {'available': metrics.memory_available, 'used': metrics.memory_used}
            )
            
            # Record disk metrics
            if metrics.disk_usage_percent > 0:
                self.performance_monitor.record_metric(
                    'disk_usage',
                    metrics.disk_usage_percent,
                    'percent'
                )
            
            # Record network metrics
            if metrics.network_bytes_sent > 0 or metrics.network_bytes_recv > 0:
                self.performance_monitor.record_metric(
                    'network_bytes_sent',
                    metrics.network_bytes_sent,
                    'bytes'
                )
                self.performance_monitor.record_metric(
                    'network_bytes_recv',
                    metrics.network_bytes_recv,
                    'bytes'
                )
            
            # Record process count
            if metrics.process_count > 0:
                self.performance_monitor.record_metric(
                    'process_count',
                    metrics.process_count,
                    'count'
                )
            
            # Record load average (if available)
            if metrics.load_average:
                for i, load in enumerate(metrics.load_average):
                    self.performance_monitor.record_metric(
                        f'load_average_{i+1}min',
                        load,
                        'load'
                    )
            
        except Exception as e:
            self.logger.error(f"Failed to record metrics: {e}")
    
    def _collect_process_metrics(self):
        """Collect metrics for the current process."""
        try:
            # Process CPU usage
            cpu_percent = self._current_process.cpu_percent()
            self.performance_monitor.record_metric(
                'process_cpu_usage',
                cpu_percent,
                'percent',
                {'pid': self._current_process.pid}
            )
            
            # Process memory usage
            memory_info = self._current_process.memory_info()
            memory_percent = self._current_process.memory_percent()
            
            self.performance_monitor.record_metric(
                'process_memory_usage',
                memory_percent,
                'percent',
                {
                    'rss': memory_info.rss,
                    'vms': memory_info.vms,
                    'pid': self._current_process.pid
                }
            )
            
            # Process thread count
            num_threads = self._current_process.num_threads()
            self.performance_monitor.record_metric(
                'process_thread_count',
                num_threads,
                'count',
                {'pid': self._current_process.pid}
            )
            
            # Process file descriptors (Unix-like systems)
            try:
                # Use getattr to safely check for num_fds method
                num_fds_method = getattr(self._current_process, 'num_fds', None)
                if num_fds_method and callable(num_fds_method):
                    num_fds = num_fds_method()
                    # Safely convert to float, handling potential type issues
                    if isinstance(num_fds, (int, float)):
                        self.performance_monitor.record_metric(
                            'process_file_descriptors',
                            float(num_fds),
                            'count',
                            {'pid': self._current_process.pid}
                        )
            except Exception:
                pass  # Not available on Windows
            
        except Exception as e:
            self.logger.debug(f"Failed to collect process metrics: {e}")
    
    def _get_process_count(self) -> int:
        """Return the process count using cached sampling to avoid heavy scans."""
        if not self._collect_processes:
            return 0

        now = time.monotonic()
        if self._last_process_count_time and (
            now - self._last_process_count_time
        ) < self._process_refresh_interval:
            return self._last_process_count

        try:
            process_count = len(psutil.pids())
            self._last_process_count = process_count
            self._last_process_count_time = now
            return process_count
        except Exception as e:
            self.logger.debug(f"Failed to collect process count: {e}")
            return self._last_process_count

    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """
        Get current system metrics snapshot.

        Returns:
            SystemMetrics or None if collection fails
        """
        try:
            return self._collect_system_metrics()
        except Exception as e:
            self.logger.error(f"Failed to get current metrics: {e}")
            return None
    
    def configure(self, **kwargs):
        """
        Configure metrics collection settings.
        
        Args:
            **kwargs: Configuration parameters
        """
        if 'interval' in kwargs:
            self._interval = float(kwargs['interval'])
            self.logger.debug(f"Set collection interval to {self._interval}s")
        
        if 'collect_network' in kwargs:
            self._collect_network = bool(kwargs['collect_network'])
            self.logger.debug(f"Network collection: {self._collect_network}")
        
        if 'collect_disk' in kwargs:
            self._collect_disk = bool(kwargs['collect_disk'])
            self.logger.debug(f"Disk collection: {self._collect_disk}")
        
        if 'collect_processes' in kwargs:
            self._collect_processes = bool(kwargs['collect_processes'])
            self.logger.debug(f"Process collection: {self._collect_processes}")
        
        if 'monitor_current_process' in kwargs:
            self._monitor_current_process = bool(kwargs['monitor_current_process'])
            self.logger.debug(f"Current process monitoring: {self._monitor_current_process}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get collector status information.
        
        Returns:
            Dictionary containing status information
        """
        return {
            'active': self._active,
            'interval': self._interval,
            'collect_network': self._collect_network,
            'collect_disk': self._collect_disk,
            'collect_processes': self._collect_processes,
            'monitor_current_process': self._monitor_current_process,
            'current_process_pid': self._current_process.pid,
            'psutil_available': self._check_psutil_availability(),
        }


# Global metrics collector instance with thread safety
_metrics_collector = None
_collector_lock = threading.RLock()

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance with thread safety."""
    global _metrics_collector
    if _metrics_collector is None:
        with _collector_lock:
            # Double-check locking pattern
            if _metrics_collector is None:
                _metrics_collector = MetricsCollector()
    return _metrics_collector