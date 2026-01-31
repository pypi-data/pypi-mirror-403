"""
Epochly License Validator

Provides license validation functionality for the Epochly (Epochly) system.
Implements validation logic, security checks, and license verification.

Author: Epochly Development Team
"""

import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ..utils.exceptions import EpochlyError


class ValidationError(EpochlyError):
    """License validation error."""
    pass


class LicenseValidator:
    """
    Validates Epochly licenses and ensures security compliance.
    
    Provides comprehensive license validation including format checking,
    signature verification, and expiry validation.
    """
    
    def __init__(self):
        """Initialize the license validator."""
        self.logger = logging.getLogger(__name__)
        self._validation_cache: Dict[str, Dict[str, Any]] = {}
    
    def validate_format(self, license_key: str) -> bool:
        """
        Validate license key format.
        
        Args:
            license_key: The license key to validate
            
        Returns:
            True if format is valid, False otherwise
        """
        if not license_key:
            return False
            
        # Check basic format requirements
        if not license_key.startswith('Epochly-'):
            self.logger.error("License key must start with 'Epochly-'")
            return False
            
        # Remove prefix for further validation
        key_body = license_key[4:]
        
        # Check minimum length
        if len(key_body) < 20:
            self.logger.error("License key too short")
            return False
            
        # Check for valid characters (alphanumeric and hyphens)
        if not all(c.isalnum() or c == '-' for c in key_body):
            self.logger.error("License key contains invalid characters")
            return False
            
        return True
    
    def validate_signature(self, license_key: str) -> bool:
        """
        Validate license key signature.
        
        Args:
            license_key: The license key to validate
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Extract components from license key
            components = self._parse_license_key(license_key)
            if not components:
                return False
                
            # Validate checksum
            expected_checksum = self._calculate_checksum(components)
            actual_checksum = components.get('checksum', '')
            
            if expected_checksum != actual_checksum:
                self.logger.error("License signature validation failed")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Signature validation error: {e}")
            return False
    
    def validate_expiry(self, license_key: str) -> bool:
        """
        Validate license expiry date.
        
        Args:
            license_key: The license key to validate
            
        Returns:
            True if license is not expired, False otherwise
        """
        try:
            components = self._parse_license_key(license_key)
            if not components:
                return False
                
            expiry_str = components.get('expiry')
            if not expiry_str:
                # No expiry date means perpetual license
                return True
                
            expiry_date = datetime.strptime(expiry_str, '%Y%m%d')
            current_date = datetime.now()
            
            if current_date > expiry_date:
                self.logger.error(f"License expired on {expiry_date.strftime('%Y-%m-%d')}")
                return False
                
            # Warn if expiring soon (within 30 days)
            days_until_expiry = (expiry_date - current_date).days
            if days_until_expiry <= 30:
                self.logger.warning(f"License expires in {days_until_expiry} days")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Expiry validation error: {e}")
            return False
    
    def validate_features(self, license_key: str, required_features: list) -> bool:
        """
        Validate that license includes required features.
        
        Args:
            license_key: The license key to validate
            required_features: List of required feature names
            
        Returns:
            True if all features are licensed, False otherwise
        """
        try:
            components = self._parse_license_key(license_key)
            if not components:
                return False
                
            licensed_features = components.get('features', [])
            
            for feature in required_features:
                if feature not in licensed_features:
                    self.logger.error(f"Feature '{feature}' not licensed")
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Feature validation error: {e}")
            return False
    
    def get_license_info(self, license_key: str) -> Optional[Dict[str, Any]]:
        """
        Extract license information from key.
        
        Args:
            license_key: The license key to parse
            
        Returns:
            Dictionary containing license information or None if invalid
        """
        try:
            components = self._parse_license_key(license_key)
            if not components:
                return None
                
            return {
                'license_type': components.get('type', 'standard'),
                'expiry_date': components.get('expiry'),
                'features': components.get('features', []),
                'user_limit': components.get('user_limit', 1),
                'issued_date': components.get('issued'),
                'version': components.get('version', '1.0')
            }
            
        except Exception as e:
            self.logger.error(f"License info extraction error: {e}")
            return None
    
    def _parse_license_key(self, license_key: str) -> Optional[Dict[str, Any]]:
        """Parse license key into components."""
        if not self.validate_format(license_key):
            return None
            
        # Check cache first
        if license_key in self._validation_cache:
            return self._validation_cache[license_key]
            
        try:
            # Remove prefix "Epochly-" (8 characters)
            key_body = license_key[8:]
            
            # For this implementation, we'll use a simple format:
            # Epochly-TYPE-FEATURES-EXPIRY-CHECKSUM
            parts = key_body.split('-')
            
            if len(parts) < 4:
                return None
                
            components = {
                'type': parts[0] if parts[0] else 'standard',
                'features': self._decode_features(parts[1]) if parts[1] else [],
                'expiry': parts[2] if parts[2] and parts[2] != 'NEVER' else None,
                'checksum': parts[3] if len(parts) > 3 else '',
                'issued': datetime.now().strftime('%Y%m%d'),
                'version': '1.0',
                'user_limit': 1
            }
            
            # Cache the result
            self._validation_cache[license_key] = components
            return components
            
        except Exception as e:
            self.logger.error(f"License parsing error: {e}")
            return None
    
    def _decode_features(self, features_str: str) -> list:
        """Decode features string into list."""
        if not features_str or features_str == 'ALL':
            return ['optimization', 'monitoring', 'deployment', 'analytics']
            
        # Simple encoding: first letter of each feature
        feature_map = {
            'O': 'optimization',
            'M': 'monitoring', 
            'D': 'deployment',
            'A': 'analytics'
        }
        
        features = []
        for char in features_str.upper():
            if char in feature_map:
                features.append(feature_map[char])
                
        return features
    
    def _calculate_checksum(self, components: Dict[str, Any]) -> str:
        """Calculate checksum for license components."""
        # Create a string from key components
        checksum_data = f"{components.get('type', '')}{components.get('features', '')}{components.get('expiry', '')}"
        
        # Calculate SHA256 hash and take first 8 characters
        hash_obj = hashlib.sha256(checksum_data.encode())
        return hash_obj.hexdigest()[:8].upper()
    
    def validate_license(self, license_key: str) -> Dict[str, Any]:
        """Perform comprehensive license validation."""
        result = {
            'valid': False,
            'license_key': license_key,
            'errors': []
        }
        
        try:
            # Format validation
            if not self.validate_format(license_key):
                result['errors'].append('Invalid license format')
                return result
            
            # Signature validation
            if not self.validate_signature(license_key):
                result['errors'].append('Invalid license signature')
                return result
            
            # Expiry validation
            if not self.validate_expiry(license_key):
                result['errors'].append('License expired')
                return result
            
            # All validations passed
            result['valid'] = True
            
            # Add license info
            license_info = self.get_license_info(license_key)
            if license_info:
                result.update(license_info)
            
            return result
            
        except Exception as e:
            result['errors'].append(f'Validation error: {e}')
            return result
    
    def validate_with_time_check(self, license_key: str) -> Dict[str, Any]:
        """Validate license with time manipulation checking."""
        try:
            from .time_protection import get_time_detector
            time_detector = get_time_detector()
            
            # Check time consistency first
            time_result = time_detector.check_time_consistency()
            
            # Validate license
            license_result = self.validate_license(license_key)
            
            # Combine results
            result = license_result.copy()
            result['time_valid'] = time_result['consistent']
            result['time_sources'] = time_result.get('sources', {})
            
            return result
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Time validation failed: {e}',
                'time_valid': False
            }