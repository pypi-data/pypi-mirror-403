"""
Epochly Security Manager

Central security manager that coordinates all security functionality including
file security, path validation, and container awareness.

Author: Epochly Development Team
"""

import os
import platform
from typing import Optional, Dict, Any, Union
from pathlib import Path
from ..utils.logger import get_logger
from .path_validator import PathValidator
from .file_security import FileSecurityManager


class SecurityManager:
    """
    Central security manager for Epochly deployment infrastructure.
    
    Provides mechanisms for:
    - Coordinated security operations
    - Container-aware resource monitoring
    - Security policy enforcement
    - Privilege management
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize security manager.
        
        Args:
            config: Security configuration dictionary
        """
        self.logger = get_logger(__name__)
        self.config = config or {}
        
        # Initialize security components
        allowed_paths = self.config.get('allowed_base_paths', [])
        self.path_validator = PathValidator(allowed_paths)
        self.file_security = FileSecurityManager(allowed_paths)
        
        # Container detection
        self._is_container: Optional[bool] = None
        self._container_limits: Optional[Dict[str, Union[int, str, None]]] = None
    
    def is_running_in_container(self) -> bool:
        """
        Detect if running in a container environment.
        
        Returns:
            True if running in container, False otherwise
        """
        if self._is_container is not None:
            return self._is_container
        
        try:
            # Check for container indicators
            container_indicators = [
                # Docker
                os.path.exists('/.dockerenv'),
                # Kubernetes
                os.path.exists('/var/run/secrets/kubernetes.io'),
                # General container indicators
                os.path.exists('/proc/1/cgroup') and self._check_cgroup_container(),
                # Environment variables
                any(env in os.environ for env in ['KUBERNETES_SERVICE_HOST', 'DOCKER_CONTAINER'])
            ]
            
            self._is_container = any(container_indicators)
            self.logger.debug(f"Container detection result: {self._is_container}")
            
        except Exception as e:
            self.logger.warning(f"Container detection failed: {e}")
            self._is_container = False
        
        return self._is_container
    
    def _check_cgroup_container(self) -> bool:
        """
        Check cgroup for container indicators.
        
        Returns:
            True if cgroup indicates container, False otherwise
        """
        try:
            with open('/proc/1/cgroup', 'r') as f:
                cgroup_content = f.read()
            
            # Look for container indicators in cgroup
            container_patterns = ['docker', 'kubepods', 'containerd', 'lxc']
            return any(pattern in cgroup_content for pattern in container_patterns)
            
        except Exception:
            return False
    
    def get_container_memory_limits(self) -> Dict[str, Union[int, str, None]]:
        """
        Get container memory limits from cgroup v1/v2.
        
        Returns:
            Dictionary with memory limit information
        """
        if self._container_limits is not None:
            return self._container_limits
        
        limits: Dict[str, Union[int, str, None]] = {
            'memory_limit': None,
            'memory_usage': None,
            'memory_available': None,
            'cgroup_version': None
        }
        
        try:
            # Try cgroup v2 first
            if os.path.exists('/sys/fs/cgroup/memory.max'):
                limits['cgroup_version'] = 'v2'
                
                # Read memory limit
                with open('/sys/fs/cgroup/memory.max', 'r') as f:
                    limit_str = f.read().strip()
                    if limit_str != 'max':
                        limits['memory_limit'] = int(limit_str)
                
                # Read current usage
                if os.path.exists('/sys/fs/cgroup/memory.current'):
                    with open('/sys/fs/cgroup/memory.current', 'r') as f:
                        limits['memory_usage'] = int(f.read().strip())
            
            # Try cgroup v1
            elif os.path.exists('/sys/fs/cgroup/memory/memory.limit_in_bytes'):
                limits['cgroup_version'] = 'v1'
                
                # Read memory limit
                with open('/sys/fs/cgroup/memory/memory.limit_in_bytes', 'r') as f:
                    limit_bytes = int(f.read().strip())
                    # Check if it's a real limit (not the default huge value)
                    if limit_bytes < (1 << 62):  # Reasonable upper bound
                        limits['memory_limit'] = limit_bytes
                
                # Read current usage
                if os.path.exists('/sys/fs/cgroup/memory/memory.usage_in_bytes'):
                    with open('/sys/fs/cgroup/memory/memory.usage_in_bytes', 'r') as f:
                        limits['memory_usage'] = int(f.read().strip())
            
            # Calculate available memory
            if isinstance(limits['memory_limit'], int) and isinstance(limits['memory_usage'], int):
                limits['memory_available'] = limits['memory_limit'] - limits['memory_usage']
            
            self._container_limits = limits
            self.logger.debug(f"Container memory limits: {limits}")
            
        except Exception as e:
            self.logger.warning(f"Failed to read container memory limits: {e}")
        
        return limits
    
    def get_effective_memory_threshold(self, default_threshold: int) -> int:
        """
        Get effective memory threshold considering container limits.
        
        Args:
            default_threshold: Default threshold in bytes
            
        Returns:
            Effective threshold considering container constraints
        """
        if not self.is_running_in_container():
            return default_threshold
        
        limits = self.get_container_memory_limits()
        memory_limit = limits.get('memory_limit')
        
        if isinstance(memory_limit, int):
            # Use percentage of container limit instead of absolute value
            container_threshold = int(memory_limit * 0.8)  # 80% of container limit
            effective_threshold = min(default_threshold, container_threshold)
            
            self.logger.debug(f"Adjusted memory threshold for container: {effective_threshold}")
            return effective_threshold
        
        return default_threshold
    
    def check_resource_constraints(self) -> Dict[str, Any]:
        """
        Check current resource constraints and limits.
        
        Returns:
            Dictionary with resource constraint information
        """
        constraints = {
            'platform': platform.system(),
            'is_container': self.is_running_in_container(),
            'memory_info': {},
            'disk_info': {},
            'security_context': {}
        }
        
        try:
            # Memory information
            if self.is_running_in_container():
                constraints['memory_info'] = self.get_container_memory_limits()
            else:
                # Get system memory info (requires psutil)
                try:
                    import psutil
                    memory = psutil.virtual_memory()
                    constraints['memory_info'] = {
                        'total': memory.total,
                        'available': memory.available,
                        'used': memory.used,
                        'percent': memory.percent
                    }
                except ImportError:
                    self.logger.warning("psutil not available for system memory info")
            
            # Disk space for backup directory
            backup_dir = self.config.get('backup_directory', os.path.expanduser('~/.epochly/backups'))
            if os.path.exists(backup_dir):
                import shutil
                disk_usage = shutil.disk_usage(backup_dir)
                constraints['disk_info'] = {
                    'total': disk_usage.total,
                    'used': disk_usage.used,
                    'free': disk_usage.free
                }
            
            # Security context (Unix-like systems only)
            if hasattr(os, 'getuid'):
                constraints['security_context'] = {
                    'uid': os.getuid(),
                    'gid': os.getgid(),
                    'effective_uid': os.geteuid() if hasattr(os, 'geteuid') else None,
                    'effective_gid': os.getegid() if hasattr(os, 'getegid') else None,
                }
            else:
                # Windows or other systems
                constraints['security_context'] = {
                    'uid': None,
                    'gid': None,
                    'effective_uid': None,
                    'effective_gid': None,
                }
            
        except Exception as e:
            self.logger.warning(f"Failed to gather resource constraints: {e}")
        
        return constraints
    
    def validate_security_context(self) -> Dict[str, Any]:
        """
        Validate current security context and permissions.
        
        Returns:
            Dictionary with security validation results
        """
        validation = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'recommendations': []
        }
        
        try:
            # Check if running as root (security risk) - Unix-like systems only
            if hasattr(os, 'getuid') and os.getuid() == 0:
                validation['warnings'].append("Running as root user - security risk")
                validation['recommendations'].append("Consider running with reduced privileges")
            
            # Check file permissions on critical directories
            critical_paths = [
                os.path.expanduser('~/.epochly'),
                self.config.get('backup_directory', os.path.expanduser('~/.epochly/backups'))
            ]
            
            for path in critical_paths:
                if os.path.exists(path):
                    stat_info = os.stat(path)
                    mode = stat_info.st_mode
                    
                    # Check if directory is world-writable
                    if mode & 0o002:
                        validation['errors'].append(f"Directory {path} is world-writable")
                        validation['valid'] = False
                    
                    # Check if directory is group-writable (warning)
                    elif mode & 0o020:
                        validation['warnings'].append(f"Directory {path} is group-writable")
            
            # Check environment variables for sensitive data
            sensitive_env_patterns = ['password', 'secret', 'key', 'token']
            for env_var in os.environ:
                if any(pattern in env_var.lower() for pattern in sensitive_env_patterns):
                    validation['warnings'].append(f"Potentially sensitive environment variable: {env_var}")
            
        except Exception as e:
            validation['errors'].append(f"Security validation failed: {e}")
            validation['valid'] = False
        
        return validation
    
    def secure_environment_setup(self) -> bool:
        """
        Set up secure environment for Epochly operations.
        
        Returns:
            True if setup successful, False otherwise
        """
        try:
            # Create secure directories
            epochly_dir = Path.home() / '.epochly'
            backup_dir = epochly_dir / 'backups'
            
            for directory in [epochly_dir, backup_dir]:
                if not directory.exists():
                    self.file_security.create_secure_directory(directory, is_private=True)
                else:
                    self.file_security.set_secure_permissions(directory, is_private=True)
            
            # Validate security context
            validation = self.validate_security_context()
            if not validation['valid']:
                for error in validation['errors']:
                    self.logger.error(f"Security validation error: {error}")
                return False
            
            for warning in validation['warnings']:
                self.logger.warning(f"Security warning: {warning}")
            
            self.logger.info("Secure environment setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set up secure environment: {e}")
            return False
    
    def sanitize_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize configuration values for security.
        
        Args:
            config: Configuration dictionary to sanitize
            
        Returns:
            Sanitized configuration dictionary
        """
        sanitized = {}
        
        for key, value in config.items():
            if isinstance(value, str):
                # Sanitize string values
                sanitized[key] = self.file_security.sanitize_environment_variable(value)
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = self.sanitize_configuration(value)
            elif isinstance(value, list):
                # Sanitize list items if they're strings
                sanitized[key] = [
                    self.file_security.sanitize_environment_variable(item) 
                    if isinstance(item, str) else item 
                    for item in value
                ]
            else:
                # Keep other types as-is
                sanitized[key] = value
        
        return sanitized
    
    def get_security_status(self) -> Dict[str, Any]:
        """
        Get comprehensive security status report.
        
        Returns:
            Dictionary with security status information
        """
        status = {
            'timestamp': __import__('time').time(),
            'security_manager_version': '1.0.0',
            'environment': {
                'platform': platform.system(),
                'is_container': self.is_running_in_container(),
                'python_version': platform.python_version()
            },
            'validation': self.validate_security_context(),
            'resource_constraints': self.check_resource_constraints(),
            'configuration': {
                'allowed_base_paths': len(self.path_validator.allowed_base_paths),
                'security_policies_active': True
            }
        }
        
        return status