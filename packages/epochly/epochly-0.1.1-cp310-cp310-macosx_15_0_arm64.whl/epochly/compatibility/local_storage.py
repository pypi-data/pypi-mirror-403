"""
Local Storage for Compatibility Data

Handles persistent storage of compatibility information using JSON files.
Future versions will support DynamoDB backend for centralized storage.

Author: Epochly Development Team
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import threading

logger = logging.getLogger(__name__)


class LocalCompatibilityStorage:
    """
    Local file-based storage for compatibility data.
    
    Stores compatibility information in JSON files in the user's data directory.
    This provides persistence across sessions and allows user overrides.
    """
    
    def __init__(self, storage_path: Optional[Path] = None, storage_dir: Optional[Path] = None):
        """
        Initialize local storage.
        
        Args:
            storage_path: Optional custom storage path (kept for backward compatibility)
            storage_dir: Optional custom storage directory (preferred)
        """
        # Handle both storage_path and storage_dir for compatibility
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        elif storage_path:
            self.storage_dir = Path(storage_path)
        else:
            self.storage_dir = self._get_default_storage_dir()
        
        # Ensure directory exists - handle permission errors gracefully
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            # Fall back to a temp directory if we can't create the requested one
            import tempfile
            logger.warning(f"Cannot create storage directory {self.storage_dir}: {e}")
            self.storage_dir = Path(tempfile.mkdtemp(prefix="epochly_compat_"))
            logger.info(f"Using temporary directory: {self.storage_dir}")
        
        # File paths
        self.registry_file = self.storage_dir / "compatibility_registry.json"
        self.overrides_file = self.storage_dir / "user_overrides.json"
        self.learning_file = self.storage_dir / "learned_data.json"
        self.metrics_file = self.storage_dir / "metrics.json"
        
        # Thread safety - use RLock for reentrant locking
        self._lock = threading.RLock()
    
    def _get_default_storage_dir(self) -> Path:
        """Get platform-specific default storage directory"""
        if sys.platform == 'win32':
            # Windows: %APPDATA%/Epochly/compatibility
            base = os.environ.get('APPDATA', os.path.expanduser('~'))
            return Path(base) / 'Epochly' / 'compatibility'
        elif sys.platform == 'darwin':
            # macOS: ~/Library/Application Support/Epochly/compatibility
            return Path.home() / 'Library' / 'Application Support' / 'Epochly' / 'compatibility'
        else:
            # Linux/Unix: ~/.local/share/epochly/compatibility
            base = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
            return Path(base) / 'epochly' / 'compatibility'
    
    def load_all(self) -> Dict[str, Any]:
        """
        Load all stored compatibility data.
        
        Returns:
            Dictionary containing all stored data
        """
        with self._lock:
            data = {}
            
            # Load registry data
            if self.registry_file.exists():
                try:
                    with open(self.registry_file, 'r') as f:
                        registry_data = json.load(f)
                        data.update(registry_data)
                except Exception as e:
                    logger.warning(f"Failed to load registry file: {e}")
            
            # Load user overrides (these take precedence)
            if self.overrides_file.exists():
                try:
                    with open(self.overrides_file, 'r') as f:
                        overrides = json.load(f)
                        
                        # Apply overrides
                        if 'force_allow' in overrides:
                            if 'allowlist' not in data:
                                data['allowlist'] = []
                            data['allowlist'].extend(overrides['force_allow'])
                            
                            # Remove from denylist if present
                            if 'denylist' in data:
                                data['denylist'] = [m for m in data['denylist'] 
                                                   if m not in overrides['force_allow']]
                        
                        if 'force_deny' in overrides:
                            if 'denylist' not in data:
                                data['denylist'] = []
                            data['denylist'].extend(overrides['force_deny'])
                            
                            # Remove from allowlist if present
                            if 'allowlist' in data:
                                data['allowlist'] = [m for m in data['allowlist']
                                                   if m not in overrides['force_deny']]
                                
                except Exception as e:
                    logger.warning(f"Failed to load overrides file: {e}")
            
            # Load learned data
            if self.learning_file.exists():
                try:
                    with open(self.learning_file, 'r') as f:
                        learned = json.load(f)
                        
                        # Merge learned data
                        if 'greylist' in learned:
                            if 'greylist' not in data:
                                data['greylist'] = {}
                            data['greylist'].update(learned['greylist'])
                        
                        if 'module_info' in learned:
                            if 'module_info' not in data:
                                data['module_info'] = {}
                            data['module_info'].update(learned['module_info'])
                            
                except Exception as e:
                    logger.warning(f"Failed to load learning file: {e}")
            
            return data
    
    def save_all(self, data: Dict[str, Any]) -> None:
        """
        Save all compatibility data.
        
        Args:
            data: Dictionary containing all data to save
        """
        with self._lock:
            try:
                # Prepare registry data
                registry_data = {
                    'version': '1.0',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'allowlist': data.get('allowlist', []),
                    'denylist': data.get('denylist', [])
                }
                
                # Save registry file
                with open(self.registry_file, 'w') as f:
                    json.dump(registry_data, f, indent=2)
                
                # Save learned data separately
                if 'greylist' in data or 'module_info' in data:
                    learned_data = {
                        'version': '1.0',
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'greylist': data.get('greylist', {}),
                        'module_info': data.get('module_info', {})
                    }
                    
                    with open(self.learning_file, 'w') as f:
                        json.dump(learned_data, f, indent=2)
                
                logger.debug(f"Saved compatibility data to {self.storage_dir}")
                
            except Exception as e:
                logger.error(f"Failed to save compatibility data: {e}")
                raise
    
    def load_user_overrides(self) -> Dict[str, Any]:
        """
        Load user-defined overrides.
        
        Returns:
            Dictionary of user overrides
        """
        with self._lock:
            if self.overrides_file.exists():
                try:
                    with open(self.overrides_file, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load user overrides: {e}")
            
            return {}
    
    def save_user_overrides(self, overrides: Dict[str, Any]) -> None:
        """
        Save user-defined overrides.
        
        Args:
            overrides: Dictionary of overrides to save
        """
        with self._lock:
            try:
                override_data = {
                    'version': '1.0',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    **overrides
                }
                
                with open(self.overrides_file, 'w') as f:
                    json.dump(override_data, f, indent=2)
                    
                logger.info(f"Saved user overrides to {self.overrides_file}")
                
            except Exception as e:
                logger.error(f"Failed to save user overrides: {e}")
                raise
    
    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Update stored metrics.
        
        Args:
            metrics: Metrics data to store
        """
        with self._lock:
            try:
                # Load existing metrics
                existing = {}
                if self.metrics_file.exists():
                    try:
                        with open(self.metrics_file, 'r') as f:
                            existing = json.load(f)
                    except:
                        pass
                
                # Update with new metrics
                existing['last_updated'] = datetime.now(timezone.utc).isoformat()
                existing.update(metrics)
                
                # Save updated metrics
                with open(self.metrics_file, 'w') as f:
                    json.dump(existing, f, indent=2)
                    
            except Exception as e:
                logger.warning(f"Failed to update metrics: {e}")
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about storage usage.
        
        Returns:
            Dictionary with storage information
        """
        info = {
            'storage_dir': str(self.storage_dir),
            'files': {}
        }
        
        for file_name, file_path in [
            ('registry', self.registry_file),
            ('overrides', self.overrides_file),
            ('learning', self.learning_file),
            ('metrics', self.metrics_file)
        ]:
            if file_path.exists():
                stat = file_path.stat()
                info['files'][file_name] = {
                    'exists': True,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            else:
                info['files'][file_name] = {'exists': False}
        
        return info
    
    def clear_all(self) -> None:
        """Clear all stored data (use with caution)"""
        with self._lock:
            for file_path in [self.registry_file, self.overrides_file, 
                            self.learning_file, self.metrics_file]:
                if file_path.exists():
                    try:
                        file_path.unlink()
                        logger.info(f"Deleted {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}: {e}")


# NOTE: DynamoDB access is handled through api.epochly.com
# See epochly.compatibility.api_backend.APICompatibilityBackend
# Direct DynamoDB access has been removed in favor of the API pattern