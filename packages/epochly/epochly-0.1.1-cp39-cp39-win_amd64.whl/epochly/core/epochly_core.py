"""
Epochly Core System

Central orchestrator for the Epochly framework.
Manages progressive enhancement levels and system initialization.
"""

# FUTURE-USE: Core system imports for planned Epochly implementation
import os        # FUTURE-USE: Shared memory file descriptors, /proc hardware detection, guard page alignment
import sys       # FUTURE-USE: System configuration, memory limits, reference counting, sub-interpreter management
import threading # FUTURE-USE: Thread-local storage, hardware thread affinity, sub-interpreter threading
import time      # FUTURE-USE: Hardware timing, performance benchmarking, timeout management
import multiprocessing  # FUTURE-USE: CPU count detection for Level 3 sub-interpreter pool sizing
from typing import Dict, Any, Callable, Optional, Union
from concurrent.futures import Future
from enum import Enum
import platform  # FUTURE-USE: Hardware fingerprinting, NUMA topology, platform-specific allocators
import functools  # Task 3: LRU cache for Level 3 compatibility checks
import re  # Task 3: Precompiled regex patterns for faster pattern matching
import inspect  # For source code analysis
from itertools import islice  # Phase 2.1: O(1) routing optimization

# Routing optimization constants
SAMPLING_MAX_ARGS = 5  # Phase 2.1: Sample size for argument inspection

from ..utils.logger import get_logger
from ..plugins.plugin_manager import PluginManager
from ..licensing.license_enforcer import check_core_limit

# CRITICAL: Worker protection function against fork bomb
# MUST be function (not constant) to check env vars at RUNTIME
# Workers set env vars AFTER module imports, so module-level constant would be too early
def _is_worker_process():
    """
    Runtime check for worker process.

    CRITICAL: Must check at call time, not module load time.
    Workers set EPOCHLY_DISABLE_* AFTER importing modules.
    """
    return (os.environ.get('EPOCHLY_DISABLE_INTERCEPTION') == '1' or
            os.environ.get('EPOCHLY_DISABLE') == '1')


# ============================================================================
# Task 4: DetectionThread - Managed Worker for Background Detection
# ============================================================================

class DetectionThread(threading.Thread):
    """
    Managed worker thread for background capability detection.

    Performance Improvement (Task 4/6):
    - Daemon threads for non-blocking exit (capability detection is non-critical)
    - Integrated stop event for graceful termination
    - Supports exponential backoff joins in shutdown
    - Registry-based lifecycle management

    Replaces ad-hoc daemon threads with unified lifecycle management.

    CRITICAL FIX (Nov 17, 2025): Changed to daemon=True after functional test analysis.
    Memory-bank guidance clarification:
    - daemon=False: For sub-interpreter workers managing state (SubInterpreterPool)
    - daemon=True: For monitoring/detection that doesn't need guaranteed completion
    DetectionThreads only detect capabilities - daemon=True allows clean exit.
    Defense-in-depth: shutdown() still properly stops threads when called explicitly.
    """

    def __init__(self, name: str, target: Callable):
        """
        Initialize detection thread.

        Args:
            name: Thread name for identification
            target: Target function to run (should accept stop_event parameter)
        """
        # CRITICAL FIX: daemon=True for capability detection threads
        # These threads DON'T manage sub-interpreters - just detect capabilities
        # Per memory-bank/THREAD-LIFECYCLE-GUIDANCE.md:
        #   - daemon=False: For sub-interpreter workers needing cleanup
        #   - daemon=True: For monitoring/detection that can be interrupted
        # DetectionThreads are capability detection → daemon=True
        # SubInterpreter worker threads remain daemon=False (correct)
        super().__init__(name=name, daemon=True)
        self._stop_event = threading.Event()  # Renamed: _stop conflicts with Thread._stop()
        self._target = target

    def run(self):
        """
        Execute target function with stop event monitoring.

        Target function should periodically check stop event and exit gracefully.
        """
        try:
            # Call target with stop event
            self._target(self._stop_event)
        except Exception as e:
            # Log but don't crash
            logger = get_logger(__name__)
            logger.debug(f"Detection thread {self.name} error: {e}")

    def request_stop(self):
        """Request thread to stop gracefully by setting stop event."""
        self._stop_event.set()

    def is_stop_requested(self) -> bool:
        """Check if stop has been requested."""
        return self._stop_event.is_set()


class EnhancementLevel(Enum):
    """
    Progressive enhancement levels for Epochly optimization.

    Each level builds upon the previous, with increasing capability
    and overhead requirements.
    """
    LEVEL_0_MONITOR = 0   # Lightweight monitoring only (baseline)
    LEVEL_1_THREADING = 1  # Basic thread optimizations
    LEVEL_2_JIT = 2       # JIT compilation enabled
    LEVEL_3_FULL = 3      # Full optimization with sub-interpreters
    LEVEL_4_GPU = 4       # GPU acceleration (if available)


