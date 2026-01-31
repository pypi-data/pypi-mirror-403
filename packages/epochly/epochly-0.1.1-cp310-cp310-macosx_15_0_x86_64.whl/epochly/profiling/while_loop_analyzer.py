"""
While Loop Analyzer - Detection and Analysis of While Loops for Parallelization

Analyzes while loops to determine if they can be safely parallelized using
generator-based chunking strategies.

Author: Epochly Development Team
Date: November 18, 2025
"""

import ast
import inspect
import textwrap
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass

from ..utils.logger import get_logger
from .source_extractor import SourceExtractor

logger = get_logger(__name__)


@dataclass
class WhileLoopAnalysis:
    """
    Analysis result for a while loop.

    Attributes:
        has_while_loop: Whether function contains a while loop
        is_parallelizable: Whether the while loop can be parallelized
        condition_type: Type of condition ('simple', 'complex', 'stateful')
        loop_variable: Variable that changes in loop (if detectable)
        accumulator_var: Accumulator variable (if detectable)
        has_break: Whether loop contains break statements
        has_continue: Whether loop contains continue statements
        estimated_max_iterations: Max iteration estimate (for safety)
        transformation_strategy: Strategy to use ('generator', 'skip', 'bounded')
    """
    has_while_loop: bool = False
    is_parallelizable: bool = False
    condition_type: str = 'none'
    loop_variable: Optional[str] = None
    accumulator_var: Optional[str] = None
    has_break: bool = False
    has_continue: bool = False
    estimated_max_iterations: Optional[int] = None
    transformation_strategy: str = 'skip'


