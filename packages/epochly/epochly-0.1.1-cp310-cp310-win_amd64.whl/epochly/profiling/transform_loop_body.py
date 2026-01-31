"""
Transform Loop Body - Apply Break/Continue Transformations to Loop Bodies

Implements the actual transformation logic for loops with break and continue
statements, using pre-filtering and proper dispatch strategies.

Author: Epochly Development Team
Date: November 18, 2025
"""

import ast
import functools
import inspect
import textwrap
from typing import Callable, Optional, Dict, Any, List

from ..utils.logger import get_logger
from .loop_body_extractor import LoopBodyExtractor, ExtractedLoopBody
from .chunk_executor import execute_indices_on_func
from .source_extractor import SourceExtractor

logger = get_logger(__name__)

# Cache for nested loop analysis results to avoid re-parsing AST
_nested_loop_analysis_cache: Dict[tuple, Dict[str, Any]] = {}


class NestedLoopBreakContinueVisitor(ast.NodeVisitor):
    """
    AST visitor that detects break/continue statements and their loop depths.

    Used to determine if break/continue statements affect the outer loop
    (not parallelizable) or only inner loops (parallelizable).
    """

    def __init__(self):
        self.current_loop_depth = 0
        self.break_depths: List[int] = []
        self.continue_depths: List[int] = []

    def visit_For(self, node):
        """Visit for loop - track depth."""
        self.current_loop_depth += 1
        self.generic_visit(node)
        self.current_loop_depth -= 1

    def visit_While(self, node):
        """Visit while loop - track depth."""
        self.current_loop_depth += 1
        self.generic_visit(node)
        self.current_loop_depth -= 1

    def visit_Break(self, node):
        """Record break statement depth."""
        self.break_depths.append(self.current_loop_depth)
        self.generic_visit(node)

    def visit_Continue(self, node):
        """Record continue statement depth."""
        self.continue_depths.append(self.current_loop_depth)
        self.generic_visit(node)


def analyze_nested_loop_break_continue(func: Callable) -> Dict[str, Any]:
    """
    Analyze a function to determine break/continue locations in nested loops.

    Uses caching to avoid re-parsing AST for the same function.

    Args:
        func: Function to analyze

    Returns:
        Dictionary with:
        - has_nested_loops: Whether function contains nested loops
        - has_outer_break: Whether break affects outer loop
        - has_outer_continue: Whether continue affects outer loop
        - break_depths: List of loop depths where breaks occur
        - continue_depths: List of loop depths where continues occur
        - can_parallelize_outer: Whether outer loop can be safely parallelized
    """
    # Check cache first to avoid expensive AST parsing
    try:
        cache_key = (
            func.__code__.co_code,
            func.__code__.co_filename,
            func.__code__.co_firstlineno
        )
        if cache_key in _nested_loop_analysis_cache:
            logger.debug(f"Cache hit for {func.__name__} nested loop analysis")
            return _nested_loop_analysis_cache[cache_key]
    except (AttributeError, TypeError):
        cache_key = None  # Built-in functions don't have __code__

    try:
        # Use SourceExtractor for notebook reliability
        source = SourceExtractor.get_source(func)
        if source is None:
            return {'can_parallelize_outer': False, 'error': 'Source extraction failed'}
        # Source is already dedented by SourceExtractor
        tree = ast.parse(source)

        # Find the function definition
        func_def = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func.__name__:
                func_def = node
                break

        if not func_def:
            return {'can_parallelize_outer': False, 'error': 'No function definition found'}

        # Find the outer for loop
        outer_loop = None
        for stmt in func_def.body:
            if isinstance(stmt, ast.For):
                outer_loop = stmt
                break

        if not outer_loop:
            return {'can_parallelize_outer': False, 'error': 'No outer for loop found'}

        # Check if there are nested loops
        has_nested_loops = False
        for node in ast.walk(outer_loop):
            if node is not outer_loop and isinstance(node, (ast.For, ast.While)):
                has_nested_loops = True
                break

        # Analyze break/continue locations within the outer loop
        visitor = NestedLoopBreakContinueVisitor()
        # Start at depth 1 for the outer loop itself
        visitor.current_loop_depth = 1
        for stmt in outer_loop.body:
            visitor.visit(stmt)

        # Determine if outer loop is affected
        # Depth 1 = outer loop level, Depth 2+ = nested loops
        has_outer_break = any(depth == 1 for depth in visitor.break_depths)
        has_outer_continue = any(depth == 1 for depth in visitor.continue_depths)

        # Can parallelize if no break/continue affects the outer loop
        can_parallelize_outer = not has_outer_break and not has_outer_continue

        result = {
            'has_nested_loops': has_nested_loops,
            'has_outer_break': has_outer_break,
            'has_outer_continue': has_outer_continue,
            'break_depths': visitor.break_depths,
            'continue_depths': visitor.continue_depths,
            'can_parallelize_outer': can_parallelize_outer
        }

        # Cache the result for future calls
        if cache_key is not None:
            _nested_loop_analysis_cache[cache_key] = result

        return result

    except Exception as e:
        logger.debug(f"Failed to analyze nested loop break/continue: {e}")
        return {'can_parallelize_outer': False, 'error': str(e)}


