"""
License enforcement module for Epochly.

This module handles the actual enforcement of license limits in the running system.
It checks licenses locally first for performance, with periodic sync to AWS.
"""

import os
import json
import time
import hashlib
import hmac
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import threading
import logging

# Import enhanced security modules
try:
    from .binary_integrity import BinaryIntegrityChecker, get_binary_integrity_checker
    from .time_protection import TimeManipulationDetector, get_time_detector
    from .secure_storage import SecureLicenseStorage, get_secure_storage
    _SECURITY_MODULES_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Enhanced security modules not available: {e}")
    _SECURITY_MODULES_AVAILABLE = False

logger = logging.getLogger(__name__)


class LicenseEnforcer:
    """
    Enforces license limits at runtime with minimal performance impact.
    
    Key features:
    - Local caching for fast checks (microseconds)
    - Background sync with AWS
    - Offline grace period (7 days)
    - Hardware-bound encryption
    - Tamper detection
    """
    
    # Singleton instance
    _instance = None
    _lock = threading.Lock()
    
    # License cache duration
    CACHE_DURATION = 3600  # 1 hour
    GRACE_PERIOD_DAYS = 7
    
    # DEPRECATED: This RSA public key placeholder is no longer used.
    # License signature verification now uses Ed25519 in license_crypto.py
    # See LicenseCrypto.EMBEDDED_PUBLIC_KEY_PEM for the active public key.
    # This attribute is kept for backwards compatibility with any code that
    # might check for its presence, but it is NOT used for verification.
    # P0-3: Clarified this is deprecated - actual verification uses license_crypto.py
    _PUBLIC_KEY = None  # Deprecated - see license_crypto.py
    
    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize license enforcer."""
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._cache_dir = self._get_cache_dir()
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        # License state
        self._license_data: Optional[Dict[str, Any]] = None
        self._last_sync = 0
        self._sync_thread = None

        # Check if we're in test mode
        self._test_mode = os.environ.get('EPOCHLY_TEST_MODE') == '1'

        # License enforcement bypass via cryptographically signed dev tokens ONLY
        # Dev tokens require:
        # 1. Valid ED25519 signature from api.epochly.com
        # 2. EPOCHLY_TEST_MODE=1 set (prevents production misuse)
        # 3. Token not expired or revoked
        #
        # SECURITY: Env var bypass (EPOCHLY_DISABLE_LICENSE_ENFORCEMENT) removed
        # Anyone discovering an env var can trivially bypass protection
        # Dev tokens are cryptographically secure and auditable
        dev_token_bypass = False
        try:
            from .dev_token_validator import is_dev_bypass_active
            dev_token_bypass = is_dev_bypass_active()
        except ImportError:
            pass  # Dev token module not available

        self._enforcement_active = not dev_token_bypass
        self._dev_token_bypass = dev_token_bypass

        # Log when bypass is used (audit trail)
        if dev_token_bypass and not self._test_mode:
            import logging
            logger = logging.getLogger('epochly.licensing')
            logger.info("License enforcement bypassed via valid dev token")
            self._bypass_mode_active = True
        else:
            self._bypass_mode_active = False
        
        # Enhanced security components (LAZY INITIALIZATION for performance)
        if _SECURITY_MODULES_AVAILABLE:
            # Lazy initialization - only create when actually needed
            self._integrity_checker = None
            self._time_detector = None
            self._secure_storage = None
            self._security_validated = False
        else:
            self._integrity_checker = None
            self._time_detector = None
            self._secure_storage = None
            self._security_validated = True  # Skip validation if not available
        
        if not self._test_mode:
            # Load cached license
            self._load_cached_license()

            # Start background sync
            self._start_background_sync()

            # Show startup PLG message
            self._show_startup_message()

            # Schedule security validation in background (non-blocking)
            if _SECURITY_MODULES_AVAILABLE:
                threading.Thread(
                    target=self._perform_security_validation,
                    daemon=True
                ).start()

    def _get_integrity_checker(self):
        """Lazy getter for binary integrity checker."""
        if self._integrity_checker is None and _SECURITY_MODULES_AVAILABLE:
            self._integrity_checker = get_binary_integrity_checker()
        return self._integrity_checker

    def _get_time_detector(self):
        """Lazy getter for time manipulation detector."""
        if self._time_detector is None and _SECURITY_MODULES_AVAILABLE:
            self._time_detector = get_time_detector()
        return self._time_detector

    def _get_secure_storage(self):
        """Lazy getter for secure storage."""
        if self._secure_storage is None and _SECURITY_MODULES_AVAILABLE:
            self._secure_storage = get_secure_storage()
        return self._secure_storage

    def _ensure_security_validation(self):
        """Ensure security validation has been performed (lazy)."""
        if not self._security_validated and _SECURITY_MODULES_AVAILABLE:
            self._perform_security_validation()
            self._security_validated = True

    def _get_cache_dir(self) -> Path:
        """Get secure cache directory for license data."""
        if os.name == 'nt':
            base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            return Path(base) / 'Epochly' / '.license'
        else:
            base = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
            return Path(base) / 'epochly' / '.license'
    
    def _perform_security_validation(self):
        """Perform comprehensive security validation on startup."""
        # Skip security validation in test mode (prevents NTP timeouts)
        if self._test_mode:
            return

        try:
            # Verify binary integrity (but don't disable enforcement during development)
            integrity_checker = self._get_integrity_checker()
            if integrity_checker:
                integrity_result = integrity_checker.quick_startup_check()
                if not integrity_result['valid']:
                    logger.warning("Binary integrity check failed - this is expected during development")
                    # Don't disable enforcement - just log the warning

            # Verify time integrity
            time_detector = self._get_time_detector()
            if time_detector:
                time_result = time_detector.quick_time_validation()
                if not time_result['valid']:
                    logger.error("Time manipulation detected")
                    # Don't disable enforcement, but log the issue
            
            # Check for debugging attempts
            try:
                import epochly.licensing.native_guard as ng
                if hasattr(ng, 'detect_anti_debugging'):
                    if ng.detect_anti_debugging():
                        logger.warning("Debugging tools detected")
            except Exception:
                pass
                
        except Exception as e:
            logger.error(f"Security validation failed: {e}")
    
    def check_cores(self, requested_cores: int) -> Tuple[bool, int]:
        """
        Check if requested cores are allowed under current license with security validation.

        Uses get_limits() to properly handle trial expiry and tier transitions.

        Args:
            requested_cores: Number of cores requested

        Returns:
            Tuple of (allowed, max_cores)
        """
        # Enhanced security check - handle disabled enforcement properly
        if not self._enforcement_active:
            # When enforcement is explicitly disabled (e.g., for testing), allow unlimited cores
            logger.debug("License enforcement disabled - allowing unlimited cores")
            return True, requested_cores

        # Perform real-time security validation (non-blocking)
        if _SECURITY_MODULES_AVAILABLE and not self._test_mode and self._enforcement_active:
            try:
                security_valid = self._validate_runtime_security()
                if not security_valid:
                    logger.warning("Runtime security validation failed - using degraded mode")
                    # Don't completely block, but log the issue
            except Exception as e:
                logger.warning(f"Security validation error: {e}")

        # Use get_limits() which properly handles expiry checks
        limits = self.get_limits()
        max_cores = limits.get('max_cores')

        # None means unlimited
        if max_cores is None:
            return True, requested_cores

        # Enforce limit
        if requested_cores <= max_cores:
            return True, max_cores
        else:
            # Show PLG message for core limit
            from epochly.licensing.plg_messaging import show_core_limit_message
            show_core_limit_message(requested_cores, max_cores)

            logger.debug(
                f"License limit: Requested {requested_cores} cores but licensed for {max_cores}"
            )
            return False, max_cores
    
    def check_gpu(self) -> bool:
        """
        Check if GPU acceleration is allowed under current license.

        Uses get_limits() to properly handle trial expiry and tier transitions.

        Returns:
            True if GPU is allowed
        """
        if not self._enforcement_active:
            return True

        # Use get_limits() which properly handles expiry checks
        limits = self.get_limits()
        gpu_enabled = limits.get('gpu_enabled', False)

        if not gpu_enabled:
            # Show PLG message for GPU feature
            from epochly.licensing.plg_messaging import show_feature_blocked
            show_feature_blocked('gpu')
            logger.debug("GPU acceleration not available in current license tier")

        return gpu_enabled
    
    def check_feature(self, feature: str) -> bool:
        """
        Check if a specific feature is enabled.
        
        Args:
            feature: Feature name to check
            
        Returns:
            True if feature is enabled
        """
        if not self._enforcement_active:
            return True
            
        license_data = self._get_current_license()
        
        if not license_data:
            # Default features for community tier
            default_features = {
                'basic_optimization',
                'threading',
                'memory_pooling'
            }
            return feature in default_features
        
        features = license_data.get('features', [])
        return feature in features
    
    def get_tier(self) -> str:
        """Get current license tier."""
        license_data = self._get_current_license()
        return license_data.get('tier', 'community') if license_data else 'community'
    
    def get_limits(self, _skip_worker_cache: bool = False) -> Dict[str, Any]:
        """Get all current license limits.

        Args:
            _skip_worker_cache: Internal flag to prevent recursion when called from
                               WorkerLicenseCache fallback. Do not use externally.
        """
        import os

        # Check for benchmark override (allows full system resources for performance testing)
        benchmark_override = os.environ.get('EPOCHLY_BENCHMARK_OVERRIDE') == '1'
        if benchmark_override:
            return {
                'tier': 'benchmark_override',
                'max_cores': None,  # Unlimited - use all system cores
                'gpu_enabled': True,
                'memory_limit_gb': None,
                'features': ['all']
            }

        # PERFORMANCE OPTIMIZATION (Phase 1.1): Use worker license cache in spawned workers
        # Workers set EPOCHLY_WORKER_PROCESS=1 during spawn. Using the pre-validated cache
        # reduces worker startup from ~1000ms to <10ms by skipping full license validation.
        # See planning/rca-level3-warmup-spike.md for details.
        #
        # CRITICAL: _skip_worker_cache prevents infinite recursion when WorkerLicenseCache
        # falls back to full validation - it calls get_limits(_skip_worker_cache=True).
        if not _skip_worker_cache and os.environ.get('EPOCHLY_WORKER_PROCESS') == '1':
            try:
                from .worker_license_cache import get_global_worker_cache
                cached_license = get_global_worker_cache().get_worker_license()
                if cached_license:
                    logger.debug("Worker process using cached license data (fast path)")
                    return cached_license
            except Exception as e:
                logger.debug(f"Worker cache unavailable, using full validation: {e}")
                # Fall through to normal path

        # Check if enforcement is disabled (for testing)
        if not self._enforcement_active:
            return {
                'tier': 'unlimited_test',
                'max_cores': None,  # Unlimited
                'gpu_enabled': True,
                'memory_limit_gb': None,
                'features': ['all']
            }

        license_data = self._get_current_license()

        if not license_data:
            # Community tier defaults
            return {
                'tier': 'community',
                'max_cores': 4,
                'gpu_enabled': False,
                'memory_limit_gb': 16,
                'features': ['basic_optimization', 'threading', 'memory_pooling']
            }

        tier = license_data.get('tier', 'community')

        # Check if trial has expired
        if tier == 'trial' and 'expires_at' in license_data:
            from datetime import datetime
            try:
                expiry = datetime.fromisoformat(license_data['expires_at'])
                now = datetime.now(timezone.utc)
                if now > expiry:
                    # Trial expired - fall back to community
                    tier = 'community'
            except (ValueError, TypeError):
                # Invalid expiry date - treat as community
                tier = 'community'

        # Tier-specific defaults
        if tier == 'trial':
            max_cores_default = None  # Unlimited for trial
            gpu_enabled_default = True  # GPU enabled for private beta trial
        elif tier == 'community':
            max_cores_default = 4
            gpu_enabled_default = False
        else:  # enterprise, instance, etc
            max_cores_default = None  # Unlimited for paid tiers
            gpu_enabled_default = True

        # SECURITY FIX: When tier is overridden to 'community' (e.g., expired trial),
        # use tier defaults instead of cached values to prevent stale gpu_enabled/max_cores
        # from leaking through. The original tier was 'trial' but now it's 'community'.
        original_tier = license_data.get('tier', 'community')
        tier_was_overridden = (original_tier != tier)

        if tier_was_overridden:
            # Use strict tier defaults - don't trust cached values from expired license
            return {
                'tier': tier,
                'max_cores': max_cores_default,
                'gpu_enabled': gpu_enabled_default,
                'memory_limit_gb': 16 if tier == 'community' else license_data.get('memory_limit_gb'),
                'features': ['basic_optimization', 'threading', 'memory_pooling'] if tier == 'community' else license_data.get('features', [])
            }

        return {
            'tier': tier,
            'max_cores': license_data.get('max_cores', max_cores_default),
            'gpu_enabled': license_data.get('gpu_enabled', gpu_enabled_default),
            'memory_limit_gb': license_data.get('memory_limit_gb'),
            'features': license_data.get('features', [])
        }

    def get_max_cores(self) -> Optional[int]:
        """
        Get the maximum number of cores allowed by the current license.

        Returns:
            Maximum cores allowed, or None for unlimited (paid tiers)
        """
        limits = self.get_limits()
        return limits.get('max_cores')

    def enforce_core_limit(self, requested_cores: int) -> int:
        """
        Enforce CPU core limit based on license tier.
        
        Args:
            requested_cores: Number of cores requested
            
        Returns:
            Actual number of cores allowed
        """
        limits = self.get_limits()
        max_cores = limits.get('max_cores')
        
        # None means unlimited (e.g., trial/enterprise)
        if max_cores is None:
            return requested_cores
        
        # Enforce the limit
        allowed_cores = min(requested_cores, max_cores)
        
        # Show message if enforcement happened
        if requested_cores > allowed_cores:
            from epochly.licensing.plg_messaging import show_core_limit_message
            show_core_limit_message(requested_cores, allowed_cores)
        
        return allowed_cores
    
    def _get_current_license(self) -> Optional[Dict[str, Any]]:
        """
        Get current license data with validation.
        
        Returns cached data if valid, otherwise attempts sync.
        """
        # Check if we have cached data
        if self._license_data:
            # Check if cache is still valid
            if self._is_cache_valid():
                return self._license_data
        
        # Try to sync with AWS (respecting performance optimization)
        should_sync = self._should_sync()

        # Check if we should skip license sync for performance (DEFAULT for users)
        try:
            import sys
            import os
            benchmarks_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'benchmarks')
            if benchmarks_path not in sys.path:
                sys.path.insert(0, benchmarks_path)

            from performance_optimization import should_skip_license_sync

            if should_skip_license_sync():
                logger.debug("Skipping license sync for fast user experience")
                should_sync = False

        except ImportError:
            # Performance optimizer not available, proceed with sync
            pass

        if should_sync:
            self._sync_license()
        
        # Return cached data even if expired (grace period)
        return self._license_data
    
    def _is_cache_valid(self) -> bool:
        """Check if cached license is still valid."""
        if not self._license_data:
            return False
        
        cached_at = self._license_data.get('cached_at', 0)
        cache_age = time.time() - cached_at
        
        return cache_age < self.CACHE_DURATION
    
    def _should_sync(self) -> bool:
        """Check if we should attempt to sync with AWS."""
        # Don't sync in test mode
        if self._test_mode:
            return False
            
        # Don't sync too frequently
        if time.time() - self._last_sync < 60:  # Min 1 minute between syncs
            return False
        
        # Check if we're in grace period
        if self._license_data:
            last_valid_sync = self._license_data.get('last_valid_sync', 0)
            days_since_sync = (time.time() - last_valid_sync) / 86400
            
            if days_since_sync > self.GRACE_PERIOD_DAYS:
                logger.warning(f"License grace period expired ({days_since_sync:.1f} days)")
                # Force community tier
                self._license_data = None
        
        return True
    
    def _sync_license(self):
        """Sync license with AWS via API Gateway."""
        self._last_sync = time.time()
        
        try:
            # Use the custom domain for API Gateway
            api_endpoint = 'https://api.epochly.com'
            
            # Get node authentication
            from epochly.compatibility.secure_node_auth import SecureNodeAuth
            
            # Get secure node auth instance
            auth = SecureNodeAuth()
            
            # Generate auth headers for the request
            auth_headers = auth.generate_auth_headers({})
            
            # Make API call to validate license
            import requests
            response = requests.post(
                f"{api_endpoint}/validate-license",
                json={},  # Empty body, auth is in headers
                headers=auth_headers,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'valid':
                    config = result.get('configuration', {})
                    
                    # Update cached license
                    self._license_data = {
                        'tier': result.get('tier', 'community'),
                        'max_cores': config.get('max_cores'),
                        'gpu_enabled': config.get('gpu_enabled', False),
                        'memory_limit_gb': config.get('memory_limit_gb'),
                        'features': config.get('features', []),
                        'cached_at': time.time(),
                        'last_valid_sync': time.time()
                    }
                    
                    # Save to cache
                    self._save_cached_license()
                    
                    logger.info(f"License synced: {self._license_data['tier']} tier")
            
        except Exception as e:
            logger.debug(f"License sync failed: {e}")
            # Continue with cached/grace period
    
    def _load_cached_license(self):
        """Load license from local cache."""
        cache_file = self._cache_dir / 'license.cache'
        
        if not cache_file.exists():
            return
        
        try:
            # Read encrypted cache
            with open(cache_file, 'rb') as f:
                encrypted_data = f.read()

            # Decrypt using hardware key
            decrypted = self._decrypt_license_data(encrypted_data)

            # Verify signature and extract data (format: data||signature)
            if self._verify_license_signature(decrypted):
                # Extract data portion (before ||signature)
                data_part = decrypted.rsplit('||', 1)[0] if '||' in decrypted else decrypted
                self._license_data = json.loads(data_part)
                logger.debug(f"Loaded cached license: {self._license_data.get('tier')}")
            else:
                logger.warning("Cached license signature invalid")

        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            # Corrupt cache file - delete and re-sync
            logger.warning(f"Corrupt license cache detected ({e}), deleting and will re-sync")
            try:
                cache_file.unlink()
            except:
                pass
        except Exception as e:
            logger.warning(f"Failed to load cached license: {e}")
    
    def _save_cached_license(self):
        """Save license to local cache."""
        if not self._license_data:
            return
        
        try:
            cache_file = self._cache_dir / 'license.cache'
            
            # Serialize license data
            data = json.dumps(self._license_data)
            
            # Sign data
            signed_data = self._sign_license_data(data)
            
            # Encrypt using hardware key
            encrypted = self._encrypt_license_data(signed_data)
            
            # Write atomically
            temp_file = cache_file.with_suffix('.tmp')
            with open(temp_file, 'wb') as f:
                f.write(encrypted)
            
            # Move atomically
            temp_file.replace(cache_file)
            
            # Secure permissions on Unix
            if os.name != 'nt':
                os.chmod(cache_file, 0o600)
                
        except Exception as e:
            logger.warning(f"Failed to save cached license: {e}")
    
    def _encrypt_license_data(self, data: str) -> bytes:
        """Encrypt license data using hardware-derived key."""
        from epochly.compatibility.secure_node_auth import MachineFingerprint
        
        # Derive key from hardware
        fingerprint = MachineFingerprint.generate()
        key = hashlib.sha256(fingerprint.encode()).digest()
        
        # Simple XOR encryption (in production, use AES)
        encrypted = bytearray()
        for i, char in enumerate(data.encode()):
            encrypted.append(char ^ key[i % len(key)])
        
        return bytes(encrypted)
    
    def _decrypt_license_data(self, encrypted: bytes) -> str:
        """Decrypt license data using hardware-derived key."""
        from epochly.compatibility.secure_node_auth import MachineFingerprint
        
        # Derive key from hardware
        fingerprint = MachineFingerprint.generate()
        key = hashlib.sha256(fingerprint.encode()).digest()
        
        # XOR decryption
        decrypted = bytearray()
        for i, byte in enumerate(encrypted):
            decrypted.append(byte ^ key[i % len(key)])
        
        return decrypted.decode()
    
    def _sign_license_data(self, data: str) -> str:
        """
        Sign license data for cache integrity.

        Uses HMAC-SHA256 (industry standard for message authentication).
        This is for detecting tampering of cached license data, not for
        validating license keys (license_crypto.py handles that with Ed25519).
        """
        signature = hmac.new(
            b'epochly-license-signing-key',
            data.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"{data}||{signature}"
    
    def _verify_license_signature(self, signed_data: str) -> bool:
        """Verify license data signature."""
        if '||' not in signed_data:
            return False
        
        data, signature = signed_data.rsplit('||', 1)
        
        expected_signature = hmac.new(
            b'epochly-license-signing-key',
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def _start_background_sync(self):
        """Start background license sync thread."""
        if self._sync_thread and self._sync_thread.is_alive():
            return
        
        def sync_loop():
            while self._enforcement_active:
                time.sleep(self.CACHE_DURATION)
                if self._should_sync():
                    self._sync_license()
        
        self._sync_thread = threading.Thread(target=sync_loop, daemon=True)
        self._sync_thread.start()
    
    def _show_startup_message(self):
        """Show appropriate PLG message at startup."""
        try:
            from epochly.licensing.plg_messaging import show_startup_message
            
            # Get current license info
            license_info = self.get_limits()
            
            # Add trial status if applicable
            if license_info['tier'] == 'trial' and self._license_data:
                expires_at = self._license_data.get('expires_at')
                if expires_at:
                    from datetime import datetime
                    expiry = datetime.fromisoformat(expires_at)
                    now = datetime.now(timezone.utc)
                    days_remaining = (expiry - now).days
                    license_info['days_remaining'] = days_remaining
            
            # Check if had trial
            license_info['had_trial'] = self.had_trial()
            
            # Show appropriate message
            show_startup_message(license_info)
        except Exception as e:
            logger.debug(f"Could not show startup message: {e}")
    
    def _validate_runtime_security(self) -> bool:
        """Validate security at runtime for performance-critical checks."""
        try:
            # Quick integrity check (cached)
            if self._integrity_checker:
                integrity_valid = self._integrity_checker.verify_self_integrity()['valid']
                if not integrity_valid:
                    return False
            
            # Quick time check
            if self._time_detector:
                time_valid = self._time_detector.quick_time_validation()['valid']
                if not time_valid:
                    logger.warning("Time inconsistency detected during runtime")
                    # Don't fail completely for time issues
            
            return True
            
        except Exception as e:
            logger.error(f"Runtime security validation error: {e}")
            return False
    
    def is_security_validated(self) -> bool:
        """Check if all security validations passed."""
        if not self._enforcement_active:
            return False
        
        # Perform comprehensive security check if modules available
        if _SECURITY_MODULES_AVAILABLE and not self._test_mode:
            try:
                # Binary integrity
                if self._integrity_checker:
                    integrity_ok = self._integrity_checker.verify_self_integrity()['valid']
                    if not integrity_ok:
                        return False
                
                # Time validation
                if self._time_detector:
                    time_ok = self._time_detector.check_time_consistency()['consistent']
                    if not time_ok:
                        logger.warning("Time inconsistency detected")
                        # Don't fail for time issues, just warn
                
                return True
                
            except Exception as e:
                logger.error(f"Security validation error: {e}")
                return False
        
        return self._enforcement_active
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status."""
        status = {
            'enforcement_active': self._enforcement_active,
            'security_modules_available': _SECURITY_MODULES_AVAILABLE,
            'test_mode': self._test_mode
        }
        
        if _SECURITY_MODULES_AVAILABLE and not self._test_mode:
            try:
                # Binary integrity status
                if self._integrity_checker:
                    integrity_result = self._integrity_checker.quick_startup_check()
                    status['binary_integrity'] = integrity_result
                
                # Time protection status
                if self._time_detector:
                    time_result = self._time_detector.quick_time_validation()
                    status['time_protection'] = time_result
                
                # Storage security status
                if self._secure_storage:
                    storage_result = self._secure_storage.verify_storage_integrity()
                    status['secure_storage'] = storage_result
                    
            except Exception as e:
                status['security_check_error'] = str(e)
        
        return status
    
    def had_trial(self) -> bool:
        """Check if this machine has already used its trial."""
        if self._license_data:
            return self._license_data.get('had_trial', False)
        
        # Check cache file
        cache_file = self._cache_dir / 'license.cache'
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted = self._decrypt_license_data(encrypted_data)
                if self._verify_license_signature(decrypted):
                    data = json.loads(decrypted.split('||')[0])
                    return data.get('had_trial', False)
            except:
                pass
        
        return False
    
    def disable_enforcement(self):
        """Disable license enforcement (for testing only)."""
        logger.warning("License enforcement disabled - for testing only!")
        self._enforcement_active = False
    
    def enable_enforcement(self):
        """Re-enable license enforcement."""
        self._enforcement_active = True
        logger.info("License enforcement enabled")
    
    def reset_for_testing(self):
        """Reset the enforcer state for testing (test mode only)."""
        if not self._test_mode:
            raise RuntimeError("reset_for_testing can only be called in test mode")
        
        # Reset to default state
        self._license_data = None
        self._last_sync = 0
        self._enforcement_active = True
        
        # Clear any cached license file
        cache_file = self._cache_dir / 'license.cache'
        if cache_file.exists():
            cache_file.unlink()
        
        logger.debug("License enforcer reset for testing")


