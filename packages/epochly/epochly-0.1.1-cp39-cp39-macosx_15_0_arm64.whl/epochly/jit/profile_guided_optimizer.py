"""
Profile-Guided Optimization for Epochly JIT Pipeline.

This module implements profile-guided optimization that uses runtime execution
profiles to make intelligent compilation decisions and optimization strategies.
"""

import time
import statistics
import threading
import numpy as np
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging
import os

logger = logging.getLogger(__name__)


# Module-level worker function for ThreadPoolExecutor
def _analyze_profile_worker(args: Tuple[str, List[float]]) -> Tuple[str, Dict[str, Any]]:
    """
    Worker function to analyze a single profile.

    This is a module-level function to support executor.map().
    """
    func_name, profile = args

    if not profile or len(profile) < 5:
        return func_name, {
            'optimization_level': 0,
            'enable_parallel': False,
            'enable_fastmath': False,
            'enable_inlining': False,
            'compilation_timeout_ms': 0.0,
            'expected_speedup': 1.0,
            'reasoning': ['Insufficient profile data']
        }

    # Analyze characteristics inline (avoid creating ProfileGuidedOptimizer in worker)
    mean_time = statistics.mean(profile)
    variance = statistics.variance(profile) if len(profile) > 1 else 0.0

    if len(profile) >= 2:
        call_frequency = len(profile) / (len(profile) * mean_time) if mean_time > 0 else 0.0
    else:
        call_frequency = 1.0 / mean_time if mean_time > 0 else 0.0

    stability = 1.0 - (np.sqrt(variance) / mean_time) if mean_time > 0 else 0.0
    stability = max(0.0, min(1.0, stability))
    potential = min(1.0, (call_frequency * mean_time * 1000))

    # Select strategy based on characteristics
    if call_frequency > 100.0 and stability > 0.8:
        strategy_key = 'high_frequency_stable'
        result = {
            'optimization_level': 3,
            'enable_parallel': True,
            'enable_fastmath': True,
            'enable_inlining': True,
            'compilation_timeout_ms': 2000.0,
            'expected_speedup': 2.5,
            'reasoning': ['High frequency', 'Stable performance', 'Aggressive optimization']
        }
    elif call_frequency > 10.0 and potential > 0.5:
        strategy_key = 'moderate_frequency_variable'
        result = {
            'optimization_level': 2,
            'enable_parallel': False,
            'enable_fastmath': True,
            'enable_inlining': True,
            'compilation_timeout_ms': 1000.0,
            'expected_speedup': 1.8,
            'reasoning': ['Moderate frequency', 'Variable performance', 'Conservative optimization']
        }
    elif potential > 0.2:
        strategy_key = 'low_frequency_simple'
        result = {
            'optimization_level': 1,
            'enable_parallel': False,
            'enable_fastmath': False,
            'enable_inlining': True,
            'compilation_timeout_ms': 500.0,
            'expected_speedup': 1.3,
            'reasoning': ['Low frequency', 'Simple optimization']
        }
    else:
        strategy_key = 'unsuitable'
        result = {
            'optimization_level': 0,
            'enable_parallel': False,
            'enable_fastmath': False,
            'enable_inlining': False,
            'compilation_timeout_ms': 0.0,
            'expected_speedup': 1.0,
            'reasoning': ['Profile indicates JIT not beneficial']
        }

    # Apply adaptations based on characteristics
    if mean_time > 0.01:  # >10ms
        result['compilation_timeout_ms'] *= 1.5
        result['reasoning'].append('Long execution - extended compilation budget')

    if stability < 0.5:
        result['enable_fastmath'] = False
        result['reasoning'].append('Variable performance - conservative optimization')

    if call_frequency > 1000:
        result['optimization_level'] = min(3, result['optimization_level'] + 1)
        result['reasoning'].append('Very high frequency - maximum optimization')

    return func_name, result


@dataclass
class OptimizationStrategy:
    """Optimization strategy based on profile analysis."""
    optimization_level: int  # 0-3 (none, basic, aggressive, maximum)
    enable_parallel: bool
    enable_fastmath: bool
    enable_inlining: bool
    compilation_timeout_ms: float
    expected_speedup: float
    reasoning: List[str]
    version: int = 1


@dataclass
class ProfileCharacteristics:
    """Characteristics derived from execution profile."""
    mean_execution_time: float
    execution_variance: float
    call_frequency: float
    performance_stability: float
    optimization_potential: float


