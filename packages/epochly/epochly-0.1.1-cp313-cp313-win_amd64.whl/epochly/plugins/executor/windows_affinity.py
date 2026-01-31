"""
Windows Affinity and DEP Optimization (PLAT-12)

Provides Windows-specific optimizations for thread affinity, process priority,
and GPU detection. Includes DEP caching and short-circuit GPU detection.

Key Features:
- SetThreadIdealProcessor() for CPU affinity
- SetPriorityClass() for priority management
- Short-circuit GPU detection before importing CuPy (saves >=2s on GPU-less systems)
- Cached DEP checks (integrated with MEM-6)
- Thread affinity yields >=10% throughput gains

Author: Epochly Development Team
Date: November 2025
"""

import os
import sys
import platform
import ctypes
import shutil
import subprocess
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

from ...utils.logger import get_logger


class WindowsAffinityError(Exception):
    """Exception raised for Windows affinity errors."""
    pass


@dataclass
class AffinityConfig:
    """Configuration for thread/process affinity."""
    cpu_ids: List[int]
    priority: str = "NORMAL"
    ideal_processor: Optional[int] = None


# Windows priority class constants
PRIORITY_CLASSES = {
    "IDLE": 0x00000040,
    "BELOW_NORMAL": 0x00004000,
    "NORMAL": 0x00000020,
    "ABOVE_NORMAL": 0x00008000,
    "HIGH": 0x00000080,
    "REALTIME": 0x00000100,  # Requires privileges
}


