"""
Epochly diagnostics system.

Provides Doctor class for diagnosing installation and compatibility issues.

Author: Epochly Development Team
"""

import os
import sys
import platform
import subprocess
import importlib
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Doctor:
    """Diagnose Epochly installation and system compatibility."""
    
    def __init__(self):
        """Initialize the diagnostics doctor."""
        self.issues_found = []
        self.fixable_issues = []
    
    def run_diagnostics(self, verbose: bool = False) -> Dict[str, Any]:
        """Run all diagnostic checks."""
        results = {}
        
        # Python version check
        results['python_version'] = self._check_python_version(verbose)
        
        # Epochly installation check
        results['epochly_installed'] = self._check_epochly_installed(verbose)
        
        # Dependencies check
        results['dependencies'] = self._check_dependencies(verbose)
        
        # C extensions check
        results['c_extensions'] = self._check_c_extensions(verbose)
        
        # Virtual environment check
        results['virtual_env'] = self._check_virtual_env(verbose)
        
        # GPU support check
        results['gpu_support'] = self._check_gpu_support(verbose)
        
        # Performance check
        results['performance'] = self._check_performance(verbose)
        
        # Configuration check
        results['configuration'] = self._check_configuration(verbose)
        
        # System resources check
        results['system_resources'] = self._check_system_resources(verbose)
        
        # File permissions check
        results['file_permissions'] = self._check_file_permissions(verbose)
        
        return results
    
    def _check_python_version(self, verbose: bool) -> Dict[str, Any]:
        """Check Python version compatibility."""
        result = {}
        version_info = sys.version_info
        version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
        
        result['message'] = f"Python {version_str}"
        
        if verbose:
            result['details'] = {
                'version': version_str,
                'implementation': platform.python_implementation(),
                'compiler': platform.python_compiler()
            }
        
        # Check minimum version
        if version_info < (3, 8):
            result['status'] = 'fail'
            result['message'] = f"Python {version_str} is not supported. Requires Python 3.8+"
            self.issues_found.append('python_version')
        elif version_info < (3, 10):
            result['status'] = 'warn'
            result['message'] = f"Python {version_str} is supported but not optimal. Recommend Python 3.10+"
        else:
            result['status'] = 'pass'
        
        return result
    
    def _check_epochly_installed(self, verbose: bool) -> Dict[str, Any]:
        """Check if Epochly is properly installed."""
        result = {}
        
        try:
            import epochly
            version = getattr(epochly, '__version__', 'unknown')
            result['status'] = 'pass'
            result['message'] = f"Epochly {version} installed"
            
            if verbose:
                result['details'] = {
                    'version': version,
                    'location': epochly.__file__,
                    'package_dir': os.path.dirname(epochly.__file__)
                }
        except ImportError as e:
            result['status'] = 'fail'
            result['message'] = "Epochly not installed or not in PYTHONPATH"
            result['error'] = str(e)
            self.issues_found.append('epochly_installed')
            self.fixable_issues.append('epochly_installed')
        
        return result
    
    def _check_dependencies(self, verbose: bool) -> Dict[str, Any]:
        """Check if all required dependencies are installed."""
        result = {}

        # Required dependencies (core functionality)
        required_packages = {
            'numpy': '>=1.20.0',
            'psutil': '>=5.8.0',
        }

        # Optional dependencies (enhanced functionality)
        optional_packages = {
            'cryptography': '>=3.4',
            'PyYAML': '>=5.4',
            'click': '>=8.0',
            'setuptools': '>=50.0',
            'numba': '>=0.50.0',
            'pandas': '>=1.0.0',
        }

        missing_required = []
        outdated_required = []
        missing_optional = []
        outdated_optional = []

        # Check required packages
        for package, version_spec in required_packages.items():
            try:
                module = importlib.import_module(package.lower().replace('-', '_'))

                # Check version if available
                if hasattr(module, '__version__'):
                    installed_version = module.__version__
                    min_version = version_spec.replace('>=', '').strip()
                    if self._compare_versions(installed_version, min_version) < 0:
                        outdated_required.append(f"{package}=={installed_version} (need {version_spec})")

            except ImportError:
                missing_required.append(f"{package}{version_spec}")

        # Check optional packages
        for package, version_spec in optional_packages.items():
            try:
                module = importlib.import_module(package.lower().replace('-', '_'))

                # Check version if available
                if hasattr(module, '__version__'):
                    installed_version = module.__version__
                    min_version = version_spec.replace('>=', '').strip()
                    if self._compare_versions(installed_version, min_version) < 0:
                        outdated_optional.append(f"{package}=={installed_version} (need {version_spec})")

            except ImportError:
                missing_optional.append(f"{package}{version_spec}")

        # Determine status based on required packages only
        if missing_required or outdated_required:
            result['status'] = 'fail'
            result['message'] = "Missing or outdated required dependencies"
            result['missing_required'] = missing_required
            result['outdated_required'] = outdated_required
            self.issues_found.append('dependencies')
            self.fixable_issues.append('dependencies')
        elif missing_optional or outdated_optional:
            result['status'] = 'warn'
            result['message'] = "All required dependencies satisfied; some optional missing"
            result['missing_optional'] = missing_optional
            result['outdated_optional'] = outdated_optional
        else:
            result['status'] = 'pass'
            result['message'] = "All dependencies satisfied"

        if verbose:
            result['details'] = {
                'required': required_packages,
                'optional': optional_packages,
                'missing_required': missing_required,
                'outdated_required': outdated_required,
                'missing_optional': missing_optional,
                'outdated_optional': outdated_optional
            }

        return result
    
    def _check_c_extensions(self, verbose: bool) -> Dict[str, Any]:
        """Check if C extensions are compiled and working."""
        result = {}
        
        try:
            # Check if C extensions exist
            import epochly
            epochly_dir = Path(epochly.__file__).parent
            
            # Look for compiled extensions (.so, .pyd files)
            extensions = list(epochly_dir.glob('**/*.so')) + list(epochly_dir.glob('**/*.pyd'))
            
            if extensions:
                result['status'] = 'pass'
                result['message'] = f"C extensions compiled ({len(extensions)} found)"
                
                if verbose:
                    result['details'] = {
                        'extensions': [str(ext.name) for ext in extensions[:10]]  # Limit to first 10
                    }
            else:
                # C extensions might not be required, so this is a warning
                result['status'] = 'warn'
                result['message'] = "C extensions not found (optional but recommended for performance)"
                result['details'] = "Run: python setup.py build_ext --inplace"
                
        except Exception as e:
            result['status'] = 'warn'
            result['message'] = "Could not check C extensions"
            result['error'] = str(e)
        
        return result
    
    def _check_virtual_env(self, verbose: bool) -> Dict[str, Any]:
        """Check if running in a virtual environment."""
        result = {}
        
        in_venv = (
            hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
            os.environ.get('VIRTUAL_ENV') is not None
        )
        
        if in_venv:
            result['status'] = 'pass'
            result['message'] = "Virtual environment active"
            
            if verbose:
                result['details'] = {
                    'venv_path': os.environ.get('VIRTUAL_ENV', sys.prefix),
                    'python_path': sys.executable
                }
        else:
            result['status'] = 'warn'
            result['message'] = "Not in virtual environment"
            result['recommendation'] = "Activate venv_new: source venv_new/bin/activate"
        
        return result
    
    def _check_gpu_support(self, verbose: bool) -> Dict[str, Any]:
        """Check GPU support and CUDA availability."""
        result = {}
        
        gpu_available = False
        cuda_info = {}
        
        # Check for NVIDIA GPU
        try:
            nvidia_smi = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if nvidia_smi.returncode == 0:
                gpu_info = nvidia_smi.stdout.strip()
                gpu_available = True
                cuda_info['gpu'] = gpu_info.split(',')[0].strip()
                
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Check CUDA version
        if gpu_available:
            try:
                nvcc = subprocess.run(
                    ['nvcc', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if nvcc.returncode == 0:
                    # Parse CUDA version from output
                    for line in nvcc.stdout.split('\n'):
                        if 'release' in line.lower():
                            cuda_info['cuda_version'] = line.split('release')[-1].strip().split(',')[0]
                            break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        # Check for CuPy
        try:
            import cupy
            cuda_info['cupy_installed'] = True
        except ImportError:
            cuda_info['cupy_installed'] = False
        
        if gpu_available:
            result['status'] = 'info'
            result['message'] = "CUDA GPU detected"
            if verbose:
                result['details'] = cuda_info
        else:
            result['status'] = 'info'
            result['message'] = "No GPU detected"
            if verbose:
                result['details'] = "GPU acceleration not available"
        
        return result
    
    def _check_performance(self, verbose: bool) -> Dict[str, Any]:
        """Check system performance characteristics."""
        result = {}
        
        try:
            import psutil
            
            # CPU info
            cpu_count = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            
            # Memory info
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            
            # Determine performance status
            if cpu_count < 4 or memory_gb < 8:
                result['status'] = 'warn'
                result['message'] = "Performance may be suboptimal"
                recommendations = []
                if cpu_count < 4:
                    recommendations.append(f"Low CPU count ({cpu_count} cores)")
                if memory_gb < 8:
                    recommendations.append(f"Low memory ({memory_gb:.1f}GB)")
                result['recommendation'] = "; ".join(recommendations)
            else:
                result['status'] = 'pass'
                result['message'] = "Performance optimal"
            
            if verbose:
                result['details'] = {
                    'cpu_count': cpu_count,
                    'cpu_freq_mhz': cpu_freq.current if cpu_freq else 'unknown',
                    'memory_gb': round(memory_gb, 1),
                    'memory_available_gb': round(memory.available / (1024**3), 1)
                }
                
        except ImportError:
            result['status'] = 'warn'
            result['message'] = "Cannot check performance (psutil not installed)"
            
        return result
    
    def _check_configuration(self, verbose: bool) -> Dict[str, Any]:
        """Check Epochly configuration."""
        result = {}
        
        try:
            from epochly.config import ConfigManager
            config_mgr = ConfigManager()
            config = config_mgr.get_all_config('effective')
            
            result['status'] = 'pass'
            result['message'] = "Configuration valid"
            
            if verbose:
                result['config'] = {
                    'mode': config.get('mode', 'unknown'),
                    'max_workers': config.get('max_workers', 'unknown'),
                    'telemetry': config.get('telemetry', 'unknown')
                }
                
        except Exception as e:
            result['status'] = 'warn'
            result['message'] = "Could not check configuration"
            result['error'] = str(e)
        
        return result
    
    def _check_system_resources(self, verbose: bool) -> Dict[str, Any]:
        """Check available system resources."""
        result = {}
        
        try:
            import psutil
            
            # Disk space
            disk_usage = psutil.disk_usage('/')
            disk_free_gb = disk_usage.free / (1024**3)
            
            # Open file descriptors (Unix-like systems)
            if hasattr(psutil.Process(), 'num_fds'):
                current_process = psutil.Process()
                num_fds = current_process.num_fds()
                max_fds = 65536  # Common default
            else:
                num_fds = None
                max_fds = None
            
            warnings = []
            if disk_free_gb < 1:
                warnings.append(f"Low disk space ({disk_free_gb:.1f}GB free)")
            
            if warnings:
                result['status'] = 'warn'
                result['message'] = "; ".join(warnings)
            else:
                result['status'] = 'pass'
                result['message'] = "System resources adequate"
            
            if verbose:
                details = {
                    'disk_free_gb': round(disk_free_gb, 1),
                    'disk_total_gb': round(disk_usage.total / (1024**3), 1)
                }
                if num_fds is not None:
                    details['open_files'] = num_fds
                    details['max_files'] = max_fds
                result['details'] = details
                
        except ImportError:
            result['status'] = 'info'
            result['message'] = "Cannot check system resources (psutil not installed)"
            
        return result
    
    def _check_file_permissions(self, verbose: bool) -> Dict[str, Any]:
        """Check file permissions for Epochly directories."""
        result = {}
        
        dirs_to_check = [
            Path.home() / '.epochly',
            Path.cwd() / '.epochly'
        ]
        
        permission_issues = []
        
        for dir_path in dirs_to_check:
            if dir_path.exists():
                # Check if writable
                test_file = dir_path / '.test_write'
                try:
                    test_file.touch()
                    test_file.unlink()
                except PermissionError:
                    permission_issues.append(str(dir_path))
        
        if permission_issues:
            result['status'] = 'warn'
            result['message'] = "Permission issues detected"
            result['directories'] = permission_issues
        else:
            result['status'] = 'pass'
            result['message'] = "File permissions OK"
        
        return result
    
    def fix_issues(self) -> Dict[str, Any]:
        """Attempt to fix detected issues."""
        fixes = {}
        
        for issue in self.fixable_issues:
            if issue == 'dependencies':
                fixes['dependencies'] = self._fix_dependencies()
            elif issue == 'epochly_installed':
                fixes['epochly_installed'] = self._fix_epochly_installation()
        
        return fixes
    
    def _fix_dependencies(self) -> Dict[str, Any]:
        """Attempt to fix missing dependencies."""
        try:
            # Run pip install for missing packages
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade',
                 'numpy>=1.20.0', 'psutil>=5.8.0', 'cryptography>=3.4',
                 'PyYAML>=5.4', 'click>=8.0'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {'fixed': True, 'message': 'Dependencies installed successfully'}
            else:
                return {'fixed': False, 'message': f'Failed to install: {result.stderr}'}
                
        except Exception as e:
            return {'fixed': False, 'message': str(e)}
    
    def _fix_epochly_installation(self) -> Dict[str, Any]:
        """Attempt to fix Epochly installation."""
        try:
            # Try to install in development mode
            epochly_root = Path(__file__).parent.parent.parent
            setup_py = epochly_root / 'setup.py'
            
            if setup_py.exists():
                result = subprocess.run(
                    [sys.executable, str(setup_py), 'develop'],
                    cwd=str(epochly_root),
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    return {'fixed': True, 'message': 'Epochly installed in development mode'}
                else:
                    return {'fixed': False, 'message': f'Installation failed: {result.stderr}'}
            else:
                return {'fixed': False, 'message': 'setup.py not found'}
                
        except Exception as e:
            return {'fixed': False, 'message': str(e)}
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """Simple version comparison."""
        def normalize(v):
            parts = [int(x) for x in v.split('.')]
            while len(parts) < 3:
                parts.append(0)
            return parts
        
        v1_parts = normalize(v1)
        v2_parts = normalize(v2)
        
        for i in range(3):
            if v1_parts[i] < v2_parts[i]:
                return -1
            elif v1_parts[i] > v2_parts[i]:
                return 1
        
        return 0