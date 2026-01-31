"""
Epochly Memory Foundation - Canary Checksums Module

This module implements comprehensive canary checksum techniques for memory corruption
detection, based on production allocator patterns from jemalloc, TCMalloc, and Scudo.

Features:
- Object-level front/rear guard zones (redzone protection)
- Magic number patterns for use-after-free detection
- CRC32 checksums for metadata integrity
- Sampling-based validation for performance optimization
- Buffer overflow and underflow detection

Author: Epochly Development Team
"""

import struct
import random
import time
import threading
from typing import Optional, Tuple, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CanaryType(Enum):
    """Types of canary protection patterns."""
    FRONT_GUARD = "front_guard"      # Pre-object guard zone
    REAR_GUARD = "rear_guard"        # Post-object guard zone
    MAGIC_FREE = "magic_free"        # Use-after-free detection
    MAGIC_ALLOC = "magic_alloc"      # Allocated object pattern
    HEADER_CRC = "header_crc"        # Metadata integrity


class CorruptionType(Enum):
    """Types of memory corruption detected."""
    BUFFER_OVERFLOW = "buffer_overflow"
    BUFFER_UNDERFLOW = "buffer_underflow"
    USE_AFTER_FREE = "use_after_free"
    DOUBLE_FREE = "double_free"
    HEADER_CORRUPTION = "header_corruption"
    UNKNOWN = "unknown"


class CanaryConfig:
    """Configuration for canary checksum system."""
    
    # Magic patterns (based on SLUB allocator and production systems)
    FRONT_GUARD_PATTERN = 0xAA  # Front guard byte (buffer underflow detection)
    REAR_GUARD_PATTERN = 0xBB   # Rear guard byte (buffer overflow detection)
    FREE_PATTERN = 0x6B         # POISON_FREE pattern (use-after-free detection)
    ALLOC_PATTERN = 0x5A        # POISON_INUSE pattern (allocated objects)
    
    # Guard zone sizes (aligned to 8-byte boundaries)
    DEFAULT_GUARD_SIZE = 8      # 8 bytes front/rear guards
    LARGE_GUARD_SIZE = 16       # 16 bytes for large objects (>4KB)
    
    # Sampling configuration (GWP-ASan style)
    DEFAULT_SAMPLE_RATE = 0.1   # 10% sampling for performance
    CRITICAL_SAMPLE_RATE = 1.0  # 100% sampling for critical allocations
    
    # CRC polynomial (CRC32-IEEE 802.3)
    CRC32_POLYNOMIAL = 0xEDB88320
    
    def __init__(self, 
                 guard_size: int = DEFAULT_GUARD_SIZE,
                 sample_rate: float = DEFAULT_SAMPLE_RATE,
                 enable_sampling: bool = True):
        """Initialize canary configuration."""
        self.guard_size = max(8, (guard_size + 7) & ~7)  # Align to 8 bytes
        self.sample_rate = max(0.0, min(1.0, sample_rate))
        self.enable_sampling = enable_sampling
        
        # Thread-local random state for sampling decisions
        self._local = threading.local()
    
    def should_protect(self, object_size: int) -> bool:
        """Determine if object should have canary protection."""
        if not self.enable_sampling:
            return True
        
        # Always protect large objects (>4KB)
        if object_size > 4096:
            return True
        
        # Use thread-local random for consistent sampling
        if not hasattr(self._local, 'random'):
            self._local.random = random.Random()
            self._local.random.seed(int(time.time() * 1000) + threading.get_ident())
        
        return self._local.random.random() < self.sample_rate


