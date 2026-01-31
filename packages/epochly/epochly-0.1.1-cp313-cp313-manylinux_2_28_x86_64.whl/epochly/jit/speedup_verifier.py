"""
JIT Speedup Verification

Verifies that JIT-compiled functions actually provide performance improvement
over the original Python baseline.

Prevents the common failure mode where compilation "succeeds" but the
compiled version is slower than pure Python (e.g., object mode fallback,
compilation overhead exceeds gains, etc.).

Author: Epochly Development Team
Date: 2025-12-12
"""

import time
import logging
from typing import Callable, Tuple, Any, NamedTuple
from dataclasses import dataclass

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SpeedupVerificationResult:
    """
    Result of speedup verification.

    Attributes:
        is_faster: True if compiled version is faster than original
        baseline_time_ms: Time for original function (milliseconds)
        compiled_time_ms: Time for compiled function (milliseconds)
        speedup_ratio: Ratio of baseline/compiled (>1.0 means compiled is faster)
        use_compiled: Recommendation whether to use compiled version
        reason: Explanation of decision
    """
    is_faster: bool
    baseline_time_ms: float
    compiled_time_ms: float
    speedup_ratio: float
    use_compiled: bool
    reason: str


# Minimum baseline time (ms) for meaningful speedup measurement
# Functions faster than this are in the noise floor - timing is unreliable
# This prevents rejecting compiled versions for micro-functions where
# both original and compiled are equally fast (<0.5ms)
MIN_MEASURABLE_BASELINE_MS = 0.5

# Maximum acceptable slowdown for sub-millisecond functions
# If compiled is >2x slower even for tiny functions, reject it
MAX_ACCEPTABLE_SLOWDOWN = 0.5  # compiled must be at least 50% as fast


def verify_speedup(
    original_func: Callable,
    compiled_func: Callable,
    test_args: Tuple[Any, ...] = (),
    test_kwargs: dict = None,
    num_trials: int = 10,
    min_speedup: float = 1.10
) -> SpeedupVerificationResult:
    """
    Verify that compiled function is actually faster than original.

    Benchmarks both versions and ensures compiled provides minimum speedup
    threshold. Prevents usage of compiled functions that are slower or
    provide marginal improvement (where compilation overhead isn't worth it).

    For very fast functions (<0.5ms baseline), speedup verification is relaxed
    since timing is in the noise floor. However, if compiled is >2x slower,
    it's still rejected.

    Args:
        original_func: Original Python function
        compiled_func: JIT-compiled version
        test_args: Arguments to use for benchmarking
        test_kwargs: Keyword arguments for benchmarking
        num_trials: Number of benchmark iterations
        min_speedup: Minimum speedup ratio required (default 1.10 = 10% faster)

    Returns:
        SpeedupVerificationResult with decision and metrics

    Example:
        >>> result = verify_speedup(original, compiled, test_args=(1000,))
        >>> if result.use_compiled:
        ...     return compiled  # Safe to use
        >>> else:
        ...     return original  # Stick with Python
    """
    if test_kwargs is None:
        test_kwargs = {}

    try:
        # Warm up both functions (avoid measuring cold start)
        for _ in range(3):
            _ = original_func(*test_args, **test_kwargs)
            _ = compiled_func(*test_args, **test_kwargs)

        # Benchmark original
        t0 = time.perf_counter()
        for _ in range(num_trials):
            _ = original_func(*test_args, **test_kwargs)
        baseline_time_ms = (time.perf_counter() - t0) * 1000 / num_trials

        # Benchmark compiled
        t0 = time.perf_counter()
        for _ in range(num_trials):
            _ = compiled_func(*test_args, **test_kwargs)
        compiled_time_ms = (time.perf_counter() - t0) * 1000 / num_trials

        # Calculate speedup
        speedup_ratio = baseline_time_ms / compiled_time_ms if compiled_time_ms > 0 else 0.0

        # CRITICAL FIX (Dec 2025): Handle sub-millisecond functions separately
        # For very fast functions, timing is unreliable (noise floor).
        # Accept compiled if it's not significantly slower (>2x).
        # This prevents rejecting equivalent implementations where both are ~0.01ms.
        if baseline_time_ms < MIN_MEASURABLE_BASELINE_MS:
            # Sub-millisecond function - timing is unreliable
            # But still reject if compiled is grossly slower
            if speedup_ratio >= MAX_ACCEPTABLE_SLOWDOWN:
                reason = f"Sub-ms function ({baseline_time_ms:.3f}ms) - accepting compiled"
                use_compiled = True
                is_faster = speedup_ratio >= 1.0
            else:
                reason = f"Sub-ms function but compiled is {speedup_ratio:.2f}x slower - rejecting"
                use_compiled = False
                is_faster = False
        else:
            # Normal speedup verification for meaningful workloads
            is_faster = speedup_ratio > 1.0
            meets_threshold = speedup_ratio >= min_speedup

            if meets_threshold:
                reason = f"{speedup_ratio:.2f}x speedup (threshold: {min_speedup:.2f}x)"
                use_compiled = True
            elif is_faster:
                reason = f"Speedup {speedup_ratio:.2f}x below threshold {min_speedup:.2f}x"
                use_compiled = False
            else:
                reason = f"Compiled is SLOWER ({speedup_ratio:.2f}x) - likely object mode"
                use_compiled = False

        logger.info(
            f"Speedup verification for {getattr(original_func, '__name__', 'unknown')}: "
            f"{baseline_time_ms:.2f}ms → {compiled_time_ms:.2f}ms "
            f"({speedup_ratio:.2f}x, use_compiled={use_compiled})"
        )

        return SpeedupVerificationResult(
            is_faster=is_faster,
            baseline_time_ms=baseline_time_ms,
            compiled_time_ms=compiled_time_ms,
            speedup_ratio=speedup_ratio,
            use_compiled=use_compiled,
            reason=reason
        )

    except Exception as e:
        logger.error(f"Speedup verification failed: {e}")
        # On error, don't use compiled (safe fallback)
        return SpeedupVerificationResult(
            is_faster=False,
            baseline_time_ms=0.0,
            compiled_time_ms=0.0,
            speedup_ratio=0.0,
            use_compiled=False,
            reason=f"Verification error: {e}"
        )


def quick_speedup_check(
    original_func: Callable,
    compiled_func: Callable,
    test_args: Tuple[Any, ...] = ()
) -> bool:
    """
    Quick check if compiled function is faster (lightweight version).

    Uses fewer trials and lower threshold for faster verification.

    Args:
        original_func: Original function
        compiled_func: Compiled function
        test_args: Test arguments

    Returns:
        True if compiled is faster, False otherwise
    """
    result = verify_speedup(
        original_func,
        compiled_func,
        test_args=test_args,
        num_trials=5,
        min_speedup=1.05  # Only 5% threshold for quick check
    )
    return result.use_compiled
