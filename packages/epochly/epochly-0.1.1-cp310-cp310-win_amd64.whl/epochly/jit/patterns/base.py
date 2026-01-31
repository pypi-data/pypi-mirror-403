"""
Base Classes for Modular Pattern Detection System

Provides the foundational infrastructure for extensible pattern detection:
- BasePatternInfo: Base dataclass for all pattern information
- PatternDetector: Abstract base class for pattern detectors
- PatternRegistry: Central registry for managing pattern detectors
- PatternDetectionResult: Wrapper for detection results with metadata

This modular architecture allows:
- Easy addition of new pattern detectors
- Priority-based detection ordering
- Feature flagging for gradual rollout
- Graceful degradation on detector failures

Author: Epochly Development Team
"""

from __future__ import annotations

import ast
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class BasePatternInfo:
    """
    Base dataclass for all pattern information.

    All specialized pattern info classes (FFTInfo, RollingStatsInfo, etc.)
    must inherit from this class to ensure consistent interface.

    Attributes:
        pattern_name: Unique identifier for the pattern type (e.g., 'fft', 'stencil')
        confidence: Detection confidence score (0.0 to 1.0)
        source_start_line: Starting line number in source code
        source_end_line: Ending line number in source code
        gpu_suitable: Whether this pattern is suitable for GPU acceleration
        memory_pattern: Memory access pattern ('coalesced', 'strided', 'random')
    """
    pattern_name: str
    confidence: float = 0.0
    source_start_line: int = 0
    source_end_line: int = 0
    gpu_suitable: bool = True
    memory_pattern: str = 'unknown'


class PatternDetector(ABC):
    """
    Abstract base class for pattern detectors.

    Pattern detectors analyze source code (as text and AST) to identify
    specific computational patterns suitable for optimization.

    Subclasses must implement:
    - pattern_name property: Unique identifier for the pattern
    - detection_priority property: Order in detection pipeline (lower = earlier)
    - detect() method: Actual pattern detection logic

    Example usage:
        class FFTPatternDetector(PatternDetector):
            @property
            def pattern_name(self) -> str:
                return 'fft'

            @property
            def detection_priority(self) -> int:
                return 5  # Check early in pipeline

            def detect(self, source: str, tree: ast.AST) -> Optional[FFTInfo]:
                # Detection logic here
                if 'fft' in source.lower():
                    return FFTInfo(pattern_name='fft', ...)
                return None
    """

    @property
    @abstractmethod
    def pattern_name(self) -> str:
        """
        Unique identifier for this pattern detector.

        This name is used for:
        - Registry lookup
        - Logging and debugging
        - Pattern result identification
        """
        pass

    @property
    @abstractmethod
    def detection_priority(self) -> int:
        """
        Detection priority (lower values = checked earlier).

        Guidelines for priority assignment:
        - 1-10: High-specificity regex patterns (FFT, Top-K)
        - 10-30: Simple structural patterns
        - 30-60: AST-based patterns
        - 60-100: Complex multi-statement patterns
        - 100+: Fallback/general patterns

        Rationale: More specific patterns should be checked first
        to avoid false positives from general patterns.
        """
        pass

    @abstractmethod
    def detect(self, source: str, tree: ast.AST) -> Optional[BasePatternInfo]:
        """
        Detect the pattern in the given source code.

        Args:
            source: Source code as a string
            tree: Parsed AST of the source code

        Returns:
            BasePatternInfo (or subclass) if pattern detected, None otherwise.

        Note:
            - Detection should be fast (avoid expensive operations)
            - Return None quickly for non-matching code
            - Set confidence appropriately based on match quality
        """
        pass

    @property
    def enabled(self) -> bool:
        """
        Whether this detector is enabled.

        Can be overridden in subclasses to support feature flags
        for gradual rollout of new detectors.

        Returns:
            True if detector should be used, False to skip.
        """
        return True


