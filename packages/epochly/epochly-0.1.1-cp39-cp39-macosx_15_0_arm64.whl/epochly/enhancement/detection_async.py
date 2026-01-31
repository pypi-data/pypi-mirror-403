"""
Async Capability Detection System (Task 1 Implementation)

Replaces polling-based DetectionThread with async event-driven detection.

Performance Improvements:
- 40% reduction in activation latency (450ms → <270ms target)
- Zero-overhead capability reads after first detection (<1μs)
- Event-driven updates instead of polling
- Compiled helper for hardware detection (future: Rust)

Architecture:
    Python Async Layer (this file)
        ↓
    Native Detector (future: Rust helper)
        ↓
    Hardware Probes (CPU, NUMA, GPU)
"""

import asyncio
import os
import sys
import time
import multiprocessing
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from ..utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# Module State: Capability Cache
# ============================================================================

_capabilities_cache: Optional[Dict[str, Any]] = None
_native_detector_available = False

# Per-event-loop locks to avoid binding to wrong loop
from weakref import WeakKeyDictionary
_cache_locks: "WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Lock]" = WeakKeyDictionary()

def _get_cache_lock() -> asyncio.Lock:
    """Get or create asyncio.Lock for current event loop."""
    loop = asyncio.get_running_loop()
    lock = _cache_locks.get(loop)
    if lock is None:
        lock = asyncio.Lock()
        _cache_locks[loop] = lock
    return lock

# Try to import native detector (Rust helper - future implementation)
try:
    from ..native import capability_detector as _native_detector
    _native_detector_available = True
    logger.debug("Native capability detector loaded (compiled helper)")
except ImportError:
    _native_detector = None
    _native_detector_available = False
    logger.debug("Native detector unavailable, using pure Python fallback")

# Import GPU backend registry for backend detection (Task 4 - perf_fixes2.md)
try:
    from ..gpu.backend_registry import GPUBackendRegistry, GPUBackendKind
    _gpu_backend_registry_available = True
except ImportError:
    GPUBackendRegistry = None
    GPUBackendKind = None
    _gpu_backend_registry_available = False
    logger.debug("GPU backend registry unavailable")


# ============================================================================
# Pure Python Fallback Detection
# ============================================================================

