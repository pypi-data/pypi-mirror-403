"""
Epochly Executor Plugin Package

This package contains the executor components for Week 5 sub-interpreter implementation:
- SubInterpreterExecutor: Manages sub-interpreter pool for true multicore parallelization
- ThreadExecutor: Thread-based executor fallback for compatibility
- SharedMemoryManager: Handles shared memory between sub-interpreters
- ZeroCopyBuffer: Provides zero-copy data transfer mechanisms
- SubInterpreterPool: Pool management for one sub-interpreter per physical core

These components work together to enable true multicore parallelization using
CPython 3.12's per-interpreter GIL, integrating with Week 4 analyzer components
for intelligent workload distribution and memory optimization.

Author: Epochly Development Team
"""

import os
import sys
import platform
from typing import Dict, Optional, Union

from .execution_types import ExecutionResult
from .sub_interpreter_executor import (
    SubInterpreterExecutor,
    SubInterpreterPool,
    SubInterpreterError
)

from .thread_executor import ThreadExecutor

from .shared_memory_manager import (
    SharedMemoryManager,
    SharedMemorySegment,
    MemoryMappingError
)

from .zero_copy_buffer import (
    ZeroCopyBuffer,
    BufferView,
    TransferError
)

__all__ = [
    # Sub-interpreter Execution
    "SubInterpreterExecutor",
    "SubInterpreterPool",
    "ExecutionResult",
    "SubInterpreterError",
    
    # Thread-based Execution
    "ThreadExecutor",
    
    # Shared Memory Management
    "SharedMemoryManager",
    "SharedMemorySegment",
    "MemoryMappingError",
    
    # Zero-Copy Transfer
    "ZeroCopyBuffer",
    "BufferView",
    "TransferError"
]

# Version information
__version__ = "1.0.0"
__author__ = "Epochly Development Team"

# Package metadata
EXECUTOR_COMPONENTS = {
    "sub_interpreter_executor": {
        "class": "SubInterpreterExecutor",
        "description": "Manages sub-interpreter pool for true multicore parallelization",
        "priority": "CRITICAL",
        "capabilities": [
            "sub_interpreter_management",
            "multicore_execution",
            "workload_distribution",
            "analyzer_integration"
        ]
    },
    "shared_memory_manager": {
        "class": "SharedMemoryManager", 
        "description": "Handles shared memory between sub-interpreters",
        "priority": "HIGH",
        "capabilities": [
            "memory_mapping",
            "cross_interpreter_sharing",
            "zero_copy_transfer",
            "memory_synchronization"
        ]
    },
    "zero_copy_buffer": {
        "class": "ZeroCopyBuffer",
        "description": "Provides zero-copy data transfer mechanisms",
        "priority": "HIGH",
        "capabilities": [
            "zero_copy_transfer",
            "buffer_management",
            "memory_views",
            "performance_optimization"
        ]
    },
    "thread_executor": {
        "class": "ThreadExecutor",
        "description": "Thread-based executor fallback for compatibility",
        "priority": "MEDIUM",
        "capabilities": [
            "thread_based_execution",
            "fallback_compatibility",
            "benchmark_discovery",
            "function_registration"
        ]
    }
}

def create_executor_suite(include_thread_executor: Optional[bool] = None) -> Union[
    Dict[str, Union[SubInterpreterExecutor, SharedMemoryManager, ZeroCopyBuffer]],
    Dict[str, Union[SubInterpreterExecutor, SharedMemoryManager, ZeroCopyBuffer, ThreadExecutor]]
]:
    """
    Create a complete executor suite with all components.
    
    Args:
        include_thread_executor: Whether to include ThreadExecutor as fallback.
                                If None, auto-detects based on environment.
    
    Returns:
        Dictionary containing initialized executor components.
        Includes ThreadExecutor when needed as fallback for compatibility.
    """
    # Base components always included
    suite = {
        "sub_interpreter_executor": SubInterpreterExecutor(),
        "shared_memory_manager": SharedMemoryManager(),
        "zero_copy_buffer": ZeroCopyBuffer("default_buffer", 1024 * 1024)  # 1MB default buffer
    }
    
    # Auto-detect if ThreadExecutor should be included
    if include_thread_executor is None:
        import sys
        import platform
        
        # Include ThreadExecutor as fallback if:
        # 1. Python version < 3.12 (no per-interpreter GIL)
        # 2. Running on Windows (sub-interpreter limitations)
        # 3. Sub-interpreter support not available
        include_thread_executor = (
            sys.version_info < (3, 12) or
            platform.system() == "Windows" or
            not hasattr(sys, '_subinterpreters')  # Check for sub-interpreter support
        )
    
    # Add ThreadExecutor if needed
    if include_thread_executor:
        suite["thread_executor"] = ThreadExecutor()
    
    return suite

def get_component_info(component_name: str) -> dict:
    """
    Get information about a specific executor component.
    
    Args:
        component_name: Name of the component
        
    Returns:
        Component information dictionary
    """
    return EXECUTOR_COMPONENTS.get(component_name, {})

def list_available_components() -> list:
    """
    List all available executor components.
    
    Returns:
        List of component names
    """
    return list(EXECUTOR_COMPONENTS.keys())