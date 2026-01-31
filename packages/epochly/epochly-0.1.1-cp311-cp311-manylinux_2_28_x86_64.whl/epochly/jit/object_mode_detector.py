"""
Object Mode Detection for Numba JIT Compilation

Detects when Numba falls back to object mode (interpreted Python)
which can be 3x SLOWER than pure Python baseline.

Critical for preventing performance regressions from "successful" compilations
that actually hurt performance.

Author: Epochly Development Team
Date: 2025-12-12
"""

import logging
from typing import Optional, Callable

from ..utils.logger import get_logger

logger = get_logger(__name__)


def detect_compilation_mode(compiled_func: Callable) -> Optional[str]:
    """
    Detect whether a Numba-compiled function is in nopython or object mode.

    Numba can silently fall back to object mode when nopython compilation fails.
    Object mode runs interpreted Python code that is often SLOWER than pure Python
    due to repeated interpreter calls and lack of optimization.

    Args:
        compiled_func: Potentially Numba-compiled function

    Returns:
        'nopython': Successfully compiled in nopython mode (fast)
        'object': Fell back to object mode (slow - often 3x slower than Python)
        None: Not a Numba function or compilation hasn't occurred yet

    Example:
        >>> import numba
        >>> @numba.njit
        ... def fast_func(x):
        ...     return x * 2
        >>> mode = detect_compilation_mode(fast_func)
        >>> assert mode == 'nopython'
    """
    # Check if this is a Numba function
    if not hasattr(compiled_func, 'nopython_signatures'):
        return None

    # Check nopython_signatures to determine mode
    # Empty tuple/list means object mode fallback occurred
    signatures = compiled_func.nopython_signatures

    if not signatures or len(signatures) == 0:
        # Object mode - compilation "succeeded" but fell back to interpreted code
        logger.warning(
            f"Object mode detected for {getattr(compiled_func, '__name__', 'unknown')}: "
            f"compiled function may be SLOWER than pure Python!"
        )
        return 'object'

    # Has nopython signatures - successfully compiled to native code
    logger.debug(
        f"Nopython mode confirmed for {getattr(compiled_func, '__name__', 'unknown')}: "
        f"{len(signatures)} signature(s)"
    )
    return 'nopython'


def is_object_mode(compiled_func: Callable) -> bool:
    """
    Quick check if function is compiled in object mode.

    Args:
        compiled_func: Function to check

    Returns:
        True if object mode, False otherwise
    """
    return detect_compilation_mode(compiled_func) == 'object'


def verify_nopython_mode(compiled_func: Callable) -> bool:
    """
    Verify function is compiled in nopython mode (not object mode).

    Use this as a gate before using compiled functions to prevent
    performance regressions from object mode fallback.

    Args:
        compiled_func: Function to verify

    Returns:
        True if nopython mode, False if object mode or not Numba

    Example:
        >>> compiled = numba.njit(my_func)
        >>> if verify_nopython_mode(compiled):
        ...     return compiled  # Safe to use
        >>> else:
        ...     return my_func  # Use original - compiled is slower
    """
    mode = detect_compilation_mode(compiled_func)

    if mode == 'nopython':
        return True

    if mode == 'object':
        logger.error(
            f"Object mode compilation rejected for {getattr(compiled_func, '__name__', 'unknown')}: "
            f"would be slower than Python baseline"
        )
        return False

    # Not a Numba function
    return False
