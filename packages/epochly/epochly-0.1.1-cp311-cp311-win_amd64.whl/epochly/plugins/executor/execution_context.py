"""
Execution Context Abstraction for Epochly

Provides a unified interface for different execution models (sub-interpreter,
thread) to replace mock contexts in production code.

ProcessContext has been removed per architectural decision - all CPU-bound 
parallel work should use SubInterpreterPool with ProcessPoolExecutor to avoid
the anti-pattern of duplicate process management.

This abstraction ensures that all execution models present a consistent
interface while maintaining their unique characteristics.

Author: Epochly Development Team
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, Union, Tuple
import threading
import multiprocessing
import time
import logging
import pickle
import marshal
import types
import sys
import os
import queue
import struct
import traceback
import atexit
import weakref
from dataclasses import dataclass, field
from concurrent.futures import Future, TimeoutError as FutureTimeoutError

# Import sub-interpreter support
try:
    # Python 3.12 uses _xxsubinterpreters
    import _xxsubinterpreters as interpreters
except ImportError:
    try:
        # Python 3.13+ uses interpreters
        import interpreters
    except ImportError:
        try:
            # Try _interpreters as a fallback
            import _interpreters as interpreters
        except ImportError:
            interpreters = None

# Global registry of all created sub-interpreters to ensure cleanup
_global_subinterpreters = set()
_global_subinterpreters_lock = threading.Lock()
_cleanup_registered = False

def _cleanup_all_subinterpreters():
    """Emergency cleanup of all sub-interpreters at process exit."""
    if not interpreters:
        return

    with _global_subinterpreters_lock:
        remaining = len(_global_subinterpreters)
        if _global_subinterpreters:
            logger = logging.getLogger(__name__)
            # CRITICAL: Don't call destroy() in venv - it blocks indefinitely
            # Just clear the registry; process exit will clean up interpreters
            logger.info(f"Clearing {remaining} sub-interpreters from registry (process exit will clean up)")
            _global_subinterpreters.clear()

# Register cleanup handler once
if interpreters and not _cleanup_registered:
    atexit.register(_cleanup_all_subinterpreters)
    _cleanup_registered = True


@dataclass
class ExecutionMetrics:
    """Metrics for execution context performance."""
    creation_time: float = field(default_factory=time.time)
    execution_count: int = 0
    total_execution_time: float = 0.0
    last_execution_time: float = 0.0
    errors: int = 0
    
    def record_execution(self, duration: float) -> None:
        """Record an execution with its duration."""
        self.execution_count += 1
        self.total_execution_time += duration
        self.last_execution_time = time.time()
    
    def record_error(self) -> None:
        """Record an execution error."""
        self.errors += 1
    
    @property
    def average_execution_time(self) -> float:
        """Get average execution time."""
        if self.execution_count == 0:
            return 0.0
        return self.total_execution_time / self.execution_count


class ExecutionContext(ABC):
    """
    Abstract base class for execution contexts.
    
    Provides a unified interface for different execution models:
    - Sub-interpreters (true isolation with per-interpreter GIL)
    - Processes (OS-level isolation)
    - Threads (shared memory, single GIL)
    """
    
    def __init__(self, context_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize execution context.
        
        Args:
            context_id: Unique identifier for this context
            config: Optional configuration for the context
        """
        self.context_id = context_id
        self.config = config or {}
        self.metrics = ExecutionMetrics()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._is_initialized = False
        self._is_active = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the execution context.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function in this context.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Function result
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the execution context and release resources."""
        pass
    
    @abstractmethod
    def is_alive(self) -> bool:
        """
        Check if the context is still alive and usable.
        
        Returns:
            True if context is alive, False otherwise
        """
        pass
    
    @property
    def is_initialized(self) -> bool:
        """Check if context is initialized."""
        return self._is_initialized
    
    @property
    def is_active(self) -> bool:
        """Check if context is currently executing."""
        return self._is_active
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get execution metrics for this context.
        
        Returns:
            Dictionary of metrics
        """
        return {
            'context_id': self.context_id,
            'type': self.__class__.__name__,
            'execution_count': self.metrics.execution_count,
            'total_execution_time': self.metrics.total_execution_time,
            'average_execution_time': self.metrics.average_execution_time,
            'errors': self.metrics.errors,
            'uptime': time.time() - self.metrics.creation_time,
            'is_alive': self.is_alive(),
            'is_active': self.is_active
        }


