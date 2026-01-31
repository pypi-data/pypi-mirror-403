"""
Optimized FineGrainedMemoryPool configuration for testing.

This module provides a way to configure the pool with fewer buckets for testing.
"""

from typing import Optional
from epochly.memory.fine_grained_memory_pool import FineGrainedMemoryPool


class OptimizedFineGrainedMemoryPool(FineGrainedMemoryPool):
    """Fine-grained memory pool with optimized bucket configuration."""
    
    # Reduced bucket configuration for testing
    SMALL_BLOCK_MAX = 256      # Same as original
    MEDIUM_BLOCK_MAX = 1024    # Reduced from 4096 to 1024
    BUCKET_SIZE_STEP = 64      # Increased from 8 to 64
    
    def _init_atomic_buckets(self) -> None:
        """Initialize fewer atomic buckets for better test performance."""
        bucket_count = 0
        
        # Small blocks: 64, 128, 192, 256 (4 buckets instead of 32)
        for size in range(self.BUCKET_SIZE_STEP, self.SMALL_BLOCK_MAX + 1, self.BUCKET_SIZE_STEP):
            bucket_id = f"small_{size}"
            self._atomic_buckets[size] = self._create_bucket(size, bucket_id)
            bucket_count += 1
        
        # Medium blocks: 320, 384, ..., 1024 (12 buckets instead of 480)
        for size in range(self.SMALL_BLOCK_MAX + self.BUCKET_SIZE_STEP,
                         self.MEDIUM_BLOCK_MAX + 1, self.BUCKET_SIZE_STEP):
            bucket_id = f"medium_{size}"
            self._atomic_buckets[size] = self._create_bucket(size, bucket_id)
            bucket_count += 1
        
        # Total: 16 buckets instead of 512
        # No print to avoid test noise
    
    def _create_bucket(self, size, bucket_id):
        """Create a bucket (allows for mocking in tests)."""
        from epochly.memory.fine_grained_memory_pool import AtomicBucket
        return AtomicBucket(size, bucket_id)
    
    def _get_size_bucket(self, size: int) -> Optional[int]:
        """Get the appropriate size bucket for a given size."""
        if size <= self.SMALL_BLOCK_MAX:
            # Round up to nearest 64-byte bucket
            return ((size + self.BUCKET_SIZE_STEP - 1) // self.BUCKET_SIZE_STEP) * self.BUCKET_SIZE_STEP
        elif size <= self.MEDIUM_BLOCK_MAX:
            # Round up to nearest 64-byte bucket
            return ((size + self.BUCKET_SIZE_STEP - 1) // self.BUCKET_SIZE_STEP) * self.BUCKET_SIZE_STEP
        else:
            # Large blocks use fallback allocation
            return None