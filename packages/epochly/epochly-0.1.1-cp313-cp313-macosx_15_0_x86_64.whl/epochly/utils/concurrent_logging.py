"""
Epochly Concurrent Logging

Queue-based logging system to eliminate race conditions in multi-threaded scenarios.
All worker threads enqueue records, one listener thread performs actual I/O.

IMPORTANT: This module ONLY configures the isolated 'epochly' logger hierarchy.
It NEVER touches the root logger or user's logging configuration.
"""

import logging
import logging.handlers
import queue
import threading
import atexit
import os
from typing import Optional, List

# Import shared Jupyter detection from logger module
from .logger import _is_jupyter_environment

# Global queue and listener for concurrent logging
# Using bounded queue (10000 records) with drop policy to prevent memory exhaustion
_MAX_QUEUE_SIZE = 10000
_log_queue: Optional[queue.Queue] = None
_log_listener: Optional[logging.handlers.QueueListener] = None
_listener_lock = threading.RLock()
_listener_handlers: List[logging.Handler] = []  # Track handlers for formatter updates


class BoundedQueueHandler(logging.handlers.QueueHandler):
    """
    QueueHandler that drops records when queue is full instead of blocking.

    This prevents memory exhaustion in pathological logging scenarios while
    ensuring the main application thread is never blocked by logging.
    """

    def enqueue(self, record: logging.LogRecord) -> None:
        """
        Enqueue a record, dropping it if the queue is full.

        Args:
            record: Log record to enqueue
        """
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            # Drop the record silently - better than blocking or crashing
            pass


