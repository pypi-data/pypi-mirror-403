"""
Epochly Path Validator

Provides path validation and security checks to prevent path traversal attacks
and ensure secure file operations.

Author: Epochly Development Team
"""

import os
import pathlib
from typing import Union, Optional
from ..utils.logger import get_logger
from ..utils.exceptions import EpochlyError


class PathValidator:
    """
    Validates file paths and prevents path traversal attacks.
    
    Provides mechanisms for:
    - Path traversal detection and prevention
    - Secure path normalization
    - Allowed directory validation
    - Path sanitization
    """
    
    def __init__(self, allowed_base_paths: Optional[list] = None):
        """
        Initialize path validator.
        
        Args:
            allowed_base_paths: List of allowed base paths for operations
        """
        self.logger = get_logger(__name__)
        self.allowed_base_paths = allowed_base_paths or []
        
        # Normalize allowed base paths
        self.normalized_base_paths = []
        for path in self.allowed_base_paths:
            try:
                normalized = pathlib.Path(path).resolve()
                self.normalized_base_paths.append(normalized)
            except Exception as e:
                self.logger.warning(f"Failed to normalize base path {path}: {e}")
    
    def sanitize_path(self, path: Union[str, pathlib.Path]) -> str:
        """
        Sanitize a file path by removing dangerous characters and sequences.

        Args:
            path: Path to sanitize

        Returns:
            Sanitized path string

        Raises:
            EpochlyError: If path contains dangerous patterns that would escape
                         allowed directories after resolution
        """
        if isinstance(path, pathlib.Path):
            path_str = str(path)
        else:
            path_str = str(path)

        # Remove null bytes and other dangerous characters
        sanitized = path_str.replace('\x00', '').replace('\r', '').replace('\n', '')

        # Check for home directory expansion attempts
        if sanitized.startswith('~/') or sanitized.startswith('~\\'):
            raise EpochlyError(f"Path contains home directory expansion: {path_str}")

        # Instead of substring matching, check if resolved path stays within bounds
        # This allows legitimate filenames like 'backup..old' or '.hidden' while
        # still detecting actual traversal attempts
        if self.allowed_base_paths:
            try:
                resolved = pathlib.Path(sanitized).resolve()
                if not self._is_within_allowed_bases(resolved):
                    raise EpochlyError(f"Path escapes allowed directories after resolution: {path_str}")
            except OSError as e:
                raise EpochlyError(f"Failed to resolve path for security check: {path_str}: {e}")
        else:
            # No base path restrictions, but still check for obvious traversal components
            # Split on both forward and back slashes to get path parts
            parts = sanitized.replace('\\', '/').split('/')
            # Only reject if '..' appears as a standalone path component
            # This allows filenames like 'backup..old' but rejects '../../../etc/passwd'
            if '..' in parts:
                raise EpochlyError(f"Path contains parent directory traversal component: {path_str}")

        # Check for absolute paths that might escape containment
        if os.path.isabs(sanitized) and self.allowed_base_paths:
            # Verify absolute path is within allowed bases
            if not self._is_within_allowed_bases(sanitized):
                raise EpochlyError(f"Absolute path not within allowed bases: {path_str}")

        return sanitized
    
    def validate_path(self, path: Union[str, pathlib.Path], 
                     must_exist: bool = False,
                     must_be_file: bool = False,
                     must_be_dir: bool = False) -> pathlib.Path:
        """
        Validate and normalize a file path.
        
        Args:
            path: Path to validate
            must_exist: Whether path must exist
            must_be_file: Whether path must be a file
            must_be_dir: Whether path must be a directory
            
        Returns:
            Validated and normalized Path object
            
        Raises:
            EpochlyError: If path validation fails
        """
        try:
            # Sanitize first
            sanitized_str = self.sanitize_path(path)
            
            # Convert to Path and resolve
            path_obj = pathlib.Path(sanitized_str)
            
            # Resolve to absolute path to detect traversal attempts
            try:
                resolved_path = path_obj.resolve()
            except Exception as e:
                raise EpochlyError(f"Failed to resolve path {sanitized_str}: {e}")
            
            # Check if resolved path is within allowed bases
            if self.allowed_base_paths and not self._is_within_allowed_bases(resolved_path):
                raise EpochlyError(f"Path outside allowed directories: {resolved_path}")
            
            # Existence checks
            if must_exist and not resolved_path.exists():
                raise EpochlyError(f"Path does not exist: {resolved_path}")
            
            if must_be_file and resolved_path.exists() and not resolved_path.is_file():
                raise EpochlyError(f"Path is not a file: {resolved_path}")
            
            if must_be_dir and resolved_path.exists() and not resolved_path.is_dir():
                raise EpochlyError(f"Path is not a directory: {resolved_path}")
            
            return resolved_path
            
        except EpochlyError:
            raise
        except Exception as e:
            raise EpochlyError(f"Path validation failed for {path}: {e}")
    
    def _is_within_allowed_bases(self, path: Union[str, pathlib.Path]) -> bool:
        """
        Check if path is within allowed base directories.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is within allowed bases, False otherwise
        """
        if not self.normalized_base_paths:
            return True  # No restrictions if no base paths specified
        
        try:
            if isinstance(path, str):
                path_obj = pathlib.Path(path).resolve()
            else:
                path_obj = path.resolve()
            
            # Check if path is within any allowed base
            for base_path in self.normalized_base_paths:
                try:
                    # Check if path is relative to base (i.e., within it)
                    path_obj.relative_to(base_path)
                    return True
                except ValueError:
                    # Path is not relative to this base, try next
                    continue
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Failed to check path containment for {path}: {e}")
            return False
    
    def secure_join(self, base: Union[str, pathlib.Path], 
                   *paths: Union[str, pathlib.Path]) -> pathlib.Path:
        """
        Securely join paths, preventing traversal attacks.
        
        Args:
            base: Base directory path
            *paths: Path components to join
            
        Returns:
            Securely joined path
            
        Raises:
            EpochlyError: If join would result in path traversal
        """
        try:
            # Validate base path
            base_path = self.validate_path(base)
            
            # Build joined path step by step
            current_path = base_path
            
            for path_component in paths:
                # Sanitize each component
                sanitized_component = self.sanitize_path(path_component)
                
                # Join with current path
                new_path = current_path / sanitized_component
                
                # Resolve and check it's still within base
                resolved_new = new_path.resolve()
                
                # Ensure we haven't escaped the base directory
                try:
                    resolved_new.relative_to(base_path.resolve())
                except ValueError:
                    raise EpochlyError(f"Path component '{path_component}' would escape base directory")
                
                current_path = resolved_new
            
            return current_path
            
        except EpochlyError:
            raise
        except Exception as e:
            raise EpochlyError(f"Secure join failed: {e}")
    
    def is_safe_filename(self, filename: str) -> bool:
        """
        Check if filename is safe (no path separators or dangerous characters).
        
        Args:
            filename: Filename to check
            
        Returns:
            True if filename is safe, False otherwise
        """
        if not filename or filename in ('.', '..'):
            return False
        
        # Check for path separators
        if os.sep in filename or os.altsep and os.altsep in filename:
            return False
        
        # Check for dangerous characters
        dangerous_chars = '\x00\r\n<>:"|?*'
        if any(char in filename for char in dangerous_chars):
            return False
        
        # Check for reserved names on Windows
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        name_upper = filename.upper()
        if name_upper in reserved_names or name_upper.split('.')[0] in reserved_names:
            return False
        
        return True