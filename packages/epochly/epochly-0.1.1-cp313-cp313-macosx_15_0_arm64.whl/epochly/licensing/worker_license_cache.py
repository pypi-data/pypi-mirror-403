"""
Worker License Pre-Cache for Fast ProcessPool Startup (Phase 1.1)

Addresses RCA finding: Workers spend ~1000ms re-validating licenses during
ProcessPool spawn because each worker:
1. Creates a LicenseEnforcer instance
2. Reads encrypted license from disk
3. Decrypts using hardware-derived key
4. Verifies signature
5. May trigger network sync

Solution: Pre-validate license in main process, store in simple JSON cache
that workers can load instantly without cryptographic operations.

Performance Target: Worker license load <10ms (vs ~1000ms currently)

Architecture:
- Main process calls initialize_main_process() during Level 2 init
- Cache file is plain JSON (no encryption needed - it's read-only validation data)
- Workers call get_worker_license() for instant access
- Falls back to full validation if cache unavailable

Author: Epochly Development Team
Date: December 11, 2025
"""

import json
import os
import time
import threading
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class WorkerLicenseCache:
    """
    Fast license cache for ProcessPool workers.

    Pre-computes license validation in main process, stores in shared file
    that workers can load instantly without re-validation overhead.
    """

    CACHE_FILENAME = "worker_license.cache"
    DEFAULT_MAX_AGE_SECONDS = 3600  # 1 hour

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_cache_age_seconds: float = DEFAULT_MAX_AGE_SECONDS
    ):
        """
        Initialize worker license cache.

        Args:
            cache_dir: Directory for cache file (default: system cache dir)
            max_cache_age_seconds: Maximum age before cache considered stale
        """
        self._cache_dir = cache_dir or self._get_default_cache_dir()
        self._max_cache_age = max_cache_age_seconds
        self._lock = threading.Lock()
        self._cached_data: Optional[Dict[str, Any]] = None

    def _get_default_cache_dir(self) -> Path:
        """Get platform-appropriate cache directory."""
        if os.name == 'nt':
            base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            return Path(base) / 'Epochly' / '.cache'
        else:
            base = os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
            return Path(base) / 'epochly'

    @property
    def _cache_file(self) -> Path:
        """Get path to cache file."""
        return self._cache_dir / self.CACHE_FILENAME

    def initialize_main_process(self) -> None:
        """
        Initialize cache from main process.

        Called during Level 2 initialization to pre-compute license state
        that workers can load instantly.
        """
        try:
            # Ensure cache directory exists
            self._cache_dir.mkdir(parents=True, exist_ok=True)

            # Get license data from enforcer
            license_data = self._get_license_from_enforcer()

            # Add metadata
            cache_data = {
                **license_data,
                'validated_at': time.time(),
                'valid': True,
                'cache_version': 1
            }

            # Write atomically
            self._write_cache(cache_data)

            # Also cache in memory
            self._cached_data = cache_data

            logger.debug(f"Worker license cache initialized: tier={cache_data.get('tier')}, max_cores={cache_data.get('max_cores')}")

        except Exception as e:
            logger.warning(f"Failed to initialize worker license cache: {e}")
            # Non-fatal - workers will use fallback

    def _get_license_from_enforcer(self) -> Dict[str, Any]:
        """Get license data from the main enforcer.

        CRITICAL: Uses _skip_worker_cache=True to prevent infinite recursion.
        When EPOCHLY_WORKER_PROCESS=1 is set and cache is unavailable, the fallback
        path calls this method. If we called get_limits() without the skip flag,
        it would try to use the worker cache again, causing infinite recursion.
        """
        try:
            from .license_enforcer import get_license_enforcer

            enforcer = get_license_enforcer()
            # CRITICAL: _skip_worker_cache=True prevents infinite recursion
            limits = enforcer.get_limits(_skip_worker_cache=True)

            return {
                'tier': limits.get('tier', 'community'),
                'max_cores': limits.get('max_cores'),
                'gpu_enabled': limits.get('gpu_enabled', False),
                'memory_limit_gb': limits.get('memory_limit_gb'),
                'features': limits.get('features', [])
            }
        except Exception as e:
            logger.debug(f"Could not get license from enforcer: {e}")
            # Return conservative defaults
            return {
                'tier': 'community',
                'max_cores': 4,
                'gpu_enabled': False,
                'memory_limit_gb': 16,
                'features': ['basic_optimization', 'threading', 'memory_pooling']
            }

    def _write_cache(self, data: Dict[str, Any]) -> None:
        """Write cache file atomically with thread safety.

        Uses atomic write pattern:
        1. Write to temp file
        2. Set secure permissions on temp file (removes race window)
        3. Atomic rename to final location
        """
        temp_file = self._cache_file.with_suffix('.tmp')

        # Thread safety: Guard writes to prevent race conditions
        with self._lock:
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f)

                # Set secure permissions on temp file BEFORE replace
                # This removes the race window where file exists with permissive perms
                # replace() preserves mode from temp file, so destination is secure immediately
                if os.name != 'nt':
                    os.chmod(temp_file, 0o600)

                # Atomic move (preserves permissions from temp file)
                temp_file.replace(self._cache_file)

            except Exception:
                # Clean up temp file if something failed
                # Use bare 'raise' to preserve original traceback
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except Exception:
                        pass
                raise

    def get_worker_license(self) -> Dict[str, Any]:
        """
        Get license data for worker process.

        Fast path: Load from cache file (<10ms)
        Slow path: Fall back to enforcer if cache unavailable

        Returns:
            License data dictionary with tier, max_cores, etc.
        """
        # Try memory cache first (fastest)
        if self._cached_data is not None:
            if not self._is_stale(self._cached_data):
                return self._cached_data

        # Try file cache
        try:
            cached = self.read_cache()
            if cached and not self._is_stale(cached):
                self._cached_data = cached
                return cached
        except Exception as e:
            logger.debug(f"Could not read worker license cache: {e}")

        # Fallback to enforcer (slow path)
        logger.debug("Worker license cache miss - using fallback")
        return self._fallback_get_license()

    def read_cache(self) -> Optional[Dict[str, Any]]:
        """
        Read cache file directly.

        Returns:
            Cached data or None if unavailable
        """
        if not self._cache_file.exists():
            return None

        with self._lock:
            try:
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.debug(f"Invalid cache file: {e}")
                return None

    def _is_stale(self, data: Dict[str, Any]) -> bool:
        """Check if cached data is too old."""
        validated_at = data.get('validated_at', 0)
        age = time.time() - validated_at
        return age > self._max_cache_age

    def _fallback_get_license(self) -> Dict[str, Any]:
        """Fallback when cache unavailable - use enforcer directly.

        Caches the result in memory with fresh timestamp to avoid repeated
        slow path calls if cache file remains unavailable.
        """
        license_data = self._get_license_from_enforcer()

        # Cache in memory with fresh timestamp to avoid repeated slow paths
        self._cached_data = {
            **license_data,
            'validated_at': time.time(),
            'valid': True,
            'cache_version': 1,
            'source': 'fallback'  # Mark as fallback-sourced for debugging
        }

        return self._cached_data

    def invalidate(self) -> None:
        """Invalidate cache (delete file)."""
        self._cached_data = None

        with self._lock:
            try:
                if self._cache_file.exists():
                    self._cache_file.unlink()
                logger.debug("Worker license cache invalidated")
            except Exception as e:
                logger.debug(f"Could not delete cache file: {e}")

    def refresh(self) -> None:
        """Refresh cache with current license data."""
        self.invalidate()
        self.initialize_main_process()


