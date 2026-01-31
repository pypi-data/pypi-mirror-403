"""
Epochly Memory Pool Selector

This module implements the MemoryPoolSelector component that provides intelligent
pool recommendations based on workload analysis and memory profiling data.

Author: Epochly Development Team
"""

import time
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import statistics

from .workload_detector import WorkloadPattern
from .memory_profiler import MemoryStats, AllocationPattern
from ...utils.exceptions import EpochlyError


class PoolRecommendation(Enum):
    """Pool recommendation types."""
    SLAB_ALLOCATOR = "slab_allocator"
    BUDDY_ALLOCATOR = "buddy_allocator"
    STACK_ALLOCATOR = "stack_allocator"
    POOL_ALLOCATOR = "pool_allocator"
    GENERAL_PURPOSE = "general_purpose"
    HYBRID = "hybrid"


@dataclass
class PoolScore:
    """Score for a memory pool recommendation."""
    pool_type: PoolRecommendation
    score: float
    confidence: float
    reasoning: List[str] = field(default_factory=list)
    performance_estimate: float = 1.0  # Relative performance multiplier
    memory_efficiency: float = 1.0     # Memory efficiency ratio


@dataclass
class SelectionCriteria:
    """Criteria for pool selection."""
    workload_pattern: WorkloadPattern
    allocation_pattern: AllocationPattern
    memory_stats: MemoryStats
    thread_count: int = 1
    performance_priority: float = 0.5  # 0.0 = memory efficiency, 1.0 = speed
    fragmentation_tolerance: float = 0.3
    size_distribution: Optional[Dict[str, Any]] = None


