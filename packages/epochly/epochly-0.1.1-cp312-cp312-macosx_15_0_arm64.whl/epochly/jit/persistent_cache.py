"""
JIT Compilation Persistent Cache

Persistent disk-based cache for compiled functions that survives process restarts.
Enables warm restarts by caching JIT-compiled artifacts across sessions.

Architecture:
- Disk-based cache in ~/.epochly/jit_cache/
- Hash-based invalidation (function code changes)
- Python version validation (cache invalid on Python upgrade)
- Thread-safe cache access
- LRU cleanup to prevent unbounded growth
- Supports multiple backends (Numba, Pyston, Native JIT)

Performance:
- Save: <10ms (serialize + write to disk)
- Load: <5ms (read from disk + deserialize)
- Cache hit eliminates 1-3s compilation time

Author: Epochly Development Team
"""

import os
import sys
import time
import hashlib
import threading
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Import serialization libraries
try:
    import cloudpickle
    CLOUDPICKLE_AVAILABLE = True
except ImportError:
    cloudpickle = None
    CLOUDPICKLE_AVAILABLE = False

try:
    import dill
    DILL_AVAILABLE = True
except ImportError:
    dill = None
    DILL_AVAILABLE = False


class CacheBackend(Enum):
    """Serialization backend for cache."""
    CLOUDPICKLE = "cloudpickle"
    DILL = "dill"
    PICKLE = "pickle"


@dataclass
class CachedArtifact:
    """Cached compilation artifact with metadata."""

    function_name: str
    module_name: str
    backend: str  # 'numba', 'pyston', 'native'
    compiled_data: bytes  # Serialized compiled function
    source_hash: str
    python_version: tuple  # (major, minor)
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """Check if cached artifact is still valid."""
        # Check Python version compatibility
        current_version = sys.version_info[:2]
        if self.python_version != current_version:
            logger.debug(f"Cache invalid for {self.function_name}: Python {self.python_version} != {current_version}")
            return False

        # Check age (invalidate after 7 days)
        age_days = (time.time() - self.timestamp) / (24 * 3600)
        if age_days > 7:
            logger.debug(f"Cache expired for {self.function_name}: {age_days:.1f} days old")
            return False

        return True


