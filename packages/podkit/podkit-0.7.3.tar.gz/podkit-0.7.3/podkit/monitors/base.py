"""Base monitor class for background thread management."""

import logging
import threading
from abc import ABC, abstractmethod


class BaseThreadMonitor(ABC):
    """Base class for background thread monitors.

    Provides common thread lifecycle management (start/stop) for monitor classes.
    Subclasses must implement the _monitor_loop method.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize base monitor.

        Args:
            logger: Optional logger instance. If not provided, uses class name.
        """
        self.running = False
        self.thread: threading.Thread | None = None
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def start(self) -> None:
        """Start monitoring thread.

        Creates a daemon thread that runs the monitoring loop.
        Safe to call multiple times (no-op if already running).
        """
        if self.running:
            self.logger.warning("Monitor already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self, timeout: int = 5) -> None:
        """Stop monitoring thread.

        Args:
            timeout: Maximum seconds to wait for thread to stop (default: 5).
        """
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=timeout)
            self.thread = None

    @abstractmethod
    def _monitor_loop(self) -> None:
        """Main monitoring loop - must be implemented by subclasses.

        This method runs in a separate daemon thread. It should check
        self.running periodically and exit when it becomes False.
        """
