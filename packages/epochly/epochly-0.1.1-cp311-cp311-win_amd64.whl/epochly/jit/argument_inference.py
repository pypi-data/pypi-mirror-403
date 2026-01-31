"""
Unified Argument Inference for JIT Compilation and Benchmarking

This module provides centralized argument generation logic for:
1. Triggering Numba compilation with appropriate dummy arguments
2. Benchmarking compiled functions with realistic test data

The key insight: Numerical computing functions often expect 2D arrays (matrices),
but naive argument generation uses scalars or 1D arrays, causing:
- Compilation trigger failures (function expects 2D, gets 1D)
- Benchmark failures (wrong argument types)
- Deferred machine code generation (first real call is slow)

This module consolidates the argument inference logic previously duplicated in:
- numba_jit.py (_trigger_compilation, _generate_trigger_arg_configs)
- manager.py (_infer_argument_value, _generate_benchmark_args)

Author: Epochly Development Team
"""

from __future__ import annotations

import inspect
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Any, Callable, List, Optional, Tuple

logger = logging.getLogger(__name__)


class InferencePurpose(Enum):
    """Purpose of argument inference - affects array sizes."""
    TRIGGER = "trigger"      # Small arrays for fast compilation trigger
    BENCHMARK = "benchmark"  # Larger arrays for meaningful performance measurement


@dataclass(frozen=True)
class ArrayShape:
    """Immutable array shape configuration."""
    rows: int
    cols: int

    def to_tuple(self) -> Tuple[int, int]:
        return (self.rows, self.cols)


