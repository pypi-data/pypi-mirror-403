"""
Epochly Import Hook - Module Interception for Transparent Optimization

Implements sys.meta_path import hook to intercept module imports and
apply optimizations transparently via post-import wrapping.

Architecture:
1. Detect target libraries (NumPy, Pandas, sklearn) at import time
2. Allow normal import to complete
3. Apply function wrappers to registered operations
4. Wrappers route to InterceptionManager for Level 3 execution

Lifecycle Management (P0-1 Remediation):
- Thread only starts after bootstrap signals completion via on_bootstrap_complete()
- Thread stops reliably via shutdown() method
- Adaptive backoff replaces fixed 50ms polling (min 50ms, max 2s)
- Bounded run window during startup phase (60 seconds)
- atexit handler registered for cleanup on interpreter exit

Author: Epochly Development Team
Date: November 16, 2025
Updated: November 25, 2025 (P0-1 lifecycle management)
"""

import sys
import importlib.abc
import importlib.machinery
import importlib.util
import functools
import threading
import atexit
import time
import os
from typing import Optional, Any

from ..utils.logger import get_logger

logger = get_logger(__name__)

# CRITICAL: Worker protection function against fork bomb
# MUST be function (not constant) to check at RUNTIME
# Cache the multiprocessing module to avoid repeated imports
_mp_module = None


def _is_worker_process():
    """
    Check if running in worker process (runtime check).

    Detects ProcessPool/ThreadPool workers to prevent fork bomb.
    Workers must NOT create their own executors.

    Detection methods:
    1. Check environment variables first (fastest, no imports)
    2. Check multiprocessing.current_process().name (worker names != 'MainProcess')

    CRITICAL: This function must NOT do imports that could block.
    If multiprocessing isn't already loaded, we skip that check.
    """
    global _mp_module

    # Method 1 (FAST): Explicit environment variable disable - check FIRST
    if (os.environ.get('EPOCHLY_DISABLE_INTERCEPTION') == '1' or
            os.environ.get('EPOCHLY_DISABLE') == '1'):
        return True

    # Method 2: Check if we're a multiprocessing worker
    # CRITICAL FIX: Only use multiprocessing if it's already loaded
    # DO NOT import it here - that could cause deadlock with the import lock
    try:
        if _mp_module is None:
            # Try to get multiprocessing from sys.modules WITHOUT importing
            _mp_module = sys.modules.get('multiprocessing')

        if _mp_module is not None:
            process_name = _mp_module.current_process().name

            # Workers have names like 'ForkPoolWorker-1', 'SpawnProcess-1', etc.
            # Main process has name 'MainProcess'
            if process_name != 'MainProcess':
                return True
    except Exception:
        # Silently handle errors - assume main process on failure
        pass

    return False

# Global recursion guard for wrapping
_wrapping_lock = threading.Lock()
_currently_wrapping = set()

# CRITICAL FIX: Flag to prevent background thread from running during epochly imports
# This is a thread-safe counter of how many epochly modules are currently being imported
_epochly_import_count = 0
_epochly_import_lock = threading.Lock()

# Note: Import deadlock prevention is handled in check_and_wrap_new_modules
# by checking if registry/manager modules are loaded before trying to wrap.


