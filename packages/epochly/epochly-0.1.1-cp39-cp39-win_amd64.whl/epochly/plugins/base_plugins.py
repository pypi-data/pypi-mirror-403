"""
Epochly Plugin Base Classes

This module provides the base classes and interfaces for the Epochly plugin architecture.
It defines the core plugin types: EpochlyAnalyzer, EpochlyExecutor, EpochlyOptimizer, EpochlyCommunicator, and EpochlyMonitor.

Author: Epochly Development Team
"""

import logging
import threading
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Callable, Set, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
import re
from packaging import version

from ..utils.exceptions import EpochlyError
from ..utils.decorators import thread_safe
from .plugin_manager import PluginInterface


class PluginType(Enum):
    """Enumeration of Epochly plugin types."""
    ANALYZER = "analyzer"
    EXECUTOR = "executor"
    OPTIMIZER = "optimizer"
    COMMUNICATOR = "communicator"
    MONITOR = "monitor"


class PluginPriority(Enum):
    """Plugin execution priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class DependencyError(EpochlyError):
    """Base exception for dependency validation errors."""
    pass


class CircularDependencyError(DependencyError):
    """Exception raised when circular dependencies are detected."""
    pass


class MissingDependencyError(DependencyError):
    """Exception raised when required dependencies are missing."""
    pass


class VersionConflictError(DependencyError):
    """Exception raised when dependency version conflicts occur."""
    pass


@dataclass
class PluginDependency:
    """Represents a plugin dependency with version constraints."""
    name: str
    version_spec: str = "*"  # Default to any version
    optional: bool = False
    resolved: bool = False
    resolved_version: Optional[str] = None
    
    def is_compatible(self, plugin_version: str) -> bool:
        """Check if a plugin version satisfies this dependency."""
        if self.version_spec == "*":
            return True
        
        try:
            # Handle multiple version constraints
            constraints = self.version_spec.split(",")
            for constraint in constraints:
                constraint = constraint.strip()
                
                # Handle != operator
                if constraint.startswith("!="):
                    excluded_version = constraint[2:].strip()
                    if plugin_version == excluded_version:
                        return False
                    continue
                
                # Handle other operators
                match = re.match(r'^([><=]+)\s*(.+)$', constraint)
                if match:
                    op, ver = match.groups()
                    
                    try:
                        plugin_ver = version.parse(plugin_version)
                        constraint_ver = version.parse(ver)
                    except:
                        # If parsing fails, do string comparison
                        plugin_ver = plugin_version
                        constraint_ver = ver
                    
                    if op == ">=":
                        if not (plugin_ver >= constraint_ver):
                            return False
                    elif op == ">":
                        if not (plugin_ver > constraint_ver):
                            return False
                    elif op == "<=":
                        if not (plugin_ver <= constraint_ver):
                            return False
                    elif op == "<":
                        if not (plugin_ver < constraint_ver):
                            return False
                    elif op == "==":
                        if not (plugin_ver == constraint_ver):
                            return False
                else:
                    # No operator means exact match
                    if plugin_version != constraint:
                        return False
            
            return True
            
        except Exception:
            # If any parsing fails, be permissive
            return True
    
    def mark_resolved(self, version: Optional[str]) -> None:
        """Mark this dependency as resolved with the given version."""
        self.resolved = True
        self.resolved_version = version


@dataclass
class ValidationResult:
    """Result of dependency validation."""
    is_valid: bool
    resolved_dependencies: Dict[str, str] = field(default_factory=dict)
    load_order: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class PluginMetadata:
    """Metadata for Epochly plugins."""
    name: str
    version: str
    plugin_type: PluginType
    priority: PluginPriority
    dependencies: List[PluginDependency] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    version_requirements: Dict[str, str] = field(default_factory=dict)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)


class EpochlyPlugin(PluginInterface):
    """
    Base class for all Epochly plugins.
    
    Provides common functionality and enforces the Epochly plugin contract.
    """
    
    def __init__(self, name: str, version: str, metadata: Optional[PluginMetadata] = None):
        self._name = name
        self._version = version
        # Create metadata if not provided
        if metadata is None:
            metadata = PluginMetadata(
                name=name,
                version=version,
                plugin_type=PluginType.EXECUTOR,  # Default type
                priority=PluginPriority.NORMAL
            )
        self._metadata = metadata
        self._logger = logging.getLogger(f"epochly.plugins.{name}")
        self._initialized = False
        self._lock = threading.RLock()
    
    @property
    def name(self) -> str:
        """Plugin name."""
        return self._name
    
    @property
    def version(self) -> str:
        """Plugin version."""
        return self._version
    
    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata."""
        return self._metadata
    
    @property
    def plugin_type(self) -> PluginType:
        """Plugin type."""
        return self._metadata.plugin_type
    
    @property
    def priority(self) -> PluginPriority:
        """Plugin priority."""
        return self._metadata.priority
    
    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized
    
    @thread_safe
    def initialize(self) -> None:
        """Initialize the plugin with thread safety."""
        if self._initialized:
            return
        
        try:
            self._logger.info(f"Initializing plugin: {self.name}")
            self._validate_dependencies()
            self._setup_plugin()
            self._initialized = True
            self._logger.info(f"Plugin initialized successfully: {self.name}")
        except Exception as e:
            self._logger.error(f"Failed to initialize plugin {self.name}: {e}")
            raise EpochlyError(f"Plugin initialization failed: {e}")
    
    @thread_safe
    def cleanup(self) -> None:
        """Clean up plugin resources with thread safety."""
        if not self._initialized:
            return
        
        try:
            self._logger.info(f"Cleaning up plugin: {self.name}")
            self._teardown_plugin()
            self._initialized = False
            self._logger.info(f"Plugin cleaned up successfully: {self.name}")
        except Exception as e:
            self._logger.error(f"Failed to cleanup plugin {self.name}: {e}")
            raise EpochlyError(f"Plugin cleanup failed: {e}")
    
    def _validate_dependencies(self) -> None:
        """Validate plugin dependencies."""
        # Get the global dependency validator
        validator = DependencyValidator.get_instance()
        
        # Register this plugin if not already registered
        if self.name not in validator.registered_plugins:
            validator.register_plugin(self)
        
        # Validate dependencies
        try:
            result = validator.validate_dependencies(self.name)
            if not result.is_valid:
                errors = "\n".join(result.errors)
                raise DependencyError(f"Dependency validation failed for {self.name}:\n{errors}")
            
            # Log warnings if any
            for warning in result.warnings:
                self._logger.warning(warning)
                
        except DependencyError:
            raise
        except Exception as e:
            raise DependencyError(f"Unexpected error during dependency validation: {e}")
    
    @abstractmethod
    def _setup_plugin(self) -> None:
        """Setup plugin-specific resources."""
        pass
    
    @abstractmethod
    def _teardown_plugin(self) -> None:
        """Teardown plugin-specific resources."""
        pass


