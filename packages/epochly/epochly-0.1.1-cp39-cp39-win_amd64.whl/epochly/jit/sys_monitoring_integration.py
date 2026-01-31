"""
sys.monitoring Integration (SPEC2 Task 12)

Uses CPython 3.12+ sys.monitoring API for low-overhead hot-path discovery.

Benefits:
- Native opcode-level instrumentation
- Minimal overhead vs manual instrumentation
- Feeds execution counts into JITManager
- Auto-disables on Python <3.12

Performance:
- Lower overhead than decorator-based instrumentation
- Per-function hotness data
- Informs JIT compilation decisions
"""

import sys
import logging
import threading
import time
from typing import Optional, Callable, Dict


logger = logging.getLogger(__name__)


# Feature flag
_SYS_MONITORING_AVAILABLE = hasattr(sys, 'monitoring') and sys.version_info >= (3, 12)


class SysMonitoringIntegration:
    """
    Integration with CPython 3.12+ sys.monitoring API.

    Automatically disabled on Python <3.12.
    """

    def __init__(self, jit_manager=None):
        """
        Initialize sys.monitoring integration.

        Args:
            jit_manager: JITManager instance to feed hotness data
        """
        self._jit_manager = jit_manager
        self._enabled = False
        self._tool_id = None

        # Execution counters per function
        self._execution_counts: Dict[str, int] = {}

        # Thread safety for enable() (Fix #3 improvement: prevent concurrent enable attempts)
        self._enable_lock = threading.Lock()

        # Rate limiting for failure warnings (Fix #3 improvement: prevent log spam)
        self._last_failure_warning_time = 0.0
        self._failure_warning_cooldown = 60.0  # Warn at most once per minute

        if not _SYS_MONITORING_AVAILABLE:
            logger.debug("sys.monitoring not available (requires Python 3.12+)")
            return

        logger.debug("sys.monitoring available (Python 3.12+)")

    def enable(self, max_retries: int = 3) -> bool:
        """
        Enable sys.monitoring integration with retry logic for race conditions.

        Fix #3 (Dec 2025): sys.monitoring.set_events() can fail with "tool X is not in use"
        during parallel initialization. This adds retry logic with exponential backoff,
        thread safety, and rate-limited warning logs.

        Improvements:
        - Thread-safe: Serializes enable attempts via _enable_lock
        - Rate-limited warnings: Max one warning per minute to prevent log spam

        Args:
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            True if enabled successfully, False otherwise
        """
        if not _SYS_MONITORING_AVAILABLE:
            return False

        # Thread safety: Serialize enable attempts
        with self._enable_lock:
            if self._enabled:
                return True

            last_error = None
            for attempt in range(max_retries):
                try:
                    # Ensure tool ID is registered
                    if self._tool_id is None:
                        # use_tool_id requires (tool_id, name) - both arguments mandatory
                        self._tool_id = sys.monitoring.PROFILER_ID
                        sys.monitoring.use_tool_id(self._tool_id, "epochly_jit_manager")

                    # Register callback for function entry events
                    sys.monitoring.register_callback(
                        self._tool_id,
                        sys.monitoring.events.PY_START,
                        self._on_function_start
                    )

                    # Enable monitoring for function start events
                    sys.monitoring.set_events(
                        self._tool_id,
                        sys.monitoring.events.PY_START
                    )

                    self._enabled = True
                    logger.debug("sys.monitoring enabled for hot-path discovery (Python 3.12+)")
                    return True

                except Exception as e:
                    last_error = e

                    # Enhancement #2 (Dec 2025): Reset stale tool ID on "not in use" error
                    # When tool ID becomes invalid (freed externally or stale), reset and reacquire
                    if "not in use" in str(e).lower():
                        logger.debug(f"Tool {self._tool_id} not in use, resetting for retry")
                        if self._tool_id is not None:
                            try:
                                sys.monitoring.free_tool_id(self._tool_id)
                            except Exception:
                                pass  # Already freed or invalid - ignore
                            self._tool_id = None  # Force reacquisition on next attempt

                    if attempt < max_retries - 1:
                        # Retry with exponential backoff
                        delay = 0.01 * (2 ** attempt)  # 10ms, 20ms, 40ms, ...
                        time.sleep(delay)
                        continue

            # All retries exhausted - log WARNING (not ERROR) with rate limiting
            current_time = time.time()
            if current_time - self._last_failure_warning_time >= self._failure_warning_cooldown:
                logger.warning(f"sys.monitoring enable failed after {max_retries} attempts: {last_error}")
                self._last_failure_warning_time = current_time

            return False

    def disable(self) -> None:
        """Disable sys.monitoring integration."""
        if not self._enabled or not _SYS_MONITORING_AVAILABLE:
            return

        try:
            if self._tool_id is not None:
                sys.monitoring.set_events(self._tool_id, 0)  # Disable all events
                sys.monitoring.free_tool_id(self._tool_id)
                self._tool_id = None

            self._enabled = False
            logger.debug("sys.monitoring disabled")

        except Exception as e:
            logger.error(f"Error disabling sys.monitoring: {e}")

    def _on_function_start(self, code, instruction_offset):
        """
        Callback for function start events.

        Args:
            code: Code object
            instruction_offset: Instruction offset
        """
        try:
            func_name = code.co_name

            # Increment execution count
            self._execution_counts[func_name] = self._execution_counts.get(func_name, 0) + 1

            # Feed to JIT manager if available
            if self._jit_manager and hasattr(self._jit_manager, 'record_execution'):
                self._jit_manager.record_execution(func_name, code)

        except Exception as e:
            logger.debug(f"Error in monitoring callback: {e}")

    def get_hot_functions(self, min_count: int = 100) -> Dict[str, int]:
        """
        Get hot functions based on execution counts.

        Args:
            min_count: Minimum execution count to be considered hot

        Returns:
            Dictionary of {function_name: execution_count}
        """
        return {
            name: count
            for name, count in self._execution_counts.items()
            if count >= min_count
        }

    def is_available(self) -> bool:
        """Check if sys.monitoring is available."""
        return _SYS_MONITORING_AVAILABLE

    def is_enabled(self) -> bool:
        """Check if currently enabled."""
        return self._enabled

    def get_stats(self) -> dict:
        """Get monitoring statistics."""
        return {
            'available': _SYS_MONITORING_AVAILABLE,
            'enabled': self._enabled,
            'functions_tracked': len(self._execution_counts),
            'total_executions': sum(self._execution_counts.values())
        }
