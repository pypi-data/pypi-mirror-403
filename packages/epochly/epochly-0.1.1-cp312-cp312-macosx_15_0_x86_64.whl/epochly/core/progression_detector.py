"""
Detection-Based Level Progression

Implements hybrid detection-based level progression system.
Replaces arbitrary time windows with explicit readiness criteria while
maintaining minimal dampening to prevent oscillation.

Design Goals:
1. Detection-based criteria for each level transition
2. Minimal dampening (default 1s) prevents oscillation without excessive delay
3. Configuration via environment variables and constructor arguments
4. Thread-safe for concurrent access

Architecture Reference:
- progressive_pipeline_architecture.md Section 3.3: EnhancementProgressionManager
- epochly-architecture-spec.md lines 102-130: Progressive enhancement algorithm

Author: Epochly Development Team
Date: December 2025
"""

import os
import sys
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

from ..utils.logger import get_logger

if TYPE_CHECKING:
    from .epochly_core import EnhancementLevel


@dataclass
class ProgressionResult:
    """
    Result of a progression check.

    Contains:
    - can_progress: Whether progression is allowed
    - blocking_criteria: List of criteria that are blocking progression
    - met_criteria: List of criteria that have been met
    """
    can_progress: bool
    blocking_criteria: List[str] = field(default_factory=list)
    met_criteria: List[str] = field(default_factory=list)


