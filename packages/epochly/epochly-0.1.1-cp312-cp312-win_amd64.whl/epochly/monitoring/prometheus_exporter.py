"""
Epochly Prometheus Exporter

Prometheus metrics exporter for Epochly monitoring data.
"""

import time
import threading
from typing import Dict, Any, List
from http.server import HTTPServer, BaseHTTPRequestHandler

from ..utils.logger import get_logger
from ..utils.config import get_config
from .performance_monitor import get_performance_monitor


class PrometheusMetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint."""
    
    def __init__(self, exporter, *args, **kwargs):
        """Initialize handler with exporter reference."""
        self.exporter = exporter
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests for metrics."""
        try:
            if self.path == '/metrics':
                self._serve_metrics()
            elif self.path == '/health':
                self._serve_health()
            else:
                self._serve_404()
        except Exception as e:
            self.exporter.logger.error(f"Error serving request: {e}")
            self._serve_500()
    
    def _serve_metrics(self):
        """Serve Prometheus metrics."""
        try:
            metrics_data = self.exporter.get_prometheus_metrics()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(metrics_data.encode('utf-8'))
            
        except Exception as e:
            self.exporter.logger.error(f"Error generating metrics: {e}")
            self._serve_500()
    
    def _serve_health(self):
        """Serve health check endpoint."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
    
    def _serve_404(self):
        """Serve 404 response."""
        self.send_response(404)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Not Found')
    
    def _serve_500(self):
        """Serve 500 response."""
        self.send_response(500)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Internal Server Error')
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        self.exporter.logger.debug(f"HTTP: {format % args}")


class PrometheusExporter:
    """
    Prometheus metrics exporter for Epochly.
    
    Exports Epochly performance metrics in Prometheus format
    via HTTP endpoint.
    """
    
    def __init__(self, port: int = 8000):
        """
        Initialize Prometheus exporter.
        
        Args:
            port: HTTP port for metrics endpoint
        """
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.performance_monitor = get_performance_monitor()
        
        # Server configuration
        self.port = port
        self.host = '0.0.0.0'
        
        # Server state
        self._server = None
        self._thread = None
        self._active = False
        
        # Metrics configuration
        self._metric_prefix = 'epochly_'
        self._include_labels = True
        
        # Metric type mappings
        self._metric_types = {
            'cpu_usage': 'gauge',
            'memory_usage': 'gauge',
            'disk_usage': 'gauge',
            'network_bytes_sent': 'counter',
            'network_bytes_recv': 'counter',
            'process_count': 'gauge',
            'response_time': 'histogram',
            'error_rate': 'gauge',
        }
    
    def start(self) -> bool:
        """
        Start the Prometheus exporter server.
        
        Returns:
            bool: True if started successfully
        """
        if self._active:
            self.logger.warning("Prometheus exporter already active")
            return True
        
        try:
            self.logger.info(f"Starting Prometheus exporter on port {self.port}")
            
            # Create HTTP server
            def handler_factory(*args, **kwargs):
                return PrometheusMetricsHandler(self, *args, **kwargs)
            
            self._server = HTTPServer((self.host, self.port), handler_factory)
            
            # Start server in background thread
            self._thread = threading.Thread(
                target=self._server_loop,
                name="Epochly-PrometheusExporter",
                daemon=True
            )
            self._thread.start()
            
            self._active = True
            self.logger.info(f"Prometheus exporter started on http://{self.host}:{self.port}/metrics")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Prometheus exporter: {e}")
            return False
    
    def stop(self):
        """Stop the Prometheus exporter server."""
        if not self._active:
            return
        
        try:
            self.logger.info("Stopping Prometheus exporter")
            
            # Shutdown server
            if self._server:
                self._server.shutdown()
                self._server.server_close()
            
            # Wait for thread to finish
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5.0)
            
            self._active = False
            self.logger.info("Prometheus exporter stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping Prometheus exporter: {e}")
    
    def is_active(self) -> bool:
        """Check if the exporter is active."""
        return self._active
    
    def _server_loop(self):
        """Main server loop."""
        try:
            self.logger.debug("Prometheus exporter server loop started")
            server = self._server
            if server is not None:
                server.serve_forever()
        except Exception as e:
            self.logger.error(f"Error in server loop: {e}")
        finally:
            self.logger.debug("Prometheus exporter server loop stopped")
    
    def get_prometheus_metrics(self) -> str:
        """
        Generate Prometheus metrics format.
        
        Returns:
            String containing Prometheus metrics
        """
        try:
            metrics_lines = []
            
            # Add metadata
            metrics_lines.append(f"# HELP {self._metric_prefix}info Epochly system information")
            metrics_lines.append(f"# TYPE {self._metric_prefix}info gauge")
            metrics_lines.append(f'{self._metric_prefix}info{{version="0.1.0"}} 1')
            metrics_lines.append("")
            
            # Get all metric names from performance monitor
            metric_names = self.performance_monitor.get_all_metric_names()
            
            for metric_name in metric_names:
                stats = self.performance_monitor.get_metric_stats(metric_name)
                if stats and stats.count > 0:
                    # Add metric help and type
                    prometheus_name = self._sanitize_metric_name(metric_name)
                    metric_type = self._metric_types.get(metric_name, 'gauge')
                    
                    metrics_lines.append(f"# HELP {self._metric_prefix}{prometheus_name} {metric_name} metric")
                    metrics_lines.append(f"# TYPE {self._metric_prefix}{prometheus_name} {metric_type}")
                    
                    # Add metric values
                    if metric_type == 'histogram':
                        metrics_lines.extend(self._format_histogram_metric(prometheus_name, stats))
                    else:
                        metrics_lines.extend(self._format_simple_metric(prometheus_name, stats))
                    
                    metrics_lines.append("")
            
            # Add system health metrics
            metrics_lines.extend(self._get_system_health_metrics())
            
            return '\n'.join(metrics_lines)
            
        except Exception as e:
            self.logger.error(f"Error generating Prometheus metrics: {e}")
            return f"# Error generating metrics: {e}\n"
    
    def _sanitize_metric_name(self, name: str) -> str:
        """
        Sanitize metric name for Prometheus format.
        
        Args:
            name: Original metric name
            
        Returns:
            Sanitized metric name
        """
        # Replace invalid characters with underscores
        sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in name)
        
        # Ensure it starts with a letter or underscore
        if sanitized and not (sanitized[0].isalpha() or sanitized[0] == '_'):
            sanitized = '_' + sanitized
        
        return sanitized.lower()
    
    def _format_simple_metric(self, name: str, stats) -> List[str]:
        """
        Format simple metric (gauge/counter) for Prometheus.
        
        Args:
            name: Metric name
            stats: Performance stats
            
        Returns:
            List of metric lines
        """
        lines = []
        timestamp = int(time.time() * 1000)
        
        # Current value (mean)
        lines.append(f'{self._metric_prefix}{name} {stats.mean} {timestamp}')
        
        # Additional statistics as separate metrics
        lines.append(f'{self._metric_prefix}{name}_max {stats.max_value} {timestamp}')
        lines.append(f'{self._metric_prefix}{name}_min {stats.min_value} {timestamp}')
        lines.append(f'{self._metric_prefix}{name}_count {stats.count} {timestamp}')
        
        return lines
    
    def _format_histogram_metric(self, name: str, stats) -> List[str]:
        """
        Format histogram metric for Prometheus.
        
        Args:
            name: Metric name
            stats: Performance stats
            
        Returns:
            List of metric lines
        """
        lines = []
        timestamp = int(time.time() * 1000)
        
        # Histogram buckets (simplified)
        buckets = [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf')]
        
        for bucket in buckets:
            # Estimate count for this bucket (simplified)
            if bucket == float('inf'):
                bucket_count = stats.count
            else:
                # Rough estimation based on percentiles
                if bucket <= stats.percentile_95:
                    bucket_count = int(stats.count * 0.95)
                elif bucket <= stats.percentile_99:
                    bucket_count = int(stats.count * 0.99)
                else:
                    bucket_count = stats.count
            
            bucket_str = '+Inf' if bucket == float('inf') else str(bucket)
            lines.append(f'{self._metric_prefix}{name}_bucket{{le="{bucket_str}"}} {bucket_count} {timestamp}')
        
        # Histogram sum and count
        histogram_sum = stats.mean * stats.count
        lines.append(f'{self._metric_prefix}{name}_sum {histogram_sum} {timestamp}')
        lines.append(f'{self._metric_prefix}{name}_count {stats.count} {timestamp}')
        
        return lines
    
    def _get_system_health_metrics(self) -> List[str]:
        """
        Get system health metrics for Prometheus.
        
        Returns:
            List of health metric lines
        """
        lines = []
        timestamp = int(time.time() * 1000)
        
        try:
            # Performance monitor status
            pm_active = 1 if self.performance_monitor.is_active() else 0
            lines.append(f"# HELP {self._metric_prefix}performance_monitor_active Performance monitor status")
            lines.append(f"# TYPE {self._metric_prefix}performance_monitor_active gauge")
            lines.append(f'{self._metric_prefix}performance_monitor_active {pm_active} {timestamp}')
            lines.append("")
            
            # System summary
            summary = self.performance_monitor.get_system_summary()
            
            lines.append(f"# HELP {self._metric_prefix}metrics_total Total metrics collected")
            lines.append(f"# TYPE {self._metric_prefix}metrics_total counter")
            lines.append(f'{self._metric_prefix}metrics_total {summary.get("total_metrics", 0)} {timestamp}')
            lines.append("")
            
            lines.append(f"# HELP {self._metric_prefix}queue_size Current metrics queue size")
            lines.append(f"# TYPE {self._metric_prefix}queue_size gauge")
            lines.append(f'{self._metric_prefix}queue_size {summary.get("queue_size", 0)} {timestamp}')
            lines.append("")
            
        except Exception as e:
            self.logger.debug(f"Error getting system health metrics: {e}")
        
        return lines
    
    def configure(self, **kwargs):
        """
        Configure Prometheus exporter settings.
        
        Args:
            **kwargs: Configuration parameters
        """
        if 'port' in kwargs:
            if self._active:
                self.logger.warning("Cannot change port while exporter is active")
            else:
                self.port = int(kwargs['port'])
                self.logger.debug(f"Set port to {self.port}")
        
        if 'metric_prefix' in kwargs:
            self._metric_prefix = str(kwargs['metric_prefix'])
            if not self._metric_prefix.endswith('_'):
                self._metric_prefix += '_'
            self.logger.debug(f"Set metric prefix to {self._metric_prefix}")
        
        if 'include_labels' in kwargs:
            self._include_labels = bool(kwargs['include_labels'])
            self.logger.debug(f"Include labels: {self._include_labels}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get exporter status information.
        
        Returns:
            Dictionary containing status information
        """
        return {
            'active': self._active,
            'port': self.port,
            'host': self.host,
            'endpoint': f"http://{self.host}:{self.port}/metrics",
            'metric_prefix': self._metric_prefix,
            'include_labels': self._include_labels,
            'performance_monitor_active': self.performance_monitor.is_active(),
        }


# Global Prometheus exporter instance with thread safety
_prometheus_exporter = None
_exporter_lock = threading.RLock()

def get_prometheus_exporter() -> PrometheusExporter:
    """Get the global Prometheus exporter instance with thread safety."""
    global _prometheus_exporter
    if _prometheus_exporter is None:
        with _exporter_lock:
            # Double-check locking pattern
            if _prometheus_exporter is None:
                port = get_config().get('monitoring.prometheus_port', 8000)
                _prometheus_exporter = PrometheusExporter(port)
    return _prometheus_exporter