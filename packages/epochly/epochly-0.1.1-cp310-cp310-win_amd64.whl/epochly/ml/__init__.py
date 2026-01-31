"""
Epochly Machine Learning Module - Ultra-Lightweight Implementation

Provides ML-based performance prediction using only numpy with graceful fallbacks.
Designed to be <100KB memory overhead with <0.1% CPU impact.

Core principle: "It just works or gets out of the way"

Author: Epochly Development Team
"""

import logging
import os

logger = logging.getLogger(__name__)

# Check for minimal ML capabilities (numpy only)
try:
    import numpy as np
    ML_AVAILABLE = True
    logger.info("Epochly ML module initialized with lightweight numpy-based predictors")
except ImportError:
    ML_AVAILABLE = False
    logger.info("Epochly ML module disabled - falling back to rule-based optimization")

# System resource detection for adaptive ML behavior
def detect_system_tier():
    """Detect system capabilities for adaptive ML configuration."""
    cpu_count = os.cpu_count() or 1
    
    if cpu_count <= 2:
        return "lightweight"  # Laptop/low-resource
    elif cpu_count <= 8:
        return "moderate"     # Standard desktop/container
    else:
        return "full"         # Server/high-resource

SYSTEM_TIER = detect_system_tier()

# Conditional imports based on availability
if ML_AVAILABLE:
    # Import real implementations
    try:
        from .performance_predictors import LSTMResourcePredictor, PerformancePredictor
    except ImportError as e:
        logger.warning(f"Failed to import performance predictors: {e}")
        # Fallback stubs if import fails
        class LSTMResourcePredictor:
            def __init__(self, *args, **kwargs):
                logger.warning("LSTMResourcePredictor unavailable - using fallback")
            def predict(self, *args, **kwargs): return None
            def update(self, *args, **kwargs): pass

        class PerformancePredictor:
            def __init__(self, *args, **kwargs):
                logger.warning("PerformancePredictor unavailable - using fallback")
            def predict_performance(self, *args, **kwargs): return None
            def learn_from_outcome(self, *args, **kwargs): pass

else:
    # Provide no-op implementations when ML not available (no numpy)
    logger.info("ML features disabled (numpy not available)")

    class LSTMResourcePredictor:
        def __init__(self, *args, **kwargs): pass
        def predict(self, *args, **kwargs): return None
        def update(self, *args, **kwargs): pass

    class PerformancePredictor:
        def __init__(self, *args, **kwargs): pass
        def predict_performance(self, *args, **kwargs): return None
        def learn_from_outcome(self, *args, **kwargs): pass

# NOTE: ReinforcementLearningScheduler and WorkloadPredictor removed
# These were unused placeholder classes. For actual implementations, use:
#   - ReinforcementLearningScheduler → epochly.plugins.analyzer.adaptive_orchestrator.LightweightRLScheduler
#   - WorkloadPredictor → epochly.plugins.analyzer.adaptive_orchestrator (prediction methods)
#   - JIT Selection → epochly.plugins.analyzer.jit_analyzer.JITAnalyzer
# These are internal components accessed via EpochlyCore, not direct imports

__all__ = [
    'LSTMResourcePredictor',
    'PerformancePredictor',
    'ML_AVAILABLE',
    'SYSTEM_TIER'
]