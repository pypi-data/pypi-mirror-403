"""
Epochly Audit Logger

Comprehensive audit logging system for security events, access control,
and system operations with structured logging and event correlation.

Author: Epochly Development Team
"""

import json
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
from collections import deque
from ..utils.logger import get_logger
from ..utils.exceptions import EpochlyError


class AuditEventType(Enum):
    """Types of audit events."""
    SECURITY_VIOLATION = "security_violation"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    FILE_ACCESS = "file_access"
    MEMORY_ACCESS = "memory_access"
    CONFIGURATION_CHANGE = "configuration_change"
    SYSTEM_EVENT = "system_event"
    ERROR = "error"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AuditEvent:
    """Represents a single audit event."""
    event_id: str
    timestamp: float
    event_type: AuditEventType
    severity: AuditSeverity
    source: str
    user_id: Optional[str]
    session_id: Optional[str]
    resource: Optional[str]
    action: str
    result: str
    details: Dict[str, Any]
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return data
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class AuditFilter:
    """Filters audit events based on criteria."""
    
    def __init__(self, event_types: Optional[List[AuditEventType]] = None,
                 severity_levels: Optional[List[AuditSeverity]] = None,
                 sources: Optional[List[str]] = None,
                 time_range: Optional[tuple] = None):
        """
        Initialize audit filter.
        
        Args:
            event_types: List of event types to include
            severity_levels: List of severity levels to include
            sources: List of sources to include
            time_range: Tuple of (start_time, end_time) for filtering
        """
        self.event_types = set(event_types) if event_types else None
        self.severity_levels = set(severity_levels) if severity_levels else None
        self.sources = set(sources) if sources else None
        self.time_range = time_range
    
    def matches(self, event: AuditEvent) -> bool:
        """
        Check if event matches filter criteria.
        
        Args:
            event: Audit event to check
            
        Returns:
            True if event matches filter
        """
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        if self.severity_levels and event.severity not in self.severity_levels:
            return False
        
        if self.sources and event.source not in self.sources:
            return False
        
        if self.time_range:
            start_time, end_time = self.time_range
            if not (start_time <= event.timestamp <= end_time):
                return False
        
        return True


