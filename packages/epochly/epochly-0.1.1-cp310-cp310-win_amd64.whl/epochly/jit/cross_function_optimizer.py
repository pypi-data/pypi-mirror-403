"""
Cross-Function Optimization for Epochly JIT Pipeline.

This module implements cross-function optimization including call graph analysis,
intelligent inlining decisions, and optimization across function boundaries.
"""

import time
import inspect
import ast
import threading
import os
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


# Module-level worker functions for ThreadPoolExecutor

def _analyze_function_chunk_worker(args: Tuple[List[str], List[str]]) -> Dict[str, Tuple[Set[str], Set[str]]]:
    """
    Worker function to analyze relationships for a chunk of functions.

    Args:
        args: Tuple of (chunk_functions, all_functions)

    Returns:
        Dict mapping func_name to (callers, callees) tuple
    """
    chunk_functions, all_functions = args
    results = {}

    for func_name in chunk_functions:
        callers = set()
        callees = set()

        for other_name in all_functions:
            if other_name != func_name:
                # Detect call relationship (simple heuristic)
                if other_name in func_name:
                    callees.add(other_name)
                    # other_name is a callee of func_name
                if func_name in other_name:
                    callers.add(other_name)
                    # func_name is called by other_name

        results[func_name] = (callers, callees)

    return results


def _calculate_importance_worker(args: Tuple[str, int, int]) -> Tuple[str, float]:
    """
    Worker function to calculate importance score for a single function.

    Args:
        args: Tuple of (func_name, caller_count, callee_count)

    Returns:
        Tuple of (func_name, importance_score)
    """
    func_name, caller_count, callee_count = args
    # Importance based on connectivity (PageRank-like)
    # Functions called by many others are important
    # Functions that call many others are also important (hubs)
    importance = caller_count * 2 + callee_count
    return func_name, importance


@dataclass
class FunctionNode:
    """Node in function call graph."""
    name: str
    function_obj: Optional[Callable] = None  # Default to None if not provided
    call_count: int = 0
    total_time: float = 0.0
    callers: Set[str] = None
    callees: Set[str] = None
    source_lines: int = 0
    complexity: int = 1
    
    def __post_init__(self):
        if self.callers is None:
            self.callers = set()
        if self.callees is None:
            self.callees = set()


@dataclass
class InliningAnalysis:
    """Analysis result for inlining decision."""
    should_inline: bool
    inlining_benefit: float
    reasoning: List[str]
    estimated_speedup: float
    size_cost: int  # Code size increase
    compile_time_cost: float


@dataclass
class CrossOptimizationPlan:
    """Plan for cross-function optimization."""
    priority_order: List[str]
    inline_candidates: Dict[str, List[str]]  # caller -> [callees to inline]
    optimization_clusters: List[List[str]]
    expected_total_speedup: float
    reasoning: List[str]


