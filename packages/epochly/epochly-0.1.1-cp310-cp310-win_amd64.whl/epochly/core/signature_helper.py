"""
Signature computation helper for ArgumentSizer integration.
"""

import hashlib
from typing import Any, Tuple, Callable


def compute_signature(func: Callable, args: Tuple, kwargs: dict) -> str:
    """
    Compute a signature for function call arguments.

    Used for caching argument size estimates.

    Args:
        func: Function being called
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Signature string
    """
    # Create signature from argument types and shapes
    arg_types = tuple(type(arg).__name__ for arg in args)
    kwarg_types = tuple((k, type(v).__name__) for k, v in sorted(kwargs.items()))

    # Include array shapes if available
    shapes = []
    for arg in args:
        if hasattr(arg, 'shape'):
            shapes.append(arg.shape)

    signature_data = (arg_types, kwarg_types, tuple(shapes))
    signature_str = str(signature_data)

    # Hash for compact representation
    return hashlib.md5(signature_str.encode()).hexdigest()[:16]
