"""
Reliable Source Code Extraction for Interactive Environments

This module provides deterministic source code extraction that works reliably
in Jupyter notebooks, IPython, and standard Python files. It uses a layered
fallback approach to maximize extraction success.

The Problem:
- inspect.getsource() fails randomly in Jupyter with 'OSError: could not get source code'
- This causes JIT compilation to work inconsistently (some iterations fast, others slow)
- Functions defined in notebook cells don't have traditional file-based source

The Solution:
- Layered extraction: inspect -> linecache -> IPython history -> dill
- Success/failure caching to ensure deterministic behavior
- Once a function's source is found (or permanently fails), result is cached

Architecture Reference:
- Designed based on Numba/JAX approaches to interactive source extraction
- Uses IPython's internal caches (linecache, _ih history)

Author: Epochly Development Team
Date: December 2025
"""

import ast
import inspect
import linecache
import textwrap
import threading
from typing import Callable, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Optional dill import for last-resort extraction
try:
    import dill
    import dill.source
    DILL_AVAILABLE = True
except ImportError:
    dill = None
    DILL_AVAILABLE = False


class SourceExtractor:
    """
    Deterministic source code extractor with multi-strategy fallback.

    Extraction order (from cheapest to most expensive):
    1. inspect.getsource() - Works for file-based functions
    2. linecache - IPython populates this for notebook cells
    3. IPython history (_ih) - Direct cell history search
    4. dill.source.getsource() - Last resort for interactive functions

    Thread Safety:
    - Uses class-level caches with a lightweight lock
    - Benign race on first access is acceptable (may duplicate work once)
    - All public methods are thread-safe

    Memory Management:
    - Bounded caches prevent unbounded growth
    - Caches are cleared when they reach max size (FIFO eviction)
    - Use clear_caches() for manual cache management

    Module Reload:
    - Class state is shared at module level (singleton pattern)
    - After module reload, call reset_all() to reinitialize state
    - This ensures hooks and caches are properly reset
    """

    # Class-level caches shared across all instances
    _success_cache: dict = {}      # code_id -> source string
    _failure_cache: set = set()    # code_id -> permanent extraction failure
    _max_cache_size: int = 10_000  # Max entries before clearing
    _cache_lock = threading.Lock()

    # Track function name to code_id mapping for selective cache invalidation
    _func_name_to_code_ids: dict = {}  # func_name -> set of code_ids

    # Configurable limits
    _max_history_search: int = 200  # Max IPython history cells to search

    # Statistics for debugging (all increments protected by _cache_lock)
    _stats = {
        'inspect_success': 0,
        'linecache_success': 0,
        'ipython_compile_cache_success': 0,
        'ipython_history_success': 0,
        'dill_success': 0,
        'cache_hit': 0,
        'permanent_failure': 0
    }

    @classmethod
    def _increment_stat(cls, stat_name: str) -> None:
        """Thread-safe stat increment (must be called with _cache_lock held or independently)."""
        with cls._cache_lock:
            if stat_name in cls._stats:
                cls._stats[stat_name] += 1
            else:
                logger.warning(f"Unknown stat name: {stat_name}")

    @classmethod
    def _increment_stat_unlocked(cls, stat_name: str) -> None:
        """Stat increment when lock is already held."""
        if stat_name in cls._stats:
            cls._stats[stat_name] += 1
        else:
            logger.warning(f"Unknown stat name: {stat_name}")

    @classmethod
    def _bounded_add_failure(cls, code_id: int) -> None:
        """Add code_id to failure cache with bounds checking."""
        with cls._cache_lock:
            if len(cls._failure_cache) >= cls._max_cache_size:
                cls._failure_cache.clear()
                logger.debug("Cleared failure cache (reached max size)")
            cls._failure_cache.add(code_id)
            cls._stats['permanent_failure'] += 1

    @classmethod
    def _bounded_add_success(cls, code_id: int, source: str, func_name: str = None) -> None:
        """Add code_id -> source to success cache with bounds checking."""
        with cls._cache_lock:
            if len(cls._success_cache) >= cls._max_cache_size:
                cls._success_cache.clear()
                cls._func_name_to_code_ids.clear()  # Also clear mapping
                logger.debug("Cleared success cache (reached max size)")
            cls._success_cache[code_id] = source
            # Track func_name -> code_id for selective invalidation
            if func_name:
                if func_name not in cls._func_name_to_code_ids:
                    cls._func_name_to_code_ids[func_name] = set()
                cls._func_name_to_code_ids[func_name].add(code_id)

    @classmethod
    def get_source(cls, func: Callable) -> Optional[str]:
        """
        Get source code for a function using layered extraction strategies.

        Args:
            func: The function to extract source from

        Returns:
            Dedented source code string, or None if extraction failed

        Note:
            Results are cached - same function always returns same result.
            This ensures DETERMINISTIC behavior (no random failures).
        """
        if not callable(func):
            return None

        if not hasattr(func, '__code__'):
            logger.debug(f"Function {getattr(func, '__name__', '<unknown>')} has no __code__")
            return None

        code_id = id(func.__code__)
        func_name = getattr(func, '__name__', '<unknown>')

        # Fast path: Check caches first (all stats incremented while lock held)
        with cls._cache_lock:
            if code_id in cls._success_cache:
                cls._increment_stat_unlocked('cache_hit')
                return cls._success_cache[code_id]
            if code_id in cls._failure_cache:
                cls._increment_stat_unlocked('cache_hit')
                return None

        # Strategy 1: Standard inspect.getsource() (works for file-based functions)
        source = cls._try_inspect_getsource(func, func_name)
        if source:
            cls._bounded_add_success(code_id, source, func_name)
            cls._increment_stat('inspect_success')
            logger.debug(f"Source extracted via inspect for {func_name}")
            return source

        # Strategy 2: IPython linecache (most reliable for notebooks)
        source = cls._try_linecache(func, func_name)
        if source:
            cls._bounded_add_success(code_id, source, func_name)
            cls._increment_stat('linecache_success')
            logger.debug(f"Source extracted via linecache for {func_name}")
            return source

        # Strategy 2.5: IPython compile cache (for modern Jupyter)
        source = cls._try_ipython_compile_cache(func, func_name)
        if source:
            cls._bounded_add_success(code_id, source, func_name)
            cls._increment_stat('ipython_compile_cache_success')
            logger.debug(f"Source extracted via IPython compile cache for {func_name}")
            return source

        # Strategy 3: IPython history search (_ih)
        source = cls._try_ipython_history(func, func_name)
        if source:
            cls._bounded_add_success(code_id, source, func_name)
            cls._increment_stat('ipython_history_success')
            logger.debug(f"Source extracted via IPython history for {func_name}")
            return source

        # Strategy 4: dill (last resort)
        source = cls._try_dill(func, func_name)
        if source:
            cls._bounded_add_success(code_id, source, func_name)
            cls._increment_stat('dill_success')
            logger.debug(f"Source extracted via dill for {func_name}")
            return source

        # Strategy 5: Sync IPython caches to linecache and retry
        # CRITICAL FIX (Jan 2025): IPython may have source in internal caches
        # that wasn't registered with linecache. Sync them and retry.
        synced = cls.sync_ipython_to_linecache()
        if synced > 0:
            # Retry linecache after sync
            source = cls._try_linecache(func, func_name)
            if source:
                cls._bounded_add_success(code_id, source, func_name)
                cls._increment_stat('linecache_success')
                logger.debug(f"Source extracted via linecache (after IPython sync) for {func_name}")
                return source

            # Retry IPython history with fresh sync
            source = cls._try_ipython_history(func, func_name)
            if source:
                cls._bounded_add_success(code_id, source, func_name)
                cls._increment_stat('ipython_history_success')
                logger.debug(f"Source extracted via IPython history (after sync) for {func_name}")
                return source

        # Strategy 6: Try to find source by searching all cells for function definition
        source = cls._try_search_all_cells(func, func_name)
        if source:
            cls._bounded_add_success(code_id, source, func_name)
            cls._increment_stat('ipython_history_success')
            logger.debug(f"Source extracted via cell search for {func_name}")
            return source

        # All strategies failed - cache as permanent failure
        cls._bounded_add_failure(code_id)
        logger.debug(
            f"Source extraction permanently failed for {func_name} "
            f"(file: {getattr(func.__code__, 'co_filename', 'unknown')})"
        )
        return None

    @classmethod
    def _try_inspect_getsource(cls, func: Callable, func_name: str) -> Optional[str]:
        """Strategy 1: Standard inspect.getsource()."""
        try:
            source = inspect.getsource(func)
            source = textwrap.dedent(source)
            # Validate it's parseable
            ast.parse(source)
            return source
        except (OSError, TypeError, SyntaxError) as e:
            logger.debug(f"inspect.getsource failed for {func_name}: {type(e).__name__}")
            return None
        except Exception as e:
            logger.debug(f"inspect.getsource unexpected error for {func_name}: {e}")
            return None

    @classmethod
    def _is_interactive_filename(cls, filename: str) -> bool:
        """
        Check if a filename indicates an interactive/notebook environment.

        Supports all major platforms and Jupyter variants:
        - Windows: C:\\Users\\...\\ipykernel_1234\\...
        - Linux: /tmp/ipykernel_1234/...
        - macOS: /var/folders/.../ipykernel_1234/...
        - Google Colab: /content/... or <ipython-input-...> (legacy patterns)
        - VS Code Jupyter: vscode-notebook-cell:// URIs and temp paths
        - Databricks: /databricks/... paths
        - AWS SageMaker: /sagemaker/... paths
        - Jupyter Lab, Jupyter Notebook, IPython shell
        """
        # Normalize path separators for cross-platform matching
        filename_normalized = filename.replace('\\', '/')
        # Lowercase for case-insensitive pattern matching (cloud services may vary)
        filename_lower = filename_normalized.lower()

        # Legacy IPython/Jupyter patterns (angle brackets indicate virtual files)
        # Note: Google Colab uses <ipython-input-...> format, covered here
        # Use normalized filename for path consistency across platforms
        legacy_patterns = (
            '<ipython-input-',
            '<stdin>',
            '<input>',
            '<string>',
            'ipython-input-',  # Without angle brackets (some versions)
        )
        if any(p in filename_normalized for p in legacy_patterns):
            return True

        # Modern IPyKernel patterns (actual temp files)
        # Works on Windows, Linux, macOS
        ipykernel_patterns = (
            'ipykernel_',       # Most common: ipykernel_12345
            '/ipykernel/',      # Path component (Linux/macOS)
            'ipykernel/',       # Path component without leading slash
            'kernel-',          # Alternative naming
            '/tmp/ipython',     # IPython temp files
        )
        if any(p in filename_normalized for p in ipykernel_patterns):
            return True

        # VS Code Jupyter patterns
        vscode_patterns = (
            'vscode-notebook-cell:',  # VS Code notebook cell URI scheme
            'vscode-notebook-cell-output:',  # VS Code output cells
            '.vscode-server/',  # VS Code remote server
        )
        if any(p in filename_lower for p in vscode_patterns):
            return True

        # Google Colab patterns (in addition to legacy <ipython-input-...>)
        if filename_normalized.startswith('/content/'):
            return True

        # Databricks patterns (case-insensitive for cloud variability)
        if '/databricks/' in filename_lower:
            return True

        # AWS SageMaker patterns (case-insensitive)
        if '/sagemaker/' in filename_lower:
            return True

        # Azure ML patterns
        if '/azureml/' in filename_lower or 'azureml-' in filename_lower:
            return True

        return False

    @classmethod
    def _try_linecache(cls, func: Callable, func_name: str) -> Optional[str]:
        """Strategy 2: IPython linecache for notebook cells."""
        import os

        try:
            filename = func.__code__.co_filename
            if not filename:
                return None

            # Check if this is an interactive/notebook filename
            if not cls._is_interactive_filename(filename):
                return None

            lines = linecache.getlines(filename)
            if not lines:
                # Force linecache to refresh
                linecache.checkcache(filename)

                # For actual files on disk (ipykernel temp files), try updatecache
                if os.path.exists(filename):
                    linecache.updatecache(filename)

                lines = linecache.getlines(filename)

            if not lines:
                return None

            source = ''.join(lines)
            source = textwrap.dedent(source)

            # Extract just the function definition if the cell contains multiple things
            source = cls._extract_function_from_source(source, func_name)
            if source:
                # Validate it's parseable
                ast.parse(source)
                return source
            return None

        except Exception as e:
            logger.debug(f"linecache extraction failed for {func_name}: {e}")
            return None

    @classmethod
    def _try_ipython_compile_cache(cls, func: Callable, func_name: str) -> Optional[str]:
        """Strategy 2.5: Access IPython's compile cache directly."""
        try:
            from IPython import get_ipython
            ip = get_ipython()
            if ip is None:
                return None

            filename = func.__code__.co_filename

            # Try IPython's internal compile cache
            # The cache structure varies by IPython version:
            # - Some versions: cache[filename] = source_string
            # - Some versions: cache[(source, filename, symbol)] = code_object
            # - Some versions: cache[filename] = (code_object, source_string)
            if hasattr(ip, 'compile') and hasattr(ip.compile, 'cache'):
                cache = ip.compile.cache

                # Try direct filename lookup first
                if filename in cache:
                    cached = cache[filename]
                    source = None

                    # Handle different cache value formats
                    if isinstance(cached, str):
                        source = cached
                    elif isinstance(cached, tuple) and len(cached) >= 2:
                        # (code_object, source_string) format
                        if isinstance(cached[1], str):
                            source = cached[1]
                        elif isinstance(cached[0], str):
                            source = cached[0]

                    if source:
                        source = textwrap.dedent(source)
                        extracted = cls._extract_function_from_source(source, func_name)
                        if extracted:
                            ast.parse(extracted)
                            return extracted

                # Try searching cache keys for matching filename
                for key, value in cache.items():
                    # Handle (source, filename, symbol) tuple keys
                    if isinstance(key, tuple) and len(key) >= 2:
                        if key[1] == filename and isinstance(key[0], str):
                            source = textwrap.dedent(key[0])
                            extracted = cls._extract_function_from_source(source, func_name)
                            if extracted:
                                ast.parse(extracted)
                                return extracted

            return None

        except Exception as e:
            logger.debug(f"IPython compile cache access failed for {func_name}: {e}")
            return None

    @classmethod
    def _try_ipython_history(cls, func: Callable, func_name: str) -> Optional[str]:
        """Strategy 3: Search IPython input history (_ih)."""
        try:
            # Try to get IPython instance
            try:
                from IPython import get_ipython
                ip = get_ipython()
            except ImportError:
                return None

            if ip is None:
                return None

            # Get input history
            ih = getattr(ip, '_ih', None)
            if ih is None and hasattr(ip, 'history_manager'):
                ih = getattr(ip.history_manager, 'input_hist_raw', None)

            if not ih:
                return None

            # Search from newest to oldest (more likely to find recent definition)
            # Limit search to prevent excessive scanning
            search_count = 0

            for cell in reversed(ih):
                if search_count >= cls._max_history_search:
                    break
                search_count += 1

                if not cell or not isinstance(cell, str):
                    continue

                # Check if this cell defines our function
                if f'def {func_name}' in cell:
                    source = textwrap.dedent(cell)
                    # Extract just the function definition
                    source = cls._extract_function_from_source(source, func_name)
                    if source:
                        # Validate it's parseable
                        ast.parse(source)
                        return source

            return None

        except Exception as e:
            logger.debug(f"IPython history search failed for {func_name}: {e}")
            return None

    @classmethod
    def _try_dill(cls, func: Callable, func_name: str) -> Optional[str]:
        """Strategy 4: Use dill for interactive function source extraction."""
        if not DILL_AVAILABLE:
            return None

        try:
            source = dill.source.getsource(func)
            if source:
                source = textwrap.dedent(source)
                # Validate it's parseable
                ast.parse(source)
                return source
            return None
        except Exception as e:
            logger.debug(f"dill.source.getsource failed for {func_name}: {e}")
            return None

    @classmethod
    def _try_search_all_cells(cls, func: Callable, func_name: str) -> Optional[str]:
        """
        Strategy 6: Aggressive search through all IPython cells and linecache.

        This is a last-resort strategy that searches ALL available sources
        for the function definition, regardless of filename matching.
        """
        try:
            # Search through everything in linecache
            for filename, cache_entry in list(linecache.cache.items()):
                if not isinstance(cache_entry, tuple) or len(cache_entry) < 3:
                    continue

                lines = cache_entry[2]
                if not lines:
                    continue

                source = ''.join(lines)
                if f'def {func_name}' in source or f'async def {func_name}' in source:
                    extracted = cls._extract_function_from_source(source, func_name)
                    if extracted:
                        try:
                            ast.parse(extracted)
                            # Verify this is actually our function by checking code structure
                            if cls._verify_function_match(func, extracted):
                                logger.debug(f"Found {func_name} via aggressive linecache search in {filename}")
                                return extracted
                        except SyntaxError:
                            continue

            # Search through IPython history if available
            try:
                from IPython import get_ipython
                ip = get_ipython()
                if ip:
                    ih = getattr(ip, '_ih', None)
                    if ih:
                        # Search from newest to oldest
                        for cell in reversed(list(ih)):
                            if cell and isinstance(cell, str):
                                if f'def {func_name}' in cell or f'async def {func_name}' in cell:
                                    extracted = cls._extract_function_from_source(cell, func_name)
                                    if extracted:
                                        try:
                                            ast.parse(extracted)
                                            if cls._verify_function_match(func, extracted):
                                                logger.debug(f"Found {func_name} via aggressive IPython history search")
                                                return extracted
                                        except SyntaxError:
                                            continue
            except ImportError:
                pass

            return None

        except Exception as e:
            logger.debug(f"Aggressive cell search failed for {func_name}: {e}")
            return None

    @classmethod
    def _verify_function_match(cls, func: Callable, source: str) -> bool:
        """
        Verify that extracted source matches the function's code structure.

        This helps avoid false positives when searching aggressively.
        """
        try:
            tree = ast.parse(source)

            # Find the function definition
            func_def = None
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == func.__name__:
                        func_def = node
                        break

            if func_def is None:
                return False

            # Compare argument count
            code = func.__code__
            expected_args = code.co_argcount + code.co_kwonlyargcount
            actual_args = len(func_def.args.args) + len(func_def.args.kwonlyargs)

            # Allow some flexibility (defaults, *args, **kwargs can vary)
            if abs(expected_args - actual_args) > 2:
                return False

            # Compare local variable count (rough heuristic)
            expected_locals = len(code.co_varnames)
            # Count assignments in the function
            assignments = sum(1 for node in ast.walk(func_def) if isinstance(node, ast.Assign))

            # If the structure is vastly different, it's probably not the same function
            if expected_locals > 5 and assignments < expected_locals // 3:
                return False

            return True

        except Exception:
            # If verification fails, be optimistic and accept the match
            return True

    @classmethod
    def _extract_function_from_source(cls, source: str, func_name: str) -> Optional[str]:
        """
        Extract a specific function definition from a larger source string.

        Used when a notebook cell contains multiple statements but we only
        want the specific function.

        Args:
            source: Full source code (may contain multiple definitions)
            func_name: Name of the function to extract

        Returns:
            Just the function definition source, or None if not found
        """
        try:
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == func_name:
                        # Get the source lines for just this function
                        lines = source.splitlines(keepends=True)
                        start_line = node.lineno - 1
                        end_line = node.end_lineno if hasattr(node, 'end_lineno') else len(lines)

                        func_source = ''.join(lines[start_line:end_line])
                        return textwrap.dedent(func_source)

            return None

        except SyntaxError:
            # Source isn't valid Python, can't parse
            return None
        except Exception:
            return None

    @classmethod
    def get_stats(cls) -> dict:
        """Get extraction statistics for debugging."""
        with cls._cache_lock:
            return {
                **cls._stats,
                'success_cache_size': len(cls._success_cache),
                'failure_cache_size': len(cls._failure_cache),
                'dill_available': DILL_AVAILABLE
            }

    @classmethod
    def clear_caches(cls) -> None:
        """Clear all caches. Useful for testing or memory management."""
        with cls._cache_lock:
            cls._success_cache.clear()
            cls._failure_cache.clear()
            cls._func_name_to_code_ids.clear()
            cls._registered_sources.clear()
        logger.debug("Source extractor caches cleared")

    @classmethod
    def reset_stats(cls) -> None:
        """Reset extraction statistics."""
        with cls._cache_lock:
            for key in cls._stats:
                cls._stats[key] = 0
        logger.debug("Source extractor stats reset")

    @classmethod
    def reset_all(cls) -> None:
        """
        Reset all class state including caches, stats, and hook state.

        Use this method after module reload to ensure consistent state.
        This is the safe way to reinitialize the SourceExtractor after
        a module reload in interactive environments.

        Note: This will uninstall any active IPython hooks.
        """
        # First uninstall the hook if active
        cls.uninstall_ipython_hook()

        with cls._cache_lock:
            # Clear all caches
            cls._success_cache.clear()
            cls._failure_cache.clear()
            cls._func_name_to_code_ids.clear()
            cls._registered_sources.clear()

            # Reset stats
            for key in cls._stats:
                cls._stats[key] = 0

            # Reset hook state
            cls._hook_installed = False
            cls._hook_function = None

        logger.debug("Source extractor fully reset")

    @classmethod
    def register_source(cls, source: str, filename: str) -> None:
        """
        Register source code with linecache for later extraction.

        CRITICAL FIX (Jan 2025): This is the key to making source extraction
        work for Jupyter notebooks and exec'd code. When code is executed via
        exec() or compile(), the source is NOT automatically registered with
        linecache. This method manually registers it.

        Call this BEFORE executing code to ensure source extraction works:

            source = "def my_func(): ..."
            filename = "<notebook-cell-1>"
            SourceExtractor.register_source(source, filename)
            exec(compile(source, filename, 'exec'), globals())
            # Now SourceExtractor.get_source(my_func) will work!

        Args:
            source: The source code string
            filename: The filename to associate with the source (used as key)
        """
        lines = source.splitlines(keepends=True)
        if lines and not lines[-1].endswith('\n'):
            lines[-1] += '\n'

        # Register with linecache
        # Format: (size, mtime, lines, fullname)
        linecache.cache[filename] = (
            len(source),  # size
            None,         # mtime (None for virtual files)
            lines,        # the actual source lines
            filename      # fullname
        )
        logger.debug(f"Registered source with linecache: {filename} ({len(lines)} lines)")

    @classmethod
    def sync_ipython_to_linecache(cls) -> int:
        """
        Sync IPython's internal source caches to linecache.

        IPython stores cell source in various internal caches, but doesn't always
        populate linecache. This method finds source in IPython's caches and
        registers it with linecache so that inspect.getsource() and our extraction
        strategies can find it.

        Returns:
            Number of sources synced to linecache
        """
        synced = 0
        try:
            from IPython import get_ipython
            ip = get_ipython()
            if ip is None:
                return 0

            # Strategy 1: Sync from IPython's compile cache
            if hasattr(ip, 'compile') and hasattr(ip.compile, 'cache'):
                for key, value in ip.compile.cache.items():
                    filename = None
                    source = None

                    # Handle different cache key/value formats
                    if isinstance(key, str):
                        filename = key
                        if isinstance(value, str):
                            source = value
                        elif isinstance(value, tuple) and len(value) >= 2:
                            if isinstance(value[1], str):
                                source = value[1]
                    elif isinstance(key, tuple) and len(key) >= 2:
                        if isinstance(key[0], str) and isinstance(key[1], str):
                            source = key[0]
                            filename = key[1]

                    if filename and source and filename not in linecache.cache:
                        cls.register_source(source, filename)
                        synced += 1

            # Strategy 2: Sync from IPython's input history
            ih = getattr(ip, '_ih', None)
            if ih:
                for idx, cell in enumerate(ih):
                    if cell and isinstance(cell, str):
                        # Create a filename matching IPython's pattern
                        filename = f"<ipython-input-{idx}-sync>"
                        if filename not in linecache.cache:
                            cls.register_source(cell, filename)
                            synced += 1

            if synced > 0:
                logger.debug(f"Synced {synced} sources from IPython to linecache")

            return synced

        except Exception as e:
            logger.debug(f"Failed to sync IPython to linecache: {e}")
            return 0

    # Track registered sources to detect updates (protected by _cache_lock)
    _registered_sources: dict = {}  # filename -> (source_hash, func_names)
    _max_registered_sources: int = 1000  # Prevent unbounded growth
    _hook_installed: bool = False  # Protected by _cache_lock
    _hook_function = None  # Store hook function reference for uninstall

    @classmethod
    def install_ipython_hook(cls) -> bool:
        """
        Install an IPython hook to automatically register cell source with linecache.

        CRITICAL (Jan 2025): This hook ensures cell source stays synchronized:
        1. Registers source with linecache after each cell execution
        2. Detects cell modifications (re-execution with changed code)
        3. Clears extraction caches for redefined functions
        4. Uses IPython's actual filename for proper lookup

        Thread Safety:
        - Uses _cache_lock to protect _hook_installed and _registered_sources
        - Safe to call from multiple threads (will only install once)
        - Uses check-then-set pattern with immediate flag set to prevent races

        Returns:
            True if hook was installed, False otherwise
        """
        import hashlib
        import re

        # Thread-safe check-and-set: Set flag IMMEDIATELY to prevent races
        # If registration fails, we reset the flag
        with cls._cache_lock:
            if cls._hook_installed:
                return True  # Already installed
            cls._hook_installed = True  # Set immediately to prevent duplicate registration

        try:
            from IPython import get_ipython
            ip = get_ipython()
            if ip is None:
                with cls._cache_lock:
                    cls._hook_installed = False  # Reset on failure
                return False

            # Pre-compile regex for performance (used in hot path)
            func_pattern = re.compile(r'^\s*(?:async\s+)?def\s+(\w+)', re.MULTILINE)

            def post_run_cell_hook(result):
                """
                Post-execution hook: Register cell source and update caches.

                This runs AFTER cell execution to:
                1. Register source with linecache using IPython's filename
                2. Detect modified cells (hash changed)
                3. Clear stale cache entries for redefined functions
                """
                try:
                    # Get raw cell source (defensive: check attributes exist)
                    raw_cell = None
                    if hasattr(result, 'info') and result.info and hasattr(result.info, 'raw_cell'):
                        raw_cell = result.info.raw_cell
                    elif hasattr(result, 'info') and result.info and hasattr(result.info, 'cell_id'):
                        # Try to get from IPython history
                        if ip._ih:
                            raw_cell = ip._ih[-1] if ip._ih else None

                    if not raw_cell:
                        return

                    # Use IPython's execution count for filename
                    # Guard against None/invalid execution_count
                    exec_count = ip.execution_count
                    if exec_count is None or not isinstance(exec_count, int):
                        exec_count = len(ip._ih) if ip._ih else 0
                    filename = f"<ipython-input-{exec_count}>"

                    # Calculate hash to detect changes (full MD5 for robustness)
                    source_hash = hashlib.md5(raw_cell.encode()).hexdigest()

                    # Extract function names (can be done outside lock)
                    func_names = func_pattern.findall(raw_cell)

                    # Collect eviction targets outside lock to avoid holding lock during I/O
                    keys_to_evict = []

                    # Thread-safe access to _registered_sources
                    with cls._cache_lock:
                        # Check if this is an update to existing source
                        prev_entry = cls._registered_sources.get(filename)
                        if prev_entry:
                            prev_hash, prev_func_names = prev_entry
                            if prev_hash != source_hash:
                                # Source changed! Clear caches for previously defined functions
                                logger.debug(f"Cell {filename} modified, clearing caches for: {prev_func_names}")
                                cls._invalidate_functions_unlocked(prev_func_names)

                        # Track this registration with bounded size (FIFO eviction)
                        cls._registered_sources[filename] = (source_hash, func_names)

                        # Evict oldest entries (FIFO) if we exceed max size
                        if len(cls._registered_sources) > cls._max_registered_sources:
                            # Remove oldest 10% of entries by insertion order
                            to_remove = len(cls._registered_sources) - int(cls._max_registered_sources * 0.9)
                            keys_to_evict = list(cls._registered_sources.keys())[:to_remove]
                            for key in keys_to_evict:
                                del cls._registered_sources[key]
                            logger.debug(f"Evicted {to_remove} old entries from _registered_sources (FIFO)")

                    # Register with linecache OUTSIDE the lock (linecache is thread-safe)
                    cls.register_source(raw_cell, filename)

                    # Clean up evicted entries from linecache outside the lock
                    for key in keys_to_evict:
                        linecache.cache.pop(key, None)

                    if func_names:
                        logger.debug(f"Registered source for cell {filename}: {func_names}")

                except Exception as e:
                    logger.debug(f"Post-run cell hook error: {e}")

            # Store hook reference for uninstall
            cls._hook_function = post_run_cell_hook

            # Register the hook (only post_run needed)
            ip.events.register('post_run_cell', post_run_cell_hook)

            logger.info("Installed IPython hook for source extraction")
            return True

        except Exception as e:
            with cls._cache_lock:
                cls._hook_installed = False  # Reset on failure
            logger.debug(f"Failed to install IPython hook: {e}")
            return False

    @classmethod
    def uninstall_ipython_hook(cls) -> bool:
        """
        Uninstall the IPython hook for source extraction.

        Thread Safety:
        - Uses _cache_lock to protect _hook_installed flag
        - Safe to call from multiple threads
        - Marks as uninstalled BEFORE releasing lock to prevent races

        Returns:
            True if hook was uninstalled, False otherwise
        """
        # Atomically check state and mark as uninstalled
        with cls._cache_lock:
            if not cls._hook_installed:
                return True  # Already uninstalled
            hook_func = cls._hook_function
            if hook_func is None:
                cls._hook_installed = False
                return True
            # Mark as uninstalled BEFORE releasing lock to prevent races
            cls._hook_installed = False
            cls._hook_function = None

        # Perform actual unregistration outside the lock
        try:
            from IPython import get_ipython
            ip = get_ipython()
            if ip is not None:
                try:
                    ip.events.unregister('post_run_cell', hook_func)
                except ValueError:
                    # Hook not registered (already removed)
                    pass

            logger.info("Uninstalled IPython hook for source extraction")
            return True

        except Exception as e:
            # Restore state on failure
            with cls._cache_lock:
                cls._hook_installed = True
                cls._hook_function = hook_func
            logger.debug(f"Failed to uninstall IPython hook: {e}")
            return False

    @classmethod
    def _invalidate_functions(cls, func_names: list) -> None:
        """
        Invalidate extraction caches for functions that have been redefined.

        When a cell is re-executed with modified code, we need to clear
        cached extraction results so the new source is used.

        Thread-safe wrapper that acquires _cache_lock.
        """
        if not func_names:
            return

        with cls._cache_lock:
            cls._invalidate_functions_unlocked(func_names)

    @classmethod
    def _invalidate_functions_unlocked(cls, func_names: list) -> None:
        """
        Selectively invalidate extraction caches (must be called with _cache_lock held).

        Uses the _func_name_to_code_ids mapping to clear only the cache entries
        for the redefined functions, rather than clearing ALL caches. This is more
        efficient and preserves cache hits for unrelated functions.
        """
        if not func_names:
            return

        invalidated_count = 0

        # Selectively clear success cache entries for affected functions
        for func_name in func_names:
            code_ids = cls._func_name_to_code_ids.get(func_name, set())
            for code_id in code_ids:
                if code_id in cls._success_cache:
                    del cls._success_cache[code_id]
                    invalidated_count += 1
                # Also remove from failure cache in case previous extraction failed
                # but new code is valid
                cls._failure_cache.discard(code_id)

            # Clear the mapping for this function (will be re-populated on next extraction)
            if func_name in cls._func_name_to_code_ids:
                del cls._func_name_to_code_ids[func_name]

        if invalidated_count > 0:
            logger.debug(f"Selectively invalidated {invalidated_count} cache entries for: {func_names}")
