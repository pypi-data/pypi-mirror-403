"""
Epochly Memory Foundation - Workload Type Definitions

This module defines the WorkloadType enum used across the memory system.
It is deliberately dependency-free to prevent circular import issues.

Author: Epochly Memory Foundation Team
Created: 2025-06-09
Purpose: Shared workload type definitions
"""

from enum import Enum


class WorkloadType(str, Enum):
    """
    Logical classification of allocation workload patterns.
    
    This enum is used throughout the memory system to adapt allocation
    strategies based on detected workload characteristics.
    """
    UNKNOWN = "unknown"
    NUMPY_HEAVY = "numpy_heavy"
    PURE_PYTHON_LOOPS = "pure_python_loops"
    IO_BOUND = "io_bound"
    MEMORY_INTENSIVE = "memory_intensive"
    CPU_BOUND = "cpu_bound"
    MIXED = "mixed"


__all__ = ["WorkloadType"]