"""
Platform-Specific Safety Checks for Epochly

Detects platform-specific restrictions that prevent Level 3 (multiprocessing):
- Linux: Container environments, /dev/shm size, thread-after-fork safety
- Windows: Frozen executables, main module guard requirements
- Cross-platform: Resource limits, active multiprocessing pools

This ensures Epochly gracefully handles all execution environments.

Author: Epochly Development Team
Date: November 19, 2025
"""

import os
import sys
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, List

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PlatformRestrictions:
    """
    Platform-specific restrictions that may prevent Level 3.

    Attributes:
        platform: Platform name (darwin, linux, win32)
        can_use_level3: Whether Level 3 is safe on this platform
        reasons: List of restriction reasons (if can_use_level3=False)
        shm_size_mb: Shared memory size in MB (Linux containers)
        thread_count: Active thread count (Linux fork safety)
        is_containerized: Whether running in container (Linux)
        is_frozen: Whether running as frozen executable (Windows)
    """
    platform: str
    can_use_level3: bool
    reasons: List[str] = field(default_factory=list)
    shm_size_mb: float = 0.0
    thread_count: int = 0
    is_containerized: bool = False
    is_frozen: bool = False


def is_containerized() -> bool:
    """
    Detect if running in Docker/Kubernetes container (Linux-specific).

    Returns:
        True if containerized, False otherwise
    """
    # Check 1: /.dockerenv file
    if os.path.exists('/.dockerenv'):
        logger.debug("Container detected: /.dockerenv exists")
        return True

    # Check 2: /proc/1/cgroup contains docker/kubepods
    try:
        with open('/proc/1/cgroup', 'r') as f:
            cgroup_content = f.read()
            if 'docker' in cgroup_content or 'kubepods' in cgroup_content:
                logger.debug("Container detected: cgroup contains docker/kubepods")
                return True
    except FileNotFoundError:
        pass  # /proc/1/cgroup doesn't exist (not Linux or not containerized)
    except Exception as e:
        logger.debug(f"Error checking cgroup: {e}")

    return False


def get_shm_size() -> int:
    """
    Get /dev/shm size in bytes (Linux-specific).

    Returns:
        Size in bytes, or 0 if /dev/shm unavailable
    """
    try:
        stat = os.statvfs('/dev/shm')
        size_bytes = stat.f_blocks * stat.f_frsize
        return size_bytes
    except FileNotFoundError:
        logger.debug("/dev/shm not found")
        return 0
    except Exception as e:
        logger.debug(f"Error checking /dev/shm size: {e}")
        return 0


def is_safe_to_fork() -> bool:
    """
    Check if it's safe to fork (Linux thread-after-fork safety).

    Fork is unsafe if background threads exist (pthread issues).

    Returns:
        True if safe (single thread), False if unsafe (multiple threads)
    """
    try:
        thread_count = threading.active_count()

        # Safe only if exactly 1 thread (main thread)
        if thread_count > 1:
            logger.debug(f"Not safe to fork: {thread_count} threads active")
            return False

        return True
    except Exception as e:
        logger.debug(f"Error checking thread count: {e}")
        return True  # Conservative - assume safe if can't check


def is_frozen_executable() -> bool:
    """
    Detect if running as frozen executable (PyInstaller, py2exe) (Windows-specific).

    Returns:
        True if frozen, False otherwise
    """
    return getattr(sys, 'frozen', False)


def has_main_guard(script_path: str) -> bool:
    """
    Check if script has 'if __name__ == "__main__"' guard (Windows requirement).

    Args:
        script_path: Path to script file

    Returns:
        True if guard present, False otherwise
    """
    try:
        with open(script_path, 'r') as f:
            content = f.read()
            # Check for common main guard patterns
            return ('if __name__' in content and '__main__' in content)
    except FileNotFoundError:
        return False
    except Exception as e:
        logger.debug(f"Error checking main guard: {e}")
        return False