class ProgressionDetector:
    """
    Detection-based level progression controller.

    Replaces arbitrary time-based stability windows with explicit
    readiness criteria for each level transition:

    Level 0 -> Level 1 (Threading):
        - Always allowed (threading is always available)

    Level 1 -> Level 2 (JIT):
        - JIT backend available (Numba, PyPy, or Python 3.13+)
        - Dampening period elapsed

    Level 2 -> Level 3 (Sub-interpreters):
        - Sub-interpreter support available (Python 3.12+ or fallback)
        - Sufficient memory for workers
        - Dampening period elapsed

    Level 3 -> Level 4 (GPU):
        - GPU hardware available
        - GPU libraries available (CuPy, etc.)
        - License allows GPU access
        - Dampening period elapsed

    Configuration:
        dampening_seconds: Minimum time at level before progression (default: 1.0s)
        Environment variables:
            EPOCHLY_PROGRESSION_DAMPENING: Override dampening time
            EPOCHLY_FORCE_JIT: Force JIT availability check to True
    """

    # Minimum memory (in GB) required per sub-interpreter worker
    MIN_MEMORY_PER_WORKER_GB = 0.5

    # Minimum total memory (in GB) for Level 3
    MIN_MEMORY_FOR_LEVEL3_GB = 2.0

    def __init__(self, dampening_seconds: Optional[float] = None):
        """
        Initialize progression detector.

        Args:
            dampening_seconds: Minimum time at level before progression.
                              Default is 1.0 seconds, or value from
                              EPOCHLY_PROGRESSION_DAMPENING env var.
        """
        self.logger = get_logger(__name__)

        # Resolve dampening from env var or constructor arg or default
        if dampening_seconds is not None:
            self.dampening_seconds = dampening_seconds
        else:
            env_dampening = os.environ.get('EPOCHLY_PROGRESSION_DAMPENING')
            if env_dampening is not None:
                try:
                    self.dampening_seconds = float(env_dampening)
                except ValueError:
                    self.logger.warning(
                        f"Invalid EPOCHLY_PROGRESSION_DAMPENING value: {env_dampening}, "
                        f"using default 1.0s"
                    )
                    self.dampening_seconds = 1.0
            else:
                self.dampening_seconds = 1.0

        # Track when each level was entered (for dampening calculation)
        self._level_entry_times: Dict[int, float] = {}

        # Thread safety
        self._lock = threading.RLock()

        # Cache detection results to avoid repeated checks
        self._jit_available_cache: Optional[bool] = None
        self._subinterp_available_cache: Optional[bool] = None
        self._memory_check_cache: Optional[bool] = None
        self._cache_timestamp: float = 0.0
        self._cache_ttl_seconds: float = 5.0  # Refresh cache every 5s

    def check_progression_criteria(
        self,
        current_level: 'EnhancementLevel',
        target_level: 'EnhancementLevel'
    ) -> ProgressionResult:
        """
        Check if progression from current to target level is allowed.

        Evaluates all criteria for the specific transition and returns
        a detailed result indicating whether progression is allowed
        and which criteria are blocking or met.

        Args:
            current_level: Current enhancement level
            target_level: Desired target level

        Returns:
            ProgressionResult with can_progress, blocking_criteria, and met_criteria
        """
        with self._lock:
            from .epochly_core import EnhancementLevel

            met_criteria: List[str] = []
            blocking_criteria: List[str] = []

            # Can't progress to same or lower level
            if target_level.value <= current_level.value:
                return ProgressionResult(
                    can_progress=False,
                    blocking_criteria=['invalid_transition'],
                    met_criteria=[]
                )

            # Check dampening for all transitions
            if self._check_dampening(current_level):
                met_criteria.append('dampening')
            else:
                blocking_criteria.append('dampening')

            # Specific criteria for each transition
            if target_level == EnhancementLevel.LEVEL_1_THREADING:
                # L0 -> L1: Threading always available
                if self._is_threading_available():
                    met_criteria.append('threading')
                else:
                    blocking_criteria.append('threading')

            elif target_level == EnhancementLevel.LEVEL_2_JIT:
                # L1 -> L2: JIT backend required
                if self._is_jit_backend_available():
                    met_criteria.append('jit_backend')
                else:
                    blocking_criteria.append('jit_backend')

            elif target_level == EnhancementLevel.LEVEL_3_FULL:
                # L2 -> L3: Sub-interpreters + memory required
                if self._is_subinterpreter_available():
                    met_criteria.append('subinterpreters')
                else:
                    blocking_criteria.append('subinterpreters')

                if self._has_sufficient_memory_for_workers():
                    met_criteria.append('memory')
                else:
                    blocking_criteria.append('memory')

            elif target_level == EnhancementLevel.LEVEL_4_GPU:
                # L3 -> L4: GPU hardware + libraries + license
                if self._is_gpu_available():
                    met_criteria.append('gpu_hardware')
                else:
                    blocking_criteria.append('gpu_hardware')

                if self._is_gpu_licensed():
                    met_criteria.append('gpu_license')
                else:
                    blocking_criteria.append('gpu_license')

            # Can progress only if no blocking criteria
            can_progress = len(blocking_criteria) == 0

            return ProgressionResult(
                can_progress=can_progress,
                blocking_criteria=blocking_criteria,
                met_criteria=met_criteria
            )

    def record_level_entry(self, level: 'EnhancementLevel') -> None:
        """
        Record when a level was entered.

        Used for dampening calculation. Call this whenever
        the enhancement level changes.

        Args:
            level: The level that was just entered
        """
        with self._lock:
            self._level_entry_times[level.value] = time.time()
            self.logger.debug(f"Recorded entry to {level.name}")

    def _check_dampening(self, current_level: 'EnhancementLevel') -> bool:
        """
        Check if dampening period has elapsed for current level.

        If level entry time was never recorded, treats as just entered
        (dampening not satisfied unless dampening_seconds is 0).

        Args:
            current_level: Current enhancement level

        Returns:
            True if dampening period has elapsed, False otherwise
        """
        # Zero dampening = immediate progression allowed
        if self.dampening_seconds <= 0.0:
            return True

        entry_time = self._level_entry_times.get(current_level.value)

        if entry_time is None:
            # Not recorded - treat as just entered (conservative)
            self._level_entry_times[current_level.value] = time.time()
            return False

        elapsed = time.time() - entry_time
        return elapsed >= self.dampening_seconds

    def _is_threading_available(self) -> bool:
        """
        Check if threading is available.

        Threading is always available in CPython.

        Returns:
            True (always)
        """
        return True

    def _is_jit_backend_available(self) -> bool:
        """
        Check if a JIT backend is available.

        Checks for:
        1. EPOCHLY_FORCE_JIT env var override
        2. Numba (most common)
        3. Python 3.13+ native JIT
        4. Pyston-Lite

        Returns:
            True if any JIT backend is available
        """
        # Check for force override
        if os.environ.get('EPOCHLY_FORCE_JIT') == '1':
            return True

        # Check cache
        if self._is_cache_valid() and self._jit_available_cache is not None:
            return self._jit_available_cache

        result = False

        # Check for Numba
        try:
            import numba
            result = True
        except ImportError:
            pass

        if not result:
            # Check for Python 3.13+ experimental JIT
            # NOTE: CPython 3.13 JIT cannot be enabled programmatically.
            # It requires compile-time flag --enable-experimental-jit.
            # We detect if it's enabled, but cannot turn it on.
            if sys.version_info >= (3, 13):
                # Check if experimental JIT is enabled via -X jit or build config
                if hasattr(sys, '_xoptions') and sys._xoptions.get('jit'):
                    result = True
                else:
                    # Also check sysconfig for JIT build flag
                    try:
                        import sysconfig
                        if sysconfig.get_config_vars().get('PY_ENABLE_EXPERIMENTAL_JIT'):
                            result = True
                    except Exception:
                        pass

        if not result:
            # Check for Pyston-Lite (only supports Python 3.7-3.10)
            if sys.version_info[:2] <= (3, 10):
                try:
                    import pyston_lite_autoload
                    result = True
                except ImportError:
                    pass

        # Cache result
        with self._lock:
            self._jit_available_cache = result
            self._update_cache_timestamp()

        return result

    def _is_subinterpreter_available(self) -> bool:
        """
        Check if sub-interpreter support is available.

        Python 3.12+ has _interpreters module for true sub-interpreters.
        Fallback to ProcessPoolExecutor is always available.

        Returns:
            True if sub-interpreters or fallback available
        """
        # Check cache
        if self._is_cache_valid() and self._subinterp_available_cache is not None:
            return self._subinterp_available_cache

        result = False

        # Python 3.12+: Check for sub-interpreters
        if sys.version_info >= (3, 12):
            try:
                import _interpreters
                result = True
            except ImportError:
                pass

        if not result:
            # Fallback: ProcessPoolExecutor always available
            try:
                from concurrent.futures import ProcessPoolExecutor
                result = True
            except ImportError:
                pass

        # Cache result
        with self._lock:
            self._subinterp_available_cache = result
            self._update_cache_timestamp()

        return result

    def _has_sufficient_memory_for_workers(self) -> bool:
        """
        Check if there's sufficient memory for Level 3 workers.

        Uses psutil for accurate memory measurement if available,
        falls back to os.sysconf on POSIX systems.

        Returns:
            True if sufficient memory available
        """
        # Check cache
        if self._is_cache_valid() and self._memory_check_cache is not None:
            return self._memory_check_cache

        result = True  # Optimistic default

        try:
            # Try psutil first (most accurate)
            try:
                import psutil
                mem = psutil.virtual_memory()
                available_gb = mem.available / (1024 ** 3)

                # Need at least MIN_MEMORY_FOR_LEVEL3_GB
                result = available_gb >= self.MIN_MEMORY_FOR_LEVEL3_GB

                if not result:
                    self.logger.debug(
                        f"Insufficient memory for Level 3: {available_gb:.1f}GB < "
                        f"{self.MIN_MEMORY_FOR_LEVEL3_GB}GB required"
                    )

            except ImportError:
                # Fallback to os.sysconf on POSIX
                if hasattr(os, 'sysconf'):
                    try:
                        total_pages = os.sysconf('SC_PHYS_PAGES')
                        page_size = os.sysconf('SC_PAGE_SIZE')
                        total_gb = (total_pages * page_size) / (1024 ** 3)

                        # Assume ~50% available (conservative)
                        available_gb = total_gb * 0.5
                        result = available_gb >= self.MIN_MEMORY_FOR_LEVEL3_GB
                    except (ValueError, OSError):
                        pass  # Keep optimistic default

        except Exception as e:
            self.logger.debug(f"Memory check failed: {e}")
            # Keep optimistic default

        # Cache result
        with self._lock:
            self._memory_check_cache = result
            self._update_cache_timestamp()

        return result

    def _is_gpu_available(self) -> bool:
        """
        Check if GPU hardware is available.

        Returns:
            True if GPU hardware detected
        """
        try:
            from ..gpu.gpu_detector import GPUDetector
            detector = GPUDetector()
            return detector.is_available()
        except ImportError:
            return False
        except Exception as e:
            self.logger.debug(f"GPU detection failed: {e}")
            return False

    def _is_gpu_licensed(self) -> bool:
        """
        Check if GPU is allowed in current license tier.

        Returns:
            True if GPU licensed or license check unavailable
        """
        try:
            from ..licensing.license_enforcer import check_gpu_access
            return check_gpu_access()
        except ImportError:
            # No licensing module - allow
            return True
        except Exception as e:
            self.logger.debug(f"GPU license check failed: {e}")
            return False

    def _is_cache_valid(self) -> bool:
        """Check if detection cache is still valid."""
        return (time.time() - self._cache_timestamp) < self._cache_ttl_seconds

    def _update_cache_timestamp(self) -> None:
        """Update cache timestamp."""
        self._cache_timestamp = time.time()

    def invalidate_cache(self) -> None:
        """Invalidate all detection caches."""
        with self._lock:
            self._jit_available_cache = None
            self._subinterp_available_cache = None
            self._memory_check_cache = None
            self._cache_timestamp = 0.0

    def get_time_at_level(self, level: 'EnhancementLevel') -> float:
        """
        Get time spent at a level.

        Args:
            level: Enhancement level to check

        Returns:
            Time in seconds at this level, or 0 if never entered
        """
        with self._lock:
            entry_time = self._level_entry_times.get(level.value)
            if entry_time is None:
                return 0.0
            return time.time() - entry_time