class ArgumentInferenceConfig:
    """
    Central configuration for argument inference.

    All pattern matching and default values are defined here to ensure
    consistency between compilation triggers and benchmarking.
    """

    # Array parameter patterns - exact matches (highest priority)
    ARRAY_EXACT_MATCHES = frozenset({
        # Core array names
        'data', 'arr', 'array', 'matrix', 'x', 'y', 'a', 'b',
        'values', 'samples', 'features', 'input', 'output',
        'inputs', 'outputs', 'batch', 'tensor',
        # Output buffer patterns (critical for in-place operations)
        'out', 'dest', 'dst', 'result', 'target', 'buffer',
        'out_array', 'output_buffer', 'result_array'
    })

    # Array parameter suffixes (e.g., input_data, returns_array)
    ARRAY_SUFFIXES = (
        '_data', '_arr', '_array', '_matrix', '_values',
        '_samples', '_features', '_input', '_output', '_batch',
        '_out', '_dest', '_dst', '_result', '_buffer', '_target'
    )

    # Array parameter prefixes (e.g., data_input, array_values)
    ARRAY_PREFIXES = (
        'input_', 'output_', 'batch_', 'data_', 'array_',
        'matrix_', 'sample_', 'feature_',
        'out_', 'dest_', 'result_', 'buffer_', 'target_'
    )

    # Window/kernel size patterns - these get small integers
    WINDOW_EXACT_MATCHES = frozenset({
        'window', 'window_size', 'kernel', 'kernel_size',
        'k', 'w', 'size', 'width', 'step', 'stride'
    })

    WINDOW_SUFFIXES = ('_window', '_kernel', '_size', '_width', '_step')

    # Index/position patterns - get 0 or small values
    INDEX_EXACT_MATCHES = frozenset({
        'i', 'j', 'idx', 'index', 'pos', 'position', 'offset'
    })

    # Iteration/count patterns - get moderate values
    COUNT_EXACT_MATCHES = frozenset({
        'n', 'num', 'count', 'length', 'iterations', 'iters',
        'steps', 'loops', 'epochs', 'max_iter', 'max_iters', 'max_iterations'
    })

    # Bounds/limit patterns - scalar floats for min/max bounds
    # CRITICAL: Parameters like x_min, y_min, x_max, y_max are SCALARS not arrays!
    # These are commonly used in Mandelbrot, coordinate transforms, clipping, etc.
    BOUNDS_EXACT_MATCHES = frozenset({
        # Core min/max
        'min', 'max', 'low', 'high', 'lower', 'upper',
        # Coordinate bounds (critical for Mandelbrot, ray tracing, etc.)
        'x_min', 'x_max', 'y_min', 'y_max', 'z_min', 'z_max',
        'xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax',
        'x0', 'x1', 'y0', 'y1', 'z0', 'z1',  # Interval notation
        'left', 'right', 'top', 'bottom',    # Bounding box edges
        'width', 'height', 'depth',          # Dimensions (scalars)
        # Named bounds
        'min_val', 'max_val', 'min_value', 'max_value',
        'lower_bound', 'upper_bound', 'lb', 'ub',
        # Range/interval markers
        'start', 'end', 'begin', 'stop', 'limit', 'threshold',
        # Greek letters (common in scientific computing)
        'alpha', 'beta', 'gamma', 'epsilon', 'delta', 'sigma', 'tau',
        'lambda_', 'mu', 'nu', 'omega', 'phi', 'psi', 'theta', 'rho',
        # Scaling/transformation parameters
        'scale', 'factor', 'ratio', 'rate', 'coef', 'coefficient',
        'gain', 'offset', 'bias', 'weight', 'amplitude', 'frequency',
        # Tolerance/precision
        'tol', 'tolerance', 'atol', 'rtol', 'eps', 'precision'
    })

    BOUNDS_SUFFIXES = ('_min', '_max', '_low', '_high', '_bound', '_limit', '_threshold',
                       '_tol', '_tolerance', '_scale', '_factor', '_coef')

    # Sequence/categorical patterns - these should use int32
    # Common in genomics (DNA/RNA sequences), NLP (token indices), categorical encoding
    SEQUENCE_EXACT_MATCHES = frozenset({
        'seq', 'seq1', 'seq2', 'sequence', 'sequence1', 'sequence2',
        'sequences', 'tokens', 'token_ids', 'indices', 'labels',
        'categories', 'classes', 'ids', 'encoding', 'encoded'
    })

    SEQUENCE_PREFIXES = (
        'seq_', 'sequence_', 'token_', 'label_', 'category_',
        'class_', 'id_', 'encoded_'
    )

    # Shape configurations for different purposes
    SHAPES = {
        InferencePurpose.TRIGGER: ArrayShape(rows=20, cols=10),    # Small for fast trigger
        InferencePurpose.BENCHMARK: ArrayShape(rows=200, cols=50),  # Larger for meaningful benchmark
    }

    # Default values for different parameter types
    DEFAULTS = {
        'window': 5,
        'index': 0,
        'count': 100,
        'float': 1.0,
        'int': 10,
        'bool': True,
        'str': "test",
    }


def is_array_parameter(name: str, annotation: Any = inspect.Parameter.empty) -> bool:
    """
    Determine if a parameter should receive a numpy array.

    Uses precise matching (exact, prefix, suffix) to avoid false positives
    like matching 'window' in 'windows_path'.

    Args:
        name: Parameter name (case-insensitive)
        annotation: Type annotation if available

    Returns:
        True if parameter should be a numpy array
    """
    name_lower = name.lower()

    # CRITICAL FIX (Dec 14 2025): Check for SCALAR annotations FIRST
    # If annotation is explicitly int, float, bool, str - NOT an array
    # This prevents false positives like sample_rate: int being treated as array
    if annotation != inspect.Parameter.empty:
        annotation_str = str(annotation).lower()
        # Check for array annotations
        if 'ndarray' in annotation_str or 'array' in annotation_str:
            return True
        if 'np.ndarray' in annotation_str or 'numpy.ndarray' in annotation_str:
            return True
        # If explicitly scalar type, NOT an array
        if annotation in (int, float, bool, str):
            return False
        if annotation_str in ('int', 'float', 'bool', 'str'):
            return False

    # Exact match (highest priority for names)
    if name_lower in ArgumentInferenceConfig.ARRAY_EXACT_MATCHES:
        return True

    # Suffix match (e.g., input_data, returns_array)
    if name_lower.endswith(ArgumentInferenceConfig.ARRAY_SUFFIXES):
        return True

    # Prefix match (e.g., data_input, array_values)
    if name_lower.startswith(ArgumentInferenceConfig.ARRAY_PREFIXES):
        return True

    return False


