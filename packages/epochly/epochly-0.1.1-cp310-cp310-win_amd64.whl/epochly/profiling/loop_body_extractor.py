"""
Loop Body Extractor - Extract and Transform Loop Bodies for Parallel Execution

Extracts loop bodies from AST, handles break/continue conditions, and creates
parallelizable versions with pre-filtering and proper accumulator handling.

Author: Epochly Development Team
Date: November 18, 2025
"""

import ast
import textwrap
from typing import Callable, Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from ..utils.logger import get_logger
from .source_extractor import SourceExtractor

logger = get_logger(__name__)


@dataclass
class ExtractedLoopBody:
    """
    Result of loop body extraction.

    Attributes:
        loop_func: The extracted loop body as a callable
        loop_var: Name of the loop variable (e.g., 'i')
        accumulator_var: Name of accumulator variable (e.g., 'result')
        break_filter: Optional function to filter indices based on break condition
        continue_filter: Optional function to filter indices based on continue conditions
        aggregation_type: Type of aggregation ('sum', 'max', 'min', 'list', 'custom')
        captured_locals: Names of local variables/parameters referenced by loop body
    """
    loop_func: Callable
    loop_var: str
    accumulator_var: str
    break_filter: Optional[Callable] = None
    continue_filter: Optional[Callable] = None
    aggregation_type: str = 'sum'
    captured_locals: Tuple[str, ...] = ()


