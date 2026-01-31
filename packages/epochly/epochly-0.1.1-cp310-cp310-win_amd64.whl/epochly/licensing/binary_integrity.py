"""
Binary integrity checking system for license protection.

This module implements comprehensive binary integrity verification to protect
against tampering with Epochly core modules and license-related files.
"""

import os
import sys
import hashlib
import hmac
import sqlite3
import threading
import time
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import psutil

logger = logging.getLogger(__name__)



class BinaryIntegrityChecker:
    """
    Comprehensive binary integrity checking system.
    
    Features:
    - Core module hash verification
    - Real-time tampering detection
    - Performance-optimized checking
    - Anti-reverse engineering protection
    """
    
    # Singleton pattern for performance
    _instance = None
    _lock = threading.Lock()
    
    # Expected hashes for core modules (updated during build)
    EXPECTED_HASHES = {
        'epochly.core.epochly_core': None,  # Calculated at runtime
        'epochly.licensing.license_enforcer': None,
        'epochly.licensing.native_guard': None,
        'epochly.memory.fast_memory_pool': None,
    }
    
    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize binary integrity checker."""
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._db_path = self._get_integrity_db_path()
        self._background_thread = None
        self._stop_background = False
        self._critical_files = self._identify_critical_files()
        
        # Initialize integrity database
        self.initialize_database()
        
        # Perform initial integrity check (respecting performance optimization)
        self._perform_initial_check()
    
    def _get_integrity_db_path(self) -> Path:
        """Get path for integrity database."""
        if os.name == 'nt':
            base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            cache_dir = Path(base) / 'Epochly' / '.integrity'
        else:
            base = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
            cache_dir = Path(base) / 'epochly' / '.integrity'
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / 'integrity.db'
    
    def initialize_database(self):
        """Initialize SQLite database for hash storage."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_hashes (
                file_path TEXT PRIMARY KEY,
                expected_hash TEXT NOT NULL,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                protection_level TEXT DEFAULT 'normal',
                tamper_count INTEGER DEFAULT 0,
                cached_mtime REAL DEFAULT 0,
                cached_hash TEXT,
                cache_timestamp REAL DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS integrity_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                file_path TEXT,
                details TEXT,
                severity TEXT DEFAULT 'info'
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_core_modules(self) -> List[Dict[str, Any]]:
        """Get list of core Epochly modules to protect."""
        core_modules = []
        
        for module_name in self.EXPECTED_HASHES.keys():
            try:
                spec = importlib.util.find_spec(module_name)
                if spec and spec.origin:
                    core_modules.append({
                        'name': module_name,
                        'path': spec.origin,
                        'protection_level': 'critical' if 'licensing' in module_name else 'high'
                    })
            except Exception as e:
                logger.warning(f"Could not locate module {module_name}: {e}")
        
        return core_modules
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file."""
        hasher = hashlib.sha256()

        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""

    def _calculate_file_hash_fast(self, file_path: str) -> str:
        """Calculate fast hash using xxHash with SHA256 fallback."""
        try:
            # Try xxHash for 10× speed improvement
            import xxhash
            hasher = xxhash.xxh64()

            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):  # Larger chunks for xxHash
                    hasher.update(chunk)
            return hasher.hexdigest()

        except ImportError:
            # Fallback to SHA256 if xxHash not available
            return self.calculate_file_hash(file_path)
        except Exception as e:
            logger.error(f"Failed to calculate fast hash for {file_path}: {e}")
            return ""
    
    def verify_binary_integrity(self, file_path: str) -> Dict[str, Any]:
        """Verify integrity of a binary file."""
        current_hash = self.calculate_file_hash(file_path)
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        result = {
            'file_path': file_path,
            'hash': current_hash,
            'size': file_size,
            'valid': True,
            'timestamp': time.time()
        }
        
        # Check against stored hash if available
        stored_hash = self.get_stored_hash(file_path)
        if stored_hash:
            result['valid'] = (current_hash == stored_hash)
            if not result['valid']:
                result['tampering_detected'] = True
                self._log_integrity_event('tampering_detected', file_path, 
                                        f"Hash mismatch: {current_hash} != {stored_hash}")
        
        return result
    
    def store_file_hash(self, file_path: str, hash_value: str, protection_level: str = 'normal'):
        """Store expected hash for a file."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO file_hashes 
            (file_path, expected_hash, protection_level)
            VALUES (?, ?, ?)
        """, (file_path, hash_value, protection_level))
        
        conn.commit()
        conn.close()
    
    def get_stored_hash(self, file_path: str) -> Optional[str]:
        """Get stored hash for a file."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT expected_hash FROM file_hashes WHERE file_path = ?
        """, (file_path,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def update_file_hash(self, file_path: str, new_hash: str):
        """Update stored hash for a file."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE file_hashes 
            SET expected_hash = ?, last_checked = CURRENT_TIMESTAMP
            WHERE file_path = ?
        """, (new_hash, file_path))
        
        conn.commit()
        conn.close()
    
    def verify_file_integrity(self, file_path: str) -> bool:
        """Verify integrity of a single file."""
        stored_hash = self.get_stored_hash(file_path)
        if not stored_hash:
            # No stored hash - calculate and store
            current_hash = self.calculate_file_hash(file_path)
            self.store_file_hash(file_path, current_hash)
            return True
        
        current_hash = self.calculate_file_hash(file_path)
        is_valid = (current_hash == stored_hash)
        
        if not is_valid:
            self._increment_tamper_count(file_path)
            
        return is_valid
    
    def verify_module_integrity(self, module_path: str) -> Dict[str, Any]:
        """Verify integrity of an entire Python module."""
        module_dir = Path(module_path)
        if not module_dir.exists():
            return {'valid': False, 'error': 'Module path does not exist'}
        
        python_files = list(module_dir.glob('**/*.py'))
        results = {
            'module_path': str(module_dir),
            'total_files': len(python_files),
            'valid_files': 0,
            'invalid_files': 0,
            'files': [],
            'valid': True
        }
        
        for py_file in python_files:
            file_result = self.verify_binary_integrity(str(py_file))
            results['files'].append(file_result)
            
            if file_result['valid']:
                results['valid_files'] += 1
            else:
                results['invalid_files'] += 1
                results['valid'] = False
        
        return results
    
    def generate_signature(self, data: bytes) -> bytes:
        """Generate cryptographic signature for data."""
        # Use HMAC-SHA256 with embedded key for simplicity
        secret_key = b"epochly_binary_integrity_key_2025"
        return hmac.new(secret_key, data, hashlib.sha256).digest()
    
    def verify_signature(self, data: bytes, signature: bytes) -> bool:
        """Verify cryptographic signature."""
        expected_signature = self.generate_signature(data)
        return hmac.compare_digest(expected_signature, signature)
    
    def verify_multiple_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Verify integrity of multiple files efficiently."""
        results = []
        
        for file_path in file_paths:
            try:
                result = self.verify_binary_integrity(file_path)
                results.append(result)
            except Exception as e:
                results.append({
                    'file_path': file_path,
                    'valid': False,
                    'error': str(e)
                })
        
        return results
    
    def set_database_path(self, db_path: str):
        """Set custom database path (for testing)."""
        self._db_path = Path(db_path)
    
    def store_expected_hash(self, file_path: str, expected_hash: str):
        """Store expected hash for a file."""
        self.store_file_hash(file_path, expected_hash, 'high')
    
    def quick_startup_check(self) -> Dict[str, Any]:
        """Perform quick integrity check during startup."""
        start_time = time.perf_counter()
        
        # Check only critical files for performance
        critical_results = []
        for critical_file in self._critical_files[:5]:  # Limit to first 5 for speed
            try:
                if os.path.exists(critical_file['path']):
                    result = self.verify_file_integrity(critical_file['path'])
                    critical_results.append({
                        'file': critical_file['name'],
                        'valid': result
                    })
            except Exception:
                critical_results.append({
                    'file': critical_file['name'],
                    'valid': False
                })
        
        duration = time.perf_counter() - start_time
        
        return {
            'valid': all(r['valid'] for r in critical_results),
            'checked_files': len(critical_results),
            'duration_ms': duration * 1000,
            'results': critical_results
        }
    
    def start_background_verification(self):
        """Start background integrity verification."""
        if self._background_thread and self._background_thread.is_alive():
            return
        
        self._stop_background = False
        self._background_thread = threading.Thread(
            target=self._background_verification_worker,
            daemon=True
        )
        self._background_thread.start()
    
    def stop_background_verification(self):
        """Stop background verification."""
        self._stop_background = True
        if self._background_thread:
            self._background_thread.join(timeout=1.0)
    
    def _background_verification_worker(self):
        """Background worker for continuous verification."""
        while not self._stop_background:
            try:
                # Verify one critical file per iteration
                for critical_file in self._critical_files:
                    if self._stop_background:
                        break
                    
                    if os.path.exists(critical_file['path']):
                        is_valid = self.verify_file_integrity(critical_file['path'])
                        if not is_valid:
                            self._log_integrity_event(
                                'background_tampering_detected',
                                critical_file['path'],
                                'File modified during runtime'
                            )
                    
                    # Sleep between checks to avoid performance impact
                    time.sleep(10)
                
                # Full cycle complete, sleep longer
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Background verification error: {e}")
                time.sleep(30)
    
    def verify_self_integrity(self) -> Dict[str, Any]:
        """Verify integrity of the integrity checker itself."""
        try:
            # Get path to this module
            integrity_checker_path = __file__
            checker_hash = self.calculate_file_hash(integrity_checker_path)
            
            # Get native guard path
            native_guard_path = None
            try:
                import epochly.licensing.native_guard
                native_guard_path = epochly.licensing.native_guard.__file__
                native_guard_hash = self.calculate_file_hash(native_guard_path)
            except Exception:
                native_guard_hash = "not_available"
            
            return {
                'valid': True,
                'integrity_checker_hash': checker_hash,
                'native_guard_hash': native_guard_hash,
                'self_check_passed': True
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'self_check_passed': False
            }
    
    def verify_import_hooks(self) -> bool:
        """Verify sys.meta_path hasn't been tampered with."""
        try:
            # Check for suspicious import hooks
            meta_path_names = [type(hook).__name__ for hook in sys.meta_path]
            
            # Known safe hooks
            safe_hooks = {
                'BuiltinImporter', 'FrozenImporter', 'PathFinder',
                'FileFinder', '_SixMetaPathImporter'
            }
            
            # Check for unknown hooks
            unknown_hooks = set(meta_path_names) - safe_hooks
            
            # Log but don't fail for unknown hooks (they might be legitimate)
            if unknown_hooks:
                logger.info(f"Unknown import hooks detected: {unknown_hooks}")
            
            return len(sys.meta_path) < 10  # Reasonable limit
            
        except Exception:
            return False
    
    def verify_memory_integrity(self) -> bool:
        """Verify in-memory integrity of critical modules."""
        try:
            # Check if critical modules are still properly loaded
            critical_modules = [
                'epochly.core.epochly_core',
                'epochly.licensing.license_enforcer'
            ]
            
            for module_name in critical_modules:
                if module_name in sys.modules:
                    module = sys.modules[module_name]
                    # Check if module has expected attributes
                    if not hasattr(module, '__file__'):
                        return False
            
            return True
            
        except Exception:
            return False
    
    def detect_debugging_tools(self) -> Dict[str, Any]:
        """Detect debugging and reverse engineering tools."""
        detection_result = {
            'debugger_present': False,
            'reverse_engineering_tools': [],
            'suspicious_processes': []
        }
        
        try:
            # Check for common debugger indicators
            if hasattr(sys, 'gettrace') and sys.gettrace() is not None:
                detection_result['debugger_present'] = True
            
            # Check for suspicious processes
            try:
                for proc in psutil.process_iter(['name']):
                    proc_name = proc.info['name'].lower()
                    suspicious_names = [
                        'gdb', 'lldb', 'x64dbg', 'ollydbg', 'ida',
                        'radare2', 'ghidra', 'wireshark', 'procmon'
                    ]
                    
                    if any(suspicious in proc_name for suspicious in suspicious_names):
                        detection_result['reverse_engineering_tools'].append(proc_name)
                        detection_result['suspicious_processes'].append(proc_name)
                        
            except Exception:
                # Process enumeration might fail due to permissions
                pass
            
        except Exception as e:
            logger.debug(f"Debug detection error: {e}")
        
        return detection_result
    
    def _identify_critical_files(self) -> List[Dict[str, Any]]:
        """Identify critical files that need protection."""
        critical_files = []
        
        # Add core modules
        for module_name in self.EXPECTED_HASHES.keys():
            try:
                spec = importlib.util.find_spec(module_name)
                if spec and spec.origin:
                    critical_files.append({
                        'name': module_name,
                        'path': spec.origin,
                        'protection_level': 'critical'
                    })
            except Exception:
                pass
        
        # Add native extensions
        try:
            import epochly.licensing.native_guard
            if hasattr(epochly.licensing.native_guard, '__file__'):
                critical_files.append({
                    'name': 'native_guard',
                    'path': epochly.licensing.native_guard.__file__,
                    'protection_level': 'critical'
                })
        except Exception:
            pass
        
        # Add license enforcer itself
        critical_files.append({
            'name': 'license_enforcer.py',
            'path': __file__,
            'protection_level': 'critical'
        })
        
        # Add trial system (lazy import to avoid AWS credential loading)
        try:
            import importlib.util
            trial_spec = importlib.util.find_spec('epochly.licensing.trial_system')
            if trial_spec and trial_spec.origin:
                critical_files.append({
                    'name': 'trial_system.py',
                    'path': trial_spec.origin,
                    'protection_level': 'high'
                })
        except Exception:
            pass
        
        return critical_files
    
    def get_critical_files(self) -> List[Dict[str, Any]]:
        """Get list of critical files."""
        return self._critical_files.copy()
    
    def _perform_initial_check(self):
        """Perform initial integrity check on startup (respecting performance optimization)."""
        # Check if we should use fast integrity checks for performance
        use_fast_checks = False
        try:
            import sys
            import os
            benchmarks_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'benchmarks')
            if benchmarks_path not in sys.path:
                sys.path.insert(0, benchmarks_path)

            from performance_optimization import get_performance_optimizer
            optimizer = get_performance_optimizer()

            logger.debug(f"Performance optimizer mode: {optimizer.mode.value}")

            # Only skip integrity checks in benchmark mode (not for regular users)
            if optimizer.mode.value == 'benchmark':
                logger.debug("Skipping integrity checks for benchmark mode only")
                return
            elif optimizer.mode.value == 'production':
                use_fast_checks = True
                logger.debug("Using fast integrity checks for production users")

        except ImportError as e:
            # Performance optimizer not available, use full checks
            logger.debug(f"Performance optimizer not available: {e}")
            pass
        except Exception as e:
            logger.debug(f"Performance optimizer error: {e}")
            pass

        logger.debug(f"use_fast_checks = {use_fast_checks}")

        try:
            if use_fast_checks:
                # STRATEGY 1: TIERED SECURITY MODEL
                # Immediate: Check ONLY license_enforcer.py (critical revenue protection)
                license_enforcer_file = next(
                    (f for f in self._critical_files if 'license_enforcer' in f['name']),
                    None
                )

                if license_enforcer_file and os.path.exists(license_enforcer_file['path']):
                    # IMMEDIATE check for revenue protection (blocks startup)
                    current_hash = self.calculate_file_hash(license_enforcer_file['path'])
                    stored_hash = self.get_stored_hash(license_enforcer_file['path'])

                    if not stored_hash:
                        # First time - store hash
                        self.store_file_hash(license_enforcer_file['path'], current_hash,
                                           license_enforcer_file['protection_level'])
                    elif stored_hash != current_hash:
                        # Handle development vs production differently
                        if self._is_development_environment():
                            logger.info("License enforcer modified during development - expected")
                            # Update stored hash for development
                            self.store_file_hash(license_enforcer_file['path'], current_hash,
                                               license_enforcer_file['protection_level'])
                        else:
                            # Critical tampering in production
                            logger.critical("License enforcer tampering detected - blocking execution")
                            self._log_integrity_event(
                                'critical_tampering_detected',
                                license_enforcer_file['path'],
                                f"License tampering: {current_hash} != {stored_hash}",
                                'critical'
                            )
                            return

                # Background: Check remaining files non-blocking
                remaining_files = [f for f in self._critical_files if 'license_enforcer' not in f['name']]
                if remaining_files:
                    threading.Thread(
                        target=self._background_integrity_check,
                        daemon=True
                    ).start()

                # Start periodic full checks to mitigate mtime spoofing
                self._schedule_periodic_full_check()

            else:
                # FULL INTEGRITY CHECKS for development/admin (comprehensive security)
                for critical_file in self._critical_files:
                    if os.path.exists(critical_file['path']):
                        current_hash = self.calculate_file_hash(critical_file['path'])
                        stored_hash = self.get_stored_hash(critical_file['path'])

                        if not stored_hash:
                            # First time - store hash
                            self.store_file_hash(critical_file['path'], current_hash,
                                               critical_file['protection_level'])
                        elif stored_hash != current_hash:
                            # Handle based on environment
                            if self._is_development_environment():
                                logger.info(f"File {critical_file['name']} modified during development")
                                # Update hash in development
                                self.store_file_hash(critical_file['path'], current_hash,
                                                   critical_file['protection_level'])
                            else:
                                # Potential tampering in production
                                self._log_integrity_event(
                                    'integrity_check_failed',
                                    critical_file['path'],
                                    f"Initial check failed: {current_hash} != {stored_hash}"
                                )
                        
        except Exception as e:
            logger.error(f"Initial integrity check failed: {e}")

    def _quick_integrity_check(self, critical_file: dict) -> bool:
        """Fast integrity check for a single critical file."""
        file_path = critical_file['path']

        try:
            # Simple approach: just check if file exists and get hash
            if not os.path.exists(file_path):
                return False

            current_hash = self.calculate_file_hash(file_path)
            stored_hash = self.get_stored_hash(file_path)

            if not stored_hash:
                # First time - store hash
                self.store_file_hash(file_path, current_hash, critical_file['protection_level'])
                return True

            is_valid = (current_hash == stored_hash)

            if not is_valid:
                self._log_integrity_event(
                    'critical_tampering_detected',
                    file_path,
                    f"License tampering: {current_hash} != {stored_hash}",
                    'critical'
                )

            return is_valid

        except Exception as e:
            logger.error(f"Quick integrity check failed for {file_path}: {e}")
            return False

    def _background_integrity_check(self):
        """Background integrity check for remaining files using fast methods."""
        logger.debug("Starting background integrity verification")

        try:
            # Check remaining files in background (skip license_enforcer.py)
            for critical_file in self._critical_files:
                if 'license_enforcer' in critical_file['name']:
                    continue  # Already checked in foreground

                if os.path.exists(critical_file['path']):
                    # Use fast mtime cache check for background verification
                    is_valid = self._quick_integrity_check_with_mtime_cache(critical_file['path'])

                    if not is_valid:
                        # Background tampering detection
                        severity = 'critical' if critical_file['protection_level'] == 'critical' else 'warning'
                        self._log_integrity_event(
                            'background_tampering_detected',
                            critical_file['path'],
                            'File tampering detected in background check',
                            severity
                        )

                # Small delay to avoid impacting performance
                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Background integrity check failed: {e}")

        logger.debug("Background integrity verification completed")

    def _store_file_mtime_cache(self, file_path: str, mtime: float, hash_value: str, timestamp: float = None):
        """Store file modification time cache for fast future checks."""
        if timestamp is None:
            timestamp = time.time()

        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO file_hashes
                (file_path, expected_hash, cached_mtime, cached_hash, cache_timestamp, protection_level)
                VALUES (?, ?, ?, ?, ?, 'normal')
            """, (file_path, hash_value, mtime, hash_value, timestamp))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.debug(f"Failed to store mtime cache for {file_path}: {e}")

    def _get_file_mtime_cache(self, file_path: str) -> dict:
        """Get cached mtime data for file."""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT cached_mtime, cached_hash, cache_timestamp FROM file_hashes
                WHERE file_path = ?
            """, (file_path,))

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'mtime': float(result[0]) if result[0] else 0.0,
                    'hash': result[1],
                    'timestamp': float(result[2]) if result[2] else 0.0
                }

            return None

        except Exception as e:
            logger.debug(f"Failed to get mtime cache for {file_path}: {e}")
            return None

    def _is_mtime_cache_expired(self, file_path: str, max_age_seconds: int = 3600) -> bool:
        """Check if mtime cache is expired."""
        cached_data = self._get_file_mtime_cache(file_path)
        if not cached_data:
            return True

        age = time.time() - cached_data['timestamp']
        return age > max_age_seconds

    def _quick_integrity_check_with_mtime_cache(self, file_path: str) -> bool:
        """Fast integrity check using mtime caching."""
        try:
            if not os.path.exists(file_path):
                return False

            current_mtime = os.path.getmtime(file_path)

            # Check mtime cache first
            cached_data = self._get_file_mtime_cache(file_path)
            if cached_data and not self._is_mtime_cache_expired(file_path):
                if abs(current_mtime - cached_data['mtime']) < 1.0:
                    # File unchanged, use cached result
                    return True

            # File changed or cache expired, recalculate
            current_hash = self._calculate_file_hash_fast(file_path)
            stored_hash = self.get_stored_hash(file_path)

            if not stored_hash:
                # First time - store hash
                self.store_file_hash(file_path, current_hash, 'normal')
                self._store_file_mtime_cache(file_path, current_mtime, current_hash)
                return True

            is_valid = (current_hash == stored_hash)

            if is_valid:
                # Update cache
                self._store_file_mtime_cache(file_path, current_mtime, current_hash)
            else:
                # Tampering detected
                self._log_integrity_event(
                    'tampering_detected',
                    file_path,
                    f"Hash mismatch: {current_hash} != {stored_hash}",
                    'warning'
                )

            return is_valid

        except Exception as e:
            logger.error(f"mtime cache check failed for {file_path}: {e}")
            return False

    def _periodic_full_integrity_check(self, file_path: str) -> bool:
        """Periodic full integrity check that ignores cache (anti-spoofing)."""
        try:
            current_hash = self.calculate_file_hash(file_path)  # Force SHA256
            stored_hash = self.get_stored_hash(file_path)

            if not stored_hash:
                self.store_file_hash(file_path, current_hash, 'normal')
                return True

            return current_hash == stored_hash

        except Exception as e:
            logger.error(f"Periodic check failed for {file_path}: {e}")
            return False

    def _is_development_environment(self) -> bool:
        """Detect if running in development environment."""
        dev_indicators = [
            'EPOCHLY_DEBUG', 'EPOCHLY_DEV_MODE', 'EPOCHLY_DEVELOPMENT',
            'DEBUG', 'DEVELOPMENT', 'DEV'
        ]

        # Check environment variables
        for indicator in dev_indicators:
            if os.environ.get(indicator, '').lower() in ('1', 'true', 'yes'):
                return True

        # Check for development files in current directory
        dev_files = ['.git', 'setup.py', 'pyproject.toml', 'requirements-dev.txt']
        try:
            current_dir = os.getcwd()
            for dev_file in dev_files:
                if os.path.exists(os.path.join(current_dir, dev_file)):
                    return True
        except:
            pass

        return False

    def _schedule_periodic_full_check(self):
        """Schedule periodic full checks to mitigate mtime spoofing."""
        def periodic_check():
            logger.debug("Running periodic full integrity check (anti-spoofing)")
            try:
                for critical_file in self._critical_files:
                    if os.path.exists(critical_file['path']):
                        is_valid = self._periodic_full_integrity_check(critical_file['path'])
                        if not is_valid:
                            self._log_integrity_event(
                                'periodic_tampering_detected',
                                critical_file['path'],
                                'Tampering detected during periodic check',
                                'critical'
                            )
            except Exception as e:
                logger.error(f"Periodic integrity check failed: {e}")

        # Schedule periodic check every 4 hours
        periodic_interval = 4 * 3600  # 4 hours
        timer = threading.Timer(periodic_interval, periodic_check)
        timer.daemon = True
        timer.start()

        # Schedule next periodic check
        threading.Timer(periodic_interval, self._schedule_periodic_full_check).start()

    def _increment_tamper_count(self, file_path: str):
        """Increment tamper count for a file."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE file_hashes 
            SET tamper_count = tamper_count + 1, last_checked = CURRENT_TIMESTAMP
            WHERE file_path = ?
        """, (file_path,))
        
        conn.commit()
        conn.close()
    
    def _log_integrity_event(self, event_type: str, file_path: str, details: str, severity: str = 'warning'):
        """Log integrity event to database."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO integrity_events (event_type, file_path, details, severity)
            VALUES (?, ?, ?, ?)
        """, (event_type, file_path, details, severity))
        
        conn.commit()
        conn.close()
        
        # Also log to Python logger
        logger.warning(f"Integrity event [{event_type}] {file_path}: {details}")


# Global instance for performance
_global_checker = None

def get_binary_integrity_checker() -> BinaryIntegrityChecker:
    """Get global binary integrity checker instance."""
    global _global_checker
    if _global_checker is None:
        _global_checker = BinaryIntegrityChecker()
    return _global_checker


def verify_epochly_integrity() -> bool:
    """Quick function to verify Epochly integrity."""
    try:
        checker = get_binary_integrity_checker()
        startup_result = checker.quick_startup_check()
        return startup_result['valid']
    except Exception:
        return False


