"""
Epochly Emergency Controls

Provides emergency controls and production safety mechanisms for Epochly.
Implements signal-based emergency controls, monitoring, and safety procedures.

Author: Epochly Development Team
"""

import os
import sys
import signal
import threading
import time
import json
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, asdict
import psutil

from ..utils.logger import get_logger


class EmergencyLevel(Enum):
    """Emergency severity levels."""
    INFO = "info"           # Informational alert
    WARNING = "warning"     # Warning condition
    CRITICAL = "critical"   # Critical condition requiring immediate attention
    EMERGENCY = "emergency" # Emergency requiring immediate shutdown


class EmergencyType(Enum):
    """Types of emergency conditions."""
    MANUAL_SHUTDOWN = "manual_shutdown"         # Manual emergency shutdown
    MEMORY_PRESSURE = "memory_pressure"        # High memory usage
    CPU_OVERLOAD = "cpu_overload"             # High CPU usage
    DISK_SPACE = "disk_space"                 # Low disk space
    PROCESS_CRASH = "process_crash"           # Process crash detected
    DEADLOCK = "deadlock"                     # Deadlock detected
    INFINITE_LOOP = "infinite_loop"           # Infinite loop detected
    RESOURCE_LEAK = "resource_leak"           # Resource leak detected
    EXTERNAL_SIGNAL = "external_signal"       # External emergency signal


@dataclass
class EmergencyEvent:
    """Emergency event information."""
    event_type: EmergencyType
    level: EmergencyLevel
    message: str
    timestamp: float
    process_id: int
    thread_id: int
    metadata: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[float] = None


