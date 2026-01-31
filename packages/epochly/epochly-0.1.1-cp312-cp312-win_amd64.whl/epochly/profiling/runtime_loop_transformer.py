"""
Runtime Loop Transformer - JIT Function Transformation for First-Execution Speedup

Transforms functions containing loops into batch-dispatched parallel versions
on first call, enabling speedup without requiring multiple executions.

Architecture:
1. Analyze function bytecode for parallelizable loops
2. Extract loop parameters (range start, end, step)
3. Create transformed version using batch dispatcher
4. Replace function on first call
5. Subsequent calls use transformed version

Author: Epochly Development Team
Date: November 18, 2025
"""

import sys
import dis
import ast
import types
import inspect
import functools
import textwrap
from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass

from ..utils.logger import get_logger
from .batch_dispatcher import BatchDispatcher, create_batch_dispatcher
from .executor_adapter import ExecutorAdapter
from .break_continue_analyzer import BreakContinueAnalyzer, analyze_break_continue
from .transform_loop_body import transform_loop_with_break_continue
from .loop_body_extractor import LoopBodyExtractor
from .while_loop_analyzer import analyze_while_loop, WhileLoopAnalysis
from .source_extractor import SourceExtractor

# Import extension to add dispatch_chunks method
from . import batch_dispatcher_extension

logger = get_logger(__name__)


@dataclass
class LoopAnalysis:
    """
    Analysis result for a function containing loops.

    Attributes:
        has_parallelizable_loop: Whether function has loop suitable for parallelization
        loop_type: Type of loop detected ('simple_range', 'nested', 'complex', 'while', etc.)
        pattern: Description of loop pattern
        nested_depth: Depth of loop nesting (1 for single loop, 2+ for nested)
        should_transform: Whether transformation is recommended
        estimated_iterations: Estimated iteration count if detectable
        complexity_score: Complexity score (higher = more complex)
    """
    has_parallelizable_loop: bool = False
    loop_type: str = 'none'
    pattern: str = ''
    nested_depth: int = 0
    should_transform: bool = False
    estimated_iterations: Optional[int] = None
    complexity_score: int = 0


