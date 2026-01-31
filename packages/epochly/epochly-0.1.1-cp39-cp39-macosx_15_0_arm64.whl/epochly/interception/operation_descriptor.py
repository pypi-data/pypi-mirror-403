"""
Operation Descriptor for Transparent Interception

Provides a picklable wrapper that workers can use to reconstruct and execute
library operations without needing to serialize the wrapped function objects.

Author: Epochly Development Team
Date: November 16, 2025
"""

import importlib
from typing import Any, Tuple, Dict, Callable


class OperationDescriptor:
    """
    Picklable descriptor for library operations.

    Instead of sending the wrapped function object (which can't be pickled),
    we send this descriptor which contains:
    - Module name (e.g., 'numpy')
    - Function path (e.g., 'dot')
    - Arguments and kwargs

    Workers reconstruct the operation by importing the module and calling the function.

    Note: Does not use __slots__ to allow function-like attributes (__name__, __module__)
    for executor compatibility.
    """

    def __init__(
        self,
        module_name: str,
        function_path: str,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any]
    ):
        """
        Initialize operation descriptor.

        Args:
            module_name: Module to import (e.g., 'numpy')
            function_path: Function path in module (e.g., 'dot' or 'linalg.eig')
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
        """
        self.module_name = module_name
        self.function_path = function_path
        self.args = args
        self.kwargs = kwargs

    def __getattr__(self, name):
        """
        Provide function-like attributes dynamically for executor compatibility.

        The executor may access func.__name__, func.__module__, func.__qualname__.
        We provide these dynamically to avoid conflicts with class variables.
        """
        if name == '__name__':
            return f"{self.module_name}.{self.function_path}"
        elif name == '__module__':
            return self.module_name
        elif name == '__qualname__':
            return self.function_path
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def execute(self) -> Any:
        """
        Execute the operation in the current process/interpreter.

        This is called by workers to reconstruct and execute the operation.

        CRITICAL: Workers inherit wrapped functions from parent via fork/forkserver.
        We must unwrap to call the ORIGINAL function and prevent recursive Level 3
        submission deadlock (workers calling Level 3 → same pool → all workers blocked).

        Returns:
            Result from the function execution

        Raises:
            ImportError: If module cannot be imported
            AttributeError: If function doesn't exist in module
            Exception: Any exception raised by the function
        """
        # Import the module
        module = importlib.import_module(self.module_name)

        # Navigate to function (handle nested attributes like 'linalg.eig')
        func = module
        for part in self.function_path.split('.'):
            func = getattr(func, part)

        # CRITICAL FIX: Unwrap Epochly wrappers to prevent recursive Level 3 deadlock
        # Workers inherit wrapped functions from parent via fork/forkserver.
        # Wrapped functions have _original_function attribute storing the unwrapped version.
        # We must call the original to avoid recursive pool submission.
        original_func = getattr(func, '_original_function', None)
        if original_func is not None:
            func = original_func
            # Function was wrapped - now calling original to prevent recursion

        # Execute the (now unwrapped) function
        return func(*self.args, **self.kwargs)

    def __call__(self, *args, **kwargs) -> Any:
        """
        Allow calling the descriptor as a function.

        The executor may call operation(*args, **kwargs).
        We ignore these arguments since the operation already has its args stored.
        """
        return self.execute()

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"OperationDescriptor({self.module_name}.{self.function_path})"


def create_operation_from_op_id(
    op_id: str,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any]
) -> OperationDescriptor:
    """
    Create an OperationDescriptor from an operation ID.

    Args:
        op_id: Operation identifier (e.g., 'numpy.dot', 'pandas.DataFrame.merge')
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        OperationDescriptor instance

    Example:
        >>> desc = create_operation_from_op_id('numpy.dot', (a, b), {})
        >>> result = desc.execute()  # Workers call this
    """
    # Parse op_id: 'numpy.dot' -> module='numpy', function='dot'
    parts = op_id.split('.')
    module_name = parts[0]
    function_path = '.'.join(parts[1:])

    return OperationDescriptor(module_name, function_path, args, kwargs)
