"""
Epochly License Manager

Manages licensing for the Epochly (Epochly) system.
Provides license validation, activation, and management functionality.

Author: Epochly Development Team
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from ..utils.exceptions import EpochlyError
from .license_crypto import LicenseCrypto, LicenseCryptoError


class LicenseError(EpochlyError):
    """License-related error."""
    pass


class LicenseManager:
    """
    Manages Epochly licensing functionality.
    
    Provides license validation, activation, and status management
    according to the Epochly architecture specification.
    """
    
    def __init__(self, config_path: Optional[str] = None, crypto: Optional[LicenseCrypto] = None):
        """
        Initialize the license manager.

        Args:
            config_path: Optional path to license configuration
            crypto: Optional LicenseCrypto instance (for testing with custom keys)
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self._license_data: Optional[Dict[str, Any]] = None
        self._is_activated = False

        # Initialize crypto handler with embedded production public key
        # In production, this will use the real Epochly public key
        self._crypto = crypto or self._get_default_crypto()
        
    def validate_license(self) -> bool:
        """
        Validate the current license.
        
        Returns:
            True if license is valid, False otherwise
        """
        try:
            # Check for license file or environment variable
            license_key = self._get_license_key()
            if not license_key:
                self.logger.warning("No license key found")
                return False
                
            # Basic validation logic
            if self._validate_license_key(license_key):
                self._is_activated = True
                self.logger.info("License validated successfully")
                return True
            else:
                self.logger.error("License validation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"License validation error: {e}")
            return False
    
    def activate_license(self, license_key: str) -> bool:
        """
        Activate a license with the given key.
        
        Args:
            license_key: The license key to activate
            
        Returns:
            True if activation successful, False otherwise
        """
        try:
            if self._validate_license_key(license_key):
                self._store_license_key(license_key)
                self._is_activated = True
                self.logger.info("License activated successfully")
                return True
            else:
                self.logger.error("Invalid license key")
                return False
                
        except Exception as e:
            self.logger.error(f"License activation error: {e}")
            return False
    
    def deactivate_license(self) -> bool:
        """
        Deactivate the current license.
        
        Returns:
            True if deactivation successful, False otherwise
        """
        try:
            self._remove_license_key()
            self._is_activated = False
            self._license_data = None
            self.logger.info("License deactivated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"License deactivation error: {e}")
            return False
    
    def get_license_status(self) -> Dict[str, Any]:
        """
        Get current license status information.
        
        Returns:
            Dictionary containing license status details
        """
        return {
            'activated': self._is_activated,
            'valid': self.validate_license() if self._is_activated else False,
            'license_type': self._get_license_type(),
            'expiry_date': self._get_expiry_date(),
            'features': self._get_licensed_features()
        }
    
    def is_feature_licensed(self, feature: str) -> bool:
        """
        Check if a specific feature is licensed.
        
        Args:
            feature: The feature name to check
            
        Returns:
            True if feature is licensed, False otherwise
        """
        if not self._is_activated:
            return False
            
        licensed_features = self._get_licensed_features()
        return feature in licensed_features
    
    def _get_license_key(self) -> Optional[str]:
        """Get license key from environment or file."""
        # Check environment variable first
        license_key = os.getenv('EPOCHLY_LICENSE_KEY')
        if license_key:
            return license_key
            
        # Check license file
        license_file = Path.home() / '.epochly' / 'license.key'
        if license_file.exists():
            try:
                return license_file.read_text().strip()
            except Exception as e:
                self.logger.error(f"Error reading license file: {e}")
                
        return None
    
    def _get_default_crypto(self) -> Optional[LicenseCrypto]:
        """Get default crypto handler with production public key.

        Priority:
        1. EPOCHLY_LICENSE_PUBLIC_KEY_PEM env var (for overriding embedded key)
        2. Embedded public key in LicenseCrypto.EMBEDDED_PUBLIC_KEY_PEM
        3. None (fallback to basic validation - NOT recommended for production)
        """
        try:
            # Check for environment variable override first
            env_public_key = os.getenv('EPOCHLY_LICENSE_PUBLIC_KEY_PEM')

            if env_public_key:
                self.logger.debug("Using public key from EPOCHLY_LICENSE_PUBLIC_KEY_PEM env var")
                return LicenseCrypto(public_key_pem=env_public_key.encode())

            # Use embedded public key (P0-3: Now available in LicenseCrypto)
            # This allows offline validation without env var configuration
            if LicenseCrypto.EMBEDDED_PUBLIC_KEY_PEM is not None:
                self.logger.debug("Using embedded public key from LicenseCrypto")
                return LicenseCrypto()  # Uses embedded key automatically

            # If no key available, return None (insecure fallback)
            self.logger.warning(
                "No public key available - using basic format validation only. "
                "This is NOT recommended for production."
            )
            return None

        except Exception as e:
            self.logger.warning(f"Failed to initialize license crypto: {e}")
            return None

    def _parse_legacy_license_key(self, license_key: str) -> Optional[Dict[str, Any]]:
        """
        Parse and validate legacy (pre-crypto) license key format.

        Legacy format: Epochly-TYPE-PLAN-EXPIRY-CHECKSUM (exactly 5 parts)
        Example: Epochly-TEST-basic-9999999999-4

        Returns:
            Dict with license data if valid legacy format, None otherwise
        """
        parts = license_key.split('-')

        # Legacy format has exactly 5 parts
        if len(parts) != 5:
            return None

        prefix, lic_type, plan, expiry_str, check_str = parts

        if prefix != 'Epochly':
            return None

        # Validate expiry is numeric
        if not expiry_str.isdigit():
            return None

        # Validate checksum is numeric
        if not check_str.isdigit():
            return None

        expiry = int(expiry_str)

        # Accept legacy format - populate license data with conservative defaults
        return {
            'type': lic_type.lower(),  # Normalize to lowercase
            'plan': plan,
            'expiry': expiry,
            'legacy': True,
            # Conservative defaults for legacy licenses
            'features': [],  # No premium features
            'max_cores': 4,  # Limited cores for legacy
        }

    def _validate_license_key(self, license_key: str) -> bool:
        """
        Validate license key format and authenticity with cryptographic signatures.

        Uses Ed25519 signatures for tamper-proof validation.
        Falls back to basic format validation for backward compatibility with
        old license formats (pre-crypto), but ONLY for explicitly legacy-format keys.
        """
        if not license_key:
            return False

        license_key = license_key.strip()

        # Minimum key length: "Epochly-TYPE-FEAT-EXPIRY-CHECK" = ~30 chars
        if len(license_key) < 20:
            return False

        # Basic format validation
        if not license_key.startswith('Epochly-'):
            return False

        # First: Check for legacy format (explicit detection, not error-based)
        # Legacy format: exactly 5 parts with specific structure
        legacy_data = self._parse_legacy_license_key(license_key)
        if legacy_data is not None:
            self.logger.warning(
                "Legacy (pre-crypto) license format detected; "
                "accepting with conservative defaults (limited features/cores)."
            )
            self._license_data = legacy_data
            return True

        # Non-legacy key requires cryptographic validation
        if not self._crypto:
            # Fail closed when crypto not available for non-legacy keys
            self.logger.error(
                "Cryptographic license validation not available; "
                "refusing non-legacy license. "
                "Set EPOCHLY_LICENSE_PUBLIC_KEY_PEM for production."
            )
            return False

        # Crypto validation (must pass for non-legacy keys)
        try:
            is_valid, license_data = self._crypto.validate_license_key(license_key)

            if is_valid and license_data:
                # Store validated license data for later use
                self._license_data = license_data
                return True
            else:
                # Clear any stale data and reject
                self._license_data = None
                self.logger.error(f"Cryptographic validation failed: {license_data}")
                return False

        except LicenseCryptoError as e:
            # Clear any stale data and reject
            self._license_data = None
            self.logger.error(f"License crypto error: {e}")
            return False
    
    def _store_license_key(self, license_key: str) -> None:
        """Store license key to file."""
        license_dir = Path.home() / '.epochly'
        license_dir.mkdir(exist_ok=True)
        
        license_file = license_dir / 'license.key'
        license_file.write_text(license_key)
        license_file.chmod(0o600)  # Restrict permissions
    
    def _remove_license_key(self) -> None:
        """Remove stored license key."""
        license_file = Path.home() / '.epochly' / 'license.key'
        if license_file.exists():
            license_file.unlink()
    
    def _get_license_type(self) -> str:
        """Get the type of license from validated data."""
        if not self._is_activated:
            return 'none'

        if self._license_data and 'type' in self._license_data:
            return self._license_data['type']

        # Fallback for non-crypto validated licenses
        return 'standard'

    def _get_expiry_date(self) -> Optional[str]:
        """Get license expiry date from validated data."""
        if not self._is_activated:
            return None

        if self._license_data and 'expiry' in self._license_data:
            # Convert Unix timestamp to ISO format
            expiry_timestamp = self._license_data['expiry']
            expiry_dt = datetime.utcfromtimestamp(expiry_timestamp)
            return expiry_dt.isoformat()

        return None

    def _get_licensed_features(self) -> list:
        """Get list of licensed features from validated data."""
        if not self._is_activated:
            return []

        if self._license_data and 'features' in self._license_data:
            return self._license_data['features']

        # Fallback for non-crypto validated licenses
        return ['optimization', 'monitoring', 'deployment']

    def get_max_cores(self) -> Optional[int]:
        """
        Get maximum allowed cores from license.

        Returns:
            Maximum cores allowed, or None if unlimited/not activated
        """
        if not self._is_activated:
            return None

        if self._license_data and 'max_cores' in self._license_data:
            return self._license_data['max_cores']

        return None