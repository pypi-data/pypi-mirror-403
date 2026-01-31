"""
Epochly Developer Token Validation Module

Provides cryptographically secure developer token validation to replace
insecure environment variable bypasses (EPOCHLY_DISABLE_LICENSE_ENFORCEMENT).

Architecture:
- Uses existing ED25519 cryptographic infrastructure from license_crypto.py
- Tokens stored at ~/.epochly/dev-token.json or .epochly/dev-token.json
- Defense-in-depth: Requires EPOCHLY_TEST_MODE=1 alongside valid token
- Optional online revocation checking via api.epochly.com

Token Structure (JWT-like):
{
    "payload": {
        "sub": "dev@company.com",     # Developer email
        "iss": "api.epochly.com",      # Issuer
        "iat": 1703980800,             # Issued at (unix timestamp)
        "exp": 1706659200,             # Expiration (unix timestamp)
        "jti": "unique-token-id",      # JWT ID for revocation
        "tier": "developer",           # developer, enterprise-dev, ci-cd
        "features": ["level_0", ...],  # Enabled features
        "env": "development"           # development, testing, ci
    },
    "signature": "base64-ed25519-signature"
}

Author: Epochly Development Team
Date: December 2025
"""

import base64
import json
import logging
import os
import stat
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from epochly.licensing.license_crypto import LicenseCrypto, LicenseCryptoError

logger = logging.getLogger(__name__)


class ValidationReason(Enum):
    """Structured validation failure reasons for debugging"""
    VALID = "valid"
    NOT_IN_TEST_MODE = "not_in_test_mode"
    TOKEN_NOT_FOUND = "token_not_found"
    TOKEN_INVALID_JSON = "token_invalid_json"
    TOKEN_INVALID_STRUCTURE = "token_invalid_structure"
    TOKEN_FILE_PERMISSIONS_UNSAFE = "token_file_permissions_unsafe"
    TOKEN_FILE_TOO_LARGE = "token_file_too_large"
    SIGNATURE_INVALID = "signature_invalid"
    PAYLOAD_INVALID = "payload_invalid"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_NOT_YET_VALID = "token_not_yet_valid"
    TOKEN_LIFETIME_EXCEEDED = "token_lifetime_exceeded"
    TOKEN_REVOKED = "token_revoked"
    ISSUER_INVALID = "issuer_invalid"
    ENVIRONMENT_INVALID = "environment_invalid"


class DevTokenError(Exception):
    """Raised when dev token validation fails"""
    pass


@dataclass
class DevTokenPayload:
    """Parsed and validated developer token payload"""
    subject: str                    # Developer email
    issuer: str                     # Always "api.epochly.com"
    issued_at: int                  # Unix timestamp
    expires_at: int                 # Unix timestamp
    token_id: str                   # Unique JTI for revocation
    tier: str                       # developer, enterprise-dev, ci-cd
    features: List[str]            # Enabled features
    environment: str               # development, testing, ci
    hardware_fingerprint: Optional[str] = None  # Optional for dev tokens


@dataclass
class DevTokenValidationResult:
    """Result of dev token validation"""
    valid: bool
    payload: Optional[DevTokenPayload] = None
    error: Optional[str] = None
    reason: ValidationReason = ValidationReason.VALID
    revoked: bool = False
    expired: bool = False

    def __bool__(self) -> bool:
        return self.valid


