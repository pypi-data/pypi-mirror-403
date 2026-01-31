"""
GPU topology cache for fast hardware queries.

Caches GPU topology information (device count, memory, NVLink connectivity)
to avoid repeated expensive queries. Provides <1μs cached reads.

Architecture:
- Single detection at startup or on-demand
- Cached topology info
- Thread-safe access
- Graceful fallback on detection errors
"""

import threading
import time
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import subprocess


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GPUInfo:
    """
    Information about a single GPU device.

    Immutable for thread-safe sharing.
    """
    device_id: int
    name: str
    memory_total: int  # MB
    compute_capability: Tuple[int, int]


@dataclass(frozen=True)
class TopologyInfo:
    """
    Complete GPU topology information.

    Immutable for thread-safe sharing.
    """
    gpus: List[GPUInfo] = field(default_factory=list)
    nvlink_enabled: bool = False
    cached_at: float = 0.0


def _detect_gpu_topology() -> TopologyInfo:
    """
    Detect GPU topology.

    This is the expensive operation we want to cache.

    Returns:
        TopologyInfo with current hardware state
    """
    try:
        # Try nvidia-smi for NVIDIA GPUs
        gpus = _detect_nvidia_gpus()
        if gpus:
            nvlink = _detect_nvlink()
            return TopologyInfo(
                gpus=gpus,
                nvlink_enabled=nvlink,
                cached_at=time.time()
            )

        # Try CuPy
        gpus = _detect_cupy_gpus()
        if gpus:
            return TopologyInfo(
                gpus=gpus,
                nvlink_enabled=False,
                cached_at=time.time()
            )

        # No GPUs found
        return TopologyInfo(
            gpus=[],
            nvlink_enabled=False,
            cached_at=time.time()
        )

    except Exception as e:
        logger.error(f"GPU topology detection failed: {e}")
        return TopologyInfo(
            gpus=[],
            nvlink_enabled=False,
            cached_at=time.time()
        )


def _detect_nvidia_gpus() -> List[GPUInfo]:
    """
    Detect NVIDIA GPUs via nvidia-smi.

    Returns:
        List of GPUInfo, or empty if detection failed
    """
    try:
        # Query GPU info
        result = subprocess.run(
            [
                'nvidia-smi',
                '--query-gpu=index,name,memory.total,compute_cap',
                '--format=csv,noheader,nounits'
            ],
            capture_output=True,
            text=True,
            timeout=2.0
        )

        if result.returncode != 0:
            return []

        # Parse output
        gpus = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 4:
                continue

            try:
                device_id = int(parts[0])
                name = parts[1]
                memory_mb = int(float(parts[2]))

                # Parse compute capability (e.g., "8.0")
                cap_parts = parts[3].split('.')
                compute_cap = (int(cap_parts[0]), int(cap_parts[1]))

                gpus.append(GPUInfo(
                    device_id=device_id,
                    name=name,
                    memory_total=memory_mb,
                    compute_capability=compute_cap
                ))

            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse GPU info: {line}: {e}")
                continue

        return gpus

    except FileNotFoundError:
        return []
    except subprocess.TimeoutExpired:
        logger.warning("nvidia-smi timeout")
        return []
    except Exception as e:
        logger.warning(f"nvidia-smi detection failed: {e}")
        return []


def _detect_nvlink() -> bool:
    """
    Detect NVLink connectivity.

    Returns:
        True if NVLink detected, False otherwise
    """
    try:
        result = subprocess.run(
            ['nvidia-smi', 'nvlink', '--status'],
            capture_output=True,
            text=True,
            timeout=2.0
        )

        # If command succeeds and mentions "Active", NVLink is available
        if result.returncode == 0:
            return 'Active' in result.stdout

        return False

    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        logger.warning("nvlink status timeout")
        return False
    except Exception as e:
        logger.debug(f"NVLink detection failed: {e}")
        return False