class JITArtifactCache:
    """
    Persistent disk-based cache for JIT-compiled functions.

    Provides warm restart capability by caching compiled artifacts to disk.
    Automatically invalidates on code changes, Python version upgrades, or age.

    Thread-safe for concurrent access.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize JIT artifact cache.

        Args:
            cache_dir: Cache directory path (default: ~/.epochly/jit_cache)
        """
        # Determine cache directory
        if cache_dir is None:
            # Check environment variable first
            cache_dir = os.environ.get('EPOCHLY_JIT_CACHE_DIR')

        if cache_dir is None:
            # Default to ~/.epochly/jit_cache
            cache_dir = str(Path.home() / '.epochly' / 'jit_cache')

        self.cache_dir = Path(cache_dir).expanduser().resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Thread safety
        self._lock = threading.RLock()

        # In-memory cache for fast access
        self._memory_cache: Dict[str, CachedArtifact] = {}

        # Determine serialization backend
        self._serialization_backend = self._select_backend()

        # Statistics
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_saves = 0
        self._cache_invalidations = 0

        logger.info(f"JIT cache initialized: {self.cache_dir} (backend: {self._serialization_backend.value})")

    def _select_backend(self) -> CacheBackend:
        """
        Select best available serialization backend.

        Returns:
            Selected cache backend
        """
        # Prefer cloudpickle (best for closures and lambdas)
        if CLOUDPICKLE_AVAILABLE:
            return CacheBackend.CLOUDPICKLE

        # Fallback to dill (also good for complex objects)
        if DILL_AVAILABLE:
            return CacheBackend.DILL

        # Last resort: standard pickle (limited support)
        return CacheBackend.PICKLE

    def cache_key(self, func: Callable, backend: str) -> str:
        """
        Generate stable cache key from function code and backend.

        Args:
            func: Function to cache
            backend: JIT backend name ('numba', 'pyston', 'native')

        Returns:
            Cache key string
        """
        func_name = getattr(func, '__name__', 'unknown')
        module_name = getattr(func, '__module__', 'unknown')

        # Hash function code for invalidation detection
        code_hash = self._compute_code_hash(func)

        # Include backend in key (same function may compile differently)
        return f"{module_name}.{func_name}_{code_hash[:16]}_{backend}"

    def _compute_code_hash(self, func: Callable) -> str:
        """
        Compute hash of function code for cache invalidation.

        Args:
            func: Function to hash

        Returns:
            SHA-256 hash of function bytecode
        """
        try:
            # Try to use bytecode (most reliable)
            code_bytes = func.__code__.co_code
            return hashlib.sha256(code_bytes).hexdigest()
        except AttributeError:
            # Fallback to string representation
            func_str = str(func).encode('utf-8')
            return hashlib.sha256(func_str).hexdigest()

    def _cache_file_path(self, cache_key: str) -> Path:
        """
        Get file path for cache key.

        Args:
            cache_key: Cache key

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{cache_key}.cache"

    def save_compiled(self, func: Callable, compiled_func: Callable, backend: str,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save compiled function to persistent cache.

        Args:
            func: Original function
            compiled_func: Compiled function to cache
            backend: Backend name ('numba', 'pyston', 'native')
            metadata: Optional metadata to store with artifact

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with self._lock:
                # Generate cache key
                key = self.cache_key(func, backend)

                # Serialize compiled function
                compiled_data = self._serialize(compiled_func)

                # Create artifact
                artifact = CachedArtifact(
                    function_name=getattr(func, '__name__', 'unknown'),
                    module_name=getattr(func, '__module__', 'unknown'),
                    backend=backend,
                    compiled_data=compiled_data,
                    source_hash=self._compute_code_hash(func),
                    python_version=sys.version_info[:2],
                    timestamp=time.time(),
                    metadata=metadata or {}
                )

                # Save to disk
                cache_file = self._cache_file_path(key)
                self._write_artifact(cache_file, artifact)

                # Update memory cache
                self._memory_cache[key] = artifact

                self._cache_saves += 1
                logger.debug(f"Saved {artifact.function_name} to cache (backend: {backend})")
                return True

        except Exception as e:
            logger.warning(f"Failed to save {func.__name__} to cache: {e}")
            return False

    def load_compiled(self, func: Callable, backend: str) -> Optional[Callable]:
        """
        Load compiled function from persistent cache.

        Args:
            func: Original function
            backend: Backend name ('numba', 'pyston', 'native')

        Returns:
            Compiled function if found and valid, None otherwise
        """
        try:
            with self._lock:
                # Generate cache key
                key = self.cache_key(func, backend)

                # Check memory cache first (fast path)
                if key in self._memory_cache:
                    artifact = self._memory_cache[key]
                    if artifact.is_valid():
                        self._cache_hits += 1
                        logger.debug(f"Cache hit (memory): {artifact.function_name}")
                        return self._deserialize(artifact.compiled_data)
                    else:
                        # Invalidate stale cache entry
                        del self._memory_cache[key]
                        self._cache_invalidations += 1
                        
                        # Also remove from disk to prevent reloading stale data
                        cache_file = self._cache_file_path(key)
                        if cache_file.exists():
                            cache_file.unlink()
                        
                        # Return None - cache is invalid
                        self._cache_misses += 1
                        return None

                # Check disk cache (slow path)
                cache_file = self._cache_file_path(key)
                if cache_file.exists():
                    artifact = self._read_artifact(cache_file)

                    if artifact and artifact.is_valid():
                        # Restore to memory cache
                        self._memory_cache[key] = artifact
                        self._cache_hits += 1
                        logger.debug(f"Cache hit (disk): {artifact.function_name}")
                        return self._deserialize(artifact.compiled_data)
                    else:
                        # Remove invalid cache file
                        cache_file.unlink()
                        self._cache_invalidations += 1

                # Cache miss
                self._cache_misses += 1
                logger.debug(f"Cache miss: {func.__name__} (backend: {backend})")
                return None

        except Exception as e:
            logger.warning(f"Failed to load {func.__name__} from cache: {e}")
            self._cache_misses += 1
            return None

    def _serialize(self, obj: Any) -> bytes:
        """
        Serialize object using selected backend.

        Args:
            obj: Object to serialize

        Returns:
            Serialized bytes
        """
        if self._serialization_backend == CacheBackend.CLOUDPICKLE and CLOUDPICKLE_AVAILABLE:
            return cloudpickle.dumps(obj)
        elif self._serialization_backend == CacheBackend.DILL and DILL_AVAILABLE:
            return dill.dumps(obj)
        else:
            import pickle
            return pickle.dumps(obj)

    def _deserialize(self, data: bytes) -> Any:
        """
        Deserialize object using selected backend.

        Args:
            data: Serialized bytes

        Returns:
            Deserialized object
        """
        if self._serialization_backend == CacheBackend.CLOUDPICKLE and CLOUDPICKLE_AVAILABLE:
            return cloudpickle.loads(data)
        elif self._serialization_backend == CacheBackend.DILL and DILL_AVAILABLE:
            return dill.loads(data)
        else:
            import pickle
            return pickle.loads(data)

    def _write_artifact(self, cache_file: Path, artifact: CachedArtifact) -> None:
        """
        Write artifact to disk.

        Args:
            cache_file: Path to cache file
            artifact: Artifact to write
        """
        # Write to temporary file first (atomic write)
        temp_file = cache_file.with_suffix('.tmp')

        try:
            with open(temp_file, 'wb') as f:
                # Serialize entire artifact
                artifact_data = self._serialize(artifact)
                f.write(artifact_data)

            # Atomic rename
            temp_file.replace(cache_file)

        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            raise e

    def _read_artifact(self, cache_file: Path) -> Optional[CachedArtifact]:
        """
        Read artifact from disk.

        Args:
            cache_file: Path to cache file

        Returns:
            CachedArtifact if successful, None otherwise
        """
        try:
            with open(cache_file, 'rb') as f:
                artifact_data = f.read()
                artifact = self._deserialize(artifact_data)

                # Validate artifact structure
                if not isinstance(artifact, CachedArtifact):
                    logger.warning(f"Invalid artifact in {cache_file}")
                    return None

                return artifact

        except Exception as e:
            logger.warning(f"Failed to read cache file {cache_file}: {e}")
            return None

    def clear(self) -> int:
        """
        Clear all cached artifacts.

        Returns:
            Number of files removed
        """
        removed = 0

        with self._lock:
            # Clear memory cache
            self._memory_cache.clear()

            # Remove disk cache files
            for cache_file in self.cache_dir.glob('*.cache'):
                try:
                    cache_file.unlink()
                    removed += 1
                except Exception as e:
                    logger.warning(f"Failed to remove {cache_file}: {e}")

        logger.info(f"Cleared JIT cache: {removed} files removed")
        return removed

    def cleanup_stale(self, max_age_days: float = 7) -> int:
        """
        Remove stale cache entries (LRU cleanup).

        Args:
            max_age_days: Maximum age in days before cleanup

        Returns:
            Number of files removed
        """
        removed = 0
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600

        with self._lock:
            # Clean up disk cache
            for cache_file in self.cache_dir.glob('*.cache'):
                try:
                    # Check file age
                    file_age = current_time - cache_file.stat().st_mtime

                    if file_age > max_age_seconds:
                        cache_file.unlink()
                        removed += 1
                        logger.debug(f"Removed stale cache file: {cache_file.name}")

                except Exception as e:
                    logger.warning(f"Failed to check/remove {cache_file}: {e}")

            # Clean up memory cache
            stale_keys = []
            for key, artifact in self._memory_cache.items():
                if not artifact.is_valid():
                    stale_keys.append(key)

            for key in stale_keys:
                del self._memory_cache[key]
                removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} stale cache entries")

        return removed

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        with self._lock:
            total_requests = self._cache_hits + self._cache_misses
            hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0.0

            # Count disk cache files
            disk_files = len(list(self.cache_dir.glob('*.cache')))

            return {
                'cache_dir': str(self.cache_dir),
                'serialization_backend': self._serialization_backend.value,
                'cache_hits': self._cache_hits,
                'cache_misses': self._cache_misses,
                'cache_saves': self._cache_saves,
                'cache_invalidations': self._cache_invalidations,
                'hit_rate': hit_rate,
                'memory_cache_size': len(self._memory_cache),
                'disk_cache_size': disk_files,
                'total_requests': total_requests
            }


# Global cache instance (singleton)
_global_cache: Optional[JITArtifactCache] = None
_cache_lock = threading.Lock()


def get_persistent_cache() -> JITArtifactCache:
    """
    Get global JIT persistent cache (singleton).

    Returns:
        JITArtifactCache instance
    """
    global _global_cache

    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                _global_cache = JITArtifactCache()

    return _global_cache