class EpochlyCore:
    """
    Core orchestrator for Epochly framework.

    Implements singleton pattern with thread-safe initialization.
    Manages the progressive enhancement system and coordinates
    all optimization features.
    """

    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        """
        Thread-safe singleton creation.

        Uses double-checked locking pattern for efficient thread-safe
        singleton initialization.

        CRITICAL: We store _singleton_initialized on the instance, not the class,
        because we need per-instance tracking for EpochlyCore.

        Returns:
            EpochlyCore: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._singleton_initialized = False
        return cls._instance

    def __init__(self, performance_config=None):
        """
        Initialize Epochly core system.

        Args:
            performance_config: Optional PerformanceConfig for tuning (perf_fixes5.md Issue F)
        """
        if self._singleton_initialized:
            return

        # CRITICAL: Worker protection - prevent core initialization in worker processes
        # mcp-reflect hardening recommendation: Runtime assertion to catch worker init attempts
        #
        # FIX (Dec 2025): Use multiprocessing.current_process() for reliable worker detection
        # The EPOCHLY_DISABLE env var alone is unreliable because:
        # - Background threads can set it in main process during pool spawn
        # - It may be stale from previous test runs
        # - Race conditions between test fixture cleanup and thread execution
        #
        # New logic:
        # 1. Check if we're ACTUALLY in a worker process (not MainProcess)
        # 2. If in main process, clear any stale EPOCHLY_DISABLE
        # 3. If in worker process AND EPOCHLY_DISABLE=1, raise error
        import multiprocessing
        current_proc = multiprocessing.current_process()
        is_main_process = current_proc.name == "MainProcess"

        if is_main_process:
            # Main process - clear any stale EPOCHLY_DISABLE from previous spawns
            # This prevents test isolation issues where background threads leave it set
            if os.environ.get('EPOCHLY_DISABLE') == '1':
                os.environ.pop('EPOCHLY_DISABLE', None)
                os.environ.pop('EPOCHLY_DISABLE_INTERCEPTION', None)
        else:
            # Worker process - check if we should block initialization
            if os.environ.get('EPOCHLY_DISABLE') == '1' or os.environ.get('EPOCHLY_DISABLE_INTERCEPTION') == '1':
                import sys
                error_msg = (
                    "CRITICAL: Attempted to initialize EpochlyCore in worker process. "
                    f"Worker processes must not initialize Epochly (process={current_proc.name}, "
                    "EPOCHLY_DISABLE=1 detected). "
                    "This indicates worker_initializer is not being called or is failing."
                )
                print(error_msg, file=sys.stderr)
                raise RuntimeError(error_msg)

        self._singleton_initialized = True
        self._initialized = False
        self._closed = False
        self.logger = get_logger(__name__)
        self._config = None  # Lazy initialization

        # perf_fixes5.md Issue F: Performance configuration for Level 3/4 tuning
        if performance_config is None:
            from ..performance_config import DEFAULT_PERFORMANCE_CONFIG
            self.performance_config = DEFAULT_PERFORMANCE_CONFIG
        else:
            self.performance_config = performance_config
        self.logger.debug(f"Performance config initialized: {self.performance_config.to_dict()}")

        self.performance_monitor = None
        self.plugin_manager = None
        self._current_level = EnhancementLevel.LEVEL_0_MONITOR  # Backing attribute
        self.enabled = True
        self._disabled_reason: Optional[str] = None  # RCA: Track WHY enabled became False
        self._compatibility_checked = False
        self._lock = threading.RLock()

        # Background initialization events for thread-safe lazy init
        # NOTE: Level 3 uses existing background detection system (_upgrade_to_level_3_full)
        # so no separate init thread needed
        self._level2_init_complete = threading.Event()
        self._level3_init_complete = threading.Event()
        self._level4_init_complete = threading.Event()

        # P1-1: Level change notification event (replaces polling with immediate notification)
        # Signaled whenever current_level changes, allowing waiters to wake immediately
        self._level_changed_event = threading.Event()

        # CRITICAL FIX (2025-11-24): Lazy Level 3 initialization to prevent fork bomb
        # When True, Level 3 is requested but executor not yet created.
        # Executor will be created on first actual use via _ensure_level3_initialized()
        self._level3_deferred = False
        self._level3_worker_count = None  # Saved for deferred init

        # TASK 4: Unified thread registry for lifecycle management (non-daemon threads)
        # Replaces individual stop events and thread tracking with centralized registry
        self._detection_threads: Dict[str, DetectionThread] = {}
        self._thread_lock = threading.Lock()  # Protects registry operations

        # Phase 2.3: Cached capability results (eliminate redundant imports)
        self._cached_full_optimization_support: Optional[bool] = None
        self._capabilities_cache_time: float = 0.0
        self._capabilities_cache_ttl: float = 300.0  # 5 minutes TTL

        # Phase 4.2: Adaptive threshold tuning from allocator telemetry
        self._threshold_adjuster = None
        try:
            from ..enhancement.adaptive_thresholds import get_threshold_adjuster
            self._threshold_adjuster = get_threshold_adjuster()
        except ImportError:
            pass

        # Phase 4.1: Load capability manifest for fast startup (10-50× faster)
        self._capability_manifest = None
        try:
            from ..enhancement.capability_manifest import get_capability_manifest
            self._capability_manifest = get_capability_manifest()
            self.logger.debug(f"Capability manifest loaded: {self._capability_manifest.physical_cores} cores")
        except ImportError:
            pass

        # GPU acceleration attributes
        self.gpu_available = False
        self.gpu_manager = None
        self.gpu_memory_threshold = 10 * 1024 * 1024  # 10MB threshold

        # Progressive enhancement validation
        self.progression_manager = None  # Initialized in initialize()

        # Auto emergency detector (R-SAFE-04: Auto-disable on degradation)
        self._auto_emergency_detector = None  # Initialized in initialize()

        # Auto-profiling for hot loop detection (product vision)
        self._auto_profiler = None  # Initialized when enabled

        # Level 1 thread executor (lazy initialization)
        self._thread_executor = None
        self._thread_executor_lock = threading.Lock()

        # Fix #2: JIT readiness flag to prevent premature access
        # Set to True after JIT manager is fully initialized in _initialize_jit_system()
        self._jit_ready = False

        # FIX (Jan 2026): Track highest initialized level for fast-path optimization
        # P0.26 added on-demand initialization checks (hasattr) that run on EVERY call,
        # causing +11.9% overhead for Level 1. This attribute enables fast-path:
        # - Integer comparison (essentially free) instead of multiple hasattr() calls
        # - Level 1 calls skip all init checks immediately after first call
        # - See planning/benchmark-regression-rca.md for full analysis
        self._initialized_level = 0  # Track highest level that's been initialized

        # Phase 2 (Dec 2025): Early ProcessPool spawn during stability wait
        # Addresses RCA finding: Workers take ~8s to spawn AFTER stability wait.
        # By starting spawn DURING stability wait, we hide most of the spawn time.
        # See planning/rca-level3-warmup-spike.md for details.
        self._spawn_future: Optional['Future'] = None  # Tracks async spawn Future
        self._spawn_lock = threading.Lock()  # Protects spawn state
        self._spawn_started = False  # Prevents duplicate spawns
        self._stop_spawn_event: Optional[threading.Event] = None  # Allow aborting spawn
        self._spawn_thread: Optional[threading.Thread] = None  # Track spawn thread for shutdown

        # Phase 2 (Dec 2025): Forkserver initialization tracking
        # Forkserver provides fast worker spawn (~50ms vs ~650ms for spawn)
        # Must be initialized BEFORE any threads are created (safety requirement)
        # See planning/level3-processpool-optimization-plan.md
        self._forkserver_init_attempted = False  # Ensures we only try once

    @property
    def config(self):
        """Lazy initialization of ConfigManager to prevent import-time side effects."""
        if self._config is None:
            # Use factory to get appropriate config implementation
            # This import can raise ImportError if modules are broken
            from ..utils.config_factory import get_config
            self._config = get_config()
        return self._config

    @property
    def current_level(self) -> EnhancementLevel:
        """
        Current enhancement level.

        P1-1: Converted to property to enable event-based notification.
        When the level changes, _level_changed_event is signaled so waiters
        can wake immediately instead of polling.
        """
        return self._current_level

    @current_level.setter
    def current_level(self, value: EnhancementLevel) -> None:
        """
        Set the current enhancement level.

        P1-1: Signals _level_changed_event when level actually changes.
        This allows background threads and external callers to wake immediately
        instead of polling with sleep intervals.

        RCA (Dec 2025): Warns if level is set while enabled=False. This catches
        the bug where background threads set current_level without checking enabled.

        Telemetry (Jan 2026): Emits level_transition event to AWS/Lens for fleet
        visibility when enhancement level changes.
        """
        if value != self._current_level:
            # Capture old level for telemetry before changing
            old_level = self._current_level

            # RCA: Warn if setting level while disabled - this indicates a bug
            if not self.enabled and value.value > EnhancementLevel.LEVEL_0_MONITOR.value:
                self.logger.warning(
                    f"INCONSISTENT STATE: Setting current_level to {value.name} but enabled=False. "
                    f"Disabled reason: {self._disabled_reason or 'unknown'}. "
                    f"JIT may not work reliably."
                )
            self._current_level = value
            # Signal all waiters that level has changed
            self._level_changed_event.set()

            # Emit level transition telemetry to AWS/Lens (non-blocking)
            self._emit_level_transition_telemetry(old_level, value)
        # Note: If setting same value, don't signal (no actual change)

    def wait_for_level(
        self,
        target_level: EnhancementLevel,
        timeout: Optional[float] = None
    ) -> bool:
        """
        Wait for the enhancement system to reach a target level.

        P1-1: Public method for external callers (like notebooks) to wait
        for level changes without polling.

        Args:
            target_level: The minimum level to wait for.
            timeout: Maximum time to wait in seconds. None = wait forever.

        Returns:
            True if target level was reached, False if timeout occurred.

        Example:
            # Wait up to 5 seconds for JIT to be ready
            if core.wait_for_level(EnhancementLevel.LEVEL_2_JIT, timeout=5.0):
                # JIT is ready, proceed with optimized execution
                pass
            else:
                # Timeout, fall back to Level 1
                pass
        """
        deadline = None if timeout is None else (time.time() + timeout)

        while True:
            # Check if already at or above target level
            if self._current_level.value >= target_level.value:
                return True

            # Calculate remaining time
            if deadline is not None:
                remaining = deadline - time.time()
                if remaining <= 0:
                    return False
            else:
                remaining = None

            # Clear event before waiting (to catch the next change)
            self._level_changed_event.clear()

            # Double-check after clearing (level may have changed)
            if self._current_level.value >= target_level.value:
                return True

            # Wait for level change notification
            self._level_changed_event.wait(timeout=remaining)

    def _emit_level_transition_telemetry(
        self,
        from_level: EnhancementLevel,
        to_level: EnhancementLevel
    ) -> None:
        """
        Emit level transition telemetry to AWS/Lens (non-blocking).

        Per telemetry-audit-findings.md GAP #4: Level 0-4 transitions must
        be tracked for Lens fleet visibility.

        Args:
            from_level: Previous enhancement level
            to_level: New enhancement level

        Thread Safety:
            Safe to call from any thread. Uses try/except to ensure
            telemetry failures never affect core functionality.
        """
        try:
            from ..telemetry.routing_events import get_routing_emitter
            emitter = get_routing_emitter()
            if emitter:
                # Determine transition reason based on level change direction
                if to_level.value > from_level.value:
                    reason = f"upgrade_{from_level.name}_to_{to_level.name}"
                elif to_level.value < from_level.value:
                    reason = f"rollback_{from_level.name}_to_{to_level.name}"
                else:
                    reason = f"reinitialization_{to_level.name}"

                emitter.emit_level_transition(
                    from_level=from_level.value,
                    to_level=to_level.value,
                    reason=reason
                )
                self.logger.debug(
                    f"Level transition telemetry emitted: {from_level.name} -> {to_level.name}"
                )
        except Exception as e:
            # Telemetry failures must never affect core functionality
            self.logger.debug(f"Failed to emit level transition telemetry: {e}")

    def _get_thread_executor(self):
        """
        Lazy initialization of ThreadExecutor for Level 1 threading enhancement.

        Uses double-checked locking pattern for thread-safe singleton creation.
        ThreadExecutor is only created when Level 1 is active and work is submitted.

        Returns:
            ThreadExecutor instance (cached after first creation)

        Architecture Reference:
            - perf-spec3.md lines 95-137: Level 1 thread executor integration
            - ThreadExecutor provides adaptive thread pool with platform-aware sizing
        """
        # Fast path: already initialized
        if self._thread_executor is not None:
            return self._thread_executor

        # Slow path: initialize with lock
        with self._thread_executor_lock:
            # Double-check: another thread may have initialized
            if self._thread_executor is not None:
                return self._thread_executor

            try:
                from ..plugins.executor.thread_executor import ThreadExecutor

                # mcp-reflect Issue #1: Pass allocator and PerformanceConfig to Level 1
                # Get allocator if available
                allocator = None
                if hasattr(self, '_shared_memory_manager') and self._shared_memory_manager:
                    try:
                        allocator = self._shared_memory_manager.get_allocator()
                    except Exception:
                        pass

                # Create ThreadExecutor with allocator and config
                self._thread_executor = ThreadExecutor(
                    enable_dynamic_scaling=True,
                    max_workers=None,  # Platform-aware default
                    min_workers=None,  # Auto-calculated from max
                    allocator=allocator,  # perf_fixes5.md Issue D.2
                    performance_config=self.performance_config  # perf_fixes5.md Finding #2
                )

                self.logger.debug("ThreadExecutor initialized for Level 1 threading enhancement")

            except ImportError as e:
                self.logger.warning(f"ThreadExecutor not available: {e}")
                self._thread_executor = None
            except Exception as e:
                self.logger.error(f"Failed to initialize ThreadExecutor: {e}")
                self._thread_executor = None

        return self._thread_executor

    def initialize(self) -> bool:
        """
        Initialize the Epochly system.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        try:
            self.logger.debug("Initializing Epochly Core System")

            # Check system compatibility
            if not self._check_compatibility():
                self._disabled_reason = "System compatibility check failed"
                self.logger.error(f"EPOCHLY DISABLED: {self._disabled_reason}")
                self.enabled = False
                return False

            # Attempt to restore state from previous session
            try:
                from ..core.state_manager import get_state_manager
                state_manager = get_state_manager()
                saved_state = state_manager.load_state()
                if saved_state:
                    self.logger.debug(f"Found saved state from {saved_state.get('timestamp', 'unknown')}s ago")
                    # State will be restored after components are initialized
                    self._pending_state_restore = saved_state
                else:
                    self._pending_state_restore = None
            except Exception as e:
                self.logger.debug(f"Could not load saved state: {e}")
                self._pending_state_restore = None

            # CRITICAL (Dec 2025 - Phase 3): Initialize forkserver BEFORE any threads exist
            # Forkserver provides ~10× faster worker spawn (50-100ms vs 650ms per worker)
            # but MUST be initialized while only MainThread exists.
            # This MUST happen before _initialize_monitoring() which starts AlertWorker thread.
            if not self._forkserver_init_attempted:
                self._forkserver_init_attempted = True
                try:
                    from .forkserver_manager import try_initialize_forkserver, get_forkserver_state
                    state = try_initialize_forkserver()
                    self.logger.debug(f"Forkserver initialization: {state.value}")
                except ImportError as e:
                    self.logger.debug(f"Forkserver manager not available: {e}")
                except Exception as e:
                    self.logger.warning(f"Forkserver initialization error: {e}")

            # Initialize components
            self._initialize_monitoring()
            self._initialize_plugins()

            # CRITICAL: DO NOT initialize auto-profiler during core init
            # It will be enabled at Level 2+ when JIT is available
            # Level 0/1 must have minimal overhead (<1% not 15× slowdown from sys.settrace)
            self._auto_profiler = None  # Will be initialized at Level 2+

            # Initialize progressive enhancement validation
            from .enhancement_progression import EnhancementProgressionManager
            self.progression_manager = EnhancementProgressionManager(self)

            # Record initial level start time
            self.progression_manager.level_start_time[EnhancementLevel.LEVEL_0_MONITOR.value] = time.time()

            # Initialize automatic emergency detector (R-SAFE-04)
            # Monitors error rate, memory failures, and latency to auto-trigger emergency disable
            from ..monitoring.auto_emergency_detector import AutoEmergencyDetector
            self._auto_emergency_detector = AutoEmergencyDetector(
                progression_manager=self.progression_manager,
                emergency_disable_callback=self._handle_auto_emergency_disable
            )
            self._auto_emergency_detector.start()

            # Start with fast level determination (monitoring only)
            # Returns True if EPOCHLY_LEVEL was set (skip background detection)
            explicit_level_set = self._determine_enhancement_level_fast()

            # Record LEVEL_1 start time if we upgraded (for stability tracking)
            # This is critical for transparent acceleration to work
            if self.current_level == EnhancementLevel.LEVEL_1_THREADING:
                self.progression_manager.level_start_time[EnhancementLevel.LEVEL_1_THREADING.value] = time.time()

            # Begin background capability detection for progressive enhancement
            # Skip if explicit level was set via EPOCHLY_LEVEL
            if not explicit_level_set:
                self._start_background_capability_detection()
            else:
                self.logger.debug("Skipping background detection (explicit EPOCHLY_LEVEL set)")

            # Note: JIT and Level 3 initialization now happens in background
            # when capabilities are confirmed. This ensures fast startup.

            self._initialized = True

            # Restore state if available (after components are initialized)
            if hasattr(self, '_pending_state_restore') and self._pending_state_restore:
                try:
                    from ..core.state_manager import get_state_manager
                    state_manager = get_state_manager()
                    if state_manager.restore_state(self, self._pending_state_restore):
                        self.logger.debug("Successfully restored previous session state")
                    self._pending_state_restore = None
                except Exception as e:
                    self.logger.debug(f"Could not restore state: {e}")

            # Don't register atexit here - it's already handled by __init__.py
            # atexit.register(self.shutdown)

            self.logger.debug(f"Epochly initialized successfully at {self.current_level.name}")
            return True

        except Exception as e:
            self._disabled_reason = f"Initialization failed: {e}"
            self.logger.error(f"EPOCHLY DISABLED: {self._disabled_reason}")
            self.enabled = False
            return False

    def _check_compatibility(self) -> bool:
        """
        Check system compatibility for Epochly features.

        Returns:
            bool: True if system is compatible
        """
        if self._compatibility_checked:
            return True

        try:
            # Check Python version
            if sys.version_info < (3, 8):
                self.logger.warning("Python 3.8+ required for Epochly")
                return False

            # Check platform support
            supported_platforms = ['Windows', 'Linux', 'Darwin']
            if platform.system() not in supported_platforms:
                self.logger.warning(f"Platform {platform.system()} not fully supported")

            # Check for required modules
            required_modules = ['threading', 'multiprocessing', 'ctypes']
            for module in required_modules:
                try:
                    __import__(module)
                except ImportError:
                    self.logger.warning(f"Required module {module} not available")
                    return False

            # Check for optional performance modules
            optional_modules = ['numpy', 'psutil']
            for module in optional_modules:
                try:
                    __import__(module)
                    self.logger.debug(f"Optional module {module} available")
                except ImportError:
                    self.logger.debug(f"Optional module {module} not available")

            self._compatibility_checked = True
            return True

        except Exception as e:
            self.logger.error(f"Compatibility check failed: {e}")
            return False

    def _initialize_monitoring(self):
        """Initialize performance monitoring system."""
        try:
            # Use the global performance monitor instance to ensure consistency
            from ..monitoring.performance_monitor import get_performance_monitor
            self.performance_monitor = get_performance_monitor()
            self.performance_monitor.start()
            self.logger.debug("Performance monitoring initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize monitoring: {e}")
            raise

    def _initialize_plugins(self):
        """Initialize plugin management system."""
        try:
            self.plugin_manager = PluginManager()
            self.plugin_manager.load_plugins()
            self.logger.debug("Plugin system initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize plugins: {e}")
            raise

    def _initialize_auto_profiler(self):
        """
        Initialize auto-profiling system for hot loop detection.

        Product Vision: "The profiler marks any loop or function exceeding 10 ms CPU,
        slices data, dispatches to workers and wraps with numba.njit"

        Architecture:
        - Uses sys.monitoring on Python 3.12+ (low overhead)
        - Falls back to sys.settrace on older Python versions
        - Detects loops exceeding 10ms CPU time threshold
        - Enables automatic JIT compilation and data slicing
        """
        self.logger.debug("_initialize_auto_profiler() called")
        try:
            from ..profiling.auto_profiler import initialize_auto_profiler

            self.logger.debug("About to call initialize_auto_profiler()...")
            # Initialize with 10ms threshold (per product vision)
            self._auto_profiler = initialize_auto_profiler(cpu_threshold_ms=10.0)
            self.logger.debug(f"initialize_auto_profiler() returned: {self._auto_profiler}")

            # Connect RuntimeLoopTransformer for anticipatory transformation
            try:
                from ..profiling.runtime_loop_transformer import create_runtime_loop_transformer

                # CRITICAL FIX (Dec 2025): Pass permanent failure callback at creation
                # Ensures extraction failures immediately disable monitoring (no retry overhead)
                loop_transformer = create_runtime_loop_transformer(
                    min_iterations=1000,
                    on_permanent_failure=self._auto_profiler._mark_permanent_failure
                )
                self._auto_profiler.set_loop_transformer(loop_transformer)
                self.logger.debug("Loop transformer connected to auto-profiler (eager transformation enabled)")
            except Exception as e:
                self.logger.warning(f"Failed to connect loop transformer: {e}")
                # Continue without loop transformation

            # Enable auto-profiling
            self.logger.debug("About to call self._auto_profiler.enable()...")
            self._auto_profiler.enable()
            self.logger.debug("self._auto_profiler.enable() completed")

            self.logger.debug("Auto-profiler initialized (10ms CPU threshold)")

        except ImportError as e:
            self.logger.warning(f"Auto-profiler not available (ImportError): {e}")
            self._auto_profiler = None
        except Exception as e:
            self.logger.warning(f"Failed to initialize auto-profiler: {e}")
            import traceback
            self.logger.warning(f"Traceback: {traceback.format_exc()}")
            self._auto_profiler = None
            # Don't raise - auto-profiling is optional enhancement

    def _initialize_jit_system(self):
        """Initialize JIT compilation system for Level 2 enhancement."""
        try:
            # CRITICAL FIX (Dec 2025): Idempotency check - prevent double initialization
            # If called multiple times, the second call would try to start CompilationWorker
            # thread again, causing "thread already started" exception which destroys the
            # JIT manager. This bug caused ALL notebooks to have zero speedup!
            if hasattr(self, '_jit_manager') and self._jit_manager is not None:
                self.logger.debug("JIT system already initialized - skipping")
                return

            # CRITICAL: Check if JIT is explicitly disabled via environment variable
            import os
            if os.environ.get('EPOCHLY_JIT_ENABLED') == '0':
                self.logger.debug("JIT explicitly disabled via EPOCHLY_JIT_ENABLED=0")
                # Set JIT manager to None to indicate JIT is disabled
                self._jit_manager = None
                # Still need orchestrator for memory pool management
                # but without JIT coordination
                return

            # CRITICAL: Stop existing JIT manager threads to prevent multiple background threads
            # FIX (Dec 2025): Also stop JIT manager, not just orchestrator
            if hasattr(self, '_jit_manager') and self._jit_manager:
                try:
                    self._jit_manager.stop_background_compilation()
                    self.logger.debug("Stopped existing JIT manager threads before re-init")
                except Exception as e:
                    self.logger.warning(f"Failed to stop existing JIT manager: {e}")

            # CRITICAL: Stop existing orchestrator to prevent multiple background threads
            if hasattr(self, '_adaptive_orchestrator') and self._adaptive_orchestrator:
                try:
                    self._adaptive_orchestrator.stop_monitoring()
                    self.logger.debug("Stopped existing adaptive orchestrator before re-init")
                except Exception as e:
                    self.logger.warning(f"Failed to stop existing orchestrator: {e}")

            # SPEC2 Task 2: Initialize ArgumentSizer for Level 2+ hot paths
            from ..enhancement.argument_sizer import ArgumentSizer
            self._argument_sizer = ArgumentSizer(max_cache_size=10000, max_age_seconds=60.0)
            self.logger.debug("ArgumentSizer initialized for Level 2+ (replaces sys.getsizeof loops)")

            # Initialize auto-profiler at Level 2+ (when JIT is available)
            # Level 0/1 must not have sys.settrace overhead
            if not hasattr(self, '_auto_profiler') or self._auto_profiler is None:
                self._initialize_auto_profiler()
                self.logger.debug("Auto-profiler enabled at Level 2+ (JIT available for hot loops)")

            # Import JIT components
            from ..jit.manager import JITManager, JITConfiguration
            from ..plugins.analyzer.adaptive_orchestrator import AdaptiveOrchestrator, OrchestrationConfig

            # Create JIT configuration optimized for Level 2
            jit_config = JITConfiguration(
                min_hot_path_score=60.0,  # Lower threshold for broader adoption
                min_function_calls=30,    # Lower threshold for faster compilation
                min_expected_speedup=1.15, # 15% minimum improvement
                enable_compilation_caching=True,
                enable_performance_learning=True
            )

            # Initialize JIT manager
            self._jit_manager = JITManager(config=jit_config)

            # Create adaptive orchestrator configuration
            orchestrator_config = OrchestrationConfig(
                enable_jit_coordination=True,
                jit_hot_path_threshold=60.0,  # Match JIT manager threshold
                min_jit_benefit_threshold=1.15, # Match JIT manager threshold
                jit_analysis_interval=5.0,   # Faster analysis for Level 2
                max_concurrent_compilations=3, # Allow more concurrent compilations
                adaptation_threshold=0.12,   # More sensitive adaptation
                monitoring_interval=3.0      # Faster monitoring
            )

            # Initialize adaptive orchestrator with JIT coordination
            self._adaptive_orchestrator = AdaptiveOrchestrator(
                config=orchestrator_config,
                performance_callback=self._get_current_performance if self.performance_monitor else None,
                jit_manager=self._jit_manager
            )

            # Start JIT background compilation and orchestrator monitoring
            self._jit_manager.start_background_compilation()
            self._adaptive_orchestrator.start_monitoring()

            # CRITICAL: Connect auto-profiler to orchestrator for ML-guided optimization
            if hasattr(self, '_auto_profiler') and self._auto_profiler:
                jit_analyzer = self._jit_manager._jit_analyzer if hasattr(self._jit_manager, '_jit_analyzer') else None
                self._auto_profiler.set_orchestrator(
                    self._adaptive_orchestrator,
                    jit_analyzer=jit_analyzer
                )
                self.logger.debug("Auto-profiler connected to adaptive orchestrator (ML-guided decisions enabled)")

                # P0.12 FIX (Dec 2025): Connect JIT manager for failed compilation checks
                # When background compilation fails, auto_profiler needs to know to return DISABLE
                if hasattr(self._auto_profiler, 'set_jit_manager'):
                    self._auto_profiler.set_jit_manager(self._jit_manager)
                    self.logger.debug("Auto-profiler connected to JIT manager (failed code checks enabled)")

                # P0.15 FIX (Dec 2025): Connect auto_profiler to JIT manager for non-transformable checks
                # When auto_profiler detects method calls in loops (P0.13), JIT manager needs to
                # check _non_transformable_code_ids before queueing to avoid compilation failures.
                if hasattr(self._jit_manager, 'set_auto_profiler'):
                    self._jit_manager.set_auto_profiler(self._auto_profiler)
                    self.logger.debug("JIT manager connected to auto-profiler (non-transformable checks enabled)")

            # Fix #2: Mark JIT as ready now that initialization is complete
            self._jit_ready = True
            self.logger.debug("JIT system initialized successfully for Level 2 enhancement")

        except ImportError as e:
            self.logger.warning(f"JIT system components not available: {e}")
            self._jit_manager = None
            self._adaptive_orchestrator = None
        except Exception as e:
            self.logger.error(f"Failed to initialize JIT system: {e}")
            self._jit_manager = None
            self._adaptive_orchestrator = None
            # Don't raise - allow Epochly to continue without JIT

    def _calculate_adaptive_pool_size(self) -> int:
        """
        Calculate adaptive pool size based on workload and system characteristics.

        ISSUE #4 FIX (perf_fixes4.md): Drive allocator sizing from workload estimates.

        Returns:
            Pool size in bytes
        """
        # Default minimum and maximum
        MIN_POOL_SIZE = 4 * 1024 * 1024    # 4MB minimum
        DEFAULT_POOL_SIZE = 16 * 1024 * 1024  # 16MB default
        MAX_POOL_SIZE = 256 * 1024 * 1024   # 256MB maximum

        # Try to get workload characteristics
        try:
            workload_chars = self._get_workload_characteristics()
            if workload_chars:
                estimated_data = workload_chars.get('estimated_data_size', 0)
                memory_intensive = workload_chars.get('memory_intensive', False)

                if memory_intensive and estimated_data > 0:
                    # Scale pool to 2x estimated data size (for double-buffering)
                    adaptive_size = min(estimated_data * 2, MAX_POOL_SIZE)
                    return max(MIN_POOL_SIZE, adaptive_size)
        except Exception as e:
            self.logger.debug(f"Workload characteristics unavailable: {e}")

        # Check NUMA topology for multi-node scaling
        try:
            if hasattr(self, '_numa_manager') or '_numa_manager_for_pool' in locals():
                numa_manager = getattr(self, '_numa_manager', None)
                if numa_manager and numa_manager.get_node_count() > 1:
                    # Multiple NUMA nodes: increase pool size proportionally
                    numa_scale = numa_manager.get_node_count()
                    return min(DEFAULT_POOL_SIZE * numa_scale, MAX_POOL_SIZE)
        except Exception:
            pass

        return DEFAULT_POOL_SIZE

    def _get_workload_characteristics(self) -> Optional[Dict[str, Any]]:
        """
        Get workload characteristics for adaptive sizing.

        Returns:
            Dictionary with workload characteristics or None
        """
        try:
            if hasattr(self, '_adaptive_orchestrator') and self._adaptive_orchestrator:
                summary = self._adaptive_orchestrator.get_performance_summary()
                if summary:
                    return {
                        'estimated_data_size': summary.get('avg_data_size', 0),
                        'memory_intensive': summary.get('memory_intensive', False),
                        'parallelizable': summary.get('parallelizable', False)
                    }
        except Exception:
            pass
        return None

    # ============================================================================
    # Phase 2 (Dec 2025): Early ProcessPool Spawn During Stability Wait
    # ============================================================================

    # ============================================================================
    # CRITICAL FIX (Jan 2026): Suspend sys.monitoring During ProcessPool Spawn
    # ============================================================================
    # Python 3.12 Bug: sys.monitoring callbacks reference parent process objects.
    # When forkserver spawns child processes, the inherited monitoring state
    # causes deadlock because callbacks can't execute in the child context.
    # Python 3.13 fixed this, but we need to support 3.9-3.13.
    # ============================================================================

    def _suspend_monitoring_for_spawn(self) -> Optional[Dict[str, Any]]:
        """
        Suspend sys.monitoring before ProcessPool spawn to prevent deadlock.

        Python 3.12 Bug: sys.monitoring callbacks reference parent process objects.
        When forkserver spawns child processes, the inherited monitoring state
        causes deadlock because callbacks can't execute in the child context.

        This fix only applies to Python 3.12.x:
        - Python 3.9-3.11: No sys.monitoring (skip)
        - Python 3.12.x: Bug present, apply fix
        - Python 3.13+: Bug fixed upstream (skip)

        Returns:
            dict with monitoring state to restore, or None if not applicable
        """
        # Only needed for Python 3.12.x - 3.11 lacks sys.monitoring, 3.13+ fixed the issue
        if not ((3, 12) <= sys.version_info < (3, 13)):
            return None

        state = None

        # Suspend auto-profiler's sys.monitoring
        # Thread-safety note: This is called at a controlled point before spawn starts.
        # The _auto_profiler is not expected to be reconfigured during spawn.
        if hasattr(self, '_auto_profiler') and self._auto_profiler:
            profiler = self._auto_profiler
            if hasattr(profiler, '_monitoring_tool_id') and hasattr(sys, 'monitoring'):
                try:
                    tool_id = profiler._monitoring_tool_id
                    if tool_id is None:
                        return None  # Monitoring not enabled

                    # Save current event mask
                    # Note: Brief race window between get_events/set_events is acceptable
                    # since this runs at a controlled point before spawn
                    current_events = sys.monitoring.get_events(tool_id)

                    if current_events:
                        # Disable all events (keeps tool registered)
                        sys.monitoring.set_events(tool_id, 0)
                        state = {
                            'tool_id': tool_id,
                            'events': current_events,
                            'profiler': profiler,
                            '_restored': False  # Track restoration for idempotency
                        }
                        self.logger.debug(f"Suspended sys.monitoring (tool_id={tool_id}) for ProcessPool spawn")
                except Exception as e:
                    self.logger.debug(f"Could not suspend sys.monitoring: {e}")

        return state

    def _restore_monitoring_after_spawn(self, state: Optional[Dict[str, Any]]) -> None:
        """
        Restore sys.monitoring after ProcessPool spawn completes.

        This method is idempotent - multiple calls with the same state are safe.
        The '_restored' flag in state prevents double restoration.

        Args:
            state: Monitoring state from _suspend_monitoring_for_spawn()
        """
        if state is None:
            return

        # Idempotent: Check if already restored
        if state.get('_restored', False):
            return

        # Only needed for Python 3.12.x (same check as suspend)
        if not ((3, 12) <= sys.version_info < (3, 13)):
            return

        try:
            tool_id = state['tool_id']
            events = state['events']

            # Re-enable events
            sys.monitoring.set_events(tool_id, events)
            state['_restored'] = True  # Mark as restored for idempotency
            self.logger.debug(f"Restored sys.monitoring (tool_id={tool_id}) after ProcessPool spawn")
        except Exception as e:
            self.logger.warning(f"Could not restore sys.monitoring: {e}")

    def _begin_worker_spawn_async(self, worker_count: int) -> Future:
        """
        Start ProcessPool worker spawn asynchronously (non-blocking).

        Phase 2 Optimization: By starting worker spawn DURING the stability wait
        instead of AFTER, we can hide most of the ~8s spawn time behind the
        1s stability wait period.

        This method:
        1. Pre-caches license for workers (Phase 1.1)
        2. Starts SubInterpreterExecutor creation in a background thread
        3. Returns immediately with a Future that completes when spawn is done

        Args:
            worker_count: Number of workers to spawn (from license check)

        Returns:
            Future that resolves to dict with spawn results:
            - 'executor': The SubInterpreterExecutor instance
            - 'shared_memory_manager': SharedMemoryManager instance
            - 'numa_manager': NumaManager instance (may be None)
            - 'fast_memory_pool': FastMemoryPool instance (may be None)
            - 'success': True if spawn succeeded

        Thread Safety:
            Uses _spawn_lock to prevent duplicate spawns from concurrent threads.
        """
        with self._spawn_lock:
            # Prevent duplicate spawns
            if self._spawn_started:
                self.logger.debug("Early spawn already started, returning existing future")
                return self._spawn_future

            self._spawn_started = True
            self._spawn_future = Future()
            self._stop_spawn_event = threading.Event()  # Allow stopping spawn thread

        self.logger.debug(f"Starting early worker spawn async with {worker_count} workers")

        # Phase 3 (Dec 2025): Forkserver is now initialized in initialize() BEFORE any threads.
        # This fallback ensures safety if Level 3 is triggered before initialize() completes.
        # The _forkserver_init_attempted flag ensures idempotency.
        if not self._forkserver_init_attempted:
            self._forkserver_init_attempted = True
            try:
                from .forkserver_manager import try_initialize_forkserver
                forkserver_state = try_initialize_forkserver()
                self.logger.debug(f"Forkserver late init (fallback): {forkserver_state.value}")
            except ImportError as e:
                self.logger.debug(f"Forkserver manager not available: {e}")
            except Exception as e:
                self.logger.warning(f"Forkserver initialization failed: {e}")

        # CRITICAL FIX (Jan 2026): Suspend sys.monitoring BEFORE spawn thread starts
        # This prevents the monitoring callbacks from being inherited by forkserver
        # and causing deadlock in Python 3.12. Python 3.13 fixed this issue.
        monitoring_state = self._suspend_monitoring_for_spawn()

        # Capture stop_event for spawn thread
        stop_spawn_event = self._stop_spawn_event

        def spawn_workers():
            """Background thread function to spawn workers."""
            result = {
                'executor': None,
                'shared_memory_manager': None,
                'numa_manager': None,
                'fast_memory_pool': None,
                'success': False,
                'worker_count': worker_count
            }

            def _cleanup_on_failure():
                """Clean up partially constructed components on failure."""
                if result['executor']:
                    try:
                        result['executor'].shutdown(wait=False)
                    except Exception:
                        pass
                if result['shared_memory_manager']:
                    try:
                        result['shared_memory_manager'].close()
                    except Exception:
                        pass
                if result['numa_manager']:
                    try:
                        if hasattr(result['numa_manager'], 'close'):
                            result['numa_manager'].close()
                    except Exception:
                        pass
                if result['fast_memory_pool']:
                    try:
                        result['fast_memory_pool'].close()
                    except Exception:
                        pass
                # CRITICAL FIX (Dec 2025): Clear env vars on ALL failure paths
                # Without this, failed spawns leave EPOCHLY_DISABLE=1 in main process,
                # blocking subsequent EpochlyCore re-initialization (e.g., in tests).
                os.environ.pop('EPOCHLY_DISABLE', None)
                os.environ.pop('EPOCHLY_DISABLE_INTERCEPTION', None)
                # CRITICAL FIX (Jan 2026): Always restore monitoring on failure
                # This prevents permanent monitoring disable if spawn fails
                self._restore_monitoring_after_spawn(monitoring_state)

            try:
                # Check stop event at start
                if stop_spawn_event.is_set():
                    self.logger.debug("Early spawn aborted before start (stop event set)")
                    # Restore monitoring even on early abort
                    self._restore_monitoring_after_spawn(monitoring_state)
                    self._spawn_future.set_result(result)
                    return

                # Phase 1.1: Pre-cache license for workers (fast worker startup)
                try:
                    from ..licensing.worker_license_cache import get_global_worker_cache
                    worker_cache = get_global_worker_cache()
                    worker_cache.initialize_main_process()
                    self.logger.debug("Worker license cache initialized for fast worker startup")
                except Exception as e:
                    self.logger.debug(f"Worker license cache init failed (workers will use fallback): {e}")

                # Check stop event before heavy work
                if stop_spawn_event.is_set():
                    self.logger.debug("Early spawn aborted after license cache (stop event set)")
                    # Restore monitoring even on early abort
                    self._restore_monitoring_after_spawn(monitoring_state)
                    self._spawn_future.set_result(result)
                    return

                # Calculate pool size ONCE and reuse (mcp-reflect optimization)
                pool_size = self._calculate_adaptive_pool_size()

                # Initialize FastMemoryPool
                try:
                    from ..memory.fast_memory_pool import FastMemoryPool
                    result['fast_memory_pool'] = FastMemoryPool(
                        total_size=pool_size,
                        name="FastMemoryPool"
                    )
                    self.logger.debug("FastMemoryPool initialized for early spawn")
                except ImportError as e:
                    self.logger.debug(f"FastMemoryPool not available: {e}")

                # Check stop event
                if stop_spawn_event.is_set():
                    self.logger.debug("Early spawn aborted after FastMemoryPool (stop event set)")
                    _cleanup_on_failure()
                    self._spawn_future.set_result(result)
                    return

                # Initialize SharedMemoryManager
                # CRITICAL FIX (Jan 2026): Skip SharedMemoryManager on Python 3.13 macOS
                # SharedMemory uses multiprocessing.resource_tracker which has known deadlock
                # issues on Python 3.13 macOS. This causes the spawn thread to hang indefinitely.
                # Since we're using ThreadExecutor fallback on this platform anyway,
                # SharedMemoryManager provides no benefit and only causes hangs.
                is_python313_macos = sys.version_info[:2] == (3, 13) and sys.platform == 'darwin'
                if is_python313_macos:
                    self.logger.debug(
                        "SharedMemoryManager skipped on Python 3.13 macOS "
                        "(resource_tracker deadlock issues)"
                    )
                else:
                    try:
                        from ..plugins.executor.shared_memory_manager import SharedMemoryManager
                        result['shared_memory_manager'] = SharedMemoryManager(pool_size=pool_size)
                        self.logger.debug(f"SharedMemoryManager initialized with {pool_size // (1024*1024)}MB")
                    except ImportError as e:
                        self.logger.debug(f"SharedMemoryManager not available: {e}")

                # Check stop event before NUMA
                if stop_spawn_event.is_set():
                    self.logger.debug("Early spawn aborted after SharedMemoryManager (stop event set)")
                    _cleanup_on_failure()
                    self._spawn_future.set_result(result)
                    return

                # Initialize NUMA manager
                try:
                    from ..numa import NumaManager
                    result['numa_manager'] = NumaManager()
                    self.logger.debug(f"NUMA manager initialized ({result['numa_manager'].get_node_count()} nodes)")
                except ImportError as e:
                    self.logger.debug(f"NUMA support not available: {e}")

                # Check stop event before the slow executor initialization
                if stop_spawn_event.is_set():
                    self.logger.debug("Early spawn aborted before SubInterpreterExecutor (stop event set)")
                    _cleanup_on_failure()
                    self._spawn_future.set_result(result)
                    return

                # Initialize SubInterpreterExecutor (THE SLOW PART - ~8s)
                try:
                    # CRITICAL FIX (Dec 2025, mcp-reflect review): Set env vars before ProcessPool
                    # This prevents workers from bootstrapping Epochly recursively (fork bomb)
                    # NOTE: os is already imported at module level - do NOT import here
                    # as it creates a local variable that shadows the global, causing
                    # NameError in _cleanup_on_failure() (P0.26 fix, same as sys import bug)
                    os.environ['EPOCHLY_DISABLE'] = '1'
                    os.environ['EPOCHLY_DISABLE_INTERCEPTION'] = '1'

                    from ..plugins.executor.sub_interpreter_executor import SubInterpreterExecutor

                    result['executor'] = SubInterpreterExecutor(
                        max_workers=worker_count,
                        shared_memory_manager=result['shared_memory_manager'],
                        numa_manager=result['numa_manager']
                    )
                    # CRITICAL: Must call initialize() to create the pool and workers
                    result['executor'].initialize()

                    # CRITICAL FIX (Dec 2025): Clear env vars AFTER workers spawned
                    # Workers have inherited these at spawn time. Clearing in main process
                    # allows subsequent EpochlyCore re-initialization (e.g., in tests).
                    os.environ.pop('EPOCHLY_DISABLE', None)
                    os.environ.pop('EPOCHLY_DISABLE_INTERCEPTION', None)

                    if result['executor'].is_initialized:
                        self.logger.debug(
                            f"SubInterpreterExecutor initialized with {result['executor'].worker_count} workers"
                        )
                        result['success'] = True
                        # CRITICAL FIX (Jan 2026): Restore monitoring after successful spawn
                        # This re-enables sys.monitoring callbacks that were suspended to prevent
                        # Python 3.12 deadlock during ProcessPool spawn
                        self._restore_monitoring_after_spawn(monitoring_state)
                    else:
                        self.logger.warning("SubInterpreterExecutor created but not fully initialized")
                        _cleanup_on_failure()

                except ImportError as e:
                    self.logger.warning(f"SubInterpreterExecutor not available: {e}")
                    _cleanup_on_failure()
                except Exception as e:
                    self.logger.warning(f"SubInterpreterExecutor initialization failed: {e}")
                    _cleanup_on_failure()

                # FIX (Dec 2025, mcp-reflect review): Reset _spawn_started on failure
                # to allow retries in future versions
                if not result.get('success'):
                    with self._spawn_lock:
                        self._spawn_started = False

                self._spawn_future.set_result(result)

            except Exception as e:
                self.logger.error(f"Early worker spawn failed: {e}")
                _cleanup_on_failure()
                # Reset spawn flag to allow retries
                with self._spawn_lock:
                    self._spawn_started = False
                self._spawn_future.set_exception(e)

        # Start spawn in background thread
        spawn_thread = threading.Thread(
            target=spawn_workers,
            name="EpochlyEarlySpawn",
            daemon=True  # Don't block exit
        )
        # Track the spawn thread for proper shutdown (Dec 2025 fix)
        self._spawn_thread = spawn_thread
        spawn_thread.start()

        return self._spawn_future

    def _finalize_worker_spawn(self, spawn_future: Future, stop_event: threading.Event = None) -> bool:
        """
        Finalize worker spawn by waiting for Future completion.

        Phase 2 Optimization: After stability wait completes, we check if spawn
        is done. If spawn completed during stability wait (expected case), this
        returns immediately. Otherwise, we wait for spawn to complete.

        Args:
            spawn_future: Future from _begin_worker_spawn_async()
            stop_event: Optional event to signal abort (skips wait if set)

        Returns:
            True if spawn completed successfully and executor is ready
        """
        # Skip if stop event is set - also signal spawn thread to abort
        if stop_event and stop_event.is_set():
            self.logger.debug("Stop event set, skipping spawn finalization")
            # Signal spawn thread to abort if still running
            if self._stop_spawn_event:
                self._stop_spawn_event.set()
            return False

        try:
            # Check if Future is already done (fast path)
            if spawn_future.done():
                result = spawn_future.result(timeout=0.1)
            else:
                # Wait for spawn to complete (slow path - should be rare)
                self.logger.debug("Spawn not yet complete, waiting...")
                # Use short timeout loops to allow stop event checking
                timeout_per_check = 1.0
                max_wait = 30.0  # Maximum wait time
                waited = 0.0

                while waited < max_wait:
                    if stop_event and stop_event.is_set():
                        self.logger.debug("Stop event set during spawn wait, aborting")
                        # Signal spawn thread to abort
                        if self._stop_spawn_event:
                            self._stop_spawn_event.set()
                        return False

                    if spawn_future.done():
                        break

                    try:
                        spawn_future.result(timeout=timeout_per_check)
                        break
                    except TimeoutError:
                        waited += timeout_per_check
                        continue

                result = spawn_future.result(timeout=0.1)

            # Store the spawned components on self
            # RACE CONDITION FIX (Dec 2025): Check if executor was already assigned
            # by _ensure_level3_initialized() which may have waited on the same spawn_future
            if result.get('success'):
                if hasattr(self, '_sub_interpreter_executor') and self._sub_interpreter_executor is not None:
                    self.logger.debug("Executor already assigned (by _ensure_level3_initialized), skipping")
                else:
                    self._sub_interpreter_executor = result.get('executor')
                    if result.get('shared_memory_manager'):
                        self._shared_memory_manager = result['shared_memory_manager']
                    if result.get('numa_manager'):
                        self._numa_manager = result['numa_manager']
                    if result.get('fast_memory_pool'):
                        self._fast_memory_pool = result['fast_memory_pool']

                self.logger.debug("Early spawn finalized successfully")
                return True
            else:
                self.logger.warning("Early spawn completed but was not successful")
                return False

        except Exception as e:
            self.logger.error(f"Failed to finalize worker spawn: {e}")
            return False

    def _initialize_level3_system(self):
        """
        Initialize Level 3 sub-interpreter system with memory pools.

        This method sets up:
        1. FastMemoryPool for allocator benchmarking
        2. SharedMemoryManager with adaptive pool sizing
        3. Sub-interpreter executor with license-aware worker count
        4. NUMA-aware memory management

        Reference: perf_fixes4.md, perf_fixes5.md
        """
        try:
            # Ensure Level 2 is initialized first (JIT system)
            if not hasattr(self, '_jit_manager') or self._jit_manager is None:
                self.logger.warning("Level 3 requires Level 2 JIT system - initializing Level 2 first")
                self._initialize_jit_system()

            # Initialize FastMemoryPool (Phase 4.1: tiered allocator with Cython optimization)
            try:
                from ..memory.fast_memory_pool import FastMemoryPool

                # Calculate pool size based on workload characteristics
                pool_size = self._calculate_adaptive_pool_size()

                self._fast_memory_pool = FastMemoryPool(
                    total_size=pool_size,  # CRITICAL FIX: Parameter is 'total_size' not 'pool_size'
                    name="FastMemoryPool"
                )
                self.logger.debug("FastAllocatorAdapter initialized for Level 3 (2x allocation throughput)")
            except ImportError as e:
                self.logger.warning(f"FastMemoryPool not available: {e}")
                self._fast_memory_pool = None

            # Initialize SharedMemoryManager for cross-interpreter data sharing
            # CRITICAL FIX (Jan 2026): Skip SharedMemoryManager on Python 3.13 macOS
            # SharedMemory uses multiprocessing.resource_tracker which has known deadlock
            # issues on Python 3.13 macOS.
            is_python313_macos = sys.version_info[:2] == (3, 13) and sys.platform == 'darwin'
            if is_python313_macos:
                self.logger.debug(
                    "SharedMemoryManager skipped on Python 3.13 macOS "
                    "(resource_tracker deadlock issues)"
                )
                self._shared_memory_manager = None
            else:
                try:
                    from ..plugins.executor.shared_memory_manager import SharedMemoryManager

                    # Calculate adaptive pool size
                    pool_size = self._calculate_adaptive_pool_size()

                    self._shared_memory_manager = SharedMemoryManager(pool_size=pool_size)  # CRITICAL FIX: Parameter is 'pool_size' not 'pool_size_bytes'
                    self.logger.debug(f"SharedMemoryManager initialized with {pool_size // (1024*1024)}MB adaptive pool")
                except ImportError as e:
                    self.logger.warning(f"SharedMemoryManager not available: {e}")
                    self._shared_memory_manager = None

            # Get license-aware worker count using check_core_limit
            system_cores = multiprocessing.cpu_count()
            try:
                allowed, max_cores = check_core_limit(system_cores)
                self.logger.debug(f"License check: allowed={allowed}, max_cores={max_cores} (system has {system_cores})")
            except Exception as e:
                self.logger.debug(f"License check failed, using system default: {e}")
                allowed = True
                max_cores = system_cores

            # Determine actual worker count based on license check
            if allowed:
                worker_count = min(max_cores, system_cores) if max_cores else system_cores
            else:
                worker_count = max_cores  # Use license limit when not fully allowed
            self.logger.debug(f"Level 3 will use {worker_count} workers (system: {system_cores}, license_max: {max_cores})")

            # PERFORMANCE OPTIMIZATION (Phase 1.1): Pre-cache license for worker processes
            # Workers will read this cache instead of doing full license validation (~1000ms -> <10ms)
            # See planning/rca-level3-warmup-spike.md for details.
            try:
                from ..licensing.worker_license_cache import get_global_worker_cache
                worker_cache = get_global_worker_cache()
                worker_cache.initialize_main_process()
                self.logger.debug("Worker license cache initialized for fast worker startup")
            except Exception as e:
                self.logger.debug(f"Worker license cache init failed (workers will use fallback): {e}")

            # Initialize NUMA manager for memory-aware scheduling
            try:
                from ..numa import NumaManager
                self._numa_manager = NumaManager()
                self.logger.debug(f"NUMA manager initialized ({self._numa_manager.get_node_count()} nodes)")
            except ImportError as e:
                self.logger.debug(f"NUMA support not available: {e}")
                self._numa_manager = None

            # Initialize sub-interpreter executor (Python 3.12+)
            try:
                from ..plugins.executor.sub_interpreter_executor import SubInterpreterExecutor

                self._sub_interpreter_executor = SubInterpreterExecutor(
                    max_workers=worker_count,
                    shared_memory_manager=self._shared_memory_manager,
                    numa_manager=self._numa_manager
                )
                # CRITICAL FIX: Must call initialize() to create the pool and workers
                self._sub_interpreter_executor.initialize()
                
                if self._sub_interpreter_executor.is_initialized:
                    self.logger.debug(
                        f"SubInterpreterExecutor initialized with {self._sub_interpreter_executor.worker_count} workers"
                    )
                else:
                    self.logger.warning("SubInterpreterExecutor created but not fully initialized")
            except ImportError as e:
                self.logger.warning(f"SubInterpreterExecutor not available: {e}")
                self._sub_interpreter_executor = None
            except Exception as e:
                self.logger.warning(f"SubInterpreterExecutor initialization failed: {e}")
                self._sub_interpreter_executor = None

            # PRE-WARM PARALLEL INFRASTRUCTURE (Dec 2025)
            # Eliminates 5.1x first-run penalty by eagerly initializing:
            # - Numba parallel threading layer
            # - OpenBLAS/MKL thread pool
            # - Memory allocator caches
            # See planning/level3-prewarm-design.md
            try:
                from .prewarm import prewarm_level3_infrastructure
                prewarm_success = prewarm_level3_infrastructure(timeout_ms=10000)
                if prewarm_success:
                    self.logger.debug("Level 3 parallel infrastructure pre-warmed")
                else:
                    self.logger.debug("Level 3 pre-warm incomplete (soft timeout)")
            except Exception as e:
                self.logger.debug(f"Level 3 pre-warm skipped (non-fatal): {e}")

            self.logger.debug("Level 3 system initialized successfully")
            # Signal that Level 3 initialization is complete
            if hasattr(self, '_level3_init_complete'):
                self._level3_init_complete.set()

        except Exception as e:
            self.logger.error(f"Failed to initialize Level 3 system: {e}")
            import traceback
            self.logger.debug(f"Traceback: {traceback.format_exc()}")

    def _ensure_level3_initialized(self) -> bool:
        """
        Ensure Level 3 executor is initialized (lazy initialization).

        CRITICAL FIX (2025-11-24): This method implements lazy Level 3 initialization
        to prevent the fork bomb that occurs when ProcessPool is created during bootstrap.

        CRITICAL FIX (2025-12-11): Wait for early spawn instead of duplicate sync spawn.
        Phase 2 starts ProcessPool spawn async in background detection thread.
        If early spawn is in progress, wait for it instead of creating a duplicate.
        This prevents the 13.7s warmup spike from CPU starvation.

        The problem:
        - sitecustomize.py runs during Python startup
        - bootstrap() restores saved state which may be Level 3
        - Creating ProcessPool during bootstrap causes workers to import Python
        - Workers run sitecustomize.py, which bootstraps Epochly again
        - Workers try to restore Level 3, creating MORE ProcessPools
        - FORK BOMB: exponential process creation

        The solution:
        - set_enhancement_level() sets _level3_deferred=True but doesn't create executor
        - This method creates the executor lazily on first actual use
        - Environment variables are set BEFORE ProcessPool creation
        - Workers inherit EPOCHLY_DISABLE=1 and don't bootstrap
        - NEW: If early spawn is in progress, wait for it instead of duplicate spawn

        Returns:
            bool: True if executor is ready for use, False otherwise
        """
        # Already initialized?
        if hasattr(self, '_sub_interpreter_executor') and self._sub_interpreter_executor is not None:
            return True

        # Not deferred and not initialized = Level 3 not requested
        if not getattr(self, '_level3_deferred', False):
            return False

        # PHASE 2 FIX (Dec 2025): Check if early spawn is in progress
        # If so, wait for it instead of creating a duplicate ProcessPool
        with self._spawn_lock:
            if self._spawn_started and self._spawn_future is not None:
                self.logger.debug("Early spawn in progress, waiting for completion instead of duplicate spawn")
                try:
                    # Wait for early spawn with timeout (spawn takes ~8s, allow extra time)
                    spawn_timeout = 30.0
                    spawn_result = self._spawn_future.result(timeout=spawn_timeout)

                    if spawn_result and spawn_result.get('success'):
                        # Assign executor from spawn result
                        self._sub_interpreter_executor = spawn_result.get('executor')

                        # Assign other Level 3 components from spawn result
                        if spawn_result.get('shared_memory_manager'):
                            self._shared_memory_manager = spawn_result.get('shared_memory_manager')
                        if spawn_result.get('numa_manager'):
                            self._numa_manager = spawn_result.get('numa_manager')
                        if spawn_result.get('fast_memory_pool'):
                            self._fast_memory_pool = spawn_result.get('fast_memory_pool')

                        self._level3_deferred = False

                        # Signal that Level 3 initialization is complete
                        # This allows tests and callers to verify init state
                        if hasattr(self, '_level3_init_complete'):
                            self._level3_init_complete.set()

                        self.logger.debug(f"Early spawn completed, executor ready with {spawn_result.get('worker_count', 'unknown')} workers")
                        return True
                    else:
                        self.logger.warning("Early spawn completed but failed, falling back to synchronous init")
                        # Fall through to synchronous init below
                except Exception as e:
                    self.logger.warning(f"Early spawn wait failed: {e}, falling back to synchronous init")
                    # Fall through to synchronous init below

        # P1-3 FIX (Dec 2025): Use async spawn instead of synchronous initialization
        # This eliminates the 505ms spike by ensuring only ONE spawn happens
        # (detection thread or this caller, whichever triggers first).
        #
        # The async spawn mechanism already handles:
        # - Environment variable setting/clearing for fork bomb prevention
        # - License-aware worker count calculation
        # - Cleanup on failure
        # - Thread safety via _spawn_lock
        #
        # By using async spawn, we:
        # 1. Prevent duplicate spawns (only one thread can start spawn)
        # 2. Allow future callers to wait on the same spawn
        # 3. Eliminate synchronous blocking in the hot path

        # Calculate worker count (same logic as _initialize_level3_system)
        import multiprocessing
        from ..licensing.license_enforcer import check_core_limit

        system_cores = multiprocessing.cpu_count()
        try:
            allowed, max_cores = check_core_limit(system_cores)
            self.logger.debug(f"Lazy init license check: allowed={allowed}, max_cores={max_cores}")
        except Exception as e:
            self.logger.debug(f"Lazy init license check failed, using defaults: {e}")
            allowed = True
            max_cores = system_cores

        if allowed:
            worker_count = min(max_cores, system_cores) if max_cores else system_cores
        else:
            worker_count = max_cores

        self.logger.debug(f"Lazy Level 3 initialization via async spawn ({worker_count} workers)")

        # Start async spawn (thread-safe - if early spawn already started, returns existing future)
        spawn_future = self._begin_worker_spawn_async(worker_count)

        # Wait for spawn to complete (still ~500ms on macOS, but consistent with early spawn path)
        spawn_timeout = 30.0
        try:
            spawn_result = spawn_future.result(timeout=spawn_timeout)

            if spawn_result and spawn_result.get('success'):
                # Assign executor from spawn result
                self._sub_interpreter_executor = spawn_result.get('executor')

                # Assign other Level 3 components from spawn result
                if spawn_result.get('shared_memory_manager'):
                    self._shared_memory_manager = spawn_result.get('shared_memory_manager')
                if spawn_result.get('numa_manager'):
                    self._numa_manager = spawn_result.get('numa_manager')
                if spawn_result.get('fast_memory_pool'):
                    self._fast_memory_pool = spawn_result.get('fast_memory_pool')

                self._level3_deferred = False

                # Signal that Level 3 initialization is complete
                # This allows tests and callers to verify init state
                if hasattr(self, '_level3_init_complete'):
                    self._level3_init_complete.set()

                self.logger.debug(f"Lazy Level 3 initialization complete ({spawn_result.get('worker_count', 'unknown')} workers)")
                return True
            else:
                self.logger.warning("Lazy async spawn completed but was not successful, falling back to synchronous")
                # Fall through to synchronous fallback below
        except Exception as e:
            self.logger.warning(f"Lazy async spawn failed ({e}), falling back to synchronous")
            # Fall through to synchronous fallback below

        # SYNCHRONOUS FALLBACK (should be rare - only if async spawn fails)
        # This preserves the original behavior as a safety net
        with self._lock:
            # Double-check under lock
            if hasattr(self, '_sub_interpreter_executor') and self._sub_interpreter_executor is not None:
                return True

            self.logger.debug("Lazy Level 3 synchronous fallback triggered")

            # CRITICAL FIX (Jan 2026): Suspend sys.monitoring before ProcessPool creation
            # Python 3.12 Bug: sys.monitoring callbacks cause deadlock during forkserver spawn
            monitoring_state = self._suspend_monitoring_for_spawn()

            # CRITICAL: Set environment variables BEFORE creating ProcessPool
            # This ensures workers inherit disabled state and prevents fork bomb
            import os
            os.environ['EPOCHLY_DISABLE'] = '1'
            os.environ['EPOCHLY_DISABLE_INTERCEPTION'] = '1'

            # Now safe to initialize Level 3 system
            # Use try/finally to GUARANTEE monitoring restoration (mcp-reflect review)
            try:
                self._initialize_level3_system()
                self._level3_deferred = False  # Clear deferred flag

                # Signal that Level 3 initialization is complete (same as async path)
                # This allows tests and callers to verify init state
                init_success = hasattr(self, '_sub_interpreter_executor') and self._sub_interpreter_executor is not None
                if init_success and hasattr(self, '_level3_init_complete'):
                    self._level3_init_complete.set()

                return init_success
            except Exception as e:
                self.logger.error(f"Lazy Level 3 initialization failed: {e}")
                return False
            finally:
                # CRITICAL FIX (Dec 2025): Clear env vars AFTER spawn completes/fails
                # Workers have inherited these at spawn time. Clearing in main process
                # allows subsequent EpochlyCore re-initialization (e.g., in tests).
                os.environ.pop('EPOCHLY_DISABLE', None)
                os.environ.pop('EPOCHLY_DISABLE_INTERCEPTION', None)
                # CRITICAL FIX (Jan 2026): ALWAYS restore monitoring (idempotent)
                self._restore_monitoring_after_spawn(monitoring_state)

    def _initialize_level4_gpu_system(self):
        """
        Initialize Level 4 GPU acceleration system.

        This method sets up:
        1. GPU detection and capability probing
        2. GPU memory manager for allocation tracking
        3. GPU executor for dispatching work to GPU

        Reference: Architecture spec lines 2500-2600
        """
        try:
            # CRITICAL GUARD (Jan 2025 RCA): Prevent duplicate initialization
            # When called multiple times (startup + set_level + background upgrade),
            # re-running the license check can DESTROY an already-working GPU executor.
            # If GPU executor exists and is enabled, skip re-initialization.
            if (hasattr(self, '_level4_gpu_executor') and
                self._level4_gpu_executor is not None and
                getattr(self._level4_gpu_executor, '_enabled', False)):
                self.logger.debug("Level 4 GPU system already initialized - skipping")
                return

            # Ensure Level 3 is initialized (Level 4 depends on Level 3)
            if getattr(self, '_sub_interpreter_executor', None) is None:
                self._initialize_level3_system()

            # Check GPU license
            try:
                from ..licensing.license_enforcer import check_feature
                if not check_feature('gpu_acceleration'):
                    self.logger.debug("GPU acceleration not licensed - skipping Level 4 init")
                    self._level4_gpu_executor = None
                    self._level4_init_complete.set()  # Signal completion even if skipped
                    return
            except ImportError:
                pass  # No license check, continue with GPU init

            # Detect GPU availability
            try:
                from ..gpu.gpu_detector import GPUDetector, GPUBackend
                detector = GPUDetector()
                gpu_info = detector.get_gpu_info()

                if gpu_info.backend == GPUBackend.NONE or gpu_info.device_count == 0:
                    self.logger.debug("No GPU detected - Level 4 unavailable")
                    self._level4_gpu_executor = None
                    self._level4_init_complete.set()
                    return

                self.gpu_available = True
                self.logger.debug(f"GPU detected: {gpu_info.device_name or 'Unknown'}")
                self.logger.debug(f"  Memory: {gpu_info.memory_total // (1024*1024)}MB")
                self.logger.debug(f"  Compute capability: {gpu_info.compute_capability or 'Unknown'}")
            except ImportError as e:
                self.logger.debug(f"GPU detection not available: {e}")
                self._level4_gpu_executor = None
                self._level4_init_complete.set()
                return

            # Initialize GPU executor
            try:
                from ..plugins.executor.gpu_executor import GPUExecutor
                self._level4_gpu_executor = GPUExecutor()
                self._level4_gpu_executor.initialize()  # Trigger _setup_plugin() for JIT components

                # Verify GPU is actually usable after initialization (CuPy might have failed)
                if hasattr(self._level4_gpu_executor, 'is_gpu_available'):
                    if not self._level4_gpu_executor.is_gpu_available():
                        self.logger.debug("GPU not available after executor initialization")
                        self._level4_gpu_executor = None
                    else:
                        self.logger.debug("GPUExecutor initialized for Level 4")
                else:
                    self.logger.debug("GPUExecutor initialized for Level 4")
            except ImportError as e:
                self.logger.warning(f"GPUExecutor not available: {e}")
                self._level4_gpu_executor = None

            # Enable intelligent memory management for OOM protection (TRANSPARENT)
            # This automatically handles large allocations and prevents crashes
            try:
                from ..gpu.intelligent_memory import enable_intelligent_memory
                enable_intelligent_memory()
                self.logger.debug("Intelligent GPU memory management enabled (OOM protection active)")
            except ImportError:
                self.logger.debug("Intelligent memory module not available")
            except Exception as e:
                self.logger.debug(f"Intelligent memory not enabled: {e}")

            # Signal completion
            self._level4_init_complete.set()
            self.logger.debug("Level 4 GPU system initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Level 4 GPU system: {e}")
            self._level4_gpu_executor = None
            self._level4_init_complete.set()

    def _clear_jit_caches_for_gpu_upgrade(self, profiler) -> None:
        """
        Clear JIT compiled function caches and restore original functions for GPU re-analysis.

        CRITICAL FIX (Jan 2025 RCA): When upgrading from LEVEL_3 (CPU JIT) to LEVEL_4 (GPU),
        functions that were already compiled at LEVEL_3 are marked as "done" in the
        _jit_compiled_code_ids set AND wrapped with _DisabledAwareWrapper. This prevents
        auto_profiler from attempting GPU compilation on those functions.

        The symptom: LEVEL_4 shows identical times to LEVEL_3 (1.0x speedup instead of 100x+).

        Root causes traced via integration testing:
        1. code_id in self._jit_compiled_code_ids - skips GPU compilation
        2. _DisabledAwareWrapper installed in module bindings - intercepts calls before
           auto_profiler can try GPU compilation

        This method:
        1. Clears JIT tracking caches (_jit_compiled_code_ids, _jit_result_cache)
        2. Restores original functions by removing ALL Epochly wrappers
        3. Restores trampolined functions (P0.18 pattern)

        IMPORTANT: This method must be called with profiler._lock held for thread safety.

        Args:
            profiler: The AutoProfiler instance whose caches should be cleared.
        """
        # Defensive check for None profiler
        if profiler is None:
            self.logger.warning("Cannot clear JIT caches: profiler is None")
            return

        cleared_count = 0
        restored_count = 0

        # Clear main JIT compiled tracking set
        if hasattr(profiler, '_jit_compiled_code_ids') and profiler._jit_compiled_code_ids:
            cleared_count = len(profiler._jit_compiled_code_ids)
            profiler._jit_compiled_code_ids.clear()

        # Clear JIT result cache if present (stores success/failure per code_id)
        if hasattr(profiler, '_jit_result_cache') and profiler._jit_result_cache:
            profiler._jit_result_cache.clear()

        # Clear function wrapper cache to force fresh analysis
        if hasattr(profiler, '_function_wrapper_cache') and profiler._function_wrapper_cache:
            profiler._function_wrapper_cache.clear()

        # CRITICAL FIX (Jan 2025): Reset hot loop optimization_applied flags
        # Without this, functions marked as "optimized" at LEVEL_3 are skipped at LEVEL_4
        # because _hot_loops[loop_id].optimization_applied == True prevents re-analysis.
        # The symptom: LEVEL_4 runs at pure Python speed instead of GPU speed.
        hot_loops_reset = 0
        if hasattr(profiler, '_hot_loops') and profiler._hot_loops:
            for loop_id, hot_loop in profiler._hot_loops.items():
                if hasattr(hot_loop, 'optimization_applied') and hot_loop.optimization_applied:
                    hot_loop.optimization_applied = False
                    hot_loops_reset += 1
            if hot_loops_reset > 0:
                self.logger.debug(
                    f"LEVEL_4 upgrade: Reset optimization_applied flag for {hot_loops_reset} hot loops"
                )

        # CRITICAL: Restore original functions by removing installed wrappers
        # This allows auto_profiler to intercept and try GPU compilation
        try:
            from ..profiling.auto_profiler import _restore_original_functions_for_gpu_upgrade
            restored_count = _restore_original_functions_for_gpu_upgrade()
        except ImportError as e:
            self.logger.warning(f"Could not import wrapper restoration function: {e}")
        except Exception as e:
            self.logger.error(f"Failed to restore original functions for GPU upgrade: {e}")

        # CRITICAL FIX (Jan 2025): Restart profiling/monitoring events
        # When monitoring callbacks return sys.monitoring.DISABLE, Python's monitoring
        # system PERMANENTLY disables monitoring for that code object at the runtime level.
        # Clearing _jit_compiled_code_ids removes our tracking, but Python still has
        # monitoring disabled for those code objects.
        #
        # For Python 3.12+: sys.monitoring.restart_events() re-enables all events that
        # were disabled by returning DISABLE from callbacks.
        #
        # For Python < 3.12: Reset _trace_auto_disabled flag which gates sys.settrace/sampling
        # callbacks from processing events after warmup.
        monitoring_restarted = False
        try:
            import sys
            # Python 3.12+: sys.monitoring API
            if hasattr(profiler, '_monitoring_tool_id') and hasattr(sys, 'monitoring'):
                if hasattr(sys.monitoring, 'restart_events'):
                    sys.monitoring.restart_events()
                    monitoring_restarted = True
                    self.logger.debug("LEVEL_4 upgrade: Restarted sys.monitoring events")

            # Python < 3.12: Reset sys.settrace/sampling auto-disable flags
            # These flags auto-disable profiling after warmup to reduce overhead.
            # For LEVEL_4 upgrade, we need to re-enable to detect hot loops for GPU.
            if hasattr(profiler, '_trace_auto_disabled') and profiler._trace_auto_disabled:
                profiler._trace_auto_disabled = False
                profiler._trace_skip_counter = 0
                monitoring_restarted = True
                self.logger.debug("LEVEL_4 upgrade: Reset sys.settrace auto-disable flags")

            # Reset sampling profiler state if it was stopped
            if hasattr(profiler, '_sampling_enabled') and not profiler._sampling_enabled:
                # Re-enable sampling if it was previously active
                if hasattr(profiler, '_enable_sampling_profiler'):
                    try:
                        profiler._enable_sampling_profiler()
                        monitoring_restarted = True
                        self.logger.debug("LEVEL_4 upgrade: Re-enabled sampling profiler")
                    except Exception as e:
                        self.logger.debug(f"Could not re-enable sampling profiler: {e}")

        except Exception as e:
            self.logger.warning(f"Failed to restart profiling events: {e}")

        if cleared_count > 0 or restored_count > 0 or hot_loops_reset > 0 or monitoring_restarted:
            self.logger.debug(
                f"LEVEL_4 upgrade: Cleared {cleared_count} JIT cache entries, "
                f"restored {restored_count} wrapped functions, "
                f"reset {hot_loops_reset} hot loops, "
                f"monitoring restarted={monitoring_restarted} for GPU re-analysis"
            )

    def _get_current_performance(self) -> float:
        """
        Get current performance metric for adaptive orchestration.

        Returns the total_metrics count from the performance monitor as a float,
        or 1.0 as the default value when no monitor is available or no metrics
        exist. This method is used as a callback for the AdaptiveOrchestrator.

        Returns:
            Performance value as float (defaults to 1.0)
        """
        if not self.performance_monitor:
            return 1.0

        try:
            summary = self.performance_monitor.get_system_summary()
            total_metrics = summary.get('total_metrics', 0)
            if total_metrics == 0:
                return 1.0
            return float(total_metrics)
        except Exception:
            return 1.0

    def _handle_auto_emergency_disable(self) -> None:
        """
        Handle automatic emergency disable triggered by AutoEmergencyDetector.

        This is called when system degradation is detected:
        - Global error rate > 50%
        - Memory allocation failures > threshold
        - Processing latency > threshold

        Safety requirement: R-SAFE-04 - Auto-disable on degradation.
        """
        self.logger.critical(
            "AUTO-EMERGENCY DISABLE: System degradation detected, disabling Epochly"
        )

        # Disable the core immediately
        self.enabled = False
        self._disabled_reason = "Auto-emergency disable: System degradation detected"

        # Force emergency shutdown of all executors
        try:
            from .executor_registry import force_emergency_shutdown
            force_emergency_shutdown()
        except ImportError as e:
            self.logger.error(f"Could not import executor_registry: {e}")
        except Exception as e:
            self.logger.error(f"Error during emergency shutdown: {e}")

        # Set emergency disable flag
        os.environ["EPOCHLY_EMERGENCY_DISABLE"] = "1"

        self.logger.critical("AUTO-EMERGENCY DISABLE: Complete. Epochly is now disabled.")

    def _determine_enhancement_level_fast(self) -> bool:
        """
        Fast enhancement level determination with EPOCHLY_LEVEL override support.

        Checks EPOCHLY_LEVEL environment variable first. If set, skips progressive
        enhancement and initializes directly at requested level for benchmarking
        and testing scenarios.

        If EPOCHLY_LEVEL not set, uses progressive enhancement (start low, upgrade in background).

        Returns:
            bool: True if explicit level was set via EPOCHLY_LEVEL, False for progressive enhancement
        """
        try:
            # CRITICAL FIX: Check EPOCHLY_LEVEL environment variable
            # If set, skip progressive enhancement and go directly to requested level
            env_level = os.environ.get('EPOCHLY_LEVEL', '').strip()

            if env_level:
                # Parse and validate requested level
                try:
                    requested_level = int(env_level)

                    # Map to EnhancementLevel enum
                    level_map = {
                        0: EnhancementLevel.LEVEL_0_MONITOR,
                        1: EnhancementLevel.LEVEL_1_THREADING,
                        2: EnhancementLevel.LEVEL_2_JIT,
                        3: EnhancementLevel.LEVEL_3_FULL,
                        4: EnhancementLevel.LEVEL_4_GPU
                    }

                    if requested_level in level_map:
                        target_level = level_map[requested_level]

                        # SUBPROCESS SAFETY CHECK: Validate Level 3+ is safe
                        if requested_level >= 3:
                            from ..compatibility.subprocess_safety import detect_subprocess_context, get_max_safe_level

                            subprocess_ctx = detect_subprocess_context()
                            max_safe = get_max_safe_level(subprocess_ctx)

                            if max_safe.value < target_level.value:  # Compare enum values, not enums directly
                                self.logger.warning(
                                    f"EPOCHLY_LEVEL={requested_level} requested but subprocess environment detected. "
                                    f"Auto-downgrading to {max_safe.name} to prevent multiprocessing deadlocks. "
                                    f"Set EPOCHLY_FORCE_LEVEL3=1 to override (may cause hangs)."
                                )
                                target_level = max_safe
                                requested_level = max_safe.value  # Update for initialization logic

                        self.current_level = target_level
                        self.logger.debug(f"EPOCHLY_LEVEL={env_level} set - forcing {target_level.name} (skipping progressive enhancement)")

                        # Initialize the requested level immediately
                        # This skips background detection and progressive validation
                        try:
                            if requested_level == 2:
                                self._initialize_jit_system()
                                # CRITICAL: Signal completion for any waiters
                                self._level2_init_complete.set()
                                self.logger.debug("JIT system initialized immediately (EPOCHLY_LEVEL=2)")
                            elif requested_level == 3:
                                self._initialize_level3_system()
                                # CRITICAL: Signal completion for any waiters
                                self._level3_init_complete.set()
                                self.logger.debug("Level 3 system initialized immediately (EPOCHLY_LEVEL=3)")
                            elif requested_level == 4:
                                # Level 4 requires Level 3 first
                                self._initialize_level3_system()
                                self._level3_init_complete.set()  # Signal Level 3 ready

                                # Try to initialize GPU, fallback to Level 3 if GPU unavailable
                                self._initialize_level4_gpu_system()

                                # Check if GPU actually initialized successfully
                                # _initialize_level4_gpu_system() doesn't raise on failure,
                                # it just sets _level4_gpu_executor to None
                                if not hasattr(self, '_level4_gpu_executor') or self._level4_gpu_executor is None:
                                    # GPU not available - fallback to Level 3
                                    self.logger.warning(
                                        "EPOCHLY_LEVEL=4 requested but GPU not available. "
                                        "Falling back to Level 3. Run 'epochly gpu check' for diagnostics."
                                    )
                                    self.logger.debug("Falling back to LEVEL_3_FULL (GPU hardware or license unavailable)")
                                    self.current_level = EnhancementLevel.LEVEL_3_FULL
                                    # Level 4 init already signaled by _initialize_level4_gpu_system()
                                else:
                                    # FIX (Dec 2025): Actually set the level to LEVEL_4_GPU!
                                    # Previously this path only logged but never set current_level
                                    self.current_level = EnhancementLevel.LEVEL_4_GPU
                                    self.logger.debug("Level 4 GPU system initialized immediately (EPOCHLY_LEVEL=4)")
                                    # Level 4 init already signaled by _initialize_level4_gpu_system()

                            # Return True to signal explicit level was set
                            # Caller should skip background detection
                            return True

                        except Exception as init_error:
                            # Initialization failed - fallback to progressive enhancement
                            self.logger.error(f"Failed to initialize EPOCHLY_LEVEL={requested_level}: {init_error}")
                            self.logger.warning(f"Falling back to progressive enhancement due to initialization failure")
                            # Reset to safe level and let progressive enhancement handle it
                            self.current_level = EnhancementLevel.LEVEL_0_MONITOR
                            # Fall through to progressive enhancement code below

                    else:
                        self.logger.warning(f"Invalid EPOCHLY_LEVEL={env_level} (must be 0-4), using progressive enhancement")

                except ValueError:
                    self.logger.warning(f"Invalid EPOCHLY_LEVEL={env_level} (must be integer), using progressive enhancement")

            # No EPOCHLY_LEVEL set - use progressive enhancement (original behavior)
            # Always start with monitoring (no heavy imports required)
            self.current_level = EnhancementLevel.LEVEL_0_MONITOR
            self.logger.debug(f"Starting at {self.current_level.name} (fast startup)")

            # Quick threading check (no imports needed)
            if sys.version_info >= (3, 8) and threading.active_count() >= 0:
                self.current_level = EnhancementLevel.LEVEL_1_THREADING
                self.logger.debug("Threading support detected - upgraded to LEVEL_1")

            # Return False to signal progressive enhancement should continue
            return False

        except Exception as e:
            self.logger.error(f"Fast enhancement level determination failed: {e}")
            self.current_level = EnhancementLevel.LEVEL_0_MONITOR
            return False

    def _start_detection(self, name: str, target: Callable) -> DetectionThread:
        """
        Start or reuse a detection thread (Task 4/6).

        Unified thread management prevents duplicate threads and provides
        registry-based lifecycle control.

        Args:
            name: Thread name for identification
            target: Target function (should accept stop_event parameter)

        Returns:
            DetectionThread: Started or existing thread instance
        """
        with self._thread_lock:
            # Check if thread already exists and is running
            thread = self._detection_threads.get(name)
            if thread and thread.is_alive():
                # Reuse running thread
                return thread

            # Create new thread
            thread = DetectionThread(name=name, target=target)
            self._detection_threads[name] = thread
            thread.start()

            return thread

    def _start_background_capability_detection(self):
        """
        Start background thread to detect capabilities and upgrade levels.

        P2-2d FIX (Dec 2025): CONSOLIDATED from 4 threads into 1 unified thread.
        Detection tasks have sequential dependencies (Level 3 waits for Level 2, etc.)
        so consolidating them:
        - Saves 3 daemon threads (4 -> 1)
        - Makes the sequential dependency explicit
        - Reduces context switching overhead
        - Maintains the same behavior and timing

        Performance Improvement (Task 4/6):
        - Uses DetectionThread class (non-daemon for proper cleanup)
        - Registry-based lifecycle management
        - Prevents duplicate threads
        - Supports graceful shutdown with exponential backoff

        ARCHITECTURE DECISION (verified with Perplexity + mcp-reflect):
        - Detection threads: Now daemon=False (was daemon=True)
        - Proper shutdown with join + exponential backoff
        Memory-bank reference: benchmarking-system-updates.md lines 456-459
        """
        try:
            # P2-2d FIX: Single unified detection thread runs all detections sequentially
            # This consolidates 4 threads into 1, saving 3 daemon threads
            self._start_detection(
                "EpochlyCapabilityDetection",
                self._unified_background_detection
            )

            self.logger.debug("Background capability detection started (unified thread)")

        except Exception as e:
            self.logger.error(f"Failed to start background capability detection: {e}")

    def _unified_background_detection(self, stop_event: threading.Event):
        """
        P2-2d FIX (Dec 2025): Unified background detection thread.

        Runs all capability detections sequentially in a single thread:
        1. JIT capabilities (Level 2)
        2. Full optimization capabilities (Level 3)
        3. GPU capabilities (Level 4)
        4. Adaptive thresholds (if enabled)

        This consolidates 4 threads into 1, saving 3 daemon threads while
        maintaining the same sequential behavior (each detection waits
        for the previous level anyway).

        Args:
            stop_event: Event to signal thread should stop
        """
        try:
            self.logger.debug("Unified capability detection: Starting")

            # Phase 1: JIT detection
            if not stop_event.is_set():
                self.logger.debug("Unified detection: Running JIT capabilities check")
                self._background_detect_jit_capabilities(stop_event)

            # Phase 2: Full optimization detection
            if not stop_event.is_set():
                self.logger.debug("Unified detection: Running full capabilities check")
                self._background_detect_full_capabilities(stop_event)

            # Phase 3: GPU detection
            if not stop_event.is_set():
                self.logger.debug("Unified detection: Running GPU capabilities check")
                self._background_detect_gpu_capabilities(stop_event)

            # Phase 4: Adaptive thresholds
            if not stop_event.is_set() and self._threshold_adjuster:
                self.logger.debug("Unified detection: Running adaptive thresholds update")
                self._background_update_adaptive_thresholds(stop_event)

            self.logger.debug("Unified capability detection: Complete")

        except Exception as e:
            self.logger.error(f"Unified capability detection error: {e}")

    def _background_detect_jit_capabilities(self, stop_event: threading.Event):
        """
        Background detection of JIT capabilities with progression validation.

        Detects if JIT compilation is available and validates transition
        from Level 1 to Level 2.

        Args:
            stop_event: Event to signal thread should stop
        """
        try:
            # P1-1c FIX (Dec 2025): Use event-based waiting for startup delay
            # Wait a bit to not impact startup, but respond to stop_event immediately
            if stop_event.is_set():
                return
            # CRITICAL FIX (Dec 2025): Clear event BEFORE waiting!
            # The event may already be set from level transition (LEVEL_0 -> LEVEL_1)
            # during initialization. Without clearing first, wait() returns immediately
            # and the 0.5s startup delay is skipped, causing time_at_current_level
            # to be too short when can_progress_to() is checked.
            self._level_changed_event.clear()
            self._level_changed_event.wait(timeout=0.5)
            self._level_changed_event.clear()
            if stop_event.is_set():
                return

            # Check JIT support first (fast check)
            if not self._check_jit_support():
                self._level2_init_complete.set()  # No JIT available
                return

            # JIT is available - wait for stability duration before upgrading
            # This ensures transparent acceleration: user doesn't need to configure anything
            stability_duration = 1.0  # Match enhancement_progression.py (reduced Dec 2025)
            if self.progression_manager:
                stability_duration = self.progression_manager.min_stability_duration

            # P1-1c FIX (Dec 2025): Use event-based waiting instead of polling
            # Wait for stability duration (checking stop_event periodically)
            stability_start = time.time()
            waited = 0.5  # Already waited 0.5s above from startup delay
            while waited < stability_duration:
                if stop_event.is_set():
                    self._level2_init_complete.set()
                    return
                remaining = stability_duration - waited
                # Wait on level_changed_event to react quickly to level changes
                # Use short timeout to check stop_event periodically
                wait_time = min(remaining, 0.5)
                self._level_changed_event.wait(timeout=wait_time)
                self._level_changed_event.clear()
                waited = time.time() - stability_start + 0.5  # Include initial 0.5s wait

            # Now validate progression (stability duration has passed)
            # RCA (Dec 2025): Check enabled before setting level to prevent inconsistent state
            if not self.enabled:
                self.logger.debug("Skipping LEVEL_2 upgrade: Epochly disabled")
                self._level2_init_complete.set()
                return

            if self.progression_manager and self.progression_manager.can_progress_to(
                self.current_level, EnhancementLevel.LEVEL_2_JIT
            ):
                # Initialize JIT system
                self._initialize_jit_system()
                # CRITICAL FIX (Jan 2026): Only upgrade if current level is BELOW target.
                # This prevents race condition where user's explicit set_level(3) gets
                # clobbered by background thread setting level back to 2.
                # The race window exists between can_progress_to() and this assignment.
                if self.current_level.value < EnhancementLevel.LEVEL_2_JIT.value:
                    self.current_level = EnhancementLevel.LEVEL_2_JIT
                    self.logger.debug("Upgraded to LEVEL_2_JIT (JIT compilation available)")
                    # CRITICAL FIX (Dec 2025): Record LEVEL_2 start time for progression tracking
                    # Without this, can_progress_to(LEVEL_3) always fails because time_at_level = 0
                    # Jan 2026: Moved INSIDE the if block to avoid corrupting timestamp when
                    # user has already set a higher level via set_level()
                    if self.progression_manager:
                        self.progression_manager.level_start_time[EnhancementLevel.LEVEL_2_JIT.value] = time.time()
                else:
                    self.logger.debug(f"Skipping LEVEL_2 upgrade: already at {self.current_level.name}")
                self._level2_init_complete.set()
            else:
                self._level2_init_complete.set()  # Signal anyway to unblock waiters
                self.logger.debug("JIT available but progression validation failed")

        except Exception as e:
            self.logger.debug(f"JIT detection error: {e}")
            self._level2_init_complete.set()

    def _background_detect_full_capabilities(self, stop_event: threading.Event):
        """
        Background detection of full optimization capabilities.

        Detects if sub-interpreter and full optimization features
        are available and validates transition to Level 3.

        CRITICAL FIX (Dec 2025): Must wait for Level 2 to actually be SET,
        then wait for stability duration from that point.

        Args:
            stop_event: Event to signal thread should stop
        """
        try:
            self.logger.debug("Level 3 detection: Starting full capabilities detection")

            # Wait for Level 2 init to complete first
            if not self._level2_init_complete.wait(timeout=10.0):
                self.logger.debug("Level 3 detection: Level 2 init timed out, continuing")

            if stop_event.is_set():
                self.logger.debug("Level 3 detection: Stop event set after Level 2 wait, aborting")
                return

            # CRITICAL FIX (Dec 2025): Wait until Level 2 is ACTUALLY SET
            # The _level2_init_complete event may be set before the level is actually upgraded
            # (e.g., during state restoration). We need to wait for current_level >= LEVEL_2_JIT.
            #
            # P1-1c FIX (Dec 2025): Use _level_changed_event for immediate notification
            # instead of polling every 0.5s. This reduces wait time from seconds to <100ms.
            max_wait_for_level2 = 30.0  # Maximum time to wait for Level 2 to be set
            level2_wait_start = time.time()
            while self.current_level.value < EnhancementLevel.LEVEL_2_JIT.value:
                # Check stop_event first (non-blocking)
                if stop_event.is_set():
                    self.logger.debug("Level 3 detection: Stop event set waiting for Level 2")
                    return
                # Check timeout
                elapsed = time.time() - level2_wait_start
                if elapsed > max_wait_for_level2:
                    self.logger.debug("Level 3 detection: Timeout waiting for Level 2 to be set")
                    self._level3_init_complete.set()
                    return
                # Wait on level change event with remaining timeout (max 1s chunks to check stop_event)
                remaining = max_wait_for_level2 - elapsed
                wait_time = min(remaining, 1.0)  # Check stop_event at least every 1s
                self._level_changed_event.wait(timeout=wait_time)
                self._level_changed_event.clear()  # Reset for next wait
            self.logger.debug(f"Level 3 detection: Level 2 is now active (current_level = {self.current_level.name})")

            # Check full optimization support
            full_support = self._check_full_optimization_support()
            self.logger.debug(f"Level 3 detection: full optimization support = {full_support}")
            if full_support:
                # ================================================================
                # PHASE 2 OPTIMIZATION (Dec 2025): Early Worker Spawn
                # Start worker spawn IMMEDIATELY, BEFORE stability wait.
                # This hides most of the ~8s spawn time behind the stability wait.
                # ================================================================

                # Calculate worker count FIRST (license check happens in main process)
                system_cores = multiprocessing.cpu_count()
                try:
                    allowed, max_cores = check_core_limit(system_cores)
                    self.logger.debug(f"License check: allowed={allowed}, max_cores={max_cores} (system has {system_cores})")
                except Exception as e:
                    self.logger.debug(f"License check failed, using system default: {e}")
                    allowed = True
                    max_cores = system_cores

                if allowed:
                    worker_count = min(max_cores, system_cores) if max_cores else system_cores
                else:
                    worker_count = max_cores

                self.logger.debug(f"Level 3 detection: Starting early spawn with {worker_count} workers")

                # Start async worker spawn IMMEDIATELY (non-blocking)
                spawn_future = self._begin_worker_spawn_async(worker_count)

                # Get stability duration from progression manager
                stability_duration = 1.0  # Default, matches min_stability_duration (reduced Dec 2025)
                if self.progression_manager and hasattr(self.progression_manager, 'min_stability_duration'):
                    stability_duration = self.progression_manager.min_stability_duration

                self.logger.debug(f"Level 3 detection: Waiting {stability_duration}s for Level 2 stability (spawn running in parallel)")

                # P1-1c FIX (Dec 2025): Use event-based waiting instead of polling
                # Wait for stability duration (spawn runs in parallel)
                stability_wait_start = time.time()
                while True:
                    if stop_event.is_set():
                        self.logger.debug("Level 3 detection: Stop event set during stability wait")
                        return

                    # Check how long we've been at Level 2
                    if self.progression_manager:
                        time_at_level = self.progression_manager._get_time_at_current_level(self.current_level)
                        if time_at_level >= stability_duration:
                            self.logger.debug(f"Level 3 detection: Stability achieved ({time_at_level:.1f}s >= {stability_duration}s)")
                            break
                    else:
                        # Fallback: simple time-based wait using event for responsiveness
                        remaining = stability_duration - (time.time() - stability_wait_start)
                        if remaining <= 0:
                            break
                        self._level_changed_event.wait(timeout=remaining)
                        self._level_changed_event.clear()
                        break

                    # Wait on level_changed_event to react quickly to level changes
                    # Use short timeout to check stop_event periodically
                    self._level_changed_event.wait(timeout=0.5)
                    self._level_changed_event.clear()

                self.logger.debug("Level 3 detection: Stability wait complete, checking can_progress_to")

                # Now validate progression (stability duration has passed)
                # RCA (Dec 2025): Check enabled before setting level to prevent inconsistent state
                if not self.enabled:
                    self.logger.debug("Skipping LEVEL_3 upgrade: Epochly disabled")
                    self._level3_init_complete.set()
                    return

                # CRITICAL FIX (Dec 2025): Retry progression check multiple times
                max_retry_time = 60.0  # Maximum time to retry progression checks
                retry_interval = 2.0   # Check every 2 seconds
                retry_start = time.time()

                while time.time() - retry_start < max_retry_time:
                    if stop_event.is_set():
                        self.logger.debug("Level 3 detection: Stop event set during progression retry")
                        self._level3_init_complete.set()  # Always signal completion
                        return

                    can_progress = False
                    if self.progression_manager:
                        can_progress = self.progression_manager.can_progress_to(
                            self.current_level, EnhancementLevel.LEVEL_3_FULL
                        )
                        self.logger.debug(f"Level 3 detection: can_progress_to(LEVEL_3_FULL) = {can_progress}")

                    if can_progress:
                        # PHASE 2: Finalize early spawn instead of initializing from scratch
                        # Spawn should be done (or nearly done) by now
                        try:
                            spawn_success = self._finalize_worker_spawn(spawn_future, stop_event)

                            # RCA (Dec 2025): Re-check enabled before committing level change
                            # This closes the race condition between initial check and level set
                            if not self.enabled:
                                self.logger.warning("Aborting LEVEL_3 upgrade: Epochly disabled during spawn")
                                self._level3_init_complete.set()
                                return

                            if spawn_success:
                                # CRITICAL FIX (Jan 2026): Only upgrade if current level is BELOW target.
                                # This prevents race condition where user's explicit set_level(4) gets
                                # clobbered by background thread setting level back to 3.
                                if self.current_level.value < EnhancementLevel.LEVEL_3_FULL.value:
                                    self.current_level = EnhancementLevel.LEVEL_3_FULL
                                    self.logger.debug("Upgraded to LEVEL_3_FULL (full optimization available) - early spawn")
                                    # Record LEVEL_3 start time for progression tracking
                                    if self.progression_manager:
                                        self.progression_manager.level_start_time[EnhancementLevel.LEVEL_3_FULL.value] = time.time()
                                else:
                                    self.logger.debug(f"Skipping LEVEL_3 upgrade: already at {self.current_level.name}")
                            else:
                                # Early spawn failed - fall back to synchronous init
                                self.logger.warning("Early spawn failed, falling back to synchronous Level 3 init")
                                self._initialize_level3_system()
                                # CRITICAL FIX (Jan 2026): Only upgrade if below target
                                if self.current_level.value < EnhancementLevel.LEVEL_3_FULL.value:
                                    self.current_level = EnhancementLevel.LEVEL_3_FULL
                                    self.logger.debug("Upgraded to LEVEL_3_FULL (via fallback)")
                                    # Record LEVEL_3 start time for progression tracking
                                    if self.progression_manager:
                                        self.progression_manager.level_start_time[EnhancementLevel.LEVEL_3_FULL.value] = time.time()
                                else:
                                    self.logger.debug(f"Skipping LEVEL_3 upgrade: already at {self.current_level.name}")

                        except Exception as e:
                            self.logger.error(f"Level 3 initialization failed: {e}")
                        finally:
                            self._level3_init_complete.set()  # Always signal completion
                        return  # Exit the thread

                    # Not yet ready - wait and retry
                    if stop_event.wait(retry_interval):
                        self.logger.debug("Level 3 detection: Stop event set during retry wait")
                        self._level3_init_complete.set()  # Always signal completion
                        return

                # After max retries, signal completion and log at INFO (progression permanently failed)
                self._level3_init_complete.set()
                self.logger.debug(f"Level 3 progression timed out after {max_retry_time}s - staying at Level 2")
            else:
                self._level3_init_complete.set()
                self.logger.debug("Level 3 detection: Full optimization NOT supported")

        except Exception as e:
            self.logger.debug(f"Full capability detection error: {e}")
            self._level3_init_complete.set()

    def _background_detect_gpu_capabilities(self, stop_event: threading.Event):
        """
        Background detection of GPU capabilities.

        Detects if GPU acceleration is available and validates
        transition to Level 4.

        Args:
            stop_event: Event to signal thread should stop
        """
        try:
            # Wait for Level 3 to complete first
            if not self._level3_init_complete.wait(timeout=30.0):
                self.logger.debug("Level 3 init timed out, continuing with GPU detection")

            if stop_event.is_set():
                return

            # RCA (Dec 2025): Check enabled before setting level to prevent inconsistent state
            if not self.enabled:
                self.logger.debug("Skipping LEVEL_4 upgrade: Epochly disabled")
                self._level4_init_complete.set()
                return

            # Check GPU support
            if self._check_gpu_support():
                # Validate progression
                if self.progression_manager and self.progression_manager.can_progress_to(
                    self.current_level, EnhancementLevel.LEVEL_4_GPU
                ):
                    # Initialize Level 4 GPU system
                    self._initialize_level4_gpu_system()
                    if self._level4_gpu_executor:
                        # CRITICAL FIX (Jan 2025 RCA): Clear JIT caches for background upgrade path
                        # Same fix as in set_enhancement_level() - see detailed comments there
                        if hasattr(self, '_auto_profiler') and self._auto_profiler is not None:
                            profiler = self._auto_profiler
                            profiler_lock = getattr(profiler, '_lock', None)
                            if profiler_lock is not None:
                                with profiler_lock:
                                    self._clear_jit_caches_for_gpu_upgrade(profiler)
                            else:
                                self._clear_jit_caches_for_gpu_upgrade(profiler)

                        # CRITICAL FIX (Jan 2026): Only upgrade if current level is BELOW target.
                        # This prevents race condition where user's explicit level setting gets
                        # clobbered by background thread.
                        if self.current_level.value < EnhancementLevel.LEVEL_4_GPU.value:
                            self.current_level = EnhancementLevel.LEVEL_4_GPU
                            self.logger.debug("Upgraded to LEVEL_4_GPU (GPU acceleration available)")
                        else:
                            self.logger.debug(f"Skipping LEVEL_4 upgrade: already at {self.current_level.name}")
                    # _level4_init_complete is set by _initialize_level4_gpu_system
                else:
                    self._level4_init_complete.set()
            else:
                self._level4_init_complete.set()

        except Exception as e:
            self.logger.debug(f"GPU detection error: {e}")
            self._level4_init_complete.set()

    def _background_update_adaptive_thresholds(self, stop_event: threading.Event):
        """
        Background thread for adaptive threshold tuning.

        Periodically updates thresholds based on allocator telemetry.

        Args:
            stop_event: Event to signal thread should stop
        """
        try:
            while not stop_event.is_set():
                # Update every 60 seconds
                if stop_event.wait(60.0):
                    return

                if self._threshold_adjuster:
                    try:
                        self._threshold_adjuster.update_thresholds()
                    except Exception as e:
                        self.logger.debug(f"Threshold update error: {e}")

        except Exception as e:
            self.logger.debug(f"Adaptive threshold thread error: {e}")

    def _determine_enhancement_level(self) -> bool:
        """
        Determine the appropriate enhancement level based on system capabilities.

        This is called during initialization and periodically to adjust the
        enhancement level based on detected capabilities.

        Returns:
            bool: True if explicit level was set, False for progressive enhancement
        """
        return self._determine_enhancement_level_fast()

    def _check_threading_support(self) -> bool:
        """Check if threading optimizations are supported."""
        try:
            # Check for sub-interpreter support (Python 3.12+)
            if sys.version_info >= (3, 12):
                try:
                    import _xxsubinterpreters  # FUTURE-USE: Sub-interpreter support for Python 3.12+
                    return True
                except ImportError:
                    self.logger.debug("Sub-interpreter support not available (Python 3.12+ required)")
                    pass

            # Fallback to standard threading
            return threading.active_count() >= 0

        except Exception:
            return False

    def _check_jit_support(self) -> bool:
        """Check if JIT compilation is supported."""
        try:
            # Check for NumPy (required for some JIT operations)
            import numpy

            # Check for potential JIT backends
            jit_backends = ['numba', 'jax', 'taichi']
            for backend in jit_backends:
                try:
                    __import__(backend)
                    self.logger.debug(f"JIT backend {backend} available")
                    return True
                except ImportError:
                    continue

            return False

        except ImportError:
            return False

    def _check_full_optimization_support(self) -> bool:
        """
        Check if full optimization features are supported (Phase 2.3: with caching).

        Uses TTL-based cache to avoid redundant module imports.
        First call: 10-50ms (imports mmap, ctypes, psutil)
        Cached calls: <1µs (check timestamp + return cached value)

        Returns:
            bool: True if full optimization supported
        """
        # Phase 2.3: Check cache validity
        current_time = time.time()
        if (self._cached_full_optimization_support is not None and
            current_time - self._capabilities_cache_time < self._capabilities_cache_ttl):
            return self._cached_full_optimization_support

        # Cache miss - perform actual check
        try:
            # Check for sub-interpreter support
            if sys.version_info < (3, 12):
                self._cached_full_optimization_support = False
                self._capabilities_cache_time = current_time
                return False

            # Check for required modules
            try:
                import mmap
                import ctypes
            except ImportError:
                self._cached_full_optimization_support = False
                self._capabilities_cache_time = current_time
                return False

            # Check for shared memory support
            try:
                from multiprocessing import shared_memory
            except ImportError:
                self._cached_full_optimization_support = False
                self._capabilities_cache_time = current_time
                return False

            # Check for psutil (memory monitoring)
            try:
                import psutil
            except ImportError:
                # psutil is optional, continue without it
                pass

            self._cached_full_optimization_support = True
            self._capabilities_cache_time = current_time
            return True

        except Exception as e:
            self.logger.debug(f"Full optimization check failed: {e}")
            self._cached_full_optimization_support = False
            self._capabilities_cache_time = current_time
            return False

    def _check_gpu_support(self) -> bool:
        """Check if GPU acceleration is supported."""
        try:
            # First check license
            try:
                from ..licensing.license_enforcer import check_feature
                if not check_feature('gpu_acceleration'):
                    return False
            except ImportError:
                pass  # No license check, continue

            # Check for GPU backend
            try:
                from ..gpu.gpu_detector import GPUDetector
                # Use class method is_available() which checks device_count > 0
                return GPUDetector.is_available()
            except ImportError:
                return False

        except Exception:
            return False

    def set_enhancement_level(self, level: EnhancementLevel, force: bool = False) -> bool:
        """
        Set the enhancement level.

        Args:
            level: Target EnhancementLevel
            force: If True, bypass progression validation (for benchmarking/testing)

        Returns:
            bool: True if level was set successfully
        """
        # Check if system is disabled
        if not self.enabled:
            self.logger.warning("Cannot set enhancement level: Epochly is disabled")
            return False

        # Check if system is initialized
        if not self._initialized:
            self.logger.warning("Cannot set enhancement level: Epochly is not initialized")
            return False

        try:
            with self._lock:
                # Idempotent check: same-level transitions are no-ops (unless forced)
                # This prevents repeated configure() calls from resetting level_start_time
                # which would block progression (see RCA Dec 2025).
                if level == self.current_level and not force:
                    self.logger.debug(f"Already at {level.name}, no-op")
                    return True

                # Validate level transition (unless forced)
                if not force and self.progression_manager:
                    if not self.progression_manager.can_progress_to(self.current_level, level):
                        self.logger.warning(f"Cannot transition from {self.current_level.name} to {level.name} (use force=True to override)")
                        return False

                # Initialize required systems for the target level
                if level.value >= EnhancementLevel.LEVEL_2_JIT.value:
                    # Check if JIT is supported before attempting to initialize
                    if not self._check_jit_support():
                        self.logger.warning("JIT is not supported on this platform")
                        # CRITICAL FIX: Signal completion to unblock waiters before returning
                        # Without this, _level2_init_complete.wait() hangs forever
                        self._level2_init_complete.set()
                        return False
                    if not hasattr(self, '_jit_manager') or self._jit_manager is None:
                        self._initialize_jit_system()

                if level.value >= EnhancementLevel.LEVEL_3_FULL.value:
                    # CRITICAL FIX (2025-11-24): Defer Level 3 initialization to prevent fork bomb
                    # During bootstrap (sitecustomize.py), creating ProcessPool causes workers to
                    # recursively bootstrap Epochly. Instead, defer executor creation until first use.
                    if not hasattr(self, '_sub_interpreter_executor') or self._sub_interpreter_executor is None:
                        self._level3_deferred = True
                        self.logger.debug("Level 3 deferred - executor will be created on first use")

                if level.value >= EnhancementLevel.LEVEL_4_GPU.value:
                    # Track if we're actually upgrading to LEVEL_4 (for cache clearing decision)
                    upgrading_to_level4 = self.current_level.value < EnhancementLevel.LEVEL_4_GPU.value

                    if not hasattr(self, '_level4_gpu_executor') or self._level4_gpu_executor is None:
                        self._initialize_level4_gpu_system()
                        if not self._level4_gpu_executor:
                            self.logger.warning(
                                "GPU not available, staying at Level 3. "
                                "Run 'epochly gpu check' for diagnostics."
                            )
                            level = EnhancementLevel.LEVEL_3_FULL

                    # CRITICAL FIX (Jan 2025 RCA): Clear JIT compiled cache when upgrading to LEVEL_4
                    # WITHOUT this fix, functions compiled at LEVEL_3 (CPU JIT) are marked as "done"
                    # in _jit_compiled_code_ids, preventing GPU compilation at LEVEL_4.
                    # The symptom: LEVEL_4 shows identical times to LEVEL_3 (1.0x speedup).
                    #
                    # Root cause traced via mcp-reflect:
                    # 1. LEVEL_3 runs, CPU JIT compiles function, adds code_id to _jit_compiled_code_ids
                    # 2. LEVEL_4 is set
                    # 3. Function runs again, but auto_profiler skips it (line ~2476):
                    #    if code_id in self._jit_compiled_code_ids: return None
                    # 4. GPU compilation is never attempted
                    #
                    # Fix: When upgrading TO LEVEL_4 AND GPU is available, clear the cache so
                    # functions can be re-analyzed for GPU acceleration. Non-GPU functions will
                    # fall through to CPU JIT and get re-cached.
                    #
                    # mcp-reflect review improvements (Jan 2025):
                    # - Only clear if we're ACTUALLY staying at LEVEL_4 (not falling back to LEVEL_3)
                    # - Use profiler lock for thread safety
                    # - Check level AFTER GPU availability check
                    if (upgrading_to_level4 and
                        level.value >= EnhancementLevel.LEVEL_4_GPU.value and
                        hasattr(self, '_auto_profiler') and self._auto_profiler is not None):

                        profiler = self._auto_profiler
                        # Use profiler's lock for thread safety (callbacks may be running)
                        profiler_lock = getattr(profiler, '_lock', None)

                        if profiler_lock is not None:
                            with profiler_lock:
                                self._clear_jit_caches_for_gpu_upgrade(profiler)
                        else:
                            # Fallback if no lock (shouldn't happen in practice)
                            self._clear_jit_caches_for_gpu_upgrade(profiler)

                self.current_level = level

                # CRITICAL FIX (Dec 2025): Record level_start_time for progression tracking
                # Without this, can_progress_to() always fails because time_at_level = 0
                if self.progression_manager:
                    self.progression_manager.level_start_time[level.value] = time.time()

                # CRITICAL FIX (Jan 2025): Signal completion events on SUCCESS to unblock waiters
                # Tests wait on these events; without setting them, tests timeout forever.
                # Previously only set on failure, but SUCCESS also needs to signal.
                if level.value >= EnhancementLevel.LEVEL_2_JIT.value:
                    self._level2_init_complete.set()
                if level.value >= EnhancementLevel.LEVEL_3_FULL.value:
                    self._level3_init_complete.set()
                if level.value >= EnhancementLevel.LEVEL_4_GPU.value:
                    self._level4_init_complete.set()

                self.logger.debug(f"Enhancement level set to {level.name}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to set enhancement level: {e}")
            # CRITICAL FIX (Jan 2025): Set completion events even on failure to prevent infinite hangs
            # Without this, waiters on these events will block forever if initialization fails.
            # Bug #2 regression test: test_level2_signals_on_failure
            if level.value >= EnhancementLevel.LEVEL_2_JIT.value:
                self._level2_init_complete.set()
            if level.value >= EnhancementLevel.LEVEL_3_FULL.value:
                self._level3_init_complete.set()
            if level.value >= EnhancementLevel.LEVEL_4_GPU.value:
                self._level4_init_complete.set()
            return False

    def get_enhancement_level(self) -> EnhancementLevel:
        """Get the current enhancement level."""
        return self.current_level

    def enable_monitoring(self, enable: bool = True) -> None:
        """
        Enable or disable performance monitoring.

        Args:
            enable: If True, start monitoring. If False, stop monitoring.
        """
        if not self.performance_monitor:
            return

        if enable:
            if not self.performance_monitor.is_active():
                self.performance_monitor.start()
        else:
            if self.performance_monitor.is_active():
                self.performance_monitor.stop()

    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive Epochly status including stability metrics.

        Returns:
            Dictionary containing:
            - enabled: Whether Epochly is enabled
            - initialized: Whether core is fully initialized
            - enhancement_level: Current enhancement level name
            - level_value: Numeric value of current level
            - python_version: Python version string
            - platform: Operating system platform
            - stability_metrics: P1-1 stability gate metrics (if available)
            - performance_config: Current performance configuration
        """
        import platform as _platform

        # Check if monitoring is active
        monitoring_active = False
        if self.performance_monitor is not None:
            try:
                monitoring_active = self.performance_monitor.is_active()
            except Exception:
                monitoring_active = False

        status = {
            'enabled': self.enabled,
            'initialized': self._initialized,
            'enhancement_level': self.current_level.name,
            'level_value': self.current_level.value,
            'level': self.current_level.value,  # Alias for level_value for backwards compatibility
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'platform': _platform.system(),
            'closed': self._closed,
            'monitoring_active': monitoring_active,
        }

        # P1-1: Include stability metrics from progression manager
        if hasattr(self, 'progression_manager') and self.progression_manager is not None:
            try:
                status['stability_metrics'] = self.progression_manager.get_stability_metrics()
            except Exception as e:
                status['stability_metrics'] = {'error': str(e)}
        else:
            status['stability_metrics'] = None

        # Include performance config if available
        if hasattr(self, 'performance_config') and self.performance_config is not None:
            try:
                status['performance_config'] = self.performance_config.to_dict()
            except Exception:
                status['performance_config'] = None

        # Include JIT system status if Level 2+ is active
        if self.current_level.value >= EnhancementLevel.LEVEL_2_JIT.value:
            if hasattr(self, '_jit_manager') and self._jit_manager is not None:
                try:
                    jit_stats = self._jit_manager.get_statistics()
                    status['jit_system'] = {
                        'enabled': True,
                        'available_backends': jit_stats.get('available_backends', []),
                        'compiled_functions': jit_stats.get('total_compiled_functions', 0),
                        'successful_compilations': jit_stats.get('successful_compilations', 0),
                        'beneficial_compilations': jit_stats.get('beneficial_compilations', 0),
                        'background_compilation_running': jit_stats.get('background_compilation_running', False)
                    }
                except Exception as e:
                    status['jit_system'] = {'enabled': True, 'error': str(e)}

            # Include adaptive orchestrator status
            if hasattr(self, '_adaptive_orchestrator') and self._adaptive_orchestrator is not None:
                try:
                    orch_stats = self._adaptive_orchestrator.get_performance_summary()
                    status['adaptive_orchestrator'] = {
                        'enabled': True,
                        'monitoring_active': orch_stats.get('monitoring_active', False),
                        'current_pool': orch_stats.get('current_pool', 'unknown'),
                        'adaptation_count': orch_stats.get('adaptation_count', 0)
                    }
                    if 'jit_statistics' in orch_stats:
                        status['adaptive_orchestrator']['jit_coordination'] = orch_stats['jit_statistics']
                except Exception as e:
                    status['adaptive_orchestrator'] = {'enabled': True, 'error': str(e)}

        # Include Level 4 GPU system status if active OR if Level 4 was attempted
        level4_attempted = hasattr(self, '_level4_init_complete') and self._level4_init_complete.is_set()
        level4_active = self.current_level.value >= EnhancementLevel.LEVEL_4_GPU.value

        if level4_active or level4_attempted:
            if hasattr(self, '_level4_gpu_executor') and self._level4_gpu_executor is not None:
                try:
                    gpu_stats = self._level4_gpu_executor.get_performance_stats()
                    gpu_status = {
                        'enabled': True,
                        'gpu_available': gpu_stats.get('gpu_available', False),
                        'gpu_enabled': gpu_stats.get('gpu_enabled', False),
                        'total_requests': gpu_stats.get('total_requests', 0),
                        'gpu_executions': gpu_stats.get('gpu_executions', 0),
                        'gpu_usage_ratio': gpu_stats.get('gpu_usage_ratio', 0.0),
                        'fallback_ratio': gpu_stats.get('fallback_ratio', 0.0),
                        'avg_gpu_time': gpu_stats.get('avg_gpu_time', 0.0),
                        'avg_cpu_time': gpu_stats.get('avg_cpu_time', 0.0)
                    }

                    # Add CuPy stats if available
                    if 'cupy_stats' in gpu_stats:
                        gpu_status['cupy_stats'] = gpu_stats['cupy_stats']

                    # Add GPU info if available
                    try:
                        gpu_info = self._level4_gpu_executor.get_gpu_info()
                        if gpu_info is not None:
                            gpu_status['gpu_info'] = {
                                'device_name': gpu_info.get('device_name', 'Unknown'),
                                'memory_total_gb': gpu_info.get('memory_total', 0) / (1024**3),
                                'compute_capability': gpu_info.get('compute_capability', 'Unknown'),
                                'cuda_version': gpu_info.get('cuda_version', 'Unknown')
                            }
                    except Exception:
                        pass

                    status['level4_gpu_system'] = gpu_status
                except Exception as e:
                    status['level4_gpu_system'] = {'enabled': True, 'error': str(e)}
            else:
                # Level 4 was attempted but GPU is not available
                status['level4_gpu_system'] = {
                    'enabled': False,
                    'reason': 'GPU not available or not initialized'
                }

        return status

    def optimize(self, func: Callable) -> Callable:
        """
        Optimize a callable based on current enhancement level.

        This is the main entry point for optimization. It wraps the
        given function with appropriate optimizations based on the
        current enhancement level.

        Args:
            func: The function to optimize

        Returns:
            Optimized wrapper function
        """
        if not self.enabled or not self._initialized:
            return func

        # Route to appropriate optimizer based on level
        if self.current_level.value >= EnhancementLevel.LEVEL_4_GPU.value:
            return self._optimize_gpu(func)
        elif self.current_level.value >= EnhancementLevel.LEVEL_3_FULL.value:
            return self._optimize_full(func)
        elif self.current_level.value >= EnhancementLevel.LEVEL_2_JIT.value:
            return self._optimize_jit(func)
        elif self.current_level.value >= EnhancementLevel.LEVEL_1_THREADING.value:
            return self._optimize_threading(func)
        else:
            return func

    def optimize_function(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
        level: Union['EnhancementLevel', int] = None,
        monitor_performance: bool = True,
        **options
    ) -> Any:
        """
        Optimize and execute a function with specified enhancement level.

        This method is called by decorators to optimize a function with
        a specific enhancement level and execute it immediately.

        Args:
            func: The function to optimize and execute
            args: Positional arguments to pass to the function
            kwargs: Keyword arguments to pass to the function
            level: Enhancement level to use (overrides current_level)
            monitor_performance: Whether to monitor performance
            **options: Additional optimization options

        Returns:
            The result of the optimized function execution
        """
        if not self.enabled or not self._initialized:
            return func(*args, **kwargs)

        # Determine which level to use
        if level is not None:
            if isinstance(level, int):
                target_level = EnhancementLevel(level)
            else:
                target_level = level
        else:
            target_level = self.current_level

        # =================================================================
        # P0.26 FIX (Jan 2026): ON-DEMAND INITIALIZATION FOR DECORATOR PATH
        # =================================================================
        # Previously, decorators could request Level 2/3/4 but the managers
        # would be None because only set_level() initialized them.
        # Now we initialize on-demand when a decorator requests a specific level.
        #
        # FIX (Jan 2026): FAST-PATH OPTIMIZATION FOR REPEATED CALLS
        # The original hasattr() checks run on EVERY call, causing +11.9% overhead.
        # Use _initialized_level integer comparison (essentially free) for fast path.
        # Only do expensive hasattr() checks when initializing for a NEW level.

        # Fast path: if already initialized for this level, skip all checks
        if target_level.value <= self._initialized_level:
            pass  # Already initialized, no overhead from getattr() checks
        else:
            # On-demand initialization (first call for this level only)
            # Use getattr() with default None to safely check attributes that may not exist
            # This is still faster than hasattr() on every call since we only hit this
            # path during first-time initialization

            # Fix 2: On-demand JIT initialization for Level 2+
            if target_level.value >= EnhancementLevel.LEVEL_2_JIT.value:
                if getattr(self, '_jit_manager', None) is None:
                    self.logger.debug(
                        f"P0.26: On-demand JIT initialization for decorator request (level={target_level.value})"
                    )
                    self._initialize_jit_system()

            # Fix 5: On-demand Level 3 initialization
            if target_level.value >= EnhancementLevel.LEVEL_3_FULL.value:
                if getattr(self, '_sub_interpreter_executor', None) is None:
                    # Set _level3_deferred so _ensure_level3_initialized() will work
                    if not getattr(self, '_level3_deferred', False):
                        self.logger.debug(
                            f"P0.26: On-demand Level 3 initialization for decorator request (level={target_level.value})"
                        )
                        self._level3_deferred = True

            # Fix 6: On-demand Level 4 GPU initialization
            if target_level.value >= EnhancementLevel.LEVEL_4_GPU.value:
                if getattr(self, '_level4_gpu_executor', None) is None:
                    self.logger.debug(
                        f"P0.26: On-demand Level 4 GPU initialization for decorator request (level={target_level.value})"
                    )
                    self._initialize_level4_gpu_system()

            # Update _initialized_level to enable fast path on subsequent calls
            self._initialized_level = max(self._initialized_level, target_level.value)

        # Route to appropriate optimizer based on level
        if target_level.value >= EnhancementLevel.LEVEL_4_GPU.value:
            optimized = self._optimize_gpu(func)
        elif target_level.value >= EnhancementLevel.LEVEL_3_FULL.value:
            optimized = self._optimize_full(func)
        elif target_level.value >= EnhancementLevel.LEVEL_2_JIT.value:
            optimized = self._optimize_jit(func)
        elif target_level.value >= EnhancementLevel.LEVEL_1_THREADING.value:
            optimized = self._optimize_threading(func)
        else:
            optimized = func

        # Execute the optimized function
        return optimized(*args, **kwargs)

    def _optimize_threading(self, func: Callable) -> Callable:
        """Apply Level 1 threading optimizations."""
        # Basic thread pool wrapper
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            executor = self._get_thread_executor()
            if executor:
                try:
                    return executor.submit(func, *args, **kwargs).result()
                except Exception:
                    return func(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper

    def _optimize_jit(self, func: Callable) -> Callable:
        """Apply Level 2 JIT optimizations."""
        if not hasattr(self, '_jit_manager') or self._jit_manager is None:
            # P0.26 FIX: Log warning instead of silent fallback
            self.logger.warning(
                f"JIT optimization requested but JIT manager is None for {getattr(func, '__name__', 'unknown')}. "
                f"Returning original function. Call epochly.set_level(2) or set EPOCHLY_LEVEL=2 to enable JIT."
            )
            return func
        try:
            # CRITICAL FIX (Dec 14 2025): Call correct JITManager method
            # JITManager has compile_function_auto(), not optimize()
            # bypass_call_count=True: Skip call count filter for immediate compilation
            # skip_benchmark=True: Skip benchmarking to avoid compilation delay
            compiled = self._jit_manager.compile_function_auto(
                func, bypass_call_count=True, skip_benchmark=True
            )
            return compiled if compiled is not None else func
        except Exception as e:
            self.logger.debug(f"JIT compilation failed for {getattr(func, '__name__', 'unknown')}: {e}")
            return func

    def _optimize_full(self, func: Callable) -> Callable:
        """
        Apply Level 3 full optimizations.

        CRITICAL FIX (Dec 2025): Added adaptive dispatch that samples execution time
        and only uses ProcessPool for functions that run long enough to amortize IPC overhead.
        Fast functions (< level3_min_work_ms) stay at Level 2 JIT optimization.

        CRITICAL FIX (Dec 14 2025): JIT-compile the function FIRST before wrapping.
        Previously, the local fallback called the original Python function instead of
        JIT-compiled code, causing Level 3 to be SLOWER than Level 2 for small workloads!
        """
        # CRITICAL FIX (2025-11-24): Trigger lazy Level 3 initialization
        # This ensures ProcessPool is created on first optimization request
        if not hasattr(self, '_sub_interpreter_executor') or self._sub_interpreter_executor is None:
            if not self._ensure_level3_initialized():
                # P0.26 FIX: Log warning instead of silent fallback
                self.logger.warning(
                    f"Level 3 parallel optimization requested but executor is None for {getattr(func, '__name__', 'unknown')}. "
                    f"Falling back to JIT (Level 2). Call epochly.set_level(3) or set EPOCHLY_LEVEL=3 to enable parallelism."
                )
                return self._optimize_jit(func)  # Fallback to JIT if init fails

        # CRITICAL FIX (Dec 14 2025): JIT-compile the function FIRST
        # So local fallback runs JIT code, not pure Python
        # This prevents Level 3 from being slower than Level 2 for small workloads
        jit_func = self._optimize_jit(func)

        # Get threshold from config or environment
        import os
        min_work_ms = 2000.0  # Default 2 seconds (conservative)
        try:
            env_min_work = os.environ.get('EPOCHLY_LEVEL3_MIN_WORK_MS')
            if env_min_work is not None:
                min_work_ms = float(env_min_work)
            else:
                from ..performance_config import DEFAULT_PERFORMANCE_CONFIG
                min_work_ms = DEFAULT_PERFORMANCE_CONFIG.process_pool.level3_min_work_ms
        except Exception:
            pass

        # Tracking state for adaptive dispatch (per-function)
        func_id = id(func)
        sample_times_key = f'_level3_sample_times_{func_id}'
        use_processpool_key = f'_level3_use_processpool_{func_id}'

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Fast path: Already determined this function should NOT use ProcessPool
            if getattr(self, use_processpool_key, None) is False:
                return jit_func(*args, **kwargs)  # JIT-optimized local execution

            # Fast path: Already determined this function SHOULD use ProcessPool
            if getattr(self, use_processpool_key, None) is True:
                try:
                    return self._sub_interpreter_executor.submit(jit_func, *args, **kwargs).result()
                except Exception:
                    return jit_func(*args, **kwargs)

            # Sampling phase: Measure execution time to decide
            import time
            sample_times = getattr(self, sample_times_key, None)
            if sample_times is None:
                sample_times = []
                setattr(self, sample_times_key, sample_times)

            if len(sample_times) < 3:
                # Still sampling - run JIT-compiled locally and measure
                start = time.perf_counter_ns()
                result = jit_func(*args, **kwargs)
                elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
                sample_times.append(elapsed_ms)

                if len(sample_times) >= 3:
                    # Enough samples - make decision
                    avg_time_ms = sum(sample_times) / len(sample_times)
                    if avg_time_ms >= min_work_ms:
                        setattr(self, use_processpool_key, True)
                        self.logger.debug(
                            f"Level 3 adaptive dispatch: {func.__name__} ({avg_time_ms:.1f}ms avg) "
                            f">= {min_work_ms}ms threshold - enabling ProcessPool"
                        )
                    else:
                        setattr(self, use_processpool_key, False)
                        self.logger.debug(
                            f"Level 3 adaptive dispatch: {func.__name__} ({avg_time_ms:.1f}ms avg) "
                            f"< {min_work_ms}ms threshold - staying local (JIT only)"
                        )
                return result
            else:
                # Should not reach here, but fallback to JIT-optimized local
                return jit_func(*args, **kwargs)

        return wrapper

    def _optimize_gpu(self, func: Callable) -> Callable:
        """Apply Level 4 GPU optimizations."""
        if not hasattr(self, '_level4_gpu_executor') or self._level4_gpu_executor is None:
            # P0.26 FIX: Log warning instead of ZERO logging on fallback
            # This was the WORST offender - users lost 8x performance silently
            self.logger.warning(
                f"Level 4 GPU optimization requested but GPU executor is None for {getattr(func, '__name__', 'unknown')}. "
                f"Falling back to Level 3 parallelism. Call epochly.set_level(4) or set EPOCHLY_LEVEL=4 to enable GPU. "
                f"Ensure GPU is available and CUDA is properly configured."
            )
            return self._optimize_full(func)  # Fallback to Level 3

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # API: execute(func, *args, **kwargs) -> result_value
                return self._level4_gpu_executor.execute(func, *args, **kwargs)
            except Exception:
                return func(*args, **kwargs)
        return wrapper

    def _apply_level_4_gpu_enhancement(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict
    ) -> Any:
        """
        Apply Level 4 GPU enhancement to a single function call.

        This method executes a function with GPU acceleration if available,
        falling back to Level 3 and then to direct execution if GPU fails.

        Args:
            func: The function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function

        Returns:
            The result of the function execution
        """
        if not hasattr(self, '_level4_gpu_executor') or self._level4_gpu_executor is None:
            # Fallback to Level 3 enhancement
            return self._apply_level_3_full_enhancement(func, args, kwargs)

        try:
            # Create execution request for the GPU executor
            from ..plugins.executor.gpu_executor import GPUExecutionRequest
            request = GPUExecutionRequest(
                func=func,
                args=args,
                kwargs=kwargs
            )

            # Execute on GPU
            result = self._level4_gpu_executor.execute_function(request)

            # Record performance metrics if monitor is available
            if self.performance_monitor and hasattr(result, 'execution_time'):
                try:
                    self.performance_monitor.record_metric(
                        metric_type='gpu_execution',
                        value=result.execution_time,
                        context={
                            'enhancement_level': 'LEVEL_4_GPU',
                            'executed_on_gpu': getattr(result, 'executed_on_gpu', False),
                            'actual_speedup': getattr(result, 'actual_speedup', 1.0)
                        }
                    )
                except Exception:
                    pass  # Don't fail on performance monitoring errors

            # Return the actual result (unwrap from ExecutionResult)
            return result.result if hasattr(result, 'result') else result

        except Exception:
            # GPU execution failed, try Level 3 fallback
            try:
                return self._apply_level_3_full_enhancement(func, args, kwargs)
            except Exception:
                # Level 3 also failed, execute directly
                return func(*args, **kwargs)

    def _apply_level_3_full_enhancement(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict
    ) -> Any:
        """
        Apply Level 3 full enhancement to a single function call.

        Falls back to direct execution if Level 3 is not available.

        Args:
            func: The function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function

        Returns:
            The result of the function execution
        """
        # Check if Level 3 executor is available
        if not hasattr(self, '_sub_interpreter_executor') or self._sub_interpreter_executor is None:
            # Try to initialize Level 3
            self._ensure_level3_initialized()

        if hasattr(self, '_sub_interpreter_executor') and self._sub_interpreter_executor:
            try:
                future = self._sub_interpreter_executor.submit(func, *args, **kwargs)
                return future.result()
            except Exception:
                pass  # Fall through to direct execution

        # Direct execution fallback
        return func(*args, **kwargs)

    def submit_task(self, func: Callable, *args, **kwargs):
        """
        Submit a task for optimization and execution.

        Routes to appropriate executor based on current enhancement level.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Future-like object for async result retrieval
        """
        if not self.enabled or not self._initialized:
            # Direct execution fallback
            class DirectResult:
                def __init__(self, result):
                    self._result = result
                def result(self):
                    return self._result
            return DirectResult(func(*args, **kwargs))

        # Route based on level
        if self.current_level.value >= EnhancementLevel.LEVEL_4_GPU.value:
            if hasattr(self, '_level4_gpu_executor') and self._level4_gpu_executor:
                return self._level4_gpu_executor.submit(func, *args, **kwargs)

        if self.current_level.value >= EnhancementLevel.LEVEL_3_FULL.value:
            # CRITICAL FIX (2025-11-24): Trigger lazy Level 3 initialization
            if not hasattr(self, '_sub_interpreter_executor') or self._sub_interpreter_executor is None:
                self._ensure_level3_initialized()
            if hasattr(self, '_sub_interpreter_executor') and self._sub_interpreter_executor:
                return self._sub_interpreter_executor.submit(func, *args, **kwargs)

        if self.current_level.value >= EnhancementLevel.LEVEL_1_THREADING.value:
            executor = self._get_thread_executor()
            if executor:
                return executor.submit(func, *args, **kwargs)

        # Fallback to direct execution
        class DirectResult:
            def __init__(self, result):
                self._result = result
            def result(self):
                return self._result
        return DirectResult(func(*args, **kwargs))

    def configure(self, enhancement_level: Optional[EnhancementLevel] = None, force: bool = False, **kwargs):
        """
        Configure Epochly settings.

        Args:
            enhancement_level: Target enhancement level to set
            force: If True, bypass progression validation (for CLI/explicit level setting)
            **kwargs: Additional configuration options (reserved for future use)
        """
        if enhancement_level is not None:
            self.set_enhancement_level(enhancement_level, force=force)

        # Process other configuration options (if any)
        for key, value in kwargs.items():
            self.logger.debug(f"Configuration option {key}={value} (not yet implemented)")

    def reset_metrics(self):
        """
        Reset performance metrics.

        Delegates to the performance monitor to reset all metrics.
        This is a convenience method for tests and monitoring.
        """
        if self.performance_monitor:
            try:
                self.performance_monitor.reset_metrics()
            except Exception as e:
                self.logger.warning(f"Failed to reset metrics: {e}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary from monitoring system.

        Returns:
            Dictionary containing performance metrics summary,
            or empty dict if monitoring not available
        """
        if not self.performance_monitor:
            return {'total_metrics': 0}

        try:
            # Get metrics from performance monitor
            all_metrics = self.performance_monitor.get_all_metrics()

            # Calculate summary statistics
            summary = {
                'total_metrics': len(all_metrics),
                'metrics': {}
            }

            for name, values in all_metrics.items():
                if values:
                    summary['metrics'][name] = {
                        'count': len(values),
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values)
                    }

            return summary
        except Exception as e:
            self.logger.debug(f"Failed to get performance summary: {e}")
            return {'error': str(e), 'total_metrics': 0}

    def shutdown(self):
        """
        Shut down the Epochly core system gracefully.

        Stops all background threads, releases resources, and resets state.
        """
        if self._closed:
            return

        self._closed = True
        self.logger.debug("Shutting down Epochly core system...")

        # Stop auto emergency detector first (R-SAFE-04)
        if hasattr(self, '_auto_emergency_detector') and self._auto_emergency_detector:
            try:
                self._auto_emergency_detector.stop()
                self.logger.debug("AutoEmergencyDetector stopped")
            except Exception as e:
                self.logger.debug(f"Error stopping AutoEmergencyDetector: {e}")

        # CRITICAL FIX (Jan 2026): Suspend sys.monitoring during shutdown to prevent deadlock
        # Python 3.12 Bug: sys.monitoring callbacks can cause deadlock when joining
        # ProcessPool workers during shutdown. Same fix as for spawn.
        monitoring_state = self._suspend_monitoring_for_spawn()

        # Stop detection threads with exponential backoff
        with self._thread_lock:
            # Python 3.13 Fix: Wrap in list() to avoid "dictionary changed size during iteration"
            for name, thread in list(self._detection_threads.items()):
                try:
                    thread.request_stop()
                except Exception:
                    pass

            # Join threads with backoff
            backoff = 0.1
            for name, thread in list(self._detection_threads.items()):
                if thread.is_alive():
                    thread.join(timeout=backoff)
                    backoff = min(backoff * 2, 2.0)  # Cap at 2 seconds

            self._detection_threads.clear()

        # CRITICAL FIX (Dec 2025): Stop spawn thread and cleanup executor to prevent sub-interpreter crash
        # The spawn thread creates SubInterpreterExecutor in background. If not stopped,
        # it continues running after singleton reset, creating sub-interpreters while
        # the next EpochlyCore instance is also trying to create them → Fatal Python error.
        #
        # Key insight: The executor is created INSIDE spawn_workers and only stored on self
        # AFTER spawn completes. We MUST wait for spawn to complete and cleanup the executor
        # from the spawn result, otherwise old sub-interpreters remain alive.
        if self._stop_spawn_event:
            self._stop_spawn_event.set()

        # Wait for spawn_future to complete (this gives us the executor to shut down)
        # Spawn takes ~8s, so we wait up to 15s to ensure it completes
        if self._spawn_future:
            try:
                spawn_result = self._spawn_future.result(timeout=15.0)
                # Shut down the executor from spawn result if we don't already have it
                if spawn_result and spawn_result.get('executor'):
                    executor = spawn_result.get('executor')
                    if executor and executor != getattr(self, '_sub_interpreter_executor', None):
                        self.logger.debug("Shutting down executor from spawn result")
                        try:
                            executor.shutdown(wait=True)
                        except Exception as e:
                            self.logger.debug(f"Failed to shutdown spawn executor: {e}")
            except TimeoutError:
                self.logger.warning("Spawn future did not complete within timeout")
            except Exception as e:
                self.logger.debug(f"Error waiting for spawn future: {e}")

        # Also wait for spawn thread to finish
        if self._spawn_thread and self._spawn_thread.is_alive():
            self.logger.debug("Waiting for spawn thread to complete...")
            self._spawn_thread.join(timeout=5.0)  # Additional wait after future
            if self._spawn_thread.is_alive():
                self.logger.warning("Spawn thread did not terminate within timeout")
        self._spawn_thread = None

        # Stop auto-profiler
        if hasattr(self, '_auto_profiler') and self._auto_profiler:
            try:
                self._auto_profiler.disable()
            except Exception:
                pass

        # Stop JIT background compilation
        if hasattr(self, '_jit_manager') and self._jit_manager:
            try:
                self._jit_manager.stop_background_compilation()
            except Exception:
                pass
            try:
                self._jit_manager.cleanup()
            except Exception:
                pass
            self._jit_manager = None

        # Stop adaptive orchestrator
        if hasattr(self, '_adaptive_orchestrator') and self._adaptive_orchestrator:
            try:
                self._adaptive_orchestrator.stop_monitoring()
            except Exception:
                pass
            self._adaptive_orchestrator = None

        # Shut down thread executor
        if hasattr(self, '_thread_executor') and self._thread_executor:
            try:
                self._thread_executor.shutdown(wait=False)
            except Exception:
                pass
            self._thread_executor = None

        # Shut down sub-interpreter executor (also known as level3 executor)
        if hasattr(self, '_sub_interpreter_executor') and self._sub_interpreter_executor:
            try:
                self._sub_interpreter_executor.shutdown(wait=True)
            except Exception:
                pass
            self._sub_interpreter_executor = None
        # Also clear the alias
        if hasattr(self, '_level3_executor'):
            self._level3_executor = None

        # Shut down GPU executor (level4)
        if hasattr(self, '_level4_gpu_executor') and self._level4_gpu_executor:
            try:
                self._level4_gpu_executor.shutdown()
            except Exception:
                pass
            self._level4_gpu_executor = None

        # Stop performance monitor
        if self.performance_monitor:
            try:
                self.performance_monitor.stop()
            except Exception:
                pass

        # Save state for next session
        try:
            from ..core.state_manager import get_state_manager
            state_manager = get_state_manager()
            state_manager.save_state(self)
        except Exception:
            pass

        # Mark as not initialized after shutdown
        self._initialized = False
        self.logger.debug("Epochly core system shut down complete")


