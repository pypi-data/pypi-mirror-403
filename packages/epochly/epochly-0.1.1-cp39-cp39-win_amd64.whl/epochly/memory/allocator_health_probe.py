"""
Fast Allocator Health Probe (perf_fixes5.md Finding #6).

Startup probe to verify fast allocator is available and performant.
"""

import time
import logging
import os
from typing import Tuple


# Global feature flag (perf_fixes5.md Finding #6)
_FAST_ALLOCATOR_ENABLED = True
_ALLOCATOR_PROBE_RESULT = None


def is_fast_allocator_enabled() -> bool:
    """
    Check if fast allocator is enabled via feature flag.

    Returns:
        True if fast allocator should be used, False to use fallback
    """
    return _FAST_ALLOCATOR_ENABLED


def get_allocator_probe_result():
    """Get cached allocator probe result."""
    return _ALLOCATOR_PROBE_RESULT


def probe_fast_allocator() -> Tuple[bool, float, str]:
    """
    Probe fast allocator availability and performance.

    Sets global feature flag based on probe results.

    Returns:
        (available, latency_us, message)
    """
    global _FAST_ALLOCATOR_ENABLED, _ALLOCATOR_PROBE_RESULT
    logger = logging.getLogger(__name__)

    try:
        # Use FastMemoryPool which wraps the Cython fast_allocator
        from .fast_memory_pool import FastMemoryPool, FAST_ALLOCATOR_AVAILABLE

        if not FAST_ALLOCATOR_AVAILABLE:
            msg = "Fast allocator Cython module not available, using Python fallback"
            logger.info(msg)
            _FAST_ALLOCATOR_ENABLED = False
            result = (False, 0.0, msg)
            _ALLOCATOR_PROBE_RESULT = result
            return result

        logger.debug("Fast allocator module imported successfully")

        # Benchmark allocation latency via FastMemoryPool
        test_pool = FastMemoryPool(total_size=10 * 1024 * 1024, name="ProbePool")
        test_size = 1024 * 1024  # 1MB
        iterations = 100

        start = time.perf_counter_ns()
        for _ in range(iterations):
            try:
                handle = test_pool.allocate(test_size)
                if handle is not None:
                    test_pool.deallocate(handle)
            except Exception as e:
                logger.warning(f"Fast allocator test failed: {e}")
                # Disable feature flag on test failure
                _FAST_ALLOCATOR_ENABLED = False
                result = (False, 0.0, f"Allocation test failed: {e}")
                _ALLOCATOR_PROBE_RESULT = result
                return result

        elapsed_ns = time.perf_counter_ns() - start
        avg_latency_us = (elapsed_ns / iterations) / 1000  # Convert to microseconds

        # perf_fixes5.md Finding #6: Set feature flag based on performance
        # Disable if slower than 100μs (2× worse than target)
        if avg_latency_us > 100:
            _FAST_ALLOCATOR_ENABLED = False
            msg = f"Fast allocator slow ({avg_latency_us:.1f}μs > 100μs threshold), DISABLED. Rebuild recommended."
            logger.warning(msg)
            result = (False, avg_latency_us, msg)
        else:
            _FAST_ALLOCATOR_ENABLED = True
            msg = f"Fast allocator healthy ({avg_latency_us:.1f}μs), ENABLED"
            logger.info(msg)
            result = (True, avg_latency_us, msg)

        _ALLOCATOR_PROBE_RESULT = result
        return result

    except ImportError as e:
        _FAST_ALLOCATOR_ENABLED = False
        msg = f"Fast allocator not available: {e}. Run: python setup_fast_allocator.py"
        logger.warning(msg)
        result = (False, 0.0, msg)
        _ALLOCATOR_PROBE_RESULT = result
        return result
    except Exception as e:
        _FAST_ALLOCATOR_ENABLED = False
        msg = f"Fast allocator probe failed: {e}"
        logger.error(msg)
        result = (False, 0.0, msg)
        _ALLOCATOR_PROBE_RESULT = result
        return result
