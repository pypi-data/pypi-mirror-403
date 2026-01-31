"""
Resource manager for per-interpreter isolation with self-adjusting limits.

Provides lightweight resource management that adapts to system capacity
and usage patterns.
"""

import os
import time
import threading
import logging
from collections import deque, defaultdict
from typing import Dict, Optional, Any
import numpy as np

# resource module is Unix-only, not available on Windows
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    
try:
    import interpreters
except ImportError:
    try:
        import _xxsubinterpreters as interpreters
    except ImportError:
        interpreters = None

logger = logging.getLogger(__name__)


class InterpreterResourceManager:
    """
    Lightweight resource management per interpreter with SELF-ADJUSTING limits.
    Integrates with existing SharedMemoryAllocator.
    """
    
    def __init__(self, shared_memory_allocator=None):
        self.allocator = shared_memory_allocator
        
        # Base limits (will self-adjust based on system resources)
        self.base_limits = {
            'memory_mb': 512,
            'cpu_seconds': 30,
            'file_descriptors': 100,
            'threads': 10,
            'shared_memory_mb': 64
        }
        
        # Current adaptive limits (start at base)
        self.limits = self.base_limits.copy()
        
        # Track resource usage
        self.usage_history = deque(maxlen=1000)
        self.interpreter_pids = {}
        
        # Self-adjustment parameters
        self.adjustment_interval = 60.0
        self.last_adjustment = time.time()
        
        # System resource detection
        self.system_resources = {}
        self._detect_system_resources()
        
        # Telemetry hook
        self.telemetry = None
        
        # Start adjustment thread
        self._start_adjustment_thread()
    
    def _detect_system_resources(self):
        """Detect available system resources for intelligent scaling"""
        if PSUTIL_AVAILABLE:
            # Get system specs (use module-level psutil, not local import)
            self.system_resources = {
                'total_memory_gb': psutil.virtual_memory().total / (1024**3),
                'cpu_count': psutil.cpu_count(),
                'available_memory_gb': psutil.virtual_memory().available / (1024**3)
            }
            
            # Adjust base limits based on system capacity
            if self.system_resources['total_memory_gb'] > 32:
                # High-memory system: increase limits
                self.limits['memory_mb'] = min(1024, self.base_limits['memory_mb'] * 2)
                self.limits['shared_memory_mb'] = min(256, self.base_limits['shared_memory_mb'] * 2)
            elif self.system_resources['total_memory_gb'] < 8:
                # Low-memory system: decrease limits
                self.limits['memory_mb'] = max(256, self.base_limits['memory_mb'] // 2)
                self.limits['shared_memory_mb'] = max(32, self.base_limits['shared_memory_mb'] // 2)
        else:
            # Default if psutil not available
            self.system_resources = {
                'total_memory_gb': 16,
                'cpu_count': 4,
                'available_memory_gb': 8
            }
    
    def _start_adjustment_thread(self):
        """Start background thread for self-adjusting limits"""
        def adjustment_loop():
            while True:
                time.sleep(self.adjustment_interval)
                try:
                    self._adjust_limits()
                except Exception as e:
                    logger.debug(f"Error adjusting limits: {e}")
        
        thread = threading.Thread(target=adjustment_loop, daemon=True, name="ResourceAdjustment")
        thread.start()
    
    def _adjustment_thread(self):
        """Background thread for self-adjusting limits"""
        while True:
            time.sleep(self.adjustment_interval)
            self._adjust_limits()
    
    def _adjust_limits(self):
        """Self-adjust limits based on usage patterns and system state"""
        
        # Need enough history
        if len(self.usage_history) < 10:
            return
        
        # Calculate statistics
        recent_usage = list(self.usage_history)[-100:] if len(self.usage_history) > 100 else list(self.usage_history)
        
        # Extract metrics
        memory_values = [u.get('memory_mb', 0) for u in recent_usage if 'memory_mb' in u]
        if not memory_values:
            return
            
        avg_memory = np.mean(memory_values)
        max_memory = np.max(memory_values)
        failure_rate = sum(1 for u in recent_usage if u.get('failed', False)) / len(recent_usage)
        
        # Get current system state
        if PSUTIL_AVAILABLE:
            # Use module-level psutil, not local import
            current_available = psutil.virtual_memory().available / (1024**2)  # MB
            current_cpu_percent = psutil.cpu_percent(interval=0.1)
        else:
            # Conservative defaults
            current_available = self.limits['memory_mb'] * 4
            current_cpu_percent = 50.0
        
        # ADJUSTMENT LOGIC
        
        # 1. Memory adjustment based on usage patterns
        if max_memory > self.limits['memory_mb'] * 0.9 and failure_rate < 0.05:
            # Hitting limits but low failure rate - increase if resources available
            if current_available > self.limits['memory_mb'] * 4:
                self.limits['memory_mb'] = int(min(
                    self.limits['memory_mb'] * 1.25,
                    self.base_limits['memory_mb'] * 3,
                    current_available // 4
                ))
                logger.info(f"Increased memory limit to {self.limits['memory_mb']}MB")
        
        elif avg_memory < self.limits['memory_mb'] * 0.3 and len(recent_usage) > 50:
            # Consistently low usage - decrease to free resources
            self.limits['memory_mb'] = int(max(
                self.limits['memory_mb'] * 0.75,
                self.base_limits['memory_mb'] * 0.5,
                256  # Minimum
            ))
            logger.info(f"Decreased memory limit to {self.limits['memory_mb']}MB")
        
        # 2. CPU adjustment based on system load
        if current_cpu_percent < 50:
            # System has spare CPU - can increase limits
            self.limits['cpu_seconds'] = int(min(
                self.limits['cpu_seconds'] * 1.2,
                60  # Max 1 minute
            ))
        elif current_cpu_percent > 80:
            # System under load - decrease limits
            self.limits['cpu_seconds'] = int(max(
                self.limits['cpu_seconds'] * 0.8,
                10  # Min 10 seconds
            ))
        
        # 3. Thread adjustment based on contention
        thread_contention = self._measure_thread_contention()
        if thread_contention < 0.1:  # Low contention
            self.limits['threads'] = min(
                self.limits['threads'] + 2,
                20  # Max threads
            )
        elif thread_contention > 0.3:  # High contention
            self.limits['threads'] = max(
                self.limits['threads'] - 1,
                4  # Min threads
            )
        
        # 4. Shared memory adjustment
        if self.allocator and hasattr(self.allocator, 'get_fragmentation'):
            if self.allocator.get_fragmentation() > 0.3:
                # High fragmentation - reduce per-interpreter allocation
                self.limits['shared_memory_mb'] = int(max(
                    self.limits['shared_memory_mb'] * 0.8,
                    16  # Minimum
                ))
        
        # Report adjustments to telemetry
        if self.telemetry:
            self.telemetry.record_event('resource_adjustment', {
                'old_limits': self.base_limits,
                'new_limits': self.limits,
                'reason': 'self_adjustment',
                'metrics': {
                    'avg_memory': avg_memory,
                    'failure_rate': failure_rate,
                    'system_cpu': current_cpu_percent
                }
            })
    
    def _measure_thread_contention(self) -> float:
        """Measure thread contention (0.0 = no contention, 1.0 = high contention)"""
        if PSUTIL_AVAILABLE:
            try:
                # Use module-level psutil, not local import
                proc = psutil.Process()
                ctx_switches = proc.num_ctx_switches()

                # Normalize to 0-1 range
                voluntary = ctx_switches.voluntary / (ctx_switches.voluntary + 1)
                return min(1.0, voluntary / 1000.0)
            except Exception:
                return 0.1
        return 0.1  # Default low contention
    
    def _create_limited_subinterpreter(self, interpreter_id: int):
        """Create sub-interpreter with soft limits"""
        
        # Allocate dedicated shared memory segment if allocator available
        memory_segment = None
        if self.allocator:
            memory_segment = self.allocator.allocate_segment(
                size=self.limits['shared_memory_mb'] * 1024 * 1024,
                interpreter_id=interpreter_id
            )
        
        # Create sub-interpreter with limits
        config = {
            'memory_segment': memory_segment,
            'max_threads': self.limits['threads'],
            'cpu_quota': self.limits['cpu_seconds']
        }
        
        # Use interpreters API if available
        if interpreters and hasattr(interpreters, 'create'):
            interp = interpreters.create(isolated=True)
            # Note: Config setting would be done through interpreter execution
            return interp
        
        return None
    
    def _create_isolated_process(self, interpreter_id: int):
        """Create fully isolated process with hard limits"""
        
        pid = os.fork()
        if pid == 0:
            # Child: Apply hard limits (Unix only)
            if HAS_RESOURCE:
                try:
                    # Memory limit (address space)
                    resource.setrlimit(
                        resource.RLIMIT_AS,
                        (self.limits['memory_mb'] * 1024 * 1024,
                         self.limits['memory_mb'] * 1024 * 1024)
                    )

                    # CPU time limit
                    resource.setrlimit(
                        resource.RLIMIT_CPU,
                        (self.limits['cpu_seconds'],
                         self.limits['cpu_seconds'] + 5)
                    )

                    # File descriptor limit
                    resource.setrlimit(
                        resource.RLIMIT_NOFILE,
                        (self.limits['file_descriptors'],
                         self.limits['file_descriptors'])
                    )

                    # Thread/process limit
                    try:
                        resource.setrlimit(
                            resource.RLIMIT_NPROC,
                            (self.limits['threads'],
                             self.limits['threads'])
                        )
                    except AttributeError:
                        # RLIMIT_NPROC not available on all systems
                        pass

                    # If in container, use cgroups for additional isolation
                    if self._in_container():
                        self._apply_cgroup_limits(interpreter_id)

                except Exception as e:
                    logger.warning(f"Failed to set resource limits: {e}")
            
            # Return to let caller execute in child
            return 0
            
        else:
            # Parent: Track the child
            self.interpreter_pids[interpreter_id] = pid
            return pid
    
    def _in_container(self) -> bool:
        """Check if running in a container"""
        return os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv')
    
    def _apply_cgroup_limits(self, interpreter_id: int):
        """Apply cgroup limits in containerized environments"""
        
        cgroup_path = f"/sys/fs/cgroup/epochly/interpreter_{interpreter_id}"
        
        try:
            # Create cgroup
            os.makedirs(cgroup_path, exist_ok=True)
            
            # Set memory limit
            with open(f"{cgroup_path}/memory.max", 'w') as f:
                f.write(str(self.limits['memory_mb'] * 1024 * 1024))
            
            # Set CPU quota (microseconds per period)
            with open(f"{cgroup_path}/cpu.max", 'w') as f:
                f.write(f"{self.limits['cpu_seconds'] * 1000000} 1000000")
            
            # Add current process to cgroup
            with open(f"{cgroup_path}/cgroup.procs", 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            logger.debug(f"Failed to apply cgroup limits: {e}")
    
    def monitor_usage(self, interpreter_id: int) -> dict:
        """Monitor resource usage for an interpreter"""

        if interpreter_id in self.interpreter_pids:
            pid = self.interpreter_pids[interpreter_id]

            if PSUTIL_AVAILABLE:
                try:
                    # Use module-level psutil, not local import
                    proc = psutil.Process(pid)

                    return {
                        'memory_mb': proc.memory_info().rss / (1024 * 1024),
                        'cpu_percent': proc.cpu_percent(interval=0.1),
                        'num_threads': proc.num_threads(),
                        'num_fds': len(proc.open_files()),
                        'status': proc.status()
                    }
                except psutil.NoSuchProcess:
                    return {'status': 'terminated'}
                except Exception as e:
                    logger.debug(f"Error monitoring process {pid}: {e}")
                    return {'status': 'error'}

        return {'status': 'unknown'}
    
    def enforce_quotas(self):
        """Periodic enforcement of quotas"""
        
        for interp_id in list(self.interpreter_pids.keys()):
            usage = self.monitor_usage(interp_id)
            
            # Record usage
            self.usage_history.append(usage)
            
            if usage['status'] == 'terminated':
                del self.interpreter_pids[interp_id]
                continue
            
            # Check for violations
            if usage.get('memory_mb', 0) > self.limits['memory_mb']:
                self._handle_quota_violation(interp_id, 'memory')
            
            if usage.get('num_threads', 0) > self.limits['threads']:
                self._handle_quota_violation(interp_id, 'threads')
    
    def _handle_quota_violation(self, interpreter_id: int, resource_type: str):
        """Handle resource quota violations"""
        
        logger.warning(f"Interpreter {interpreter_id} exceeded {resource_type} quota")
        
        # Report to telemetry
        if self.telemetry:
            self.telemetry.record_event('quota_violation', {
                'interpreter_id': interpreter_id,
                'resource_type': resource_type,
                'usage': self.monitor_usage(interpreter_id)
            })
        
        # Terminate if critical
        if resource_type in ['memory', 'cpu']:
            self.terminate_interpreter(interpreter_id)
    
    def terminate_interpreter(self, interpreter_id: int):
        """Terminate an interpreter process"""
        if interpreter_id in self.interpreter_pids:
            pid = self.interpreter_pids[interpreter_id]
            try:
                os.kill(pid, 15)  # SIGTERM
                time.sleep(0.5)
                if PSUTIL_AVAILABLE and psutil.pid_exists(pid):
                    os.kill(pid, 9)  # SIGKILL
            except Exception as e:
                logger.debug(f"Error terminating interpreter {interpreter_id}: {e}")
            finally:
                del self.interpreter_pids[interpreter_id]