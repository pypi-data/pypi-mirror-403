"""
Epochly GPU Acceleration Module (Level 4 Enhancement)

This module provides optional GPU acceleration for Epochly through CuPy integration,
implementing the Level 4 progressive enhancement tier. GPU acceleration is
transparent to users and gracefully falls back to CPU when unavailable.

Key features:
- Automatic GPU availability detection
- Zero-code-change acceleration
- Dynamic NumPy/CuPy switching  
- Intelligent workload offloading
- Unified memory management
- Performance monitoring

Author: Epochly Development Team
"""

from .cupy_manager import CuPyManager
from .offload_optimizer import GPUOffloadOptimizer
from .gpu_detector import GPUDetector
from .gpu_memory_manager import GPUMemoryManager
from .gpu_diagnostics import (
    run_diagnostics,
    format_report,
    get_installation_guide,
    get_user_friendly_gpu_error,
    GPUDiagnosticReport,
    GPUDiagnosticStatus
)

__all__ = [
    'CuPyManager',
    'GPUOffloadOptimizer',
    'GPUDetector',
    'GPUMemoryManager',
    # Diagnostics and user guidance
    'run_diagnostics',
    'format_report',
    'get_installation_guide',
    'get_user_friendly_gpu_error',
    'GPUDiagnosticReport',
    'GPUDiagnosticStatus'
]

def get_gpu_manager():
    """Get the global GPU manager instance."""
    return CuPyManager.get_instance()

def is_gpu_available():
    """Check if GPU acceleration is available."""
    return GPUDetector.is_available()

def get_gpu_info():
    """Get information about available GPU resources."""
    return GPUDetector.get_gpu_info()