"""
Workload-aware strategy layer for Epochly.

Provides a clean abstraction between high-level workload optimization strategies
and concrete memory pool implementations.

Author: Epochly Development Team
"""

from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass

from .pool_selector import PoolRecommendation


class WorkloadStrategy(Enum):
    """High-level workload optimization strategies."""
    # Memory-focused strategies
    MEMORY_INTENSIVE = "memory_intensive"
    LARGE_BLOCK_OPTIMIZED = "large_block_optimized"
    FINE_GRAINED = "fine_grained"
    
    # Performance-focused strategies
    CPU_INTENSIVE = "cpu_intensive" 
    LOW_LATENCY = "low_latency"
    LOCK_FREE = "lock_free"
    
    # Framework-specific strategies
    NUMPY_OPTIMIZED = "numpy_optimized"
    PANDAS_OPTIMIZED = "pandas_optimized"
    SKLEARN_OPTIMIZED = "sklearn_optimized"
    
    # Adaptive strategies
    WORKLOAD_AWARE = "workload_aware"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    
    # Default fallback
    GENERAL_PURPOSE = "general_purpose"


@dataclass
class PoolConfiguration:
    """Configuration for a specific pool implementation."""
    pool_type: PoolRecommendation
    config: Dict[str, Any]
    rationale: str
    expected_benefit: float  # Expected performance improvement multiplier


