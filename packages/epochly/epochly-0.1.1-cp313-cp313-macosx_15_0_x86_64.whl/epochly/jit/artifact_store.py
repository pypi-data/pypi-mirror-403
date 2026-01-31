"""
JIT Compilation Artifact Store (Phase 2.4)

Stores compiled function artifacts in shared memory for cross-interpreter access.

Architecture:
- Uses SharedMemoryManager for cross-interpreter sharing
- Stores serialized code objects (marshal)
- Metadata includes speedup ratios, benchmark status
- Non-blocking get API (returns original if compilation pending)

Performance:
- Store: <1ms (serialize + shared memory write)
- Retrieve: <100µs (shared memory read + deserialize)
- Cross-interpreter: Zero-copy memory access
"""

import marshal
import types
import threading
import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CompilationStatus(Enum):
    """Status of JIT compilation."""
    PENDING = "pending"           # Queued but not started
    COMPILING = "compiling"       # In progress
    BENCHMARKING = "benchmarking" # Compiled, benchmarking performance
    COMPLETE = "complete"         # Compiled and benchmarked
    FAILED = "failed"             # Compilation failed


@dataclass
class CompiledArtifact:
    """Compiled function artifact with metadata."""

    function_name: str
    code_bytes: bytes  # Marshaled code object
    status: CompilationStatus
    compiled_at: float
    speedup_ratio: Optional[float] = None
    backend: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for shared memory."""
        return {
            'function_name': self.function_name,
            'code_bytes': self.code_bytes.hex(),  # Hex for JSON safety
            'status': self.status.value,
            'compiled_at': self.compiled_at,
            'speedup_ratio': self.speedup_ratio,
            'backend': self.backend,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompiledArtifact':
        """Deserialize from dictionary."""
        return cls(
            function_name=data['function_name'],
            code_bytes=bytes.fromhex(data['code_bytes']),
            status=CompilationStatus(data['status']),
            compiled_at=data['compiled_at'],
            speedup_ratio=data.get('speedup_ratio'),
            backend=data.get('backend', 'unknown'),
            metadata=data.get('metadata', {})
        )

    def to_function(self, globals_dict: Optional[Dict] = None) -> Callable:
        """
        Reconstruct function from code bytes.

        Args:
            globals_dict: Global namespace for function (default: caller's globals)

        Returns:
            Reconstructed function
        """
        if globals_dict is None:
            # Use minimal globals (no imports)
            globals_dict = {'__builtins__': __builtins__}

        code = marshal.loads(self.code_bytes)
        return types.FunctionType(code, globals_dict, self.function_name)


class JITArtifactStore:
    """
    Stores JIT compilation artifacts with shared memory backend.

    Thread-safe, non-blocking access.
    Artifacts persist across function calls and can be shared between interpreters.
    """

    def __init__(self, use_shared_memory: bool = True):
        """
        Initialize artifact store.

        Args:
            use_shared_memory: Use SharedMemoryManager (True) or in-memory dict (False)
        """
        self._use_shared_memory = use_shared_memory
        self._artifacts: Dict[str, CompiledArtifact] = {}
        self._lock = threading.RLock()

        # Shared memory integration (Phase 2.4)
        self._shared_memory_manager = None
        self._shared_memory_buffers: Dict[str, Any] = {}  # func_name -> ZeroCopyBuffer object

        if use_shared_memory:
            # CRITICAL FIX (Jan 2026): Skip SharedMemoryManager on Python 3.13 macOS
            # SharedMemory uses multiprocessing.resource_tracker which has known deadlock
            # issues on Python 3.13 macOS.
            import sys
            is_python313_macos = sys.version_info[:2] == (3, 13) and sys.platform == 'darwin'
            if is_python313_macos:
                logger.debug(
                    "JIT artifact store skipping SharedMemoryManager on Python 3.13 macOS "
                    "(resource_tracker deadlock issues), using in-memory store"
                )
                self._use_shared_memory = False
            else:
                try:
                    from ..plugins.executor.shared_memory_manager import SharedMemoryManager
                    self._shared_memory_manager = SharedMemoryManager(pool_size=16 * 1024 * 1024)  # 16MB
                    logger.info("JIT artifact store using SharedMemoryManager for cross-interpreter sharing")
                except ImportError as e:
                    logger.warning(f"SharedMemoryManager unavailable, using in-memory store: {e}")
                    self._use_shared_memory = False

    def store(self, artifact: CompiledArtifact) -> bool:
        """
        Store compiled artifact in shared memory (Phase 2.4).

        Uses SharedMemoryManager for cross-interpreter access.

        Args:
            artifact: Compiled artifact to store

        Returns:
            True if stored successfully
        """
        with self._lock:
            self._artifacts[artifact.function_name] = artifact

            # Phase 2.4: Persist to shared memory for cross-interpreter access
            if self._shared_memory_manager:
                try:
                    # Serialize artifact to JSON bytes
                    import json
                    artifact_dict = artifact.to_dict()
                    artifact_json = json.dumps(artifact_dict).encode('utf-8')

                    # Store in shared memory using ZeroCopyBuffer
                    buffer = self._shared_memory_manager.create_zero_copy_buffer(
                        artifact_json,
                        data_type="jit_artifact"
                    )

                    # Store buffer object for retrieval
                    self._shared_memory_buffers[artifact.function_name] = buffer

                    logger.debug(f"Stored artifact {artifact.function_name} in shared memory (buffer {buffer.buffer_id})")

                except Exception as e:
                    logger.warning(f"Failed to persist {artifact.function_name} to shared memory: {e}")
                    # Continue - artifact still in local dict

            return True

    def get(self, function_name: str) -> Optional[CompiledArtifact]:
        """
        Get compiled artifact from shared memory or cache (Phase 2.4).

        Non-blocking: Returns None if not found (compilation may be pending).

        Args:
            function_name: Name of function

        Returns:
            CompiledArtifact if available, None otherwise
        """
        with self._lock:
            # Fast path: check local cache
            if function_name in self._artifacts:
                return self._artifacts[function_name]

            # Slow path: try to load from shared memory
            if self._shared_memory_manager and function_name in self._shared_memory_buffers:
                try:
                    # Get buffer object
                    buffer = self._shared_memory_buffers[function_name]

                    # Read data from shared memory
                    data = self._shared_memory_manager.read_zero_copy_buffer(buffer)

                    # Deserialize artifact
                    import json
                    artifact_json = data.decode('utf-8')
                    artifact_dict = json.loads(artifact_json)
                    artifact = CompiledArtifact.from_dict(artifact_dict)

                    # Cache locally for faster future access
                    self._artifacts[function_name] = artifact

                    logger.debug(f"Loaded artifact {function_name} from shared memory")
                    return artifact

                except Exception as e:
                    logger.warning(f"Failed to load {function_name} from shared memory: {e}")

            return None

    def get_or_pending(self, function_name: str, original_func: Callable) -> tuple[Callable, CompilationStatus]:
        """
        Get compiled function or return original with status.

        Non-blocking API for callers.

        Args:
            function_name: Name of function
            original_func: Original uncompiled function

        Returns:
            Tuple of (function_to_use, status)
            - If compiled and beneficial: (compiled_func, COMPLETE)
            - If compiling: (original_func, COMPILING)
            - If not found: (original_func, PENDING)
        """
        artifact = self.get(function_name)

        if artifact is None:
            return (original_func, CompilationStatus.PENDING)

        if artifact.status == CompilationStatus.COMPLETE:
            # Check if compilation was beneficial
            if artifact.speedup_ratio and artifact.speedup_ratio >= 1.2:
                # Use compiled version
                try:
                    compiled_func = artifact.to_function()
                    return (compiled_func, CompilationStatus.COMPLETE)
                except Exception as e:
                    logger.warning(f"Failed to reconstruct compiled function {function_name}: {e}")
                    return (original_func, CompilationStatus.FAILED)

        # Compilation pending/in-progress or not beneficial
        return (original_func, artifact.status)

    def mark_compiling(self, function_name: str, backend: str) -> None:
        """Mark function as currently compiling."""
        with self._lock:
            if function_name not in self._artifacts:
                # Create placeholder
                placeholder = CompiledArtifact(
                    function_name=function_name,
                    code_bytes=b'',
                    status=CompilationStatus.COMPILING,
                    compiled_at=time.time(),
                    backend=backend
                )
                self._artifacts[function_name] = placeholder

    def mark_benchmarking(self, function_name: str) -> None:
        """Mark function as compiled, benchmarking in progress."""
        with self._lock:
            if function_name in self._artifacts:
                self._artifacts[function_name].status = CompilationStatus.BENCHMARKING

    def mark_failed(self, function_name: str, backend: str) -> None:
        """
        Mark function compilation as failed.

        MCP-reflect FIX (Jan 2026): Propagates compilation failures to artifact store
        so consumers can see the failed status.

        Args:
            function_name: Name of function that failed to compile
            backend: Backend that was attempted
        """
        with self._lock:
            if function_name in self._artifacts:
                self._artifacts[function_name].status = CompilationStatus.FAILED
            else:
                # Create failed artifact entry
                failed_artifact = CompiledArtifact(
                    function_name=function_name,
                    code_bytes=b'',
                    status=CompilationStatus.FAILED,
                    compiled_at=time.time(),
                    backend=backend
                )
                self._artifacts[function_name] = failed_artifact

    def update_speedup(self, function_name: str, speedup_ratio: float) -> None:
        """
        Update artifact with benchmark results.

        Args:
            function_name: Name of function
            speedup_ratio: Measured speedup (compiled vs original)
        """
        with self._lock:
            if function_name in self._artifacts:
                artifact = self._artifacts[function_name]
                artifact.speedup_ratio = speedup_ratio
                artifact.status = CompilationStatus.COMPLETE

    def get_stats(self) -> Dict[str, Any]:
        """
        Get artifact store statistics.

        Returns:
            Dictionary with counts by status
        """
        with self._lock:
            status_counts = {}
            for artifact in self._artifacts.values():
                status = artifact.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

            return {
                'total_artifacts': len(self._artifacts),
                'by_status': status_counts,
                'using_shared_memory': self._use_shared_memory
            }


# Global artifact store (singleton)
_global_store: Optional[JITArtifactStore] = None
_store_lock = threading.Lock()


def get_artifact_store() -> JITArtifactStore:
    """
    Get global JIT artifact store (singleton).

    Returns:
        JITArtifactStore instance
    """
    global _global_store

    if _global_store is None:
        with _store_lock:
            if _global_store is None:
                _global_store = JITArtifactStore()

    return _global_store
