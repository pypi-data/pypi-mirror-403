"""
Enhancement Progression Manager

Manages progressive enhancement level upgrades with validation.
Ensures stability and performance improvements before level transitions.

Architecture Reference:
- progressive_pipeline_architecture.md Section 3.3: EnhancementProgressionManager
- epochly-architecture-spec.md lines 102-130: Progressive enhancement algorithm

Author: Epochly Development Team
Date: November 13, 2025
"""

import time
import threading
import sys
from typing import Dict, Optional, TYPE_CHECKING
from collections import defaultdict, deque
from enum import Enum

from ..utils.logger import get_logger

if TYPE_CHECKING:
    from ..monitoring.level_health_snapshot import LevelHealthSnapshot
    from .progression_detector import ProgressionDetector


class EnhancementProgressionManager:
    """
    Manages progression through enhancement levels with validation.

    Responsibilities:
    - Track time at each level
    - Monitor stability (error count, crash detection)
    - Validate performance improvements
    - Coordinate level upgrades
    - Handle rollbacks on failure

    Validation Criteria for Level Upgrade:
    1. Stability: 30s minimum at current level with zero errors
    2. Performance: >5% improvement over baseline
    3. Compatibility: Next level compatible with environment
    4. Resources: Sufficient memory/CPU available
    5. License: Feature allowed in current license tier
    """

    def __init__(self, core: 'EpochlyCore'):
        """
        Initialize enhancement progression manager.

        Args:
            core: EpochlyCore instance to manage
        """
        self.core = core
        self.logger = get_logger(__name__)

        # Track when each level was first entered
        self.level_start_time: Dict[int, float] = {}

        # Track error counts per level
        self.level_error_counts = defaultdict(int)

        # Baseline performance for comparison
        self.baseline_performance: Optional[float] = None

        # Thread safety
        self.lock = threading.RLock()

        # Performance improvement threshold (5%)
        self.min_improvement_factor = 1.05

        # Minimum time at level before upgrade (1 second)
        # Reduced from 5s (originally 30s) because:
        # 1. Same-level transition guard prevents oscillation (Dec 2025 fix)
        # 2. Event-based init_complete signals actual readiness
        # 3. Rollback mechanism handles any issues if upgrade fails
        # The stability wait is now just a sanity check, not a critical safeguard
        self.min_stability_duration = 1.0

        # Snapshot windows for automatic rollback (maxlen=100 per level)
        from .epochly_core import EnhancementLevel
        self._snapshot_window: Dict[int, deque] = {
            level.value: deque(maxlen=100)
            for level in EnhancementLevel
        }

        # Rollback state
        self._rollback_scheduled = False
        self._previous_stable_level: Optional['EnhancementLevel'] = None

        # Rollback thresholds
        self._rollback_threshold_throughput = 1.0  # Must maintain baseline
        self._rollback_threshold_errors = 2  # Max 2 errors in window
        self._rollback_window_seconds = 10.0  # Error burst detection window

        # P1-1: Package deny/allow lists for stability gates
        self.package_denylist: set = set()
        self.package_allowlist: set = set()

        # P1-1: Package error tracking for auto-denylist
        self._package_error_counts: Dict[str, int] = defaultdict(int)
        self.package_error_threshold = 3  # Errors before auto-denylist

        # Detection-based progression (hybrid mode)
        # When enabled, uses ProgressionDetector for criteria-based progression
        # instead of purely time-based stability windows
        self._use_detection_based_progression = False
        self._progression_detector: Optional['ProgressionDetector'] = None

    @property
    def use_detection_based_progression(self) -> bool:
        """Check if detection-based progression is enabled."""
        return self._use_detection_based_progression

    @use_detection_based_progression.setter
    def use_detection_based_progression(self, value: bool) -> None:
        """
        Enable or disable detection-based progression.

        When enabled, progression checks use ProgressionDetector
        for criteria-based decisions instead of time-based stability.
        """
        self._use_detection_based_progression = value
        if value and self._progression_detector is None:
            # Lazy-initialize detector
            from .progression_detector import ProgressionDetector
            self._progression_detector = ProgressionDetector()

    @property
    def progression_detector(self) -> Optional['ProgressionDetector']:
        """Get the progression detector instance."""
        return self._progression_detector

    @progression_detector.setter
    def progression_detector(self, detector: 'ProgressionDetector') -> None:
        """Set a custom progression detector instance."""
        self._progression_detector = detector

    def can_progress_to(self, current_level: 'EnhancementLevel', target_level: 'EnhancementLevel') -> bool:
        """
        Check if progression from current to target level is allowed.

        Args:
            current_level: Current enhancement level (for compatibility)
            target_level: Desired target level

        Returns:
            bool: True if progression is allowed

        Note: This is an alias/wrapper for can_upgrade_to_level for backward compatibility.
              Called from epochly_core.py:1063, 1101, 1139, 1328

        When use_detection_based_progression is True, delegates to
        ProgressionDetector for criteria-based checks instead of
        time-based stability windows.
        """
        # Use detection-based progression if enabled
        if self._use_detection_based_progression and self._progression_detector is not None:
            result = self._progression_detector.check_progression_criteria(
                current_level, target_level
            )
            return result.can_progress

        # Fall back to time-based progression
        return self.can_upgrade_to_level(target_level)

    def can_upgrade_to_level(self, target_level: 'EnhancementLevel') -> bool:
        """
        Check if safe to upgrade to target enhancement level.

        Validates:
        1. Stability at current level (time + error count)
        2. Performance improvement over baseline
        3. Compatibility with target level
        4. Resource availability
        5. License permissions

        Args:
            target_level: Target enhancement level

        Returns:
            True if all validation criteria met, False otherwise
        """
        with self.lock:
            current_level = self.core.current_level

            # DIAGNOSTIC: Log entry with all relevant state
            self.logger.debug(
                f"can_upgrade_to_level({target_level.name}): "
                f"current={current_level.name}, "
                f"level_start_time={dict(self.level_start_time)}, "
                f"error_counts={dict(self.level_error_counts)}"
            )

            # 0. CRITICAL FIX (Dec 2025): Reject same-level or downgrade transitions
            # Root Cause Analysis: The Level 3 regression was caused by JIT detection
            # thread calling can_progress_to(LEVEL_2, LEVEL_2) which passed without this
            # guard, causing level_start_time[2] to be reset and blocking Level 3 forever.
            # This mirrors the guard in ProgressionDetector.check_progression_criteria().
            if target_level.value <= current_level.value:
                self.logger.debug(
                    f"CHECK 0 FAILED: Invalid transition rejected: {current_level.name} -> {target_level.name} "
                    f"(must be upgrade to higher level)"
                )
                return False
            self.logger.debug(f"CHECK 0 PASSED: {current_level.name} -> {target_level.name} is valid upgrade")

            # 1. Stability Validation: Check time at current level
            time_at_current = self._get_time_at_current_level(current_level)

            if time_at_current < self.min_stability_duration:
                self.logger.debug(
                    f"CHECK 1 FAILED: Stability check failed: {time_at_current:.1f}s < "
                    f"{self.min_stability_duration}s required"
                )
                return False
            self.logger.debug(f"CHECK 1 PASSED: time_at_current={time_at_current:.1f}s >= {self.min_stability_duration}s")

            # 2. Stability Validation: Check error count
            error_count = self.level_error_counts[current_level.value]
            if error_count > 0:
                self.logger.debug(
                    f"CHECK 2 FAILED: Stability check failed: {error_count} "
                    f"errors at {current_level.name}"
                )
                return False
            self.logger.debug(f"CHECK 2 PASSED: error_count={error_count} at {current_level.name}")

            # 3. Performance Validation
            perf_valid = self._validates_performance_improvement()
            if not perf_valid:
                self.logger.debug("CHECK 3 FAILED: Performance improvement check failed")
                return False
            self.logger.debug(f"CHECK 3 PASSED: performance validation OK")

            # 4. Compatibility Validation
            compat_valid = self._check_level_compatibility(target_level)
            if not compat_valid:
                self.logger.debug(f"CHECK 4 FAILED: Compatibility check failed for {target_level.name}")
                return False
            self.logger.debug(f"CHECK 4 PASSED: {target_level.name} is compatible")

            # 5. Resource Validation (future enhancement)
            # if not self._has_sufficient_resources(target_level):
            #     return False

            # 6. License Validation (future enhancement)
            # if not self._license_allows_level(target_level):
            #     return False

            self.logger.debug(f"ALL CHECKS PASSED: can upgrade to {target_level.name}")
            return True

    def upgrade_to_level(self, target_level: 'EnhancementLevel'):
        """
        Upgrade to target enhancement level with proper state management.

        This method:
        1. Calls core's set_enhancement_level (handles initialization)
        2. Records level start time
        3. Resets error count for new level
        4. Logs success or handles failure

        Args:
            target_level: Target enhancement level

        Raises:
            Exception: If upgrade fails (caller should handle)
        """
        with self.lock:
            try:
                # Call core's set_enhancement_level (handles initialization)
                self.core.set_enhancement_level(target_level)

                # Record when we entered this level
                self.level_start_time[target_level.value] = time.time()

                # Reset error count for new level
                self.level_error_counts[target_level.value] = 0

                self.logger.debug(f"Successfully upgraded to {target_level.name}")

            except Exception as e:
                # Track error for this level
                self.level_error_counts[target_level.value] += 1

                self.logger.error(
                    f"Failed to upgrade to {target_level.name}: {e}. "
                    f"Error count: {self.level_error_counts[target_level.value]}"
                )

                # Re-raise for caller to handle
                raise

    def record_error_at_current_level(self):
        """
        Record an error at the current enhancement level.

        Used by background detection or other components to report
        instability at current level.
        """
        with self.lock:
            current_level = self.core.current_level
            self.level_error_counts[current_level.value] += 1

            self.logger.warning(
                f"Error recorded at {current_level.name}. "
                f"Total errors: {self.level_error_counts[current_level.value]}"
            )

    def _get_time_at_current_level(self, level: 'EnhancementLevel') -> float:
        """
        Get time spent at current enhancement level.

        Args:
            level: Enhancement level to check

        Returns:
            Time in seconds at this level, or 0 if never entered
        """
        start_time = self.level_start_time.get(level.value)

        if start_time is None:
            return 0.0

        return time.time() - start_time

    def _validates_performance_improvement(self) -> bool:
        """
        Validate performance improvement over baseline.

        Checks if current performance is at least 5% better than baseline.
        Uses baseline from performance monitor, not local cache.

        Returns:
            True if performance improved >=5%, False otherwise
        """
        try:
            if not hasattr(self.core, 'performance_monitor'):
                return True  # No monitor, assume valid

            if self.core.performance_monitor is None:
                return True  # No monitor, assume valid

            # Get current and baseline performance from monitor
            current_perf = self.core.performance_monitor.get_current_performance()
            baseline_perf = self.core.performance_monitor.get_baseline_performance()

            # Store baseline for reference (but don't use it for validation)
            if self.baseline_performance is None:
                self.baseline_performance = baseline_perf

            # Calculate improvement
            if baseline_perf <= 0:
                return True  # Avoid division by zero

            improvement_factor = current_perf / baseline_perf

            # Check if improvement meets threshold (5%)
            meets_threshold = improvement_factor >= self.min_improvement_factor

            if not meets_threshold:
                self.logger.debug(
                    f"Performance improvement {improvement_factor:.2f}x < "
                    f"{self.min_improvement_factor:.2f}x required"
                )

            return meets_threshold

        except Exception as e:
            self.logger.debug(f"Performance validation error: {e}")
            return True  # Assume valid on error (graceful degradation)

    def _check_level_compatibility(self, target_level: 'EnhancementLevel') -> bool:
        """
        Check if target enhancement level is compatible with environment.

        Validates:
        - Python version requirements
        - Platform compatibility
        - Required modules availability
        - Hardware requirements (for GPU level)

        Args:
            target_level: Target enhancement level

        Returns:
            True if compatible, False otherwise
        """
        try:
            # Import EnhancementLevel enum for comparison
            from .epochly_core import EnhancementLevel

            # Level 0 and 1 are always compatible
            if target_level.value <= EnhancementLevel.LEVEL_1_THREADING.value:
                return True

            # Level 2 (JIT): Check if JIT support available
            if target_level == EnhancementLevel.LEVEL_2_JIT:
                return self._check_jit_compatibility()

            # Level 3 (Full): Check Python 3.12+ for sub-interpreters
            if target_level == EnhancementLevel.LEVEL_3_FULL:
                return self._check_level3_compatibility()

            # Level 4 (GPU): Check GPU hardware availability
            if target_level == EnhancementLevel.LEVEL_4_GPU:
                return self._check_gpu_compatibility()

            # Unknown level - be conservative
            return False

        except Exception as e:
            self.logger.debug(f"Compatibility check error: {e}")
            return False  # Conservative on error

    def _check_jit_compatibility(self) -> bool:
        """
        Check if JIT compilation is available.

        Returns:
            True if JIT available (Numba, PyPy, or Python 3.13+)
        """
        try:
            # Check for Numba
            try:
                import numba
                return True
            except ImportError:
                pass

            # Check for Python 3.13+ experimental JIT
            # NOTE: CPython 3.13 JIT cannot be enabled programmatically.
            # It requires compile-time flag --enable-experimental-jit.
            # We detect if it's enabled, but cannot turn it on.
            if sys.version_info >= (3, 13):
                # Check if experimental JIT is enabled via -X jit or build config
                if hasattr(sys, '_xoptions') and sys._xoptions.get('jit'):
                    return True
                # Also check sysconfig for JIT build flag
                try:
                    import sysconfig
                    if sysconfig.get_config_vars().get('PY_ENABLE_EXPERIMENTAL_JIT'):
                        return True
                except Exception:
                    pass

            # Check for Pyston-Lite (only supports Python 3.7-3.10)
            if sys.version_info[:2] <= (3, 10):
                try:
                    import pyston_lite_autoload
                    return True
                except ImportError:
                    pass

            return False

        except Exception:
            return False

    def _check_level3_compatibility(self) -> bool:
        """
        Check if Level 3 (multicore execution) is compatible.

        Level 3 provides multicore speedups via:
        - Python 3.12+: Sub-interpreters with per-interpreter GIL
        - Python <3.12: Process/thread pool fallback

        Both modes are valid Level 3 and provide multicore benefits.

        Returns:
            True if Level 3 compatible (sub-interpreters OR fallback available)
        """
        try:
            # Python 3.12+: Check for sub-interpreter support
            if sys.version_info >= (3, 12):
                try:
                    import _interpreters
                    self.logger.debug("Level 3 compatible: sub-interpreters available")
                    return True
                except ImportError:
                    self.logger.debug("_interpreters module not available, checking fallback")
                    # Fall through to fallback check

            # Python <3.12 or sub-interpreters unavailable: Check for fallback support
            # Level 3 fallback uses ProcessPoolExecutor or ThreadExecutor
            try:
                from concurrent.futures import ProcessPoolExecutor
                self.logger.debug("Level 3 compatible: ProcessPoolExecutor fallback available")
                return True
            except ImportError:
                try:
                    from concurrent.futures import ThreadPoolExecutor
                    self.logger.debug("Level 3 compatible: ThreadPoolExecutor fallback available")
                    return True
                except ImportError:
                    self.logger.debug("Level 3 incompatible: no fallback executors available")
                    return False

        except Exception as e:
            self.logger.debug(f"Level 3 compatibility check failed: {e}")
            return False

    def _check_gpu_compatibility(self) -> bool:
        """
        Check if GPU acceleration is available.

        Checks for:
        - GPU hardware presence (via detector)
        - CuPy or other GPU libraries
        - License permission for GPU (CACHED for performance)

        Returns:
            True if GPU compatible
        """
        try:
            # PERFORMANCE FIX (perf_review.md v2 Section 6): Cache license check
            # Background detection calls this every ~10 seconds, redundant license overhead
            try:
                from ..licensing.license_cache import get_license_cache
                from ..licensing.license_enforcer import check_gpu_access as _check_gpu_access_impl

                # Use cached license check (5-minute TTL)
                license_cache = get_license_cache()
                gpu_licensed = license_cache.get_or_check('gpu_access', _check_gpu_access_impl)

                if not gpu_licensed:
                    # GPU license bypass via cryptographically signed dev tokens ONLY
                    # SECURITY: Env var bypass (EPOCHLY_DISABLE_LICENSE_ENFORCEMENT,
                    #           EPOCHLY_GPU_TEST_OVERRIDE) removed
                    # Dev tokens require:
                    # 1. Valid ED25519 signature from api.epochly.com
                    # 2. EPOCHLY_TEST_MODE=1 set (prevents production misuse)
                    # 3. Token not expired or revoked
                    dev_token_bypass = False
                    try:
                        from ..licensing.dev_token_validator import is_dev_bypass_active
                        dev_token_bypass = is_dev_bypass_active()
                    except ImportError:
                        pass  # Dev token module not available

                    if not dev_token_bypass:
                        self.logger.debug("GPU not available in current license tier")
                        return False
                    self.logger.debug("GPU license bypassed via valid dev token")
            except ImportError:
                # No licensing module - allow GPU check
                pass

            # Check for GPU hardware
            try:
                from ..gpu.gpu_detector import GPUDetector
                detector = GPUDetector()
                return detector.is_available()
            except ImportError:
                self.logger.debug("GPU detector not available")
                return False

        except Exception as e:
            self.logger.debug(f"GPU compatibility check failed: {e}")
            return False

    def on_snapshot(self, snapshot: 'LevelHealthSnapshot'):
        """
        Process incoming health snapshot from PerformanceMonitor.

        Stores snapshot in rolling window and evaluates rollback conditions.
        Triggers automatic rollback when metrics degrade below thresholds.

        Args:
            snapshot: Health snapshot from PerformanceMonitor

        Rollback Conditions:
        - Throughput ratio < 1.0 (below baseline)
        - Error rate > 0.01 (>1% error rate)
        - Allocator on fallback path
        - >2 errors in last 10 seconds (error burst)
        """
        with self.lock:
            # Store in window (per-level deque with maxlen=100)
            level_key = snapshot.level.value
            self._snapshot_window[level_key].append(snapshot)

            # Check if rollback needed
            if self._should_rollback(snapshot):
                self.logger.warning(
                    f"Health degradation detected at {snapshot.level.name}: "
                    f"throughput={snapshot.throughput_ratio:.2f}, "
                    f"error_rate={snapshot.error_rate:.3f}, "
                    f"allocator_fast={snapshot.allocator_fast_path}"
                )
                self._schedule_rollback()

    def _should_rollback(self, snapshot: 'LevelHealthSnapshot') -> bool:
        """
        Evaluate if rollback is needed based on snapshot.

        Rollback conditions:
        1. Throughput ratio < 1.0 (below baseline)
        2. Error rate > 0.01 (>1% error rate)
        3. Allocator on fallback path (critical for performance)
        4. >2 errors in last 10 seconds (error burst)

        Args:
            snapshot: Current health snapshot

        Returns:
            True if rollback should be scheduled, False otherwise
        """
        # Already scheduled - don't re-evaluate (prevent reentrancy)
        if self._rollback_scheduled:
            return False

        # Check throughput regression
        if snapshot.throughput_ratio < self._rollback_threshold_throughput:
            self.logger.warning(
                f"Throughput regression: {snapshot.throughput_ratio:.2f} < "
                f"{self._rollback_threshold_throughput:.2f}"
            )
            return True

        # Check high error rate
        if snapshot.error_rate > 0.01:  # >1% error rate
            self.logger.warning(f"High error rate: {snapshot.error_rate:.3f} > 0.01")
            return True

        # Check allocator fallback (critical for performance)
        if not snapshot.allocator_fast_path:
            self.logger.warning("Allocator on fallback path - triggering rollback")
            return True

        # Check error burst in recent window
        window = self._snapshot_window[snapshot.level.value]
        if len(window) >= 3:
            # Filter to snapshots within window (last 10 seconds)
            recent = [
                s for s in window
                if snapshot.timestamp - s.timestamp <= self._rollback_window_seconds
            ]
            # Count snapshots with errors
            error_count = sum(1 for s in recent if s.error_rate > 0)
            if error_count > self._rollback_threshold_errors:
                self.logger.warning(
                    f"Error burst detected: {error_count} errors in last "
                    f"{self._rollback_window_seconds}s"
                )
                return True

        return False

    def _schedule_rollback(self):
        """
        Schedule rollback to previous stable level.

        Executes rollback in background thread to avoid blocking monitoring.
        Prevents multiple concurrent rollbacks with _rollback_scheduled flag.
        """
        if self._rollback_scheduled:
            return  # Already scheduled

        self._rollback_scheduled = True

        # Execute rollback in background thread (non-blocking)
        threading.Thread(
            target=self._execute_rollback,
            name="Epochly-Rollback",
            daemon=True
        ).start()

    def _execute_rollback(self):
        """
        Execute rollback to previous stable level.

        Called in background thread by _schedule_rollback() or directly for testing.
        Downgrades to one level below current level, resets error counts,
        and clears rollback flag.
        """
        with self.lock:
            current_level = self.core.current_level

            # Determine target level (one level down or use _previous_stable_level)
            if self._previous_stable_level is not None:
                # Use explicitly set target if available
                target_level = self._previous_stable_level
            else:
                # Calculate one level down
                target_level = self._get_rollback_target(current_level)

            if target_level is None:
                self.logger.error("Cannot rollback - no previous level available")
                self._rollback_scheduled = False
                return

            try:
                self.logger.warning(
                    f"Executing rollback from {current_level.name} to {target_level.name}"
                )

                # Execute rollback via core
                # Use force=True to bypass progression checks - rollback is an
                # emergency mechanism that must succeed even when normal progression
                # would be blocked (e.g., by the invalid_transition guard).
                self.core.set_enhancement_level(target_level, force=True)

                # Record as stable level
                self._previous_stable_level = target_level

                # Reset error count for rollback target
                self.level_error_counts[target_level.value] = 0

                self.logger.debug(f"Rollback complete: now at {target_level.name}")

            except Exception as e:
                self.logger.error(f"Rollback failed: {e}", exc_info=True)

            finally:
                # Clear rollback flag (safe even if not set)
                self._rollback_scheduled = False

    def _get_rollback_target(self, current_level: 'EnhancementLevel') -> Optional['EnhancementLevel']:
        """
        Get target level for rollback (one level down from current).

        Args:
            current_level: Current enhancement level

        Returns:
            Target level (one down), or None if already at lowest level
        """
        from .epochly_core import EnhancementLevel

        # Define level ordering (ascending)
        level_order = [
            EnhancementLevel.LEVEL_0_MONITOR,
            EnhancementLevel.LEVEL_1_THREADING,
            EnhancementLevel.LEVEL_2_JIT,
            EnhancementLevel.LEVEL_3_FULL,
            EnhancementLevel.LEVEL_4_GPU
        ]

        try:
            current_idx = level_order.index(current_level)
            if current_idx > 0:
                # Return one level down
                return level_order[current_idx - 1]
        except ValueError:
            self.logger.error(f"Unknown level: {current_level}")

        # Can't go below LEVEL_0
        return None

    # =========================================================================
    # P1-1: Stability Gates - Metrics and Package Management
    # =========================================================================

    def get_stability_metrics(self) -> Dict[str, any]:
        """
        Get current stability metrics for the enhancement progression.

        P1-1 Acceptance Criteria: Stability metrics visible in get_status()

        Returns:
            Dictionary containing:
            - current_level: Current enhancement level name
            - time_at_level_seconds: Seconds spent at current level
            - error_count: Number of errors at current level
            - is_stable: Whether current level is considered stable
            - denied_packages: List of packages in denylist
            - min_stability_duration: Required seconds for stability
            - rollback_scheduled: Whether a rollback is pending
        """
        with self.lock:
            current_level = self.core.current_level
            time_at_level = self._get_time_at_current_level(current_level)
            error_count = self.level_error_counts[current_level.value]

            # Level is stable if: time >= min_stability_duration AND error_count == 0
            is_stable = (
                time_at_level >= self.min_stability_duration and
                error_count == 0
            )

            return {
                'current_level': current_level.name,
                'time_at_level_seconds': time_at_level,
                'error_count': error_count,
                'is_stable': is_stable,
                'denied_packages': list(self.package_denylist),
                'allowed_packages': list(self.package_allowlist),
                'min_stability_duration': self.min_stability_duration,
                'rollback_scheduled': self._rollback_scheduled,
                'package_error_threshold': self.package_error_threshold,
            }

    def add_to_denylist(self, package_name: str) -> None:
        """
        Add a package to the denylist.

        Packages in the denylist will trigger fallback to safer levels
        when detected in the execution path.

        Args:
            package_name: Name of the package to deny
        """
        with self.lock:
            self.package_denylist.add(package_name)
            self.logger.debug(f"Package '{package_name}' added to denylist")

    def remove_from_denylist(self, package_name: str) -> None:
        """
        Remove a package from the denylist.

        Args:
            package_name: Name of the package to remove
        """
        with self.lock:
            self.package_denylist.discard(package_name)
            self.logger.debug(f"Package '{package_name}' removed from denylist")

    def add_to_allowlist(self, package_name: str) -> None:
        """
        Add a package to the allowlist.

        Packages in the allowlist are explicitly permitted even if
        they might otherwise be flagged.

        Args:
            package_name: Name of the package to allow
        """
        with self.lock:
            self.package_allowlist.add(package_name)
            self.logger.debug(f"Package '{package_name}' added to allowlist")

    def is_package_denied(self, package_name: str) -> bool:
        """
        Check if a package is in the denylist.

        Args:
            package_name: Name of the package to check

        Returns:
            True if package is denied, False otherwise
        """
        with self.lock:
            # Allowlist takes precedence
            if package_name in self.package_allowlist:
                return False
            return package_name in self.package_denylist

    def is_package_allowed(self, package_name: str) -> bool:
        """
        Check if a package is explicitly allowed.

        Args:
            package_name: Name of the package to check

        Returns:
            True if package is in allowlist, False otherwise
        """
        with self.lock:
            return package_name in self.package_allowlist

    def report_package_error(self, package_name: str, error_message: str) -> None:
        """
        Report an error associated with a specific package.

        If a package exceeds the error threshold, it will be automatically
        added to the denylist to prevent future issues.

        P1-1 Acceptance Criteria: Known-problematic packages trigger fallback

        Args:
            package_name: Name of the package that caused the error
            error_message: Description of the error
        """
        with self.lock:
            # Skip if package is in allowlist
            if package_name in self.package_allowlist:
                self.logger.debug(
                    f"Package '{package_name}' error ignored (in allowlist): {error_message}"
                )
                return

            # Increment error count
            self._package_error_counts[package_name] += 1
            error_count = self._package_error_counts[package_name]

            self.logger.warning(
                f"Package '{package_name}' error ({error_count}/{self.package_error_threshold}): "
                f"{error_message}"
            )

            # Check if threshold exceeded
            if error_count >= self.package_error_threshold:
                self.add_to_denylist(package_name)
                self.logger.warning(
                    f"Package '{package_name}' auto-added to denylist after "
                    f"{error_count} errors"
                )

                # Record error at current level (may trigger rollback)
                self.record_error_at_current_level()

    def get_package_error_count(self, package_name: str) -> int:
        """
        Get the current error count for a package.

        Args:
            package_name: Name of the package

        Returns:
            Number of errors recorded for this package
        """
        with self.lock:
            return self._package_error_counts.get(package_name, 0)

    def clear_package_errors(self, package_name: str) -> None:
        """
        Clear error count for a package.

        Useful when a package issue has been resolved.

        Args:
            package_name: Name of the package to clear errors for
        """
        with self.lock:
            if package_name in self._package_error_counts:
                del self._package_error_counts[package_name]
                self.logger.debug(f"Error count cleared for package '{package_name}'")
