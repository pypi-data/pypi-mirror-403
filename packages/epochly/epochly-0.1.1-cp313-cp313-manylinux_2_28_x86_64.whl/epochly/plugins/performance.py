"""
Epochly Plugin Communication Performance Enhancements

Message batching, connection pooling, and compression utilities for optimizing
plugin communication performance.
"""

import asyncio
import base64
import gzip
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..utils.event_bus import EventBus, get_event_bus
from ..utils.logger import get_logger
from .communication import PluginMessage, PluginMessageEvent

logger = get_logger(__name__)


@dataclass
class MessageBatcher:
    """
    Batches plugin messages to reduce event bus load for high-throughput scenarios.
    
    Automatically flushes batches when size threshold is reached or after time interval.
    """
    
    batch_size: int = 100
    flush_interval: float = 0.1  # seconds
    
    def __post_init__(self):
        self.pending_messages: List[PluginMessage] = []
        self._flush_task: Optional[asyncio.Task] = None
        self._event_bus = get_event_bus()
        self.logger = get_logger(f"{__name__}.batcher")
        self._shutdown = False
        
        # Start periodic flush task
        self._start_flush_timer()
    
    async def add_message(self, message: PluginMessage) -> None:
        """
        Add a message to the batch queue.
        
        Args:
            message: Message to batch
        """
        if self._shutdown:
            self.logger.warning("Batcher is shutdown, cannot add message")
            return
            
        self.pending_messages.append(message)
        self.logger.debug(f"Added message to batch, queue size: {len(self.pending_messages)}")
        
        # Flush if batch size reached
        if len(self.pending_messages) >= self.batch_size:
            await self._flush_batch()
    
    async def _flush_batch(self) -> None:
        """Flush pending messages to event bus."""
        if not self.pending_messages:
            return
            
        messages_to_send = self.pending_messages.copy()
        self.pending_messages.clear()
        
        try:
            # Send all messages in batch
            tasks = []
            for message in messages_to_send:
                event = PluginMessageEvent(payload=message)
                tasks.append(self._event_bus.publish(event))
            
            # Execute batch publish
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            success_count = sum(1 for r in results if r is True)
            error_count = len(results) - success_count
            
            self.logger.debug(f"Batch flush: {success_count} success, {error_count} errors")
            
            if error_count > 0:
                self.logger.warning(f"Failed to send {error_count} messages in batch")
                
        except Exception as e:
            self.logger.error(f"Error flushing message batch: {e}")
    
    def _start_flush_timer(self):
        """Start the periodic flush timer."""
        if not self._flush_task or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._periodic_flush())
    
    async def _periodic_flush(self):
        """Periodically flush pending messages."""
        try:
            while not self._shutdown:
                await asyncio.sleep(self.flush_interval)
                if self.pending_messages:
                    await self._flush_batch()
        except asyncio.CancelledError:
            # Final flush on cancellation
            if self.pending_messages:
                await self._flush_batch()
            raise
        except Exception as e:
            self.logger.error(f"Error in periodic flush: {e}")
    
    async def flush_now(self) -> None:
        """Force immediate flush of pending messages."""
        await self._flush_batch()
    
    async def shutdown(self) -> None:
        """Shutdown the batcher and flush remaining messages."""
        self._shutdown = True
        
        # Cancel flush task safely
        if self._flush_task and not self._flush_task.done():
            try:
                # Check if we can safely cancel the task
                current_loop = asyncio.get_running_loop()
                if (hasattr(self._flush_task, '_loop') and
                    self._flush_task._loop is current_loop and
                    not current_loop.is_closed()):
                    self._flush_task.cancel()
                    try:
                        await self._flush_task
                    except asyncio.CancelledError:
                        pass
                else:
                    # Just mark as cancelled without awaiting
                    self._flush_task.cancel()
            except (RuntimeError, AttributeError):
                # Event loop issues or task already cancelled - ignore
                pass
        
        # Flush any remaining messages
        if self.pending_messages:
            await self._flush_messages()
        
        self.logger.info("Message batcher shutdown complete")
    
    async def _flush_messages(self) -> None:
        """Helper method to flush messages without the full batch logic."""
        if not self.pending_messages:
            return
            
        messages_to_send = self.pending_messages.copy()
        self.pending_messages.clear()
        
        try:
            # Send all messages
            tasks = []
            for message in messages_to_send:
                event = PluginMessageEvent(payload=message)
                tasks.append(self._event_bus.publish(event))
            
            # Execute batch publish
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            success_count = sum(1 for r in results if r is True)
            error_count = len(results) - success_count
            
            self.logger.debug(f"Final flush: {success_count} success, {error_count} errors")
            
        except Exception as e:
            self.logger.error(f"Error in final flush: {e}")


