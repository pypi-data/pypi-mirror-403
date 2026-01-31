"""
Epochly Sitecustomize Installer

Manages installation and removal of sitecustomize.py for transparent Epochly activation.
Handles conflicts with existing sitecustomize.py files and provides backup/restore functionality.

Author: Epochly Development Team
"""

import os
import sys
import shutil
import tempfile
import threading
import contextlib
from typing import Optional, List, Dict, Any
import importlib.util
import ast

from ..utils.logger import get_logger
from ..utils.exceptions import EpochlyError
from ..security.security_manager import SecurityManager


class SitecustomizeInstaller:
    """
    Manages installation and removal of sitecustomize.py for transparent Epochly activation.
    
    Provides mechanisms for:
    - Installing Epochly sitecustomize.py
    - Handling conflicts with existing sitecustomize.py
    - Backup and restore functionality
    - Validation of sitecustomize.py integrity
    """
    
    def __init__(self, security_config: Optional[Dict[str, Any]] = None):
        """Initialize sitecustomize installer with security features."""
        self.logger = get_logger(__name__)
        self._backup_dir = self._get_backup_directory()
        self._sitecustomize_template = self._get_sitecustomize_template()
        self._file_lock = threading.RLock()
        
        # Initialize security manager
        self.security_manager = SecurityManager(security_config)
        
        # Set up secure environment
        if not self.security_manager.secure_environment_setup():
            self.logger.warning("Security environment setup had issues - proceeding with caution")
    
    def _get_backup_directory(self) -> str:
        """Get directory for storing backups."""
        backup_dir = os.path.join(os.path.expanduser('~'), '.epochly', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir
    
    def _get_sitecustomize_template(self) -> str:
        """Get the sitecustomize.py template for Epochly."""
        return '''"""
Epochly Sitecustomize Module

This module is automatically installed by Epochly to enable transparent activation.
It initializes Epochly when Python starts up, allowing for seamless optimization.

WARNING: This file is managed by Epochly. Manual modifications may be overwritten.
"""

import sys
import os

# Epochly initialization flag to prevent double initialization
_epochly_initialized = False

def _initialize_epochly():
    """Initialize Epochly if conditions are met."""
    global _epochly_initialized
    
    if _epochly_initialized:
        return
    
    try:
        # Check if Epochly should be activated
        from epochly.deployment.deployment_controller import DeploymentController
        from epochly.deployment.activation_manager import ActivationManager
        
        controller = DeploymentController()
        if controller.should_activate():
            # Initialize activation manager
            activation_manager = ActivationManager(controller)
            
            # Store reference for later use
            sys._epochly_activation_manager = activation_manager
            
            # Activate for main module if appropriate
            main_module = getattr(sys.modules.get('__main__'), '__file__', '')
            if main_module:
                context = {
                    'script_path': main_module,
                    'module_name': '__main__'
                }
                activation_manager.activate_module('__main__', context)
        
        _epochly_initialized = True
        
    except Exception as e:
        # Silently fail to avoid breaking Python startup
        # Log to stderr if possible
        try:
            import sys
            print(f"Epochly initialization failed: {e}", file=sys.stderr)
        except:
            pass

# Initialize Epochly
_initialize_epochly()

# Original sitecustomize content (if any) will be appended below
# --- Epochly ORIGINAL CONTENT MARKER ---
'''
    
    @contextlib.contextmanager
    def _atomic_file_operation(self, file_path: str):
        """
        Context manager for atomic file operations with path validation.
        
        Ensures file operations are atomic by using temporary files
        and atomic moves, with proper locking, cleanup, and security validation.
        
        Args:
            file_path: Path to the target file
            
        Yields:
            Temporary file path for writing
        """
        with self._file_lock:
            # Validate file path for security
            validated_path = self.security_manager.path_validator.validate_path(file_path)
            
            # Create temporary file in same directory as target
            target_dir = os.path.dirname(validated_path)
            if not target_dir:
                target_dir = '.'
            
            # Ensure target directory exists with secure permissions
            os.makedirs(target_dir, exist_ok=True)
            self.security_manager.file_security.set_secure_permissions(target_dir, is_private=False)
            
            # Create temporary file with secure permissions
            temp_fd, temp_path = tempfile.mkstemp(
                dir=target_dir,
                prefix='.epochly_temp_',
                suffix='.py'
            )
            
            try:
                # Close the file descriptor, we'll use the path
                os.close(temp_fd)
                
                # Set secure permissions on temporary file
                self.security_manager.file_security.set_secure_permissions(temp_path)
                
                yield temp_path
                
                # Atomic move on completion
                if os.path.exists(temp_path):
                    # On Windows, need to remove target first if it exists
                    if os.name == 'nt' and os.path.exists(validated_path):
                        os.remove(validated_path)
                    
                    # Atomic move
                    shutil.move(temp_path, validated_path)
                    self.logger.debug(f"Atomically moved {temp_path} to {validated_path}")
                    
            except Exception as e:
                # Clean up temporary file on error
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except Exception as cleanup_error:
                    self.logger.warning(f"Failed to cleanup temp file {temp_path}: {cleanup_error}")
                raise e
    
    def _atomic_backup_operation(self, source_path: str, backup_path: str) -> None:
        """
        Perform atomic backup operation.
        
        Args:
            source_path: Path to source file
            backup_path: Path to backup destination
        """
        with self._file_lock:
            # Ensure backup directory exists
            backup_dir = os.path.dirname(backup_path)
            os.makedirs(backup_dir, exist_ok=True)
            
            # Use atomic file operation for backup
            with self._atomic_file_operation(backup_path) as temp_backup:
                shutil.copy2(source_path, temp_backup)
                self.logger.debug(f"Atomically backed up {source_path} to {backup_path}")
    
    def _atomic_read_operation(self, file_path: str) -> str:
        """
        Perform atomic read operation with proper locking.
        
        Args:
            file_path: Path to file to read
            
        Returns:
            File content as string
        """
        with self._file_lock:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"Failed to read file {file_path}: {e}")
                raise
    
    def get_site_packages_paths(self) -> List[str]:
        """Get all site-packages directories where sitecustomize.py could be installed."""
        paths = []
        
        # Get standard site-packages paths
        import site
        paths.extend(site.getsitepackages())
        
        # Add user site-packages
        user_site = site.getusersitepackages()
        if user_site:
            paths.append(user_site)
        
        # Add current working directory's site-packages if in virtual environment
        if hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix:
            venv_site = os.path.join(sys.prefix, 'lib', 'python{}.{}'.format(*sys.version_info[:2]), 'site-packages')
            if os.path.exists(venv_site):
                paths.append(venv_site)
        
        # Remove duplicates and ensure directories exist
        unique_paths = []
        for path in paths:
            if path and os.path.isdir(path) and path not in unique_paths:
                unique_paths.append(path)
        
        return unique_paths
    
    def find_existing_sitecustomize(self) -> Optional[str]:
        """
        Find existing sitecustomize.py file.
        
        Returns:
            Path to existing sitecustomize.py or None if not found
        """
        for site_path in self.get_site_packages_paths():
            sitecustomize_path = os.path.join(site_path, 'sitecustomize.py')
            if os.path.exists(sitecustomize_path):
                return sitecustomize_path
        return None
    
    def is_epochly_sitecustomize(self, sitecustomize_path: str) -> bool:
        """
        Check if sitecustomize.py was created by Epochly.
        
        Args:
            sitecustomize_path: Path to sitecustomize.py file
            
        Returns:
            True if file was created by Epochly, False otherwise
        """
        try:
            content = self._atomic_read_operation(sitecustomize_path)
            
            # Check for Epochly markers
            return ('Epochly Sitecustomize Module' in content and
                    '_initialize_epochly' in content and
                    'Epochly ORIGINAL CONTENT MARKER' in content)
        except Exception as e:
            self.logger.warning(f"Failed to check sitecustomize.py: {e}")
            return False
    
    def backup_existing_sitecustomize(self, sitecustomize_path: str) -> str:
        """
        Create secure backup of existing sitecustomize.py with integrity hash.
        
        Args:
            sitecustomize_path: Path to existing sitecustomize.py
            
        Returns:
            Path to backup file
        """
        import time
        timestamp = int(time.time())
        backup_filename = f"sitecustomize_backup_{timestamp}.py"
        
        # Use secure backup with integrity hash - pass directory and filename separately
        backup_result = self.security_manager.file_security.secure_backup_with_hash(
            sitecustomize_path, self._backup_dir, backup_filename
        )
        
        backup_path = backup_result['backup_path']
        self.logger.info(f"Backed up sitecustomize.py to: {backup_path}")
        self.logger.debug(f"Backup integrity hash: {backup_result['hash']}")
        
        return backup_path
    
    def extract_original_content(self, sitecustomize_path: str) -> str:
        """
        Extract original content from Epochly-managed sitecustomize.py using atomic operations.
        
        Args:
            sitecustomize_path: Path to Epochly sitecustomize.py
            
        Returns:
            Original content that was preserved
        """
        try:
            content = self._atomic_read_operation(sitecustomize_path)
            
            marker = '# --- Epochly ORIGINAL CONTENT MARKER ---'
            if marker in content:
                parts = content.split(marker, 1)
                if len(parts) > 1:
                    return parts[1].strip()
            
            return ''
        except Exception as e:
            self.logger.warning(f"Failed to extract original content: {e}")
            return ''
    
    def create_epochly_sitecustomize(self, target_path: str, original_content: str = '') -> None:
        """
        Create Epochly sitecustomize.py file using atomic operations.
        
        Args:
            target_path: Path where to create sitecustomize.py
            original_content: Original content to preserve
        """
        content = self._sitecustomize_template
        
        if original_content.strip():
            content += '\n' + original_content
        
        # Use atomic file operation for creation
        with self._atomic_file_operation(target_path) as temp_path:
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        self.logger.info(f"Created Epochly sitecustomize.py at: {target_path}")
    
    def install(self, force: bool = False, preserve_existing: bool = True) -> bool:
        """
        Install Epochly sitecustomize.py.
        
        Args:
            force: Force installation even if conflicts exist
            preserve_existing: Preserve existing sitecustomize.py content
            
        Returns:
            True if installation was successful, False otherwise
        """
        try:
            # Find target installation path
            site_paths = self.get_site_packages_paths()
            if not site_paths:
                raise EpochlyError("No site-packages directories found")
            
            # Prefer user site-packages for installation
            import site
            target_dir = site.getusersitepackages()
            if not target_dir or not os.access(os.path.dirname(target_dir), os.W_OK):
                # Fall back to first writable site-packages
                target_dir = None
                for path in site_paths:
                    if os.access(path, os.W_OK):
                        target_dir = path
                        break
            
            if not target_dir:
                raise EpochlyError("No writable site-packages directory found")
            
            # Ensure target directory exists
            os.makedirs(target_dir, exist_ok=True)
            
            target_path = os.path.join(target_dir, 'sitecustomize.py')
            
            # Check for existing sitecustomize.py
            existing_path = self.find_existing_sitecustomize()
            original_content = ''
            
            if existing_path:
                if self.is_epochly_sitecustomize(existing_path):
                    self.logger.info("Epochly sitecustomize.py already installed")
                    return True
                
                if not force:
                    raise EpochlyError(f"Existing sitecustomize.py found at {existing_path}. Use force=True to override.")
                
                if preserve_existing:
                    # Backup existing file
                    self.backup_existing_sitecustomize(existing_path)
                    
                    # Read original content using atomic operation
                    original_content = self._atomic_read_operation(existing_path)
            
            # Create Epochly sitecustomize.py
            self.create_epochly_sitecustomize(target_path, original_content)
            
            # Validate installation
            if self.validate_installation():
                self.logger.info("Epochly sitecustomize.py installed successfully")
                return True
            else:
                raise EpochlyError("Installation validation failed")
                
        except Exception as e:
            self.logger.error(f"Failed to install sitecustomize.py: {e}")
            return False
    
    def uninstall(self, restore_backup: bool = True) -> bool:
        """
        Uninstall Epochly sitecustomize.py.
        
        Args:
            restore_backup: Restore original sitecustomize.py from backup
            
        Returns:
            True if uninstallation was successful, False otherwise
        """
        try:
            existing_path = self.find_existing_sitecustomize()
            if not existing_path:
                self.logger.info("No sitecustomize.py found")
                return True
            
            if not self.is_epochly_sitecustomize(existing_path):
                self.logger.warning("Existing sitecustomize.py was not created by Epochly")
                return False
            
            # Extract original content
            original_content = self.extract_original_content(existing_path)
            
            # Remove Epochly sitecustomize.py
            os.remove(existing_path)
            self.logger.info(f"Removed Epochly sitecustomize.py from: {existing_path}")
            
            # Restore original content if it exists and restore_backup is True
            if restore_backup and original_content.strip():
                with self._atomic_file_operation(existing_path) as temp_path:
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                self.logger.info("Restored original sitecustomize.py content")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to uninstall sitecustomize.py: {e}")
            return False
    
    def validate_installation(self) -> bool:
        """
        Validate that Epochly sitecustomize.py is properly installed.
        
        Returns:
            True if installation is valid, False otherwise
        """
        try:
            existing_path = self.find_existing_sitecustomize()
            if not existing_path:
                return False
            
            if not self.is_epochly_sitecustomize(existing_path):
                return False
            
            # Try to parse the file to ensure it's valid Python
            content = self._atomic_read_operation(existing_path)
            
            try:
                ast.parse(content)
            except SyntaxError as e:
                self.logger.error(f"Sitecustomize.py has syntax errors: {e}")
                return False
            
            # Check if file is importable
            spec = importlib.util.spec_from_file_location("sitecustomize", existing_path)
            if spec is None:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return False
    
    def get_installation_status(self) -> Dict[str, Any]:
        """
        Get current installation status.
        
        Returns:
            Dictionary with installation status information
        """
        existing_path = self.find_existing_sitecustomize()
        
        status = {
            'installed': False,
            'epochly_managed': False,
            'path': existing_path,
            'valid': False,
            'site_packages_paths': self.get_site_packages_paths(),
            'backup_directory': self._backup_dir
        }
        
        if existing_path:
            status['installed'] = True
            status['epochly_managed'] = self.is_epochly_sitecustomize(existing_path)
            status['valid'] = self.validate_installation()
        
        return status
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List available backup files.
        
        Returns:
            List of backup file information
        """
        backups = []
        
        try:
            if os.path.exists(self._backup_dir):
                for filename in os.listdir(self._backup_dir):
                    if filename.startswith('sitecustomize_backup_') and filename.endswith('.py'):
                        backup_path = os.path.join(self._backup_dir, filename)
                        stat = os.stat(backup_path)
                        
                        backups.append({
                            'filename': filename,
                            'path': backup_path,
                            'size': stat.st_size,
                            'created': stat.st_ctime,
                            'modified': stat.st_mtime
                        })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """
        Restore sitecustomize.py from a backup file.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if restore was successful, False otherwise
        """
        try:
            if not os.path.exists(backup_path):
                raise EpochlyError(f"Backup file not found: {backup_path}")
            
            # Find current sitecustomize.py location
            current_path = self.find_existing_sitecustomize()
            if not current_path:
                # Use user site-packages as default
                import site
                target_dir = site.getusersitepackages()
                os.makedirs(target_dir, exist_ok=True)
                current_path = os.path.join(target_dir, 'sitecustomize.py')
            
            # Copy backup to current location
            shutil.copy2(backup_path, current_path)
            self.logger.info(f"Restored sitecustomize.py from backup: {backup_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore from backup: {e}")
            return False