class SubInterpreterContext(ExecutionContext):
    """
    Execution context for Python sub-interpreters.
    
    Provides true isolation with per-interpreter GIL for parallel execution.
    This is the preferred context for CPU-bound parallel workloads.
    """
    
    # Shared memory for inter-interpreter communication
    _shared_results = {}
    _shared_lock = threading.Lock()
    
    def __init__(self, context_id: str, config: Optional[Dict[str, Any]] = None, manager=None):
        """Initialize sub-interpreter context."""
        super().__init__(context_id, config)
        self._interpreter_id = None
        self._result_future = None
        self._creation_thread_id = None  # Track thread that created the interpreter
        self._manager = manager  # Manager for serialized destroy() calls
    
    def initialize(self) -> bool:
        """Initialize the sub-interpreter."""
        if interpreters is None:
            self.logger.error("Sub-interpreters not available in this Python version")
            return False
            
        try:
            # Track the thread that creates the interpreter
            self._creation_thread_id = threading.get_ident()
            
            # Create new sub-interpreter
            self._interpreter_id = interpreters.create()
            
            # Register in global registry for emergency cleanup
            with _global_subinterpreters_lock:
                _global_subinterpreters.add(self._interpreter_id)
            
            # Initialize the interpreter with required setup code
            setup_code = """
import sys
import pickle
import traceback
import marshal
import types

# Global storage for results
_results = {}

def _execute_marshaled_function(task_id, func_data, args_data, kwargs_data):
    '''Execute a marshaled function and store result.'''
    try:
        # Unmarshal function
        code = marshal.loads(func_data['code'])
        func = types.FunctionType(
            code,
            {'__builtins__': __builtins__},
            func_data['name'],
            func_data['defaults'],
            func_data['closure']
        )
        
        # Deserialize arguments
        args = pickle.loads(args_data) if args_data else ()
        kwargs = pickle.loads(kwargs_data) if kwargs_data else {}
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Store result
        _results[task_id] = ('success', pickle.dumps(result))
        
    except Exception as e:
        # Store error with traceback
        error_info = {
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        _results[task_id] = ('error', pickle.dumps(error_info))

def _get_result(task_id):
    '''Retrieve and remove result for task.'''
    return _results.pop(task_id, None)
"""
            
            interpreters.run_string(self._interpreter_id, setup_code)
            
            self._is_initialized = True
            self.logger.info(f"Initialized sub-interpreter context {self.context_id} with ID {self._interpreter_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize sub-interpreter context: {e}")
            if self._interpreter_id is not None:
                # Remove from global registry
                with _global_subinterpreters_lock:
                    _global_subinterpreters.discard(self._interpreter_id)
                try:
                    interpreters.destroy(self._interpreter_id)
                except:
                    pass
            return False
    
    def _marshal_function(self, func: Callable) -> Dict[str, Any]:
        """Marshal a function for transfer to sub-interpreter."""
        return {
            'code': marshal.dumps(func.__code__),
            'name': func.__name__,
            'defaults': func.__defaults__,
            'closure': None  # Closures not supported across interpreters
        }
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function in sub-interpreter."""
        if not self._is_initialized:
            raise RuntimeError(f"Context {self.context_id} not initialized")
        
        start_time = time.time()
        self._is_active = True
        task_id = f"{self.context_id}_{int(time.time() * 1000000)}"
        
        try:
            # Marshal function and serialize arguments
            func_data = self._marshal_function(func)
            args_data = pickle.dumps(args) if args else b''
            kwargs_data = pickle.dumps(kwargs) if kwargs else b''
            
            # Create execution code with file-based result storage
            exec_code = f"""
