"""
Epochly Plugin Communication Security Module

This module provides security and validation features for the Epochly Plugin Communication System,
including message validation, sanitization, retry logic, and circuit breaker patterns.

Author: Epochly Development Team
Version: 1.0.0
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import logging

from .communication import PluginMessage

# Configure logging
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when message validation fails."""
    pass


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


@dataclass
class ValidationResult:
    """Result of message validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class SecurityConfig:
    """Configuration for security features."""
    max_message_size: int = 1024 * 1024  # 1MB
    max_payload_depth: int = 10
    max_string_length: int = 10000
    allowed_message_types: Optional[List[str]] = None
    enable_sanitization: bool = True
    retry_max_attempts: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: float = 60.0


class MessageValidator:
    """Validates and sanitizes plugin messages for security."""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        """Initialize the message validator.
        
        Args:
            config: Security configuration. Uses defaults if None.
        """
        self.config = config or SecurityConfig()
        
    def validate_message(self, message: PluginMessage) -> ValidationResult:
        """Validate a plugin message for security and correctness.
        
        Args:
            message: The message to validate.
            
        Returns:
            ValidationResult with validation status and any errors/warnings.
        """
        errors = []
        warnings = []
        
        try:
            # Size validation
            serialized = json.dumps(message.to_dict())
            serialized_size = len(serialized.encode('utf-8'))
            
            if serialized_size > self.config.max_message_size:
                errors.append(
                    f"Message size {serialized_size} bytes exceeds limit of "
                    f"{self.config.max_message_size} bytes"
                )
            
            # Payload depth validation
            if message.payload:
                depth = self._get_dict_depth(message.payload)
                if depth > self.config.max_payload_depth:
                    errors.append(
                        f"Payload nesting depth {depth} exceeds limit of "
                        f"{self.config.max_payload_depth}"
                    )
            
            # Sender ID validation
            if not self._validate_sender_id(message.sender_id):
                errors.append("Invalid sender ID format")
            
            # Recipient ID validation (for requests)
            if hasattr(message, 'recipient_id') and message.recipient_id:
                if not self._validate_sender_id(message.recipient_id):
                    errors.append("Invalid recipient ID format")
            
            # Message type validation
            if (self.config.allowed_message_types and 
                message.message_type not in self.config.allowed_message_types):
                errors.append(
                    f"Message type '{message.message_type}' not in allowed types: "
                    f"{self.config.allowed_message_types}"
                )
            
            # String length validation in payload
            if message.payload:
                string_errors = self._validate_string_lengths(message.payload)
                errors.extend(string_errors)
            
            # Check for potentially dangerous content
            security_warnings = self._check_security_concerns(message)
            warnings.extend(security_warnings)
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            logger.exception("Error during message validation")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def sanitize_message(self, message: PluginMessage) -> PluginMessage:
        """Sanitize a message by removing or modifying potentially dangerous content.
        
        Args:
            message: The message to sanitize.
            
        Returns:
            A sanitized copy of the message.
        """
        if not self.config.enable_sanitization:
            return message
        
        # Create a copy to avoid modifying the original
        sanitized_dict = message.to_dict().copy()
        
        # Sanitize payload
        if sanitized_dict.get('payload'):
            sanitized_dict['payload'] = self._sanitize_payload(sanitized_dict['payload'])
        
        # Truncate overly long strings
        for field in ['sender_id', 'action']:
            if field in sanitized_dict and isinstance(sanitized_dict[field], str):
                if len(sanitized_dict[field]) > self.config.max_string_length:
                    sanitized_dict[field] = sanitized_dict[field][:self.config.max_string_length]
        
        # Recreate message from sanitized data
        return PluginMessage.from_dict(sanitized_dict)
    
    def _get_dict_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate the maximum nesting depth of a dictionary or list.
        
        Args:
            obj: The object to analyze.
            current_depth: Current nesting depth.
            
        Returns:
            Maximum depth found.
        """
        if not isinstance(obj, (dict, list)):
            return current_depth
        
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(
                self._get_dict_depth(value, current_depth + 1)
                for value in obj.values()
            )
        
        if isinstance(obj, list):
            if not obj:
                return current_depth
            return max(
                self._get_dict_depth(item, current_depth + 1)
                for item in obj
            )
        
        return current_depth
    
    def _validate_sender_id(self, sender_id: str) -> bool:
        """Validate sender ID format.
        
        Args:
            sender_id: The sender ID to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        if not isinstance(sender_id, str):
            return False
        
        if not sender_id or len(sender_id) > 255:
            return False
        
        # Check for basic format (alphanumeric, hyphens, underscores, dots)
        import re
        pattern = r'^[a-zA-Z0-9._-]+$'
        return bool(re.match(pattern, sender_id))
    
    def _validate_string_lengths(self, obj: Any, path: str = "") -> List[str]:
        """Validate string lengths in nested objects.
        
        Args:
            obj: The object to validate.
            path: Current path in the object hierarchy.
            
        Returns:
            List of validation errors.
        """
        errors = []
        
        if isinstance(obj, str):
            if len(obj) > self.config.max_string_length:
                errors.append(
                    f"String at {path} length {len(obj)} exceeds limit of "
                    f"{self.config.max_string_length}"
                )
        elif isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                errors.extend(self._validate_string_lengths(value, new_path))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]" if path else f"[{i}]"
                errors.extend(self._validate_string_lengths(item, new_path))
        
        return errors
    
    def _check_security_concerns(self, message: PluginMessage) -> List[str]:
        """Check for potential security concerns in the message.
        
        Args:
            message: The message to check.
            
        Returns:
            List of security warnings.
        """
        warnings = []
        
        # Check for script injection patterns
        if message.payload:
            payload_str = json.dumps(message.payload).lower()
            
            dangerous_patterns = [
                '<script', 'javascript:', 'eval(', 'exec(',
                'import ', '__import__', 'subprocess', 'os.system'
            ]
            
            for pattern in dangerous_patterns:
                if pattern in payload_str:
                    warnings.append(f"Potentially dangerous pattern detected: {pattern}")
        
        return warnings
    
    def _sanitize_payload(self, payload: Any) -> Any:
        """Sanitize payload content recursively.
        
        Args:
            payload: The payload to sanitize.
            
        Returns:
            Sanitized payload.
        """
        if isinstance(payload, str):
            # Remove potentially dangerous characters/patterns
            sanitized = payload.replace('<script', '&lt;script')
            sanitized = sanitized.replace('javascript:', 'javascript_')
            return sanitized[:self.config.max_string_length]
        
        elif isinstance(payload, dict):
            return {
                key: self._sanitize_payload(value)
                for key, value in payload.items()
            }
        
        elif isinstance(payload, list):
            return [self._sanitize_payload(item) for item in payload]
        
        return payload


class RetryPolicy:
    """Implements retry logic with exponential backoff for failed operations."""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        """Initialize the retry policy.
        
        Args:
            config: Security configuration. Uses defaults if None.
        """
        self.config = config or SecurityConfig()
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute a function with retry logic and exponential backoff.
        
        Args:
            func: The async function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.
            
        Returns:
            The result of the function call.
            
        Raises:
            The last exception if all retries fail.
        """
        last_exception = None
        
        for attempt in range(self.config.retry_max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt + 1}/{self.config.retry_max_attempts + 1} failed: {e}"
                )
                
                if attempt == self.config.retry_max_attempts:
                    break
                
                # Calculate delay with exponential backoff
                delay = min(
                    self.config.retry_base_delay * (2 ** attempt),
                    self.config.retry_max_delay
                )
                
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
        
        logger.error(f"All retry attempts failed. Last error: {last_exception}")
        if last_exception is not None:
            raise last_exception
        else:
            raise RuntimeError("All retry attempts failed with no recorded exception")


