"""
Epochly Profiler - Automatic Loop Detection and Parallelization

Implements transparent performance optimization via sys.setprofile hook.
Detects hot loops and automatically parallelizes suitable workloads.

Architecture Reference:
- epochly-architecture-spec.md lines 2012-2086: EpochlyProfiler specification
- Lines 2025-2031: Profiling callbacks (call, return, c_call events)
- Lines 2041-2050: Hot loop detection via bytecode analysis
- Lines 2055-2086: Automatic parallelization algorithm

Performance Improvements:
- CPU-2: Scoped sys.setprofile usage (perf_improvements.md lines 78-106)
  - Context manager APIs for scoped profiling
  - macOS GUI detection and opt-out
  - Infrastructure for future C-extension trampoline

Author: Epochly Development Team
Date: October 1, 2025
"""

import sys
import time
import dis
import threading
import weakref
from typing import Dict, Any, Optional, Callable, List, Set
from collections import defaultdict
from dataclasses import dataclass
from contextlib import contextmanager

from ..utils.logger import get_logger


@dataclass
class ThreadContext:
    """
    Per-thread profiling context (Task 2: Sampling Profiler).

    Each thread maintains its own sample buffer to avoid lock contention.
    Uses ring buffer for fixed-size storage with automatic wrapping.
    """
    buffer: List[Any]  # Ring buffer for samples
    index: int  # Current position in ring buffer
    last_sample_ns: int  # Timestamp of last sample (monotonic nanoseconds)


