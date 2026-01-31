"""
Cross-platform utilities for memory operations.

Provides platform-independent wrappers for system calls that differ
between Unix and Windows platforms.
"""
import mmap
import sys
import tempfile
import os
import time
from typing import Optional


def get_map_private() -> int:
    """
    Get platform-appropriate MAP_PRIVATE flag for mmap.

    Returns:
        On Unix: mmap.MAP_PRIVATE
        On Windows: -1 (default anonymous mapping)
    """
    if sys.platform == 'win32':
        return -1  # Windows default for anonymous mapping
    return mmap.MAP_PRIVATE


# Module-level constant for convenience
MAP_PRIVATE = get_map_private()


def get_temp_dir() -> str:
    """
    Get cross-platform temporary directory.

    Returns:
        Path to system temp directory (works on all platforms)
    """
    return tempfile.gettempdir()


def safe_remove(path: str, retries: int = 3, delay: float = 0.1) -> bool:
    """
    Safely remove a file with Windows file locking consideration.

    On Windows, files can remain locked briefly after closing.
    This function retries removal to handle this scenario.

    Args:
        path: File path to remove
        retries: Number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        True if file was removed, False otherwise
    """
    if not os.path.exists(path):
        return True

    for attempt in range(retries):
        try:
            os.remove(path)
            return True
        except PermissionError:
            if attempt < retries - 1:
                # Windows file still locked, wait and retry
                time.sleep(delay)
            else:
                # Final attempt failed
                return False
        except Exception:
            # Other errors (file doesn't exist, etc.)
            return False

    return False


def get_temp_file(suffix: str = '', prefix: str = 'tmp', dir: Optional[str] = None) -> str:
    """
    Create a temporary file with platform-appropriate path handling.

    Args:
        suffix: File suffix/extension
        prefix: File prefix
        dir: Directory (None for system temp)

    Returns:
        Path to created temporary file
    """
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
    os.close(fd)  # Close file descriptor, just return path
    return path


def normalize_path(path: str) -> str:
    """
    Normalize path for cross-platform compatibility.

    Handles forward/backslash differences between Unix and Windows.

    Args:
        path: Path to normalize

    Returns:
        Normalized path using os.path.normpath
    """
    return os.path.normpath(path)


def create_anonymous_mmap(size: int) -> mmap.mmap:
    """
    Create anonymous memory-mapped region (cross-platform).

    Args:
        size: Size of mapping in bytes

    Returns:
        mmap object
    """
    if sys.platform == 'win32':
        # Windows: use -1 for anonymous mapping
        return mmap.mmap(-1, size)
    else:
        # Unix: use MAP_PRIVATE | MAP_ANONYMOUS
        return mmap.mmap(-1, size, flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS)


# Platform detection helpers
def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform == 'win32'


def is_unix() -> bool:
    """Check if running on Unix-like system."""
    return sys.platform in ('linux', 'darwin')


def is_macos() -> bool:
    """Check if running on macOS."""
    return sys.platform == 'darwin'


def is_linux() -> bool:
    """Check if running on Linux."""
    return sys.platform == 'linux'
