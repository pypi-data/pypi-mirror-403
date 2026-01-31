"""
Break/Continue Pattern Analyzer - AST Analysis for Control Flow

Analyzes loops containing break and continue statements to determine
if they can be safely parallelized using early filtering strategies.

Author: Epochly Development Team
Date: November 18, 2025
"""

import ast
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BreakContinueAnalysis:
    """
    Analysis result for break/continue patterns in a loop.

    Attributes:
        has_break: Whether loop contains break statement(s)
        has_continue: Whether loop contains continue statement(s)
        break_count: Number of break statements
        continue_count: Number of continue statements
        break_condition: AST node of break condition (if simple)
        continue_conditions: List of AST nodes for continue conditions
        break_condition_complexity: Complexity of break condition ('simple', 'moderate', 'complex')
        is_transformable: Whether pattern can be safely parallelized
        transformation_strategy: Strategy to use ('pre_filter', 'skip', 'early_terminate')
    """
    has_break: bool = False
    has_continue: bool = False
    break_count: int = 0
    continue_count: int = 0
    break_condition: Optional[ast.expr] = None
    continue_conditions: List[ast.expr] = None
    break_condition_complexity: str = 'none'
    is_transformable: bool = True
    transformation_strategy: str = 'none'

    def __post_init__(self):
        if self.continue_conditions is None:
            self.continue_conditions = []


class BreakContinueVisitor(ast.NodeVisitor):
    """
    AST visitor that detects break and continue statements in loops.

    Analyzes the complexity of conditions and determines if the loop
    can be parallelized using pre-filtering or other strategies.
    """

    def __init__(self, target_loop_depth: int = 1):
        """
        Initialize visitor.

        Args:
            target_loop_depth: Only analyze breaks/continues at this depth
                              (1 = outer loop, 2+ = nested loops)
        """
        self.target_loop_depth = target_loop_depth
        self.current_loop_depth = 0

        # Analysis results
        self.has_break = False
        self.has_continue = False
        self.break_count = 0
        self.continue_count = 0
        self.break_conditions = []
        self.continue_conditions = []

        # Track state-dependent breaks (not transformable)
        self.has_state_dependent_break = False
        self.has_cross_iteration_dependency = False

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
        """Visit break statement."""
        if self.current_loop_depth == self.target_loop_depth:
            self.has_break = True
            self.break_count += 1

            # Extract break condition from parent If node
            # This requires tracking the AST structure
            logger.debug(f"Found break at loop depth {self.current_loop_depth}")

        self.generic_visit(node)

    def visit_Continue(self, node):
        """Visit continue statement."""
        if self.current_loop_depth == self.target_loop_depth:
            self.has_continue = True
            self.continue_count += 1

            logger.debug(f"Found continue at loop depth {self.current_loop_depth}")

        self.generic_visit(node)


