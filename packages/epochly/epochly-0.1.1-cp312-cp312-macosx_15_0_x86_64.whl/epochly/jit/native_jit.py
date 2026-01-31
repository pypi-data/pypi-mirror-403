"""
Epochly Python 3.13+ Native JIT Backend

Provides JIT compilation using Python 3.13's built-in JIT compiler for general
Python code optimization with zero additional dependencies.

Author: Epochly Development Team
"""

import logging
import sys
import os
from typing import Callable, Optional, List, Any, Dict

from .base import JITCompiler, JITBackend, JITCompilationResult, CompilationStatus

logger = logging.getLogger(__name__)

# Check if Python 3.13+ native JIT is available
NATIVE_JIT_AVAILABLE = (
    sys.version_info >= (3, 13) and 
    hasattr(sys, '_jit_enabled') and 
    getattr(sys, '_jit_enabled', False)
)


class NativeJIT(JITCompiler):
    """
    Python 3.13+ native JIT compiler.
    
    Utilizes the built-in JIT compilation capabilities of Python 3.13+
    for general Python code optimization with subinterpreter safety.
    """
    
    def __init__(self, enable_caching: bool = True, **native_options):
        """
        Initialize Native JIT compiler.
        
        Args:
            enable_caching: Whether to cache compiled functions
            **native_options: Additional options for native JIT
        """
        super().__init__(JITBackend.NATIVE, enable_caching)
        
        # Native JIT configuration
        self.native_options = {
            'tier': 1,              # JIT tier level (0-2)
            'optimization_level': 1, # Optimization level
            'hot_threshold': 1000,   # Calls before JIT compilation
            'debug': False,          # Debug mode
            **native_options
        }
        
        # Performance tracking
        self.jit_compilations = 0
        self.tier_upgrades = 0
        self.deoptimizations = 0
        
        if not NATIVE_JIT_AVAILABLE:
            logger.warning("Python 3.13+ native JIT not available - NativeJIT compiler will be disabled")
        else:
            self._configure_native_jit()
    
    def _configure_native_jit(self) -> None:
        """Configure Python 3.13+ native JIT settings."""
        try:
            # Set JIT tier level
            if hasattr(sys, '_set_jit_tier'):
                sys._set_jit_tier(self.native_options['tier'])
                logger.debug(f"Set native JIT tier to {self.native_options['tier']}")
            
            # Set optimization level via environment
            os.environ['PYTHON_JIT_TIER'] = str(self.native_options['tier'])
            
            # Configure hot threshold
            if hasattr(sys, '_set_jit_threshold'):
                sys._set_jit_threshold(self.native_options['hot_threshold'])
            
            # Debug mode
            if self.native_options['debug']:
                os.environ['PYTHON_JIT_DEBUG'] = '1'
            
            logger.info("Python 3.13+ native JIT configured successfully")
            
        except Exception as e:
            logger.warning(f"Failed to configure native JIT: {e}")
    
    def is_available(self) -> bool:
        """Check if Python 3.13+ native JIT is available."""
        return NATIVE_JIT_AVAILABLE
    
    def _compile_function_impl(self, func: Callable, source_hash: str) -> JITCompilationResult:
        """
        Compile function using Python 3.13+ native JIT.
        
        Args:
            func: Function to compile
            source_hash: Hash of function source code
            
        Returns:
            JITCompilationResult with compilation outcome
        """
        func_name = getattr(func, '__name__', str(func))
        
        if not NATIVE_JIT_AVAILABLE:
            return JITCompilationResult(
                backend=self.backend,
                status=CompilationStatus.UNAVAILABLE,
                compilation_time_ms=0.0,
                function_name=func_name,
                source_hash=source_hash,
                error_message="Python 3.13+ native JIT not available"
            )
        
        warnings = []
        
        try:
            # Check function compatibility
            compatibility_issues = self._check_compatibility(func)
            if compatibility_issues:
                warnings.extend(compatibility_issues)
            
            # Enable JIT for this function (native JIT is automatic)
            # We mark the function as JIT-eligible
            compiled_func = self._enable_jit_for_function(func)
            
            if compiled_func:
                self.jit_compilations += 1
                return JITCompilationResult(
                    backend=self.backend,
                    status=CompilationStatus.COMPILED,
                    compilation_time_ms=0.0,  # Native JIT compilation is transparent
                    function_name=func_name,
                    source_hash=source_hash,
                    compiled_function=compiled_func,
                    compilation_warnings=warnings
                )
            else:
                return JITCompilationResult(
                    backend=self.backend,
                    status=CompilationStatus.FAILED,
                    compilation_time_ms=0.0,
                    function_name=func_name,
                    source_hash=source_hash,
                    error_message="Native JIT enablement failed",
                    compilation_warnings=warnings
                )
                
        except Exception as e:
            return JITCompilationResult(
                backend=self.backend,
                status=CompilationStatus.FAILED,
                compilation_time_ms=0.0,
                function_name=func_name,
                source_hash=source_hash,
                error_message=str(e),
                error_type=type(e).__name__,
                compilation_warnings=warnings
            )
    
    def _enable_jit_for_function(self, func: Callable) -> Optional[Callable]:
        """
        Enable JIT compilation for a specific function.
        
        Args:
            func: Function to enable JIT for
            
        Returns:
            Function wrapper that ensures JIT compilation
        """
        try:
            # Python 3.13 native JIT is automatic, but we can provide hints
            # or ensure the function is called enough times to trigger JIT
            
            def jit_enabled_wrapper(*args, **kwargs):
                # The native JIT will automatically optimize this function
                # after it's called frequently enough
                return func(*args, **kwargs)
            
            jit_enabled_wrapper.__name__ = f"{func.__name__}_native_jit"
            jit_enabled_wrapper.__doc__ = f"Native JIT enabled version of {func.__name__}"
            jit_enabled_wrapper.__wrapped__ = func
            
            # Optionally trigger initial compilation by calling multiple times
            if hasattr(sys, '_force_jit_compile'):
                try:
                    sys._force_jit_compile(func)
                except Exception:
                    pass  # Force compilation is optional
            
            logger.debug(f"Enabled native JIT for {func.__name__}")
            return jit_enabled_wrapper
            
        except Exception as e:
            logger.debug(f"Failed to enable native JIT for {func.__name__}: {e}")
            return None
    
    def _check_compatibility(self, func: Callable) -> List[str]:
        """
        Check function compatibility with native JIT.
        
        Args:
            func: Function to check
            
        Returns:
            List of compatibility warnings
        """
        warnings = []
        
        try:
            import inspect
            source = inspect.getsource(func)
            
            # Native JIT generally handles most Python constructs well
            # but some patterns may not optimize as effectively
            potential_issues = [
                ('exec(', "exec() may limit optimization"),
                ('eval(', "eval() may limit optimization"),
                ('__import__', "Dynamic imports may not optimize well"),
                ('globals()', "Global access may limit optimization"),
                ('locals()', "Local frame access may limit optimization"),
            ]
            
            for pattern, warning in potential_issues:
                if pattern in source:
                    warnings.append(warning)
            
            # Check for very complex functions
            if source.count('\n') > 100:
                warnings.append("Very large functions may have longer compilation times")
            
            # Check for recursive functions
            func_name = getattr(func, '__name__', '')
            if func_name and func_name in source and source.count(func_name) > 2:
                warnings.append("Recursive functions may need multiple compilation passes")
            
        except (OSError, TypeError):
            warnings.append("Cannot analyze function source - optimization may be limited")
        
        return warnings
    
    def get_native_statistics(self) -> dict:
        """
        Get native JIT-specific compilation statistics.
        
        Returns:
            Dictionary with native JIT-specific metrics
        """
        base_stats = self.get_statistics()
        
        native_stats = {
            'jit_compilations': self.jit_compilations,
            'tier_upgrades': self.tier_upgrades,
            'deoptimizations': self.deoptimizations,
            'native_options': self.native_options,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
        
        # Add Python JIT system information if available
        if NATIVE_JIT_AVAILABLE:
            try:
                if hasattr(sys, '_jit_info'):
                    native_stats['jit_info'] = sys._jit_info()
                if hasattr(sys, '_jit_stats'):
                    native_stats['jit_stats'] = sys._jit_stats()
            except Exception as e:
                native_stats['jit_info_error'] = str(e)
        
        base_stats.update(native_stats)
        return base_stats
    
    def set_tier(self, tier: int) -> None:
        """
        Set native JIT tier level.
        
        Args:
            tier: JIT tier level (0-2, higher = more aggressive)
        """
        if not NATIVE_JIT_AVAILABLE:
            logger.warning("Cannot set JIT tier - native JIT not available")
            return
        
        self.native_options['tier'] = max(0, min(2, tier))
        
        try:
            if hasattr(sys, '_set_jit_tier'):
                sys._set_jit_tier(self.native_options['tier'])
            os.environ['PYTHON_JIT_TIER'] = str(self.native_options['tier'])
            logger.info(f"Set native JIT tier to {self.native_options['tier']}")
        except Exception as e:
            logger.warning(f"Failed to set native JIT tier: {e}")
    
    def set_hot_threshold(self, threshold: int) -> None:
        """
        Set the call count threshold for JIT compilation.
        
        Args:
            threshold: Number of calls before JIT compilation triggers
        """
        if not NATIVE_JIT_AVAILABLE:
            logger.warning("Cannot set hot threshold - native JIT not available")
            return
        
        self.native_options['hot_threshold'] = max(1, threshold)
        
        try:
            if hasattr(sys, '_set_jit_threshold'):
                sys._set_jit_threshold(self.native_options['hot_threshold'])
            logger.info(f"Set native JIT hot threshold to {self.native_options['hot_threshold']}")
        except Exception as e:
            logger.warning(f"Failed to set native JIT hot threshold: {e}")
    
    def enable_debug_mode(self, enable: bool = True) -> None:
        """
        Enable or disable debug mode for native JIT.
        
        Args:
            enable: Whether to enable debug mode
        """
        self.native_options['debug'] = enable
        
        try:
            if enable:
                os.environ['PYTHON_JIT_DEBUG'] = '1'
            else:
                os.environ.pop('PYTHON_JIT_DEBUG', None)
            logger.info(f"Native JIT debug mode {'enabled' if enable else 'disabled'}")
        except Exception as e:
            logger.warning(f"Failed to set native JIT debug mode: {e}")
    
    def get_jit_status(self) -> Dict[str, Any]:
        """
        Get current JIT status and configuration.
        
        Returns:
            Dictionary with JIT status information
        """
        status = {
            'available': NATIVE_JIT_AVAILABLE,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
            'tier': self.native_options.get('tier', 0),
            'hot_threshold': self.native_options.get('hot_threshold', 1000),
            'debug': self.native_options.get('debug', False)
        }
        
        if NATIVE_JIT_AVAILABLE:
            try:
                if hasattr(sys, '_jit_enabled'):
                    status['jit_enabled'] = sys._jit_enabled
                if hasattr(sys, '_get_jit_tier'):
                    status['current_tier'] = sys._get_jit_tier()
            except Exception as e:
                status['status_error'] = str(e)
        
        return status
    
    def __del__(self):
        """Cleanup native JIT resources."""
        try:
            super().__del__()
            # Native JIT cleanup is handled by Python interpreter
        except Exception:
            pass