"""
Global Module Compatibility Registry

Central registry for tracking module compatibility with Epochly features,
particularly sub-interpreters and other optimization techniques.

Author: Epochly Development Team
"""

import os
import sys
import json
import logging
import threading
import importlib.util
from enum import Enum
from typing import Dict, Set, Optional, Any, List, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .local_storage import LocalCompatibilityStorage
from .cloud_sync import CloudCompatibilitySync
from .analyzer import ModuleAnalyzer, ExtensionDetector

logger = logging.getLogger(__name__)


class CompatibilityLevel(Enum):
    """Module compatibility levels with Epochly features"""
    FULL = "full"           # Fully compatible with all features
    PARTIAL = "partial"     # Works with limitations
    NONE = "none"          # Not compatible
    UNKNOWN = "unknown"    # Not yet analyzed
    TESTING = "testing"    # Under observation


@dataclass
class CompatibilityResult:
    """Result of a compatibility check"""
    module_name: str
    level: CompatibilityLevel
    score: float  # 0.0 to 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['level'] = self.level.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompatibilityResult':
        """Create from dictionary"""
        data = data.copy()
        data['level'] = CompatibilityLevel(data['level'])
        return cls(**data)


@dataclass
class ModuleCompatibilityInfo:
    """Detailed compatibility information for a module"""
    module_name: str
    compatible: bool = True
    sub_interpreter_safe: bool = True
    has_c_extensions: bool = False
    failure_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModuleCompatibilityInfo':
        """Create from dictionary"""
        data = data.copy()
        # Handle legacy 'name' field
        if 'name' in data and 'module_name' not in data:
            data['module_name'] = data.pop('name')
        # Ensure metadata is a dict
        if 'metadata' not in data:
            data['metadata'] = {}
        # Remove unknown fields that might exist in old data
        valid_fields = {'module_name', 'compatible', 'sub_interpreter_safe', 'has_c_extensions', 'failure_count', 'metadata'}
        data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**data)


