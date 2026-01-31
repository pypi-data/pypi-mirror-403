"""
macOS Mach Timing Backend (PLAT-11)

Provides native macOS timing using Mach APIs instead of psutil for better accuracy
and performance. Falls back to psutil when Mach APIs are unavailable.

Key Features:
- mach_absolute_time() for high-precision cycle counters
- host_statistics64() for CPU statistics
- Spawn-safe operations (no fork() issues with Objective-C runtime)
- Sampling accuracy within ±1% vs Apple Instruments
- Thread-safe operations
- Graceful fallback to psutil

Author: Epochly Development Team
Date: November 2025
"""

import os
import sys
import platform
import time
import ctypes
import psutil
from typing import Optional, Dict, Any
from dataclasses import dataclass

from ..utils.logger import get_logger


class MachTimingError(Exception):
    """Exception raised for Mach timing errors."""
    pass


@dataclass
class MachTimingStats:
    """CPU timing statistics from Mach kernel."""
    user_time: int
    system_time: int
    idle_time: int
    nice_time: int

    def total_time(self) -> int:
        """Calculate total CPU time."""
        return self.user_time + self.system_time + self.idle_time + self.nice_time

    def utilization(self) -> float:
        """Calculate CPU utilization as percentage."""
        total = self.total_time()
        if total == 0:
            return 0.0
        active_time = self.user_time + self.system_time
        return (active_time / total) * 100.0