def is_window_parameter(name: str) -> bool:
    """
    Determine if a parameter is a window/kernel size.

    Args:
        name: Parameter name (case-insensitive)

    Returns:
        True if parameter should be a small integer (window size)
    """
    name_lower = name.lower()

    if name_lower in ArgumentInferenceConfig.WINDOW_EXACT_MATCHES:
        return True

    if name_lower.endswith(ArgumentInferenceConfig.WINDOW_SUFFIXES):
        return True

    return False


def is_index_parameter(name: str) -> bool:
    """Determine if a parameter is an index/position."""
    return name.lower() in ArgumentInferenceConfig.INDEX_EXACT_MATCHES


def is_count_parameter(name: str) -> bool:
    """Determine if a parameter is a count/iteration number."""
    name_lower = name.lower()
    if name_lower in ArgumentInferenceConfig.COUNT_EXACT_MATCHES:
        return True
    # Also check for common patterns
    return any(p in name_lower for p in ['iter', 'count', 'num_', 'n_'])


def is_bounds_parameter(name: str) -> bool:
    """
    Determine if a parameter is a bounds/limit scalar (NOT an array).

    CRITICAL (Dec 2025): Parameters like x_min, y_min, x_max, y_max are SCALARS!
    The Mandelbrot demo was failing because these were being passed as 2D arrays
    instead of floats, causing Numba typing errors like:
        "Cannot unify float64 and array(float64, 2d, C) for 'y.2'"

    Returns:
        True if parameter should be treated as a scalar float
    """
    name_lower = name.lower()

    if name_lower in ArgumentInferenceConfig.BOUNDS_EXACT_MATCHES:
        return True

    if name_lower.endswith(ArgumentInferenceConfig.BOUNDS_SUFFIXES):
        return True

    return False


def is_sequence_parameter(name: str) -> bool:
    """
    Determine if a parameter is a sequence/categorical that should use int32.

    Common in:
    - Genomics: DNA/RNA sequences (seq1, seq2, sequences)
    - NLP: Token indices (tokens, token_ids)
    - ML: Categorical data (labels, categories, classes)

    Args:
        name: Parameter name (case-insensitive)

    Returns:
        True if parameter should be int32 (sequence/categorical data)
    """
    name_lower = name.lower()

    if name_lower in ArgumentInferenceConfig.SEQUENCE_EXACT_MATCHES:
        return True

    if name_lower.startswith(ArgumentInferenceConfig.SEQUENCE_PREFIXES):
        return True

    return False


def is_plural_sequence(name: str) -> bool:
    """
    Determine if a sequence parameter is plural (batch of sequences = 2D).

    Plural sequences get 2D arrays (batch dimension + sequence length).
    Singular sequences get 1D arrays (just sequence length).

    Args:
        name: Parameter name (case-insensitive)

    Returns:
        True if parameter represents multiple sequences (2D array needed)
    """
    name_lower = name.lower()

    # Plural forms need 2D arrays (batch of sequences)
    plural_indicators = ('sequences', 'tokens', 'token_ids', 'indices',
                         'labels', 'categories', 'classes', 'ids',
                         'encodings', 'encoded', 'seqs')

    return name_lower in plural_indicators or name_lower.endswith('s')


def generate_array(purpose: InferencePurpose, dtype: str = 'float64') -> Any:
    """
    Generate a numpy array appropriate for the given purpose.

    Args:
        purpose: TRIGGER (small) or BENCHMARK (larger)
        dtype: Array data type

    Returns:
        2D numpy array with appropriate shape, or None if numpy unavailable
    """
    try:
        import numpy as np
    except ImportError:
        logger.warning("NumPy not available for array generation")
        return None

    shape = ArgumentInferenceConfig.SHAPES[purpose]
    arr = np.random.rand(shape.rows, shape.cols)

    if dtype == 'float64':
        return arr.astype(np.float64)
    elif dtype == 'float32':
        return arr.astype(np.float32)
    elif dtype == 'int64':
        return (arr * 100).astype(np.int64)
    elif dtype == 'int32':
        return (arr * 100).astype(np.int32)
    else:
        return arr.astype(np.float64)