class DevTokenValidator:
    """
    Validates cryptographically signed developer tokens.

    This replaces the insecure EPOCHLY_DISABLE_LICENSE_ENFORCEMENT env var
    with a secure, auditable token-based system.

    Security Layers:
    1. ED25519 signature verification (forgery-proof)
    2. Token expiration check (time-bound access)
    3. EPOCHLY_TEST_MODE environment check (prevents production misuse)
    4. Optional JTI revocation check (server-side revocation)
    """

    # Token file locations (checked in order)
    TOKEN_LOCATIONS = [
        Path.home() / '.epochly' / 'dev-token.json',  # User-level (preferred)
        Path('.epochly') / 'dev-token.json',           # Project-level
    ]

    # Required payload fields
    REQUIRED_FIELDS = ['sub', 'iss', 'iat', 'exp', 'jti', 'tier', 'features', 'env']

    # Valid token tiers
    VALID_TIERS = ['developer', 'enterprise-dev', 'ci-cd']

    # Valid environments
    VALID_ENVIRONMENTS = ['development', 'testing', 'ci']

    # Required issuer
    REQUIRED_ISSUER = 'api.epochly.com'

    # Clock skew tolerance (5 minutes)
    CLOCK_SKEW_TOLERANCE = 300

    # Maximum token file size (64 KB - prevents memory abuse)
    MAX_TOKEN_FILE_SIZE = 65536

    # Maximum token lifetime (90 days in seconds)
    MAX_TOKEN_LIFETIME = 90 * 24 * 60 * 60

    # Timestamp sanity check (reject exp > year 2100 to catch ms timestamps)
    MAX_TIMESTAMP = 4102444800  # 2100-01-01

    # Domain separation prefix for signature verification
    SIGNATURE_DOMAIN = b"EPOCHLY_DEV_TOKEN_V1:"

    def __init__(
        self,
        crypto: Optional[LicenseCrypto] = None,
        revocation_endpoint: Optional[str] = None,
        require_test_mode: bool = True
    ):
        """
        Initialize developer token validator.

        Args:
            crypto: LicenseCrypto instance (uses default if not provided)
            revocation_endpoint: URL for JTI revocation checking (optional)
            require_test_mode: Require EPOCHLY_TEST_MODE=1 (default True)
        """
        self._crypto = crypto or LicenseCrypto()
        self._revocation_endpoint = revocation_endpoint or 'https://api.epochly.com/v1/revocation'
        self._require_test_mode = require_test_mode
        self._cached_token: Optional[Dict] = None
        self._cached_result: Optional[DevTokenValidationResult] = None
        self._cache_timestamp: float = 0.0

        # Cache TTL: 5 minutes
        self._cache_ttl = 300.0

    def find_token_file(self) -> Optional[Path]:
        """
        Find the dev token file in standard locations.

        Returns:
            Path to token file if found, None otherwise
        """
        for path in self.TOKEN_LOCATIONS:
            if path.exists() and path.is_file():
                logger.debug(f"Found dev token at: {path}")
                return path
        return None

    def _check_file_permissions(self, path: Path) -> Tuple[bool, Optional[str]]:
        """
        Verify token file has safe permissions (POSIX only).

        Args:
            path: Path to check

        Returns:
            Tuple of (is_safe, error_message)
        """
        if os.name != 'posix':
            # Skip permission check on non-POSIX systems
            return True, None

        try:
            # Resolve symlinks and check final target
            resolved = path.resolve()

            # Get file stats
            file_stat = resolved.stat()

            # Check it's a regular file
            if not stat.S_ISREG(file_stat.st_mode):
                return False, f"Token path is not a regular file: {resolved}"

            # Check file is owned by current user (or root)
            current_uid = os.getuid()
            if file_stat.st_uid != current_uid and file_stat.st_uid != 0:
                return False, f"Token file not owned by current user: {resolved}"

            # Check file is not group-writable or world-writable
            unsafe_bits = stat.S_IWGRP | stat.S_IWOTH
            if file_stat.st_mode & unsafe_bits:
                return False, f"Token file has unsafe permissions (group/world writable): {resolved}"

            return True, None

        except OSError as e:
            return False, f"Failed to check file permissions: {e}"

    def _check_file_size(self, path: Path) -> Tuple[bool, Optional[str]]:
        """
        Verify token file is not too large.

        Args:
            path: Path to check

        Returns:
            Tuple of (is_safe, error_message)
        """
        try:
            file_size = path.stat().st_size
            if file_size > self.MAX_TOKEN_FILE_SIZE:
                return False, f"Token file too large ({file_size} bytes, max {self.MAX_TOKEN_FILE_SIZE})"
            return True, None
        except OSError as e:
            return False, f"Failed to check file size: {e}"

    def load_token_from_file(self, path: Optional[Path] = None) -> Tuple[Optional[Dict], ValidationReason]:
        """
        Load and parse token from file with security checks.

        Args:
            path: Specific path to load from (uses standard locations if not provided)

        Returns:
            Tuple of (token_data or None, validation_reason)
        """
        token_path = path or self.find_token_file()
        if not token_path:
            logger.debug("No dev token file found")
            return None, ValidationReason.TOKEN_NOT_FOUND

        # If a specific path was provided, verify it exists
        if path is not None and not path.exists():
            logger.debug(f"Specified token file does not exist: {path}")
            return None, ValidationReason.TOKEN_NOT_FOUND

        # Security: Check file size first (before reading)
        size_ok, size_error = self._check_file_size(token_path)
        if not size_ok:
            logger.warning(size_error)
            return None, ValidationReason.TOKEN_FILE_TOO_LARGE

        # Security: Check file permissions (POSIX only)
        perms_ok, perms_error = self._check_file_permissions(token_path)
        if not perms_ok:
            logger.warning(perms_error)
            return None, ValidationReason.TOKEN_FILE_PERMISSIONS_UNSAFE

        try:
            with open(token_path, 'r', encoding='utf-8') as f:
                token_data = json.load(f)

            # Basic structure validation
            if not isinstance(token_data, dict):
                logger.warning(f"Invalid token structure in {token_path}")
                return None, ValidationReason.TOKEN_INVALID_STRUCTURE

            if 'payload' not in token_data or 'signature' not in token_data:
                logger.warning(f"Token missing required fields in {token_path}")
                return None, ValidationReason.TOKEN_INVALID_STRUCTURE

            return token_data, ValidationReason.VALID

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse token file {token_path}: {e}")
            return None, ValidationReason.TOKEN_INVALID_JSON
        except IOError as e:
            logger.warning(f"Failed to read token file {token_path}: {e}")
            return None, ValidationReason.TOKEN_NOT_FOUND

    def validate_signature(self, token_data: Dict) -> bool:
        """
        Validate the ED25519 signature on the token payload.

        Args:
            token_data: Token dict with 'payload' and 'signature'

        Returns:
            True if signature is valid
        """
        try:
            payload = token_data.get('payload', {})
            signature_b64 = token_data.get('signature', '')

            if not payload or not signature_b64:
                return False

            # Use LicenseCrypto for signature validation
            return self._crypto.validate_license_signature(payload, signature_b64)

        except Exception as e:
            logger.debug(f"Signature validation failed: {e}")
            return False

    def validate_payload(self, payload: Dict) -> Tuple[bool, Optional[str], ValidationReason]:
        """
        Validate token payload structure and fields.

        Args:
            payload: Token payload dict

        Returns:
            Tuple of (is_valid, error_message, reason)
        """
        # Check required fields
        missing_fields = [f for f in self.REQUIRED_FIELDS if f not in payload]
        if missing_fields:
            return False, f"Missing required fields: {missing_fields}", ValidationReason.PAYLOAD_INVALID

        # Validate issuer (must be exact match)
        if payload.get('iss') != self.REQUIRED_ISSUER:
            return False, f"Invalid issuer: {payload.get('iss')}", ValidationReason.ISSUER_INVALID

        # Validate tier
        tier = payload.get('tier')
        if tier not in self.VALID_TIERS:
            return False, f"Invalid tier: {tier}", ValidationReason.PAYLOAD_INVALID

        # Validate environment
        env = payload.get('env')
        if env not in self.VALID_ENVIRONMENTS:
            return False, f"Invalid environment: {env}", ValidationReason.ENVIRONMENT_INVALID

        # Validate features is a list
        features = payload.get('features')
        if not isinstance(features, list):
            return False, "features must be a list", ValidationReason.PAYLOAD_INVALID

        # Validate timestamps are integers
        for field in ['iat', 'exp']:
            val = payload.get(field)
            if not isinstance(val, int):
                return False, f"{field} must be an integer timestamp", ValidationReason.PAYLOAD_INVALID

        # Security: Timestamp sanity checks
        iat = payload['iat']
        exp = payload['exp']
        current_time = int(time.time())

        # Reject if exp is too large (likely milliseconds instead of seconds)
        if exp > self.MAX_TIMESTAMP:
            return False, f"exp timestamp too large (max {self.MAX_TIMESTAMP})", ValidationReason.PAYLOAD_INVALID

        # Reject if iat is in the future (beyond clock skew)
        if iat > current_time + self.CLOCK_SKEW_TOLERANCE:
            return False, "Token issued in the future (iat > now + skew)", ValidationReason.TOKEN_NOT_YET_VALID

        # Enforce maximum token lifetime
        token_lifetime = exp - iat
        if token_lifetime > self.MAX_TOKEN_LIFETIME:
            return False, f"Token lifetime too long ({token_lifetime}s, max {self.MAX_TOKEN_LIFETIME}s)", ValidationReason.TOKEN_LIFETIME_EXCEEDED

        # Reject negative lifetime (exp < iat)
        if token_lifetime < 0:
            return False, "Token expiration before issued time", ValidationReason.PAYLOAD_INVALID

        return True, None, ValidationReason.VALID

    def check_expiration(self, payload: Dict) -> Tuple[bool, bool]:
        """
        Check if token is expired.

        Args:
            payload: Token payload dict

        Returns:
            Tuple of (is_valid, is_expired)
        """
        current_time = int(time.time())
        exp = payload.get('exp', 0)

        # Allow some clock skew
        is_expired = current_time > (exp + self.CLOCK_SKEW_TOLERANCE)

        return not is_expired, is_expired

    def check_revocation(self, jti: str) -> bool:
        """
        Check if token is revoked via API.

        This is a best-effort check - fails open if network unavailable.

        Args:
            jti: Token ID to check

        Returns:
            True if token is revoked, False otherwise (or on network error)
        """
        try:
            import requests

            url = f"{self._revocation_endpoint}/{jti}"
            response = requests.get(url, timeout=5)

            # 200 = not revoked, 404 = revoked
            if response.status_code == 404:
                logger.warning(f"Token {jti[:8]}... is revoked")
                return True

            return False

        except ImportError:
            logger.debug("requests library not available, skipping revocation check")
            return False
        except Exception as e:
            logger.debug(f"Revocation check failed (failing open): {e}")
            return False

    def check_test_mode(self) -> bool:
        """
        Check if EPOCHLY_TEST_MODE environment variable is set.

        This is a defense-in-depth measure to prevent accidental
        production use of developer tokens.

        Returns:
            True if test mode is enabled or not required
        """
        if not self._require_test_mode:
            return True

        return os.environ.get('EPOCHLY_TEST_MODE') == '1'

    def validate(
        self,
        token_data: Optional[Dict] = None,
        skip_revocation: bool = False
    ) -> DevTokenValidationResult:
        """
        Perform full token validation.

        Args:
            token_data: Token dict (loads from file if not provided)
            skip_revocation: Skip online revocation check

        Returns:
            DevTokenValidationResult with validation status
        """
        # Check cache first
        if self._use_cache(token_data):
            return self._cached_result

        # Check test mode requirement FIRST (before even loading token)
        # This reduces exposure when test mode isn't enabled
        if not self.check_test_mode():
            return DevTokenValidationResult(
                valid=False,
                error="EPOCHLY_TEST_MODE=1 required for dev token bypass",
                reason=ValidationReason.NOT_IN_TEST_MODE
            )

        # Load token if not provided
        if token_data is None:
            token_data, load_reason = self.load_token_from_file()
            if token_data is None:
                return DevTokenValidationResult(
                    valid=False,
                    error=f"Failed to load token: {load_reason.value}",
                    reason=load_reason
                )

        # Validate signature
        if not self.validate_signature(token_data):
            return DevTokenValidationResult(
                valid=False,
                error="Invalid token signature",
                reason=ValidationReason.SIGNATURE_INVALID
            )

        payload = token_data.get('payload', {})

        # Validate payload structure
        is_valid, error, reason = self.validate_payload(payload)
        if not is_valid:
            return DevTokenValidationResult(
                valid=False,
                error=error,
                reason=reason
            )

        # Check expiration
        not_expired, is_expired = self.check_expiration(payload)
        if not not_expired:
            return DevTokenValidationResult(
                valid=False,
                error="Token expired",
                reason=ValidationReason.TOKEN_EXPIRED,
                expired=True
            )

        # Check revocation (optional)
        if not skip_revocation:
            jti = payload.get('jti', '')
            if jti:
                revoked = self.check_revocation(jti)
                if revoked:
                    return DevTokenValidationResult(
                        valid=False,
                        error="Token has been revoked",
                        reason=ValidationReason.TOKEN_REVOKED,
                        revoked=True
                    )

        # Build validated payload
        validated_payload = DevTokenPayload(
            subject=payload['sub'],
            issuer=payload['iss'],
            issued_at=payload['iat'],
            expires_at=payload['exp'],
            token_id=payload['jti'],
            tier=payload['tier'],
            features=payload['features'],
            environment=payload['env'],
            hardware_fingerprint=payload.get('hwfp')
        )

        result = DevTokenValidationResult(
            valid=True,
            payload=validated_payload,
            reason=ValidationReason.VALID
        )

        # Update cache
        self._update_cache(token_data, result)

        # Log success without sensitive data (only truncated JTI)
        jti_short = payload['jti'][:8] if payload.get('jti') else 'unknown'
        logger.info(f"Dev token validated: tier={validated_payload.tier}, jti={jti_short}...")
        return result

    def _use_cache(self, token_data: Optional[Dict]) -> bool:
        """Check if cached result is still valid"""
        if self._cached_result is None:
            return False

        if time.time() - self._cache_timestamp > self._cache_ttl:
            return False

        # If specific token provided, compare to cached
        if token_data is not None and token_data != self._cached_token:
            return False

        return True

    def _update_cache(self, token_data: Dict, result: DevTokenValidationResult):
        """Update the validation cache"""
        self._cached_token = token_data
        self._cached_result = result
        self._cache_timestamp = time.time()

    def clear_cache(self):
        """Clear the validation cache"""
        self._cached_token = None
        self._cached_result = None
        self._cache_timestamp = 0.0

    def has_feature(self, feature: str) -> bool:
        """
        Check if validated token has a specific feature enabled.

        Args:
            feature: Feature name to check (e.g., 'level_3', 'gpu')

        Returns:
            True if feature is enabled in current token
        """
        result = self.validate()
        if not result.valid or not result.payload:
            return False

        return feature in result.payload.features


def get_dev_token_validator() -> DevTokenValidator:
    """
    Get a singleton DevTokenValidator instance.

    Returns:
        DevTokenValidator instance
    """
    if not hasattr(get_dev_token_validator, '_instance'):
        get_dev_token_validator._instance = DevTokenValidator()
    return get_dev_token_validator._instance


def is_dev_bypass_active() -> bool:
    """
    Check if a valid dev token bypass is active.

    This function should be used at license enforcement points
    to determine if developer bypass is authorized.

    Returns:
        True if valid dev token exists and EPOCHLY_TEST_MODE=1
    """
    try:
        validator = get_dev_token_validator()
        result = validator.validate(skip_revocation=True)  # Skip for performance
        return result.valid
    except Exception as e:
        logger.debug(f"Dev bypass check failed: {e}")
        return False


def get_dev_token_features() -> List[str]:
    """
    Get the list of features enabled by the dev token.

    Returns:
        List of feature names, or empty list if no valid token
    """
    try:
        validator = get_dev_token_validator()
        result = validator.validate(skip_revocation=True)
        if result.valid and result.payload:
            return result.payload.features
    except Exception:
        pass
    return []
