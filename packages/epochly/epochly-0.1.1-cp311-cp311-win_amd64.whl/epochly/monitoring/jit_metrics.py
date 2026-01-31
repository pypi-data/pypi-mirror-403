"""
JIT Compilation Metrics Collection for Benchmarking

Tracks JIT compilation statistics to validate Epochly's JIT features:
- Cache hit/miss ratio
- Cold start (compilation) vs warm start (cached) performance
- Compilation time per function
- Cache evictions and size

This module provides benchmarking-specific metrics for measuring JIT
compilation effectiveness separate from general runtime monitoring.

Author: Epochly Development Team
Date: November 19, 2025
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from collections import defaultdict


@dataclass
class JITMetrics:
    """
    Metrics for JIT compilation performance.

    Attributes:
        cache_hits: Number of cache hits (function found in cache)
        cache_misses: Number of cache misses (function had to be compiled)
        cache_evictions: Number of cache evictions (function removed from cache)
        cold_start_compilation_ms: Compilation time per cache miss (milliseconds)
        warm_start_retrieval_ms: Cache retrieval time per hit (milliseconds)
        compiled_functions: Number of unique functions compiled
        cache_size_bytes: Current cache size in bytes
    """
    cache_hits: int
    cache_misses: int
    cache_evictions: int
    cold_start_compilation_ms: List[float]
    warm_start_retrieval_ms: List[float]
    compiled_functions: int
    cache_size_bytes: int

    @property
    def cache_hit_rate(self) -> float:
        """
        Cache hit ratio (0.0 to 1.0).

        Returns:
            Fraction of accesses that were cache hits
        """
        total_accesses = self.cache_hits + self.cache_misses
        if total_accesses == 0:
            return 0.0
        return self.cache_hits / total_accesses

    @property
    def cold_start_mean_ms(self) -> float:
        """
        Mean compilation time for cold starts.

        Returns:
            Average time in milliseconds to compile a function
        """
        if not self.cold_start_compilation_ms:
            return 0.0
        return sum(self.cold_start_compilation_ms) / len(self.cold_start_compilation_ms)

    @property
    def warm_start_mean_ms(self) -> float:
        """
        Mean cache retrieval time for warm starts.

        Returns:
            Average time in milliseconds to load from cache
        """
        if not self.warm_start_retrieval_ms:
            return 0.0
        return sum(self.warm_start_retrieval_ms) / len(self.warm_start_retrieval_ms)

    @property
    def speedup_from_cache(self) -> float:
        """
        Speedup from caching (cold_start / warm_start).

        Target from architecture spec: ~400× speedup

        Returns:
            Ratio of cold start time to warm start time
        """
        if self.warm_start_mean_ms == 0.0:
            return 1.0
        return self.cold_start_mean_ms / self.warm_start_mean_ms


class JITTracker:
    """
    Track JIT compilation metrics during benchmark execution.

    Monitors cache hits/misses, compilation times, and cache behavior to
    validate that Epochly's JIT compilation is working effectively.

    Usage:
        tracker = JITTracker()
        tracker.start_tracking()

        # Run benchmark (JIT events recorded via callbacks)
        # func_a compiles: record_cache_miss("func_a", 120.0)
        # func_a cached:   record_cache_hit("func_a", 0.5)

        tracker.stop_tracking()
        metrics = tracker.get_metrics()

        print(f"Cache hit rate: {metrics.cache_hit_rate:.1%}")
        print(f"Cache speedup: {metrics.speedup_from_cache:.0f}×")

    Integration Points:
        - JITManager: Reports compilation events via callbacks
        - JITArtifactCache: Reports cache hits/misses/evictions
        - Auto-profiler: Triggers compilation on hot path detection
    """

    def __init__(self):
        """Initialize JIT compilation tracker."""
        # Event counters
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._cache_evictions: int = 0

        # Timing data
        self._cold_compilation_times: List[float] = []
        self._warm_retrieval_times: List[float] = []

        # Function tracking
        self._compiled_functions: Set[str] = set()

        # Session metadata
        self._start_time: Optional[float] = None

        # Thread safety
        self._lock = threading.Lock()

    def start_tracking(self) -> None:
        """
        Begin tracking JIT metrics.

        Resets all counters and starts new tracking session.

        Thread Safety:
            Safe to call from any thread.
        """
        self._start_time = time.time()
        with self._lock:
            self._reset_counters()

    def stop_tracking(self) -> None:
        """
        Stop tracking and finalize metrics.

        Thread Safety:
            Safe to call from any thread.
        """
        # All data already collected via callbacks
        pass

    def _reset_counters(self) -> None:
        """
        Reset all counters for new tracking session.

        Note: Caller must hold self._lock.
        """
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_evictions = 0
        self._cold_compilation_times.clear()
        self._warm_retrieval_times.clear()
        self._compiled_functions.clear()

    def record_cache_hit(self, function_id: str, retrieval_time_ms: float) -> None:
        """
        Record JIT cache hit event.

        Args:
            function_id: Unique identifier for function (e.g., module.function)
            retrieval_time_ms: Time to retrieve from cache in milliseconds

        Thread Safety:
            Safe to call from any thread with proper locking.
        """
        with self._lock:
            self._cache_hits += 1
            self._warm_retrieval_times.append(retrieval_time_ms)

    def record_cache_miss(self, function_id: str, compilation_time_ms: float) -> None:
        """
        Record JIT cache miss and compilation event.

        Args:
            function_id: Unique identifier for function
            compilation_time_ms: Time to compile function in milliseconds

        Thread Safety:
            Safe to call from any thread with proper locking.
        """
        with self._lock:
            self._cache_misses += 1
            self._cold_compilation_times.append(compilation_time_ms)
            self._compiled_functions.add(function_id)

    def record_cache_eviction(self, function_id: str) -> None:
        """
        Record cache eviction event.

        Args:
            function_id: Unique identifier for evicted function

        Thread Safety:
            Safe to call from any thread with proper locking.
        """
        with self._lock:
            self._cache_evictions += 1

    def get_metrics(self) -> JITMetrics:
        """
        Compute final JIT metrics.

        Returns:
            JITMetrics with statistical summary of JIT compilation

        Thread Safety:
            Safe to call while tracking is active. Returns snapshot of current state.
        """
        # Query actual cache size from JIT artifact store
        cache_size_bytes = self._get_cache_size_bytes()

        with self._lock:
            return JITMetrics(
                cache_hits=self._cache_hits,
                cache_misses=self._cache_misses,
                cache_evictions=self._cache_evictions,
                cold_start_compilation_ms=self._cold_compilation_times.copy(),
                warm_start_retrieval_ms=self._warm_retrieval_times.copy(),
                compiled_functions=len(self._compiled_functions),
                cache_size_bytes=cache_size_bytes
            )

    def _get_cache_size_bytes(self) -> int:
        """
        Get actual JIT cache size in bytes from artifact store.

        Calculates total size by summing code_bytes from all compiled artifacts.

        Returns:
            Total cache size in bytes
        """
        try:
            from ..jit.artifact_store import get_artifact_store
            store = get_artifact_store()

            # Calculate total size from all artifacts
            total_size = 0
            with store._lock:
                for artifact in store._artifacts.values():
                    # Sum up the code_bytes from each artifact
                    if artifact.code_bytes:
                        total_size += len(artifact.code_bytes)

            return total_size

        except ImportError:
            # JIT artifact store not available
            return 0
        except Exception as e:
            # Any error accessing the store - log for debugging
            import logging
            logging.getLogger(__name__).debug(f"Failed to get cache size from artifact store: {e}")
            return 0
