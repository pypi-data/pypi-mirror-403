"""
Shared execution types for Epochly executor plugins.

This module contains common data structures used across different executor
implementations to avoid circular imports.

Author: Epochly Development Team
"""

from dataclasses import dataclass
from typing import Any, Optional, Callable, Tuple, Dict
from enum import Enum


class ExecutionMode(Enum):
    """Execution modes for different executors."""
    SYNC = "sync"
    ASYNC = "async"
    PARALLEL = "parallel"
    SUB_INTERPRETER = "sub_interpreter"


class ExecutionError(Exception):
    """Base exception for execution errors."""
    pass


@dataclass
class ExecutionRequest:
    """Base execution request."""
    func: Callable
    args: Tuple[Any, ...] = ()
    kwargs: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}


@dataclass
class ExecutionResult:
    """Result of task execution."""
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    memory_usage: int = 0
    interpreter_id: Optional[int] = None