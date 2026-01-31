"""Orphan container cleanup monitor."""

import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from podkit.monitors.base import BaseThreadMonitor

if TYPE_CHECKING:
    from podkit.backends.base import BackendInterface
    from podkit.core.events import PodkitEventHandler


class OrphanContainerCleaner(BaseThreadMonitor):
    """Background monitor that cleans up orphaned containers.

    This is a safety net for containers that were left behind after crashes
    or other abnormal terminations. It periodically scans for stopped containers
    with a given prefix and removes those older than a threshold.

    Unlike ContainerHealthMonitor which watches tracked containers,
    this cleaner finds ANY container matching the prefix - including
    those that escaped normal tracking.

    Example:
        cleaner = OrphanContainerCleaner(
            backend=backend,
            container_prefix="myapp",
            check_interval=300,  # Check every 5 minutes
            max_age_seconds=3600,  # Remove if stopped for >1 hour
            event_handler=my_event_handler,  # Optional: receive cleanup notifications
        )
        cleaner.start()

        # Later...
        cleaner.stop()
    """

    def __init__(
        self,
        backend: "BackendInterface",
        container_prefix: str,
        check_interval: int = 300,
        max_age_seconds: int = 3600,
        event_handler: "PodkitEventHandler | None" = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize orphan container cleaner.

        Args:
            backend: Docker backend for container operations.
            container_prefix: Prefix to match containers (e.g., "myapp" matches "myapp-*").
            check_interval: Seconds between cleanup checks (default: 300 = 5 minutes).
            max_age_seconds: Remove stopped containers older than this (default: 3600 = 1 hour).
            event_handler: Optional event handler for cleanup notifications.
            logger: Optional logger instance.
        """
        super().__init__(logger or logging.getLogger("podkit.orphans"))
        self.backend = backend
        self.container_prefix = container_prefix
        self.check_interval = check_interval
        self.max_age_seconds = max_age_seconds
        self.event_handler = event_handler

    def start(self) -> None:
        """Start cleanup thread."""
        super().start()
        if self.running:
            self.logger.info(
                f"Started orphan container cleaner "
                f"(prefix: {self.container_prefix}, interval: {self.check_interval}s, "
                f"max_age: {self.max_age_seconds}s)"
            )

    def stop(self, timeout: int = 5) -> None:
        """Stop cleanup thread."""
        was_running = self.running
        super().stop(timeout=timeout)
        if was_running:
            self.logger.info("Stopped orphan container cleaner")

    def _monitor_loop(self) -> None:
        """Main cleanup loop."""
        while self.running:
            try:
                self._cleanup_orphans()
            except Exception as e:
                self.logger.error(f"Orphan cleanup error: {e}", exc_info=True)

            time.sleep(self.check_interval)

    def _cleanup_orphans(self) -> None:
        """Find and remove orphaned containers."""
        try:
            # List all containers with our prefix (including stopped)
            containers = self.backend.list_workloads(
                filters={"name": f"^{self.container_prefix}-"},
            )

            for container_info in containers:
                try:
                    self._check_and_remove_container(container_info)
                except Exception as e:
                    self.logger.warning(f"Failed to check container {container_info.get('name', 'unknown')}: {e}")

        except Exception as e:
            self.logger.error(f"Failed to list containers: {e}")

    def _check_and_remove_container(self, container_info: dict) -> None:
        """Check if container should be removed and remove it.

        Args:
            container_info: Container info dict from list_workloads.
        """
        # Skip running containers
        status = container_info.get("status", "")
        if status == "running":
            return

        # Get container age
        created_at = container_info.get("created", "")
        if not created_at:
            return

        age_seconds = self._calculate_age_seconds(created_at)

        # Skip if not old enough
        if age_seconds < self.max_age_seconds:
            return

        # Remove the orphan
        container_id = container_info["id"]
        container_name = container_info.get("name", "unknown")

        try:
            self.backend.stop_workload(container_id, timeout=1)
        except Exception:
            pass  # May already be stopped

        self.backend.remove_workload(container_id, force=True)

        self.logger.info(f"Removed orphan container {container_name} (age: {age_seconds:.0f}s, status: {status})")

        # Notify event handler
        if self.event_handler:
            try:
                self.event_handler.on_orphan_container_removed(container_id, container_name, age_seconds)
            except Exception as e:
                self.logger.error(f"Event handler error: {e}")

    def _calculate_age_seconds(self, created_at: str) -> float:
        """Calculate container age in seconds.

        Args:
            created_at: ISO format timestamp from Docker.

        Returns:
            Age in seconds.
        """
        # Docker returns timestamps like "2024-01-15T10:30:00.123456789Z"
        # We parse just the main part
        try:
            timestamp_str = created_at.split(".")[0]
            created_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
            created_time = created_time.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            return (now - created_time).total_seconds()
        except Exception:
            return 0
