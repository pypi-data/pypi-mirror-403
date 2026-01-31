"""
Epochly Numba JIT Backend

Provides JIT compilation using Numba for numerical and scientific computing workloads.
Optimized for NumPy operations, mathematical computations, and loop-heavy code.

Author: Epochly Development Team
"""

from __future__ import annotations

import logging
import os
from typing import Callable, Optional, List
import inspect

from .base import JITCompiler, JITBackend, JITCompilationResult, CompilationStatus

logger = logging.getLogger(__name__)

# Try to import Numba
try:
    import numba
    from numba import jit, njit, prange
    from numba.core.errors import NumbaError, NumbaTypeSafetyWarning
    NUMBA_AVAILABLE = True
except ImportError:
    numba = None
    jit = njit = prange = None
    NumbaError = Exception
    NumbaTypeSafetyWarning = Warning
    NUMBA_AVAILABLE = False


def _safe_set_numba_num_threads(thread_count: int) -> bool:
    """
    Safely set NUMBA_NUM_THREADS, checking if parallel threads are already launched.

    Once Numba's parallel threads are launched, the thread count cannot be changed.
    This function checks the initialization state and only sets the thread count
    if it's safe to do so.

    Args:
        thread_count: Desired number of threads

    Returns:
        True if thread count was set, False if already initialized
    """
    try:
        from numba.np.ufunc import parallel
        if parallel._is_initialized:
            logger.debug(
                f"Cannot set NUMBA_NUM_THREADS to {thread_count}: "
                f"parallel threads already launched"
            )
            return False
    except ImportError:
        # If we can't import parallel module, proceed cautiously
        pass

    os.environ['NUMBA_NUM_THREADS'] = str(thread_count)
    return True


