"""
Cloud Synchronization for Compatibility Data

Handles synchronization with Epochly central servers for community-driven
compatibility data. Designed for graceful offline/airgapped operation.

Author: Epochly Development Team
"""

import os
import json
import logging
import threading
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib

# Try to import requests - it's optional for offline/airgapped systems
try:
    import requests
    from requests.adapters import HTTPAdapter
    try:
        # Try newer version first
        from urllib3.util.retry import Retry
    except ImportError:
        # Fall back to requests bundled version
        from requests.packages.urllib3.util.retry import Retry
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CloudCompatibilitySync:
    """
    Cloud synchronization for compatibility data.
    
    Features:
    - Graceful offline/airgapped operation
    - Automatic connectivity detection
    - Secure HTTPS-only communication
    - Weekly background sync (configurable)
    - Automatic retry with exponential backoff
    - Local caching of cloud data
    - Telemetry consent checking
    - Non-intrusive background operation
    """
    
    DEFAULT_API_ENDPOINT = "https://api.epochly.com"
    FALLBACK_ENDPOINTS = [
        "https://compatibility-api.epochly.com",  # Old domain as fallback
        "https://6g2po3kxnd.execute-api.us-west-2.amazonaws.com/prod",  # Direct API Gateway URL
        "https://api.epochly.dev/v1/compatibility"  # Future endpoint
    ]
    
    # Sync intervals
    DEFAULT_SYNC_INTERVAL = 7 * 24 * 3600  # Weekly by default
    MIN_SYNC_INTERVAL = 24 * 3600  # Daily minimum
    MAX_SYNC_INTERVAL = 30 * 24 * 3600  # Monthly maximum
    
    def __init__(self, 
                 api_endpoint: Optional[str] = None,
                 cache_duration: int = 3600,
                 enable_background_sync: bool = True,
                 offline_mode: bool = False,
                 sync_interval: Optional[int] = None):
        """
        Initialize cloud sync.
        
        Args:
            api_endpoint: API endpoint URL (uses default if None)
            cache_duration: Cache duration in seconds (default: 1 hour)
            enable_background_sync: Enable background synchronization
            offline_mode: Force offline mode (for airgapped systems)
            sync_interval: Sync interval in seconds (default: weekly)
        """
        # Configuration
        self.api_endpoint = api_endpoint or os.environ.get(
            'EPOCHLY_COMPAT_API', 
            self.DEFAULT_API_ENDPOINT
        )
        self.cache_duration = cache_duration
        self.enable_background_sync = enable_background_sync
        
        # Sync interval configuration
        if sync_interval is not None:
            self.sync_interval = max(self.MIN_SYNC_INTERVAL, 
                                    min(sync_interval, self.MAX_SYNC_INTERVAL))
        else:
            # Check environment or use default
            env_interval = os.environ.get('EPOCHLY_SYNC_INTERVAL')
            if env_interval:
                try:
                    self.sync_interval = int(env_interval)
                except ValueError:
                    self.sync_interval = self.DEFAULT_SYNC_INTERVAL
            else:
                self.sync_interval = self.DEFAULT_SYNC_INTERVAL
        
        # Offline/airgapped support - force offline if requests not available
        self.offline_mode = offline_mode or not REQUESTS_AVAILABLE or os.environ.get('EPOCHLY_OFFLINE_MODE', '').lower() in ('1', 'true', 'yes')
        
        if not REQUESTS_AVAILABLE and not offline_mode:
            logger.debug("Requests library not available - operating in offline mode. "
                        "Install 'requests' package for cloud sync capabilities.")
        
        self.last_successful_sync = None
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5
        
        # Connectivity detection
        self._connectivity_available = False
        self._last_connectivity_check = 0
        self._connectivity_check_interval = 3600  # Check hourly
        
        # Telemetry consent
        self.telemetry_enabled = self._check_telemetry_consent()
        
        # Cache
        self.cache_dir = self._get_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "cloud_compatibility_cache.json"
        self.last_sync_file = self.cache_dir / "last_sync.json"
        
        # HTTP session with retry
        self.session = self._create_session()
        
        # Background sync thread
        self._sync_thread = None
        self._stop_sync = threading.Event()
        
        # Load last sync info
        self._load_last_sync_info()
        
        # Start background sync if enabled and possible
        if enable_background_sync and not self.offline_mode and REQUESTS_AVAILABLE:
            self._start_background_sync()
    
    def _create_session(self) -> Optional['requests.Session']:
        """Create HTTP session with retry strategy and security settings"""
        if not REQUESTS_AVAILABLE:
            return None
            
        session = requests.Session()
        
        # Configure retry strategy
        # Handle both old and new parameter names for compatibility
        retry_kwargs = {
            'total': 3,
            'backoff_factor': 1,
            'status_forcelist': [429, 500, 502, 503, 504]
        }
        
        # Try newer parameter name first
        try:
            retry_strategy = Retry(
                **retry_kwargs,
                allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
            )
        except TypeError:
            # Fall back to older parameter name
            retry_strategy = Retry(
                **retry_kwargs,
                method_whitelist=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
            )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        
        # Remove default HTTP adapter for security
        if 'http://' in session.adapters:
            del session.adapters['http://']
        
        session.mount("https://", adapter)  # ONLY HTTPS - no HTTP
        
        # Security settings
        session.verify = True  # Always verify SSL certificates
        session.timeout = (5, 30)  # (connect, read) timeouts
        
        # Add security headers
        session.headers.update({
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        return session
    
    def _get_authenticated_headers(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Get authentication headers using fingerprint auth system."""
        try:
            from .secure_node_auth import SecureNodeAuth
            auth = SecureNodeAuth()
            auth_headers = auth.generate_auth_headers(data)
            return auth_headers
        except Exception as e:
            logger.debug(f"Failed to generate auth headers: {e}")
            return {}
    
    def _check_telemetry_consent(self) -> bool:
        """Check if user has consented to telemetry"""
        # Check environment variable
        telemetry_env = os.environ.get('EPOCHLY_TELEMETRY', '').lower()
        if telemetry_env in ('0', 'false', 'no', 'disabled'):
            return False
        
        # Check config file
        config_paths = [
            Path.home() / '.epochly' / 'config.yaml',
            Path('/etc/epochly/config.yaml')
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    import yaml
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                        if config and 'telemetry' in config:
                            return config['telemetry']
                except:
                    pass
        
        # Default to enabled (opt-out model)
        return True
    
    def _get_cache_dir(self) -> Path:
        """Get cache directory for cloud data"""
        if os.environ.get('EPOCHLY_CACHE_DIR'):
            return Path(os.environ['EPOCHLY_CACHE_DIR']) / 'cloud'
        
        if os.name == 'nt':
            base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            return Path(base) / 'Epochly' / 'cache' / 'cloud'
        else:
            base = os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
            return Path(base) / 'epochly' / 'cloud'
    
    def _load_last_sync_info(self) -> None:
        """Load information about last successful sync"""
        if self.last_sync_file.exists():
            try:
                with open(self.last_sync_file, 'r') as f:
                    info = json.load(f)
                    self.last_successful_sync = datetime.fromisoformat(info['timestamp'])
                    self.consecutive_failures = info.get('consecutive_failures', 0)
            except Exception as e:
                logger.debug(f"Failed to load last sync info: {e}")
    
    def _save_last_sync_info(self, success: bool = True) -> None:
        """Save information about sync attempt"""
        try:
            if success:
                self.last_successful_sync = datetime.now(timezone.utc)
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1
            
            info = {
                'timestamp': self.last_successful_sync.isoformat() if self.last_successful_sync else None,
                'consecutive_failures': self.consecutive_failures,
                'last_attempt': datetime.now(timezone.utc).isoformat()
            }
            
            with open(self.last_sync_file, 'w') as f:
                json.dump(info, f, indent=2)
                
        except Exception as e:
            logger.debug(f"Failed to save sync info: {e}")
    
    def _check_connectivity(self) -> bool:
        """
        Check if we have network connectivity to cloud services.
        
        This method performs a lightweight connectivity check to avoid
        unnecessary network attempts on airgapped or firewalled systems.
        
        Returns:
            True if connectivity is available
        """
        if self.offline_mode or not REQUESTS_AVAILABLE:
            return False
        
        # Rate limit connectivity checks
        now = time.time()
        if now - self._last_connectivity_check < self._connectivity_check_interval:
            return self._connectivity_available
        
        self._last_connectivity_check = now
        
        # Try a lightweight connectivity check
        if not self.session:
            return False
            
        try:
            # Prepare auth headers for connectivity check
            check_data = {'endpoint': '/sync', 'check_type': 'connectivity'}
            auth_headers = self._get_authenticated_headers(check_data)
            
            # Use HEAD request for minimal data transfer with authentication
            response = self.session.head(
                self.api_endpoint + "/sync",
                headers=auth_headers,  # Include authentication
                timeout=(2, 5),  # Short timeout for connectivity check
                allow_redirects=False
            )
            
            # Any response (even error codes) means we have connectivity
            self._connectivity_available = True
            logger.debug("Connectivity check successful")
            return True
            
        except Exception as e:
            # Common issues: timeout, connection refused, DNS failure
            logger.debug(f"Connectivity check failed: {type(e).__name__}")
            self._connectivity_available = False
            
            # Extend check interval on failure to reduce overhead
            self._connectivity_check_interval = min(
                self._connectivity_check_interval * 2,
                24 * 3600  # Max 24 hours between checks
            )
            return False
    
    def is_available(self) -> bool:
        """
        Check if cloud sync is available.
        
        Returns:
            True if cloud sync can be attempted
        """
        # Check offline mode
        if self.offline_mode:
            return False
        
        # Check telemetry consent
        if not self.telemetry_enabled:
            return False
        
        # Check connectivity (cached)
        if not self._check_connectivity():
            return False
        
        # Check if we've had too many failures
        if self.consecutive_failures >= self.max_consecutive_failures:
            # Check if enough time has passed for retry (exponential backoff)
            if self.last_successful_sync:
                backoff_minutes = min(2 ** self.consecutive_failures, 1440)  # Max 24 hours
                next_retry = self.last_successful_sync + timedelta(minutes=backoff_minutes)
                if datetime.now(timezone.utc) < next_retry:
                    logger.debug(f"Cloud sync unavailable: backing off after {self.consecutive_failures} failures")
                    return False
        
        return True
    
    def fetch_updates(self, force: bool = False) -> Optional[Dict[str, Any]]:
        """
        Fetch compatibility updates from cloud.
        
        Args:
            force: Force fetch even if cache is fresh
            
        Returns:
            Dictionary of compatibility data or None if unavailable
        """
        if not self.is_available():
            return self._load_cached_data()
        
        # Check cache unless forced
        if not force and self._is_cache_fresh():
            return self._load_cached_data()
        
        # Try primary endpoint
        data = self._fetch_from_endpoint(self.api_endpoint)
        
        # Try fallback endpoints if primary fails
        if data is None:
            for endpoint in self.FALLBACK_ENDPOINTS:
                data = self._fetch_from_endpoint(endpoint)
                if data is not None:
                    break
        
        # Update sync info
        if data is not None:
            self._save_cached_data(data)
            self._save_last_sync_info(success=True)
        else:
            self._save_last_sync_info(success=False)
            # Return cached data as fallback
            data = self._load_cached_data()
        
        return data

    def report_compatibility(self, module_name: str, compatibility_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Report module compatibility data to cloud.

        Args:
            module_name: Name of module
            compatibility_data: Compatibility information to report

        Returns:
            Dict with result: {'success': bool, 'message': str}
        """
        if not self.is_available():
            logger.debug("Cloud sync not available, cannot report")
            return {'success': False, 'message': 'Cloud sync not available'}

        try:
            logger.debug(f"Reporting compatibility for {module_name} to cloud")

            # Prepare report data
            report_data = {
                'module': module_name,
                'data': compatibility_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            # Get authenticated headers
            auth_headers = self._get_authenticated_headers(report_data)

            # Prepare request headers
            headers = {
                'User-Agent': f'Epochly/{self._get_version()}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                **auth_headers
            }

            # Make POST request to report endpoint
            report_url = f"{self.api_endpoint}/compatibility/report"
            response = self.session.post(
                report_url,
                json=report_data,
                headers=headers,
                timeout=(5, 30)
            )

            response.raise_for_status()

            result = response.json()
            logger.info(f"Successfully reported {module_name} to cloud")

            return {
                'success': True,
                'message': result.get('message', 'Reported successfully')
            }

        except Exception as e:
            logger.warning(f"Failed to report {module_name} to cloud: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def _fetch_from_endpoint(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Fetch data from a specific endpoint"""
        try:
            logger.debug(f"Fetching compatibility data from {endpoint}")
            
            # Prepare request data for authentication
            request_data = {
                'endpoint': '/sync',  # Correct endpoint per API Gateway
                'telemetry_enabled': self.telemetry_enabled
            }
            
            # Get authenticated headers using fingerprint system
            auth_headers = self._get_authenticated_headers(request_data)
            
            # Prepare request headers with authentication
            headers = {
                'User-Agent': f'Epochly/{self._get_version()}',
                'Accept': 'application/json',
                **auth_headers  # Include fingerprint authentication
            }
            
            if self.telemetry_enabled:
                headers['X-Epochly-Telemetry'] = 'enabled'
            
            # Make request with timeout to correct endpoint
            sync_url = endpoint if '/sync' in endpoint else f"{endpoint}/sync"
            response = self.session.get(
                sync_url,
                headers=headers,
                timeout=(5, 30)
            )
            
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Successfully fetched compatibility data from {endpoint}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.debug(f"Failed to fetch from {endpoint}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON from {endpoint}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Unexpected error fetching from {endpoint}: {e}")
            return None
    
    def report_incompatibility(self, module_name: str, error_info: Dict[str, Any]) -> bool:
        """
        Report module incompatibility to cloud service.
        
        Args:
            module_name: Name of incompatible module
            error_info: Error information
            
        Returns:
            True if report was sent successfully
        """
        if not self.is_available() or not self.telemetry_enabled:
            logger.debug("Cannot report incompatibility: cloud sync unavailable")
            return False
        
        try:
            endpoint = f"{self.api_endpoint}/report"
            
            payload = {
                'module': module_name,
                'data': error_info,  # Changed from 'error' to 'data' to match Lambda function
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'epochly_version': self._get_version(),
                'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
                'platform': os.sys.platform
            }
            
            # Get authenticated headers for report payload
            auth_headers = self._get_authenticated_headers(payload)
            
            headers = {
                'User-Agent': f'Epochly/{self._get_version()}',
                'Content-Type': 'application/json',
                **auth_headers  # Include fingerprint authentication
            }
            
            response = self.session.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=(5, 10)
            )
            
            response.raise_for_status()
            logger.debug(f"Reported incompatibility for {module_name}")
            return True
            
        except Exception as e:
            logger.debug(f"Failed to report incompatibility: {e}")
            return False
    
    def _is_cache_fresh(self) -> bool:
        """Check if cached data is still fresh"""
        if not self.cache_file.exists():
            return False
        
        try:
            stat = self.cache_file.stat()
            age = time.time() - stat.st_mtime
            return age < self.cache_duration
        except:
            return False
    
    def _load_cached_data(self) -> Optional[Dict[str, Any]]:
        """Load cached cloud data"""
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                logger.debug("Loaded cached cloud compatibility data")
                return data
        except Exception as e:
            logger.debug(f"Failed to load cached data: {e}")
            return None
    
    def _save_cached_data(self, data: Dict[str, Any]) -> None:
        """Save cloud data to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                logger.debug("Saved cloud compatibility data to cache")
        except Exception as e:
            logger.warning(f"Failed to cache cloud data: {e}")
    
    def _get_version(self) -> str:
        """Get Epochly version"""
        try:
            from epochly import __version__
            return __version__
        except:
            return "unknown"
    
    def _start_background_sync(self) -> None:
        """Start background synchronization thread"""
        if self._sync_thread is not None and self._sync_thread.is_alive():
            return
        
        self._stop_sync.clear()
        self._sync_thread = threading.Thread(
            target=self._background_sync_worker,
            name="CloudCompatibilitySync",
            daemon=True
        )
        self._sync_thread.start()
        logger.debug("Started background compatibility sync")
    
    def _background_sync_worker(self) -> None:
        """Background worker for periodic sync"""
        while not self._stop_sync.is_set():
            try:
                # Calculate time until next sync
                if self.last_successful_sync:
                    # Time since last sync
                    time_since_sync = (datetime.now(timezone.utc) - self.last_successful_sync).total_seconds()
                    time_until_sync = max(0, self.sync_interval - time_since_sync)
                else:
                    # No previous sync, check immediately
                    time_until_sync = 0
                
                # Wait until next sync time or stop signal
                if time_until_sync > 0:
                    if self._stop_sync.wait(timeout=time_until_sync):
                        break
                
                # Attempt sync if available
                if self.is_available():
                    self.fetch_updates()
                else:
                    # If sync unavailable, check again in an hour
                    if self._stop_sync.wait(timeout=3600):
                        break
                    
            except Exception as e:
                logger.debug(f"Background sync error: {e}")
                # On error, wait a bit before retrying
                if self._stop_sync.wait(timeout=300):  # 5 minutes
                    break
    
    def stop_background_sync(self) -> None:
        """Stop background synchronization"""
        if self._sync_thread is not None:
            self._stop_sync.set()
            self._sync_thread.join(timeout=5)
            self._sync_thread = None
            logger.debug("Stopped background compatibility sync")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        return {
            'enabled': not self.offline_mode,
            'telemetry_enabled': self.telemetry_enabled,
            'last_successful_sync': self.last_successful_sync.isoformat() if self.last_successful_sync else None,
            'consecutive_failures': self.consecutive_failures,
            'cache_fresh': self._is_cache_fresh(),
            'background_sync_active': self._sync_thread is not None and self._sync_thread.is_alive()
        }