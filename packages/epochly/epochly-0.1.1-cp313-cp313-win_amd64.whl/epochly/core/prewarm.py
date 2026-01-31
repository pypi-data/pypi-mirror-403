"""
Pre-warming module for Level 3 parallel infrastructure.

This module implements eager initialization of parallel subsystems to eliminate
the 5.1x first-run penalty observed in Level 3 operations. The problem is that
Numba's parallel threading layer, OpenBLAS/MKL threads, and memory allocators
all initialize lazily on first use.

Design validated via mcp-reflect (Dec 2025). Key improvements:
- Use 256x256 matrices for BLAS (not 64x64) to ensure thread pool activation
- Thread-safety with locks around initialization
- Optional skip via EPOCHLY_SKIP_PREWARM environment variable
- Explicit array patterns for Numba to avoid race conditions

Reference: planning/level3-prewarm-design.md
"""

import logging
import os
import threading
import time
from typing import Optional

__all__ = [
    'prewarm_level3_infrastructure',
    'reset_prewarm_state',
    'get_prewarm_status',
]

# Thread-safety locks for initialization
_numba_init_lock = threading.Lock()
_blas_init_lock = threading.Lock()
_memory_init_lock = threading.Lock()

# Track initialization state
_numba_initialized = False
_blas_initialized = False
_memory_initialized = False

logger = logging.getLogger(__name__)


def _initialize_numba_threading() -> bool:
    """
    Initialize Numba's parallel threading infrastructure.

    Uses prange to force parallel thread pool creation. The explicit array
    pattern avoids race conditions that can occur with scalar reductions.

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    global _numba_initialized

    with _numba_init_lock:
        if _numba_initialized:
            return True

        try:
            from numba import njit, prange
            import numpy as np

            # Define pre-warm function with explicit array pattern
            # This avoids race conditions that can occur with scalar reductions
            @njit(parallel=True, cache=False)
            def _prewarm_numba_parallel(arr):
                """
                Minimal parallel function to initialize Numba's threading layer.
                Uses explicit array output to avoid race conditions.
                """
                n = len(arr)
                result = np.zeros(n, dtype=np.float64)
                for i in prange(n):
                    result[i] = arr[i] * 2.0
                return result

            # Execute with enough iterations to trigger parallel execution
            # 10000 elements is small but sufficient to activate thread pool
            test_arr = np.ones(10000, dtype=np.float64)
            _ = _prewarm_numba_parallel(test_arr)

            _numba_initialized = True
            logger.debug("Numba parallel threading layer initialized")
            return True

        except ImportError:
            logger.debug("Numba not available, skipping parallel pre-warm")
            return False
        except Exception as e:
            logger.warning(f"Numba parallel pre-warm failed (non-fatal): {e}")
            return False


def _initialize_blas_threading() -> bool:
    """
    Initialize OpenBLAS/MKL threading infrastructure.

    Triggers BLAS thread pool initialization with a matrix operation.
    256x256 matrices ensure BLAS actually uses threading (64x64 is too small).

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    global _blas_initialized

    with _blas_init_lock:
        if _blas_initialized:
            return True

        try:
            import numpy as np

            # 256x256 matrices ensure BLAS threading is activated
            # Smaller matrices may not trigger multi-threaded paths
            a = np.random.rand(256, 256).astype(np.float64)
            b = np.random.rand(256, 256).astype(np.float64)
            _ = np.dot(a, b)

            _blas_initialized = True
            logger.debug("BLAS threading layer initialized (256x256 matmul)")
            return True

        except Exception as e:
            logger.warning(f"BLAS pre-warm failed (non-fatal): {e}")
            return False


def _initialize_memory_paths() -> bool:
    """
    Pre-warm memory allocation paths.

    Exercises large allocation paths to warm up memory subsystem,
    TLB entries, and page tables.

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    global _memory_initialized

    with _memory_init_lock:
        if _memory_initialized:
            return True

        try:
            import numpy as np

            # Allocate and touch a medium-sized array (1MB)
            # This warms TLB without significant overhead
            arr = np.zeros(131072, dtype=np.float64)  # 1MB
            arr[0] = 1.0  # Touch first page
            arr[-1] = 1.0  # Touch last page

            # Touch middle pages to ensure full TLB warming
            stride = len(arr) // 8
            for i in range(8):
                arr[i * stride] = 1.0

            del arr

            _memory_initialized = True
            logger.debug("Memory paths pre-warmed (1MB array)")
            return True

        except Exception as e:
            logger.warning(f"Memory pre-warm failed (non-fatal): {e}")
            return False


def _initialize_fft_cache() -> bool:
    """
    Pre-warm NumPy FFT cache.

    FFT operations cache their plans, causing first-run overhead.
    A small FFT primes this cache.

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    try:
        import numpy as np

        # Small FFT to prime the cache
        # 1024 is a common FFT size that will cache nicely
        arr = np.random.rand(1024).astype(np.float64)
        _ = np.fft.fft(arr)

        logger.debug("FFT cache pre-warmed")
        return True

    except Exception as e:
        logger.debug(f"FFT pre-warm skipped (non-fatal): {e}")
        return False


