"""
Worker Process Initializer

Provides the initialization function for all Level 3 worker processes.
Ensures workers have proper environment setup to prevent double interception
AND proper pre-warming to eliminate first-run variance.

RCA Fix (Jan 2025): Workers are now pre-warmed during initialization to
eliminate the 3.72x execution variance observed when:
1. Pre-warming ran only in main process (workers are separate processes)
2. Each worker had to JIT-compile Numba functions on first call
3. OpenBLAS thread pools initialized lazily per-worker

Author: Epochly Development Team
Date: November 16, 2025
Updated: January 2025 (Pre-warming fix for LEVEL_3 variance)
"""

import os
import sys
import multiprocessing


def _get_threads_per_worker() -> int:
    """
    Calculate optimal thread count per worker.

    Prevents thread oversubscription by dividing CPU cores among workers.
    Assumes 4 workers (default pre-warm count) if not specified.

    Returns:
        int: Number of threads per worker (minimum 1)
    """
    try:
        cpu_count = multiprocessing.cpu_count()
        # Assume 4 workers (default pre-warm count) for thread calculation
        # Can be overridden via EPOCHLY_WORKER_COUNT env var
        worker_count = int(os.environ.get('EPOCHLY_WORKER_COUNT', '4'))
        threads_per_worker = max(1, cpu_count // worker_count)
        return threads_per_worker
    except Exception:
        return 2  # Safe default


def _set_thread_control_env_vars():
    """
    Set thread control environment variables to prevent oversubscription.

    With N workers each spawning CPU_COUNT OpenBLAS threads:
    Total threads = N * CPU_COUNT >> available cores
    This causes context switching overhead and reduces performance.

    Fix: Limit threads per worker to CPU_COUNT / N_WORKERS.
    """
    threads = _get_threads_per_worker()
    threads_str = str(threads)

    # OpenMP threads (used by many BLAS implementations)
    os.environ['OMP_NUM_THREADS'] = threads_str

    # OpenBLAS threads
    os.environ['OPENBLAS_NUM_THREADS'] = threads_str

    # Intel MKL threads
    os.environ['MKL_NUM_THREADS'] = threads_str

    # Numba threads (for prange parallelism)
    os.environ['NUMBA_NUM_THREADS'] = threads_str


def _prewarm_numba_threading() -> bool:
    """
    Pre-warm Numba's parallel threading infrastructure in worker.

    Numba JIT functions are compiled per-process. When a function is pickled
    and sent to a worker, the compiled code is NOT transferred. Each worker
    must recompile on first call.

    This pre-warms the threading layer (not the user's function) to reduce
    first-call overhead.

    Returns:
        bool: True if pre-warming succeeded
    """
    try:
        from numba import njit, prange
        import numpy as np

        # Pre-warm threading layer with a simple parallel function
        # cache=True allows caching the pre-warm function itself
        @njit(parallel=True, cache=True)
        def _worker_prewarm_numba(arr):
            """Minimal parallel function to initialize threading layer."""
            n = len(arr)
            result = np.zeros(n, dtype=np.float64)
            for i in prange(n):
                result[i] = arr[i] * 2.0
            return result

        # Execute to trigger compilation and threading init
        test_arr = np.ones(1000, dtype=np.float64)
        _ = _worker_prewarm_numba(test_arr)

        os.environ['EPOCHLY_WORKER_NUMBA_READY'] = '1'
        return True

    except ImportError:
        # Numba not available - not an error
        return True
    except Exception:
        # Pre-warm failed but not fatal
        return False


def _prewarm_blas_threading() -> bool:
    """
    Pre-warm OpenBLAS/MKL threading infrastructure in worker.

    BLAS libraries initialize their thread pools lazily on first use.
    This causes variable first-call overhead.

    Pre-warming triggers thread pool creation during worker startup.

    Returns:
        bool: True if pre-warming succeeded
    """
    try:
        import numpy as np

        # 256x256 matrices trigger BLAS threading (smaller matrices may not)
        a = np.random.rand(256, 256).astype(np.float64)
        b = np.random.rand(256, 256).astype(np.float64)
        _ = np.dot(a, b)

        os.environ['EPOCHLY_WORKER_BLAS_READY'] = '1'
        return True

    except Exception:
        # Pre-warm failed but not fatal
        return False


def _prewarm_memory_paths() -> bool:
    """
    Pre-warm memory allocation paths in worker.

    Exercises large allocation paths to warm up memory subsystem,
    TLB entries, and page tables.

    Returns:
        bool: True if pre-warming succeeded
    """
    try:
        import numpy as np

        # Allocate and touch a medium-sized array (1MB)
        arr = np.zeros(131072, dtype=np.float64)  # 1MB
        arr[0] = 1.0  # Touch first page
        arr[-1] = 1.0  # Touch last page

        # Touch middle pages for full TLB warming
        stride = len(arr) // 8
        for i in range(8):
            arr[i * stride] = 1.0

        del arr
        return True

    except Exception:
        return False


def _prewarm_worker():
    """
    Pre-warm all infrastructure in worker process.

    Called during worker initialization to eliminate first-run variance.
    Sets EPOCHLY_WORKER_PREWARMED=1 on success.

    Can be disabled via EPOCHLY_SKIP_WORKER_PREWARM=1 for debugging.

    CRITICAL (Jan 2026): In CI environments, skip pre-warming entirely because
    Numba's parallel JIT compilation can cause segfaults that Python cannot catch.
    This was identified as the root cause of BrokenProcessPool errors on Python 3.11+
    in GitHub Actions. The segfault occurs during parallel threading initialization.
    """
    # Check if pre-warming is disabled
    if os.environ.get('EPOCHLY_SKIP_WORKER_PREWARM', '').lower() in ('1', 'true', 'yes'):
        return

    # CRITICAL FIX (Jan 2026): Skip pre-warming in CI environments
    # Numba's parallel=True JIT compilation can cause segfaults that crash workers
    # The segfaults are not catchable by Python's try/except and cause BrokenProcessPool
    # This was observed on Python 3.11, 3.12, 3.13 in GitHub Actions CI
    if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS') or os.environ.get('PYTEST_CURRENT_TEST'):
        return

    try:
        # Pre-warm in order of importance
        _prewarm_numba_threading()
        _prewarm_blas_threading()
        _prewarm_memory_paths()

        # Mark worker as pre-warmed
        os.environ['EPOCHLY_WORKER_PREWARMED'] = '1'

    except Exception:
        # Pre-warming failed but worker can still function
        pass


def epochly_worker_initializer():
    """
    Initialize worker process with Epochly disabled and infrastructure pre-warmed.

    CRITICAL: This function MUST be called at worker process startup to:
    1. Prevent recursive interception when workers execute OperationDescriptor
    2. Pre-warm Numba/BLAS/memory to eliminate first-run variance (RCA fix Jan 2025)
    3. Control thread count to prevent oversubscription

    Environment Variables Set:
    - EPOCHLY_DISABLE_INTERCEPTION=1: Prevents import hook from wrapping functions
    - EPOCHLY_DISABLE=1: Completely disables Epochly in workers
    - EPOCHLY_DISABLE_AUTO_INIT=1: Prevents auto-initialization
    - EPOCHLY_WORKER_PROCESS=1: Signals this is a worker process
    - OMP_NUM_THREADS: Limits OpenMP threads per worker
    - OPENBLAS_NUM_THREADS: Limits OpenBLAS threads per worker
    - MKL_NUM_THREADS: Limits Intel MKL threads per worker
    - NUMBA_NUM_THREADS: Limits Numba parallel threads per worker
    - EPOCHLY_WORKER_PREWARMED=1: Set after successful pre-warm
    - EPOCHLY_WORKER_NUMBA_READY=1: Set after Numba threading is ready
    - EPOCHLY_WORKER_BLAS_READY=1: Set after BLAS threading is ready

    Contract:
    - Workers must NOT initialize EpochlyCore
    - Workers must NOT wrap library functions
    - Workers should import and use libraries normally
    - OperationDescriptor.execute() should call unwrapped functions
    - First task should be fast (no lazy initialization overhead)

    Troubleshooting:
    - If workers still wrap functions: Check that import hook respects env vars
    - If workers fail to start: Check SharedMemory compatibility
    - If tests hang: Increase timeout or reduce array sizes
    - If variance is high: Check EPOCHLY_SKIP_WORKER_PREWARM is not set

    See Also:
    - src/epochly/interception/WORKER_CONTRACT.md
    - tests/unit/executor/test_worker_environment.py
    - tests/unit/executor/test_worker_prewarm.py (RCA fix tests)
    - planning/rca-level3-warmup-spike.md (Phase 1.1 optimization)
    """
    try:
        # Step 1: Disable all Epochly functionality in workers
        os.environ['EPOCHLY_DISABLE_INTERCEPTION'] = '1'
        os.environ['EPOCHLY_DISABLE'] = '1'
        os.environ['EPOCHLY_DISABLE_AUTO_INIT'] = '1'

        # Phase 1.1 Performance Optimization: Mark this as a worker process
        # This enables fast license cache lookup instead of full validation
        os.environ['EPOCHLY_WORKER_PROCESS'] = '1'

        # Step 2: Set thread control env vars BEFORE any imports
        # This prevents OpenBLAS/MKL from spawning too many threads
        _set_thread_control_env_vars()

        # Step 3: Pre-warm infrastructure
        # This eliminates first-run variance by eagerly initializing:
        # - Numba parallel threading layer
        # - OpenBLAS/MKL thread pool
        # - Memory allocation paths
        _prewarm_worker()

    except Exception as e:
        # Log warning but don't fail - worker should try to continue
        print(f"Warning: Failed to initialize worker: {e}",
              file=sys.stderr)
        # Worker will attempt to execute without these protections
        # May result in degraded performance but won't crash


# Alias for compatibility
worker_init = epochly_worker_initializer
