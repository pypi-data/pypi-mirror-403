"""
Epochly Isolation Enforcer

Provides memory isolation and sub-interpreter security enforcement mechanisms
to prevent unauthorized access between execution contexts.

Author: Epochly Development Team
"""

import threading
from typing import Dict, Any, Optional, Set, List, Callable
from ..utils.logger import get_logger
from ..utils.exceptions import EpochlyError
from .audit_logger import AuditLogger


class IsolationViolationError(EpochlyError):
    """Raised when isolation boundaries are violated."""
    pass


class MemorySegment:
    """Represents an isolated memory segment with access controls."""
    
    def __init__(self, segment_id: str, size: int, permissions: str = 'rw'):
        """
        Initialize memory segment.
        
        Args:
            segment_id: Unique identifier for the segment
            size: Size of the segment in bytes
            permissions: Access permissions (r=read, w=write, x=execute)
        """
        self.segment_id = segment_id
        self.size = size
        self.permissions = set(permissions.lower())
        self.data: Dict[str, Any] = {}
        self.access_count = 0
        self.last_access = None
        self._lock = threading.RLock()
    
    def check_permission(self, operation: str) -> bool:
        """
        Check if operation is permitted on this segment.
        
        Args:
            operation: Operation type ('r', 'w', 'x')
            
        Returns:
            True if operation is permitted
        """
        return operation.lower() in self.permissions
    
    def read(self, key: str) -> Any:
        """
        Read data from segment with permission check.
        
        Args:
            key: Data key to read
            
        Returns:
            Data value
            
        Raises:
            IsolationViolationError: If read permission denied
        """
        if not self.check_permission('r'):
            raise IsolationViolationError(f"Read access denied to segment {self.segment_id}")
        
        with self._lock:
            self.access_count += 1
            self.last_access = threading.current_thread().ident
            return self.data.get(key)
    
    def write(self, key: str, value: Any) -> None:
        """
        Write data to segment with permission check.
        
        Args:
            key: Data key to write
            value: Data value to store
            
        Raises:
            IsolationViolationError: If write permission denied
        """
        if not self.check_permission('w'):
            raise IsolationViolationError(f"Write access denied to segment {self.segment_id}")
        
        with self._lock:
            self.access_count += 1
            self.last_access = threading.current_thread().ident
            self.data[key] = value


class SubInterpreterContext:
    """Manages isolated execution context for sub-interpreters."""
    
    def __init__(self, context_id: str, allowed_modules: Optional[Set[str]] = None):
        """
        Initialize sub-interpreter context.
        
        Args:
            context_id: Unique identifier for the context
            allowed_modules: Set of allowed module names
        """
        self.context_id = context_id
        self.allowed_modules = allowed_modules or set()
        self.memory_segments: Dict[str, MemorySegment] = {}
        self.imported_modules: Set[str] = set()
        self.thread_id = threading.current_thread().ident
        self._lock = threading.RLock()
    
    def add_memory_segment(self, segment: MemorySegment) -> None:
        """
        Add memory segment to context.
        
        Args:
            segment: Memory segment to add
        """
        with self._lock:
            self.memory_segments[segment.segment_id] = segment
    
    def get_memory_segment(self, segment_id: str) -> Optional[MemorySegment]:
        """
        Get memory segment by ID.
        
        Args:
            segment_id: Segment identifier
            
        Returns:
            Memory segment or None if not found
        """
        return self.memory_segments.get(segment_id)
    
    def check_module_access(self, module_name: str) -> bool:
        """
        Check if module access is allowed.
        
        Args:
            module_name: Name of module to check
            
        Returns:
            True if access is allowed
        """
        if not self.allowed_modules:
            return True  # No restrictions if no allowed modules specified
        
        return module_name in self.allowed_modules