class CanaryValidator:
    """High-performance canary checksum validator."""
    
    def __init__(self, config: Optional[CanaryConfig] = None):
        """Initialize canary validator."""
        self.config = config or CanaryConfig()
        self._corruption_count = 0
        self._validation_count = 0
        self._lock = threading.Lock()
    
    def _compute_crc32(self, data: bytes) -> int:
        """Compute CRC32 checksum using IEEE 802.3 polynomial."""
        crc = 0xFFFFFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ self.config.CRC32_POLYNOMIAL
                else:
                    crc >>= 1
        return crc ^ 0xFFFFFFFF
    
    def _fill_pattern(self, memory_view: memoryview, pattern: int) -> None:
        """Fill memory region with specified pattern byte."""
        pattern_bytes = bytes([pattern] * len(memory_view))
        memory_view[:] = pattern_bytes
    
    def _check_pattern(self, memory_view: memoryview, pattern: int) -> bool:
        """Check if memory region contains expected pattern."""
        expected = bytes([pattern] * len(memory_view))
        return bytes(memory_view) == expected
    
    def install_canaries(self, 
                        base_memory: memoryview, 
                        object_offset: int, 
                        object_size: int) -> Dict[str, Any]:
        """
        Install canary protection around allocated object.
        
        Args:
            base_memory: Base memory view containing the object
            object_offset: Offset of object within base memory
            object_size: Size of allocated object
            
        Returns:
            Dictionary with canary metadata for validation
        """
        if not self.config.should_protect(object_size):
            return {'protected': False}
        
        guard_size = self.config.guard_size
        
        # Calculate guard zone boundaries
        front_guard_start = object_offset - guard_size
        front_guard_end = object_offset
        rear_guard_start = object_offset + object_size
        rear_guard_end = rear_guard_start + guard_size
        
        # Validate boundaries
        if (front_guard_start < 0 or 
            rear_guard_end > len(base_memory)):
            logger.warning("Cannot install canaries: insufficient space")
            return {'protected': False}
        
        try:
            # Install front guard (buffer underflow detection)
            front_guard = base_memory[front_guard_start:front_guard_end]
            self._fill_pattern(front_guard, self.config.FRONT_GUARD_PATTERN)
            
            # Install rear guard (buffer overflow detection)
            rear_guard = base_memory[rear_guard_start:rear_guard_end]
            self._fill_pattern(rear_guard, self.config.REAR_GUARD_PATTERN)
            
            # Fill object with allocation pattern
            object_memory = base_memory[object_offset:object_offset + object_size]
            self._fill_pattern(object_memory, self.config.ALLOC_PATTERN)
            
            # Compute metadata checksum
            metadata = struct.pack('<QQQ', object_offset, object_size, guard_size)
            metadata_crc = self._compute_crc32(metadata)
            
            return {
                'protected': True,
                'object_offset': object_offset,
                'object_size': object_size,
                'guard_size': guard_size,
                'front_guard_start': front_guard_start,
                'rear_guard_start': rear_guard_start,
                'metadata_crc': metadata_crc,
                'install_time': time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to install canaries: {e}")
            return {'protected': False, 'error': str(e)}
    
    def validate_canaries(self, 
                         base_memory: memoryview, 
                         canary_metadata: Dict[str, Any]) -> Tuple[bool, Optional[CorruptionType]]:
        """
        Validate canary protection and detect corruption.
        
        Args:
            base_memory: Base memory view containing the object
            canary_metadata: Metadata returned from install_canaries
            
        Returns:
            Tuple of (is_valid, corruption_type)
        """
        with self._lock:
            self._validation_count += 1
        
        if not canary_metadata.get('protected', False):
            return True, None  # No protection installed
        
        try:
            object_offset = canary_metadata['object_offset']
            object_size = canary_metadata['object_size']
            guard_size = canary_metadata['guard_size']
            front_guard_start = canary_metadata['front_guard_start']
            rear_guard_start = canary_metadata['rear_guard_start']
            expected_crc = canary_metadata['metadata_crc']
            
            # Validate metadata integrity
            metadata = struct.pack('<QQQ', object_offset, object_size, guard_size)
            actual_crc = self._compute_crc32(metadata)
            if actual_crc != expected_crc:
                self._record_corruption(CorruptionType.HEADER_CORRUPTION)
                return False, CorruptionType.HEADER_CORRUPTION
            
            # Check front guard (buffer underflow detection)
            front_guard = base_memory[front_guard_start:object_offset]
            if not self._check_pattern(front_guard, self.config.FRONT_GUARD_PATTERN):
                self._record_corruption(CorruptionType.BUFFER_UNDERFLOW)
                return False, CorruptionType.BUFFER_UNDERFLOW
            
            # Check rear guard (buffer overflow detection)
            rear_guard = base_memory[rear_guard_start:rear_guard_start + guard_size]
            if not self._check_pattern(rear_guard, self.config.REAR_GUARD_PATTERN):
                self._record_corruption(CorruptionType.BUFFER_OVERFLOW)
                return False, CorruptionType.BUFFER_OVERFLOW
            
            return True, None
            
        except Exception as e:
            logger.error(f"Canary validation failed: {e}")
            self._record_corruption(CorruptionType.UNKNOWN)
            return False, CorruptionType.UNKNOWN
    
    def mark_freed(self, 
                   base_memory: memoryview, 
                   canary_metadata: Dict[str, Any]) -> None:
        """
        Mark object as freed with poison pattern for use-after-free detection.
        
        Args:
            base_memory: Base memory view containing the object
            canary_metadata: Metadata from install_canaries
        """
        if not canary_metadata.get('protected', False):
            return
        
        try:
            object_offset = canary_metadata['object_offset']
            object_size = canary_metadata['object_size']
            
            # Fill object with free pattern (use-after-free detection)
            object_memory = base_memory[object_offset:object_offset + object_size]
            self._fill_pattern(object_memory, self.config.FREE_PATTERN)
            
            # Update metadata to reflect freed state
            canary_metadata['freed'] = True
            canary_metadata['free_time'] = time.time()
            
        except Exception as e:
            logger.error(f"Failed to mark object as freed: {e}")
    
    def detect_use_after_free(self, 
                             base_memory: memoryview, 
                             canary_metadata: Dict[str, Any]) -> bool:
        """
        Detect use-after-free by checking for free pattern.
        
        Args:
            base_memory: Base memory view containing the object
            canary_metadata: Metadata from install_canaries
            
        Returns:
            True if use-after-free detected
        """
        if not canary_metadata.get('protected', False):
            return False
        
        if not canary_metadata.get('freed', False):
            return False  # Object not marked as freed
        
        try:
            object_offset = canary_metadata['object_offset']
            object_size = canary_metadata['object_size']
            
            # Check if object still contains free pattern
            object_memory = base_memory[object_offset:object_offset + object_size]
            if not self._check_pattern(object_memory, self.config.FREE_PATTERN):
                self._record_corruption(CorruptionType.USE_AFTER_FREE)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Use-after-free detection failed: {e}")
            return False
    
    def _record_corruption(self, corruption_type: CorruptionType) -> None:
        """Record corruption detection for statistics."""
        with self._lock:
            self._corruption_count += 1
        
        logger.critical(
            f"Memory corruption detected: {corruption_type.value} "
            f"(total corruptions: {self._corruption_count})"
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get canary validation statistics."""
        with self._lock:
            return {
                'validation_count': self._validation_count,
                'corruption_count': self._corruption_count,
                'corruption_rate': (
                    self._corruption_count / max(1, self._validation_count)
                ),
                'config': {
                    'guard_size': self.config.guard_size,
                    'sample_rate': self.config.sample_rate,
                    'enable_sampling': self.config.enable_sampling
                }
            }
    
    def reset_statistics(self) -> None:
        """Reset validation statistics."""
        with self._lock:
            self._validation_count = 0
            self._corruption_count = 0


# Global canary validator instance
_global_validator: Optional[CanaryValidator] = None
_validator_lock = threading.Lock()


def get_global_validator() -> CanaryValidator:
    """Get or create global canary validator instance."""
    global _global_validator
    
    if _global_validator is None:
        with _validator_lock:
            if _global_validator is None:
                _global_validator = CanaryValidator()
    
    return _global_validator


def configure_global_validator(config: CanaryConfig) -> None:
    """Configure global canary validator."""
    global _global_validator
    
    with _validator_lock:
        _global_validator = CanaryValidator(config)


# Convenience functions for common operations
def install_object_canaries(base_memory: memoryview, 
                           object_offset: int, 
                           object_size: int) -> Dict[str, Any]:
    """Install canaries around object using global validator."""
    validator = get_global_validator()
    return validator.install_canaries(base_memory, object_offset, object_size)


def validate_object_canaries(base_memory: memoryview, 
                            canary_metadata: Dict[str, Any]) -> Tuple[bool, Optional[CorruptionType]]:
    """Validate object canaries using global validator."""
    validator = get_global_validator()
    return validator.validate_canaries(base_memory, canary_metadata)


def mark_object_freed(base_memory: memoryview, 
                     canary_metadata: Dict[str, Any]) -> None:
    """Mark object as freed using global validator."""
    validator = get_global_validator()
    validator.mark_freed(base_memory, canary_metadata)


def detect_object_use_after_free(base_memory: memoryview, 
                                canary_metadata: Dict[str, Any]) -> bool:
    """Detect use-after-free using global validator."""
    validator = get_global_validator()
    return validator.detect_use_after_free(base_memory, canary_metadata)