def generate_sequence_array(purpose: InferencePurpose, is_plural: bool) -> Any:
    """
    Generate an int32 array for sequence/categorical data.

    Sequence data (DNA/RNA, token IDs, categorical labels) uses int32.
    - Singular (seq1, seq2): 1D array of length cols
    - Plural (sequences, tokens): 2D array of shape (rows, cols)

    Args:
        purpose: TRIGGER (small) or BENCHMARK (larger)
        is_plural: True for 2D batch array, False for 1D single sequence

    Returns:
        int32 array (1D or 2D based on is_plural), or None if numpy unavailable
    """
    try:
        import numpy as np
    except ImportError:
        logger.warning("NumPy not available for sequence array generation")
        return None

    shape = ArgumentInferenceConfig.SHAPES[purpose]

    if is_plural:
        # 2D: batch of sequences (rows x cols)
        # Values 0-3 typical for DNA (A,C,G,T) or small categorical
        return np.random.randint(0, 4, size=(shape.rows, shape.cols), dtype=np.int32)
    else:
        # 1D: single sequence (just cols)
        return np.random.randint(0, 4, size=(shape.cols,), dtype=np.int32)


def infer_single_argument(
    param: inspect.Parameter,
    purpose: InferencePurpose,
    func: Optional[Callable] = None
) -> Any:
    """
    Infer an appropriate test value for a single parameter.

    Args:
        param: Function parameter to infer value for
        purpose: TRIGGER or BENCHMARK
        func: Optional function for additional context

    Returns:
        Inferred argument value, or fallback scalar if array generation fails
    """
    name = param.name
    annotation = param.annotation
    default = param.default

    # Try to import numpy for ndarray check
    try:
        import numpy as np
        has_numpy = True
    except ImportError:
        np = None
        has_numpy = False

    # Use default value if available (except for arrays which need proper shape)
    if default != inspect.Parameter.empty:
        # If default is a scalar but param looks like array, generate array
        is_default_ndarray = has_numpy and isinstance(default, np.ndarray)
        if not is_default_ndarray and is_array_parameter(name, annotation):
            arr = generate_array(purpose)
            if arr is not None:
                return arr
            # Fallback to scalar if array generation fails
            return ArgumentInferenceConfig.DEFAULTS['float']
        # If default is a scalar but param looks like sequence, generate int32 array
        if not is_default_ndarray and is_sequence_parameter(name):
            plural = is_plural_sequence(name)
            arr = generate_sequence_array(purpose, is_plural=plural)
            if arr is not None:
                return arr
            return ArgumentInferenceConfig.DEFAULTS['int']
        return default

    # CRITICAL FIX (Dec 27, 2025): Check bounds parameters FIRST!
    # Parameters like x_min, y_min, x_max, y_max are SCALARS, not arrays.
    # Without this check first, they might match is_array_parameter() if they
    # start with 'x' or 'y' (which are in ARRAY_EXACT_MATCHES).
    # The Mandelbrot demo was failing because bounds were passed as 2D arrays.
    if is_bounds_parameter(name):
        return ArgumentInferenceConfig.DEFAULTS['float']

    # Check for window/kernel size (scalars)
    if is_window_parameter(name):
        return ArgumentInferenceConfig.DEFAULTS['window']

    # Check for index (scalars)
    if is_index_parameter(name):
        return ArgumentInferenceConfig.DEFAULTS['index']

    # Check for count/iterations (scalars)
    if is_count_parameter(name):
        return ArgumentInferenceConfig.DEFAULTS['count']

    # CRITICAL FIX (Dec 14 2025 P0.5): Check sequence parameters BEFORE generic arrays!
    # Sequence parameters (seq1, seq2, sequences) have np.ndarray annotations but need
    # int32 dtype, not float64. Without this fix, they match is_array_parameter first
    # and get float64, causing signature mismatch and recompilation on every call.
    if is_sequence_parameter(name):
        plural = is_plural_sequence(name)
        arr = generate_sequence_array(purpose, is_plural=plural)
        if arr is not None:
            return arr
        # Fallback to scalar if array generation fails
        return ArgumentInferenceConfig.DEFAULTS['int']

    # Check for generic array parameter (after all scalar checks)
    if is_array_parameter(name, annotation):
        arr = generate_array(purpose)
        if arr is not None:
            return arr
        # Fallback to scalar if array generation fails
        return ArgumentInferenceConfig.DEFAULTS['float']

    # Check type annotation
    if annotation != inspect.Parameter.empty:
        if annotation in (int, 'int') or 'int' in str(annotation).lower():
            return ArgumentInferenceConfig.DEFAULTS['int']
        if annotation in (float, 'float') or 'float' in str(annotation).lower():
            return ArgumentInferenceConfig.DEFAULTS['float']
        if annotation in (bool, 'bool'):
            return ArgumentInferenceConfig.DEFAULTS['bool']
        if annotation in (str, 'str'):
            return ArgumentInferenceConfig.DEFAULTS['str']

    # Default: assume small integer (works for most window/size params)
    return ArgumentInferenceConfig.DEFAULTS['int']