class ProfileGuidedOptimizer:
    """
    Profile-guided optimization system for intelligent JIT compilation.
    
    Uses runtime execution profiles to determine optimal compilation strategies,
    adaptation decisions, and performance improvements.
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """Initialize profile-guided optimizer.

        Args:
            max_workers: Maximum workers for parallel processing. Defaults to CPU count.
        """
        self.logger = logging.getLogger(__name__)
        self._max_workers = max_workers or min(os.cpu_count() or 4, 8)
        self._executor: Optional[ThreadPoolExecutor] = None
        self._warm_pool = None
        self._lock = threading.Lock()
        self._is_shutdown = False
        
        # Strategy templates based on profile characteristics
        self._strategy_templates = {
            'high_frequency_stable': OptimizationStrategy(
                optimization_level=3,
                enable_parallel=True,
                enable_fastmath=True,
                enable_inlining=True,
                compilation_timeout_ms=2000.0,
                expected_speedup=2.5,
                reasoning=['High frequency', 'Stable performance', 'Aggressive optimization beneficial']
            ),
            'moderate_frequency_variable': OptimizationStrategy(
                optimization_level=2,
                enable_parallel=False,
                enable_fastmath=True,
                enable_inlining=True,
                compilation_timeout_ms=1000.0,
                expected_speedup=1.8,
                reasoning=['Moderate frequency', 'Variable performance', 'Conservative optimization']
            ),
            'low_frequency_simple': OptimizationStrategy(
                optimization_level=1,
                enable_parallel=False,
                enable_fastmath=False,
                enable_inlining=True,
                compilation_timeout_ms=500.0,
                expected_speedup=1.3,
                reasoning=['Low frequency', 'Simple optimization', 'Quick compilation']
            ),
            'unsuitable': OptimizationStrategy(
                optimization_level=0,
                enable_parallel=False,
                enable_fastmath=False,
                enable_inlining=False,
                compilation_timeout_ms=0.0,
                expected_speedup=1.0,
                reasoning=['Profile indicates JIT not beneficial']
            )
        }
        
        # Learning data for strategy adaptation
        self._strategy_feedback: Dict[str, List[float]] = {}
        self._adaptation_history: List[Dict[str, Any]] = []
    
    def determine_optimization_strategy(self, func_name: str, 
                                     execution_profile: List[float]) -> Dict[str, Any]:
        """
        Determine optimization strategy based on execution profile.
        
        Args:
            func_name: Name of function to optimize
            execution_profile: List of execution times (seconds)
            
        Returns:
            Optimization strategy dictionary
        """
        if not execution_profile or len(execution_profile) < 5:
            return self._strategy_templates['unsuitable'].__dict__
        
        # Analyze profile characteristics
        characteristics = self._analyze_profile_characteristics(execution_profile)
        
        # Select strategy template based on characteristics
        strategy_key = self._select_strategy_template(characteristics)
        strategy = self._strategy_templates[strategy_key]
        
        # Adapt strategy based on specific characteristics
        adapted_strategy = self._adapt_strategy_to_profile(strategy, characteristics)
        
        # Record strategy decision for learning
        self._record_strategy_decision(func_name, strategy_key, characteristics, adapted_strategy)
        
        return adapted_strategy.__dict__
    
    def adapt_strategy_from_feedback(self, func_name: str, 
                                   new_profile: List[float],
                                   current_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt optimization strategy based on feedback from new execution profile.
        
        Args:
            func_name: Name of function
            new_profile: New execution profile data
            current_strategy: Current optimization strategy
            
        Returns:
            Adapted strategy
        """
        if not new_profile:
            return current_strategy
        
        # Analyze new profile
        new_characteristics = self._analyze_profile_characteristics(new_profile)
        
        # Check if strategy should be adapted
        adaptation_needed = self._should_adapt_strategy(new_characteristics, current_strategy)
        
        if adaptation_needed:
            # Create adapted strategy
            adapted_strategy = current_strategy.copy()
            adapted_strategy['version'] = current_strategy.get('version', 1) + 1
            adapted_strategy['adapted'] = True
            
            # Adjust based on new profile
            if new_characteristics.optimization_potential > 0.8:
                adapted_strategy['optimization_level'] = min(3, adapted_strategy['optimization_level'] + 1)
            elif new_characteristics.optimization_potential < 0.3:
                adapted_strategy['optimization_level'] = max(0, adapted_strategy['optimization_level'] - 1)
            
            # Update reasoning
            adapted_strategy['reasoning'] = adapted_strategy.get('reasoning', []) + [
                f'Adapted based on profile feedback',
                f'New optimization potential: {new_characteristics.optimization_potential:.2f}'
            ]
            
            # Record adaptation
            self._record_adaptation(func_name, current_strategy, adapted_strategy, new_characteristics)
            
            return adapted_strategy
        
        return current_strategy
    
    def optimize_function_with_profile(self, func: Callable, 
                                     execution_profile: List[float]) -> Callable:
        """
        Optimize function using profile-guided optimization.
        
        Args:
            func: Function to optimize
            execution_profile: Execution profile data
            
        Returns:
            Optimized function
        """
        func_name = getattr(func, '__name__', str(func))
        
        # Get optimization strategy from profile
        strategy = self.determine_optimization_strategy(func_name, execution_profile)
        
        if strategy['optimization_level'] == 0:
            return func  # No optimization beneficial
        
        try:
            # Apply profile-guided compilation
            from epochly.jit.numba_jit import NumbaJIT
            
            # Configure Numba based on profile-guided strategy
            numba_options = {
                'nopython': True,
                'cache': True,
                'parallel': strategy['enable_parallel'],
                'fastmath': strategy['enable_fastmath'],
            }
            
            compiler = NumbaJIT(**numba_options)
            compilation_result = compiler.compile_function(func)
            
            if compilation_result and compilation_result.is_successful:
                logger.info(f"Profile-guided optimization successful: {func_name}")
                return compilation_result.compiled_function
            else:
                logger.debug(f"Profile-guided optimization failed: {func_name}")
                return func
                
        except Exception as e:
            logger.warning(f"Profile-guided optimization error for {func_name}: {e}")
            return func
    
    def _analyze_profile_characteristics(self, execution_profile: List[float]) -> ProfileCharacteristics:
        """Analyze execution profile to extract characteristics."""
        if not execution_profile:
            return ProfileCharacteristics(0.0, 0.0, 0.0, 0.0, 0.0)
        
        mean_time = statistics.mean(execution_profile)
        variance = statistics.variance(execution_profile) if len(execution_profile) > 1 else 0.0
        
        # Calculate call frequency (calls per second, estimated)
        if len(execution_profile) >= 2:
            # Estimate based on profile collection rate
            call_frequency = len(execution_profile) / (len(execution_profile) * mean_time)
        else:
            call_frequency = 1.0 / mean_time if mean_time > 0 else 0.0
        
        # Performance stability (inverse of coefficient of variation)
        stability = 1.0 - (np.sqrt(variance) / mean_time) if mean_time > 0 else 0.0
        stability = max(0.0, min(1.0, stability))
        
        # Optimization potential (based on execution time and frequency)
        potential = min(1.0, (call_frequency * mean_time * 1000))  # Scale to 0-1
        
        return ProfileCharacteristics(
            mean_execution_time=mean_time,
            execution_variance=variance,
            call_frequency=call_frequency,
            performance_stability=stability,
            optimization_potential=potential
        )
    
    def _select_strategy_template(self, characteristics: ProfileCharacteristics) -> str:
        """Select strategy template based on profile characteristics."""
        # High frequency and stable performance
        if (characteristics.call_frequency > 100.0 and 
            characteristics.performance_stability > 0.8):
            return 'high_frequency_stable'
        
        # Moderate frequency with variable performance
        elif (characteristics.call_frequency > 10.0 and 
              characteristics.optimization_potential > 0.5):
            return 'moderate_frequency_variable'
        
        # Low frequency but some optimization potential
        elif characteristics.optimization_potential > 0.2:
            return 'low_frequency_simple'
        
        # Not suitable for optimization
        else:
            return 'unsuitable'
    
    def _adapt_strategy_to_profile(self, base_strategy: OptimizationStrategy,
                                 characteristics: ProfileCharacteristics) -> OptimizationStrategy:
        """Adapt base strategy to specific profile characteristics."""
        adapted = OptimizationStrategy(
            optimization_level=base_strategy.optimization_level,
            enable_parallel=base_strategy.enable_parallel,
            enable_fastmath=base_strategy.enable_fastmath,
            enable_inlining=base_strategy.enable_inlining,
            compilation_timeout_ms=base_strategy.compilation_timeout_ms,
            expected_speedup=base_strategy.expected_speedup,
            reasoning=base_strategy.reasoning.copy()
        )
        
        # Adjust based on specific characteristics
        if characteristics.mean_execution_time > 0.01:  # >10ms execution time
            adapted.compilation_timeout_ms *= 1.5  # Allow more compilation time
            adapted.reasoning.append('Long execution time - extended compilation budget')
        
        if characteristics.performance_stability < 0.5:  # Variable performance
            adapted.enable_fastmath = False  # Disable aggressive optimizations
            adapted.reasoning.append('Variable performance - conservative optimization')
        
        if characteristics.call_frequency > 1000:  # Very high frequency
            adapted.optimization_level = min(3, adapted.optimization_level + 1)
            adapted.reasoning.append('Very high call frequency - maximum optimization')
        
        return adapted
    
    def _should_adapt_strategy(self, new_characteristics: ProfileCharacteristics,
                             current_strategy: Dict[str, Any]) -> bool:
        """Determine if strategy should be adapted based on new profile."""
        # Simple adaptation logic - more sophisticated version could use ML
        current_level = current_strategy.get('optimization_level', 1)
        
        # Adapt if optimization potential significantly changed
        if new_characteristics.optimization_potential > 0.8 and current_level < 3:
            return True
        elif new_characteristics.optimization_potential < 0.3 and current_level > 1:
            return True
        
        return False
    
    def _record_strategy_decision(self, func_name: str, strategy_key: str,
                                characteristics: ProfileCharacteristics,
                                strategy: OptimizationStrategy) -> None:
        """Record strategy decision for learning."""
        decision_record = {
            'timestamp': time.time(),
            'func_name': func_name,
            'strategy_key': strategy_key,
            'characteristics': characteristics.__dict__,
            'strategy': strategy.__dict__
        }
        
        self._adaptation_history.append(decision_record)
        
        # Keep recent history only
        if len(self._adaptation_history) > 1000:
            self._adaptation_history = self._adaptation_history[-1000:]
    
    def _record_adaptation(self, func_name: str, old_strategy: Dict[str, Any],
                         new_strategy: Dict[str, Any],
                         characteristics: ProfileCharacteristics) -> None:
        """Record strategy adaptation for learning."""
        adaptation_record = {
            'timestamp': time.time(),
            'func_name': func_name,
            'old_strategy': old_strategy,
            'new_strategy': new_strategy,
            'characteristics': characteristics.__dict__,
            'adaptation_type': 'profile_feedback'
        }

        self._adaptation_history.append(adaptation_record)

    def batch_analyze_profiles(self, profiles: Dict[str, List[float]],
                               parallel: bool = True,
                               use_warm_pool: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Analyze multiple function profiles in batch, optionally in parallel.

        This method provides significant speedup (6-8x on 8 cores) when analyzing
        many function profiles by distributing the work across processes.

        Args:
            profiles: Dictionary mapping function name to execution profile
            parallel: If True, use parallel processing (default True)
            use_warm_pool: If True, use WarmWorkerPool for reduced startup overhead

        Returns:
            Dictionary mapping function name to optimization strategy
        """
        if not profiles:
            return {}

        if not parallel or len(profiles) < 4:
            # Sequential for small batches (overhead not worth it)
            return {
                func_name: self.determine_optimization_strategy(func_name, profile)
                for func_name, profile in profiles.items()
            }

        # Parallel processing
        results = {}

        if use_warm_pool:
            # Use WarmWorkerPool if requested
            try:
                from epochly.profiling.adaptive_executor import WarmWorkerPool

                with self._lock:
                    if self._warm_pool is None:
                        self._warm_pool = WarmWorkerPool(
                            max_workers=self._max_workers,
                            pre_import_modules=['statistics', 'numpy']
                        )

                # Submit all tasks
                work_items = list(profiles.items())
                analyzed = self._warm_pool.map(_analyze_profile_worker, work_items)

                for func_name, strategy in analyzed:
                    results[func_name] = strategy

            except ImportError:
                # Fall back to ThreadPoolExecutor
                parallel = True  # Will use standard parallel below
            except OSError as e:
                # Handle semaphore exhaustion (ENOSPC on macOS) and other OS-level errors
                # that prevent ProcessPoolExecutor from creating workers.
                # This can happen when POSIX semaphores are exhausted (macOS has limited pool).
                # See Python bugs #46391, #90549 for known semaphore leak issues.
                import logging
                logging.getLogger(__name__).warning(
                    f"WarmWorkerPool unavailable due to OS error (errno={e.errno}), "
                    f"falling back to ThreadPoolExecutor: {e}"
                )
                # Clean up failed warm pool
                with self._lock:
                    if self._warm_pool is not None:
                        try:
                            self._warm_pool.shutdown(wait=False)
                        except Exception:
                            pass
                        self._warm_pool = None
                # Will fall through to ThreadPoolExecutor below

        if not results:
            # ThreadPoolExecutor (no orphan risk, safe for trivial workloads)
            work_items = list(profiles.items())

            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                for func_name, strategy in executor.map(_analyze_profile_worker, work_items):
                    results[func_name] = strategy

        return results

    def shutdown(self) -> None:
        """Shutdown parallel resources and release worker pools."""
        with self._lock:
            if self._is_shutdown:
                return

            self._is_shutdown = True

            if self._warm_pool is not None:
                try:
                    self._warm_pool.shutdown()
                except Exception:
                    pass
                self._warm_pool = None

            if self._executor is not None:
                try:
                    self._executor.shutdown(wait=False)
                except Exception:
                    pass
                self._executor = None

    def __enter__(self) -> 'ProfileGuidedOptimizer':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - shutdown resources."""
        self.shutdown()


# Global instance for performance
_global_optimizer = None

def get_profile_guided_optimizer() -> ProfileGuidedOptimizer:
    """Get global profile-guided optimizer instance."""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = ProfileGuidedOptimizer()
    return _global_optimizer