class LoopBodyExtractor:
    """
    Extracts loop bodies from functions and transforms them for parallel execution.

    Handles:
    - Break conditions by pre-filtering iteration indices
    - Continue conditions by filtering during execution
    - Accumulator variable rewriting for partial results
    - Multiple accumulator patterns
    - Closure capture for functions with parameters

    Source Extraction (Dec 2025):
    - Uses SourceExtractor for RELIABLE source code extraction
    - Works in Jupyter notebooks, IPython, and standard Python files
    - Layered fallback: inspect -> linecache -> IPython history -> dill
    - Deterministic behavior with caching (no random failures)
    """

    # Legacy cache attributes kept for backward compatibility
    # Actual caching is now handled by SourceExtractor
    _source_extraction_failures = set()  # Deprecated - use SourceExtractor
    _source_extraction_failures_max_size = 10000  # Deprecated

    def __init__(self):
        """Initialize loop body extractor."""
        pass  # Cache is at class level

    @classmethod
    def _add_to_failure_cache(cls, code_id: int) -> None:
        """
        DEPRECATED: Use SourceExtractor which handles caching internally.

        Kept for backward compatibility only.
        """
        # BOUNDED: Clear cache if it grows too large (prevents memory leak)
        if len(cls._source_extraction_failures) >= cls._source_extraction_failures_max_size:
            cls._source_extraction_failures.clear()
        cls._source_extraction_failures.add(code_id)

    def _find_local_dependencies(
        self,
        for_loop: ast.For,
        loop_var: str,
        accumulator_var: str,
        func_def: ast.FunctionDef,
        func_globals: dict,
        func_freevars: tuple = ()
    ) -> set:
        """
        Find variables that must be captured from caller's locals.

        Returns names of parameters/locals/closures referenced in loop body.

        Handles:
        - All parameter types (positional, keyword, positional-only, keyword-only, *args, **kwargs)
        - Local variables defined before the loop
        - Closure variables
        - Parameter/global name collisions (parameters take precedence)

        Args:
            for_loop: For loop AST node
            loop_var: Name of loop variable
            accumulator_var: Name of accumulator variable
            func_def: Function definition AST node
            func_globals: Global scope from original function
            func_freevars: Free variables (closure variables) from original function
        """
        # Get ALL parameter names (Issue 5 fix)
        param_names = set()

        # Standard positional/keyword parameters
        param_names.update(arg.arg for arg in func_def.args.args)

        # Positional-only parameters (Python 3.8+)
        if hasattr(func_def.args, 'posonlyargs'):
            param_names.update(arg.arg for arg in func_def.args.posonlyargs)

        # Keyword-only parameters
        if hasattr(func_def.args, 'kwonlyargs'):
            param_names.update(arg.arg for arg in func_def.args.kwonlyargs)

        # *args parameter
        if func_def.args.vararg:
            param_names.add(func_def.args.vararg.arg)

        # **kwargs parameter
        if func_def.args.kwarg:
            param_names.add(func_def.args.kwarg.arg)

        # Get local variables defined before the loop (Issue 1 fix)
        local_vars = self._find_locals_before_loop(func_def, for_loop)

        # Combine all local scope names (params + locals + closures)
        local_scope = param_names | local_vars | set(func_freevars)

        # Find all names referenced in loop body
        referenced = set()
        for node in ast.walk(for_loop):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                referenced.add(node.id)

        # Capture names that are in local scope (Issue 2 fix: check local scope FIRST)
        captured = set()
        for name in referenced:
            # Skip loop infrastructure
            if name in (loop_var, accumulator_var, 'partial_result'):
                continue

            # Capture if in local scope (parameters, locals, or closures)
            if name in local_scope:
                captured.add(name)
                continue

            # Only skip if it's a module global AND not shadowed by local scope
            # (Already handled above, so if we reach here it's truly a global)

        return captured

    def _find_locals_before_loop(self, func_def: ast.FunctionDef, for_loop: ast.For) -> set:
        """
        Find local variables defined before the for loop.

        Returns names of variables assigned before the loop starts.
        """
        local_vars = set()

        # Walk function body up to the for loop
        for stmt in func_def.body:
            # Stop when we reach the for loop
            if stmt is for_loop:
                break

            # Collect assignment targets
            for node in ast.walk(stmt):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            local_vars.add(target.id)
                elif isinstance(node, ast.AnnAssign):
                    if isinstance(node.target, ast.Name):
                        local_vars.add(node.target.id)
                elif isinstance(node, ast.AugAssign):
                    if isinstance(node.target, ast.Name):
                        local_vars.add(node.target.id)
                # Also handle with statements (with foo as bar:)
                elif isinstance(node, ast.withitem):
                    if node.optional_vars and isinstance(node.optional_vars, ast.Name):
                        local_vars.add(node.optional_vars.id)

        return local_vars

    def extract_simple_loop(
        self,
        func: Callable,
        analysis: Dict[str, Any]
    ) -> Optional[ExtractedLoopBody]:
        """
        Extract loop body from a simple for-range loop.

        Args:
            func: Original function containing the loop
            analysis: Loop analysis results from RuntimeLoopTransformer

        Returns:
            ExtractedLoopBody with callable and filters, or None if extraction failed
        """
        # Use SourceExtractor for RELIABLE source extraction in all environments
        # (Jupyter notebooks, IPython, standard Python files)
        # SourceExtractor handles caching internally - no need for manual cache checks
        try:
            source = SourceExtractor.get_source(func)
            if not source:
                # SourceExtractor already logged and cached the failure
                return None

            tree = ast.parse(source)

            # Find function definition
            func_def = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func.__name__:
                    func_def = node
                    break

            if not func_def:
                logger.debug(f"Cannot find function definition for {func.__name__} in extracted source")
                return None

            # Find for loop
            for_loop = None
            for stmt in func_def.body:
                if isinstance(stmt, ast.For):
                    for_loop = stmt
                    break

            if not for_loop:
                logger.debug(f"No for loop found in {func.__name__}")
                return None

            # Extract loop variable
            if not isinstance(for_loop.target, ast.Name):
                logger.debug("Loop target is not a simple variable")
                return None

            loop_var = for_loop.target.id

            # Find accumulator variable (initialized before loop)
            accumulator_var = self._find_accumulator_var(func_def, for_loop)

            # Extract break condition if present
            break_filter = None
            if analysis.get('has_break', False):
                break_filter = self._create_break_filter(
                    for_loop,
                    loop_var,
                    analysis.get('break_condition')
                )

            # Extract continue conditions if present
            continue_filter = None
            if analysis.get('has_continue', False):
                continue_filter = self._create_continue_filter(
                    for_loop,
                    loop_var
                )

            # Create loop body function
            loop_body_func = self._create_loop_body_function(
                for_loop,
                loop_var,
                accumulator_var,
                func.__globals__
            )

            if not loop_body_func:
                logger.debug("Failed to create loop body function")
                return None

            # Capture locals/parameters/closures that loop body references
            func_freevars = func.__code__.co_freevars if hasattr(func, '__code__') else ()
            captured_locals = self._find_local_dependencies(
                for_loop, loop_var, accumulator_var, func_def, func.__globals__, func_freevars
            )

            return ExtractedLoopBody(
                loop_func=loop_body_func,
                loop_var=loop_var,
                accumulator_var=accumulator_var,
                break_filter=break_filter,
                continue_filter=continue_filter,
                aggregation_type='sum',  # Default for now
                captured_locals=tuple(sorted(captured_locals))
            )

        except Exception as e:
            # SourceExtractor handles caching internally
            # Log the error but don't cache here - AST parsing errors are function-specific
            logger.error(f"Failed to extract simple loop: {e}")
            return None

    def _find_accumulator_var(self, func_def: ast.FunctionDef, for_loop: ast.For) -> str:
        """
        Find accumulator variable initialized before the loop.

        Args:
            func_def: Function AST node
            for_loop: For loop AST node

        Returns:
            Name of accumulator variable, or 'result' as default
        """
        accumulator_var = None

        for stmt in func_def.body:
            if stmt is for_loop:
                break

            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if isinstance(target, ast.Name):
                    # Check if initialized to 0 (typical accumulator)
                    if isinstance(stmt.value, ast.Constant) and stmt.value.value == 0:
                        accumulator_var = target.id
                        break

        return accumulator_var or 'result'

    def _create_break_filter(
        self,
        for_loop: ast.For,
        loop_var: str,
        break_condition: Optional[ast.expr]
    ) -> Optional[Callable]:
        """
        Create a filter function that pre-filters indices based on break condition.

        For pattern: if i > 100: break
        Creates: lambda indices: [i for i in indices if not (i > 100)]

        Args:
            for_loop: For loop AST node
            loop_var: Name of loop variable
            break_condition: AST expression of break condition

        Returns:
            Filter function or None if complex pattern
        """
        try:
            # Find break condition in loop body
            if not break_condition:
                for stmt in for_loop.body:
                    if isinstance(stmt, ast.If):
                        # Check if body contains break
                        for body_stmt in stmt.body:
                            if isinstance(body_stmt, ast.Break):
                                break_condition = stmt.test
                                break

            if not break_condition:
                logger.debug("No break condition found")
                return None

            # Generate filter function code
            # We need to find the first index where the condition becomes true
            # and filter out all indices >= that index
            condition_str = ast.unparse(break_condition)

            # Create filter that stops at first break condition
            filter_code = f"""
def break_filter(start, end):
    '''Pre-filter indices based on break condition.'''
    indices = []
    for {loop_var} in range(start, end):
        if {condition_str}:
            break  # Stop at first break condition
        indices.append({loop_var})
    return indices
"""

            # Compile and return filter function
            exec_globals = {}
            exec_locals = {}
            exec(filter_code, exec_globals, exec_locals)

            logger.info(f"Created break filter for condition: {condition_str}")
            return exec_locals['break_filter']

        except Exception as e:
            logger.debug(f"Failed to create break filter: {e}")
            return None

    def _create_continue_filter(
        self,
        for_loop: ast.For,
        loop_var: str
    ) -> Optional[Callable]:
        """
        Create a filter function that filters out continued iterations.

        For pattern: if i % 2 == 0: continue
        Creates: lambda i: not (i % 2 == 0)

        Args:
            for_loop: For loop AST node
            loop_var: Name of loop variable

        Returns:
            Filter function or None if complex pattern
        """
        try:
            continue_conditions = []

            # Find all continue conditions
            for stmt in for_loop.body:
                if isinstance(stmt, ast.If):
                    # Check if body contains continue
                    for body_stmt in stmt.body:
                        if isinstance(body_stmt, ast.Continue):
                            continue_conditions.append(stmt.test)
                            break

            if not continue_conditions:
                return None

            # Combine multiple continue conditions with OR
            if len(continue_conditions) == 1:
                condition_str = ast.unparse(continue_conditions[0])
            else:
                # Multiple conditions: any can trigger continue
                conditions_str = ' or '.join(f"({ast.unparse(c)})" for c in continue_conditions)
                condition_str = conditions_str

            # Create filter function
            filter_code = f"""
def continue_filter({loop_var}):
    '''Check if iteration should be skipped (continue).'''
    return not ({condition_str})
"""

            exec_globals = {}
            exec_locals = {}
            exec(filter_code, exec_globals, exec_locals)

            logger.info(f"Created continue filter for condition: {condition_str}")
            return exec_locals['continue_filter']

        except Exception as e:
            logger.debug(f"Failed to create continue filter: {e}")
            return None

    def _create_loop_body_function(
        self,
        for_loop: ast.For,
        loop_var: str,
        accumulator_var: str,
        func_globals: dict
    ) -> Optional[Callable]:
        """
        Create the loop body as a standalone function.

        Rewrites accumulator references to partial_result for parallel aggregation.

        Args:
            for_loop: For loop AST node
            loop_var: Name of loop variable
            accumulator_var: Name of accumulator variable
            func_globals: Global scope from original function

        Returns:
            Callable that executes one iteration of the loop
        """
        try:
            # Clone and rewrite loop body
            loop_body_stmts = []

            for stmt in for_loop.body:
                # Skip break and continue statements (handled by filters)
                if isinstance(stmt, ast.If):
                    # Check if it's a break/continue statement
                    has_break_or_continue = False
                    for body_stmt in stmt.body:
                        if isinstance(body_stmt, (ast.Break, ast.Continue)):
                            has_break_or_continue = True
                            break

                    if has_break_or_continue:
                        # Skip this if statement (handled by filters)
                        continue

                # Rewrite accumulator references
                rewritten_stmt = self._rewrite_accumulator(stmt, accumulator_var, 'partial_result')
                loop_body_stmts.append(rewritten_stmt)

            # Generate loop body function code
            if loop_body_stmts:
                body_code = ast.unparse(ast.Module(body=loop_body_stmts, type_ignores=[]))
            else:
                # Empty body after filtering - just accumulate the index
                body_code = f"    partial_result += {loop_var}"

            func_code = f"""
def loop_body({loop_var}):
    '''Execute one iteration of the loop.'''
    partial_result = 0
{textwrap.indent(body_code, '    ')}
    return partial_result
"""

            # Compile function in proper scope
            exec_globals = func_globals.copy()
            exec_locals = {}
            exec(func_code, exec_globals, exec_locals)

            logger.debug(f"Created loop body function for variable '{loop_var}'")
            return exec_locals['loop_body']

        except Exception as e:
            logger.error(f"Failed to create loop body function: {e}")
            return None

    def _rewrite_accumulator(self, node, old_name: str, new_name: str):
        """
        Rewrite accumulator variable references in AST node.

        Changes references from old_name to new_name.

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
                if node.id == old_name:
                    return ast.Name(id=new_name, ctx=node.ctx)
                return node

        # Deep copy to avoid modifying original
        node_copy = copy.deepcopy(node)
        rewriter = AccumulatorRewriter()
        return rewriter.visit(node_copy)
