"""
External supervisor process for catastrophic failure recovery.

Provides watchdog functionality with heartbeat monitoring and automatic
recovery mechanisms following industry-standard patterns.
"""

import os
import signal
import time
import struct
import logging
from multiprocessing import shared_memory
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Optional imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - limited supervisor functionality")


class EpochlySupervisor:
    """
    External watchdog process for catastrophic failure recovery.
    Runs as separate process, monitors main Epochly via shared memory heartbeats.
    
    Industry-standard pattern (Erlang/BEAM, systemd, supervisord).
    """
    
    def __init__(self):
        # Shared memory for heartbeat monitoring (zero-copy)
        # CRITICAL FIX (Jan 2026): Skip SharedMemory on Python 3.13 macOS
        # SharedMemory uses multiprocessing.resource_tracker which has known deadlock
        # issues on Python 3.13 macOS.
        import sys
        is_python313_macos = sys.version_info[:2] == (3, 13) and sys.platform == 'darwin'
        if is_python313_macos:
            self.heartbeat_shm = None
        else:
            try:
                self.heartbeat_shm = shared_memory.SharedMemory(
                    create=True,
                    size=64,  # Small: timestamp + interpreter_count + status
                    name='epochly_heartbeat'
                )
            except FileExistsError:
                # Already exists, connect to it
                self.heartbeat_shm = shared_memory.SharedMemory(
                    name='epochly_heartbeat',
                    create=False
                )
        
        # Process tracking
        self.monitored_pid: Optional[int] = None
        self.interpreter_pids: Dict[int, int] = {}
        
        # Thresholds
        self.heartbeat_timeout = 5.0  # 5 seconds
        self.memory_limit_gb = 16.0   # Configurable
        
        # Telemetry connection
        self.telemetry_endpoint = os.environ.get('EPOCHLY_TELEMETRY_ENDPOINT')
        self.telemetry_client = self._init_telemetry_client()
        
        # Logger
        self.logger = logger
    
    def _init_telemetry_client(self):
        """Initialize telemetry client if available"""
        try:
            from .aws_telemetry_client import AWSSecureTelemetryClient
            return AWSSecureTelemetryClient()
        except ImportError:
            return None
    
    def start_monitoring(self, target_pid: int):
        """Start monitoring Epochly main process"""
        self.monitored_pid = target_pid
        self.logger.info(f"Starting supervisor for PID {target_pid}")
        
        while True:
            try:
                self._monitoring_iteration()
                time.sleep(1.0)  # Check every second
            except KeyboardInterrupt:
                self.logger.info("Supervisor shutdown requested")
                break
            except Exception as e:
                self.logger.error(f"Supervisor error: {e}")
                time.sleep(5.0)  # Back off on error
    
    def _monitoring_iteration(self):
        """Single monitoring iteration"""
        try:
            # Check heartbeat
            last_heartbeat = self._read_heartbeat()
            if time.time() - last_heartbeat > self.heartbeat_timeout:
                self._handle_stall(last_heartbeat)

            # Check resource usage
            if self._check_resource_exhaustion():
                self._handle_resource_exhaustion()

            # Check for zombie interpreters
            self._cleanup_zombies()

            # Report health to telemetry
            self._report_health_metrics()
        except Exception as e:
            # Supervisor must not crash due to monitoring errors
            self.logger.debug(f"Error in monitoring iteration: {e}")
    
    def _read_heartbeat(self) -> float:
        """Read heartbeat timestamp from shared memory"""
        try:
            # Read timestamp (first 8 bytes as double)
            timestamp_bytes = bytes(self.heartbeat_shm.buf[:8])
            timestamp = struct.unpack('d', timestamp_bytes)[0]
            return timestamp
        except Exception as e:
            self.logger.debug(f"Error reading heartbeat: {e}")
            return time.time()  # Return current time to avoid false positives
    
    def _write_heartbeat(self, timestamp: Optional[float] = None):
        """Write heartbeat timestamp (for testing)"""
        if timestamp is None:
            timestamp = time.time()
        struct.pack_into('d', self.heartbeat_shm.buf, 0, timestamp)
    
    def _check_resource_exhaustion(self) -> bool:
        """Check if process is exhausting resources"""
        if not PSUTIL_AVAILABLE or not self.monitored_pid:
            return False
        
        try:
            proc = psutil.Process(self.monitored_pid)
            memory_gb = proc.memory_info().rss / (1024**3)
            
            if memory_gb > self.memory_limit_gb:
                self.logger.warning(f"Process {self.monitored_pid} using {memory_gb:.1f}GB memory")
                return True
            
            return False
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _cleanup_zombies(self):
        """Clean up zombie interpreter processes"""
        if not PSUTIL_AVAILABLE:
            return
        
        for interp_id, pid in list(self.interpreter_pids.items()):
            try:
                proc = psutil.Process(pid)
                if proc.status() == 'zombie':
                    self.logger.warning(f"Cleaning up zombie interpreter {interp_id} (PID {pid})")
                    os.kill(pid, signal.SIGKILL)
                    del self.interpreter_pids[interp_id]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process doesn't exist anymore
                del self.interpreter_pids[interp_id]
            except Exception as e:
                self.logger.debug(f"Error checking process {pid}: {e}")
    
    def _handle_stall(self, last_heartbeat: float):
        """Handle stalled process with escalation

        Args:
            last_heartbeat: Timestamp of last heartbeat (avoids redundant read)
        """
        if not self.monitored_pid:
            return

        self.logger.critical(f"Process {self.monitored_pid} stalled!")

        # Report to telemetry
        self._send_critical_event('process_stall', {
            'pid': self.monitored_pid,
            'last_heartbeat': last_heartbeat
        })

        try:
            # Try graceful shutdown first
            os.kill(self.monitored_pid, signal.SIGTERM)
            time.sleep(2.0)

            # Force kill if needed
            if PSUTIL_AVAILABLE and psutil.pid_exists(self.monitored_pid):
                os.kill(self.monitored_pid, signal.SIGKILL)

        except ProcessLookupError:
            # Process already dead
            pass
        except Exception as e:
            self.logger.error(f"Error handling stall: {e}")

        # Restart with recovery mode
        self._restart_with_recovery()
    
    def _handle_resource_exhaustion(self):
        """Handle resource exhaustion"""
        self.logger.warning(f"Process {self.monitored_pid} exhausting resources")
        
        # Report to telemetry
        self._send_critical_event('resource_exhaustion', {
            'pid': self.monitored_pid,
            'memory_gb': self._get_process_memory()
        })
        
        # Try to reduce resource usage
        if self.monitored_pid:
            try:
                # Send signal to reduce resource usage
                os.kill(self.monitored_pid, signal.SIGUSR1)
            except Exception as e:
                self.logger.debug(f"Error sending signal: {e}")
    
    def _restart_with_recovery(self):
        """Restart process with recovery mode"""
        self.logger.info("Initiating recovery restart")
        
        # Report restart
        self._send_critical_event('recovery_restart', {
            'reason': 'stall_detection'
        })
        
        # Note: Actual process restart is delegated to external process managers
        # (systemd, supervisord, Kubernetes). This function signals the need for
        # recovery and the external manager handles the actual restart.
    
    def _report_health_metrics(self):
        """Report health metrics to telemetry"""
        if not self.monitored_pid:
            return
        
        metrics = {
            'heartbeat_age': time.time() - self._read_heartbeat(),
            'interpreter_count': len(self.interpreter_pids),
            'supervisor_uptime': time.time()  # Would track actual uptime
        }
        
        if PSUTIL_AVAILABLE:
            try:
                proc = psutil.Process(self.monitored_pid)
                metrics['cpu_percent'] = proc.cpu_percent(interval=0.1)
                metrics['memory_gb'] = proc.memory_info().rss / (1024**3)
                metrics['num_threads'] = proc.num_threads()
            except Exception:
                pass
        
        self._send_telemetry(metrics)
    
    def _get_process_memory(self) -> float:
        """Get process memory usage in GB"""
        if not PSUTIL_AVAILABLE or not self.monitored_pid:
            return 0.0
        
        try:
            proc = psutil.Process(self.monitored_pid)
            return proc.memory_info().rss / (1024**3)
        except Exception:
            return 0.0
    
    def _send_telemetry(self, metrics: dict):
        """Send telemetry metrics"""
        if self.telemetry_client:
            try:
                self.telemetry_client.send_telemetry(metrics)
            except Exception as e:
                self.logger.debug(f"Failed to send telemetry: {e}")
    
    def _send_critical_event(self, event_type: str, data: dict):
        """Send critical event to telemetry"""
        if self.telemetry_client:
            try:
                self.telemetry_client.send_critical_event(event_type, data)
            except Exception as e:
                self.logger.debug(f"Failed to send critical event: {e}")
    
    def _detect_crash(self) -> bool:
        """Detect if monitored process has crashed"""
        if not self.monitored_pid:
            return False
        
        if PSUTIL_AVAILABLE:
            return not psutil.pid_exists(self.monitored_pid)
        else:
            # Fallback: try to send signal 0 (no-op)
            try:
                os.kill(self.monitored_pid, 0)
                return False
            except ProcessLookupError:
                return True
    
    def _handle_crash(self):
        """Handle process crash"""
        self.logger.critical(f"Process {self.monitored_pid} crashed!")
        
        self._send_critical_event('process_crash', {
            'pid': self.monitored_pid
        })
        
        self._coordinate_recovery()
    
    def _coordinate_recovery(self):
        """Coordinate recovery after crash"""
        self.logger.info("Coordinating crash recovery")
        
        # Clean up resources
        self._cleanup_zombies()
        
        # Reset shared memory
        if self.heartbeat_shm:
            self._write_heartbeat(0.0)
        
        # Note: Actual recovery would involve restarting the process
        # This is handled by external process manager (systemd, etc.)
    
    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Supervisor shutting down")
        
        if self.monitored_pid:
            try:
                # Send graceful shutdown to monitored process
                os.kill(self.monitored_pid, signal.SIGTERM)
            except Exception:
                pass
        
        # Clean up shared memory
        if hasattr(self, 'heartbeat_shm') and self.heartbeat_shm:
            try:
                self.heartbeat_shm.close()
                self.heartbeat_shm.unlink()
            except Exception:
                pass
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.shutdown()
        except Exception:
            pass


def main():
    """Main entry point for supervisor process"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m epochly.compatibility.supervisor <pid>")
        sys.exit(1)
    
    try:
        pid = int(sys.argv[1])
    except ValueError:
        print("Invalid PID")
        sys.exit(1)
    
    supervisor = EpochlySupervisor()
    
    # Set up signal handlers
    def signal_handler(signum, frame):
        supervisor.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start monitoring
    supervisor.start_monitoring(pid)


if __name__ == '__main__':
    main()