def _detect_cupy_gpus() -> List[GPUInfo]:
    """
    Detect GPUs via CuPy.

    Returns:
        List of GPUInfo, or empty if detection failed
    """
    try:
        import cupy as cp

        device_count = cp.cuda.runtime.getDeviceCount()
        gpus = []

        for device_id in range(device_count):
            with cp.cuda.Device(device_id):
                props = cp.cuda.runtime.getDeviceProperties(device_id)

                # Extract info
                name = props['name'].decode('utf-8')
                memory_mb = props['totalGlobalMem'] // (1024 * 1024)
                compute_cap = (props['major'], props['minor'])

                gpus.append(GPUInfo(
                    device_id=device_id,
                    name=name,
                    memory_total=memory_mb,
                    compute_capability=compute_cap
                ))

        return gpus

    except ImportError:
        return []
    except Exception as e:
        logger.debug(f"CuPy detection failed: {e}")
        return []


def _invalidate_cache() -> None:
    """Invalidate GPU topology cache (for testing)."""
    GPUTopologyCache._instance = None


class GPUTopologyCache:
    """
    Singleton cache for GPU topology information.

    Provides fast (<1μs) cached reads of GPU hardware configuration.
    Manual refresh updates when hardware changes (e.g., GPU hotplug).

    Example:
        cache = GPUTopologyCache()
        topo = cache.get_topology()

        if topo.gpus:
            print(f"Found {len(topo.gpus)} GPUs")
            for gpu in topo.gpus:
                print(f"  {gpu.device_id}: {gpu.name}")
    """

    _instance: Optional['GPUTopologyCache'] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize cache (only once)."""
        if self._initialized:
            return

        self._initialized = True

        # Cached topology (guarded by lock for writes)
        self._topology_lock = threading.Lock()
        self._topology: Optional[TopologyInfo] = None

        logger.info("GPU topology cache initialized")

    def get_topology(self) -> TopologyInfo:
        """
        Get cached GPU topology.

        Performs detection on first call, then returns cached result.

        Returns:
            TopologyInfo with current hardware state

        Performance:
            <1μs for cached reads
            10-100ms for initial detection
        """
        # Fast path: read cached value
        topology = self._topology

        if topology is not None:
            return topology

        # Slow path: detect topology
        with self._topology_lock:
            # Double-check after acquiring lock
            if self._topology is not None:
                return self._topology

            # Perform detection with error handling
            try:
                self._topology = _detect_gpu_topology()

                logger.info(
                    f"GPU topology detected: {len(self._topology.gpus)} GPU(s), "
                    f"NVLink: {self._topology.nvlink_enabled}"
                )
            except Exception as e:
                # On detection failure, use safe default
                logger.error(f"GPU topology detection failed: {e}")
                self._topology = TopologyInfo(
                    gpus=[],
                    nvlink_enabled=False,
                    cached_at=time.time()
                )

            return self._topology

    def refresh(self):
        """
        Refresh topology (expensive operation).

        Performs actual hardware detection and updates cache.
        Should be called sparingly (e.g., after GPU hotplug event).

        Performance:
            10-100ms (subprocess calls)
        """
        with self._topology_lock:
            self._topology = _detect_gpu_topology()

        logger.info(
            f"GPU topology refreshed: {len(self._topology.gpus)} GPU(s), "
            f"NVLink: {self._topology.nvlink_enabled}"
        )

    def get_gpu_count(self) -> int:
        """
        Get number of available GPUs.

        Returns:
            Number of GPUs detected

        Performance:
            <1μs (cached read)
        """
        topology = self.get_topology()
        return len(topology.gpus)

    def has_nvlink(self) -> bool:
        """
        Check if NVLink is available.

        Returns:
            True if NVLink detected, False otherwise

        Performance:
            <1μs (cached read)
        """
        topology = self.get_topology()
        return topology.nvlink_enabled


# Global instance
_global_cache: Optional[GPUTopologyCache] = None


def get_gpu_topology_cache() -> GPUTopologyCache:
    """
    Get global GPU topology cache instance.

    Returns:
        Singleton GPUTopologyCache
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = GPUTopologyCache()
    return _global_cache
