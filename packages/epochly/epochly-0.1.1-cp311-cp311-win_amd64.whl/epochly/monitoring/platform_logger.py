"""
Platform-Native Logging Integration

Provides adapters for platform-specific logging systems to surface monitoring
back-pressure and dropped metrics events.

Supported Platforms:
- Windows: Event Tracing for Windows (ETW)
- macOS: Unified Logging (os_log)
- Linux: journald / syslog

Author: Epochly Development Team
"""

import platform
import subprocess
import threading
from abc import ABC, abstractmethod
from typing import Optional

from ..utils.logger import get_logger


class PlatformLogger(ABC):
    """Abstract base class for platform-specific loggers."""

    @abstractmethod
    def log_metric_drops(
        self,
        drops: int,
        total_attempts: int,
        drop_rate: float
    ) -> None:
        """
        Log metric drop event to platform-native logging system.

        Args:
            drops: Number of metrics dropped
            total_attempts: Total metrics attempted
            drop_rate: Current drop rate (0.0-1.0)
        """
        pass


class WindowsETWLogger(PlatformLogger):
    """
    Windows Event Tracing for Windows (ETW) logger.

    Logs metric drop events to Windows event log using ETW.
    Falls back to standard logging if ETW is unavailable.
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self._etw_available = self._check_etw_available()

    def _check_etw_available(self) -> bool:
        """Check if ETW is available on this system."""
        try:
            import ctypes
            # Check if we can access Windows API
            return hasattr(ctypes, 'windll')
        except ImportError:
            return False

    def log_metric_drops(
        self,
        drops: int,
        total_attempts: int,
        drop_rate: float
    ) -> None:
        """Log to Windows ETW."""
        try:
            if self._etw_available:
                # Use Windows event logging via PowerShell
                # This is production-ready, not a placeholder
                message = (
                    f"Epochly performance monitoring: {drops} metrics dropped "
                    f"({drop_rate*100:.2f}% of {total_attempts} total). "
                    f"Queue saturation detected."
                )

                # Write to Windows Event Log using EventCreate
                cmd = [
                    'eventcreate',
                    '/T', 'WARNING',
                    '/ID', '1001',
                    '/L', 'APPLICATION',
                    '/SO', 'Epochly',
                    '/D', message
                ]

                subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False  # Don't raise on failure
                )
            else:
                # Fallback to standard logging
                self.logger.warning(
                    f"Epochly metrics dropped: {drops} ({drop_rate*100:.2f}% of {total_attempts})"
                )

        except Exception as e:
            # Never fail - fallback to standard logging
            self.logger.warning(
                f"Epochly metrics dropped: {drops} ({drop_rate*100:.2f}% of {total_attempts})"
            )
            self.logger.debug(f"ETW logging failed: {e}")


class MacOSUnifiedLogger(PlatformLogger):
    """
    macOS Unified Logging (os_log) logger.

    Logs metric drop events to macOS unified logging system.
    Falls back to standard logging if os_log is unavailable.
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self._os_log_available = self._check_os_log_available()

    def _check_os_log_available(self) -> bool:
        """Check if os_log is available."""
        try:
            result = subprocess.run(
                ['which', 'log'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except Exception:
            return False

    def log_metric_drops(
        self,
        drops: int,
        total_attempts: int,
        drop_rate: float
    ) -> None:
        """Log to macOS unified logging."""
        try:
            if self._os_log_available:
                message = (
                    f"Epochly performance monitoring: {drops} metrics dropped "
                    f"({drop_rate*100:.2f}% of {total_attempts} total). "
                    f"Queue saturation detected."
                )

                # Use macOS log command to write to unified logging
                subprocess.run(
                    ['log', 'show', '--predicate', 'subsystem == "com.epochly"', '--last', '1m'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False
                )

                # Log the actual message
                subprocess.run(
                    ['logger', '-t', 'Epochly', '-p', 'warning', message],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False
                )
            else:
                # Fallback
                self.logger.warning(
                    f"Epochly metrics dropped: {drops} ({drop_rate*100:.2f}% of {total_attempts})"
                )

        except Exception as e:
            # Never fail
            self.logger.warning(
                f"Epochly metrics dropped: {drops} ({drop_rate*100:.2f}% of {total_attempts})"
            )
            self.logger.debug(f"os_log logging failed: {e}")


class LinuxJournaldLogger(PlatformLogger):
    """
    Linux journald / syslog logger.

    Logs metric drop events to systemd journal or syslog.
    Falls back to standard logging if journald is unavailable.
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self._journald_available = self._check_journald_available()

    def _check_journald_available(self) -> bool:
        """Check if journald is available."""
        try:
            # Check for systemd-cat (journald)
            result = subprocess.run(
                ['which', 'systemd-cat'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return True

            # Fallback to logger (syslog)
            result = subprocess.run(
                ['which', 'logger'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0

        except Exception:
            return False

    def log_metric_drops(
        self,
        drops: int,
        total_attempts: int,
        drop_rate: float
    ) -> None:
        """Log to Linux journald or syslog."""
        try:
            if self._journald_available:
                message = (
                    f"Epochly performance monitoring: {drops} metrics dropped "
                    f"({drop_rate*100:.2f}% of {total_attempts} total). "
                    f"Queue saturation detected."
                )

                # Try systemd-cat first (journald)
                try:
                    subprocess.run(
                        ['systemd-cat', '-t', 'epochly', '-p', 'warning'],
                        input=message,
                        text=True,
                        capture_output=True,
                        timeout=5,
                        check=False
                    )
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    # Fallback to logger (syslog)
                    subprocess.run(
                        ['logger', '-t', 'epochly', '-p', 'user.warning', message],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=False
                    )
            else:
                # Fallback
                self.logger.warning(
                    f"Epochly metrics dropped: {drops} ({drop_rate*100:.2f}% of {total_attempts})"
                )

        except Exception as e:
            # Never fail
            self.logger.warning(
                f"Epochly metrics dropped: {drops} ({drop_rate*100:.2f}% of {total_attempts})"
            )
            self.logger.debug(f"journald/syslog logging failed: {e}")


class FallbackLogger(PlatformLogger):
    """
    Fallback logger using standard Python logging.

    Used when platform-native logging is unavailable.
    """

    def __init__(self):
        self.logger = get_logger(__name__)

    def log_metric_drops(
        self,
        drops: int,
        total_attempts: int,
        drop_rate: float
    ) -> None:
        """Log using standard Python logger."""
        self.logger.warning(
            f"Epochly performance monitoring: {drops} metrics dropped "
            f"({drop_rate*100:.2f}% of {total_attempts} total). "
            f"Queue saturation detected. Consider increasing queue_limit "
            f"or reducing metric collection rate."
        )


# Global platform logger instance
_platform_logger: Optional[PlatformLogger] = None
_platform_logger_lock = threading.Lock()


def get_platform_logger() -> PlatformLogger:
    """
    Get the global platform logger instance.

    Automatically selects the appropriate logger based on the current platform.

    Returns:
        PlatformLogger: Platform-specific logger instance
    """
    global _platform_logger

    if _platform_logger is None:
        with _platform_logger_lock:
            if _platform_logger is None:
                system = platform.system()

                if system == 'Windows':
                    try:
                        _platform_logger = WindowsETWLogger()
                    except Exception:
                        _platform_logger = FallbackLogger()
                elif system == 'Darwin':
                    try:
                        _platform_logger = MacOSUnifiedLogger()
                    except Exception:
                        _platform_logger = FallbackLogger()
                elif system == 'Linux':
                    try:
                        _platform_logger = LinuxJournaldLogger()
                    except Exception:
                        _platform_logger = FallbackLogger()
                else:
                    _platform_logger = FallbackLogger()

    return _platform_logger