# Retrieve marshaled data
import pickle
import tempfile
import os
import json

func_data = {repr(func_data)}
args_data = {repr(args_data)}
kwargs_data = {repr(kwargs_data)}
task_id = {repr(task_id)}

# Execute the function and store result in file
try:
    _execute_marshaled_function(task_id, func_data, args_data, kwargs_data)
    
    # Get result from internal storage
    if task_id in _results:
        status, result_data = _results[task_id]
        
        # Write result to temporary file for retrieval
        result_dict = {{
            'status': status,
            'data': result_data.hex() if isinstance(result_data, bytes) else str(result_data)
        }}
        
        result_file = os.path.join(tempfile.gettempdir(), f"epochly_result_{{task_id}}.json")
        with open(result_file, 'w') as f:
            json.dump(result_dict, f)
except Exception as e:
    # Write error to file
    error_dict = {{
        'status': 'error',
        'error': str(e)
    }}
    result_file = os.path.join(tempfile.gettempdir(), f"epochly_result_{{task_id}}.json")
    with open(result_file, 'w') as f:
        json.dump(error_dict, f)
"""
            
            # Run in sub-interpreter
            interpreters.run_string(self._interpreter_id, exec_code)
            
            # Retrieve result with polling and timeout using file-based communication
            import tempfile
            import json
            
            timeout = self.config.get('execution_timeout', 30.0)
            poll_interval = 0.01  # 10ms polling
            elapsed = 0.0
            
            result_file = os.path.join(tempfile.gettempdir(), f"epochly_result_{task_id}.json")
            
            while elapsed < timeout:
                # Check if result file exists
                if os.path.exists(result_file):
                    try:
                        with open(result_file, 'r') as f:
                            result_dict = json.load(f)
                        
                        # Clean up result file
                        os.unlink(result_file)
                        
                        status = result_dict['status']
                        
                        if status == 'error':
                            error_msg = result_dict.get('error', 'Unknown error')
                            raise RuntimeError(f"Execution error in sub-interpreter: {error_msg}")
                        
                        # Decode result data
                        if 'data' in result_dict:
                            result_data = bytes.fromhex(result_dict['data'])
                        else:
                            result_data = b''
                        
                        break
                    except (json.JSONDecodeError, IOError):
                        # File might be in process of being written, try again
                        pass
                
                time.sleep(poll_interval)
                elapsed += poll_interval
            else:
                # Cleanup file if it exists
                if os.path.exists(result_file):
                    try:
                        os.unlink(result_file)
                    except:
                        pass
                raise TimeoutError(f"Execution timed out after {timeout} seconds")
            
            # Process result
            if status == 'error':
                raise RuntimeError(f"Execution error in sub-interpreter")
            
            result = pickle.loads(result_data)
            
            duration = time.time() - start_time
            self.metrics.record_execution(duration)
            
            return result
            
        except Exception as e:
            self.metrics.record_error()
            self.logger.error(f"Execution error in context {self.context_id}: {e}")
            raise
        finally:
            self._is_active = False
    
    def shutdown(self, *, timeout: float = 2.0) -> None:
        """Shutdown the sub-interpreter with bounded timeout.
        
        Args:
            timeout: Maximum time to wait for interpreter destruction (default: 2.0 seconds)
        """
        if self._interpreter_id is None or self._interpreter_id == -1:
            return
        
        # Prevent double shutdown
        if getattr(self, "_shutting_down", False):
            return
        self._shutting_down = True

        try:
            # Remove from global registry first
            with _global_subinterpreters_lock:
                _global_subinterpreters.discard(self._interpreter_id)
            
            # Check if we're in the same thread that created the interpreter
            current_thread_id = threading.get_ident()
            
            # CRITICAL FIX: Route destroy through manager to avoid orphaned threads
            # mcp-reflect/perplexity guidance: ALL destroy calls must be serialized
            if self._manager:
                try:
                    self._manager.destroy(self._interpreter_id)
                    self.logger.info(f"Successfully destroyed sub-interpreter {self._interpreter_id} via manager")
                    return
                except Exception as e:
                    self.logger.error(f"Manager destroy failed for interpreter {self._interpreter_id}: {e}")
            else:
                # Fallback if no manager: Log warning, interpreter cleaned at process exit
                self.logger.warning(
                    f"No manager available for interpreter {self._interpreter_id}. "
                    "Interpreter will be cleaned up at process exit."
                )
        finally:
            self._interpreter_id = -1
            self._is_initialized = False
    
    def is_alive(self) -> bool:
        """Check if sub-interpreter is alive."""
        if not interpreters or self._interpreter_id is None:
            return False
        
        try:
            # Check if interpreter still exists
            all_interpreters = interpreters.list_all()
            return self._interpreter_id in all_interpreters
        except Exception:
            return False


# ProcessContext removed per architectural decision:
# All CPU-bound work should use SubInterpreterPool with ProcessPoolExecutor
# to avoid the anti-pattern of duplicate process management


class ThreadContext(ExecutionContext):
    """
    Execution context using threading.
    
    Provides lightweight concurrency but no true parallelism due to GIL.
    Suitable for I/O-bound workloads or when isolation is not required.
    """
    
    def __init__(self, context_id: str, config: Optional[Dict[str, Any]] = None):
        """Initialize thread context."""
        super().__init__(context_id, config)
        self._thread: Optional[threading.Thread] = None
        self._task_queue: Optional[queue.Queue] = None
        self._result_dict: Dict[str, Tuple[str, Any]] = {}
        self._result_lock = threading.Lock()
        self._shutdown_event = threading.Event()
        self._thread_ready = threading.Event()
    
    def initialize(self) -> bool:
        """Initialize the thread context."""
        try:
            # Create communication infrastructure
            self._task_queue = queue.Queue()
            
            # Start worker thread
            self._thread = threading.Thread(
                target=self._worker_loop,
                name=f"ThreadContext-{self.context_id}",
                daemon=False
            )
            self._thread.start()
            
            # Wait for thread to be ready
            if not self._thread_ready.wait(timeout=2.0):
                raise RuntimeError("Thread failed to initialize within timeout")
            
            self._is_initialized = True
            self.logger.info(f"Initialized thread context {self.context_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize thread context: {e}")
            self.shutdown()
            return False
    
    def _worker_loop(self) -> None:
        """Worker loop running in the thread."""
        # Signal thread is ready
        self._thread_ready.set()
        
        while not self._shutdown_event.is_set():
            try:
                # Get task from queue with timeout
                task = self._task_queue.get(timeout=0.1)
                
                task_id, func, args, kwargs = task
                
                # Execute function
                try:
                    result = func(*args, **kwargs)
                    with self._result_lock:
                        self._result_dict[task_id] = ('success', result)
                except Exception as e:
                    error_info = {
                        'error': str(e),
                        'type': type(e).__name__,
                        'traceback': traceback.format_exc()
                    }
                    with self._result_lock:
                        self._result_dict[task_id] = ('error', error_info)
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Critical error in worker thread: {e}")
                break
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function in thread."""
        if not self._is_initialized or not self.is_alive():
            raise RuntimeError(f"Context {self.context_id} not available")
        
        start_time = time.time()
        self._is_active = True
        task_id = f"{self.context_id}_{int(time.time() * 1000000)}"
        
        try:
            # Send task to thread
            self._task_queue.put((task_id, func, args, kwargs))
            
            # Wait for result
            timeout = self.config.get('execution_timeout', 30.0)
            deadline = time.time() + timeout
            
            while time.time() < deadline:
                with self._result_lock:
                    if task_id in self._result_dict:
                        status, result = self._result_dict.pop(task_id)
                        
                        if status == 'error':
                            raise RuntimeError(
                                f"Execution error: {result['error']}\n{result['traceback']}"
                            )
                        
                        duration = time.time() - start_time
                        self.metrics.record_execution(duration)
                        return result
                
                time.sleep(0.001)  # 1ms polling
            
            raise TimeoutError(f"Execution timed out after {timeout} seconds")
            
        except Exception as e:
            self.metrics.record_error()
            self.logger.error(f"Execution error in context {self.context_id}: {e}")
            raise
        finally:
            self._is_active = False
    
    def shutdown(self) -> None:
        """Shutdown the thread."""
        if self._thread:
            try:
                # Signal shutdown
                self._shutdown_event.set()
                
                # Clear task queue
                try:
                    while not self._task_queue.empty():
                        self._task_queue.get_nowait()
                except:
                    pass
                
                # Wait for thread to terminate
                self._thread.join(timeout=2.0)
                
                if self._thread.is_alive():
                    self.logger.warning(f"Thread {self.context_id} did not terminate gracefully")
                
                self.logger.info(f"Shutdown thread context {self.context_id}")
                
            except Exception as e:
                self.logger.error(f"Error shutting down thread: {e}")
            finally:
                self._thread = None
                self._task_queue = None
                self._result_dict.clear()
                self._is_initialized = False
    
    def is_alive(self) -> bool:
        """Check if thread is alive."""
        return self._thread is not None and self._thread.is_alive()