def _initialize_ufunc_buffers() -> bool:
    """
    Pre-warm NumPy ufunc buffers.

    NumPy allocates internal buffers for ufunc operations on first use.
    This primes those buffers.

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    try:
        import numpy as np

        # Exercise common ufuncs with reasonable array sizes
        arr = np.random.rand(10000).astype(np.float64)
        _ = np.exp(arr)
        _ = np.sin(arr)
        _ = np.sqrt(arr)

        logger.debug("Ufunc buffers pre-warmed")
        return True

    except Exception as e:
        logger.debug(f"Ufunc pre-warm skipped (non-fatal): {e}")
        return False


def prewarm_level3_infrastructure(timeout_ms: float = 10000.0) -> bool:
    """
    Pre-warm all Level 3 parallel infrastructure.

    This function should be called after ProcessPool workers are ready
    but before returning from set_level(3) or Level 3 initialization.

    The goal is to eliminate the 5.1x first-run penalty by eagerly
    initializing all lazy components:
    - Numba parallel threading layer (~2-5 seconds on first JIT compilation)
    - OpenBLAS/MKL thread pool (~0.5-1 second lazy)
    - Memory allocator caches (~0.5-1 second lazy)
    - FFT plan cache (~0.2 seconds lazy)
    - NumPy ufunc buffers (~0.1 seconds lazy)

    Args:
        timeout_ms: Maximum time to spend on pre-warming (default 10000ms / 10s)
                   Note: This is a soft limit - each component runs to completion.
                   First call includes Numba JIT compilation (~2-5s), subsequent
                   calls complete in < 100ms due to caching.

    Returns:
        bool: True if all pre-warming completed, False if timed out or failed

    Environment Variables:
        EPOCHLY_SKIP_PREWARM: Set to truthy value ('1', 'true', 'yes', 'y', 'on') to skip
    """
    # Check for skip flag - accept common truthy values (case-insensitive)
    if os.environ.get('EPOCHLY_SKIP_PREWARM', '').lower() in ('1', 'true', 'yes', 'y', 'on'):
        logger.debug("Pre-warming skipped (EPOCHLY_SKIP_PREWARM set)")
        return True

    start = time.perf_counter()
    all_success = True

    # 1. Numba parallel threading (most important - causes largest first-run delay)
    if not _initialize_numba_threading():
        all_success = False

    # Check timeout after each component
    elapsed_ms = (time.perf_counter() - start) * 1000
    if elapsed_ms > timeout_ms:
        logger.debug(f"Pre-warm soft timeout after {elapsed_ms:.0f}ms (Numba only)")
        return False

    # 2. BLAS threading (second most important)
    if not _initialize_blas_threading():
        all_success = False

    elapsed_ms = (time.perf_counter() - start) * 1000
    if elapsed_ms > timeout_ms:
        logger.debug(f"Pre-warm soft timeout after {elapsed_ms:.0f}ms (Numba + BLAS)")
        return False

    # 3. Memory paths
    if not _initialize_memory_paths():
        all_success = False

    # 4. FFT cache (optional, low priority)
    elapsed_ms = (time.perf_counter() - start) * 1000
    if elapsed_ms < timeout_ms:
        _initialize_fft_cache()

    # 5. Ufunc buffers (optional, low priority)
    elapsed_ms = (time.perf_counter() - start) * 1000
    if elapsed_ms < timeout_ms:
        _initialize_ufunc_buffers()

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(f"Level 3 pre-warming completed in {elapsed_ms:.0f}ms")

    return all_success


def reset_prewarm_state():
    """
    Reset pre-warm state flags.

    This is primarily for testing - allows re-running pre-warm operations.
    In production, pre-warming should only happen once.
    """
    global _numba_initialized, _blas_initialized, _memory_initialized

    with _numba_init_lock:
        _numba_initialized = False
    with _blas_init_lock:
        _blas_initialized = False
    with _memory_init_lock:
        _memory_initialized = False

    logger.debug("Pre-warm state reset")


def get_prewarm_status() -> dict:
    """
    Get current pre-warm initialization status.

    Returns:
        dict: Status of each pre-warm component
    """
    return {
        'numba_initialized': _numba_initialized,
        'blas_initialized': _blas_initialized,
        'memory_initialized': _memory_initialized,
    }
