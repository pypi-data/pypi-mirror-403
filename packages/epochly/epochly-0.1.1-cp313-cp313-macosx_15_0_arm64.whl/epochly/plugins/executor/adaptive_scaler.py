"""
Memory-Aware Adaptive Pool Scaler

Provides intelligent auto-scaling for process pools based on:
- Memory pressure (CRITICAL/WARNING triggers immediate scale-down)
- Queue depth (triggers scale-up)
- Idle timeout (returns to pre_warm baseline)
- User configuration (EPOCHLY_MAX_WORKERS respected as ceiling)
- License limits (business constraints)
- Hardware limits (physical cores)

Architecture:
- Pre-warm workers (default 4) ALWAYS stay warm
- Scale up based on queue depth, capped by ceiling
- Scale down on memory pressure (CRITICAL bypasses cooldown)
- Scale down on idle timeout (respects cooldown)
- 30s cooldown prevents thrashing

Safety guarantees:
- Memory safety is the hard ceiling (can't exceed safe limit)
- User configuration is explicit intent (always respected)
- Never crashes the system (memory pressure triggers scale-down)
- Pre-warm workers never terminated

Author: Epochly Development Team
Created: 2025-11-26
"""

import os
import time
import threading
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple

from .memory_monitor import ProcessPoolMemoryMonitor

logger = logging.getLogger(__name__)


# Import license enforcer lazily to avoid circular imports
def get_license_enforcer():
    """Lazy import of license enforcer."""
    from epochly.licensing.license_enforcer import get_license_enforcer as _get_enforcer
    return _get_enforcer()


@dataclass
class AdaptiveScalerConfig:
    """Configuration for adaptive pool scaling."""

    pre_warm: int = 4                    # Workers to keep warm (never terminate)
    monitor_interval_sec: float = 5.0    # Check memory every N seconds
    idle_timeout_sec: float = 60.0       # Scale down after N seconds idle
    scale_cooldown_sec: float = 30.0     # Minimum time between scale operations
    max_scale_step: int = 8              # Maximum workers to add per scale-up


