"""
Shared Capability Manifest (Phase 4.1)

Persistent capability cache so runtime reads precomputed CPU/GPU/NUMA features
instead of detecting on every process startup.

Architecture:
- Installer/first run: Detects and persists to ~/.epochly/capability_manifest.json
- Runtime: Reads from file (<1ms) instead of detecting (10-50ms)
- Invalidation: On hardware change or manual trigger
- Integrates with detection_async.py

Performance:
- First detection: 10-50ms (nvidia-smi, cpu detection, etc.)
- Cached read: <1ms (JSON file read)
- 10-50× speedup on process startup
"""

import json
import time
import threading
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CapabilityManifest:
    """Hardware and software capability manifest."""

    # Hardware
    physical_cores: int
    numa_nodes: int
    has_gpu: bool
    gpu_count: int = 0
    gpu_memory_mb: int = 0

    # GPU Backend (Task 4 - perf_fixes2.md)
    cuda_available: bool = False
    rocm_available: bool = False
    oneapi_available: bool = False
    active_backend: str = "cpu"  # One of: cuda, rocm, oneapi, cpu
    backend_version: str = ""    # Version of active backend

    # Software
    python_version: str = ""
    subinterpreter_support: bool = False
    platform: str = ""

    # Metadata
    detected_at: float = 0.0
    hardware_hash: str = ""  # Hash to detect hardware changes

    def __post_init__(self):
        """Initialize defaults and normalize fields."""
        import sys

        if not self.python_version:
            self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        if not self.platform:
            self.platform = sys.platform

        if not self.detected_at:
            self.detected_at = time.time()

        # Normalize backend fields (Task 4)
        self.active_backend = (self.active_backend or 'cpu').lower().strip()
        self.backend_version = str(self.backend_version or '').strip()

        # Validate backend consistency
        if self.active_backend != 'cpu' and not (self.cuda_available or self.rocm_available or self.oneapi_available):
            logger.warning(f"Inconsistent backend state: active_backend={self.active_backend} but no backend available; falling back to cpu")
            self.active_backend = 'cpu'

        # Generate hardware hash if not provided
        if not self.hardware_hash:
            self.hardware_hash = self._compute_hardware_hash()

    def _compute_hardware_hash(self) -> str:
        """
        Compute hash of hardware characteristics.

        Includes GPU backend info and memory to detect hardware/driver changes.
        """
        hw_str = (f"{self.physical_cores}:{self.numa_nodes}:{self.has_gpu}:{self.gpu_count}:"
                  f"{self.gpu_memory_mb}:"
                  f"{self.cuda_available}:{self.rocm_available}:{self.oneapi_available}:"
                  f"{self.active_backend}:{self.backend_version}")
        return hashlib.md5(hw_str.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CapabilityManifest':
        """
        Deserialize from dictionary.

        Tolerates unknown keys for forward/backward compatibility.
        """
        from dataclasses import fields as dc_fields

        # Filter to known fields only (ignore extra keys from future versions)
        allowed = {f.name for f in dc_fields(cls)}
        filtered = {k: v for k, v in data.items() if k in allowed}

        return cls(**filtered)

    @classmethod
    def detect(cls) -> 'CapabilityManifest':
        """
        Detect hardware/software capabilities.

        Uses detection_async module for detection logic.

        Returns:
            CapabilityManifest with detected capabilities
        """
        try:
            # Use async detector
            from .detection_async import get_capabilities_sync

            caps = get_capabilities_sync()

            return cls(
                physical_cores=caps.get('physical_cores', 1),
                numa_nodes=caps.get('numa_nodes', 1),
                has_gpu=caps.get('has_gpu', False),
                gpu_count=caps.get('gpu_count', 0),
                gpu_memory_mb=caps.get('gpu_memory_mb', 0),
                cuda_available=caps.get('cuda_available', False),
                rocm_available=caps.get('rocm_available', False),
                oneapi_available=caps.get('oneapi_available', False),
                active_backend=caps.get('active_backend', 'cpu'),
                backend_version=caps.get('backend_version', ''),
                python_version=caps.get('python_version', ''),
                subinterpreter_support=caps.get('subinterpreter_support', False),
                platform=caps.get('platform', ''),
                detected_at=caps.get('detected_at', time.time())
            )

        except Exception as e:
            logger.warning(f"Capability detection failed, using defaults: {e}")

            # Safe defaults
            import os, sys
            return cls(
                physical_cores=os.cpu_count() or 1,
                numa_nodes=1,
                has_gpu=False,
                python_version=f"{sys.version_info.major}.{sys.version_info.minor}",
                subinterpreter_support=sys.version_info >= (3, 12),
                platform=sys.platform
            )

    def has_changed(self, other: 'CapabilityManifest') -> bool:
        """
        Check if hardware changed compared to another manifest.

        Args:
            other: Previous manifest

        Returns:
            True if hardware changed
        """
        return (
            self.hardware_hash != other.hardware_hash or
            self.physical_cores != other.physical_cores or
            self.numa_nodes != other.numa_nodes or
            self.has_gpu != other.has_gpu or
            self.has_backend_changed(other)
        )

    def has_backend_changed(self, other: 'CapabilityManifest') -> bool:
        """
        Check if GPU backend changed compared to another manifest.

        Detects:
        - Backend availability changes (CUDA → ROCm, etc.)
        - Active backend switch
        - Backend version updates

        Args:
            other: Previous manifest

        Returns:
            True if GPU backend changed
        """
        return (
            self.cuda_available != other.cuda_available or
            self.rocm_available != other.rocm_available or
            self.oneapi_available != other.oneapi_available or
            self.active_backend != other.active_backend or
            self.backend_version != other.backend_version
        )


class CapabilityManifestLoader:
    """
    Loads and caches capability manifest.

    Installer/first run detects and persists.
    Runtime reads from disk for fast startup.
    """

    def __init__(self, manifest_path: Optional[Path] = None):
        """
        Initialize manifest loader.

        Args:
            manifest_path: Optional custom path (default: ~/.epochly/capability_manifest.json)
        """
        if manifest_path:
            self.manifest_path = manifest_path
        else:
            epochly_dir = Path.home() / '.epochly'
            epochly_dir.mkdir(exist_ok=True)
            self.manifest_path = epochly_dir / 'capability_manifest.json'

        # Cache
        self._manifest_cache: Optional[CapabilityManifest] = None
        self._cache_lock = threading.RLock()  # Reentrant to allow nested acquisition (load→save)

    def load(self, force_detect: bool = False) -> CapabilityManifest:
        """
        Load capability manifest with caching.

        Fast path: Load from disk (~1ms)
        Slow path: Detect and persist (10-50ms)

        Args:
            force_detect: Force fresh detection

        Returns:
            CapabilityManifest
        """
        # Fast path: cached
        if not force_detect and self._manifest_cache is not None:
            return self._manifest_cache

        with self._cache_lock:
            # Double-check
            if not force_detect and self._manifest_cache is not None:
                return self._manifest_cache

            # Try to load from disk
            if not force_detect and self.manifest_path.exists():
                try:
                    manifest = self._load_from_disk()

                    # Quick hardware change detection (skip slow GPU check)
                    # Only re-detect if CPU/NUMA topology changed
                    import os
                    current_cores = os.cpu_count() or 1
                    if current_cores == manifest.physical_cores:
                        # CPU topology unchanged - use cached manifest
                        # (GPU changes are rare and handled by periodic refresh)
                        self._manifest_cache = manifest
                        logger.debug("Loaded capability manifest from disk (hardware unchanged)")
                        return manifest
                    else:
                        logger.info(f"CPU topology changed ({manifest.physical_cores} → {current_cores}), re-detecting")

                except Exception as e:
                    logger.warning(f"Failed to load manifest from disk: {e}")

            # Detect fresh
            manifest = CapabilityManifest.detect()
            self._manifest_cache = manifest

            # Save for future loads
            try:
                self.save(manifest)
                logger.info("Capability manifest detected and persisted")
            except Exception as e:
                logger.warning(f"Failed to save manifest: {e}")

            return manifest

    def _load_from_disk(self) -> CapabilityManifest:
        """Load manifest from JSON file."""
        with open(self.manifest_path, 'r') as f:
            data = json.load(f)
        return CapabilityManifest.from_dict(data)

    def save(self, manifest: CapabilityManifest) -> None:
        """
        Save manifest to disk.

        Args:
            manifest: Manifest to save
        """
        with self._cache_lock:
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.manifest_path, 'w') as f:
                json.dump(manifest.to_dict(), f, indent=2)

    def invalidate(self) -> None:
        """Invalidate cache, force re-detection on next load."""
        with self._cache_lock:
            self._manifest_cache = None


# Global loader (singleton)
_global_loader: Optional[CapabilityManifestLoader] = None
_loader_lock = threading.Lock()


def get_capability_manifest(force_detect: bool = False) -> CapabilityManifest:
    """
    Get capability manifest (global singleton).

    First call: Detects or loads from disk
    Subsequent calls: Returns cached result

    Args:
        force_detect: Force fresh detection

    Returns:
        CapabilityManifest
    """
    global _global_loader

    if _global_loader is None:
        with _loader_lock:
            if _global_loader is None:
                _global_loader = CapabilityManifestLoader()

    return _global_loader.load(force_detect=force_detect)