class WrappingLoader(importlib.abc.Loader):
    """
    PEP 451 compliant loader that wraps modules after execution.

    This loader delegates to the original loader for module execution,
    then applies Epochly wrapping to enable transparent acceleration.

    Architecture:
    1. create_module() - Let Python create module (default behavior)
    2. exec_module() - Execute module code via original loader
    3. exec_module() - Then wrap target functions for interception
    4. Result: Module works normally + Epochly acceleration

    Thread Safety: Wrapping happens under import lock (thread-safe)
    Error Handling: Wrapping errors are logged but don't break import
    """

    def __init__(self, original_loader, hook, fullname):
        """
        Initialize wrapping loader.

        Args:
            original_loader: Original module loader (executes module code)
            hook: EpochlyImportHook instance (provides wrapping logic)
            fullname: Fully qualified module name
        """
        self.original_loader = original_loader
        self.hook = hook
        self.fullname = fullname

    def create_module(self, spec):
        """
        Create the module object (PEP 451 requirement).

        Returns None to use default module creation.
        """
        # Let Python create the module using default mechanism
        return None

    def exec_module(self, module):
        """
        Execute module and wrap it.

        PEP 451 protocol: This is called after create_module() to populate
        the module. We execute normally, then wrap.

        CRITICAL: Temporarily removes hook from sys.meta_path during execution
        to prevent intercepting submodule imports (which causes circular import).

        Args:
            module: Module object to execute and wrap
        """
        # WINDOWS FIX: Ensure __file__ is set before exec_module
        # NumPy's delvewheel patches on Windows require __file__ to be defined
        # during module initialization. Python's import machinery should set this
        # from spec.origin, but our wrapped spec may not trigger it correctly.
        if hasattr(module, '__spec__') and module.__spec__ is not None:
            spec = module.__spec__
            if spec.origin is not None and not hasattr(module, '__file__'):
                module.__file__ = spec.origin
            # Also ensure __cached__ is set if needed
            if spec.cached is not None and not hasattr(module, '__cached__'):
                module.__cached__ = spec.cached

        # Step 1: Execute module normally via original loader
        # CRITICAL: Remove our hook from sys.meta_path during execution
        # This prevents us from intercepting submodule imports (numpy.core, etc)
        # which would cause circular import errors
        hook_was_in_path = self.hook in sys.meta_path

        try:
            if hook_was_in_path:
                sys.meta_path.remove(self.hook)

            # Now execute module - submodules will import normally
            self.original_loader.exec_module(module)

        finally:
            # Restore hook to sys.meta_path
            if hook_was_in_path and self.hook not in sys.meta_path:
                sys.meta_path.insert(0, self.hook)

        # Step 2: Wrap the module NOW (after execution complete)
        # Module is fully loaded, submodules are imported, safe to wrap
        try:
            self.hook._wrap_module(module, self.fullname)
            self.hook.logger.debug(f"Wrapped {self.fullname} after exec_module")
        except Exception as e:
            # Log wrapping errors but don't break import
            self.hook.logger.warning(f"Failed to wrap {self.fullname}: {e}")
            # Don't raise - import succeeds even if wrapping fails