class WhileLoopVisitor(ast.NodeVisitor):
    """
    AST visitor to analyze while loops.
    """

    def __init__(self):
        """Initialize visitor."""
        self.has_while = False
        self.while_nodes = []
        self.current_depth = 0
        self.has_break = False
        self.has_continue = False
        self.modified_vars = set()
        self.used_vars = set()

    def visit_While(self, node):
        """Visit while loop node."""
        self.has_while = True
        self.while_nodes.append(node)
        self.current_depth += 1

        # Analyze condition
        self._analyze_condition(node.test)

        # Visit body
        self.generic_visit(node)
        self.current_depth -= 1

    def visit_Break(self, node):
        """Track break statements."""
        if self.current_depth > 0:
            self.has_break = True
        self.generic_visit(node)

    def visit_Continue(self, node):
        """Track continue statements."""
        if self.current_depth > 0:
            self.has_continue = True
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        """Track augmented assignments (+=, -=, etc.)."""
        if isinstance(node.target, ast.Name):
            self.modified_vars.add(node.target.id)
        self.generic_visit(node)

    def visit_Assign(self, node):
        """Track assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.modified_vars.add(target.id)
        self.generic_visit(node)

    def _analyze_condition(self, condition):
        """Analyze the while loop condition."""
        # Extract variables used in condition
        class VarExtractor(ast.NodeVisitor):
            def __init__(self):
                self.vars = set()

            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    self.vars.add(node.id)

        extractor = VarExtractor()
        extractor.visit(condition)
        self.used_vars.update(extractor.vars)


class WhileLoopAnalyzer:
    """
    Analyzer for while loops to determine parallelization strategy.
    """

    def __init__(self):
        """Initialize analyzer."""
        pass

    def analyze_function(self, func: Callable) -> WhileLoopAnalysis:
        """
        Analyze a function for while loops.

        Args:
            func: Function to analyze

        Returns:
            WhileLoopAnalysis with detection results
        """
        try:
            # Get source code using SourceExtractor for notebook reliability
            source = SourceExtractor.get_source(func)
            if source is None:
                logger.debug(f"SourceExtractor failed for {func.__name__}")
                return WhileLoopAnalysis()
            # Source is already dedented by SourceExtractor
            tree = ast.parse(source)

            # Find function definition
            func_def = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func.__name__:
                    func_def = node
                    break

            if not func_def:
                return WhileLoopAnalysis()

            # Visit function body
            visitor = WhileLoopVisitor()
            visitor.visit(func_def)

            if not visitor.has_while:
                return WhileLoopAnalysis()

            # Analyze first while loop
            while_node = visitor.while_nodes[0] if visitor.while_nodes else None
            if not while_node:
                return WhileLoopAnalysis()

            # Determine condition type
            condition_type = self._classify_condition(while_node.test, visitor)

            # Find loop variable (variable that changes in loop and is used in condition)
            loop_vars = visitor.modified_vars.intersection(visitor.used_vars)
            loop_variable = list(loop_vars)[0] if len(loop_vars) == 1 else None

            # Find accumulator (initialized before loop, modified in loop, but NOT the loop variable)
            accumulator_var = self._find_accumulator(func_def, while_node, visitor.modified_vars, exclude_var=loop_variable)

            # Determine if parallelizable
            is_parallelizable = self._is_parallelizable(
                condition_type,
                visitor.has_break,
                visitor.has_continue,
                loop_variable
            )

            # Determine transformation strategy
            strategy = self._determine_strategy(
                is_parallelizable,
                condition_type,
                visitor.has_break,
                loop_variable
            )

            return WhileLoopAnalysis(
                has_while_loop=True,
                is_parallelizable=is_parallelizable,
                condition_type=condition_type,
                loop_variable=loop_variable,
                accumulator_var=accumulator_var,
                has_break=visitor.has_break,
                has_continue=visitor.has_continue,
                estimated_max_iterations=1000000,  # Safety limit
                transformation_strategy=strategy
            )

        except Exception as e:
            logger.error(f"Failed to analyze while loop: {e}")
            return WhileLoopAnalysis()

    def _classify_condition(self, condition: ast.expr, visitor: WhileLoopVisitor) -> str:
        """
        Classify the complexity of a while loop condition.

        Args:
            condition: AST node of the condition
            visitor: WhileLoopVisitor with analysis data

        Returns:
            Condition type: 'simple', 'complex', 'stateful'
        """
        try:
            # Simple comparison (i < n)
            if isinstance(condition, ast.Compare):
                if len(condition.comparators) == 1:
                    # Check if involves loop variable
                    if isinstance(condition.left, ast.Name):
                        if condition.left.id in visitor.modified_vars:
                            return 'simple'
                return 'complex'

            # Boolean constant (while True)
            elif isinstance(condition, ast.Constant):
                if condition.value is True:
                    return 'infinite'  # Needs break to exit
                return 'simple'

            # Complex expression
            else:
                return 'complex'

        except Exception:
            return 'complex'

    def _find_accumulator(
        self,
        func_def: ast.FunctionDef,
        while_node: ast.While,
        modified_vars: set,
        exclude_var: Optional[str] = None
    ) -> Optional[str]:
        """
        Find accumulator variable for the while loop.

        Args:
            func_def: Function AST node
            while_node: While loop AST node
            modified_vars: Variables modified in loop
            exclude_var: Variable to exclude (typically the loop counter)

        Returns:
            Name of accumulator variable or None
        """
        try:
            # Look for variable initialized before loop and modified in loop
            # Exclude the loop variable (counter) from consideration
            for stmt in func_def.body:
                if stmt is while_node:
                    break

                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                    target = stmt.targets[0]
                    if isinstance(target, ast.Name):
                        var_name = target.id

                        # Skip if this is the loop variable
                        if var_name == exclude_var:
                            continue

                        # Check if modified in loop
                        if var_name in modified_vars:
                            # Check if initialized to 0 or empty collection
                            if isinstance(stmt.value, ast.Constant):
                                if stmt.value.value in (0, 0.0, [], ""):
                                    return var_name
                            elif isinstance(stmt.value, (ast.List, ast.Dict)):
                                return var_name

            return None

        except Exception:
            return None

    def _is_parallelizable(
        self,
        condition_type: str,
        has_break: bool,
        has_continue: bool,
        loop_variable: Optional[str]
    ) -> bool:
        """
        Determine if while loop can be parallelized.

        Args:
            condition_type: Type of condition
            has_break: Has break statement
            has_continue: Has continue statement
            loop_variable: Detected loop variable

        Returns:
            True if parallelizable
        """
        # Can't parallelize infinite loops without break
        if condition_type == 'infinite' and not has_break:
            return False

        # Can parallelize simple conditions with clear loop variable
        if condition_type == 'simple' and loop_variable:
            return True

        # Complex or stateful conditions are risky
        if condition_type in ('complex', 'stateful'):
            return False

        return False

    def _determine_strategy(
        self,
        is_parallelizable: bool,
        condition_type: str,
        has_break: bool,
        loop_variable: Optional[str]
    ) -> str:
        """
        Determine transformation strategy.

        Args:
            is_parallelizable: Whether loop is parallelizable
            condition_type: Type of condition
            has_break: Has break statement
            loop_variable: Loop variable name

        Returns:
            Strategy: 'generator', 'bounded', 'skip'
        """
        if not is_parallelizable:
            return 'skip'

        # Simple incrementing/decrementing loops can be bounded
        if condition_type == 'simple' and loop_variable:
            return 'bounded'

        # Infinite loops with break need generator approach
        if condition_type == 'infinite' and has_break:
            return 'generator'

        return 'skip'


def analyze_while_loop(func: Callable) -> WhileLoopAnalysis:
    """
    Convenience function to analyze while loops in a function.

    Args:
        func: Function to analyze

    Returns:
        WhileLoopAnalysis result
    """
    analyzer = WhileLoopAnalyzer()
    return analyzer.analyze_function(func)