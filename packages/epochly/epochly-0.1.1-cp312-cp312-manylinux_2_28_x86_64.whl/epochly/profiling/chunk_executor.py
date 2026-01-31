"""
Chunk Executor - Module-level functions for parallel chunk execution.

Provides picklable functions for multiprocessing execution of loop chunks.
These functions must be at module level to be picklable by multiprocessing.

Author: Epochly Development Team
Date: November 18, 2025
"""

from typing import List, Any, Callable

from ..utils.logger import get_logger

logger = get_logger(__name__)


def execute_indices_on_func(args):
    """
    Execute a loop body function on a list of indices.

    This function is at module level so it can be pickled for multiprocessing.

    Args:
        args: Tuple of (loop_func, indices)
            - loop_func: The loop body function to execute
            - indices: List of indices to process

    Returns:
        Sum of results from executing loop_func on each index
    """
    loop_func, indices = args
    partial_result = 0
    for idx in indices:
        partial_result += loop_func(idx)
    return partial_result


def execute_chunk_simple(args):
    """
    Execute a function on each element in a chunk.

    Args:
        args: Tuple of (func, chunk)
            - func: Function to apply to each element
            - chunk: List of elements to process

    Returns:
        List of results from applying func to each element
    """
    func, chunk = args
    results = []
    for item in chunk:
        results.append(func(item))
    return results


def execute_filtered_indices(args):
    """
    Execute loop body on pre-filtered indices with optional continue filter.

    Args:
        args: Tuple of (loop_func, indices, continue_filter)
            - loop_func: The loop body function
            - indices: List of indices to process
            - continue_filter: Optional filter function for continue conditions

    Returns:
        Sum of results from valid indices
    """
    loop_func, indices, continue_filter = args
    partial_result = 0

    for idx in indices:
        # Apply continue filter if present
        if continue_filter and not continue_filter(idx):
            continue
        partial_result += loop_func(idx)

    return partial_result