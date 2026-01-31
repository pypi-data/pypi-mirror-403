"""
Epochly JIT Compilation Manager

Coordinates JIT compilation with analyzer plugins to provide intelligent,
automated JIT compilation for Level 2 optimization.

Author: Epochly Development Team
"""

import gc
import time
import threading
import functools
import atexit
import weakref
from contextlib import contextmanager
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass
import logging

from .base import JITCompiler, JITBackend, JITCompilationResult
from .loop_classifier import LoopAwareJITClassifier, JITStrategy


class CompilationMode(Enum):
    """Compilation mode for JIT compilation.

    P1 WARMUP OPTIMIZATION (Jan 2026): Allows users to control compilation timing.

    BACKGROUND (default): Non-blocking compilation in background thread.
        - Best for long-running services and interactive applications
        - Functions are available immediately (using original implementation)
        - Compiled version takes over once ready

    SYNCHRONOUS: Blocking compilation that waits for completion.
        - Best for one-shot scripts that need predictable timing
        - First call may be slower, but subsequent calls are always optimized
        - Use via `eager_mode()` context manager

    Usage:
        # For scripts that run once:
        with epochly.eager_mode():
            result = heavy_computation(data)  # Compiled synchronously
    """
    BACKGROUND = auto()    # Current default - non-blocking
    SYNCHRONOUS = auto()   # New - blocks until compiled
from .base import CompilationStatus as BaseCompilationStatus  # Legacy status enum
from ..plugins.analyzer.jit_analyzer import JITAnalyzer, JITSuitability, JITBackendType

# Phase 2.4: Import new compilation infrastructure
try:
    from .artifact_store import CompilationStatus
except ImportError:
    # Fallback to base status if artifact_store not available
    CompilationStatus = BaseCompilationStatus

# Phase 3: Persistent cache for warm restarts
try:
    from .persistent_cache import get_persistent_cache
    PERSISTENT_CACHE_AVAILABLE = True
except ImportError:
    get_persistent_cache = None
    PERSISTENT_CACHE_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class JITConfiguration:
    """Configuration for JIT compilation manager."""
    
    # Compilation thresholds
    min_hot_path_score: float = 60.0
    min_function_calls: int = 50
    max_compilation_time_ms: float = 1000.0
    
    # Performance requirements
    min_expected_speedup: float = 1.2  # 20% improvement minimum
    max_compilation_overhead: float = 0.05  # 5% overhead maximum
    
    # Backend preferences
    preferred_backends: List[JITBackend] = None
    enable_fallback_backends: bool = True
    
    # Caching and optimization
    enable_compilation_caching: bool = True
    max_cache_size: int = 1000
    enable_performance_learning: bool = True
    
    def __post_init__(self):
        """Initialize default values (Multi-JIT Strategy 2025)."""
        if self.preferred_backends is None:
            import sys
            # Default backend preferences based on Python version
            # Numba 0.59.0+ supports Python 3.9-3.12
            # IMPORTANT: Pyston-Lite only supports Python 3.7-3.10
            if sys.version_info >= (3, 13):
                # Python 3.13+: Native JIT experimental, Numba available
                self.preferred_backends = [JITBackend.NATIVE, JITBackend.NUMBA]
            elif sys.version_info >= (3, 11):
                # Python 3.11-3.12: Numba only (Pyston doesn't support 3.11+)
                self.preferred_backends = [JITBackend.NUMBA]
            elif sys.version_info >= (3, 9):
                # Python 3.9-3.10: Numba and Pyston both available
                self.preferred_backends = [JITBackend.NUMBA, JITBackend.PYSTON]
            else:
                # Python 3.7-3.8: Pyston only (Numba may have compatibility issues)
                self.preferred_backends = [JITBackend.PYSTON]


