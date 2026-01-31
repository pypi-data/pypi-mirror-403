"""
Epochly Side-Channel Protection

Basic side-channel protection mechanisms for timing attack mitigation
and secure computation patterns in the Epochly security framework.

Author: Epochly Development Team
"""

import time
import random
import secrets
from typing import Any, Callable, Optional, TypeVar, Union
from functools import wraps
from ..utils.logger import get_logger
from ..utils.exceptions import EpochlyError

T = TypeVar('T')

class TimingAttackProtection:
    """
    Protection mechanisms against timing-based side-channel attacks.
    
    Provides constant-time operations and timing normalization
    to prevent information leakage through execution time variations.
    """
    
    def __init__(self, base_delay_ms: float = 1.0, jitter_range: float = 0.5):
        """
        Initialize timing protection.
        
        Args:
            base_delay_ms: Base delay in milliseconds for timing normalization
            jitter_range: Random jitter range as fraction of base delay
        """
        self.logger = get_logger(__name__)
        self.base_delay = base_delay_ms / 1000.0  # Convert to seconds
        self.jitter_range = jitter_range
        self._rng = random.SystemRandom()
    
    def constant_time_compare(self, a: bytes, b: bytes) -> bool:
        """
        Constant-time comparison of byte sequences using hmac.compare_digest.
        
        Args:
            a: First byte sequence
            b: Second byte sequence
            
        Returns:
            True if sequences are equal, False otherwise
        """
        import hmac
        return hmac.compare_digest(a, b)
    
    def constant_time_string_compare(self, a: str, b: str) -> bool:
        """
        Constant-time comparison of strings.
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            True if strings are equal, False otherwise
        """
        return self.constant_time_compare(a.encode('utf-8'), b.encode('utf-8'))
    
    def add_timing_jitter(self, min_delay: Optional[float] = None) -> None:
        """
        Add random timing jitter to prevent timing analysis.
        
        Args:
            min_delay: Minimum delay in seconds (uses base_delay if None)
        """
        delay = min_delay or self.base_delay
        jitter = self._rng.uniform(-self.jitter_range, self.jitter_range) * delay
        total_delay = max(0, delay + jitter)
        
        if total_delay > 0:
            time.sleep(total_delay)
    
    def normalize_execution_time(self, target_time: float) -> Callable:
        """
        Decorator to normalize function execution time.
        
        Args:
            target_time: Target execution time in seconds
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                start_time = time.perf_counter()
                
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    elapsed = time.perf_counter() - start_time
                    remaining = target_time - elapsed
                    
                    if remaining > 0:
                        # Add remaining time plus small jitter
                        jitter = self._rng.uniform(0, self.jitter_range * target_time)
                        time.sleep(remaining + jitter)
                    else:
                        # Function took longer than target, add minimal jitter
                        self.add_timing_jitter(0.001)  # 1ms minimum
            
            return wrapper
        return decorator


class MemoryProtection:
    """
    Memory protection mechanisms to prevent memory-based side-channel attacks.
    
    Provides secure memory clearing and access pattern obfuscation.
    """
    
    def __init__(self):
        """Initialize memory protection."""
        self.logger = get_logger(__name__)
    
    def secure_zero(self, data: Union[bytearray, memoryview]) -> None:
        """
        Securely zero memory to prevent data recovery.
        
        Args:
            data: Memory buffer to zero
        """
        if isinstance(data, (bytearray, memoryview)):
            # Overwrite with random data first
            for i in range(len(data)):
                data[i] = secrets.randbits(8)
            
            # Then zero the memory
            for i in range(len(data)):
                data[i] = 0
        else:
            self.logger.warning("secure_zero called on immutable data type")
    
    def obfuscate_access_pattern(self, data_size: int, access_indices: list) -> list:
        """
        Obfuscate memory access patterns to prevent cache-based attacks.
        
        Args:
            data_size: Size of the data structure
            access_indices: Actual indices to access
            
        Returns:
            Obfuscated access pattern with dummy accesses
        """
        # Create dummy accesses to mask real pattern
        dummy_count = max(10, len(access_indices) * 2)
        dummy_indices = [secrets.randbelow(data_size) for _ in range(dummy_count)]
        
        # Combine real and dummy accesses
        all_indices = list(access_indices) + dummy_indices
        random.shuffle(all_indices)
        
        return all_indices


class CacheProtection:
    """
    Protection against cache-based side-channel attacks.
    
    Provides cache-aware algorithms and access pattern randomization.
    """
    
    def __init__(self, cache_line_size: int = 64):
        """
        Initialize cache protection.
        
        Args:
            cache_line_size: CPU cache line size in bytes
        """
        self.logger = get_logger(__name__)
        self.cache_line_size = cache_line_size
    
    def cache_oblivious_search(self, data: list, target: Any) -> int:
        """
        Cache-oblivious linear search to prevent timing attacks.
        
        Args:
            data: List to search
            target: Target value to find
            
        Returns:
            Index of target or -1 if not found
        """
        result_index = -1
        
        # Always scan entire list to maintain constant access pattern
        for i, item in enumerate(data):
            # Use constant-time comparison
            if isinstance(item, (str, bytes)):
                if isinstance(target, str):
                    is_match = TimingAttackProtection().constant_time_string_compare(str(item), target)
                else:
                    is_match = TimingAttackProtection().constant_time_compare(
                        str(item).encode(), str(target).encode()
                    )
            else:
                is_match = (item == target)
            
            # Update result without branching
            result_index = i if is_match and result_index == -1 else result_index
        
        return result_index
    
    def randomize_data_layout(self, data: list) -> tuple:
        """
        Randomize data layout to prevent cache-based analysis.
        
        Args:
            data: Original data list
            
        Returns:
            Tuple of (randomized_data, index_mapping)
        """
        indices = list(range(len(data)))
        random.shuffle(indices)
        
        randomized_data = [data[i] for i in indices]
        
        # Create reverse mapping for reconstruction
        index_mapping = {new_idx: old_idx for old_idx, new_idx in enumerate(indices)}
        
        return randomized_data, index_mapping


class SideChannelProtector:
    """
    Main side-channel protection coordinator.
    
    Combines timing, memory, and cache protection mechanisms
    for comprehensive side-channel attack mitigation.
    """
    
    def __init__(self, enable_timing: bool = True, enable_memory: bool = True,
                 enable_cache: bool = True):
        """
        Initialize side-channel protector.
        
        Args:
            enable_timing: Enable timing attack protection
            enable_memory: Enable memory protection
            enable_cache: Enable cache protection
        """
        self.logger = get_logger(__name__)
        
        self.timing_protection = TimingAttackProtection() if enable_timing else None
        self.memory_protection = MemoryProtection() if enable_memory else None
        self.cache_protection = CacheProtection() if enable_cache else None
        
        self.logger.debug(f"Side-channel protection initialized: "
                         f"timing={enable_timing}, memory={enable_memory}, cache={enable_cache}")
    
    def secure_operation(self, operation: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute operation with side-channel protection.
        
        Args:
            operation: Function to execute securely
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            Result of the operation
        """
        try:
            # Add timing jitter before operation
            if self.timing_protection:
                self.timing_protection.add_timing_jitter()
            
            # Execute operation
            result = operation(*args, **kwargs)
            
            # Add timing jitter after operation
            if self.timing_protection:
                self.timing_protection.add_timing_jitter()
            
            return result
            
        except Exception as e:
            # Ensure consistent timing even on errors
            if self.timing_protection:
                self.timing_protection.add_timing_jitter()
            raise EpochlyError(f"Secure operation failed: {e}")
    
    def secure_compare(self, a: Union[str, bytes], b: Union[str, bytes]) -> bool:
        """
        Perform secure comparison resistant to timing attacks.
        
        Args:
            a: First value to compare
            b: Second value to compare
            
        Returns:
            True if values are equal, False otherwise
        """
        if not self.timing_protection:
            return a == b
        
        if isinstance(a, str) and isinstance(b, str):
            return self.timing_protection.constant_time_string_compare(a, b)
        elif isinstance(a, bytes) and isinstance(b, bytes):
            return self.timing_protection.constant_time_compare(a, b)
        else:
            # Convert to strings for comparison
            return self.timing_protection.constant_time_string_compare(str(a), str(b))
    
    def secure_search(self, data: list, target: Any) -> int:
        """
        Perform secure search resistant to cache attacks.
        
        Args:
            data: List to search
            target: Target value to find
            
        Returns:
            Index of target or -1 if not found
        """
        if not self.cache_protection:
            try:
                return data.index(target)
            except ValueError:
                return -1
        
        return self.cache_protection.cache_oblivious_search(data, target)
    
    def get_protection_status(self) -> dict:
        """
        Get current protection status.
        
        Returns:
            Dictionary with protection status
        """
        return {
            'timing_protection': self.timing_protection is not None,
            'memory_protection': self.memory_protection is not None,
            'cache_protection': self.cache_protection is not None,
            'protection_level': 'high' if all([
                self.timing_protection,
                self.memory_protection,
                self.cache_protection
            ]) else 'partial'
        }


# Global instance for easy access
_global_protector: Optional[SideChannelProtector] = None

def get_side_channel_protector() -> SideChannelProtector:
    """
    Get global side-channel protector instance.
    
    Returns:
        Global SideChannelProtector instance
    """
    global _global_protector
    if _global_protector is None:
        _global_protector = SideChannelProtector()
    return _global_protector

def secure_compare(a: Union[str, bytes], b: Union[str, bytes]) -> bool:
    """
    Convenience function for secure comparison.
    
    Args:
        a: First value to compare
        b: Second value to compare
        
    Returns:
        True if values are equal, False otherwise
    """
    return get_side_channel_protector().secure_compare(a, b)

def secure_search(data: list, target: Any) -> int:
    """
    Convenience function for secure search.
    
    Args:
        data: List to search
        target: Target value to find
        
    Returns:
        Index of target or -1 if not found
    """
    return get_side_channel_protector().secure_search(data, target)