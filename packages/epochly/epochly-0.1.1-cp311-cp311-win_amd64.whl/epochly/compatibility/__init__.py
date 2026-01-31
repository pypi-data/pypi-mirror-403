"""
Epochly Compatibility Package

Compatibility detection and handling for various execution environments:
- Module compatibility tracking (registry.py)
- Subprocess safety detection (subprocess_safety.py) - NEW
- Platform-specific safety checks (platform_safety.py) - NEW
- Cloud sync and local storage
- API-based compatibility backend (api_backend.py)

Author: Epochly Development Team
"""

# Existing compatibility system
from .registry import (
    CompatibilityRegistry,
    get_global_registry,
    CompatibilityLevel,
    CompatibilityResult,
    ModuleCompatibilityInfo,
)

# API-based compatibility backend (replaces direct DynamoDB access)
from .api_backend import (
    APICompatibilityBackend,
    create_compatibility_backend,
)

# NEW: Subprocess and platform safety
from .subprocess_safety import (
    is_nested_subprocess,
    can_spawn_processes_safely,
    get_max_safe_level,
    SubprocessContext,
    detect_subprocess_context,
)

from .platform_safety import (
    is_containerized,
    get_shm_size,
    is_safe_to_fork,
    is_frozen_executable,
    has_main_guard,
    check_process_limits,
    has_active_multiprocessing_pool,
    detect_platform_restrictions,
    PlatformRestrictions,
)

__all__ = [
    # Existing registry system
    'CompatibilityRegistry',
    'get_global_registry',
    'CompatibilityLevel',
    'CompatibilityResult',
    'ModuleCompatibilityInfo',
    # API-based compatibility backend
    'APICompatibilityBackend',
    'create_compatibility_backend',
    # Subprocess safety (NEW)
    'is_nested_subprocess',
    'can_spawn_processes_safely',
    'get_max_safe_level',
    'SubprocessContext',
    'detect_subprocess_context',
    # Platform safety (NEW)
    'is_containerized',
    'get_shm_size',
    'is_safe_to_fork',
    'is_frozen_executable',
    'has_main_guard',
    'check_process_limits',
    'has_active_multiprocessing_pool',
    'detect_platform_restrictions',
    'PlatformRestrictions',
]