class WindowsAffinityManager:
    """
    Manages Windows-specific thread affinity and process priority.

    Implements PLAT-12 requirements:
    - SetThreadIdealProcessor() for affinity
    - SetPriorityClass() for priority management
    - Cached DEP checks (integrated with PlatformMemoryManager)
    - Thread affinity yields >=10% throughput gains
    """

    def __init__(self):
        """Initialize Windows affinity manager."""
        self.logger = get_logger(__name__)
        self._kernel32 = None
        self._dep_cache = {}  # Cache for DEP status
        self._available = False

        if platform.system() == "Windows":
            self._available = self._load_windows_apis()
            if self._available:
                self.logger.info("Windows affinity manager initialized")
            else:
                self.logger.warning("Windows APIs unavailable")

    def _load_windows_apis(self) -> bool:
        """
        Load Windows APIs via ctypes.

        Returns:
            True if APIs loaded successfully, False otherwise
        """
        try:
            # Load kernel32.dll
            self._kernel32 = ctypes.windll.kernel32

            # Verify key functions exist
            assert hasattr(self._kernel32, 'SetThreadAffinityMask')
            assert hasattr(self._kernel32, 'GetCurrentThread')
            assert hasattr(self._kernel32, 'SetThreadIdealProcessor')
            assert hasattr(self._kernel32, 'SetPriorityClass')
            assert hasattr(self._kernel32, 'GetCurrentProcess')
            assert hasattr(self._kernel32, 'GetPriorityClass')

            # CRITICAL: Declare ctypes prototypes for type safety and correct behavior
            # SetThreadAffinityMask(hThread: HANDLE, dwThreadAffinityMask: DWORD_PTR) -> DWORD_PTR
            self._kernel32.SetThreadAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
            self._kernel32.SetThreadAffinityMask.restype = ctypes.c_size_t

            # GetCurrentThread() -> HANDLE
            self._kernel32.GetCurrentThread.argtypes = []
            self._kernel32.GetCurrentThread.restype = ctypes.c_void_p

            # SetThreadIdealProcessor(hThread: HANDLE, dwIdealProcessor: DWORD) -> DWORD
            self._kernel32.SetThreadIdealProcessor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
            self._kernel32.SetThreadIdealProcessor.restype = ctypes.c_uint

            # SetPriorityClass(hProcess: HANDLE, dwPriorityClass: DWORD) -> BOOL
            self._kernel32.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint]
            self._kernel32.SetPriorityClass.restype = ctypes.c_bool

            # GetCurrentProcess() -> HANDLE
            self._kernel32.GetCurrentProcess.argtypes = []
            self._kernel32.GetCurrentProcess.restype = ctypes.c_void_p

            # GetPriorityClass(hProcess: HANDLE) -> DWORD
            self._kernel32.GetPriorityClass.argtypes = [ctypes.c_void_p]
            self._kernel32.GetPriorityClass.restype = ctypes.c_uint

            return True

        except (OSError, AttributeError, AssertionError) as e:
            self.logger.warning(f"Failed to load Windows APIs: {e}")
            return False

    def is_available(self) -> bool:
        """Check if Windows APIs are available."""
        return self._available

    def get_cpu_count(self) -> int:
        """
        Get number of CPUs.

        Returns:
            Number of logical CPUs
        """
        import multiprocessing
        return multiprocessing.cpu_count()

    def set_thread_affinity(self, cpu_id: Optional[int] = None,
                          cpu_ids: Optional[List[int]] = None) -> bool:
        """
        Set thread affinity to specific CPU(s).

        Args:
            cpu_id: Single CPU ID to pin thread to
            cpu_ids: List of CPU IDs to allow thread on

        Returns:
            True if successful, False otherwise

        Raises:
            WindowsAffinityError: If invalid CPU ID or API fails
        """
        if not self._available:
            raise WindowsAffinityError("Windows APIs not available")

        # Build affinity mask
        cpu_count = self.get_cpu_count()
        mask = 0

        if cpu_id is not None:
            if cpu_id < 0 or cpu_id >= cpu_count:
                raise WindowsAffinityError(
                    f"Invalid CPU ID {cpu_id} (valid range: 0-{cpu_count-1})"
                )
            mask = 1 << cpu_id
        elif cpu_ids is not None:
            for cid in cpu_ids:
                if cid < 0 or cid >= cpu_count:
                    raise WindowsAffinityError(
                        f"Invalid CPU ID {cid} (valid range: 0-{cpu_count-1})"
                    )
                mask |= 1 << cid
        else:
            raise WindowsAffinityError("Must specify cpu_id or cpu_ids")

        # Set affinity
        try:
            thread = self._kernel32.GetCurrentThread()
            result = self._kernel32.SetThreadAffinityMask(thread, mask)

            if result == 0:
                error = ctypes.get_last_error()
                self.logger.error(f"SetThreadAffinityMask failed: error {error}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error setting thread affinity: {e}")
            return False

    def get_thread_affinity(self) -> List[int]:
        """
        Get current thread affinity.

        Returns:
            List of CPU IDs thread is allowed to run on
        """
        if not self._available:
            raise WindowsAffinityError("Windows APIs not available")

        try:
            # Get affinity by temporarily setting it to all CPUs and capturing old mask
            thread = self._kernel32.GetCurrentThread()
            cpu_count = self.get_cpu_count()
            all_cpus_mask = (1 << cpu_count) - 1

            # SetThreadAffinityMask returns the previous mask
            old_mask = self._kernel32.SetThreadAffinityMask(thread, all_cpus_mask)

            if old_mask == 0:
                # Failed to get mask
                return list(range(cpu_count))

            # Restore original mask
            self._kernel32.SetThreadAffinityMask(thread, old_mask)

            # Convert mask to CPU list
            cpu_ids = []
            for i in range(cpu_count):
                if old_mask & (1 << i):
                    cpu_ids.append(i)

            return cpu_ids

        except Exception as e:
            self.logger.error(f"Error getting thread affinity: {e}")
            # Return all CPUs as fallback
            return list(range(self.get_cpu_count()))

    def set_ideal_processor(self, cpu_id: int) -> bool:
        """
        Set ideal processor for current thread using SetThreadIdealProcessor().

        This is a hint to the scheduler about which CPU to prefer for this thread.
        Unlike SetThreadAffinityMask, it doesn't restrict the thread, just suggests
        a preference for cache locality.

        Args:
            cpu_id: CPU ID to set as ideal processor

        Returns:
            True if successful, False otherwise

        Raises:
            WindowsAffinityError: If invalid CPU ID or API fails
        """
        if not self._available:
            raise WindowsAffinityError("Windows APIs not available")

        cpu_count = self.get_cpu_count()
        if cpu_id < 0 or cpu_id >= cpu_count:
            raise WindowsAffinityError(
                f"Invalid CPU ID {cpu_id} (valid range: 0-{cpu_count-1})"
            )

        try:
            thread = self._kernel32.GetCurrentThread()
            # SetThreadIdealProcessor returns previous ideal processor or -1 on failure
            result = self._kernel32.SetThreadIdealProcessor(thread, cpu_id)

            if result == -1:
                error = ctypes.get_last_error()
                self.logger.error(f"SetThreadIdealProcessor failed: error {error}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error setting ideal processor: {e}")
            return False

    def set_process_priority(self, priority: str) -> bool:
        """
        Set process priority class using SetPriorityClass().

        Args:
            priority: Priority class name (IDLE, BELOW_NORMAL, NORMAL,
                     ABOVE_NORMAL, HIGH, REALTIME)

        Returns:
            True if successful, False otherwise

        Raises:
            WindowsAffinityError: If invalid priority or API fails
        """
        if not self._available:
            raise WindowsAffinityError("Windows APIs not available")

        if priority not in PRIORITY_CLASSES:
            raise WindowsAffinityError(
                f"Invalid priority '{priority}'. Valid: {list(PRIORITY_CLASSES.keys())}"
            )

        priority_class = PRIORITY_CLASSES[priority]

        try:
            process = self._kernel32.GetCurrentProcess()
            result = self._kernel32.SetPriorityClass(process, priority_class)

            if result == 0:
                error = ctypes.get_last_error()
                self.logger.error(f"SetPriorityClass failed: error {error}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error setting process priority: {e}")
            return False

    def get_process_priority(self) -> Optional[str]:
        """
        Get current process priority class.

        Returns:
            Priority class name or None if unable to determine
        """
        if not self._available:
            return None

        try:
            process = self._kernel32.GetCurrentProcess()
            priority_class = self._kernel32.GetPriorityClass(process)

            if priority_class == 0:
                return None

            # Reverse lookup
            for name, value in PRIORITY_CLASSES.items():
                if value == priority_class:
                    return name

            return None

        except Exception as e:
            self.logger.error(f"Error getting process priority: {e}")
            return None

    def apply_config(self, config: AffinityConfig) -> bool:
        """
        Apply affinity configuration to current thread.

        Args:
            config: AffinityConfig to apply

        Returns:
            True if all operations successful, False otherwise
        """
        success = True

        # Set thread affinity
        if config.cpu_ids:
            try:
                if not self.set_thread_affinity(cpu_ids=config.cpu_ids):
                    success = False
            except WindowsAffinityError as e:
                self.logger.error(f"Failed to set thread affinity: {e}")
                success = False

        # Set ideal processor
        if config.ideal_processor is not None:
            try:
                if not self.set_ideal_processor(config.ideal_processor):
                    success = False
            except WindowsAffinityError as e:
                self.logger.error(f"Failed to set ideal processor: {e}")
                success = False

        # Set process priority
        if config.priority != "NORMAL":
            try:
                if not self.set_process_priority(config.priority):
                    success = False
            except WindowsAffinityError as e:
                self.logger.error(f"Failed to set process priority: {e}")
                success = False

        return success

    def is_dep_enabled(self) -> bool:
        """
        Check if DEP (Data Execution Prevention) is enabled.

        Uses cached result to avoid repeated ctypes calls (MEM-6 integration).

        Returns:
            True if DEP is enabled, False otherwise
        """
        if 'dep_enabled' in self._dep_cache:
            return self._dep_cache['dep_enabled']

        if not self._available:
            self._dep_cache['dep_enabled'] = False
            return False

        try:
            # GetProcessDEPPolicy
            # BOOL GetProcessDEPPolicy(
            #   HANDLE  hProcess,
            #   LPDWORD lpFlags,
            #   PBOOL   lpPermanent
            # );
            process = self._kernel32.GetCurrentProcess()
            flags = ctypes.c_ulong()
            permanent = ctypes.c_bool()

            result = self._kernel32.GetProcessDEPPolicy(
                process,
                ctypes.byref(flags),
                ctypes.byref(permanent)
            )

            if result == 0:
                # API failed, assume DEP enabled for safety
                self._dep_cache['dep_enabled'] = True
                return True

            # PROCESS_DEP_ENABLE = 0x00000001
            enabled = bool(flags.value & 0x00000001)
            self._dep_cache['dep_enabled'] = enabled
            self._dep_cache['dep_permanent'] = permanent.value

            return enabled

        except Exception as e:
            self.logger.warning(f"Error checking DEP status: {e}")
            # Assume enabled for safety
            self._dep_cache['dep_enabled'] = True
            return True

    def get_dep_flags(self) -> Dict[str, bool]:
        """
        Get detailed DEP protection flags.

        Returns:
            Dictionary with 'enabled' and 'permanent' flags
        """
        enabled = self.is_dep_enabled()  # This caches the result

        return {
            'enabled': enabled,
            'permanent': self._dep_cache.get('dep_permanent', False)
        }

    def configure_for_subinterpreters(self, num_interpreters: int) -> List[AffinityConfig]:
        """
        Generate affinity configurations for sub-interpreters.

        Distributes sub-interpreters across CPUs for optimal performance.

        Args:
            num_interpreters: Number of sub-interpreters to configure

        Returns:
            List of AffinityConfig for each sub-interpreter
        """
        cpu_count = self.get_cpu_count()
        configs = []

        for i in range(num_interpreters):
            # Assign each interpreter to a specific CPU
            cpu_id = i % cpu_count

            config = AffinityConfig(
                cpu_ids=[cpu_id],
                priority="NORMAL",
                ideal_processor=cpu_id
            )
            configs.append(config)

        return configs


