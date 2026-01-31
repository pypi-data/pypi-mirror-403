"""
JIT Capability Detection Module

Provides runtime detection of available JIT backends and acceleration
capabilities. Uses capability-based detection (try import/probe) rather
than version-based assumptions.

This module is the single source of truth for what JIT acceleration
is available on the current Python installation.

Key Design Principles:
1. Capability-based detection (not version-locked)
2. Graceful degradation when backends unavailable
3. Clear messaging about what acceleration is active
4. Python version-aware but not version-dependent

Author: Epochly Development Team
"""

import sys
import logging
import importlib.util
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, List

logger = logging.getLogger(__name__)


class JITCapability(Enum):
    """Available JIT acceleration capabilities."""
    NONE = auto()
    PYSTON_LITE = auto()      # General code JIT (3.8-3.10 only)
    NUMBA = auto()            # Numerical array JIT
    CPYTHON_NATIVE = auto()   # CPython 3.11+ specializing interpreter
    CPYTHON_JIT = auto()      # CPython 3.13+ experimental JIT


@dataclass
class JITCapabilityReport:
    """Report of detected JIT capabilities."""
    python_version: str
    general_code_acceleration: JITCapability
    numerical_acceleration: Optional[JITCapability]
    cpython_jit_detected: bool
    pyston_available: bool
    numba_available: bool
    numba_version: Optional[str]
    recommendations: List[str]


def detect_pyston_availability() -> bool:
    """
    Detect if Pyston-Lite is available and applicable.

    Pyston-Lite only supports Python 3.7-3.10. On Python 3.11+,
    this function always returns False.

    IMPORTANT: Uses importlib.util.find_spec to check availability WITHOUT
    importing the module. This prevents side effects that can cause conflicts
    with other JIT compilers like Numba.

    Returns:
        True if Pyston-Lite is available and can be used
    """
    # Version check first (Pyston only supports 3.7-3.10)
    if sys.version_info[:2] > (3, 10):
        return False

    # Use find_spec to check availability WITHOUT importing
    # Importing pyston_lite can cause side effects that conflict with Numba
    return importlib.util.find_spec("pyston_lite") is not None


def detect_numba_availability() -> tuple:
    """
    Detect if Numba is available and functional.

    Performs both import check and optional compilation test
    to verify Numba actually works on this platform.

    Returns:
        Tuple of (available: bool, version: Optional[str])
    """
    try:
        import numba
        version = numba.__version__

        # Optionally run a minimal compilation test
        # to verify Numba actually works on this platform
        try:
            @numba.njit
            def _test_func(x):
                return x + 1
            _test_func(1)  # Trigger compilation
            return True, version
        except Exception as e:
            logger.warning(f"Numba installed but compilation failed: {e}")
            return False, version

    except ImportError:
        return False, None


def detect_cpython_jit_status() -> bool:
    """
    Detect if CPython experimental JIT is enabled.

    Note: This is detection only. Epochly cannot enable CPython JIT;
    it must be compiled with --enable-experimental-jit flag.

    Returns:
        True if CPython experimental JIT is detected and enabled
    """
    if sys.version_info[:2] < (3, 13):
        return False

    # Check various indicators that JIT might be enabled

    # Method 1: Check -X jit option
    if hasattr(sys, '_xoptions'):
        xoptions = getattr(sys, '_xoptions', {})
        if xoptions and xoptions.get('jit'):
            return True

    # Method 2: Check sysconfig for JIT build flag
    try:
        import sysconfig
        config = sysconfig.get_config_vars()
        if config and config.get('PY_ENABLE_EXPERIMENTAL_JIT'):
            return True
    except Exception:
        pass

    # Method 3: Check for JIT-specific attributes
    # (May vary by CPython version)
    if hasattr(sys, '_jit_enabled'):
        return bool(getattr(sys, '_jit_enabled', False))

    return False


def detect_capabilities() -> JITCapabilityReport:
    """
    Detect all available JIT capabilities for the current environment.

    This is the main entry point for capability detection. It returns
    a comprehensive report of what acceleration is available.

    Returns:
        JITCapabilityReport with all detected capabilities
    """
    # Use indexing for version access to support both real sys.version_info
    # and tests that patch it as a tuple (e.g., with patch('sys.version_info', (3, 13, 0)))
    python_version = f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"

    # Detect individual capabilities
    pyston_available = detect_pyston_availability()
    numba_available, numba_version = detect_numba_availability()
    cpython_jit = detect_cpython_jit_status()

    # Determine general code acceleration strategy
    if sys.version_info[:2] <= (3, 10) and pyston_available:
        general_acceleration = JITCapability.PYSTON_LITE
    elif sys.version_info[:2] >= (3, 11):
        general_acceleration = JITCapability.CPYTHON_NATIVE
    else:
        general_acceleration = JITCapability.NONE

    # Determine numerical acceleration
    numerical_acceleration = JITCapability.NUMBA if numba_available else None

    # Build recommendations
    recommendations = _build_recommendations(
        python_version,
        pyston_available,
        numba_available,
        cpython_jit
    )

    return JITCapabilityReport(
        python_version=python_version,
        general_code_acceleration=general_acceleration,
        numerical_acceleration=numerical_acceleration,
        cpython_jit_detected=cpython_jit,
        pyston_available=pyston_available,
        numba_available=numba_available,
        numba_version=numba_version,
        recommendations=recommendations
    )


def _build_recommendations(
    python_version: str,
    pyston_available: bool,
    numba_available: bool,
    cpython_jit: bool
) -> List[str]:
    """
    Build list of recommendations based on detected capabilities.

    Args:
        python_version: Current Python version string
        pyston_available: Whether Pyston-Lite is available
        numba_available: Whether Numba is available
        cpython_jit: Whether CPython experimental JIT is enabled

    Returns:
        List of recommendation strings
    """
    recommendations = []

    if not numba_available:
        recommendations.append(
            "Install Numba for 10-100x speedup on numerical operations: pip install numba"
        )

    if sys.version_info[:2] <= (3, 10) and not pyston_available:
        recommendations.append(
            "Install Pyston-Lite for 10-25% general code speedup: pip install pyston_lite_autoload"
        )

    if sys.version_info[:2] >= (3, 11) and sys.version_info[:2] < (3, 13):
        recommendations.append(
            f"Python {python_version} includes native specializing interpreter (~25% faster than 3.10)"
        )

    if sys.version_info[:2] >= (3, 13):
        if cpython_jit:
            recommendations.append(
                "CPython experimental JIT detected and enabled"
            )
        else:
            recommendations.append(
                "CPython 3.13+ experimental JIT available but not enabled. "
                "Rebuild Python with --enable-experimental-jit for potential additional speedups"
            )

    return recommendations


def get_jit_status_message() -> str:
    """
    Get a human-readable JIT status message for logging/display.

    Returns:
        Multi-line string describing current JIT capabilities
    """
    report = detect_capabilities()

    lines = [
        f"Python {report.python_version} JIT Capabilities:",
        f"  General Code: {report.general_code_acceleration.name}",
    ]

    if report.numerical_acceleration:
        lines.append(f"  Numerical: {report.numerical_acceleration.name} (v{report.numba_version})")
    else:
        lines.append("  Numerical: NOT AVAILABLE")

    if report.cpython_jit_detected:
        lines.append("  CPython JIT: ENABLED (experimental)")

    if report.recommendations:
        lines.append("  Recommendations:")
        for rec in report.recommendations:
            lines.append(f"    - {rec}")

    return "\n".join(lines)