def _get_cached_signature(func: Callable) -> inspect.Signature:
    """
    Get cached function signature to avoid repeated introspection.

    Uses functools.lru_cache for:
    - Bounded memory usage (maxsize=1024)
    - Thread safety
    - Automatic cache management

    Args:
        func: Function to get signature for

    Returns:
        Function signature
    """
    return _cached_signature_impl(func)


@lru_cache(maxsize=1024)
def _cached_signature_impl(func: Callable) -> inspect.Signature:
    """Internal cached implementation of signature extraction."""
    return inspect.signature(func)


def _has_variadic_params(params: List[inspect.Parameter]) -> bool:
    """
    Check if parameters include *args or **kwargs.

    Args:
        params: List of parameters to check

    Returns:
        True if any parameter is VAR_POSITIONAL or VAR_KEYWORD
    """
    variadic_kinds = (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    return any(p.kind in variadic_kinds for p in params)


def generate_arguments(
    func: Callable,
    purpose: InferencePurpose
) -> Optional[List[Any]]:
    """
    Generate a complete set of test arguments for a function.

    Args:
        func: Function to generate arguments for
        purpose: TRIGGER or BENCHMARK

    Returns:
        List of arguments or None if generation fails
    """
    func_name = getattr(func, '__name__', str(func))

    try:
        sig = _get_cached_signature(func)
        params = list(sig.parameters.values())

        if not params:
            return []

        # Handle functions with *args or **kwargs - we cannot reliably infer these
        if _has_variadic_params(params):
            logger.debug(
                f"Cannot infer args for {func_name} with *args/**kwargs"
            )
            return None

        args = []
        for param in params:
            # Skip VAR_POSITIONAL and VAR_KEYWORD (already filtered above, but defensive)
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            arg_value = infer_single_argument(param, purpose, func)
            args.append(arg_value)

        return args

    except Exception as e:
        logger.debug(f"Argument generation failed for {func_name}: {e}")
        return None


def generate_argument_configs(
    func: Callable,
    purpose: InferencePurpose
) -> List[List[Any]]:
    """
    Generate multiple argument configurations to try.

    CRITICAL: Numba compiles separate specializations for each dtype. We generate
    configurations for BOTH float64 AND int32 to avoid 10+ second compilation spikes
    when real data uses a different dtype than the trigger dtype.

    Tries different configurations in order of likelihood to succeed:
    1. Smart inference based on parameter names (float64)
    2. All 2D arrays with float64 (numerical computing default)
    3. All 2D arrays with int32 (genomics, text, categorical data)
    4. All 1D arrays with float64
    5. All 1D arrays with int32
    6. MIXED dtype: sequence params get int32, others get float64
       (CRITICAL for genomics - seq1/seq2 are int32, scoring_matrix is float64)
    7. Simple scalars (last resort)

    Args:
        func: Function to generate arguments for
        purpose: TRIGGER or BENCHMARK

    Returns:
        List of argument configurations to try
    """
    func_name = getattr(func, '__name__', str(func))

    try:
        import numpy as np
    except ImportError:
        logger.debug("NumPy not available for argument config generation")
        return []

    configs = []

    try:
        sig = _get_cached_signature(func)
        params = list(sig.parameters.values())

        if not params:
            return [[]]

        # Filter out variadic parameters (*args, **kwargs)
        regular_params = [
            p for p in params
            if p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        ]

        if not regular_params:
            logger.debug(f"No regular parameters for {func_name} (only *args/**kwargs)")
            return [[]]

        # Config 1: Smart inference (most likely to succeed)
        smart_args = generate_arguments(func, purpose)
        if smart_args:
            configs.append(smart_args)

        # Config 2: All 2D arrays with float64 (numerical computing default)
        shape = ArgumentInferenceConfig.SHAPES[purpose]
        all_2d_float64_args = []
        for param in regular_params:
            name = param.name.lower()
            if is_window_parameter(name) or is_index_parameter(name) or is_count_parameter(name):
                all_2d_float64_args.append(5)  # Small integer
            elif is_bounds_parameter(name):
                all_2d_float64_args.append(1.0)  # Scalar float for bounds (x_min, y_max, etc.)
            else:
                all_2d_float64_args.append(np.random.rand(shape.rows, shape.cols).astype(np.float64))
        configs.append(all_2d_float64_args)

        # Config 3: All 2D arrays with int32 (CRITICAL: genomics, text, categorical data)
        # Many real-world workloads use int32 for sequences, indices, categorical encodings
        all_2d_int32_args = []
        for param in regular_params:
            name = param.name.lower()
            if is_window_parameter(name) or is_index_parameter(name) or is_count_parameter(name):
                all_2d_int32_args.append(5)  # Small integer
            elif is_bounds_parameter(name):
                all_2d_int32_args.append(1.0)  # Scalar float for bounds
            else:
                # Generate int32 array with values in reasonable range (0-99)
                all_2d_int32_args.append(
                    np.random.randint(0, 100, size=(shape.rows, shape.cols), dtype=np.int32)
                )
        configs.append(all_2d_int32_args)

        # Config 4: All 1D arrays with float64 (some functions expect this)
        all_1d_float64_args = []
        for param in regular_params:
            name = param.name.lower()
            if is_window_parameter(name) or is_index_parameter(name) or is_count_parameter(name):
                all_1d_float64_args.append(5)
            elif is_bounds_parameter(name):
                all_1d_float64_args.append(1.0)  # Scalar float for bounds
            else:
                all_1d_float64_args.append(np.random.rand(shape.rows * shape.cols).astype(np.float64))
        configs.append(all_1d_float64_args)

        # Config 5: All 1D arrays with int32
        all_1d_int32_args = []
        for param in regular_params:
            name = param.name.lower()
            if is_window_parameter(name) or is_index_parameter(name) or is_count_parameter(name):
                all_1d_int32_args.append(5)
            elif is_bounds_parameter(name):
                all_1d_int32_args.append(1.0)  # Scalar float for bounds
            else:
                all_1d_int32_args.append(
                    np.random.randint(0, 100, size=shape.rows * shape.cols, dtype=np.int32)
                )
        configs.append(all_1d_int32_args)

        # Config 6: MIXED dtype - sequence params get int32, others get float64
        # This is CRITICAL for genomics/NLP workloads where:
        # - seq1, seq2 are int32 (DNA sequences, token IDs)
        # - scoring_matrix, weights are float64
        mixed_dtype_args = []
        for param in regular_params:
            name = param.name.lower()
            if is_window_parameter(name) or is_index_parameter(name) or is_count_parameter(name):
                mixed_dtype_args.append(5)  # Small integer
            elif is_bounds_parameter(name):
                mixed_dtype_args.append(1.0)  # Scalar float for bounds
            elif is_sequence_parameter(name):
                # Sequence parameters get 1D int32 (like DNA sequences)
                mixed_dtype_args.append(
                    np.random.randint(0, 4, size=shape.rows * shape.cols, dtype=np.int32)  # 0-3 for ACGT
                )
            else:
                # Other array parameters get 2D float64 (like scoring matrices)
                mixed_dtype_args.append(np.random.rand(shape.rows, shape.cols).astype(np.float64))
        configs.append(mixed_dtype_args)

        # Config 7: Simple scalars (last resort)
        scalar_args = []
        for param in regular_params:
            name = param.name.lower()
            if is_window_parameter(name) or is_index_parameter(name) or is_count_parameter(name):
                scalar_args.append(5)
            elif is_bounds_parameter(name):
                scalar_args.append(1.0)  # Scalar float for bounds
            else:
                scalar_args.append(1.0)
        configs.append(scalar_args)

        return configs

    except Exception as e:
        logger.debug(f"Config generation failed for {func_name}: {e}")
        return []


def validate_arguments(func: Callable, args: List[Any]) -> bool:
    """
    Validate that arguments work with the function.

    Args:
        func: Function to validate against
        args: Arguments to test

    Returns:
        True if arguments produce a valid result
    """
    try:
        result = func(*args)
        return result is not None
    except Exception:
        return False


def trigger_compilation(
    compiled_func: Callable,
    original_func: Callable,
    compile_all_dtypes: bool = False,
    parallel: bool = False
) -> bool:
    """
    Trigger Numba compilation by calling with dummy arguments.

    P0 WARMUP OPTIMIZATION (Jan 2026): Default changed from True to False.
    This reduces warmup time from ~14s to ~2s by compiling only the first
    successful dtype configuration. Additional dtypes are compiled on-demand
    when first encountered at runtime (Numba's standard behavior).

    P4 WARMUP OPTIMIZATION (Jan 2026): Added parallel compilation support.
    When compile_all_dtypes=True and parallel=True, dtype compilations run
    concurrently using a ThreadPoolExecutor. This reduces multi-dtype
    compilation time when eager mode is needed.

    Numba compiles separate native code for each dtype (float64, int32, etc).
    With compile_all_dtypes=False (default), we compile one dtype upfront and
    let Numba compile others on-demand. This is faster for most use cases.

    For scientific computing libraries that need predictable performance across
    all dtypes, pass compile_all_dtypes=True explicitly.

    Args:
        compiled_func: Numba-compiled function (CPUDispatcher)
        original_func: Original Python function for signature analysis
        compile_all_dtypes: If True, try all configs to compile multiple dtype specializations.
                           If False (default), stop at first success for faster warmup.
        parallel: If True and compile_all_dtypes=True, compile dtypes in parallel using
                 ThreadPoolExecutor. Default False for backwards compatibility.

    Returns:
        True if at least one compilation was triggered successfully
    """
    configs = generate_argument_configs(original_func, InferencePurpose.TRIGGER)

    if not configs:
        logger.debug(f"No argument configs generated for {original_func.__name__}")
        return False

    # P4: Use parallel compilation when requested and compiling all dtypes
    if compile_all_dtypes and parallel:
        return _trigger_compilation_parallel(compiled_func, original_func, configs)

    # Sequential compilation (original behavior)
    return _trigger_compilation_sequential(compiled_func, original_func, configs, compile_all_dtypes)


def _trigger_compilation_sequential(
    compiled_func: Callable,
    original_func: Callable,
    configs: List[Tuple],
    compile_all_dtypes: bool
) -> bool:
    """
    Sequential dtype compilation (original behavior).

    Args:
        compiled_func: Numba-compiled function
        original_func: Original Python function
        configs: List of argument configurations
        compile_all_dtypes: Whether to compile all dtypes or stop at first success

    Returns:
        True if at least one compilation succeeded
    """
    last_error = None
    success_count = 0
    triggered_dtypes = set()

    for i, args in enumerate(configs):
        try:
            # Track dtypes we're triggering
            arg_dtypes = tuple(
                getattr(a, 'dtype', type(a).__name__) for a in args
                if hasattr(a, 'dtype') or not isinstance(a, (int, float))
            )

            compiled_func(*args)
            success_count += 1
            triggered_dtypes.add(arg_dtypes)

            logger.debug(
                f"Triggered compilation for {original_func.__name__} with config {i}: "
                f"{[type(a).__name__ + (str(a.shape) + '/' + str(a.dtype) if hasattr(a, 'shape') else '') for a in args]}"
            )

            # If not compiling all dtypes, return after first success
            if not compile_all_dtypes:
                return True

            # Continue to try more configs to compile more dtype specializations
        except Exception as e:
            last_error = e
            logger.debug(f"Trigger config {i} failed for {original_func.__name__}: {e}")
            continue

    if success_count > 0:
        logger.debug(
            f"Triggered {success_count} Numba specializations for {original_func.__name__} "
            f"with dtypes: {triggered_dtypes}"
        )
        return True

    # All configs failed - log warning for debugging
    logger.warning(
        f"All trigger configurations failed for {original_func.__name__}. "
        f"Last error: {last_error}. Function will compile on first real call."
    )
    return False


def _trigger_compilation_parallel(
    compiled_func: Callable,
    original_func: Callable,
    configs: List[Tuple]
) -> bool:
    """
    P4 WARMUP OPTIMIZATION (Jan 2026): Parallel dtype compilation.

    Compiles multiple dtype configurations concurrently using ThreadPoolExecutor.
    This reduces total compilation time when eager mode requires all dtypes.

    Note: Due to Numba's internal locking and Python's GIL, parallelism may
    not provide dramatic speedups, but it enables compilation overlap and
    prevents blocking on individual long-running compilations.

    Args:
        compiled_func: Numba-compiled function
        original_func: Original Python function
        configs: List of argument configurations

    Returns:
        True if at least one compilation succeeded
    """
    success_count = 0
    triggered_dtypes = set()
    errors = []

    def compile_config(config_tuple):
        """Compile a single config (runs in thread pool)."""
        i, args = config_tuple
        try:
            # Track dtypes we're triggering
            arg_dtypes = tuple(
                getattr(a, 'dtype', type(a).__name__) for a in args
                if hasattr(a, 'dtype') or not isinstance(a, (int, float))
            )

            compiled_func(*args)

            logger.debug(
                f"[Parallel] Triggered compilation for {original_func.__name__} with config {i}: "
                f"{[type(a).__name__ + (str(a.shape) + '/' + str(a.dtype) if hasattr(a, 'shape') else '') for a in args]}"
            )

            return (True, arg_dtypes, None)
        except Exception as e:
            logger.debug(f"[Parallel] Trigger config {i} failed for {original_func.__name__}: {e}")
            return (False, None, e)

    # Use thread pool for parallel compilation
    # Limit workers to avoid overwhelming Numba's internal resources
    max_workers = min(4, len(configs))

    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="P4-Compile") as executor:
        # Submit all configs for parallel compilation
        futures = {
            executor.submit(compile_config, (i, args)): i
            for i, args in enumerate(configs)
        }

        # Collect results as they complete
        for future in as_completed(futures):
            success, dtypes, error = future.result()
            if success:
                success_count += 1
                if dtypes:
                    triggered_dtypes.add(dtypes)
            elif error:
                errors.append(error)

    if success_count > 0:
        logger.debug(
            f"[Parallel] Triggered {success_count} Numba specializations for {original_func.__name__} "
            f"with dtypes: {triggered_dtypes}"
        )
        return True

    # All configs failed - log warning for debugging
    last_error = errors[-1] if errors else None
    logger.warning(
        f"[Parallel] All trigger configurations failed for {original_func.__name__}. "
        f"Last error: {last_error}. Function will compile on first real call."
    )
    return False
