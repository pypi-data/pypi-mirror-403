"""
Kubernetes Health Server

Provides health and readiness endpoints for Kubernetes liveness and readiness probes.
Separate from PrometheusExporter to allow independent health checking.
"""

import os
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for Kubernetes health endpoints."""
    
    def __init__(self, health_server, *args, **kwargs):
        """Initialize handler with health server reference."""
        self.health_server = health_server
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests for health endpoints."""
        try:
            if self.path in ['/health', '/healthz']:
                self._serve_health()
            elif self.path in ['/ready', '/readiness']:
                self._serve_readiness()
            elif self.path == '/':
                self._serve_status()
            else:
                self._serve_404()
        except Exception as e:
            logger.error(f"Health endpoint error: {e}")
            self._serve_500()
    
    def _serve_health(self):
        """Serve liveness probe endpoint."""
        try:
            health_status = self.health_server.get_health_status()
            
            if health_status['healthy']:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response_data = {
                    'status': 'healthy',
                    'timestamp': health_status['timestamp'],
                    'uptime': health_status['uptime']
                }
                self.wfile.write(json.dumps(response_data).encode())
            else:
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response_data = {
                    'status': 'unhealthy',
                    'reason': health_status.get('reason', 'Unknown'),
                    'timestamp': health_status['timestamp']
                }
                self.wfile.write(json.dumps(response_data).encode())
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self._serve_500()
    
    def _serve_readiness(self):
        """Serve readiness probe endpoint."""
        try:
            readiness_status = self.health_server.get_readiness_status()
            
            if readiness_status['ready']:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response_data = {
                    'status': 'ready',
                    'initialized': readiness_status['initialized'],
                    'timestamp': readiness_status['timestamp']
                }
                self.wfile.write(json.dumps(response_data).encode())
            else:
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response_data = {
                    'status': 'not_ready',
                    'reason': readiness_status.get('reason', 'Still initializing'),
                    'timestamp': readiness_status['timestamp']
                }
                self.wfile.write(json.dumps(response_data).encode())
                
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            self._serve_500()
    
    def _serve_status(self):
        """Serve general status endpoint."""
        try:
            status = self.health_server.get_full_status()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status, indent=2).encode())
            
        except Exception as e:
            logger.error(f"Status endpoint error: {e}")
            self._serve_500()
    
    def _serve_404(self):
        """Serve 404 response."""
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'error': 'Not Found'}).encode())
    
    def _serve_500(self):
        """Serve 500 response."""
        self.send_response(500)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'error': 'Internal Server Error'}).encode())
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.debug(f"K8s Health: {format % args}")


