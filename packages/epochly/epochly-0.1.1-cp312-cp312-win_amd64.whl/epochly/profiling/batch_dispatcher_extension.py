"""
Batch Dispatcher Extension - Methods for dispatching pre-filtered chunks.

Extends BatchDispatcher with methods to handle pre-filtered indices from
break/continue transformations.

Author: Epochly Development Team
Date: November 18, 2025
"""

from typing import Callable, List, Any, Optional
import multiprocessing
import atexit
import os
import threading

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Global persistent pool for batch dispatch (eliminates creation overhead)
_global_pool = None
_global_pool_lock = None


def dispatch_chunks(self, func: Callable, chunks: List[List[Any]]) -> List[Any]:
    """
    Dispatch pre-chunked work items to parallel workers.

    This method is added to BatchDispatcher to support break/continue patterns
    where indices are pre-filtered and need custom chunking.

    Args:
        func: Function to apply to each chunk
        chunks: List of pre-prepared chunks to process

    Returns:
        List of results from each chunk
    """
    try:
        # PRIORITY 1: Use Level 3 executor if available
        try:
            from ..core.epochly_core import get_epochly_core
            core = get_epochly_core()

            # Trigger lazy Level 3 initialization if deferred
            if hasattr(core, '_ensure_level3_initialized'):
                core._ensure_level3_initialized()

            if core and hasattr(core, '_sub_interpreter_executor') and core._sub_interpreter_executor:
                # Level 3 has pre-warmed workers
                return self._dispatch_chunks_with_level3(core._sub_interpreter_executor, func, chunks)
        except Exception as e:
            logger.debug(f"Level 3 executor not available for chunks: {e}")

        # PRIORITY 2: Use custom executor if provided
        if self.executor and self.executor.is_available():
            return self._dispatch_chunks_with_executor(func, chunks)

        # PRIORITY 3: Use multiprocessing.Pool
        return self._dispatch_chunks_with_multiprocessing(func, chunks)

    except Exception as e:
        logger.error(f"Failed to dispatch chunks: {e}")
        # Fallback: Sequential execution
        results = []
        for chunk in chunks:
            results.append(func(chunk))
        return results


def _dispatch_chunks_with_level3(self, level3_executor, func: Callable, chunks: List[List[Any]]) -> List[Any]:
    """
    Dispatch chunks using Level 3's pre-warmed executor.

    Args:
        level3_executor: Level 3 executor instance
        func: Function to apply to each chunk
        chunks: List of chunks to process

    Returns:
        List of results
    """
    try:
        logger.info(f"Dispatching {len(chunks)} chunks via Level 3 executor")

        # Submit all chunks
        futures = []
        for chunk in chunks:
            future = level3_executor.execute(func, chunk)
            futures.append(future)

        # Collect results
        results = []
        for future in futures:
            result = future.result()
            # Handle ExecutionResult wrapper
            if hasattr(result, 'result'):
                results.append(result.result)
            else:
                results.append(result)

        return results

    except Exception as e:
        logger.debug(f"Level 3 chunk dispatch failed: {e}")
        raise


def _dispatch_chunks_with_executor(self, func: Callable, chunks: List[List[Any]]) -> List[Any]:
    """
    Dispatch chunks using custom executor.

    Args:
        func: Function to apply to each chunk
        chunks: List of chunks to process

    Returns:
        List of results
    """
    try:
        logger.debug(f"Dispatching {len(chunks)} chunks via executor adapter")

        # Submit chunks
        futures = []
        for chunk in chunks:
            future = self.executor.submit(func, chunk)
            futures.append(future)

        # Collect results
        results = []
        for future in futures:
            unified_result = self.executor.get_result(future)
            if unified_result.success:
                results.append(unified_result.result)
            else:
                logger.warning(f"Chunk failed: {unified_result.error}")
                # Return empty result for failed chunk
                results.append(0)

        return results

    except Exception as e:
        logger.debug(f"Executor chunk dispatch failed: {e}")
        raise


def _dispatch_chunks_with_multiprocessing(self, func: Callable, chunks: List[List[Any]]) -> List[Any]:
    """
    Dispatch chunks using multiprocessing.Pool.

    Args:
        func: Function to apply to each chunk
        chunks: List of chunks to process

    Returns:
        List of results
    """
    global _global_pool, _global_pool_lock

    try:
        # Initialize lock if needed
        if _global_pool_lock is None:
            _global_pool_lock = threading.Lock()

        with _global_pool_lock:
            # Create persistent pool if needed
            if _global_pool is None:
                num_workers = min(os.cpu_count() or 4, 8)
                _global_pool = multiprocessing.Pool(processes=num_workers)
                logger.info(f"Created persistent multiprocessing.Pool with {num_workers} workers")

                # Register cleanup
                def cleanup_pool():
                    global _global_pool
                    if _global_pool:
                        _global_pool.close()
                        _global_pool.join()
                        _global_pool = None
                atexit.register(cleanup_pool)

            pool = _global_pool

        logger.info(f"Using multiprocessing.Pool for {len(chunks)} chunks")

        # Map function to chunks
        results = pool.map(func, chunks)

        return results

    except Exception as e:
        logger.debug(f"Multiprocessing chunk dispatch failed: {e}")
        raise


# Monkey-patch the methods onto BatchDispatcher class
def extend_batch_dispatcher():
    """Extend BatchDispatcher with chunk dispatch methods."""
    from .batch_dispatcher import BatchDispatcher

    # Add methods to the class
    BatchDispatcher.dispatch_chunks = dispatch_chunks
    BatchDispatcher._dispatch_chunks_with_level3 = _dispatch_chunks_with_level3
    BatchDispatcher._dispatch_chunks_with_executor = _dispatch_chunks_with_executor
    BatchDispatcher._dispatch_chunks_with_multiprocessing = _dispatch_chunks_with_multiprocessing

    logger.debug("Extended BatchDispatcher with chunk dispatch methods")


# Auto-extend when module is imported
extend_batch_dispatcher()