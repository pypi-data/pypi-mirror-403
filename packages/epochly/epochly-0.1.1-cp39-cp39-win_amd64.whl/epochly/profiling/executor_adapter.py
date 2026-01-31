"""
Executor Adapter - Unified API for Different Executor Types

Provides a consistent interface across:
- SubInterpreterPool (submit_task → Future[ExecutionResult])
- ProcessPoolExecutor (submit → Future[result])
- ThreadPoolExecutor (submit → Future[result])

This allows batch dispatcher to work with any executor type transparently.

Author: Epochly Development Team
Date: November 17, 2025
"""

from typing import Callable, Any
from concurrent.futures import Future
from dataclasses import dataclass

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class UnifiedResult:
    """
    Unified result wrapper.

    Attributes:
        value: The actual result value
        execution_time: Time taken to execute (seconds)
        success: Whether execution succeeded
        error: Error message if failed
    """
    value: Any
    execution_time: float = 0.0
    success: bool = True
    error: str = None


class ExecutorAdapter:
    """
    Unified adapter for different executor types.

    Provides consistent submit() and get_result() interface regardless of
    underlying executor implementation.
    """

    def __init__(self, executor):
        """
        Initialize adapter with an executor.

        Args:
            executor: SubInterpreterPool, ProcessPoolExecutor, or ThreadPoolExecutor
        """
        self.executor = executor
        self._executor_type = self._detect_executor_type()
        logger.debug(f"ExecutorAdapter initialized with {self._executor_type} executor")

    def _detect_executor_type(self) -> str:
        """
        Detect executor type based on available methods.

        Returns:
            'subinterpreter', 'process', or 'thread'
        """
        if hasattr(self.executor, 'submit_task'):
            # SubInterpreterPool has unique submit_task method
            return 'subinterpreter'
        elif hasattr(self.executor, 'submit'):
            # ProcessPoolExecutor or ThreadPoolExecutor
            executor_class = self.executor.__class__.__name__
            if 'Process' in executor_class:
                return 'process'
            elif 'Thread' in executor_class:
                return 'thread'
            else:
                # Generic concurrent.futures executor
                return 'concurrent_futures'
        else:
            return 'unknown'

    def submit(self, func: Callable, *args, **kwargs) -> Future:
        """
        Submit task for execution.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Future object

        Raises:
            RuntimeError: If executor doesn't support submission
        """
        try:
            if self._executor_type == 'subinterpreter':
                # SubInterpreterPool API
                return self.executor.submit_task(func, *args, **kwargs)

            elif self._executor_type in ('process', 'thread', 'concurrent_futures'):
                # Standard concurrent.futures API
                return self.executor.submit(func, *args, **kwargs)

            else:
                raise RuntimeError(f"Executor type '{self._executor_type}' does not support submission")

        except Exception as e:
            logger.error(f"Failed to submit task: {e}")
            raise

    def get_result(self, future: Future, timeout: float = None) -> UnifiedResult:
        """
        Get result from Future, handling different result types.

        Args:
            future: Future object from submit()
            timeout: Optional timeout in seconds

        Returns:
            UnifiedResult with extracted value

        Raises:
            TimeoutError: If result not available within timeout
            Exception: If task execution failed
        """
        try:
            # Get result with timeout
            result = future.result(timeout=timeout)

            # Handle different result types
            if hasattr(result, 'success') and hasattr(result, 'result'):
                # ExecutionResult from SubInterpreterPool
                return UnifiedResult(
                    value=result.result,
                    execution_time=getattr(result, 'execution_time', 0.0),
                    success=result.success,
                    error=getattr(result, 'error', None)
                )

            else:
                # Raw result from ProcessPoolExecutor or ThreadPoolExecutor
                return UnifiedResult(
                    value=result,
                    success=True
                )

        except Exception as e:
            logger.debug(f"Failed to get result: {e}")
            return UnifiedResult(
                value=None,
                success=False,
                error=str(e)
            )

    def get_worker_count(self) -> int:
        """
        Get number of available workers.

        Returns:
            Number of workers or default value
        """
        # Try various methods to get worker count
        if hasattr(self.executor, 'get_worker_count'):
            return self.executor.get_worker_count()

        elif hasattr(self.executor, '_max_workers'):
            return self.executor._max_workers

        elif hasattr(self.executor, '_processes') and self.executor._processes:
            return len(self.executor._processes)

        elif hasattr(self.executor, '_threads') and self.executor._threads:
            return len(self.executor._threads)

        else:
            # Default to CPU count
            import os
            return os.cpu_count() or 4

    def is_available(self) -> bool:
        """
        Check if executor is available and functional.

        Returns:
            True if executor can accept tasks
        """
        if not self.executor:
            return False

        # Check if executor has been shut down
        if hasattr(self.executor, '_shutdown') and self.executor._shutdown:
            return False

        # Check if executor is initialized (for SubInterpreterPool)
        if hasattr(self.executor, '_initialized') and not self.executor._initialized:
            return False

        return True


def create_executor_adapter(executor=None):
    """
    Create an executor adapter with auto-detection.

    Args:
        executor: Executor instance or None for auto-detection

    Returns:
        ExecutorAdapter or None if no executor available
    """
    if executor is None:
        # Try to get Level 3 executor from core
        try:
            from ..core.epochly_core import get_epochly_core
            core = get_epochly_core()

            # Trigger lazy Level 3 initialization if deferred
            if hasattr(core, '_ensure_level3_initialized'):
                core._ensure_level3_initialized()

            if core and hasattr(core, '_sub_interpreter_executor') and core._sub_interpreter_executor:
                # Level 3 has SubInterpreterExecutor wrapper
                if hasattr(core._sub_interpreter_executor, '_pool'):
                    executor = core._sub_interpreter_executor._pool
                    logger.debug("Using Level 3 SubInterpreterPool")
                else:
                    executor = core._sub_interpreter_executor
                    logger.debug("Using Level 3 SubInterpreterExecutor")

        except Exception as e:
            logger.debug(f"Could not get Level 3 executor: {e}")
            return None

    if executor:
        return ExecutorAdapter(executor)

    return None
