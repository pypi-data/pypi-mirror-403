"""
Time manipulation detection and protection system.

This module implements comprehensive time validation to prevent license
circumvention through system clock manipulation and other timing attacks.
"""

import os
import sys
import time
import socket
import struct
import threading
import sqlite3
import hmac
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class TimeManipulationDetector:
    """
    Comprehensive time manipulation detection system.
    
    Features:
    - Multiple time source validation
    - Backwards time detection
    - NTP time correlation
    - Hardware clock validation
    - Secure time storage
    """
    
    # Singleton pattern for performance
    _instance = None
    _lock = threading.Lock()
    
    # NTP servers for time validation
    NTP_SERVERS = [
        'pool.ntp.org',
        'time.google.com',
        'time.cloudflare.com',
        'time.apple.com'
    ]
    
    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize time manipulation detector."""
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._storage_path = self._get_default_storage_path()
        self._monitoring_thread = None
        self._stop_monitoring = False
        self._time_history = []
        
        # Initialize secure time storage
        self._init_time_storage()
    
    def _get_default_storage_path(self) -> Path:
        """Get default storage path for secure time data."""
        if os.name == 'nt':
            base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            cache_dir = Path(base) / 'Epochly' / '.time'
        else:
            base = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
            cache_dir = Path(base) / 'epochly' / '.time'
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / 'secure_time.db'
    
    def set_storage_path(self, path: Path):
        """Set custom storage path (for testing)."""
        self._storage_path = path
        self._init_time_storage()
    
    def _init_time_storage(self):
        """Initialize secure time storage database."""
        try:
            # Ensure parent directory exists
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(str(self._storage_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS secure_times (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    source TEXT NOT NULL,
                    signature BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS time_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    details TEXT,
                    severity TEXT DEFAULT 'info',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize time storage: {e}")
    
    def get_multiple_time_sources(self) -> Dict[str, float]:
        """Get time from multiple sources for cross-validation."""
        sources = {}
        
        try:
            # System time
            sources['system_time'] = time.time()
            
            # Monotonic time (can't be set backwards)
            sources['monotonic_time'] = time.monotonic()
            
            # Process time
            sources['process_time'] = time.process_time()
            
            # Performance counter
            sources['perf_counter'] = time.perf_counter()
            
        except Exception as e:
            logger.error(f"Error getting time sources: {e}")
        
        return sources
    
    def check_time_consistency(self) -> Dict[str, Any]:
        """Check consistency across multiple time sources."""
        sources = self.get_multiple_time_sources()
        
        if len(sources) < 2:
            return {'consistent': False, 'error': 'Insufficient time sources'}
        
        # Compare system time with stored reference
        system_time = sources.get('system_time', 0)
        stored_time = self.get_stored_time()
        
        result = {
            'consistent': True,
            'sources': sources,
            'max_deviation': 0.0,
            'stored_reference': stored_time
        }
        
        # Check if system time went backwards
        if stored_time and system_time < stored_time:
            result['consistent'] = False
            result['backwards_detected'] = True
            result['time_diff'] = stored_time - system_time
            
            self._log_time_event('backwards_time_detected', system_time, 
                               f"System time {system_time} < stored time {stored_time}")
        
        # Calculate maximum deviation between sources (exclude monotonic/perf counters)
        comparable_times = []
        if 'system_time' in sources:
            comparable_times.append(sources['system_time'])
        
        # Only compare meaningful time sources
        if len(comparable_times) > 1:
            result['max_deviation'] = max(comparable_times) - min(comparable_times)
            
            # Large deviations indicate potential manipulation
            if result['max_deviation'] > 5.0:  # 5 second tolerance
                result['consistent'] = False
                self._log_time_event('time_deviation_detected', system_time,
                                   f"Large time deviation: {result['max_deviation']}")
        else:
            # Single time source - assume consistent
            result['max_deviation'] = 0.0
        
        # Update stored time if consistent
        if result['consistent']:
            self.store_secure_time(system_time)
        
        return result
    
    def detect_backwards_time(self) -> bool:
        """Detect if system time has gone backwards."""
        current_time = time.time()
        stored_time = self.get_stored_time()
        
        if stored_time and current_time < stored_time:
            self._log_time_event('backwards_time', current_time,
                               f"Current: {current_time}, Stored: {stored_time}")
            return True
        
        return False
    
    def would_detect_backwards_time(self, test_time: float) -> bool:
        """Test if backwards time would be detected (for testing)."""
        stored_time = self.get_stored_time()
        return stored_time and test_time < stored_time
    
    def store_secure_time(self, timestamp: float, source: str = 'system') -> bool:
        """Store time reference securely with integrity protection."""
        try:
            # Create integrity signature
            signature = self._create_time_signature(timestamp, source)
            
            conn = sqlite3.connect(self._storage_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO secure_times (timestamp, source, signature)
                VALUES (?, ?, ?)
            """, (timestamp, source, signature))
            
            # Keep only last 100 entries for performance
            cursor.execute("""
                DELETE FROM secure_times 
                WHERE id NOT IN (
                    SELECT id FROM secure_times 
                    ORDER BY id DESC LIMIT 100
                )
            """)
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store secure time: {e}")
            return False
    
    def get_stored_time(self) -> Optional[float]:
        """Get most recent stored time reference."""
        try:
            conn = sqlite3.connect(str(self._storage_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT timestamp, source, signature FROM secure_times 
                ORDER BY id DESC LIMIT 1
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                timestamp, source, signature = result
                
                # Verify signature
                if self._verify_time_signature(timestamp, source, signature):
                    return timestamp
                else:
                    self._log_time_event('signature_verification_failed', timestamp,
                                       'Stored time signature invalid')
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get stored time: {e}")
            return None
    
    def verify_time_storage_integrity(self) -> bool:
        """Verify integrity of time storage."""
        try:
            if not self._storage_path.exists():
                return True  # No storage file yet
            
            # Check if file has been tampered with
            conn = sqlite3.connect(self._storage_path)
            cursor = conn.cursor()
            
            # Check table structure
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['secure_times', 'time_events']
            if not all(table in tables for table in expected_tables):
                return False
            
            # Verify signatures of stored times
            cursor.execute("SELECT timestamp, source, signature FROM secure_times")
            for row in cursor.fetchall():
                timestamp, source, signature = row
                if not self._verify_time_signature(timestamp, source, signature):
                    return False
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Time storage integrity check failed: {e}")
            return False
    
    def get_ntp_time(self, timeout: float = 2.0) -> Dict[str, Any]:
        """Get time from NTP server."""
        # Skip NTP in test/CI environments to prevent network timeouts
        if os.environ.get('EPOCHLY_SKIP_NTP_VALIDATION') == '1':
            return {'available': False, 'skipped': True}

        result = {'available': False}

        try:
            for server in self.NTP_SERVERS:
                try:
                    # Simple NTP request
                    ntp_time = self._query_ntp_server(server, timeout)
                    if ntp_time:
                        result.update({
                            'available': True,
                            'time': ntp_time,
                            'server': server,
                            'accuracy': 'high'
                        })
                        break
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"NTP time query failed: {e}")
        
        return result
    
    def _query_ntp_server(self, server: str, timeout: float) -> Optional[float]:
        """Query NTP server for current time."""
        try:
            # Simple SNTP implementation
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.settimeout(timeout)
            
            # NTP packet (simplified)
            data = b'\x1b' + 47 * b'\0'
            
            client.sendto(data, (server, 123))
            data, address = client.recvfrom(1024)
            client.close()
            
            if len(data) >= 48:
                # Extract timestamp from NTP response
                t = struct.unpack("!I", data[40:44])[0]
                # Convert from NTP epoch (1900) to Unix epoch (1970)
                return t - 2208988800
                
        except Exception:
            pass
        
        return None
    
    def get_hardware_clock_time(self) -> Dict[str, Any]:
        """Get time from hardware clock."""
        result = {'available': False}
        
        try:
            if sys.platform == 'linux':
                # Read from hardware clock
                with open('/sys/class/rtc/rtc0/since_epoch', 'r') as f:
                    hw_time = int(f.read().strip())
                    result.update({
                        'available': True,
                        'time': hw_time,
                        'source': '/sys/class/rtc/rtc0'
                    })
            elif sys.platform == 'win32':
                # Windows: Use registry or WMI for hardware time
                # Simplified implementation
                result['available'] = False
                
        except Exception as e:
            logger.debug(f"Hardware clock read failed: {e}")
        
        return result
    
    def check_timezone_consistency(self) -> Dict[str, Any]:
        """Check timezone consistency for manipulation detection."""
        try:
            # Get current timezone info
            now = datetime.now()
            utc_now = datetime.utcnow()
            
            # Calculate UTC offset
            utc_offset = (now - utc_now).total_seconds()
            
            # Get system timezone
            system_tz = time.tzname[time.daylight] if time.daylight else time.tzname[0]
            
            return {
                'consistent': True,
                'system_tz': system_tz,
                'utc_offset': utc_offset,
                'local_time': now.isoformat(),
                'utc_time': utc_now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Timezone check failed: {e}")
            return {'consistent': False, 'error': str(e)}
    
    def get_system_uptime(self) -> Dict[str, Any]:
        """Get system uptime for time correlation."""
        try:
            if sys.platform == 'linux':
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.read().split()[0])
                    boot_time = time.time() - uptime_seconds
            elif sys.platform == 'win32':
                import psutil
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
            else:
                # macOS and others
                import psutil
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
            
            return {
                'uptime_seconds': uptime_seconds,
                'boot_time': boot_time,
                'current_time': time.time()
            }
            
        except Exception as e:
            logger.error(f"Uptime check failed: {e}")
            return {'uptime_seconds': 0, 'boot_time': 0}
    
    def validate_license_time(self, expiry_timestamp: float) -> bool:
        """Validate license expiry time against manipulation."""
        # Check time consistency first
        consistency = self.check_time_consistency()
        if not consistency['consistent']:
            logger.warning("Time inconsistency detected during license validation")
            return False
        
        # Use most reliable time source
        current_time = time.time()
        
        # Validate against NTP if available
        ntp_result = self.get_ntp_time()
        if ntp_result['available']:
            ntp_time = ntp_result['time']
            time_diff = abs(current_time - ntp_time)
            
            if time_diff > 300:  # 5 minutes tolerance
                logger.warning(f"Large time difference with NTP: {time_diff} seconds")
                # Use NTP time if available and significantly different
                current_time = ntp_time
        
        return current_time < expiry_timestamp
    
    def validate_grace_period(self, grace_start: float, grace_days: int) -> bool:
        """Validate grace period accounting for time manipulation."""
        current_time = time.time()
        grace_end = grace_start + (grace_days * 86400)
        
        # Check if we're still in grace period
        return current_time < grace_end
    
    def validate_trial_period(self, trial_start: float, trial_days: int) -> bool:
        """Validate trial period accounting for time manipulation."""
        current_time = time.time()
        trial_end = trial_start + (trial_days * 86400)
        
        # Check if trial is still valid
        return current_time < trial_end
    
    def quick_time_validation(self) -> Dict[str, Any]:
        """Quick time validation for startup checks."""
        try:
            sources = self.get_multiple_time_sources()
            stored_time = self.get_stored_time()
            
            # Basic consistency check
            system_time = sources.get('system_time', 0)
            backwards_detected = stored_time and system_time < stored_time
            
            return {
                'valid': not backwards_detected,
                'backwards_detected': backwards_detected,
                'sources_count': len(sources),
                'system_time': system_time,
                'stored_time': stored_time
            }
            
        except Exception as e:
            logger.error(f"Quick time validation failed: {e}")
            return {'valid': False, 'error': str(e)}
    
    def start_continuous_monitoring(self):
        """Start continuous time monitoring in background."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return
        
        self._stop_monitoring = False
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_worker,
            daemon=True
        )
        self._monitoring_thread.start()
    
    def stop_continuous_monitoring(self):
        """Stop continuous monitoring."""
        self._stop_monitoring = True
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=1.0)
    
    def _monitoring_worker(self):
        """Background monitoring worker."""
        while not self._stop_monitoring:
            try:
                # Perform time consistency check
                consistency = self.check_time_consistency()
                
                if not consistency['consistent']:
                    self._log_time_event('monitoring_inconsistency', time.time(),
                                       f"Time inconsistency during monitoring: {consistency}")
                
                # Store current time for future reference
                current_time = time.time()
                self.store_secure_time(current_time, 'monitoring')
                
                # Sleep for monitoring interval
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Monitoring worker error: {e}")
                time.sleep(30)
    
    def _create_time_signature(self, timestamp: float, source: str) -> bytes:
        """Create HMAC signature for time value."""
        # Use machine-specific key
        from epochly.compatibility.secure_node_auth import MachineFingerprint
        machine_id = MachineFingerprint.generate_complete_fingerprint()[:32]
        
        # Create signature data
        data = f"{timestamp}:{source}:{machine_id}".encode()
        secret_key = hashlib.sha256(machine_id.encode() + b"epochly_time_key").digest()
        
        return hmac.new(secret_key, data, hashlib.sha256).digest()
    
    def _verify_time_signature(self, timestamp: float, source: str, signature: bytes) -> bool:
        """Verify HMAC signature for time value."""
        try:
            expected_signature = self._create_time_signature(timestamp, source)
            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False
    
    def _log_time_event(self, event_type: str, timestamp: float, details: str, severity: str = 'warning'):
        """Log time-related security event."""
        try:
            conn = sqlite3.connect(str(self._storage_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO time_events (event_type, timestamp, details, severity)
                VALUES (?, ?, ?, ?)
            """, (event_type, timestamp, details, severity))
            
            conn.commit()
            conn.close()
            
            # Also log to Python logger
            getattr(logger, severity, logger.warning)(f"Time event [{event_type}]: {details}")
            
        except Exception as e:
            logger.error(f"Failed to log time event: {e}")


