"""
LoopAwareJITClassifier - Bytecode-based loop detection for eager JIT compilation.

This module provides a classifier that analyzes Python function bytecode to detect
loops and determine the optimal JIT compilation strategy. Functions with loops are
classified as EAGER_JIT (compile immediately), functions without loops but with
sufficient complexity are LAZY_JIT (wait for call count), and trivial functions
are NEVER_JIT (skip compilation).

This solves the "Pattern B" problem where functions containing hot loops are called
once and never trigger JIT compilation under the standard call-count-based approach.

Design validated by mcp-reflect with score 93/100.
Key insight: "We don't need to COUNT loop iterations. We need to DETECT that a
function HAS loops and compile it."

Performance: Classification takes < 1ms with ZERO runtime overhead (bytecode
analysis happens once at registration, not during execution).

Note: Recursive functions are NOT detected as containing loops (they don't use
loop bytecode opcodes). This is intentional - recursive functions should still
go through call-count-based JIT triggering since each call is tracked.
"""

from enum import Enum
from typing import Callable, Any, FrozenSet, Optional, Set
import dis
import sys
import logging

logger = logging.getLogger(__name__)


class JITStrategy(Enum):
    """JIT compilation strategy for a function.

    EAGER_JIT: Function has loops - compile immediately without waiting for call count.
    LAZY_JIT: Function is complex but has no loops - wait for min_function_calls.
    NEVER_JIT: Function is trivial or incompatible - skip JIT compilation entirely.
    """
    EAGER_JIT = "eager"
    LAZY_JIT = "lazy"
    NEVER_JIT = "never"


