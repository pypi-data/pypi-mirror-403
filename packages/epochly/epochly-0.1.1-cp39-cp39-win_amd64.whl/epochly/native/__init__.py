"""
Native Module (Phase 3.2)

Compiled helpers for performance-critical operations.

Modules:
- capability_detector: Fast hardware capability detection (<5ms)
"""

__all__ = ['capability_detector']

# Try to import compiled extensions, provide stub if unavailable
try:
    from . import capability_detector
    NATIVE_AVAILABLE = True
except ImportError:
    # Compiled extension not available
    # detection_async.py will fall back to pure Python
    capability_detector = None
    NATIVE_AVAILABLE = False