def check_process_limits() -> bool:
    """
    Check if system allows spawning enough processes (cross-platform).

    Requires >= 32 processes for Level 3 (16 workers + overhead).

    Returns:
        True if limits sufficient, False otherwise
    """
    # Windows doesn't have resource module
    if sys.platform == 'win32':
        return True  # Assume OK on Windows

    try:
        import resource
        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NPROC)

        # Need at least 32 processes
        if soft_limit < 32:
            logger.warning(f"Process limit too low: {soft_limit} (need >= 32 for Level 3)")
            return False

        return True
    except ImportError:
        # resource module not available
        return True  # Conservative - assume OK
    except Exception as e:
        logger.debug(f"Error checking process limits: {e}")
        return True


def has_active_multiprocessing_pool() -> bool:
    """
    Check if already running inside a multiprocessing Pool worker.

    Returns:
        True if in Pool worker, False otherwise
    """
    try:
        import multiprocessing
        current = multiprocessing.current_process()

        # Pool workers have non-empty _identity tuple
        if hasattr(current, '_identity') and current._identity:
            logger.debug(f"Running in Pool worker: identity={current._identity}")
            return True

        return False
    except Exception as e:
        logger.debug(f"Error checking multiprocessing pool: {e}")
        return False


def detect_platform_restrictions() -> PlatformRestrictions:
    """
    Detect all platform-specific restrictions for Level 3.

    Checks:
    - Linux: Containerization, /dev/shm size, thread safety
    - Windows: Frozen executable, main guard
    - Cross-platform: Resource limits, active pools

    Returns:
        PlatformRestrictions with complete platform analysis
    """
    platform = sys.platform
    can_use_level3 = True
    reasons = []

    # Platform-specific data
    shm_size_bytes = 0
    thread_count = 0
    is_container = False
    is_frozen = False

    # Cross-platform checks FIRST (apply to all platforms)
    if not check_process_limits():
        can_use_level3 = False
        reasons.append("Insufficient process limit (need >= 32)")

    if has_active_multiprocessing_pool():
        can_use_level3 = False
        reasons.append("Already running in multiprocessing Pool worker (nested Pool not allowed)")

    # Linux-specific checks
    if platform == 'linux':
        # Container detection
        is_container = is_containerized()
        if is_container:
            shm_size_bytes = get_shm_size()
            shm_size_mb = shm_size_bytes / (1024 * 1024)

            if shm_size_mb < 64:  # Minimum 64MB for Level 3
                can_use_level3 = False
                reasons.append(f"Container /dev/shm too small: {shm_size_mb:.0f}MB (need >= 64MB)")

        # Thread-after-fork safety
        thread_count = threading.active_count()
        if not is_safe_to_fork():
            # Don't block Level 3, just warn (we can use spawn instead of fork)
            reasons.append(f"Active threads: {thread_count} (will use 'spawn' instead of 'fork')")

    # Windows-specific checks
    elif platform == 'win32':
        # Frozen executable
        is_frozen = is_frozen_executable()
        if is_frozen:
            can_use_level3 = False
            reasons.append("Frozen executable (PyInstaller/py2exe) - multiprocessing unsupported")

        # Main guard (warning only, don't block)
        if sys.argv and not has_main_guard(sys.argv[0]):
            reasons.append("Missing 'if __name__ == \"__main__\"' guard (recommended for Windows)")

    # macOS-specific (handled by subprocess_safety.py)
    elif platform == 'darwin':
        # Subprocess detection already handles macOS fork issues
        pass

    return PlatformRestrictions(
        platform=platform,
        can_use_level3=can_use_level3,
        reasons=reasons,
        shm_size_mb=shm_size_bytes / (1024 * 1024) if shm_size_bytes > 0 else 0.0,
        thread_count=thread_count,
        is_containerized=is_container,
        is_frozen=is_frozen
    )