# Module-level singleton and lock
_epochly_core: Optional[EpochlyCore] = None
_core_lock = threading.Lock()


def get_epochly_core() -> EpochlyCore:
    """
    Get the global Epochly core instance with thread safety.

    WORKER PROTECTION: Returns a minimal no-op core in worker processes
    to prevent fork bomb from recursive ProcessPoolExecutor creation.

    CRITICAL FIX (Nov 23, 2025): Now calls initialize() after creating core.
    Previous bug: get_epochly_core() created EpochlyCore() but never called
    initialize(), leaving _initialized=False. This broke benchmarks that
    called auto_enable() without force=True.

    CRITICAL FIX (Dec 2025): Replace WorkerNoOpCore when no longer in worker context.
    Previous bug: During Level 3 init, env vars are temporarily set causing
    _is_worker_process() to return True. If get_epochly_core() was called during
    this window, a WorkerNoOpCore was created and NEVER replaced, causing 5x slowdown.

    P3-1 FIX (Dec 2025): Return existing EpochlyCore even when _is_worker_process()
    returns True due to temporarily set env vars. An already-initialized core should
    keep running during ProcessPool init. The env vars are meant to prevent NEW
    initialization in actual workers, not to replace an existing core in the main process.
    """
    global _epochly_core

    # P3-1 FIX: Check for existing REAL core BEFORE worker check.
    # If we already have a real EpochlyCore instance, return it regardless of env vars.
    # This prevents the main process core from being replaced by WorkerNoOpCore
    # when EPOCHLY_DISABLE=1 is temporarily set during ProcessPool initialization.
    #
    # CRITICAL: Check BOTH _epochly_core AND EpochlyCore._instance!
    # When initialization happens via __init__.py's _ensure_core_initialized(),
    # it creates EpochlyCore._instance but doesn't set _epochly_core.
    # We need to check both to detect an already-running core.
    if isinstance(_epochly_core, EpochlyCore):
        return _epochly_core

    # Also check the class-level singleton - it may exist if init happened elsewhere
    if EpochlyCore._instance is not None and isinstance(EpochlyCore._instance, EpochlyCore):
        # Sync the module-level variable with class-level singleton
        _epochly_core = EpochlyCore._instance
        return _epochly_core

    # CRITICAL: Worker protection - prevent recursive initialization fork bomb
    # Only applies when we DON'T have a real EpochlyCore anywhere
    if _is_worker_process():
        # Return a minimal no-op core that won't create more workers
        if _epochly_core is None:
            # Only create WorkerNoOpCore if we don't have any core yet
            class WorkerNoOpCore:
                """
                Minimal no-op core for worker processes.

                Prevents fork bomb by providing safe no-op methods that don't
                create ProcessPoolExecutors or other resource-intensive objects.
                All methods are intentionally no-ops to prevent recursive initialization.
                """
                # CRITICAL: current_level is accessed by context_managers.py, decorators.py, etc.
                # Workers should report LEVEL_0_MONITOR to indicate no enhancement active
                current_level = EnhancementLevel.LEVEL_0_MONITOR

                # CRITICAL: These attributes are accessed by context_managers.py
                enabled = False  # Workers are not enabled for optimization
                performance_monitor = None  # No performance monitoring in workers

                _initialized = False  # For compatibility with test assertions

                def initialize(self):
                    """No-op: Workers don't need initialization."""
                    pass

                def shutdown(self):
                    """No-op: Workers have no resources to shut down."""
                    pass

                def set_enhancement_level(self, level):
                    """No-op: Workers don't manage enhancement levels."""
                    pass

                def get_enhancement_level(self):
                    """Return LEVEL_0_MONITOR since workers have no enhancement."""
                    return EnhancementLevel.LEVEL_0_MONITOR

                def optimize_function(self, func, args, kwargs, **options):
                    """No-op: Just call the original function without optimization."""
                    return func(*args, **kwargs)

                def enable_monitoring(self, enable=True):
                    """No-op: Workers don't support monitoring."""
                    pass

            _epochly_core = WorkerNoOpCore()
        return _epochly_core

    # CRITICAL FIX (Dec 2025): Check if we have a WorkerNoOpCore that needs replacement
    # This can happen if get_epochly_core() was called during Level 3 init when env vars
    # were temporarily set. Now that env vars are cleared, replace with real core.
    is_worker_no_op = (_epochly_core is not None and
                       not isinstance(_epochly_core, EpochlyCore) and
                       type(_epochly_core).__name__ == 'WorkerNoOpCore')

    if _epochly_core is None or is_worker_no_op:
        with _core_lock:
            # Double-check locking pattern (re-check both conditions under lock)
            is_worker_no_op = (_epochly_core is not None and
                               not isinstance(_epochly_core, EpochlyCore) and
                               type(_epochly_core).__name__ == 'WorkerNoOpCore')
            if _epochly_core is None or is_worker_no_op:
                _epochly_core = EpochlyCore()
                # CRITICAL FIX: Call initialize() after creating the core
                # This ensures _initialized=True when the core is returned
                _epochly_core.initialize()
    return _epochly_core

