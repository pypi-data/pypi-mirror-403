"""
Epochly JIT Compilation Base Classes

Defines base interfaces and data structures for JIT compilation backends.
Provides standardized compilation result format and backend abstraction.

Author: Epochly Development Team
"""

from __future__ import annotations

import enum
import hashlib
import time
import logging
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class JITBackend(enum.Enum):
    """Supported JIT compilation backends (Multi-JIT Strategy 2025)."""
    NUMBA = "numba"        # Numba JIT (Python 3.10+ numerical workloads)
    NATIVE = "native"      # Python 3.13+ native JIT (general Python)
    PYSTON = "pyston"      # Pyston-Lite (Python 3.7-3.10 ONLY general optimization)
    AUTO = "auto"          # Auto-select best backend


class CompilationStatus(enum.Enum):
    """Status of JIT compilation attempt (Phase 2.4 enhanced states)."""
    NOT_COMPILED = "not_compiled"     # Function not yet compiled
    PENDING = "pending"                # Queued for compilation
    COMPILING = "compiling"            # Compilation in progress
    COMPILED = "compiled"              # Successfully compiled
    CACHED = "cached"                  # Retrieved from cache (previously compiled)
    BENCHMARKING = "benchmarking"      # Benchmarking in progress (Phase 2.4)
    FAILED = "failed"                  # Compilation failed
    UNAVAILABLE = "unavailable"        # Backend not available
    SKIPPED = "skipped"                # Skipped (not suitable for JIT)


