"""
Container Adapter for Environment-Specific Optimizations

This module implements container-specific adaptations for optimal Epochly
performance in Docker, Kubernetes, Lambda, and other container environments.
"""

import os
import signal
import sys
import threading
import time
from typing import Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class ContainerAdapter:
    """
    Container environment adapter for Epochly optimizations.
    
    Provides environment-specific adaptations and optimizations for
    containerized deployments including graceful shutdown, health monitoring,
    and resource optimization.
    """
    
    def __init__(self, environment: Dict[str, Any]):
        """
        Initialize container adapter.
        
        Args:
            environment: Environment information from ResourceLimiter
        """
        self.environment = environment
        self.adaptations = self._determine_adaptations()
        self._shutdown_handlers: list[Callable] = []
        self._health_server: Optional['HealthServer'] = None
        
        logger.info(f"Container adapter initialized for {environment['type']} environment")
    
    def _determine_adaptations(self) -> Dict[str, Any]:
        """Determine necessary adaptations based on environment."""
        adaptations = {}
        env_type = self.environment['type']
        
        if env_type == 'docker':
            adaptations.update({
                'shared_memory_backend': self._select_docker_shm_backend(),
                'worker_isolation': 'process',  # Processes work better in containers
                'gc_strategy': 'aggressive',    # Free memory quickly
                'numa_aware': False,           # NUMA doesn't apply in containers
                'health_endpoint': True,       # Enable health endpoint
                'metrics_endpoint': True       # Enable metrics endpoint
            })
        
        elif env_type == 'kubernetes':
            adaptations.update({
                'shared_memory_backend': 'emptydir_volume',  # Use K8s volumes
                'worker_isolation': 'thread',               # Avoid process overhead
                'health_endpoint': True,                    # Enable liveness/readiness probes
                'metrics_endpoint': True,                   # Prometheus metrics
                'graceful_shutdown': True,                  # Handle SIGTERM properly
                'pod_optimization': True,                   # K8s-specific optimizations
                'resource_quotas': True                     # Respect K8s resource quotas
            })
        
        elif env_type == 'lambda':
            adaptations.update({
                'bootstrap_mode': 'lazy',           # Minimize cold start
                'shared_memory_backend': 'heap',    # No shared memory in Lambda
                'workers': 0,                       # Single-threaded only
                'jit_level': 0,                     # Disable JIT (cold start overhead)
                'persist_nothing': True,            # Stateless execution
                'optimization_level': 'minimal'     # Minimal overhead
            })
        
        elif env_type in ['cloud_run', 'azure_container']:
            adaptations.update({
                'shared_memory_backend': 'tmpfs',   # Use temp filesystem
                'auto_scale_aware': True,           # Respect scaling
                'request_scoped': True,             # Clean up after each request
                'health_endpoint': True,            # Health checks
                'metrics_endpoint': True            # Monitoring
            })
        
        return adaptations
    
    def apply_adaptations(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply container-specific adaptations to Epochly configuration.
        
        Args:
            config: Epochly configuration dictionary
            
        Returns:
            Modified configuration with container adaptations
        """
        # Apply all adaptations
        for key, value in self.adaptations.items():
            config[key] = value
        
        # Special handling for specific environments
        env_type = self.environment['type']
        
        if env_type == 'kubernetes':
            config = self._setup_k8s_integration(config)
        elif env_type == 'lambda':
            config = self._setup_lambda_optimization(config)
        elif env_type == 'docker':
            config = self._setup_docker_optimization(config)
        
        return config
    
    def _setup_k8s_integration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup Kubernetes-specific integrations."""
        # Health check endpoint
        if config.get('health_endpoint'):
            try:
                from epochly.k8s.health_server import HealthServer
                self._health_server = HealthServer(port=8080)
                self._health_server.start()
                logger.info("Kubernetes health endpoints started on port 8080")
            except Exception as e:
                logger.error(f"Failed to start health server: {e}")
        
        # Graceful shutdown handling
        if config.get('graceful_shutdown'):
            signal.signal(signal.SIGTERM, self._handle_sigterm)
            logger.info("Registered SIGTERM handler for graceful K8s shutdown")
        
        # Prometheus metrics endpoint
        if config.get('metrics_endpoint'):
            try:
                from epochly.monitoring.prometheus_exporter import PrometheusExporter
                metrics_exporter = PrometheusExporter(port=8000)
                metrics_exporter.start()
                logger.info("Prometheus metrics endpoint started on port 8000")
            except Exception as e:
                logger.error(f"Failed to start metrics exporter: {e}")
        
        return config
    
    def _setup_lambda_optimization(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup AWS Lambda-specific optimizations."""
        # Minimize cold start by disabling heavy components
        config.update({
            'enhancement_level': 0,        # Start at monitoring only
            'disable_progressive_enhancement': True,
            'disable_background_threads': True,
            'memory_pool_size': 0,         # No memory pool
            'enable_request_scoped_cleanup': True
        })
        
        logger.info("Applied Lambda cold-start optimizations")
        return config
    
    def _setup_docker_optimization(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup Docker-specific optimizations."""
        # Docker optimizations
        config.update({
            'aggressive_memory_cleanup': True,
            'container_signal_handling': True,
            'disable_numa_optimizations': True  # NUMA doesn't apply in containers
        })
        
        # Health endpoint for Docker health checks
        if config.get('health_endpoint'):
            try:
                from epochly.monitoring.prometheus_exporter import PrometheusExporter
                # Use PrometheusExporter which already has /health endpoint
                metrics_exporter = PrometheusExporter(port=8080)
                metrics_exporter.start()
                logger.info("Docker health endpoint started on port 8080")
            except Exception as e:
                logger.error(f"Failed to start Docker health endpoint: {e}")
        
        return config
    
    def _select_docker_shm_backend(self) -> str:
        """Select appropriate shared memory backend for Docker."""
        constraints = self.environment['constraints']
        
        # Check if /dev/shm is available and sufficient
        if 'shm_size' in constraints and constraints['shm_size'] > 128 * 1024 * 1024:
            return 'posix_shm'  # Use /dev/shm
        
        # Fall back to memory-mapped files
        return 'mmap_tmpfs'  # Use /tmp (usually tmpfs in containers)
    
    def _handle_sigterm(self, signum: int, frame) -> None:
        """Handle Kubernetes pod termination signal."""
        logger.info("Received SIGTERM, starting graceful shutdown")
        
        try:
            # Notify all registered shutdown handlers
            for handler in self._shutdown_handlers:
                try:
                    handler()
                except Exception as e:
                    logger.error(f"Shutdown handler error: {e}")
            
            # Stop health server
            if self._health_server:
                self._health_server.stop()
            
            # Import Epochly core for shutdown
            try:
                import epochly
                if hasattr(epochly, 'shutdown'):
                    epochly.shutdown()
                elif hasattr(epochly, 'stop_accepting_work'):
                    epochly.stop_accepting_work()
                    if hasattr(epochly, 'wait_for_completion'):
                        epochly.wait_for_completion(timeout=30)
            except Exception as e:
                logger.error(f"Epochly shutdown error: {e}")
            
            logger.info("Graceful shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
        finally:
            # Force exit after timeout
            threading.Timer(35.0, lambda: os._exit(0)).start()
    
    def register_shutdown_handler(self, handler: Callable) -> None:
        """
        Register a function to be called during graceful shutdown.
        
        Args:
            handler: Function to call during shutdown
        """
        self._shutdown_handlers.append(handler)
        logger.debug(f"Registered shutdown handler: {handler.__name__}")
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get comprehensive environment information."""
        return {
            'environment': self.environment,
            'adaptations': self.adaptations,
            'platform_details': {
                'python_version': sys.version,
                'platform': sys.platform,
                'container_type': self.environment['type']
            }
        }


# Factory function for easy usage
def create_container_adapter() -> ContainerAdapter:
    """Create container adapter with auto-detected environment."""
    from epochly.core.resource_limiter import get_resource_limiter
    
    limiter = get_resource_limiter()
    return ContainerAdapter(limiter.environment)