class CircuitBreaker:
    """Implements circuit breaker pattern to prevent cascading failures."""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        """Initialize the circuit breaker.
        
        Args:
            config: Security configuration. Uses defaults if None.
        """
        self.config = config or SecurityConfig()
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitBreakerState.CLOSED
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function through the circuit breaker.
        
        Args:
            func: The async function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.
            
        Returns:
            The result of the function call.
            
        Raises:
            CircuitBreakerOpenError: If the circuit breaker is open.
            Any exception raised by the function.
        """
        async with self._lock:
            # Check if we should transition from OPEN to HALF_OPEN
            if self.state == CircuitBreakerState.OPEN:
                if (self.last_failure_time and 
                    time.time() - self.last_failure_time > self.config.circuit_breaker_recovery_timeout):
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is OPEN. Failure count: {self.failure_count}"
                    )
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - reset failure count and close circuit if half-open
            async with self._lock:
                if self.state == CircuitBreakerState.HALF_OPEN:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    logger.info("Circuit breaker reset to CLOSED")
            
            return result
            
        except Exception as e:
            # Failure - increment count and potentially open circuit
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.config.circuit_breaker_failure_threshold:
                    self.state = CircuitBreakerState.OPEN
                    logger.warning(
                        f"Circuit breaker opened after {self.failure_count} failures"
                    )
            
            raise e
    
    def get_state(self) -> Dict[str, Any]:
        """Get the current state of the circuit breaker.
        
        Returns:
            Dictionary containing circuit breaker state information.
        """
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "threshold": self.config.circuit_breaker_failure_threshold,
            "recovery_timeout": self.config.circuit_breaker_recovery_timeout
        }
    
    async def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED state."""
        async with self._lock:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            logger.info("Circuit breaker manually reset")


# Global instances
_security_config: Optional[SecurityConfig] = None
_message_validator: Optional[MessageValidator] = None
_retry_policy: Optional[RetryPolicy] = None
_circuit_breaker: Optional[CircuitBreaker] = None


def configure_security(config: SecurityConfig) -> None:
    """Configure global security settings.
    
    Args:
        config: The security configuration to use.
    """
    global _security_config, _message_validator, _retry_policy, _circuit_breaker
    
    _security_config = config
    _message_validator = MessageValidator(config)
    _retry_policy = RetryPolicy(config)
    _circuit_breaker = CircuitBreaker(config)


def get_message_validator() -> MessageValidator:
    """Get the global message validator instance.
    
    Returns:
        The global MessageValidator instance.
    """
    global _message_validator
    
    if _message_validator is None:
        _message_validator = MessageValidator()
    
    return _message_validator


def get_retry_policy() -> RetryPolicy:
    """Get the global retry policy instance.
    
    Returns:
        The global RetryPolicy instance.
    """
    global _retry_policy
    
    if _retry_policy is None:
        _retry_policy = RetryPolicy()
    
    return _retry_policy


def get_circuit_breaker() -> CircuitBreaker:
    """Get the global circuit breaker instance.
    
    Returns:
        The global CircuitBreaker instance.
    """
    global _circuit_breaker
    
    if _circuit_breaker is None:
        _circuit_breaker = CircuitBreaker()
    
    return _circuit_breaker


def reset_security_utilities() -> None:
    """Reset all global security utilities."""
    global _security_config, _message_validator, _retry_policy, _circuit_breaker
    
    _security_config = None
    _message_validator = None
    _retry_policy = None
    _circuit_breaker = None