def transform_loop_with_break_continue(
    func: Callable,
    analysis: Dict[str, Any],
    batch_dispatcher,
    min_iterations: int = 1000
) -> Optional[Callable]:
    """
    Transform a loop containing break/continue into a parallel version.

    Uses pre-filtering for break conditions and filtering for continue conditions
    to enable safe parallelization while maintaining correctness.

    Args:
        func: Original function to transform
        analysis: Loop analysis from RuntimeLoopTransformer
        batch_dispatcher: Batch dispatcher for parallel execution
        min_iterations: Minimum iterations for parallelization

    Returns:
        Transformed function or None if transformation failed
    """
    try:
        # Extract loop body and filters
        extractor = LoopBodyExtractor()
        extracted = extractor.extract_simple_loop(func, analysis)

        if not extracted:
            logger.debug(f"Failed to extract loop body from {func.__name__}")
            return None

        # Create transformed wrapper
        @functools.wraps(func)
        def transformed_wrapper(*args, **kwargs):
            """
            Parallelized version with break/continue support.

            Pre-filters indices for break conditions, applies continue
            filtering during execution, and aggregates partial results.
            """
            try:
                # Get iteration count from first argument (typical pattern)
                if not args:
                    return func(*args, **kwargs)

                n = args[0]
                if not isinstance(n, int) or n <= 0:
                    return func(*args, **kwargs)

                # For small workloads, use sequential
                if n < min_iterations:
                    logger.debug(f"Small workload ({n} < {min_iterations}), using sequential")
                    return func(*args, **kwargs)

                # Pre-filter indices based on break condition
                if extracted.break_filter:
                    # Apply break filter to get valid indices
                    valid_indices = extracted.break_filter(0, n)

                    if not valid_indices:
                        # Break on first iteration - return initial value
                        return 0

                    logger.debug(f"Break filter reduced {n} iterations to {len(valid_indices)}")
                else:
                    # No break - use all indices
                    valid_indices = list(range(n))

                # Apply continue filter if present
                if extracted.continue_filter:
                    # Filter out continued iterations
                    filtered_indices = [i for i in valid_indices if extracted.continue_filter(i)]
                    logger.debug(f"Continue filter reduced {len(valid_indices)} to {len(filtered_indices)} iterations")
                else:
                    filtered_indices = valid_indices

                if not filtered_indices:
                    # All iterations filtered out
                    return 0

                # Dispatch filtered work to parallel workers
                if batch_dispatcher:
                    # Split filtered indices into chunks for parallel execution
                    chunk_size = max(100, len(filtered_indices) // (8 * 4))  # 8 workers * 4 chunks each
                    chunks = []
                    for i in range(0, len(filtered_indices), chunk_size):
                        chunk = filtered_indices[i:i + chunk_size]
                        chunks.append(chunk)

                    # Prepare arguments for module-level executor
                    # Each chunk gets (loop_func, indices) tuple
                    chunk_args = [(extracted.loop_func, chunk) for chunk in chunks]

                    # Use multiprocessing.Pool directly if dispatcher fails
                    try:
                        # Try batch dispatcher first
                        partial_results = batch_dispatcher.dispatch_chunks(
                            execute_indices_on_func,
                            chunk_args
                        )
                    except Exception as e:
                        logger.debug(f"Batch dispatcher failed: {e}, using direct multiprocessing")
                        # Fallback: Use multiprocessing.Pool directly
                        import multiprocessing
                        with multiprocessing.Pool() as pool:
                            partial_results = pool.map(execute_indices_on_func, chunk_args)

                    # Aggregate results based on type
                    if extracted.aggregation_type == 'sum':
                        return sum(partial_results)
                    elif extracted.aggregation_type == 'max':
                        return max(partial_results) if partial_results else 0
                    elif extracted.aggregation_type == 'min':
                        return min(partial_results) if partial_results else 0
                    else:
                        # Default to sum
                        return sum(partial_results)

                else:
                    # No dispatcher - execute sequentially on filtered indices
                    result = 0
                    for idx in filtered_indices:
                        result += extracted.loop_func(idx)
                    return result

            except Exception as e:
                logger.debug(f"Transformation execution failed: {e}, falling back to original")
                return func(*args, **kwargs)

        # Mark as transformed
        transformed_wrapper._epochly_transformed = True
        transformed_wrapper._original_function = func
        transformed_wrapper._has_break = analysis.get('has_break', False)
        transformed_wrapper._has_continue = analysis.get('has_continue', False)

        logger.info(f"Successfully transformed {func.__name__} with break/continue support")
        return transformed_wrapper

    except Exception as e:
        logger.error(f"Failed to transform loop with break/continue: {e}")
        return None


def transform_nested_loop_with_patterns(
    func: Callable,
    analysis: Dict[str, Any],
    batch_dispatcher,
    min_iterations: int = 1000
) -> Optional[Callable]:
    """
    Transform nested loops that may contain break/continue patterns.

    Parallelizes outer loop when break/continue only affects inner loops.
    If break/continue affects the outer loop, returns None (not parallelizable).

    Args:
        func: Original function
        analysis: Loop analysis results
        batch_dispatcher: Batch dispatcher for parallel execution
        min_iterations: Minimum iterations threshold

    Returns:
        Transformed function or None if outer loop cannot be parallelized
    """
    try:
        # Analyze break/continue locations to determine if outer loop can be parallelized
        nested_analysis = analyze_nested_loop_break_continue(func)

        if 'error' in nested_analysis:
            logger.debug(f"Nested loop analysis failed for {func.__name__}: {nested_analysis.get('error')}")
            return None

        # If break/continue affects outer loop, cannot parallelize
        if not nested_analysis.get('can_parallelize_outer', False):
            if nested_analysis.get('has_outer_break'):
                logger.debug(f"Cannot parallelize {func.__name__}: break affects outer loop")
            if nested_analysis.get('has_outer_continue'):
                logger.debug(f"Cannot parallelize {func.__name__}: continue affects outer loop")
            return None

        # Log analysis results for debugging
        if nested_analysis.get('has_nested_loops'):
            logger.debug(
                f"Nested loop analysis for {func.__name__}: "
                f"break_depths={nested_analysis.get('break_depths', [])}, "
                f"continue_depths={nested_analysis.get('continue_depths', [])}, "
                f"can_parallelize_outer=True"
            )

        # Outer loop can be parallelized - extract and transform
        extractor = LoopBodyExtractor()
        extracted = extractor.extract_simple_loop(func, analysis)

        if not extracted:
            logger.warning(f"Failed to extract nested loop body from {func.__name__}")
            return None

        # Validate extracted loop function is callable
        if not callable(getattr(extracted, 'loop_func', None)):
            logger.warning(f"Extracted loop_func is not callable for {func.__name__}")
            return None

        # Create transformed wrapper for nested loops
        @functools.wraps(func)
        def transformed_nested_wrapper(*args, **kwargs):
            """
            Parallelized version of nested loop with inner break/continue preserved.

            The outer loop is parallelized while inner loops (with their break/continue)
            execute sequentially within each parallel task.
            """
            try:
                # Get iteration count from first argument (typical pattern)
                if not args:
                    return func(*args, **kwargs)

                n = args[0]
                if not isinstance(n, int) or n <= 0:
                    return func(*args, **kwargs)

                # For small workloads, use sequential
                if n < min_iterations:
                    logger.debug(f"Small nested workload ({n} < {min_iterations}), using sequential")
                    return func(*args, **kwargs)

                # All outer loop indices are valid (no outer break/continue)
                indices = list(range(n))

                # Dispatch work to parallel workers
                if batch_dispatcher:
                    # Split indices into chunks for parallel execution
                    chunk_size = max(100, len(indices) // (8 * 4))  # 8 workers * 4 chunks each
                    chunks = []
                    for i in range(0, len(indices), chunk_size):
                        chunk = indices[i:i + chunk_size]
                        chunks.append(chunk)

                    # Prepare arguments for module-level executor
                    chunk_args = [(extracted.loop_func, chunk) for chunk in chunks]

                    # Execute chunks in parallel
                    try:
                        partial_results = batch_dispatcher.dispatch_chunks(
                            execute_indices_on_func,
                            chunk_args
                        )
                    except Exception as e:
                        logger.debug(f"Batch dispatcher failed: {e}, using direct multiprocessing")
                        import multiprocessing
                        with multiprocessing.Pool() as pool:
                            partial_results = pool.map(execute_indices_on_func, chunk_args)

                    # Aggregate results based on type
                    if extracted.aggregation_type == 'sum':
                        return sum(partial_results)
                    elif extracted.aggregation_type == 'max':
                        return max(partial_results) if partial_results else 0
                    elif extracted.aggregation_type == 'min':
                        return min(partial_results) if partial_results else 0
                    else:
                        return sum(partial_results)

                else:
                    # No dispatcher - execute sequentially with proper aggregation
                    results = [extracted.loop_func(idx) for idx in indices]
                    if not results:
                        return 0
                    if extracted.aggregation_type == 'sum':
                        return sum(results)
                    elif extracted.aggregation_type == 'max':
                        return max(results)
                    elif extracted.aggregation_type == 'min':
                        return min(results)
                    else:
                        return sum(results)

            except Exception as e:
                logger.debug(f"Nested transformation execution failed: {e}, falling back to original")
                return func(*args, **kwargs)

        # Mark as transformed
        transformed_nested_wrapper._epochly_transformed = True
        transformed_nested_wrapper._original_function = func
        transformed_nested_wrapper._nested_analysis = nested_analysis
        transformed_nested_wrapper._has_nested_loops = nested_analysis.get('has_nested_loops', False)

        logger.info(
            f"Successfully transformed nested loop {func.__name__} "
            f"(inner break/continue preserved, outer parallelized)"
        )
        return transformed_nested_wrapper

    except Exception as e:
        logger.error(f"Failed to transform nested loop with patterns: {e}")
        return None