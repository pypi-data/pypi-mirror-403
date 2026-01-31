"""
API-based Trial System for Epochly

Replaces direct AWS/DynamoDB access with API calls to api.epochly.com.
This eliminates AWS credential requirements for users.

User-side functionality MUST go through api.epochly.com - no exceptions.
"""

import os
import json
import logging
import hashlib
import platform
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Lightweight imports only - NO boto3
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not available - trial system disabled")


class APITrialSystem:
    """
    API-based trial system that eliminates AWS dependencies for users.

    All trial operations go through api.epochly.com instead of direct DynamoDB.
    """

    def __init__(self, api_endpoint: Optional[str] = None, timeout: int = 10):
        """
        Initialize API trial system.

        Args:
            api_endpoint: API endpoint (defaults to api.epochly.com)
            timeout: Request timeout in seconds
        """
        self.api_endpoint = api_endpoint or os.environ.get('EPOCHLY_API_ENDPOINT', 'https://api.epochly.com')
        self.timeout = timeout
        self.available = REQUESTS_AVAILABLE

        if not self.available:
            logger.warning("Trial system disabled - requests library not available")

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Epochly-Client/1.0.0'
        }

        # Add node authentication if available
        try:
            from epochly.compatibility.secure_node_auth import get_secure_auth
            node_auth = get_secure_auth()
            if node_auth:
                auth_data = node_auth.generate_auth_headers({})
                headers.update(auth_data)
        except ImportError:
            logger.debug("Secure node auth not available")
        except Exception as e:
            logger.debug(f"Error getting node auth headers: {e}")

        return headers

    def get_machine_fingerprint(self) -> str:
        """Generate machine fingerprint for trial registration."""
        try:
            from epochly.compatibility.secure_node_auth import MachineFingerprint
            return MachineFingerprint.generate_complete_fingerprint()
        except ImportError:
            # Fallback fingerprint generation
            system_info = f"{platform.system()}:{platform.machine()}:{platform.processor()}"
            return hashlib.sha256(system_info.encode()).hexdigest()

    def activate_trial(self, email: str, machine_fingerprint: Optional[str] = None) -> Dict[str, Any]:
        """
        Activate trial via API.

        Args:
            email: User email address
            machine_fingerprint: Machine fingerprint (auto-generated if None)

        Returns:
            Activation result dictionary
        """
        if not self.available:
            return {'success': False, 'error': 'API not available'}

        if not machine_fingerprint:
            machine_fingerprint = self.get_machine_fingerprint()

        data = {
            'email': email,
            'machine_fingerprint': machine_fingerprint,
            'platform': platform.system(),
            'python_version': f"{platform.python_version()}"
        }

        try:
            response = requests.post(
                f"{self.api_endpoint}/trial/activate",
                json=data,
                headers=self._get_auth_headers(),
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f'API error: {response.status_code}',
                    'message': response.text
                }

        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Network error: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {e}'}

    def validate_license(self, license_key: str) -> Dict[str, Any]:
        """
        Validate license via API.

        Args:
            license_key: License key to validate

        Returns:
            Validation result dictionary
        """
        if not self.available:
            return {'valid': False, 'reason': 'api_unavailable'}

        data = {
            'license_key': license_key,
            'machine_fingerprint': self.get_machine_fingerprint()
        }

        try:
            response = requests.post(
                f"{self.api_endpoint}/validate-license",
                json=data,
                headers=self._get_auth_headers(),
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {'valid': False, 'reason': f'api_error_{response.status_code}'}

        except Exception as e:
            logger.debug(f"License validation error: {e}")
            return {'valid': False, 'reason': 'network_error'}

    def check_trial_status(self, machine_fingerprint: Optional[str] = None) -> Dict[str, Any]:
        """
        Check trial status via API.

        Args:
            machine_fingerprint: Machine fingerprint (auto-generated if None)

        Returns:
            Trial status dictionary
        """
        if not self.available:
            return {'has_trial': False, 'error': 'api_unavailable'}

        if not machine_fingerprint:
            machine_fingerprint = self.get_machine_fingerprint()

        try:
            response = requests.get(
                f"{self.api_endpoint}/trial/status",
                params={'machine_fingerprint': machine_fingerprint},
                headers=self._get_auth_headers(),
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {'has_trial': False, 'error': f'api_error_{response.status_code}'}

        except Exception as e:
            logger.debug(f"Trial status check error: {e}")
            return {'has_trial': False, 'error': 'network_error'}


class TrialPolicy:
    """
    API-based trial policy enforcement.

    Replaces direct DynamoDB access with API calls for user-side operations.
    """

    def __init__(self, api_endpoint: Optional[str] = None):
        """Initialize trial policy with API backend."""
        self.api_trial_system = APITrialSystem(api_endpoint)

    def can_use_email(self, email: str) -> bool:
        """Check if email can be used for trial via API."""
        if not self.api_trial_system.available:
            return True  # Graceful fallback - allow trial attempts

        try:
            response = requests.get(
                f"{self.api_trial_system.api_endpoint}/trial/check-email",
                params={'email': email},
                headers=self.api_trial_system._get_auth_headers(),
                timeout=self.api_trial_system.timeout
            )

            if response.status_code == 200:
                return response.json().get('available', True)
            else:
                return True  # Graceful fallback

        except Exception as e:
            logger.debug(f"Email availability check failed: {e}")
            return True  # Graceful fallback

    def can_use_machine(self, machine_fingerprint: str) -> bool:
        """Check if machine can use trial via API."""
        if not self.api_trial_system.available:
            return True  # Graceful fallback

        try:
            response = requests.get(
                f"{self.api_trial_system.api_endpoint}/trial/check-machine",
                params={'machine_fingerprint': machine_fingerprint},
                headers=self.api_trial_system._get_auth_headers(),
                timeout=self.api_trial_system.timeout
            )

            if response.status_code == 200:
                return response.json().get('available', True)
            else:
                return True  # Graceful fallback

        except Exception as e:
            logger.debug(f"Machine availability check failed: {e}")
            return True  # Graceful fallback

    def check_eligibility(self, email: str, machine_fingerprint: str) -> Dict[str, Any]:
        """Check trial eligibility via API."""
        if not self.api_trial_system.available:
            return {
                'eligible': True,
                'reason': 'api_unavailable'
            }

        data = {
            'email': email,
            'machine_fingerprint': machine_fingerprint
        }

        try:
            response = requests.post(
                f"{self.api_trial_system.api_endpoint}/trial/check-eligibility",
                json=data,
                headers=self.api_trial_system._get_auth_headers(),
                timeout=self.api_trial_system.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'eligible': True,  # Graceful fallback
                    'reason': f'api_error_{response.status_code}'
                }

        except Exception as e:
            logger.debug(f"Eligibility check failed: {e}")
            return {
                'eligible': True,  # Graceful fallback
                'reason': 'network_error'
            }

    def mark_email_used(self, email: str, machine_fingerprint: str):
        """Mark email as used via API (called after successful activation)."""
        # This is automatically handled by the trial activation API
        # No separate call needed
        pass

    def mark_machine_used(self, machine_fingerprint: str, email: str):
        """Mark machine as used via API (called after successful activation)."""
        # This is automatically handled by the trial activation API
        # No separate call needed
        pass


# Factory function for backward compatibility
def create_trial_system() -> APITrialSystem:
    """Create API-based trial system instance."""
    return APITrialSystem()


def create_trial_policy() -> TrialPolicy:
    """Create API-based trial policy instance."""
    return TrialPolicy()