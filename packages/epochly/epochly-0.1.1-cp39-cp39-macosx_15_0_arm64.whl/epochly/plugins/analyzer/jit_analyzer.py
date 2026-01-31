"""
Epochly JIT Analysis Plugin

This analyzer plugin detects JIT compilation opportunities by identifying hot paths,
analyzing function characteristics, and determining optimal JIT backend selection.
Integrates with the existing workload detection infrastructure.

Author: Epochly Development Team
"""

import time
import threading
import inspect
import ast
from collections import defaultdict, deque
from typing import Dict, Any, List, Optional, Callable, Set, FrozenSet
from dataclasses import dataclass, field
from enum import Enum

from ..base_plugins import EpochlyAnalyzer, create_analyzer_metadata, PluginPriority


class JITSuitability(Enum):
    """JIT compilation suitability levels."""
    EXCELLENT = "excellent"      # >80% confidence, high benefit expected
    GOOD = "good"               # 60-80% confidence, moderate benefit
    MARGINAL = "marginal"       # 40-60% confidence, low benefit
    UNSUITABLE = "unsuitable"   # <40% confidence, not worth compiling


class JITBackendType(Enum):
    """Available JIT compilation backends (Multi-JIT Strategy 2025)."""
    NUMBA = "numba"            # Numerical computations (3.10-3.13)
    NATIVE = "native"          # Python 3.13+ built-in JIT
    PYSTON = "pyston"          # General Python optimization (3.7-3.10 ONLY)
    AUTO = "auto"              # Automatic selection


@dataclass
class FunctionCharacteristics:
    """Detailed characteristics of a function for JIT analysis."""
    
    name: str
    source_hash: str
    source_lines: int = 0
    
    # Code features
    has_loops: bool = False
    has_numerical_ops: bool = False
    has_numpy_usage: bool = False
    has_list_comprehensions: bool = False
    has_recursion: bool = False
    has_string_ops: bool = False
    
    # Complexity metrics
    cyclomatic_complexity: int = 1
    nesting_depth: int = 0
    operation_count: int = 0
    
    # Call patterns
    call_count: int = 0
    total_execution_time_ns: int = 0
    average_execution_time_ns: float = 0.0
    recent_calls: deque = field(default_factory=lambda: deque(maxlen=100))
    
    # JIT compatibility
    compatibility_issues: List[str] = field(default_factory=list)
    jit_suitability: JITSuitability = JITSuitability.UNSUITABLE
    recommended_backend: JITBackendType = JITBackendType.AUTO
    
    # Performance predictions
    estimated_speedup: float = 1.0
    compilation_cost_ms: float = 0.0
    break_even_calls: int = 0


@dataclass
class HotPathCandidate:
    """A function identified as a potential hot path for JIT compilation."""
    
    function_name: str
    characteristics: FunctionCharacteristics
    hot_path_score: float = 0.0
    detection_timestamp: float = field(default_factory=time.time)
    
    # Selection criteria scores
    frequency_score: float = 0.0
    execution_time_score: float = 0.0
    complexity_score: float = 0.0
    workload_match_score: float = 0.0
    
    @property
    def should_compile(self) -> bool:
        """Whether this candidate should be JIT compiled."""
        return (self.hot_path_score >= 60.0 and 
                self.characteristics.jit_suitability in [JITSuitability.EXCELLENT, JITSuitability.GOOD])