class ExecutionContextFactory:
    """
    Factory for creating execution contexts.
    
    Determines the appropriate context type based on availability
    and configuration.
    """
    
    @staticmethod
    def create_context(
        context_type: str,
        context_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> ExecutionContext:
        """
        Create an execution context of the specified type.
        
        Args:
            context_type: Type of context ('subinterpreter', 'process', 'thread')
            context_id: Unique identifier for the context
            config: Optional configuration
            
        Returns:
            ExecutionContext instance
            
        Raises:
            ValueError: If context type is invalid
        """
        context_type = context_type.lower()
        
        if context_type == 'subinterpreter':
            if interpreters is None:
                raise ValueError("Sub-interpreters not available in this Python version")
            return SubInterpreterContext(context_id, config)
        elif context_type == 'process':
            # ProcessContext removed per architectural decision - use SubInterpreterPool for CPU-bound work
            raise ValueError("ProcessContext has been removed. Use SubInterpreterPool for CPU-bound parallel work.")
        elif context_type == 'thread':
            return ThreadContext(context_id, config)
        else:
            raise ValueError(f"Invalid context type: {context_type}")
    
    @staticmethod
    def create_best_context(
        context_id: str,
        config: Optional[Dict[str, Any]] = None,
        prefer_isolation: bool = True
    ) -> ExecutionContext:
        """
        Create the best available execution context.
        
        Args:
            context_id: Unique identifier for the context
            config: Optional configuration
            prefer_isolation: If True, prefer isolated contexts
            
        Returns:
            Best available ExecutionContext instance
        """
        # Try sub-interpreters first if isolation is preferred
        if prefer_isolation and interpreters is not None:
            try:
                context = SubInterpreterContext(context_id, config)
                if context.initialize():
                    return context
                else:
                    context.shutdown()
            except Exception:
                pass
        
        # ProcessContext removed per architectural decision
        # When sub-interpreters are not available and isolation is preferred,
        # CPU-bound work should use SubInterpreterPool with ProcessPoolExecutor
        
        # Use thread as last resort
        context = ThreadContext(context_id, config)
        if not context.initialize():
            raise RuntimeError("Failed to create any execution context")
        return context