"""
Performance Configuration Schema (Task 5.1)

Per perf_fixes3.md Section 5.8: Runtime configuration knobs for
performance tuning and fallback behavior.

Author: Epochly Development Team
Created: 2025-11-15
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class FallbackConfig:
    """Configuration for fallback executor selection."""

    # Default workload type assumption when analyzer unavailable
    default_workload_type: str = "cpu_bound"  # 'cpu_bound', 'io_bound', 'mixed'

    # CPU intensity threshold for CPU-bound classification
    cpu_intensity_threshold: float = 0.6

    # I/O wait ratio threshold for I/O-bound classification
    io_wait_threshold: float = 0.4

    # GPU suitability threshold for GPU fallback
    gpu_suitability_threshold: float = 0.6


@dataclass
class ProcessPoolConfig:
    """Configuration for process pool executors."""

    # Maximum workers per NUMA node
    max_workers_per_numa: Optional[int] = None

    # Context method ('fork', 'forkserver', 'spawn', 'auto')
    context_method: str = "auto"

    # Shared memory threshold for zero-copy (bytes)
    shared_memory_threshold: int = 1024 * 1024  # 1MB

    # =============================================================
    # Level 3 ProcessPool Dispatch Thresholds (Dec 2025 Performance Fix)
    # =============================================================
    # CRITICAL: ProcessPool dispatch has ~50-200ms overhead per call.
    # Dispatching small workloads causes catastrophic regressions.
    # These thresholds prevent ProcessPool dispatch for unsuitable workloads.

    # Minimum estimated work time (ms) to enable Level 3 ProcessPool dispatch.
    # Workloads below this threshold stay at Level 2 (JIT only).
    # Default 2000ms based on measured ~1700ms IPC overhead.
    level3_min_work_ms: float = 2000.0

    # Minimum total iterations to enable parallelized loop dispatch.
    # Tiny loops have too much per-chunk overhead.
    level3_min_iterations: int = 100

    # Override via environment variable EPOCHLY_LEVEL3_MIN_WORK_MS
    # Override via environment variable EPOCHLY_LEVEL3_MIN_ITERATIONS


@dataclass
class SharedMemoryConfig:
    """Configuration for shared memory pools."""

    # Initial pool size in MB
    initial_pool_mb: int = 64

    # Enable adaptive sizing
    adaptive_sizing: bool = False

    # Growth factor when pool full
    growth_factor: float = 2.0

    # Utilization threshold for expansion (0-1)
    expand_threshold: float = 0.8

    # Utilization threshold for shrinkage (0-1)
    shrink_threshold: float = 0.3


@dataclass
class ThreadPoolConfig:
    """Configuration for thread pool executors."""

    # Enable dynamic scaling
    dynamic_scaling: bool = False  # Disabled per Task 3.2 (stable pool)

    # Oversubscription factor for CPU-bound
    cpu_oversubscription: float = 1.25  # ceil(cores × 1.25)

    # Oversubscription factor for I/O-bound
    io_oversubscription: float = 2.0  # 2× cores


@dataclass
class AsyncIOConfig:
    """Configuration for async I/O executor."""

    # Maximum concurrent I/O operations
    max_concurrent: int = 100

    # Enable async executor for I/O workloads
    enabled: bool = True

    # Minimum I/O wait ratio to use async
    min_io_wait_ratio: float = 0.5


@dataclass
class PerformanceConfig:
    """
    Master performance configuration.

    Task 5.1: Extends runtime config with knobs from perf_fixes3.md.
    """

    fallback: FallbackConfig = field(default_factory=FallbackConfig)
    process_pool: ProcessPoolConfig = field(default_factory=ProcessPoolConfig)
    shared_memory: SharedMemoryConfig = field(default_factory=SharedMemoryConfig)
    thread_pool: ThreadPoolConfig = field(default_factory=ThreadPoolConfig)
    async_io: AsyncIOConfig = field(default_factory=AsyncIOConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'fallback': self.fallback.__dict__,
            'process_pool': self.process_pool.__dict__,
            'shared_memory': self.shared_memory.__dict__,
            'thread_pool': self.thread_pool.__dict__,
            'async_io': self.async_io.__dict__
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceConfig':
        """Load from dictionary."""
        return cls(
            fallback=FallbackConfig(**data.get('fallback', {})),
            process_pool=ProcessPoolConfig(**data.get('process_pool', {})),
            shared_memory=SharedMemoryConfig(**data.get('shared_memory', {})),
            thread_pool=ThreadPoolConfig(**data.get('thread_pool', {})),
            async_io=AsyncIOConfig(**data.get('async_io', {}))
        )


# Default configuration instance
DEFAULT_PERFORMANCE_CONFIG = PerformanceConfig()
