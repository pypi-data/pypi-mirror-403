"""
Epochly JIT Backend Selection Logic

Intelligent selection of JIT compilation backends based on workload analysis.
Routes different types of functions to the most suitable JIT compiler.

Author: Epochly Development Team
"""

import logging
import ast
import sys
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from .base import JITBackend, FunctionProfile

logger = logging.getLogger(__name__)


class FunctionAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze function characteristics."""
    
    def __init__(self):
        self.has_loops = False
        self.has_numpy = False
        self.has_numerical = False
        self.has_list_comp = False
        self.has_recursion = False
        self.complexity = 0
        self.max_loop_depth = 0
        self.current_loop_depth = 0
        self.function_name = None
        self.has_dict_ops = False
        self.has_list_ops = False
        self.has_string_ops = False
    
    def visit_FunctionDef(self, node):
        if self.function_name is None:
            self.function_name = node.name
        self.generic_visit(node)
    
    def visit_For(self, node):
        self.has_loops = True
        self.current_loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.current_loop_depth)
        self.complexity += 3
        self.generic_visit(node)
        self.current_loop_depth -= 1
    
    def visit_While(self, node):
        self.has_loops = True
        self.current_loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.current_loop_depth)
        self.complexity += 3
        self.generic_visit(node)
        self.current_loop_depth -= 1
    
    def visit_ListComp(self, node):
        self.has_list_comp = True
        self.complexity += 2
        self.generic_visit(node)
    
    def visit_Call(self, node):
        # Check for NumPy usage
        if isinstance(node.func, ast.Attribute):
            if hasattr(node.func.value, 'id') and node.func.value.id in ['np', 'numpy']:
                self.has_numpy = True
                self.has_numerical = True
            # Check for string operations
            if node.func.attr in ['upper', 'lower', 'strip', 'split', 'join', 'replace']:
                self.has_string_ops = True
            # Check for list operations
            if node.func.attr in ['append', 'extend', 'pop', 'remove', 'sort']:
                self.has_list_ops = True
        elif isinstance(node.func, ast.Name):
            if node.func.id in ['sin', 'cos', 'exp', 'log', 'sqrt']:
                self.has_numerical = True
            # Check for recursion
            if node.func.id == self.function_name:
                self.has_recursion = True
            # Check for built-in data functions
            if node.func.id in ['dict', 'list', 'set', 'tuple', 'str']:
                self.has_dict_ops = True
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_BinOp(self, node):
        if isinstance(node.op, (ast.Mult, ast.Div, ast.Pow, ast.MatMult)):
            self.has_numerical = True
        self.generic_visit(node)
    
    def visit_Subscript(self, node):
        # Dictionary/list subscript operations
        if isinstance(node.ctx, ast.Store):
            self.has_dict_ops = True
        self.generic_visit(node)
    
    def visit_Dict(self, node):
        self.has_dict_ops = True
        self.generic_visit(node)


class WorkloadType(Enum):
    """Types of computational workloads for JIT selection."""
    NUMERICAL = "numerical"        # Heavy math, NumPy operations
    ALGORITHMIC = "algorithmic"    # Loops, conditionals, general computation
    DATA_PROCESSING = "data"       # List/dict operations, string processing
    MIXED = "mixed"               # Combination of above
    UNKNOWN = "unknown"           # Cannot determine workload type


@dataclass
class BackendSelection:
    """Result of JIT backend selection for a function."""
    
    primary_backend: Optional[JITBackend]
    fallback_backends: List[JITBackend]
    workload_type: WorkloadType
    confidence: float  # 0.0 to 1.0
    selection_reason: str
    
    @property
    def all_backends(self) -> List[JITBackend]:
        """Get all backends (primary + fallbacks) in priority order."""
        if self.primary_backend is None:
            return self.fallback_backends
        return [self.primary_backend] + self.fallback_backends


class JITSelector:
    """
    Intelligent JIT backend selector.
    
    Analyzes function characteristics and workload patterns to choose
    the most appropriate JIT compilation backend for optimal performance.
    """
    
    def __init__(self, available_backends: Optional[List[JITBackend]] = None, 
                 available_compilers: Optional[Dict[JITBackend, Any]] = None):
        """
        Initialize JIT selector.
        
        Args:
            available_backends: List of available JIT backends
                               If None, auto-detect available backends
            available_compilers: Dict of compiler instances (for testing)
        """
        if available_compilers:
            # Extract available backends from compiler dict
            self.available_backends = [b for b, c in available_compilers.items() if c.is_available()]
            self.compilers = available_compilers
        else:
            # Use provided backends or auto-detect if None
            if available_backends is None:
                self.available_backends = self._detect_available_backends()
            else:
                self.available_backends = available_backends
            self.compilers = {}
        
        self.selection_history: Dict[str, BackendSelection] = {}
        self.performance_history: Dict[str, Dict[JITBackend, float]] = {}
        self.custom_rules: List[Callable] = []
        
        # Selection criteria weights
        self.criteria_weights = {
            'numerical_ops': 0.3,
            'numpy_usage': 0.25,
            'loop_complexity': 0.2,
            'function_size': 0.15,
            'call_frequency': 0.1
        }
        
        logger.info(f"JIT selector initialized with backends: {[b.value for b in self.available_backends]}")
    
    def _detect_available_backends(self) -> List[JITBackend]:
        """
        Auto-detect which JIT backends are available in the environment.
        
        Returns:
            List of available JIT backends
        """
        available = []

        # Check Numba
        try:
            import numba
            available.append(JITBackend.NUMBA)
            logger.debug("Numba JIT backend detected")
        except ImportError:
            logger.debug("Numba not available")

        # Check Native (Python 3.13+)
        try:
            if sys.version_info >= (3, 13):
                available.append(JITBackend.NATIVE)
                logger.debug("Native JIT backend detected (Python 3.13+)")
        except Exception:
            logger.debug("Native JIT not available")

        # Check Pyston (only supports Python 3.7-3.10)
        if sys.version_info[:2] <= (3, 10):
            try:
                # Pyston-lite doesn't have an import, it's built into the runtime
                # Check if pyston_lite module exists
                try:
                    import pyston_lite
                    available.append(JITBackend.PYSTON)
                    logger.debug("Pyston JIT backend detected")
                except ImportError:
                    try:
                        import pyston_lite_autoload
                        available.append(JITBackend.PYSTON)
                        logger.debug("Pyston JIT backend detected (autoload)")
                    except ImportError:
                        logger.debug("Pyston not available")
            except Exception:
                logger.debug("Pyston not available")
        else:
            logger.debug("Pyston not supported on Python 3.11+ (pyston-lite 2.3.5 limitation)")
        
        # Check JAX
        try:
            import jax
            available.append(JITBackend.JAX)
            logger.debug("JAX JIT backend detected")
        except ImportError:
            logger.debug("JAX not available")
        
        if not available:
            logger.warning("No JIT backends available - JIT compilation disabled")
        
        return available
    
    def _analyze_function(self, func: Callable) -> FunctionProfile:
        """
        Analyze a function to create a profile for JIT selection.
        
        Args:
            func: Function to analyze
            
        Returns:
            FunctionProfile with analyzed characteristics
        """
        import ast
        import inspect
        
        # Handle partial functions and other callables
        if hasattr(func, '__name__'):
            func_name = func.__name__
        elif hasattr(func, 'func') and hasattr(func.func, '__name__'):
            # functools.partial case
            func_name = f"partial({func.func.__name__})"
        else:
            func_name = str(type(func).__name__)
        
        try:
            source = inspect.getsource(func)
            # Remove common leading whitespace to handle inline definitions
            import textwrap
            source = textwrap.dedent(source)
            tree = ast.parse(source)
            
            # Basic metrics
            source_lines = len(source.splitlines())
            
            # Analyze AST
            analyzer = FunctionAnalyzer()
            analyzer.visit(tree)
            
            profile = FunctionProfile(
                function_name=func_name,
                source_lines=source_lines,
                has_loops=analyzer.has_loops,
                has_numpy_usage=analyzer.has_numpy,
                has_numerical_ops=analyzer.has_numerical,
                has_list_comprehensions=analyzer.has_list_comp,
                complexity_score=analyzer.complexity,
                loop_depth=analyzer.max_loop_depth,
                has_recursion=analyzer.has_recursion,
                is_generator=inspect.isgeneratorfunction(func),
                is_async=inspect.iscoroutinefunction(func)
            )
            # Store analyzer attributes for data processing detection
            profile._analyzer_attrs = {
                'has_dict_ops': analyzer.has_dict_ops,
                'has_list_ops': analyzer.has_list_ops,
                'has_string_ops': analyzer.has_string_ops
            }
            
        except (OSError, TypeError):
            # Can't analyze - return minimal profile
            profile = FunctionProfile(
                function_name=func_name,
                jit_compatible=False,
                is_async=inspect.iscoroutinefunction(func),
                is_generator=inspect.isgeneratorfunction(func)
            )
        
        return profile
    
    def select_backend(self, func: Callable, profile: Optional[FunctionProfile] = None) -> BackendSelection:
        """
        Select the best JIT backend for a function.
        
        Args:
            func: Function to compile
            profile: Function profiling information (optional, will analyze if not provided)
            
        Returns:
            BackendSelection with recommended backend and alternatives
        """
        if profile is None:
            profile = self._analyze_function(func)
            
        func_name = profile.function_name
        
        # Check for async/generator functions - these can't be JIT compiled
        if profile.is_async or profile.is_generator:
            return BackendSelection(
                primary_backend=None,
                fallback_backends=[],
                workload_type=WorkloadType.UNKNOWN,
                confidence=0.0,
                selection_reason="Async/generator functions cannot be JIT compiled"
            )
        
        # Check if we have a cached selection
        if func_name in self.selection_history:
            cached_selection = self.selection_history[func_name]
            cached_selection = BackendSelection(
                primary_backend=cached_selection.primary_backend,
                fallback_backends=cached_selection.fallback_backends,
                workload_type=cached_selection.workload_type,
                confidence=cached_selection.confidence,
                selection_reason="Previously selected backend"
            )
            logger.debug(f"Using cached backend selection for {func_name}: {cached_selection.primary_backend.value}")
            return cached_selection
        
        # Check custom rules first
        for rule in self.custom_rules:
            try:
                custom_backend = rule(profile)
                if custom_backend is not None:
                    # Custom rule matched
                    selection = BackendSelection(
                        primary_backend=custom_backend,
                        fallback_backends=[b for b in self.available_backends if b != custom_backend],
                        workload_type=WorkloadType.UNKNOWN,
                        confidence=0.9,  # High confidence for custom rules
                        selection_reason="Custom rule match"
                    )
                    self.selection_history[func_name] = selection
                    return selection
            except Exception as e:
                logger.warning(f"Custom rule failed: {e}")
        
        # Analyze workload type
        workload_type = self._analyze_workload_type(profile)
        
        # Score each available backend
        backend_scores = {}
        for backend in self.available_backends:
            score = self._score_backend_for_workload(backend, workload_type, profile)
            backend_scores[backend] = score
        
        if not backend_scores:
            # No backends available
            selection = BackendSelection(
                primary_backend=None,
                fallback_backends=[],
                workload_type=workload_type,
                confidence=0.0,
                selection_reason="No JIT backends available"
            )
        else:
            # Sort backends by score
            sorted_backends = sorted(backend_scores.items(), key=lambda x: x[1], reverse=True)
            
            primary_backend, primary_score = sorted_backends[0]
            fallback_backends = [backend for backend, _ in sorted_backends[1:]]
            
            confidence = min(primary_score / 100.0, 1.0)  # Normalize to 0-1
            
            # Reduce confidence for mixed workloads
            if workload_type == WorkloadType.MIXED:
                confidence *= 0.8  # Cap at 0.8 for mixed workloads
            
            selection = BackendSelection(
                primary_backend=primary_backend,
                fallback_backends=fallback_backends,
                workload_type=workload_type,
                confidence=confidence,
                selection_reason=self._get_selection_reason(primary_backend, workload_type, profile)
            )
        
        # Cache the selection
        self.selection_history[func_name] = selection
        
        backend_name = selection.primary_backend.value if selection.primary_backend else "None"
        logger.info(f"Selected {backend_name} for {func_name} "
                   f"(workload: {workload_type.value}, confidence: {selection.confidence:.2f})")
        
        return selection
    
    def _determine_workload_type(self, profile: FunctionProfile) -> WorkloadType:
        """
        Determine workload type from function profile.
        Alias for _analyze_workload_type for backward compatibility.
        """
        return self._analyze_workload_type(profile)
    
    def _analyze_workload_type(self, profile: FunctionProfile) -> WorkloadType:
        """
        Analyze function profile to determine workload type.
        
        Args:
            profile: Function profiling information
            
        Returns:
            Detected workload type
        """
        score_numerical = 0
        score_algorithmic = 0
        score_data_processing = 0
        
        # Numerical indicators
        if profile.has_numpy_usage:
            score_numerical += 40
        if profile.has_numerical_ops:
            score_numerical += 20
        
        # Algorithmic indicators
        if profile.has_loops:
            score_algorithmic += 30
        if profile.source_lines > 20:
            score_algorithmic += 15
        
        # Data processing indicators
        if profile.has_list_comprehensions:
            score_data_processing += 25
        # Add detection for dict/list/string operations
        analyzer_attrs = getattr(profile, '_analyzer_attrs', {})
        if analyzer_attrs.get('has_dict_ops', False):
            score_data_processing += 20
        if analyzer_attrs.get('has_list_ops', False):
            score_data_processing += 15
        if analyzer_attrs.get('has_string_ops', False):
            score_data_processing += 15
        
        # Determine primary workload type
        max_score = max(score_numerical, score_algorithmic, score_data_processing)
        
        if max_score == 0:
            return WorkloadType.UNKNOWN
        
        # Check for mixed workload (multiple high scores)
        # Only consider it mixed if scores are close
        scores = [score_numerical, score_algorithmic, score_data_processing]
        scores.sort(reverse=True)
        
        # If top two scores are close (within 20%), it's mixed
        if scores[0] > 0 and scores[1] > 0:
            if scores[1] / scores[0] >= 0.8:  # Second highest is at least 80% of highest
                return WorkloadType.MIXED
        
        # Single dominant workload
        if score_numerical == max_score:
            return WorkloadType.NUMERICAL
        elif score_algorithmic == max_score:
            return WorkloadType.ALGORITHMIC
        else:
            return WorkloadType.DATA_PROCESSING
    
    def _score_backend_for_workload(self, backend: JITBackend, workload_type: WorkloadType, 
                                  profile: FunctionProfile) -> float:
        """
        Score how well a backend fits a workload.
        
        Args:
            backend: JIT backend to score
            workload_type: Type of workload
            profile: Function profiling information
            
        Returns:
            Score from 0-100 (higher is better)
        """
        base_score = 50.0  # Base compatibility score
        
        # Backend-specific scoring
        if backend == JITBackend.NUMBA:
            if workload_type == WorkloadType.NUMERICAL:
                base_score += 40
            elif workload_type == WorkloadType.ALGORITHMIC:
                base_score += 20
            elif workload_type == WorkloadType.DATA_PROCESSING:
                base_score += 10
            
            # Numba specific bonuses
            if profile.has_numpy_usage:
                base_score += 30
            if profile.has_loops:
                base_score += 10  # Reduced to make other backends more competitive
            if profile.has_numerical_ops:
                base_score += 15
        
        elif backend == JITBackend.PYSTON:
            if workload_type == WorkloadType.ALGORITHMIC:
                base_score += 35
            elif workload_type == WorkloadType.DATA_PROCESSING:
                base_score += 30
            elif workload_type == WorkloadType.NUMERICAL:
                base_score += 15
            
            # Pyston specific bonuses
            if profile.has_loops:
                base_score += 25
            if profile.source_lines > 10:
                base_score += 15
            if profile.call_count > 1000:  # Benefits from frequent calls
                base_score += 20
        
        elif backend == JITBackend.NATIVE:
            if workload_type == WorkloadType.ALGORITHMIC:
                base_score += 40  # Native is good for general algorithms
            elif workload_type == WorkloadType.DATA_PROCESSING:
                base_score += 30
            elif workload_type == WorkloadType.NUMERICAL:
                base_score += 20
            
            # Native JIT specific bonuses
            if profile.has_loops:
                base_score += 25
            if profile.complexity_score > 10:
                base_score += 15
        
        elif backend == JITBackend.JAX:
            # JAX excels at numerical/ML workloads
            if workload_type == WorkloadType.NUMERICAL:
                base_score += 45
            if profile.has_numpy_usage:
                base_score += 35
        
        # Performance history adjustment
        func_name = profile.function_name
        if func_name in self.performance_history:
            if backend in self.performance_history[func_name]:
                historical_performance = self.performance_history[func_name][backend]
                # Scale historical performance to adjustment factor
                adjustment = (historical_performance - 1.0) * 20  # 20 points per 1x speedup
                base_score += adjustment
        
        # Penalty for compatibility issues
        if not profile.jit_compatible:
            base_score *= 0.1  # Severe penalty
        
        # Penalty for recursion (JIT compilers often struggle with recursion)
        if profile.has_recursion:
            base_score *= 0.7  # 30% penalty for recursive functions
        
        return max(0.0, min(100.0, base_score))
    
    def _get_selection_reason(self, backend: JITBackend, workload_type: WorkloadType, 
                            profile: FunctionProfile) -> str:
        """
        Generate human-readable reason for backend selection.
        
        Args:
            backend: Selected backend
            workload_type: Detected workload type
            profile: Function profiling information
            
        Returns:
            Reason string for selection
        """
        reasons = []
        
        if backend == JITBackend.NUMBA:
            if profile.has_numpy_usage:
                reasons.append("NumPy operations detected")
            if workload_type == WorkloadType.NUMERICAL:
                reasons.append("numerical workload")
            if profile.has_loops:
                reasons.append("loop optimization")
        
        elif backend == JITBackend.PYSTON:
            if workload_type == WorkloadType.ALGORITHMIC:
                reasons.append("algorithmic workload")
            if profile.call_count > 500:
                reasons.append("high call frequency")
            if profile.source_lines > 15:
                reasons.append("complex function")
        
        base_reason = f"Best fit for {workload_type.value} workload"
        if reasons:
            return f"{base_reason} ({', '.join(reasons)})"
        else:
            return base_reason
    
    def update_performance_history(self, func_name: str, backend: JITBackend, 
                                 speedup: float) -> None:
        """
        Update performance history for backend selection learning.
        
        Args:
            func_name: Name of the function
            backend: Backend that was used
            speedup: Performance speedup achieved (1.0 = no improvement)
        """
        if func_name not in self.performance_history:
            self.performance_history[func_name] = {}
        
        self.performance_history[func_name][backend] = speedup
        
        logger.debug(f"Updated performance history: {func_name} + {backend.value} = {speedup:.2f}x speedup")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get JIT selector statistics.
        
        Returns:
            Dictionary with selection and performance metrics
        """
        backend_selections = {}
        for selection in self.selection_history.values():
            if selection.primary_backend:
                backend = selection.primary_backend.value
                backend_selections[backend] = backend_selections.get(backend, 0) + 1
            else:
                backend_selections['none'] = backend_selections.get('none', 0) + 1
        
        workload_types = {}
        for selection in self.selection_history.values():
            workload = selection.workload_type.value
            workload_types[workload] = workload_types.get(workload, 0) + 1
        
        return {
            'available_backends': [b.value for b in self.available_backends],
            'total_selections': len(self.selection_history),
            'backend_selections': backend_selections,
            'workload_distributions': workload_types,
            'functions_with_performance_history': len(self.performance_history)
        }
    
    def add_selection_rule(self, rule: Callable[[FunctionProfile], Optional[JITBackend]]) -> None:
        """
        Add a custom selection rule.
        
        Args:
            rule: Function that takes a FunctionProfile and returns a JITBackend or None
        """
        self.custom_rules.append(rule)