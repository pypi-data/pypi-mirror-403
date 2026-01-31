"""
Modular Pattern Detection System for Epochly

This module provides extensible pattern detection infrastructure for identifying
computational patterns suitable for GPU acceleration.

Pattern Categories:
- Spectral: FFT variants (numpy.fft, scipy.fft, cupy.fft)
- Time Series: Rolling statistics (pandas.rolling, ewm)
- Financial: Black-Scholes, Monte Carlo, Greeks

Usage:
    from epochly.jit.patterns import PatternRegistry, FFTPatternDetector

    # Create registry and register detectors
    registry = PatternRegistry()
    registry.register(FFTPatternDetector())

    # Detect patterns in source code
    import ast
    source = "result = np.fft.fft(data)"
    tree = ast.parse(source)
    result = registry.detect_first(source, tree)

    if result:
        print(f"Detected: {result.pattern_name} (confidence={result.confidence})")

Author: Epochly Development Team
"""

from .base import (
    BasePatternInfo,
    PatternDetector,
    PatternRegistry,
    PatternDetectionResult,
    detect_with_timing,
)

from .spectral_patterns import (
    FFTInfo,
    FFTPatternDetector,
)

from .timeseries_patterns import (
    RollingStatsInfo,
    RollingStatsDetector,
)

from .financial_patterns import (
    BlackScholesInfo,
    BlackScholesDetector,
    MonteCarloInfo,
    MonteCarloDetector,
)

__all__ = [
    # Base infrastructure
    'BasePatternInfo',
    'PatternDetector',
    'PatternRegistry',
    'PatternDetectionResult',
    'detect_with_timing',
    # Spectral patterns
    'FFTInfo',
    'FFTPatternDetector',
    # Time series patterns
    'RollingStatsInfo',
    'RollingStatsDetector',
    # Financial patterns
    'BlackScholesInfo',
    'BlackScholesDetector',
    'MonteCarloInfo',
    'MonteCarloDetector',
]


def create_default_registry() -> PatternRegistry:
    """
    Create a PatternRegistry with all default pattern detectors registered.

    Returns:
        PatternRegistry with FFT, RollingStats, BlackScholes, and MonteCarlo
        detectors registered in priority order.

    Usage:
        registry = create_default_registry()
        result = registry.detect_first(source, ast.parse(source))
    """
    registry = PatternRegistry()

    # Register detectors in priority order (they auto-sort, but this is explicit)
    registry.register(FFTPatternDetector())          # Priority 5
    registry.register(BlackScholesDetector())        # Priority 20
    registry.register(RollingStatsDetector())        # Priority 25
    registry.register(MonteCarloDetector())          # Priority 55

    return registry