class EmergencyControls:
    """
    Provides emergency controls and production safety mechanisms.
    
    Provides mechanisms for:
    - Signal-based emergency controls
    - Resource monitoring and alerts
    - Emergency shutdown procedures
    - Production safety monitoring
    - Emergency event logging and tracking
    """
    
    def __init__(self):
        """Initialize emergency controls."""
        self.logger = get_logger(__name__)
        self._lock = threading.RLock()
        
        # Emergency state
        self._emergency_active = False
        self._emergency_events: List[EmergencyEvent] = []
        self._emergency_callbacks: Dict[str, Callable] = {}
        
        # Thread-safe monitoring state using Events instead of boolean flags
        self._stop_event = threading.Event()
        self._monitor_lock = threading.Lock()
        self._monitoring_thread: Optional[threading.Thread] = None
        
        # Configuration
        self._config = self._load_emergency_config()
        
        # Resource monitoring
        self._last_memory_check = 0.0
        self._last_cpu_check = 0.0
        self._last_disk_check = 0.0
        
        # Signal handlers
        self._original_handlers: Dict[int, Any] = {}
        
        # Initialize emergency controls - signal handlers must be registered from main thread
        if threading.current_thread() is threading.main_thread():
            self._initialize_signal_handlers()
        else:
            self.logger.warning("EmergencyControls created from non-main thread; signal handlers not installed")
        
        self._start_monitoring()
    
    def _load_emergency_config(self) -> Dict[str, Any]:
        """Load emergency control configuration."""
        default_config = {
            'memory_threshold_percent': 90.0,
            'cpu_threshold_percent': 95.0,
            'disk_threshold_percent': 95.0,
            'monitoring_interval': 5.0,
            'emergency_log_path': os.path.join(os.path.expanduser('~'), '.epochly', 'emergency.log'),
            'auto_shutdown_on_critical': True,
            'max_emergency_events': 1000,
            'signal_handlers_enabled': True
        }
        
        try:
            config_path = os.path.join(os.path.expanduser('~'), '.epochly', 'emergency_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            self.logger.warning(f"Failed to load emergency config: {e}")
        
        return default_config
    
    def _initialize_signal_handlers(self) -> None:
        """Initialize signal handlers for emergency control."""
        if not self._config.get('signal_handlers_enabled', True):
            return
        
        # Check if we're in the main thread - signal handlers can only be registered from main thread
        if threading.current_thread() is not threading.main_thread():
            self.logger.warning("Signal handlers can only be registered from main thread, skipping signal handler setup")
            return
        
        try:
            # Handle SIGTERM for graceful shutdown
            if hasattr(signal, 'SIGTERM'):
                self._original_handlers[signal.SIGTERM] = signal.signal(
                    signal.SIGTERM, self._handle_emergency_signal
                )
            
            # Handle SIGINT (Ctrl+C) for emergency shutdown
            if hasattr(signal, 'SIGINT'):
                self._original_handlers[signal.SIGINT] = signal.signal(
                    signal.SIGINT, self._handle_emergency_signal
                )
            
            # Handle SIGUSR1 for emergency disable (Unix only)
            try:
                if hasattr(signal, 'SIGUSR1'):
                    sigusr1 = getattr(signal, 'SIGUSR1')
                    self._original_handlers[sigusr1] = signal.signal(
                        sigusr1, self._handle_emergency_signal
                    )
            except (OSError, ValueError, AttributeError):
                # Signal not supported on this platform (Windows)
                pass
            
            self.logger.debug("Emergency signal handlers initialized")
            
        except ValueError as e:
            self.logger.error(f"Failed to register signal handlers (must be called from main thread): {e}")
            # Fall back to alternative shutdown mechanism
            self._use_alternative_shutdown_mechanism()
        except Exception as e:
            self.logger.warning(f"Failed to initialize signal handlers: {e}")
    
    def _use_alternative_shutdown_mechanism(self) -> None:
        """Use alternative shutdown mechanism when signal handlers can't be registered."""
        self.logger.info("Using alternative shutdown mechanism (polling-based)")
        # This could be implemented as a polling mechanism or other alternative
        # Log that we're using an alternative approach
        pass
    
    def _handle_emergency_signal(self, signum: int, frame) -> None:
        """Handle emergency signals."""
        signal_names = {
            getattr(signal, 'SIGTERM', None): 'SIGTERM',
            getattr(signal, 'SIGINT', None): 'SIGINT',
            getattr(signal, 'SIGUSR1', None): 'SIGUSR1'
        }
        
        signal_name = signal_names.get(signum, f'Signal {signum}')
        
        self.logger.critical(f"Emergency signal received: {signal_name}")
        
        # Create emergency event
        event = EmergencyEvent(
            event_type=EmergencyType.EXTERNAL_SIGNAL,
            level=EmergencyLevel.EMERGENCY,
            message=f"Emergency signal received: {signal_name}",
            timestamp=time.time(),
            process_id=os.getpid(),
            thread_id=threading.get_ident(),
            metadata={'signal': signum, 'signal_name': signal_name}
        )
        
        self._handle_emergency_event(event)
    
    def _start_monitoring(self) -> None:
        """Start resource monitoring thread with thread-safe patterns."""
        with self._monitor_lock:
            if self._monitoring_thread and self._monitoring_thread.is_alive():
                return  # Already running
            
            self._stop_event.clear()
            self._monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="Epochly-EmergencyMonitor"
            )
            self._monitoring_thread.start()
            self.logger.debug("Emergency monitoring thread started")
    
    def _stop_monitoring(self, timeout: float = 5.0) -> None:
        """Stop resource monitoring with thread-safe shutdown patterns."""
        with self._monitor_lock:
            self._stop_event.set()
            thread = self._monitoring_thread
        
        if not thread or not thread.is_alive():
            return
        
        # Avoid self-join deadlock
        if thread is threading.current_thread():
            self.logger.debug("Monitoring thread called shutdown itself; skipping self-join")
            return
        
        self.logger.debug(f"Joining monitoring thread (timeout={timeout}s)")
        thread.join(timeout)
        if thread.is_alive():
            self.logger.warning(f"Monitoring thread did not terminate within {timeout}s - waiting indefinitely")
            thread.join()  # Final unlimited wait
        
        self.logger.debug("Emergency monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        interval = self._config.get('monitoring_interval', 5.0)
        
        while not self._stop_event.is_set():
            try:
                self._check_system_resources()
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _check_system_resources(self) -> None:
        """Check system resources for emergency conditions."""
        current_time = time.time()
        
        # Check memory usage
        if current_time - self._last_memory_check > 10.0:  # Check every 10 seconds
            self._check_memory_usage()
            self._last_memory_check = current_time
        
        # Check CPU usage
        if current_time - self._last_cpu_check > 15.0:  # Check every 15 seconds
            self._check_cpu_usage()
            self._last_cpu_check = current_time
        
        # Check disk space
        if current_time - self._last_disk_check > 60.0:  # Check every minute
            self._check_disk_space()
            self._last_disk_check = current_time
    
    def _check_memory_usage(self) -> None:
        """Check memory usage and trigger alerts if necessary."""
        try:
            memory = psutil.virtual_memory()
            threshold = self._config.get('memory_threshold_percent', 90.0)
            
            if memory.percent > threshold:
                level = EmergencyLevel.CRITICAL if memory.percent > 95.0 else EmergencyLevel.WARNING
                
                event = EmergencyEvent(
                    event_type=EmergencyType.MEMORY_PRESSURE,
                    level=level,
                    message=f"High memory usage: {memory.percent:.1f}% (threshold: {threshold}%)",
                    timestamp=time.time(),
                    process_id=os.getpid(),
                    thread_id=threading.get_ident(),
                    metadata={
                        'memory_percent': memory.percent,
                        'memory_available': memory.available,
                        'memory_total': memory.total,
                        'threshold': threshold
                    }
                )
                
                self._handle_emergency_event(event)
                
        except Exception as e:
            self.logger.warning(f"Failed to check memory usage: {e}")
    
    def _check_cpu_usage(self) -> None:
        """Check CPU usage and trigger alerts if necessary."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1.0)
            threshold = self._config.get('cpu_threshold_percent', 95.0)
            
            if cpu_percent > threshold:
                level = EmergencyLevel.CRITICAL if cpu_percent > 98.0 else EmergencyLevel.WARNING
                
                event = EmergencyEvent(
                    event_type=EmergencyType.CPU_OVERLOAD,
                    level=level,
                    message=f"High CPU usage: {cpu_percent:.1f}% (threshold: {threshold}%)",
                    timestamp=time.time(),
                    process_id=os.getpid(),
                    thread_id=threading.get_ident(),
                    metadata={
                        'cpu_percent': cpu_percent,
                        'cpu_count': psutil.cpu_count(),
                        'threshold': threshold
                    }
                )
                
                self._handle_emergency_event(event)
                
        except Exception as e:
            self.logger.warning(f"Failed to check CPU usage: {e}")
    
    def _check_disk_space(self) -> None:
        """Check disk space and trigger alerts if necessary."""
        try:
            disk = psutil.disk_usage('/')
            threshold = self._config.get('disk_threshold_percent', 95.0)
            used_percent = (disk.used / disk.total) * 100
            
            if used_percent > threshold:
                level = EmergencyLevel.CRITICAL if used_percent > 98.0 else EmergencyLevel.WARNING
                
                event = EmergencyEvent(
                    event_type=EmergencyType.DISK_SPACE,
                    level=level,
                    message=f"Low disk space: {used_percent:.1f}% used (threshold: {threshold}%)",
                    timestamp=time.time(),
                    process_id=os.getpid(),
                    thread_id=threading.get_ident(),
                    metadata={
                        'disk_used_percent': used_percent,
                        'disk_free': disk.free,
                        'disk_total': disk.total,
                        'threshold': threshold
                    }
                )
                
                self._handle_emergency_event(event)
                
        except Exception as e:
            self.logger.warning(f"Failed to check disk space: {e}")
    
    def _handle_emergency_event(self, event: EmergencyEvent) -> None:
        """Handle an emergency event."""
        with self._lock:
            # Add to event list
            self._emergency_events.append(event)
            
            # Limit event history
            max_events = self._config.get('max_emergency_events', 1000)
            if len(self._emergency_events) > max_events:
                self._emergency_events = self._emergency_events[-max_events:]
            
            # Log event
            self._log_emergency_event(event)
            
            # Execute callbacks
            self._execute_emergency_callbacks(event)
            
            # Handle critical/emergency events
            if event.level in (EmergencyLevel.CRITICAL, EmergencyLevel.EMERGENCY):
                if self._config.get('auto_shutdown_on_critical', True):
                    self._trigger_emergency_shutdown(event)
    
    def _log_emergency_event(self, event: EmergencyEvent) -> None:
        """Log emergency event to file."""
        try:
            log_path = self._config.get('emergency_log_path')
            if log_path:
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                
                log_entry = {
                    'timestamp': event.timestamp,
                    'level': event.level.value,
                    'type': event.event_type.value,
                    'message': event.message,
                    'process_id': event.process_id,
                    'thread_id': event.thread_id,
                    'metadata': event.metadata
                }
                
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry) + '\n')
                    
        except Exception as e:
            self.logger.error(f"Failed to log emergency event: {e}")
    
    def _execute_emergency_callbacks(self, event: EmergencyEvent) -> None:
        """Execute registered emergency callbacks."""
        for name, callback in self._emergency_callbacks.items():
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Emergency callback {name} failed: {e}")
    
    def _trigger_emergency_shutdown(self, event: EmergencyEvent) -> None:
        """Trigger emergency shutdown."""
        if self._emergency_active:
            return  # Already in emergency mode
        
        self._emergency_active = True
        self.logger.critical(f"Emergency shutdown triggered: {event.message}")
        
        # Save state immediately before emergency shutdown
        try:
            from ..core.state_manager import get_state_manager
            from ..core.epochly_core import _get_epochly_core
            
            core = _get_epochly_core()
            if core:
                state_manager = get_state_manager()
                if state_manager.save_state(core):
                    self.logger.debug("State saved before emergency shutdown")
        except Exception as e:
            self.logger.debug(f"Could not save state during emergency shutdown: {e}")
        
        try:
            # Import here to avoid circular imports
            from .deployment_controller import DeploymentController
            
            # Emergency disable deployment
            controller = DeploymentController()
            controller.emergency_disable()
            
            # Emergency shutdown activation manager
            try:
                activation_manager = getattr(sys, '_epochly_activation_manager', None)
                if activation_manager is not None:
                    activation_manager.emergency_shutdown()
            except AttributeError:
                # Activation manager not available
                pass
            
        except Exception as e:
            self.logger.error(f"Failed to execute emergency shutdown: {e}")
    
    def register_emergency_callback(self, name: str, callback: Callable[[EmergencyEvent], None]) -> None:
        """
        Register callback for emergency events.
        
        Args:
            name: Name of the callback
            callback: Callback function that takes EmergencyEvent
        """
        with self._lock:
            self._emergency_callbacks[name] = callback
            self.logger.debug(f"Registered emergency callback: {name}")
    
    def unregister_emergency_callback(self, name: str) -> None:
        """
        Unregister emergency callback.
        
        Args:
            name: Name of the callback to remove
        """
        with self._lock:
            self._emergency_callbacks.pop(name, None)
            self.logger.debug(f"Unregistered emergency callback: {name}")
    
    def trigger_manual_emergency(self, message: str, level: EmergencyLevel = EmergencyLevel.EMERGENCY) -> None:
        """
        Manually trigger an emergency event.
        
        Args:
            message: Emergency message
            level: Emergency level
        """
        event = EmergencyEvent(
            event_type=EmergencyType.MANUAL_SHUTDOWN,
            level=level,
            message=message,
            timestamp=time.time(),
            process_id=os.getpid(),
            thread_id=threading.get_ident(),
            metadata={'manual': True}
        )
        
        self._handle_emergency_event(event)
    
    def is_emergency_active(self) -> bool:
        """Check if emergency mode is active."""
        with self._lock:
            return self._emergency_active
    
    def clear_emergency_state(self) -> None:
        """Clear emergency state (use with caution)."""
        with self._lock:
            self._emergency_active = False
            self.logger.info("Emergency state cleared")
    
    def get_emergency_events(self, limit: Optional[int] = None) -> List[EmergencyEvent]:
        """
        Get emergency events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of emergency events
        """
        with self._lock:
            events = self._emergency_events.copy()
            if limit:
                events = events[-limit:]
            return events
    
    def get_emergency_status(self) -> Dict[str, Any]:
        """Get emergency control status."""
        with self._lock:
            recent_events = self._emergency_events[-10:] if self._emergency_events else []
            
            return {
                'emergency_active': self._emergency_active,
                'monitoring_active': not self._stop_event.is_set(),
                'total_events': len(self._emergency_events),
                'recent_events': [asdict(event) for event in recent_events],
                'callbacks_registered': len(self._emergency_callbacks),
                'config': self._config.copy()
            }
    
    def shutdown(self) -> None:
        """Shutdown emergency controls."""
        self.logger.info("Shutting down emergency controls")
        
        # Stop monitoring
        self._stop_monitoring()
        
        # Restore signal handlers - only from main thread
        if threading.current_thread() is threading.main_thread():
            for signum, handler in self._original_handlers.items():
                try:
                    signal.signal(signum, handler)
                except Exception as e:
                    self.logger.warning(f"Failed to restore signal handler for {signum}: {e}")
        else:
            self.logger.warning("Signal handlers can only be restored from main thread; skipping signal handler restoration")
        
        self._original_handlers.clear()
        
        # Clear callbacks
        with self._lock:
            self._emergency_callbacks.clear()