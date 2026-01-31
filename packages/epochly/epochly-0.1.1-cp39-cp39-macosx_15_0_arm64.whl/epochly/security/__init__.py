"""
Epochly Security Module

Provides security utilities and hardening mechanisms for the Epochly deployment infrastructure.

Author: Epochly Development Team
"""

from .security_manager import SecurityManager
from .file_security import FileSecurityManager
from .path_validator import PathValidator
from .isolation_enforcer import IsolationEnforcer, MemorySegment, SubInterpreterContext, IsolationViolationError
from .audit_logger import AuditLogger, AuditEvent, AuditEventType, AuditSeverity, AuditFilter
from .side_channel_protection import (
    SideChannelProtector, TimingAttackProtection, MemoryProtection, CacheProtection,
    get_side_channel_protector, secure_compare, secure_search
)

__all__ = [
    'SecurityManager',
    'FileSecurityManager',
    'PathValidator',
    'IsolationEnforcer',
    'MemorySegment',
    'SubInterpreterContext',
    'IsolationViolationError',
    'AuditLogger',
    'AuditEvent',
    'AuditEventType',
    'AuditSeverity',
    'AuditFilter',
    'SideChannelProtector',
    'TimingAttackProtection',
    'MemoryProtection',
    'CacheProtection',
    'get_side_channel_protector',
    'secure_compare',
    'secure_search'
]