class IsolationEnforcer:
    """
    Enforces isolation boundaries between execution contexts and memory segments.
    
    Provides mechanisms for:
    - Sub-interpreter isolation
    - Memory segment access control
    - Module import restrictions
    - Cross-context communication prevention
    """
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """Initialize isolation enforcer."""
        self.logger = get_logger(__name__)
        self.audit_logger = audit_logger
        self.contexts: Dict[str, SubInterpreterContext] = {}
        self.global_segments: Dict[str, MemorySegment] = {}
        self.violation_handlers: List[Callable[[str, str], None]] = []
        self._lock = threading.RLock()
    
    def create_context(self, context_id: str, 
                      allowed_modules: Optional[Set[str]] = None) -> SubInterpreterContext:
        """
        Create new isolated execution context.
        
        Args:
            context_id: Unique identifier for the context
            allowed_modules: Set of allowed module names
            
        Returns:
            Created sub-interpreter context
            
        Raises:
            IsolationViolationError: If context already exists
        """
        with self._lock:
            if context_id in self.contexts:
                raise IsolationViolationError(f"Context {context_id} already exists")
            
            context = SubInterpreterContext(context_id, allowed_modules)
            self.contexts[context_id] = context
            
            self.logger.debug(f"Created isolation context: {context_id}")
            return context
    
    def destroy_context(self, context_id: str) -> None:
        """
        Destroy isolation context and clean up resources.
        
        Args:
            context_id: Context identifier to destroy
        """
        with self._lock:
            if context_id in self.contexts:
                context = self.contexts[context_id]
                
                # Clear memory segments
                context.memory_segments.clear()
                
                # Remove from contexts
                del self.contexts[context_id]
                
                self.logger.debug(f"Destroyed isolation context: {context_id}")
    
    def create_memory_segment(self, segment_id: str, size: int, 
                            permissions: str = 'rw',
                            context_id: Optional[str] = None) -> MemorySegment:
        """
        Create isolated memory segment.
        
        Args:
            segment_id: Unique identifier for the segment
            size: Size of the segment in bytes
            permissions: Access permissions (r=read, w=write, x=execute)
            context_id: Optional context to associate with
            
        Returns:
            Created memory segment
            
        Raises:
            IsolationViolationError: If segment already exists
        """
        with self._lock:
            # Check if segment already exists globally or in context
            if segment_id in self.global_segments:
                raise IsolationViolationError(f"Global segment {segment_id} already exists")
            
            if context_id and context_id in self.contexts:
                context = self.contexts[context_id]
                if segment_id in context.memory_segments:
                    raise IsolationViolationError(
                        f"Segment {segment_id} already exists in context {context_id}"
                    )
            
            segment = MemorySegment(segment_id, size, permissions)
            
            if context_id and context_id in self.contexts:
                # Add to specific context
                self.contexts[context_id].add_memory_segment(segment)
                self.logger.debug(f"Created memory segment {segment_id} in context {context_id}")
            else:
                # Add to global segments
                self.global_segments[segment_id] = segment
                self.logger.debug(f"Created global memory segment {segment_id}")
            
            return segment
    
    def access_memory_segment(self, segment_id: str, operation: str,
                            context_id: Optional[str] = None) -> Optional[MemorySegment]:
        """
        Access memory segment with isolation checks.
        
        Args:
            segment_id: Segment identifier
            operation: Operation type ('r', 'w', 'x')
            context_id: Context requesting access
            
        Returns:
            Memory segment if access allowed, None otherwise
            
        Raises:
            IsolationViolationError: If access is denied
        """
        with self._lock:
            segment = None
            
            # Try to find segment in context first
            if context_id and context_id in self.contexts:
                context = self.contexts[context_id]
                segment = context.get_memory_segment(segment_id)
            
            # Fall back to global segments if not found in context
            if not segment:
                segment = self.global_segments.get(segment_id)
            
            if not segment:
                violation_msg = f"Memory segment {segment_id} not found"
                self._handle_violation(context_id or "unknown", violation_msg)
                raise IsolationViolationError(violation_msg)
            
            # Check permissions
            if not segment.check_permission(operation):
                violation_msg = f"Access denied: {operation} on segment {segment_id}"
                self._handle_violation(context_id or "unknown", violation_msg)
                raise IsolationViolationError(violation_msg)
            
            return segment
    
    def check_cross_context_access(self, source_context: str, 
                                 target_context: str) -> bool:
        """
        Check if cross-context access is allowed.
        
        Args:
            source_context: Source context identifier
            target_context: Target context identifier
            
        Returns:
            True if access is allowed (currently always False for isolation)
        """
        # For strict isolation, cross-context access is not allowed
        if source_context != target_context:
            violation_msg = f"Cross-context access denied: {source_context} -> {target_context}"
            self._handle_violation(source_context, violation_msg)
            return False
        
        return True
    
    def validate_module_import(self, module_name: str, 
                             context_id: Optional[str] = None) -> bool:
        """
        Validate if module import is allowed in context.
        
        Args:
            module_name: Name of module to import
            context_id: Context requesting import
            
        Returns:
            True if import is allowed
        """
        if not context_id or context_id not in self.contexts:
            return True  # No restrictions for global context
        
        context = self.contexts[context_id]
        allowed = context.check_module_access(module_name)
        
        if allowed:
            context.imported_modules.add(module_name)
            self.logger.debug(f"Module import allowed: {module_name} in {context_id}")
        else:
            violation_msg = f"Module import denied: {module_name} in {context_id}"
            self._handle_violation(context_id, violation_msg)
            self.logger.warning(violation_msg)
        
        return allowed
    
    def add_violation_handler(self, handler: Callable[[str, str], None]) -> None:
        """
        Add violation event handler.
        
        Args:
            handler: Function to call on violations (context_id, message)
        """
        self.violation_handlers.append(handler)
    
    def _handle_violation(self, context_id: str, message: str) -> None:
        """
        Handle isolation violation.
        
        Args:
            context_id: Context where violation occurred
            message: Violation description
        """
        self.logger.error(f"Isolation violation in {context_id}: {message}")
        
        # Log to audit system if available
        if self.audit_logger:
            try:
                self.audit_logger.log_security_violation(
                    source="IsolationEnforcer",
                    violation_type="isolation_boundary_violation",
                    details={
                        "context_id": context_id,
                        "violation_message": message,
                        "thread_id": threading.current_thread().ident
                    },
                    resource=context_id
                )
            except Exception as e:
                self.logger.error(f"Failed to log violation to audit system: {e}")
        
        # Notify handlers
        for handler in self.violation_handlers:
            try:
                handler(context_id, message)
            except Exception as e:
                self.logger.error(f"Violation handler error: {e}")
    
    def get_isolation_status(self) -> Dict[str, Any]:
        """
        Get current isolation status.
        
        Returns:
            Dictionary with isolation status information
        """
        with self._lock:
            status = {
                'contexts': len(self.contexts),
                'global_segments': len(self.global_segments),
                'context_details': {},
                'segment_details': {}
            }
            
            # Context details
            for context_id, context in self.contexts.items():
                status['context_details'][context_id] = {
                    'memory_segments': len(context.memory_segments),
                    'imported_modules': len(context.imported_modules),
                    'thread_id': context.thread_id,
                    'allowed_modules': len(context.allowed_modules) if context.allowed_modules else 0
                }
            
            # Global segment details
            for segment_id, segment in self.global_segments.items():
                status['segment_details'][segment_id] = {
                    'size': segment.size,
                    'permissions': ''.join(sorted(segment.permissions)),
                    'access_count': segment.access_count,
                    'last_access': segment.last_access
                }
            
            return status