"""
While Loop Transformer - Transform While Loops for Parallel Execution

Transforms while loops into parallelizable versions using generator-based
chunking or bounded iteration strategies.

Author: Epochly Development Team
Date: November 18, 2025
"""

import ast
import inspect
import textwrap
import functools
from typing import Callable, Optional, Dict, Any, List

from ..utils.logger import get_logger
from .while_loop_analyzer import WhileLoopAnalysis, analyze_while_loop
from .source_extractor import SourceExtractor

logger = get_logger(__name__)


class WhileLoopTransformer:
    """
    Transforms while loops for parallel execution.

    Strategies:
    1. Bounded: Convert to for-range when bounds can be determined
    2. Generator: Use generator with sentinel-based chunking
    3. Skip: Leave as sequential for complex patterns
    """

    def __init__(self, batch_dispatcher=None, max_iterations: int = 1000000):
        """
        Initialize transformer.

        Args:
            batch_dispatcher: Batch dispatcher for parallel execution
            max_iterations: Maximum iterations safety limit
        """
        self.batch_dispatcher = batch_dispatcher
        self.max_iterations = max_iterations

    def transform_function(
        self,
        func: Callable,
        analysis: Optional[WhileLoopAnalysis] = None
    ) -> Optional[Callable]:
        """
        Transform a function containing a while loop.

        Args:
            func: Function to transform
            analysis: Pre-computed analysis or None to analyze

        Returns:
            Transformed function or None if not transformable
        """
        try:
            # Analyze if not provided
            if analysis is None:
                analysis = analyze_while_loop(func)

            if not analysis.has_while_loop or not analysis.is_parallelizable:
                logger.debug(f"While loop in {func.__name__} not parallelizable")
                return None

            # Choose transformation based on strategy
            if analysis.transformation_strategy == 'bounded':
                return self._transform_bounded_while(func, analysis)
            elif analysis.transformation_strategy == 'generator':
                return self._transform_generator_while(func, analysis)
            else:
                logger.debug(f"No transformation strategy for {func.__name__}")
                return None

        except Exception as e:
            logger.error(f"Failed to transform while loop: {e}")
            return None

    def _transform_bounded_while(
        self,
        func: Callable,
        analysis: WhileLoopAnalysis
    ) -> Optional[Callable]:
        """
        Transform while loop with bounded iterations.

        Pattern:
            i = 0
            while i < n:
                result += compute(i)
                i += 1

        Becomes:
            for i in range(n):
                result += compute(i)

        Args:
            func: Function to transform
            analysis: While loop analysis

        Returns:
            Transformed function
        """
        try:
            # Get source using SourceExtractor for notebook reliability
            source = SourceExtractor.get_source(func)
            if source is None:
                logger.debug(f"SourceExtractor failed for {func.__name__}")
                return None
            # Source is already dedented by SourceExtractor
            tree = ast.parse(source)

            # Find function definition
            func_def = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func.__name__:
                    func_def = node
                    break

            if not func_def:
                return None

            # Find while loop
            while_node = None
            for stmt in func_def.body:
                if isinstance(stmt, ast.While):
                    while_node = stmt
                    break

            if not while_node:
                return None

            # Extract loop bounds if possible
            loop_bound = self._extract_loop_bound(while_node, analysis.loop_variable)
            if not loop_bound:
                logger.debug("Cannot extract loop bound for bounded transformation")
                return None

            # Create wrapper
            @functools.wraps(func)
            def bounded_while_transformed(*args, **kwargs):
                """
                Parallel version of bounded while loop.
                """
                try:
                    # Get bound from arguments
                    if not args:
                        return func(*args, **kwargs)

                    n = args[0] if len(args) > 0 else self.max_iterations

                    # Safety check
                    if not isinstance(n, int) or n <= 0:
                        return func(*args, **kwargs)

                    # Too small for parallelization
                    if n < 100:
                        return func(*args, **kwargs)

                    # Extract and execute loop body in parallel
                    loop_body = self._extract_while_body(func, while_node, analysis)
                    if not loop_body:
                        return func(*args, **kwargs)

                    # Dispatch to workers
                    if self.batch_dispatcher:
                        partial_results = self.batch_dispatcher.dispatch_loop(
                            loop_body,
                            start=0,
                            end=min(n, self.max_iterations),
                            step=1
                        )
                        return sum(partial_results)
                    else:
                        # Sequential fallback
                        result = 0
                        for i in range(min(n, self.max_iterations)):
                            result += loop_body(i)
                        return result

                except Exception as e:
                    logger.debug(f"Bounded while transformation failed: {e}")
                    return func(*args, **kwargs)

            # Mark as transformed
            bounded_while_transformed._epochly_transformed = True
            bounded_while_transformed._original_function = func
            bounded_while_transformed._transformation_type = 'bounded_while'

            logger.info(f"Transformed bounded while loop in {func.__name__}")
            return bounded_while_transformed

        except Exception as e:
            logger.error(f"Failed bounded while transformation: {e}")
            return None

    def _transform_generator_while(
        self,
        func: Callable,
        analysis: WhileLoopAnalysis
    ) -> Optional[Callable]:
        """
        Transform while loop using generator-based chunking.

        Pattern:
            while condition():
                result += work()

        Becomes:
            Generate chunks of work items
            Dispatch chunks to workers
            Aggregate results

        Args:
            func: Function to transform
            analysis: While loop analysis

        Returns:
            Transformed function
        """
        try:
            # Generator-based while transformation requires runtime condition
            # evaluation which is complex to implement statically. Falls back
            # to standard execution for these patterns.
            logger.debug("Generator-based while transformation deferred to runtime")
            return None

        except Exception as e:
            logger.error(f"Failed generator while transformation: {e}")
            return None

    def _extract_loop_bound(
        self,
        while_node: ast.While,
        loop_variable: Optional[str]
    ) -> Optional[str]:
        """
        Extract loop bound from while condition.

        Args:
            while_node: While loop AST node
            loop_variable: Name of loop variable

        Returns:
            Bound expression or None
        """
        try:
            condition = while_node.test

            # Simple comparison: i < n
            if isinstance(condition, ast.Compare):
                if len(condition.comparators) == 1:
                    left = condition.left
                    if isinstance(left, ast.Name) and left.id == loop_variable:
                        # Extract the bound
                        comparator = condition.comparators[0]
                        if isinstance(comparator, ast.Name):
                            return comparator.id
                        elif isinstance(comparator, ast.Constant):
                            return str(comparator.value)

            return None

        except Exception:
            return None

    def _extract_while_body(
        self,
        func: Callable,
        while_node: ast.While,
        analysis: WhileLoopAnalysis
    ) -> Optional[Callable]:
        """
        Extract while loop body as a callable function.

        Args:
            func: Original function
            while_node: While loop AST node
            analysis: While loop analysis

        Returns:
            Callable that executes loop body for one iteration
        """
        try:
            loop_var = analysis.loop_variable or 'i'
            accumulator = analysis.accumulator_var or 'result'

            # Extract body statements (skip increment statements)
            body_stmts = []
            for stmt in while_node.body:
                # Skip loop variable increment (i += 1, i = i + 1)
                if isinstance(stmt, ast.AugAssign):
                    if isinstance(stmt.target, ast.Name) and stmt.target.id == loop_var:
                        continue
                elif isinstance(stmt, ast.Assign):
                    # Skip i = i + 1 pattern
                    skip = False
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == loop_var:
                            skip = True
                            break
                    if skip:
                        continue

                # Rewrite accumulator references
                body_stmts.append(self._rewrite_accumulator(stmt, accumulator, 'partial_result'))

            # Generate loop body code
            if body_stmts:
                body_code = ast.unparse(ast.Module(body=body_stmts, type_ignores=[]))
            else:
                body_code = f"    partial_result += {loop_var}"

            # Create loop body function
            func_code = f"""
def while_loop_body({loop_var}):
    '''Execute one iteration of while loop body.'''
    partial_result = 0
{textwrap.indent(body_code, '    ')}
    return partial_result
"""

            # Compile in function's scope
            exec_globals = func.__globals__.copy()
            exec_locals = {}
            exec(func_code, exec_globals, exec_locals)

            return exec_locals['while_loop_body']

        except Exception as e:
            logger.error(f"Failed to extract while body: {e}")
            return None

    def _rewrite_accumulator(self, node, old_name: str, new_name: str):
        """
        Rewrite accumulator variable references.

        Args:
            node: AST node to rewrite
            old_name: Old variable name
            new_name: New variable name

        Returns:
            Rewritten AST node
        """
        import copy

        class AccumulatorRewriter(ast.NodeTransformer):
            def visit_Name(self, node):
                if node.id == old_name:
                    return ast.Name(id=new_name, ctx=node.ctx)
                return node

        node_copy = copy.deepcopy(node)
        rewriter = AccumulatorRewriter()
        return rewriter.visit(node_copy)


def transform_while_loop(
    func: Callable,
    batch_dispatcher=None,
    max_iterations: int = 1000000
) -> Optional[Callable]:
    """
    Convenience function to transform while loops.

    Args:
        func: Function to transform
        batch_dispatcher: Batch dispatcher for parallel execution
        max_iterations: Maximum iterations safety limit

    Returns:
        Transformed function or None
    """
    transformer = WhileLoopTransformer(batch_dispatcher, max_iterations)
    return transformer.transform_function(func)