class EpochlyAnalyzer(EpochlyPlugin):
    """
    Base class for Epochly analyzer plugins.
    
    Analyzers examine code and runtime behavior to identify optimization opportunities.
    """
    
    def __init__(self, name: str, version: str, metadata: PluginMetadata):
        if metadata.plugin_type != PluginType.ANALYZER:
            raise EpochlyError(f"Invalid plugin type for analyzer: {metadata.plugin_type}")
        super().__init__(name, version, metadata)
    
    @abstractmethod
    def analyze_code(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code for optimization opportunities.
        
        Args:
            code: Source code to analyze
            context: Analysis context and metadata
            
        Returns:
            Analysis results with optimization recommendations
        """
        pass
    
    @abstractmethod
    def analyze_runtime(self, runtime_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze runtime behavior for optimization opportunities.
        
        Args:
            runtime_data: Runtime performance and behavior data
            
        Returns:
            Runtime analysis results
        """
        pass
    
    def get_analysis_capabilities(self) -> List[str]:
        """Get list of analysis capabilities."""
        return self.metadata.capabilities


class EpochlyExecutor(EpochlyPlugin):
    """
    Base class for Epochly executor plugins.
    
    Executors handle the actual execution of optimized code.
    """
    
    def __init__(self, name: str, version: str, metadata: PluginMetadata):
        if metadata.plugin_type != PluginType.EXECUTOR:
            raise EpochlyError(f"Invalid plugin type for executor: {metadata.plugin_type}")
        super().__init__(name, version, metadata)
        self._shutdown = False
        self._registered_functions = {}
    
    @abstractmethod
    def execute_optimized(self, code: str, optimization_plan: Dict[str, Any]) -> Any:
        """
        Execute optimized code according to the optimization plan.
        
        Args:
            code: Optimized code to execute
            optimization_plan: Optimization strategy and parameters
            
        Returns:
            Execution result
        """
        pass
    
    @abstractmethod
    def supports_optimization(self, optimization_type: str) -> bool:
        """
        Check if executor supports a specific optimization type.
        
        Args:
            optimization_type: Type of optimization to check
            
        Returns:
            True if supported, False otherwise
        """
        pass
    
    def get_execution_capabilities(self) -> List[str]:
        """Get list of execution capabilities."""
        return self.metadata.capabilities
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return self.metadata
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get executor status.
        
        Returns:
            Status dictionary with executor information
        """
        return {
            "executor_name": self.name,
            "executor_version": self.version,
            "initialized": self._initialized,
            "shutdown": self._shutdown,
            "capabilities": self.get_execution_capabilities()
        }
    
    def execute(self, func: Callable, *args, timeout: Optional[float] = None, **kwargs) -> Any:
        """
        Execute a function with optional timeout.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            timeout: Optional timeout in seconds
            **kwargs: Keyword arguments
            
        Returns:
            Execution result
        """
        raise NotImplementedError("Subclasses must implement execute method")
    
    def register(self, name: str, func: Callable) -> None:
        """
        Register a function for later execution.
        
        Args:
            name: Name to register the function under
            func: Function to register
        """
        self._registered_functions[name] = func
    
    def get_registered_function(self, name: str) -> Optional[Callable]:
        """
        Get a registered function by name.
        
        Args:
            name: Name of the function to retrieve
            
        Returns:
            The registered function or None if not found
        """
        return self._registered_functions.get(name)
    
    def discover_benchmarks(self) -> List[str]:
        """
        Discover available benchmarks.
        
        Returns:
            List of benchmark names
        """
        return []
    
    def discover_integration_tests(self) -> List[str]:
        """
        Discover available integration tests.
        
        Returns:
            List of integration test names
        """
        return []
    
    def get_fallback_executor(self) -> Optional['EpochlyExecutor']:
        """
        Get fallback executor if available.
        
        Returns:
            Fallback executor or None
        """
        return None
    
    def cleanup(self) -> None:
        """Clean up executor resources."""
        super().cleanup()
        self._shutdown = True
    
    def create_actor(self, actor_class: type, *args, **kwargs) -> Any:
        """
        Create an actor for exceptional stateful needs.
        
        This method is provided for cases where stateful execution is absolutely
        necessary. However, it should be used sparingly as it goes against the
        stateless design principles of Epochly.
        
        Args:
            actor_class: The actor class to instantiate
            *args: Positional arguments for the actor constructor
            **kwargs: Keyword arguments for the actor constructor
            
        Returns:
            Actor instance or proxy
            
        Raises:
            NotImplementedError: If the executor doesn't support actors
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support actor creation. "
            "Use a specialized actor-supporting executor if stateful execution is required."
        )