class CrossFunctionOptimizer:
    """
    Cross-function optimization system for intelligent JIT compilation.
    
    Analyzes function relationships, call graphs, and implements optimization
    strategies that work across function boundaries including inlining.
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """Initialize cross-function optimizer.

        Args:
            max_workers: Maximum workers for parallel processing. Defaults to CPU count.
        """
        self.logger = logging.getLogger(__name__)

        # Parallel processing configuration
        self._max_workers = max_workers or min(os.cpu_count() or 4, 8)
        self._lock = threading.Lock()
        self._is_shutdown = False

        # Call graph analysis
        self._call_graphs: Dict[str, Dict[str, FunctionNode]] = {}
        self._optimization_history: List[Dict[str, Any]] = []

        # Inlining thresholds
        self._inlining_config = {
            'max_inline_size_lines': 10,  # Maximum lines for inlining
            'min_call_frequency': 50,     # Minimum calls to consider inlining
            'max_nesting_depth': 3,       # Maximum inlining nesting
            'min_speedup_threshold': 1.05  # Minimum 5% speedup for inlining
        }
    
    def analyze_function_relationships(self, function_names: List[str],
                                         parallel: bool = False) -> Dict[str, Any]:
        """
        Analyze relationships between functions to build call graph.

        Args:
            function_names: List of function names to analyze
            parallel: If True, use parallel processing for O(n^2) analysis

        Returns:
            Call graph analysis results
        """
        if not function_names:
            return {}

        call_graph = {}

        # Initialize nodes for each function
        for func_name in function_names:
            call_graph[func_name] = FunctionNode(name=func_name)

        if not parallel or len(function_names) < 20:
            # Sequential for small inputs (overhead not worth it)
            for func_name in function_names:
                node = call_graph[func_name]

                for other_name in function_names:
                    if other_name != func_name:
                        if other_name in func_name or self._detect_call_relationship(func_name, other_name):
                            node.callees.add(other_name)
                            call_graph[other_name].callers.add(func_name)
        else:
            # Parallel processing for large inputs
            # Chunk the function names for parallel analysis
            chunk_size = max(1, len(function_names) // self._max_workers)
            chunks = []
            for i in range(0, len(function_names), chunk_size):
                chunk = function_names[i:i + chunk_size]
                chunks.append((chunk, function_names))

            # Analyze chunks in parallel using ThreadPool (no orphan risk)
            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                chunk_results = list(executor.map(_analyze_function_chunk_worker, chunks))

            # Merge results into call graph
            for chunk_result in chunk_results:
                for func_name, (callers, callees) in chunk_result.items():
                    node = call_graph[func_name]
                    node.callers.update(callers)
                    node.callees.update(callees)

            # Update reverse relationships
            for func_name, node in call_graph.items():
                for callee_name in node.callees:
                    if callee_name in call_graph:
                        call_graph[callee_name].callers.add(func_name)

        return call_graph
    
    def create_cross_optimization_plan(self, call_graph: Dict[str, Any],
                                        parallel: bool = False) -> Dict[str, Any]:
        """
        Create cross-function optimization plan based on call graph.

        Args:
            call_graph: Function call graph
            parallel: If True, use parallel processing for importance calculation

        Returns:
            Cross-optimization plan
        """
        # Analyze function importance (based on connectivity and usage)
        if parallel:
            importance_scores = self.calculate_function_importance_parallel(call_graph)
        else:
            importance_scores = self._calculate_function_importance(call_graph)
        
        # Sort by importance for priority order
        priority_order = sorted(importance_scores.keys(), 
                              key=lambda x: importance_scores[x], reverse=True)
        
        # Identify inlining candidates
        inline_candidates = self._identify_inlining_candidates(call_graph)
        
        # Identify optimization clusters (related functions)
        optimization_clusters = self._identify_optimization_clusters(call_graph)
        
        # Estimate total speedup
        expected_speedup = self._estimate_cross_optimization_speedup(
            call_graph, inline_candidates, optimization_clusters
        )
        
        plan = CrossOptimizationPlan(
            priority_order=priority_order,
            inline_candidates=inline_candidates,
            optimization_clusters=optimization_clusters,
            expected_total_speedup=expected_speedup,
            reasoning=[
                f'Prioritized {len(priority_order)} functions by call graph importance',
                f'Identified {len(inline_candidates)} inlining opportunities',
                f'Found {len(optimization_clusters)} optimization clusters'
            ]
        )
        
        return plan.__dict__
    
    def analyze_function_cluster(self, function_cluster: Dict[str, Callable]) -> Dict[str, Any]:
        """
        Analyze a cluster of related functions for optimization.
        
        Args:
            function_cluster: Dictionary of function name -> function object
            
        Returns:
            Cluster analysis results
        """
        cluster_analysis = {
            'cluster_size': len(function_cluster),
            'cluster_root': None,
            'optimization_opportunities': [],
            'interconnectedness': 0.0
        }
        
        # Build call relationships within cluster
        relationships = {}
        for name, func in function_cluster.items():
            relationships[name] = self._analyze_function_dependencies(func, function_cluster)
        
        # Find cluster root (most connected function)
        connectivity_scores = {}
        for name, deps in relationships.items():
            connectivity_scores[name] = len(deps['calls']) + len(deps['called_by'])
        
        if connectivity_scores:
            cluster_root = max(connectivity_scores.keys(), key=lambda x: connectivity_scores[x])
            cluster_analysis['cluster_root'] = cluster_root
            cluster_analysis['interconnectedness'] = max(connectivity_scores.values()) / len(function_cluster)
        
        # Identify optimization opportunities
        opportunities = []
        for name, deps in relationships.items():
            if len(deps['calls']) > 0:
                opportunities.append({
                    'type': 'inlining_opportunity',
                    'caller': name,
                    'callees': list(deps['calls']),
                    'benefit_estimate': len(deps['calls']) * 0.1  # 10% per inlined call
                })
        
        cluster_analysis['optimization_opportunities'] = opportunities
        
        return cluster_analysis
    
    def analyze_inlining_opportunity(self, caller_func: Callable, callee_func: Callable,
                                   call_frequency: int, callee_size: int) -> Dict[str, Any]:
        """
        Analyze inlining opportunity between two functions.
        
        Args:
            caller_func: Function that calls the other
            callee_func: Function being called
            call_frequency: How often the call happens
            callee_size: Size of callee function (lines)
            
        Returns:
            Inlining analysis results
        """
        analysis = InliningAnalysis(
            should_inline=False,
            inlining_benefit=1.0,
            reasoning=[],
            estimated_speedup=1.0,
            size_cost=callee_size,
            compile_time_cost=callee_size * 0.1  # Estimate: 0.1ms per line
        )
        
        # Analyze inlining criteria
        if callee_size <= self._inlining_config['max_inline_size_lines']:
            analysis.reasoning.append('small_function')
            analysis.inlining_benefit += 0.1
        
        if call_frequency >= self._inlining_config['min_call_frequency']:
            analysis.reasoning.append('high_frequency')
            analysis.inlining_benefit += call_frequency / 1000.0
        
        # Calculate estimated speedup (avoid function call overhead)
        call_overhead_reduction = call_frequency * 0.00001  # 10μs per call saved
        analysis.estimated_speedup = 1.0 + call_overhead_reduction
        
        # Make inlining decision
        if (analysis.inlining_benefit > 1.2 and  # 20% benefit threshold
            analysis.estimated_speedup >= self._inlining_config['min_speedup_threshold']):
            analysis.should_inline = True
            analysis.reasoning.append('benefit_threshold_met')
        
        return analysis.__dict__
    
    def create_inlined_version(self, caller_func: Callable, callee_func: Callable) -> Optional[Callable]:
        """
        Create inlined version of caller function with callee inlined.
        
        Args:
            caller_func: Function to inline into
            callee_func: Function to inline
            
        Returns:
            Inlined function if possible, None otherwise
        """
        try:
            # Get source code of both functions
            caller_source = inspect.getsource(caller_func)
            callee_source = inspect.getsource(callee_func)
            
            # Simple inlining: replace function calls with function body
            # This is a simplified implementation - real inlining is more complex
            callee_name = callee_func.__name__
            
            # Extract callee function body
            callee_tree = ast.parse(callee_source)
            callee_func_def = callee_tree.body[0]  # Assume single function
            
            if isinstance(callee_func_def, ast.FunctionDef):
                # Create inlined version (simplified)
                inlined_source = self._perform_simple_inlining(caller_source, callee_name, callee_func_def)
                
                # Compile inlined version
                namespace = caller_func.__globals__.copy()
                exec(inlined_source, namespace)
                
                # Get the inlined function
                inlined_func_name = f"{caller_func.__name__}_inlined"
                if inlined_func_name in namespace:
                    return namespace[inlined_func_name]
            
            return None
            
        except Exception as e:
            logger.warning(f"Inlining failed for {caller_func.__name__}: {e}")
            return None
    
    def build_call_graph_from_profile_data(self, call_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build call graph from profiling data.
        
        Args:
            call_data: Dictionary of function name -> profile data
            
        Returns:
            Call graph structure
        """
        call_graph = {}
        
        for func_name, profile in call_data.items():
            call_graph[func_name] = {
                'call_count': profile.get('call_count', 0),
                'total_time': profile.get('total_time', 0.0),
                'average_time': profile.get('total_time', 0.0) / max(1, profile.get('call_count', 1)),
                'importance_score': profile.get('call_count', 0) * profile.get('total_time', 0.0)
            }
        
        return call_graph
    
    def identify_critical_functions(self, call_graph: Dict[str, Any]) -> List[str]:
        """
        Identify critical functions based on call graph analysis.
        
        Args:
            call_graph: Call graph data
            
        Returns:
            List of function names sorted by criticality
        """
        # Sort by importance score (call count * total time)
        functions_by_importance = sorted(
            call_graph.keys(),
            key=lambda f: call_graph[f].get('importance_score', 0),
            reverse=True
        )
        
        return functions_by_importance
    
    def determine_inlining_strategy(self, call_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine inlining strategy based on call graph.
        
        Args:
            call_graph: Call graph data
            
        Returns:
            Inlining strategy
        """
        inline_targets = []
        
        # Simple inlining strategy: inline small, frequently called functions
        for func_name, data in call_graph.items():
            if (data.get('call_count', 0) > 100 and  # Frequently called
                data.get('average_time', 0) < 0.001):  # Fast execution (small function)
                inline_targets.append(func_name)
        
        return {
            'inline_targets': inline_targets,
            'strategy': 'frequency_based',
            'total_inline_opportunities': len(inline_targets)
        }
    
    def _detect_call_relationship(self, caller_name: str, callee_name: str) -> bool:
        """Detect if caller function calls callee function."""
        # Simple heuristic: if callee name appears in caller name structure
        # Real implementation would use AST analysis or runtime call tracking
        return callee_name in caller_name
    
    def _calculate_function_importance(self, call_graph: Dict[str, Any]) -> Dict[str, float]:
        """Calculate importance scores for functions in call graph."""
        importance_scores = {}
        
        for func_name, node in call_graph.items():
            # Importance based on connectivity (PageRank-like algorithm)
            caller_count = len(node.callers) if hasattr(node, 'callers') else 0
            callee_count = len(node.callees) if hasattr(node, 'callees') else 0
            
            # Functions called by many others are important
            # Functions that call many others are also important (hubs)
            importance = caller_count * 2 + callee_count
            importance_scores[func_name] = importance
        
        return importance_scores
    
    def _identify_inlining_candidates(self, call_graph: Dict[str, Any]) -> Dict[str, List[str]]:
        """Identify functions that should be inlined into their callers."""
        inline_candidates = defaultdict(list)
        
        for func_name, node in call_graph.items():
            if not hasattr(node, 'callees'):
                continue
                
            for callee_name in node.callees:
                callee_node = call_graph.get(callee_name)
                if callee_node:
                    # Simple inlining criteria
                    if (len(callee_node.callers) <= 2 and  # Not widely used
                        callee_node.source_lines <= 5):    # Small function
                        inline_candidates[func_name].append(callee_name)
        
        return dict(inline_candidates)
    
    def _identify_optimization_clusters(self, call_graph: Dict[str, Any]) -> List[List[str]]:
        """Identify clusters of related functions for joint optimization."""
        clusters = []
        visited = set()
        
        # Simple clustering: functions that call each other form clusters
        for func_name, node in call_graph.items():
            if func_name in visited or not hasattr(node, 'callees'):
                continue
            
            cluster = [func_name]
            visited.add(func_name)
            
            # Add related functions to cluster
            for callee_name in node.callees:
                if callee_name not in visited and callee_name in call_graph:
                    cluster.append(callee_name)
                    visited.add(callee_name)
            
            if len(cluster) > 1:
                clusters.append(cluster)
        
        return clusters
    
    def _estimate_cross_optimization_speedup(self, call_graph: Dict[str, Any],
                                           inline_candidates: Dict[str, List[str]],
                                           clusters: List[List[str]]) -> float:
        """Estimate total speedup from cross-function optimization."""
        total_speedup = 1.0
        
        # Speedup from inlining (avoid function call overhead)
        for caller, callees in inline_candidates.items():
            inlining_speedup = 1.0 + len(callees) * 0.05  # 5% per inlined call
            total_speedup *= inlining_speedup
        
        # Speedup from cluster optimization (better instruction scheduling)
        cluster_speedup = 1.0 + len(clusters) * 0.02  # 2% per optimized cluster
        total_speedup *= cluster_speedup
        
        return total_speedup
    
    def _analyze_function_dependencies(self, func: Callable, 
                                     function_cluster: Dict[str, Callable]) -> Dict[str, Any]:
        """Analyze dependencies of a function within a cluster."""
        dependencies = {
            'calls': set(),
            'called_by': set()
        }
        
        try:
            # Get function source for analysis
            source = inspect.getsource(func)
            func_name = func.__name__
            
            # Simple dependency detection: check if other function names appear in source
            for other_name, other_func in function_cluster.items():
                if other_name != func_name:
                    if other_name in source:
                        dependencies['calls'].add(other_name)
                    
                    # Check reverse dependency
                    try:
                        other_source = inspect.getsource(other_func)
                        if func_name in other_source:
                            dependencies['called_by'].add(other_name)
                    except:
                        pass
            
        except Exception as e:
            logger.debug(f"Function dependency analysis failed for {func.__name__}: {e}")
        
        return dependencies
    
    def _perform_simple_inlining(self, caller_source: str, callee_name: str, 
                                callee_ast: ast.FunctionDef) -> str:
        """
        Perform simple inlining transformation.
        
        Args:
            caller_source: Source code of caller function
            callee_name: Name of function to inline
            callee_ast: AST of callee function
            
        Returns:
            Modified source code with inlining
        """
        # Simple inlining: replace function calls with function body
        # This is a simplified implementation - real inlining is much more complex
        
        # Create a new inlined version that includes both functions
        # Real inlining would perform AST transformation
        
        caller_lines = caller_source.split('\n')
        
        # Find the caller function and create inlined version
        inlined_lines = []
        for line in caller_lines:
            if f'def {caller_lines[0].split("def ")[1].split("(")[0]}' in line:
                # Replace function name to create inlined version
                inlined_lines.append(line.replace(
                    caller_lines[0].split("def ")[1].split("(")[0],
                    caller_lines[0].split("def ")[1].split("(")[0] + "_inlined"
                ))
            else:
                inlined_lines.append(line)
        
        return '\n'.join(inlined_lines)

    def calculate_function_importance_parallel(self, call_graph: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate importance scores for functions in parallel.

        Args:
            call_graph: Function call graph

        Returns:
            Dictionary mapping function name to importance score
        """
        if not call_graph:
            return {}

        # Prepare work items
        work_items = []
        for func_name, node in call_graph.items():
            caller_count = len(node.callers) if hasattr(node, 'callers') else 0
            callee_count = len(node.callees) if hasattr(node, 'callees') else 0
            work_items.append((func_name, caller_count, callee_count))

        if len(work_items) < 10:
            # Sequential for small inputs
            return self._calculate_function_importance(call_graph)

        # Parallel processing (ThreadPool - no orphan risk)
        importance_scores = {}
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            for func_name, importance in executor.map(_calculate_importance_worker, work_items):
                importance_scores[func_name] = importance

        return importance_scores

    def build_call_graph_from_profile_data(self, call_data: Dict[str, Dict[str, Any]],
                                           parallel: bool = False) -> Dict[str, Any]:
        """
        Build call graph from profiling data.

        Args:
            call_data: Dictionary of function name -> profile data
            parallel: If True, use parallel processing (currently unused)

        Returns:
            Call graph structure
        """
        call_graph = {}

        for func_name, profile in call_data.items():
            call_graph[func_name] = {
                'call_count': profile.get('call_count', 0),
                'total_time': profile.get('total_time', 0.0),
                'average_time': profile.get('total_time', 0.0) / max(1, profile.get('call_count', 1)),
                'importance_score': profile.get('call_count', 0) * profile.get('total_time', 0.0)
            }

        return call_graph

    def shutdown(self) -> None:
        """Shutdown parallel resources and release worker pools."""
        with self._lock:
            if self._is_shutdown:
                return
            self._is_shutdown = True

    def __enter__(self) -> 'CrossFunctionOptimizer':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - shutdown resources."""
        self.shutdown()


# Global instance for performance
_global_cross_optimizer = None

def get_cross_function_optimizer() -> CrossFunctionOptimizer:
    """Get global cross-function optimizer instance."""
    global _global_cross_optimizer
    if _global_cross_optimizer is None:
        _global_cross_optimizer = CrossFunctionOptimizer()
    return _global_cross_optimizer