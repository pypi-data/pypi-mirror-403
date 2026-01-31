"""
Epochly Access Control Implementation

This module provides access control functionality for Epochly's shared memory system.
It manages permissions, validates access requests, and enforces security policies
for memory regions to prevent unauthorized access and maintain isolation.

Author: Epochly Development Team
"""

import threading
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum, Flag
import logging

from .exceptions import (
    AccessDeniedError,
    InvalidRegionError
)

logger = logging.getLogger(__name__)


class AccessPermission(Flag):
    """Memory access permissions."""
    NONE = 0
    READ = 1
    WRITE = 2
    EXECUTE = 4
    READ_WRITE = READ | WRITE
    ALL = READ | WRITE | EXECUTE


class AccessResult(Enum):
    """Results of access control checks."""
    ALLOWED = "allowed"
    DENIED = "denied"
    EXPIRED = "expired"
    INVALID_REGION = "invalid_region"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"


@dataclass
class AccessGrant:
    """Represents an access grant for a memory region."""
    region_id: str
    offset: int
    size: int
    permissions: AccessPermission
    granted_at: float
    expires_at: Optional[float] = None
    granted_to: Optional[str] = None  # Principal/user identifier
    
    @property
    def is_expired(self) -> bool:
        """Check if access grant has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    @property
    def remaining_time(self) -> Optional[float]:
        """Get remaining time before expiration."""
        if self.expires_at is None:
            return None
        return max(0.0, self.expires_at - time.time())


@dataclass
class MemoryRegion:
    """Represents a controlled memory region."""
    region_id: str
    offset: int
    size: int
    owner: Optional[str] = None
    created_at: Optional[float] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    @property
    def end_offset(self) -> int:
        """Get end offset of the region."""
        return self.offset + self.size
    
    def contains(self, offset: int, size: int = 1) -> bool:
        """Check if region contains the specified range."""
        return (self.offset <= offset and 
                offset + size <= self.end_offset)


# Note: Using unified exception classes from .exceptions module
# AccessControlError -> MemoryFoundationError
# AccessDeniedError -> AccessDeniedError (from exceptions)
# InvalidRegionError -> InvalidRegionError (from exceptions)


class AccessController:
    """
    Access controller for memory regions.
    
    Manages access permissions, validates requests, and enforces security
    policies for shared memory regions in the Epochly system.
    """
    
    def __init__(
        self,
        default_permissions: AccessPermission = AccessPermission.READ_WRITE,
        enable_expiration: bool = True,
        default_grant_duration: Optional[float] = None,
        max_grant_duration: Optional[float] = None,
        audit_enabled: bool = True
    ):
        """
        Initialize access controller.
        
        Args:
            default_permissions: Default permissions for new regions
            enable_expiration: Whether to enable grant expiration
            default_grant_duration: Default grant duration in seconds
            max_grant_duration: Maximum allowed grant duration
            audit_enabled: Whether to enable access auditing
        """
        self._default_permissions = default_permissions
        self._enable_expiration = enable_expiration
        self._default_grant_duration = default_grant_duration
        self._max_grant_duration = max_grant_duration
        self._audit_enabled = audit_enabled
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Memory regions
        self._regions: Dict[str, MemoryRegion] = {}
        self._offset_to_region: Dict[int, str] = {}  # offset -> region_id
        
        # Access grants - CRITICAL FIX: Use composite keys to prevent collisions
        self._grants: Dict[str, List[AccessGrant]] = {}  # region_id -> grants
        self._principal_grants: Dict[str, List[AccessGrant]] = {}  # principal -> grants
        self._grant_keys: Dict[Tuple[str, str], AccessGrant] = {}  # (principal, region_id) -> grant
        
        # Audit log
        self._audit_log: List[Dict] = []
        self._max_audit_entries = 10000
        
        # Statistics
        self._total_grants_issued = 0
        self._total_access_checks = 0
        self._total_access_denied = 0
        self._total_expired_grants = 0
        
        logger.debug("Initialized AccessController")
    
    def register_region(
        self,
        region_id: str,
        offset: int,
        size: int,
        owner: Optional[str] = None
    ) -> bool:
        """
        Register a memory region for access control.
        
        Args:
            region_id: Unique identifier for the region
            offset: Starting offset of the region
            size: Size of the region
            owner: Owner of the region
            
        Returns:
            True if region registered successfully
        """
        if size <= 0:
            raise ValueError("Region size must be positive")
        
        with self._lock:
            # Check for conflicts with existing regions
            end_offset = offset + size
            for existing_offset, existing_region_id in self._offset_to_region.items():
                existing_region = self._regions[existing_region_id]
                if (offset < existing_region.end_offset and 
                    end_offset > existing_region.offset):
                    logger.warning(
                        f"Region {region_id} overlaps with existing region {existing_region_id}"
                    )
                    return False
            
            # Create and register region
            region = MemoryRegion(
                region_id=region_id,
                offset=offset,
                size=size,
                owner=owner
            )
            
            self._regions[region_id] = region
            self._offset_to_region[offset] = region_id
            self._grants[region_id] = []
            
            self._audit_access(
                "REGION_REGISTERED",
                region_id=region_id,
                offset=offset,
                size=size,
                owner=owner
            )
            
            logger.debug(f"Registered region {region_id} at offset {offset}")
            return True
    
    def unregister_region(self, region_id: str) -> bool:
        """
        Unregister a memory region.
        
        Args:
            region_id: Region to unregister
            
        Returns:
            True if region unregistered successfully
        """
        with self._lock:
            if region_id not in self._regions:
                return False
            
            region = self._regions[region_id]
            
            # Revoke all grants for this region
            grants = self._grants.get(region_id, [])
            for grant in grants:
                if grant.granted_to and grant.granted_to in self._principal_grants:
                    try:
                        self._principal_grants[grant.granted_to].remove(grant)
                    except ValueError:
                        pass
            
            # Remove region
            del self._regions[region_id]
            del self._offset_to_region[region.offset]
            del self._grants[region_id]
            
            self._audit_access(
                "REGION_UNREGISTERED",
                region_id=region_id,
                offset=region.offset,
                size=region.size
            )
            
            logger.debug(f"Unregistered region {region_id}")
            return True
    
    def grant_access(
        self,
        region_id: str,
        permissions: AccessPermission,
        principal: Optional[str] = None,
        duration: Optional[float] = None
    ) -> Optional[AccessGrant]:
        """
        Grant access to a memory region.
        
        Args:
            region_id: Region to grant access to
            permissions: Permissions to grant
            principal: Principal to grant access to
            duration: Duration of grant in seconds
            
        Returns:
            AccessGrant if successful, None otherwise
            
        Raises:
            ValueError: If region_id is empty or principal is empty string
        """
        # Validate inputs
        if not region_id or region_id.strip() == "":
            raise ValueError("Region ID cannot be empty")
        if principal is not None and principal.strip() == "":
            raise ValueError("Principal cannot be empty string")
            
        with self._lock:
            if region_id not in self._regions:
                logger.warning(f"Cannot grant access to unknown region {region_id}")
                return None
            
            region = self._regions[region_id]
            
            # Validate duration
            if duration is not None:
                if self._max_grant_duration and duration > self._max_grant_duration:
                    duration = self._max_grant_duration
            elif self._enable_expiration and self._default_grant_duration:
                duration = self._default_grant_duration
            
            # Calculate expiration
            expires_at = None
            if duration is not None:
                expires_at = time.time() + duration
            
            # Create grant
            grant = AccessGrant(
                region_id=region_id,
                offset=region.offset,
                size=region.size,
                permissions=permissions,
                granted_at=time.time(),
                expires_at=expires_at,
                granted_to=principal
            )
            
            # Add to tracking structures with collision prevention
            self._grants[region_id].append(grant)
            if principal:
                if principal not in self._principal_grants:
                    self._principal_grants[principal] = []
                self._principal_grants[principal].append(grant)
                
                # CRITICAL FIX: Use composite key to prevent grant collisions
                grant_key = (principal, region_id)
                if grant_key in self._grant_keys:
                    # Revoke existing grant before adding new one
                    old_grant = self._grant_keys[grant_key]
                    self._grants[region_id].remove(old_grant)
                    self._principal_grants[principal].remove(old_grant)
                
                self._grant_keys[grant_key] = grant
            
            self._total_grants_issued += 1
            
            self._audit_access(
                "ACCESS_GRANTED",
                region_id=region_id,
                principal=principal,
                permissions=permissions.name,
                duration=duration
            )
            
            logger.debug(
                f"Granted {permissions.name} access to region {region_id} "
                f"for principal {principal}"
            )
            
            return grant
    
    def revoke_access(
        self,
        region_id: str,
        principal: Optional[str] = None
    ) -> int:
        """
        Revoke access to a memory region.
        
        Args:
            region_id: Region to revoke access from
            principal: Principal to revoke access from (all if None)
            
        Returns:
            Number of grants revoked
        """
        with self._lock:
            if region_id not in self._grants:
                return 0
            
            grants_to_remove = []
            
            for grant in self._grants[region_id]:
                if principal is None or grant.granted_to == principal:
                    grants_to_remove.append(grant)
            
            # Remove grants
            for grant in grants_to_remove:
                self._grants[region_id].remove(grant)
                if grant.granted_to and grant.granted_to in self._principal_grants:
                    try:
                        self._principal_grants[grant.granted_to].remove(grant)
                    except ValueError:
                        pass
            
            if grants_to_remove:
                self._audit_access(
                    "ACCESS_REVOKED",
                    region_id=region_id,
                    principal=principal,
                    grants_revoked=len(grants_to_remove)
                )
            
            logger.debug(f"Revoked {len(grants_to_remove)} grants for region {region_id}")
            return len(grants_to_remove)
    
    def check_access(
        self,
        offset: int,
        size: int,
        permission: AccessPermission,
        principal: Optional[str] = None
    ) -> AccessResult:
        """
        Check if access is allowed for a memory range.
        
        Args:
            offset: Starting offset of access
            size: Size of access
            permission: Required permission
            principal: Principal requesting access
            
        Returns:
            AccessResult indicating if access is allowed
        """
        with self._lock:
            self._total_access_checks += 1
            
            # Find region containing the access
            region_id = self._find_region_for_offset(offset)
            if not region_id:
                self._total_access_denied += 1
                self._audit_access(
                    "ACCESS_DENIED",
                    reason="INVALID_REGION",
                    offset=offset,
                    size=size,
                    principal=principal
                )
                return AccessResult.INVALID_REGION
            
            region = self._regions[region_id]
            
            # Check if access is within region bounds
            if not region.contains(offset, size):
                self._total_access_denied += 1
                self._audit_access(
                    "ACCESS_DENIED",
                    reason="OUT_OF_BOUNDS",
                    region_id=region_id,
                    offset=offset,
                    size=size,
                    principal=principal
                )
                return AccessResult.INVALID_REGION
            
            # Check grants for this region
            valid_grants = []
            for grant in self._grants[region_id]:
                if grant.is_expired:
                    self._total_expired_grants += 1
                    continue
                
                # Check if grant applies to this principal
                if principal and grant.granted_to and grant.granted_to != principal:
                    continue
                
                # Check if grant covers required permission
                if permission & grant.permissions == permission:
                    valid_grants.append(grant)
            
            if valid_grants:
                self._audit_access(
                    "ACCESS_ALLOWED",
                    region_id=region_id,
                    offset=offset,
                    size=size,
                    permission=permission.name,
                    principal=principal
                )
                return AccessResult.ALLOWED
            
            # Check if any grants exist but are expired
            expired_grants = [g for g in self._grants[region_id] if g.is_expired]
            if expired_grants:
                self._total_access_denied += 1
                self._audit_access(
                    "ACCESS_DENIED",
                    reason="EXPIRED",
                    region_id=region_id,
                    principal=principal
                )
                return AccessResult.EXPIRED
            
            # No valid grants found
            self._total_access_denied += 1
            self._audit_access(
                "ACCESS_DENIED",
                reason="INSUFFICIENT_PERMISSIONS",
                region_id=region_id,
                principal=principal
            )
            return AccessResult.INSUFFICIENT_PERMISSIONS
    
    def validate_access(
        self,
        offset: int,
        size: int,
        permission: AccessPermission,
        principal: Optional[str] = None
    ) -> None:
        """
        Validate access and raise exception if denied.
        
        Args:
            offset: Starting offset of access
            size: Size of access
            permission: Required permission
            principal: Principal requesting access
            
        Raises:
            AccessDeniedError: If access is denied
            InvalidRegionError: If region is invalid
        """
        result = self.check_access(offset, size, permission, principal)
        
        if result == AccessResult.ALLOWED:
            return
        elif result == AccessResult.INVALID_REGION:
            raise InvalidRegionError(f"Invalid memory region at offset {offset}")
        else:
            raise AccessDeniedError(
                f"Access denied for offset {offset}, size {size}, "
                f"permission {permission.name}: {result.value}"
            )
    
    def _find_region_for_offset(self, offset: int) -> Optional[str]:
        """Find region that contains the given offset."""
        for region_id, region in self._regions.items():
            if region.offset <= offset < region.end_offset:
                return region_id
        return None
    
    def cleanup_expired_grants(self) -> int:
        """
        Clean up expired grants.
        
        Returns:
            Number of grants cleaned up
        """
        with self._lock:
            cleaned_count = 0
            
            for region_id in list(self._grants.keys()):
                grants = self._grants[region_id]
                expired_grants = [g for g in grants if g.is_expired]
                
                for grant in expired_grants:
                    grants.remove(grant)
                    if grant.granted_to and grant.granted_to in self._principal_grants:
                        try:
                            self._principal_grants[grant.granted_to].remove(grant)
                        except ValueError:
                            pass
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.debug(f"Cleaned up {cleaned_count} expired grants")
            
            return cleaned_count
    
    def _audit_access(self, action: str, **kwargs) -> None:
        """Add entry to audit log."""
        if not self._audit_enabled:
            return
        
        with self._lock:
            entry = {
                'timestamp': time.time(),
                'action': action,
                **kwargs
            }
            
            self._audit_log.append(entry)
            
            # Trim audit log if too large
            if len(self._audit_log) > self._max_audit_entries:
                self._audit_log = self._audit_log[-self._max_audit_entries:]
    
    def get_region_info(self, region_id: str) -> Optional[MemoryRegion]:
        """Get information about a memory region."""
        with self._lock:
            return self._regions.get(region_id)
    
    def get_grants_for_region(self, region_id: str) -> List[AccessGrant]:
        """Get all grants for a region."""
        with self._lock:
            return list(self._grants.get(region_id, []))
    
    def get_grants_for_principal(self, principal: str) -> List[AccessGrant]:
        """Get all grants for a principal."""
        with self._lock:
            return list(self._principal_grants.get(principal, []))
    
    def get_statistics(self) -> Dict:
        """Get access controller statistics."""
        with self._lock:
            active_grants = sum(
                len([g for g in grants if not g.is_expired])
                for grants in self._grants.values()
            )
            
            return {
                'total_regions': len(self._regions),
                'total_grants_issued': self._total_grants_issued,
                'active_grants': active_grants,
                'total_access_checks': self._total_access_checks,
                'total_access_denied': self._total_access_denied,
                'total_expired_grants': self._total_expired_grants,
                'audit_entries': len(self._audit_log),
                'principals_with_grants': len(self._principal_grants)
            }
    
    def get_audit_log(self, limit: Optional[int] = None) -> List[Dict]:
        """Get audit log entries."""
        with self._lock:
            if limit is None:
                return list(self._audit_log)
            return list(self._audit_log[-limit:])
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up access controller resources."""
        with self._lock:
            # Clear all data structures
            self._regions.clear()
            self._offset_to_region.clear()
            self._grants.clear()
            self._principal_grants.clear()
            self._grant_keys.clear()  # CRITICAL FIX: Clear grant keys to prevent memory leaks
            self._audit_log.clear()
            
            logger.debug("Cleaned up AccessController")