class ScopedProfiler:
    """
    Context manager for scoped profiling (CPU-2).

    Installs profiler hook only for specific code section,
    avoiding global overhead when not needed.

    Usage:
        with profiler.scoped('hot_section'):
            run_hot_workload()  # Only profile this section
    """

    def __init__(self, profiler: 'EpochlyProfiler', section_id: str):
        """
        Initialize scoped profiler context manager.

        Args:
            profiler: Parent EpochlyProfiler instance
            section_id: Identifier for this profiled section
        """
        self.profiler = profiler
        self.section_id = section_id
        self._previous_hook = None
        self._nesting_count = 0

    def __enter__(self):
        """Enter scoped profiling context - install hook."""
        # Track nesting level (thread-local)
        nesting = getattr(self.profiler._thread_ctx, 'nesting_count', 0)
        self.profiler._thread_ctx.nesting_count = nesting + 1

        # Only install hook on first entry (outermost scope)
        if nesting == 0:
            # Save previous hook (might be None or another profiler)
            self._previous_hook = sys.getprofile()

            # Check if we should skip profiling (macOS GUI opt-out)
            if self.profiler._should_skip_profiling():
                # Don't install hook - just return
                return self

            # Install our profiler hook
            sys.setprofile(self.profiler)

        # Track current section being profiled
        self.profiler._current_section = self.section_id

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit scoped profiling context - remove hook."""
        # Decrement nesting count
        nesting = getattr(self.profiler._thread_ctx, 'nesting_count', 1)
        self.profiler._thread_ctx.nesting_count = nesting - 1

        # Only remove hook on last exit (outermost scope)
        if nesting == 1:
            # Restore previous hook (usually None)
            sys.setprofile(self._previous_hook)

        # Clear current section
        self.profiler._current_section = None

        # Don't suppress exceptions
        return False


class EpochlyProfiler:
    """
    Lightweight profiler for detecting hot paths and optimization opportunities.

    Uses sys.setprofile to monitor function calls with minimal overhead.
    Detects loops that execute frequently and triggers parallelization.

    CPU-2 Enhancement: Supports scoped profiling to reduce overhead.
    """

    def __init__(self, sampling_interval_ms=5.0, buffer_size=1000):
        """
        Initialize the profiler with sampling support.

        Args:
            sampling_interval_ms (float): Minimum interval between samples in milliseconds.
                                          Default: 5ms (balances overhead vs. coverage)
            buffer_size (int): Size of per-thread ring buffer. Default: 1000 samples.

        Performance Improvements (Task 2/6):
        - Per-thread ring buffers to avoid lock contention
        - Sampling interval to skip hot-path work when too recent
        - Bytecode cache to avoid repeated analysis

        CPU-2: Scoped profiling support
        - Context manager API for section-specific profiling
        - macOS GUI detection and opt-out
        - Workload detector integration
        """
        self.logger = get_logger(__name__)

        # ========== TASK 2: SAMPLING PROFILER IMPROVEMENTS ==========

        # Per-thread context storage (avoids shared dict + lock on every call)
        self._thread_ctx = threading.local()

        # Sampling configuration
        self._sampling_interval_ns = int(sampling_interval_ms * 1_000_000)  # Convert ms to ns
        self._buffer_size = buffer_size

        # Bytecode analysis cache (WeakKeyDictionary for automatic GC)
        # Maps code object -> analysis result (loop info, etc.)
        self._code_cache = weakref.WeakKeyDictionary()
        self._cache_lock = threading.Lock()  # Only for cache population

        # ========== CPU-2: SCOPED PROFILING STATE ==========

        # Current section being profiled (None if not in scoped context)
        self._current_section: Optional[str] = None

        # Sections enabled for profiling (workload detector integration)
        self._enabled_sections: Set[str] = set()
        self._enabled_sections_lock = threading.Lock()

        # macOS GUI framework opt-out configuration
        self.allow_gui_profiling: bool = False

        # ========== ORIGINAL PROFILER STATE (Preserved) ==========

        # Function statistics (kept for backward compatibility)
        self.function_stats: Dict[int, Dict[str, Any]] = {}

        # Loop counters for hot loop detection
        self.loop_counters: Dict[tuple, int] = defaultdict(int)
        self.parallelized_loops: set = set()  # Track already parallelized loops

        # Thresholds from architecture spec
        self.hot_threshold = 10_000  # iterations before considering "hot"
        self.time_threshold = 0.002   # 2ms minimum execution time

        # Thread safety (RLock for backward compatibility, but used sparingly now)
        self._lock = threading.RLock()

        # Integration with existing ML/RNN system
        self._adaptive_orchestrator = None  # Set by auto_enable
        self._jit_analyzer = None  # Set by auto_enable
        self._workload_detector = None  # Set by auto_enable

        # Executor integration for parallelization
        self._executor_pool = None  # Set by EpochlyCore

    def scoped(self, section_id: str) -> ScopedProfiler:
        """
        Create context manager for scoped profiling (CPU-2).

        Only profiles code within this context, avoiding global overhead.

        Args:
            section_id: Identifier for this profiled section

        Returns:
            ScopedProfiler context manager

        Example:
            with profiler.scoped('hot_workload'):
                run_cpu_intensive_code()
        """
        return ScopedProfiler(self, section_id)

    def enable_for_section(self, section_id: str):
        """
        Enable profiling for specific section (workload detector integration).

        Args:
            section_id: Section to enable profiling for
        """
        with self._enabled_sections_lock:
            self._enabled_sections.add(section_id)

    def disable_for_section(self, section_id: str):
        """
        Disable profiling for specific section.

        Args:
            section_id: Section to disable profiling for
        """
        with self._enabled_sections_lock:
            self._enabled_sections.discard(section_id)

    def _is_macos(self) -> bool:
        """Check if running on macOS platform."""
        return sys.platform == 'darwin'

    def _detect_gui_framework(self) -> Optional[str]:
        """
        Detect if GUI framework is loaded (macOS specific).

        Returns:
            Name of detected GUI framework or None
        """
        # Check for common GUI frameworks in sys.modules
        gui_frameworks = {
            'PyQt5': 'PyQt5',
            'PyQt6': 'PyQt6',
            'PySide2': 'PySide2',
            'PySide6': 'PySide6',
            'tkinter': 'Tkinter',
            'wx': 'wxPython',
            'PyObjC': 'PyObjC',
        }

        for module, name in gui_frameworks.items():
            if module in sys.modules:
                return name

        return None

    def _should_skip_profiling(self) -> bool:
        """
        Check if profiling should be skipped (macOS GUI opt-out).

        Returns:
            True if profiling should be skipped, False otherwise
        """
        # If explicitly allowed, never skip
        if self.allow_gui_profiling:
            return False

        # Only check on macOS
        if not self._is_macos():
            return False

        # Check if GUI framework is present
        gui_framework = self._detect_gui_framework()
        if gui_framework:
            self.logger.debug(
                f"GUI framework detected ({gui_framework}) on macOS - "
                f"skipping profiling (set allow_gui_profiling=True to override)"
            )
            return True

        return False

    def _get_thread_context(self) -> ThreadContext:
        """
        Get or create per-thread profiling context.

        Each thread gets its own ThreadContext with isolated ring buffer.
        This avoids lock contention on every profiling event.

        Returns:
            ThreadContext: Thread-local context with ring buffer
        """
        ctx = getattr(self._thread_ctx, 'ctx', None)
        if ctx is None:
            # Lazy initialization of thread context
            ctx = ThreadContext(
                buffer=[None] * self._buffer_size,
                index=0,
                last_sample_ns=0
            )
            self._thread_ctx.ctx = ctx
        return ctx

    def _get_code_info(self, code):
        """
        Get cached bytecode analysis for code object.

        Uses WeakKeyDictionary cache to avoid repeated analysis.
        Lock is only taken on cache miss, not on hits.

        Args:
            code: Code object to analyze

        Returns:
            dict: Cached analysis result with loop information
        """
        # Fast path: check cache without lock
        info = self._code_cache.get(code)
        if info is not None:
            return info

        # Slow path: analyze and cache (with lock)
        with self._cache_lock:
            # Double-check: another thread may have cached while we waited
            info = self._code_cache.get(code)
            if info is not None:
                return info

            # Analyze bytecode for loop instructions
            loop_instructions = []
            try:
                for i, instr in enumerate(dis.get_instructions(code)):
                    if instr.opname in ('FOR_ITER', 'JUMP_BACKWARD'):
                        loop_instructions.append((i, instr))
            except Exception as e:
                # If bytecode analysis fails, cache empty result
                self.logger.debug(f"Bytecode analysis failed for {code.co_name}: {e}")

            # Cache result
            info = {
                'func_name': code.co_name,
                'filename': code.co_filename,
                'loop_instructions': loop_instructions,
                'analyzed_at': time.monotonic()
            }
            self._code_cache[code] = info

        return info

    def _emit_samples(self, buffer: List[Any]):
        """
        Process and emit samples from ring buffer.

        Called when buffer wraps around or on periodic flush.
        This is where we aggregate data and send to orchestrator.

        Args:
            buffer: Ring buffer containing samples to process
        """
        # Filter out None entries (unfilled buffer positions)
        samples = [s for s in buffer if s is not None]

        if not samples:
            return

        # Aggregate and process samples
        # (Detailed processing can be added here as needed)
        # For now, we just clear the processed samples
        # This method can be extended to send to adaptive orchestrator, etc.

        # Note: This method runs outside the profiling hot path,
        # so it can do more expensive operations if needed

    def __call__(self, frame, event, arg):
        """
        Profile callback function for sys.setprofile with sampling.

        Performance Optimization (Task 2/6):
        - Uses sampling interval to skip most events (low overhead)
        - Per-thread storage avoids lock contention
        - Only samples at configured interval

        Args:
            frame: Current stack frame
            event: Event type ('call', 'return', 'c_call', etc.)
            arg: Event-specific argument
        """
        try:
            # ========== TASK 2: SAMPLING LOGIC (HOT PATH OPTIMIZATION) ==========

            # Get thread-local context (no lock required)
            ctx = self._get_thread_context()

            # Check sampling interval (fast comparison, no lock)
            now = time.monotonic_ns()
            if now - ctx.last_sample_ns < self._sampling_interval_ns:
                # Too recent - skip this event (FAST PATH EXIT)
                return

            # Update last sample time
            ctx.last_sample_ns = now

            # ========== EXISTING PROFILER LOGIC (SAMPLED) ==========

            # Process event (now only happens at sampling interval)
            if event == 'call':
                self._on_call(frame)
            elif event == 'return':
                self._on_return(frame, arg)
            elif event == 'c_call':
                self._on_c_call(frame, arg)

        except Exception as e:
            # Never let profiler break user code
            self.logger.debug(f"Profiler error: {e}")

    def _on_call(self, frame):
        """Handle function call event."""
        with self._lock:
            func_id = id(frame.f_code)
            self.function_stats[func_id] = {
                'start_time': time.perf_counter(),
                'frame': frame,
                'name': frame.f_code.co_name,
                'filename': frame.f_code.co_filename
            }

    def _on_return(self, frame, arg):
        """Handle function return event."""
        with self._lock:
            func_id = id(frame.f_code)
            if func_id in self.function_stats:
                start_time = self.function_stats[func_id]['start_time']
                elapsed = time.perf_counter() - start_time
                elapsed_ns = int(elapsed * 1_000_000_000)

                # Feed data to adaptive orchestrator if available
                if self._adaptive_orchestrator and elapsed_ns > 0:
                    try:
                        # Get function reference
                        func_name = frame.f_code.co_name
                        # Record with orchestrator for ML analysis
                        self._adaptive_orchestrator.record_function_call(
                            func=frame.f_code,
                            execution_time_ns=elapsed_ns,
                            context={'name': func_name}
                        )
                    except Exception as e:
                        self.logger.debug(f"Failed to record with orchestrator: {e}")

                # Check for hot loops that could benefit from parallelization
                if elapsed > self.time_threshold:
                    self._check_hot_loop(frame)

    def _on_c_call(self, frame, arg):
        """Handle C function call event."""
        # Minimal tracking for C calls
        pass

    def _check_hot_loop(self, frame):
        """
        Detect hot loops via cached bytecode analysis.

        Architecture spec lines 2041-2050: Loop detection algorithm

        Performance Optimization (Task 2/6):
        - Uses cached bytecode analysis instead of repeated dis.get_instructions()
        - Cache hit: ~1 microsecond lookup
        - Cache miss: ~1ms analysis (but only happens once per code object)
        """
        try:
            code = frame.f_code

            # TASK 2: Use cached bytecode analysis (fast path)
            code_info = self._get_code_info(code)

            # Iterate over cached loop instructions (no expensive disassembly)
            for i, instr in code_info.get('loop_instructions', []):
                loop_id = (id(code), i)

                with self._lock:
                    self.loop_counters[loop_id] = self.loop_counters.get(loop_id, 0) + 1

                    # Check if loop has crossed hot threshold and not yet analyzed
                    if (self.loop_counters[loop_id] > self.hot_threshold and
                        loop_id not in self.parallelized_loops):
                        # Potential parallelization candidate
                        self._attempt_parallelization(frame, instr, loop_id)

        except Exception as e:
            self.logger.debug(f"Hot loop check failed: {e}")

    def _attempt_parallelization(self, frame, loop_instr, loop_id):
        """
        Attempt to parallelize detected hot loop.

        Architecture spec lines 2055-2086: Parallelization algorithm

        This is a conservative implementation that records hot loops for
        JIT compilation and sub-interpreter optimization rather than
        attempting runtime bytecode rewriting (which is fragile).
        """
        func_name = frame.f_code.co_name

        self.logger.debug(
            f"Hot loop detected in {func_name} "
            f"(instruction: {loop_instr.opname} at offset {loop_instr.offset})"
        )

        # Mark as analyzed to avoid repeated analysis
        self.parallelized_loops.add(loop_id)

        # Notify adaptive orchestrator if available
        # This allows JIT compiler and sub-interpreter pool to optimize this function
        if self._adaptive_orchestrator:
            try:
                # Record hot loop for optimization consideration
                iteration_count = self.loop_counters.get(loop_id, 0)

                self._adaptive_orchestrator.record_hot_loop(
                    func=frame.f_code,
                    loop_instruction=loop_instr.opname,
                    loop_offset=loop_instr.offset,
                    iteration_count=iteration_count,
                    context={'name': func_name}
                )

                self.logger.info(
                    f"Hot loop in {func_name} flagged for JIT optimization "
                    f"({iteration_count:,} iterations)"
                )

            except Exception as e:
                self.logger.debug(f"Failed to record hot loop with orchestrator: {e}")


# Global profiler instance
_global_profiler = None


# Thread-local re-entrancy guard (global var doesn't work for threading)
import threading
_profiler_guard = threading.local()


def epochly_profile_hook(frame, event, arg):
    """
    Global profiling hook function for sys.setprofile.

    This function is installed by auto_enable() and delegates to
    the global profiler instance.

    Args:
        frame: Current stack frame
        event: Event type
        arg: Event argument
    """
    global _global_profiler

    # Thread-local re-entrancy guard - prevents deadlocks during profiler work
    # Check if this thread is already executing the profiler hook
    # CRITICAL: Check if _profiler_guard is None (can happen during interpreter shutdown)
    try:
        if _profiler_guard is None or getattr(_profiler_guard, 'in_hook', False):
            return
    except (TypeError, AttributeError):
        # Guard was garbage collected during shutdown
        return

    # Skip profiling during module imports to prevent hangs
    # When importing modules, the import machinery calls many functions that
    # trigger the profile hook, potentially causing deadlocks or infinite loops
    if frame is not None:
        filename = frame.f_code.co_filename
        # Skip frozen modules (import machinery)
        if filename.startswith('<frozen'):
            return
        # Skip Epochly source code (not installed via pip)
        # P0.12 fix: Use '/src/epochly/' for precision, not 'epochly' (too broad)
        if '/src/epochly/' in filename:
            return
        # Skip standard library internals that can be triggered during imports
        if 'importlib' in filename or 'abc.py' in filename:
            return

    try:
        _profiler_guard.in_hook = True

        # Lazy initialization
        if _global_profiler is None:
            _global_profiler = EpochlyProfiler()

        # Delegate to profiler
        _global_profiler(frame, event, arg)
    finally:
        _profiler_guard.in_hook = False


def get_global_profiler() -> Optional[EpochlyProfiler]:
    """Get the global profiler instance."""
    return _global_profiler
