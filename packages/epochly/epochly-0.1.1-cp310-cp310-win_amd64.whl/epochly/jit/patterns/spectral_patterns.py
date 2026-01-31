"""
Spectral Pattern Detection (FFT Variants)

Detects FFT and spectral computation patterns:
- FFT/IFFT (1D, 2D, N-D)
- Real FFT (RFFT/IRFFT)
- Short-Time Fourier Transform (STFT)
- FFT-based convolution
- FFT shift operations

Author: Epochly Development Team
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Set

from .base import BasePatternInfo, PatternDetector

logger = logging.getLogger(__name__)


@dataclass
class FFTInfo(BasePatternInfo):
    """
    Information about a detected FFT pattern.

    Attributes:
        variant: Specific FFT variant ('fft', 'ifft', 'rfft', 'irfft', 'fft2', 'fftn',
                 'stft', 'istft', 'fftconvolve')
        dimensions: Number of dimensions (1, 2, or n)
        is_inverse: True if this is an inverse transform
        axis: Specified axis for transform (None if not specified)
        is_real_input: True if input is real (rfft variants)
        is_real_output: True if output is real (irfft variants)
        is_convolution: True if this is FFT-based convolution
        has_shift: True if fftshift/ifftshift is applied
        has_frequency_axis: True if fftfreq/rfftfreq is used
    """
    variant: str = 'fft'
    dimensions: int = 1
    is_inverse: bool = False
    axis: Optional[int] = None
    is_real_input: bool = False
    is_real_output: bool = False
    is_convolution: bool = False
    has_shift: bool = False
    has_frequency_axis: bool = False


class FFTPatternDetector(PatternDetector):
    """
    Detects FFT and spectral computation patterns.

    Uses regex-based detection for high accuracy and low false positives.
    FFT patterns are highly distinctive (function names, module paths) making
    regex reliable.

    Detection priority: 5 (very early, highly specific)
    """

    # FFT function patterns with their properties
    FFT_PATTERNS = {
        # Basic FFT variants
        'fft': {'variant': 'fft', 'dimensions': 1, 'is_inverse': False},
        'ifft': {'variant': 'ifft', 'dimensions': 1, 'is_inverse': True},
        # Real FFT
        'rfft': {'variant': 'rfft', 'dimensions': 1, 'is_inverse': False, 'is_real_input': True},
        'irfft': {'variant': 'irfft', 'dimensions': 1, 'is_inverse': True, 'is_real_output': True},
        # 2D FFT
        'fft2': {'variant': 'fft2', 'dimensions': 2, 'is_inverse': False},
        'ifft2': {'variant': 'ifft2', 'dimensions': 2, 'is_inverse': True},
        'rfft2': {'variant': 'rfft2', 'dimensions': 2, 'is_inverse': False, 'is_real_input': True},
        'irfft2': {'variant': 'irfft2', 'dimensions': 2, 'is_inverse': True, 'is_real_output': True},
        # N-D FFT
        'fftn': {'variant': 'fftn', 'dimensions': -1, 'is_inverse': False},  # -1 = N-D
        'ifftn': {'variant': 'ifftn', 'dimensions': -1, 'is_inverse': True},
        'rfftn': {'variant': 'rfftn', 'dimensions': -1, 'is_inverse': False, 'is_real_input': True},
        'irfftn': {'variant': 'irfftn', 'dimensions': -1, 'is_inverse': True, 'is_real_output': True},
        # STFT
        'stft': {'variant': 'stft', 'dimensions': 1, 'is_inverse': False},
        'istft': {'variant': 'istft', 'dimensions': 1, 'is_inverse': True},
        # Convolution via FFT
        'fftconvolve': {'variant': 'fftconvolve', 'dimensions': 1, 'is_inverse': False, 'is_convolution': True},
    }

    # Regex patterns for detecting FFT calls
    # Matches: np.fft.fft, numpy.fft.fft, scipy.fft.fft, cupy.fft.fft, fft.fft, etc.
    FFT_CALL_REGEX = re.compile(
        r'\b(?:np|numpy|scipy|cupy|cp|fft|signal)\.(?:fft\.)?'
        r'(fft|ifft|rfft|irfft|fft2|ifft2|rfft2|irfft2|fftn|ifftn|rfftn|irfftn|'
        r'stft|istft|fftconvolve)\s*\(',
        re.IGNORECASE
    )

    # Regex for direct function calls (after from-import)
    # Matches: fft(x), stft(x, fs), fftconvolve(a, b) when imported directly
    FFT_DIRECT_CALL_REGEX = re.compile(
        r'(?<![.\w])(fft|ifft|rfft|irfft|fft2|ifft2|rfft2|irfft2|fftn|ifftn|'
        r'rfftn|irfftn|stft|istft|fftconvolve)\s*\(',
        re.IGNORECASE
    )

    # Regex for fftshift/ifftshift
    FFT_SHIFT_REGEX = re.compile(
        r'\b(?:np|numpy|scipy|cupy|cp)\.fft\.(fftshift|ifftshift)\s*\(',
        re.IGNORECASE
    )

    # Regex for fftfreq/rfftfreq
    FFT_FREQ_REGEX = re.compile(
        r'\b(?:np|numpy|scipy|cupy|cp)\.fft\.(fftfreq|rfftfreq)\s*\(',
        re.IGNORECASE
    )

    @property
    def pattern_name(self) -> str:
        return 'fft'

    @property
    def detection_priority(self) -> int:
        return 5  # Very early - highly specific pattern

    def detect(self, source: str, tree: ast.AST) -> Optional[FFTInfo]:
        """
        Detect FFT patterns in source code.

        Uses regex for initial detection, then AST for detailed analysis.

        Args:
            source: Source code as string
            tree: Parsed AST

        Returns:
            FFTInfo if FFT pattern detected, None otherwise.
        """
        # Quick regex check first - try module-qualified calls
        match = self.FFT_CALL_REGEX.search(source)
        if match is None:
            # Try direct function calls (from-import style)
            match = self.FFT_DIRECT_CALL_REGEX.search(source)
        if match is None:
            return None

        # Extract the matched FFT function name
        fft_func = match.group(1).lower()

        # Look up properties for this FFT variant
        props = self.FFT_PATTERNS.get(fft_func, {})

        # Create base FFTInfo
        info = FFTInfo(
            pattern_name='fft',
            variant=props.get('variant', fft_func),
            dimensions=props.get('dimensions', 1),
            is_inverse=props.get('is_inverse', False),
            is_real_input=props.get('is_real_input', False),
            is_real_output=props.get('is_real_output', False),
            is_convolution=props.get('is_convolution', False),
            confidence=0.85
        )

        # Check for fftshift
        if self.FFT_SHIFT_REGEX.search(source):
            info.has_shift = True

        # Check for fftfreq
        if self.FFT_FREQ_REGEX.search(source):
            info.has_frequency_axis = True

        # AST analysis for axis parameter
        axis_value = self._extract_axis_from_ast(tree, fft_func)
        if axis_value is not None:
            info.axis = axis_value

        # Adjust confidence based on context
        info.confidence = self._calculate_confidence(source, info)

        # Set memory pattern (FFT has specific access patterns)
        info.memory_pattern = 'coalesced' if info.dimensions == 1 else 'strided'

        return info

    def _extract_axis_from_ast(self, tree: ast.AST, target_func: str) -> Optional[int]:
        """
        Extract axis parameter from AST if present.

        Looks for calls like np.fft.fft(x, axis=1).
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if this is an FFT call
                call_name = self._get_call_name(node)
                if call_name and call_name.lower() == target_func:
                    # Look for axis keyword argument
                    for keyword in node.keywords:
                        if keyword.arg == 'axis':
                            if isinstance(keyword.value, ast.Constant):
                                return keyword.value.value
                            elif isinstance(keyword.value, ast.UnaryOp) and \
                                 isinstance(keyword.value.op, ast.USub) and \
                                 isinstance(keyword.value.operand, ast.Constant):
                                # Handle negative axis like axis=-1
                                return -keyword.value.operand.value
        return None

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """Extract the function name from a Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _calculate_confidence(self, source: str, info: FFTInfo) -> float:
        """
        Calculate detection confidence based on context.

        Higher confidence when:
        - Multiple FFT-related functions are used together
        - FFT is used with frequency axis (fftfreq)
        - Standard library usage (numpy, scipy)
        """
        confidence = 0.85

        # Boost for standard library usage
        if any(lib in source.lower() for lib in ['numpy', 'scipy', 'cupy']):
            confidence += 0.05

        # Boost for frequency axis usage (indicates full spectral analysis)
        if info.has_frequency_axis:
            confidence += 0.05

        # Boost for shift usage (indicates proper spectral handling)
        if info.has_shift:
            confidence += 0.03

        # Cap at 0.98
        return min(confidence, 0.98)