class PatternRegistry:
    """
    Central registry for managing pattern detectors.

    Provides:
    - Registration and unregistration of detectors
    - Priority-sorted detection ordering
    - First-match and all-match detection methods
    - Graceful error handling for failing detectors
    - Feature flag support via detector.enabled

    Example usage:
        registry = PatternRegistry()
        registry.register(FFTPatternDetector())
        registry.register(StencilPatternDetector())

        result = registry.detect_first(source, tree)
        if result:
            print(f"Detected: {result.pattern_name}")
    """

    def __init__(self):
        """Initialize empty registry."""
        self._detectors: List[PatternDetector] = []
        self._sorted_cache: Optional[List[PatternDetector]] = None

    @property
    def detectors(self) -> List[PatternDetector]:
        """
        Get list of registered detectors, sorted by priority.

        Returns:
            List of PatternDetector instances, sorted by detection_priority
            (lower priority values first).

        Note:
            Sorting is cached for performance; cache is invalidated on
            register/unregister.
        """
        if self._sorted_cache is None:
            self._sorted_cache = sorted(
                self._detectors,
                key=lambda d: d.detection_priority
            )
        return self._sorted_cache

    def register(self, detector: PatternDetector) -> None:
        """
        Register a new pattern detector.

        Args:
            detector: PatternDetector instance to register

        Note:
            Detectors are automatically sorted by priority when accessed.
            Duplicate detectors (same pattern_name) are allowed but not recommended.
        """
        self._detectors.append(detector)
        self._sorted_cache = None  # Invalidate cache
        logger.debug(f"Registered pattern detector: {detector.pattern_name} "
                     f"(priority={detector.detection_priority})")

    def unregister(self, pattern_name: str) -> bool:
        """
        Unregister a detector by pattern name.

        Args:
            pattern_name: Name of the pattern to unregister

        Returns:
            True if detector was found and removed, False otherwise.
        """
        original_count = len(self._detectors)
        self._detectors = [d for d in self._detectors if d.pattern_name != pattern_name]
        removed = len(self._detectors) < original_count
        if removed:
            self._sorted_cache = None  # Invalidate cache
            logger.debug(f"Unregistered pattern detector: {pattern_name}")
        return removed

    def get_detector(self, pattern_name: str) -> Optional[PatternDetector]:
        """
        Get a detector by pattern name.

        Args:
            pattern_name: Name of the pattern to look up

        Returns:
            PatternDetector instance if found, None otherwise.
        """
        for detector in self._detectors:
            if detector.pattern_name == pattern_name:
                return detector
        return None

    def detect_first(self, source: str, tree: ast.AST) -> Optional[BasePatternInfo]:
        """
        Detect the first matching pattern.

        Detectors are tried in priority order (lower priority first).
        Returns immediately when the first detector returns a match.

        Args:
            source: Source code as a string
            tree: Parsed AST of the source code

        Returns:
            BasePatternInfo if a pattern is detected, None if no match.

        Note:
            - Disabled detectors are skipped
            - Exceptions in detectors are logged and skipped (graceful degradation)
        """
        for detector in self.detectors:
            if not detector.enabled:
                continue

            try:
                result = detector.detect(source, tree)
                if result is not None:
                    logger.debug(f"Pattern detected by {detector.pattern_name}: "
                                 f"confidence={result.confidence}")
                    return result
            except Exception as e:
                # Graceful degradation: log and continue to next detector
                # Using debug level since this is expected behavior, not an error
                logger.debug(f"Detector {detector.pattern_name} failed: {e}")
                continue

        return None

    def detect_all(self, source: str, tree: ast.AST) -> List[BasePatternInfo]:
        """
        Detect all matching patterns.

        Runs all detectors and collects all matches (not just the first).

        Args:
            source: Source code as a string
            tree: Parsed AST of the source code

        Returns:
            List of BasePatternInfo for all detected patterns (may be empty).
            Results are ordered by detector priority.

        Note:
            - Disabled detectors are skipped
            - Exceptions in detectors are logged and skipped
        """
        results: List[BasePatternInfo] = []

        for detector in self.detectors:
            if not detector.enabled:
                continue

            try:
                result = detector.detect(source, tree)
                if result is not None:
                    results.append(result)
            except Exception as e:
                # Graceful degradation: log and continue to next detector
                # Using debug level since this is expected behavior, not an error
                logger.debug(f"Detector {detector.pattern_name} failed: {e}")
                continue

        return results


@dataclass
class PatternDetectionResult:
    """
    Wrapper for pattern detection results with metadata.

    Provides additional context about the detection process:
    - Which detector produced the result
    - How long detection took
    - Convenience accessors for common fields

    Useful for debugging, profiling, and logging detection performance.
    """
    pattern_info: BasePatternInfo
    detector_name: str
    detection_time_ms: float = 0.0

    @property
    def pattern_name(self) -> str:
        """Shortcut to pattern_info.pattern_name."""
        return self.pattern_info.pattern_name

    @property
    def confidence(self) -> float:
        """Shortcut to pattern_info.confidence."""
        return self.pattern_info.confidence


def detect_with_timing(
    registry: PatternRegistry,
    source: str,
    tree: ast.AST
) -> Optional[PatternDetectionResult]:
    """
    Detect pattern with timing information.

    Utility function that wraps registry.detect_first() with timing.

    Args:
        registry: Pattern registry to use
        source: Source code as a string
        tree: Parsed AST

    Returns:
        PatternDetectionResult with timing info if pattern detected, None otherwise.
    """
    start_time = time.perf_counter()
    result = registry.detect_first(source, tree)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    if result is None:
        return None

    # Find which detector produced the result
    for detector in registry.detectors:
        if detector.pattern_name == result.pattern_name:
            return PatternDetectionResult(
                pattern_info=result,
                detector_name=type(detector).__name__,
                detection_time_ms=elapsed_ms
            )

    # Fallback if detector not found
    return PatternDetectionResult(
        pattern_info=result,
        detector_name='unknown',
        detection_time_ms=elapsed_ms
    )
