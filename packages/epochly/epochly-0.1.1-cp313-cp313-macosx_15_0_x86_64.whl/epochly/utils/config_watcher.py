"""
Configuration File Watcher for Hot Reload

Monitors configuration files for changes and triggers automatic reloads
without requiring process restart. Ensures atomic updates and graceful
handling of invalid configurations.

Author: Epochly Development Team
Date: November 18, 2025
"""

import os
import threading
import time
from pathlib import Path
from typing import Callable, Optional, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConfigFileEventHandler(FileSystemEventHandler):
    """Handler for config file modification events."""

    def __init__(self, config_path: Path, reload_callback: Callable):
        """
        Initialize event handler.

        Args:
            config_path: Path to config file being watched
            reload_callback: Function to call when config changes
        """
        super().__init__()
        self.config_path = config_path
        self.reload_callback = reload_callback
        self._last_reload = 0
        self._debounce_seconds = 0.5  # Ignore rapid successive changes

    def on_modified(self, event):
        """Handle file modification event."""
        if event.is_directory:
            return

        # Check if this is our config file
        if Path(event.src_path).resolve() == self.config_path.resolve():
            # Debounce rapid changes
            now = time.time()
            if now - self._last_reload < self._debounce_seconds:
                return

            self._last_reload = now

            try:
                logger.info(f"Config file modified: {self.config_path}")
                self.reload_callback()
            except Exception as e:
                logger.error(f"Error during config reload: {e}")


class ConfigFileWatcher:
    """
    Watches configuration file for changes and triggers hot reload.

    Features:
    - Automatic detection of config file changes
    - Debounced reloads (prevents rapid successive reloads)
    - Graceful error handling (invalid config doesn't crash)
    - Atomic updates (all-or-nothing application)
    - Background monitoring thread

    Usage:
        watcher = ConfigFileWatcher(config_path, reload_callback)
        watcher.start()
        # ... config changes are automatically detected ...
        watcher.stop()
    """

    def __init__(
        self,
        config_path: Path,
        reload_callback: Callable[[], None]
    ):
        """
        Initialize config file watcher.

        Args:
            config_path: Path to config file to watch
            reload_callback: Function to call when config changes
        """
        self.config_path = Path(config_path).resolve()
        self.reload_callback = reload_callback
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[ConfigFileEventHandler] = None
        self._running = False

        logger.debug(f"ConfigFileWatcher initialized for {self.config_path}")

    def start(self) -> bool:
        """
        Start watching config file for changes.

        Returns:
            bool: True if watching started successfully
        """
        if self._running:
            logger.warning("Config watcher already running")
            return True

        if not self.config_path.exists():
            logger.warning(f"Config file does not exist: {self.config_path}")
            return False

        try:
            # Create event handler
            self.event_handler = ConfigFileEventHandler(
                self.config_path,
                self.reload_callback
            )

            # Create observer
            self.observer = Observer()

            # Watch the directory containing the config file
            watch_dir = self.config_path.parent
            self.observer.schedule(
                self.event_handler,
                str(watch_dir),
                recursive=False
            )

            # Start observer thread
            self.observer.start()
            self._running = True

            logger.info(f"Config file watcher started for {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to start config watcher: {e}")
            self._running = False
            return False

    def stop(self):
        """Stop watching config file."""
        if not self._running:
            return

        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=2)

            self._running = False
            logger.info("Config file watcher stopped")

        except Exception as e:
            logger.error(f"Error stopping config watcher: {e}")

    def is_running(self) -> bool:
        """Check if watcher is currently running."""
        return self._running

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def create_config_watcher(
    config_path: Path,
    reload_callback: Callable[[], None]
) -> ConfigFileWatcher:
    """
    Create and start a config file watcher.

    Args:
        config_path: Path to config file
        reload_callback: Function to call on changes

    Returns:
        ConfigFileWatcher instance (started)
    """
    watcher = ConfigFileWatcher(config_path, reload_callback)
    watcher.start()
    return watcher
