"""
Async GPU Detection (SPEC2 Task 11)

Prevents GPU detection from blocking CPU-focused workloads.

Features:
- Background detection thread with low priority
- Negative results cached with TTL
- CPU workloads don't wait for GPU probe completion
- Periodic re-probing for hotplug GPUs

Performance:
- CPU workloads start immediately
- GPU probe overhead deferred to background
- Negative cache reduces repeated expensive probes
"""

import threading
import time
import logging
from typing import Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class GPUCapability:
    """GPU capability result."""

    available: bool
    device_count: int
    total_memory_mb: int
    driver_version: str
    timestamp: float


class AsyncGPUDetector(threading.Thread):
    """
    Background GPU detection with caching.

    Runs GPU probes in low-priority background thread.
    Caches negative results to avoid repeated expensive checks.

    Example:
        detector = AsyncGPUDetector()
        detector.start()

        # Non-blocking check
        gpu_available = detector.is_available()  # Fast

        # Get cached result
        capability = detector.get_capability()  # Fast

        detector.stop()
    """

    def __init__(self, negative_cache_ttl: float = 300.0, positive_cache_ttl: float = 3600.0):
        """
        Initialize async GPU detector.

        Args:
            negative_cache_ttl: Cache duration for negative results (5 min default)
            positive_cache_ttl: Cache duration for positive results (1 hour default)
        """
        super().__init__(daemon=True, name="AsyncGPUDetector")

        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Cache configuration
        self._negative_ttl = negative_cache_ttl
        self._positive_ttl = positive_cache_ttl
        self._poll_interval = 60.0  # Check every 60 seconds

        # Cached capability
        self._cached_capability: Optional[GPUCapability] = None
        self._cache_valid_until: float = 0.0

        # Statistics
        self._probe_count = 0
        self._cache_hits = 0

        logger.info(f"AsyncGPUDetector initialized (negative TTL: {negative_cache_ttl}s)")

    def run(self) -> None:
        """Background loop for GPU detection."""
        logger.info("AsyncGPUDetector started")

        # Initial probe
        self._probe_gpu()

        # Periodic re-probing
        while not self._stop_event.wait(timeout=self._poll_interval):
            # Check if cache still valid
            if time.time() < self._cache_valid_until:
                continue  # Cache still valid, skip probe

            # Re-probe GPU
            self._probe_gpu()

        logger.info(f"AsyncGPUDetector stopped (probes: {self._probe_count}, hits: {self._cache_hits})")

    def _probe_gpu(self) -> None:
        """
        Probe for GPU availability (expensive operation).

        Runs in background thread - safe to be slow.
        """
        try:
            # Try to detect GPU
            capability = self._detect_gpu_capability()

            with self._lock:
                self._cached_capability = capability
                self._probe_count += 1

                # Set cache expiry based on result
                if capability.available:
                    ttl = self._positive_ttl
                    logger.info(
                        f"GPU detected: {capability.device_count} devices, "
                        f"{capability.total_memory_mb}MB (driver: {capability.driver_version})"
                    )
                else:
                    ttl = self._negative_ttl
                    logger.debug("No GPU detected (cached for {ttl}s)")

                self._cache_valid_until = time.time() + ttl

        except Exception as e:
            logger.warning(f"GPU detection failed: {e}")

            # Cache negative result on error
            with self._lock:
                self._cached_capability = GPUCapability(
                    available=False,
                    device_count=0,
                    total_memory_mb=0,
                    driver_version="",
                    timestamp=time.time()
                )
                self._cache_valid_until = time.time() + self._negative_ttl

    def _detect_gpu_capability(self) -> GPUCapability:
        """
        Detect GPU capability (blocking, expensive).

        Returns:
            GPUCapability with detection results
        """
        # Try NVIDIA CUDA
        try:
            import cupy
            device_count = cupy.cuda.runtime.getDeviceCount()

            if device_count > 0:
                # Get info from first device
                cupy.cuda.Device(0).use()
                props = cupy.cuda.runtime.getDeviceProperties(0)
                driver_version = str(cupy.cuda.runtime.driverGetVersion())

                total_memory_mb = props['totalGlobalMem'] // (1024 * 1024)

                return GPUCapability(
                    available=True,
                    device_count=device_count,
                    total_memory_mb=total_memory_mb,
                    driver_version=driver_version,
                    timestamp=time.time()
                )

        except (ImportError, Exception) as e:
            logger.debug(f"CUDA detection failed: {e}")

        # No GPU found
        return GPUCapability(
            available=False,
            device_count=0,
            total_memory_mb=0,
            driver_version="",
            timestamp=time.time()
        )

    def is_available(self) -> bool:
        """
        Check if GPU is available (fast, uses cache).

        Returns:
            True if GPU available, False otherwise
        """
        with self._lock:
            if self._cached_capability is None:
                # No result yet - assume no GPU
                return False

            self._cache_hits += 1
            return self._cached_capability.available

    def get_capability(self) -> Optional[GPUCapability]:
        """
        Get cached GPU capability.

        Returns:
            GPUCapability if probed, None if not yet available
        """
        with self._lock:
            if self._cached_capability:
                self._cache_hits += 1
            return self._cached_capability

    def stop(self, timeout: float = 2.0) -> bool:
        """
        Stop detector and wait for shutdown.

        Args:
            timeout: Maximum wait time

        Returns:
            True if stopped cleanly
        """
        logger.info("Stopping AsyncGPUDetector...")
        self._stop_event.set()

        self.join(timeout=timeout)

        if self.is_alive():
            logger.warning(f"AsyncGPUDetector did not stop within {timeout}s")
            return False

        return True

    def get_stats(self) -> dict:
        """Get detector statistics."""
        with self._lock:
            return {
                'probe_count': self._probe_count,
                'cache_hits': self._cache_hits,
                'cache_valid': time.time() < self._cache_valid_until,
                'gpu_available': self._cached_capability.available if self._cached_capability else None
            }