class AuditLogger:
    """
    Comprehensive audit logging system for Epochly security events.
    
    Provides mechanisms for:
    - Structured audit event logging
    - Event correlation and tracking
    - Secure log storage and rotation
    - Real-time event monitoring
    - Compliance reporting
    """
    
    def __init__(self, log_directory: Optional[Path] = None,
                 max_log_size: int = 10 * 1024 * 1024,  # 10MB
                 max_log_files: int = 10,
                 max_memory_events: int = 1000,
                 enable_real_time: bool = True):
        """
        Initialize audit logger.
        
        Args:
            log_directory: Directory for audit log files
            max_log_size: Maximum size per log file in bytes
            max_log_files: Maximum number of log files to keep
            max_memory_events: Maximum number of events to keep in memory
            enable_real_time: Enable real-time event processing
        """
        self.logger = get_logger(__name__)
        self.log_directory = log_directory or Path.home() / '.epochly' / 'audit'
        self.max_log_size = max_log_size
        self.max_log_files = max_log_files
        self.max_memory_events = max_memory_events
        self.enable_real_time = enable_real_time
        
        # Event storage - bounded to prevent memory leaks
        self.events: deque = deque(maxlen=max_memory_events)
        self.event_handlers: List[Callable[[AuditEvent], None]] = []
        self.correlation_map: Dict[str, List[str]] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        self._event_counter = 0
        
        # Initialize log directory
        self._setup_log_directory()
        
        # Current log file
        self.current_log_file: Optional[Path] = None
        self._rotate_log_if_needed()
    
    def _setup_log_directory(self) -> None:
        """Set up audit log directory with secure permissions."""
        try:
            self.log_directory.mkdir(parents=True, exist_ok=True)
            
            # Set secure permissions (owner only)
            if hasattr(self.log_directory, 'chmod'):
                self.log_directory.chmod(0o700)
            
            self.logger.debug(f"Audit log directory: {self.log_directory}")
            
        except Exception as e:
            raise EpochlyError(f"Failed to setup audit log directory: {e}")
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        with self._lock:
            self._event_counter += 1
            timestamp = int(time.time() * 1000000)  # microseconds
            return f"audit_{timestamp}_{self._event_counter:06d}"
    
    def _rotate_log_if_needed(self) -> None:
        """Rotate log file if current file exceeds size limit."""
        import os

        if not self.current_log_file or not self.current_log_file.exists():
            # Create new log file with secure permissions (owner read/write only)
            timestamp = int(time.time())
            self.current_log_file = self.log_directory / f"audit_{timestamp}.log"
            # Pre-create file with secure permissions to avoid race conditions
            try:
                fd = os.open(str(self.current_log_file), os.O_CREAT | os.O_WRONLY, 0o600)
                os.close(fd)
            except OSError as e:
                self.logger.warning(f"Failed to create audit log with secure permissions: {e}")
            return

        # Check if rotation is needed
        if self.current_log_file.stat().st_size >= self.max_log_size:
            # Archive current file
            timestamp = int(time.time())
            archived_name = f"audit_{timestamp}.log"
            self.current_log_file = self.log_directory / archived_name
            # Pre-create new file with secure permissions
            try:
                fd = os.open(str(self.current_log_file), os.O_CREAT | os.O_WRONLY, 0o600)
                os.close(fd)
            except OSError as e:
                self.logger.warning(f"Failed to create rotated audit log with secure permissions: {e}")

            # Clean up old files
            self._cleanup_old_logs()
    
    def _cleanup_old_logs(self) -> None:
        """Remove old log files beyond retention limit."""
        try:
            log_files = sorted(
                [f for f in self.log_directory.glob("audit_*.log")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Remove files beyond limit
            for old_file in log_files[self.max_log_files:]:
                old_file.unlink()
                self.logger.debug(f"Removed old audit log: {old_file}")
                
        except Exception as e:
            self.logger.warning(f"Failed to cleanup old audit logs: {e}")
    
    def _write_to_file(self, event: AuditEvent) -> None:
        """Write audit event to log file."""
        try:
            self._rotate_log_if_needed()
            
            if self.current_log_file is not None:
                with open(self.current_log_file, 'a', encoding='utf-8') as f:
                    f.write(event.to_json() + '\n')
                    f.flush()
                
        except Exception as e:
            self.logger.error(f"Failed to write audit event to file: {e}")
    
    def log_event(self, event_type: AuditEventType, severity: AuditSeverity,
                  source: str, action: str, result: str,
                  user_id: Optional[str] = None,
                  session_id: Optional[str] = None,
                  resource: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None,
                  correlation_id: Optional[str] = None) -> str:
        """
        Log an audit event.
        
        Args:
            event_type: Type of audit event
            severity: Severity level
            source: Source component or module
            action: Action being performed
            result: Result of the action
            user_id: Optional user identifier
            session_id: Optional session identifier
            resource: Optional resource being accessed
            details: Optional additional details
            correlation_id: Optional correlation identifier
            
        Returns:
            Generated event ID
        """
        with self._lock:
            event_id = self._generate_event_id()
            timestamp = time.time()
            
            event = AuditEvent(
                event_id=event_id,
                timestamp=timestamp,
                event_type=event_type,
                severity=severity,
                source=source,
                user_id=user_id,
                session_id=session_id,
                resource=resource,
                action=action,
                result=result,
                details=details or {},
                correlation_id=correlation_id
            )
            
            # Store event
            self.events.append(event)
            
            # Update correlation map
            if correlation_id:
                if correlation_id not in self.correlation_map:
                    self.correlation_map[correlation_id] = []
                self.correlation_map[correlation_id].append(event_id)
            
            # Write to file
            self._write_to_file(event)
            
            # Real-time processing
            if self.enable_real_time:
                self._process_real_time_event(event)
            
            self.logger.debug(f"Logged audit event: {event_id}")
            return event_id
    
    def _process_real_time_event(self, event: AuditEvent) -> None:
        """Process event in real-time with handlers."""
        for handler in self.event_handlers:
            try:
                handler(event)
            except Exception as e:
                self.logger.error(f"Event handler error: {e}")
    
    def log_security_violation(self, source: str, violation_type: str,
                             details: Dict[str, Any],
                             user_id: Optional[str] = None,
                             resource: Optional[str] = None) -> str:
        """
        Log a security violation event.
        
        Args:
            source: Source of the violation
            violation_type: Type of violation
            details: Violation details
            user_id: Optional user identifier
            resource: Optional resource involved
            
        Returns:
            Generated event ID
        """
        return self.log_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            severity=AuditSeverity.CRITICAL,
            source=source,
            action=f"security_violation_{violation_type}",
            result="violation_detected",
            user_id=user_id,
            resource=resource,
            details=details
        )
    
    def log_access_attempt(self, source: str, resource: str, action: str,
                          granted: bool, user_id: Optional[str] = None,
                          session_id: Optional[str] = None,
                          details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log an access attempt event.
        
        Args:
            source: Source of the access attempt
            resource: Resource being accessed
            action: Action being attempted
            granted: Whether access was granted
            user_id: Optional user identifier
            session_id: Optional session identifier
            details: Optional additional details
            
        Returns:
            Generated event ID
        """
        event_type = AuditEventType.ACCESS_GRANTED if granted else AuditEventType.ACCESS_DENIED
        severity = AuditSeverity.INFO if granted else AuditSeverity.MEDIUM
        result = "granted" if granted else "denied"
        
        return self.log_event(
            event_type=event_type,
            severity=severity,
            source=source,
            action=action,
            result=result,
            user_id=user_id,
            session_id=session_id,
            resource=resource,
            details=details
        )
    
    def log_file_access(self, source: str, file_path: str, operation: str,
                       success: bool, user_id: Optional[str] = None,
                       details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a file access event.
        
        Args:
            source: Source of the file access
            file_path: Path to the file
            operation: File operation (read, write, delete, etc.)
            success: Whether operation was successful
            user_id: Optional user identifier
            details: Optional additional details
            
        Returns:
            Generated event ID
        """
        result = "success" if success else "failure"
        severity = AuditSeverity.INFO if success else AuditSeverity.MEDIUM
        
        return self.log_event(
            event_type=AuditEventType.FILE_ACCESS,
            severity=severity,
            source=source,
            action=f"file_{operation}",
            result=result,
            user_id=user_id,
            resource=file_path,
            details=details
        )
    
    def add_event_handler(self, handler: Callable[[AuditEvent], None]) -> None:
        """
        Add real-time event handler.
        
        Args:
            handler: Function to call for each event (takes AuditEvent)
        """
        self.event_handlers.append(handler)
    
    def remove_event_handler(self, handler: Callable[[AuditEvent], None]) -> None:
        """
        Remove event handler.
        
        Args:
            handler: Handler function to remove
        """
        if handler in self.event_handlers:
            self.event_handlers.remove(handler)
    
    def query_events(self, filter_criteria: Optional[AuditFilter] = None,
                    limit: Optional[int] = None) -> List[AuditEvent]:
        """
        Query audit events with optional filtering.
        
        Args:
            filter_criteria: Optional filter criteria
            limit: Optional limit on number of results
            
        Returns:
            List of matching audit events
        """
        with self._lock:
            # Convert deque to list for filtering and sorting
            events = list(self.events)
        
        # Apply filter
        if filter_criteria:
            events = [e for e in events if filter_criteria.matches(e)]
        
        # Sort by timestamp (newest first)
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit
        if limit:
            events = events[:limit]
        
        return events
    
    def get_correlated_events(self, correlation_id: str) -> List[AuditEvent]:
        """
        Get all events with the same correlation ID.
        
        Args:
            correlation_id: Correlation identifier
            
        Returns:
            List of correlated events
        """
        if correlation_id not in self.correlation_map:
            return []
        
        event_ids = self.correlation_map[correlation_id]
        # Convert deque to list for filtering and sorting
        events = [e for e in list(self.events) if e.event_id in event_ids]
        events.sort(key=lambda x: x.timestamp)
        
        return events
    
    def generate_report(self, filter_criteria: Optional[AuditFilter] = None,
                       format_type: str = 'json') -> str:
        """
        Generate audit report.
        
        Args:
            filter_criteria: Optional filter criteria
            format_type: Report format ('json', 'csv', 'summary')
            
        Returns:
            Generated report as string
        """
        events = self.query_events(filter_criteria)
        
        if format_type == 'json':
            return json.dumps([e.to_dict() for e in events], indent=2, default=str)
        
        elif format_type == 'csv':
            if not events:
                return "No events found"
            
            # CSV header
            headers = ['event_id', 'timestamp', 'event_type', 'severity', 'source',
                      'user_id', 'action', 'result', 'resource']
            csv_lines = [','.join(headers)]
            
            # CSV data
            for event in events:
                row = [
                    event.event_id,
                    str(event.timestamp),
                    event.event_type.value,
                    event.severity.value,
                    event.source,
                    event.user_id or '',
                    event.action,
                    event.result,
                    event.resource or ''
                ]
                csv_lines.append(','.join(f'"{field}"' for field in row))
            
            return '\n'.join(csv_lines)
        
        elif format_type == 'summary':
            if not events:
                return "No events found"
            
            # Generate summary statistics
            total_events = len(events)
            event_types = {}
            severity_counts = {}
            sources = {}
            
            for event in events:
                event_types[event.event_type.value] = event_types.get(event.event_type.value, 0) + 1
                severity_counts[event.severity.value] = severity_counts.get(event.severity.value, 0) + 1
                sources[event.source] = sources.get(event.source, 0) + 1
            
            summary = "Audit Report Summary\n"
            summary += f"Total Events: {total_events}\n\n"
            summary += "Event Types:\n"
            for event_type, count in sorted(event_types.items()):
                summary += f"  {event_type}: {count}\n"
            summary += "\nSeverity Levels:\n"
            for severity, count in sorted(severity_counts.items()):
                summary += f"  {severity}: {count}\n"
            summary += "\nTop Sources:\n"
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10]:
                summary += f"  {source}: {count}\n"
            
            return summary
        
        else:
            raise EpochlyError(f"Unsupported report format: {format_type}")
    
    def get_audit_status(self) -> Dict[str, Any]:
        """
        Get current audit system status.
        
        Returns:
            Dictionary with audit system status
        """
        with self._lock:
            status = {
                'total_events': len(self.events),
                'log_directory': str(self.log_directory),
                'current_log_file': str(self.current_log_file) if self.current_log_file else None,
                'max_log_size': self.max_log_size,
                'max_log_files': self.max_log_files,
                'real_time_enabled': self.enable_real_time,
                'event_handlers': len(self.event_handlers),
                'correlation_groups': len(self.correlation_map)
            }
            
            # Recent activity
            if self.events:
                # Convert deque to list for sorting and slicing
                recent_events = sorted(list(self.events), key=lambda x: x.timestamp, reverse=True)[:10]
                status['recent_events'] = [
                    {
                        'event_id': e.event_id,
                        'timestamp': e.timestamp,
                        'event_type': e.event_type.value,
                        'severity': e.severity.value,
                        'source': e.source
                    }
                    for e in recent_events
                ]
            
            return status