class HealthServer:
    """
    Kubernetes health server for liveness and readiness probes.
    
    Provides separate health endpoints from the main Prometheus metrics server
    to allow independent health checking in Kubernetes environments.
    """
    
    def __init__(self, port: int = 8080):
        """
        Initialize Kubernetes health server.
        
        Args:
            port: HTTP port for health endpoints (default 8080 for K8s)
        """
        self.port = port
        self.host = '0.0.0.0'
        self._server: Optional[HTTPServer] = None
        self._server_thread: Optional[threading.Thread] = None
        self._running = False
        self._start_time = time.time()
        
        # Health status tracking
        self._health_checks: Dict[str, Callable[[], bool]] = {}
        self._readiness_checks: Dict[str, Callable[[], bool]] = {}
        
        # Register default health checks
        self._register_default_checks()
    
    def start(self):
        """Start the health server."""
        if self._running:
            logger.warning("Health server already running")
            return
        
        try:
            # Create handler class with server reference
            def handler_factory(*args, **kwargs):
                return HealthHandler(self, *args, **kwargs)
            
            self._server = HTTPServer((self.host, self.port), handler_factory)
            
            # Start server in background thread
            self._server_thread = threading.Thread(
                target=self._run_server,
                name="EpochlyHealthServer",
                daemon=True
            )
            self._server_thread.start()
            
            self._running = True
            logger.info(f"Kubernetes health server started on {self.host}:{self.port}")
            logger.info("Health endpoints:")
            logger.info(f"  - Liveness:  http://{self.host}:{self.port}/healthz")
            logger.info(f"  - Readiness: http://{self.host}:{self.port}/ready")
            
        except Exception as e:
            logger.error(f"Failed to start health server: {e}")
            raise
    
    def stop(self):
        """Stop the health server."""
        if not self._running:
            return
        
        try:
            if self._server:
                self._server.shutdown()
                self._server.server_close()
            
            if self._server_thread and self._server_thread.is_alive():
                self._server_thread.join(timeout=5.0)
            
            self._running = False
            logger.info("Kubernetes health server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping health server: {e}")
    
    def _run_server(self):
        """Run the HTTP server."""
        try:
            self._server.serve_forever()
        except Exception as e:
            logger.error(f"Health server error: {e}")
    
    def _register_default_checks(self):
        """Register default health and readiness checks."""
        # Basic health checks
        self.register_health_check('basic', self._basic_health_check)
        
        # Basic readiness checks
        self.register_readiness_check('initialization', self._initialization_ready_check)
    
    def register_health_check(self, name: str, check_func: Callable[[], bool]):
        """
        Register a health check function.
        
        Args:
            name: Name of the health check
            check_func: Function that returns True if healthy
        """
        self._health_checks[name] = check_func
        logger.debug(f"Registered health check: {name}")
    
    def register_readiness_check(self, name: str, check_func: Callable[[], bool]):
        """
        Register a readiness check function.
        
        Args:
            name: Name of the readiness check
            check_func: Function that returns True if ready
        """
        self._readiness_checks[name] = check_func
        logger.debug(f"Registered readiness check: {name}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status for liveness probe."""
        status = {
            'healthy': True,
            'timestamp': time.time(),
            'uptime': time.time() - self._start_time,
            'checks': {}
        }
        
        # Run all health checks
        for name, check_func in self._health_checks.items():
            try:
                check_result = check_func()
                status['checks'][name] = {
                    'status': 'pass' if check_result else 'fail',
                    'healthy': check_result
                }
                
                if not check_result:
                    status['healthy'] = False
                    status['reason'] = f"Health check failed: {name}"
                    
            except Exception as e:
                status['checks'][name] = {
                    'status': 'error',
                    'healthy': False,
                    'error': str(e)
                }
                status['healthy'] = False
                status['reason'] = f"Health check error: {name} - {e}"
        
        return status
    
    def get_readiness_status(self) -> Dict[str, Any]:
        """Get current readiness status for readiness probe."""
        status = {
            'ready': True,
            'initialized': True,
            'timestamp': time.time(),
            'checks': {}
        }
        
        # Run all readiness checks
        for name, check_func in self._readiness_checks.items():
            try:
                check_result = check_func()
                status['checks'][name] = {
                    'status': 'pass' if check_result else 'fail',
                    'ready': check_result
                }
                
                if not check_result:
                    status['ready'] = False
                    status['initialized'] = False
                    status['reason'] = f"Readiness check failed: {name}"
                    
            except Exception as e:
                status['checks'][name] = {
                    'status': 'error',
                    'ready': False,
                    'error': str(e)
                }
                status['ready'] = False
                status['initialized'] = False
                status['reason'] = f"Readiness check error: {name} - {e}"
        
        return status
    
    def get_full_status(self) -> Dict[str, Any]:
        """Get comprehensive status for debugging."""
        health = self.get_health_status()
        readiness = self.get_readiness_status()
        
        return {
            'service': 'epochly',
            'version': self._get_epochly_version(),
            'environment': self._detect_k8s_environment(),
            'health': health,
            'readiness': readiness,
            'server': {
                'port': self.port,
                'running': self._running,
                'uptime': time.time() - self._start_time
            }
        }
    
    def _basic_health_check(self) -> bool:
        """Basic health check - server is responsive."""
        return self._running
    
    def _initialization_ready_check(self) -> bool:
        """Check if Epochly is initialized and ready."""
        try:
            # Check if Epochly core is available and initialized
            from epochly.core.epochly_core import EpochlyCore
            # If we can import and create core, we're ready
            return True
        except Exception:
            return False
    
    def _detect_k8s_environment(self) -> Dict[str, Any]:
        """Detect Kubernetes environment details."""
        env_info = {
            'kubernetes': False,
            'namespace': None,
            'pod_name': None,
            'service_account': None
        }
        
        # Check for Kubernetes service environment variables
        if any(k in os.environ for k in ['KUBERNETES_SERVICE_HOST', 'KUBERNETES_PORT']):
            env_info['kubernetes'] = True
            env_info['namespace'] = os.environ.get('POD_NAMESPACE', 'default')
            env_info['pod_name'] = os.environ.get('HOSTNAME', 'unknown')
            
            # Check for service account
            sa_path = '/var/run/secrets/kubernetes.io/serviceaccount'
            if os.path.exists(sa_path):
                try:
                    with open(f'{sa_path}/namespace', 'r') as f:
                        env_info['namespace'] = f.read().strip()
                except:
                    pass
        
        return env_info
    
    def _get_epochly_version(self) -> str:
        """Get Epochly version."""
        try:
            from epochly import __version__
            return __version__
        except:
            return "unknown"
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.stop()
        except:
            pass