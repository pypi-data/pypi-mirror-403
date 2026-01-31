#!/usr/bin/env python3
"""
Forkserver Manager Module.

Centralized management of forkserver lifecycle with safety checks.

The forkserver start method provides significantly faster worker spawn times
(~50-100ms vs ~650ms for spawn) but has strict requirements:
1. Must be initialized BEFORE any threads exist
2. Only available on Unix-like platforms (not Windows)
3. Must be called from the main process

This module provides safe initialization with automatic fallback to spawn.

Author: Epochly Development Team
Date: December 12, 2025
"""

import threading
import multiprocessing
import logging
from enum import Enum
from typing import Optional, List

_logger = logging.getLogger(__name__)


class ForkserverState(Enum):
    """State machine for forkserver initialization."""
    UNKNOWN = "unknown"           # Not yet checked
    INITIALIZING = "initializing"  # Currently starting
    READY = "ready"               # Forkserver running, safe to use
    UNAVAILABLE = "unavailable"   # Cannot use (threads exist, platform, etc.)
    FAILED = "failed"             # Attempted but failed


# Module-level state (protected by lock)
_forkserver_state: ForkserverState = ForkserverState.UNKNOWN
_forkserver_lock = threading.Lock()
_initialization_error: Optional[str] = None


def get_forkserver_state() -> ForkserverState:
    """
    Thread-safe state accessor.

    Returns:
        Current forkserver state
    """
    with _forkserver_lock:
        return _forkserver_state


def is_forkserver_safe() -> bool:
    """
    Check if forkserver can be safely initialized.

    Safety requirements:
    1. Platform supports forkserver
    2. No threads exist yet (ONLY main thread via enumerate, not active_count)
    3. We are in the main process (not a worker)
    4. No conflicting multiprocessing contexts active

    NOTE: Uses threading.enumerate() instead of active_count() because:
    - enumerate() is more reliable per Python documentation
    - active_count() can miss daemon threads or threads started by C extensions
    - enumerate() gives us thread names for debugging

    Returns:
        True if forkserver can be safely started, False otherwise
    """
    import sys

    # CRITICAL FIX (Jan 2026): Skip forkserver entirely on Python 3.13 macOS
    # Python 3.13 macOS has resource tracker issues that can cause hangs during
    # forkserver initialization (ensure_running()) and ProcessPool operations.
    # Since we already use ThreadExecutor fallback on Python 3.13 macOS (in
    # sub_interpreter_executor.py), forkserver provides no benefit.
    # See: https://github.com/python/cpython/issues/82
    if sys.version_info[:2] == (3, 13) and sys.platform == 'darwin':
        _logger.debug("Forkserver disabled on Python 3.13 macOS (resource tracker issues)")
        return False

    # Check 1: Platform support
    try:
        available_methods = multiprocessing.get_all_start_methods()
        if "forkserver" not in available_methods:
            _logger.debug("Forkserver not available on this platform")
            return False
    except Exception as e:
        _logger.debug(f"Failed to get start methods: {e}")
        return False

    # Check 2: Thread count (CRITICAL - forkserver unsafe after threads exist)
    # NOTE: Use enumerate() not active_count() - more reliable per research
    current_threads = threading.enumerate()
    if len(current_threads) != 1:
        thread_names = [t.name for t in current_threads]
        _logger.debug(
            f"Forkserver unsafe: {len(current_threads)} threads exist: {thread_names}"
        )
        return False

    # Verify the single thread is the main thread
    if current_threads[0].name != "MainThread":
        _logger.debug(f"Forkserver unsafe: only thread is {current_threads[0].name}")
        return False

    # Check 3: Main process check
    try:
        if multiprocessing.current_process().name != "MainProcess":
            _logger.debug("Forkserver init skipped: not main process")
            return False
    except Exception as e:
        _logger.debug(f"Failed to check process name: {e}")
        return False

    # Check 4: No existing context (would conflict)
    # This is harder to detect, so we rely on try/except during actual init

    return True


def try_initialize_forkserver(
    preload_modules: Optional[List[str]] = None
) -> ForkserverState:
    """
    Attempt to initialize forkserver if safe.

    This should be called ONCE at first auto_enable() or Level 3 trigger,
    NOT at import time (to allow user to set their own start method first).

    Args:
        preload_modules: Modules to preload in forkserver for faster worker startup.
                        If None, uses default list: ["epochly.core", "numpy"]

    Returns:
        Final state after initialization attempt
    """
    global _forkserver_state, _initialization_error

    with _forkserver_lock:
        # Already initialized or failed - don't retry
        if _forkserver_state in (ForkserverState.READY, ForkserverState.FAILED):
            return _forkserver_state

        # Already unavailable - don't retry
        if _forkserver_state == ForkserverState.UNAVAILABLE:
            return _forkserver_state

    # Safety check (outside lock to avoid holding lock during checks)
    if not is_forkserver_safe():
        with _forkserver_lock:
            _forkserver_state = ForkserverState.UNAVAILABLE
        return ForkserverState.UNAVAILABLE

    with _forkserver_lock:
        _forkserver_state = ForkserverState.INITIALIZING

    try:
        # Get forkserver context
        ctx = multiprocessing.get_context("forkserver")

        # Configure preload modules (reduces worker startup time)
        default_preloads = [
            "epochly.core",
            "numpy",
        ]
        modules_to_preload = preload_modules or default_preloads

        try:
            ctx.set_forkserver_preload(modules_to_preload)
            _logger.debug(f"Forkserver preload configured: {modules_to_preload}")
        except Exception as e:
            # Preload failure is non-fatal - forkserver can still work
            _logger.debug(f"Forkserver preload failed (non-fatal): {e}")

        # Ensure forkserver is running (this actually starts the server process)
        # Note: ensure_running() is the key call that starts the forkserver
        from multiprocessing.forkserver import ensure_running
        ensure_running()

        with _forkserver_lock:
            _forkserver_state = ForkserverState.READY
            _logger.info("Forkserver initialized successfully")

        return ForkserverState.READY

    except Exception as e:
        with _forkserver_lock:
            _forkserver_state = ForkserverState.FAILED
            _initialization_error = str(e)
            _logger.warning(f"Forkserver initialization failed, will use spawn: {e}")

        return ForkserverState.FAILED


def get_recommended_start_method() -> str:
    """
    Get the recommended ProcessPool start method based on forkserver state.

    Returns:
        "forkserver" if ready, "spawn" otherwise (always safe fallback)
    """
    state = get_forkserver_state()

    if state == ForkserverState.READY:
        return "forkserver"
    else:
        # spawn is always safe (cross-platform, no thread restrictions)
        return "spawn"


def get_initialization_error() -> Optional[str]:
    """
    Get the error message if initialization failed.

    Returns:
        Error message string if failed, None otherwise
    """
    with _forkserver_lock:
        return _initialization_error


def _demote_forkserver_state(error_message: str) -> None:
    """
    Demote forkserver state to FAILED after runtime failure.

    Called when forkserver was READY but pool creation failed at runtime.
    This ensures subsequent calls use spawn instead.

    Args:
        error_message: Description of what failed
    """
    global _forkserver_state, _initialization_error

    with _forkserver_lock:
        # Only demote from READY - other states should not change
        if _forkserver_state == ForkserverState.READY:
            _forkserver_state = ForkserverState.FAILED
            _initialization_error = f"Runtime failure: {error_message}"
            _logger.warning(f"Forkserver demoted to FAILED: {error_message}")
