"""
Fixed FineGrainedMemoryPool for testing - removes problematic __del__ method.
"""

from epochly.memory.fine_grained_memory_pool_optimized import OptimizedFineGrainedMemoryPool


class FixedFineGrainedMemoryPool(OptimizedFineGrainedMemoryPool):
    """Fine-grained memory pool with __del__ disabled to prevent double cleanup."""
    
    def __del__(self):
        """Override to disable automatic cleanup in __del__."""
        # Do nothing - explicit cleanup only
        pass
    
    def _init_atomic_buckets(self) -> None:
        """Initialize fewer atomic buckets without print statements."""
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
        # No print statement to avoid I/O overhead in tests