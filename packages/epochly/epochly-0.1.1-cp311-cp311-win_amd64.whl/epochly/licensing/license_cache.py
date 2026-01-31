"""
License State Cache for Performance Optimization

Caches license check results to avoid redundant overhead on hot paths.
Particularly important for GPU license checks that happen in background
detection threads every ~10 seconds.

Architecture Reference:
- perf_review.md v2 Section 6: Cache license state at startup, revalidate on signal
- Pattern: TTL-based cache with signal invalidation

Author: Epochly Development Team
Date: November 13, 2025
"""

import time
import threading
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Single cache entry with value and expiration"""
    value: Any
    expires_at: float


class LicenseCache:
    """
    Thread-safe cache for license check results with TTL and invalidation.

    Features:
    - TTL-based expiration (default: 300 seconds = 5 minutes)
    - Signal-based invalidation for license changes
    - Thread-safe access via RLock
    - Graceful handling of check function failures

    Usage:
        cache = LicenseCache(ttl_seconds=300)

        # First call checks license, subsequent calls use cache
        gpu_allowed = cache.get_or_check('gpu_access', lambda: check_gpu_access())

        # Invalidate on license change signal
        cache.invalidate('gpu_access')
    """

    def __init__(self, ttl_seconds: float = 300.0):
        """
        Initialize license cache.

        Args:
            ttl_seconds: Time-to-live for cached entries (default: 5 minutes)
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()

    def get_or_check(self, key: str, check_function: Callable[[], Any]) -> Any:
        """
        Get cached license result or call check function if not cached/expired.

        Thread-safe with double-checked locking pattern for performance.

        Args:
            key: Cache key (e.g., 'gpu_access', 'feature_x')
            check_function: Function to call if cache miss/expired

        Returns:
            Cached or freshly checked license result
        """
        current_time = time.time()

        # Fast path: Check cache without lock
        entry = self._cache.get(key)
        if entry and current_time < entry.expires_at:
            return entry.value

        # Slow path: Refresh with lock
        with self._lock:
            # Double-check: another thread may have refreshed
            entry = self._cache.get(key)
            if entry and current_time < entry.expires_at:
                return entry.value

            # Call check function
            try:
                value = check_function()
            except ImportError:
                # Licensing module unavailable - return conservative default
                value = False
            except Exception as e:
                # Check function failed - return cached value if available or False
                if entry:
                    # Extend TTL since we can't refresh
                    self._cache[key] = CacheEntry(
                        value=entry.value,
                        expires_at=current_time + self.ttl_seconds
                    )
                    return entry.value
                else:
                    # No cached value - return False
                    value = False

            # Store in cache
            self._cache[key] = CacheEntry(
                value=value,
                expires_at=current_time + self.ttl_seconds
            )

            return value

    def invalidate(self, key: str):
        """
        Invalidate specific cache entry.

        Args:
            key: Cache key to invalidate
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def invalidate_all(self):
        """Clear entire cache (all entries)."""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.

        Returns:
            Dictionary with cache stats (size, entries, etc.)
        """
        with self._lock:
            return {
                'size': len(self._cache),
                'ttl_seconds': self.ttl_seconds,
                'entries': list(self._cache.keys())
            }


# Global singleton cache instance
_global_license_cache: Optional[LicenseCache] = None
_global_cache_lock = threading.Lock()


def get_license_cache() -> LicenseCache:
    """
    Get global license cache singleton.

    Returns:
        Global LicenseCache instance
    """
    global _global_license_cache

    # Fast path
    if _global_license_cache is not None:
        return _global_license_cache

    # Slow path: create with lock
    with _global_cache_lock:
        # Double-check
        if _global_license_cache is not None:
            return _global_license_cache

        # Create global cache with 5-minute TTL
        _global_license_cache = LicenseCache(ttl_seconds=300.0)

        return _global_license_cache
