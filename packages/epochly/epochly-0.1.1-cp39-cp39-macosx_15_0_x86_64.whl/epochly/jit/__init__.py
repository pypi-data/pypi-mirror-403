"""
Epochly JIT Compilation Module - Multi-JIT Strategy 2025

Provides Just-In-Time compilation capabilities for Level 2 optimization
using multiple JIT backends (Numba, Python 3.13 Native, Pyston-Lite) 
with intelligent selection based on Python version and workload type.

Author: Epochly Development Team
"""

import logging
import sys
from typing import List, Optional

# Import base classes
from .base import JITBackend, CompilationStatus, JITCompilationResult, JITCompiler

# Import JIT backends conditionally based on Multi-JIT Strategy 2025
_available_backends = []

# Try to import Numba (Python 3.10+, numerical workloads)
try:
    if sys.version_info >= (3, 10):
        from .numba_jit import NumbaJIT
        _available_backends.append(JITBackend.NUMBA)
        NUMBA_AVAILABLE = True
    else:
        NumbaJIT = None
        NUMBA_AVAILABLE = False
except ImportError:
    NumbaJIT = None
    NUMBA_AVAILABLE = False

# Try to import Python 3.13+ Native JIT
try:
    if sys.version_info >= (3, 13):
        from .native_jit import NativeJIT
        # Check if JIT is actually enabled
        if hasattr(sys, '_jit_enabled') and getattr(sys, '_jit_enabled', False):
            _available_backends.append(JITBackend.NATIVE)
            NATIVE_JIT_AVAILABLE = True
        else:
            NATIVE_JIT_AVAILABLE = False
    else:
        NativeJIT = None
        NATIVE_JIT_AVAILABLE = False
except ImportError:
    NativeJIT = None
    NATIVE_JIT_AVAILABLE = False

# Try to import Pyston-Lite (Python 3.7-3.10 ONLY - pyston-lite 2.3.5 limitation)
try:
    if sys.version_info[:2] <= (3, 10):
        from .pyston_jit import PystonJIT
        _available_backends.append(JITBackend.PYSTON)
        PYSTON_AVAILABLE = True
    else:
        PystonJIT = None
        PYSTON_AVAILABLE = False
except ImportError:
    PystonJIT = None
    PYSTON_AVAILABLE = False

# Import manager
from .manager import JITManager, JITConfiguration

# Import CUDA pattern detection and kernel compilation (Level 4 GPU loop acceleration)
try:
    from .cuda_pattern_detector import (
        CUDAPatternDetector,
        PatternAnalysis,
        StencilInfo,
        MapInfo,
        ReduceInfo
    )
    from .cuda_kernel_compiler import (
        CUDAKernelCompiler,
        CompiledKernel,
        CUPY_AVAILABLE as CUDA_JIT_AVAILABLE
    )
except ImportError:
    CUDAPatternDetector = None
    CUDAKernelCompiler = None
    CompiledKernel = None
    PatternAnalysis = None
    StencilInfo = None
    MapInfo = None
    ReduceInfo = None
    CUDA_JIT_AVAILABLE = False

logger = logging.getLogger(__name__)

def get_available_backends() -> List[JITBackend]:
    """
    Get list of available JIT backends.
    
    Returns:
        List of available JIT backends
    """
    return _available_backends.copy()

def is_backend_available(backend: JITBackend) -> bool:
    """
    Check if a specific JIT backend is available.
    
    Args:
        backend: JIT backend to check
        
    Returns:
        True if backend is available, False otherwise
    """
    return backend in _available_backends

def get_recommended_backend() -> Optional[JITBackend]:
    """
    Get the recommended JIT backend for the current Python version.
    
    Returns:
        Recommended JIT backend or None if no backends available
    """
    if sys.version_info >= (3, 13) and NATIVE_JIT_AVAILABLE:
        return JITBackend.NATIVE
    elif sys.version_info >= (3, 10) and NUMBA_AVAILABLE:
        return JITBackend.NUMBA
    elif sys.version_info[:2] <= (3, 10) and PYSTON_AVAILABLE:
        return JITBackend.PYSTON
    else:
        return None

def create_jit_manager(config: Optional[JITConfiguration] = None) -> JITManager:
    """
    Create a JIT manager with available backends.
    
    Args:
        config: Optional JIT configuration
        
    Returns:
        Configured JIT manager instance
    """
    return JITManager(config=config)

def get_jit_compatibility_info() -> dict:
    """
    Get JIT compatibility information for the current environment.
    
    Returns:
        Dictionary with compatibility information
    """
    return {
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'available_backends': [b.value for b in _available_backends],
        'recommended_backend': get_recommended_backend().value if get_recommended_backend() else None,
        'backend_availability': {
            'numba': NUMBA_AVAILABLE,
            'native': NATIVE_JIT_AVAILABLE,
            'pyston': PYSTON_AVAILABLE,
            'cuda_jit': CUDA_JIT_AVAILABLE
        },
        'strategy': 'Multi-JIT Strategy 2025',
        'cuda_loop_acceleration': CUDA_JIT_AVAILABLE
    }

# Public API
__all__ = [
    # Base classes
    'JITBackend',
    'CompilationStatus',
    'JITCompilationResult',
    'JITCompiler',

    # Backends (conditionally available)
    'NumbaJIT',
    'NativeJIT',
    'PystonJIT',

    # Manager
    'JITManager',
    'JITConfiguration',

    # CUDA Pattern Detection and Kernel Compilation (Level 4 GPU loop acceleration)
    'CUDAPatternDetector',
    'CUDAKernelCompiler',
    'CompiledKernel',
    'PatternAnalysis',
    'StencilInfo',
    'MapInfo',
    'ReduceInfo',

    # Utilities
    'get_available_backends',
    'is_backend_available',
    'get_recommended_backend',
    'create_jit_manager',
    'get_jit_compatibility_info',

    # Availability flags
    'NUMBA_AVAILABLE',
    'NATIVE_JIT_AVAILABLE',
    'PYSTON_AVAILABLE',
    'CUDA_JIT_AVAILABLE'
]

# Log available backends and strategy
try:
    compatibility_info = get_jit_compatibility_info()
    logger.info(f"Epochly JIT module loaded - {compatibility_info['strategy']}")
    logger.info(f"Python {compatibility_info['python_version']} with backends: {compatibility_info['available_backends']}")
    if compatibility_info['recommended_backend']:
        logger.info(f"Recommended backend: {compatibility_info['recommended_backend']}")
    else:
        logger.warning("No JIT backends available for this Python version")
except Exception as e:
    logger.error(f"Error initializing JIT module: {e}")

# Module metadata
__version__ = "2.0.0"  # Updated for Multi-JIT Strategy 2025
__author__ = "Epochly Development Team"