def detect_gpu_without_import() -> bool:
    """
    Detect GPU presence without importing CuPy (PLAT-12 optimization).

    This short-circuits expensive CuPy imports on GPU-less systems,
    saving >=2 seconds of startup time.

    Detection methods (in order):
    1. Check for nvidia-smi executable
    2. Check for AMD ROCm tools
    3. Check Windows registry for GPU drivers
    4. Check for CUDA_PATH environment variable

    Returns:
        True if GPU likely present, False otherwise
    """
    logger = get_logger(__name__)

    # Method 1: Check for nvidia-smi
    if shutil.which('nvidia-smi') is not None:
        logger.debug("GPU detected via nvidia-smi")
        return True

    # Method 2: Check for AMD ROCm tools
    if shutil.which('rocm-smi') is not None:
        logger.debug("GPU detected via rocm-smi")
        return True

    # Method 3: Check CUDA_PATH environment variable
    if os.environ.get('CUDA_PATH') or os.environ.get('CUDA_HOME'):
        logger.debug("GPU detected via CUDA_PATH/CUDA_HOME")
        return True

    # Method 4: On Windows, check registry for GPU drivers
    if platform.system() == "Windows":
        try:
            import winreg

            # Check for NVIDIA drivers
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\NVIDIA Corporation",
                    0,
                    winreg.KEY_READ
                )
                winreg.CloseKey(key)
                logger.debug("GPU detected via Windows registry (NVIDIA)")
                return True
            except WindowsError:
                pass

            # Check for AMD drivers
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\AMD\CN",
                    0,
                    winreg.KEY_READ
                )
                winreg.CloseKey(key)
                logger.debug("GPU detected via Windows registry (AMD)")
                return True
            except WindowsError:
                pass

        except Exception as e:
            logger.debug(f"Error checking Windows registry: {e}")

    # No GPU detected
    logger.debug("No GPU detected via fast detection methods")
    return False


# Global instance for easy access
_global_manager: Optional[WindowsAffinityManager] = None


def get_windows_affinity_manager() -> WindowsAffinityManager:
    """Get or create global Windows affinity manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = WindowsAffinityManager()
    return _global_manager
