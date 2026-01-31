"""
CUDA Pattern Detector for Epochly LEVEL_4 GPU Loop Acceleration

Analyzes Python function AST to detect parallelizable loop patterns
(stencil, map, reduce, scan, matmul, transpose, gather, scatter, histogram,
filter, convolution, outer) suitable for GPU acceleration via Numba CUDA JIT.

This module implements the Pattern Detection phase of the GPU Loop Acceleration
design thesis, enabling automatic identification of code patterns that can be
safely and efficiently executed on GPU.

Author: Epochly Development Team
"""

from __future__ import annotations

import ast
import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from ..profiling.source_extractor import SourceExtractor

# Import modular pattern detection system (Phase 1: FFT, Rolling Stats, Black-Scholes, Monte Carlo)
from .patterns import (
    create_default_registry,
    FFTInfo,
    RollingStatsInfo,
    BlackScholesInfo,
    MonteCarloInfo,
)

logger = logging.getLogger(__name__)


@dataclass
class ExprSpec:
    """Specification of an expression extracted from AST."""
    src: str  # Normalized expression string
    input_arrays: List[str] = field(default_factory=list)
    scalar_vars: List[str] = field(default_factory=list)


@dataclass
class LoopDomain:
    """Loop domain specification."""
    index_vars: Tuple[str, ...] = field(default_factory=tuple)
    bounds_src: Tuple[str, ...] = field(default_factory=tuple)


@dataclass
class StencilInfo:
    """Information about a detected stencil pattern."""

    stencil_type: str = 'unknown'  # '5-point', '9-point', 'custom'
    dimensions: int = 0
    radius: int = 1
    neighbor_offsets: List[Tuple[int, ...]] = field(default_factory=list)
    input_arrays: List[str] = field(default_factory=list)
    output_array: Optional[str] = None
    loop_bounds: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class MapInfo:
    """Information about a detected map pattern."""

    dimensions: int = 1
    operation_complexity: str = 'simple'  # 'simple', 'moderate', 'complex'
    has_conditionals: bool = False
    input_arrays: List[str] = field(default_factory=list)
    output_array: Optional[str] = None
    math_operations: List[str] = field(default_factory=list)
    expr_spec: Optional[ExprSpec] = None
    loop_domain: Optional[LoopDomain] = None


@dataclass
class ReduceInfo:
    """Information about a detected reduce pattern."""

    operation: str = 'unknown'  # 'sum', 'max', 'min', 'product'
    is_associative: bool = False
    is_commutative: bool = False
    identity_element: Optional[float] = None
    accumulator_var: Optional[str] = None
    input_array: Optional[str] = None
    input_expr: Optional[ExprSpec] = None


@dataclass
class ScanInfo:
    """Information about a detected scan/prefix pattern."""
    operation: str = 'sum'  # 'sum', 'product', 'max', 'min'
    is_inclusive: bool = True
    input_array: Optional[str] = None
    output_array: Optional[str] = None
    axis: int = 0
    input_expr: Optional[ExprSpec] = None


@dataclass
class MatMulInfo:
    """Information about a detected matrix multiplication pattern."""
    left_matrix: Optional[str] = None
    right_matrix: Optional[str] = None
    output_matrix: Optional[str] = None
    transpose_left: bool = False
    transpose_right: bool = False


@dataclass
class TransposeInfo:
    """Information about a detected transpose pattern."""
    input_array: Optional[str] = None
    output_array: Optional[str] = None
    axes: Tuple[int, ...] = (1, 0)


@dataclass
class GatherInfo:
    """Information about a detected gather pattern."""
    input_array: Optional[str] = None
    index_array: Optional[str] = None
    output_array: Optional[str] = None


@dataclass
class ScatterInfo:
    """Information about a detected scatter pattern."""
    input_array: Optional[str] = None
    index_array: Optional[str] = None
    output_array: Optional[str] = None
    operation: str = 'assign'  # 'assign', 'add', 'max', 'min'


@dataclass
class HistogramInfo:
    """Information about a detected histogram pattern."""
    input_array: Optional[str] = None
    bins_array: Optional[str] = None
    is_weighted: bool = False
    weights_array: Optional[str] = None


@dataclass
class FilterInfo:
    """Information about a detected filter/compact pattern."""
    input_array: Optional[str] = None
    output_array: Optional[str] = None
    predicate_src: Optional[str] = None
    has_transform: bool = False
    transform_expr: Optional[ExprSpec] = None


@dataclass
class ConvolutionInfo:
    """Information about a detected convolution pattern."""
    dimensions: int = 1
    kernel_size: Tuple[int, ...] = field(default_factory=lambda: (3,))
    input_array: Optional[str] = None
    kernel_array: Optional[str] = None
    output_array: Optional[str] = None


@dataclass
class OuterInfo:
    """Information about a detected outer product pattern."""
    left_vector: Optional[str] = None
    right_vector: Optional[str] = None
    output_matrix: Optional[str] = None
    operation: str = 'multiply'


@dataclass
class CompareSwapInfo:
    """Information about a detected compare-swap pattern (sorting networks)."""
    array: Optional[str] = None
    is_parallel_phase: bool = False  # True for odd-even sort phases
    step: int = 1  # Loop step size (2 for odd-even sort)


@dataclass
class PatternAnalysis:
    """Result of pattern analysis for a function."""

    pattern_type: str = 'unknown'  # 'stencil', 'map', 'reduce', 'scan', 'matmul', 'transpose', 'gather', 'scatter', 'histogram', 'filter', 'convolution', 'outer', 'fft', 'rolling_stats', 'black_scholes', 'monte_carlo', 'unknown'
    parallelizable: bool = False
    confidence: float = 0.0
    dimensions: int = 0
    memory_pattern: str = 'unknown'  # 'coalesced', 'strided', 'random'
    has_loop_carried_dependency: bool = False
    rejection_reason: str = ''
    # Loop-based pattern info (existing)
    stencil_info: Optional[StencilInfo] = None
    map_info: Optional[MapInfo] = None
    reduce_info: Optional[ReduceInfo] = None
    scan_info: Optional[ScanInfo] = None
    matmul_info: Optional[MatMulInfo] = None
    transpose_info: Optional[TransposeInfo] = None
    gather_info: Optional[GatherInfo] = None
    scatter_info: Optional[ScatterInfo] = None
    histogram_info: Optional[HistogramInfo] = None
    filter_info: Optional[FilterInfo] = None
    convolution_info: Optional[ConvolutionInfo] = None
    outer_info: Optional[OuterInfo] = None
    compare_swap_info: Optional[CompareSwapInfo] = None
    # Modular pattern info (Phase 1: spectral, time series, financial)
    fft_info: Optional[FFTInfo] = None
    rolling_stats_info: Optional[RollingStatsInfo] = None
    black_scholes_info: Optional[BlackScholesInfo] = None
    monte_carlo_info: Optional[MonteCarloInfo] = None
    function_name: str = ''
    source_lines: int = 0


class LoopAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze loop structures and access patterns."""

    def __init__(self):
        self.loops: List[ast.For] = []
        self.while_loops: List[ast.While] = []
        self.loop_depth: int = 0
        self.max_loop_depth: int = 0
        self.array_reads: Dict[str, List[Tuple[int, ...]]] = {}
        self.array_writes: Dict[str, List[Tuple[int, ...]]] = {}
        self.loop_vars: List[str] = []
        self.has_raise: bool = False
        self.has_print: bool = False
        self.has_function_call: bool = False
        self.has_function_call_in_loop: bool = False  # Only calls INSIDE loops
        self.function_calls: List[str] = []
        self.function_calls_in_loop: List[str] = []  # Track calls inside loops separately
        self.has_recursion: bool = False
        # Additional rejection conditions (Dec 2025 mcp-reflect recommendation)
        self.has_break: bool = False
        self.has_continue: bool = False
        self.has_return_in_loop: bool = False
        self.has_try_except: bool = False
        self.has_yield: bool = False
        self.has_comprehension_in_loop: bool = False
        self.function_name: Optional[str] = None
        self.accumulator_ops: List[Tuple[str, str]] = []  # (var, op) pairs
        self.conditionals_in_loop: bool = False
        self.nested_functions: List[str] = []
        self.current_loop_vars: List[str] = []
        self.assignments: List[ast.Assign] = []
        self.aug_assignments: List[ast.AugAssign] = []
        self.has_tuple_swap: bool = False  # Detect a[i], a[i+1] = a[i+1], a[i] pattern
        self.loop_step: int = 1  # Step size of innermost loop (for odd-even sort)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track function definition for recursion detection."""
        if self.function_name is None:
            self.function_name = node.name
            self.generic_visit(node)
        else:
            # Nested function definition
            self.nested_functions.append(node.name)
            self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Analyze for loop."""
        self.loops.append(node)
        self.loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)

        # Track loop variable
        if isinstance(node.target, ast.Name):
            self.loop_vars.append(node.target.id)
            self.current_loop_vars.append(node.target.id)

        # Detect loop step size from range() call
        if isinstance(node.iter, ast.Call):
            if isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                # range(start, end, step) has 3 args
                if len(node.iter.args) >= 3:
                    step_arg = node.iter.args[2]
                    if isinstance(step_arg, ast.Constant):
                        self.loop_step = step_arg.value

        self.generic_visit(node)

        self.loop_depth -= 1
        if isinstance(node.target, ast.Name) and self.current_loop_vars:
            self.current_loop_vars.pop()

    def visit_While(self, node: ast.While) -> None:
        """Analyze while loop."""
        self.while_loops.append(node)
        self.loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_Raise(self, node: ast.Raise) -> None:
        """Detect raise statements."""
        self.has_raise = True
        self.generic_visit(node)

    def visit_Break(self, node: ast.Break) -> None:
        """Detect break statements (not supported in CUDA kernels)."""
        self.has_break = True
        self.generic_visit(node)

    def visit_Continue(self, node: ast.Continue) -> None:
        """Detect continue statements (not supported in CUDA kernels)."""
        self.has_continue = True
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        """Detect return statements inside loops (problematic for parallelization)."""
        if self.loop_depth > 0:
            self.has_return_in_loop = True
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """Detect try/except blocks (not supported in CUDA kernels)."""
        self.has_try_except = True
        self.generic_visit(node)

    def visit_Yield(self, node: ast.Yield) -> None:
        """Detect yield statements (generators not supported in CUDA)."""
        self.has_yield = True
        self.generic_visit(node)

    def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
        """Detect yield from statements (generators not supported in CUDA)."""
        self.has_yield = True
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        """Detect list comprehensions inside loops."""
        if self.loop_depth > 0:
            self.has_comprehension_in_loop = True
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        """Detect set comprehensions inside loops."""
        if self.loop_depth > 0:
            self.has_comprehension_in_loop = True
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        """Detect dict comprehensions inside loops."""
        if self.loop_depth > 0:
            self.has_comprehension_in_loop = True
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        """Detect generator expressions inside loops."""
        if self.loop_depth > 0:
            self.has_comprehension_in_loop = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Analyze function calls."""
        func_name = self._get_call_name(node)

        if func_name:
            self.function_calls.append(func_name)

            # Check for print
            if func_name == 'print':
                self.has_print = True
            # Check for recursion
            elif func_name == self.function_name:
                self.has_recursion = True
            # Check for safe math functions
            elif func_name not in self._safe_functions():
                # Not in nested functions list means it's an external call
                if func_name not in self.nested_functions:
                    self.has_function_call = True
                    # CRITICAL: Only flag calls INSIDE loops as problematic for parallelization
                    # Calls outside loops (setup/teardown) don't affect parallelism
                    if self.loop_depth > 0:
                        self.has_function_call_in_loop = True
                        self.function_calls_in_loop.append(func_name)

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Analyze array subscript access patterns."""
        if isinstance(node.value, ast.Name):
            array_name = node.value.id
            offsets = self._extract_subscript_offsets(node.slice)

            if isinstance(node.ctx, ast.Load):
                if array_name not in self.array_reads:
                    self.array_reads[array_name] = []
                self.array_reads[array_name].append(offsets)
            elif isinstance(node.ctx, ast.Store):
                if array_name not in self.array_writes:
                    self.array_writes[array_name] = []
                self.array_writes[array_name].append(offsets)

        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """Detect accumulator patterns like total += x."""
        self.aug_assignments.append(node)

        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            if isinstance(node.op, ast.Add):
                self.accumulator_ops.append((var_name, 'sum'))
            elif isinstance(node.op, ast.Mult):
                self.accumulator_ops.append((var_name, 'product'))

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Detect max/min patterns and tuple swap patterns."""
        self.assignments.append(node)

        # Detect tuple swap pattern: arr[i], arr[j] = arr[j], arr[i]
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple):
            target_tuple = node.targets[0]
            if isinstance(node.value, ast.Tuple) and len(target_tuple.elts) == 2:
                # Check if both targets are subscripts to the same array
                t0, t1 = target_tuple.elts
                v0, v1 = node.value.elts
                if (isinstance(t0, ast.Subscript) and isinstance(t1, ast.Subscript) and
                    isinstance(v0, ast.Subscript) and isinstance(v1, ast.Subscript)):
                    # Check if same array and indices are swapped
                    if (isinstance(t0.value, ast.Name) and isinstance(t1.value, ast.Name) and
                        isinstance(v0.value, ast.Name) and isinstance(v1.value, ast.Name)):
                        if t0.value.id == t1.value.id == v0.value.id == v1.value.id:
                            # Same array - check if it looks like a swap
                            # t0.slice should match v1.slice and t1.slice should match v0.slice
                            self.has_tuple_swap = True

        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id

            # Check for max/min function calls
            if isinstance(node.value, ast.Call):
                func_name = self._get_call_name(node.value)
                if func_name == 'max':
                    # Check if target is one of the arguments (running max)
                    for arg in node.value.args:
                        if isinstance(arg, ast.Name) and arg.id == target_name:
                            self.accumulator_ops.append((target_name, 'max'))
                            break
                elif func_name == 'min':
                    for arg in node.value.args:
                        if isinstance(arg, ast.Name) and arg.id == target_name:
                            self.accumulator_ops.append((target_name, 'min'))
                            break

            # CRITICAL FIX (Dec 2025): Detect plain-assignment reductions
            # Pattern: acc = acc + arr[i] (not just acc += arr[i])
            # This is equivalent to augmented assignment but uses plain assignment
            elif isinstance(node.value, ast.BinOp):
                # Check for pattern: target = target OP something
                # e.g., acc = acc + x, total = total * factor
                if isinstance(node.value.left, ast.Name) and node.value.left.id == target_name:
                    # target = target OP something
                    if isinstance(node.value.op, ast.Add):
                        self.accumulator_ops.append((target_name, 'sum'))
                    elif isinstance(node.value.op, ast.Mult):
                        self.accumulator_ops.append((target_name, 'product'))
                elif isinstance(node.value.right, ast.Name) and node.value.right.id == target_name:
                    # Check for commutative ops: target = something OP target
                    if isinstance(node.value.op, ast.Add):
                        self.accumulator_ops.append((target_name, 'sum'))
                    elif isinstance(node.value.op, ast.Mult):
                        self.accumulator_ops.append((target_name, 'product'))

        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        """Detect conditionals in loops, including max/min patterns."""
        if self.loop_depth > 0:
            self.conditionals_in_loop = True

            # Check for max pattern: if arr[i] > max_val: max_val = arr[i]
            # Also handles scatter-max: if data[i] > result[idx]: result[idx] = data[i]
            if isinstance(node.test, ast.Compare) and len(node.test.ops) == 1:
                if isinstance(node.test.ops[0], ast.Gt):
                    # Check if body assigns to same variable/subscript being compared
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Assign):
                        assign = node.body[0]
                        if len(assign.targets) == 1:
                            target = assign.targets[0]
                            comparators = node.test.comparators

                            # Handle ast.Name targets (simple max)
                            if isinstance(target, ast.Name):
                                target_id = target.id
                                if comparators and isinstance(comparators[0], ast.Name):
                                    if comparators[0].id == target_id:
                                        self.accumulator_ops.append((target_id, 'max'))

                            # Handle ast.Subscript targets (scatter-max)
                            # Pattern: if data[i] > result[idx]: result[idx] = data[i]
                            elif isinstance(target, ast.Subscript):
                                # Check if the comparator is also a subscript to the same array
                                if comparators and isinstance(comparators[0], ast.Subscript):
                                    if isinstance(target.value, ast.Name) and isinstance(comparators[0].value, ast.Name):
                                        if target.value.id == comparators[0].value.id:
                                            # Same array, this is a max pattern
                                            self.accumulator_ops.append((target.value.id, 'max'))

                elif isinstance(node.test.ops[0], ast.Lt):
                    # Check for min pattern
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Assign):
                        assign = node.body[0]
                        if len(assign.targets) == 1:
                            target = assign.targets[0]
                            comparators = node.test.comparators

                            # Handle ast.Name targets
                            if isinstance(target, ast.Name):
                                target_id = target.id
                                if comparators and isinstance(comparators[0], ast.Name):
                                    if comparators[0].id == target_id:
                                        self.accumulator_ops.append((target_id, 'min'))

                            # Handle ast.Subscript targets (scatter-min)
                            elif isinstance(target, ast.Subscript):
                                if comparators and isinstance(comparators[0], ast.Subscript):
                                    if isinstance(target.value, ast.Name) and isinstance(comparators[0].value, ast.Name):
                                        if target.value.id == comparators[0].value.id:
                                            self.accumulator_ops.append((target.value.id, 'min'))

        self.generic_visit(node)

    def extract_rhs_expression(self, node: ast.AST) -> Optional[str]:
        """Extract the RHS expression from an assignment."""
        if isinstance(node, ast.Assign):
            return ast.unparse(node.value)
        elif isinstance(node, ast.AugAssign):
            # For +=, extract the RHS operand
            return ast.unparse(node.value)
        return None

    def extract_expression_spec(self, node: ast.AST, array_names: Set[str]) -> Optional[ExprSpec]:
        """Extract expression specification from an assignment node."""
        expr_str = self.extract_rhs_expression(node)
        if not expr_str:
            return None

        # Identify input arrays and scalar vars in the expression
        input_arrays = []
        scalar_vars = []

        # Simple heuristic: check if array names appear in expression
        for array_name in array_names:
            if array_name in expr_str:
                input_arrays.append(array_name)

        return ExprSpec(
            src=expr_str,
            input_arrays=input_arrays,
            scalar_vars=scalar_vars
        )

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """Extract function name from call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _safe_functions(self) -> Set[str]:
        """
        Return set of safe functions that can be used in parallelizable code.

        These functions are safe because they:
        1. Have no side effects (don't modify global state)
        2. Are deterministic (same input = same output)
        3. Can be executed independently on each GPU thread
        4. Are supported by Numba/CUDA JIT compilation

        Categories:
        - Python builtins: range, len, abs, min, max, etc.
        - Math functions: sin, cos, exp, log, sqrt, etc.
        - NumPy allocation: empty, zeros, ones, etc. (outside loops only)
        - NumPy utilities: copy, shape, dtype access

        Note: This list is comprehensive but not exhaustive. Custom functions
        that meet the criteria above can also be used.
        """
        return {
            # Python builtins - control flow and basic operations
            'range', 'len', 'abs', 'min', 'max', 'sum', 'round',
            'int', 'float', 'bool', 'complex',
            'enumerate', 'zip', 'reversed', 'sorted',
            'all', 'any', 'filter', 'map',
            'divmod', 'pow', 'hash', 'id',

            # Type conversions
            'str', 'bytes', 'bytearray', 'list', 'tuple', 'set', 'dict',

            # Math module functions - basic
            'sin', 'cos', 'tan', 'exp', 'log', 'log10', 'log2', 'sqrt', 'pow',
            'floor', 'ceil', 'fabs', 'trunc',

            # Math module functions - trigonometric
            'asin', 'acos', 'atan', 'atan2',
            'sinh', 'cosh', 'tanh',
            'asinh', 'acosh', 'atanh',
            'degrees', 'radians',
            'hypot',

            # Math module functions - special
            'erf', 'erfc', 'gamma', 'lgamma',
            'factorial', 'comb', 'perm',
            'gcd', 'lcm',
            'isfinite', 'isinf', 'isnan',
            'copysign', 'fmod', 'remainder',
            'ldexp', 'frexp', 'modf',

            # NumPy allocation functions (safe outside loops)
            'empty', 'empty_like', 'zeros', 'zeros_like', 'ones', 'ones_like',
            'full', 'full_like', 'copy', 'asarray', 'array',
            'arange', 'linspace', 'logspace', 'meshgrid',
            'eye', 'identity', 'diag', 'diagflat',

            # NumPy utility functions
            'shape', 'size', 'ndim', 'dtype',
            'reshape', 'flatten', 'ravel', 'squeeze', 'expand_dims',
            'transpose', 'swapaxes', 'moveaxis',
            'concatenate', 'stack', 'vstack', 'hstack', 'dstack',
            'split', 'hsplit', 'vsplit', 'dsplit',

            # NumPy math (element-wise, GPU-acceleratable)
            'sqrt', 'square', 'cbrt', 'power',
            'exp', 'exp2', 'expm1', 'log', 'log2', 'log10', 'log1p',
            'sin', 'cos', 'tan', 'arcsin', 'arccos', 'arctan', 'arctan2',
            'sinh', 'cosh', 'tanh', 'arcsinh', 'arccosh', 'arctanh',
            'floor', 'ceil', 'trunc', 'rint', 'round',
            'abs', 'absolute', 'fabs', 'sign', 'negative', 'positive',
            'reciprocal', 'divide', 'multiply', 'add', 'subtract',
            'mod', 'fmod', 'remainder', 'divmod',
            'clip', 'minimum', 'maximum', 'fmin', 'fmax',

            # NumPy reduction functions
            'sum', 'prod', 'mean', 'std', 'var',
            'min', 'max', 'argmin', 'argmax', 'ptp',
            'cumsum', 'cumprod', 'diff',

            # NumPy boolean operations
            'logical_and', 'logical_or', 'logical_not', 'logical_xor',
            'greater', 'greater_equal', 'less', 'less_equal',
            'equal', 'not_equal', 'isclose', 'allclose',

            # NumPy special values
            'isfinite', 'isinf', 'isnan', 'isneginf', 'isposinf',
            'nan_to_num', 'real', 'imag', 'conj', 'angle',

            # Conditional/masking (Dec 2025 mcp-reflect recommendation)
            'where', 'select', 'heaviside', 'signbit',

            # Bitwise operations (Dec 2025 mcp-reflect recommendation)
            'bitwise_and', 'bitwise_or', 'bitwise_xor', 'bitwise_not',
            'left_shift', 'right_shift', 'invert',

            # Additional division operations
            'floor_divide', 'true_divide',
        }

    def _safe_functions_in_loop(self) -> Set[str]:
        """
        Return set of functions that are safe to call INSIDE a parallel loop.

        This is a SUBSET of _safe_functions() that excludes:
        - Memory allocation functions (empty, zeros, ones, etc.) - can't allocate in GPU kernel
        - Functions that create new collections (sorted, list, dict, etc.)
        - Functions that require runtime iteration (enumerate, zip, filter, map)

        Only pure mathematical/computational functions are allowed inside loops.
        """
        return {
            # Python builtins - only pure computational ones
            'range', 'len', 'abs', 'min', 'max', 'round',
            'int', 'float', 'bool', 'complex',
            'divmod', 'pow',

            # Math module functions - ALL of these are safe in GPU kernels
            'sin', 'cos', 'tan', 'exp', 'log', 'log10', 'log2', 'sqrt', 'pow',
            'floor', 'ceil', 'fabs', 'trunc',
            'asin', 'acos', 'atan', 'atan2',
            'sinh', 'cosh', 'tanh',
            'asinh', 'acosh', 'atanh',
            'degrees', 'radians',
            'hypot',
            'erf', 'erfc', 'gamma', 'lgamma',
            'gcd', 'lcm',
            'isfinite', 'isinf', 'isnan',
            'copysign', 'fmod', 'remainder',
            'ldexp', 'frexp', 'modf',

            # NumPy math (element-wise, GPU-acceleratable)
            'sqrt', 'square', 'cbrt', 'power',
            'exp', 'exp2', 'expm1', 'log', 'log2', 'log10', 'log1p',
            'sin', 'cos', 'tan', 'arcsin', 'arccos', 'arctan', 'arctan2',
            'sinh', 'cosh', 'tanh', 'arcsinh', 'arccosh', 'arctanh',
            'floor', 'ceil', 'trunc', 'rint', 'round',
            'abs', 'absolute', 'fabs', 'sign', 'negative', 'positive',
            'reciprocal', 'divide', 'multiply', 'add', 'subtract',
            'mod', 'fmod', 'remainder', 'divmod',
            'clip', 'minimum', 'maximum', 'fmin', 'fmax',
            'floor_divide', 'true_divide',

            # NumPy boolean operations
            'logical_and', 'logical_or', 'logical_not', 'logical_xor',
            'greater', 'greater_equal', 'less', 'less_equal',
            'equal', 'not_equal',

            # NumPy special values
            'isfinite', 'isinf', 'isnan', 'isneginf', 'isposinf',
            'real', 'imag', 'conj', 'angle',

            # Conditional/masking
            'where', 'select', 'heaviside', 'signbit',

            # Bitwise operations
            'bitwise_and', 'bitwise_or', 'bitwise_xor', 'bitwise_not',
            'left_shift', 'right_shift', 'invert',
        }

    def _extract_subscript_offsets(self, slice_node: ast.AST) -> Tuple[Any, ...]:
        """Extract offset information from subscript slice."""
        if isinstance(slice_node, ast.Tuple):
            return tuple(self._analyze_index(elt) for elt in slice_node.elts)
        else:
            return (self._analyze_index(slice_node),)

    def _analyze_index(self, node: ast.AST) -> Any:
        """Analyze a single index expression to extract offset."""
        if isinstance(node, ast.Name):
            return ('var', node.id, 0)  # Variable with no offset
        elif isinstance(node, ast.BinOp):
            # Handle i+1, i-1, etc.
            if isinstance(node.op, ast.Add):
                if isinstance(node.left, ast.Name) and isinstance(node.right, ast.Constant):
                    return ('var', node.left.id, node.right.value)
                elif isinstance(node.right, ast.Name) and isinstance(node.left, ast.Constant):
                    return ('var', node.right.id, node.left.value)
            elif isinstance(node.op, ast.Sub):
                if isinstance(node.left, ast.Name) and isinstance(node.right, ast.Constant):
                    return ('var', node.left.id, -node.right.value)
            elif isinstance(node.op, ast.Mult):
                # Strided access: i * stride
                return ('strided', str(ast.dump(node)))
        elif isinstance(node, ast.Constant):
            return ('const', node.value)

        return ('complex', str(ast.dump(node)))


class CUDAPatternDetector:
    """
    Detects parallelizable loop patterns suitable for GPU acceleration.

    Supports detection of:
    - Stencil patterns (5-point, 9-point, etc.)
    - Map patterns (element-wise operations)
    - Reduce patterns (sum, max, min, product)
    - Scan/Prefix patterns (cumulative sum, product, max, min)
    - MatMul patterns (matrix multiplication)
    - Transpose patterns (matrix transpose)
    - Gather patterns (indexed read)
    - Scatter patterns (indexed write)
    - Histogram patterns (binning/counting)
    - Filter/Compact patterns (conditional selection)
    - Convolution patterns (weighted stencils)
    - Outer Product patterns (vector outer product)

    Also performs dependency analysis to ensure parallelization is safe.
    """

    def __init__(self):
        """Initialize the pattern detector."""
        self._cache: Dict[str, PatternAnalysis] = {}

    def analyze(self, func: Callable) -> PatternAnalysis:
        """
        Analyze a function for GPU-parallelizable patterns.

        Args:
            func: The function to analyze

        Returns:
            PatternAnalysis with detected pattern information
        """
        func_name = getattr(func, '__name__', '<unknown>')

        # Check cache
        cache_key = self._get_cache_key(func)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Get source code using multi-strategy SourceExtractor (handles Jupyter notebooks)
        source = SourceExtractor.get_source(func)
        if source is None:
            logger.debug(f"Cannot get source for {func_name} via SourceExtractor")

            # CRITICAL FIX (Jan 2025 RCA): Bytecode-based stencil detection fallback
            # For Jupyter notebooks and exec'd code, source extraction fails because
            # co_filename='<string>'. However, we can still detect stencil patterns
            # by analyzing the bytecode. This enables GPU acceleration for notebooks
            # without requiring source code.
            #
            # User requirement: "Level 4 to actually accelerate this demo notebook"
            bytecode_analysis = self._analyze_bytecode_for_stencil(func)
            if bytecode_analysis is not None:
                logger.info(f"Bytecode analysis detected stencil pattern for {func_name}")
                self._cache[cache_key] = bytecode_analysis
                return bytecode_analysis

            return PatternAnalysis(
                pattern_type='unknown',
                parallelizable=False,
                rejection_reason="Cannot analyze source: could not get source code (bytecode fallback also failed)",
                function_name=func_name
            )

        # Parse AST
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            logger.debug(f"Cannot parse source for {func_name}: {e}")
            return PatternAnalysis(
                pattern_type='unknown',
                parallelizable=False,
                rejection_reason=f"Syntax error: {e}",
                function_name=func_name
            )

        # Check for modular patterns FIRST (FFT, Rolling Stats, Black-Scholes, Monte Carlo)
        # These are library-call patterns that don't require loop analysis
        modular_result = self._detect_modular_patterns(source, tree, func_name)
        if modular_result is not None:
            self._cache[cache_key] = modular_result
            return modular_result

        # Analyze with AST visitor
        analyzer = LoopAnalyzer()
        analyzer.visit(tree)

        # Create base analysis
        analysis = PatternAnalysis(
            function_name=func_name,
            source_lines=len(source.splitlines())
        )

        # Check for rejection conditions first
        rejection = self._check_rejection_conditions(analyzer)
        if rejection:
            analysis.parallelizable = False
            analysis.rejection_reason = rejection
            self._cache[cache_key] = analysis
            return analysis

        # No loops = not parallelizable (for GPU loop acceleration)
        if not analyzer.loops and not analyzer.while_loops:
            analysis.pattern_type = 'unknown'
            analysis.parallelizable = False
            analysis.rejection_reason = 'No loops found'
            self._cache[cache_key] = analysis
            return analysis

        # CRITICAL: Check for SCAN pattern FIRST before rejecting as dependency
        # Scan patterns (prefix sum, cumulative product, running max/min) ARE parallelizable
        # using specialized GPU algorithms (Blelloch scan, Hillis-Steele scan)
        scan_analysis = self._detect_scan_pattern(analyzer)
        if scan_analysis:
            analysis.pattern_type = 'scan'
            analysis.scan_info = scan_analysis
            analysis.dimensions = 1
            analysis.parallelizable = True
            analysis.confidence = 0.9
            analysis.memory_pattern = 'coalesced'
            self._cache[cache_key] = analysis
            return analysis

        # Check for COMPARE-SWAP pattern BEFORE rejecting as dependency
        # Sorting networks (bubble sort, odd-even sort) use tuple swap which is atomic
        # within an iteration: arr[i], arr[i+1] = arr[i+1], arr[i]
        compare_swap_analysis = self._detect_compare_swap_pattern(analyzer)
        if compare_swap_analysis:
            analysis.pattern_type = 'compare_swap'
            analysis.compare_swap_info = compare_swap_analysis
            analysis.dimensions = 1
            # Odd-even sort phases (step=2) are parallelizable
            # Bubble sort (step=1) is not parallelizable across the outer loop
            analysis.parallelizable = compare_swap_analysis.is_parallel_phase
            analysis.confidence = 0.85
            analysis.memory_pattern = 'strided' if compare_swap_analysis.step > 1 else 'coalesced'
            if not analysis.parallelizable:
                analysis.has_loop_carried_dependency = True
            self._cache[cache_key] = analysis
            return analysis

        # NOW check for non-parallelizable sequential dependencies
        # (e.g., fibonacci where arr[i] = arr[i-1] + arr[i-2])
        # But skip if we detected a tuple swap (handled by compare_swap above)
        if not analyzer.has_tuple_swap and self._has_sequential_dependency(analyzer):
            analysis.has_loop_carried_dependency = True
            analysis.parallelizable = False
            analysis.rejection_reason = 'Loop-carried dependency detected: array element depends on previous iteration'
            self._cache[cache_key] = analysis
            return analysis

        # Analyze for specific patterns
        # Order matters: check more specific patterns first

        # Check for convolution FIRST (weighted stencil with separate kernel array)
        # This must come before stencil and gather
        convolution_analysis = self._detect_convolution_pattern(analyzer)
        if convolution_analysis:
            analysis.pattern_type = 'convolution'
            analysis.convolution_info = convolution_analysis
            analysis.dimensions = convolution_analysis.dimensions
            analysis.parallelizable = True
            analysis.confidence = 0.85
            analysis.memory_pattern = 'coalesced'
            self._cache[cache_key] = analysis
            return analysis

        stencil_analysis = self._detect_stencil_pattern(analyzer)
        if stencil_analysis:
            analysis.pattern_type = 'stencil'
            analysis.stencil_info = stencil_analysis
            analysis.dimensions = stencil_analysis.dimensions
            analysis.parallelizable = True
            analysis.confidence = self._calculate_stencil_confidence(stencil_analysis, analyzer)
            analysis.memory_pattern = 'coalesced'
            self._cache[cache_key] = analysis
            return analysis

        # Check for matmul (triple nested loop with accumulation)
        matmul_analysis = self._detect_matmul_pattern(analyzer)
        if matmul_analysis:
            analysis.pattern_type = 'matmul'
            analysis.matmul_info = matmul_analysis
            analysis.dimensions = 2
            analysis.parallelizable = True
            analysis.confidence = 0.9
            analysis.memory_pattern = 'coalesced'
            self._cache[cache_key] = analysis
            return analysis

        # Check for transpose
        transpose_analysis = self._detect_transpose_pattern(analyzer)
        if transpose_analysis:
            analysis.pattern_type = 'transpose'
            analysis.transpose_info = transpose_analysis
            analysis.dimensions = 2
            analysis.parallelizable = True
            analysis.confidence = 0.95
            analysis.memory_pattern = 'strided'
            self._cache[cache_key] = analysis
            return analysis

        # Check for outer product
        outer_analysis = self._detect_outer_pattern(analyzer)
        if outer_analysis:
            analysis.pattern_type = 'outer'
            analysis.outer_info = outer_analysis
            analysis.dimensions = 2
            analysis.parallelizable = True
            analysis.confidence = 0.9
            analysis.memory_pattern = 'coalesced'
            self._cache[cache_key] = analysis
            return analysis

        # Check for filter/compact BEFORE histogram (more specific)
        # Filter: result[j] = data[i]; j += 1 (secondary index increment)
        filter_analysis = self._detect_filter_pattern(analyzer)
        if filter_analysis:
            analysis.pattern_type = 'filter'
            analysis.filter_info = filter_analysis
            analysis.dimensions = 1
            analysis.parallelizable = True
            analysis.confidence = 0.8
            analysis.memory_pattern = 'coalesced'
            self._cache[cache_key] = analysis
            return analysis

        # Check for histogram BEFORE scatter
        # Histogram: bins[data[i]] += 1 or bins[data[i]] += weights[i]
        # Uses augmented assignment to accumulate counts/weights
        histogram_analysis = self._detect_histogram_pattern(analyzer)
        if histogram_analysis:
            analysis.pattern_type = 'histogram'
            analysis.histogram_info = histogram_analysis
            analysis.dimensions = 1
            analysis.parallelizable = True
            analysis.confidence = 0.85
            analysis.memory_pattern = 'random'
            self._cache[cache_key] = analysis
            return analysis

        # Check for scatter (indexed write with data values)
        # Scatter: result[indices[i]] = data[i] or result[indices[i]] += data[i]
        scatter_analysis = self._detect_scatter_pattern(analyzer)
        if scatter_analysis:
            analysis.pattern_type = 'scatter'
            analysis.scatter_info = scatter_analysis
            analysis.dimensions = 1
            analysis.parallelizable = True
            analysis.confidence = 0.85
            analysis.memory_pattern = 'random'
            self._cache[cache_key] = analysis
            return analysis

        # Check for gather (indexed read)
        gather_analysis = self._detect_gather_pattern(analyzer)
        if gather_analysis:
            analysis.pattern_type = 'gather'
            analysis.gather_info = gather_analysis
            analysis.dimensions = 1
            analysis.parallelizable = True
            analysis.confidence = 0.9
            analysis.memory_pattern = 'random'
            self._cache[cache_key] = analysis
            return analysis

        # Check reduce BEFORE map - reduce patterns have accumulator ops
        reduce_analysis = self._detect_reduce_pattern(analyzer)
        if reduce_analysis:
            analysis.pattern_type = 'reduce'
            analysis.reduce_info = reduce_analysis
            analysis.dimensions = 1
            analysis.parallelizable = True
            analysis.confidence = self._calculate_reduce_confidence(reduce_analysis, analyzer)
            analysis.memory_pattern = 'coalesced'
            self._cache[cache_key] = analysis
            return analysis

        map_analysis = self._detect_map_pattern(analyzer)
        if map_analysis:
            analysis.pattern_type = 'map'
            analysis.map_info = map_analysis
            analysis.dimensions = map_analysis.dimensions
            analysis.parallelizable = True
            analysis.confidence = self._calculate_map_confidence(map_analysis, analyzer)
            analysis.memory_pattern = self._detect_memory_pattern(analyzer)
            self._cache[cache_key] = analysis
            return analysis

        # Check for loop-carried dependencies
        if self._has_loop_carried_dependency(analyzer):
            analysis.has_loop_carried_dependency = True
            analysis.parallelizable = False
            analysis.rejection_reason = 'Loop-carried dependency detected'
            self._cache[cache_key] = analysis
            return analysis

        # Unknown pattern
        analysis.pattern_type = 'unknown'
        analysis.parallelizable = False
        analysis.rejection_reason = 'Pattern not recognized'
        self._cache[cache_key] = analysis
        return analysis

    def _get_cache_key(self, func: Callable) -> str:
        """Generate cache key for a function."""
        source = SourceExtractor.get_source(func)
        if source:
            import hashlib
            return hashlib.md5(source.encode()).hexdigest()
        # Fallback to code object id for functions without extractable source
        return str(id(func.__code__)) if hasattr(func, '__code__') else str(id(func))

    def _check_rejection_conditions(self, analyzer: LoopAnalyzer) -> Optional[str]:
        """
        Check for conditions that make a function non-parallelizable.

        This method implements comprehensive rejection checks based on:
        1. Exception handling (not supported in CUDA kernels)
        2. Print/IO operations (not supported in CUDA)
        3. Control flow that prevents parallelization (break, continue, early return)
        4. Generator patterns (yield)
        5. Try/except blocks
        6. Comprehensions inside loops (create dynamic allocations)
        7. Unsafe function calls inside loops

        Returns rejection reason string if not parallelizable, None otherwise.
        """
        # Exception handling
        if analyzer.has_raise:
            return "Exception handling (raise) not supported in CUDA kernels"
        if analyzer.has_try_except:
            return "Try/except blocks not supported in CUDA kernels"

        # IO operations
        if analyzer.has_print:
            return "Print statements not supported in CUDA kernels"

        # Generator patterns
        if analyzer.has_yield:
            return "Generator patterns (yield) not supported in CUDA kernels"

        # Control flow that prevents parallelization
        if analyzer.has_recursion:
            return "Recursive functions not supported in CUDA kernels"
        if analyzer.has_break:
            return "Break statements prevent parallel execution (early exit not allowed)"
        if analyzer.has_continue:
            return "Continue statements complicate parallel execution"
        if analyzer.has_return_in_loop:
            return "Return statements inside loops prevent parallelization"

        # Dynamic allocations inside loops
        if analyzer.has_comprehension_in_loop:
            return "Comprehensions inside loops create dynamic allocations (not GPU-compatible)"

        # CRITICAL FIX (Dec 2025): Explicit while loop rejection
        # While loops cannot be parallelized on GPU because:
        # 1. Unknown iteration count - GPU kernels need fixed grid dimensions at launch
        # 2. Condition-dependent termination - each thread might run different iterations
        # 3. Cannot map to parallel for/range model used by CUDA
        # Reject ANY function containing while loops - even if for loops exist,
        # the while loop portion cannot be parallelized
        if analyzer.while_loops:
            return "While loops cannot be parallelized: unknown iteration count (GPU requires fixed grid dimensions)"

        # CRITICAL FIX (Dec 2025): Only reject based on function calls INSIDE loops
        # Function calls outside loops (memory allocation, setup, teardown) are fine
        # because they don't affect the parallelizability of the loop body itself.
        # The GPU kernel only needs to parallelize the loop body.
        if analyzer.has_function_call_in_loop:
            # Check if it's a potentially unsafe external call INSIDE a loop
            safe = analyzer._safe_functions_in_loop()
            unsafe_calls = [c for c in analyzer.function_calls_in_loop
                          if c not in safe and c not in analyzer.nested_functions]
            if unsafe_calls:
                return f"External function calls inside loop with unknown side effects: {unsafe_calls}"
        return None

    def _detect_scan_pattern(self, analyzer: LoopAnalyzer) -> Optional[ScanInfo]:
        """
        Detect scan/prefix pattern (cumulative sum, product, max, min).

        Pattern: result[i] = result[i-1] OP arr[i]
        - Inclusive scan: result[0] = arr[0], result[i] = result[i-1] + arr[i]
        - Exclusive scan: result[0] = 0, result[i] = result[i-1] + arr[i-1]

        These ARE parallelizable using specialized GPU scan algorithms.
        """
        if len(analyzer.loops) < 1:
            return None

        # Look for pattern where output array depends on previous element
        for out_array, writes in analyzer.array_writes.items():
            if out_array not in analyzer.array_reads:
                continue

            reads = analyzer.array_reads[out_array]

            # Collect all read offsets from the output array
            # For valid scan, we should have EXACTLY ONE lookback of -1
            # Fibonacci-like patterns have MULTIPLE lookbacks (e.g., -1 AND -2)
            lookback_offsets = set()
            for read in reads:
                read_offset = self._get_loop_var_offset(read, analyzer.loop_vars)
                if read_offset is not None and read_offset < 0:
                    lookback_offsets.add(read_offset)

            # Reject if multiple lookback offsets (fibonacci-like: arr[i-1] + arr[i-2])
            if len(lookback_offsets) > 1:
                continue

            # Check if we read from previous index and write to current
            for write in writes:
                write_offset = self._get_loop_var_offset(write, analyzer.loop_vars)
                if write_offset != 0:
                    continue

                for read in reads:
                    read_offset = self._get_loop_var_offset(read, analyzer.loop_vars)
                    if read_offset == -1:
                        # Found pattern: result[i] depends on result[i-1]
                        # Determine the operation from assignments and function calls
                        operation = self._detect_scan_operation(analyzer)

                        # Check if it's inclusive or exclusive
                        # Exclusive: result[i] = result[i-1] + arr[i-1] (input uses i-1)
                        # Inclusive: result[i] = result[i-1] + arr[i] (input uses i)
                        is_inclusive = True
                        input_array = None

                        # Find the input array (array other than output that we read from)
                        for in_array in analyzer.array_reads:
                            if in_array != out_array:
                                input_array = in_array
                                # Check if input array is accessed at i-1 (exclusive) or i (inclusive)
                                for in_read in analyzer.array_reads[in_array]:
                                    in_offset = self._get_loop_var_offset(in_read, analyzer.loop_vars)
                                    if in_offset == -1:
                                        is_inclusive = False
                                break

                        return ScanInfo(
                            operation=operation,
                            is_inclusive=is_inclusive,
                            input_array=input_array,
                            output_array=out_array,
                            axis=0
                        )

        return None

    def _detect_scan_operation(self, analyzer: LoopAnalyzer) -> str:
        """Detect the operation type for a scan pattern."""
        # Check for max/min function calls in the loop
        for call in analyzer.function_calls:
            if call == 'max':
                return 'max'
            elif call == 'min':
                return 'min'

        # Check augmented assignments for *= (product)
        for aug in analyzer.aug_assignments:
            if isinstance(aug.target, ast.Subscript):
                if isinstance(aug.op, ast.Mult):
                    return 'product'
                elif isinstance(aug.op, ast.Add):
                    return 'sum'

        # Check regular assignments for multiplication pattern
        for assign in analyzer.assignments:
            if isinstance(assign.value, ast.BinOp):
                if isinstance(assign.value.op, ast.Mult):
                    # Check if this is part of a scan (result[i] = result[i-1] * arr[i])
                    if isinstance(assign.value.left, ast.Subscript) or isinstance(assign.value.right, ast.Subscript):
                        return 'product'
                elif isinstance(assign.value.op, ast.Add):
                    return 'sum'
            # Check for max/min calls in assignment
            elif isinstance(assign.value, ast.Call):
                func_name = None
                if isinstance(assign.value.func, ast.Name):
                    func_name = assign.value.func.id
                if func_name == 'max':
                    return 'max'
                elif func_name == 'min':
                    return 'min'

        # Default to sum
        return 'sum'

    def _detect_matmul_pattern(self, analyzer: LoopAnalyzer) -> Optional[MatMulInfo]:
        """
        Detect matrix multiplication pattern.

        Pattern: C[i,j] += A[i,k] * B[k,j] (triple nested loop)
        Also handles: y[i] += A[i,j] * x[j] (matrix-vector multiply, 2 loops)

        CRITICAL: Must verify triple-index pattern to avoid false positives.
        Row-sum like: result[i] += data[i, j] is NOT matmul (no second input array).
        """
        # Need at least 2 loops for matrix-vector, 3 for matrix-matrix
        if analyzer.max_loop_depth < 2:
            return None

        # Need accumulation operation (+=) on a subscripted target
        accumulator_target = None
        for aug in analyzer.aug_assignments:
            if isinstance(aug.op, ast.Add) and isinstance(aug.target, ast.Subscript):
                accumulator_target = aug.target
                break

        if not accumulator_target:
            return None

        # Look for pattern with 2+ loop variables
        if len(analyzer.loop_vars) < 2:
            return None

        # Extract indices used in the output array
        output_indices = self._extract_index_vars(accumulator_target.slice, analyzer.loop_vars)
        if not output_indices:
            return None

        # CRITICAL FIX (Dec 2025): Require triple-index pattern
        # For matmul C[i,j] += A[i,k] * B[k,j], we need:
        # 1. Output uses 2 loop vars (i, j)
        # 2. Two input arrays each use 2 loop vars
        # 3. One loop var (k) is shared between inputs but NOT in output
        # 4. Multiplication of the two array accesses

        # Check for characteristic matmul access pattern
        out_array = accumulator_target.value.id if isinstance(accumulator_target.value, ast.Name) else None
        if not out_array:
            return None

        # Look for two input arrays with compatible access patterns
        input_arrays = [arr for arr in analyzer.array_reads if arr != out_array]

        # For matmul: need exactly 2 input arrays
        if len(input_arrays) < 2:
            return None

        # Check for multiplication in loop body (in the augmented assignment's RHS)
        has_mult_of_arrays = False
        left_array = None
        right_array = None

        for aug in analyzer.aug_assignments:
            if isinstance(aug.value, ast.BinOp) and isinstance(aug.value.op, ast.Mult):
                # Check if both sides are array subscripts
                left = aug.value.left
                right = aug.value.right
                if isinstance(left, ast.Subscript) and isinstance(right, ast.Subscript):
                    if isinstance(left.value, ast.Name) and isinstance(right.value, ast.Name):
                        left_array = left.value.id
                        right_array = right.value.id
                        # Both must be different from output and be input arrays
                        if (left_array in input_arrays and right_array in input_arrays
                            and left_array != out_array and right_array != out_array):
                            # CRITICAL: Verify shared index pattern
                            # A[i,k] * B[k,j] requires k to be in both but not in output
                            left_indices = self._extract_index_vars(left.slice, analyzer.loop_vars)
                            right_indices = self._extract_index_vars(right.slice, analyzer.loop_vars)

                            # Defensive check: skip if we can't extract indices
                            if not left_indices or not right_indices or not output_indices:
                                continue

                            # Find shared index (k in the pattern)
                            shared = set(left_indices) & set(right_indices)
                            # Shared index should NOT be in output
                            shared_not_in_output = shared - set(output_indices)

                            if shared_not_in_output:
                                # Valid matmul pattern: has shared reduction index
                                has_mult_of_arrays = True

        if not has_mult_of_arrays:
            return None

        return MatMulInfo(
            left_matrix=left_array,
            right_matrix=right_array,
            output_matrix=out_array
        )

    def _extract_index_vars(self, slice_node: ast.AST, loop_vars: List[str]) -> List[str]:
        """Extract loop variable names used in a subscript slice."""
        found_vars = []

        if isinstance(slice_node, ast.Tuple):
            for elt in slice_node.elts:
                found_vars.extend(self._extract_index_vars_from_expr(elt, loop_vars))
        else:
            found_vars.extend(self._extract_index_vars_from_expr(slice_node, loop_vars))

        return found_vars

    def _extract_index_vars_from_expr(self, node: ast.AST, loop_vars: List[str]) -> List[str]:
        """Extract loop variable names from an expression."""
        found = []
        if isinstance(node, ast.Name) and node.id in loop_vars:
            found.append(node.id)
        elif isinstance(node, ast.BinOp):
            found.extend(self._extract_index_vars_from_expr(node.left, loop_vars))
            found.extend(self._extract_index_vars_from_expr(node.right, loop_vars))
        return found

    def _detect_transpose_pattern(self, analyzer: LoopAnalyzer) -> Optional[TransposeInfo]:
        """
        Detect matrix transpose pattern.

        Pattern 1 (out-of-place): B[j,i] = A[i,j]
        Pattern 2 (in-place swap): temp = A[i,j]; A[i,j] = A[j,i]; A[j,i] = temp
        """
        if analyzer.max_loop_depth < 2:
            return None

        # Pattern 1: Out-of-place transpose with different input/output arrays
        for out_array, writes in analyzer.array_writes.items():
            for in_array, reads in analyzer.array_reads.items():
                if in_array == out_array:
                    continue

                # Check if indices are swapped
                for write in writes:
                    for read in reads:
                        if len(write) == 2 and len(read) == 2:
                            # Check if indices are swapped
                            w0, w1 = write
                            r0, r1 = read

                            # Simple heuristic: check if variable names are swapped
                            if (isinstance(w0, tuple) and isinstance(w1, tuple) and
                                isinstance(r0, tuple) and isinstance(r1, tuple)):
                                if (len(w0) >= 2 and len(w1) >= 2 and
                                    len(r0) >= 2 and len(r1) >= 2):
                                    w0_var = w0[1] if w0[0] == 'var' else None
                                    w1_var = w1[1] if w1[0] == 'var' else None
                                    r0_var = r0[1] if r0[0] == 'var' else None
                                    r1_var = r1[1] if r1[0] == 'var' else None

                                    if (w0_var and w1_var and r0_var and r1_var and
                                        w0_var == r1_var and w1_var == r0_var):
                                        return TransposeInfo(
                                            input_array=in_array,
                                            output_array=out_array,
                                            axes=(1, 0)
                                        )

        # Pattern 2: In-place transpose (swap pattern)
        # Check if same array is both read and written with swapped indices
        for array_name in analyzer.array_writes:
            if array_name not in analyzer.array_reads:
                continue

            writes = analyzer.array_writes[array_name]
            reads = analyzer.array_reads[array_name]

            # Need at least 2 writes (for swap: A[i,j] = ..., A[j,i] = ...)
            if len(writes) < 2:
                continue

            # Check for swapped index patterns in reads and writes
            index_patterns = set()
            for access in reads + writes:
                if len(access) == 2:
                    idx0, idx1 = access
                    if (isinstance(idx0, tuple) and isinstance(idx1, tuple) and
                        idx0[0] == 'var' and idx1[0] == 'var'):
                        var0 = idx0[1]
                        var1 = idx1[1]
                        # Store as sorted tuple to detect (i,j) and (j,i) pairs
                        pattern = tuple(sorted([var0, var1]))
                        index_patterns.add((var0, var1, pattern))

            # Check if we have both (i,j) and (j,i) access patterns
            has_swap = False
            for v0, v1, pattern in index_patterns:
                # Look for the reverse pattern
                for v0_other, v1_other, pattern_other in index_patterns:
                    if pattern == pattern_other and (v0, v1) != (v0_other, v1_other):
                        has_swap = True
                        break
                if has_swap:
                    break

            if has_swap:
                return TransposeInfo(
                    input_array=array_name,
                    output_array=array_name,
                    axes=(1, 0)
                )

        return None

    def _detect_gather_pattern(self, analyzer: LoopAnalyzer) -> Optional[GatherInfo]:
        """
        Detect gather (indexed read) pattern.

        Pattern 1: result[i] = data[indices[i]]  (direct complex indexing)
        Pattern 2: idx = indices[i]; result[i] = data[idx]  (via local variable)
        """
        if len(analyzer.loops) < 1:
            return None

        # Find local variables computed from array reads (e.g., idx = indices[i])
        local_index_vars = {}
        for assign in analyzer.assignments:
            if isinstance(assign.targets[0], ast.Name) and isinstance(assign.value, ast.Subscript):
                local_var = assign.targets[0].id
                if isinstance(assign.value.value, ast.Name):
                    source_array = assign.value.value.id
                    local_index_vars[local_var] = source_array

        # Look for indirect array access (array indexed by another array or local var)
        for out_array, writes in analyzer.array_writes.items():
            for in_array, reads in analyzer.array_reads.items():
                if in_array == out_array:
                    continue

                # Check if any read uses complex indexing or local index variable
                for read in reads:
                    for idx in read:
                        index_array = None
                        is_gather = False

                        if isinstance(idx, tuple) and idx[0] == 'complex':
                            # Direct complex indexing: data[indices[i]]
                            is_gather = True
                            for arr in analyzer.array_reads:
                                if arr != in_array and arr != out_array:
                                    index_array = arr
                                    break

                        elif isinstance(idx, tuple) and idx[0] == 'var':
                            # Check if the variable is a computed index
                            var_name = idx[1]
                            if var_name in local_index_vars:
                                # data[idx] where idx = indices[i]
                                is_gather = True
                                index_array = local_index_vars[var_name]

                        if is_gather:
                            return GatherInfo(
                                input_array=in_array,
                                index_array=index_array,
                                output_array=out_array
                            )

        return None

    def _detect_scatter_pattern(self, analyzer: LoopAnalyzer) -> Optional[ScatterInfo]:
        """
        Detect scatter (indexed write) pattern.

        Pattern: result[indices[i]] = data[i] or result[indices[i]] += data[i]

        Scatter writes to output at positions determined by an index array.
        Different from histogram: histogram increments by constant, scatter uses input values.

        Key: Scatter requires WRITING DATA VALUES (not constants) to indexed positions.
        """
        if len(analyzer.loops) < 1:
            return None

        # Scatter requires at least 2 read arrays: index array + data array
        # Or at least 1 read array with regular assignments (not aug with constant)
        read_arrays = list(analyzer.array_reads.keys())

        # Check if we have augmented assignment writing a constant (histogram pattern)
        is_incrementing_by_constant = False
        for aug in analyzer.aug_assignments:
            if isinstance(aug.target, ast.Subscript):
                if isinstance(aug.value, ast.Constant):
                    is_incrementing_by_constant = True
                    break

        # If incrementing by constant, this is histogram, not scatter
        if is_incrementing_by_constant:
            return None

        # Look for indirect write access (output indexed by another array)
        for out_array, writes in analyzer.array_writes.items():
            for write in writes:
                for idx in write:
                    is_indirect = False

                    # Check for complex indexing (arr[other_arr[i]])
                    if isinstance(idx, tuple) and idx[0] == 'complex':
                        is_indirect = True

                    if is_indirect:
                        # Find input and index arrays
                        input_array = None
                        index_array = None
                        non_output_reads = [arr for arr in read_arrays if arr != out_array]

                        # Need at least one input array that provides values
                        # The index array is embedded in the complex subscript
                        if len(non_output_reads) >= 2:
                            # First is data values, second is index mapping
                            input_array = non_output_reads[0]
                            index_array = non_output_reads[1]
                        elif len(non_output_reads) == 1:
                            # The single read array is used as index - this is histogram, not scatter
                            # Scatter needs BOTH an index array AND a data array
                            return None

                        # Determine operation
                        operation = 'assign'

                        # Check for augmented assignment (+=, etc.)
                        for aug in analyzer.aug_assignments:
                            if isinstance(aug.target, ast.Subscript):
                                if isinstance(aug.op, ast.Add):
                                    operation = 'add'
                                elif isinstance(aug.op, ast.Mult):
                                    operation = 'multiply'

                        # Check for conditional max/min
                        if analyzer.conditionals_in_loop:
                            for var, op in analyzer.accumulator_ops:
                                if op == 'max':
                                    operation = 'max'
                                elif op == 'min':
                                    operation = 'min'

                        return ScatterInfo(
                            input_array=input_array,
                            index_array=index_array,
                            output_array=out_array,
                            operation=operation
                        )

        # Also check for scatter pattern where index is computed from another array
        # Pattern: idx = indices[i]; result[idx] = ...
        # This requires looking at the assignment structure more carefully
        if analyzer.conditionals_in_loop or analyzer.aug_assignments:
            # Look for pattern where we have indirect indexing via local variable
            for assign in analyzer.assignments:
                if isinstance(assign.value, ast.Subscript):
                    # idx = indices[i] pattern
                    if isinstance(assign.targets[0], ast.Name):
                        local_idx_var = assign.targets[0].id

                        # Check if this local var is used to index output
                        for out_array, writes in analyzer.array_writes.items():
                            for write in writes:
                                for idx in write:
                                    if isinstance(idx, tuple) and idx[0] == 'var':
                                        if idx[1] == local_idx_var:
                                            # Found scatter via local variable
                                            read_arrays = list(analyzer.array_reads.keys())
                                            index_array = None
                                            input_array = None

                                            for arr in read_arrays:
                                                if arr != out_array:
                                                    # First non-output array is likely indices
                                                    if index_array is None:
                                                        index_array = arr
                                                    else:
                                                        input_array = arr

                                            operation = 'assign'
                                            if analyzer.conditionals_in_loop:
                                                # Check for max/min
                                                for var, op in analyzer.accumulator_ops:
                                                    if op == 'max':
                                                        operation = 'max'
                                                    elif op == 'min':
                                                        operation = 'min'

                                            return ScatterInfo(
                                                input_array=input_array,
                                                index_array=index_array,
                                                output_array=out_array,
                                                operation=operation
                                            )

        return None

    def _detect_histogram_pattern(self, analyzer: LoopAnalyzer) -> Optional[HistogramInfo]:
        """
        Detect histogram pattern.

        Pattern: bins[data[i]] += 1 or bins[data[i]] += weights[i]
        Also: bin_idx = int(data[i] / width); bins[bin_idx] += 1

        Key characteristics:
        - Output indexed by INPUT VALUE or computed index
        - Incrementing by constant or weight from secondary array
        - Different from scatter: histogram bins data values, scatter writes data to indexed positions

        Key distinction from scatter:
        - Histogram: bins[data[i]] += ... (output indexed by DATA VALUE)
        - Scatter: result[indices[i]] = data[i] (output indexed by INDEX, value from DATA)
        """
        if len(analyzer.loops) < 1:
            return None

        # Look for augmented assignment to indexed output
        has_aug_to_subscript = False
        aug_value_is_constant = False
        aug_value_is_subscript = False
        output_index_var = None
        output_index_is_complex = False
        weights_array = None

        index_source_array = None  # The array name from complex subscript (e.g., 'data' in bins[data[i]])

        for aug in analyzer.aug_assignments:
            if isinstance(aug.target, ast.Subscript):
                has_aug_to_subscript = True
                # Get the index variable/expression
                if isinstance(aug.target.slice, ast.Name):
                    output_index_var = aug.target.slice.id
                elif isinstance(aug.target.slice, ast.Subscript):
                    # Direct complex indexing: bins[data[i]]
                    output_index_is_complex = True
                    # Extract the array name from complex subscript
                    if isinstance(aug.target.slice.value, ast.Name):
                        index_source_array = aug.target.slice.value.id
                # Check what we're adding
                if isinstance(aug.value, ast.Constant):
                    # bins[...] += 1 (constant)
                    aug_value_is_constant = True
                elif isinstance(aug.value, ast.Subscript):
                    # bins[...] += weights[i] (weight from another array)
                    aug_value_is_subscript = True
                    # Get the weights array name
                    if isinstance(aug.value.value, ast.Name):
                        weights_array = aug.value.value.id

        if not has_aug_to_subscript:
            return None

        # For histogram, we need to be incrementing by constant or weights
        if not (aug_value_is_constant or aug_value_is_subscript):
            return None

        # Check for computed index pattern: idx = int(data[i] / width)
        # The index variable should be computed from a data array
        computed_index_uses_data = False
        if output_index_var:
            for assign in analyzer.assignments:
                if (isinstance(assign.targets[0], ast.Name) and
                    assign.targets[0].id == output_index_var):
                    # Check if the assignment involves a subscript (data access)
                    expr_str = ast.dump(assign.value)
                    for arr in analyzer.array_reads:
                        if arr in expr_str:
                            computed_index_uses_data = True
                            break

        # Check for direct complex indexing (bins[data[i]]) or computed index
        for out_array, writes in analyzer.array_writes.items():
            for write in writes:
                for idx in write:
                    is_histogram_index = False

                    if isinstance(idx, tuple) and idx[0] == 'complex':
                        # Complex indexing like bins[data[i]]
                        is_histogram_index = True
                    elif isinstance(idx, tuple) and idx[0] == 'var' and computed_index_uses_data:
                        # Simple var index but computed from data (binned histogram)
                        is_histogram_index = True

                    if is_histogram_index:
                        input_array = None
                        is_weighted = aug_value_is_subscript

                        read_arrays = list(analyzer.array_reads.keys())

                        # For weighted histogram: bins[data[i]] += weights[i]
                        # - data array: provides the index/bin (typically first parameter)
                        # - weights array: provides the value to add (typically second)
                        #
                        # For scatter-add: result[indices[i]] += data[i]
                        # - indices array: provides the index (typically second parameter)
                        # - data array: provides the value (typically first)
                        #
                        # Key distinction: Use naming heuristics based on index_source_array
                        # Scatter patterns typically use 'indices', 'index', 'idx', etc.
                        # Histogram patterns typically use 'data', 'values', 'pixels', etc.
                        if is_weighted and weights_array and index_source_array:
                            # Check naming convention of index source array
                            scatter_indicators = ('index', 'indices', 'idx', 'pos', 'offset', 'ptr', 'loc')
                            if any(hint in index_source_array.lower() for hint in scatter_indicators):
                                # Index source has scatter-like naming → not histogram
                                return None

                            # Input array is the one that provides the index (not the weights)
                            for arr in read_arrays:
                                if arr != weights_array:
                                    input_array = arr
                                    break
                        elif len(read_arrays) >= 1:
                            input_array = read_arrays[0]

                        return HistogramInfo(
                            input_array=input_array,
                            bins_array=out_array,
                            is_weighted=is_weighted,
                            weights_array=weights_array if is_weighted else None
                        )

        return None

    def _detect_filter_pattern(self, analyzer: LoopAnalyzer) -> Optional[FilterInfo]:
        """
        Detect filter/compact pattern.

        Pattern:
        j = 0
        for i in range(n):
            if condition(data[i]):
                result[j] = data[i]  # or transform(data[i])
                j += 1

        Key difference from histogram:
        - Filter: result[j] = data[i]; j += 1 (output indexed by secondary var)
        - Histogram: bins[data[i]] += 1 (output indexed by data value)
        """
        if len(analyzer.loops) < 1:
            return None

        # Look for pattern with conditional in loop
        if not analyzer.conditionals_in_loop:
            return None

        # Check for secondary index increment (j += 1)
        # This is a scalar being incremented, not an array operation
        has_secondary_index = False
        secondary_var = None

        for aug in analyzer.aug_assignments:
            if isinstance(aug.target, ast.Name):  # j += 1 (scalar, not array)
                if isinstance(aug.op, ast.Add):
                    # Check if incrementing by 1
                    if isinstance(aug.value, ast.Constant) and aug.value.value == 1:
                        has_secondary_index = True
                        secondary_var = aug.target.id
                        break

        if not has_secondary_index:
            return None

        # Check if output array is indexed by the secondary variable
        output_uses_secondary = False
        for out_array, writes in analyzer.array_writes.items():
            for write in writes:
                for idx in write:
                    if isinstance(idx, tuple) and len(idx) >= 2:
                        kind, var = idx[0], idx[1]
                        if kind == 'var' and var == secondary_var:
                            output_uses_secondary = True
                            break

        if not output_uses_secondary:
            return None

        # Find input and output arrays
        input_array = None
        output_array = None

        if analyzer.array_reads:
            input_array = list(analyzer.array_reads.keys())[0]
        if analyzer.array_writes:
            output_array = list(analyzer.array_writes.keys())[0]

        # Check if there's a transformation
        has_transform = False
        transform_expr = None

        # Check for transformation in assignments
        for assign in analyzer.assignments:
            if isinstance(assign.value, ast.BinOp):
                has_transform = True
                break
            if isinstance(assign.value, ast.Call):
                has_transform = True
                break

        # Also check for math function calls
        if analyzer.function_calls:
            math_funcs = {'abs', 'sqrt', 'exp', 'log', 'sin', 'cos'}
            if any(f in math_funcs for f in analyzer.function_calls):
                has_transform = True

        return FilterInfo(
            input_array=input_array,
            output_array=output_array,
            has_transform=has_transform,
            transform_expr=transform_expr
        )

    def _detect_convolution_pattern(self, analyzer: LoopAnalyzer) -> Optional[ConvolutionInfo]:
        """
        Detect convolution pattern.

        Pattern: weighted stencil with separate kernel/weights array
        result[i] = sum(data[i+offset] * kernel[offset] for offset in range)

        Key difference from stencil:
        - Convolution: data[i+j] * kernel[j] (kernel indexed by inner loop var)
        - Stencil: (T[i-1] + T[i+1]) / 2 (fixed weights, no separate kernel array)
        """
        if len(analyzer.loops) < 1:
            return None

        # Check for at least 2 read arrays (data + kernel/weights)
        read_arrays = list(analyzer.array_reads.keys())
        if len(read_arrays) < 2:
            return None

        # Check for multiplication in the loop (data * kernel)
        has_mult = False
        for assign in analyzer.assignments:
            if isinstance(assign.value, ast.BinOp) and isinstance(assign.value.op, ast.Mult):
                has_mult = True
            # Also check for addition with multiplication inside
            if isinstance(assign.value, ast.BinOp) and isinstance(assign.value.op, ast.Add):
                # Check operands for multiplication
                for operand in [assign.value.left, assign.value.right]:
                    if isinstance(operand, ast.BinOp) and isinstance(operand.op, ast.Mult):
                        has_mult = True
        for aug in analyzer.aug_assignments:
            if isinstance(aug.value, ast.BinOp) and isinstance(aug.value.op, ast.Mult):
                has_mult = True

        if not has_mult:
            return None

        # Look for pattern where one array has offset access (data[i+offset])
        # and another array is accessed by the offset variable (kernel[offset])
        data_array = None
        kernel_array = None
        has_complex_access = False  # Complex index expression (data[i+j-k])
        has_kernel_access = False   # Simple loop var access (kernel[j])

        for arr, reads in analyzer.array_reads.items():
            for read in reads:
                # Check each index in the read (1D has 1 index, 2D has 2, etc.)
                has_complex_in_read = False
                has_simple_var_in_read = True  # Assume all simple until proven otherwise

                for idx in read:
                    if isinstance(idx, tuple) and len(idx) >= 2:
                        kind = idx[0]
                        if kind == 'complex':
                            has_complex_in_read = True
                        elif kind == 'var':
                            var = idx[1]
                            if var not in analyzer.loop_vars:
                                has_simple_var_in_read = False
                        else:
                            has_simple_var_in_read = False
                    else:
                        has_simple_var_in_read = False

                # If any index is complex, this is the data array
                if has_complex_in_read:
                    data_array = arr
                    has_complex_access = True
                # If all indices are simple loop vars, this is the kernel array
                elif has_simple_var_in_read and len(read) > 0:
                    kernel_array = arr
                    has_kernel_access = True

        # For convolution, we need:
        # 1. One array with complex/offset access (data array)
        # 2. Another array with simple loop var access (kernel array)
        # 3. They must be different arrays
        # 4. The kernel array should use DIFFERENT loop variables than the output
        #    (Jacobi: f[i,j] uses same indices as output - NOT a kernel)
        #    (Convolution: kernel[j] uses DIFFERENT/inner loop vars)
        is_true_kernel = False
        if kernel_array and analyzer.array_writes:
            output_array_name = list(analyzer.array_writes.keys())[0]
            output_writes = analyzer.array_writes.get(output_array_name, [])
            kernel_reads = analyzer.array_reads.get(kernel_array, [])

            # Get the set of loop vars used in output writes
            output_loop_vars_used = set()
            for write in output_writes:
                for idx in write:
                    if isinstance(idx, tuple) and idx[0] == 'var' and len(idx) >= 2:
                        output_loop_vars_used.add(idx[1])

            # Check if kernel uses DIFFERENT loop vars than output
            # - Jacobi: f[i,j] uses {i,j}, output uses {i,j} - SAME vars → NOT kernel
            # - Convolution: kernel[j] uses {j}, output uses {i} - DIFFERENT vars → IS kernel
            # - Weighted stencil: weights[0] uses constants, not loop vars → also valid
            for read in kernel_reads:
                kernel_loop_vars_used = set()
                all_simple_indices = True
                has_constant_indices = False

                for idx in read:
                    if isinstance(idx, tuple) and idx[0] == 'var' and len(idx) >= 2:
                        kernel_loop_vars_used.add(idx[1])
                    elif isinstance(idx, tuple) and idx[0] == 'const':
                        has_constant_indices = True
                    elif not isinstance(idx, tuple):
                        all_simple_indices = False

                # True kernel if:
                # 1. Uses constant indices (weights[0], weights[1]) - weighted stencil
                # 2. Uses DIFFERENT loop vars than output (kernel[j] vs result[i])
                # 3. Uses a SUBSET of output loop vars (for nested convolutions)
                if has_constant_indices:
                    is_true_kernel = True
                    break
                elif kernel_loop_vars_used and not kernel_loop_vars_used.intersection(output_loop_vars_used):
                    # Kernel uses completely different loop vars (inner loop vars)
                    is_true_kernel = True
                    break
                elif kernel_loop_vars_used and kernel_loop_vars_used < output_loop_vars_used:
                    # Kernel uses a proper subset (fewer vars)
                    is_true_kernel = True
                    break

        if has_complex_access and has_kernel_access and data_array != kernel_array and is_true_kernel:
            output_array = None
            if analyzer.array_writes:
                output_array = list(analyzer.array_writes.keys())[0]

            # Determine dimensions from the kernel array's access pattern
            # The kernel array's index count gives us the convolution dimensions
            dimensions = 1
            if kernel_array in analyzer.array_reads:
                for read in analyzer.array_reads[kernel_array]:
                    dimensions = max(dimensions, len(read))

            kernel_size = tuple([3] * dimensions)

            return ConvolutionInfo(
                dimensions=dimensions,
                kernel_size=kernel_size,
                input_array=data_array,
                kernel_array=kernel_array,
                output_array=output_array
            )

        # Also check for weighted stencil pattern: data[i+k] * weights[k]
        # where weights is a small array accessed by inner loop variable or constants
        if has_mult and len(read_arrays) >= 2 and analyzer.max_loop_depth >= 1:
            # Check if one array has stencil-like access
            for arr, reads in analyzer.array_reads.items():
                for read in reads:
                    offset = self._extract_neighbor_offset(read, analyzer.loop_vars)
                    if offset and any(o != 0 for o in offset):
                        # Found data array with stencil access
                        # Find the weights array - must use DIFFERENT or SUBSET of loop vars
                        output_array = list(analyzer.array_writes.keys())[0] if analyzer.array_writes else None
                        output_writes = analyzer.array_writes.get(output_array, []) if output_array else []

                        # Get loop vars used in output
                        output_loop_vars = set()
                        for write in output_writes:
                            for idx in write:
                                if isinstance(idx, tuple) and idx[0] == 'var' and len(idx) >= 2:
                                    output_loop_vars.add(idx[1])

                        for other_arr in read_arrays:
                            if other_arr != arr:
                                # Check if this other array uses different/subset of loop vars
                                other_reads = analyzer.array_reads.get(other_arr, [])
                                is_valid_kernel = False

                                for other_read in other_reads:
                                    other_vars = set()
                                    has_constant_idx = False
                                    for idx in other_read:
                                        if isinstance(idx, tuple) and idx[0] == 'var' and len(idx) >= 2:
                                            other_vars.add(idx[1])
                                        elif isinstance(idx, tuple) and idx[0] == 'const':
                                            has_constant_idx = True

                                    # Valid kernel if:
                                    # 1. Uses constant indices (weighted stencil: weights[0])
                                    # 2. Uses DIFFERENT loop vars (convolution: kernel[j] vs result[i])
                                    # 3. Uses proper subset
                                    if has_constant_idx:
                                        is_valid_kernel = True
                                        break
                                    elif other_vars and not other_vars.intersection(output_loop_vars):
                                        is_valid_kernel = True
                                        break
                                    elif other_vars and other_vars < output_loop_vars:
                                        is_valid_kernel = True
                                        break

                                if is_valid_kernel:
                                    kernel_array = other_arr
                                    return ConvolutionInfo(
                                        dimensions=1 if analyzer.max_loop_depth == 1 else analyzer.max_loop_depth,
                                        kernel_size=(3,),
                                        input_array=arr,
                                        kernel_array=kernel_array,
                                        output_array=output_array
                                    )

        return None

    def _detect_outer_pattern(self, analyzer: LoopAnalyzer) -> Optional[OuterInfo]:
        """
        Detect outer product pattern.

        Pattern: C[i,j] = a[i] * b[j] (or other operation)
        """
        if analyzer.max_loop_depth < 2:
            return None

        # Look for pattern where we access two 1D arrays with different indices
        # and write to a 2D array

        for out_array, writes in analyzer.array_writes.items():
            # Check if output has 2D access
            for write in writes:
                if len(write) != 2:
                    continue

                # Find input arrays with 1D access
                input_arrays_1d = []
                for in_array, reads in analyzer.array_reads.items():
                    if in_array == out_array:
                        continue
                    for read in reads:
                        if len(read) == 1:
                            input_arrays_1d.append(in_array)
                            break

                if len(input_arrays_1d) >= 2:
                    # Likely outer product
                    # Determine operation
                    operation = 'multiply'

                    # Check assignments to see what operation is used
                    for assign in analyzer.assignments:
                        if isinstance(assign.value, ast.BinOp):
                            if isinstance(assign.value.op, ast.Add):
                                operation = 'add'
                            elif isinstance(assign.value.op, ast.Sub):
                                operation = 'subtract'
                            elif isinstance(assign.value.op, ast.Mult):
                                operation = 'multiply'

                    return OuterInfo(
                        left_vector=input_arrays_1d[0],
                        right_vector=input_arrays_1d[1] if len(input_arrays_1d) > 1 else None,
                        output_matrix=out_array,
                        operation=operation
                    )

        return None

    def _detect_stencil_pattern(self, analyzer: LoopAnalyzer) -> Optional[StencilInfo]:
        """Detect stencil computation patterns."""
        if len(analyzer.loops) < 1:
            return None

        # Need at least one nested loop for 2D stencil, or one loop for 1D
        if analyzer.max_loop_depth < 1:
            return None

        # Check for characteristic stencil access pattern
        # Stencil reads from neighbors: arr[i-1], arr[i+1], etc.
        neighbor_offsets: List[Tuple[int, ...]] = []
        input_arrays: Set[str] = set()
        output_arrays: Set[str] = set()

        for array_name, reads in analyzer.array_reads.items():
            offsets_for_array = []
            for read in reads:
                offset_tuple = self._extract_neighbor_offset(read, analyzer.loop_vars)
                if offset_tuple and any(o != 0 for o in offset_tuple):
                    offsets_for_array.append(offset_tuple)
                    input_arrays.add(array_name)

            neighbor_offsets.extend(offsets_for_array)

        for array_name in analyzer.array_writes:
            output_arrays.add(array_name)

        # Need neighbor access pattern for stencil
        if not neighbor_offsets:
            return None

        # Determine stencil type
        stencil_type = self._classify_stencil_type(neighbor_offsets)
        radius = self._calculate_stencil_radius(neighbor_offsets)
        dimensions = analyzer.max_loop_depth

        return StencilInfo(
            stencil_type=stencil_type,
            dimensions=dimensions,
            radius=radius,
            neighbor_offsets=neighbor_offsets,
            input_arrays=list(input_arrays),
            output_array=list(output_arrays)[0] if output_arrays else None
        )

    def _detect_map_pattern(self, analyzer: LoopAnalyzer) -> Optional[MapInfo]:
        """Detect element-wise map patterns."""
        if len(analyzer.loops) < 1:
            return None

        # Check for loop-carried dependency first
        if self._has_loop_carried_dependency(analyzer):
            return None

        # Map pattern: each iteration reads and writes to same index
        # arr[i] = f(arr[i]) or result[i] = f(input[i])
        has_array_access = bool(analyzer.array_reads or analyzer.array_writes)
        if not has_array_access:
            return None

        # Check that writes don't read from different indices
        for array_name, writes in analyzer.array_writes.items():
            # If we write to an array, check if we read from it at different offsets
            if array_name in analyzer.array_reads:
                reads = analyzer.array_reads[array_name]
                for read in reads:
                    for write in writes:
                        if self._has_offset_difference(read, write, analyzer.loop_vars):
                            # Reading from different index than writing - not a simple map
                            # Could be stencil, already checked
                            return None

        dimensions = analyzer.max_loop_depth
        complexity = 'simple'
        if analyzer.conditionals_in_loop:
            complexity = 'moderate'
        if len(analyzer.function_calls) > 3:
            complexity = 'complex'

        # Extract expression spec from assignments in loop
        expr_spec = None
        loop_domain = None

        if analyzer.assignments or analyzer.aug_assignments:
            # Get all array names
            all_arrays = set(analyzer.array_reads.keys()) | set(analyzer.array_writes.keys())

            # Try to extract from regular assignment first
            for assign in analyzer.assignments:
                if isinstance(assign.targets[0], ast.Subscript):
                    expr_spec = analyzer.extract_expression_spec(assign, all_arrays)
                    if expr_spec:
                        break

            # Fall back to augmented assignment
            if not expr_spec and analyzer.aug_assignments:
                expr_spec = analyzer.extract_expression_spec(analyzer.aug_assignments[0], all_arrays)

        # Extract loop domain
        if analyzer.loop_vars:
            loop_domain = LoopDomain(
                index_vars=tuple(analyzer.loop_vars),
                bounds_src=tuple(['0:n'] * len(analyzer.loop_vars))
            )

        return MapInfo(
            dimensions=dimensions,
            operation_complexity=complexity,
            has_conditionals=analyzer.conditionals_in_loop,
            input_arrays=list(analyzer.array_reads.keys()),
            output_array=list(analyzer.array_writes.keys())[0] if analyzer.array_writes else None,
            expr_spec=expr_spec,
            loop_domain=loop_domain
        )

    def _detect_reduce_pattern(self, analyzer: LoopAnalyzer) -> Optional[ReduceInfo]:
        """Detect reduction patterns (sum, max, min, product)."""
        if len(analyzer.loops) < 1 and len(analyzer.while_loops) < 1:
            return None

        # Look for accumulator operations
        if not analyzer.accumulator_ops:
            return None

        # Get the most common accumulator operation
        op_counts: Dict[str, int] = {}
        accum_vars: Dict[str, str] = {}
        for var, op in analyzer.accumulator_ops:
            op_counts[op] = op_counts.get(op, 0) + 1
            accum_vars[op] = var

        if not op_counts:
            return None

        main_op = max(op_counts, key=lambda x: op_counts[x])
        accum_var = accum_vars[main_op]

        # Determine properties based on operation
        is_associative = main_op in ('sum', 'product', 'max', 'min')
        is_commutative = main_op in ('sum', 'product', 'max', 'min')
        identity = {
            'sum': 0.0,
            'product': 1.0,
            'max': float('-inf'),
            'min': float('inf')
        }.get(main_op)

        input_array = list(analyzer.array_reads.keys())[0] if analyzer.array_reads else None

        # Extract the input expression (value being accumulated)
        input_expr = None
        all_arrays = set(analyzer.array_reads.keys())

        # Look for the expression in augmented assignments
        for aug in analyzer.aug_assignments:
            if isinstance(aug.target, ast.Name) and aug.target.id == accum_var:
                input_expr = analyzer.extract_expression_spec(aug, all_arrays)
                break

        # For conditional max/min patterns (if abs(arr[i]) > max_val: max_val = abs(arr[i]))
        # Extract the expression from the assignment inside the conditional
        if input_expr is None and main_op in ('max', 'min'):
            for assign in analyzer.assignments:
                if (isinstance(assign.targets[0], ast.Name) and
                    assign.targets[0].id == accum_var):
                    # Extract the RHS of the assignment
                    expr_src = ast.unparse(assign.value)
                    input_arrays_in_expr = [arr for arr in all_arrays if arr in expr_src]
                    input_expr = ExprSpec(
                        src=expr_src,
                        input_arrays=input_arrays_in_expr,
                        scalar_vars=[]
                    )
                    break

        return ReduceInfo(
            operation=main_op,
            is_associative=is_associative,
            is_commutative=is_commutative,
            identity_element=identity,
            accumulator_var=accum_var,
            input_array=input_array,
            input_expr=input_expr
        )

    def _has_sequential_dependency(self, analyzer: LoopAnalyzer) -> bool:
        """
        Check for sequential dependencies that prevent parallelization.

        This specifically detects patterns where:
        - result[i] = result[i-1] + ... (prefix sum)
        - arr[i] = arr[i-1] + arr[i-2] (fibonacci/recurrence)

        These are NOT parallelizable because each iteration depends on
        the result of the previous iteration(s).

        This is DIFFERENT from stencil patterns where:
        - T_new[i,j] = (T[i-1,j] + T[i+1,j] + ...) / 4
        Here T and T_new are DIFFERENT arrays, so no dependency.
        """
        for array_name, writes in analyzer.array_writes.items():
            # Only check if we WRITE to an array that we also READ from
            if array_name not in analyzer.array_reads:
                continue

            reads = analyzer.array_reads[array_name]

            # For each write to this array
            for write in writes:
                write_offset = self._get_loop_var_offset(write, analyzer.loop_vars)
                if write_offset is None:
                    continue

                # Check if any read from the SAME array uses an earlier index
                for read in reads:
                    read_offset = self._get_loop_var_offset(read, analyzer.loop_vars)
                    if read_offset is None:
                        continue

                    # Sequential dependency: reading from earlier index of same array
                    # Example: result[i] (write, offset=0) depends on result[i-1] (read, offset=-1)
                    if read_offset < write_offset:
                        return True

        return False

    def _detect_loop_carried_dependency_in_writes(
        self,
        analyzer: LoopAnalyzer
    ) -> bool:
        """
        Specifically detect loop-carried dependencies where:
        - result[i] depends on result[i-1] (prefix sum pattern)
        - arr[i] depends on arr[i-1] and arr[i-2] (fibonacci pattern)
        """
        for array_name, writes in analyzer.array_writes.items():
            if array_name not in analyzer.array_reads:
                continue

            reads = analyzer.array_reads[array_name]

            # Check each write against reads of the SAME array
            for write in writes:
                write_offset = self._get_loop_var_offset(write, analyzer.loop_vars)
                if write_offset is None:
                    continue

                for read in reads:
                    read_offset = self._get_loop_var_offset(read, analyzer.loop_vars)
                    if read_offset is None:
                        continue

                    # If we read from an earlier index than we write, it's a dependency
                    # Example: result[i] = result[i-1] + arr[i]
                    # write_offset = 0 (i), read_offset = -1 (i-1)
                    # Since read comes from earlier iteration, dependency exists
                    if read_offset < write_offset:
                        return True

        return False

    def _get_loop_var_offset(
        self,
        access: Tuple[Any, ...],
        loop_vars: List[str]
    ) -> Optional[int]:
        """Extract offset relative to loop variable from array access."""
        for idx in access:
            if isinstance(idx, tuple) and len(idx) >= 3:
                kind, var, offset = idx[0], idx[1], idx[2]
                if kind == 'var' and var in loop_vars:
                    return offset if isinstance(offset, int) else 0
            elif isinstance(idx, tuple) and len(idx) >= 2:
                kind, var = idx[0], idx[1]
                if kind == 'var' and var in loop_vars:
                    return 0
        return None

    def _has_loop_carried_dependency(self, analyzer: LoopAnalyzer) -> bool:
        """Check for loop-carried dependencies."""
        # Use the more precise detection method
        if self._detect_loop_carried_dependency_in_writes(analyzer):
            return True

        # Also check with the original method for edge cases
        for array_name, writes in analyzer.array_writes.items():
            if array_name not in analyzer.array_reads:
                continue

            reads = analyzer.array_reads[array_name]

            for write in writes:
                for read in reads:
                    # Check if read depends on write from previous iteration
                    if self._read_depends_on_previous_write(read, write, analyzer.loop_vars):
                        return True

        return False

    def _read_depends_on_previous_write(
        self,
        read: Tuple[Any, ...],
        write: Tuple[Any, ...],
        loop_vars: List[str]
    ) -> bool:
        """Check if a read depends on a write from a previous iteration."""
        # For each dimension, check if read index is write index minus some value
        for r, w in zip(read, write):
            if len(r) >= 3 and len(w) >= 3:
                r_kind, r_var, r_offset = r[0], r[1], r[2] if len(r) > 2 else 0
                w_kind, w_var, w_offset = w[0], w[1], w[2] if len(w) > 2 else 0

                if r_kind == 'var' and w_kind == 'var':
                    if r_var == w_var and r_var in loop_vars:
                        # Same loop variable - check offset
                        # If reading from i-1 and writing to i, it's a dependency
                        if isinstance(r_offset, (int, float)) and isinstance(w_offset, (int, float)):
                            if r_offset < w_offset:
                                # Reading from earlier index than writing
                                return True

        return False

    def _extract_neighbor_offset(
        self,
        access: Tuple[Any, ...],
        loop_vars: List[str]
    ) -> Optional[Tuple[int, ...]]:
        """Extract the offset from a neighbor access pattern."""
        offsets = []
        for idx in access:
            if isinstance(idx, tuple) and len(idx) >= 3:
                kind, var, offset = idx[0], idx[1], idx[2]
                if kind == 'var' and var in loop_vars:
                    offsets.append(offset if isinstance(offset, int) else 0)
                else:
                    offsets.append(0)
            elif isinstance(idx, tuple) and len(idx) >= 2:
                kind = idx[0]
                if kind == 'var':
                    offsets.append(0)
                else:
                    offsets.append(0)
            else:
                offsets.append(0)

        return tuple(offsets) if offsets else None

    def _has_offset_difference(
        self,
        read: Tuple[Any, ...],
        write: Tuple[Any, ...],
        loop_vars: List[str]
    ) -> bool:
        """Check if read and write have different offsets."""
        for r, w in zip(read, write):
            if len(r) >= 3 and len(w) >= 3:
                r_offset = r[2] if len(r) > 2 else 0
                w_offset = w[2] if len(w) > 2 else 0
                if r_offset != w_offset:
                    return True
        return False

    def _classify_stencil_type(self, neighbor_offsets: List[Tuple[int, ...]]) -> str:
        """Classify stencil type based on neighbor offsets."""
        unique_offsets = set(neighbor_offsets)

        # Check for 2D stencils
        if all(len(o) == 2 for o in unique_offsets):
            # 5-point: (+-1, 0) and (0, +-1)
            cardinal = {(-1, 0), (1, 0), (0, -1), (0, 1)}
            if cardinal.issubset(unique_offsets):
                # Check for diagonals
                diagonal = {(-1, -1), (-1, 1), (1, -1), (1, 1)}
                if diagonal.issubset(unique_offsets):
                    return '9-point'
                return '5-point'

        # Check for 1D stencils
        if all(len(o) == 1 for o in unique_offsets):
            return '3-point' if len(unique_offsets) <= 3 else 'custom'

        return 'custom'

    def _calculate_stencil_radius(self, neighbor_offsets: List[Tuple[int, ...]]) -> int:
        """Calculate the stencil radius from neighbor offsets."""
        max_offset = 0
        for offset in neighbor_offsets:
            for o in offset:
                if isinstance(o, int):
                    max_offset = max(max_offset, abs(o))
        return max_offset if max_offset > 0 else 1

    def _detect_memory_pattern(self, analyzer: LoopAnalyzer) -> str:
        """Detect memory access pattern (coalesced, strided, random)."""
        # Check for strided access
        for reads in analyzer.array_reads.values():
            for read in reads:
                for idx in read:
                    if isinstance(idx, tuple) and idx[0] == 'strided':
                        return 'strided'

        for writes in analyzer.array_writes.values():
            for write in writes:
                for idx in write:
                    if isinstance(idx, tuple) and idx[0] == 'strided':
                        return 'strided'

        # Default to coalesced for simple sequential access
        return 'coalesced'

    def _calculate_stencil_confidence(
        self,
        stencil_info: StencilInfo,
        analyzer: LoopAnalyzer
    ) -> float:
        """Calculate confidence score for stencil detection."""
        confidence = 0.8  # Base confidence

        # Higher confidence for recognized patterns
        if stencil_info.stencil_type in ('5-point', '9-point', '3-point'):
            confidence += 0.1

        # Lower confidence for conditionals
        if analyzer.conditionals_in_loop:
            confidence -= 0.1

        # Higher confidence for clean nested loops
        if len(analyzer.loops) == stencil_info.dimensions:
            confidence += 0.05

        return min(max(confidence, 0.0), 1.0)

    def _calculate_map_confidence(
        self,
        map_info: MapInfo,
        analyzer: LoopAnalyzer
    ) -> float:
        """Calculate confidence score for map detection."""
        confidence = 0.85  # Base confidence for map

        # Lower for conditionals
        if map_info.has_conditionals:
            confidence -= 0.15

        # Lower for complex operations
        if map_info.operation_complexity == 'complex':
            confidence -= 0.1
        elif map_info.operation_complexity == 'moderate':
            confidence -= 0.05

        return min(max(confidence, 0.0), 1.0)

    def _calculate_reduce_confidence(
        self,
        reduce_info: ReduceInfo,
        analyzer: LoopAnalyzer
    ) -> float:
        """Calculate confidence score for reduce detection."""
        confidence = 0.85  # Base confidence

        # Higher for associative operations
        if reduce_info.is_associative:
            confidence += 0.1

        return min(max(confidence, 0.0), 1.0)

    def _detect_compare_swap_pattern(self, analyzer: LoopAnalyzer) -> Optional[CompareSwapInfo]:
        """
        Detect compare-swap pattern (sorting networks).

        Pattern: if arr[i] > arr[i+1]: arr[i], arr[i+1] = arr[i+1], arr[i]

        This is used in:
        - Bubble sort (step=1, not parallelizable across outer loop)
        - Odd-even sort phases (step=2, parallelizable within phase)
        - Bitonic sort phases (various patterns, parallelizable)
        """
        # Need tuple swap and conditionals
        if not analyzer.has_tuple_swap:
            return None

        if not analyzer.conditionals_in_loop:
            return None

        # Find the array being sorted
        array_name = None
        for arr in analyzer.array_writes:
            if arr in analyzer.array_reads:
                array_name = arr
                break

        if not array_name:
            return None

        # Check if step is 2 (odd-even sort phase - parallelizable)
        # or step is 1 (bubble sort - sequential)
        step = analyzer.loop_step
        is_parallel_phase = step >= 2

        return CompareSwapInfo(
            array=array_name,
            is_parallel_phase=is_parallel_phase,
            step=step
        )

    def _analyze_bytecode_for_stencil(self, func: Callable) -> Optional[PatternAnalysis]:
        """
        Analyze function bytecode to detect stencil patterns when source is unavailable.

        CRITICAL FIX (Jan 2025 RCA): For Jupyter notebooks and exec'd code,
        source extraction fails because co_filename='<string>'. This method
        enables GPU acceleration for notebooks by detecting stencil patterns
        via bytecode analysis.

        Stencil pattern indicators in bytecode:
        1. Nested FOR_ITER loops (typically 2 levels for 2D arrays)
        2. LOAD_GLOBAL 'range' calls
        3. BINARY_SUBSCR (array indexing)
        4. BINARY_OP with constants (i-1, i+1, j-1, j+1 patterns)
        5. STORE_SUBSCR (array writes)

        Args:
            func: Function to analyze

        Returns:
            PatternAnalysis if stencil pattern detected, None otherwise
        """
        import dis
        import types

        if not isinstance(func, types.FunctionType):
            return None

        func_name = getattr(func, '__name__', '<unknown>')

        try:
            code = func.__code__
            instructions = list(dis.get_instructions(code))

            # Counters for stencil pattern indicators
            for_iter_count = 0
            range_calls = 0
            binary_subscr_count = 0
            store_subscr_count = 0
            offset_patterns = 0  # i-1, i+1, j-1, j+1 patterns

            # Track local variable indices that might be loop vars
            loop_vars = set()
            pending_var = None

            for i, instr in enumerate(instructions):
                # Count FOR_ITER (loop headers)
                if instr.opname == 'FOR_ITER':
                    for_iter_count += 1

                # Detect range() calls
                if instr.opname in ('LOAD_GLOBAL', 'LOAD_NAME') and instr.argval == 'range':
                    range_calls += 1

                # Count array subscript operations
                if instr.opname == 'BINARY_SUBSCR':
                    binary_subscr_count += 1

                if instr.opname == 'STORE_SUBSCR':
                    store_subscr_count += 1

                # Track loop iteration variables (typically stored after FOR_ITER)
                if instr.opname == 'STORE_FAST':
                    # After FOR_ITER, next STORE_FAST is loop variable
                    if i > 0 and instructions[i-1].opname == 'FOR_ITER':
                        loop_vars.add(instr.argval)

                # Detect offset patterns like (i - 1), (i + 1), (j - 1), (j + 1)
                # Pattern: LOAD_FAST loop_var, LOAD_CONST 1, BINARY_OP ADD/SUB
                if instr.opname == 'LOAD_FAST' and instr.argval in loop_vars:
                    pending_var = instr.argval
                elif pending_var and instr.opname == 'LOAD_CONST' and instr.argval == 1:
                    # Next instruction should be BINARY_OP
                    if i + 1 < len(instructions):
                        next_instr = instructions[i + 1]
                        if next_instr.opname == 'BINARY_OP' and next_instr.argval in (0, 10, 5, 11):
                            # 0=ADD, 10=SUB, 5=ADD, 11=SUBTRACT (varies by Python version)
                            offset_patterns += 1
                            pending_var = None
                elif instr.opname not in ('LOAD_CONST', 'NOP', 'RESUME'):
                    pending_var = None

            # Stencil pattern heuristics:
            # - At least 2 nested loops (for 2D stencil)
            # - Range-based iteration
            # - Multiple array accesses (reads)
            # - Array writes (result storage)
            # - Offset patterns (i-1, i+1, etc.) for neighbor access
            is_stencil = (
                for_iter_count >= 2 and            # At least 2 nested loops
                range_calls >= 2 and               # Range-based iteration
                binary_subscr_count >= 4 and       # Multiple array reads (neighbor access)
                store_subscr_count >= 1 and        # At least one array write
                offset_patterns >= 2               # At least 2 offset patterns (left/right or up/down)
            )

            if is_stencil:
                logger.info(
                    f"Bytecode stencil detection for '{func_name}': "
                    f"loops={for_iter_count}, range_calls={range_calls}, "
                    f"subscr_reads={binary_subscr_count}, subscr_writes={store_subscr_count}, "
                    f"offset_patterns={offset_patterns} -> STENCIL DETECTED"
                )

                # Create PatternAnalysis for stencil pattern
                # Use correct StencilInfo fields: stencil_type, dimensions, radius,
                # neighbor_offsets, input_arrays, output_array, loop_bounds
                analysis = PatternAnalysis(
                    function_name=func_name,
                    pattern_type='stencil',
                    parallelizable=True,
                    confidence=0.75,  # Lower confidence for bytecode-based detection
                    dimensions=2,     # Assume 2D stencil (most common)
                    memory_pattern='strided',
                    stencil_info=StencilInfo(
                        stencil_type='5-point',  # Assume 5-point stencil (most common)
                        dimensions=2,
                        radius=1,
                        neighbor_offsets=[(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)],
                        input_arrays=['grid'],
                        output_array='result'
                    )
                )
                return analysis

            logger.debug(
                f"Bytecode stencil detection for '{func_name}': "
                f"loops={for_iter_count}, range_calls={range_calls}, "
                f"subscr_reads={binary_subscr_count}, subscr_writes={store_subscr_count}, "
                f"offset_patterns={offset_patterns} -> NOT STENCIL"
            )
            return None

        except Exception as e:
            logger.debug(f"Bytecode stencil analysis failed for {func_name}: {e}")
            return None

    def _detect_modular_patterns(
        self,
        source: str,
        tree: ast.AST,
        func_name: str
    ) -> Optional[PatternAnalysis]:
        """
        Detect patterns using the modular PatternRegistry system.

        This checks for FFT, Rolling Stats, Black-Scholes, and Monte Carlo patterns
        which are library-call patterns that don't require loop analysis.

        Args:
            source: Source code as string
            tree: Parsed AST
            func_name: Function name for logging

        Returns:
            PatternAnalysis if a modular pattern is detected, None otherwise.
        """
        try:
            registry = create_default_registry()
            pattern_info = registry.detect_first(source, tree)

            if pattern_info is None:
                return None

            # Convert the pattern info to PatternAnalysis
            analysis = PatternAnalysis(
                function_name=func_name,
                pattern_type=pattern_info.pattern_name,
                parallelizable=pattern_info.gpu_suitable,
                confidence=pattern_info.confidence,
                dimensions=getattr(pattern_info, 'dimensions', 1),
                memory_pattern=pattern_info.memory_pattern,
                source_lines=len(source.splitlines())
            )

            # Set the appropriate pattern-specific info field
            if isinstance(pattern_info, FFTInfo):
                analysis.fft_info = pattern_info
            elif isinstance(pattern_info, RollingStatsInfo):
                analysis.rolling_stats_info = pattern_info
            elif isinstance(pattern_info, BlackScholesInfo):
                analysis.black_scholes_info = pattern_info
            elif isinstance(pattern_info, MonteCarloInfo):
                analysis.monte_carlo_info = pattern_info

            logger.debug(
                f"Modular pattern detected for '{func_name}': "
                f"{pattern_info.pattern_name} (confidence={pattern_info.confidence:.2f})"
            )
            return analysis

        except Exception as e:
            # Graceful degradation: log warning and fall back to traditional detection
            logger.warning(f"Modular pattern detection failed for {func_name}: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self._cache.clear()
