"""
Epochly Licensing Module

This module provides licensing infrastructure for the Epochly (Epochly) system.
It implements the licensing manager, validation, and CLI tools as specified in the
Epochly architecture specification.

Author: Epochly Development Team
"""

from .license_manager import LicenseManager
from .license_validator import LicenseValidator
from .dev_token_validator import (
    DevTokenValidator,
    DevTokenPayload,
    DevTokenValidationResult,
    DevTokenError,
    ValidationReason,
    is_dev_bypass_active,
    get_dev_token_features,
    get_dev_token_validator,
)

__all__ = [
    'LicenseManager',
    'LicenseValidator',
    'DevTokenValidator',
    'DevTokenPayload',
    'DevTokenValidationResult',
    'DevTokenError',
    'ValidationReason',
    'is_dev_bypass_active',
    'get_dev_token_features',
    'get_dev_token_validator',
]