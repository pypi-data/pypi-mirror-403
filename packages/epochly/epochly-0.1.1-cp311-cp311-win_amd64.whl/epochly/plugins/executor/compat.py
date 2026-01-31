"""
Compatibility module for Python 3.8-3.13 support.

This module provides feature detection and compatibility shims for different
Python versions, ensuring the Epochly executor system works across Python 3.8-3.13.
"""

import sys
import platform
from typing import Dict, Any, Optional, Tuple
import importlib.util


class PythonFeatures:
    """Detects and tracks Python version-specific features."""
    
    def __init__(self):
        self.version_info = sys.version_info
        self.version = f"{self.version_info.major}.{self.version_info.minor}"
        self.platform = platform.system()
        
        # Feature detection results
        self._features: Dict[str, bool] = {}
        self._detect_features()
    
    def _detect_features(self) -> None:
        """Detect available features based on Python version and platform."""
        # Sub-interpreters (PEP 554) - available in Python 3.12+
        self._features['subinterpreters'] = (
            self.version_info >= (3, 12) and
            self._check_subinterpreter_support()
        )
        
        # ProcessPoolExecutor with initializer - available in all supported versions
        self._features['process_pool_initializer'] = True
        
        # SharedMemory - available in Python 3.8+
        self._features['shared_memory'] = self.version_info >= (3, 8)
        
        # Union types using | operator - Python 3.10+
        self._features['union_operator'] = self.version_info >= (3, 10)
        
        # match/case statements - Python 3.10+
        self._features['match_case'] = self.version_info >= (3, 10)
        
        # ExceptionGroup - Python 3.11+
        self._features['exception_group'] = self.version_info >= (3, 11)
        
        # Task groups - Python 3.11+
        self._features['task_groups'] = self.version_info >= (3, 11)
        
        # Windows-specific limitations
        if self.platform == 'Windows':
            # Windows has limited fork support
            self._features['fork_support'] = False
            # Sub-interpreters have additional limitations on Windows
            if self._features['subinterpreters']:
                self._features['subinterpreters'] = self._check_windows_subinterpreter()
        else:
            self._features['fork_support'] = True
    
    def _check_subinterpreter_support(self) -> bool:
        """Check if sub-interpreters are actually available."""
        try:
            # Try to import _interpreters module (Python 3.12+)
            spec = importlib.util.find_spec('_interpreters')
            if spec is None:
                return False
            
            # Try to create a test interpreter
            import _interpreters
            interp_id = _interpreters.create()
            _interpreters.destroy(interp_id)
            return True
        except (ImportError, AttributeError, RuntimeError):
            return False
    
    def _check_windows_subinterpreter(self) -> bool:
        """Additional checks for sub-interpreter support on Windows."""
        # Windows may have additional restrictions
        # Check for specific Windows versions or configurations
        try:
            import _interpreters
            # Test if we can actually run code in sub-interpreters
            interp_id = _interpreters.create()
            try:
                _interpreters.run_string(interp_id, "x = 1")
                return True
            except Exception:
                return False
            finally:
                _interpreters.destroy(interp_id)
        except Exception:
            return False
    
    def has_feature(self, feature: str) -> bool:
        """Check if a specific feature is available."""
        return self._features.get(feature, False)
    
    def get_all_features(self) -> Dict[str, bool]:
        """Get all detected features."""
        return self._features.copy()
    
    def get_executor_recommendation(self) -> str:
        """Recommend the best executor based on available features."""
        if self.has_feature('subinterpreters') and self.platform != 'Windows':
            return 'SubInterpreterExecutor'
        elif self.has_feature('fork_support'):
            return 'ProcessPoolExecutor'
        else:
            return 'ThreadExecutor'


# Global instance for easy access
python_features = PythonFeatures()


def requires_python(min_version: Tuple[int, int]) -> bool:
    """Check if current Python version meets minimum requirement."""
    return sys.version_info >= min_version


def get_optimal_executor_config() -> Dict[str, Any]:
    """Get optimal executor configuration for current environment."""
    config = {
        'executor_type': python_features.get_executor_recommendation(),
        'features': python_features.get_all_features(),
        'python_version': python_features.version,
        'platform': python_features.platform,
    }
    
    # Add platform-specific optimizations
    if python_features.platform == 'Windows':
        config['process_start_method'] = 'spawn'
        config['use_shared_memory'] = False  # More limited on Windows
    else:
        config['process_start_method'] = 'fork' if python_features.has_feature('fork_support') else 'spawn'
        config['use_shared_memory'] = python_features.has_feature('shared_memory')
    
    return config


def import_optional(module_name: str, attribute: Optional[str] = None) -> Optional[Any]:
    """Safely import optional modules or attributes."""
    try:
        module = importlib.import_module(module_name)
        if attribute:
            return getattr(module, attribute, None)
        return module
    except ImportError:
        return None


# Compatibility shims for older Python versions
if sys.version_info < (3, 10):
    # Provide Union type helper for older Python
    from typing import Union as UnionType
    
    def create_union(*types):
        """Create a Union type for Python < 3.10."""
        return UnionType[types]
else:
    def create_union(*types):
        """Create a union type using | operator for Python 3.10+."""
        result = types[0]
        for t in types[1:]:
            result = result | t
        return result


# Provide compatibility for missing features
class CompatibilityError(Exception):
    """Raised when a required feature is not available in current Python version."""
    pass


def ensure_feature(feature: str) -> None:
    """Ensure a feature is available, raise error if not."""
    if not python_features.has_feature(feature):
        raise CompatibilityError(
            f"Feature '{feature}' is not available in Python {python_features.version} "
            f"on {python_features.platform}"
        )


# Export key functions and classes
__all__ = [
    'PythonFeatures',
    'python_features',
    'requires_python',
    'get_optimal_executor_config',
    'import_optional',
    'create_union',
    'CompatibilityError',
    'ensure_feature',
]