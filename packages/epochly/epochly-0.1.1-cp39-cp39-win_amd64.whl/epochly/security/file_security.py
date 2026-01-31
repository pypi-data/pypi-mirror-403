"""
Epochly File Security Manager

Provides secure file operations with proper permissions, integrity checks,
and security hardening mechanisms.

Author: Epochly Development Team
"""

import os
import hashlib
import shutil
from typing import Optional, Dict, Any, Union
from pathlib import Path
from ..utils.logger import get_logger
from ..utils.exceptions import EpochlyError
from .path_validator import PathValidator


class FileSecurityManager:
    """
    Manages secure file operations with proper permissions and integrity checks.
    
    Provides mechanisms for:
    - Secure file permissions (0o644 for files, 0o755 for dirs)
    - File integrity verification with hashes
    - Secure temporary file operations
    - Environment variable sanitization
    """
    
    # Secure file permissions
    SECURE_FILE_MODE = 0o644  # rw-r--r--
    SECURE_DIR_MODE = 0o755   # rwxr-xr-x
    PRIVATE_FILE_MODE = 0o600 # rw-------
    PRIVATE_DIR_MODE = 0o700  # rwx------
    
    def __init__(self, allowed_base_paths: Optional[list] = None):
        """
        Initialize file security manager.
        
        Args:
            allowed_base_paths: List of allowed base paths for operations
        """
        self.logger = get_logger(__name__)
        self.path_validator = PathValidator(allowed_base_paths)
    
    def set_secure_permissions(self, path: Union[str, Path], 
                             is_private: bool = False) -> None:
        """
        Set secure permissions on a file or directory.
        
        Args:
            path: Path to file or directory
            is_private: Whether to use private permissions (owner only)
            
        Raises:
            EpochlyError: If permission setting fails
        """
        try:
            validated_path = self.path_validator.validate_path(path, must_exist=True)
            
            if validated_path.is_file():
                mode = self.PRIVATE_FILE_MODE if is_private else self.SECURE_FILE_MODE
            elif validated_path.is_dir():
                mode = self.PRIVATE_DIR_MODE if is_private else self.SECURE_DIR_MODE
            else:
                raise EpochlyError(f"Path is neither file nor directory: {validated_path}")
            
            # Set permissions
            os.chmod(validated_path, mode)
            self.logger.debug(f"Set permissions {oct(mode)} on {validated_path}")
            
        except EpochlyError:
            raise
        except Exception as e:
            raise EpochlyError(f"Failed to set permissions on {path}: {e}")
    
    def create_secure_file(self, path: Union[str, Path], 
                          content: str = '',
                          is_private: bool = False,
                          encoding: str = 'utf-8') -> Path:
        """
        Create a file with secure permissions.
        
        Args:
            path: Path to create
            content: File content
            is_private: Whether to use private permissions
            encoding: File encoding
            
        Returns:
            Path to created file
            
        Raises:
            EpochlyError: If file creation fails
        """
        try:
            validated_path = self.path_validator.validate_path(path)
            
            # Ensure parent directory exists with secure permissions
            parent_dir = validated_path.parent
            if not parent_dir.exists():
                parent_dir.mkdir(parents=True, mode=self.SECURE_DIR_MODE)
                self.set_secure_permissions(parent_dir, is_private)
            
            # Create file with secure permissions
            mode = self.PRIVATE_FILE_MODE if is_private else self.SECURE_FILE_MODE
            
            # Use os.open with specific mode for security
            fd = os.open(validated_path, 
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL, 
                        mode)
            
            try:
                with os.fdopen(fd, 'w', encoding=encoding) as f:
                    f.write(content)
            except Exception:
                # Close fd if fdopen fails
                os.close(fd)
                raise
            
            self.logger.debug(f"Created secure file {validated_path} with mode {oct(mode)}")
            return validated_path
            
        except FileExistsError:
            raise EpochlyError(f"File already exists: {path}")
        except EpochlyError:
            raise
        except Exception as e:
            raise EpochlyError(f"Failed to create secure file {path}: {e}")
    
    def create_secure_directory(self, path: Union[str, Path], 
                               is_private: bool = False) -> Path:
        """
        Create a directory with secure permissions.
        
        Args:
            path: Directory path to create
            is_private: Whether to use private permissions
            
        Returns:
            Path to created directory
            
        Raises:
            EpochlyError: If directory creation fails
        """
        try:
            validated_path = self.path_validator.validate_path(path)
            
            mode = self.PRIVATE_DIR_MODE if is_private else self.SECURE_DIR_MODE
            
            # Create directory with secure permissions
            validated_path.mkdir(parents=True, mode=mode, exist_ok=False)
            
            # Ensure permissions are set correctly (mkdir mode can be affected by umask)
            self.set_secure_permissions(validated_path, is_private)
            
            self.logger.debug(f"Created secure directory {validated_path} with mode {oct(mode)}")
            return validated_path
            
        except FileExistsError:
            raise EpochlyError(f"Directory already exists: {path}")
        except EpochlyError:
            raise
        except Exception as e:
            raise EpochlyError(f"Failed to create secure directory {path}: {e}")
    
    def calculate_file_hash(self, path: Union[str, Path], 
                           algorithm: str = 'sha256') -> str:
        """
        Calculate hash of a file for integrity verification.
        
        Args:
            path: Path to file
            algorithm: Hash algorithm to use
            
        Returns:
            Hex digest of file hash
            
        Raises:
            EpochlyError: If hash calculation fails
        """
        try:
            validated_path = self.path_validator.validate_path(
                path, must_exist=True, must_be_file=True
            )
            
            hash_obj = hashlib.new(algorithm)
            
            with open(validated_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_obj.update(chunk)
            
            file_hash = hash_obj.hexdigest()
            self.logger.debug(f"Calculated {algorithm} hash for {validated_path}: {file_hash}")
            return file_hash
            
        except EpochlyError:
            raise
        except Exception as e:
            raise EpochlyError(f"Failed to calculate hash for {path}: {e}")
    
    def verify_file_integrity(self, path: Union[str, Path], 
                             expected_hash: str,
                             algorithm: str = 'sha256') -> bool:
        """
        Verify file integrity using hash comparison.
        
        Args:
            path: Path to file
            expected_hash: Expected hash value
            algorithm: Hash algorithm used
            
        Returns:
            True if integrity check passes, False otherwise
        """
        try:
            actual_hash = self.calculate_file_hash(path, algorithm)
            is_valid = actual_hash.lower() == expected_hash.lower()
            
            if is_valid:
                self.logger.debug(f"File integrity verified for {path}")
            else:
                self.logger.warning(f"File integrity check failed for {path}")
                
            return is_valid
            
        except Exception as e:
            self.logger.error(f"File integrity verification failed for {path}: {e}")
            return False
    
    def secure_copy(self, src: Union[str, Path], 
                   dst: Union[str, Path],
                   preserve_permissions: bool = False,
                   verify_integrity: bool = True) -> Dict[str, Any]:
        """
        Securely copy a file with integrity verification.
        
        Args:
            src: Source file path
            dst: Destination file path
            preserve_permissions: Whether to preserve source permissions
            verify_integrity: Whether to verify copy integrity
            
        Returns:
            Dictionary with copy operation details
            
        Raises:
            EpochlyError: If copy operation fails
        """
        try:
            src_path = self.path_validator.validate_path(
                src, must_exist=True, must_be_file=True
            )
            dst_path = self.path_validator.validate_path(dst)
            
            # Calculate source hash if verification requested
            src_hash = None
            if verify_integrity:
                src_hash = self.calculate_file_hash(src_path)
            
            # Ensure destination directory exists
            dst_parent = dst_path.parent
            if not dst_parent.exists():
                self.create_secure_directory(dst_parent)
            
            # Perform copy
            shutil.copy2(src_path, dst_path)
            
            # Set secure permissions if not preserving
            if not preserve_permissions:
                self.set_secure_permissions(dst_path)
            
            # Verify integrity if requested
            if verify_integrity and src_hash:
                if not self.verify_file_integrity(dst_path, src_hash):
                    # Clean up failed copy
                    try:
                        os.remove(dst_path)
                    except Exception:
                        pass
                    raise EpochlyError("File integrity verification failed after copy")
            
            result = {
                'source': str(src_path),
                'destination': str(dst_path),
                'size': dst_path.stat().st_size,
                'hash': src_hash,
                'verified': verify_integrity
            }
            
            self.logger.info(f"Securely copied {src_path} to {dst_path}")
            return result
            
        except EpochlyError:
            raise
        except Exception as e:
            raise EpochlyError(f"Secure copy failed from {src} to {dst}: {e}")
    
    def sanitize_environment_variable(self, value: str) -> str:
        """
        Sanitize environment variable value by removing dangerous characters.
        
        Args:
            value: Environment variable value
            
        Returns:
            Sanitized value
        """
        if not isinstance(value, str):
            value = str(value)
        
        # Remove null bytes and control characters
        sanitized = value.replace('\x00', '').replace('\r', '').replace('\n', '')
        
        # Remove other potentially dangerous characters
        dangerous_chars = '\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f'
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    def secure_backup_with_hash(self, src: Union[str, Path], 
                               backup_dir: Union[str, Path],
                               backup_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a secure backup with integrity hash.
        
        Args:
            src: Source file to backup
            backup_dir: Directory to store backup
            backup_name: Optional backup filename
            
        Returns:
            Dictionary with backup details including hash
            
        Raises:
            EpochlyError: If backup operation fails
        """
        try:
            src_path = self.path_validator.validate_path(
                src, must_exist=True, must_be_file=True
            )
            backup_dir_path = self.path_validator.validate_path(backup_dir)
            
            # Ensure backup directory exists
            if not backup_dir_path.exists():
                self.create_secure_directory(backup_dir_path, is_private=True)
            
            # Generate backup filename if not provided
            if not backup_name:
                import time
                timestamp = int(time.time())
                backup_name = f"{src_path.stem}_backup_{timestamp}{src_path.suffix}"
            
            backup_path = backup_dir_path / backup_name
            
            # Perform secure copy with verification
            copy_result = self.secure_copy(src_path, backup_path, verify_integrity=True)
            
            # Create hash file for additional verification
            hash_file = backup_path.with_suffix(backup_path.suffix + '.sha256')
            hash_content = f"{copy_result['hash']}  {backup_path.name}\n"
            
            with open(hash_file, 'w', encoding='utf-8') as f:
                f.write(hash_content)
            
            self.set_secure_permissions(hash_file, is_private=True)
            
            result = {
                'source': str(src_path),
                'backup_path': str(backup_path),
                'hash_file': str(hash_file),
                'hash': copy_result['hash'],
                'size': copy_result['size'],
                'timestamp': backup_path.stat().st_mtime
            }
            
            self.logger.info(f"Created secure backup of {src_path} at {backup_path}")
            return result
            
        except EpochlyError:
            raise
        except Exception as e:
            raise EpochlyError(f"Secure backup failed for {src}: {e}")