class JITManager:
    """
    Manages JIT compilation coordination with analyzer plugins.
    
    Integrates with JITAnalyzer to automatically detect hot paths and
    coordinate intelligent JIT compilation using the best available backends.
    """
    
    def __init__(self,
                 jit_analyzer: Optional[JITAnalyzer] = None,
                 available_backends: Optional[List[JITBackend]] = None,
                 config: Optional[JITConfiguration] = None):
        """
        Initialize JIT manager.

        Args:
            jit_analyzer: JIT analyzer plugin instance
            available_backends: List of available JIT backends
            config: JIT configuration options
        """
        self.jit_analyzer = jit_analyzer or JITAnalyzer()
        self.config = config or JITConfiguration()

        # Initialize available backends
        self.available_backends = available_backends if available_backends is not None else self._detect_backends()
        self.jit_compilers: Dict[JITBackend, JITCompiler] = {}
        self._initialize_compilers()

        # Compilation state
        self.compiled_functions: Dict[str, JITCompilationResult] = {}
        self.compilation_queue: Set[str] = set()
        self._failed_compilations: Set[str] = set()  # P0.14: Cache failed compilations to prevent retries
        self._failed_code_ids: Set[int] = set()  # P0.12: Track by code_id for monitoring callback checks
        self.performance_history: Dict[str, List[float]] = {}

        # P0.15 FIX (Dec 2025): Reference to auto_profiler for non-transformable checks
        # When auto_profiler detects method calls in loops (P0.13), it sets code_ids in
        # _non_transformable_code_ids. JITManager needs to check this before queueing.
        self._auto_profiler_ref: Optional[Any] = None

        # Thread safety
        self._lock = threading.RLock()

        # P1 WARMUP OPTIMIZATION (Jan 2026): Compilation mode control
        # Default to BACKGROUND for non-blocking compilation
        # Use eager_mode() context manager to switch to SYNCHRONOUS
        # MCP-reflect FIX: Use lock for thread-safe mode access
        self._compilation_mode = CompilationMode.BACKGROUND
        self._compilation_mode_lock = threading.Lock()

        # Task 3 - perf_fixes2.md: Allocator health tracking
        self._allocator = None  # Will be injected by EpochlyCore if available
        self._last_pause_log_time = 0.0  # Rate limiting for pause logs (first pause always logs)
        self._pause_log_interval = 10.0  # Log pause reason at most every 10s

        # Background compilation
        self._compilation_thread: Optional[threading.Thread] = None
        self._stop_background_compilation = threading.Event()

        # Phase 2.4: Background compilation worker with artifact store
        self._compilation_worker = None
        self._artifact_store = None
        try:
            from .artifact_store import get_artifact_store
            from .compilation_worker import CompilationWorker

            self._artifact_store = get_artifact_store()
            self._compilation_worker = CompilationWorker(
                jit_manager=self,
                artifact_store=self._artifact_store
            )
            logger.debug("Background compilation worker initialized (non-blocking API)")
        except ImportError as e:
            logger.debug(f"Compilation worker unavailable: {e}")

        # Profiling system integration for background compilation
        self._registered_functions: Dict[str, Callable] = {}
        self._function_profiles: Dict[str, List[float]] = {}

        # Code object to function cache (for sys.monitoring auto-registration)
        # Key: id(code_object), Value: function object or None if not found
        # BOUNDED CACHE (Dec 2025): Prevent unbounded memory growth
        self._code_to_function_cache: Dict[int, Optional[Callable]] = {}
        self._code_to_function_cache_max_size = 10000  # Max 10k entries

        # SPEC2 Task 10: Adaptive JIT policy for intelligent compilation
        try:
            from .adaptive_policy import AdaptivePolicy
            from .telemetry_store import TelemetryStore

            self._adaptive_policy = AdaptivePolicy()
            self._telemetry_store = TelemetryStore()
            logger.debug("Adaptive JIT policy enabled (target: <10% compile rate)")
        except ImportError as e:
            logger.warning(f"Adaptive JIT policy unavailable: {e}")
            self._adaptive_policy = None
            self._telemetry_store = None

        # Bytecode-based loop classifier for eager JIT compilation
        # Solves "Pattern B" problem: functions with hot loops called once
        # that never trigger JIT under call-count-based approach
        self._loop_classifier = LoopAwareJITClassifier()
        logger.debug("Loop-aware JIT classifier enabled (bytecode analysis)")

        # SPEC2 Task 12: sys.monitoring integration (Python 3.12+)
        # ISSUE #5 FIX (perf_fixes4.md): Aggressive default enabling on 3.12+
        self._execution_counts: Dict[str, int] = {}  # Track function execution counts
        try:
            import sys
            if sys.version_info >= (3, 12):
                # AGGRESSIVE: Default enable sys.monitoring on Python 3.12+
                from .sys_monitoring_integration import SysMonitoringIntegration
                self._sys_monitoring = SysMonitoringIntegration(jit_manager=self)
                if self._sys_monitoring.is_available():
                    self._sys_monitoring.enable()
                    logger.debug("sys.monitoring AGGRESSIVELY enabled on Python 3.12+ (perf_fixes4.md Issue #5)")

                    # Schedule pre-warm pass for hot functions from telemetry store
                    if self._telemetry_store:
                        self._schedule_prewarm_pass()
                else:
                    self._sys_monitoring = None
            else:
                # Python <3.12: sys.monitoring not available
                self._sys_monitoring = None
                logger.debug("sys.monitoring requires Python 3.12+")
        except ImportError as e:
            logger.debug(f"sys.monitoring integration unavailable: {e}")
            self._sys_monitoring = None


        # Phase 3: Persistent cache for warm restarts
        self._persistent_cache = None
        if PERSISTENT_CACHE_AVAILABLE:
            try:
                self._persistent_cache = get_persistent_cache()
                logger.debug("Persistent JIT cache enabled for warm restarts")
            except Exception as e:
                logger.warning(f"Failed to initialize persistent cache: {e}")

        # CRITICAL FIX (Dec 2025): Register atexit handler to prevent KeyError during shutdown
        # Daemon threads can cause KeyError in threading._active dict during interpreter shutdown
        # This ensures we cleanly stop the compilation worker before Python's threading cleanup
        self._cleanup_registered = False
        self._register_atexit_cleanup()

        logger.debug(f"JIT manager initialized with backends: {[b.value for b in self.available_backends]}")

    def set_auto_profiler(self, auto_profiler) -> None:
        """
        P0.15 FIX (Dec 2025): Set reference to auto_profiler for non-transformable checks.

        When auto_profiler detects method calls in loops (P0.13), it adds code_ids to
        _non_transformable_code_ids. JITManager uses this to skip queuing functions
        that would fail JIT compilation anyway (e.g., random_state.binomial() calls).

        Args:
            auto_profiler: AutoProfiler instance
        """
        self._auto_profiler_ref = auto_profiler
        logger.debug("JITManager: Auto-profiler reference set for P0.15 non-transformable checks")

    def _is_non_transformable(self, code_object) -> bool:
        """
        P0.15: Check if code_object is marked as non-transformable by auto_profiler.

        The auto_profiler's P0.13 method call detection is more comprehensive than
        the JIT analyzer and catches patterns like random_state.binomial() that
        would fail JIT compilation.

        Args:
            code_object: Code object to check

        Returns:
            True if code_object should NOT be JIT compiled
        """
        if code_object is None or self._auto_profiler_ref is None:
            return False

        code_id = id(code_object)

        # Check auto_profiler's non_transformable set (populated by P0.13)
        if hasattr(self._auto_profiler_ref, '_non_transformable_code_ids'):
            if code_id in self._auto_profiler_ref._non_transformable_code_ids:
                return True

        return False

    @property
    def compilation_mode(self) -> CompilationMode:
        """
        Get current compilation mode (thread-safe).

        MCP-reflect FIX (Jan 2026): Uses lock for thread-safe access to
        prevent race conditions when mode is changed from multiple threads.

        Returns:
            Current CompilationMode (BACKGROUND or SYNCHRONOUS)
        """
        with self._compilation_mode_lock:
            return self._compilation_mode

    @compilation_mode.setter
    def compilation_mode(self, mode: CompilationMode) -> None:
        """
        Set compilation mode (thread-safe).

        MCP-reflect FIX (Jan 2026): Uses lock for thread-safe access to
        prevent race conditions when mode is changed from multiple threads.

        Args:
            mode: New CompilationMode to set
        """
        with self._compilation_mode_lock:
            self._compilation_mode = mode

    def _schedule_prewarm_pass(self):
        """
        Schedule pre-warm pass for hot functions from telemetry store.

        ISSUE #5 FIX (perf_fixes4.md): Pre-warm top N functions to reduce cold-start.
        """
        def prewarm_task():
            try:
                # Wait briefly to avoid interfering with startup
                import time
                time.sleep(1.0)

                # Get top N hot functions from telemetry
                if self._telemetry_store:
                    hot_functions = self._telemetry_store.get_top_functions(limit=10)
                    for func_name in hot_functions:
                        if func_name in self._registered_functions:
                            func = self._registered_functions[func_name]
                            # P0.13 FIX: Telemetry store has already proven these functions
                            # are hot. Bypass static call_count filter.
                            self.compile_function_auto(func, bypass_call_count=True, skip_benchmark=True)
                            logger.debug(f"Pre-warmed {func_name} from telemetry (P0.13: bypass_call_count=True)")
            except Exception as e:
                logger.debug(f"Pre-warm pass failed: {e}")

        # Schedule as background thread
        prewarm_thread = threading.Thread(target=prewarm_task, daemon=True, name="JIT-Prewarm")
        prewarm_thread.start()
        logger.debug("Scheduled pre-warm pass for hot functions (Issue #5)")

    def _register_atexit_cleanup(self):
        """
        Register atexit handler for clean shutdown.

        CRITICAL FIX (Dec 2025): This prevents KeyError exceptions during interpreter
        shutdown caused by daemon threads not being properly stopped.

        The KeyError occurs because:
        1. Daemon threads are abruptly terminated during shutdown
        2. The threading module's _active dict cleanup races with thread termination
        3. Thread tries to remove itself but entry is already gone

        Solution: Register cleanup that stops daemon threads BEFORE Python's threading cleanup.
        """
        if self._cleanup_registered:
            return

        # Use weakref to avoid preventing garbage collection
        weak_self = weakref.ref(self)

        def cleanup_on_exit():
            """Cleanup handler called on interpreter exit."""
            manager = weak_self()
            if manager is not None:
                try:
                    manager.stop_background_compilation()
                except Exception:
                    pass  # Ignore errors during cleanup

        atexit.register(cleanup_on_exit)
        self._cleanup_registered = True

    # Dunder methods that should NEVER be JIT compiled
    # These are auto-generated by dataclasses, protocols, ABCs and cannot be compiled by Numba.
    # Attempting to compile them wastes time and floods logs with "Benchmark failed" warnings.
    # P0.14 FIX (Dec 2025): Filter these early to prevent 10+ minute initialization hangs.
    _DUNDER_SKIP_LIST = frozenset({
        # Object lifecycle
        '__new__', '__init__', '__del__', '__init_subclass__',
        # Representation
        '__repr__', '__str__', '__bytes__', '__format__',
        # Comparison
        '__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__', '__hash__',
        # Attribute access
        '__getattr__', '__getattribute__', '__setattr__', '__delattr__', '__dir__',
        # Descriptor protocol
        '__get__', '__set__', '__delete__', '__set_name__',
        # Container/sequence
        '__len__', '__length_hint__', '__getitem__', '__setitem__', '__delitem__',
        '__missing__', '__iter__', '__reversed__', '__contains__',
        # Numeric operations (usually trivial wrappers)
        '__add__', '__radd__', '__iadd__', '__sub__', '__rsub__', '__isub__',
        '__mul__', '__rmul__', '__imul__', '__truediv__', '__rtruediv__', '__itruediv__',
        '__floordiv__', '__rfloordiv__', '__ifloordiv__', '__mod__', '__rmod__', '__imod__',
        '__divmod__', '__rdivmod__', '__pow__', '__rpow__', '__ipow__',
        '__neg__', '__pos__', '__abs__', '__invert__',
        '__lshift__', '__rlshift__', '__ilshift__', '__rshift__', '__rrshift__', '__irshift__',
        '__and__', '__rand__', '__iand__', '__or__', '__ror__', '__ior__',
        '__xor__', '__rxor__', '__ixor__', '__matmul__', '__rmatmul__', '__imatmul__',
        # Type conversion
        '__int__', '__float__', '__complex__', '__bool__', '__index__', '__round__',
        '__trunc__', '__floor__', '__ceil__',
        # Context managers
        '__enter__', '__exit__', '__aenter__', '__aexit__',
        # Async
        '__await__', '__aiter__', '__anext__',
        # Callable
        '__call__',
        # Class/instance
        '__class__', '__class_getitem__', '__instancecheck__', '__subclasscheck__',
        # Dataclass-specific
        '__post_init__', '__match_args__', '__dataclass_fields__', '__dataclass_params__',
        # Other special methods
        '__copy__', '__deepcopy__', '__reduce__', '__reduce_ex__', '__getnewargs__',
        '__getnewargs_ex__', '__getstate__', '__setstate__', '__sizeof__',
        # Dataclass internals (generated by @dataclass decorator)
        '__create_fn__',
    })

    def record_execution(self, func_name: str, code_object=None):
        """
        Record function execution from sys.monitoring (SPEC2 Task 12).

        Auto-registers function for JIT compilation when hot enough.
        Critical fix (Dec 2025): Extract and register function object from
        code object to enable JIT compilation for notebook-defined functions.

        Args:
            func_name: Function name
            code_object: Optional code object (used for auto-registration)
        """
        # P0.14 FIX: Skip dunder methods IMMEDIATELY - they cannot be JIT compiled
        # and attempting to compile them causes 10+ minute initialization hangs.
        # This must come FIRST before any other filtering to prevent wasted cycles.
        if func_name in self._DUNDER_SKIP_LIST:
            return

        # P0.9 FIX: Filter out internal/library functions early
        # This prevents the compilation queue from being flooded with stdlib/framework code
        if not self._is_user_code(code_object):
            return

        # P0.15 FIX: Skip functions marked as non-transformable by auto_profiler
        # This catches method calls in loops (e.g., random_state.binomial()) that
        # would fail JIT compilation. The auto_profiler's P0.13 detection is more
        # comprehensive than the JIT analyzer for these patterns.
        if self._is_non_transformable(code_object):
            logger.debug(f"P0.15: Skipping {func_name} - marked as non-transformable by auto_profiler")
            return

        # P0.9 FIX: Track function to queue OUTSIDE the lock to prevent deadlock
        # queue_compilation() may acquire other locks internally
        func_to_queue = None

        with self._lock:
            self._execution_counts[func_name] = self._execution_counts.get(func_name, 0) + 1

            # Feed to telemetry store
            if self._telemetry_store:
                self._telemetry_store.record_call(func_name)

            # Check if hot enough for compilation
            count = self._execution_counts[func_name]
            if count >= self.config.min_function_calls:
                # P0.14: Also skip functions that previously failed to compile
                if func_name not in self.compilation_queue and func_name not in self.compiled_functions and func_name not in self._failed_compilations:
                    # Task 3: Check system health before queueing
                    if self._should_compile(func_name):
                        # CRITICAL FIX (Dec 2025): Auto-register function from code object
                        # Previously, notebook functions weren't registered because
                        # adaptive_orchestrator.record_hot_loop() called
                        # _jit_analyzer.register_function_for_profiling() which doesn't exist.
                        # Now we extract and register the function directly here.
                        if code_object is not None and func_name not in self._registered_functions:
                            func_obj = self._extract_function_from_code(code_object)
                            if func_obj is not None:
                                self._registered_functions[func_name] = func_obj
                                logger.debug(f"Auto-registered function '{func_name}' from code object")

                        self.compilation_queue.add(func_name)
                        logger.debug(f"Function {func_name} marked as hot via sys.monitoring (count={count})")

                        # P0.9 FIX: Prepare to trigger background compilation OUTSIDE lock
                        # Previously, we only added to the queue SET but never called
                        # queue_compilation() to send to the background worker
                        func_to_queue = self._registered_functions.get(func_name)
                    else:
                        logger.debug(f"Skipping hot function {func_name} (compilation paused)")

        # P0.9 FIX: Queue compilation OUTSIDE the lock to prevent deadlock
        # queue_compilation() acquires its own locks and may block
        if func_to_queue is not None and self._compilation_worker is not None:
            # P0.13 FIX: sys.monitoring has proven this function is hot (execution count
            # >= min_function_calls). Bypass static call_count filter.
            self.queue_compilation(func_to_queue, bypass_call_count=True)
            logger.debug(f"Queued {func_name} for background compilation (P0.13: bypass_call_count=True)")

    def _extract_function_from_code(self, code_object) -> Optional[Callable]:
        """
        Extract actual function object from code object with caching.

        Uses gc.get_referrers() to find the function that owns this code object.
        Critical for notebook/REPL functions where inspect.getsource() fails.

        Performance: Results are cached to avoid expensive gc.get_referrers()
        on every call (100x speedup for cached lookups).

        Args:
            code_object: Code object to find function for

        Returns:
            Function object or None if not found
        """
        code_id = id(code_object)

        # Fast path: check cache
        if code_id in self._code_to_function_cache:
            return self._code_to_function_cache[code_id]

        # Slow path: use gc.get_referrers
        try:
            referrers = gc.get_referrers(code_object)

            # Look for function objects
            for referrer in referrers:
                if isinstance(referrer, type(lambda: None)):  # Function type
                    if referrer.__code__ is code_object:
                        # Cache for future lookups (with bounds checking)
                        if len(self._code_to_function_cache) >= self._code_to_function_cache_max_size:
                            self._code_to_function_cache.clear()
                        self._code_to_function_cache[code_id] = referrer
                        return referrer

            # Not found - cache None to avoid repeated expensive searches (with bounds checking)
            if len(self._code_to_function_cache) >= self._code_to_function_cache_max_size:
                self._code_to_function_cache.clear()
            self._code_to_function_cache[code_id] = None
            logger.debug(f"Could not find function for code object {code_object.co_name}")
            return None

        except Exception as e:
            logger.debug(f"Error extracting function from code: {e}")
            return None

    def _is_user_code(self, code_object) -> bool:
        """
        Determine if code object is user code vs library/internal code.

        P0.9 FIX: Filters out stdlib, site-packages, and framework internals
        to prevent compilation queue from being flooded with non-user functions.

        Note: We ALLOW notebook/REPL code (<stdin>, <ipython-input-...>, etc.)
        since those are user code that should be JIT compiled. Only frozen
        modules (<frozen ...>) are excluded.

        CROSS-PLATFORM FIX (Dec 2025): Works on macOS, Linux, and Windows.
        - Linux: /usr/lib/python3.X/..., ~/.local/lib/python3.X/...
        - macOS: /Library/Frameworks/Python.framework/.../lib/python3.X/...
        - Windows: C:/PythonXX/Lib/..., C:/Users/.../Python/PythonXX/Lib/...

        Args:
            code_object: Code object to check

        Returns:
            True if this appears to be user code worth JIT compiling
        """
        if code_object is None:
            return True  # Allow if no code object (legacy path)

        try:
            filename = code_object.co_filename

            # Skip ONLY frozen modules (e.g., <frozen importlib._bootstrap>)
            # IMPORTANT: DO NOT skip all <...> filenames - that would exclude:
            # - <stdin> (interactive Python)
            # - <ipython-input-N-...> (Jupyter notebooks)
            # - <string> (exec/eval'd code)
            # These ARE user code and should be JIT compiled!
            if filename.startswith('<frozen '):
                return False

            # Normalize path separators for cross-platform compatibility
            # This ensures Windows paths work with Unix-style patterns
            normalized = filename.replace('\\', '/')

            # Also normalize to lowercase for case-insensitive matching on Windows
            # (Windows paths are case-insensitive: C:\Lib == c:\lib)
            normalized_lower = normalized.lower()

            # LEVEL 1: Always skip installed packages (site-packages/dist-packages)
            # These are definitely not user code (works on all platforms)
            if 'site-packages/' in normalized_lower or 'dist-packages/' in normalized_lower:
                return False

            # LEVEL 2: Skip Python stdlib
            # Linux/macOS: /lib/python3.X/ or /lib/pythonX.Y/
            # Windows: /Lib/ (capital L, but we use lowercase comparison)
            # The /lib/ check catches Windows stdlib after normalization
            if '/lib/python' in normalized_lower:
                return False
            # Windows stdlib: C:/PythonXX/Lib/ or .../Python/PythonXX/Lib/
            # Pattern: /pythonXX/lib/ where XX is version (e.g., python311, python313)
            import re
            if re.search(r'/python3?\d+/lib/', normalized_lower):
                return False

            # LEVEL 3: Skip third-party packages (numba, numpy) even when not in site-packages
            # (e.g., editable installs or development setups)
            if '/numba/' in normalized_lower or '/numpy/' in normalized_lower:
                return False

            # LEVEL 4: Skip Epochly internals (don't JIT compile the framework itself)
            # P0.14 FIX: Match library source code but NOT user notebooks/demos
            # Must check for src/epochly to avoid blocking notebooks/demos/02_genomics.py
            if '/src/epochly/' in normalized_lower:
                return False

            return True

        except Exception:
            return True  # Allow on error (conservative)

    def _detect_backends(self) -> List[JITBackend]:
        """
        Detect available JIT backends using capability-based detection.

        Uses the capability_detector module for accurate, version-aware
        detection of available JIT backends.

        Returns:
            List of available JIT backends
        """
        import sys
        available = []

        # Use capability detector for accurate detection
        try:
            from .capability_detector import (
                detect_capabilities,
                get_jit_status_message,
                JITCapability
            )

            report = detect_capabilities()
            logger.debug(get_jit_status_message())

            # Map capabilities to backends
            if report.numba_available:
                available.append(JITBackend.NUMBA)
                logger.debug(f"Numba JIT backend available (v{report.numba_version})")

            if report.pyston_available:
                available.append(JITBackend.PYSTON)
                logger.debug("Pyston-Lite JIT backend available (not yet enabled)")

            if report.cpython_jit_detected:
                available.append(JITBackend.NATIVE)
                logger.debug("CPython 3.13+ experimental JIT detected and enabled")

            # Log Python 3.11+ native optimization status
            if (report.general_code_acceleration == JITCapability.CPYTHON_NATIVE
                    and not report.pyston_available):
                logger.info(
                    "Python 3.11+ detected: using native CPython specializing interpreter "
                    "(~25% faster than 3.10). No external general JIT needed."
                )

        except ImportError:
            # Fallback to direct detection if capability_detector unavailable
            logger.debug("capability_detector unavailable, using direct detection")
            available = self._detect_backends_fallback()

        return available

    def _detect_backends_fallback(self) -> List[JITBackend]:
        """
        Fallback backend detection if capability_detector is unavailable.

        Returns:
            List of available JIT backends
        """
        import sys
        available = []

        # Check Numba (primary for numerical workloads)
        try:
            import numba
            available.append(JITBackend.NUMBA)
            logger.debug("Numba JIT backend available")
        except ImportError:
            logger.debug("Numba not available")

        # Check Python 3.13+ experimental JIT (detect only, cannot enable)
        if sys.version_info >= (3, 13):
            jit_enabled = False
            if hasattr(sys, '_xoptions') and sys._xoptions.get('jit'):
                jit_enabled = True
            if jit_enabled:
                available.append(JITBackend.NATIVE)
                logger.debug("CPython 3.13+ experimental JIT detected")

        # Check Pyston-Lite (3.8-3.10 only)
        if sys.version_info[:2] <= (3, 10):
            try:
                import pyston_lite
                available.append(JITBackend.PYSTON)
                logger.debug("Pyston-Lite JIT backend available (not yet enabled)")
            except ImportError:
                logger.debug("Pyston-Lite not available")

        return available
    
    def _initialize_compilers(self) -> None:
        """Initialize JIT compiler instances for available backends (Multi-JIT Strategy 2025)."""
        for backend in self.available_backends:
            try:
                if backend == JITBackend.NUMBA:
                    from .numba_jit import NumbaJIT
                    self.jit_compilers[backend] = NumbaJIT(
                        enable_caching=self.config.enable_compilation_caching
                    )
                elif backend == JITBackend.NATIVE:
                    from .native_jit import NativeJIT
                    self.jit_compilers[backend] = NativeJIT(
                        enable_caching=self.config.enable_compilation_caching
                    )
                elif backend == JITBackend.PYSTON:
                    from .pyston_jit import PystonJIT
                    self.jit_compilers[backend] = PystonJIT(
                        enable_caching=self.config.enable_compilation_caching
                    )
                
                logger.debug(f"Initialized {backend.value} JIT compiler")
                
            except ImportError as e:
                logger.warning(f"Failed to initialize {backend.value} compiler: {e}")
    
    def start_background_compilation(self) -> None:
        """Start background thread for automatic hot path compilation (Phase 2.4: with worker)."""
        # Phase 2.4: Start compilation worker if available
        # P0.8 FIX (Dec 2025): CompilationWorker now uses composition instead of Thread inheritance.
        # Its start() method is idempotent and handles all thread lifecycle internally.
        # No need for complex _started checks or thread recreation logic.
        if self._compilation_worker:
            try:
                self._compilation_worker.start()
                logger.debug("Started background JIT compilation worker (async benchmark)")
            except Exception as e:
                logger.warning(f"Failed to start compilation worker: {e}")

        # P0.12 FIX (Dec 2025): Re-queue functions that were detected during Level 1
        # sys.monitoring is enabled during JITManager.__init__(), but CompilationWorker
        # isn't started until Level 2. Functions detected during Level 1 are added to
        # compilation_queue SET but queue_compilation() fails silently (_running=False).
        # Re-queue them now that the worker is running.
        if self._compilation_worker and self._compilation_worker._running:
            pending_count = 0
            with self._lock:
                pending_funcs = list(self.compilation_queue)

            for func_name in pending_funcs:
                if func_name in self._registered_functions:
                    func = self._registered_functions[func_name]
                    # Queue to worker (now that it's running)
                    # P0.13 FIX: These functions were detected by sys.monitoring during Level 1,
                    # so they're already proven hot. Bypass static call_count filter.
                    if self.queue_compilation(func, bypass_call_count=True):
                        pending_count += 1
                        logger.debug(f"P0.12: Re-queued pending function '{func_name}' to CompilationWorker (P0.13: bypass_call_count=True)")

            if pending_count > 0:
                logger.info(f"P0.12: Re-queued {pending_count} pending functions from Level 1 detection")

        # Legacy background compilation loop (for hot path detection)
        if self._compilation_thread and self._compilation_thread.is_alive():
            return  # Already running

        self._stop_background_compilation.clear()
        self._compilation_thread = threading.Thread(
            target=self._background_compilation_loop,
            daemon=True
        )
        self._compilation_thread.start()

        logger.debug("Started background JIT hot path detection")
    
    def stop_background_compilation(self) -> None:
        """Stop background compilation thread (Phase 2.4: includes worker)."""
        # Phase 2.4: Stop compilation worker
        if self._compilation_worker:
            self._compilation_worker.stop()

        # Legacy thread
        self._stop_background_compilation.set()
        
        if self._compilation_thread:
            self._compilation_thread.join(timeout=5.0)
            self._compilation_thread = None
        
        logger.debug("Stopped background JIT compilation")
    
    def _background_compilation_loop(self) -> None:
        """
        Background loop for automatic hot path compilation.

        SPEC2 Task 12: Drains sys.monitoring compilation queue.

        CRITICAL FIX (Dec 2025): Reduced timeout from 10s to 2s to ensure
        compilation happens during warmup rather than delaying until steady-state.
        With 10s timeout and 4s warmup, compilation would happen during STEADY_1
        causing a 13+ second spike. 2s ensures at least one queue drain during warmup.
        """
        while not self._stop_background_compilation.wait(timeout=2.0):
            try:
                # SPEC2 Task 12: Process sys.monitoring hot functions first
                self._process_sysmon_queue()

                # Then compile analyzer-driven hot paths
                self._compile_hot_paths()
            except Exception as e:
                logger.error(f"Error in background compilation: {e}")
    
    def _process_sysmon_queue(self):
        """
        Process sys.monitoring compilation queue (SPEC2 Task 12).

        Drains functions marked hot by sys.monitoring and compiles them.
        """
        if not self.compilation_queue:
            return

        drained = []
        with self._lock:
            drained = list(self.compilation_queue)
            self.compilation_queue.clear()

        for func_name in drained:
            try:
                # Look up function object from registered functions
                if func_name not in self._registered_functions:
                    logger.debug(f"sys.monitoring hot '{func_name}' not registered; skipping")
                    continue

                func_obj = self._registered_functions[func_name]

                # Compile the function
                # P0.13 FIX (Dec 2025): sys.monitoring has ALREADY proven this function
                # is hot (execution count >= min_function_calls). We MUST bypass the
                # static call_count filter (FILTER 5) because static analysis returns
                # call_count=0 for notebook/REPL functions. Also skip benchmarking
                # since sys.monitoring already validated hotness.
                result = self.compile_function_auto(func_obj, bypass_call_count=True, skip_benchmark=True)
                if result != func_obj:
                    logger.debug(f"Compiled {func_name} from sys.monitoring queue (P0.13: bypass_call_count=True)")

            except Exception as e:
                logger.debug(f"Failed to compile {func_name} from sys.monitoring: {e}")

    def flush_compilation_queue(self, timeout_ms: float = 5000.0) -> int:
        """
        Force immediate processing of the compilation queue.

        CRITICAL FIX (Dec 2025): This method allows explicit flushing of hot
        functions that have been queued but not yet compiled. Call this after
        warmup iterations to ensure JIT compilation completes before steady-state.

        Use cases:
            - After warmup: Ensure all hot paths are compiled before measurement
            - Testing: Force compilation for deterministic benchmarks
            - Interactive: User wants to ensure compilation is done

        Args:
            timeout_ms: Maximum time to spend compiling (default 5000ms)

        Returns:
            Number of functions compiled
        """
        import time
        start_time = time.monotonic()
        compiled_count = 0
        deadline = start_time + (timeout_ms / 1000.0)

        # Process the queue immediately (bypass background loop timing)
        while self.compilation_queue and time.monotonic() < deadline:
            # Get next function to compile
            func_name = None
            with self._lock:
                if self.compilation_queue:
                    func_name = next(iter(self.compilation_queue))
                    self.compilation_queue.discard(func_name)

            if func_name is None:
                break

            try:
                # Look up function object
                if func_name not in self._registered_functions:
                    logger.debug(f"flush_compilation_queue: '{func_name}' not registered; skipping")
                    continue

                func_obj = self._registered_functions[func_name]

                # Compile the function
                # P0.13 FIX (Dec 2025): Functions in the compilation queue were added
                # because sys.monitoring detected them as hot (execution count >= threshold).
                # We MUST bypass static call_count filter (FILTER 5) and skip benchmarking
                # since runtime execution has already proven hotness.
                result = self.compile_function_auto(func_obj, bypass_call_count=True, skip_benchmark=True)
                if result != func_obj:
                    compiled_count += 1
                    logger.debug(f"flush_compilation_queue: Compiled {func_name} (P0.13: bypass_call_count=True)")

            except Exception as e:
                logger.debug(f"flush_compilation_queue: Failed to compile {func_name}: {e}")

        elapsed_ms = (time.monotonic() - start_time) * 1000
        logger.debug(f"flush_compilation_queue: Compiled {compiled_count} functions in {elapsed_ms:.1f}ms")
        return compiled_count

    def _should_compile(self, func_name: str) -> bool:
        """
        Determine if a function should be compiled based on system health.

        Task 3 - perf_fixes2.md: Pause compilation when allocator on fallback path
        to prevent memory pressure.

        Args:
            func_name: Name of function to check

        Returns:
            True if compilation should proceed, False if paused

        Reasons for pause:
            - Allocator on Python fallback (Cython module unavailable)
            - Memory pressure detected (future enhancement)
            - P0.14: Dunder methods (never compile)
        """
        # P0.14 FIX: Skip dunder methods - they cannot be JIT compiled by Numba
        # and attempting to compile them wastes 2+ seconds per method.
        # This is the CENTRAL gatekeeper that ALL compilation paths go through.
        if func_name in self._DUNDER_SKIP_LIST:
            return False

        # P0.21 FIX (Dec 2025): Skip module-level code (<module>)
        # Module-level code:
        # 1. Runs once at import (not a hot loop candidate)
        # 2. Can't be JIT compiled (uses STORE_NAME, STORE_GLOBAL opcodes)
        # 3. Causes "Use of unsupported opcode (STORE_NAME)" errors
        if func_name == '<module>':
            return False

        # CRITICAL FIX (Dec 28, 2025): Removed allocator health check that was blocking JIT
        # The previous logic paused ALL JIT compilation when the fast allocator was slow,
        # but this is incorrect because:
        # 1. JIT compilation happens in a background thread - minimal memory impact
        # 2. Blocking JIT defeats Epochly's core purpose (acceleration)
        # 3. Allocator performance and JIT compilation are independent systems
        # 4. This was causing 0.9x speedup (slower than baseline!) in demos
        #
        # The allocator health check was intended to prevent memory pressure, but
        # the actual cause of slow allocator is typically Cython module rebuild needed,
        # which doesn't affect JIT compilation at all.
        #
        # Original code (Task 3 - perf_fixes2.md) was removed here.
        # If memory pressure monitoring is needed in the future, it should be done
        # via a separate mechanism that doesn't block JIT compilation entirely.

        # Allow compilation (function name checks passed)
        return True

    def _compile_hot_paths(self) -> None:
        """Compile detected hot paths automatically."""
        # Get hot path candidates from analyzer
        candidates = self.jit_analyzer.get_hot_path_candidates(
            min_score=self.config.min_hot_path_score
        )
        
        for candidate in candidates:
            func_name = candidate.function_name

            # Task 3 - perf_fixes2.md: Check system health before compilation
            if not self._should_compile(func_name):
                continue  # Skip this function (health check failed)

            # SPEC2 Task 10: Use adaptive policy for intelligent compilation
            should_compile_candidate = candidate.should_compile
            if self._adaptive_policy and self._telemetry_store:
                # Record function call for adaptive policy
                self._telemetry_store.record_call(func_name)

                # Use adaptive policy to decide (overrides static analyzer)
                should_compile_adaptive = self._adaptive_policy.should_compile(
                    func_name, self._telemetry_store
                )
                # Use AND logic - both must agree
                should_compile_candidate = should_compile_candidate and should_compile_adaptive

            if should_compile_candidate:
                # Skip if already compiled, in queue, or previously failed (P0.14)
                with self._lock:
                    if (func_name in self.compiled_functions or
                        func_name in self.compilation_queue or
                        func_name in self._failed_compilations):
                        continue

                    self.compilation_queue.add(func_name)
                
                try:
                    # Get the function object from profiling system
                    func_obj = self.get_function_object_for_compilation(func_name)
                    if func_obj:
                        # Perform actual background compilation
                        logger.debug(f"Compiling hot path in background: {func_name} "
                                   f"(score: {candidate.hot_path_score:.1f})")

                        # compile_function_auto stores result in compiled_functions dict
                        compiled_func = self.compile_function_auto(func_obj)

                        # Check if compilation was successful by looking at stored result
                        with self._lock:
                            if func_name in self.compiled_functions:
                                result = self.compiled_functions[func_name]
                                if result.is_successful:
                                    logger.debug(f"Background compilation successful: {func_name}")

                                    # SPEC2 Task 10: Update adaptive policy with compilation result
                                    if self._adaptive_policy and self._telemetry_store:
                                        speedup = result.speedup if hasattr(result, 'speedup') else 1.0
                                        self._telemetry_store.record_compile(func_name, speedup)
                                        self._adaptive_policy.update(func_name, self._telemetry_store)
                                else:
                                    # P0.14: Add to failed cache to prevent retries
                                    self._failed_compilations.add(func_name)
                                    logger.debug(f"Background compilation failed: {func_name} (cached to prevent retry)")
                            else:
                                logger.debug(f"Compilation result not stored for: {func_name}")
                    else:
                        logger.debug(f"Function object not available for background compilation: {func_name}")
                    
                finally:
                    with self._lock:
                        self.compilation_queue.discard(func_name)
    
    def compile_function_auto(self, func: Callable, bypass_call_count: bool = False, skip_benchmark: bool = False) -> Optional[Callable]:
        """
        Automatically compile function if it meets JIT criteria.

        Checks persistent cache first for warm restart optimization.

        Args:
            func: Function to potentially compile
            bypass_call_count: If True, skip call_count filter (for auto-profiler hot detection)
            skip_benchmark: If True, skip benchmarking to avoid double execution (for auto-profiler)

        Returns:
            Compiled function if compilation was beneficial, original function otherwise
        """
        func_name = getattr(func, '__name__', str(func))

        # Task 3: Check system health before compilation
        if not self._should_compile(func_name):
            logger.debug(f"FILTER 1: Skipping compilation of {func_name} (system health check failed)")
            return func  # Return original function

        # Check memory cache first (fast path with double-check pattern)
        with self._lock:
            if func_name in self.compiled_functions:
                return self.compiled_functions[func_name].compiled_function

        # PHASE 3: Check persistent cache SECOND (warm restart optimization)
        if self._persistent_cache and self.config.enable_compilation_caching:
            try:
                characteristics = self.jit_analyzer.analyze_function(func)

                # CRITICAL: Check JIT suitability BEFORE loading from cache
                # Functions that call user-defined functions are NOT suitable
                # even if they were cached before (cache may be stale)
                if characteristics.jit_suitability not in [JITSuitability.EXCELLENT, JITSuitability.GOOD]:
                    logger.debug(f"FILTER CACHE: Function {func_name} not suitable for JIT: {characteristics.jit_suitability.value} - skipping cache")
                    return func

                backend = self._select_backend(characteristics)

                if backend:
                    # Try to load from persistent cache
                    cached_func = self._persistent_cache.load_compiled(func, backend.value)
                    if cached_func is not None:
                        logger.debug(f"Warm restart: Loaded {func_name} from persistent cache (backend: {backend.value})")

                        # Store in memory cache with double-check pattern (prevent TOCTOU race)
                        with self._lock:
                            # Double-check: another thread may have compiled while we were loading
                            if func_name in self.compiled_functions:
                                return self.compiled_functions[func_name].compiled_function

                            result = JITCompilationResult(
                                backend=backend,
                                status=BaseCompilationStatus.COMPILED,
                                compilation_time_ms=0.0,  # Cache hit - no compilation
                                function_name=func_name,
                                source_hash=self._persistent_cache._compute_code_hash(func),
                                compiled_function=cached_func,
                                speedup_ratio=1.5  # Assume cached functions were beneficial
                            )
                            self.compiled_functions[func_name] = result

                        return cached_func
            except Exception as e:
                logger.debug(f"Persistent cache lookup failed for {func_name}: {e}")
                # Continue with normal compilation path

        # Check if already compiled (in-memory cache)
        with self._lock:
            if func_name in self.compiled_functions:
                result = self.compiled_functions[func_name]
                if result.is_successful and result.has_performance_benefit:
                    logger.debug(f"Using cached compilation for {func_name}")
                    return result.compiled_function
                else:
                    logger.debug(f"FILTER 2: Previous compilation of {func_name} had no benefit, skipping")
                    return func  # Use original if compilation didn't help

        # Analyze function characteristics
        try:
            characteristics = self.jit_analyzer.analyze_function(func)
            logger.debug(f"Analyzed {func_name}: suitability={characteristics.jit_suitability.value}, call_count={characteristics.call_count}, bypass_call_count={bypass_call_count}")
        except Exception as e:
            logger.warning(f"FILTER 3: Failed to analyze function {func_name}: {e}")
            return func  # Return original if analysis fails

        # Check if function is suitable for JIT compilation
        if characteristics.jit_suitability not in [JITSuitability.EXCELLENT, JITSuitability.GOOD]:
            logger.debug(f"FILTER 4: Function {func_name} not suitable for JIT: {characteristics.jit_suitability.value}")
            return func

        # Check if function has enough calls (unless bypassed by auto-profiler)
        if not bypass_call_count and characteristics.call_count < self.config.min_function_calls:
            logger.debug(f"FILTER 5: Function {func_name} needs more calls for JIT: {characteristics.call_count} < {self.config.min_function_calls}")
            return func
        elif bypass_call_count:
            logger.debug(f"FILTER 5 BYPASSED: Auto-profiler hot detection (call_count={characteristics.call_count}) - compiling immediately")
        
        # Select best backend
        backend = self._select_backend(characteristics)
        if not backend:
            logger.debug(f"No suitable backend for {func_name}")
            return func
        
        # Compile the function
        result = self._compile_with_backend(func, backend)
        
        with self._lock:
            self.compiled_functions[func_name] = result
        
        if result.is_successful:
            # Benchmark the compiled function (unless skipped)
            if not skip_benchmark:
                speedup = self._benchmark_compilation(func, result.compiled_function)
                if speedup and speedup >= self.config.min_expected_speedup:
                    result.speedup_ratio = speedup

                    # PHASE 3: Save to persistent cache for warm restart
                    if self._persistent_cache and self.config.enable_compilation_caching:
                        try:
                            self._persistent_cache.save_compiled(
                                func,
                                result.compiled_function,
                                backend.value,
                                metadata={'speedup': speedup}
                            )
                            logger.debug(f"Saved {func_name} to persistent cache for warm restart")
                        except Exception as e:
                            logger.warning(f"Failed to save {func_name} to persistent cache: {e}")

                    logger.debug(f"Successfully compiled {func_name} with {backend.value}: "
                               f"{speedup:.2f}x speedup")
                    return result.compiled_function
                else:
                    logger.debug(f"Compilation of {func_name} did not meet performance threshold")
                    return func  # Return original if speedup not achieved
            else:
                # Skip benchmarking (auto-profiler already confirmed function is hot)
                # Set assumed speedup since auto-profiler pre-validated this function
                # This ensures has_performance_benefit returns True for beneficial_compilations tracking
                result.speedup_ratio = 1.5  # Assumed beneficial (same as cache hits)

                # PHASE 3: Still save to cache
                if self._persistent_cache and self.config.enable_compilation_caching:
                    try:
                        self._persistent_cache.save_compiled(
                            func,
                            result.compiled_function,
                            backend.value,
                            metadata={'skip_benchmark': True, 'assumed_speedup': 1.5}
                        )
                        logger.debug(f"Saved {func_name} to persistent cache (no benchmark)")
                    except Exception as e:
                        logger.warning(f"Failed to save {func_name} to persistent cache: {e}")

                logger.debug(f"Successfully compiled {func_name} with {backend.value} (benchmark skipped, assumed beneficial)")
                return result.compiled_function

        return func  # Return original if compilation failed
    
    def _select_backend(self, characteristics) -> Optional[JITBackend]:
        """
        Select the best JIT backend for a function.
        
        Args:
            characteristics: Function characteristics from analyzer
            
        Returns:
            Selected JIT backend or None if none suitable
        """
        # Map analyzer backend recommendations to JIT backends (Multi-JIT Strategy 2025)
        backend_mapping = {
            JITBackendType.NUMBA: JITBackend.NUMBA,
            JITBackendType.NATIVE: JITBackend.NATIVE,
            JITBackendType.PYSTON: JITBackend.PYSTON,
            JITBackendType.AUTO: None  # Will select automatically
        }
        
        recommended_backend = backend_mapping.get(characteristics.recommended_backend)
        
        # If specific backend recommended and available, use it
        if recommended_backend and recommended_backend in self.jit_compilers:
            return recommended_backend
        
        # Otherwise, select from available backends based on characteristics
        candidates = []
        
        for backend in self.config.preferred_backends:
            if backend in self.jit_compilers:
                score = self._score_backend_compatibility(backend, characteristics)
                candidates.append((backend, score))
        
        if candidates:
            # Sort by score and return best
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]
        
        return None
    
    def _score_backend_compatibility(self, backend: JITBackend, characteristics) -> float:
        """
        Score how well a backend fits function characteristics.
        
        Args:
            backend: JIT backend to score
            characteristics: Function characteristics
            
        Returns:
            Compatibility score (0-100)
        """
        score = 50.0  # Base score
        
        if backend == JITBackend.NUMBA:
            if characteristics.has_numpy_usage:
                score += 30
            if characteristics.has_numerical_ops:
                score += 20
            if characteristics.has_loops:
                score += 15
        
        elif backend == JITBackend.NATIVE:
            # Python 3.13+ native JIT for general code
            if characteristics.has_loops:
                score += 20
            if characteristics.operation_count > 10:
                score += 15
            if characteristics.call_count > 50:
                score += 10
        
        elif backend == JITBackend.PYSTON:
            # Pyston-Lite for general Python optimization
            if characteristics.has_loops:
                score += 25
            if characteristics.operation_count > 20:
                score += 20
            if characteristics.call_count > 100:
                score += 15
        
        return score
    
    def _compile_with_backend(self, func: Callable, backend: JITBackend) -> JITCompilationResult:
        """
        Compile function with specific backend.

        Args:
            func: Function to compile
            backend: JIT backend to use

        Returns:
            Compilation result
        """
        func_name = getattr(func, '__name__', str(func))

        # P0.14 FIX: Final safety net - block dunder methods at the compilation level.
        # This catches any requests that bypassed the _should_compile filter.
        if func_name in self._DUNDER_SKIP_LIST:
            return JITCompilationResult(
                backend=backend,
                status=BaseCompilationStatus.SKIPPED,
                compilation_time_ms=0.0,
                function_name=func_name,
                source_hash="",
                error_message=f"Dunder method '{func_name}' cannot be JIT compiled"
            )

        # P0.21 FIX (Dec 2025): Final safety net - block module-level code at compilation.
        # Module-level code (<module>):
        # 1. Runs once at import (not a hot loop candidate)
        # 2. Can't be JIT compiled (uses STORE_NAME, STORE_GLOBAL opcodes)
        # 3. Causes "Use of unsupported opcode (STORE_NAME)" errors
        # This catches requests that bypassed the _should_compile filter.
        if func_name == '<module>':
            return JITCompilationResult(
                backend=backend,
                status=BaseCompilationStatus.SKIPPED,
                compilation_time_ms=0.0,
                function_name=func_name,
                source_hash="",
                error_message="Module-level code '<module>' cannot be JIT compiled"
            )

        compiler = self.jit_compilers.get(backend)
        if not compiler:
            return JITCompilationResult(
                backend=backend,
                status=BaseCompilationStatus.FAILED,
                compilation_time_ms=0.0,
                function_name=func_name,
                source_hash="",
                error_message=f"Backend {backend.value} not available"
            )
        
        return compiler.compile_function(func)
    
    def _benchmark_compilation(self, original_func: Callable, compiled_func: Callable) -> Optional[float]:
        """
        Benchmark compiled function against original.

        Uses intelligent test argument generation to properly benchmark
        numerical functions with realistic workload sizes.

        Args:
            original_func: Original function
            compiled_func: Compiled function

        Returns:
            Speedup ratio or None if benchmark fails
        """
        try:
            import inspect

            # Generate intelligent test arguments
            test_args = self._generate_benchmark_args(original_func)
            test_kwargs = {}

            if test_args is None:
                logger.debug(f"Could not generate test arguments for {original_func.__name__}")
                return None

            # Try benchmarking with the backend's benchmark method
            for compiler in self.jit_compilers.values():
                try:
                    speedup = compiler.benchmark_function(original_func, compiled_func, *test_args, **test_kwargs)
                    if speedup and speedup > 0:
                        logger.debug(f"Benchmark result for {original_func.__name__}: {speedup:.1f}x speedup")
                        return speedup
                except Exception as e:
                    logger.debug(f"Backend benchmark failed: {e}")
                    continue

            return None

        except Exception as e:
            logger.debug(f"Benchmarking failed: {e}")
            return None

    def _generate_benchmark_args(self, func: Callable) -> Optional[list]:
        """
        Generate intelligent test arguments for benchmarking.

        Uses the centralized argument_inference module for consistent
        behavior across compilation triggers and benchmarking.

        Args:
            func: Function to generate arguments for

        Returns:
            List of test arguments or None if generation fails
        """
        try:
            from .argument_inference import (
                generate_arguments,
                generate_argument_configs,
                InferencePurpose,
            )

            # First try smart inference with BENCHMARK purpose (larger arrays)
            test_args = generate_arguments(func, InferencePurpose.BENCHMARK)
            if test_args is not None:
                # Validate arguments work with the original function
                try:
                    result = func(*test_args)
                    if result is not None:
                        return test_args
                    logger.debug(f"Function returned None with primary args, trying fallbacks")
                except Exception as e:
                    logger.debug(f"Primary benchmark args failed: {e}")

            # Fall back to trying multiple configurations
            configs = generate_argument_configs(func, InferencePurpose.BENCHMARK)
            for config in configs:
                try:
                    result = func(*config)
                    if result is not None:
                        logger.debug(f"Found working benchmark args with config")
                        return config
                except Exception:
                    continue

            return None

        except ImportError as e:
            logger.debug(f"Could not import argument_inference: {e}")
            return None
        except Exception as e:
            logger.debug(f"Argument generation failed: {e}")
            return None
    
    def profile_function_decorator(self, func: Callable) -> Callable:
        """
        Decorator to add JIT profiling and automatic compilation to a function.
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function with JIT integration
        """
        @functools.wraps(func)
        def jit_wrapper(*args, **kwargs):
            # Profile the function call
            start_time = time.perf_counter_ns()
            result = func(*args, **kwargs)
            execution_time = time.perf_counter_ns() - start_time
            
            # Record call data with analyzer
            self.jit_analyzer.profile_function_call(func, execution_time)
            
            # Check if we should try JIT compilation
            characteristics = self.jit_analyzer.get_function_characteristics(func.__name__)
            if (characteristics and 
                characteristics.call_count % 50 == 0 and  # Check every 50 calls
                characteristics.call_count >= self.config.min_function_calls):
                
                # Try automatic compilation
                compiled_func = self.compile_function_auto(func)
                if compiled_func != func:
                    # Replace the wrapper with compiled version
                    jit_wrapper.__wrapped__ = compiled_func
                    logger.debug(f"Switched to JIT compiled version of {func.__name__}")
            
            return result
        
        return jit_wrapper

    def queue_compilation(self, func: Callable, backend: Optional[JITBackend] = None, bypass_call_count: bool = False) -> bool:
        """
        Queue function for background compilation (Phase 2.4 non-blocking API).

        Returns immediately without blocking on compilation or benchmarking.

        P1 WARMUP OPTIMIZATION (Jan 2026): Respects compilation_mode setting.
        When compilation_mode is SYNCHRONOUS (via eager_mode() context manager),
        this method compiles synchronously instead of queueing.

        Args:
            func: Function to compile
            backend: Optional specific backend (auto-selected if None)
            bypass_call_count: If True, bypass static call_count filter (P0.13)

        Returns:
            True if queued/compiled successfully, False if queue full or paused
        """
        func_name = getattr(func, '__name__', str(func))

        # P1 WARMUP OPTIMIZATION: Synchronous mode bypasses background queue
        if self.compilation_mode == CompilationMode.SYNCHRONOUS:
            logger.debug(f"SYNCHRONOUS mode: compiling {func_name} immediately")
            compiled = self.compile_function_auto(func, bypass_call_count=bypass_call_count)
            return compiled is not None and compiled is not func

        if self._compilation_worker is None:
            # Fallback to synchronous compilation
            return False

        # Task 3: Check system health before queueing
        if not self._should_compile(func_name):
            logger.debug(f"Skipping queue_compilation for {func_name} (compilation paused)")
            return False  # Indicate "not queued" due to pause

        # Auto-select backend if not specified
        if backend is None:
            try:
                characteristics = self.jit_analyzer.analyze_function(func)
                backend = self._select_backend(characteristics)
            except Exception:
                backend = self.available_backends[0] if self.available_backends else JITBackend.NUMBA

        if backend is None:
            return False

        # Create compilation request
        from .compilation_worker import CompilationRequest
        request = CompilationRequest(
            function=func,
            function_name=func_name,
            backend=backend,
            priority=0,
            bypass_call_count=bypass_call_count  # P0.13: Propagate bypass flag
        )

        # Queue for background processing (non-blocking)
        return self._compilation_worker.queue_compilation(request)

    def get_compiled_artifact(self, func: Callable) -> Callable:
        """
        Get compiled function if available (Phase 2.4 non-blocking API).

        Returns immediately:
        - If compiled and beneficial: returns compiled function
        - If pending/compiling: returns original function
        - If failed: returns original function

        Callers never block waiting for compilation or benchmarking.

        Args:
            func: Original function

        Returns:
            Compiled function if available and beneficial, otherwise original
        """
        func_name = getattr(func, '__name__', str(func))

        # Check in-memory compiled_functions first (has actual CPUDispatcher objects)
        # This is the primary source for JIT-compiled functions
        with self._lock:
            if func_name in self.compiled_functions:
                result = self.compiled_functions[func_name]
                if result.is_successful and result.compiled_function is not None:
                    # Check if compilation was beneficial (speedup > 1.2x)
                    if result.speedup_ratio is None or result.speedup_ratio >= 1.2:
                        return result.compiled_function
                    else:
                        # Compilation not beneficial, return original
                        return func

        # Fall back to artifact store for cross-process artifacts
        if self._artifact_store is not None:
            compiled_func, status = self._artifact_store.get_or_pending(func_name, func)
            return compiled_func

        return func  # Not found anywhere

    def get_compilation_result(self, func: Callable) -> Optional[Dict[str, Any]]:
        """
        Get compilation result metadata (Phase 2.4).

        Returns metadata about compilation status, speedup, etc.

        Args:
            func: Function to check

        Returns:
            Dictionary with compilation info, or None if not found
        """
        if self._artifact_store is None:
            return None

        func_name = getattr(func, '__name__', str(func))
        artifact = self._artifact_store.get(func_name)

        if artifact is None:
            return None

        return {
            'status': artifact.status.value,
            'speedup': artifact.speedup_ratio,
            'backend': artifact.backend,
            'compiled_at': artifact.compiled_at,
            'benchmark_pending': artifact.status == CompilationStatus.BENCHMARKING
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive JIT manager statistics.
        
        Returns:
            Dictionary with JIT compilation metrics
        """
        with self._lock:
            # Aggregate compiler statistics
            compiler_stats = {}
            for backend, compiler in self.jit_compilers.items():
                compiler_stats[backend.value] = compiler.get_statistics()
            
            # Get analyzer statistics
            analyzer_stats = self.jit_analyzer.get_statistics()
            
            # Compilation summary
            total_compiled = len(self.compiled_functions)
            successful_compilations = sum(
                1 for result in self.compiled_functions.values()
                if result.is_successful
            )
            
            beneficial_compilations = sum(
                1 for result in self.compiled_functions.values()
                if result.has_performance_benefit
            )
            
            return {
                'available_backends': [b.value for b in self.available_backends],
                'compiler_statistics': compiler_stats,
                'analyzer_statistics': analyzer_stats,
                'total_compiled_functions': total_compiled,
                'successful_compilations': successful_compilations,
                'beneficial_compilations': beneficial_compilations,
                'compilation_queue_size': len(self.compilation_queue),
                'failed_compilations_cached': len(self._failed_compilations),  # P0.14
                'background_compilation_running': (
                    self._compilation_thread and self._compilation_thread.is_alive()
                ),
                'configuration': {
                    'min_hot_path_score': self.config.min_hot_path_score,
                    'min_function_calls': self.config.min_function_calls,
                    'min_expected_speedup': self.config.min_expected_speedup
                }
            }
    
    def cleanup(self) -> None:
        """Cleanup JIT manager resources."""
        self.stop_background_compilation()
        
        # Clear caches
        for compiler in self.jit_compilers.values():
            compiler.clear_cache()
        
        with self._lock:
            self.compiled_functions.clear()
            self.compilation_queue.clear()
            self._failed_compilations.clear()  # P0.14: Also reset failure cache
            self.performance_history.clear()

        logger.debug("JIT manager cleanup completed")
    
    def register_function_for_profiling(self, func: Callable) -> None:
        """
        Register a function for profiling and potential background compilation.

        Uses the LoopAwareJITClassifier to determine JIT strategy:
        - EAGER_JIT: Functions with loops are queued for immediate compilation
        - LAZY_JIT: Functions wait for min_function_calls threshold
        - NEVER_JIT: Trivial functions are skipped

        Args:
            func: Function to register for profiling
        """
        func_name = getattr(func, '__name__', str(func))

        # Classify function using bytecode analysis (ZERO runtime overhead)
        strategy = self._loop_classifier.classify(func)

        with self._lock:
            self._registered_functions[func_name] = func
            if func_name not in self._function_profiles:
                self._function_profiles[func_name] = []

        # EAGER_JIT: Queue for immediate compilation (solves Pattern B problem)
        if strategy == JITStrategy.EAGER_JIT:
            logger.debug(f"EAGER_JIT: Function '{func_name}' has loops, queuing for immediate compilation")
            # Queue for background compilation immediately
            # TYPE GUARD: queue_compilation requires callable, not string
            # This check catches the bug where func_name was passed instead of func
            # NOTE: Using explicit check instead of assert (assert can be stripped with -O)
            if not callable(func):
                raise TypeError(
                    f"queue_compilation requires a callable, got {type(func).__name__}"
                )
            # bypass_call_count=True ensures compilation happens even on first call
            self.queue_compilation(func, bypass_call_count=True)
        elif strategy == JITStrategy.NEVER_JIT:
            logger.debug(f"NEVER_JIT: Function '{func_name}' is trivial, skipping JIT")
        else:
            # LAZY_JIT: Wait for call count threshold (default behavior)
            logger.debug(f"LAZY_JIT: Registered function '{func_name}' for profiling")
    
    def get_function_object_for_compilation(self, func_name: str) -> Optional[Callable]:
        """
        Get function object for background compilation from profiling system.
        
        Args:
            func_name: Name of function to retrieve
            
        Returns:
            Function object if available, None otherwise
        """
        with self._lock:
            return self._registered_functions.get(func_name)
    
    def record_function_profile(self, func_name: str, execution_time: float) -> None:
        """
        Record function execution profile for optimization decisions.
        
        Args:
            func_name: Name of function
            execution_time: Execution time in seconds
        """
        with self._lock:
            if func_name not in self._function_profiles:
                self._function_profiles[func_name] = []
            
            self._function_profiles[func_name].append(execution_time)
            
            # Keep only recent profile data (last 1000 samples)
            if len(self._function_profiles[func_name]) > 1000:
                self._function_profiles[func_name] = self._function_profiles[func_name][-1000:]
    
    def get_function_profile(self, func_name: str) -> List[float]:
        """
        Get execution profile for a function.
        
        Args:
            func_name: Name of function
            
        Returns:
            List of execution times
        """
        with self._lock:
            return self._function_profiles.get(func_name, []).copy()
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore cleanup errors

    @contextmanager
    def eager_mode_context(self):
        """
        Context manager for synchronous compilation mode.

        P1 WARMUP OPTIMIZATION (Jan 2026): Enables synchronous compilation mode
        for the duration of the context. When inside this context, all compilation
        requests are processed immediately instead of being queued for background
        processing.

        This is useful for:
        - One-shot scripts that need predictable timing
        - Benchmarking where warmup should happen upfront
        - Testing where you need immediate compilation results

        Usage:
            jit_manager = JITManager()
            with jit_manager.eager_mode_context():
                # All compilation happens synchronously here
                result = heavy_computation(data)

        Note:
            The compilation mode change affects the entire JITManager instance.
            In multi-threaded scenarios, ensure only one thread uses eager_mode_context
            at a time, or coordinate mode changes externally.

        Yields:
            None
        """
        original_mode = self.compilation_mode
        try:
            self.compilation_mode = CompilationMode.SYNCHRONOUS
            logger.debug("Entered eager compilation mode (SYNCHRONOUS)")
            yield
        finally:
            self.compilation_mode = original_mode
            logger.debug(f"Exited eager compilation mode, restored to {original_mode.name}")


@contextmanager
def eager_mode(timeout_seconds: float = 120.0, wait_for_compilation: bool = True):
    """
    Context manager for synchronous JIT compilation mode.

    P1 WARMUP OPTIMIZATION (Jan 2026): Enables synchronous compilation for
    one-shot scripts that need predictable timing. When inside this context,
    all JIT compilation happens immediately instead of in the background.

    This is ideal for:
    - Data processing scripts that run once
    - Benchmarking where warmup should happen upfront
    - Testing where you need immediate compilation results

    Without eager_mode():
        - Run 1: ~60s (background compilation + Python fallback)
        - Run 2: ~40s (canary verification)
        - Run 3: ~3s (full compiled speed)

    With eager_mode():
        - Run 1: ~10s upfront compilation, then ~3s execution
        - No variance between runs

    Args:
        timeout_seconds: Maximum time to wait for pending compilations (default: 120s)
        wait_for_compilation: If True, waits for any pending compilations to complete
                             when exiting the context (default: True)

    Usage:
        import epochly

        # For one-shot scripts:
        with epochly.eager_mode():
            epochly.auto_enable()
            epochly.set_level(3)
            result = heavy_computation(data)  # Compiled synchronously

    Yields:
        None
    """
    try:
        from ..core.epochly_core import get_epochly_core
        core = get_epochly_core()
    except ImportError:
        # Epochly core not available, yield immediately
        logger.warning("eager_mode: Epochly core not available, no effect")
        yield
        return

    if core is None or not hasattr(core, 'jit_manager') or core.jit_manager is None:
        logger.warning("eager_mode: JIT manager not available, no effect")
        yield
        return

    jit_manager = core.jit_manager
    original_mode = jit_manager.compilation_mode

    try:
        jit_manager.compilation_mode = CompilationMode.SYNCHRONOUS
        logger.info("Entered eager compilation mode (SYNCHRONOUS)")
        yield

        if wait_for_compilation:
            # Wait for any pending background compilations to complete
            # (In synchronous mode, there shouldn't be any, but this ensures
            # any pre-existing background work finishes)
            start_time = time.time()
            while time.time() - start_time < timeout_seconds:
                if hasattr(jit_manager, '_compilation_worker') and jit_manager._compilation_worker:
                    worker = jit_manager._compilation_worker
                    if hasattr(worker, '_queue') and worker._queue.empty():
                        break
                else:
                    break
                time.sleep(0.1)
    finally:
        jit_manager.compilation_mode = original_mode
        logger.info(f"Exited eager compilation mode, restored to {original_mode.name}")