class EpochlyImportHook(importlib.abc.MetaPathFinder):
    """
    Import hook for transparent Epochly activation.

    Intercepts module imports to apply optimizations without code changes.
    Installed in sys.meta_path by auto_enable().

    Lifecycle Management (P0-1):
    - Thread only starts after bootstrap signals completion via on_bootstrap_complete()
    - Thread stops reliably via shutdown() method
    - Adaptive backoff: min 50ms, max 2s, increases when idle
    - Bounded run window: 60 seconds of aggressive polling at startup
    - atexit handler registered for cleanup on interpreter exit

    Thread-safety: All state mutations protected by _module_lock
    """

    def __init__(self):
        """Initialize the import hook with lifecycle management."""
        self.logger = logger
        self._intercepted_modules = set()
        self._wrapped_modules = set()  # Track modules we've wrapped
        self._target_modules = {'numpy', 'pandas', 'sklearn'}  # Libraries to wrap
        self._importing = set()  # Track modules currently being imported
        self._module_lock = threading.Lock()  # Thread safety for concurrent imports
        self._shutdown = False  # Flag to stop wrapping thread
        self._shutdown_event = threading.Event()  # Event for thread coordination

        # P0-1: Lifecycle management - thread gating on bootstrap
        self._thread_started = False  # Flag to track if thread has started
        self._wrapping_thread = None  # Thread reference (starts lazily)

        # P0-1: Adaptive backoff configuration
        self._min_poll_interval = 0.05  # 50ms minimum (fast during activity)
        self._max_poll_interval = 2.0   # 2 seconds maximum (low overhead when idle)
        self._current_poll_interval = self._min_poll_interval
        self._backoff_factor = 1.5      # Exponential backoff multiplier
        self._backoff_lock = threading.Lock()

        # P0-1: Bounded run window during startup
        self._startup_window_seconds = 60.0  # 60 seconds of aggressive polling
        self._startup_start_time = None  # Set when thread starts

        # Install post-import callback for automatic wrapping
        self._install_post_import_hook()

        # P0-1: Register atexit handler for clean shutdown
        atexit.register(self.shutdown)
        self.logger.debug("Registered atexit handler for import hook cleanup")

        # NOTE: Thread does NOT start here - waits for on_bootstrap_complete()
        self.logger.debug("Import hook initialized (thread pending bootstrap)")

    def on_bootstrap_complete(self):
        """
        Signal that bootstrap has completed successfully.

        P0-1: This method gates thread startup on bootstrap completion.
        The background wrapping thread only starts after this is called.

        Thread-safe: Multiple calls are idempotent.
        Thread reference set before lock release to prevent race with shutdown().
        """
        # Define thread function outside lock (but before starting)
        def _periodic_wrapping_check():
            """Background thread that wraps newly imported target modules."""
            self.logger.debug(f"Wrapping thread {threading.current_thread().name} started")
            while not self._shutdown:
                # Double-check shutdown flag before expensive work
                if self._shutdown:
                    break

                wrapped_count = 0
                try:
                    # Get count of wrapped modules before
                    with self._module_lock:
                        before_count = len(self._wrapped_modules)

                    self.check_and_wrap_new_modules()

                    # Get count after to determine if wrapping occurred
                    with self._module_lock:
                        after_count = len(self._wrapped_modules)
                    wrapped_count = after_count - before_count

                except Exception as e:
                    # Silently fail to avoid breaking imports
                    self.logger.debug(f"Periodic wrapping check failed: {e}")

                # P0-1: Adjust poll interval based on activity
                self._adjust_poll_interval(wrapped_count)

                # P0-1: Sleep using event for responsive shutdown
                current_interval = self._get_poll_interval()
                self._shutdown_event.wait(current_interval)

        # CRITICAL: Create thread reference BEFORE releasing lock to prevent
        # race condition with shutdown() being called before thread is set
        with self._module_lock:
            if self._thread_started:
                self.logger.debug("Bootstrap already signaled, thread already running")
                return

            self._thread_started = True
            self._startup_start_time = time.time()

            # Set thread reference while holding lock
            self._wrapping_thread = threading.Thread(
                target=_periodic_wrapping_check,
                daemon=True,
                name='EpochlyModuleWrapper'
            )

        # Start thread AFTER releasing lock (safe - thread not running yet)
        self._wrapping_thread.start()
        self.logger.debug(f"Started periodic module wrapping thread (adaptive backoff, startup window {self._startup_window_seconds}s)")

    def shutdown(self):
        """
        Explicitly stop the background wrapping thread.

        P0-1: This method provides reliable thread termination.
        Called automatically via atexit or can be called explicitly.

        Thread-safe: Multiple calls are idempotent (no-op after first call).
        Uses lock to prevent race condition in concurrent shutdown calls.
        """
        # CRITICAL: Use lock for atomic check-and-set to prevent race condition
        with self._module_lock:
            if self._shutdown:
                return  # Already shutdown (idempotent)
            self._shutdown = True

        # Wake up thread immediately (outside lock - Event is thread-safe)
        self._shutdown_event.set()

        # Wait for thread to stop with timeout
        if self._wrapping_thread is not None and self._wrapping_thread.is_alive():
            self._wrapping_thread.join(timeout=1.0)
            if self._wrapping_thread.is_alive():
                self.logger.warning("Wrapping thread did not stop within timeout")
            else:
                self.logger.debug("Wrapping thread stopped cleanly")
        else:
            self.logger.debug("Wrapping thread was not running")

    def _adjust_poll_interval(self, wrapped_count: int):
        """
        Adjust polling interval based on wrapping activity.

        P0-1: Implements adaptive backoff to reduce overhead when idle.

        Args:
            wrapped_count: Number of modules wrapped in this cycle
        """
        with self._backoff_lock:
            if wrapped_count > 0:
                # Activity detected - reset to minimum interval
                self._current_poll_interval = self._min_poll_interval
            else:
                # No activity - back off exponentially (up to max)
                self._current_poll_interval = min(
                    self._current_poll_interval * self._backoff_factor,
                    self._max_poll_interval
                )

    def _get_poll_interval(self) -> float:
        """
        Get current polling interval, considering startup phase.

        P0-1: During startup window, uses more aggressive polling.
        After startup, allows backoff to reduce overhead.

        Returns:
            Current polling interval in seconds
        """
        with self._backoff_lock:
            # During startup phase, cap at minimum for responsiveness
            if self._past_startup_window():
                return self._current_poll_interval
            else:
                # Startup phase - use minimum interval for responsiveness
                return min(self._current_poll_interval, self._min_poll_interval * 2)

    def _past_startup_window(self) -> bool:
        """
        Check if past the bounded startup window.

        P0-1: After startup window, polling becomes less aggressive.

        Returns:
            True if past startup window or thread not started, False if in startup phase
        """
        if self._startup_start_time is None:
            return True  # No startup window if thread never started
        elapsed = time.time() - self._startup_start_time
        return elapsed > self._startup_window_seconds

    def is_startup_phase(self) -> bool:
        """
        Check if currently in startup phase.

        Returns:
            True if in startup phase (first 60 seconds after thread start)
        """
        return not self._past_startup_window()

    def find_module(self, fullname, path=None):
        """
        Legacy import hook method (Python < 3.4 compatibility).

        Returns:
            Module loader or None
        """
        # Delegate to find_spec for modern Python
        return None

    def find_spec(self, fullname, path=None, target=None):
        """
        Modern import hook method (Python 3.4+ PEP 451).

        For target modules (numpy, pandas, sklearn), returns ModuleSpec with
        WrappingLoader that applies transparent acceleration after import.

        For non-target modules, returns None to use default import machinery.

        Args:
            fullname: Fully qualified module name (e.g., 'numpy.core.multiarray')
            path: Package search path
            target: Module object being reloaded (for importlib.reload)

        Returns:
            ModuleSpec with WrappingLoader for targets, None otherwise
        """
        # CRITICAL: Worker protection - no-op in worker processes to prevent fork bomb
        if _is_worker_process():
            return None

        # Check if this is a target module we want to wrap
        base_module = fullname.split('.')[0]

        # Only intercept base target modules (numpy, pandas, sklearn)
        # Don't intercept submodules - they're handled by the module's own import
        if fullname not in self._target_modules:
            return None

        # CRITICAL: Recursion guard - check if we're already finding spec for this module
        with self._module_lock:
            if fullname in self._importing:
                # Already processing this module - avoid recursion
                return None
            self._importing.add(fullname)

        try:
            # Get the original spec by temporarily removing ourselves from sys.meta_path
            # This prevents infinite recursion
            try:
                sys.meta_path.remove(self)
            except ValueError:
                pass  # Not in meta_path (shouldn't happen, but safe)

            try:
                # Find original spec using standard import machinery
                original_spec = importlib.util.find_spec(fullname)
            finally:
                # Always restore ourselves to sys.meta_path
                if self not in sys.meta_path:
                    sys.meta_path.insert(0, self)

            if original_spec is None or original_spec.loader is None:
                # Module not found or no loader - let default machinery handle it
                return None

            # Track this module
            if fullname not in self._intercepted_modules:
                self._intercepted_modules.add(fullname)
                self.logger.debug(f"Intercepting target module: {fullname}")

            # Create new ModuleSpec with our WrappingLoader
            wrapped_spec = importlib.machinery.ModuleSpec(
                name=original_spec.name,
                loader=WrappingLoader(original_spec.loader, self, fullname),
                origin=original_spec.origin,
                is_package=original_spec.submodule_search_locations is not None,
            )

            # Copy submodule search locations if this is a package
            if original_spec.submodule_search_locations is not None:
                wrapped_spec.submodule_search_locations = list(original_spec.submodule_search_locations)

            return wrapped_spec

        finally:
            # Release importing lock
            with self._module_lock:
                self._importing.discard(fullname)

    def _install_post_import_hook(self):
        """
        Install callback that wraps modules after they're imported.

        Uses sys.modules monitoring to detect when target modules become available.
        """
        # Store reference to original sys.modules for comparison
        self._known_modules = set(sys.modules.keys())

    def _schedule_post_import_wrap(self, fullname: str):
        """
        Schedule post-import wrapping for a module.

        Uses sys.modules hook to wrap after import completes.

        Args:
            fullname: Module name to wrap after import
        """
        # Mark as importing
        self._importing.add(fullname)

        # Don't wrap immediately - let import complete first
        # Wrapping will be triggered by check_and_wrap_new_modules()
        # after import is done

    def check_and_wrap_new_modules(self):
        """
        Check for newly imported target modules and wrap them.

        Called periodically or on-demand to wrap modules that were
        imported after hook installation.

        Also wraps already-imported modules if they haven't been wrapped yet.

        Thread-safe: Uses lock to protect shared state during concurrent imports.
        """
        # CRITICAL: Worker protection - no-op in worker processes to prevent fork bomb
        if _is_worker_process():
            return

        # CRITICAL: Don't try to wrap if registry module isn't loaded yet
        # This prevents deadlock - the import of registry requires the import lock,
        # and we can't acquire it if the main thread is currently importing
        if 'epochly.interception.registry' not in sys.modules:
            return

        # Also check if manager is loaded (both are needed for wrapping)
        if 'epochly.interception.manager' not in sys.modules:
            return

        # CRITICAL FIX: Don't run during epochly initialization
        # Wait until epochly.core.epochly_core is loaded - this is one of the last
        # modules loaded during initialization. If it's not present, initialization
        # is still in progress and we could cause deadlocks.
        if 'epochly.core.epochly_core' not in sys.modules:
            return

        # Thread-safe snapshot of current modules
        current_modules = set(sys.modules.keys())

        # Check for new modules AND already-imported target modules
        for module_name in current_modules:
            base_module = module_name.split('.')[0]

            # Thread-safe check for already-wrapped
            with self._module_lock:
                already_wrapped = module_name in self._wrapped_modules

            if base_module in self._target_modules and not already_wrapped:
                # Only wrap base modules (numpy, pandas, sklearn)
                # Don't wrap submodules (numpy.random, numpy.linalg, etc.)
                # This prevents recursion during NumPy's lazy submodule loading
                if module_name == base_module and module_name in sys.modules:
                    # Thread-safe update of importing state
                    with self._module_lock:
                        self._importing.discard(module_name)

                    # Now safe to wrap
                    self._wrap_module(sys.modules[module_name], module_name)

        self._known_modules = current_modules

    def _wrap_module(self, module, fullname: str):
        """
        Wrap functions in imported module.

        Replaces registered functions with wrappers that route to InterceptionManager.

        Args:
            module: Imported module object
            fullname: Full module name
        """
        global _currently_wrapping

        self.logger.info(f"🔍 _wrap_module called for: {fullname}")

        if fullname in self._wrapped_modules:
            self.logger.debug(f"Skipping {fullname} (already wrapped)")
            return  # Already wrapped (idempotent)

        # Don't wrap if currently importing (avoid recursion)
        if fullname in self._importing:
            self.logger.debug(f"Skipping {fullname} (currently importing)")
            return

        # CRITICAL: Recursion guard for wrapping process
        # Prevents circular imports during wrapping
        with _wrapping_lock:
            if fullname in _currently_wrapping:
                self.logger.debug(f"Skipping {fullname} (wrapping in progress - recursion guard)")
                return

            _currently_wrapping.add(fullname)

        try:
            # CRITICAL FIX: Use sys.modules dict lookup instead of import statements
            # This avoids the import lock and prevents deadlocks when the background
            # thread runs while the main thread is importing epochly modules.
            # The import lock is NOT needed for sys.modules dict access.
            registry_module = sys.modules.get('epochly.interception.registry')
            manager_module = sys.modules.get('epochly.interception.manager')

            if registry_module is None or manager_module is None:
                # Registry/manager not loaded yet - skip wrapping for now
                # The periodic thread will try again later
                self.logger.debug(f"Skipping {fullname} (registry/manager modules not in sys.modules)")
                return

            # Get the actual functions from the cached modules
            get_registry = getattr(registry_module, 'get_registry', None)
            get_interception_manager = getattr(manager_module, 'get_interception_manager', None)

            if get_registry is None or get_interception_manager is None:
                self.logger.debug(f"Skipping {fullname} (registry/manager functions not found)")
                return

            registry = get_registry()
            manager = get_interception_manager()

            self.logger.debug(f"   Registry and manager loaded")

            # Get functions to wrap for this module
            # Only wrap base modules to avoid recursion
            if fullname == 'numpy':  # Only base numpy, not numpy.linalg, etc.
                descriptors = registry.get_all_numpy_functions()
                self.logger.debug(f"   Found {len(descriptors)} NumPy functions to wrap")
            elif fullname == 'pandas':  # Only base pandas
                descriptors = registry.get_all_pandas_functions()
                self.logger.debug(f"   Found {len(descriptors)} Pandas functions to wrap")
            elif fullname.startswith('sklearn'):  # sklearn has many submodules
                descriptors = registry.get_all_sklearn_functions()
                self.logger.debug(f"   Found {len(descriptors)} sklearn functions to wrap")
            else:
                descriptors = []
                self.logger.debug(f"   No descriptors for {fullname}")

            if not descriptors:
                self.logger.debug(f"   Nothing to wrap for {fullname}")
                return  # Nothing to wrap for this module

            # Wrap each registered function
            wrapped_count = 0
            for desc in descriptors:
                if self._wrap_function(module, desc, manager):
                    wrapped_count += 1

            if wrapped_count > 0:
                self.logger.debug(f"Wrapped {wrapped_count} functions in {fullname}")
                # Thread-safe update
                with self._module_lock:
                    self._wrapped_modules.add(fullname)

        except Exception as e:
            self.logger.error(f"Failed to wrap module {fullname}: {e}")
        finally:
            # Release recursion guard
            with _wrapping_lock:
                _currently_wrapping.discard(fullname)

    def _wrap_function(self, module, descriptor, manager) -> bool:
        """
        Wrap a single function in the module.

        Args:
            module: Module object
            descriptor: FunctionDescriptor from registry
            manager: InterceptionManager instance

        Returns:
            True if wrapping succeeded
        """
        try:
            # Navigate to function (handle nested attributes like numpy.linalg.eig)
            parts = descriptor.function.split('.')
            obj = module

            for part in parts[:-1]:
                if not hasattr(obj, part):
                    return False
                obj = getattr(obj, part)

            func_name = parts[-1]
            if not hasattr(obj, func_name):
                return False

            original_func = getattr(obj, func_name)

            # Check if already wrapped (idempotent behavior)
            if getattr(original_func, '_epochly_wrapped', False):
                # Re-register with manager (in case manager was reset between tests)
                op_id = f"{descriptor.module}.{descriptor.function}"
                stored_original = getattr(original_func, '_original_function', None)
                if stored_original:
                    manager.register_original_function(op_id, stored_original)
                    self.logger.debug(f"Re-registered already-wrapped {op_id} with manager")
                return False  # Already wrapped (idempotent)

            # Create wrapper
            op_id = f"{descriptor.module}.{descriptor.function}"

            @functools.wraps(original_func)
            def epochly_wrapper(*args, **kwargs):
                """Wrapper that routes to InterceptionManager."""
                # DEBUG: Log wrapper invocation
                import os
                if os.environ.get('EPOCHLY_DEBUG_INTERCEPTION') == '1':
                    logger.info(f"🎯 WRAPPER CALLED for {op_id} with {len(args)} args")

                # CRITICAL: Dynamic manager lookup instead of closure
                # This ensures test isolation - wrapper uses current global manager
                from ..interception.manager import get_interception_manager
                current_manager = get_interception_manager()
                # CRITICAL: Pass op_id and original_func as positional arguments
                # to avoid conflicts with *args unpacking
                return current_manager.execute_vector_op(
                    op_id,           # Positional (not op_id=...)
                    original_func,   # Positional (not original_func=...)
                    *args,
                    **kwargs
                )

            # Mark as wrapped
            epochly_wrapper._epochly_wrapped = True
            epochly_wrapper._original_function = original_func

            # Replace in module
            setattr(obj, func_name, epochly_wrapper)

            # Register original with manager
            manager.register_original_function(op_id, original_func)

            self.logger.debug(f"Wrapped {op_id}")
            return True

        except Exception as e:
            self.logger.debug(f"Failed to wrap {descriptor.module}.{descriptor.function}: {e}")
            return False

    def invalidate_caches(self):
        """Invalidate any caches used by the finder."""
        pass


def get_import_hook() -> Optional[EpochlyImportHook]:
    """
    Get the installed Epochly import hook from sys.meta_path.

    Returns:
        EpochlyImportHook instance or None if not installed
    """
    for hook in sys.meta_path:
        if isinstance(hook, EpochlyImportHook):
            return hook
    return None
