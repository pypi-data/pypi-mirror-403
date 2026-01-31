"""
Epochly Memory Profiling Compatibility Module

This module provides safe wrappers and utilities for using Python's memory
profiling tools (tracemalloc, memory_profiler) alongside Epochly's custom
memory management systems.

The main issue is that Epochly uses custom memory allocators (especially the
Cython fast allocator) that can conflict with tracemalloc's internal
memory tracking, potentially causing segfaults or memory corruption.

Author: Epochly Development Team
"""

import tracemalloc
import threading
import warnings
from contextlib import contextmanager
from typing import Tuple, Optional, Dict, Any
import psutil

from .logger import get_logger

logger = get_logger(__name__)


class TracememallocConflictError(Exception):
    """Raised when tracemalloc conflicts with Epochly memory management"""
    pass


class SafeTracemalloc:
    """
    Safe wrapper for tracemalloc that handles Epochly conflicts gracefully.
    
    This class provides a drop-in replacement for tracemalloc functions
    that won't crash when used with Epochly's memory management.
    """
    
    _lock = threading.Lock()
    _epochly_initialized = False
    _conflict_detected = False
    _fallback_mode = False
    
    @classmethod
    def mark_epochly_initialized(cls):
        """Mark that Epochly memory management is active"""
        cls._epochly_initialized = True
        logger.debug("Epochly memory management marked as initialized")
    
    @classmethod
    def start(cls, nframe: int = 1) -> bool:
        """
        Safely start tracemalloc.
        
        Returns:
            True if tracemalloc was started successfully, False otherwise
        """
        with cls._lock:
            if cls._conflict_detected:
                logger.debug("Tracemalloc conflict detected, using fallback mode")
                return False
                
            try:
                if not tracemalloc.is_tracing():
                    tracemalloc.start(nframe)
                    logger.debug(f"Tracemalloc started with nframe={nframe}")
                return True
                
            except Exception as e:
                cls._handle_conflict(e)
                return False
    
    @classmethod
    def stop(cls) -> bool:
        """
        Safely stop tracemalloc.
        
        Returns:
            True if tracemalloc was stopped successfully, False otherwise
        """
        with cls._lock:
            try:
                if tracemalloc.is_tracing():
                    tracemalloc.stop()
                    logger.debug("Tracemalloc stopped")
                return True
                
            except Exception as e:
                logger.warning(f"Error stopping tracemalloc: {e}")
                # Don't mark as conflict - stopping errors are less critical
                return False
    
    @classmethod
    def get_traced_memory(cls) -> Tuple[int, int]:
        """
        Safely get traced memory statistics.
        
        Returns:
            Tuple of (current, peak) memory usage in bytes.
            Returns (0, 0) if tracemalloc is not available.
        """
        if cls._fallback_mode:
            return cls._get_psutil_memory()
            
        try:
            if tracemalloc.is_tracing():
                return tracemalloc.get_traced_memory()
            return (0, 0)
            
        except Exception as e:
            cls._handle_conflict(e)
            return cls._get_psutil_memory()
    
    @classmethod
    def take_snapshot(cls):
        """
        Safely take a memory snapshot.
        
        Returns:
            Snapshot object or None if not available
        """
        if cls._fallback_mode:
            return None
            
        try:
            if tracemalloc.is_tracing():
                return tracemalloc.take_snapshot()
            return None
            
        except Exception as e:
            cls._handle_conflict(e)
            return None
    
    @classmethod
    def is_tracing(cls) -> bool:
        """Check if tracemalloc is currently tracing"""
        if cls._fallback_mode:
            return False
            
        try:
            return tracemalloc.is_tracing()
        except Exception:
            return False
    
    @classmethod
    def clear_traces(cls):
        """Safely clear all traces"""
        try:
            if tracemalloc.is_tracing():
                tracemalloc.clear_traces()
        except Exception as e:
            logger.debug(f"Error clearing traces: {e}")
    
    @classmethod
    def _handle_conflict(cls, error: Exception):
        """Handle a detected conflict with Epochly"""
        cls._conflict_detected = True
        cls._fallback_mode = True
        
        if cls._epochly_initialized:
            logger.warning(
                f"Tracemalloc conflict detected with Epochly memory management: {error}. "
                "Falling back to psutil-based memory monitoring."
            )
        else:
            # Re-raise if Epochly isn't initialized - this is a real error
            raise error
    
    @classmethod
    def _get_psutil_memory(cls) -> Tuple[int, int]:
        """Get memory usage via psutil as fallback"""
        try:
            process = psutil.Process()
            info = process.memory_info()
            # Return RSS as both current and peak (approximation)
            return (info.rss, info.rss)
        except Exception:
            return (0, 0)
    
    @classmethod
    def reset_conflict_detection(cls):
        """Reset conflict detection (mainly for testing)"""
        cls._conflict_detected = False
        cls._fallback_mode = False