class MemoryPoolSelector:
    """
    Memory pool selector for intelligent pool recommendations.
    
    This component analyzes workload characteristics and memory usage patterns
    to recommend the most suitable memory pool configuration.
    """
    
    def __init__(self):
        """Initialize the memory pool selector."""
        self._lock = threading.RLock()
        
        # Pool characteristics database
        self._pool_characteristics = self._initialize_pool_characteristics()
        
        # Selection history for learning
        self._selection_history: List[Dict[str, Any]] = []
        self._performance_feedback: Dict[str, List[float]] = {}
        
        # Scoring weights
        self._scoring_weights = {
            "allocation_speed": 0.3,
            "memory_efficiency": 0.25,
            "fragmentation_resistance": 0.2,
            "thread_safety": 0.15,
            "scalability": 0.1
        }
    
    def recommend_pool(
        self, 
        criteria: SelectionCriteria,
        candidate_pools: Optional[List[PoolRecommendation]] = None
    ) -> List[PoolScore]:
        """
        Recommend memory pools based on selection criteria.
        
        Args:
            criteria: Selection criteria including workload and memory patterns
            candidate_pools: Optional list of pools to consider (all if None)
            
        Returns:
            List of pool scores sorted by recommendation strength
        """
        if candidate_pools is None:
            candidate_pools = list(PoolRecommendation)
        
        with self._lock:
            scores = []
            
            for pool_type in candidate_pools:
                score = self._calculate_pool_score(pool_type, criteria)
                scores.append(score)
            
            # Sort by score (descending)
            scores.sort(key=lambda x: x.score, reverse=True)
            
            # Record selection for learning
            self._record_selection(criteria, scores)
            
            return scores
    
    def get_best_recommendation(self, criteria: SelectionCriteria) -> PoolScore:
        """
        Get the single best pool recommendation.
        
        Args:
            criteria: Selection criteria
            
        Returns:
            Best pool recommendation
        """
        recommendations = self.recommend_pool(criteria)
        if not recommendations:
            raise EpochlyError("No pool recommendations available")
        
        return recommendations[0]
    
    def recommend_hybrid_configuration(
        self, 
        criteria: SelectionCriteria
    ) -> Dict[str, Any]:
        """
        Recommend a hybrid pool configuration for complex workloads.
        
        Args:
            criteria: Selection criteria
            
        Returns:
            Hybrid configuration with multiple pools
        """
        with self._lock:
            config = {
                "primary_pool": None,
                "secondary_pools": [],
                "allocation_strategy": "size_based",
                "size_thresholds": [],
                "thread_local_pools": False
            }
            
            # Analyze size distribution for hybrid strategy
            if criteria.size_distribution:
                config.update(self._analyze_size_based_strategy(criteria))
            
            # Check for multi-threaded workload
            if criteria.thread_count > 1:
                config["thread_local_pools"] = True
                config["allocation_strategy"] = "thread_aware"
            
            # Determine primary and secondary pools
            recommendations = self.recommend_pool(criteria)
            if recommendations:
                config["primary_pool"] = recommendations[0].pool_type
                if len(recommendations) > 1:
                    config["secondary_pools"] = [
                        rec.pool_type for rec in recommendations[1:3]
                    ]
            
            return config
    
    def provide_performance_feedback(
        self, 
        pool_type: PoolRecommendation, 
        performance_metric: float,
        criteria_hash: Optional[str] = None
    ) -> None:
        """
        Provide performance feedback for learning.
        
        Args:
            pool_type: Pool type that was used
            performance_metric: Performance measurement (higher is better)
            criteria_hash: Optional hash of the criteria used
        """
        with self._lock:
            pool_key = pool_type.value
            if pool_key not in self._performance_feedback:
                self._performance_feedback[pool_key] = []
            
            self._performance_feedback[pool_key].append(performance_metric)
            
            # Keep only recent feedback (last 100 measurements)
            if len(self._performance_feedback[pool_key]) > 100:
                self._performance_feedback[pool_key] = self._performance_feedback[pool_key][-100:]
    
    def get_pool_characteristics(self, pool_type: PoolRecommendation) -> Dict[str, Any]:
        """
        Get characteristics of a specific pool type.
        
        Args:
            pool_type: Pool type to query
            
        Returns:
            Pool characteristics
        """
        return self._pool_characteristics.get(pool_type, {})
    
    def analyze_workload_compatibility(
        self, 
        workload_pattern: WorkloadPattern,
        allocation_pattern: AllocationPattern
    ) -> Dict[PoolRecommendation, float]:
        """
        Analyze compatibility between workload patterns and pool types.
        
        Args:
            workload_pattern: Detected workload pattern
            allocation_pattern: Detected allocation pattern
            
        Returns:
            Compatibility scores for each pool type
        """
        compatibility = {}
        
        for pool_type in PoolRecommendation:
            score = self._calculate_pattern_compatibility(
                pool_type, workload_pattern, allocation_pattern
            )
            compatibility[pool_type] = score
        
        return compatibility
    
    def _calculate_pool_score(
        self, 
        pool_type: PoolRecommendation, 
        criteria: SelectionCriteria
    ) -> PoolScore:
        """Calculate comprehensive score for a pool type."""
        characteristics = self._pool_characteristics[pool_type]
        
        # Base compatibility score
        pattern_score = self._calculate_pattern_compatibility(
            pool_type, criteria.workload_pattern, criteria.allocation_pattern
        )
        
        # Performance factors
        speed_score = self._calculate_speed_score(pool_type, criteria)
        efficiency_score = self._calculate_efficiency_score(pool_type, criteria)
        fragmentation_score = self._calculate_fragmentation_score(pool_type, criteria)
        thread_score = self._calculate_thread_score(pool_type, criteria)
        scalability_score = self._calculate_scalability_score(pool_type, criteria)
        
        # Weighted final score
        final_score = (
            pattern_score * 0.3 +
            speed_score * self._scoring_weights["allocation_speed"] +
            efficiency_score * self._scoring_weights["memory_efficiency"] +
            fragmentation_score * self._scoring_weights["fragmentation_resistance"] +
            thread_score * self._scoring_weights["thread_safety"] +
            scalability_score * self._scoring_weights["scalability"]
        )
        
        # Apply performance priority weighting
        if criteria.performance_priority > 0.5:
            final_score += (speed_score - efficiency_score) * (criteria.performance_priority - 0.5)
        else:
            final_score += (efficiency_score - speed_score) * (0.5 - criteria.performance_priority)
        
        # Calculate confidence based on historical performance
        confidence = self._calculate_confidence(pool_type, criteria)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            pool_type, criteria, pattern_score, speed_score, 
            efficiency_score, fragmentation_score
        )
        
        return PoolScore(
            pool_type=pool_type,
            score=max(0.0, min(1.0, final_score)),
            confidence=confidence,
            reasoning=reasoning,
            performance_estimate=characteristics.get("performance_multiplier", 1.0),
            memory_efficiency=characteristics.get("memory_efficiency", 1.0)
        )
    
    def _calculate_pattern_compatibility(
        self, 
        pool_type: PoolRecommendation,
        workload_pattern: WorkloadPattern,
        allocation_pattern: AllocationPattern
    ) -> float:
        """Calculate compatibility between patterns and pool type."""
        characteristics = self._pool_characteristics[pool_type]
        
        # Workload pattern compatibility
        workload_compatibility = characteristics["workload_compatibility"].get(
            workload_pattern, 0.5
        )
        
        # Allocation pattern compatibility
        allocation_compatibility = characteristics["allocation_compatibility"].get(
            allocation_pattern, 0.5
        )
        
        return (workload_compatibility + allocation_compatibility) / 2.0
    
    def _calculate_speed_score(
        self, 
        pool_type: PoolRecommendation, 
        criteria: SelectionCriteria
    ) -> float:
        """Calculate allocation speed score."""
        characteristics = self._pool_characteristics[pool_type]
        base_speed = characteristics.get("allocation_speed", 0.5)
        
        # Adjust based on allocation pattern
        if criteria.allocation_pattern == AllocationPattern.SMALL_FREQUENT:
            if pool_type in [PoolRecommendation.SLAB_ALLOCATOR, PoolRecommendation.POOL_ALLOCATOR]:
                base_speed += 0.2
        elif criteria.allocation_pattern == AllocationPattern.LARGE_BLOCKS:
            if pool_type == PoolRecommendation.BUDDY_ALLOCATOR:
                base_speed += 0.15
        
        return min(1.0, base_speed)
    
    def _calculate_efficiency_score(
        self, 
        pool_type: PoolRecommendation, 
        criteria: SelectionCriteria
    ) -> float:
        """Calculate memory efficiency score."""
        characteristics = self._pool_characteristics[pool_type]
        base_efficiency = characteristics.get("memory_efficiency", 0.5)
        
        # Adjust based on fragmentation
        if criteria.memory_stats.fragmentation_ratio > criteria.fragmentation_tolerance:
            if pool_type in [PoolRecommendation.BUDDY_ALLOCATOR, PoolRecommendation.SLAB_ALLOCATOR]:
                base_efficiency += 0.1
        
        return min(1.0, base_efficiency)
    
    def _calculate_fragmentation_score(
        self, 
        pool_type: PoolRecommendation, 
        criteria: SelectionCriteria
    ) -> float:
        """Calculate fragmentation resistance score."""
        characteristics = self._pool_characteristics[pool_type]
        return characteristics.get("fragmentation_resistance", 0.5)
    
    def _calculate_thread_score(
        self, 
        pool_type: PoolRecommendation, 
        criteria: SelectionCriteria
    ) -> float:
        """Calculate thread safety score."""
        characteristics = self._pool_characteristics[pool_type]
        base_score = characteristics.get("thread_safety", 0.5)
        
        # Boost score for multi-threaded workloads
        if criteria.thread_count > 1:
            if pool_type in [PoolRecommendation.SLAB_ALLOCATOR, PoolRecommendation.POOL_ALLOCATOR]:
                base_score += 0.1
        
        return min(1.0, base_score)
    
    def _calculate_scalability_score(
        self, 
        pool_type: PoolRecommendation, 
        criteria: SelectionCriteria
    ) -> float:
        """Calculate scalability score."""
        characteristics = self._pool_characteristics[pool_type]
        return characteristics.get("scalability", 0.5)
    
    def _calculate_confidence(
        self, 
        pool_type: PoolRecommendation, 
        criteria: SelectionCriteria
    ) -> float:
        """Calculate confidence in recommendation based on historical data."""
        pool_key = pool_type.value
        
        if pool_key not in self._performance_feedback:
            return 0.5  # Neutral confidence for untested pools
        
        feedback = self._performance_feedback[pool_key]
        if len(feedback) < 3:
            return 0.6  # Slightly higher for some data
        
        # Calculate confidence based on consistency of feedback
        mean_performance = statistics.mean(feedback)
        std_dev = statistics.stdev(feedback) if len(feedback) > 1 else 0
        
        # Higher confidence for consistent good performance
        consistency = 1.0 - min(1.0, std_dev / mean_performance if mean_performance > 0 else 1.0)
        performance_factor = min(1.0, mean_performance / 100.0)  # Normalize to 0-1
        
        return (consistency + performance_factor) / 2.0
    
    def _generate_reasoning(
        self, 
        pool_type: PoolRecommendation,
        criteria: SelectionCriteria,
        pattern_score: float,
        speed_score: float,
        efficiency_score: float,
        fragmentation_score: float
    ) -> List[str]:
        """Generate human-readable reasoning for the recommendation."""
        reasoning = []
        
        # Pattern compatibility
        if pattern_score > 0.7:
            reasoning.append(f"Excellent compatibility with {criteria.workload_pattern.value} workload")
        elif pattern_score > 0.5:
            reasoning.append(f"Good compatibility with {criteria.allocation_pattern.value} allocation pattern")
        
        # Performance characteristics
        if speed_score > 0.8:
            reasoning.append("High allocation speed for this workload type")
        if efficiency_score > 0.8:
            reasoning.append("Excellent memory efficiency")
        if fragmentation_score > 0.7:
            reasoning.append("Strong fragmentation resistance")
        
        # Thread considerations
        if criteria.thread_count > 1:
            characteristics = self._pool_characteristics[pool_type]
            if characteristics.get("thread_safety", 0) > 0.7:
                reasoning.append(f"Well-suited for {criteria.thread_count} threads")
        
        # Memory usage patterns
        if criteria.memory_stats.fragmentation_ratio > 0.3:
            reasoning.append("Addresses high fragmentation in current workload")
        
        if not reasoning:
            reasoning.append("General-purpose allocation suitable for this workload")
        
        return reasoning
    
    def _analyze_size_based_strategy(self, criteria: SelectionCriteria) -> Dict[str, Any]:
        """Analyze size distribution for hybrid pool strategy."""
        if not criteria.size_distribution:
            return {}
        
        buckets = criteria.size_distribution.get("size_buckets", {})
        total_allocations = sum(buckets.values())
        
        if total_allocations == 0:
            return {}
        
        strategy = {}
        
        # Determine size thresholds based on distribution
        if buckets.get("small", 0) / total_allocations > 0.6:
            strategy["size_thresholds"] = [1024, 64*1024]  # Small, medium, large
            strategy["pool_mapping"] = {
                "small": PoolRecommendation.SLAB_ALLOCATOR,
                "medium": PoolRecommendation.BUDDY_ALLOCATOR,
                "large": PoolRecommendation.GENERAL_PURPOSE
            }
        elif buckets.get("large", 0) / total_allocations > 0.4:
            strategy["size_thresholds"] = [64*1024]  # Medium, large
            strategy["pool_mapping"] = {
                "medium": PoolRecommendation.BUDDY_ALLOCATOR,
                "large": PoolRecommendation.GENERAL_PURPOSE
            }
        
        return strategy
    
    def _record_selection(
        self, 
        criteria: SelectionCriteria, 
        scores: List[PoolScore]
    ) -> None:
        """Record selection for learning purposes."""
        selection_record = {
            "timestamp": time.time(),
            "workload_pattern": criteria.workload_pattern.value,
            "allocation_pattern": criteria.allocation_pattern.value,
            "thread_count": criteria.thread_count,
            "top_recommendation": scores[0].pool_type.value if scores else None,
            "top_score": scores[0].score if scores else 0.0
        }
        
        self._selection_history.append(selection_record)
        
        # Keep only recent history
        if len(self._selection_history) > 1000:
            self._selection_history = self._selection_history[-1000:]
    
    def _initialize_pool_characteristics(self) -> Dict[PoolRecommendation, Dict[str, Any]]:
        """Initialize pool characteristics database."""
        return {
            PoolRecommendation.SLAB_ALLOCATOR: {
                "allocation_speed": 0.9,
                "memory_efficiency": 0.8,
                "fragmentation_resistance": 0.9,
                "thread_safety": 0.8,
                "scalability": 0.7,
                "performance_multiplier": 1.2,
                "workload_compatibility": {
                    WorkloadPattern.CPU_INTENSIVE: 0.8,
                    WorkloadPattern.MEMORY_INTENSIVE: 0.9,
                    WorkloadPattern.IO_BOUND: 0.6,
                    WorkloadPattern.MIXED: 0.7,
                    WorkloadPattern.PARALLEL_FRIENDLY: 0.8,
                    WorkloadPattern.SEQUENTIAL: 0.7
                },
                "allocation_compatibility": {
                    AllocationPattern.SMALL_FREQUENT: 0.95,
                    AllocationPattern.LARGE_BLOCKS: 0.3,
                    AllocationPattern.SEQUENTIAL: 0.8,
                    AllocationPattern.RANDOM: 0.7,
                    AllocationPattern.BURST: 0.6,
                    AllocationPattern.STEADY: 0.8
                }
            },
            PoolRecommendation.BUDDY_ALLOCATOR: {
                "allocation_speed": 0.7,
                "memory_efficiency": 0.9,
                "fragmentation_resistance": 0.8,
                "thread_safety": 0.6,
                "scalability": 0.8,
                "performance_multiplier": 1.0,
                "workload_compatibility": {
                    WorkloadPattern.CPU_INTENSIVE: 0.7,
                    WorkloadPattern.MEMORY_INTENSIVE: 0.8,
                    WorkloadPattern.IO_BOUND: 0.7,
                    WorkloadPattern.MIXED: 0.8,
                    WorkloadPattern.PARALLEL_FRIENDLY: 0.6,
                    WorkloadPattern.SEQUENTIAL: 0.8
                },
                "allocation_compatibility": {
                    AllocationPattern.SMALL_FREQUENT: 0.4,
                    AllocationPattern.LARGE_BLOCKS: 0.9,
                    AllocationPattern.SEQUENTIAL: 0.7,
                    AllocationPattern.RANDOM: 0.8,
                    AllocationPattern.BURST: 0.7,
                    AllocationPattern.STEADY: 0.8
                }
            },
            PoolRecommendation.STACK_ALLOCATOR: {
                "allocation_speed": 0.95,
                "memory_efficiency": 0.95,
                "fragmentation_resistance": 1.0,
                "thread_safety": 0.4,
                "scalability": 0.3,
                "performance_multiplier": 1.5,
                "workload_compatibility": {
                    WorkloadPattern.CPU_INTENSIVE: 0.9,
                    WorkloadPattern.MEMORY_INTENSIVE: 0.7,
                    WorkloadPattern.IO_BOUND: 0.5,
                    WorkloadPattern.MIXED: 0.6,
                    WorkloadPattern.PARALLEL_FRIENDLY: 0.3,
                    WorkloadPattern.SEQUENTIAL: 0.95
                },
                "allocation_compatibility": {
                    AllocationPattern.SMALL_FREQUENT: 0.8,
                    AllocationPattern.LARGE_BLOCKS: 0.6,
                    AllocationPattern.SEQUENTIAL: 0.95,
                    AllocationPattern.RANDOM: 0.2,
                    AllocationPattern.BURST: 0.4,
                    AllocationPattern.STEADY: 0.9
                }
            },
            PoolRecommendation.POOL_ALLOCATOR: {
                "allocation_speed": 0.85,
                "memory_efficiency": 0.85,
                "fragmentation_resistance": 0.9,
                "thread_safety": 0.9,
                "scalability": 0.8,
                "performance_multiplier": 1.1,
                "workload_compatibility": {
                    WorkloadPattern.CPU_INTENSIVE: 0.8,
                    WorkloadPattern.MEMORY_INTENSIVE: 0.8,
                    WorkloadPattern.IO_BOUND: 0.7,
                    WorkloadPattern.MIXED: 0.8,
                    WorkloadPattern.PARALLEL_FRIENDLY: 0.9,
                    WorkloadPattern.SEQUENTIAL: 0.7
                },
                "allocation_compatibility": {
                    AllocationPattern.SMALL_FREQUENT: 0.9,
                    AllocationPattern.LARGE_BLOCKS: 0.5,
                    AllocationPattern.SEQUENTIAL: 0.7,
                    AllocationPattern.RANDOM: 0.8,
                    AllocationPattern.BURST: 0.8,
                    AllocationPattern.STEADY: 0.8
                }
            },
            PoolRecommendation.GENERAL_PURPOSE: {
                "allocation_speed": 0.6,
                "memory_efficiency": 0.7,
                "fragmentation_resistance": 0.5,
                "thread_safety": 0.7,
                "scalability": 0.9,
                "performance_multiplier": 0.8,
                "workload_compatibility": {
                    WorkloadPattern.CPU_INTENSIVE: 0.6,
                    WorkloadPattern.MEMORY_INTENSIVE: 0.6,
                    WorkloadPattern.IO_BOUND: 0.8,
                    WorkloadPattern.MIXED: 0.9,
                    WorkloadPattern.PARALLEL_FRIENDLY: 0.7,
                    WorkloadPattern.SEQUENTIAL: 0.6
                },
                "allocation_compatibility": {
                    AllocationPattern.SMALL_FREQUENT: 0.6,
                    AllocationPattern.LARGE_BLOCKS: 0.8,
                    AllocationPattern.SEQUENTIAL: 0.6,
                    AllocationPattern.RANDOM: 0.9,
                    AllocationPattern.BURST: 0.7,
                    AllocationPattern.STEADY: 0.7
                }
            },
            PoolRecommendation.HYBRID: {
                "allocation_speed": 0.8,
                "memory_efficiency": 0.85,
                "fragmentation_resistance": 0.8,
                "thread_safety": 0.8,
                "scalability": 0.9,
                "performance_multiplier": 1.15,
                "workload_compatibility": {
                    WorkloadPattern.CPU_INTENSIVE: 0.8,
                    WorkloadPattern.MEMORY_INTENSIVE: 0.9,
                    WorkloadPattern.IO_BOUND: 0.8,
                    WorkloadPattern.MIXED: 0.95,
                    WorkloadPattern.PARALLEL_FRIENDLY: 0.9,
                    WorkloadPattern.SEQUENTIAL: 0.8
                },
                "allocation_compatibility": {
                    AllocationPattern.SMALL_FREQUENT: 0.8,
                    AllocationPattern.LARGE_BLOCKS: 0.8,
                    AllocationPattern.SEQUENTIAL: 0.8,
                    AllocationPattern.RANDOM: 0.9,
                    AllocationPattern.BURST: 0.9,
                    AllocationPattern.STEADY: 0.8
                }
            }
        }