class BreakContinueAnalyzer:
    """
    Analyzer for break/continue patterns in loops.

    Determines if loops with break/continue can be parallelized and
    provides transformation strategies.
    """

    def __init__(self):
        """Initialize analyzer."""
        pass

    def analyze_loop(self, loop_node: ast.For, func_ast: ast.FunctionDef) -> BreakContinueAnalysis:
        """
        Analyze a for loop for break/continue patterns.

        Args:
            loop_node: AST node of the for loop
            func_ast: AST node of the containing function

        Returns:
            BreakContinueAnalysis with detected patterns and strategy
        """
        try:
            # Visit loop body to find break/continue
            # Note: We visit body statements directly (not the For node),
            # so breaks/continues are at depth 0, not depth 1
            visitor = BreakContinueVisitor(target_loop_depth=0)

            # Visit only the loop body
            for stmt in loop_node.body:
                visitor.visit(stmt)

            # Extract break conditions from If statements
            break_condition = None
            break_condition_complexity = 'none'
            continue_conditions = []

            if visitor.has_break:
                break_condition, break_condition_complexity = self._extract_break_condition(loop_node)

            if visitor.has_continue:
                continue_conditions = self._extract_continue_conditions(loop_node)

            # Determine if transformable
            is_transformable = self._is_transformable(
                visitor.has_break,
                visitor.has_continue,
                break_condition_complexity,
                visitor.has_state_dependent_break,
                visitor.has_cross_iteration_dependency
            )

            # Determine transformation strategy
            transformation_strategy = self._determine_strategy(
                visitor.has_break,
                visitor.has_continue,
                break_condition_complexity,
                is_transformable
            )

            return BreakContinueAnalysis(
                has_break=visitor.has_break,
                has_continue=visitor.has_continue,
                break_count=visitor.break_count,
                continue_count=visitor.continue_count,
                break_condition=break_condition,
                continue_conditions=continue_conditions,
                break_condition_complexity=break_condition_complexity,
                is_transformable=is_transformable,
                transformation_strategy=transformation_strategy
            )

        except Exception as e:
            logger.error(f"Failed to analyze loop for break/continue: {e}")
            return BreakContinueAnalysis()

    def _extract_break_condition(self, loop_node: ast.For) -> Tuple[Optional[ast.expr], str]:
        """
        Extract break condition from loop body.

        Looks for pattern: if condition: break

        Args:
            loop_node: For loop AST node

        Returns:
            Tuple of (condition AST node, complexity level)
        """
        try:
            for stmt in loop_node.body:
                if isinstance(stmt, ast.If):
                    # Check if body contains break
                    for body_stmt in stmt.body:
                        if isinstance(body_stmt, ast.Break):
                            # Found break condition
                            condition = stmt.test
                            complexity = self._assess_condition_complexity(condition)
                            return condition, complexity

            return None, 'none'

        except Exception as e:
            logger.debug(f"Failed to extract break condition: {e}")
            return None, 'complex'

    def _extract_continue_conditions(self, loop_node: ast.For) -> List[ast.expr]:
        """
        Extract continue conditions from loop body.

        Args:
            loop_node: For loop AST node

        Returns:
            List of condition AST nodes
        """
        conditions = []

        try:
            for stmt in loop_node.body:
                if isinstance(stmt, ast.If):
                    # Check if body contains continue
                    for body_stmt in stmt.body:
                        if isinstance(body_stmt, ast.Continue):
                            conditions.append(stmt.test)

        except Exception as e:
            logger.debug(f"Failed to extract continue conditions: {e}")

        return conditions

    def _assess_condition_complexity(self, condition: ast.expr) -> str:
        """
        Assess complexity of a condition expression.

        Args:
            condition: AST expression node

        Returns:
            Complexity level: 'simple', 'moderate', 'complex'
        """
        try:
            # Simple: Single comparison (i > 100, i % 2 == 0)
            if isinstance(condition, ast.Compare):
                # Check if involves loop variable only
                if len(condition.comparators) == 1:
                    return 'simple'
                else:
                    return 'moderate'

            # Moderate: Boolean operations with simple comparisons
            elif isinstance(condition, ast.BoolOp):
                return 'moderate'

            # Complex: Function calls, attribute access, etc.
            else:
                return 'complex'

        except Exception:
            return 'complex'

    def _is_transformable(
        self,
        has_break: bool,
        has_continue: bool,
        break_complexity: str,
        state_dependent: bool,
        cross_iteration: bool
    ) -> bool:
        """
        Determine if loop with break/continue is transformable.

        Args:
            has_break: Has break statement
            has_continue: Has continue statement
            break_complexity: Complexity of break condition
            state_dependent: Break depends on accumulated state
            cross_iteration: Dependencies across iterations

        Returns:
            True if can be safely transformed
        """
        # Can't transform state-dependent or cross-iteration patterns
        if state_dependent or cross_iteration:
            return False

        # Continue statements are generally transformable (filtering)
        if has_continue and not has_break:
            return True

        # Break with simple/moderate conditions can be pre-filtered
        if has_break and break_complexity in ('simple', 'moderate'):
            return True

        # Complex break conditions - skip transformation
        if has_break and break_complexity == 'complex':
            return False

        # Both break and continue - more complex
        if has_break and has_continue:
            # Only if break is simple
            return break_complexity == 'simple'

        return True

    def _determine_strategy(
        self,
        has_break: bool,
        has_continue: bool,
        break_complexity: str,
        is_transformable: bool
    ) -> str:
        """
        Determine transformation strategy.

        Args:
            has_break: Has break statement
            has_continue: Has continue statement
            break_complexity: Complexity of break condition
            is_transformable: Whether transformable

        Returns:
            Strategy name: 'pre_filter', 'skip', 'none'
        """
        if not is_transformable:
            return 'skip'

        if has_break and break_complexity in ('simple', 'moderate'):
            return 'pre_filter'

        if has_continue:
            return 'pre_filter'

        if has_break and has_continue:
            return 'pre_filter' if break_complexity == 'simple' else 'skip'

        return 'none'


def analyze_break_continue(loop_node: ast.For, func_ast: ast.FunctionDef) -> BreakContinueAnalysis:
    """
    Convenience function to analyze break/continue patterns.

    Args:
        loop_node: For loop AST node
        func_ast: Function AST node

    Returns:
        BreakContinueAnalysis result
    """
    analyzer = BreakContinueAnalyzer()
    return analyzer.analyze_loop(loop_node, func_ast)
