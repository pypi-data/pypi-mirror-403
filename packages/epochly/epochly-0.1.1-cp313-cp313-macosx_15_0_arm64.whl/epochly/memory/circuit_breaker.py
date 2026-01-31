"""
Epochly Memory Foundation - Circuit Breaker Implementation

This module implements circuit breaker patterns to prevent infinite loops
and pathological behaviors in memory allocation operations.

Author: Epochly Memory Foundation Team
"""

import time
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .atomic_primitives import AtomicCounter
from .exceptions import AllocationError


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures before opening
    timeout_seconds: float = 60.0       # Time before trying half-open
    success_threshold: int = 3          # Successes to close from half-open
    max_iterations: int = 1000          # Max iterations before breaking
    max_time_seconds: float = 0.1       # Max time before breaking


class CircuitBreaker:
    """
    Circuit breaker for preventing infinite loops and cascading failures.
    
    Monitors operation failures and automatically opens the circuit
    when failure thresholds are exceeded, preventing further attempts
    until the system has time to recover.
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name for identification and logging
            config: Configuration parameters
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        # State management
        self.state = CircuitBreakerState.CLOSED
        self.last_failure_time = 0.0
        self.last_success_time = 0.0
        
        # Atomic counters for thread safety
        self.failure_count = AtomicCounter()
        self.success_count = AtomicCounter()
        self.total_calls = AtomicCounter()
        self.total_failures = AtomicCounter()
        self.total_successes = AtomicCounter()
        self.circuit_opens = AtomicCounter()
        self.fast_failures = AtomicCounter()
        
        # Thread safety
        self._lock = threading.RLock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            AllocationError: If circuit is open or function fails
        """
        self.total_calls.increment()
        
        with self._lock:
            # Check if circuit is open
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count.store(0)
                else:
                    self.fast_failures.increment()
                    raise AllocationError(f"Circuit breaker '{self.name}' is OPEN")
            
            # Execute function with monitoring
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            
            except Exception:
                elapsed = time.perf_counter() - start_time
                self._on_failure(elapsed)
                raise
    
    def call_with_iteration_limit(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with iteration and time limits.
        
        Args:
            func: Function to execute (should accept iteration_limit and timeout)
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            AllocationError: If limits exceeded or circuit open
        """
        self.total_calls.increment()
        
        with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count.store(0)
                else:
                    self.fast_failures.increment()
                    raise AllocationError(f"Circuit breaker '{self.name}' is OPEN")
            
            # Add limits to kwargs
            kwargs['max_iterations'] = self.config.max_iterations
            kwargs['timeout_seconds'] = self.config.max_time_seconds
            
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            
            except Exception:
                elapsed = time.perf_counter() - start_time
                self._on_failure(elapsed)
                raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (time.perf_counter() - self.last_failure_time) >= self.config.timeout_seconds
    
    def _on_success(self) -> None:
        """Handle successful operation."""
        self.last_success_time = time.perf_counter()
        self.total_successes.increment()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count.increment()
            if self.success_count.load() >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count.store(0)
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count.store(0)  # Reset failure count on success
    
    def _on_failure(self, elapsed_time: float) -> None:
        """Handle failed operation."""
        self.last_failure_time = time.perf_counter()
        self.total_failures.increment()
        self.failure_count.increment()
        
        # Check if we should open the circuit
        if (self.state == CircuitBreakerState.CLOSED and 
            self.failure_count.load() >= self.config.failure_threshold):
            self.state = CircuitBreakerState.OPEN
            self.circuit_opens.increment()
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Any failure in half-open state reopens the circuit
            self.state = CircuitBreakerState.OPEN
            self.circuit_opens.increment()
    
    def force_open(self) -> None:
        """Manually open the circuit."""
        with self._lock:
            self.state = CircuitBreakerState.OPEN
            self.circuit_opens.increment()
    
    def force_close(self) -> None:
        """Manually close the circuit."""
        with self._lock:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count.store(0)
            self.success_count.store(0)
    
    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        with self._lock:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count.store(0)
            self.success_count.store(0)
            self.last_failure_time = 0.0
            self.last_success_time = 0.0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        total_calls = self.total_calls.load()
        total_failures = self.total_failures.load()
        total_successes = self.total_successes.load()
        
        failure_rate = (total_failures / total_calls * 100) if total_calls > 0 else 0.0
        success_rate = (total_successes / total_calls * 100) if total_calls > 0 else 0.0
        
        return {
            'name': self.name,
            'state': self.state.value,
            'total_calls': total_calls,
            'total_failures': total_failures,
            'total_successes': total_successes,
            'current_failure_count': self.failure_count.load(),
            'current_success_count': self.success_count.load(),
            'circuit_opens': self.circuit_opens.load(),
            'fast_failures': self.fast_failures.load(),
            'failure_rate_percent': failure_rate,
            'success_rate_percent': success_rate,
            'last_failure_time': self.last_failure_time,
            'last_success_time': self.last_success_time,
            'config': {
                'failure_threshold': self.config.failure_threshold,
                'timeout_seconds': self.config.timeout_seconds,
                'success_threshold': self.config.success_threshold,
                'max_iterations': self.config.max_iterations,
                'max_time_seconds': self.config.max_time_seconds
            }
        }


class MemoryCircuitBreakerManager:
    """
    Manager for memory-specific circuit breakers.
    
    Provides pre-configured circuit breakers for different memory
    operations with appropriate thresholds and timeouts.
    """
    
    def __init__(self):
        """Initialize circuit breaker manager."""
        self.breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
        
        # Create default circuit breakers
        self._create_default_breakers()
    
    def _create_default_breakers(self) -> None:
        """Create default circuit breakers for memory operations."""
        # Allocation circuit breaker - more sensitive
        allocation_config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout_seconds=30.0,
            success_threshold=2,
            max_iterations=500,
            max_time_seconds=0.05  # 50ms
        )
        self.breakers['allocation'] = CircuitBreaker('allocation', allocation_config)
        
        # Deallocation circuit breaker - less sensitive
        deallocation_config = CircuitBreakerConfig(
            failure_threshold=5,
            timeout_seconds=60.0,
            success_threshold=3,
            max_iterations=1000,
            max_time_seconds=0.1  # 100ms
        )
        self.breakers['deallocation'] = CircuitBreaker('deallocation', deallocation_config)
        
        # Coalescing circuit breaker - very sensitive to prevent fragmentation loops
        coalescing_config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout_seconds=120.0,
            success_threshold=5,
            max_iterations=100,
            max_time_seconds=0.02  # 20ms
        )
        self.breakers['coalescing'] = CircuitBreaker('coalescing', coalescing_config)
    
    def get_breaker(self, name: str) -> CircuitBreaker:
        """Get circuit breaker by name."""
        with self._lock:
            if name not in self.breakers:
                # Create default circuit breaker
                self.breakers[name] = CircuitBreaker(name)
            return self.breakers[name]
    
    def create_breaker(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Create custom circuit breaker."""
        with self._lock:
            breaker = CircuitBreaker(name, config)
            self.breakers[name] = breaker
            return breaker
    
    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        with self._lock:
            return {name: breaker.get_statistics() 
                   for name, breaker in self.breakers.items()}
    
    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self.breakers.values():
                breaker.reset()


# Global circuit breaker manager instance
_circuit_breaker_manager = None
_manager_lock = threading.Lock()


def get_circuit_breaker_manager() -> MemoryCircuitBreakerManager:
    """Get global circuit breaker manager instance."""
    global _circuit_breaker_manager
    
    if _circuit_breaker_manager is None:
        with _manager_lock:
            if _circuit_breaker_manager is None:
                _circuit_breaker_manager = MemoryCircuitBreakerManager()
    
    return _circuit_breaker_manager


def get_memory_circuit_breaker(operation: str) -> CircuitBreaker:
    """Get circuit breaker for specific memory operation."""
    manager = get_circuit_breaker_manager()
    return manager.get_breaker(operation)