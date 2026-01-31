"""
Cross-language Accelerator Plugin Interface (SPEC2 Task 16).

Allows Rust/C++ accelerators to register as Level 3 executors.
"""

import logging
import threading
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class PluginLanguage(Enum):
    """Supported plugin languages."""
    PYTHON = "python"
    RUST = "rust"
    CPP = "cpp"
    C = "c"


class PluginStatus(Enum):
    """Plugin lifecycle status."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class PluginCapabilities:
    """Plugin capability descriptor."""
    language: PluginLanguage
    supports_shared_memory: bool
    supports_async: bool
    max_concurrent_tasks: int
    memory_requirements_mb: int

    # Performance hints
    preferred_batch_size: int = 1
    warm_up_required: bool = False

    def __post_init__(self):
        """Validate capabilities."""
        if self.max_concurrent_tasks < 1:
            raise ValueError("max_concurrent_tasks must be >= 1")
        if self.memory_requirements_mb < 0:
            raise ValueError("memory_requirements_mb must be non-negative")


class PluginError(Exception):
    """Base exception for plugin errors."""
    pass


class AcceleratorPlugin(ABC):
    """
    Base class for accelerator plugins.

    Plugins must implement this interface to integrate with Epochly.
    """

    def __init__(self, name: str, capabilities: PluginCapabilities):
        """
        Initialize plugin.

        Args:
            name: Unique plugin name
            capabilities: Plugin capabilities descriptor
        """
        self.name = name
        self.capabilities = capabilities
        self._status = PluginStatus.UNINITIALIZED
        self._status_lock = threading.Lock()
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initialize the plugin.

        Called once before any execution.

        Args:
            config: Optional configuration dict

        Returns:
            True if initialization successful

        Raises:
            PluginError: If initialization fails
        """
        pass

    @abstractmethod
    def execute(self, task_data: Any, shared_memory_handle: Optional[Any] = None) -> Any:
        """
        Execute a task.

        Args:
            task_data: Task input data (serializable)
            shared_memory_handle: Optional shared memory handle

        Returns:
            Task result

        Raises:
            PluginError: If execution fails
        """
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """
        Shutdown the plugin.

        Called once during cleanup.

        Returns:
            True if shutdown successful
        """
        pass

    def get_status(self) -> PluginStatus:
        """Get current plugin status (thread-safe)."""
        with self._status_lock:
            return self._status

    def _set_status(self, status: PluginStatus) -> None:
        """Set plugin status (thread-safe)."""
        with self._status_lock:
            self._status = status

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.

        Returns:
            Dict with health status
        """
        return {
            'name': self.name,
            'status': self._status.value,
            'capabilities': {
                'language': self.capabilities.language.value,
                'supports_shared_memory': self.capabilities.supports_shared_memory,
                'max_concurrent_tasks': self.capabilities.max_concurrent_tasks
            }
        }

    def validate_task_data(self, task_data: Any) -> bool:
        """
        Validate task data.

        Override to implement custom validation.

        Args:
            task_data: Task data to validate

        Returns:
            True if valid
        """
        return task_data is not None


class PythonAcceleratorPlugin(AcceleratorPlugin):
    """
    Python-based accelerator plugin.

    Example implementation for Python plugins.
    """

    def __init__(self, name: str, executor_func):
        """
        Initialize Python plugin.

        Args:
            name: Plugin name
            executor_func: Callable that executes tasks
        """
        capabilities = PluginCapabilities(
            language=PluginLanguage.PYTHON,
            supports_shared_memory=False,
            supports_async=False,
            max_concurrent_tasks=1,
            memory_requirements_mb=0
        )
        super().__init__(name, capabilities)
        self._executor_func = executor_func

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize Python plugin."""
        self._set_status(PluginStatus.READY)
        self.logger.info(f"Python plugin '{self.name}' initialized")
        return True

    def execute(self, task_data: Any, shared_memory_handle: Optional[Any] = None) -> Any:
        """Execute task using Python function."""
        try:
            self._set_status(PluginStatus.RUNNING)
            result = self._executor_func(task_data)
            self._set_status(PluginStatus.READY)
            return result
        except Exception as e:
            self._set_status(PluginStatus.ERROR)
            raise PluginError(f"Execution failed: {e}") from e

    def shutdown(self) -> bool:
        """Shutdown Python plugin."""
        self._set_status(PluginStatus.SHUTDOWN)
        self.logger.info(f"Python plugin '{self.name}' shutdown")
        return True