def _reset_singleton():
    """
    Reset the Epochly singleton for testing.

    CRITICAL: Prevents thread accumulation across pytest tests.
    - Shuts down existing instance (stops background threads)
    - Clears both module and class-level singletons
    - Next get_epochly_core() creates fresh instance

    Use in pytest teardown to prevent resource exhaustion.
    """
    global _epochly_core

    with _core_lock:
        if _epochly_core is not None:
            # Disable auto-profiler FIRST (remove sys.settrace)
            if hasattr(_epochly_core, '_auto_profiler') and _epochly_core._auto_profiler:
                try:
                    _epochly_core._auto_profiler.disable()
                except Exception:
                    pass  # Best effort

            # Shut down background threads
            try:
                _epochly_core.shutdown()
            except:
                pass  # Shutdown may not exist or may fail, continue cleanup

            # Clear singletons
            _epochly_core = None
            EpochlyCore._instance = None

            # CRITICAL: Also reset the __init__.py singleton
            # This ensures _ensure_core_initialized() creates a fresh core
            try:
                import epochly
                epochly._core_singleton = None
                epochly._auto_enabled = False
            except (ImportError, AttributeError):
                pass

            # CRITICAL: Reset global performance monitor singleton
            # Prevents "threads can only be started once" error on next init
            try:
                from ..monitoring.performance_monitor import _reset_performance_monitor
                _reset_performance_monitor()
            except (ImportError, Exception):
                pass

            # Force garbage collection of background threads
            import gc
            gc.collect()
