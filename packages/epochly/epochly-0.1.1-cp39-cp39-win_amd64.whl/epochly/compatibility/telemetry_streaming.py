"""
High-performance secure telemetry streaming for compatibility analyzer.

Provides zero-allocation metric recording with TLS 1.3 encryption and
automatic failover.
"""

import ssl
import socket
import threading
import numpy as np
import hashlib
import hmac
import time
import struct
import json
import zlib
import os
import logging
from collections import deque
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SecureTelemetryStreamer:
    """
    High-performance, secure telemetry streaming to centralized location.
    
    Features:
    - Ring buffer for zero-allocation metrics collection
    - TLS 1.3 encrypted streaming
    - Batching and compression for efficiency
    - Automatic failover and buffering
    - HMAC authentication for data integrity
    """
    
    def __init__(self, endpoint: str, api_key: str):
        # Connection settings
        self.endpoint = endpoint
        self.api_key = api_key
        
        # Ring buffers for different metric types (fixed memory)
        self.metrics_buffer = np.zeros((10000, 8), dtype=np.float32)  # 320KB
        self.events_buffer = deque(maxlen=1000)
        self.traces_buffer = deque(maxlen=500)
        
        # Buffer indices (atomic operations)
        self.metrics_index = 0
        
        # TLS configuration
        self.ssl_context = self._create_ssl_context()
        
        # Connection management
        self.connection = None
        self.connection_lock = threading.Lock()

        # Thread shutdown control
        self._shutdown_event = threading.Event()
        self._streaming_thread = None

        # Batching settings
        self.batch_size = 100
        self.batch_interval = 1.0  # seconds
        
        # Local buffer for failed sends
        self.local_buffer_file = os.path.join(
            os.path.expanduser('~/.epochly'),
            'telemetry_buffer.dat'
        )

        # Check if telemetry should be disabled (test mode or explicit disable)
        # mcp-reflect guidance: Don't create thread if disabled
        # CRITICAL: Disable in test mode to prevent CI hangs from network retries
        test_mode = os.environ.get('EPOCHLY_TEST_MODE', '0') == '1'
        offline_mode = os.environ.get('EPOCHLY_OFFLINE_MODE', '0') == '1'
        disable_telemetry = os.environ.get('EPOCHLY_DISABLE_TELEMETRY', '0') == '1'

        self.enabled = not (test_mode or offline_mode or disable_telemetry)

        # Test mode settings: ultra-fast timeouts to prevent hangs
        if test_mode:
            self.connection_timeout = 0.05  # 50ms max
            self.retry_count = 0  # No retries in tests
            self.retry_backoff = 0.01  # 10ms
        else:
            self.connection_timeout = 5.0  # 5s for production
            self.retry_count = 3  # 3 retries
            self.retry_backoff = 1.0  # exponential from 1s

        # Start streaming thread (only if enabled)
        if self.enabled:
            self._start_streaming()
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create secure TLS 1.3 context"""
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        return context
    
    def record_metric(self, metric_type: int, module_hash: int, 
                     confidence: float, latency_ns: int, 
                     strategy: int, success: bool):
        """
        Record metric with zero allocation (lock-free).
        All operations are atomic writes to pre-allocated buffer.
        """
        idx = self.metrics_index % 10000
        
        # Pack metric into buffer (single cache line)
        self.metrics_buffer[idx] = [
            time.time(),           # timestamp
            metric_type,           # 0=check, 1=fallback, 2=recovery
            module_hash % 1000000, # module identifier
            confidence,            # confidence score
            latency_ns / 1000.0,   # microseconds
            strategy,              # execution strategy used
            1.0 if success else 0.0,  # success flag
            0.0                    # reserved
        ]
        
        # Atomic increment
        self.metrics_index += 1
    
    def record_event(self, event_type: str, data: dict):
        """Record high-priority event"""
        event = {
            'timestamp': time.time(),
            'type': event_type,
            'data': data,
            'node_id': self._get_node_id()
        }
        
        # Sign event for integrity
        event['signature'] = self._sign_event(event)
        
        # Non-blocking append
        try:
            self.events_buffer.append(event)
        except:
            pass  # Buffer full, drop oldest
    
    def _get_node_id(self) -> str:
        """Get unique node identifier"""
        import platform
        return f"{platform.node()}_{os.getpid()}"
    
    def _get_node_info(self) -> dict:
        """Get node information for telemetry"""
        import platform
        return {
            'hostname': platform.node(),
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'pid': os.getpid()
        }
    
    def _convert_numpy_types(self, obj):
        """Convert numpy types to native Python types for JSON serialization"""
        if isinstance(obj, dict):
            return {k: self._convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return obj

    def _sign_event(self, event: dict) -> str:
        """Sign event with HMAC for integrity"""
        # Serialize event (without signature field)
        event_copy = {k: v for k, v in event.items() if k != 'signature'}
        # Convert numpy types to native Python types
        event_copy = self._convert_numpy_types(event_copy)
        event_bytes = json.dumps(event_copy, sort_keys=True).encode()

        # Create HMAC signature
        signature = hmac.new(
            self.api_key.encode(),
            event_bytes,
            hashlib.sha256
        ).hexdigest()

        return signature
    
    def _start_streaming(self):
        """Start background streaming thread"""
        def streaming_loop():
            while not self._shutdown_event.is_set():
                try:
                    # Collect batch
                    batch = self._collect_batch()

                    if batch:
                        # Compress
                        compressed = self._compress_batch(batch)

                        # Stream with retry
                        self._stream_with_retry(compressed)

                    # Wait with shutdown check (allows quick termination)
                    self._shutdown_event.wait(timeout=self.batch_interval)

                except Exception as e:
                    # Safe logging that handles closed streams
                    try:
                        logger.error(f"Telemetry streaming error: {e}")
                    except (ValueError, OSError):
                        pass  # Log stream closed, ignore
                    self._shutdown_event.wait(timeout=5.0)  # Back off on error

        self._streaming_thread = threading.Thread(
            target=streaming_loop, daemon=True, name="TelemetryStreamer"
        )
        self._streaming_thread.start()
    
    def _collect_batch(self) -> Optional[dict]:
        """Collect metrics batch for streaming"""
        current_idx = self.metrics_index
        
        if current_idx == 0:
            return None
        
        # Calculate range to send
        start_idx = max(0, current_idx - self.batch_size)
        end_idx = min(current_idx, start_idx + self.batch_size)
        
        # Extract metrics (copy to avoid race)
        metrics_slice = self.metrics_buffer[start_idx:end_idx].copy()
        
        # Collect events
        events = []
        try:
            for _ in range(min(10, len(self.events_buffer))):
                events.append(self.events_buffer.popleft())
        except:
            pass
        
        return {
            'metrics': metrics_slice.tolist(),
            'events': events,
            'node_info': self._get_node_info(),
            'timestamp': time.time()
        }
    
    def _compress_batch(self, batch: dict) -> bytes:
        """Compress batch using zlib for efficiency"""
        # Convert numpy types before serialization
        batch = self._convert_numpy_types(batch)
        # Serialize to JSON
        json_data = json.dumps(batch).encode('utf-8')

        # Compress
        compressed = zlib.compress(json_data, level=6)

        # Add HMAC for integrity
        signature = hmac.new(
            self.api_key.encode(),
            compressed,
            hashlib.sha256
        ).digest()

        # Pack: [signature(32)] [compressed_data]
        return signature + compressed
    
    def _stream_with_retry(self, data: bytes, retries: Optional[int] = None):
        """Stream data with automatic retry and failover"""
        if retries is None:
            retries = self.retry_count
        for attempt in range(retries):
            # Check shutdown before each retry attempt
            if self._shutdown_event.is_set():
                return  # Exit immediately on shutdown

            try:
                with self.connection_lock:
                    if not self.connection:
                        self._connect()

                    # Check if connection was established
                    if not self.connection:
                        raise ConnectionError("Failed to establish connection")

                    # Send data
                    header = struct.pack('!I', len(data))
                    self.connection.send(header + data)
                    
                    # Wait for ACK (with timeout)
                    self.connection.settimeout(self.connection_timeout)
                    ack = self.connection.recv(1)
                    if ack == b'\x06':  # ACK
                        return
                        
            except (ConnectionError, socket.timeout, OSError) as e:
                # Safe logging that handles closed streams
                try:
                    logger.warning(f"Streaming attempt {attempt + 1} failed: {e}")
                except (ValueError, OSError, AttributeError):
                    pass  # Logging unavailable during shutdown
                self.connection = None

                if attempt < retries - 1:
                    # Interruptible backoff - exits immediately on shutdown (mcp-reflect validated)
                    backoff = self.retry_backoff * (2 ** attempt)
                    if self._shutdown_event.wait(timeout=backoff):
                        return  # Shutdown requested during backoff, exit immediately
        
        # All retries failed, buffer locally
        self._buffer_locally(data)
    
    def _connect(self):
        """Establish secure connection to telemetry endpoint"""
        # Check shutdown before attempting connection (save 5s timeout - mcp-reflect validated)
        if self._shutdown_event.is_set():
            return

        try:
            host, port = self.endpoint.split(':')
            
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.connection_timeout)
            
            # Wrap with TLS
            self.connection = self.ssl_context.wrap_socket(
                sock,
                server_hostname=host
            )
            
            # Connect
            self.connection.connect((host, int(port)))
            
            # Authenticate
            auth_packet = {
                'api_key': self.api_key,
                'client_version': '1.0.0',
                'capabilities': ['compression', 'batching', 'hmac']
            }
            auth_json = json.dumps(auth_packet).encode()
            self.connection.send(struct.pack('!I', len(auth_json)) + auth_json)
            
        except Exception as e:
            # Safe logging during shutdown (handles closed file handles)
            try:
                logger.error(f"Failed to connect to telemetry endpoint: {e}")
            except (ValueError, OSError, AttributeError):
                pass  # Logging unavailable during shutdown
            self.connection = None
            # Don't raise - allow graceful degradation in test mode
            if not os.environ.get('EPOCHLY_TEST_MODE'):
                raise
    
    def _buffer_locally(self, data: bytes):
        """Buffer data locally when streaming fails"""
        try:
            os.makedirs(os.path.dirname(self.local_buffer_file), exist_ok=True)
            
            with open(self.local_buffer_file, 'ab') as f:
                # Write length header and data
                f.write(struct.pack('!I', len(data)))
                f.write(data)
            
            try:
                logger.info(f"Buffered {len(data)} bytes locally")
            except (ValueError, OSError, AttributeError):
                pass  # Logging unavailable during shutdown

        except Exception as e:
            try:
                logger.error(f"Failed to buffer data locally: {e}")
            except (ValueError, OSError, AttributeError):
                pass  # Logging unavailable during shutdown
    
    def _retry_buffered_data(self):
        """Retry sending buffered data"""
        if not os.path.exists(self.local_buffer_file):
            return
        
        try:
            with open(self.local_buffer_file, 'rb') as f:
                while True:
                    # Read length header
                    header = f.read(4)
                    if not header:
                        break
                    
                    length = struct.unpack('!I', header)[0]
                    data = f.read(length)
                    
                    # Try to send
                    try:
                        self._stream_with_retry(data, retries=1)
                    except:
                        # Failed again, keep in buffer
                        return
            
            # All data sent, remove buffer file
            os.remove(self.local_buffer_file)
            
        except Exception as e:
            try:
                logger.error(f"Error retrying buffered data: {e}")
            except (ValueError, OSError, AttributeError):
                pass  # Logging unavailable during shutdown
    
    def shutdown(self):
        """Clean shutdown of telemetry streamer"""
        # Signal shutdown
        self._shutdown_event.set()

        # Wait for streaming thread to finish (with timeout)
        if self._streaming_thread and self._streaming_thread.is_alive():
            self._streaming_thread.join(timeout=2.0)

        # Close connection
        if self.connection:
            try:
                self.connection.close()
            except:
                pass

    def _safe_log_error(self, message: str):
        """Log error with protection against closed file handles"""
        try:
            logger.error(message)
        except (ValueError, OSError, AttributeError):
            pass  # Logging unavailable during shutdown

    def _safe_log_warning(self, message: str):
        """Log warning with protection against closed file handles"""
        try:
            logger.warning(message)
        except (ValueError, OSError, AttributeError):
            pass  # Logging unavailable during shutdown

    def _safe_log_info(self, message: str):
        """Log info with protection against closed file handles"""
        try:
            logger.info(message)
        except (ValueError, OSError, AttributeError):
            pass  # Logging unavailable during shutdown