@contextmanager
def safe_memory_profiling(nframe: int = 1):
    """
    Context manager for safe memory profiling with Epochly.
    
    This ensures tracemalloc is safely started and stopped,
    handling any conflicts with Epochly's memory management.
    
    Example:
        with safe_memory_profiling():
            # Your code here
            current, peak = SafeTracemalloc.get_traced_memory()
    """
    was_tracing = SafeTracemalloc.is_tracing()
    started_by_us = False
    
    try:
        if not was_tracing:
            started_by_us = SafeTracemalloc.start(nframe)
            
        yield SafeTracemalloc
        
    finally:
        if started_by_us:
            SafeTracemalloc.stop()


class MemoryProfilingAdapter:
    """
    Adapter that provides a unified interface for memory profiling,
    automatically selecting the best available method.
    """
    
    def __init__(self):
        self._method = self._detect_best_method()
        self._baseline_memory = None
        
    def _detect_best_method(self) -> str:
        """Detect the best available memory profiling method"""
        # Try tracemalloc first
        if SafeTracemalloc.start():
            SafeTracemalloc.stop()
            return 'tracemalloc'
            
        # Fall back to psutil
        try:
            process = psutil.Process()
            process.memory_info()
            return 'psutil'
        except Exception:
            pass
            
        # Last resort - use OS-level info
        return 'basic'
    
    def start_profiling(self):
        """Start memory profiling"""
        if self._method == 'tracemalloc':
            SafeTracemalloc.start()
        elif self._method == 'psutil':
            process = psutil.Process()
            self._baseline_memory = process.memory_info().rss
            
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get current memory usage statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        stats = {
            'method': self._method,
            'current_mb': 0,
            'peak_mb': 0,
            'available': True
        }
        
        if self._method == 'tracemalloc':
            current, peak = SafeTracemalloc.get_traced_memory()
            stats.update({
                'current_mb': current / 1024 / 1024,
                'peak_mb': peak / 1024 / 1024
            })
            
        elif self._method == 'psutil':
            try:
                process = psutil.Process()
                info = process.memory_info()
                stats.update({
                    'current_mb': info.rss / 1024 / 1024,
                    'peak_mb': info.rss / 1024 / 1024,  # Approximation
                    'vms_mb': info.vms / 1024 / 1024
                })
                
                if self._baseline_memory:
                    stats['delta_mb'] = (info.rss - self._baseline_memory) / 1024 / 1024
                    
            except Exception as e:
                stats['error'] = str(e)
                stats['available'] = False
                
        elif self._method == 'basic':
            # Very basic - just report total system memory
            try:
                import resource
                usage = resource.getrusage(resource.RUSAGE_SELF)
                stats.update({
                    'current_mb': usage.ru_maxrss / 1024,  # May need adjustment per platform
                    'peak_mb': usage.ru_maxrss / 1024
                })
            except Exception:
                stats['available'] = False
                
        return stats
    
    def stop_profiling(self):
        """Stop memory profiling"""
        if self._method == 'tracemalloc':
            SafeTracemalloc.stop()
        self._baseline_memory = None
    
    def take_snapshot(self) -> Optional[Any]:
        """Take a memory snapshot if supported"""
        if self._method == 'tracemalloc':
            return SafeTracemalloc.take_snapshot()
        return None


# Global instance for convenience
_global_profiler = MemoryProfilingAdapter()


def start_memory_profiling():
    """Convenience function to start memory profiling"""
    _global_profiler.start_profiling()


def get_memory_usage() -> Dict[str, Any]:
    """Convenience function to get memory usage"""
    return _global_profiler.get_memory_usage()


def stop_memory_profiling():
    """Convenience function to stop memory profiling"""
    _global_profiler.stop_profiling()


# Monkey-patch warnings for common issues
def _warn_on_memory_profiler_import():
    """Warn when memory_profiler is imported with Epochly"""
    warnings.warn(
        "memory_profiler may conflict with Epochly's memory management. "
        "Consider using epochly.utils.memory_profiling_compat instead.",
        UserWarning,
        stacklevel=2
    )


# Install warning hooks if epochly is already initialized
try:
    from .. import __epochly_initialized__
    if __epochly_initialized__:
        SafeTracemalloc.mark_epochly_initialized()
except Exception:
    pass