class JITAnalyzer(EpochlyAnalyzer):
    """
    Analyzer plugin for JIT compilation opportunity detection.

    Analyzes function call patterns, code characteristics, and workload types
    to identify optimal JIT compilation candidates and backend selection.
    """

    # Class-level constant: JIT-incompatible modules with standardized messages
    # All messages prefixed with "JIT-incompatible module" for critical disqualifier matching
    # Used by visit_Import, visit_ImportFrom, visit_Call, and bytecode analysis
    _JIT_INCOMPATIBLE_MODULES: Dict[str, str] = {
        'hashlib': "JIT-incompatible module 'hashlib': uses C extension modules",
        'json': "JIT-incompatible module 'json': uses dynamic string processing",
        'pickle': "JIT-incompatible module 'pickle': serialization not supported",
        'sqlite3': "JIT-incompatible module 'sqlite3': C library wrapper",
        'socket': "JIT-incompatible module 'socket': low-level networking",
        'subprocess': "JIT-incompatible module 'subprocess': process spawning",
        'multiprocessing': "JIT-incompatible module 'multiprocessing': process management",
        'threading': "JIT-incompatible module 'threading': thread management",
        'io': "JIT-incompatible module 'io': file operations",
        're': "JIT-incompatible module 're': regex operations",
        'csv': "JIT-incompatible module 'csv': CSV parsing",
        'xml': "JIT-incompatible module 'xml': XML processing",
        'html': "JIT-incompatible module 'html': HTML processing",
        'urllib': "JIT-incompatible module 'urllib': URL handling",
        'http': "JIT-incompatible module 'http': HTTP operations",
        'email': "JIT-incompatible module 'email': email processing",
        'logging': "JIT-incompatible module 'logging': logging operations",
        'pandas': "JIT-incompatible module 'pandas': DataFrame operations",
        'ctypes': "JIT-incompatible module 'ctypes': dynamic library loading",
        'cffi': "JIT-incompatible module 'cffi': dynamic library loading",
        'uuid': "JIT-incompatible module 'uuid': uses C extension modules",
    }
    _JIT_INCOMPATIBLE_MODULE_NAMES: FrozenSet[str] = frozenset(_JIT_INCOMPATIBLE_MODULES.keys())

    def __init__(self):
        metadata = create_analyzer_metadata(
            name="jit_analyzer",
            version="1.0.0",
            priority=PluginPriority.HIGH,
            capabilities=[
                "hot_path_detection",
                "jit_suitability_analysis", 
                "backend_selection",
                "performance_prediction",
                "compilation_planning"
            ]
        )
        super().__init__("jit_analyzer", "1.0.0", metadata)
        
        # Analysis state
        self._function_characteristics: Dict[str, FunctionCharacteristics] = {}
        self._hot_path_candidates: Dict[str, HotPathCandidate] = {}
        self._profiled_functions: Set[str] = set()
        self._lock = threading.RLock()
        
        # Configuration
        self._hot_path_threshold = 60.0
        self._min_calls_for_analysis = 10
        self._analysis_window_seconds = 30.0
        self._enable_adaptive_profiling = True
        self._profile_sample_rate = 0.1
        
        # Performance tracking
        self._sample_counters: Dict[str, int] = defaultdict(int)
        self._profiling_overhead_ns = 0
        self._total_profiled_calls = 0
        
        # Background analysis
        self._analysis_timer: Optional[threading.Timer] = None
        
    def _setup_plugin(self) -> None:
        """Setup JIT analysis resources."""
        self._logger.debug("Setting up JIT analyzer plugin")
        with self._lock:
            self._function_characteristics.clear()
            self._hot_path_candidates.clear()
            self._profiled_functions.clear()
        
        # Start background analysis
        self._start_background_analysis()
        
    def _teardown_plugin(self) -> None:
        """Teardown JIT analysis resources."""
        self._logger.debug("Tearing down JIT analyzer plugin")
        
        # Stop background analysis
        if self._analysis_timer:
            self._analysis_timer.cancel()
            self._analysis_timer = None
        
        with self._lock:
            self._function_characteristics.clear()
            self._hot_path_candidates.clear()
            self._profiled_functions.clear()
    
    def analyze_function(self, func: Callable, context: Optional[Dict[str, Any]] = None) -> FunctionCharacteristics:
        """
        Analyze a function for JIT compilation suitability.
        Uses recursive analysis to check entire call chain.

        Args:
            func: Function to analyze
            context: Optional analysis context

        Returns:
            FunctionCharacteristics with detailed analysis
        """
        func_name = getattr(func, '__name__', str(func))
        context = context or {}

        with self._lock:
            # Check if already analyzed
            if func_name in self._function_characteristics:
                return self._function_characteristics[func_name]

        # Perform recursive analysis to check entire call chain
        characteristics = self._analyze_function_with_recursion(func, visited=set(), depth=0)

        with self._lock:
            # Store characteristics
            self._function_characteristics[func_name] = characteristics

            self._logger.debug(f"Analyzed function {func_name}: "
                             f"suitability={characteristics.jit_suitability.value}, "
                             f"backend={characteristics.recommended_backend.value}")

            return characteristics

    def _analyze_function_with_recursion(
        self,
        func: Callable,
        visited: Optional[Set[str]] = None,
        depth: int = 0
    ) -> FunctionCharacteristics:
        """
        Recursively analyze function and its callees for JIT suitability.

        This enables JIT compilation for functions that call other user-defined
        functions, as long as the called functions are themselves JIT-compatible.

        Args:
            func: Function to analyze
            visited: Set of already-visited function names (cycle detection)
            depth: Current recursion depth (prevents runaway analysis)

        Returns:
            FunctionCharacteristics with recursive analysis results
        """
        import types

        if visited is None:
            visited = set()

        func_name = getattr(func, '__name__', str(func))

        # Prevent infinite recursion
        MAX_DEPTH = 10
        if depth > MAX_DEPTH:
            self._logger.debug(f"Max recursion depth reached analyzing {func_name}")
            characteristics = FunctionCharacteristics(
                name=func_name,
                source_hash=f"max_depth_{id(func)}"
            )
            characteristics.compatibility_issues.append(
                "Analysis depth limit reached - may have circular dependencies"
            )
            characteristics.jit_suitability = JITSuitability.UNSUITABLE
            return characteristics

        # Check memoization (without lock - we're already in recursive call)
        if func_name in self._function_characteristics:
            return self._function_characteristics[func_name]

        # Check for cycles
        if func_name in visited:
            self._logger.debug(f"Circular dependency detected: {func_name}")
            characteristics = FunctionCharacteristics(
                name=func_name,
                source_hash=f"circular_{id(func)}"
            )
            characteristics.compatibility_issues.append(
                "Circular function dependency detected"
            )
            characteristics.jit_suitability = JITSuitability.UNSUITABLE
            return characteristics

        visited.add(func_name)

        # Perform static analysis on this function
        characteristics = self._analyze_function_code_internal(func)

        # Extract called user-defined functions for recursive analysis
        if hasattr(func, '__globals__'):
            called_functions = self._extract_called_user_functions(func)

            for called_func_name, called_func in called_functions.items():
                if called_func is None:
                    continue

                # Skip if it's the same function (recursion handled by visited set)
                if called_func_name == func_name:
                    continue

                # Recursively analyze the called function
                called_characteristics = self._analyze_function_with_recursion(
                    called_func,
                    visited.copy(),  # Pass copy to allow different branches
                    depth + 1
                )

                # Propagate incompatibility up the call chain
                if called_characteristics.jit_suitability == JITSuitability.UNSUITABLE:
                    # Check if it's a hard blocker (I/O, eval, etc.) vs soft (just other calls)
                    hard_blockers = [
                        "I/O operation", "eval", "exec", "compile", "Dynamic",
                        "Generator", "Class definition", "JIT-incompatible module",
                        "Unsupported NumPy", "Unsupported SciPy"
                    ]
                    has_hard_blocker = any(
                        any(hb in issue for hb in hard_blockers)
                        for issue in called_characteristics.compatibility_issues
                    )

                    if has_hard_blocker:
                        # Propagate hard blockers as blocking issues
                        issue_summary = '; '.join(called_characteristics.compatibility_issues[:2])
                        characteristics.compatibility_issues.append(
                            f"Calls '{called_func_name}' with blocking issues: {issue_summary}"
                        )
                    else:
                        # Soft issues - note but don't necessarily block
                        self._logger.debug(
                            f"{func_name} calls {called_func_name} which has soft issues, "
                            f"allowing for potential JIT inlining"
                        )
                elif called_characteristics.jit_suitability == JITSuitability.MARGINAL:
                    # Marginal callee = slight penalty but not disqualifying
                    characteristics.compatibility_issues.append(
                        f"Calls marginally-suitable function '{called_func_name}'"
                    )

        # Remove the generic "user-defined function" issues that we've now analyzed
        characteristics.compatibility_issues = [
            issue for issue in characteristics.compatibility_issues
            if "Calls user-defined function" not in issue
            or any(name in issue for name in ["blocking issues", "marginally-suitable"])
        ]

        # Re-assess suitability with propagated issues
        self._assess_jit_suitability(characteristics)

        visited.discard(func_name)
        return characteristics

    def _extract_called_user_functions(self, func: Callable) -> Dict[str, Optional[Callable]]:
        """
        Extract user-defined functions called by this function.

        Args:
            func: Function to analyze

        Returns:
            Dict mapping function names to callable objects (or None if unresolvable)
        """
        import types

        called_functions: Dict[str, Optional[Callable]] = {}

        if not hasattr(func, '__globals__'):
            return called_functions

        func_globals = func.__globals__
        func_name = getattr(func, '__name__', '')

        # Safe modules whose functions we DON'T need to recursively analyze
        SAFE_MODULE_PREFIXES = (
            'numpy', 'numba', 'scipy', 'math', 'cmath',
            'builtins', '__builtin__', '_operator', 'operator',
            'functools', 'itertools', 'collections', 'random',
        )

        # Try AST-based extraction first (more reliable)
        try:
            source = inspect.getsource(func)
            import textwrap
            source = textwrap.dedent(source)
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        called_name = node.func.id
                        if called_name in func_globals:
                            obj = func_globals[called_name]
                            if isinstance(obj, (types.FunctionType, types.LambdaType)):
                                module = getattr(obj, '__module__', '') or ''
                                # Only include if NOT from a safe module
                                if not any(module.startswith(sm) for sm in SAFE_MODULE_PREFIXES):
                                    called_functions[called_name] = obj
        except (OSError, TypeError, SyntaxError):
            # Fall back to bytecode-based extraction
            if hasattr(func, '__code__'):
                code = func.__code__
                for name in code.co_names:
                    if name in func_globals:
                        obj = func_globals[name]
                        if isinstance(obj, (types.FunctionType, types.LambdaType)):
                            module = getattr(obj, '__module__', '') or ''
                            if not any(module.startswith(sm) for sm in SAFE_MODULE_PREFIXES):
                                called_functions[name] = obj

        return called_functions

    def _analyze_function_code_internal(self, func: Callable) -> FunctionCharacteristics:
        """
        Perform static analysis of function source code.
        
        Args:
            func: Function to analyze
            
        Returns:
            FunctionCharacteristics with static analysis results
        """
        if func is None:
            raise AttributeError("Cannot analyze None function")
            
        func_name = getattr(func, '__name__', str(func))
        
        try:
            # Get source code
            source = inspect.getsource(func)
            
            # Dedent the source to handle nested function definitions
            import textwrap
            source = textwrap.dedent(source)
            
            import hashlib
            source_hash = hashlib.md5(source.encode()).hexdigest()
            
            characteristics = FunctionCharacteristics(
                name=func_name,
                source_hash=source_hash,
                source_lines=len(source.splitlines())
            )
            
            # Parse AST for detailed analysis
            try:
                tree = ast.parse(source)
                # Debug: log what we're parsing
                self._logger.debug(f"Parsing source for {func_name}, first line: {source.splitlines()[0] if source else 'empty'}")
                # Pass function globals for user-defined function detection
                func_globals = getattr(func, '__globals__', {})
                self._analyze_ast(tree, characteristics, func_globals)
            except SyntaxError as e:
                characteristics.compatibility_issues.append(f"Cannot parse function syntax: {str(e)}")
                self._logger.warning(f"SyntaxError parsing {func_name}: {e}")
            
            # Determine JIT suitability
            self._assess_jit_suitability(characteristics)
            
            return characteristics
            
        except (OSError, TypeError) as e:
            # Cannot get source (built-in function, etc.)
            characteristics = FunctionCharacteristics(
                name=func_name,
                source_hash=f"builtin_{id(func)}"
            )
            
            # Enhanced analysis for functions without accessible source
            if hasattr(func, '__code__'):
                code = func.__code__
                characteristics.source_lines = code.co_firstlineno
                
                # Comprehensive bytecode analysis for JIT suitability
                import dis
                bytecode = dis.Bytecode(func)
                
                # Count different operation types
                loop_ops = numeric_ops = call_ops = 0
                operation_count = 0
                
                for instr in bytecode:
                    operation_count += 1
                    
                    # Loop detection
                    if instr.opname in ('FOR_ITER', 'JUMP_BACKWARD', 'JUMP_FORWARD', 'SETUP_LOOP'):
                        loop_ops += 1
                        characteristics.has_loops = True
                    
                    # Numerical operation detection
                    elif instr.opname in ('BINARY_ADD', 'BINARY_MULTIPLY', 'BINARY_SUBTRACT', 
                                        'BINARY_TRUE_DIVIDE', 'BINARY_FLOOR_DIVIDE', 'BINARY_POWER',
                                        'INPLACE_ADD', 'INPLACE_MULTIPLY', 'INPLACE_SUBTRACT'):
                        numeric_ops += 1
                        characteristics.has_numerical_ops = True
                    
                    # Function call detection
                    elif instr.opname in ('CALL_FUNCTION', 'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX'):
                        call_ops += 1
                    
                    # List comprehension detection
                    elif instr.opname in ('LIST_EXTEND', 'SET_UPDATE', 'DICT_UPDATE'):
                        characteristics.has_list_comprehensions = True

                    # JIT-incompatible module import detection (bytecode fallback)
                    # Uses class-level _JIT_INCOMPATIBLE_MODULE_NAMES for consistency
                    elif instr.opname == 'IMPORT_NAME':
                        imported_module = instr.argval if instr.argval else ''
                        base_module = imported_module.split('.')[0] if imported_module else ''
                        if base_module in JITAnalyzer._JIT_INCOMPATIBLE_MODULE_NAMES:
                            characteristics.compatibility_issues.append(
                                f"JIT-incompatible module '{base_module}': detected via bytecode analysis"
                            )

                # NUMPY DETECTION FIX (Dec 2025): Detect numpy usage from bytecode
                # When source code isn't available (e.g., notebooks, stdin), AST analysis fails
                # This fallback checks co_names and __globals__ to detect numpy imports
                if hasattr(code, 'co_names'):
                    numpy_aliases = {'np', 'numpy'}
                    for name in code.co_names:
                        if name in numpy_aliases:
                            # Verify it's actually numpy in globals (not shadowed)
                            if hasattr(func, '__globals__'):
                                global_val = func.__globals__.get(name)
                                if global_val is not None:
                                    # Check if it's numpy module
                                    if hasattr(global_val, '__name__') and 'numpy' in getattr(global_val, '__name__', ''):
                                        characteristics.has_numpy_usage = True
                                        characteristics.has_numerical_ops = True  # numpy implies numerical
                                        self._logger.debug(f"Bytecode analysis: detected numpy usage via {name}")
                                        break
                            else:
                                # No globals - assume it's numpy if name matches
                                characteristics.has_numpy_usage = True
                                characteristics.has_numerical_ops = True
                                break

                # CRITICAL: Detect user-defined function calls AND unsupported numpy patterns from bytecode
                # This handles Jupyter notebooks and exec() contexts where inspect.getsource() fails
                # We use func.__code__.co_names (all global names) and func.__globals__ to resolve callees
                user_defined_calls, unsupported_numpy_calls = self._detect_user_defined_calls_from_bytecode(func)

                # Add user-defined calls to compatibility issues
                for udf_name in user_defined_calls:
                    characteristics.compatibility_issues.append(
                        f"Calls user-defined function '{udf_name}' which is not JIT-compatible"
                    )

                # Add unsupported numpy patterns to compatibility issues
                for numpy_issue in unsupported_numpy_calls:
                    characteristics.compatibility_issues.append(numpy_issue)

                # Check for any critical issues (JIT-incompatible modules, user-defined calls, unsupported numpy)
                # This applies the same critical-issue gate as _assess_jit_suitability
                critical_issues = [
                    "JIT-incompatible module", "user-defined function",
                    "Unsupported NumPy", "Unsupported SciPy"
                ]
                has_critical = any(
                    critical in issue
                    for issue in characteristics.compatibility_issues
                    for critical in critical_issues
                )

                if has_critical or user_defined_calls or unsupported_numpy_calls:
                    characteristics.jit_suitability = JITSuitability.UNSUITABLE
                    characteristics.recommended_backend = JITBackendType.AUTO
                    all_issues = (user_defined_calls + unsupported_numpy_calls +
                                  [i for i in characteristics.compatibility_issues if "JIT-incompatible" in i])
                    self._logger.debug(
                        f"Bytecode analysis for {func_name}: UNSUITABLE due to incompatible patterns: {all_issues}"
                    )
                    # Skip score calculation - already unsuitable
                    characteristics.operation_count = operation_count
                    characteristics.cyclomatic_complexity = max(1, loop_ops + call_ops // 10)
                    characteristics.nesting_depth = loop_ops
                    return characteristics

                # Calculate complexity metrics
                characteristics.operation_count = operation_count
                characteristics.cyclomatic_complexity = max(1, loop_ops + call_ops // 10)
                characteristics.nesting_depth = loop_ops  # Approximation
                
                # Enhanced JIT suitability assessment for bytecode analysis
                suitability_score = 50.0  # Base score
                
                # Strong positive indicators
                if characteristics.has_loops:
                    suitability_score += 20.0
                if characteristics.has_numerical_ops:
                    suitability_score += 15.0
                if operation_count > 20:
                    suitability_score += 10.0
                if loop_ops > 1:  # Nested or multiple loops
                    suitability_score += 10.0
                
                # Set suitability based on score
                if suitability_score >= 85:
                    characteristics.jit_suitability = JITSuitability.EXCELLENT
                elif suitability_score >= 70:
                    characteristics.jit_suitability = JITSuitability.GOOD
                elif suitability_score >= 50:
                    characteristics.jit_suitability = JITSuitability.MARGINAL
                else:
                    characteristics.jit_suitability = JITSuitability.UNSUITABLE
                
                # Backend recommendation
                if characteristics.has_numerical_ops or loop_ops > 0:
                    characteristics.recommended_backend = JITBackendType.NUMBA
                else:
                    characteristics.recommended_backend = JITBackendType.AUTO
                
                # Performance estimation
                if characteristics.jit_suitability == JITSuitability.EXCELLENT:
                    characteristics.estimated_speedup = 2.0 + (suitability_score / 100.0) * 3.0
                elif characteristics.jit_suitability == JITSuitability.GOOD:
                    characteristics.estimated_speedup = 1.5 + (suitability_score / 100.0) * 1.0
                elif characteristics.jit_suitability == JITSuitability.MARGINAL:
                    characteristics.estimated_speedup = 1.1 + (suitability_score / 100.0) * 0.4
                
                self._logger.debug(f"Bytecode analysis for {func_name}: score={suitability_score:.1f}, "
                                 f"loops={loop_ops}, numeric_ops={numeric_ops}, operations={operation_count}")
                
            else:
                characteristics.compatibility_issues.append(f"Source not available: {e}")
                characteristics.jit_suitability = JITSuitability.UNSUITABLE
                
            return characteristics
    
    def _analyze_ast(self, tree: ast.AST, characteristics: FunctionCharacteristics,
                     func_globals: Optional[Dict[str, Any]] = None) -> None:
        """
        Analyze AST to extract function characteristics.

        Args:
            tree: AST tree of the function
            characteristics: Characteristics object to populate
            func_globals: Optional dict of function's global namespace for user-defined function detection
        """
        # Known safe functions that are JIT-compatible (builtins, numpy, math, numba)
        KNOWN_SAFE_FUNCTIONS: Set[str] = {
            # Python builtins that Numba supports
            'abs', 'all', 'any', 'bool', 'complex', 'divmod', 'enumerate', 'filter',
            'float', 'hash', 'int', 'iter', 'len', 'list', 'map', 'max', 'min',
            'next', 'pow', 'range', 'reversed', 'round', 'set', 'slice', 'sorted',
            'str', 'sum', 'tuple', 'type', 'zip',
            # Math functions
            'acos', 'acosh', 'asin', 'asinh', 'atan', 'atan2', 'atanh', 'ceil',
            'copysign', 'cos', 'cosh', 'degrees', 'erf', 'erfc', 'exp', 'expm1',
            'fabs', 'factorial', 'floor', 'fmod', 'frexp', 'gamma', 'gcd', 'hypot',
            'isfinite', 'isinf', 'isnan', 'ldexp', 'lgamma', 'log', 'log10', 'log1p',
            'log2', 'modf', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh', 'trunc',
            # NumPy array creation (commonly used inline)
            'array', 'zeros', 'ones', 'empty', 'arange', 'linspace', 'logspace',
            'zeros_like', 'ones_like', 'empty_like', 'full', 'full_like',
            # NumPy math operations
            'dot', 'matmul', 'mean', 'std', 'var', 'median', 'percentile',
            'argmax', 'argmin', 'argsort', 'sort', 'cumsum', 'cumprod',
            'reshape', 'flatten', 'ravel', 'transpose', 'swapaxes',
            'concatenate', 'stack', 'vstack', 'hstack', 'dstack',
            'split', 'vsplit', 'hsplit', 'dsplit',
            'where', 'clip', 'copy', 'astype', 'asarray', 'ascontiguousarray',
            # Numba specific
            'prange', 'njit', 'jit', 'vectorize', 'guvectorize',
            # Common utility functions
            'isinstance', 'issubclass', 'callable', 'hasattr', 'getattr', 'setattr',
            'id', 'repr', 'ascii', 'bin', 'oct', 'hex', 'ord', 'chr',
        }

        # Safe modules whose functions are JIT-compatible
        # Used for detecting module.func() calls to user-defined functions
        # NOTE: pandas/pd intentionally EXCLUDED - pandas is JIT-incompatible
        SAFE_MODULES: Set[str] = {
            'builtins', 'numpy', 'np', 'numba', 'math', 'cmath', 'operator',
            'functools', 'itertools', 'collections', 'random', 'scipy',
            'sklearn', 'torch', 'tensorflow', 'tf',
        }

        class AnalysisVisitor(ast.NodeVisitor):
            def __init__(self, chars: FunctionCharacteristics, func_globals: Optional[Dict[str, Any]] = None):
                self.chars = chars
                self.func_globals = func_globals or {}
                self.nesting_level = 0
                self.max_nesting = 0
                
            def visit_For(self, node):
                self.chars.has_loops = True
                self.chars.operation_count += 1
                self.nesting_level += 1
                self.max_nesting = max(self.max_nesting, self.nesting_level)
                self.generic_visit(node)
                self.nesting_level -= 1
                
            def visit_While(self, node):
                self.chars.has_loops = True
                self.chars.operation_count += 1
                self.nesting_level += 1
                self.max_nesting = max(self.max_nesting, self.nesting_level)
                self.generic_visit(node)
                self.nesting_level -= 1
                
            def visit_ListComp(self, node):
                self.chars.has_list_comprehensions = True
                self.chars.operation_count += 1
                self.generic_visit(node)
                
            def visit_BinOp(self, node):
                if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow)):
                    self.chars.has_numerical_ops = True
                self.chars.operation_count += 1
                self.generic_visit(node)
                
            def visit_Import(self, node):
                # Check for numpy imports and JIT-incompatible modules
                # Uses class-level JITAnalyzer._JIT_INCOMPATIBLE_MODULES for consistency
                for alias in node.names:
                    if alias.name in ['numpy', 'np']:
                        self.chars.has_numpy_usage = True
                    # Check for JIT-incompatible module imports
                    elif alias.name in JITAnalyzer._JIT_INCOMPATIBLE_MODULES:
                        self.chars.compatibility_issues.append(
                            JITAnalyzer._JIT_INCOMPATIBLE_MODULES[alias.name]
                        )
                self.generic_visit(node)
                
            def visit_ImportFrom(self, node):
                # Uses class-level JITAnalyzer._JIT_INCOMPATIBLE_MODULES for consistency
                if node.module:
                    # Check for numpy imports
                    if 'numpy' in node.module or 'np' in node.module:
                        self.chars.has_numpy_usage = True

                    # Check for JIT-incompatible module imports (handles submodules too)
                    # e.g., "from hashlib import sha256" or "from xml.etree import ElementTree"
                    base_module = node.module.split('.')[0]
                    if base_module in JITAnalyzer._JIT_INCOMPATIBLE_MODULES:
                        self.chars.compatibility_issues.append(
                            JITAnalyzer._JIT_INCOMPATIBLE_MODULES[base_module]
                        )
                self.generic_visit(node)
                
            def visit_Call(self, node):
                # Check for NumPy usage
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        base_name = node.func.value.id
                        attr_name = node.func.attr

                        if base_name in ['np', 'numpy']:
                            self.chars.has_numpy_usage = True

                            # Check for unsupported NumPy functions
                            unsupported_numpy = ['argwhere', 'as_strided', 'choose', 'lexsort',
                                               'nonzero', 'partition', 'busday_offset', 'busday_count']
                            if attr_name in unsupported_numpy:
                                self.chars.compatibility_issues.append(f"Unsupported NumPy function: numpy.{attr_name}")

                            # Check for limited support functions
                            limited_numpy = ['permutation', 'searchsorted', 'digitize']
                            if attr_name in limited_numpy:
                                self.chars.compatibility_issues.append(f"Limited NumPy support: numpy.{attr_name} may have restrictions")

                        # CRITICAL FIX: Detect module.func() calls to user-defined functions
                        # This catches patterns like: feature_utils.compute_features(x)
                        elif self.func_globals and base_name not in SAFE_MODULES:
                            base_obj = self.func_globals.get(base_name)
                            if base_obj is not None:
                                # Check if it's a module containing user-defined functions
                                import types
                                if isinstance(base_obj, types.ModuleType):
                                    # CRITICAL: Check if module itself is JIT-incompatible
                                    # This catches module-level imports like: import hashlib
                                    # When function uses: hashlib.sha256()
                                    # Uses class-level _JIT_INCOMPATIBLE_MODULE_NAMES plus runtime-only modules
                                    runtime_incompatible = JITAnalyzer._JIT_INCOMPATIBLE_MODULE_NAMES | {
                                        'datetime', 'os', 'sys', 'struct'  # Additional runtime-detected modules
                                    }

                                    # Get the actual module name (handles aliased imports)
                                    module_name = getattr(base_obj, '__name__', base_name)
                                    base_module_name = module_name.split('.')[0]

                                    if base_module_name in runtime_incompatible:
                                        self.chars.compatibility_issues.append(
                                            f"JIT-incompatible module '{base_module_name}': runtime usage detected"
                                        )
                                    else:
                                        # Not a known incompatible module - check for user-defined functions
                                        # Get the attribute from the module
                                        attr_obj = getattr(base_obj, attr_name, None)
                                        if attr_obj is not None and callable(attr_obj):
                                            # Check if it's a user-defined function in the module
                                            is_user_defined = isinstance(attr_obj, (types.FunctionType, types.LambdaType))
                                            is_safe_module = getattr(attr_obj, '__module__', '') in SAFE_MODULES

                                            if is_user_defined and not is_safe_module:
                                                self.chars.compatibility_issues.append(
                                                    f"Calls user-defined function '{base_name}.{attr_name}' which is not JIT-compatible"
                                                )

                    # Check for dictionary mutation methods
                    if node.func.attr in ['pop', 'popitem', 'update', 'clear', 'setdefault']:
                        self.chars.compatibility_issues.append(f"Dictionary mutation method '{node.func.attr}' is not JIT-compatible")

                    # Check for string operations
                    if node.func.attr in ['join', 'split', 'replace', 'format']:
                        self.chars.has_string_ops = True
                        
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id

                    if func_name in ['array', 'zeros', 'ones', 'arange']:
                        self.chars.has_numpy_usage = True

                    # Check for recursion
                    if func_name == self.chars.name:
                        self.chars.has_recursion = True

                    # Check for JIT-incompatible built-in functions
                    incompatible_builtins = ['eval', 'exec', 'compile', 'globals', 'locals',
                                           'vars', 'dir', 'help', 'input', '__import__']
                    if func_name in incompatible_builtins:
                        self.chars.compatibility_issues.append(f"Uses JIT-incompatible function: {func_name}")

                    # Check for I/O functions
                    io_functions = ['print', 'open', 'input']
                    if func_name in io_functions:
                        self.chars.compatibility_issues.append(f"I/O operation '{func_name}' limits JIT optimization")

                    # CRITICAL: Check for calls to user-defined functions
                    # These cause Numba TypingError at runtime because Numba can't type them
                    # This is the root cause of notebook crashes when Epochly tries to JIT-compile
                    # functions that call other user-defined functions
                    #
                    # FIX: Check bound object FIRST, not just the name. This catches shadowing
                    # e.g., user defines their own `mean` function that shadows numpy.mean

                    if (func_name != self.chars.name and  # Not recursion (already handled)
                        func_name not in incompatible_builtins and
                        func_name not in io_functions):

                        # Check if this is a user-defined function in the function's globals
                        if self.func_globals:
                            global_value = self.func_globals.get(func_name)
                            if global_value is not None and callable(global_value):
                                import types
                                import builtins

                                # User-defined functions are types.FunctionType or LambdaType
                                is_user_defined = isinstance(global_value, (types.FunctionType, types.LambdaType))

                                if is_user_defined:
                                    # CRITICAL: Check bound object's module, not just the name
                                    # This catches cases where user shadows 'mean', 'sum', etc.
                                    obj_module = getattr(global_value, '__module__', '')

                                    # Only trust it if it's actually from a safe module
                                    is_from_safe_module = obj_module in SAFE_MODULES or obj_module.startswith(('numpy', 'numba', 'scipy'))

                                    # Also check if it's a builtin (different check)
                                    is_builtin = isinstance(global_value, types.BuiltinFunctionType)

                                    if not is_from_safe_module and not is_builtin:
                                        self.chars.compatibility_issues.append(
                                            f"Calls user-defined function '{func_name}' which is not JIT-compatible"
                                        )

                self.chars.operation_count += 1
                self.generic_visit(node)
                
            def visit_If(self, node):
                self.chars.cyclomatic_complexity += 1
                self.nesting_level += 1
                self.max_nesting = max(self.max_nesting, self.nesting_level)
                self.generic_visit(node)
                self.nesting_level -= 1
                
            def visit_Subscript(self, node):
                # Detect dynamic dictionary access (JIT incompatible for Numba)
                # Note: We can't reliably distinguish between array and dict access without type info
                # Only flag if we have strong indicators it's a dictionary
                
                # Check if the subscript target looks like a dictionary
                is_likely_dict = False
                if isinstance(node.value, ast.Name):
                    # If the variable name suggests it's a dict
                    name = node.value.id
                    if any(hint in name.lower() for hint in ['dict', 'map', 'cache', 'lookup']):
                        is_likely_dict = True
                elif isinstance(node.value, ast.Call):
                    # If it's a dict() call or similar
                    if isinstance(node.value.func, ast.Name) and node.value.func.id == 'dict':
                        is_likely_dict = True
                
                # Only flag dynamic access for likely dictionaries
                if is_likely_dict and not isinstance(node.slice, ast.Constant):
                    self.chars.compatibility_issues.append("Dynamic dictionary key access detected")
                
                self.chars.operation_count += 1
                self.generic_visit(node)
                
            def visit_Yield(self, node):
                # Generators are not supported in Numba nopython mode
                self.chars.compatibility_issues.append("Generator functions (yield) are not JIT-compatible")
                self.generic_visit(node)
                
            def visit_YieldFrom(self, node):
                # Yield from is also incompatible
                self.chars.compatibility_issues.append("Generator delegation (yield from) is not JIT-compatible")
                self.generic_visit(node)
                
            def visit_Global(self, node):
                # Global variable modifications can be problematic
                for name in node.names:
                    self.chars.compatibility_issues.append(f"Global variable '{name}' usage may limit JIT optimization")
                self.generic_visit(node)
                
            def visit_Nonlocal(self, node):
                # Nonlocal closures with mutations are problematic
                for name in node.names:
                    self.chars.compatibility_issues.append(f"Nonlocal variable '{name}' may cause closure issues")
                self.generic_visit(node)
                
            def visit_Try(self, node):
                # Exception handling has overhead
                self.chars.cyclomatic_complexity += len(node.handlers) + 1
                self.generic_visit(node)
                
            def visit_ClassDef(self, node):
                # Class definitions inside functions are incompatible
                self.chars.compatibility_issues.append("Class definition inside function is not JIT-compatible")
                self.generic_visit(node)

            def visit_FunctionDef(self, node):
                # CRITICAL FIX: Nested function definitions are not JIT-compatible
                # This catches patterns like:
                #   def outer(x):
                #       def inner(y): return y * 2
                #       return inner(x)
                # If this is the top-level function being analyzed, skip (nesting_level == 0)
                # But if we're inside the function (nesting_level > 0), it's a nested def
                if self.nesting_level > 0 or len([n for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]) > 1:
                    self.chars.compatibility_issues.append(
                        f"Nested function definition '{node.name}' is not JIT-compatible (calls user-defined function)"
                    )
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node):
                # Async function definitions are not JIT-compatible
                self.chars.compatibility_issues.append(
                    f"Async function definition '{node.name}' is not JIT-compatible"
                )
                self.generic_visit(node)

            def visit_Lambda(self, node):
                # Lambda functions may have limitations
                self.chars.operation_count += 1
                self.generic_visit(node)
                
            def visit_DictComp(self, node):
                # Dictionary comprehensions may have limitations
                self.chars.has_list_comprehensions = True  # Treat similarly
                self.chars.operation_count += 1
                self.generic_visit(node)
                
            def visit_SetComp(self, node):
                # Set comprehensions
                self.chars.has_list_comprehensions = True
                self.chars.operation_count += 1
                self.generic_visit(node)
                
            def visit_GeneratorExp(self, node):
                # Generator expressions are problematic
                self.chars.compatibility_issues.append("Generator expressions are not fully JIT-compatible")
                self.generic_visit(node)
                
            def visit_With(self, node):
                # Context managers may indicate I/O operations
                self.chars.operation_count += 1
                # Check for file operations
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        if isinstance(item.context_expr.func, ast.Name) and item.context_expr.func.id == 'open':
                            self.chars.compatibility_issues.append("File I/O operations are not JIT-optimizable")
                self.generic_visit(node)
        
        visitor = AnalysisVisitor(characteristics, func_globals)
        visitor.visit(tree)
        characteristics.nesting_depth = visitor.max_nesting

    def _detect_user_defined_calls_from_bytecode(self, func: Callable) -> List[str]:
        """
        Detect user-defined function calls using comprehensive bytecode stack analysis.

        This is used when inspect.getsource() fails (Jupyter notebooks, exec(), python -c).
        Uses symbolic stack simulation to accurately identify call targets, handling:
        - Direct function calls: foo()
        - Attribute chains: utils.submodule.func()
        - Closure variables: captured_func()
        - Method calls: obj.method()

        Based on mcp-reflect design for production-grade detection.

        Args:
            func: Function to analyze

        Returns:
            List of user-defined function names that are called
        """
        import dis
        import types
        import builtins as builtins_module

        user_defined_calls: List[str] = []
        unsupported_numpy_calls: List[str] = []

        if not hasattr(func, '__code__') or not hasattr(func, '__globals__'):
            return user_defined_calls, unsupported_numpy_calls

        code = func.__code__
        func_globals = func.__globals__
        func_closure = func.__closure__
        func_name = getattr(func, '__name__', '')

        # Safe modules - functions from these won't cause TypingError (frozenset for O(1) lookup)
        # NOTE: numpy.fft, numpy.random, numpy.linalg are NOT safe for Numba (most functions unsupported)
        SAFE_MODULES = frozenset({
            'numpy', 'numba', 'scipy', 'math', 'cmath',
            'builtins', '__builtin__', '_operator', 'operator',
            'functools', 'itertools', 'collections',
            'numpy.core',  # Core numpy array operations are generally supported
            'scipy.special',  # Many scipy.special functions have numba implementations
        })

        # Unsupported NumPy submodule patterns for Numba JIT compilation
        # Format: {(base, submodule): {function1, function2, ...} or '*' for all}
        # These will be flagged even though they're "safe" numpy functions
        UNSUPPORTED_NUMPY_PATTERNS = {
            # np.fft.* - FFT functions not supported by Numba
            ('numpy', 'fft'): {'*'},
            ('np', 'fft'): {'*'},
            # np.linalg.* - Most linalg functions not supported by Numba
            ('numpy', 'linalg'): {'eig', 'eigvals', 'svd', 'qr', 'cholesky', 'lstsq', 'solve'},
            ('np', 'linalg'): {'eig', 'eigvals', 'svd', 'qr', 'cholesky', 'lstsq', 'solve'},
            # np.random.* - Most random functions not supported by Numba
            ('numpy', 'random'): {'*'},
            ('np', 'random'): {'*'},
            # scipy.fft.* - FFT functions not supported
            ('scipy', 'fft'): {'*'},
            # scipy.linalg.* - Many linalg functions not supported
            ('scipy', 'linalg'): {'eig', 'eigvals', 'svd', 'qr', 'lu', 'cholesky'},
            # scipy.signal.* - Signal processing functions not supported
            ('scipy', 'signal'): {'*'},
        }

        # Safe module prefixes - functions from modules starting with these won't cause TypingError
        SAFE_MODULE_PREFIXES = (
            'numpy', 'numba', 'scipy', 'math', 'cmath',
            'builtins', '__builtin__', '_operator', 'operator',
            'functools', 'itertools', 'collections', 'random',
        )

        # Maximum recursion depth for descriptor resolution (prevents infinite loops)
        MAX_RESOLVE_DEPTH = 20

        def _extract_attribute_chain(desc: tuple) -> Optional[tuple]:
            """Extract full attribute chain from a stack descriptor.

            Examples:
                ('global', 'np') -> ('np',)
                ('attr', ('global', 'np'), 'fft') -> ('np', 'fft')
                ('attr', ('attr', ('global', 'np'), 'fft'), 'rfft') -> ('np', 'fft', 'rfft')

            Args:
                desc: Stack descriptor tuple

            Returns:
                Tuple of names in the chain, or None if not an attribute chain
            """
            if not desc or not isinstance(desc, tuple):
                return None

            kind = desc[0]

            if kind == 'global':
                return (desc[1],)
            elif kind == 'freevar':
                return (desc[1],)
            elif kind == 'attr':
                base_desc, attr_name = desc[1], desc[2]
                base_chain = _extract_attribute_chain(base_desc)
                if base_chain:
                    return base_chain + (attr_name,)
                return (attr_name,)

            return None

        def _check_unsupported_numpy_pattern(desc: tuple) -> Optional[str]:
            """Check if a descriptor represents an unsupported NumPy submodule function.

            Checks attribute chains like np.fft.rfft against UNSUPPORTED_NUMPY_PATTERNS.

            Args:
                desc: Stack descriptor tuple (callee before CALL)

            Returns:
                Error message if unsupported pattern found, None otherwise
            """
            chain = _extract_attribute_chain(desc)
            if not chain or len(chain) < 3:
                return None

            # Check for patterns like np.fft.rfft (base.submodule.func)
            base = chain[0]  # e.g., 'np' or 'numpy'
            submodule = chain[1]  # e.g., 'fft'
            func = chain[2]  # e.g., 'rfft'

            key = (base, submodule)
            if key in UNSUPPORTED_NUMPY_PATTERNS:
                denied_funcs = UNSUPPORTED_NUMPY_PATTERNS[key]
                # '*' means all functions in that submodule are unsupported
                if '*' in denied_funcs or func in denied_funcs:
                    return f"Unsupported NumPy/SciPy function for Numba: {'.'.join(chain[:3])}"

            return None

        def _resolve_descriptor(desc: tuple, depth: int = 0) -> Any:
            """Resolve a stack descriptor to an actual Python object.

            Args:
                desc: Stack descriptor tuple
                depth: Current recursion depth (for cycle protection)

            Returns:
                Resolved Python object or None if unresolvable
            """
            # Guard against circular attribute chains
            if depth > MAX_RESOLVE_DEPTH:
                return None

            if not desc or not isinstance(desc, tuple):
                return None

            kind = desc[0]

            if kind == 'global':
                name = desc[1]
                # Try globals first
                if name in func_globals:
                    return func_globals[name]
                # Fall back to builtins
                return getattr(builtins_module, name, None)

            elif kind == 'freevar':
                name = desc[1]
                if not func_closure:
                    return None
                freevars = code.co_freevars
                try:
                    idx = freevars.index(name)
                    cell = func_closure[idx]
                    return cell.cell_contents
                except (ValueError, IndexError, AttributeError, NameError):
                    # NameError: cell contents may be uninitialized
                    return None

            elif kind == 'attr':
                base_desc, attr_name = desc[1], desc[2]
                base_obj = _resolve_descriptor(base_desc, depth + 1)
                if base_obj is None:
                    return None
                return getattr(base_obj, attr_name, None)

            # 'other' or anything else
            return None

        def _is_user_defined_callable(obj: Any) -> bool:
            """Check if object is a user-defined callable that would cause TypingError.

            CRITICAL: This must also detect already-JIT-compiled functions (Numba Dispatchers)
            because calling a JIT-compiled function from another JIT-compiled function can
            cause type propagation issues (e.g., dict return types becoming ndarray).

            The issue: If function A calls function B, and B returns a dict, but B gets
            JIT-compiled first, then when we analyze A, we see B as a CPUDispatcher.
            If we don't detect this, A gets JIT-compiled and the dict return from B
            becomes an ndarray due to Numba's type inference, causing AttributeError
            when downstream code calls .keys() on what should be a dict.
            """
            if obj is None or not callable(obj):
                return False

            # Exclude builtins
            if isinstance(obj, types.BuiltinFunctionType):
                return False

            # CRITICAL: Detect already-JIT-compiled Numba functions
            # These are CPUDispatcher or similar Dispatcher subclasses
            # Calling a JIT function from another JIT function can cause type issues
            try:
                from numba.core.dispatcher import Dispatcher
                if isinstance(obj, Dispatcher):
                    # Already JIT-compiled - treat as user-defined to prevent
                    # cascading JIT compilation that causes type mismatch issues
                    return True
            except ImportError:
                pass  # Numba not available

            # Only treat plain Python functions / lambdas as "user-defined"
            if not isinstance(obj, (types.FunctionType, types.LambdaType)):
                return False

            mod = getattr(obj, '__module__', '') or ''

            # From a "safe" module?
            if mod in SAFE_MODULES:
                return False
            if mod.startswith(SAFE_MODULE_PREFIXES):
                return False

            return True

        def _get_callee_name(desc: tuple, obj: Any) -> str:
            """Get a human-readable name for the callee."""
            if obj is not None:
                name = getattr(obj, '__name__', None)
                if name:
                    return name

            if desc and isinstance(desc, tuple):
                kind = desc[0]
                if kind == 'global':
                    return desc[1]
                elif kind == 'freevar':
                    return desc[1]
                elif kind == 'attr':
                    base_desc, attr_name = desc[1], desc[2]
                    base_name = _get_callee_name(base_desc, None)
                    if base_name:
                        return f"{base_name}.{attr_name}"
                    return attr_name

            return repr(obj) if obj else '<unknown>'

        def _check_callee(desc: tuple) -> None:
            """Check if callee is user-defined or uses unsupported NumPy submodules."""
            # FIRST: Check for unsupported NumPy submodule patterns
            # This catches np.fft.rfft, np.linalg.eig, etc. which are NOT Numba-compatible
            numpy_error = _check_unsupported_numpy_pattern(desc)
            if numpy_error:
                if numpy_error not in unsupported_numpy_calls:
                    unsupported_numpy_calls.append(numpy_error)
                return  # Don't also check user-defined (it's a numpy function)

            # THEN: Check for user-defined functions
            obj = _resolve_descriptor(desc)
            if _is_user_defined_callable(obj):
                name = _get_callee_name(desc, obj)
                # Skip self-recursion
                if name != func_name and name not in user_defined_calls:
                    user_defined_calls.append(name)

        # Symbolic stack simulation
        # Descriptors: ('global', name), ('freevar', name), ('attr', base_desc, attr_name), ('other', None)
        stack: List[tuple] = []

        try:
            instructions = list(dis.get_instructions(code))
        except Exception:
            return user_defined_calls, unsupported_numpy_calls

        for instr in instructions:
            op = instr.opname

            # Load operations - push descriptors onto stack
            if op == 'LOAD_GLOBAL':
                # Python 3.11+: arg & 1 means push NULL first (for function calls)
                # This is critical for correct stack simulation!
                # See: https://docs.python.org/3/library/dis.html#opcode-LOAD_GLOBAL
                if instr.arg is not None and (instr.arg & 1):
                    stack.append(('other', None))  # NULL placeholder for call
                stack.append(('global', instr.argval))

            elif op in ('LOAD_DEREF', 'LOAD_CLASSDEREF'):
                # Free / cell variable (closure)
                # LOAD_CLASSDEREF is like LOAD_DEREF but checks class namespace first
                stack.append(('freevar', instr.argval))

            elif op == 'LOAD_ATTR':
                # Attribute access: base.attr - pushes 1 item
                base = stack.pop() if stack else ('other', None)
                stack.append(('attr', base, instr.argval))

            elif op == 'LOAD_METHOD':
                # Method access: base.method - pushes 2 items (NULL + method) or (self + method)
                # See: https://docs.python.org/3/library/dis.html#opcode-LOAD_METHOD
                base = stack.pop() if stack else ('other', None)
                stack.append(('other', None))  # NULL placeholder (or self for bound methods)
                stack.append(('attr', base, instr.argval))  # The method itself

            elif op in ('LOAD_FAST', 'LOAD_CONST', 'LOAD_CLOSURE', 'LOAD_NAME'):
                stack.append(('other', None))

            elif op == 'PUSH_NULL':
                # Python 3.11+ pushes NULL before function for consistency with CALL
                stack.append(('other', None))

            # Call operations - check callee and pop from stack
            elif op == 'CALL_FUNCTION':
                nargs = instr.argval or 0
                # Pop argument values
                for _ in range(nargs):
                    if stack:
                        stack.pop()
                # Pop and check callee
                callee_desc = stack.pop() if stack else None
                _check_callee(callee_desc)
                # Push result placeholder
                stack.append(('other', None))

            elif op == 'CALL_FUNCTION_KW':
                nargs = instr.argval or 0
                # Top of stack: tuple of keyword names
                if stack:
                    stack.pop()  # kw names tuple
                for _ in range(nargs):
                    if stack:
                        stack.pop()
                callee_desc = stack.pop() if stack else None
                _check_callee(callee_desc)
                stack.append(('other', None))

            elif op == 'CALL_FUNCTION_EX':
                flags = instr.argval or 0
                # Layout: ..., func, *args, (**kwargs if flags & 0x01)
                if flags & 0x01 and stack:
                    stack.pop()  # kwargs mapping
                if stack:
                    stack.pop()  # args iterable
                callee_desc = stack.pop() if stack else None
                _check_callee(callee_desc)
                stack.append(('other', None))

            elif op == 'CALL_METHOD':
                nargs = instr.argval or 0
                # Pop arguments
                for _ in range(nargs):
                    if stack:
                        stack.pop()
                # LOAD_METHOD pushed 2 items: (NULL/self, method)
                # Pop method (the callee we care about)
                callee_desc = stack.pop() if stack else None
                _check_callee(callee_desc)
                # Pop NULL/self placeholder
                if stack:
                    stack.pop()
                # Push result placeholder
                stack.append(('other', None))

            elif op == 'CALL':
                # Python 3.11+ unified CALL opcode
                # Stack layout: NULL/self?, callable, arg1, ..., argN
                nargs = instr.argval or 0
                # Pop arguments
                for _ in range(nargs):
                    if stack:
                        stack.pop()
                # Pop callable
                callee_desc = stack.pop() if stack else None
                _check_callee(callee_desc)
                # After LOAD_METHOD or PUSH_NULL, there's a NULL/self on stack - pop it
                # Check if top of stack is a NULL placeholder (('other', None))
                if stack and stack[-1] == ('other', None):
                    stack.pop()
                # Push result placeholder
                stack.append(('other', None))

            elif op == 'PRECALL':
                # Python 3.11 PRECALL - no stack effect we care about
                pass

            else:
                # Generic stack handling via dis.stack_effect
                # Keeps stack approximately consistent for other opcodes
                # CRITICAL: In Python 3.12+, opcodes that don't take args will raise
                # ValueError if you pass an arg. We must check whether to pass arg.
                try:
                    # Check if opcode accepts an argument
                    if instr.opcode >= dis.HAVE_ARGUMENT and instr.arg is not None:
                        eff = dis.stack_effect(instr.opcode, instr.arg)
                    else:
                        # Opcode doesn't take arg or arg is None
                        eff = dis.stack_effect(instr.opcode)
                except (ValueError, TypeError):
                    # Fallback: try without arg, then default to 0
                    try:
                        eff = dis.stack_effect(instr.opcode)
                    except (ValueError, TypeError):
                        eff = 0

                if eff < 0:
                    for _ in range(-eff):
                        if stack:
                            stack.pop()
                elif eff > 0:
                    for _ in range(eff):
                        stack.append(('other', None))

        return user_defined_calls, unsupported_numpy_calls

    def _assess_jit_suitability(self, characteristics: FunctionCharacteristics) -> None:
        """
        Assess JIT compilation suitability and recommend backend.
        
        Uses research-based scoring algorithm with weighted factors.
        
        Args:
            characteristics: Function characteristics to assess
        """
        # Start with neutral score
        score = 50.0
        
        # Critical disqualifiers (immediate UNSUITABLE)
        # User-defined function calls are critical because Numba can't type them,
        # causing TypingError at runtime which crashes the user's workload
        # Unsupported NumPy/SciPy functions cause similar TypingErrors
        critical_issues = [
            "eval", "exec", "compile", "pandas", "Generator functions",
            "Generator expression",  # CRITICAL: genexp not supported in nopython mode
            "yield from",  # CRITICAL: yield from delegation not supported
            "async", "Async",  # CRITICAL: async/await not supported in JIT (both cases)
            "nonlocal", "Nonlocal",  # CRITICAL: nonlocal mutations cause typing issues (both cases)
            "Class definition", "Dynamic library loading",
            "user-defined function",  # CRITICAL: Prevents Numba TypingError
            "Unsupported NumPy",  # CRITICAL: np.fft.*, np.linalg.*, np.random.* etc.
            "Unsupported SciPy",  # CRITICAL: scipy.fft.*, scipy.signal.* etc.
            "JIT-incompatible module"  # CRITICAL: hashlib, json, pickle, etc.
        ]
        for issue in characteristics.compatibility_issues:
            if any(critical in issue for critical in critical_issues):
                characteristics.jit_suitability = JITSuitability.UNSUITABLE
                characteristics.recommended_backend = JITBackendType.AUTO
                return
        
        # Weighted positive factors
        if characteristics.has_loops:
            score += 15.0 * min(characteristics.nesting_depth + 1, 3)  # Bonus for nested loops
        if characteristics.has_numerical_ops:
            score += 12.0
        if characteristics.has_numpy_usage:
            score += 20.0  # Strong indicator for Numba
        if characteristics.has_list_comprehensions:
            score += 8.0
        if characteristics.operation_count > 20:
            score += 10.0
        elif characteristics.operation_count > 10:
            score += 5.0
        
        # Weighted negative factors
        compatibility_penalty = len(characteristics.compatibility_issues) * 10.0
        score -= min(compatibility_penalty, 40.0)  # Cap maximum penalty
        
        if characteristics.has_recursion:
            score -= 5.0  # Recursion is supported but may limit optimization
        if characteristics.has_string_ops:
            score -= 8.0  # String operations are generally not JIT-optimized
        if characteristics.nesting_depth > 4:
            score -= 10.0  # High complexity
        if characteristics.cyclomatic_complexity > 10:
            score -= 5.0
        
        # Clamp score to valid range
        score = max(0.0, min(100.0, score))
        
        # Determine suitability based on final score
        if score >= 85:
            characteristics.jit_suitability = JITSuitability.EXCELLENT
        elif score >= 70:
            characteristics.jit_suitability = JITSuitability.GOOD
        elif score >= 50:
            characteristics.jit_suitability = JITSuitability.MARGINAL
        else:
            characteristics.jit_suitability = JITSuitability.UNSUITABLE
        
        # Recommend backend based on Multi-JIT Strategy 2025
        # Version-aware backend selection:
        # - Python 3.13+: NATIVE available (experimental CPython JIT)
        # - Python 3.11-3.12: No PYSTON (Pyston not compatible), use NUMBA or AUTO
        # - Python 3.8-3.10: PYSTON available for general Python optimization
        import sys
        py_version = sys.version_info[:2]

        if characteristics.has_numpy_usage or characteristics.has_numerical_ops:
            # NUMBA is always the best choice for numerical code on all versions
            characteristics.recommended_backend = JITBackendType.NUMBA
        elif characteristics.has_loops or characteristics.operation_count > 20:
            # General code with loops - version-dependent backend
            if py_version >= (3, 13):
                # Python 3.13+: Use NATIVE (CPython experimental JIT)
                characteristics.recommended_backend = JITBackendType.NATIVE
            elif py_version >= (3, 11):
                # Python 3.11-3.12: No PYSTON, use AUTO (native specializing interpreter)
                characteristics.recommended_backend = JITBackendType.AUTO
            else:
                # Python 3.8-3.10: PYSTON available
                characteristics.recommended_backend = JITBackendType.PYSTON
        else:
            characteristics.recommended_backend = JITBackendType.AUTO
        
        # Estimate performance benefit
        if characteristics.jit_suitability == JITSuitability.EXCELLENT:
            characteristics.estimated_speedup = 2.0 + (score / 100.0) * 3.0  # 2-5x
        elif characteristics.jit_suitability == JITSuitability.GOOD:
            characteristics.estimated_speedup = 1.5 + (score / 100.0) * 1.0  # 1.5-2.5x
        elif characteristics.jit_suitability == JITSuitability.MARGINAL:
            characteristics.estimated_speedup = 1.1 + (score / 100.0) * 0.4  # 1.1-1.5x
        
        # Estimate compilation cost
        characteristics.compilation_cost_ms = max(10.0, characteristics.source_lines * 2.0)
        
        # Calculate break-even point
        if characteristics.estimated_speedup > 1.0:
            benefit_per_call_ns = characteristics.average_execution_time_ns * (characteristics.estimated_speedup - 1.0)
            if benefit_per_call_ns > 0:
                characteristics.break_even_calls = int((characteristics.compilation_cost_ms * 1_000_000) / benefit_per_call_ns)
    
    def profile_function_call(self, func: Callable, execution_time_ns: int) -> None:
        """
        Record a function call for hot path detection.
        
        Args:
            func: Function that was called
            execution_time_ns: Execution time in nanoseconds
        """
        func_name = getattr(func, '__name__', str(func))
        
        # Adaptive sampling
        if self._enable_adaptive_profiling:
            with self._lock:
                self._sample_counters[func_name] += 1
                if self._sample_counters[func_name] % max(1, int(1.0 / self._profile_sample_rate)) != 0:
                    return  # Skip this sample
        
        with self._lock:
            # Ensure function is analyzed
            if func_name not in self._function_characteristics:
                self.analyze_function(func)
            
            characteristics = self._function_characteristics[func_name]
            
            # Update call statistics
            characteristics.call_count += 1
            characteristics.total_execution_time_ns += execution_time_ns
            characteristics.average_execution_time_ns = (
                characteristics.total_execution_time_ns / characteristics.call_count
            )
            characteristics.recent_calls.append(time.time())
            
            self._total_profiled_calls += 1
            
            # Check if this becomes a hot path candidate
            if characteristics.call_count >= self._min_calls_for_analysis:
                self._evaluate_hot_path_candidate(func_name, characteristics)
    
    def _evaluate_hot_path_candidate(self, func_name: str, characteristics: FunctionCharacteristics) -> None:
        """
        Evaluate if a function should be considered a hot path candidate.
        
        Args:
            func_name: Name of the function
            characteristics: Function characteristics
        """
        # Calculate hot path score
        score = 0.0
        
        # Frequency component (0-30 points)
        recent_calls = sum(1 for call_time in characteristics.recent_calls 
                         if call_time > time.time() - self._analysis_window_seconds)
        call_frequency = recent_calls / self._analysis_window_seconds
        frequency_score = min(30.0, call_frequency * 3.0)  # 10 calls/sec = max
        score += frequency_score
        
        # Execution time component (0-25 points)
        time_score = min(25.0, (characteristics.total_execution_time_ns / 10_000_000) * 25.0)  # 10ms = max
        score += time_score
        
        # Complexity component (0-20 points)
        complexity_score = min(20.0, characteristics.operation_count * 0.5)  # 40 ops = max
        score += complexity_score
        
        # JIT suitability component (0-25 points)
        suitability_scores = {
            JITSuitability.EXCELLENT: 25.0,
            JITSuitability.GOOD: 20.0,
            JITSuitability.MARGINAL: 10.0,
            JITSuitability.UNSUITABLE: 0.0
        }
        workload_score = suitability_scores[characteristics.jit_suitability]
        score += workload_score
        
        # Create or update hot path candidate
        if func_name not in self._hot_path_candidates:
            self._hot_path_candidates[func_name] = HotPathCandidate(
                function_name=func_name,
                characteristics=characteristics
            )
        
        candidate = self._hot_path_candidates[func_name]
        candidate.hot_path_score = score
        candidate.frequency_score = frequency_score
        candidate.execution_time_score = time_score
        candidate.complexity_score = complexity_score
        candidate.workload_match_score = workload_score
        
        if score >= self._hot_path_threshold:
            self._logger.debug(f"Hot path detected: {func_name} (score: {score:.1f})")
    
    def get_hot_path_candidates(self, min_score: float = 0.0) -> List[HotPathCandidate]:
        """
        Get current hot path candidates for JIT compilation.
        
        Args:
            min_score: Minimum hot path score threshold
            
        Returns:
            List of hot path candidates sorted by score
        """
        with self._lock:
            candidates = [
                candidate for candidate in self._hot_path_candidates.values()
                if candidate.hot_path_score >= min_score
            ]
            
            # Sort by hot path score (highest first)
            candidates.sort(key=lambda c: c.hot_path_score, reverse=True)
            
            return candidates
    
    def get_function_characteristics(self, func_name: str) -> Optional[FunctionCharacteristics]:
        """
        Get characteristics for a specific function.
        
        Args:
            func_name: Name of the function
            
        Returns:
            FunctionCharacteristics if available, None otherwise
        """
        with self._lock:
            return self._function_characteristics.get(func_name)
    
    def _start_background_analysis(self) -> None:
        """Start background hot path analysis."""
        def analyze_periodically():
            try:
                self._run_background_analysis()
            except Exception as e:
                self._logger.error(f"Error in background JIT analysis: {e}")
            finally:
                # Schedule next analysis
                self._analysis_timer = threading.Timer(
                    self._analysis_window_seconds, analyze_periodically
                )
                self._analysis_timer.daemon = True
                self._analysis_timer.start()
        
        # Start the timer
        self._analysis_timer = threading.Timer(
            self._analysis_window_seconds, analyze_periodically
        )
        self._analysis_timer.daemon = True
        self._analysis_timer.start()
    
    def _run_background_analysis(self) -> None:
        """Run periodic background analysis."""
        with self._lock:
            # Re-evaluate all hot path candidates
            for func_name, characteristics in self._function_characteristics.items():
                if characteristics.call_count >= self._min_calls_for_analysis:
                    self._evaluate_hot_path_candidate(func_name, characteristics)
            
            # Adaptive sampling rate adjustment
            if self._enable_adaptive_profiling:
                self._adjust_sampling_rate()
    
    def _adjust_sampling_rate(self) -> None:
        """Adjust profiling sampling rate based on overhead."""
        if self._total_profiled_calls < 100:
            return
        
        # Calculate overhead (simplified estimation)
        estimated_overhead_ratio = min(0.1, self._total_profiled_calls / 10000.0)
        target_overhead = 0.02  # 2%
        
        if estimated_overhead_ratio > target_overhead * 2:
            self._profile_sample_rate *= 0.8
            self._logger.debug(f"Reduced JIT profiling sample rate to {self._profile_sample_rate:.3f}")
        elif estimated_overhead_ratio < target_overhead * 0.5:
            self._profile_sample_rate = min(1.0, self._profile_sample_rate * 1.2)
            self._logger.debug(f"Increased JIT profiling sample rate to {self._profile_sample_rate:.3f}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get JIT analyzer statistics.
        
        Returns:
            Dictionary with analysis metrics
        """
        with self._lock:
            hot_paths = [c for c in self._hot_path_candidates.values() 
                        if c.hot_path_score >= self._hot_path_threshold]
            
            suitability_counts = defaultdict(int)
            for chars in self._function_characteristics.values():
                suitability_counts[chars.jit_suitability.value] += 1
            
            backend_recommendations = defaultdict(int)
            for chars in self._function_characteristics.values():
                backend_recommendations[chars.recommended_backend.value] += 1
            
            return {
                'analyzed_functions': len(self._function_characteristics),
                'hot_path_candidates': len(hot_paths),
                'total_profiled_calls': self._total_profiled_calls,
                'profiling_sample_rate': self._profile_sample_rate,
                'jit_suitability_distribution': dict(suitability_counts),
                'backend_recommendations': dict(backend_recommendations),
                'analysis_window_seconds': self._analysis_window_seconds,
                'hot_path_threshold': self._hot_path_threshold
            }
    
    def analyze_code(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code for JIT compilation opportunities.
        
        Args:
            code: Source code to analyze
            context: Analysis context and metadata
            
        Returns:
            Analysis results with JIT compilation recommendations
        """
        try:
            # Parse code to extract function definitions
            tree = ast.parse(code)
            results = {
                'jit_candidates': [],
                'analysis_metadata': {
                    'analyzer': 'jit_analyzer',
                    'timestamp': time.time(),
                    'context': context
                }
            }
            
            # Find function definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_analysis = self._analyze_ast_function(node, context)
                    if func_analysis['jit_suitability'] != JITSuitability.UNSUITABLE:
                        results['jit_candidates'].append(func_analysis)
            
            return results
            
        except Exception as e:
            return {
                'error': str(e),
                'jit_candidates': [],
                'analysis_metadata': {
                    'analyzer': 'jit_analyzer',
                    'timestamp': time.time(),
                    'error': str(e)
                }
            }
    
    def analyze_runtime(self, runtime_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze runtime behavior for JIT optimization opportunities.
        
        Args:
            runtime_data: Runtime performance and behavior data
            
        Returns:
            Runtime analysis results with hot path detection
        """
        results = {
            'hot_paths': [],
            'compilation_recommendations': [],
            'performance_metrics': {},
            'analysis_metadata': {
                'analyzer': 'jit_analyzer',
                'timestamp': time.time()
            }
        }
        
        try:
            # Extract function performance data
            function_stats = runtime_data.get('function_stats', {})
            call_patterns = runtime_data.get('call_patterns', {})
            
            for func_name, stats in function_stats.items():
                # Analyze function performance characteristics
                if self._should_analyze_for_jit(stats):
                    hot_path_score = self._calculate_runtime_hot_path_score(stats, call_patterns.get(func_name, {}))
                    
                    if hot_path_score >= self._hot_path_threshold:
                        results['hot_paths'].append({
                            'function_name': func_name,
                            'hot_path_score': hot_path_score,
                            'call_frequency': stats.get('call_count', 0),
                            'average_execution_time': stats.get('average_time_ns', 0),
                            'total_time_spent': stats.get('total_time_ns', 0)
                        })
                        
                        results['compilation_recommendations'].append({
                            'function_name': func_name,
                            'priority': 'high' if hot_path_score > 80 else 'medium',
                            'expected_benefit': self._estimate_jit_benefit(stats),
                            'recommended_backend': self._recommend_backend_from_runtime(stats)
                        })
            
            # Calculate overall performance metrics
            results['performance_metrics'] = {
                'total_functions_analyzed': len(function_stats),
                'hot_paths_detected': len(results['hot_paths']),
                'compilation_candidates': len(results['compilation_recommendations']),
                'average_hot_path_score': sum(hp['hot_path_score'] for hp in results['hot_paths']) / max(1, len(results['hot_paths']))
            }
            
        except Exception as e:
            results['analysis_metadata']['error'] = str(e)
        
        return results
    
    def _analyze_ast_function(self, node: ast.FunctionDef, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a function AST node for JIT suitability."""
        # Count different types of operations
        loop_count = 0
        numeric_ops = 0
        call_count = 0
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While)):
                loop_count += 1
            elif isinstance(child, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
                numeric_ops += 1
            elif isinstance(child, ast.Call):
                call_count += 1
            elif isinstance(child, (ast.If, ast.For, ast.While)):
                complexity += 1
        
        # Determine suitability based on AST analysis
        score = 0
        if loop_count > 0:
            score += 30
        if numeric_ops > 5:
            score += 25
        if complexity > 3:
            score += 15
        
        suitability = JITSuitability.UNSUITABLE
        if score >= 60:
            suitability = JITSuitability.EXCELLENT
        elif score >= 40:
            suitability = JITSuitability.GOOD
        elif score >= 20:
            suitability = JITSuitability.MARGINAL
        
        # Version-aware backend selection for Multi-JIT Strategy 2025
        import sys
        py_version = sys.version_info[:2]
        if numeric_ops > loop_count:
            backend = JITBackendType.NUMBA
        elif py_version >= (3, 13):
            backend = JITBackendType.NATIVE
        elif py_version >= (3, 11):
            backend = JITBackendType.AUTO  # No PYSTON on 3.11+
        else:
            backend = JITBackendType.PYSTON

        return {
            'function_name': node.name,
            'jit_suitability': suitability,
            'loop_count': loop_count,
            'numeric_operations': numeric_ops,
            'call_count': call_count,
            'complexity_score': complexity,
            'recommended_backend': backend
        }
    
    def _should_analyze_for_jit(self, stats: Dict[str, Any]) -> bool:
        """Check if function stats warrant JIT analysis."""
        call_count = stats.get('call_count', 0)
        avg_time = stats.get('average_time_ns', 0)
        
        # Only analyze functions with significant call count and execution time
        return call_count >= 10 and avg_time > 100000  # > 0.1ms average
    
    def _calculate_runtime_hot_path_score(self, stats: Dict[str, Any], call_patterns: Dict[str, Any]) -> float:
        """Calculate hot path score from runtime statistics."""
        call_count = stats.get('call_count', 0)
        total_time = stats.get('total_time_ns', 0)
        avg_time = stats.get('average_time_ns', 0)
        
        # Base score from call frequency
        frequency_score = min(40, call_count / 10)
        
        # Score from execution time
        time_score = min(30, avg_time / 1000000)  # Score based on ms
        
        # Score from total time impact
        impact_score = min(20, total_time / 100000000)  # Score based on 100ms total
        
        # Pattern-based scoring
        pattern_score = 10  # Base pattern score
        if call_patterns.get('regular_intervals', False):
            pattern_score += 5
        if call_patterns.get('burst_calls', False):
            pattern_score += 3
        
        return frequency_score + time_score + impact_score + pattern_score
    
    def _estimate_jit_benefit(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate potential benefit from JIT compilation."""
        avg_time = stats.get('average_time_ns', 0)
        stats.get('call_count', 0)
        
        # Conservative estimates
        expected_speedup = 1.5 if avg_time > 1000000 else 1.2  # Better speedup for slower functions
        compilation_cost_ms = max(50, avg_time / 100000)  # Compilation cost estimate
        
        return {
            'expected_speedup': expected_speedup,
            'compilation_cost_ms': compilation_cost_ms,
            'break_even_calls': int(compilation_cost_ms * 1000000 / (avg_time * (expected_speedup - 1))) if expected_speedup > 1 else float('inf')
        }
    
    def _recommend_backend_from_runtime(self, stats: Dict[str, Any]) -> JITBackendType:
        """Recommend JIT backend based on runtime characteristics."""
        # Simple heuristic based on execution patterns
        avg_time = stats.get('average_time_ns', 0)
        call_count = stats.get('call_count', 0)

        if avg_time > 5000000:  # > 5ms suggests complex computation
            return JITBackendType.NUMBA
        elif call_count > 1000:  # High frequency suggests algorithmic optimization
            # Version-aware backend selection for Multi-JIT Strategy 2025
            import sys
            py_version = sys.version_info[:2]
            if py_version >= (3, 13):
                return JITBackendType.NATIVE
            elif py_version >= (3, 11):
                return JITBackendType.AUTO  # No PYSTON on 3.11+
            else:
                return JITBackendType.PYSTON
        else:
            return JITBackendType.AUTO


def create_jit_analyzer_metadata():
    """Create metadata for the JIT analyzer plugin."""
    return create_analyzer_metadata(
        name="jit_analyzer",
        version="1.0.0",
        priority=PluginPriority.HIGH,
        capabilities=[
            "hot_path_detection",
            "jit_suitability_analysis",
            "backend_selection", 
            "performance_prediction",
            "compilation_planning"
        ]
    )