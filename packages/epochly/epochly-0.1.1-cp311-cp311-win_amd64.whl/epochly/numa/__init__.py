"""
NUMA-aware scheduling module (SPEC2 Task 14).
"""

from .numa_manager import NumaManager, NumaNode
from .numa_detector import NumaDetector


__all__ = ['NumaManager', 'NumaNode', 'NumaDetector']