class PoolSelectionStrategy:
    """Maps workload strategies to concrete pool implementations."""
    
    # Core mapping from strategies to pool configurations
    STRATEGY_MAPPING: Dict[WorkloadStrategy, PoolConfiguration] = {
        # Memory-intensive workloads
        WorkloadStrategy.MEMORY_INTENSIVE: PoolConfiguration(
            pool_type=PoolRecommendation.SLAB_ALLOCATOR,
            config={
                "large_slabs": True,
                "numa_aware": True,
                "prefetch_enabled": True,
                "min_slab_size": 65536  # 64KB minimum
            },
            rationale="Memory-intensive workloads benefit from slab allocation to reduce fragmentation",
            expected_benefit=1.5
        ),
        
        WorkloadStrategy.LARGE_BLOCK_OPTIMIZED: PoolConfiguration(
            pool_type=PoolRecommendation.BUDDY_ALLOCATOR,
            config={
                "max_order": 20,  # Up to 1MB blocks
                "coalescing_enabled": True,
                "defragmentation_threshold": 0.3
            },
            rationale="Large block allocations are efficiently handled by buddy allocator",
            expected_benefit=1.4
        ),
        
        WorkloadStrategy.FINE_GRAINED: PoolConfiguration(
            pool_type=PoolRecommendation.SLAB_ALLOCATOR,
            config={
                "small_slabs": True,
                "cache_line_aligned": True,
                "min_slab_size": 64,
                "max_slab_size": 4096
            },
            rationale="Fine-grained allocations benefit from small slab sizes",
            expected_benefit=1.3
        ),
        
        # Performance-focused strategies
        WorkloadStrategy.CPU_INTENSIVE: PoolConfiguration(
            pool_type=PoolRecommendation.HYBRID,
            config={
                "thread_local_caches": True,
                "cache_size": 1048576,  # 1MB per thread
                "batch_allocation": True
            },
            rationale="CPU-intensive workloads benefit from thread-local caching",
            expected_benefit=1.8
        ),
        
        WorkloadStrategy.LOW_LATENCY: PoolConfiguration(
            pool_type=PoolRecommendation.POOL_ALLOCATOR,
            config={
                "pre_allocated": True,
                "pool_size": 104857600,  # 100MB pre-allocated
                "zero_init": False
            },
            rationale="Low latency requires pre-allocated pools",
            expected_benefit=2.0
        ),
        
        WorkloadStrategy.LOCK_FREE: PoolConfiguration(
            pool_type=PoolRecommendation.HYBRID,
            config={
                "lock_free_enabled": True,
                "cas_retry_limit": 1000,
                "backoff_strategy": "exponential"
            },
            rationale="Lock-free operations for high concurrency",
            expected_benefit=2.5
        ),
        
        # Framework-specific optimizations
        WorkloadStrategy.NUMPY_OPTIMIZED: PoolConfiguration(
            pool_type=PoolRecommendation.SLAB_ALLOCATOR,
            config={
                "alignment": 64,  # AVX-512 alignment
                "huge_pages": True,
                "numa_aware": True,
                "numpy_dtype_optimization": True
            },
            rationale="NumPy arrays benefit from aligned memory and huge pages",
            expected_benefit=2.2
        ),
        
        WorkloadStrategy.PANDAS_OPTIMIZED: PoolConfiguration(
            pool_type=PoolRecommendation.HYBRID,
            config={
                "column_store_optimization": True,
                "string_intern_pool": True,
                "category_cache": True
            },
            rationale="Pandas DataFrames benefit from column-oriented optimization",
            expected_benefit=1.8
        ),
        
        WorkloadStrategy.SKLEARN_OPTIMIZED: PoolConfiguration(
            pool_type=PoolRecommendation.BUDDY_ALLOCATOR,
            config={
                "matrix_layout_optimization": True,
                "sparse_matrix_support": True,
                "aligned_allocation": True
            },
            rationale="Scikit-learn models benefit from matrix-optimized allocation",
            expected_benefit=1.6
        ),
        
        # Adaptive strategies
        WorkloadStrategy.WORKLOAD_AWARE: PoolConfiguration(
            pool_type=PoolRecommendation.HYBRID,
            config={
                "adaptive_sizing": True,
                "workload_detection": True,
                "auto_tuning": True
            },
            rationale="Automatically adapts to detected workload patterns",
            expected_benefit=1.7
        ),
        
        WorkloadStrategy.BALANCED: PoolConfiguration(
            pool_type=PoolRecommendation.GENERAL_PURPOSE,
            config={
                "balanced_allocation": True,
                "moderate_caching": True,
                "adaptive_thresholds": True
            },
            rationale="Balanced approach for mixed workloads",
            expected_benefit=1.4
        ),
        
        WorkloadStrategy.CONSERVATIVE: PoolConfiguration(
            pool_type=PoolRecommendation.GENERAL_PURPOSE,
            config={
                "safe_mode": True,
                "fallback_enabled": True,
                "minimal_optimization": True
            },
            rationale="Conservative approach for maximum compatibility",
            expected_benefit=1.1
        ),
        
        # Default
        WorkloadStrategy.GENERAL_PURPOSE: PoolConfiguration(
            pool_type=PoolRecommendation.GENERAL_PURPOSE,
            config={},
            rationale="General purpose allocation for unknown workloads",
            expected_benefit=1.0
        )
    }
    
    def __init__(self):
        """Initialize the pool selection strategy."""
        self._custom_mappings: Dict[WorkloadStrategy, PoolConfiguration] = {}
        self._framework_hints: Dict[str, WorkloadStrategy] = {
            "numpy": WorkloadStrategy.NUMPY_OPTIMIZED,
            "pandas": WorkloadStrategy.PANDAS_OPTIMIZED,
            "sklearn": WorkloadStrategy.SKLEARN_OPTIMIZED,
            "scipy": WorkloadStrategy.NUMPY_OPTIMIZED,  # Similar to NumPy
            "torch": WorkloadStrategy.LARGE_BLOCK_OPTIMIZED,  # Large tensors
            "tensorflow": WorkloadStrategy.LARGE_BLOCK_OPTIMIZED
        }
    
    def get_pool_for_strategy(self, strategy: WorkloadStrategy) -> PoolConfiguration:
        """Get pool configuration for a given strategy."""
        # Check custom mappings first
        if strategy in self._custom_mappings:
            return self._custom_mappings[strategy]
        
        # Fall back to default mappings
        return self.STRATEGY_MAPPING.get(strategy, 
                                         self.STRATEGY_MAPPING[WorkloadStrategy.GENERAL_PURPOSE])
    
    def get_pool_recommendation(self, strategy: WorkloadStrategy) -> PoolRecommendation:
        """Get just the pool type recommendation for a strategy."""
        config = self.get_pool_for_strategy(strategy)
        return config.pool_type
    
    def get_pool_config(self, strategy: WorkloadStrategy) -> Dict[str, Any]:
        """Get the configuration parameters for a strategy."""
        config = self.get_pool_for_strategy(strategy)
        return config.config
    
    def register_custom_mapping(self, 
                               strategy: WorkloadStrategy, 
                               config: PoolConfiguration) -> None:
        """Register a custom strategy mapping."""
        self._custom_mappings[strategy] = config
    
    def get_strategy_for_framework(self, framework: str) -> WorkloadStrategy:
        """Get recommended strategy for a specific framework."""
        return self._framework_hints.get(framework.lower(), 
                                        WorkloadStrategy.GENERAL_PURPOSE)
    
    def get_all_strategies(self) -> List[WorkloadStrategy]:
        """Get all available strategies."""
        return list(WorkloadStrategy)
    
    def explain_strategy(self, strategy: WorkloadStrategy) -> Dict[str, Any]:
        """Get detailed explanation of a strategy."""
        config = self.get_pool_for_strategy(strategy)
        return {
            "strategy": strategy.value,
            "pool_type": config.pool_type.value,
            "rationale": config.rationale,
            "expected_benefit": config.expected_benefit,
            "configuration": config.config
        }