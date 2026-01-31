"""
Epochly Analyzer Plugin Package

This package contains the analyzer components for Week 4 multicore capabilities:
- WorkloadDetectionAnalyzer: Detects workload patterns for multicore distribution
- MemoryProfiler: Tracks memory allocation patterns and usage statistics
- MemoryPoolSelector: Provides intelligent pool recommendations
- AdaptiveOrchestrator: Coordinates dynamic pool switching and optimization

These components work together to enable intelligent workload distribution across
sub-interpreters and optimal memory pool selection for multicore performance.

Author: Epochly Development Team
"""

from .workload_detector import (
    WorkloadDetectionAnalyzer,
    WorkloadPattern,
    WorkloadCharacteristics,
    AllocationEvent
)

from .memory_profiler import (
    MemoryProfiler,
    MemoryStats,
    AllocationPattern,
    AllocationInfo
)

from .pool_selector import (
    MemoryPoolSelector,
    PoolRecommendation,
    PoolScore,
    SelectionCriteria
)

from .adaptive_orchestrator import (
    AdaptiveOrchestrator,
    AdaptationTrigger,
    AdaptationEvent,
    OrchestrationConfig
)

from .jit_analyzer import (
    JITAnalyzer,
    JITSuitability,
    JITBackendType,
    FunctionCharacteristics,
    HotPathCandidate
)

__all__ = [
    # Workload Detection
    "WorkloadDetectionAnalyzer",
    "WorkloadPattern", 
    "WorkloadCharacteristics",
    "AllocationEvent",
    
    # Memory Profiling
    "MemoryProfiler",
    "MemoryStats",
    "AllocationPattern", 
    "AllocationInfo",
    
    # Pool Selection
    "MemoryPoolSelector",
    "PoolRecommendation",
    "PoolScore",
    "SelectionCriteria",
    
    # Adaptive Orchestration
    "AdaptiveOrchestrator",
    "AdaptationTrigger",
    "AdaptationEvent", 
    "OrchestrationConfig",
    
    # JIT Analysis
    "JITAnalyzer",
    "JITSuitability",
    "JITBackendType",
    "FunctionCharacteristics",
    "HotPathCandidate"
]

# Version information
__version__ = "1.0.0"
__author__ = "Epochly Development Team"

# Package metadata
ANALYZER_COMPONENTS = {
    "workload_detector": {
        "class": "WorkloadDetectionAnalyzer",
        "description": "Detects workload patterns for multicore distribution",
        "priority": "HIGH",
        "capabilities": [
            "workload_pattern_detection",
            "memory_profiling", 
            "parallelization_analysis",
            "multicore_distribution"
        ]
    },
    "memory_profiler": {
        "class": "MemoryProfiler", 
        "description": "Tracks memory allocation patterns and usage statistics",
        "priority": "HIGH",
        "capabilities": [
            "allocation_tracking",
            "pattern_detection",
            "fragmentation_analysis",
            "performance_metrics"
        ]
    },
    "pool_selector": {
        "class": "MemoryPoolSelector",
        "description": "Provides intelligent pool recommendations", 
        "priority": "HIGH",
        "capabilities": [
            "pool_recommendation",
            "performance_estimation",
            "compatibility_analysis",
            "hybrid_configuration"
        ]
    },
    "adaptive_orchestrator": {
        "class": "AdaptiveOrchestrator",
        "description": "Coordinates dynamic pool switching and optimization",
        "priority": "CRITICAL",
        "capabilities": [
            "dynamic_adaptation",
            "performance_monitoring",
            "predictive_optimization",
            "real_time_coordination"
        ]
    },
    "jit_analyzer": {
        "class": "JITAnalyzer",
        "description": "Analyzes functions for JIT compilation opportunities",
        "priority": "HIGH",
        "capabilities": [
            "hot_path_detection",
            "jit_suitability_analysis",
            "backend_selection",
            "performance_prediction",
            "compilation_planning"
        ]
    }
}

def create_analyzer_suite():
    """
    Create a complete analyzer suite with all components.
    
    Returns:
        Dictionary containing initialized analyzer components
    """
    return {
        "workload_detector": WorkloadDetectionAnalyzer(),
        "memory_profiler": MemoryProfiler(),
        "pool_selector": MemoryPoolSelector(),
        "adaptive_orchestrator": AdaptiveOrchestrator(),
        "jit_analyzer": JITAnalyzer()
    }

def get_component_info(component_name: str) -> dict:
    """
    Get information about a specific analyzer component.
    
    Args:
        component_name: Name of the component
        
    Returns:
        Component information dictionary
    """
    return ANALYZER_COMPONENTS.get(component_name, {})

def list_available_components() -> list:
    """
    List all available analyzer components.
    
    Returns:
        List of component names
    """
    return list(ANALYZER_COMPONENTS.keys())