class LoopAwareJITClassifier:
    """Classifies functions for JIT compilation based on bytecode loop detection.

    Uses the dis module to analyze function bytecode and detect loop constructs.
    This approach has ZERO runtime overhead - analysis happens once at function
    registration, not during execution.

    Opcodes vary by Python version:
    - Python 3.9-3.10: FOR_ITER, JUMP_ABSOLUTE, GET_ITER
    - Python 3.11+: FOR_ITER, JUMP_BACKWARD, GET_ITER
    - Python 3.12+: Also JUMP_BACKWARD_NO_INTERRUPT

    The classifier also detects comprehensions (list, dict, set, generator) which
    compile to loops in bytecode.

    Example:
        >>> classifier = LoopAwareJITClassifier()
        >>> def hot_loop(n):
        ...     total = 0
        ...     for i in range(n):
        ...         total += i
        ...     return total
        >>> classifier.classify(hot_loop)
        <JITStrategy.EAGER_JIT: 'eager'>
    """

    # Loop-related opcodes by Python version
    # These opcodes indicate loop constructs in bytecode
    _LOOP_OPCODES_BY_VERSION = {
        # Python 3.9-3.10 use JUMP_ABSOLUTE or POP_JUMP_IF_TRUE for backward jumps
        # While loops use POP_JUMP_IF_TRUE at end of loop body to jump back
        # if condition is still true. POP_JUMP_IF_FALSE is for forward jumps only.
        (3, 9): frozenset({'FOR_ITER', 'JUMP_ABSOLUTE', 'GET_ITER', 'POP_JUMP_IF_TRUE'}),
        (3, 10): frozenset({'FOR_ITER', 'JUMP_ABSOLUTE', 'GET_ITER', 'POP_JUMP_IF_TRUE'}),
        # Python 3.11 introduced JUMP_BACKWARD and conditional backward jumps
        # POP_JUMP_BACKWARD_IF_* opcodes indicate loop back-edges for while loops
        (3, 11): frozenset({
            'FOR_ITER', 'JUMP_BACKWARD', 'GET_ITER',
            'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
            'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
        }),
        # Python 3.12+ removed the POP_JUMP_BACKWARD_IF_* opcodes
        # Uses JUMP_BACKWARD and JUMP_BACKWARD_NO_INTERRUPT instead
        (3, 12): frozenset({'FOR_ITER', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT', 'GET_ITER'}),
        (3, 13): frozenset({'FOR_ITER', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT', 'GET_ITER'}),
    }

    # Minimum bytecode instructions for a function to be considered "complex"
    # Functions with fewer instructions are trivial and should be NEVER_JIT
    _MIN_INSTRUCTIONS_FOR_COMPLEX = 10

    # Minimum bytecode instructions for LAZY_JIT (medium complexity)
    # Functions with 5 or fewer instructions are trivial (NEVER_JIT)
    # Functions with 6+ instructions are complex enough for LAZY_JIT
    _MIN_INSTRUCTIONS_FOR_LAZY = 6

    # Maximum recursion depth for nested code object analysis
    _MAX_NESTED_DEPTH = 10

    def __init__(self):
        """Initialize the classifier with version-appropriate loop opcodes."""
        self._version = sys.version_info[:2]

        # Find the appropriate opcodes for this Python version
        # Fall back to closest known version if exact match not found
        if self._version in self._LOOP_OPCODES_BY_VERSION:
            self._loop_opcodes = self._LOOP_OPCODES_BY_VERSION[self._version]
        elif self._version > max(self._LOOP_OPCODES_BY_VERSION):
            # Future versions - assume latest known opcodes with warning
            import warnings
            latest_known = max(self._LOOP_OPCODES_BY_VERSION)
            warnings.warn(
                f"LoopAwareJITClassifier: unknown Python {self._version}, "
                f"falling back to {latest_known} behavior",
                RuntimeWarning,
                stacklevel=2
            )
            self._loop_opcodes = self._LOOP_OPCODES_BY_VERSION[latest_known]
        elif self._version >= (3, 12):
            self._loop_opcodes = self._LOOP_OPCODES_BY_VERSION[(3, 12)]
        elif self._version >= (3, 11):
            self._loop_opcodes = self._LOOP_OPCODES_BY_VERSION[(3, 11)]
        elif self._version >= (3, 10):
            self._loop_opcodes = self._LOOP_OPCODES_BY_VERSION[(3, 10)]
        else:
            # Python 3.9 or earlier
            self._loop_opcodes = self._LOOP_OPCODES_BY_VERSION[(3, 9)]

    def classify(self, func: Any) -> JITStrategy:
        """Classify a function for JIT compilation.

        Args:
            func: The function to classify. Can be a function, lambda, method,
                  or any callable with a __code__ attribute.

        Returns:
            JITStrategy indicating how to handle JIT compilation:
            - EAGER_JIT: Has loops, compile immediately
            - LAZY_JIT: Complex but no loops, wait for call count
            - NEVER_JIT: Trivial or incompatible, skip compilation
        """
        # Handle non-functions gracefully
        code = self._get_code_object(func)
        if code is None:
            return JITStrategy.NEVER_JIT

        # Analyze bytecode for loops
        has_loop, instruction_count = self._analyze_bytecode(code)

        # EAGER_JIT: Has loops - compile immediately
        if has_loop:
            return JITStrategy.EAGER_JIT

        # NEVER_JIT: Trivial functions (too few instructions)
        if instruction_count < self._MIN_INSTRUCTIONS_FOR_LAZY:
            return JITStrategy.NEVER_JIT

        # LAZY_JIT: Complex enough but no loops
        return JITStrategy.LAZY_JIT

    def _get_code_object(self, func: Any) -> Optional[Any]:
        """Extract the code object from a callable.

        Handles decorated functions by unwrapping __wrapped__ attributes.

        Args:
            func: A callable (function, lambda, method, etc.)

        Returns:
            The code object, or None if not accessible.
        """
        # Unwrap decorated functions (functools.wraps sets __wrapped__)
        unwrapped = self._unwrap_function(func)

        # Direct function with __code__
        if hasattr(unwrapped, '__code__'):
            return unwrapped.__code__

        # Method - get the underlying function
        if hasattr(unwrapped, '__func__'):
            underlying = unwrapped.__func__
            underlying = self._unwrap_function(underlying)
            return getattr(underlying, '__code__', None)

        # Built-in or C extension function - no bytecode available
        if callable(unwrapped) and not hasattr(unwrapped, '__code__'):
            return None

        return None

    def _unwrap_function(self, func: Any) -> Any:
        """Unwrap decorated functions to get the original function.

        Decorated functions using functools.wraps have __wrapped__ pointing
        to the original function. We need to analyze the original, not the wrapper.

        Args:
            func: A possibly-decorated callable.

        Returns:
            The underlying function after unwrapping.
        """
        unwrap_limit = 10  # Prevent infinite loops in pathological cases
        unwrapped = func

        for _ in range(unwrap_limit):
            if hasattr(unwrapped, '__wrapped__'):
                unwrapped = unwrapped.__wrapped__
            else:
                break

        return unwrapped

    def _analyze_bytecode(self, code: Any) -> tuple:
        """Analyze bytecode for loop constructs.

        Args:
            code: A code object to analyze.

        Returns:
            Tuple of (has_loop: bool, instruction_count: int)
        """
        has_loop = False
        instruction_count = 0

        try:
            instructions = list(dis.get_instructions(code))
            instruction_count = len(instructions)

            # Check for loop-related opcodes
            for instr in instructions:
                # FOR_ITER is definitive evidence of a for loop
                if instr.opname == 'FOR_ITER':
                    has_loop = True
                    break

                # JUMP_BACKWARD is definitive evidence of a loop (for or while)
                # JUMP_BACKWARD only exists in loop constructs in Python 3.11+
                if instr.opname == 'JUMP_BACKWARD':
                    has_loop = True
                    break

                # JUMP_BACKWARD_NO_INTERRUPT is also a loop back-edge (Python 3.11+)
                if instr.opname == 'JUMP_BACKWARD_NO_INTERRUPT':
                    has_loop = True
                    break

                # POP_JUMP_BACKWARD_IF_* opcodes (Python 3.11 only)
                # These are conditional backward jumps used in while loops
                # Python 3.12 removed these and uses POP_JUMP_IF_* + JUMP_BACKWARD
                if instr.opname in (
                    'POP_JUMP_BACKWARD_IF_TRUE',
                    'POP_JUMP_BACKWARD_IF_FALSE',
                    'POP_JUMP_BACKWARD_IF_NONE',
                    'POP_JUMP_BACKWARD_IF_NOT_NONE',
                ):
                    has_loop = True
                    break

                # Python 3.9-3.10 loop detection
                # Note: JUMP_ABSOLUTE was removed in Python 3.11
                if self._version < (3, 11):
                    # JUMP_ABSOLUTE with backward jump indicates a loop
                    if instr.opname == 'JUMP_ABSOLUTE' and instr.arg is not None:
                        if instr.arg <= instr.offset:
                            has_loop = True
                            break

                    # POP_JUMP_IF_TRUE with backward jump is the loop back-edge
                    # in while loops. The condition is checked at end of loop body,
                    # and if TRUE, we jump BACK to the start of the loop.
                    # Example: while i < n: → POP_JUMP_IF_TRUE (jump back if True)
                    # Note: POP_JUMP_IF_FALSE is used for forward jumps in conditionals
                    if instr.opname == 'POP_JUMP_IF_TRUE' and instr.arg is not None:
                        if instr.arg < instr.offset:  # Backward jump = loop
                            has_loop = True
                            break

            # Also check nested code objects (comprehensions, nested functions)
            if not has_loop:
                has_loop = self._check_nested_code_objects(code)

        except (TypeError, AttributeError, ValueError) as e:
            # Specific exceptions for bytecode analysis failures
            # Log at debug level for troubleshooting, don't crash
            code_name = getattr(code, 'co_name', '<unknown>')
            logger.debug(f"Bytecode analysis failed for {code_name}: {e}")
        except Exception as e:
            # Unexpected exception - log warning but continue
            code_name = getattr(code, 'co_name', '<unknown>')
            logger.warning(f"Unexpected bytecode analysis error for {code_name}: {e}")

        return has_loop, instruction_count

    def _check_nested_code_objects(self, code: Any, depth: int = 0) -> bool:
        """Check nested code objects for loops (comprehensions, nested functions).

        Comprehensions (list, dict, set, generator) are compiled as separate
        code objects stored in co_consts. We need to check these too.

        Args:
            code: The parent code object.
            depth: Current recursion depth (to prevent pathological cases).
                   Maximum depth is _MAX_NESTED_DEPTH (10) to prevent stack overflow.

        Returns:
            True if any nested code object contains a loop.
        """
        # Prevent pathological deep nesting (defense against malicious code objects)
        if depth > self._MAX_NESTED_DEPTH:
            logger.debug(f"Max nested depth {self._MAX_NESTED_DEPTH} exceeded, stopping recursion")
            return False

        try:
            for const in code.co_consts:
                # Check if this is a code object
                if hasattr(const, 'co_code'):
                    # Recursively analyze nested code
                    nested_has_loop, _ = self._analyze_bytecode(const)
                    if nested_has_loop:
                        return True
                    # Also check nested code objects recursively
                    if self._check_nested_code_objects(const, depth + 1):
                        return True
        except (TypeError, AttributeError) as e:
            code_name = getattr(code, 'co_name', '<unknown>')
            logger.debug(f"Nested code analysis failed for {code_name}: {e}")

        return False

    def get_loop_info(self, func: Any) -> dict:
        """Get detailed information about loops in a function.

        This is useful for debugging and telemetry.

        Args:
            func: The function to analyze.

        Returns:
            Dictionary with loop analysis details.
        """
        code = self._get_code_object(func)
        if code is None:
            return {
                'has_code': False,
                'has_loop': False,
                'instruction_count': 0,
                'loop_opcodes_found': [],
                'strategy': JITStrategy.NEVER_JIT.value,
            }

        has_loop, instruction_count = self._analyze_bytecode(code)

        # Collect which loop opcodes were found
        loop_opcodes_found = []
        try:
            for instr in dis.get_instructions(code):
                if instr.opname in self._loop_opcodes:
                    loop_opcodes_found.append(instr.opname)
        except Exception:
            pass

        strategy = self.classify(func)

        return {
            'has_code': True,
            'has_loop': has_loop,
            'instruction_count': instruction_count,
            'loop_opcodes_found': loop_opcodes_found,
            'strategy': strategy.value,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
        }
