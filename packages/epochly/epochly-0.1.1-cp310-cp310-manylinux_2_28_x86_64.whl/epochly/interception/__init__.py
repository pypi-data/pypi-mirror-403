"""
Epochly Transparent Interception System

Implements automatic function routing to Level 3 executor via import-time wrapping.
Safe, deterministic, and compatible with Python 3.8-3.13.

Architecture:
1. Registry - Defines which library functions are safe for Level 3
2. Import Hook - Wraps functions at import time (not during execution)
3. InterceptionManager - Central routing for all intercepted calls
4. Telemetry - Tracks what gets optimized

Author: Epochly Development Team
Date: November 16, 2025
"""

from .registry import InterceptionRegistry, FunctionDescriptor
from .manager import InterceptionManager
from .telemetry import InterceptionTelemetry

__all__ = [
    'InterceptionRegistry',
    'FunctionDescriptor',
    'InterceptionManager',
    'InterceptionTelemetry',
]
