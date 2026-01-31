"""
Resource Limiter for Container Environments

This module implements container-aware resource limitation to prevent resource
exhaustion in Docker, Kubernetes, Lambda, and other containerized environments.

PERFORMANCE FIX (perf_review.md v2 Section 7): Defer heavy imports (psutil)
until actually needed to avoid penalizing cold start time.
"""

import os
import mmap
# CRITICAL FIX: psutil imported lazily (not at module level)
# import psutil  # REMOVED - now imported only when needed
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ResourceLimiter:
    """
    Container-aware resource limiter to prevent resource exhaustion.

    Detects container environments and calculates safe resource limits
    based on container constraints and available resources.

    PERFORMANCE FIX: Lazy initialization pattern
    - Environment detection: Cheap (file checks only)
    - Limits calculation: Expensive (psutil) - deferred until first use
    """

    def __init__(self):
        """
        Initialize resource limiter with lazy limit calculation.

        Environment detection happens immediately (cheap: file checks).
        Limit calculation deferred until first access (expensive: psutil import).
        """
        # Detect environment immediately (cheap: file system checks only)
        self._environment = self._detect_environment()

        # CRITICAL FIX: Defer limits calculation until first use
        self._limits = None  # Lazy initialization
        self._limits_lock = None  # Will be created on first use

        logger.info(f"Resource limiter initialized for {self._environment['type']} environment")
        if self._environment['type'] != 'bare_metal':
            logger.debug(f"Container constraints detected: {self._environment['constraints']}")

    @property
    def environment(self) -> Dict[str, Any]:
        """Get environment information (already computed in __init__)."""
        return self._environment

    @property
    def limits(self) -> Dict[str, Any]:
        """
        Get resource limits (lazy loading with double-checked locking).

        First access imports psutil and calculates limits.
        Subsequent accesses return cached result.
        """
        # Fast path: already calculated
        if self._limits is not None:
            return self._limits

        # Slow path: calculate with lock
        import threading

        # Create lock on first use
        if self._limits_lock is None:
            self._limits_lock = threading.Lock()

        with self._limits_lock:
            # Double-check: another thread may have calculated
            if self._limits is not None:
                return self._limits

            # LAZY IMPORT: psutil loaded here, not at module level
            try:
                import psutil  # Only imported when limits needed
                self._limits = self._calculate_safe_limits()
            except ImportError:
                logger.warning("psutil not available, using conservative defaults")
                self._limits = self._get_conservative_defaults()
            except Exception as e:
                logger.error(f"Failed to calculate resource limits: {e}")
                self._limits = self._get_conservative_defaults()

        return self._limits

    def _get_conservative_defaults(self) -> Dict[str, Any]:
        """Get conservative default limits when psutil unavailable."""
        return {
            'max_shared_memory': 64 * 1024 * 1024,  # 64MB
            'max_workers': 4,  # Conservative default
            'max_queue_size': 1000,
            'environment': self._environment
        }
    
    def _detect_environment(self) -> Dict[str, Any]:
        """Detect container/cloud environment with comprehensive detection."""
        env = {
            'type': 'bare_metal',
            'constraints': {},
            'platform': {}
        }
        
        # Docker detection (multiple methods)
        if self._is_docker_environment():
            env['type'] = 'docker'
            env['constraints'] = self._get_docker_constraints()
            logger.debug("Docker environment detected")
        
        # Kubernetes detection (overrides Docker)
        elif self._is_kubernetes_environment():
            env['type'] = 'kubernetes'
            env['constraints'] = self._get_k8s_constraints()
            env['platform']['namespace'] = os.environ.get('POD_NAMESPACE', 'default')
            env['platform']['pod_name'] = os.environ.get('HOSTNAME', 'unknown')
            logger.debug("Kubernetes environment detected")
        
        # AWS Lambda detection
        elif self._is_lambda_environment():
            env['type'] = 'lambda'
            env['constraints'] = self._get_lambda_constraints()
            logger.debug("AWS Lambda environment detected")
        
        # Google Cloud Run detection
        elif self._is_cloud_run_environment():
            env['type'] = 'cloud_run'
            env['constraints'] = self._get_cloud_run_constraints()
            logger.debug("Google Cloud Run environment detected")
        
        # Azure Container Instances
        elif self._is_azure_container_environment():
            env['type'] = 'azure_container'
            env['constraints'] = self._get_azure_constraints()
            logger.debug("Azure Container environment detected")
        
        return env
    
    def _is_docker_environment(self) -> bool:
        """Check if running in Docker container."""
        # Method 1: Check for .dockerenv file
        if os.path.exists('/.dockerenv'):
            return True
        
        # Method 2: Check cgroup for docker
        try:
            with open('/proc/self/cgroup', 'r') as f:
                cgroup_content = f.read()
                return 'docker' in cgroup_content.lower()
        except:
            pass
        
        # Method 3: Check for container runtime indicators
        try:
            with open('/proc/1/cgroup', 'r') as f:
                init_cgroup = f.read()
                container_indicators = ['docker', 'containerd', 'lxc']
                return any(indicator in init_cgroup.lower() for indicator in container_indicators)
        except:
            pass
        
        return False
    
    def _is_kubernetes_environment(self) -> bool:
        """Check if running in Kubernetes pod."""
        # Check for Kubernetes service environment variables
        k8s_env_vars = ['KUBERNETES_SERVICE_HOST', 'KUBERNETES_PORT']
        if any(var in os.environ for var in k8s_env_vars):
            return True
        
        # Check for service account token
        if os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount/token'):
            return True
        
        # Check for downward API
        if os.path.exists('/etc/podinfo'):
            return True
        
        return False
    
    def _is_lambda_environment(self) -> bool:
        """Check if running in AWS Lambda."""
        return 'AWS_LAMBDA_FUNCTION_NAME' in os.environ
    
    def _is_cloud_run_environment(self) -> bool:
        """Check if running in Google Cloud Run."""
        return 'K_SERVICE' in os.environ
    
    def _is_azure_container_environment(self) -> bool:
        """Check if running in Azure Container Instances."""
        return 'WEBSITE_INSTANCE_ID' in os.environ
    
    def _get_docker_constraints(self) -> Dict[str, Any]:
        """Get Docker resource constraints from cgroups."""
        constraints = {}
        
        # Memory limits (cgroup v1 and v2 compatible)
        memory_limit = self._read_cgroup_value('memory.limit_in_bytes')
        if memory_limit > 0 and memory_limit < (1 << 62):  # Valid limit
            constraints['memory_bytes'] = memory_limit
        
        # CPU limits
        cpu_quota = self._read_cgroup_value('cpu.cfs_quota_us')
        cpu_period = self._read_cgroup_value('cpu.cfs_period_us')
        if cpu_quota > 0 and cpu_period > 0:
            constraints['cpu_cores'] = cpu_quota / cpu_period
        
        # Shared memory size
        if os.path.exists('/dev/shm'):
            try:
                shm_stat = os.statvfs('/dev/shm')
                shm_size = shm_stat.f_blocks * shm_stat.f_frsize
                constraints['shm_size'] = shm_size
            except:
                pass
        
        return constraints
    
    def _get_k8s_constraints(self) -> Dict[str, Any]:
        """Get Kubernetes resource constraints from downward API or cgroups."""
        constraints = {}
        
        # Try downward API first (more reliable)
        if os.path.exists('/etc/podinfo/cpu_limit'):
            try:
                with open('/etc/podinfo/cpu_limit', 'r') as f:
                    constraints['cpu_millicores'] = int(f.read().strip())
            except:
                pass
        
        if os.path.exists('/etc/podinfo/mem_limit'):
            try:
                with open('/etc/podinfo/mem_limit', 'r') as f:
                    constraints['memory_bytes'] = int(f.read().strip())
            except:
                pass
        
        # Fallback to cgroup detection
        if not constraints:
            constraints = self._get_docker_constraints()
        
        return constraints
    
    def _get_lambda_constraints(self) -> Dict[str, Any]:
        """Get AWS Lambda resource constraints."""
        return {
            'memory_mb': int(os.environ.get('AWS_LAMBDA_FUNCTION_MEMORY_SIZE', 128)),
            'timeout_seconds': int(os.environ.get('AWS_LAMBDA_FUNCTION_TIMEOUT', 900)),
            'ephemeral_storage_mb': int(os.environ.get('AWS_LAMBDA_EPHEMERAL_STORAGE', 512)),
            'max_workers': 1,  # Lambda is single-threaded
            'disable_shared_memory': True,  # No shared memory in Lambda
            'optimize_cold_start': True
        }
    
    def _get_cloud_run_constraints(self) -> Dict[str, Any]:
        """Get Google Cloud Run constraints."""
        constraints = {}
        
        # Cloud Run memory limit
        if 'MEMORY' in os.environ:
            try:
                # Format: "512Mi", "1Gi", etc.
                memory_str = os.environ['MEMORY']
                if memory_str.endswith('Mi'):
                    constraints['memory_bytes'] = int(memory_str[:-2]) * 1024 * 1024
                elif memory_str.endswith('Gi'):
                    constraints['memory_bytes'] = int(memory_str[:-2]) * 1024 * 1024 * 1024
            except:
                pass
        
        # Cloud Run CPU limit
        if 'CPU' in os.environ:
            try:
                constraints['cpu_cores'] = float(os.environ['CPU'])
            except:
                pass
        
        return constraints
    
    def _get_azure_constraints(self) -> Dict[str, Any]:
        """Get Azure Container Instances constraints."""
        constraints = {}
        
        # Azure typically uses standard cgroup limits
        constraints.update(self._get_docker_constraints())
        
        return constraints
    
    def _calculate_safe_limits(self) -> Dict[str, Any]:
        """
        Calculate safe resource limits based on environment.

        CRITICAL FIX: Import psutil locally so it's available in method scope.
        Module-level import removed for lazy loading, but method needs the symbol.
        """
        # LOCAL IMPORT: psutil available in this method scope
        import psutil

        total_memory = psutil.virtual_memory().total
        available_memory = psutil.virtual_memory().available
        cpu_count = os.cpu_count() or 4
        
        # Base limits (conservative)
        limits = {
            'max_shared_memory': int(available_memory * 0.5),
            'max_workers': cpu_count,
            'max_queue_size': 10000
        }
        
        # Environment-specific adjustments
        env_type = self.environment['type']
        constraints = self.environment['constraints']
        
        if env_type == 'docker':
            limits = self._apply_docker_limits(limits, constraints)
        elif env_type == 'kubernetes':
            limits = self._apply_k8s_limits(limits, constraints)
        elif env_type == 'lambda':
            limits = self._apply_lambda_limits(limits, constraints)
        elif env_type in ['cloud_run', 'azure_container']:
            limits = self._apply_serverless_limits(limits, constraints)
        
        # Final safety checks
        limits['max_shared_memory'] = max(64 * 1024 * 1024, limits['max_shared_memory'])  # Minimum 64MB
        limits['max_workers'] = max(1, min(limits['max_workers'], 32))  # Between 1 and 32
        
        return limits
    
    def _apply_docker_limits(self, limits: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Docker-specific resource limits."""
        # Respect Docker memory limits
        if 'memory_bytes' in constraints:
            container_memory = constraints['memory_bytes']
            # Use 40% of container memory for shared memory
            limits['max_shared_memory'] = min(limits['max_shared_memory'], int(container_memory * 0.4))
        
        # Respect Docker shared memory size
        if 'shm_size' in constraints:
            # Docker default /dev/shm is often 64MB
            shm_limit = int(constraints['shm_size'] * 0.8)
            limits['max_shared_memory'] = min(limits['max_shared_memory'], shm_limit)
        
        # Respect Docker CPU limits
        if 'cpu_cores' in constraints:
            limits['max_workers'] = max(1, int(constraints['cpu_cores']))
        
        return limits
    
    def _apply_k8s_limits(self, limits: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Kubernetes-specific resource limits (more conservative)."""
        # K8s: More conservative due to pod eviction policies
        if 'memory_bytes' in constraints:
            container_memory = constraints['memory_bytes']
            # Use only 30% of pod memory for shared memory (more conservative)
            limits['max_shared_memory'] = min(limits['max_shared_memory'], int(container_memory * 0.3))
        
        # K8s CPU limits
        if 'cpu_millicores' in constraints:
            cpu_cores = constraints['cpu_millicores'] / 1000.0
            limits['max_workers'] = max(1, int(cpu_cores))
        elif 'cpu_cores' in constraints:
            limits['max_workers'] = max(1, int(constraints['cpu_cores']))
        
        return limits
    
    def _apply_lambda_limits(self, limits: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Apply AWS Lambda-specific limits."""
        # Lambda: Very conservative
        lambda_memory_mb = constraints.get('memory_mb', 128)
        
        # Lambda shared memory is very limited
        limits['max_shared_memory'] = min(64 * 1024 * 1024, lambda_memory_mb * 1024 * 1024 // 4)
        limits['max_workers'] = 1  # Lambda is single-threaded
        limits['disable_sub_interpreters'] = True
        limits['disable_jit'] = True  # Minimize cold start overhead
        
        return limits
    
    def _apply_serverless_limits(self, limits: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Apply serverless container limits (Cloud Run, Azure Container)."""
        # Serverless: Conservative approach
        if 'memory_bytes' in constraints:
            serverless_memory = constraints['memory_bytes']
            limits['max_shared_memory'] = min(limits['max_shared_memory'], 
                                            min(256 * 1024 * 1024, int(serverless_memory * 0.3)))
        
        if 'cpu_cores' in constraints:
            limits['max_workers'] = max(1, int(constraints['cpu_cores']))
        
        return limits
    
    def _read_cgroup_value(self, filename: str) -> int:
        """Read value from cgroup file (v1 and v2 compatible)."""
        # cgroup v2 paths
        v2_paths = [
            f'/sys/fs/cgroup/{filename}',
            f'/sys/fs/cgroup/system.slice/{filename}'
        ]
        
        # cgroup v1 paths  
        v1_paths = [
            f'/sys/fs/cgroup/memory/{filename}',
            f'/sys/fs/cgroup/cpu/{filename}',
            f'/sys/fs/cgroup/cpu,cpuacct/{filename}'
        ]
        
        for path in v2_paths + v1_paths:
            try:
                with open(path, 'r') as f:
                    return int(f.read().strip())
            except:
                continue
        
        return -1  # Not found or error
    
    def get_max_workers(self) -> int:
        """Get maximum number of workers allowed."""
        return self.limits['max_workers']
    
    def get_max_shared_memory(self) -> int:
        """Get maximum shared memory allowed."""
        return self.limits['max_shared_memory']
    
    def get_environment_type(self) -> str:
        """Get detected environment type."""
        return self.environment['type']
    
    def is_container_environment(self) -> bool:
        """Check if running in any container environment."""
        return self.environment['type'] != 'bare_metal'
    
    def get_container_optimizations(self) -> Dict[str, Any]:
        """Get recommended optimizations for container environment."""
        env_type = self.environment['type']
        
        optimizations = {
            'shared_memory_strategy': 'conservative',
            'worker_strategy': 'limited',
            'memory_strategy': 'aggressive_cleanup'
        }
        
        if env_type == 'kubernetes':
            optimizations.update({
                'enable_health_endpoints': True,
                'enable_metrics_endpoint': True,
                'enable_graceful_shutdown': True,
                'shared_memory_backend': 'emptydir_volume'
            })
        elif env_type == 'docker':
            optimizations.update({
                'shared_memory_backend': self._select_docker_shm_backend(),
                'worker_isolation': 'process',
                'gc_strategy': 'aggressive'
            })
        elif env_type == 'lambda':
            optimizations.update({
                'bootstrap_mode': 'minimal',
                'shared_memory_backend': 'heap',
                'workers': 0,
                'disable_jit': True,
                'disable_sub_interpreters': True
            })
        
        return optimizations
    
    def _select_docker_shm_backend(self) -> str:
        """Select appropriate shared memory backend for Docker."""
        constraints = self.environment['constraints']
        
        # Check if /dev/shm is available and sufficient
        if 'shm_size' in constraints and constraints['shm_size'] > 128 * 1024 * 1024:
            return 'posix_shm'  # Use /dev/shm
        
        # Fall back to memory-mapped files in /tmp
        return 'mmap_tmpfs'


# Global instance for performance
_global_limiter: Optional[ResourceLimiter] = None

def get_resource_limiter() -> ResourceLimiter:
    """Get global resource limiter instance."""
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = ResourceLimiter()
    return _global_limiter