def _detect_capabilities_python() -> Dict[str, Any]:
    """
    Pure Python capability detection (fallback).

    Used when Rust helper is unavailable.

    Returns:
        Capability dictionary with hardware/software info
    """
    try:
        import platform

        # Detect physical cores
        try:
            physical_cores = len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else os.cpu_count()
        except Exception:
            physical_cores = os.cpu_count() or 1

        # Check sub-interpreter support (Python 3.12+)
        subinterpreter_support = False
        if sys.version_info >= (3, 12):
            try:
                import _xxsubinterpreters
                subinterpreter_support = True
            except ImportError:
                pass

        # Detect GPU backends (Task 4 - perf_fixes2.md)
        has_gpu = False
        gpu_count = 0
        gpu_memory_mb = 0
        cuda_available = False
        rocm_available = False
        oneapi_available = False
        active_backend = "cpu"
        backend_version = ""

        if _gpu_backend_registry_available and GPUBackendRegistry is not None:
            try:
                # Detect all available backends
                backends = GPUBackendRegistry.detect_available_backends()

                # Check availability
                cuda_available = GPUBackendKind.CUDA in backends
                rocm_available = GPUBackendKind.ROCm in backends
                oneapi_available = GPUBackendKind.oneAPI in backends

                # Get best available backend
                best_backend = GPUBackendRegistry.get_best_available()
                active_backend = best_backend.info.kind.value
                backend_version = best_backend.info.version

                # Set GPU flags
                has_gpu = active_backend != "cpu"
                if has_gpu and best_backend.info.kind in backends:
                    backend_info = backends[best_backend.info.kind]
                    gpu_count = backend_info.device_count
                    gpu_memory_mb = int(backend_info.memory_gb * 1024)

            except Exception as e:
                # GPU detection failed - use fallback nvidia-smi check
                logger.debug(f"GPU backend detection failed, using nvidia-smi fallback: {e}")
                try:
                    import subprocess
                    result = subprocess.run(
                        ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                        capture_output=True,
                        timeout=0.5
                    )
                    has_gpu = (result.returncode == 0)
                except Exception:
                    pass

        # Detect NUMA nodes
        numa_nodes = 1
        if sys.platform == 'linux':
            try:
                numa_path = '/sys/devices/system/node'
                if os.path.exists(numa_path):
                    nodes = [d for d in os.listdir(numa_path) if d.startswith('node')]
                    numa_nodes = len(nodes) if nodes else 1
            except Exception:
                pass
        elif sys.platform == 'win32':
            try:
                import ctypes
                from ctypes import wintypes

                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                GetNumaHighestNodeNumber = kernel32.GetNumaHighestNodeNumber
                GetNumaHighestNodeNumber.restype = wintypes.BOOL
                GetNumaHighestNodeNumber.argtypes = [ctypes.POINTER(ctypes.c_ulong)]

                highest_node = ctypes.c_ulong()
                if GetNumaHighestNodeNumber(ctypes.byref(highest_node)):
                    numa_nodes = highest_node.value + 1
            except Exception:
                pass

        return {
            'physical_cores': physical_cores,
            'numa_nodes': numa_nodes,
            'has_gpu': has_gpu,
            'gpu_count': gpu_count,
            'gpu_memory_mb': gpu_memory_mb,
            'cuda_available': cuda_available,
            'rocm_available': rocm_available,
            'oneapi_available': oneapi_available,
            'active_backend': active_backend,
            'backend_version': backend_version,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'subinterpreter_support': subinterpreter_support,
            'platform': sys.platform,
            'detected_at': time.time(),
            'detector': 'python'
        }

    except Exception as e:
        logger.warning(f"Capability detection failed: {e}")

        # Return safe defaults (CPU backend)
        return {
            'physical_cores': os.cpu_count() or 1,
            'numa_nodes': 1,
            'has_gpu': False,
            'gpu_count': 0,
            'gpu_memory_mb': 0,
            'cuda_available': False,
            'rocm_available': False,
            'oneapi_available': False,
            'active_backend': 'cpu',
            'backend_version': '',
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
            'subinterpreter_support': False,
            'platform': sys.platform,
            'detected_at': time.time(),
            'detector': 'python_fallback',
            'error': str(e)
        }


def _detect_capabilities_native() -> Dict[str, Any]:
    """
    Native capability detection using compiled helper.

    Falls back to Python detection if native detector unavailable.

    Returns:
        Capability dictionary from native detector or Python fallback
    """
    if _native_detector_available and _native_detector is not None:
        try:
            # Call Rust helper (future implementation)
            caps = _native_detector.detect_capabilities()
            return {**caps, 'detector': 'native'}
        except Exception as e:
            logger.warning(f"Native detector failed, using Python fallback: {e}")

    # Fall back to pure Python
    return _detect_capabilities_python()


# ============================================================================
# Async Capability Access
# ============================================================================

