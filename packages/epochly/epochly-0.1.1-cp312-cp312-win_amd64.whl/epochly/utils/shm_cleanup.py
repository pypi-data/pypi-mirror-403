"""
Safe shared memory cleanup utilities.

CRITICAL FIX (Nov 23, 2025): This module provides utilities for safely cleaning up
shared memory segments without leaving orphaned resource_tracker processes.

The Problem:
When SharedMemory.close() and .unlink() are called without first unregistering
from resource_tracker, the tracker keeps a reference and tries to clean up
segments that are already gone. This causes KeyError and infinite CPU loops.

The Solution:
Always unregister from resource_tracker BEFORE calling close() and unlink().
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from multiprocessing.shared_memory import SharedMemory


def unregister_from_resource_tracker(shm_name: str) -> None:
    """
    Unregister shared memory from resource_tracker BEFORE close/unlink.

    CRITICAL FIX (Nov 23, 2025): This prevents resource_tracker from trying to
    clean up a segment that's already gone, which causes:
    - KeyError exceptions in resource_tracker
    - Infinite CPU spin in resource_tracker processes
    - Orphaned resource_tracker processes (100% CPU each)

    The proper cleanup sequence is:
    1. Unregister from resource_tracker (this function)
    2. Close the shared memory segment
    3. Unlink the shared memory segment

    Args:
        shm_name: The name of the shared memory segment (with or without leading '/')
    """
    try:
        from multiprocessing import resource_tracker

        # The name in resource_tracker doesn't have the leading '/'
        tracker_name = shm_name
        if tracker_name and tracker_name.startswith('/'):
            tracker_name = tracker_name[1:]

        # Unregister to prevent resource_tracker from trying to clean this up
        resource_tracker.unregister(tracker_name, 'shared_memory')

    except Exception:
        # Silently ignore - resource_tracker may not have this registered,
        # or we may be in a subprocess where the tracker isn't initialized
        pass


def safe_close_and_unlink_shm(shm: 'SharedMemory', is_creator: bool = True) -> None:
    """
    Safely close and unlink shared memory with proper resource_tracker cleanup.

    CRITICAL FIX (Nov 23, 2025): This is the correct sequence to prevent
    orphaned resource_tracker processes that spin at 100% CPU.

    The problem: When SharedMemory.unlink() is called, the segment is removed
    from the filesystem, but resource_tracker still has a reference. On exit,
    resource_tracker tries to clean up the segment, gets KeyError because it's
    gone, and enters an infinite loop.

    The solution: Unregister from resource_tracker FIRST, then close, then unlink.

    Args:
        shm: SharedMemory object to clean up
        is_creator: If True, we created this segment and should unlink it
    """
    if shm is None:
        return

    name = getattr(shm, 'name', None) or getattr(shm, '_name', None)

    try:
        # Step 1: CRITICAL - Unregister from resource_tracker FIRST
        # This prevents the resource_tracker from spinning on KeyError
        if name:
            unregister_from_resource_tracker(name)

        # Step 2: Close the shared memory
        try:
            shm.close()
        except Exception:
            pass  # May already be closed

        # Step 3: Unlink if we're the creator
        if is_creator:
            try:
                shm.unlink()
            except FileNotFoundError:
                pass  # Already unlinked
            except Exception:
                pass  # May be owned by another process

    except Exception:
        # Last resort - just try to close
        try:
            shm.close()
        except Exception:
            pass


def safe_connect_shared_memory(shm_name: str) -> 'SharedMemory':
    """
    Safely connect to existing shared memory and unregister from resource_tracker.

    CRITICAL FIX (Nov 26, 2025): Workers MUST use this function instead of
    SharedMemory(name=x, create=False) when connecting to parent-owned segments.

    The Problem:
    When a worker connects via SharedMemory(create=False), Python's resource_tracker
    in the worker process also registers the segment. When the parent cleans up
    the segment, the worker's resource_tracker tries to clean it up too, causing:
    - KeyError: 'shm_name' in resource_tracker
    - Orphaned resource_tracker processes
    - Infinite CPU spin loops

    The Solution:
    Connect to the SharedMemory AND immediately unregister from this process's
    resource_tracker. The parent process owns the segment and is responsible
    for cleanup - workers are just borrowing access.

    Args:
        shm_name: The name of the shared memory segment to connect to

    Returns:
        SharedMemory: Connected shared memory object (caller should .close() when done)

    Raises:
        FileNotFoundError: If the shared memory segment doesn't exist
    """
    from multiprocessing.shared_memory import SharedMemory

    # Connect to existing shared memory (this auto-registers with resource_tracker)
    shm = SharedMemory(name=shm_name, create=False)

    # CRITICAL: Immediately unregister from this process's resource_tracker
    # The parent process owns this segment, not us. We're just borrowing access.
    # Without this, when parent cleans up, our tracker tries to clean up
    # an already-unlinked segment -> KeyError -> infinite loop
    #
    # Use shm.name (not shm_name) to guarantee we unregister the exact name
    # that was registered, in case SharedMemory normalizes or munges names
    unregister_from_resource_tracker(shm.name)

    return shm


__all__ = ['unregister_from_resource_tracker', 'safe_close_and_unlink_shm', 'safe_connect_shared_memory']
