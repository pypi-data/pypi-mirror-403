"""
Epochly Activation Manager

Manages runtime activation and deactivation of Epochly optimizations.
Provides module-level and process-level control mechanisms.

Author: Epochly Development Team
"""

import os
import threading
import time
import inspect
import concurrent.futures
from typing import Dict, Set, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass

from ..utils.logger import get_logger
from .deployment_controller import DeploymentController


class ActivationMode(Enum):
    """Activation modes for runtime control."""
    DISABLED = "disabled"        # Epochly completely disabled
    MONITOR = "monitor"          # Monitor only, no optimizations
    SELECTIVE = "selective"      # Selective activation based on rules
    FULL = "full"               # Full activation


@dataclass
class ActivationContext:
    """Context information for activation decisions."""
    module_name: str
    script_path: str
    process_id: int
    thread_id: int
    timestamp: float
    metadata: Dict[str, Any]


class ActivationManager:
    """
    Manages runtime activation and deactivation of Epochly optimizations.
    
    Provides mechanisms for:
    - Module-level activation control
    - Process-level activation control
    - Runtime mode switching
    - Activation context tracking
    
    Can be used as a context manager for automatic resource cleanup:
        with ActivationManager() as manager:
            manager.activate_module("my_module")
    """
    
    def __init__(self, deployment_controller: Optional[DeploymentController] = None):
        """
        Initialize activation manager.
        
        Args:
            deployment_controller: Optional deployment controller instance
        """
        self.logger = get_logger(__name__)
        self._lock = threading.RLock()
        self._deployment_controller = deployment_controller or DeploymentController()
        
        # Activation state tracking
        self._current_mode = ActivationMode.DISABLED
        self._activated_modules: Set[str] = set()
        self._activation_contexts: Dict[str, ActivationContext] = {}
        self._activation_callbacks: Dict[str, Callable] = {}
        
        # Performance tracking
        self._activation_count = 0
        self._deactivation_count = 0
        self._last_activation_time = 0.0
        
        # Thread pool for callback execution (bounded to prevent resource exhaustion)
        self._callback_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=4,
            thread_name_prefix="Epochly-Callback"
        )
        
        # Initialize based on deployment controller
        self._initialize_from_deployment()
    
    def _initialize_from_deployment(self) -> None:
        """Initialize activation state from deployment controller."""
        try:
            if self._deployment_controller.should_activate():
                mode = self._deployment_controller.get_current_mode()
                
                # Map deployment modes to activation modes
                mode_mapping = {
                    'monitor': ActivationMode.MONITOR,
                    'conservative': ActivationMode.SELECTIVE,
                    'balanced': ActivationMode.SELECTIVE,
                    'aggressive': ActivationMode.FULL
                }
                
                self._current_mode = mode_mapping.get(mode.value, ActivationMode.DISABLED)
                self.logger.info(f"Initialized activation mode: {self._current_mode.value}")
            else:
                self._current_mode = ActivationMode.DISABLED
                self.logger.info("Epochly activation disabled by deployment controller")
                
        except Exception as e:
            self.logger.warning(f"Failed to initialize from deployment controller: {e}")
            self._current_mode = ActivationMode.DISABLED
    
    def get_current_mode(self) -> ActivationMode:
        """Get current activation mode."""
        with self._lock:
            return self._current_mode
    
    def set_mode(self, mode: ActivationMode) -> None:
        """
        Set activation mode.
        
        Args:
            mode: New activation mode
        """
        with self._lock:
            old_mode = self._current_mode
            self._current_mode = mode
            
            self.logger.info(f"Activation mode changed: {old_mode.value} -> {mode.value}")
            
            # Handle mode transitions
            if mode == ActivationMode.DISABLED:
                self._deactivate_all_modules()
            elif old_mode == ActivationMode.DISABLED and mode != ActivationMode.DISABLED:
                self._reactivate_eligible_modules()
    
    def should_activate_module(self, module_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if a module should be activated.
        
        Args:
            module_name: Name of the module
            context: Optional context information
            
        Returns:
            True if module should be activated, False otherwise
        """
        with self._lock:
            # Check global activation mode
            if self._current_mode == ActivationMode.DISABLED:
                return False
            
            # Check deployment controller
            activation_context = {
                'module_name': module_name,
                'script_path': context.get('script_path', '') if context else '',
                **(context or {})
            }
            
            if not self._deployment_controller.should_activate(activation_context):
                return False
            
            # Check mode-specific rules
            if self._current_mode == ActivationMode.MONITOR:
                return False  # Monitor mode doesn't activate optimizations
            elif self._current_mode == ActivationMode.SELECTIVE:
                return self._should_activate_selective(module_name, context)
            elif self._current_mode == ActivationMode.FULL:
                return True
            
            return False
    
    def _should_activate_selective(self, module_name: str, context: Optional[Dict[str, Any]]) -> bool:
        """Determine if module should be activated in selective mode."""
        # Implement selective activation logic
        # This could be based on module patterns, performance metrics, etc.
        
        # Don't activate empty module names
        if not module_name or not module_name.strip():
            return False
        
        # Implement basic rules
        if module_name.startswith('test_') or module_name.endswith('_test'):
            return False  # Don't activate for test modules
        
        if 'debug' in module_name.lower():
            return False  # Don't activate for debug modules
        
        # Check if module is in a critical path
        critical_patterns = ['main', 'core', 'engine', 'process']
        if any(pattern in module_name.lower() for pattern in critical_patterns):
            return True
        
        return True  # Default to activation for other modules
    
    def activate_module(self, module_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Activate Epochly for a specific module.
        
        Args:
            module_name: Name of the module to activate
            context: Optional context information
            
        Returns:
            True if activation was successful, False otherwise
        """
        with self._lock:
            if not self.should_activate_module(module_name, context):
                return False
            
            if module_name in self._activated_modules:
                return True  # Already activated
            
            try:
                # Create activation context
                activation_context = ActivationContext(
                    module_name=module_name,
                    script_path=context.get('script_path', '') if context else '',
                    process_id=os.getpid(),
                    thread_id=threading.get_ident(),
                    timestamp=time.time(),
                    metadata=context or {}
                )
                
                # Store context
                self._activation_contexts[module_name] = activation_context
                self._activated_modules.add(module_name)

                # CRITICAL: Actually enable Epochly runtime hooks
                import epochly
                if not hasattr(epochly, '_auto_enabled') or not epochly._auto_enabled:
                    epochly.auto_enable()
                    self.logger.info("Epochly runtime hooks enabled via auto_enable()")

                # Update metrics
                self._activation_count += 1
                self._last_activation_time = time.time()

                # Execute activation callbacks
                self._execute_activation_callbacks(module_name, activation_context)

                self.logger.debug(f"Activated Epochly for module: {module_name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to activate module {module_name}: {e}")
                return False
    
    def deactivate_module(self, module_name: str) -> bool:
        """
        Deactivate Epochly for a specific module.
        
        Args:
            module_name: Name of the module to deactivate
            
        Returns:
            True if deactivation was successful, False otherwise
        """
        with self._lock:
            if module_name not in self._activated_modules:
                return True  # Already deactivated
            
            try:
                # Remove from activated modules
                self._activated_modules.discard(module_name)
                
                # Remove context
                context = self._activation_contexts.pop(module_name, None)
                
                # Update metrics
                self._deactivation_count += 1
                
                # Execute deactivation callbacks
                self._execute_deactivation_callbacks(module_name, context)
                
                self.logger.debug(f"Deactivated Epochly for module: {module_name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to deactivate module {module_name}: {e}")
                return False
    
    def _deactivate_all_modules(self) -> None:
        """Deactivate all currently activated modules."""
        modules_to_deactivate = list(self._activated_modules)
        for module_name in modules_to_deactivate:
            self.deactivate_module(module_name)
    
    def _reactivate_eligible_modules(self) -> None:
        """Reactivate modules that are eligible for activation."""
        # This would typically be called when transitioning from disabled to enabled
        # Let modules reactivate naturally as they're accessed
        pass
    
    def register_activation_callback(self, name: str, callback: Callable) -> None:
        """
        Register a callback to be executed on module activation.
        
        Args:
            name: Name of the callback
            callback: Callback function
        """
        with self._lock:
            self._activation_callbacks[name] = callback
            self.logger.debug(f"Registered activation callback: {name}")
    
    def unregister_activation_callback(self, name: str) -> None:
        """
        Unregister an activation callback.
        
        Args:
            name: Name of the callback to remove
        """
        with self._lock:
            self._activation_callbacks.pop(name, None)
            self.logger.debug(f"Unregistered activation callback: {name}")
    
    def _execute_activation_callbacks(self, module_name: str, context: ActivationContext) -> None:
        """Execute all registered activation callbacks."""
        # Capture callback list while holding lock, then release lock before dispatch
        callbacks_to_execute = []
        with self._lock:
            callbacks_to_execute = list(self._activation_callbacks.items())
        
        # Execute callbacks outside of lock to prevent deadlock
        for name, callback in callbacks_to_execute:
            try:
                # Add timeout protection for callback execution using threading
                self._execute_callback_with_timeout(name, callback, module_name, context, timeout=30.0)
            except TimeoutError as e:
                self.logger.error(f"Activation callback {name} timed out: {e}")
            except Exception as e:
                self.logger.warning(f"Activation callback {name} failed: {e}")
    
    def _execute_callback_with_timeout(self, name: str, callback: Callable, module_name: str, context: Optional[ActivationContext], timeout: float, deactivating: bool = False) -> None:
        """Execute a callback with timeout protection using thread pool executor."""
        def callback_wrapper():
            try:
                # Use inspect.signature for proper parameter introspection
                sig = inspect.signature(callback)
                params = list(sig.parameters.keys())
                
                if deactivating and len(params) >= 3 and 'deactivating' in params:
                    # Deactivation callback with deactivating parameter
                    return callback(module_name, context, deactivating=True)
                else:
                    # Standard activation callback
                    return callback(module_name, context)
            except Exception as e:
                # Log callback wrapper errors for debugging
                self.logger.error(f"Error in callback wrapper for {name}: {e}")
                raise
        
        # Submit callback to thread pool with timeout
        future = None
        try:
            future = self._callback_executor.submit(callback_wrapper)
            future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            self.logger.warning(f"Callback {name} timed out after {timeout}s")
            # Attempt to cancel the future (may not work if already running)
            if future is not None:
                future.cancel()
            raise TimeoutError(f"Callback {name} timed out after {timeout} seconds")
        except Exception:
            # Re-raise the original exception from the callback, preserving traceback
            raise
    
    def _execute_deactivation_callbacks(self, module_name: str, context: Optional[ActivationContext]) -> None:
        """Execute all registered deactivation callbacks."""
        # Capture callback list while holding lock, then release lock before dispatch
        callbacks_to_execute = []
        with self._lock:
            callbacks_to_execute = list(self._activation_callbacks.items())
        
        # Execute callbacks outside of lock to prevent deadlock
        for name, callback in callbacks_to_execute:
            try:
                # Execute deactivation callback with timeout protection
                self._execute_callback_with_timeout(name, callback, module_name, context, timeout=30.0, deactivating=True)
            except TimeoutError as e:
                self.logger.error(f"Deactivation callback {name} timed out: {e}")
            except Exception as e:
                self.logger.warning(f"Deactivation callback {name} failed: {e}")
    
    def get_activated_modules(self) -> Set[str]:
        """Get set of currently activated modules."""
        with self._lock:
            return self._activated_modules.copy()
    
    def get_activation_context(self, module_name: str) -> Optional[ActivationContext]:
        """
        Get activation context for a module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            Activation context if module is activated, None otherwise
        """
        with self._lock:
            return self._activation_contexts.get(module_name)
    
    def get_activation_stats(self) -> Dict[str, Any]:
        """Get activation statistics."""
        with self._lock:
            return {
                'current_mode': self._current_mode.value,
                'activated_modules_count': len(self._activated_modules),
                'total_activations': self._activation_count,
                'total_deactivations': self._deactivation_count,
                'last_activation_time': self._last_activation_time,
                'activated_modules': list(self._activated_modules)
            }
    
    def emergency_shutdown(self) -> None:
        """Emergency shutdown of all activations."""
        with self._lock:
            self.logger.critical("Emergency shutdown initiated")
            self._current_mode = ActivationMode.DISABLED
            self._deactivate_all_modules()
            
            # Clear all state
            self._activated_modules.clear()
            self._activation_contexts.clear()
            
            # Trigger deployment controller emergency disable
            self._deployment_controller.emergency_disable()
        
        # Shutdown thread pool executor outside of lock
        if hasattr(self, '_callback_executor') and self._callback_executor:
            try:
                self.logger.info("Shutting down callback thread pool executor")
                self._callback_executor.shutdown(wait=True)
            except Exception as e:
                self.logger.error(f"Error shutting down thread pool executor: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        try:
            self.emergency_shutdown()
        except Exception as e:
            self.logger.error(f"Error during context manager cleanup: {e}")
        return False  # Don't suppress exceptions
    
    def close(self) -> None:
        """Explicit cleanup method for deterministic shutdown."""
        self.emergency_shutdown()
    
    def __del__(self):
        """Destructor to ensure cleanup if not explicitly closed."""
        try:
            if hasattr(self, '_callback_executor') and self._callback_executor:
                self._callback_executor.shutdown(wait=False)
        except Exception:
            # Ignore errors in destructor to prevent issues during interpreter shutdown
            pass
    
    def is_module_activated(self, module_name: str) -> bool:
        """
        Check if a module is currently activated.
        
        Args:
            module_name: Name of the module
            
        Returns:
            True if module is activated, False otherwise
        """
        with self._lock:
            return module_name in self._activated_modules