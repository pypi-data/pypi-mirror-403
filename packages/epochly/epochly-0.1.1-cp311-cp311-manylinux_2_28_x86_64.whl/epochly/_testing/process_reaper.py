"""
ProcessReaper - Background daemon for cleaning up orphaned multiprocessing workers.

This module provides continuous cleanup of accumulated processes during test runs,
preventing the process explosion observed when running large test suites.

Problem Solved:
- Forkserver workers accumulate (60+ observed) during test runs
- Workers whose parent died (PPID=1) never get cleaned up
- Resource trackers pile up
- System runs out of resources before session-end cleanup

Solution:
- Background daemon thread runs every N seconds
- Identifies orphaned workers (PPID=1 or epochly-related with dead parent)
- Terminates stale workers gracefully, then force-kills if needed
- Maintains a reasonable process count throughout test execution

Author: Epochly Development Team
Date: November 2025
"""

import os
import sys
import time
import signal
import threading
import logging
from typing import Optional, Set, List, Tuple
from dataclasses import dataclass

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Information about a running process."""
    pid: int
    ppid: int
    command: str
    start_time: Optional[float] = None


class ProcessReaper:
    """
    Background daemon that reaps orphaned multiprocessing workers.

    Targets:
    - multiprocessing.forkserver workers
    - multiprocessing.spawn workers
    - resource_tracker processes
    - ProcessPoolExecutor workers

    Only kills processes that are:
    1. Related to epochly (in command line or cwd)
    2. Orphaned (PPID=1 or parent process dead)
    3. OR idle for too long (configurable threshold)
    """

    # Process patterns to look for
    PATTERNS = [
        'multiprocessing.forkserver',
        'multiprocessing.spawn',
        'multiprocessing.resource_tracker',
    ]

    # Default settings
    DEFAULT_INTERVAL_SECONDS = 30.0  # Check every 30 seconds
    DEFAULT_MAX_IDLE_SECONDS = 120.0  # Kill workers idle for 2 minutes
    DEFAULT_MAX_PROCESSES = 20  # Target max process count

    def __init__(
        self,
        interval: float = DEFAULT_INTERVAL_SECONDS,
        max_idle: float = DEFAULT_MAX_IDLE_SECONDS,
        max_processes: int = DEFAULT_MAX_PROCESSES,
        enabled: bool = True
    ):
        """
        Initialize the ProcessReaper.

        Args:
            interval: Seconds between reaping cycles
            max_idle: Maximum idle time before killing a worker
            max_processes: Target maximum number of worker processes
            enabled: Whether reaper is active (can be disabled via env var)
        """
        self.interval = interval
        self.max_idle = max_idle
        self.max_processes = max_processes
        self.enabled = enabled and os.getenv('EPOCHLY_REAPER_DISABLED', '0') != '1'

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Track when we first saw each process (for idle detection)
        self._first_seen: dict[int, float] = {}

        # Statistics
        self.processes_killed = 0
        self.reap_cycles = 0

    def start(self) -> None:
        """Start the background reaper thread."""
        if not self.enabled:
            logger.debug("ProcessReaper disabled via EPOCHLY_REAPER_DISABLED")
            return

        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return  # Already running

            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._reap_loop,
                name="ProcessReaper",
                daemon=True
            )
            self._thread.start()
            logger.info(f"ProcessReaper started (interval={self.interval}s, max_idle={self.max_idle}s)")

    def stop(self, timeout: float = 5.0) -> None:
        """
        Stop the reaper thread.

        Args:
            timeout: Maximum time to wait for thread to stop
        """
        with self._lock:
            if self._thread is None:
                return

            self._stop_event.set()

            if self._thread.is_alive():
                self._thread.join(timeout=timeout)

            if self._thread.is_alive():
                logger.warning("ProcessReaper thread did not stop cleanly")
            else:
                logger.info(f"ProcessReaper stopped (killed {self.processes_killed} processes in {self.reap_cycles} cycles)")

            self._thread = None

    def _reap_loop(self) -> None:
        """Main reaping loop - runs in background thread."""
        while not self._stop_event.wait(self.interval):
            try:
                self._reap_cycle()
            except Exception as e:
                logger.warning(f"ProcessReaper cycle failed: {e}")

    # Safety limit: refuse to kill too many processes in one cycle
    MAX_KILL_PER_CYCLE = 50

    def _reap_cycle(self, include_all_orphans: bool = False) -> None:
        """
        Execute one reaping cycle.

        Args:
            include_all_orphans: If True, include all multiprocessing orphans (PPID=1)
                                 regardless of whether they have 'epochly' in command.
        """
        self.reap_cycles += 1

        if include_all_orphans:
            logger.info("ProcessReaper: Aggressive mode - including all orphaned multiprocessing processes")

        # Find candidate processes
        candidates = self._find_candidates(include_all_orphans=include_all_orphans)

        if not candidates:
            return

        # Telemetry: track candidate breakdown
        orphan_count = sum(1 for c in candidates if c.ppid == 1)
        epochly_count = sum(1 for c in candidates if 'epochly' in c.command.lower())
        logger.debug(
            f"Reaper cycle {self.reap_cycles}: "
            f"{len(candidates)} candidates "
            f"({orphan_count} orphans, {epochly_count} epochly)"
        )

        # Identify which to kill
        to_kill = self._identify_targets(candidates)

        # Safety: refuse to kill too many processes at once
        if len(to_kill) > self.MAX_KILL_PER_CYCLE:
            logger.error(
                f"ProcessReaper: Refusing to kill {len(to_kill)} processes in one cycle "
                f"(max {self.MAX_KILL_PER_CYCLE}). Possible bug - investigate!"
            )
            return  # Abort this cycle

        if to_kill:
            killed = self._terminate_processes(to_kill)
            self.processes_killed += killed
            if killed > 0:
                logger.info(f"ProcessReaper killed {killed} orphaned workers")

    def _find_candidates(self, include_all_orphans: bool = False) -> List[ProcessInfo]:
        """
        Find all candidate processes that might need reaping.

        Uses psutil for cross-platform compatibility (Windows/Linux/macOS).
        Falls back to Unix 'ps' command if psutil is not available.

        Args:
            include_all_orphans: If True, include multiprocessing processes with PPID=1
                                 even if they don't have 'epochly' in the command.
                                 This is useful for session-start cleanup where any
                                 orphaned multiprocessing process is likely from previous tests.
        """
        if PSUTIL_AVAILABLE:
            return self._find_candidates_psutil(include_all_orphans)
        else:
            return self._find_candidates_ps(include_all_orphans)

    def _find_candidates_psutil(self, include_all_orphans: bool = False) -> List[ProcessInfo]:
        """Find candidates using psutil (cross-platform)."""
        candidates = []
        current_pid = os.getpid()
        parent_pid = os.getppid()

        try:
            for proc in psutil.process_iter(['pid', 'ppid', 'cmdline']):
                try:
                    pid = proc.info['pid']
                    ppid = proc.info['ppid']
                    cmdline = proc.info.get('cmdline')

                    # Skip our own process and its parent
                    if pid == current_pid or pid == parent_pid:
                        continue

                    if not cmdline:
                        continue

                    # Join command line for pattern matching
                    command = ' '.join(cmdline) if isinstance(cmdline, list) else str(cmdline)

                    # Check if it matches our patterns
                    if any(pattern in command for pattern in self.PATTERNS):
                        # Check if we should include this process:
                        # 1. Always include if it has 'epochly' in command (definitely ours)
                        # 2. Include if PPID=1 AND include_all_orphans is True (true orphans)
                        is_epochly = 'epochly' in command.lower()
                        is_true_orphan = ppid == 1 and include_all_orphans

                        if is_epochly or is_true_orphan:
                            candidates.append(ProcessInfo(
                                pid=pid,
                                ppid=ppid,
                                command=command
                            ))

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Process may have exited or we don't have access
                    pass

        except Exception as e:
            logger.debug(f"Failed to find candidates via psutil: {e}")

        return candidates

    def _find_candidates_ps(self, include_all_orphans: bool = False) -> List[ProcessInfo]:
        """Find candidates using Unix 'ps' command (fallback for non-Windows without psutil)."""
        candidates = []

        # Only try ps command on Unix-like systems
        if sys.platform == 'win32':
            logger.debug("ps command not available on Windows, psutil required")
            return []

        try:
            import subprocess

            # Get process list with PID, PPID, and command
            result = subprocess.run(
                ['ps', '-eo', 'pid,ppid,command'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return []

            for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                parts = line.split(None, 2)
                if len(parts) < 3:
                    continue

                try:
                    pid = int(parts[0])
                    ppid = int(parts[1])
                    command = parts[2]
                except (ValueError, IndexError):
                    continue

                # Skip our own process and its parent
                if pid == os.getpid() or pid == os.getppid():
                    continue

                # Check if it matches our patterns
                if any(pattern in command for pattern in self.PATTERNS):
                    # Check if we should include this process:
                    # 1. Always include if it has 'epochly' in command (definitely ours)
                    # 2. Include if PPID=1 AND include_all_orphans is True (true orphans)
                    is_epochly = 'epochly' in command.lower()
                    is_true_orphan = ppid == 1 and include_all_orphans

                    if is_epochly or is_true_orphan:
                        candidates.append(ProcessInfo(
                            pid=pid,
                            ppid=ppid,
                            command=command
                        ))

        except Exception as e:
            logger.debug(f"Failed to find candidates via ps: {e}")

        return candidates

    def _identify_targets(self, candidates: List[ProcessInfo]) -> List[int]:
        """
        Identify which candidate processes should be killed.

        Criteria:
        1. Orphaned (PPID=1 means parent died)
        2. Parent process no longer exists
        3. Idle too long (exceeded max_idle threshold)
        """
        to_kill = []
        current_time = time.monotonic()

        for proc in candidates:
            kill_reason = None

            # Check if orphaned (PPID=1)
            if proc.ppid == 1:
                kill_reason = "orphaned (PPID=1)"

            # Check if parent exists
            elif not self._process_exists(proc.ppid):
                kill_reason = f"parent {proc.ppid} dead"

            # Check idle time
            else:
                # Track when we first saw this process
                if proc.pid not in self._first_seen:
                    self._first_seen[proc.pid] = current_time
                else:
                    idle_time = current_time - self._first_seen[proc.pid]
                    if idle_time > self.max_idle:
                        kill_reason = f"idle {idle_time:.0f}s > {self.max_idle:.0f}s"

            if kill_reason:
                logger.debug(f"Marking PID {proc.pid} for termination: {kill_reason}")
                to_kill.append(proc.pid)

        # Clean up first_seen for processes no longer running
        current_pids = {p.pid for p in candidates}
        self._first_seen = {
            pid: t for pid, t in self._first_seen.items()
            if pid in current_pids
        }

        return to_kill

    def _process_exists(self, pid: int) -> bool:
        """Check if a process exists (cross-platform)."""
        if PSUTIL_AVAILABLE:
            return psutil.pid_exists(pid)
        else:
            try:
                os.kill(pid, 0)  # Signal 0 = check existence
                return True
            except (ProcessLookupError, PermissionError):
                return False
            except OSError:
                return False

    def _terminate_processes(self, pids: List[int]) -> int:
        """
        Terminate processes gracefully, then force if needed.

        Cross-platform: uses psutil on Windows, signals on Unix.

        Returns number of processes successfully killed.
        """
        killed = 0

        # First pass: Graceful termination
        for pid in pids:
            try:
                if PSUTIL_AVAILABLE:
                    # psutil.Process.terminate() is cross-platform
                    proc = psutil.Process(pid)
                    proc.terminate()
                    killed += 1
                elif sys.platform != 'win32':
                    # Unix: use SIGTERM
                    os.kill(pid, signal.SIGTERM)
                    killed += 1
                else:
                    # Windows without psutil - skip graceful termination
                    pass
            except (ProcessLookupError, PermissionError):
                pass  # Already dead or no permission
            except OSError as e:
                logger.debug(f"Failed to terminate {pid}: {e}")
            except Exception as e:
                # Catch psutil exceptions when available
                if PSUTIL_AVAILABLE and isinstance(e, (psutil.NoSuchProcess, psutil.AccessDenied)):
                    pass
                else:
                    raise

        if not killed:
            return 0

        # Brief wait for graceful shutdown
        time.sleep(0.5)

        # Second pass: Force kill for stragglers
        for pid in pids:
            if self._process_exists(pid):
                try:
                    if PSUTIL_AVAILABLE:
                        proc = psutil.Process(pid)
                        proc.kill()  # Cross-platform force kill
                    elif sys.platform != 'win32':
                        os.kill(pid, signal.SIGKILL)
                    # Windows without psutil can't force kill
                except (ProcessLookupError, PermissionError, OSError):
                    pass
                except Exception as e:
                    # Catch psutil exceptions when available
                    if PSUTIL_AVAILABLE and isinstance(e, (psutil.NoSuchProcess, psutil.AccessDenied)):
                        pass
                    else:
                        raise

        return killed

    def reap_now(self, include_all_orphans: bool = False) -> int:
        """
        Trigger an immediate reaping cycle (for use between tests).

        Args:
            include_all_orphans: If True, include all multiprocessing orphans (PPID=1)
                                 regardless of whether they have 'epochly' in command.
                                 Use True for session-start cleanup to catch orphans from
                                 previous test sessions.

        Returns:
            Number of processes killed.
        """
        before = self.processes_killed
        self._reap_cycle(include_all_orphans=include_all_orphans)
        return self.processes_killed - before


# Global singleton instance
_reaper: Optional[ProcessReaper] = None
_reaper_lock = threading.Lock()


def get_reaper() -> ProcessReaper:
    """Get the global ProcessReaper singleton."""
    global _reaper

    if _reaper is None:
        with _reaper_lock:
            if _reaper is None:
                _reaper = ProcessReaper()
    return _reaper


def start_reaper() -> None:
    """Start the global reaper."""
    get_reaper().start()


def stop_reaper() -> None:
    """Stop the global reaper."""
    if _reaper is not None:
        _reaper.stop()


def reap_orphans(include_all_orphans: bool = False) -> int:
    """
    Trigger immediate orphan cleanup.

    Call this between tests or when process count gets high.

    Args:
        include_all_orphans: If True, include all multiprocessing orphans (PPID=1)
                             regardless of whether they have 'epochly' in command.
                             Use True for session-start cleanup to catch orphans from
                             previous test sessions.

    Returns:
        Number of processes killed.
    """
    return get_reaper().reap_now(include_all_orphans=include_all_orphans)