@dataclass
class EventBusConnectionPool:
    """
    Connection pool for event bus instances to optimize connection management.
    
    Maintains a pool of reusable event bus connections for high-throughput scenarios.
    """
    
    pool_size: int = 10
    
    def __post_init__(self):
        self.connections: asyncio.Queue = asyncio.Queue(maxsize=self.pool_size)
        self._initialized = False
        self.logger = get_logger(f"{__name__}.pool")
    
    async def _initialize_pool(self) -> None:
        """Initialize the connection pool."""
        if self._initialized:
            return
            
        try:
            for _ in range(self.pool_size):
                # Use singleton event bus pattern
                # In future, this could create separate instances
                connection = get_event_bus()
                await self.connections.put(connection)
            
            self._initialized = True
            self.logger.info(f"Initialized connection pool with {self.pool_size} connections")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    async def get_connection(self) -> EventBus:
        """
        Get a connection from the pool.
        
        Returns:
            EventBus instance from pool
        """
        if not self._initialized:
            await self._initialize_pool()
        
        try:
            connection = await asyncio.wait_for(self.connections.get(), timeout=5.0)
            self.logger.debug("Retrieved connection from pool")
            return connection
        except asyncio.TimeoutError:
            self.logger.warning("Timeout getting connection from pool, creating new one")
            return get_event_bus()
    
    async def return_connection(self, connection: EventBus) -> None:
        """
        Return a connection to the pool.
        
        Args:
            connection: EventBus instance to return
        """
        try:
            await asyncio.wait_for(self.connections.put(connection), timeout=1.0)
            self.logger.debug("Returned connection to pool")
        except asyncio.TimeoutError:
            self.logger.warning("Timeout returning connection to pool")
        except Exception as e:
            self.logger.error(f"Error returning connection to pool: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown the connection pool."""
        # Drain the pool
        connections = []
        while not self.connections.empty():
            try:
                conn = self.connections.get_nowait()
                connections.append(conn)
            except asyncio.QueueEmpty:
                break
        
        self.logger.info(f"Connection pool shutdown, drained {len(connections)} connections")


class MessageCompressor:
    """
    Compresses large message payloads to optimize network usage.
    
    Automatically compresses payloads above threshold size using gzip compression.
    """
    
    @staticmethod
    def compress_payload(payload: Dict[str, Any], threshold: int = 1024) -> Dict[str, Any]:
        """
        Compress payload if it exceeds size threshold.
        
        Args:
            payload: Original payload data
            threshold: Size threshold in bytes for compression
            
        Returns:
            Compressed payload or original if below threshold
        """
        try:
            serialized = json.dumps(payload, default=str)
            
            if len(serialized) > threshold:
                # Compress the data
                compressed = gzip.compress(serialized.encode('utf-8'))
                encoded = base64.b64encode(compressed).decode('ascii')
                
                logger.debug(f"Compressed payload: {len(serialized)} -> {len(encoded)} bytes")
                
                return {
                    "compressed": True,
                    "data": encoded,
                    "original_size": len(serialized),
                    "compressed_size": len(encoded)
                }
            else:
                return {"compressed": False, "data": payload}
                
        except Exception as e:
            logger.error(f"Error compressing payload: {e}")
            return {"compressed": False, "data": payload}
    
    @staticmethod
    def decompress_payload(compressed_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decompress a compressed payload.
        
        Args:
            compressed_payload: Compressed payload data
            
        Returns:
            Original payload data
        """
        try:
            if not compressed_payload.get("compressed", False):
                return compressed_payload.get("data", {})
            
            # Decompress the data
            encoded_data = compressed_payload["data"]
            compressed_bytes = base64.b64decode(encoded_data.encode('ascii'))
            decompressed = gzip.decompress(compressed_bytes)
            original_data = json.loads(decompressed.decode('utf-8'))
            
            logger.debug(f"Decompressed payload: {len(encoded_data)} -> {compressed_payload.get('original_size', 0)} bytes")
            
            return original_data
            
        except Exception as e:
            logger.error(f"Error decompressing payload: {e}")
            return compressed_payload.get("data", {})


@dataclass
class PerformanceConfig:
    """Configuration for performance optimizations."""
    
    # Message batching
    enable_batching: bool = True
    batch_size: int = 100
    batch_flush_interval: float = 0.1
    
    # Connection pooling
    enable_connection_pooling: bool = True
    connection_pool_size: int = 10
    
    # Message compression
    enable_compression: bool = True
    compression_threshold: int = 1024
    
    # Timeouts
    default_timeout: float = 30.0
    connection_timeout: float = 5.0


# Global performance utilities
_global_batcher: Optional[MessageBatcher] = None
_global_connection_pool: Optional[EventBusConnectionPool] = None


async def get_message_batcher(config: Optional[PerformanceConfig] = None) -> MessageBatcher:
    """Get or create global message batcher."""
    global _global_batcher
    
    if config is None:
        config = PerformanceConfig()
    
    # If batcher exists but config differs, recreate it
    if _global_batcher is not None:
        if (_global_batcher.batch_size != config.batch_size or
            _global_batcher.flush_interval != config.batch_flush_interval):
            await _global_batcher.shutdown()
            _global_batcher = None
    
    if _global_batcher is None:
        _global_batcher = MessageBatcher(
            batch_size=config.batch_size,
            flush_interval=config.batch_flush_interval
        )
    
    return _global_batcher


async def get_connection_pool(config: Optional[PerformanceConfig] = None) -> EventBusConnectionPool:
    """Get or create global connection pool."""
    global _global_connection_pool
    
    if config is None:
        config = PerformanceConfig()
    
    # If pool exists but config differs, recreate it
    if _global_connection_pool is not None:
        if _global_connection_pool.pool_size != config.connection_pool_size:
            await _global_connection_pool.shutdown()
            _global_connection_pool = None
    
    if _global_connection_pool is None:
        _global_connection_pool = EventBusConnectionPool(
            pool_size=config.connection_pool_size
        )
    
    return _global_connection_pool


async def shutdown_performance_utilities():
    """Shutdown global performance utilities."""
    global _global_batcher, _global_connection_pool
    
    if _global_batcher:
        await _global_batcher.shutdown()
        _global_batcher = None
    
    if _global_connection_pool:
        await _global_connection_pool.shutdown()
        _global_connection_pool = None