class EpochlyOptimizer(EpochlyPlugin):
    """
    Base class for Epochly optimizer plugins.
    
    Optimizers transform code and create optimization plans.
    """
    
    def __init__(self, name: str, version: str, metadata: PluginMetadata):
        if metadata.plugin_type != PluginType.OPTIMIZER:
            raise EpochlyError(f"Invalid plugin type for optimizer: {metadata.plugin_type}")
        super().__init__(name, version, metadata)
    
    @abstractmethod
    def optimize_code(self, code: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize code based on analysis results.
        
        Args:
            code: Source code to optimize
            analysis_results: Results from analyzer plugins
            
        Returns:
            Optimization results including optimized code and plan
        """
        pass
    
    @abstractmethod
    def create_optimization_plan(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an optimization plan based on analysis results.
        
        Args:
            analysis_results: Results from analyzer plugins
            
        Returns:
            Optimization plan with strategy and parameters
        """
        pass
    
    def get_optimization_capabilities(self) -> List[str]:
        """Get list of optimization capabilities."""
        return self.metadata.capabilities


class EpochlyCommunicator(EpochlyPlugin):
    """
    Base class for Epochly communicator plugins.
    
    Communicators handle inter-process and inter-interpreter communication.
    """
    
    def __init__(self, name: str, version: str, metadata: PluginMetadata):
        if metadata.plugin_type != PluginType.COMMUNICATOR:
            raise EpochlyError(f"Invalid plugin type for communicator: {metadata.plugin_type}")
        super().__init__(name, version, metadata)
    
    @abstractmethod
    def send_message(self, target: str, message: Dict[str, Any]) -> bool:
        """
        Send a message to a target.
        
        Args:
            target: Target identifier
            message: Message data
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def receive_message(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Receive a message.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            Received message or None if timeout
        """
        pass
    
    @abstractmethod
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """
        Register a message handler.
        
        Args:
            message_type: Type of message to handle
            handler: Handler function
        """
        pass
    
    def get_communication_capabilities(self) -> List[str]:
        """Get list of communication capabilities."""
        return self.metadata.capabilities


class EpochlyMonitor(EpochlyPlugin):
    """
    Base class for Epochly monitor plugins.
    
    Monitors track performance and system behavior.
    """
    
    def __init__(self, name: str, version: str, metadata: PluginMetadata):
        if metadata.plugin_type != PluginType.MONITOR:
            raise EpochlyError(f"Invalid plugin type for monitor: {metadata.plugin_type}")
        super().__init__(name, version, metadata)
    
    @abstractmethod
    def start_monitoring(self, targets: List[str]) -> None:
        """
        Start monitoring specified targets.
        
        Args:
            targets: List of targets to monitor
        """
        pass
    
    @abstractmethod
    def stop_monitoring(self) -> None:
        """Stop monitoring."""
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current monitoring metrics.
        
        Returns:
            Current metrics data
        """
        pass
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return self.metadata
    
    @abstractmethod
    def set_alert_threshold(self, metric: str, threshold: float) -> None:
        """
        Set alert threshold for a metric.
        
        Args:
            metric: Metric name
            threshold: Alert threshold value
        """
        pass
    
    def get_monitoring_capabilities(self) -> List[str]:
        """Get list of monitoring capabilities."""
        return self.metadata.capabilities


# Plugin factory functions
def create_analyzer_metadata(
    name: str = "GenericAnalyzer",
    version: str = "1.0.0",
    priority: PluginPriority = PluginPriority.NORMAL,
    dependencies: Optional[List[Union[str, PluginDependency]]] = None,
    capabilities: Optional[List[str]] = None
) -> PluginMetadata:
    """Create metadata for analyzer plugins."""
    return PluginMetadata(
        name=name,
        version=version,
        plugin_type=PluginType.ANALYZER,
        priority=priority,
        dependencies=dependencies or [],
        capabilities=capabilities or [],
        version_requirements={},
        resource_requirements={}
    )


def create_executor_metadata(
    name: str = "GenericExecutor",
    version: str = "1.0.0",
    priority: PluginPriority = PluginPriority.HIGH,
    dependencies: Optional[List[Union[str, PluginDependency]]] = None,
    capabilities: Optional[List[str]] = None
) -> PluginMetadata:
    """Create metadata for executor plugins."""
    return PluginMetadata(
        name=name,
        version=version,
        plugin_type=PluginType.EXECUTOR,
        priority=priority,
        dependencies=dependencies or [],
        capabilities=capabilities or [],
        version_requirements={},
        resource_requirements={}
    )


def create_optimizer_metadata(
    name: str = "GenericOptimizer",
    version: str = "1.0.0",
    priority: PluginPriority = PluginPriority.HIGH,
    dependencies: Optional[List[Union[str, PluginDependency]]] = None,
    capabilities: Optional[List[str]] = None
) -> PluginMetadata:
    """Create metadata for optimizer plugins."""
    return PluginMetadata(
        name=name,
        version=version,
        plugin_type=PluginType.OPTIMIZER,
        priority=priority,
        dependencies=dependencies or [],
        capabilities=capabilities or [],
        version_requirements={},
        resource_requirements={}
    )


def create_communicator_metadata(
    name: str = "GenericCommunicator",
    version: str = "1.0.0",
    priority: PluginPriority = PluginPriority.CRITICAL,
    dependencies: Optional[List[Union[str, PluginDependency]]] = None,
    capabilities: Optional[List[str]] = None
) -> PluginMetadata:
    """Create metadata for communicator plugins."""
    return PluginMetadata(
        name=name,
        version=version,
        plugin_type=PluginType.COMMUNICATOR,
        priority=priority,
        dependencies=dependencies or [],
        capabilities=capabilities or [],
        version_requirements={},
        resource_requirements={}
    )


def create_monitor_metadata(
    name: str = "GenericMonitor",
    version: str = "1.0.0",
    priority: PluginPriority = PluginPriority.NORMAL,
    dependencies: Optional[List[Union[str, PluginDependency]]] = None,
    capabilities: Optional[List[str]] = None
) -> PluginMetadata:
    """Create metadata for monitor plugins."""
    # Convert string dependencies to PluginDependency objects
    dep_objects = []
    if dependencies:
        for dep in dependencies:
            if isinstance(dep, str):
                dep_objects.append(PluginDependency(name=dep))
            elif isinstance(dep, PluginDependency):
                dep_objects.append(dep)
    
    return PluginMetadata(
        name=name,
        version=version,
        plugin_type=PluginType.MONITOR,
        priority=priority,
        dependencies=dep_objects,
        capabilities=capabilities or [],
        version_requirements={},
        resource_requirements={}
    )


class DependencyValidator:
    """
    Validates and resolves plugin dependencies.
    
    This class manages plugin dependency resolution, circular dependency detection,
    version conflict resolution, and load order determination.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> 'DependencyValidator':
        """Get singleton instance of DependencyValidator."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    def __init__(self):
        """Initialize the dependency validator."""
        self.registered_plugins: Dict[str, EpochlyPlugin] = {}
        self._validation_cache: Dict[str, ValidationResult] = {}
        self._logger = logging.getLogger("epochly.plugins.dependency_validator")
    
    def register_plugin(self, plugin: EpochlyPlugin) -> None:
        """Register a plugin with the validator."""
        self.registered_plugins[plugin.name] = plugin
        # Clear validation cache when new plugin is registered
        self._validation_cache.clear()
        self._logger.debug(f"Registered plugin: {plugin.name} v{plugin.version}")
    
    def validate_dependencies(self, plugin_name: str) -> ValidationResult:
        """
        Validate dependencies for a specific plugin.
        
        Args:
            plugin_name: Name of the plugin to validate
            
        Returns:
            ValidationResult with validation status and details
            
        Raises:
            CircularDependencyError: If circular dependencies are detected
            MissingDependencyError: If required dependencies are missing
            VersionConflictError: If version conflicts are found
        """
        # Check cache first
        if plugin_name in self._validation_cache:
            return self._validation_cache[plugin_name]
        
        # Initialize result
        result = ValidationResult(is_valid=True)
        
        # Check if plugin exists
        if plugin_name not in self.registered_plugins:
            raise MissingDependencyError(f"Plugin not found: {plugin_name}")
        
        # Perform dependency resolution
        try:
            visited = set()
            stack = []
            self._resolve_dependencies(
                plugin_name, 
                visited, 
                stack, 
                result
            )
            
            # Cache successful result
            self._validation_cache[plugin_name] = result
            
        except DependencyError:
            # Re-raise dependency errors
            raise
        except Exception as e:
            # Wrap other errors
            raise DependencyError(f"Dependency validation failed: {e}")
        
        return result
    
    def _resolve_dependencies(
        self,
        plugin_name: str,
        visited: Set[str],
        stack: List[str],
        result: ValidationResult
    ) -> None:
        """Recursively resolve plugin dependencies."""
        # Check for circular dependencies
        if plugin_name in stack:
            cycle = " -> ".join(stack[stack.index(plugin_name):] + [plugin_name])
            raise CircularDependencyError(
                f"Circular dependency detected: {cycle}"
            )
        
        # Skip if already visited
        if plugin_name in visited:
            return
        
        # Get plugin
        plugin = self.registered_plugins.get(plugin_name)
        if not plugin:
            raise MissingDependencyError(f"Missing dependency: {plugin_name}")
        
        # Add to stack for circular dependency detection
        stack.append(plugin_name)
        
        # Process dependencies
        metadata = plugin.get_metadata()
        for dep in metadata.dependencies:
            # Check if dependency exists
            dep_plugin = self.registered_plugins.get(dep.name)
            
            if not dep_plugin:
                if dep.optional:
                    # Optional dependency missing - add warning
                    result.warnings.append(
                        f"Optional dependency not found: {dep.name}"
                    )
                    continue
                else:
                    # Required dependency missing
                    raise MissingDependencyError(
                        f"Missing dependency: {dep.name} required by {plugin_name}"
                    )
            
            # Check version compatibility
            dep_version = dep_plugin.version
            if not dep.is_compatible(dep_version):
                raise VersionConflictError(
                    f"Version conflict for {dep.name}: "
                    f"{plugin_name} requires {dep.version_spec} "
                    f"but {dep_version} is available"
                )
            
            # Recursively resolve dependencies
            self._resolve_dependencies(dep.name, visited, stack, result)
            
            # Mark as resolved
            result.resolved_dependencies[dep.name] = dep_version
        
        # Remove from stack
        stack.pop()
        
        # Mark as visited
        visited.add(plugin_name)
        
        # Add to load order (dependencies first)
        result.load_order.append(plugin_name)
    
    def get_all_dependencies(self, plugin_name: str) -> Set[str]:
        """Get all dependencies (direct and transitive) for a plugin."""
        result = self.validate_dependencies(plugin_name)
        return set(result.resolved_dependencies.keys())
    
    def validate_all(self) -> Dict[str, ValidationResult]:
        """Validate all registered plugins."""
        results = {}
        
        for plugin_name in self.registered_plugins:
            try:
                results[plugin_name] = self.validate_dependencies(plugin_name)
            except DependencyError as e:
                # Create error result
                results[plugin_name] = ValidationResult(
                    is_valid=False,
                    errors=[str(e)]
                )
        
        return results
    
    def get_global_load_order(self) -> List[str]:
        """Get global load order for all plugins."""
        # Validate all plugins
        results = self.validate_all()
        
        # Collect all plugins in dependency order
        loaded = set()
        load_order = []
        
        # Use topological sort
        for plugin_name in self.registered_plugins:
            if plugin_name not in loaded:
                self._add_to_global_order(
                    plugin_name, 
                    loaded, 
                    load_order, 
                    results
                )
        
        return load_order
    
    def _add_to_global_order(
        self,
        plugin_name: str,
        loaded: Set[str],
        load_order: List[str],
        results: Dict[str, ValidationResult]
    ) -> None:
        """Add plugin to global load order."""
        if plugin_name in loaded:
            return
        
        # Skip invalid plugins
        if not results[plugin_name].is_valid:
            return
        
        # Add dependencies first
        plugin = self.registered_plugins[plugin_name]
        metadata = plugin.get_metadata()
        
        for dep in metadata.dependencies:
            if dep.name in self.registered_plugins and not dep.optional:
                self._add_to_global_order(dep.name, loaded, load_order, results)
        
        # Add this plugin
        loaded.add(plugin_name)
        load_order.append(plugin_name)
    
    def get_dependency_graph(self) -> Dict[str, Dict[str, List[str]]]:
        """Get dependency graph for visualization."""
        graph = {}
        
        for plugin_name, plugin in self.registered_plugins.items():
            metadata = plugin.get_metadata()
            
            # Direct dependencies
            dependencies = [
                dep.name for dep in metadata.dependencies 
                if not dep.optional and dep.name in self.registered_plugins
            ]
            
            # Reverse dependencies (dependents)
            dependents = []
            for other_name, other_plugin in self.registered_plugins.items():
                if other_name == plugin_name:
                    continue
                    
                other_metadata = other_plugin.get_metadata()
                for dep in other_metadata.dependencies:
                    if dep.name == plugin_name and not dep.optional:
                        dependents.append(other_name)
                        break
            
            graph[plugin_name] = {
                "dependencies": dependencies,
                "dependents": dependents,
                "version": plugin.version
            }
        
        return graph
    
    def clear(self) -> None:
        """Clear all registered plugins and caches."""
        self.registered_plugins.clear()
        self._validation_cache.clear()
        self._logger.debug("Cleared plugin registry and caches")