@dataclass
class FunctionProfile:
    """
    Profile of a function for JIT compilation decisions.

    Contains analysis results used by JITSelector to determine
    the most appropriate backend for compilation.
    """
    function_name: str = ""
    source_lines: int = 0
    has_loops: bool = False
    has_numpy_usage: bool = False
    has_numerical_ops: bool = False
    has_list_comprehensions: bool = False
    complexity_score: int = 0
    loop_depth: int = 0
    has_recursion: bool = False
    is_generator: bool = False
    is_async: bool = False
    jit_compatible: bool = True
    call_count: int = 0  # Number of times the function has been called

    # Internal analyzer attributes (set dynamically)
    _analyzer_attrs: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for serialization."""
        return {
            'function_name': self.function_name,
            'source_lines': self.source_lines,
            'has_loops': self.has_loops,
            'has_numpy_usage': self.has_numpy_usage,
            'has_numerical_ops': self.has_numerical_ops,
            'has_list_comprehensions': self.has_list_comprehensions,
            'complexity_score': self.complexity_score,
            'loop_depth': self.loop_depth,
            'has_recursion': self.has_recursion,
            'is_generator': self.is_generator,
            'is_async': self.is_async,
            'jit_compatible': self.jit_compatible,
            'call_count': self.call_count
        }


@dataclass
class JITCompilationResult:
    """Result of a JIT compilation attempt."""

    backend: JITBackend
    status: CompilationStatus
    compilation_time_ms: float
    function_name: str
    source_hash: str

    # Optional fields
    compiled_function: Optional[Callable] = None
    speedup_ratio: Optional[float] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    compilation_warnings: List[str] = field(default_factory=list)

    # Phase 2.4: Additional metadata
    compiled_at: Optional[float] = None  # Timestamp of compilation
    benchmark_time_ms: Optional[float] = None  # Time spent benchmarking

    @property
    def is_successful(self) -> bool:
        """Check if compilation was successful (either freshly compiled or cached)."""
        return self.status in (CompilationStatus.COMPILED, CompilationStatus.CACHED) and self.compiled_function is not None

    @property
    def has_performance_benefit(self) -> bool:
        """Check if compiled version has measurable performance benefit (>10% speedup)."""
        return self.is_successful and self.speedup_ratio is not None and self.speedup_ratio > 1.1

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'backend': self.backend.value,
            'status': self.status.value,
            'compilation_time_ms': self.compilation_time_ms,
            'function_name': self.function_name,
            'source_hash': self.source_hash,
            'speedup_ratio': self.speedup_ratio,
            'error_message': self.error_message,
            'error_type': self.error_type,
            'compilation_warnings': self.compilation_warnings,
            'compiled_at': self.compiled_at,
            'benchmark_time_ms': self.benchmark_time_ms
        }


class JITCompiler:
    """
    Base class for JIT compilation backends.

    Provides standardized interface for different JIT compilation strategies
    and handles common operations like caching and benchmarking.
    """

    def __init__(self, backend: JITBackend, enable_caching: bool = True):
        """
        Initialize JIT compiler.

        Args:
            backend: JIT backend type
            enable_caching: Whether to cache compiled functions
        """
        self.backend = backend
        self.enable_caching = enable_caching

        # Thread safety lock for cache and counters
        self._lock = threading.Lock()

        # Compilation cache: source_hash -> compiled_function
        self._compilation_cache: Dict[str, Callable] = {}

        # Statistics
        self._compilation_attempts = 0
        self._compilation_successes = 0
        self._compilation_failures = 0
        self._total_compilation_time_ms = 0.0
        self._cache_hits = 0

    @property
    def compilation_cache(self) -> Dict[str, Callable]:
        """Get the compilation cache (read-only access)."""
        return self._compilation_cache

    @property
    def total_compilations(self) -> int:
        """Get total number of compilation attempts."""
        return self._compilation_attempts

    @property
    def successful_compilations(self) -> int:
        """Get number of successful compilations."""
        return self._compilation_successes

    @property
    def total_compilation_time_ms(self) -> float:
        """Get total compilation time in milliseconds."""
        return self._total_compilation_time_ms

    @property
    def cache_hits(self) -> int:
        """Get number of cache hits."""
        return self._cache_hits

    def _get_function_hash(self, func: Callable) -> str:
        """Alias for _compute_source_hash for backwards compatibility."""
        return self._compute_source_hash(func)

    def compile_function(self, func: Callable, force_recompile: bool = False) -> JITCompilationResult:
        """
        Compile a function using this backend.

        Thread-safe compilation with caching and error handling.
        Uses lock to ensure only one thread compiles a given function
        while others wait and get the cached result.

        Args:
            func: Function to compile
            force_recompile: If True, bypass cache and recompile

        Returns:
            JITCompilationResult with compilation outcome
        """
        func_name = getattr(func, '__name__', str(func))

        # Generate source hash for caching
        source_hash = self._compute_source_hash(func)

        # Check if backend is available
        is_backend_available = getattr(self, 'is_backend_available', None)
        if is_backend_available is False or (callable(self.is_available) and not self.is_available()):
            return JITCompilationResult(
                backend=self.backend,
                status=CompilationStatus.UNAVAILABLE,
                compilation_time_ms=0.0,
                function_name=func_name,
                source_hash=source_hash,
                compiled_function=None,
                error_message=f"{self.backend.value} backend not available"
            )

        # Thread-safe compilation: lock ensures only one thread compiles a given function
        with self._lock:
            # Check cache (unless force_recompile)
            if self.enable_caching and not force_recompile and source_hash in self._compilation_cache:
                self._cache_hits += 1
                logger.debug(f"Using cached compilation for {func_name}")
                return JITCompilationResult(
                    backend=self.backend,
                    status=CompilationStatus.CACHED,
                    compilation_time_ms=0.0,
                    function_name=func_name,
                    source_hash=source_hash,
                    compiled_function=self._compilation_cache[source_hash]
                )

            # Count this as an actual compilation attempt (not cache hit)
            self._compilation_attempts += 1

            # Perform compilation inside lock to ensure only one thread compiles
            start_time = time.perf_counter_ns()
            try:
                result = self._compile_function_impl(func, source_hash)
            except Exception as e:
                # Handle errors in _compile_function_impl
                compilation_time_ms = (time.perf_counter_ns() - start_time) / 1_000_000
                error_type = type(e).__name__
                self._compilation_failures += 1
                self._total_compilation_time_ms += compilation_time_ms
                return JITCompilationResult(
                    backend=self.backend,
                    status=CompilationStatus.FAILED,
                    compilation_time_ms=compilation_time_ms,
                    function_name=func_name,
                    source_hash=source_hash,
                    compiled_function=None,
                    error_message=str(e),
                    error_type=error_type
                )

            compilation_time_ms = (time.perf_counter_ns() - start_time) / 1_000_000

            result.compilation_time_ms = compilation_time_ms
            result.compiled_at = time.time()
            self._total_compilation_time_ms += compilation_time_ms

            # Update statistics
            if result.is_successful:
                self._compilation_successes += 1
                # Cache successful compilations
                if self.enable_caching:
                    self._compilation_cache[source_hash] = result.compiled_function
            else:
                self._compilation_failures += 1

            return result

    def _compile_function_impl(self, func: Callable, source_hash: str) -> JITCompilationResult:
        """
        Backend-specific compilation implementation.

        Args:
            func: Function to compile
            source_hash: Hash of function source code

        Returns:
            JITCompilationResult with compilation outcome
        """
        raise NotImplementedError("Subclasses must implement _compile_function_impl")

    def _compute_source_hash(self, func: Callable) -> str:
        """
        Compute hash of function source code for caching.

        Args:
            func: Function to hash

        Returns:
            SHA-256 hash of function source, or builtin_ prefix for built-ins
        """
        try:
            import inspect
            source = inspect.getsource(func)
            return hashlib.sha256(source.encode()).hexdigest()
        except (OSError, TypeError):
            # Can't get source (e.g., built-in function)
            # Check if it has __code__ attribute (user-defined functions)
            if hasattr(func, '__code__'):
                import marshal
                code_bytes = marshal.dumps(func.__code__)
                return hashlib.sha256(code_bytes).hexdigest()
            else:
                # Built-in function without __code__ - use name-based hash
                func_name = getattr(func, '__name__', str(func))
                return f"builtin_{hashlib.sha256(func_name.encode()).hexdigest()[:16]}"

    def clear_cache(self) -> None:
        """Clear compilation cache."""
        self._compilation_cache.clear()
        logger.info(f"{self.backend.value} compilation cache cleared")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get compilation statistics.

        Returns:
            Dictionary with compilation metrics
        """
        success_rate = (
            self._compilation_successes / self._compilation_attempts
            if self._compilation_attempts > 0 else 0.0
        )
        return {
            'backend': self.backend.value,
            'available': self.is_available() if callable(self.is_available) else False,
            # Primary key names (expected by tests)
            'total_compilations': self._compilation_attempts,
            'successful_compilations': self._compilation_successes,
            # Legacy key names (for backwards compatibility)
            'compilation_attempts': self._compilation_attempts,
            'compilation_successes': self._compilation_successes,
            'compilation_failures': self._compilation_failures,
            'success_rate': success_rate,
            'success_rate_percent': success_rate * 100.0,
            'total_compilation_time_ms': self._total_compilation_time_ms,
            'average_compilation_time_ms': (
                self._total_compilation_time_ms / self._compilation_attempts
                if self._compilation_attempts > 0 else 0.0
            ),
            'cache_hits': self._cache_hits,
            'cached_functions': len(self._compilation_cache),
            'cache_hit_rate': (
                self._cache_hits / self._compilation_attempts
                if self._compilation_attempts > 0 else 0.0
            )
        }

    def is_available(self) -> bool:
        """
        Check if this JIT backend is available.

        Subclasses MUST override this method to provide their specific
        availability check.

        Returns:
            True if backend can be used, False otherwise

        Raises:
            NotImplementedError: If subclass does not override this method
        """
        raise NotImplementedError("Subclasses must implement is_available()")

    def benchmark_function(self, original_func: Callable, compiled_func: Callable,
                          *args, **kwargs) -> Optional[float]:
        """
        Benchmark compiled function against original to measure speedup.

        TIME-BUDGETED BENCHMARKING (Dec 2025 P0 Fix):
        - First probes function execution time with 1 call
        - Expensive functions (>500ms): Skip benchmark, assume 1.5x speedup
        - Medium functions (>100ms): Use reduced iterations (3 instead of 10)
        - Fast functions (<100ms): Use full benchmark (10 iterations)
        - Total benchmark time capped at ~2 seconds max

        CRITICAL: Disables auto-profiling during benchmarking to prevent
        recursive compilation and script re-execution bugs.

        Args:
            original_func: Original function
            compiled_func: Compiled function
            *args: Test arguments
            **kwargs: Test keyword arguments

        Returns:
            Speedup ratio (compiled vs original) or None if benchmark fails
        """
        # Time budget constants (configurable via environment)
        import os
        MAX_BENCHMARK_TIME_MS = float(os.environ.get('EPOCHLY_JIT_MAX_BENCHMARK_MS', '2000'))
        EXPENSIVE_THRESHOLD_MS = float(os.environ.get('EPOCHLY_JIT_EXPENSIVE_THRESHOLD_MS', '500'))
        MEDIUM_THRESHOLD_MS = float(os.environ.get('EPOCHLY_JIT_MEDIUM_THRESHOLD_MS', '100'))

        try:
            # CRITICAL FIX: Disable auto-profiling during benchmarking
            # This prevents recursive JIT compilation that causes script re-execution
            profiler_disabled = False
            auto_profiler = None

            try:
                from ..profiling.auto_profiler import get_auto_profiler
                auto_profiler = get_auto_profiler()
                if auto_profiler and auto_profiler._enabled:
                    auto_profiler.disable()
                    profiler_disabled = True
                    logger.debug("Disabled auto-profiler for benchmarking")
            except Exception as e:
                logger.debug(f"Could not disable auto-profiler: {e}")

            try:
                # PHASE 1: Probe function execution time (single call)
                probe_start = time.perf_counter_ns()
                original_func(*args, **kwargs)
                probe_time_ns = time.perf_counter_ns() - probe_start
                probe_time_ms = probe_time_ns / 1_000_000

                # PHASE 2: Determine benchmark strategy based on probe time
                if probe_time_ms > EXPENSIVE_THRESHOLD_MS:
                    # Expensive function (>500ms): Skip benchmark, assume speedup
                    # Running 26 iterations would take 13+ seconds - unacceptable
                    logger.info(
                        f"Skipping benchmark for expensive function "
                        f"(probe: {probe_time_ms:.1f}ms > {EXPENSIVE_THRESHOLD_MS}ms threshold). "
                        f"Assuming 1.5x speedup."
                    )
                    return 1.5  # Conservative assumed speedup

                elif probe_time_ms > MEDIUM_THRESHOLD_MS:
                    # Medium function (100-500ms): Use reduced iterations
                    # Stay within ~2s total: 3 warmup + 3 original + 3 compiled = 9 calls
                    warmup_iters = 1
                    benchmark_iters = 3
                    logger.debug(
                        f"Using reduced benchmark iterations for medium function "
                        f"(probe: {probe_time_ms:.1f}ms, iters: {benchmark_iters})"
                    )
                else:
                    # Fast function (<100ms): Use full benchmark
                    warmup_iters = 3
                    benchmark_iters = 10
                    logger.debug(
                        f"Using full benchmark for fast function "
                        f"(probe: {probe_time_ms:.1f}ms, iters: {benchmark_iters})"
                    )

                # PHASE 3: Warm up (already did 1 call for probe)
                for _ in range(warmup_iters):
                    original_func(*args, **kwargs)
                    compiled_func(*args, **kwargs)

                # PHASE 4: Benchmark original
                original_times = []
                for _ in range(benchmark_iters):
                    start = time.perf_counter_ns()
                    original_func(*args, **kwargs)
                    original_times.append(time.perf_counter_ns() - start)

                # PHASE 5: Benchmark compiled
                compiled_times = []
                for _ in range(benchmark_iters):
                    start = time.perf_counter_ns()
                    compiled_func(*args, **kwargs)
                    compiled_times.append(time.perf_counter_ns() - start)

                # Calculate averages
                avg_original = sum(original_times) / len(original_times)
                avg_compiled = sum(compiled_times) / len(compiled_times)

                speedup = avg_original / avg_compiled if avg_compiled > 0 else None

                # Log benchmark summary
                total_calls = 1 + (warmup_iters * 2) + (benchmark_iters * 2)  # probe + warmup + benchmark
                estimated_time_ms = total_calls * probe_time_ms
                logger.debug(
                    f"Benchmark complete: {speedup:.2f}x speedup, "
                    f"{total_calls} calls, ~{estimated_time_ms:.0f}ms total"
                )

                return speedup

            finally:
                # CRITICAL: Re-enable auto-profiler after benchmarking
                if profiler_disabled and auto_profiler:
                    auto_profiler.enable()
                    logger.debug("Re-enabled auto-profiler after benchmarking")

        except Exception as e:
            logger.debug(f"Benchmarking failed: {e}")
            return None

    def __del__(self):
        """Cleanup JIT compiler resources."""
        try:
            # Clear compilation cache
            self._compilation_cache.clear()
        except Exception:
            pass  # Ignore cleanup errors during interpreter shutdown


__all__ = [
    'JITBackend',
    'CompilationStatus',
    'FunctionProfile',
    'JITCompilationResult',
    'JITCompiler'
]