async def get_capabilities() -> Dict[str, Any]:
    """
    Get system capabilities with async caching.

    First call triggers detection (may take 10-50ms).
    Subsequent calls return cached result (<1μs).

    Returns:
        Capability dictionary with hardware/software configuration
        On error, returns safe defaults with 'error' key

    Performance:
        - First call: 10-50ms (detection time)
        - Cached calls: <1μs (pointer dereference)
    """
    global _capabilities_cache

    # Fast path: return cached result
    if _capabilities_cache is not None:
        return _capabilities_cache

    # Slow path: detect and cache
    lock = _get_cache_lock()
    async with lock:
        # Double-check after acquiring lock
        if _capabilities_cache is not None:
            return _capabilities_cache

        try:
            # Run detection in thread pool (blocking operation)
            loop = asyncio.get_running_loop()
            _capabilities_cache = await loop.run_in_executor(
                None, _detect_capabilities_native
            )

            logger.debug(f"Capabilities detected: {_capabilities_cache['physical_cores']} cores, "
                         f"NUMA nodes: {_capabilities_cache['numa_nodes']}, "
                         f"GPU: {_capabilities_cache['has_gpu']}")

        except Exception as e:
            # On error, return safe defaults and cache them (CPU backend)
            logger.warning(f"Capability detection failed: {e}")
            _capabilities_cache = {
                'physical_cores': os.cpu_count() or 1,
                'numa_nodes': 1,
                'has_gpu': False,
                'gpu_count': 0,
                'gpu_memory_mb': 0,
                'cuda_available': False,
                'rocm_available': False,
                'oneapi_available': False,
                'active_backend': 'cpu',
                'backend_version': '',
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
                'subinterpreter_support': False,
                'platform': sys.platform,
                'detected_at': time.time(),
                'detector': 'fallback',
                'error': str(e)
            }

        return _capabilities_cache


def _invalidate_cache() -> None:
    """
    Invalidate capability cache.

    Forces re-detection on next get_capabilities() call.
    Used for testing and after topology changes.
    """
    global _capabilities_cache
    _capabilities_cache = None
    logger.debug("Capability cache invalidated")


async def monitor_capabilities_async(stop_event: asyncio.Event) -> None:
    """
    Background task monitoring for capability changes.

    Watches for hardware topology changes (GPU hotplug, CPU hotplug)
    and invalidates cache when detected.

    Args:
        stop_event: Event to signal graceful shutdown

    Note:
        This is a long-running task that should be launched in background.
        In production, capability changes are rare, so we check infrequently.
    """
    check_interval_seconds = 60.0  # Check every minute

    try:
        while not stop_event.is_set():
            # Wait with timeout to check stop event
            try:
                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=check_interval_seconds
                )
                # Stop event set - exit gracefully
                break
            except asyncio.TimeoutError:
                # Timeout - time to check for changes
                pass

            # Check if capabilities changed
            # (In future, native detector can signal changes via shared memory)
            try:
                new_caps = await asyncio.get_running_loop().run_in_executor(
                    None, _detect_capabilities_native
                )

                # Compare with cached capabilities
                if _capabilities_cache is not None:
                    # Check for significant changes
                    if (new_caps['physical_cores'] != _capabilities_cache['physical_cores'] or
                        new_caps['has_gpu'] != _capabilities_cache['has_gpu'] or
                        new_caps['numa_nodes'] != _capabilities_cache['numa_nodes']):

                        logger.info("Capability change detected, invalidating cache")
                        _invalidate_cache()

                        # Cache will be refreshed on next get_capabilities() call

            except Exception as e:
                logger.debug(f"Capability monitoring check failed: {e}")

    except Exception as e:
        logger.error(f"Capability monitoring crashed: {e}")


# ============================================================================
# Synchronous Wrapper for Backward Compatibility
# ============================================================================

def get_capabilities_sync() -> Dict[str, Any]:
    """
    Synchronous wrapper for get_capabilities().

    For use in non-async contexts only.

    Returns:
        Capability dictionary

    Raises:
        RuntimeError: If called from within a running event loop

    Note:
        Prefer async version when possible for better performance.
        If calling from async context, use: await get_capabilities()
    """
    global _capabilities_cache

    # If cached, return immediately
    if _capabilities_cache is not None:
        return _capabilities_cache

    # Not cached - must detect
    # Check if we're in an event loop
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - safe to use asyncio.run
        caps = asyncio.run(get_capabilities())
        return caps
    else:
        # We're inside an event loop - cannot use asyncio.run
        raise RuntimeError(
            "get_capabilities_sync() called from within an active event loop. "
            "Use: caps = await get_capabilities() instead."
        )