# Global singleton
_global_worker_cache: Optional[WorkerLicenseCache] = None
_global_cache_lock = threading.Lock()


def get_global_worker_cache() -> WorkerLicenseCache:
    """
    Get global worker license cache singleton.

    Auto-initializes on first access in main process.

    Returns:
        Global WorkerLicenseCache instance
    """
    global _global_worker_cache

    # Fast path
    if _global_worker_cache is not None:
        return _global_worker_cache

    # Slow path with lock
    with _global_cache_lock:
        if _global_worker_cache is not None:
            return _global_worker_cache

        _global_worker_cache = WorkerLicenseCache()

        # Auto-initialize if we're in main process
        # Worker processes have EPOCHLY_WORKER_PROCESS=1; skip init for them
        # Use explicit != '1' check to handle edge cases like EPOCHLY_WORKER_PROCESS="0"
        if os.environ.get('EPOCHLY_WORKER_PROCESS') != '1':
            try:
                _global_worker_cache.initialize_main_process()
            except Exception as e:
                logger.debug(f"Auto-init of worker license cache failed: {e}")

        return _global_worker_cache


def reset_global_worker_cache() -> None:
    """Reset global cache (for testing)."""
    global _global_worker_cache

    with _global_cache_lock:
        if _global_worker_cache is not None:
            _global_worker_cache.invalidate()
        _global_worker_cache = None