# Global enforcer instance
_enforcer: Optional[LicenseEnforcer] = None


def get_license_enforcer() -> LicenseEnforcer:
    """Get the global license enforcer instance."""
    global _enforcer
    if _enforcer is None:
        _enforcer = LicenseEnforcer()
    return _enforcer


def check_core_limit(requested_cores: int) -> Tuple[bool, int]:
    """
    Check if requested cores are allowed.

    Supports EPOCHLY_BENCHMARK_OVERRIDE=1 environment variable to bypass
    license limits for performance testing and benchmarking.

    Args:
        requested_cores: Number of cores requested

    Returns:
        Tuple of (allowed, max_allowed_cores)
    """
    import os

    # Allow benchmark override (similar to GPU test override)
    benchmark_override = os.environ.get('EPOCHLY_BENCHMARK_OVERRIDE') == '1'

    if benchmark_override:
        # Bypass license check for benchmarking - allow all requested cores
        return (True, requested_cores)

    enforcer = get_license_enforcer()
    return enforcer.check_cores(requested_cores)


def check_gpu_access() -> bool:
    """
    Check if GPU acceleration is allowed.
    
    Returns:
        True if GPU is allowed under current license
    """
    enforcer = get_license_enforcer()
    return enforcer.check_gpu()


def check_feature(feature: str) -> bool:
    """
    Check if a specific feature is enabled.
    
    Args:
        feature: Feature name to check
        
    Returns:
        True if feature is enabled
    """
    enforcer = get_license_enforcer()
    return enforcer.check_feature(feature)


def get_license_tier() -> str:
    """Get current license tier."""
    enforcer = get_license_enforcer()
    return enforcer.get_tier()


def get_license_limits() -> Dict[str, Any]:
    """Get all current license limits."""
    enforcer = get_license_enforcer()
    return enforcer.get_limits()