def configure_concurrent_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure queue-based concurrent logging for Epochly loggers only.

    NOTE: This ONLY configures the 'epochly' logger hierarchy.
    It does NOT touch the root logger or user's configuration.

    Uses a bounded queue with drop policy to prevent memory exhaustion
    in pathological logging scenarios.

    Args:
        level: Logging level (default: INFO)

    Returns:
        Configured epochly logger instance
    """
    global _log_queue, _log_listener, _listener_handlers

    # Get the isolated epochly logger (NOT root)
    epochly_logger = logging.getLogger('epochly')

    # Check if already configured
    if getattr(epochly_logger, '_epochly_concurrent', False):
        return epochly_logger

    with _listener_lock:
        # Double-check pattern
        if getattr(epochly_logger, '_epochly_concurrent', False):
            return epochly_logger

        # CRITICAL: Do NOT propagate to root logger
        epochly_logger.propagate = False
        epochly_logger.setLevel(level)

        # Remove existing handlers from epochly logger only
        for handler in epochly_logger.handlers[:]:
            epochly_logger.removeHandler(handler)

        # In Jupyter, use NullHandler to avoid IOPub flooding unless explicitly enabled
        if _is_jupyter_environment() and not os.environ.get('EPOCHLY_JUPYTER_LOGGING', '').lower() in ('1', 'true', 'yes'):
            epochly_logger.addHandler(logging.NullHandler())
            epochly_logger._epochly_concurrent = True
            return epochly_logger

        # Create bounded queue for thread-safe logging (prevents memory exhaustion)
        _log_queue = queue.Queue(maxsize=_MAX_QUEUE_SIZE)

        # Producer side: BoundedQueueHandler that drops records when full
        queue_handler = BoundedQueueHandler(_log_queue)
        epochly_logger.addHandler(queue_handler)

        # Consumer side: StreamHandler with proper formatting
        fmt = "%(asctime)s [%(threadName)s] %(levelname)-8s %(name)s: %(message)s"
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(fmt))

        # Track listener handlers for formatter updates
        _listener_handlers = [stream_handler]

        # Create and start queue listener
        _log_listener = logging.handlers.QueueListener(
            _log_queue,
            stream_handler,
            respect_handler_level=True
        )
        _log_listener.daemon = True
        _log_listener.start()

        # Register cleanup on exit
        atexit.register(stop_concurrent_logging)

        # Mark as configured
        epochly_logger._epochly_concurrent = True

    return epochly_logger


def get_listener_handlers() -> List[logging.Handler]:
    """
    Get the list of handlers attached to the queue listener.

    This allows external code (like logging_bootstrap) to update
    formatters on the actual output handlers, not the QueueHandler.

    Returns:
        List of handlers attached to the listener
    """
    return _listener_handlers.copy()


def stop_concurrent_logging() -> None:
    """Stop the concurrent logging listener."""
    global _log_listener
    
    with _listener_lock:
        if _log_listener:
            _log_listener.stop()
            _log_listener = None


class SafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    Thread-safe rotating file handler that uses explicit locking.
    """
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record with thread-safe file operations.
        
        Args:
            record: Log record to emit
        """
        try:
            with self.lock:  # Use built-in lock from base class
                super().emit(record)
        except Exception:
            self.handleError(record)


def add_file_handler(
    log_file: str,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    level: int = logging.INFO
) -> None:
    """
    Add a thread-safe file handler to the concurrent logging system.

    Args:
        log_file: Path to log file
        max_bytes: Maximum file size before rotation
        backup_count: Number of backup files to keep
        level: Logging level for file handler
    """
    global _log_queue, _log_listener, _listener_handlers

    if not _log_queue or not _log_listener:
        raise RuntimeError("Concurrent logging not configured. Call configure_concurrent_logging() first.")

    with _listener_lock:
        # Stop current listener
        _log_listener.stop()

        # Create new file handler
        file_handler = SafeRotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(level)

        fmt = "%(asctime)s [%(threadName)s] %(levelname)-8s %(name)s: %(message)s"
        file_handler.setFormatter(logging.Formatter(fmt))

        # Add to tracked handlers list
        _listener_handlers.append(file_handler)

        # Create new listener with all handlers
        _log_listener = logging.handlers.QueueListener(
            _log_queue,
            *_listener_handlers,
            respect_handler_level=True
        )
        _log_listener.daemon = True
        _log_listener.start()


def get_concurrent_logger(name: str) -> logging.Logger:
    """
    Get a logger configured for concurrent use under the epochly hierarchy.

    Args:
        name: Logger name

    Returns:
        Logger instance configured for concurrent logging
    """
    # Ensure concurrent logging is configured for epochly
    epochly_logger = logging.getLogger('epochly')
    if not getattr(epochly_logger, '_epochly_concurrent', False):
        configure_concurrent_logging()

    # Return a logger under the epochly hierarchy
    if name.startswith('epochly'):
        return logging.getLogger(name)
    else:
        return logging.getLogger(f'epochly.{name}')


# Stress test function for validation
def _log_spam_worker(worker_id: int, iterations: int = 1000) -> None:
    """
    Worker function for stress testing concurrent logging.
    
    Args:
        worker_id: Unique worker identifier
        iterations: Number of log messages to generate
    """
    logger = get_concurrent_logger(f"spam_worker_{worker_id}")
    
    for i in range(iterations):
        logger.info(f"Worker {worker_id} - Message {i}")
        if i % 100 == 0:
            logger.warning(f"Worker {worker_id} - Checkpoint at {i}")


def stress_test_concurrent_logging(
    num_workers: int = 10,
    iterations_per_worker: int = 1000
) -> bool:
    """
    Stress test the concurrent logging system.
    
    Args:
        num_workers: Number of worker threads
        iterations_per_worker: Messages per worker
        
    Returns:
        True if test completed without errors
    """
    try:
        # Configure concurrent logging
        configure_concurrent_logging()
        
        # Create and start worker threads
        threads = []
        for worker_id in range(num_workers):
            thread = threading.Thread(
                target=_log_spam_worker,
                args=(worker_id, iterations_per_worker)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        return True
        
    except Exception as e:
        print(f"Stress test failed: {e}")
        return False


if __name__ == "__main__":
    # Run stress test
    print("Running concurrent logging stress test...")
    success = stress_test_concurrent_logging()
    print(f"Stress test {'PASSED' if success else 'FAILED'}")