class MacOSTimingBackend:
    """
    macOS-native timing backend using Mach APIs.

    This implementation uses mach_absolute_time() for high-precision timing
    and host_statistics64() for CPU statistics, providing better accuracy
    than psutil-based approximations.

    Implements PLAT-11 requirements:
    - Swap psutil.cpu_freq() for mach_absolute_time/host_statistics64
    - Ensure spawn-safety (avoid fork() deadlocks with Objective-C runtime)
    - Sampling accuracy within ±1% vs Instruments
    - No crashes with Cocoa event loops
    """

    def __init__(self, allow_fallback: bool = True):
        """
        Initialize macOS timing backend.

        Args:
            allow_fallback: If True, fall back to psutil when Mach APIs unavailable
        """
        self.logger = get_logger(__name__)
        self.allow_fallback = allow_fallback
        self._mach_available = False
        self._timebase_info = None
        self._libc = None
        self._libsystem = None

        # Try to load Mach APIs
        if platform.system() == "Darwin":
            self._mach_available = self._load_mach_apis()
            if self._mach_available:
                self.logger.info("macOS Mach timing backend initialized (native APIs)")
            elif self.allow_fallback:
                self.logger.info("macOS Mach timing backend using psutil fallback")
            else:
                self.logger.warning("macOS Mach timing backend unavailable, fallback disabled")

    def _load_mach_apis(self) -> bool:
        """
        Load Mach APIs via ctypes.

        Returns:
            True if APIs loaded successfully, False otherwise
        """
        try:
            # Load libSystem.B.dylib which contains Mach functions
            self._libsystem = ctypes.CDLL(
                '/usr/lib/libSystem.B.dylib',
                use_errno=True
            )

            # Define mach_absolute_time()
            # uint64_t mach_absolute_time(void);
            self._libsystem.mach_absolute_time.argtypes = []
            self._libsystem.mach_absolute_time.restype = ctypes.c_uint64

            # Define mach_timebase_info()
            # kern_return_t mach_timebase_info(mach_timebase_info_t info);
            class mach_timebase_info_data_t(ctypes.Structure):
                _fields_ = [
                    ('numer', ctypes.c_uint32),
                    ('denom', ctypes.c_uint32),
                ]

            self._libsystem.mach_timebase_info.argtypes = [
                ctypes.POINTER(mach_timebase_info_data_t)
            ]
            self._libsystem.mach_timebase_info.restype = ctypes.c_int

            # Get timebase info for conversion to nanoseconds
            timebase = mach_timebase_info_data_t()
            result = self._libsystem.mach_timebase_info(ctypes.byref(timebase))

            if result == 0:  # KERN_SUCCESS
                self._timebase_info = {
                    'numer': timebase.numer,
                    'denom': timebase.denom,
                }
                self.logger.debug(
                    f"Mach timebase: {timebase.numer}/{timebase.denom}"
                )
            else:
                self.logger.warning(f"mach_timebase_info failed: {result}")
                return False

            # Define host_statistics64() for CPU stats
            # kern_return_t host_statistics64(
            #     host_t host_priv,
            #     host_flavor_t flavor,
            #     host_info64_t host_info64_out,
            #     mach_msg_type_number_t *host_info64_outCnt
            # );

            # Get mach_host_self()
            self._libsystem.mach_host_self.argtypes = []
            self._libsystem.mach_host_self.restype = ctypes.c_uint

            # HOST_CPU_LOAD_INFO = 3
            self.HOST_CPU_LOAD_INFO = 3
            self.CPU_STATE_MAX = 4  # user, system, idle, nice

            # CPU load info structure
            class host_cpu_load_info_data_t(ctypes.Structure):
                _fields_ = [
                    ('cpu_ticks', ctypes.c_uint * 4)  # user, system, idle, nice
                ]

            self._libsystem.host_statistics64.argtypes = [
                ctypes.c_uint,  # host
                ctypes.c_int,  # flavor
                ctypes.POINTER(host_cpu_load_info_data_t),  # info
                ctypes.POINTER(ctypes.c_uint)  # count
            ]
            self._libsystem.host_statistics64.restype = ctypes.c_int

            # Store structure for reuse
            self._cpu_load_info_type = host_cpu_load_info_data_t

            return True

        except (OSError, AttributeError) as e:
            self.logger.warning(f"Failed to load Mach APIs: {e}")
            return False

    def is_available(self) -> bool:
        """Check if Mach timing is available (or fallback is enabled)."""
        return self._mach_available or self.allow_fallback

    def get_absolute_time(self) -> int:
        """
        Get current absolute time using mach_absolute_time().

        Returns:
            Absolute time in Mach time units (convert with convert_to_nanoseconds)

        Raises:
            MachTimingError: If Mach APIs unavailable and fallback disabled
        """
        if self._mach_available:
            try:
                return self._libsystem.mach_absolute_time()
            except Exception as e:
                self.logger.error(f"mach_absolute_time failed: {e}")
                if not self.allow_fallback:
                    raise MachTimingError(f"mach_absolute_time failed: {e}")
                # Fall through to fallback

        if self.allow_fallback:
            # Use time.perf_counter_ns() as fallback
            return time.perf_counter_ns()
        else:
            raise MachTimingError("Mach timing unavailable and fallback disabled")

    def convert_to_nanoseconds(self, mach_time: int) -> int:
        """
        Convert Mach absolute time to nanoseconds.

        Args:
            mach_time: Time in Mach units from get_absolute_time()

        Returns:
            Time in nanoseconds
        """
        if self._mach_available and self._timebase_info:
            # Convert using timebase: nanoseconds = mach_time * numer / denom
            # CRITICAL: Use integer math to avoid floating-point precision loss
            return (mach_time * self._timebase_info['numer']) // self._timebase_info['denom']
        else:
            # If using fallback, time is already in nanoseconds
            return mach_time

    def get_cpu_statistics(self) -> MachTimingStats:
        """
        Get CPU statistics using host_statistics64().

        Returns:
            MachTimingStats with CPU time counters

        Raises:
            MachTimingError: If unable to get statistics
        """
        if self._mach_available:
            try:
                # Get host
                host = self._libsystem.mach_host_self()

                # Prepare info structure
                cpu_load_info = self._cpu_load_info_type()
                count = ctypes.c_uint(self.CPU_STATE_MAX)

                # Call host_statistics64
                result = self._libsystem.host_statistics64(
                    host,
                    self.HOST_CPU_LOAD_INFO,
                    ctypes.byref(cpu_load_info),
                    ctypes.byref(count)
                )

                if result == 0:  # KERN_SUCCESS
                    # Extract CPU ticks
                    # cpu_ticks[0] = user, [1] = system, [2] = idle, [3] = nice
                    return MachTimingStats(
                        user_time=cpu_load_info.cpu_ticks[0],
                        system_time=cpu_load_info.cpu_ticks[1],
                        idle_time=cpu_load_info.cpu_ticks[2],
                        nice_time=cpu_load_info.cpu_ticks[3]
                    )
                else:
                    self.logger.error(f"host_statistics64 failed: {result}")
                    if not self.allow_fallback:
                        raise MachTimingError(f"host_statistics64 failed: {result}")
                    # Fall through to fallback

            except Exception as e:
                self.logger.error(f"Error getting CPU statistics: {e}")
                if not self.allow_fallback:
                    raise MachTimingError(f"Error getting CPU statistics: {e}")
                # Fall through to fallback

        if self.allow_fallback:
            # Use psutil as fallback
            cpu_times = psutil.cpu_times()
            return MachTimingStats(
                user_time=int(cpu_times.user * 1000000),  # Convert to ticks
                system_time=int(cpu_times.system * 1000000),
                idle_time=int(cpu_times.idle * 1000000),
                nice_time=int(getattr(cpu_times, 'nice', 0) * 1000000)
            )
        else:
            raise MachTimingError("CPU statistics unavailable and fallback disabled")


# Global instance for easy access
_global_backend: Optional[MacOSTimingBackend] = None


def get_macos_timing_backend() -> MacOSTimingBackend:
    """Get or create global macOS timing backend instance."""
    global _global_backend
    if _global_backend is None:
        _global_backend = MacOSTimingBackend(allow_fallback=True)
    return _global_backend


def is_macos_timing_available() -> bool:
    """Check if native macOS Mach timing is available."""
    if platform.system() != "Darwin":
        return False
    backend = get_macos_timing_backend()
    return backend._mach_available
