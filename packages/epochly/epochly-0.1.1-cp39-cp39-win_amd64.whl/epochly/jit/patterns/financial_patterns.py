"""
Financial Pattern Detection

Detects financial computation patterns:
- Black-Scholes option pricing
- Greeks calculations (delta, gamma, theta, vega, rho)
- Monte Carlo simulations
- Normal CDF patterns

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
class BlackScholesInfo(BasePatternInfo):
    """
    Information about a detected Black-Scholes pattern.

    Attributes:
        option_type: Type of option ('call', 'put', 'both', 'unknown')
        has_d1_d2: True if d1/d2 intermediate values are computed
        has_greeks: True if any Greeks are computed
        greeks: List of detected Greeks ('delta', 'gamma', 'theta', 'vega', 'rho')
        uses_erf: True if using math.erf instead of norm.cdf
    """
    option_type: str = 'unknown'
    has_d1_d2: bool = False
    has_greeks: bool = False
    greeks: List[str] = field(default_factory=list)
    uses_erf: bool = False


class BlackScholesDetector(PatternDetector):
    """
    Detects Black-Scholes option pricing patterns.

    Looks for the characteristic d1/d2 calculation pattern and norm.cdf usage.

    Detection priority: 20 (moderately specific)
    """

    # Regex for norm.cdf calls (scipy.stats.norm)
    NORM_CDF_REGEX = re.compile(
        r'\bnorm\.cdf\s*\(',
        re.IGNORECASE
    )

    # Regex for norm.pdf calls (used in Greeks)
    NORM_PDF_REGEX = re.compile(
        r'\bnorm\.pdf\s*\(',
        re.IGNORECASE
    )

    # Regex for d1 calculation pattern
    # d1 = (np.log(S/K) + (r + sigma**2/2)*T) / (sigma * np.sqrt(T))
    D1_PATTERN_REGEX = re.compile(
        r'd1\s*=\s*[^;]*?(?:log|ln)\s*\([^)]*[/]\s*[KX]',
        re.IGNORECASE
    )

    # Regex for d2 = d1 - sigma * sqrt(T) pattern
    D2_PATTERN_REGEX = re.compile(
        r'd2\s*=\s*d1\s*[-]',
        re.IGNORECASE
    )

    # Regex for erf-based CDF implementation
    ERF_CDF_REGEX = re.compile(
        r'(?:math\.)?erf\s*\([^)]*[/]\s*(?:math\.)?sqrt\s*\(\s*2\s*\)',
        re.IGNORECASE
    )

    @property
    def pattern_name(self) -> str:
        return 'black_scholes'

    @property
    def detection_priority(self) -> int:
        return 20

    def detect(self, source: str, tree: ast.AST) -> Optional[BlackScholesInfo]:
        """
        Detect Black-Scholes patterns in source code.

        Args:
            source: Source code as string
            tree: Parsed AST

        Returns:
            BlackScholesInfo if Black-Scholes pattern detected, None otherwise.
        """
        # Check for norm.cdf or erf-based CDF
        has_norm_cdf = self.NORM_CDF_REGEX.search(source) is not None
        has_erf_cdf = self.ERF_CDF_REGEX.search(source) is not None
        # Also check for norm.pdf (used in Greeks calculations)
        has_norm_pdf = self.NORM_PDF_REGEX.search(source) is not None

        # Check for d1/d2 pattern
        has_d1 = self.D1_PATTERN_REGEX.search(source) is not None
        has_d2 = self.D2_PATTERN_REGEX.search(source) is not None
        has_d1_d2 = has_d1 and has_d2

        # Require d1 pattern for a match (core of Black-Scholes)
        if not has_d1:
            return None

        # Need at least one of: norm.cdf, erf, norm.pdf (for Greeks), or d1+d2 pattern
        # d1+d2 pattern with custom CDF is also valid Black-Scholes
        if not (has_norm_cdf or has_erf_cdf or has_norm_pdf or has_d1_d2):
            return None

        # Create info object
        info = BlackScholesInfo(
            pattern_name='black_scholes',
            has_d1_d2=has_d1_d2,
            uses_erf=has_erf_cdf,
            confidence=0.85,
            gpu_suitable=True,
            memory_pattern='coalesced'
        )

        # Determine option type from context
        info.option_type = self._detect_option_type(source)

        # Detect Greeks
        greeks = self._detect_greeks(source)
        if greeks:
            info.has_greeks = True
            info.greeks = greeks

        # Adjust confidence based on pattern completeness
        info.confidence = self._calculate_confidence(has_d1_d2, info.option_type, greeks)

        return info

    def _detect_option_type(self, source: str) -> str:
        """Detect whether this is call, put, or both."""
        source_lower = source.lower()

        # Look for characteristic formulas
        # Call: S * N(d1) - K * exp(-rT) * N(d2)
        # Put: K * exp(-rT) * N(-d2) - S * N(-d1)

        has_call_pattern = bool(re.search(
            r'[sS]\s*\*\s*norm\.cdf\s*\(\s*d1\s*\)',
            source
        )) or bool(re.search(
            r'norm\.cdf\s*\(\s*d1\s*\)\s*[*-]',
            source
        ))

        has_put_pattern = bool(re.search(
            r'norm\.cdf\s*\(\s*-\s*d[12]\s*\)',
            source
        ))

        if has_call_pattern and has_put_pattern:
            return 'both'
        elif has_put_pattern:
            return 'put'
        elif has_call_pattern:
            return 'call'
        else:
            return 'unknown'

    def _detect_greeks(self, source: str) -> List[str]:
        """Detect which Greeks are computed."""
        greeks = []

        # Delta: norm.cdf(d1) for call, norm.cdf(-d1) for put
        # Simple delta is just N(d1), so check for isolated norm.cdf(d1)
        if re.search(r'(?:delta|Delta)\s*=', source):
            greeks.append('delta')
        elif re.search(r'return\s+norm\.cdf\s*\(\s*d1\s*\)', source):
            greeks.append('delta')

        # Gamma: norm.pdf(d1) / (S * sigma * sqrt(T))
        if self.NORM_PDF_REGEX.search(source):
            if re.search(r'norm\.pdf\s*\([^)]*d1[^)]*\)\s*/\s*\([^)]*[sS]\s*\*', source):
                greeks.append('gamma')

        # Vega: S * norm.pdf(d1) * sqrt(T)
        if re.search(r'[sS]\s*\*\s*norm\.pdf\s*\([^)]*\)\s*\*\s*(?:np\.)?sqrt', source):
            greeks.append('vega')

        # Theta: Contains norm.pdf and negative sign and time derivative
        if re.search(r'(?:theta|Theta)\s*=', source, re.IGNORECASE):
            greeks.append('theta')
        elif self.NORM_PDF_REGEX.search(source) and re.search(r'/\s*\([^)]*2\s*\*\s*(?:np\.)?sqrt', source):
            greeks.append('theta')

        # Rho: K * T * exp(-r*T) * N(d2)
        if re.search(r'(?:rho|Rho)\s*=', source, re.IGNORECASE):
            greeks.append('rho')
        elif re.search(r'[KX]\s*\*\s*[tT]\s*\*\s*(?:np\.)?exp', source):
            greeks.append('rho')

        return greeks

    def _calculate_confidence(
        self,
        has_d1_d2: bool,
        option_type: str,
        greeks: List[str]
    ) -> float:
        """Calculate detection confidence based on pattern completeness."""
        confidence = 0.7

        # Boost for complete d1/d2 pattern
        if has_d1_d2:
            confidence += 0.15

        # Boost for known option type
        if option_type != 'unknown':
            confidence += 0.05

        # Boost for Greeks (indicates sophisticated implementation)
        if greeks:
            confidence += min(0.08, len(greeks) * 0.02)

        return min(confidence, 0.98)


@dataclass
class MonteCarloInfo(BasePatternInfo):
    """
    Information about a detected Monte Carlo simulation pattern.

    Attributes:
        has_random_generation: True if random number generation is detected
        simulation_type: Type of simulation ('option_pricing', 'path_simulation',
                        'integration', 'general')
        uses_standard_normal: True if standard normal distribution is used
    """
    has_random_generation: bool = False
    simulation_type: str = 'general'
    uses_standard_normal: bool = False


class MonteCarloDetector(PatternDetector):
    """
    Detects Monte Carlo simulation patterns.

    Looks for random number generation combined with aggregation.

    Detection priority: 55 (moderate - needs context)
    """

    # Regex for random number generation
    RANDOM_REGEX = re.compile(
        r'\b(?:np|numpy)\.random\.'
        r'(standard_normal|randn|uniform|normal|random)\s*\(',
        re.IGNORECASE
    )

    # Regex for standard normal specifically
    STANDARD_NORMAL_REGEX = re.compile(
        r'\b(?:np|numpy)\.random\.(standard_normal|randn)\s*\(',
        re.IGNORECASE
    )

    # Regex for aggregation (mean, sum, average - NOT exp which causes false positives)
    # exp is a transformation, not an aggregation - random + exp is not Monte Carlo
    AGGREGATION_REGEX = re.compile(
        r'\b(?:np|numpy)\.(mean|sum|average)\s*\(',
        re.IGNORECASE
    )

    # Regex for maximum payoff pattern (option pricing)
    PAYOFF_REGEX = re.compile(
        r'\b(?:np|numpy)\.(maximum|fmax)\s*\([^,]+,\s*0',
        re.IGNORECASE
    )

    # Regex for path simulation pattern (paths[:, t] = paths[:, t-1] * ...)
    # This indicates time-stepping MC simulation (GBM, etc.)
    PATH_SIMULATION_REGEX = re.compile(
        r'paths\s*\[\s*:\s*,\s*[tT]\s*\]\s*=\s*paths\s*\[\s*:\s*,\s*[tT]\s*-\s*1\s*\]',
        re.IGNORECASE
    )

    @property
    def pattern_name(self) -> str:
        return 'monte_carlo'

    @property
    def detection_priority(self) -> int:
        return 55

    def detect(self, source: str, tree: ast.AST) -> Optional[MonteCarloInfo]:
        """
        Detect Monte Carlo simulation patterns.

        Args:
            source: Source code as string
            tree: Parsed AST

        Returns:
            MonteCarloInfo if Monte Carlo pattern detected, None otherwise.
        """
        # Check for random number generation
        random_match = self.RANDOM_REGEX.search(source)
        if random_match is None:
            return None

        # Check for aggregation (MC often aggregates results)
        has_aggregation = self.AGGREGATION_REGEX.search(source) is not None

        # Check for path simulation pattern (alternative to aggregation)
        has_path_simulation = self.PATH_SIMULATION_REGEX.search(source) is not None

        # Need at least aggregation or path simulation to qualify as Monte Carlo
        # Without either, this might just be random data generation
        if not (has_aggregation or has_path_simulation):
            return None

        # Create info object
        info = MonteCarloInfo(
            pattern_name='monte_carlo',
            has_random_generation=True,
            uses_standard_normal=self.STANDARD_NORMAL_REGEX.search(source) is not None,
            confidence=0.8,
            gpu_suitable=True,
            memory_pattern='coalesced'
        )

        # Determine simulation type
        info.simulation_type = self._detect_simulation_type(source)

        return info

    def _detect_simulation_type(self, source: str) -> str:
        """Detect the type of Monte Carlo simulation."""
        # Option pricing: has payoff calculation (max(S-K, 0))
        if self.PAYOFF_REGEX.search(source):
            return 'option_pricing'

        # Path simulation: has sequential updates (paths[:, t] = paths[:, t-1] * ...)
        if re.search(r'paths\s*\[\s*:\s*,\s*t\s*\]', source):
            return 'path_simulation'

        # Pi estimation: x**2 + y**2 <= 1
        if re.search(r'\*\*\s*2\s*\+\s*\w+\s*\*\*\s*2\s*<=\s*1', source):
            return 'integration'

        return 'general'