class CompatibilityRegistry:
    """
    Global registry for module compatibility with Epochly features.
    
    This registry maintains:
    - Allowlist: Known compatible modules
    - Denylist: Known incompatible modules  
    - Greylist: Modules under observation
    - Local learning from failures
    - Cloud sync for community data
    """
    
    # Known compatible modules (safe for sub-interpreters)
    DEFAULT_ALLOWLIST = {
        # Standard library modules
        'json', 'math', 'random', 'datetime', 'collections',
        'itertools', 'functools', 'operator', 'decimal',
        'fractions', 'statistics', 'typing', 'dataclasses',
        'enum', 'pathlib', 're', 'string', 'textwrap',
        'hashlib', 'hmac', 'secrets', 'uuid', 'copy',
        'pprint', 'reprlib', 'contextlib', 'abc',
        
        # Pure Python popular packages
        'requests', 'urllib3', 'certifi', 'charset-normalizer',
        'idna', 'six', 'attrs', 'more-itertools',
        'click', 'pyyaml', 'toml', 'tomli', 'packaging',
        'pyparsing', 'python-dateutil', 'pytz',
        
        # Web frameworks (pure Python parts)
        'flask', 'werkzeug', 'jinja2', 'markupsafe',
        'itsdangerous', 'django', 'fastapi', 'starlette',
        'pydantic', 'uvicorn', 'httptools', 'websockets',
        
        # Testing frameworks
        'pytest', 'unittest', 'nose', 'mock', 'coverage',
        'hypothesis', 'tox', 'pytest-cov', 'pytest-mock'
    }
    
    # Known incompatible modules (require main interpreter)
    DEFAULT_DENYLIST = {
        # C extensions with global state
        'numpy', 'scipy', 'pandas', 'matplotlib', 'seaborn',
        'sklearn', 'scikit-learn', 'cv2', 'opencv-python',
        'PIL', 'Pillow', 'tensorflow', 'torch', 'pytorch',
        'jax', 'mxnet', 'theano', 'keras',
        
        # GUI frameworks
        'tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'wxPython', 'kivy', 'pygame', 'pyglet',
        
        # Database drivers with C extensions
        'psycopg2', 'mysqlclient', 'cx_Oracle', 'pymssql',
        
        # System/Hardware interfaces
        'pyserial', 'pyusb', 'pybluez', 'RPi', 'pigpio',
        
        # Multiprocessing/Threading
        'multiprocessing', 'concurrent.futures',
        
        # Other problematic modules
        'h5py', 'netCDF4', 'gdal', 'shapely', 'fiona',
        'cryptography', 'pycrypto', 'bcrypt', 'nacl'
    }
    
    def __init__(self, 
                 storage_path: Optional[Path] = None,
                 enable_cloud_sync: bool = True,
                 enable_learning: bool = True):
        """
        Initialize the compatibility registry.
        
        Args:
            storage_path: Path for local storage (defaults to user data dir)
            enable_cloud_sync: Enable cloud synchronization
            enable_learning: Enable local learning from failures
        """
        self.enable_cloud_sync = enable_cloud_sync
        self.enable_learning = enable_learning
        
        # Initialize storage
        self.storage = LocalCompatibilityStorage(storage_path)
        
        # Initialize cloud sync (if enabled)
        self.cloud_sync = CloudCompatibilitySync() if enable_cloud_sync else None
        
        # Initialize analyzer
        self.analyzer = ModuleAnalyzer()
        self.extension_detector = ExtensionDetector()
        
        # Module lists
        self.allowlist: Set[str] = set()
        self.denylist: Set[str] = set()
        self.greylist: Dict[str, ModuleCompatibilityInfo] = {}
        
        # Caches
        self.compatibility_cache: Dict[str, CompatibilityResult] = {}
        self.module_info_cache: Dict[str, ModuleCompatibilityInfo] = {}
        
        # Thread safety - use RLock for reentrant locking
        self._lock = threading.RLock()
        
        # Load initial data
        self._initialize_lists()
    
    def _initialize_lists(self) -> None:
        """Initialize compatibility lists from defaults and storage"""
        # Start with defaults
        self.allowlist.update(self.DEFAULT_ALLOWLIST)
        self.denylist.update(self.DEFAULT_DENYLIST)
        
        # Load persisted data
        persisted = self.storage.load_all()
        if persisted:
            # Merge persisted allowlist
            if 'allowlist' in persisted:
                self.allowlist.update(persisted['allowlist'])
            
            # Merge persisted denylist
            if 'denylist' in persisted:
                self.denylist.update(persisted['denylist'])
            
            # Load greylist
            if 'greylist' in persisted:
                for name, info_dict in persisted['greylist'].items():
                    self.greylist[name] = ModuleCompatibilityInfo.from_dict(info_dict)
            
            # Load module info cache
            if 'module_info' in persisted:
                for name, info_dict in persisted['module_info'].items():
                    self.module_info_cache[name] = ModuleCompatibilityInfo.from_dict(info_dict)
        
        # Sync with cloud if enabled
        if self.cloud_sync and self.cloud_sync.is_available():
            try:
                cloud_data = self.cloud_sync.fetch_updates()
                if cloud_data:
                    self._merge_cloud_data(cloud_data)
            except Exception as e:
                logger.debug(f"Cloud sync failed during initialization: {e}")
    
    def _merge_cloud_data(self, cloud_data: Dict[str, Any]) -> None:
        """Merge cloud-sourced compatibility data"""
        if not cloud_data:
            return
        
        # Merge verified compatible modules
        if 'verified_compatible' in cloud_data:
            for module in cloud_data['verified_compatible']:
                if module not in self.denylist:  # User overrides take precedence
                    self.allowlist.add(module)
                    logger.debug(f"Added {module} to allowlist from cloud data")
        
        # Merge verified incompatible modules
        if 'verified_incompatible' in cloud_data:
            for module in cloud_data['verified_incompatible']:
                if module not in self.allowlist:  # User overrides take precedence
                    self.denylist.add(module)
                    logger.debug(f"Added {module} to denylist from cloud data")
        
        # Update greylist with observation data
        if 'under_observation' in cloud_data:
            for module, info in cloud_data['under_observation'].items():
                if module not in self.allowlist and module not in self.denylist:
                    if module not in self.greylist:
                        self.greylist[module] = ModuleCompatibilityInfo(
                            module_name=module,
                            compatible=True,
                            sub_interpreter_safe=True,
                            metadata={'notes': [f"Under community observation: {info}"]}
                        )
    
    def check_module(
        self,
        module_name: str,
        force: bool = False,
        force_recheck: bool = False,
        skip_analysis: bool = False
    ) -> CompatibilityResult:
        """
        Check compatibility of a module.

        Args:
            module_name: Name of the module to check
            force: Force recheck (alias for force_recheck)
            force_recheck: Force recheck even if in cache
            skip_analysis: If True, skip slow analysis for unknown modules and
                          assume they are safe. Used for fast bulk scanning.

        Returns:
            CompatibilityResult with compatibility information
        """
        with self._lock:
            # Check cache first (unless forced)
            should_force = force or force_recheck
            if not should_force and module_name in self.compatibility_cache:
                cached = self.compatibility_cache[module_name]
                # Cache for 1 hour
                cache_time = datetime.fromisoformat(cached.timestamp)
                # Ensure both datetimes are timezone-aware for comparison
                if not cache_time.tzinfo:
                    cache_time = cache_time.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) - cache_time < timedelta(hours=1):
                    return cached

            # Check known lists
            if module_name in self.allowlist:
                result = CompatibilityResult(
                    module_name=module_name,
                    level=CompatibilityLevel.FULL,
                    score=1.0,
                    details={'source': 'allowlist'}
                )
            elif module_name in self.denylist:
                result = CompatibilityResult(
                    module_name=module_name,
                    level=CompatibilityLevel.NONE,
                    score=0.0,
                    details={'source': 'denylist',
                            'reason': 'Known incompatible with sub-interpreters'}
                )
            elif module_name in self.greylist:
                info = self.greylist[module_name]
                # Determine level from compatibility flags
                if info.compatible and info.sub_interpreter_safe:
                    level = CompatibilityLevel.FULL
                elif info.compatible:
                    level = CompatibilityLevel.PARTIAL
                else:
                    level = CompatibilityLevel.TESTING

                result = CompatibilityResult(
                    module_name=module_name,
                    level=level,
                    score=0.5,  # Conservative score for greylist
                    details={
                        'source': 'greylist',
                        'failure_count': info.failure_count,
                        'notes': info.metadata.get('notes', []),
                        'metadata': info.metadata
                    }
                )
            elif skip_analysis:
                # Fast path: assume unknown modules are safe (score 0.8)
                # This is used during bulk scanning to avoid slow analysis
                # Actual safety is verified at runtime
                result = CompatibilityResult(
                    module_name=module_name,
                    level=CompatibilityLevel.UNKNOWN,
                    score=0.8,  # Assume safe until proven otherwise
                    details={'source': 'unknown_fast_path', 'analyzed': False}
                )
                # Don't cache fast-path results to allow full analysis later
                return result
            else:
                # Analyze unknown module
                result = self._analyze_module(module_name)

            # Cache result
            self.compatibility_cache[module_name] = result

            return result
    
    def _analyze_module(self, module_name: str) -> CompatibilityResult:
        """Analyze an unknown module for compatibility"""
        try:
            # Check if module can be imported
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                return CompatibilityResult(
                    module_name=module_name,
                    level=CompatibilityLevel.UNKNOWN,
                    score=0.0,
                    details={'error': 'Module not found'}
                )
            
            # Use analyzer to check module
            analysis = self.analyzer.analyze(module_name)
            
            # Check for C extensions
            has_c_extension = self.extension_detector.has_c_extension(module_name)
            
            # Calculate compatibility score
            score = 1.0
            level = CompatibilityLevel.FULL
            details = {
                'has_c_extension': has_c_extension,
                'analysis': analysis
            }
            
            if has_c_extension:
                # C extensions are problematic for sub-interpreters
                score *= 0.3
                level = CompatibilityLevel.PARTIAL
                details['warning'] = 'Has C extension - may not work with sub-interpreters'
                
                # Check if it's a known problematic pattern
                if self.extension_detector.is_unsafe_for_subinterpreters(module_name):
                    score = 0.0
                    level = CompatibilityLevel.NONE
                    details['error'] = 'C extension uses global state - incompatible with sub-interpreters'
            
            # Store module info
            has_c_ext = has_c_extension
            compatible_flag = (level in [CompatibilityLevel.FULL, CompatibilityLevel.PARTIAL])
            sub_interp_safe = (score > 0.5)
            self.module_info_cache[module_name] = ModuleCompatibilityInfo(
                module_name=module_name,
                compatible=compatible_flag,
                sub_interpreter_safe=sub_interp_safe,
                has_c_extensions=has_c_ext,
                metadata={'level': level.value, 'score': score}
            )
            
            return CompatibilityResult(
                module_name=module_name,
                level=level,
                score=score,
                details=details
            )
            
        except Exception as e:
            logger.warning(f"Failed to analyze module {module_name}: {e}")
            return CompatibilityResult(
                module_name=module_name,
                level=CompatibilityLevel.UNKNOWN,
                score=0.5,
                details={'error': str(e)}
            )
    
    def report_failure(self, module_name: str, error_info: Dict[str, Any]) -> None:
        """
        Report a module failure for learning.
        
        Args:
            module_name: Name of the module that failed
            error_info: Information about the failure
        """
        if not self.enable_learning:
            return
        
        with self._lock:
            # Get or create module info
            if module_name in self.module_info_cache:
                info = self.module_info_cache[module_name]
            else:
                info = ModuleCompatibilityInfo(
                    module_name=module_name,
                    compatible=False,
                    sub_interpreter_safe=False,
                    metadata={'reason': 'Unknown module'}
                )
            
            # Update failure information
            info.failure_count += 1
            last_failure_time = datetime.now(timezone.utc).isoformat()
            if 'notes' not in info.metadata:
                info.metadata['notes'] = []
            info.metadata['notes'].append(f"Failure at {last_failure_time}: {error_info.get('error', 'Unknown')}")
            info.metadata['last_failure'] = last_failure_time
            
            # Auto-denylist after 3 failures
            if info.failure_count >= 3:
                logger.warning(f"Module {module_name} failed {info.failure_count} times, adding to denylist")
                self.add_to_denylist(module_name, f"Automatic after {info.failure_count} failures")
                
                # Report to cloud if enabled
                if self.cloud_sync and self.cloud_sync.is_available():
                    try:
                        self.cloud_sync.report_incompatibility(module_name, error_info)
                    except Exception as e:
                        logger.debug(f"Failed to report to cloud: {e}")
            
            # Add to greylist after 1 failure
            elif info.failure_count >= 1:
                info.level = CompatibilityLevel.TESTING
                self.greylist[module_name] = info
            
            # Update cache
            self.module_info_cache[module_name] = info
            
            # Persist changes
            self._persist_changes()
    
    def add_to_allowlist(self, module_name: str, reason: str = "") -> None:
        """Add a module to the allowlist"""
        with self._lock:
            self.allowlist.add(module_name)
            self.denylist.discard(module_name)
            self.greylist.pop(module_name, None)
            
            # Clear cache
            self.compatibility_cache.pop(module_name, None)
            
            # Log reason
            if module_name not in self.module_info_cache:
                self.module_info_cache[module_name] = ModuleCompatibilityInfo(
                    module_name=module_name,
                    compatible=True,
                    sub_interpreter_safe=True,
                    metadata={'reason': reason} if reason else {}
                )
            if 'notes' not in self.module_info_cache[module_name].metadata:
                self.module_info_cache[module_name].metadata['notes'] = []
            self.module_info_cache[module_name].metadata['notes'].append(f"Added to allowlist: {reason}")
            
            # Persist
            self._persist_changes()
    
    def add_to_denylist(self, module_name: str, reason: str = "") -> None:
        """Add a module to the denylist"""
        with self._lock:
            self.denylist.add(module_name)
            self.allowlist.discard(module_name)
            self.greylist.pop(module_name, None)
            
            # Clear cache
            self.compatibility_cache.pop(module_name, None)
            
            # Log reason
            if module_name not in self.module_info_cache:
                self.module_info_cache[module_name] = ModuleCompatibilityInfo(
                    module_name=module_name,
                    compatible=False,
                    sub_interpreter_safe=False,
                    metadata={'reason': reason} if reason else {}
                )
            if 'notes' not in self.module_info_cache[module_name].metadata:
                self.module_info_cache[module_name].metadata['notes'] = []
            self.module_info_cache[module_name].metadata['notes'].append(f"Added to denylist: {reason}")
            
            # Persist
            self._persist_changes()
    
    def is_safe_for_subinterpreter(
        self,
        module_name: str,
        skip_analysis: bool = False
    ) -> bool:
        """
        Quick check if a module is safe for sub-interpreters.

        Args:
            module_name: Module to check
            skip_analysis: If True, skip slow analysis for unknown modules.
                          Use this for fast bulk scanning where unknown modules
                          are assumed safe until proven otherwise.

        Returns:
            True if safe, False otherwise
        """
        result = self.check_module(module_name, skip_analysis=skip_analysis)
        return result.score > 0.7 and result.level != CompatibilityLevel.NONE
    
    def get_unsafe_modules(self) -> Set[str]:
        """Get set of known unsafe modules"""
        return self.denylist.copy()
    
    def get_safe_modules(self) -> Set[str]:
        """Get set of known safe modules"""
        return self.allowlist.copy()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a compatibility report"""
        with self._lock:
            # Calculate total unique modules checked
            total_modules = len(self.allowlist) + len(self.denylist) + len(self.greylist)

            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total_modules': total_modules,
                'safe_count': len(self.allowlist),  # Alias for compatibility
                'unsafe_count': len(self.denylist),  # Alias for denylist
                'unknown_count': len(self.greylist),  # Alias for greylist
                'allowlist_count': len(self.allowlist),
                'denylist_count': len(self.denylist),
                'greylist_count': len(self.greylist),
                'cache_size': len(self.compatibility_cache),
                'allowlist_sample': list(self.allowlist)[:10],
                'denylist_sample': list(self.denylist)[:10],
                'greylist': {name: info.to_dict() for name, info in self.greylist.items()},
                'recent_failures': [
                    info.to_dict() for info in self.module_info_cache.values()
                    if info.failure_count > 0
                ][:10]
            }

    def load_state(self) -> None:
        """
        Explicitly reload state from local storage.

        Useful for:
        - Refreshing after external changes
        - Manual cache invalidation
        - Testing scenarios

        Note: State is automatically loaded on initialization.
        This method allows forcing a reload.
        """
        with self._lock:
            # Clear current state
            self.allowlist.clear()
            self.denylist.clear()
            self.greylist.clear()
            self.compatibility_cache.clear()
            self.module_info_cache.clear()

            # Reload from storage
            self._initialize_lists()

            logger.info("Registry state reloaded from storage")

    def save_state(self) -> None:
        """
        Explicitly save registry state to local storage.

        Note: State is normally auto-persisted on changes via _persist_changes().
        This method allows forcing an immediate save, useful for:
        - Ensuring data is written before shutdown
        - Manual checkpoint creation
        - Testing scenarios
        """
        with self._lock:
            # Prepare data
            data = {
                'allowlist': list(self.allowlist),
                'denylist': list(self.denylist),
                'greylist': {k: v.to_dict() for k, v in self.greylist.items()},
                'module_info': {k: v.to_dict() for k, v in self.module_info_cache.items()},
                'last_updated': datetime.now(timezone.utc).isoformat()
            }

            # Save via storage
            self.storage.save_all(data)

            logger.info("Registry state saved to storage")

    def sync_with_cloud(self, force: bool = False) -> Dict[str, Any]:
        """
        Explicitly sync with cloud compatibility data.

        Args:
            force: Force sync even if recently synced

        Returns:
            Dict with sync results: {'updated': int, 'modules': List[str]}

        Note: Cloud sync happens automatically on initialization.
        This method allows forcing a sync to get latest community data.
        """
        if not self.enable_cloud_sync or not self.cloud_sync:
            logger.debug("Cloud sync not enabled")
            return {'updated': 0, 'modules': []}

        if not self.cloud_sync.is_available():
            logger.debug("Cloud sync not available")
            return {'updated': 0, 'modules': []}

        with self._lock:
            try:
                # Fetch updates from cloud
                cloud_data = self.cloud_sync.fetch_updates(force=force)

                if cloud_data:
                    # Track what was updated
                    updated_modules = []

                    # Merge into local state
                    self._merge_cloud_data(cloud_data)

                    # Auto-persist merged data
                    self._persist_changes()

                    # Extract module list if available
                    if 'verified_compatible' in cloud_data:
                        updated_modules.extend(cloud_data['verified_compatible'])
                    if 'verified_incompatible' in cloud_data:
                        updated_modules.extend(cloud_data['verified_incompatible'])

                    logger.info(f"Synced {len(updated_modules)} modules from cloud")

                    return {
                        'updated': len(updated_modules),
                        'modules': updated_modules
                    }

                return {'updated': 0, 'modules': []}

            except Exception as e:
                logger.error(f"Cloud sync failed: {e}")
                return {'updated': 0, 'modules': [], 'error': str(e)}

    def report_to_cloud(self, module_name: str, compatibility_data: Dict[str, Any]) -> bool:
        """
        Report module compatibility data to cloud.

        Args:
            module_name: Name of module
            compatibility_data: Compatibility information to report

        Returns:
            bool: True if reported successfully

        Allows contributing compatibility findings to the community database.
        """
        if not self.enable_cloud_sync or not self.cloud_sync:
            logger.debug("Cloud sync not enabled, cannot report")
            return False

        if not self.cloud_sync.is_available():
            logger.debug("Cloud sync not available")
            return False

        try:
            # Report via cloud sync client
            result = self.cloud_sync.report_compatibility(module_name, compatibility_data)

            if result and result.get('success', False):
                logger.info(f"Successfully reported {module_name} to cloud")
                return True
            else:
                logger.warning(f"Failed to report {module_name} to cloud: {result}")
                return False

        except Exception as e:
            logger.error(f"Failed to report to cloud: {e}")
            return False

    def _persist_changes(self) -> None:
        """Persist current state to storage"""
        try:
            data = {
                'allowlist': list(self.allowlist),
                'denylist': list(self.denylist),
                'greylist': {name: info.to_dict() for name, info in self.greylist.items()},
                'module_info': {name: info.to_dict() for name, info in self.module_info_cache.items()}
            }
            self.storage.save_all(data)
        except Exception as e:
            logger.error(f"Failed to persist compatibility data: {e}")


# Global registry instance
_global_registry: Optional[CompatibilityRegistry] = None
_registry_lock = threading.Lock()


def get_global_registry() -> CompatibilityRegistry:
    """
    Get the global compatibility registry instance.
    
    Returns:
        The global CompatibilityRegistry instance
    """
    global _global_registry
    
    if _global_registry is None:
        with _registry_lock:
            if _global_registry is None:
                _global_registry = CompatibilityRegistry()
    
    return _global_registry