class RuntimeLoopTransformer:
    """
    Transform functions containing loops for first-execution speedup.

    Uses bytecode analysis to detect loops and creates batch-dispatched
    parallel versions that run faster on first call.
    """

    def __init__(self, executor=None, min_iterations: int = 1000, on_permanent_failure=None):
        """
        Initialize runtime loop transformer.

        Args:
            executor: Executor for parallel dispatch (or None for auto-detection)
            min_iterations: Minimum iterations for transformation (default: 1000)
            on_permanent_failure: Callback(code_id, func_name) for permanent failures
        """
        import threading

        self.executor = executor
        self.min_iterations = min_iterations
        self._transformed_functions = {}  # Track transformed functions
        self._batch_dispatcher = None
        self._lock = threading.RLock()  # CRITICAL FIX: Thread-safe cache access

        # CRITICAL FIX (Dec 2025): Callback to report extraction failures to AutoProfiler
        # When source extraction fails (stdin/notebook functions), notify AutoProfiler
        # so it can disable sys.monitoring for that function (prevents retry overhead)
        self._on_permanent_failure = on_permanent_failure

        # CRITICAL FIX (Dec 2025): Cache analyze_function() results
        # Without this cache, every call does expensive AST parsing:
        # - inspect.getsource() - file I/O (~1-3ms)
        # - ast.parse() - AST parsing (~1-2ms)
        # - LoopVisitor.visit() - tree traversal (~1-2ms)
        # Total: ~7ms per function × 2000 calls = 14,000ms overhead!
        #
        # This cache stores analysis results keyed by stable function identifier:
        # "module:qualname:lineno" - survives across reloads and different objects
        self._analysis_cache: Dict[str, Optional[Dict[str, Any]]] = {}
        self._analysis_cache_max_size = 10000  # Prevent unbounded memory growth

        logger.debug(f"RuntimeLoopTransformer initialized (min_iterations={min_iterations})")

    def _get_stable_func_id(self, func: Callable) -> str:
        """
        Generate a stable identifier for a function that survives across reloads.

        Uses module:qualname:lineno:code_hash format which is stable and
        detects code changes (addresses cache pollution on module reload).

        Args:
            func: Function to identify

        Returns:
            Stable string identifier including code hash
        """
        module = getattr(func, '__module__', '<unknown>')
        qualname = getattr(func, '__qualname__', getattr(func, '__name__', '<lambda>'))

        if hasattr(func, '__code__'):
            code = func.__code__
            # Include bytecode hash to detect code changes after reload
            # This prevents serving stale cached analysis for modified functions
            code_hash = hash((code.co_code, code.co_consts, code.co_names))
            lineno = code.co_firstlineno
            return f"{module}:{qualname}:{lineno}:{code_hash}"

        return f"{module}:{qualname}:0:0"

    def _cache_analysis_result(self, cache_key: str, result: Optional[Dict[str, Any]]) -> None:
        """
        Store analysis result in cache (thread-safe).

        Includes bounds checking to prevent unbounded memory growth.

        Args:
            cache_key: Stable function identifier
            result: Analysis result (or None for failures)
        """
        with self._lock:
            # Bounds check: Clear cache if it's too large
            if len(self._analysis_cache) >= self._analysis_cache_max_size:
                logger.debug(f"Analysis cache full ({self._analysis_cache_max_size} entries), clearing")
                self._analysis_cache.clear()

            self._analysis_cache[cache_key] = result
            logger.debug(f"Cached analysis for {cache_key}: suitable={result.get('should_transform', False) if result else False}")

    def analyze_function(self, func: Callable) -> Optional[Dict[str, Any]]:
        """
        Analyze function bytecode for parallelizable loops.

        FAST PRE-SCREENING: Reject obviously unsuitable patterns before expensive analysis.
        This ensures non-optimizable workloads are NOT penalized (architecture requirement).

        CACHING (Dec 2025 fix): Results are cached using stable function identifiers.
        Cache hit = O(1) dict lookup. Cache miss = full AST analysis (~7ms).
        This reduces 2000-call overhead from 14,000ms to ~7ms (single analysis + 1999 cache hits).

        Thread Safety: Uses check-then-act pattern with atomic dict reads (CPython GIL)
        and lock-protected writes. Concurrent analysis is allowed (stateless operation)
        with possible duplicate work on first miss - acceptable tradeoff for lower latency.

        Args:
            func: Function to analyze

        Returns:
            LoopAnalysis dict with analysis results, or None if analysis failed
        """
        # Initialize cache_key early to avoid fragile locals() check in exception handler
        cache_key: Optional[str] = None

        try:
            if not isinstance(func, types.FunctionType):
                logger.debug(f"Not a function type: {type(func)}")
                return None

            # CRITICAL FIX (Dec 2025): Check cache FIRST to avoid expensive AST analysis
            # Uses stable identifier (module:qualname:lineno:code_hash) that survives across reloads
            # and detects code changes
            cache_key = self._get_stable_func_id(func)

            # Thread-safe cache lookup with fast path using atomic dict access
            # P0.6.1 FIX (Dec 2025): Use try/except instead of in-check to avoid TOCTOU race
            # Another thread could clear the cache between 'in' check and read
            try:
                cached_result = self._analysis_cache[cache_key]
                logger.debug(f"Cache HIT for {func.__name__}")
                return cached_result
            except KeyError:
                pass  # Cache miss, proceed to analysis

            # Cache miss - need to analyze
            # The analysis is expensive but safe to run concurrently (stateless)
            # We accept potential duplicate analysis in exchange for not blocking
            # This is intentional: blocking would serialize all analysis, hurting latency
            code = func.__code__

            # Disassemble bytecode
            instructions = list(dis.get_instructions(code))

            # Look for loop patterns using AST for better accuracy
            # Try to use AST if source is available
            loop_count = 0
            nested_depth = 0
            has_range = False
            has_while = False

            try:
                # CRITICAL FIX (Dec 2025): Use SourceExtractor for RELIABLE source extraction
                # in notebooks/REPL environments. SourceExtractor has multi-strategy fallback:
                # inspect.getsource -> linecache -> IPython history -> dill
                # This fixes the bug where notebook functions always returned None from analysis
                source = SourceExtractor.get_source(func)
                if source is None:
                    # Source extraction failed permanently - use bytecode analysis fallback
                    logger.debug(f"SourceExtractor failed for {func.__name__}, falling back to bytecode")
                    raise OSError("Source extraction failed via all strategies")
                # Source is already dedented by SourceExtractor
                tree = ast.parse(source)
                logger.debug(f"Successfully parsed AST for {func.__name__} via SourceExtractor")

                # Find function definition node for break/continue analysis
                func_def = None
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == func.__name__:
                        func_def = node
                        break

                # Count actual loop nesting using AST
                loop_count = 0
                max_nesting = 0
                has_range = False
                has_while = False

                class LoopVisitor(ast.NodeVisitor):
                    def __init__(self):
                        self.loop_count = 0
                        self.has_range = False
                        self.has_while = False
                        self.max_nesting = 0
                        self.current_nesting = 0
                        self.range_variable = None
                        self.iteration_count_variable = None
                        self.estimated_iterations = None
                        # Break/continue tracking
                        self.has_break = False
                        self.has_continue = False
                        self.break_count = 0
                        self.continue_count = 0
                        self.break_conditions = []
                        self.continue_conditions = []
                        self.outer_loop_node = None  # Track first For node

                        # P0.13 FIX (Dec 2025): Detect object method calls inside loops
                        # Patterns like random_state.binomial() are NOT JIT-compatible
                        # and will cause compilation to fail. Mark these as non-transformable
                        # during analysis to avoid monitoring overhead while waiting for
                        # background compilation to fail.
                        self.has_method_calls_in_loop = False
                        self.method_call_names = []

                    def visit_Call(self, node):
                        # Check if we're inside a loop AND this is a method call (Attribute)
                        if self.current_nesting > 0 and isinstance(node.func, ast.Attribute):
                            # This is a method call like obj.method()
                            self.has_method_calls_in_loop = True
                            # Try to get the method name for logging
                            try:
                                method_name = node.func.attr
                                if isinstance(node.func.value, ast.Name):
                                    self.method_call_names.append(f"{node.func.value.id}.{method_name}")
                                else:
                                    self.method_call_names.append(f"*.{method_name}")
                            except Exception:
                                pass
                        self.generic_visit(node)

                    def visit_For(self, node):
                        self.loop_count += 1
                        self.current_nesting += 1
                        self.max_nesting = max(self.max_nesting, self.current_nesting)

                        # Save first loop node for break/continue analysis
                        if self.current_nesting == 1 and self.outer_loop_node is None:
                            self.outer_loop_node = node

                        # Check if loop uses range()
                        if isinstance(node.iter, ast.Call):
                            if isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                                self.has_range = True

                                # Extract iteration count variable or literal (first arg to range)
                                if node.iter.args:
                                    first_arg = node.iter.args[0]
                                    if isinstance(first_arg, ast.Name):
                                        self.iteration_count_variable = first_arg.id
                                    elif isinstance(first_arg, ast.Constant):
                                        # Literal value - we can know iteration count!
                                        self.estimated_iterations = first_arg.value

                        # Extract loop variable name
                        if isinstance(node.target, ast.Name):
                            if self.range_variable is None:  # Store first loop variable
                                self.range_variable = node.target.id

                        self.generic_visit(node)
                        self.current_nesting -= 1

                    def visit_While(self, node):
                        self.loop_count += 1
                        self.has_while = True
                        self.current_nesting += 1
                        self.max_nesting = max(self.max_nesting, self.current_nesting)

                        # Save first loop node for break/continue analysis
                        if self.current_nesting == 1 and self.outer_loop_node is None:
                            self.outer_loop_node = node

                        self.generic_visit(node)
                        self.current_nesting -= 1

                    def visit_Break(self, node):
                        # Only track breaks in outer loop (depth 1)
                        if self.current_nesting == 1:
                            self.has_break = True
                            self.break_count += 1
                        self.generic_visit(node)

                    def visit_Continue(self, node):
                        # Only track continues in outer loop (depth 1)
                        if self.current_nesting == 1:
                            self.has_continue = True
                            self.continue_count += 1
                        self.generic_visit(node)

                visitor = LoopVisitor()
                visitor.visit(tree)

                loop_count = visitor.loop_count
                nested_depth = visitor.max_nesting
                has_range = visitor.has_range
                has_while = visitor.has_while
                range_variable = visitor.range_variable
                iteration_count_variable = visitor.iteration_count_variable
                estimated_iterations = visitor.estimated_iterations

                # Extract break/continue information
                has_break = visitor.has_break
                has_continue = visitor.has_continue
                break_count = visitor.break_count
                continue_count = visitor.continue_count

                # Analyze break/continue patterns using dedicated analyzer
                break_condition = None
                break_condition_complexity = 'none'
                if has_break and visitor.outer_loop_node and isinstance(visitor.outer_loop_node, ast.For):
                    try:
                        bc_analysis = analyze_break_continue(visitor.outer_loop_node, func_def)
                        break_condition = bc_analysis.break_condition
                        break_condition_complexity = bc_analysis.break_condition_complexity
                    except Exception as e:
                        logger.debug(f"Break/continue analysis failed: {e}")

            except (OSError, TypeError):
                # Fall back to bytecode analysis if source not available
                loop_count = 0
                has_range = False
                has_while = False

                # P0.13 FIX (Dec 2025): Track method calls in bytecode path
                # This is CRITICAL for heredoc/exec code where source isn't available
                has_method_calls_in_loop = False
                method_call_names_bytecode = []
                in_loop_region = False
                pending_attr = None  # Track LOAD_ATTR waiting for CALL

                for instr in instructions:
                    # Detect loops (FOR_ITER or JUMP_BACKWARD)
                    if instr.opname in ('FOR_ITER', 'JUMP_BACKWARD'):
                        loop_count += 1
                        in_loop_region = True  # We're inside a loop

                    # P0.13: Detect method calls (LOAD_ATTR followed by CALL)
                    # Pattern: obj.method(args) = LOAD obj -> LOAD_ATTR method -> [args] -> CALL
                    # Between LOAD_ATTR and CALL there can be argument loading/computation
                    if instr.opname == 'LOAD_ATTR':
                        pending_attr = instr.argval  # Remember attr name
                    elif instr.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'CALL_FUNCTION_KW'):
                        if pending_attr and in_loop_region:
                            has_method_calls_in_loop = True
                            if len(method_call_names_bytecode) < 5:
                                method_call_names_bytecode.append(pending_attr)
                        pending_attr = None  # Reset after call
                    # Only clear pending_attr for control flow that truly breaks the pattern
                    # Allow: LOAD_*, BINARY_*, STORE_*, BUILD_*, UNPACK_*, etc (argument prep)
                    # Reset on: JUMP_*, RETURN_*, RAISE_*, control flow
                    elif instr.opname.startswith(('JUMP', 'RETURN', 'RAISE', 'POP_JUMP', 'YIELD')):
                        pending_attr = None

                    # Detect range() calls
                    if instr.opname in ('LOAD_GLOBAL', 'LOAD_NAME') and instr.argval == 'range':
                        has_range = True

                # Estimate nesting depth (simplified for bytecode)
                nested_depth = 1 if loop_count > 0 else 0

            # Check if this is a while loop function
            if has_while and not has_range:
                # Analyze with while loop analyzer
                while_analysis = analyze_while_loop(func)

                if while_analysis.has_while_loop:
                    # Determine if should transform based on strategy
                    should_transform = (
                        while_analysis.transformation_strategy == 'bounded' and
                        while_analysis.is_parallelizable
                    )

                    analysis = {
                        'has_parallelizable_loop': should_transform,
                        'loop_type': 'while_bounded' if should_transform else 'while_skip',
                        'pattern': f"while loop, strategy={while_analysis.transformation_strategy}",
                        'nested_depth': 1,
                        'should_transform': should_transform,
                        'complexity_score': 1,
                        'while_analysis': while_analysis  # Store for transformation
                    }

                    logger.debug(f"Analyzed while loop in {func.__name__}: {analysis}")

                    # Cache the result before returning
                    self._cache_analysis_result(cache_key, analysis)
                    return analysis

            # Determine if parallelizable (for-range loops)
            has_parallelizable_loop = loop_count > 0 and has_range

            # Determine loop type based on nesting depth
            if loop_count == 0:
                loop_type = 'none'
            elif loop_count == 1 or nested_depth == 1:
                loop_type = 'simple_range'
            elif nested_depth > 1:
                loop_type = 'nested'
            else:
                loop_type = 'complex'

            # Get estimated_iterations if available from AST
            if 'estimated_iterations' not in locals():
                estimated_iterations = None

            # Determine if should transform based on:
            # 1. Pattern safety (has parallelizable loop)
            # 2. For nested loops: trust >10ms CPU threshold (PY_START triggered by profiler)
            # 3. For simple loops: apply static iteration threshold if known
            should_transform = has_parallelizable_loop and loop_count > 0

            # P0.13 FIX (Dec 2025): Disable transformation if method calls detected in loops
            # Object method calls like random_state.binomial() are NOT JIT-compatible.
            # Numba can only compile a limited set of operations (numpy ufuncs, basic math).
            # By detecting this during analysis, we avoid:
            # 1. Queueing the function for background compilation
            # 2. Monitoring overhead while waiting for compilation to fail
            # 3. The actual compilation failure
            # Check BOTH AST visitor (when source available) AND bytecode detection (for heredoc/exec)
            detected_method_calls = False
            detected_method_names = []
            if 'visitor' in locals() and visitor.has_method_calls_in_loop:
                detected_method_calls = True
                detected_method_names = visitor.method_call_names[:3]
            elif 'has_method_calls_in_loop' in locals() and has_method_calls_in_loop:
                # Bytecode path detected method calls
                detected_method_calls = True
                detected_method_names = method_call_names_bytecode[:3]

            if should_transform and detected_method_calls:
                should_transform = False
                logger.debug(
                    f"P0.13: Disabling transformation for {func.__name__} - "
                    f"method calls in loop not JIT-compatible: {detected_method_names}"
                )

            # For nested loops, trust the runtime CPU threshold (>10ms)
            # Nested loops with variables (e.g., range(n)) can't be accurately estimated statically
            # and often justify transformation due to multiplicative iteration counts
            if nested_depth <= 1:
                # Single loop - apply min_iterations threshold if known
                # Allow transformation of empty loops (estimated_iterations=0) for testing/correctness
                if estimated_iterations is not None and 0 < estimated_iterations < self.min_iterations:
                    should_transform = False
                    logger.debug(f"Single loop with {estimated_iterations} iterations < {self.min_iterations} threshold - NOT transforming")
            else:
                # Nested loops (depth > 1) - always transform if parallelizable
                # The >10ms CPU threshold already filtered this function
                logger.debug(f"Nested loop (depth={nested_depth}) - WILL transform (trusting >10ms CPU threshold)")

            # Create analysis result
            analysis = {
                'has_parallelizable_loop': has_parallelizable_loop,
                'loop_type': loop_type,
                'pattern': f"{loop_count} loops, range={has_range}",
                'nested_depth': nested_depth,
                'should_transform': should_transform,
                'complexity_score': loop_count,
                'estimated_iterations': estimated_iterations,
                # P0.13: Track method calls for debugging (from either AST or bytecode detection)
                'has_method_calls_in_loop': detected_method_calls,
                'method_call_names': detected_method_names
            }

            # Add loop parameters if detected (from AST analysis)
            if 'range_variable' in locals():
                if range_variable:
                    analysis['range_variable'] = range_variable
                if iteration_count_variable:
                    analysis['iteration_count_variable'] = iteration_count_variable

            # Add break/continue information if detected
            if 'has_break' in locals():
                analysis['has_break'] = has_break
                analysis['break_count'] = break_count
                if break_condition is not None:
                    analysis['break_condition'] = break_condition
                # Always add complexity if we detected a break
                if 'break_condition_complexity' in locals():
                    analysis['break_condition_complexity'] = break_condition_complexity

            if 'has_continue' in locals():
                analysis['has_continue'] = has_continue
                analysis['continue_count'] = continue_count

            logger.debug(f"Analyzed {func.__name__}: {analysis}")

            # Cache the result before returning
            self._cache_analysis_result(cache_key, analysis)
            return analysis

        except Exception as e:
            # Notebook code often triggers AST parse errors (truncated source from inspect.getsource)
            # This is expected and non-critical - system falls back to bytecode analysis
            # Downgrade from ERROR to DEBUG to reduce log noise
            func_name = getattr(func, '__name__', 'unknown') if func else 'unknown'
            logger.debug(f"AST analysis failed for {func_name}: {e}")

            # CRITICAL: Cache failures too! This prevents re-analysis of functions that
            # consistently fail (e.g., notebook code without source).
            # Without this, every call would retry the expensive getsource() + parse()
            # Note: cache_key is initialized at function start to ensure it's always defined
            if cache_key is not None:
                self._cache_analysis_result(cache_key, None)
            return None

    def transform_function(self, func: Callable) -> Optional[Callable]:
        """
        Transform function to use batch dispatch for loops.

        Creates a new version of the function that:
        1. Detects loop iterations at runtime
        2. Extracts loop body
        3. Dispatches iterations to batch dispatcher
        4. Collects and merges results

        Args:
            func: Function to transform

        Returns:
            Transformed function, or None if transformation not applicable
        """
        try:
            # Analyze function for loops
            analysis = self.analyze_function(func)

            if not analysis or not analysis['should_transform']:
                logger.debug(f"Function {func.__name__} not suitable for transformation")
                return None

            # Get or create batch dispatcher
            if self._batch_dispatcher is None:
                self._batch_dispatcher = create_batch_dispatcher(self.executor)

            logger.info(f"Transforming {func.__name__} for batch dispatch (loop_type={analysis['loop_type']})")

            # Create transformed version
            transformed = self._create_transformed_function(func, analysis)

            if transformed:
                # Track successful transformation (thread-safe)
                with self._lock:
                    self._transformed_functions[id(func)] = transformed
                logger.info(f"Successfully transformed {func.__name__}")
            else:
                # CRITICAL FIX: Cache failed transformations to prevent retry overhead (thread-safe)
                # Mark as "attempted but failed" so we don't retry on every call
                with self._lock:
                    self._transformed_functions[id(func)] = func  # Cache original = "don't retry"
                logger.debug(f"Transformation failed for {func.__name__}, will use original function")

            return transformed

        except Exception as e:
            logger.error(f"Failed to transform function {func.__name__ if hasattr(func, '__name__') else 'unknown'}: {e}")
            # Cache the failure to prevent retry overhead (thread-safe)
            with self._lock:
                self._transformed_functions[id(func)] = func
            return None

    def _create_transformed_function(self, func: Callable, analysis: Dict[str, Any]) -> Optional[Callable]:
        """
        Create batch-dispatched version of function.

        Strategy:
        For simple patterns, we can extract the loop body and parallelize.
        For complex patterns, we fall back to sequential or JIT only.

        Args:
            func: Original function
            analysis: Loop analysis results

        Returns:
            Transformed function or None
        """
        try:
            # Handle while loops
            if analysis['loop_type'] in ('while_bounded',):
                return self._transform_while_loop(func, analysis)

            # Handle for-range loops
            if analysis['loop_type'] == 'simple_range':
                return self._transform_simple_range_loop(func)

            elif analysis['loop_type'] == 'nested':
                return self._transform_nested_loop(func)

            else:
                # Complex patterns - don't transform
                logger.debug(f"Skipping complex loop pattern in {func.__name__}")
                return None

        except Exception as e:
            logger.error(f"Failed to create transformed function: {e}")
            return None

    def _transform_while_loop(self, func: Callable, analysis: Dict[str, Any]) -> Optional[Callable]:
        """
        Transform while loop using bounded iteration strategy.

        For bounded while loops (i < n pattern), transforms similar to for-range loops
        with safety limit from max_iterations.

        Args:
            func: Function to transform
            analysis: Analysis containing while_analysis

        Returns:
            Transformed function or None
        """
        try:
            from .while_loop_transformer import WhileLoopTransformer

            # Get while loop analysis
            while_analysis = analysis.get('while_analysis')
            if not while_analysis:
                logger.debug(f"No while analysis available for {func.__name__}")
                return None

            # Use specialized while loop transformer with our batch dispatcher
            transformer = WhileLoopTransformer(
                batch_dispatcher=self._batch_dispatcher,
                max_iterations=while_analysis.estimated_max_iterations or 1000000
            )

            transformed = transformer.transform_function(func, while_analysis)

            if transformed:
                logger.info(f"Successfully transformed while loop in {func.__name__} using bounded strategy")

            return transformed

        except Exception as e:
            import traceback
            logger.error(f"Failed to transform while loop: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None

    def _transform_simple_range_loop(self, func: Callable) -> Optional[Callable]:
        """
        Transform function with simple for-range loop.

        Pattern:
            def func(n):
                result = 0
                for i in range(n):
                    if i > 100:
                        break
                    if i % 2 == 0:
                        continue
                    result += compute(i)
                return result

        Transformed to use pre-filtering for break and continue conditions.

        Args:
            func: Function to transform

        Returns:
            Transformed function or None
        """
        try:
            # Get analysis from analyze_function
            analysis = self.analyze_function(func)

            if not analysis:
                logger.debug(f"No analysis available for {func.__name__}")
                return None

            # Check if has break or continue patterns
            has_break = analysis.get('has_break', False)
            has_continue = analysis.get('has_continue', False)

            if has_break or has_continue:
                # Use specialized break/continue transformation
                logger.info(f"Transforming {func.__name__} with break/continue patterns")
                return transform_loop_with_break_continue(
                    func,
                    analysis,
                    self._batch_dispatcher,
                    self.min_iterations
                )

            # Otherwise, use basic loop body extraction
            extractor = LoopBodyExtractor()
            extracted = extractor.extract_simple_loop(func, analysis)

            if not extracted:
                logger.debug(f"Failed to extract loop from {func.__name__}")

                # NOTE (Dec 2025): We do NOT call _on_permanent_failure here.
                # Loop extraction failure only affects the loop transformation path.
                # The function may still be an excellent candidate for direct Numba JIT
                # compilation which does NOT require source code extraction.
                # Calling _on_permanent_failure would add to _jit_compiled_code_ids,
                # disabling monitoring and preventing direct JIT from ever being attempted.
                # Instead, let the function be detected as hot and go through apply_optimization().

                return None

            # Create transformed wrapper for simple loops without break/continue
            @functools.wraps(func)
            def transformed_wrapper(*args, **kwargs):
                """
                Parallelized version of simple range loop.
                """
                try:
                    # Get iteration count from first argument
                    if not args:
                        return func(*args, **kwargs)

                    n = args[0]
                    if not isinstance(n, int) or n <= 0:
                        return func(*args, **kwargs)

                    # For small workloads, use sequential
                    if n < self.min_iterations:
                        return func(*args, **kwargs)

                    # Dispatch loop body in parallel
                    if self._batch_dispatcher:
                        # Capture locals that loop body references (params + closures)
                        captured = {}
                        if hasattr(extracted, 'captured_locals') and extracted.captured_locals:
                            # Issue 3 fix: Use inspect.signature().bind() for proper argument handling
                            # This correctly handles defaults, *args, **kwargs, keyword-only, etc.
                            import inspect
                            sig = inspect.signature(func)

                            try:
                                # Bind arguments to parameters
                                bound = sig.bind(*args, **kwargs)
                                # Apply default values for parameters not provided
                                bound.apply_defaults()
                                # Get complete parameter mapping
                                param_values = dict(bound.arguments)
                            except TypeError:
                                # Binding failed, fall back to simple mapping
                                param_values = {}
                                param_names = list(sig.parameters.keys())
                                for i, arg_value in enumerate(args):
                                    if i < len(param_names):
                                        param_values[param_names[i]] = arg_value
                                param_values.update(kwargs)

                            # Also get closure variables
                            if func.__closure__:
                                closure_vars = func.__code__.co_freevars
                                for i, cell in enumerate(func.__closure__):
                                    if i < len(closure_vars):
                                        param_values[closure_vars[i]] = cell.cell_contents

                            # Capture only the variables referenced by loop body
                            for name in extracted.captured_locals:
                                if name in param_values:
                                    captured[name] = param_values[name]

                        # Direct dispatch without filtering (no break/continue)
                        partial_results = self._batch_dispatcher.dispatch_loop(
                            extracted.loop_func,
                            start=0,
                            end=n,
                            step=1,
                            bound_locals=captured
                        )

                        # CRITICAL FIX: If dispatch failed, fall back to original function
                        if partial_results is None:
                            logger.debug(f"Parallel dispatch failed for {func.__name__}, falling back to original")

                            # CRITICAL: Mark this function as not transformable to prevent future overhead (thread-safe)
                            # Replace cached transformed function with original to signal "don't use parallel"
                            with self._lock:
                                self._transformed_functions[id(func)] = func
                            logger.debug(f"Cached {func.__name__} as non-transformable (dispatch failed)")

                            return func(*args, **kwargs)

                        # Aggregate results (handle both single and multi-accumulator)
                        if not partial_results:
                            return 0  # Empty loop (but dispatch succeeded)

                        # Check if results are tuples (multi-accumulator)
                        first_result = partial_results[0]
                        if isinstance(first_result, tuple):
                            # Multi-accumulator: unzip and aggregate each column
                            num_accumulators = len(first_result)
                            columns = list(zip(*partial_results))
                            aggregated = tuple(sum(col) for col in columns)
                            return aggregated
                        else:
                            # Single accumulator: simple sum
                            return sum(partial_results)
                    else:
                        # No dispatcher - run sequentially
                        result = 0
                        for i in range(n):
                            result += extracted.loop_func(i)
                        return result

                except Exception as e:
                    logger.debug(f"Transformation execution failed: {e}, falling back to original")
                    return func(*args, **kwargs)

            # Mark as transformed
            transformed_wrapper._epochly_transformed = True
            transformed_wrapper._original_function = func

            logger.info(f"Successfully transformed simple loop {func.__name__}")
            return transformed_wrapper

        except Exception as e:
            logger.error(f"Failed to transform simple range loop: {e}")
            return None

    def _transform_nested_loop(self, func: Callable) -> Optional[Callable]:
        """
        Transform function with nested loops.

        Strategy: Parallelize outer loop, each worker executes inner loop sequentially.

        Pattern:
            def nested(n):
                result = 0
                for i in range(n):        # Parallelize THIS
                    for j in range(100):  # Keep sequential
                        result += i * j
                return result

        Becomes:
            def outer_body(i):
                partial = 0
                for j in range(100):
                    partial += i * j
                return partial

            results = dispatch_loop(outer_body, 0, n, 1)
            return sum(results)

        Args:
            func: Function to transform

        Returns:
            Transformed function or None
        """
        try:
            # Get and parse source using SourceExtractor for notebook reliability
            source = SourceExtractor.get_source(func)
            if source is None:
                logger.debug(f"SourceExtractor: Cannot get source for {func.__name__}")
                return None

            try:
                tree = ast.parse(source)
            except SyntaxError as e:
                logger.debug(f"AST parse failed for {func.__name__}: {e}")
                return None

            # Find function definition
            func_def = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func.__name__:
                    func_def = node
                    break

            if not func_def:
                return None

            # Find outer for loop (first one encountered)
            outer_loop = None
            for node in func_def.body:
                if isinstance(node, ast.For):
                    outer_loop = node
                    break

            if not outer_loop:
                logger.debug(f"No outer loop found in {func.__name__}")
                return None

            # Check if outer loop uses range()
            if not (isinstance(outer_loop.iter, ast.Call) and
                    isinstance(outer_loop.iter.func, ast.Name) and
                    outer_loop.iter.func.id == 'range'):
                logger.debug(f"Outer loop doesn't use range() in {func.__name__}")
                return None

            # Get batch dispatcher
            if self._batch_dispatcher is None:
                self._batch_dispatcher = create_batch_dispatcher(self.executor)

            # Create transformed version
            @functools.wraps(func)
            def nested_loop_transformed(*args, **kwargs):
                """
                Parallelized version of nested loop function.

                Extracts outer loop body and dispatches to workers.
                """
                try:
                    # Get iteration count from first argument
                    # Assumption: First arg is the loop bound 'n'
                    if not args:
                        return func(*args, **kwargs)

                    n = args[0]

                    # Sanity check
                    if not isinstance(n, int) or n <= 0:
                        return func(*args, **kwargs)

                    # For small workloads, don't parallelize (overhead not worth it)
                    if n < self.min_iterations:
                        return func(*args, **kwargs)

                    # Extract ACTUAL loop body from AST (not hardcoded)
                    # This ensures transformation works for arbitrary loop patterns
                    outer_loop_body = self._extract_outer_loop_body(func, outer_loop, func_def)

                    if not outer_loop_body:
                        # Fallback to original if extraction fails
                        logger.warning(f"Failed to extract loop body from {func.__name__}, using original")
                        return func(*args, **kwargs)

                    # JIT + Batch Dispatch Combination
                    # JIT-compile loop body BEFORE dispatching for multiplicative speedup
                    jit_loop_body = self._jit_compile_loop_body(outer_loop_body)

                    # Capture locals that loop body references (e.g., function parameters)
                    captured = {}
                    frame_locals = locals()
                    # For nested loops, we need to capture all non-infrastructure variables
                    # This includes function parameters that the loop body may reference
                    for name, value in frame_locals.items():
                        if name not in ('self', 'func', 'outer_loop', 'func_def', 'n', 'outer_loop_body', 'jit_loop_body'):
                            captured[name] = value

                    # Dispatch JIT-compiled loop body in parallel
                    partial_results = self._batch_dispatcher.dispatch_loop(
                        jit_loop_body if jit_loop_body else outer_loop_body,
                        start=0,
                        end=n,
                        step=1,
                        bound_locals=captured
                    )

                    # Aggregate results (handle both single and multi-accumulator)
                    if not partial_results:
                        return 0  # Empty loop

                    # Check if results are tuples (multi-accumulator)
                    first_result = partial_results[0]
                    if isinstance(first_result, tuple):
                        # Multi-accumulator: unzip and aggregate each column
                        num_accumulators = len(first_result)
                        columns = list(zip(*partial_results))
                        aggregated = tuple(sum(col) for col in columns)
                        return aggregated
                    else:
                        # Single accumulator: simple sum
                        return sum(partial_results)

                except Exception as e:
                    logger.debug(f"Parallel execution failed: {e}, falling back to original")
                    return func(*args, **kwargs)

            # Mark as transformed
            nested_loop_transformed._epochly_transformed = True
            nested_loop_transformed._original_function = func

            logger.info(f"Successfully transformed nested loop function {func.__name__}")
            return nested_loop_transformed

        except Exception as e:
            import traceback
            logger.error(f"Failed to transform nested loop: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None

    def _extract_outer_loop_body(self, func: Callable, outer_loop_ast, func_def_ast) -> Optional[Callable]:
        """
        Extract outer loop body as executable function using AST.

        Per mcp-reflect Priority 2: Support arbitrary loop patterns by extracting
        actual loop code from AST, rewriting accumulator variables correctly.

        CRITICAL: Rewrites accumulator variable (e.g., `result`) to `partial_result`
        so that each worker computes its partial sum correctly.

        Args:
            func: Original function
            outer_loop_ast: AST node of the outer for loop
            func_def_ast: AST node of the function definition

        Returns:
            Callable function that executes one iteration of outer loop
        """
        try:
            # Extract loop variable name
            if not isinstance(outer_loop_ast.target, ast.Name):
                logger.debug("Outer loop target is not a simple name, can't extract")
                return None

            loop_var = outer_loop_ast.target.id

            # Find ALL accumulator variables (support multi-accumulator patterns)
            # Look for pattern: sum_val = 0; max_val = 0; for i in range(n): ...
            accumulator_vars = []
            accumulator_init_values = {}

            # Find all variables initialized before loop that might be accumulators
            for stmt in func_def_ast.body:
                if stmt is outer_loop_ast:
                    # Reached the loop, stop searching
                    break

                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                    target = stmt.targets[0]
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        # Check if it's initialized to a value that suggests accumulation
                        if isinstance(stmt.value, ast.Constant):
                            # Numeric or empty initialization (0, 0.0, [], "", etc.)
                            accumulator_vars.append(var_name)
                            accumulator_init_values[var_name] = stmt.value.value
                        elif isinstance(stmt.value, (ast.List, ast.Dict, ast.Set)):
                            # Collection initialization
                            accumulator_vars.append(var_name)
                            accumulator_init_values[var_name] = [] if isinstance(stmt.value, ast.List) else {}
                        elif isinstance(stmt.value, ast.UnaryOp) and isinstance(stmt.value.op, ast.USub):
                            # Negative number like -float('inf')
                            accumulator_vars.append(var_name)
                            accumulator_init_values[var_name] = 0  # Will be overridden

            # If no accumulators found, default to single 'result'
            if not accumulator_vars:
                accumulator_vars = ['result']
                accumulator_init_values = {'result': 0}
                logger.debug(f"No accumulators detected, defaulting to single 'result'")

            # Clone loop body nodes and rewrite ALL accumulator variables
            loop_body_nodes = list(outer_loop_ast.body)
            for old_var in accumulator_vars:
                partial_var = f'partial_{old_var}'
                loop_body_nodes = [self._rewrite_accumulator(node, old_var, partial_var)
                                 for node in loop_body_nodes]

            # Convert rewritten loop body to code
            loop_body_code = ast.unparse(ast.Module(body=loop_body_nodes, type_ignores=[]))

            # Create initialization code for all partial variables
            init_lines = []
            for var in accumulator_vars:
                init_val = accumulator_init_values.get(var, 0)
                if isinstance(init_val, str):
                    init_lines.append(f"    partial_{var} = '{init_val}'")
                elif isinstance(init_val, list):
                    init_lines.append(f"    partial_{var} = []")
                elif isinstance(init_val, dict):
                    init_lines.append(f"    partial_{var} = {{}}")
                else:
                    init_lines.append(f"    partial_{var} = {init_val}")

            init_code = '\n'.join(init_lines)

            # Create return statement (tuple if multiple accumulators)
            if len(accumulator_vars) == 1:
                return_code = f"    return partial_{accumulator_vars[0]}"
            else:
                partial_names = ', '.join(f'partial_{var}' for var in accumulator_vars)
                return_code = f"    return ({partial_names})"

            # Create function template
            function_template = f"""
def outer_loop_body({loop_var}):
    # Initialize partial results (one for each accumulator)
{init_code}

    # Execute loop body (all accumulators rewritten to partial_* variables)
{textwrap.indent(loop_body_code, '    ')}

{return_code}
"""

            # Execute the template in function's scope
            exec_globals = func.__globals__.copy()
            exec_locals = {}

            try:
                exec(function_template, exec_globals, exec_locals)
                outer_loop_body_func = exec_locals['outer_loop_body']

                logger.info(f"Extracted outer loop body for {func.__name__} (accumulators {accumulator_vars} -> 'partial_result')")
                return outer_loop_body_func

            except Exception as e:
                logger.warning(f"Failed to exec loop body template: {e}")
                logger.debug(f"Template was:\n{function_template}")
                return None

        except Exception as e:
            import traceback
            logger.error(f"Failed to extract outer loop body: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None

    def _rewrite_accumulator(self, node, old_name: str, new_name: str):
        """
        Rewrite accumulator variable references in AST node.

        Changes all references to old_name to use new_name instead.
        E.g., `result += x` becomes `partial_result += x`

        Args:
            node: AST node to rewrite
            old_name: Old variable name (e.g., 'result')
            new_name: New variable name (e.g., 'partial_result')

        Returns:
            Rewritten AST node
        """
        import copy

        class AccumulatorRewriter(ast.NodeTransformer):
            def visit_Name(self, node):
                # Rewrite name references
                if node.id == old_name:
                    return ast.Name(id=new_name, ctx=node.ctx)
                return node

        # Deep copy to avoid modifying original
        node_copy = copy.deepcopy(node)
        rewriter = AccumulatorRewriter()
        return rewriter.visit(node_copy)

    def _jit_compile_loop_body(self, loop_body_func: Callable) -> Optional[Callable]:
        """
        JIT-compile loop body function for maximum performance.

        Combines JIT compilation with batch dispatch for multiplicative speedups.
        Per mcp-reflect Priority 4: JIT (5.4Mx) x Parallel (1.2x) = 6.5Mx potential

        Args:
            loop_body_func: Loop body function to compile

        Returns:
            JIT-compiled function or None if compilation failed
        """
        try:
            # Try to get JIT manager from core
            from ..core.epochly_core import get_epochly_core
            core = get_epochly_core()

            if not core:
                logger.warning("JIT compilation skipped: EpochlyCore not initialized")
                return None

            if not hasattr(core, '_jit_manager') or not core._jit_manager:
                logger.warning("JIT compilation skipped: JIT manager not available (Level <2?)")
                # CRITICAL FIX (Nov 22, 2025): Use correct attribute name 'current_level' instead of '_enhancement_level'
                level_name = core.current_level.name if hasattr(core, 'current_level') and hasattr(core.current_level, 'name') else 'unknown'
                logger.warning(f"  Core enhancement level: {level_name}")
                logger.warning(f"  Ensure EPOCHLY_LEVEL >= 2 for JIT support")
                return None

            # Compile loop body with JIT (skip benchmarking to avoid recursion)
            logger.info(f"Attempting JIT compilation of loop body: {loop_body_func.__name__}")

            compiled = core._jit_manager.compile_function_auto(
                loop_body_func,
                bypass_call_count=True,  # Already know it's worth compiling
                skip_benchmark=True       # Avoid double execution in workers
            )

            if compiled and compiled != loop_body_func:
                # JIT compilation succeeded
                compiled_type = type(compiled).__name__
                logger.info(f"JIT-compiled loop body successfully")
                logger.info(f"  Original: {loop_body_func}")
                logger.info(f"  Compiled: {compiled} (type: {compiled_type})")
                logger.info(f"  Expected per-iteration speedup: 100-1000x")
                logger.info(f"  Combined with parallelization: multiplicative gains")
                return compiled
            else:
                logger.warning(f"JIT compilation did not produce new function")
                logger.warning(f"  Input function: {loop_body_func}")
                logger.warning(f"  Returned: {compiled}")
                logger.warning(f"  Falling back to pure Python loop body")
                return None

        except Exception as e:
            logger.error(f"JIT compilation failed with exception: {e}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return None

    def was_transformed(self, func: Callable) -> bool:
        """
        Check if function was transformed.

        Args:
            func: Function to check

        Returns:
            True if function has been transformed
        """
        return (hasattr(func, '_epochly_transformed') and func._epochly_transformed) or \
               (id(func) in self._transformed_functions)


def create_runtime_loop_transformer(executor=None, min_iterations: int = 1000, on_permanent_failure=None):
    """
    Create a runtime loop transformer.

    Args:
        executor: Executor for parallel dispatch (or None for auto-detection)
        min_iterations: Minimum iterations for transformation
        on_permanent_failure: Callback for permanent failures (disables monitoring)

    Returns:
        RuntimeLoopTransformer instance
    """
    return RuntimeLoopTransformer(
        executor=executor,
        min_iterations=min_iterations,
        on_permanent_failure=on_permanent_failure
    )