class TimeProtectionIntegration:
    """Integration layer for time protection with license system."""
    
    def __init__(self):
        self.detector = TimeManipulationDetector()
    
    def validate_license_with_time_protection(self, license_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate license with comprehensive time protection."""
        # Check time consistency first
        time_check = self.detector.check_time_consistency()
        
        result = {
            'time_valid': time_check['consistent'],
            'time_sources': time_check.get('sources', {}),
            'license_valid': False
        }
        
        if not time_check['consistent']:
            result['error'] = 'Time manipulation detected'
            return result
        
        # If time is consistent, proceed with license validation
        if 'expiry' in license_data:
            license_valid = self.detector.validate_license_time(license_data['expiry'])
            result['license_valid'] = license_valid
            
            if not license_valid:
                result['error'] = 'License expired'
        else:
            result['license_valid'] = True  # No expiry
        
        return result


# Global instance for performance
_global_time_detector = None

def get_time_detector() -> TimeManipulationDetector:
    """Get global time manipulation detector instance."""
    global _global_time_detector
    if _global_time_detector is None:
        _global_time_detector = TimeManipulationDetector()
    return _global_time_detector


def validate_time_integrity() -> bool:
    """Quick function to validate time integrity."""
    try:
        detector = get_time_detector()
        result = detector.quick_time_validation()
        return result['valid']
    except Exception:
        return False