"""
Static safety analyzer for AST-based compatibility detection.

Performs fast analysis of Python modules to detect patterns that are
incompatible with sub-interpreter execution.
"""

import ast
import importlib.util
from typing import Set, Optional
import logging
import time

logger = logging.getLogger(__name__)


class StaticSafetyAnalyzer:
    """
    Lightweight AST analysis for compatibility detection.
    Runs in background, updates confidence scores.
    """
    
    # Known problematic patterns for sub-interpreters
    UNSAFE_PATTERNS = {
        'ctypes',           # FFI library
        'cffi',            # Another FFI library
        '__file__',        # File path access
        'signal.signal',   # Signal handlers
        'threading.Lock',  # Global locks
        'threading.RLock', # Reentrant locks
        'multiprocessing.Manager',  # Shared state
        'os.fork',         # Process forking
        'os.execv',        # Process replacement
    }
    
    # Known safe modules (cached for speed)
    KNOWN_SAFE = {
        'json', 'math', 'datetime', 'collections', 'itertools',
        're', 'hashlib', 'base64', 'uuid', 'random',
        'decimal', 'fractions', 'statistics', 'csv', 'urllib'
    }
    
    # Known unsafe modules
    KNOWN_UNSAFE = {
        'ctypes', 'cffi', 'signal', 'mmap', 'gc',
        'sys', 'os', 'subprocess', 'multiprocessing'
    }
    
    def analyze_module_fast(self, module_name: str) -> float:
        """
        Quick static analysis - returns safety score 0.0-1.0.
        Designed to run in < 10ms.
        """
        start_time = time.perf_counter()
        
        try:
            # Fast path: Check known lists
            if module_name in self.KNOWN_SAFE:
                return 0.8
            if module_name in self.KNOWN_UNSAFE:
                return 0.2
            
            # Find module spec
            spec = importlib.util.find_spec(module_name)
            if not spec or not spec.origin:
                return 0.5  # Unknown
            
            # Check for C extension
            if spec.origin.endswith(('.so', '.pyd', '.dll')):
                # Check if marked as multi-interpreter safe (PEP 684)
                try:
                    module = importlib.import_module(module_name)
                    
                    # Check for PEP 684 compatibility flag
                    if hasattr(module, '__interpreter_compatible__'):
                        return 0.9 if module.__interpreter_compatible__ else 0.1
                    
                    # Check for older compatibility flag
                    if hasattr(module, '_multiinterp_compatible'):
                        return 0.9 if module._multiinterp_compatible else 0.1
                    
                except Exception:
                    pass
                
                return 0.3  # C extension, unknown safety
            
            # Quick AST scan for .py files
            if spec.origin.endswith('.py'):
                try:
                    with open(spec.origin, 'r', encoding='utf-8') as f:
                        # Read limited amount to avoid long analysis
                        source = f.read(50000)  # First 50KB only
                    
                    tree = ast.parse(source, filename=spec.origin)
                    
                    # Check for unsafe patterns
                    visitor = UnsafePatternVisitor(self.UNSAFE_PATTERNS)
                    visitor.visit(tree)
                    
                    # Calculate score based on issues found
                    if visitor.critical_issues > 0:
                        score = 0.1
                    elif visitor.warnings > 0:
                        score = max(0.3, 0.5 - (visitor.warnings * 0.1))
                    else:
                        score = 0.8
                    
                    # Ensure we complete within 10ms
                    elapsed = time.perf_counter() - start_time
                    if elapsed > 0.01:  # 10ms
                        logger.debug(f"Static analysis of {module_name} took {elapsed*1000:.1f}ms")
                    
                    return score
                    
                except Exception as e:
                    logger.debug(f"Error analyzing {module_name}: {e}")
                    return 0.5
            
            return 0.5  # Default for unknown
            
        except Exception as e:
            logger.debug(f"Error in module analysis: {e}")
            return 0.5  # Error analyzing, neutral score


class UnsafePatternVisitor(ast.NodeVisitor):
    """Fast AST visitor for unsafe patterns"""
    
    def __init__(self, unsafe_patterns: Optional[Set[str]] = None):
        self.unsafe_patterns = unsafe_patterns or StaticSafetyAnalyzer.UNSAFE_PATTERNS
        self.critical_issues = 0
        self.warnings = 0
        self._depth = 0  # Track recursion depth
        self._max_depth = 10  # Limit recursion for speed
    
    def visit(self, node):
        """Visit node with depth limiting"""
        if self._depth >= self._max_depth:
            return  # Stop deep recursion
        
        self._depth += 1
        try:
            super().visit(node)
        finally:
            self._depth -= 1
    
    def visit_Import(self, node):
        """Check import statements"""
        for alias in node.names:
            # Check if importing unsafe module
            for unsafe in self.unsafe_patterns:
                if unsafe in alias.name:
                    self.critical_issues += 1
                    break
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Check from...import statements"""
        if node.module:
            for unsafe in self.unsafe_patterns:
                if unsafe in node.module:
                    self.critical_issues += 1
                    break
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Check for name references like __file__"""
        if node.id == '__file__':
            self.warnings += 1
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        """Check for attribute access"""
        if isinstance(node.attr, str):
            if node.attr in ['Lock', 'RLock', 'Semaphore', 'Event', 'Condition']:
                # Threading primitives - but don't double count
                pass  # Will be handled in visit_Call
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Check for problematic function calls"""
        # Check for threading primitive creation
        if isinstance(node.func, ast.Attribute):
            if hasattr(node.func, 'attr'):
                if node.func.attr in ['Lock', 'RLock', 'Semaphore', 'Event', 'Condition']:
                    self.warnings += 1
                elif node.func.attr in ['fork', 'execv', 'execve', 'spawn']:
                    self.critical_issues += 1
        
        # Check for signal.signal calls
        if isinstance(node.func, ast.Attribute):
            if hasattr(node.func, 'value') and isinstance(node.func.value, ast.Name):
                if node.func.value.id == 'signal' and node.func.attr == 'signal':
                    self.critical_issues += 1
        
        self.generic_visit(node)
    
    def visit_Global(self, node):
        """Check for global statement usage"""
        # Global state modification is a warning
        self.warnings += 1
        self.generic_visit(node)
    
    def visit_Nonlocal(self, node):
        """Check for nonlocal statement usage"""
        # Nonlocal state modification is a warning
        self.warnings += 1
        self.generic_visit(node)