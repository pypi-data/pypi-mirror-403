"""
Reader-Writer Lock (Task 5 Implementation)

Allows multiple concurrent readers while ensuring exclusive writer access.

Performance Improvements:
- 2× throughput for read-heavy workloads (target)
- Eliminates serialization of concurrent reads
- Maintains mutual exclusion for writes

Usage:
    from epochly.plugins.rwlock import RWLock

    lock = RWLock()

    # Multiple readers can acquire concurrently
    with lock.reader():
        data = read_shared_data()

    # Writers get exclusive access
    with lock.writer():
        modify_shared_data()
"""

import threading
from contextlib import contextmanager
from typing import Generator

# Try to use proven library implementation
try:
    from readerwriterlock import rwlock as _rwlock_lib
    _HAS_LIBRARY = True
except ImportError:
    _rwlock_lib = None
    _HAS_LIBRARY = False


class RWLock:
    """
    Reader-writer lock wrapper.

    Uses readerwriterlock library when available (proven implementation),
    falls back to SimplifiedRWLock otherwise.
    """

    def __init__(self):
        """Initialize RWLock with best available implementation."""
        if _HAS_LIBRARY:
            self._lock = _rwlock_lib.RWLockFair()
            self._using_library = True
        else:
            self._lock = SimplifiedRWLock()
            self._using_library = False

    @contextmanager
    def reader(self) -> Generator[None, None, None]:
        """Acquire read lock (multiple concurrent readers allowed)."""
        if self._using_library:
            lock_handle = self._lock.gen_rlock()
            lock_handle.acquire()
            try:
                yield
            finally:
                lock_handle.release()
        else:
            with self._lock.reader():
                yield

    @contextmanager
    def writer(self) -> Generator[None, None, None]:
        """Acquire write lock (exclusive access)."""
        if self._using_library:
            lock_handle = self._lock.gen_wlock()
            lock_handle.acquire()
            try:
                yield
            finally:
                lock_handle.release()
        else:
            with self._lock.writer():
                yield


class SimplifiedRWLock:
    """
    Simplified reader-writer lock fallback.

    Uses readers-preference algorithm (simple but can starve writers).
    """

    def __init__(self):
        self._readers = 0
        self._writers = 0
        self._read_lock = threading.Lock()
        self._write_lock = threading.Lock()

    @contextmanager
    def reader(self):
        with self._read_lock:
            self._readers += 1
            if self._readers == 1:
                self._write_lock.acquire()

        try:
            yield
        finally:
            with self._read_lock:
                self._readers -= 1
                if self._readers == 0:
                    self._write_lock.release()

    @contextmanager
    def writer(self):
        self._write_lock.acquire()
        try:
            yield
        finally:
            self._write_lock.release()
