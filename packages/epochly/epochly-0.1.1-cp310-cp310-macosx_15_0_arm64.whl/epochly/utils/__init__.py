"""
Epochly Utilities Package

Common utilities and helper functions for the Epochly framework.
"""

from .logger import get_logger, setup_logging
from .config import ConfigManager
from .decorators import singleton, thread_safe
from .exceptions import EpochlyError, EpochlyConfigError, EpochlyCompatibilityError

# Safe memory profiling compatibility
try:
    from .memory_profiling_compat import (
        SafeTracemalloc, 
        safe_memory_profiling,
        start_memory_profiling,
        get_memory_usage,
        stop_memory_profiling
    )
    _memory_profiling_available = True
except ImportError:
    _memory_profiling_available = False

__all__ = [
    'get_logger',
    'setup_logging', 
    'ConfigManager',
    'singleton',
    'thread_safe',
    'EpochlyError',
    'EpochlyConfigError',
    'EpochlyCompatibilityError',
]

# Add memory profiling exports if available
if _memory_profiling_available:
    __all__.extend([
        'SafeTracemalloc',
        'safe_memory_profiling',
        'start_memory_profiling',
        'get_memory_usage',
        'stop_memory_profiling'
    ])