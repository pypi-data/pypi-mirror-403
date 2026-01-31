"""
JIT Backend Manifest Loader (Phase 2.4)

Persistent caching of JIT backend availability to eliminate runtime discovery overhead.

Architecture:
- Manifest stored: ~/.epochly/jit_manifest.json
- TTL: 1 hour (backends don't change frequently)
- Async refresh in background
- Fast load from disk (<10ms)

Performance:
- First load: 50-100ms (backend discovery)
- Cached load: <1ms (JSON read)
- Eliminates RLock-guarded imports on every JITManager instantiation
"""

import json
import time
import threading
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import sys
import logging

logger = logging.getLogger(__name__)


@dataclass
class JITManifest:
    """JIT backend availability manifest."""

    backends: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    detected_at: float = 0.0
    python_version: str = ""
    platform: str = ""

    def __post_init__(self):
        """Initialize defaults."""
        if not self.python_version:
            self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if not self.platform:
            self.platform = sys.platform

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JITManifest':
        """Deserialize from dictionary."""
        return cls(**data)

    @classmethod
    def detect(cls) -> 'JITManifest':
        """
        Detect JIT backend availability.

        Performs actual imports to check backend availability.
        This is the slow path (50-100ms).

        Returns:
            JITManifest with detected backends
        """
        backends = {}

        # Check Numba
        try:
            import numba
            backends['NUMBA'] = {
                'available': True,
                'version': numba.__version__,
                'supports_parallel': hasattr(numba, 'prange')
            }
        except ImportError:
            backends['NUMBA'] = {'available': False}

        # Check Python 3.13 native JIT
        if sys.version_info >= (3, 13):
            native_jit = hasattr(sys, '_jit_enabled') or hasattr(sys, 'experimental_jit_compiler')
            backends['NATIVE'] = {
                'available': native_jit,
                'version': f"{sys.version_info.major}.{sys.version_info.minor}"
            }
        else:
            backends['NATIVE'] = {'available': False, 'reason': 'Python < 3.13'}

        # Check Pyston (only supports Python 3.7-3.10)
        if sys.version_info[:2] <= (3, 10):
            try:
                import pyston_lite_autoload
                backends['PYSTON'] = {
                    'available': True,
                    'version': getattr(pyston_lite_autoload, '__version__', 'unknown')
                }
            except ImportError:
                backends['PYSTON'] = {'available': False, 'reason': 'Not installed'}
        else:
            backends['PYSTON'] = {'available': False, 'reason': 'Python > 3.10'}

        return cls(
            backends=backends,
            detected_at=time.time()
        )

    def is_stale(self, max_age_seconds: float = 3600.0) -> bool:
        """
        Check if manifest is stale.

        Args:
            max_age_seconds: Maximum age before refresh (default: 1 hour)

        Returns:
            True if manifest should be refreshed
        """
        return (time.time() - self.detected_at) > max_age_seconds


class ManifestLoader:
    """
    Loads and caches JIT backend manifest.

    First load: Reads from ~/.epochly/jit_manifest.json or detects
    Subsequent loads: Returns cached result
    Async refresh: Updates manifest in background if stale
    """

    def __init__(self, manifest_path: Optional[Path] = None):
        """
        Initialize manifest loader.

        Args:
            manifest_path: Optional custom path (default: ~/.epochly/jit_manifest.json)
        """
        if manifest_path:
            self.manifest_path = manifest_path
        else:
            epochly_dir = Path.home() / '.epochly'
            epochly_dir.mkdir(exist_ok=True)
            self.manifest_path = epochly_dir / 'jit_manifest.json'

        # Cache
        self._manifest_cache: Optional[JITManifest] = None
        self._manifest_cache_time: float = 0.0
        # Use RLock (reentrant) because load() calls save() while holding the lock
        self._cache_lock = threading.RLock()

        # Async refresh state
        self._refresh_task: Optional[threading.Thread] = None

    def load(self, force_refresh: bool = False) -> JITManifest:
        """
        Load JIT manifest with caching.

        Fast path: Return cached manifest if fresh
        Slow path: Load from disk or detect

        Args:
            force_refresh: Force fresh detection even if cached

        Returns:
            JITManifest with backend availability
        """
        # Fast path: return cached if fresh
        if not force_refresh and self._manifest_cache is not None:
            if not self._manifest_cache.is_stale():
                return self._manifest_cache

        # Slow path: load or detect
        with self._cache_lock:
            # Double-check after lock
            if not force_refresh and self._manifest_cache is not None:
                if not self._manifest_cache.is_stale():
                    return self._manifest_cache

            # Try to load from disk
            if self.manifest_path.exists():
                try:
                    manifest = self._load_from_disk()
                    if not manifest.is_stale():
                        self._manifest_cache = manifest
                        return manifest
                except Exception as e:
                    logger.warning(f"Failed to load manifest from disk: {e}")

            # Detect fresh
            manifest = JITManifest.detect()
            self._manifest_cache = manifest

            # Save to disk for future loads
            try:
                self.save(manifest)
            except Exception as e:
                logger.warning(f"Failed to save manifest: {e}")

            return manifest

    def _load_from_disk(self) -> JITManifest:
        """Load manifest from JSON file."""
        with open(self.manifest_path, 'r') as f:
            data = json.load(f)
        return JITManifest.from_dict(data)

    def save(self, manifest: JITManifest) -> None:
        """
        Save manifest to disk.

        Args:
            manifest: Manifest to save
        """
        with self._cache_lock:
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.manifest_path, 'w') as f:
                json.dump(manifest.to_dict(), f, indent=2)

    def refresh_async(self) -> None:
        """
        Refresh manifest asynchronously in background.

        Returns immediately, updates cache in background thread.
        """
        if self._refresh_task and self._refresh_task.is_alive():
            return  # Already refreshing

        def background_refresh():
            try:
                manifest = JITManifest.detect()
                with self._cache_lock:
                    self._manifest_cache = manifest
                    self.save(manifest)
                logger.debug("Async manifest refresh complete")
            except Exception as e:
                logger.warning(f"Async manifest refresh failed: {e}")

        self._refresh_task = threading.Thread(target=background_refresh, daemon=True)
        self._refresh_task.start()


# Global manifest loader (singleton pattern)
_global_loader: Optional[ManifestLoader] = None
_loader_lock = threading.Lock()


def get_manifest(force_refresh: bool = False) -> JITManifest:
    """
    Get JIT backend manifest (global singleton).

    First call: Detects or loads from disk
    Subsequent calls: Returns cached result

    Args:
        force_refresh: Force fresh detection

    Returns:
        JITManifest with backend availability
    """
    global _global_loader

    if _global_loader is None:
        with _loader_lock:
            if _global_loader is None:
                _global_loader = ManifestLoader()

    return _global_loader.load(force_refresh=force_refresh)