class AdaptivePoolScaler:
    """
    Memory-aware adaptive scaler for process pools.

    Scales pool size based on:
    - Queue depth (scale up when work is queued)
    - Memory pressure (scale down when memory is constrained)
    - Idle timeout (return to baseline when idle)

    Usage:
        pool = ForkingProcessExecutor(max_workers=4)
        scaler = AdaptivePoolScaler(pool)
        scaler.start()

        # Pool will auto-scale based on workload
        # ...

        scaler.stop()
        pool.shutdown()

    Or as context manager:
        with AdaptivePoolScaler(pool) as scaler:
            # Pool auto-scales
            pass
    """

    def __init__(
        self,
        pool,
        config: Optional[AdaptiveScalerConfig] = None
    ):
        """
        Initialize adaptive scaler.

        Args:
            pool: Pool with resize() method (ForkingProcessExecutor)
            config: Optional configuration
        """
        self._pool = pool
        self._config = config or AdaptiveScalerConfig()
        self._pre_warm = self._config.pre_warm

        # Memory monitor
        self._monitor = ProcessPoolMemoryMonitor()

        # Calculate ceiling from all constraints
        self._ceiling = self._calculate_ceiling()

        # Effective pre_warm (can't exceed ceiling)
        self._effective_pre_warm = min(self._pre_warm, self._ceiling)

        # Scaling state
        self._last_scale_time: Optional[float] = None
        self._last_task_time: float = time.time()
        self._scale_up_count: int = 0
        self._scale_down_count: int = 0

        # Lifecycle state
        self._running: bool = False
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        logger.info(
            f"AdaptivePoolScaler initialized: "
            f"pre_warm={self._effective_pre_warm}, ceiling={self._ceiling}, "
            f"cooldown={self._config.scale_cooldown_sec}s"
        )

    def _calculate_ceiling(self) -> int:
        """
        Calculate hard ceiling from all constraints.

        Returns min(memory_safe, user_config, license_limit, hardware_limit)
        """
        limits = []

        # 1. Memory safety (ALWAYS the hard limit)
        try:
            memory_safe = self._monitor.calculate_safe_worker_count(999)
            limits.append(memory_safe)
        except Exception as e:
            logger.warning(f"Memory safety check failed: {e}")
            limits.append(os.cpu_count() or 4)

        # 2. User configuration (explicit intent)
        user_limit = os.environ.get('EPOCHLY_MAX_WORKERS')
        if user_limit:
            try:
                limits.append(int(user_limit))
            except ValueError:
                logger.warning(f"Invalid EPOCHLY_MAX_WORKERS: {user_limit}")

        # 3. License limit (business constraint)
        try:
            enforcer = get_license_enforcer()
            license_info = enforcer.get_limits()
            max_cores = license_info.get('max_cores')
            if max_cores is not None:
                limits.append(max_cores)
        except Exception as e:
            logger.debug(f"License check failed: {e}, defaulting to community tier (4)")
            limits.append(4)  # Default to community tier

        # 4. Hardware limit (physical cores)
        hardware_limit = os.cpu_count() or 4
        limits.append(hardware_limit)

        # Ceiling is minimum of all limits, but at least 1
        ceiling = max(1, min(limits))

        logger.debug(f"Ceiling calculated: {ceiling} from limits {limits}")
        return ceiling

    def _calculate_scale_step(self, queue_depth: int) -> int:
        """
        Calculate scale-up step based on queue depth.

        Formula: max(2, min(queue_depth // 2, max_scale_step))
        """
        return max(2, min(queue_depth // 2, self._config.max_scale_step))

    def _calculate_scale_up_target(self, queue_depth: int, current_workers: int) -> int:
        """
        Calculate target worker count for scale-up.

        Args:
            queue_depth: Number of queued/pending tasks
            current_workers: Current worker count

        Returns:
            Target worker count (may equal current if at ceiling)
        """
        headroom = self._ceiling - current_workers

        if headroom <= 0:
            return current_workers  # At ceiling

        step = self._calculate_scale_step(queue_depth)
        step = min(step, headroom)  # Don't exceed ceiling

        return current_workers + step

    def _should_scale_up(
        self,
        queue_depth: int,
        current_workers: int
    ) -> Tuple[bool, int]:
        """
        Determine if scale-up should happen.

        Returns:
            (should_scale, target_workers)
        """
        if current_workers >= self._ceiling:
            return False, current_workers

        if queue_depth <= 0:
            return False, current_workers

        if not self._can_scale():
            return False, current_workers

        target = self._calculate_scale_up_target(queue_depth, current_workers)

        if target > current_workers:
            return True, target

        return False, current_workers

    def _calculate_memory_pressure_target(
        self,
        current_workers: int,
        status: str
    ) -> int:
        """
        Calculate target workers based on memory pressure.

        Args:
            current_workers: Current worker count
            status: Memory status (OK, WARNING, CRITICAL)

        Returns:
            Target worker count (never below pre_warm)
        """
        if status == 'CRITICAL':
            # 50% reduction
            target = current_workers // 2
        elif status == 'WARNING':
            # 25% reduction (keep 75%)
            target = int(current_workers * 0.75)
        else:
            return current_workers

        # Never go below pre_warm
        return max(self._effective_pre_warm, target)

    def _calculate_idle_target(self, current_workers: int) -> int:
        """
        Calculate target workers for idle timeout.

        Returns pre_warm (baseline).
        """
        return self._effective_pre_warm

    def _should_scale_down(
        self,
        current_workers: int,
        memory_status: str
    ) -> Tuple[bool, int]:
        """
        Determine if scale-down should happen.

        Memory CRITICAL bypasses cooldown.

        Returns:
            (should_scale, target_workers)
        """
        # Already at minimum
        if current_workers <= self._effective_pre_warm:
            return False, current_workers

        # Memory pressure check (CRITICAL bypasses cooldown because:
        # - System stability is at risk (potential OOM)
        # - Thrashing is preferable to crashing
        # - Scale-down is reversible, crash is not)
        if memory_status == 'CRITICAL':
            target = self._calculate_memory_pressure_target(current_workers, 'CRITICAL')
            if target < current_workers:
                return True, target  # Bypass cooldown for safety

        # Memory WARNING (respects cooldown)
        if memory_status == 'WARNING' and self._can_scale():
            target = self._calculate_memory_pressure_target(current_workers, 'WARNING')
            if target < current_workers:
                return True, target

        # Idle timeout (respects cooldown)
        if self._is_idle() and self._can_scale():
            target = self._calculate_idle_target(current_workers)
            if target < current_workers:
                return True, target

        return False, current_workers

    def _can_scale(self) -> bool:
        """
        Check if scaling is allowed (cooldown passed).

        Returns:
            True if cooldown has passed or no previous scale
        """
        if self._last_scale_time is None:
            return True

        elapsed = time.time() - self._last_scale_time
        return elapsed >= self._config.scale_cooldown_sec

    def _is_idle(self) -> bool:
        """
        Check if pool is idle (no tasks for idle_timeout_sec).

        Returns:
            True if idle timeout exceeded
        """
        elapsed = time.time() - self._last_task_time
        return elapsed >= self._config.idle_timeout_sec

    def _perform_scale(self, target: int) -> None:
        """
        Perform the actual scale operation.

        Args:
            target: Target worker count
        """
        current = self._pool.num_workers

        if target == current:
            return

        try:
            self._pool.resize(target)
            self._last_scale_time = time.time()

            if target > current:
                self._scale_up_count += 1
                logger.info(f"Scaled UP: {current} -> {target} workers")
            else:
                self._scale_down_count += 1
                logger.info(f"Scaled DOWN: {current} -> {target} workers")

        except Exception as e:
            logger.error(f"Scale operation failed: {e}")

    def _get_queue_depth(self) -> int:
        """
        Get current queue depth from pool.

        Returns:
            Number of pending/queued tasks
        """
        # Try common attributes
        if hasattr(self._pool, '_pending_futures'):
            return len(self._pool._pending_futures)
        if hasattr(self._pool, '_task_queue'):
            try:
                return self._pool._task_queue.qsize()
            except Exception as e:
                logger.debug(f"Failed to get queue size: {e}")
        return 0

    def _check_and_scale(self) -> None:
        """
        Check conditions and perform scaling if needed.

        Called periodically by monitor thread.
        """
        with self._lock:
            current_workers = self._pool.num_workers
            queue_depth = self._get_queue_depth()

            # Get memory status
            try:
                memory_metrics = self._monitor.check_memory_usage(self._pool)
                memory_status = memory_metrics.get('status', 'OK')
            except Exception as e:
                logger.debug(f"Memory check failed: {e}")
                memory_status = 'OK'

            # Check scale-down first (safety)
            should_down, down_target = self._should_scale_down(current_workers, memory_status)
            if should_down:
                self._perform_scale(down_target)
                return

            # Check scale-up
            should_up, up_target = self._should_scale_up(queue_depth, current_workers)
            if should_up:
                self._perform_scale(up_target)

    def _monitor_loop(self) -> None:
        """
        Main monitoring loop running in background thread.
        """
        logger.debug("Scaler monitor thread started")

        while not self._stop_event.is_set():
            try:
                self._check_and_scale()
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")

            # Sleep for interval (interruptible)
            self._stop_event.wait(timeout=self._config.monitor_interval_sec)

        logger.debug("Scaler monitor thread stopped")

    def notify_task_submitted(self) -> None:
        """
        Notify scaler that a task was submitted.

        Updates last_task_time for idle detection.
        """
        self._last_task_time = time.time()

    def start(self) -> None:
        """
        Start the adaptive scaler.

        Spawns background monitoring thread.
        """
        if self._running:
            return

        self._running = True
        self._stop_event.clear()

        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="AdaptivePoolScaler-Monitor"
        )
        self._monitor_thread.start()

        logger.info("AdaptivePoolScaler started")

    def stop(self) -> None:
        """
        Stop the adaptive scaler.

        Terminates monitoring thread.
        """
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)

        logger.info("AdaptivePoolScaler stopped")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current scaler statistics.

        Returns:
            Dictionary with stats
        """
        return {
            'current_workers': self._pool.num_workers,
            'ceiling': self._ceiling,
            'pre_warm': self._effective_pre_warm,
            'scale_up_count': self._scale_up_count,
            'scale_down_count': self._scale_down_count,
            'running': self._running,
            'last_scale_time': self._last_scale_time,
            'last_task_time': self._last_task_time,
        }

    def __enter__(self):
        """Context manager entry - start scaler."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop scaler."""
        self.stop()
        return False