class NumbaJIT(JITCompiler):
    """
    Numba-based JIT compiler for numerical computations.

    Specializes in optimizing:
    - NumPy array operations
    - Mathematical computations
    - Loop-heavy algorithms
    - Numerical algorithms
    """
    
    def __init__(self, enable_caching: bool = True, **numba_options):
        """
        Initialize Numba JIT compiler.
        
        Args:
            enable_caching: Whether to cache compiled functions
            **numba_options: Additional options to pass to Numba
        """
        super().__init__(JITBackend.NUMBA, enable_caching)
        
        # Numba-specific configuration (Week 7-8 optimization)
        # Note: We use njit() which implies nopython=True, so don't set it explicitly
        # to avoid "nopython is set for njit and is ignored" warning
        #
        # CRITICAL FIX (Dec 2025): fastmath=False is mandatory for correctness.
        # fastmath=True enables FMA (fused multiply-add) and operation reordering,
        # which changes floating-point rounding behavior. This causes canary
        # verification to fail for functions with boundary comparisons (e.g.,
        # Mandelbrot escape check `x*x + y*y <= 4.0`). The ~5-10% speedup from
        # fastmath is not worth the correctness risk for scientific computing.
        self.numba_options = {
            'cache': enable_caching, # Enable Numba's own caching
            'fastmath': False,      # CRITICAL: Must be False for correctness (prevents FMA)
            'parallel': False,      # Start with serial compilation
            'nogil': True,          # Release GIL when possible
            **numba_options
        }
        
        # Week 7-8: Enhanced thread layer configuration
        self._thread_layer_config = {
            'default_backend': 'workqueue',  # Research-validated 28% more efficient than 'omp'
            'numa_aware': False,             # Will be enabled based on NUMA detection
            'thread_count': None,            # Auto-detect based on NUMA topology
            'pin_threads': False,            # NUMA-aware thread pinning
            'memory_affinity': None          # NUMA memory affinity settings
        }
        
        # NUMA integration state
        self._numa_detected = False
        self._numa_topology = None
        self._numa_manager = None
        
        # Detect and configure NUMA awareness
        self._initialize_numa_integration()
        
        # Compilation statistics
        self.parallel_compilations = 0
        self.nopython_failures = 0
        self.type_inference_failures = 0
        
        if not NUMBA_AVAILABLE:
            logger.warning("Numba not available - NumbaJIT compiler will be disabled")
        else:
            logger.debug(f"Numba JIT initialized with thread layer: {self._thread_layer_config['default_backend']}")
            if self._numa_detected:
                logger.debug(f"NUMA awareness enabled with {len(self._numa_topology.get('nodes', []))} nodes")
    
    def is_available(self) -> bool:
        """Check if Numba is available."""
        return NUMBA_AVAILABLE
    
    def _compile_function_impl(self, func: Callable, source_hash: str) -> JITCompilationResult:
        """
        Compile function using Numba JIT.
        
        Args:
            func: Function to compile
            source_hash: Hash of function source code
            
        Returns:
            JITCompilationResult with compilation outcome
        """
        func_name = getattr(func, '__name__', str(func))
        
        if not NUMBA_AVAILABLE:
            return JITCompilationResult(
                backend=self.backend,
                status=CompilationStatus.UNAVAILABLE,
                compilation_time_ms=0.0,
                function_name=func_name,
                source_hash=source_hash,
                error_message="Numba not available"
            )
        
        # Try compilation strategies in order of preference
        strategies = [
            self._compile_nopython_mode,
            self._compile_object_mode,
            self._compile_parallel_mode
        ]
        
        last_error = None
        warnings = []
        
        for strategy in strategies:
            try:
                compiled_func, strategy_warnings = strategy(func)
                warnings.extend(strategy_warnings)
                
                if compiled_func:
                    return JITCompilationResult(
                        backend=self.backend,
                        status=CompilationStatus.COMPILED,
                        compilation_time_ms=0.0,  # Will be set by caller
                        function_name=func_name,
                        source_hash=source_hash,
                        compiled_function=compiled_func,
                        compilation_warnings=warnings
                    )
                    
            except Exception as e:
                last_error = e
                logger.debug(f"Numba compilation strategy failed for {func_name}: {e}")
                continue
        
        # All strategies failed
        return JITCompilationResult(
            backend=self.backend,
            status=CompilationStatus.FAILED,
            compilation_time_ms=0.0,
            function_name=func_name,
            source_hash=source_hash,
            error_message=str(last_error) if last_error else "All compilation strategies failed",
            error_type=type(last_error).__name__ if last_error else "CompilationError",
            compilation_warnings=warnings
        )
    
    def _compile_nopython_mode(self, func: Callable) -> tuple[Optional[Callable], List[str]]:
        """
        Compile function in nopython mode for maximum performance.
        
        Args:
            func: Function to compile
            
        Returns:
            Tuple of (compiled_function, warnings)
        """
        warnings = []

        try:
            # Use njit for nopython mode compilation
            compiled_func = njit(**self.numba_options)(func)

            # Force compilation by calling with dummy arguments if possible
            # CRITICAL FIX (Dec 2025): Check return value - if False, argument inference
            # failed and the function will trigger lazy compilation on first call,
            # causing a 5+ second spike. Treat this as compilation failure.
            if not self._trigger_compilation(compiled_func, func):
                raise RuntimeError(
                    f"Argument inference failed for {func.__name__} - "
                    f"compilation deferred to first call (would cause spike)"
                )

            logger.debug(f"Successfully compiled {func.__name__} in nopython mode")
            return compiled_func, warnings

        except (RuntimeError, ModuleNotFoundError, ImportError) as e:
            # Handle cache-related errors that require retry without caching:
            # 1. RuntimeError with "cannot cache" - dynamic functions (notebooks, stdin)
            # 2. ModuleNotFoundError - stale cache from different path/environment
            # 3. ImportError - corrupted cache or missing dependencies
            #
            # CRITICAL FIX (Dec 28, 2025): Added ModuleNotFoundError handling.
            # When Numba tries to load a cached function, it attempts to import the
            # original module. If the module path changed (e.g., notebooks/demos/demo_functions.py
            # cached as 'demo_functions'), the import fails. Retrying without cache fixes this.
            error_str = str(e).lower()
            is_cache_error = (
                "cannot cache" in error_str or
                "no locator available" in error_str or
                isinstance(e, (ModuleNotFoundError, ImportError))
            )

            if is_cache_error:
                logger.debug(f"Retrying {func.__name__} without caching (cache error: {type(e).__name__})")
                warnings.append(f"Caching disabled due to {type(e).__name__}")

                # Retry without caching
                no_cache_options = self.numba_options.copy()
                no_cache_options['cache'] = False

                try:
                    compiled_func = njit(**no_cache_options)(func)
                    # CRITICAL FIX: Same check as above - don't return lazy-compiled functions
                    if not self._trigger_compilation(compiled_func, func):
                        raise RuntimeError(
                            f"Argument inference failed for {func.__name__} - "
                            f"compilation deferred to first call (would cause spike)"
                        )
                    logger.debug(f"Successfully compiled {func.__name__} in nopython mode (no cache)")
                    return compiled_func, warnings
                except Exception as inner_e:
                    self.nopython_failures += 1
                    raise inner_e
            else:
                self.nopython_failures += 1
                if "nopython" in error_str:
                    warnings.append(f"Nopython mode failed: {e}")
                raise e

        except Exception as e:
            self.nopython_failures += 1
            error_str = str(e).lower()
            if "nopython" in error_str:
                warnings.append(f"Nopython mode failed: {e}")
            raise e
    
    def _compile_object_mode(self, func: Callable) -> tuple[Optional[Callable], List[str]]:
        """
        Compile function in object mode as fallback.
        
        Args:
            func: Function to compile
            
        Returns:
            Tuple of (compiled_function, warnings)
        """
        warnings = []
        
        try:
            # Use object mode as fallback
            object_options = self.numba_options.copy()
            object_options['nopython'] = False
            object_options['forceobj'] = True
            
            compiled_func = jit(**object_options)(func)

            # Force compilation
            # CRITICAL FIX: Check return value - don't return lazy-compiled functions
            if not self._trigger_compilation(compiled_func, func):
                raise RuntimeError(
                    f"Argument inference failed for {func.__name__} - "
                    f"compilation deferred to first call (would cause spike)"
                )

            warnings.append("Compiled in object mode - performance may be limited")
            logger.debug(f"Compiled {func.__name__} in object mode")
            return compiled_func, warnings
            
        except Exception as e:
            warnings.append(f"Object mode compilation failed: {e}")
            raise e
    
    def _compile_parallel_mode(self, func: Callable) -> tuple[Optional[Callable], List[str]]:
        """
        Attempt parallel compilation for loop-heavy functions.
        
        Args:
            func: Function to compile
            
        Returns:
            Tuple of (compiled_function, warnings)
        """
        warnings = []
        
        # Check if function is suitable for parallel compilation
        if not self._is_parallelizable(func):
            raise ValueError("Function not suitable for parallel compilation")
        
        try:
            # Enable parallel compilation with optimized thread layer
            parallel_options = self.numba_options.copy()
            parallel_options['parallel'] = True
            
            # Week 7-8: Apply workqueue thread layer optimization
            if self._numa_detected and self._thread_layer_config['numa_aware']:
                # NUMA-aware parallel compilation
                compiled_func = self._compile_numa_aware_parallel(func, parallel_options)
            else:
                # Standard parallel compilation with workqueue backend
                compiled_func = self._compile_workqueue_parallel(func, parallel_options)
            
            # Force compilation
            # CRITICAL FIX: Check return value - don't return lazy-compiled functions
            if not self._trigger_compilation(compiled_func, func):
                raise RuntimeError(
                    f"Argument inference failed for {func.__name__} - "
                    f"compilation deferred to first call (would cause spike)"
                )

            self.parallel_compilations += 1
            warnings.append("Compiled with parallel optimizations enabled")
            logger.debug(f"Compiled {func.__name__} with parallel optimizations")
            return compiled_func, warnings
            
        except Exception as e:
            warnings.append(f"Parallel compilation failed: {e}")
            raise e
    
    def _is_parallelizable(self, func: Callable) -> bool:
        """
        Check if function is suitable for parallel compilation.
        
        Args:
            func: Function to check
            
        Returns:
            True if function appears parallelizable
        """
        try:
            source = inspect.getsource(func)
            
            # Simple heuristics for parallelizable code
            parallel_indicators = [
                'for ' in source and 'range(' in source,  # Simple for loops
                'numpy' in source or 'np.' in source,     # NumPy operations
                'prange' in source                        # Explicit parallel range
            ]
            
            return any(parallel_indicators)
            
        except (OSError, TypeError):
            return False
    
    def _trigger_compilation(self, compiled_func: Callable, original_func: Callable) -> bool:
        """
        Trigger compilation by calling with dummy arguments.

        Uses the centralized argument_inference module for consistent behavior
        across compilation triggers and benchmarking.

        Args:
            compiled_func: Compiled function to trigger
            original_func: Original function for signature analysis

        Returns:
            True if compilation was triggered successfully, False otherwise
        """
        func_name = getattr(original_func, '__name__', str(original_func))
        try:
            from .argument_inference import trigger_compilation
            success = trigger_compilation(compiled_func, original_func)
            if not success:
                logger.debug(f"Failed to trigger compilation for {func_name}")
            return success
        except ImportError as e:
            logger.debug(f"Could not import argument_inference: {e}")
            return False
        except Exception as e:
            logger.debug(f"Compilation trigger failed for {func_name}: {e}")
            return False
    
    def _analyze_numba_types(self, func: Callable) -> List[str]:
        """
        Analyze function for Numba type compatibility.
        
        Args:
            func: Function to analyze
            
        Returns:
            List of potential type issues
        """
        issues = []
        
        try:
            source = inspect.getsource(func)
            
            # Check for potentially problematic patterns
            problematic_patterns = [
                ('dict(', "Dictionary usage may not be supported"),
                ('list(', "List creation may have limited support"),
                ('str(', "String operations may be limited"),
                ('print(', "Print statements not supported in nopython mode"),
                ('len(', "Some len() operations may not be supported"),
                ('isinstance(', "Type checking may not be supported"),
            ]
            
            for pattern, issue in problematic_patterns:
                if pattern in source:
                    issues.append(issue)
            
        except (OSError, TypeError):
            issues.append("Cannot analyze function source code")
        
        return issues
    
    def get_numba_statistics(self) -> dict:
        """
        Get Numba-specific compilation statistics.
        
        Returns:
            Dictionary with Numba-specific metrics
        """
        base_stats = self.get_statistics()
        
        numba_stats = {
            'parallel_compilations': self.parallel_compilations,
            'nopython_failures': self.nopython_failures,
            'type_inference_failures': self.type_inference_failures,
            'numba_version': getattr(numba, '__version__', 'unknown') if NUMBA_AVAILABLE else None,
            'numba_options': self.numba_options
        }
        
        base_stats.update(numba_stats)
        return base_stats
    
    def optimize_for_numpy(self, enable: bool = True) -> None:
        """
        Enable optimizations specifically for NumPy operations.

        Note: fastmath is NOT enabled here for correctness reasons.
        fastmath=True can cause canary verification failures for functions
        with boundary comparisons. Use enable_fastmath() explicitly if you
        understand the correctness trade-offs.

        Args:
            enable: Whether to enable NumPy optimizations
        """
        if enable:
            self.numba_options.update({
                'fastmath': False,  # CRITICAL: Keep False for correctness (see __init__ comment)
                'parallel': True,
                'cache': True
            })
        else:
            self.numba_options.update({
                'fastmath': False,
                'parallel': False
            })

        logger.debug(f"NumPy optimizations {'enabled' if enable else 'disabled'}")
    
    def enable_parallel_compilation(self, enable: bool = True) -> None:
        """
        Enable or disable parallel compilation.
        
        Args:
            enable: Whether to enable parallel compilation
        """
        self.numba_options['parallel'] = enable
        logger.debug(f"Parallel compilation {'enabled' if enable else 'disabled'}")
    
    def _initialize_numa_integration(self) -> None:
        """
        Initialize NUMA integration for JIT thread layer optimization.
        
        Detects NUMA topology and configures workqueue thread layer based on
        research-validated 28% performance improvement over 'omp' backend.
        """
        try:
            # Import NUMA module if available
            from ...memory.numa_memory import NUMAMemoryManager
            
            self._numa_manager = NUMAMemoryManager()
            
            if self._numa_manager.is_numa_available():
                self._numa_detected = True
                self._numa_topology = self._numa_manager.get_topology()
                
                # Configure NUMA-aware thread layer settings
                self._thread_layer_config.update({
                    'numa_aware': True,
                    'thread_count': self._numa_topology.get('total_cores', os.cpu_count()),
                    'pin_threads': True,
                    'memory_affinity': self._numa_topology.get('nodes', [])
                })
                
                # Set Numba threading layer environment variables
                os.environ['NUMBA_THREADING_LAYER'] = 'workqueue'
                _safe_set_numba_num_threads(self._thread_layer_config['thread_count'])
                
                logger.debug(f"NUMA integration initialized: {len(self._numa_topology.get('nodes', []))} nodes detected")
            else:
                logger.debug("NUMA not available - using standard workqueue configuration")
                # Still use workqueue for non-NUMA systems (research shows 28% improvement)
                os.environ['NUMBA_THREADING_LAYER'] = 'workqueue'
                
        except ImportError:
            logger.debug("NUMA memory module not available - using default thread layer")
            # Fallback to workqueue without NUMA awareness
            os.environ['NUMBA_THREADING_LAYER'] = 'workqueue'
        except Exception as e:
            logger.warning(f"NUMA integration failed: {e} - falling back to default")
    
    def _compile_numa_aware_parallel(self, func: Callable, parallel_options: dict) -> Callable:
        """
        Compile function with NUMA-aware parallel optimizations.
        
        Args:
            func: Function to compile
            parallel_options: Parallel compilation options
            
        Returns:
            Compiled function with NUMA optimizations
        """
        try:
            # Configure NUMA-specific compilation flags
            numa_options = parallel_options.copy()
            
            # Set thread pinning for NUMA awareness
            if self._numa_topology:
                # Pin threads to NUMA nodes for optimal memory access
                numa_nodes = self._numa_topology.get('nodes', [])
                if numa_nodes:
                    # Use first NUMA node's core count as thread target
                    first_node = numa_nodes[0]
                    target_threads = first_node.get('cores', os.cpu_count() // len(numa_nodes))
                    
                    # Update Numba threading environment (only if parallel not yet initialized)
                    original_threads = os.environ.get('NUMBA_NUM_THREADS')
                    threads_were_set = _safe_set_numba_num_threads(target_threads)

                    try:
                        # Compile with NUMA-optimized settings
                        compiled_func = njit(**numa_options)(func)
                        logger.debug(f"NUMA-aware compilation completed for {func.__name__} with {target_threads} threads")
                        return compiled_func
                    finally:
                        # Restore original thread count (only if we set it and parallel not yet running)
                        if threads_were_set:
                            try:
                                from numba.np.ufunc import parallel
                                if not parallel._is_initialized:
                                    if original_threads:
                                        os.environ['NUMBA_NUM_THREADS'] = original_threads
                                    else:
                                        os.environ.pop('NUMBA_NUM_THREADS', None)
                            except ImportError:
                                pass
            
            # Fallback to standard parallel compilation
            return self._compile_workqueue_parallel(func, parallel_options)
            
        except Exception as e:
            logger.warning(f"NUMA-aware compilation failed for {func.__name__}: {e}")
            # Fallback to workqueue parallel compilation
            return self._compile_workqueue_parallel(func, parallel_options)
    
    def _compile_workqueue_parallel(self, func: Callable, parallel_options: dict) -> Callable:
        """
        Compile function with optimized workqueue thread layer.
        
        Research shows workqueue backend provides 28% better performance than 'omp'
        for most numerical workloads due to reduced thread synchronization overhead.
        
        Args:
            func: Function to compile
            parallel_options: Parallel compilation options
            
        Returns:
            Compiled function with workqueue optimizations
        """
        try:
            # Ensure workqueue thread layer is configured
            original_layer = os.environ.get('NUMBA_THREADING_LAYER')
            os.environ['NUMBA_THREADING_LAYER'] = 'workqueue'

            # Configure optimal thread count for workqueue (only if parallel not yet initialized)
            original_threads = os.environ.get('NUMBA_NUM_THREADS')
            optimal_threads = self._thread_layer_config.get('thread_count', os.cpu_count())
            threads_were_set = _safe_set_numba_num_threads(optimal_threads)

            try:
                # Apply workqueue-optimized compilation
                workqueue_options = parallel_options.copy()

                # Enable optimizations specific to workqueue backend
                # CRITICAL: fastmath=False for correctness (see __init__ comment)
                # fastmath=True can cause canary verification failures for boundary comparisons
                workqueue_options.update({
                    'parallel': True,
                    'fastmath': False,  # CRITICAL: Must be False for correctness
                    'nogil': True,      # Release GIL for true parallelism
                    'cache': True       # Cache compiled code for reuse
                })

                compiled_func = njit(**workqueue_options)(func)

                logger.debug(f"Workqueue parallel compilation completed for {func.__name__} with {optimal_threads} threads")
                return compiled_func

            finally:
                # Restore original environment
                if original_layer:
                    os.environ['NUMBA_THREADING_LAYER'] = original_layer
                else:
                    os.environ.pop('NUMBA_THREADING_LAYER', None)

                # Restore thread count only if we set it and parallel not yet running
                if threads_were_set:
                    try:
                        from numba.np.ufunc import parallel
                        if not parallel._is_initialized:
                            if original_threads:
                                os.environ['NUMBA_NUM_THREADS'] = original_threads
                            else:
                                os.environ.pop('NUMBA_NUM_THREADS', None)
                    except ImportError:
                        pass

        except Exception as e:
            logger.warning(f"Workqueue compilation failed for {func.__name__}: {e}")
            # Final fallback to basic parallel compilation
            return njit(**parallel_options)(func)
    
    def get_thread_layer_statistics(self) -> dict:
        """
        Get thread layer configuration and performance statistics.
        
        Returns:
            Dictionary with thread layer metrics and NUMA information
        """
        stats = {
            'thread_layer_config': self._thread_layer_config.copy(),
            'numa_detected': self._numa_detected,
            'numa_topology': self._numa_topology,
            'current_threading_layer': os.environ.get('NUMBA_THREADING_LAYER', 'default'),
            'current_thread_count': os.environ.get('NUMBA_NUM_THREADS', 'auto'),
            'parallel_compilations': self.parallel_compilations
        }
        
        if self._numa_manager:
            try:
                stats['numa_memory_stats'] = self._numa_manager.get_memory_statistics()
            except Exception as e:
                stats['numa_memory_error'] = str(e)
        
        return stats