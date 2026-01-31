"""Container health monitoring with background thread."""

import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from podkit.constants import DEFAULT_HEALTH_CHECK_INTERVAL, DEFAULT_HEALTH_CHECK_LOG_LINES
from podkit.core.manager import BaseContainerManager
from podkit.core.models import ContainerStatus
from podkit.monitors.base import BaseThreadMonitor

if TYPE_CHECKING:
    from podkit.core.events import PodkitEventHandler


class ContainerHealthMonitor(BaseThreadMonitor):
    """Background monitor that provides container health information.

    This monitor does NOT decide what is "healthy" or "failed" - it simply
    checks all containers and provides their current state to registered handlers.
    Handlers decide what action to take based on the provided information.

    Example:
        monitor = ContainerHealthMonitor(
            container_manager=container_manager,
            check_interval=30,
            log_lines=50  # Capture last 50 lines on issues (0 or None to disable)
        )

        # Register handler (decides what to do with health info)
        def handle_health_info(container_states: dict[str, dict]):
            for container_id, state in container_states.items():
                # Handler decides if this is a failure
                if state["status"] not in ("running", "creating"):
                    print(f"Container {state['container_name']} has issues!")
                    # Take action: mark sessions, send alerts, etc.

            # Handler can also do periodic tasks
            cleanup_expired_sessions()

        monitor.register_handler(handle_health_info)
        monitor.start()
    """

    def __init__(
        self,
        container_manager: BaseContainerManager,
        check_interval: int = DEFAULT_HEALTH_CHECK_INTERVAL,
        log_lines: int | None = DEFAULT_HEALTH_CHECK_LOG_LINES,
        event_handler: "PodkitEventHandler | None" = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize container health monitor.

        Args:
            container_manager: Container manager to monitor.
            check_interval: Seconds between health checks (default: 30).
            log_lines: Number of log lines to capture for non-running containers.
                      If 0 or None, logs are not captured (default: 50).
            event_handler: Optional event handler for health check events.
            logger: Optional logger instance.
        """
        super().__init__(logger or logging.getLogger("podkit.health"))
        self.container_manager = container_manager
        self.check_interval = check_interval
        self.log_lines = log_lines if log_lines else 0  # Normalize None to 0
        self.event_handler = event_handler
        self.handlers: list[Callable[[dict[str, dict]], None]] = []

    def start(self) -> None:
        """Start monitoring thread.

        Creates a daemon thread that runs the monitoring loop.
        Safe to call multiple times (no-op if already running).
        """
        super().start()
        if self.running:  # Only log if actually started
            self.logger.info(f"Started container health monitor (interval: {self.check_interval}s)")

    def stop(self, timeout: int = 5) -> None:
        """Stop monitoring thread.

        Args:
            timeout: Maximum seconds to wait for thread to stop (default: 5).
        """
        was_running = self.running
        super().stop(timeout=timeout)
        if was_running:  # Only log if actually stopped
            self.logger.info("Stopped container health monitor")

    def register_handler(
        self,
        handler: Callable[[dict[str, dict]], None],
    ) -> None:
        """Register handler to receive container health information.

        Handler will be called with container_states dict on every check cycle.
        Handler decides what to do with the information (mark sessions, cleanup,
        send alerts, update metrics, etc.). Multiple handlers can be registered.

        Args:
            handler: Callback function taking (container_states: dict[str, dict]).
                    Format: {container_id: {container_name, status, logs, checked_at}}
                    Handler should not raise exceptions.
        """
        self.handlers.append(handler)
        self.logger.debug(f"Registered health handler: {handler.__name__}")

    def _monitor_loop(self) -> None:
        """Main monitoring loop.

        Runs continuously while self.running is True. Catches all exceptions
        to prevent the monitoring thread from crashing.
        """
        while self.running:
            try:
                # Get current state of all containers
                container_states = self._get_container_states()

                # Notify all handlers with the information
                for handler in self.handlers:
                    try:
                        handler(container_states)
                    except Exception as e:
                        # Don't let handler errors crash the monitor
                        self.logger.error(f"Health handler error: {e}", exc_info=True)

            except Exception as e:
                # Don't crash the monitoring thread
                self.logger.error(f"Monitor loop error: {e}", exc_info=True)

            time.sleep(self.check_interval)

    def _get_container_states(self) -> dict[str, dict]:
        """Get current state of all tracked containers.

        Returns:
            Dict mapping container_id -> state_info for all tracked containers.
            Format:
            {
                "container_id": {
                    "container_id": str,
                    "container_name": str,
                    "status": str,  # "running", "stopped", "creating", "error"
                    "logs": str | None,  # Last N lines if log_lines > 0
                    "checked_at": str,  # ISO format timestamp
                }
            }
        """
        states = {}
        checked_at = datetime.now(UTC).isoformat()

        # Get snapshot of tracked containers
        container_ids = self.container_manager.get_tracked_containers()

        for container_id in container_ids:
            try:
                # Get current status (with refresh from Docker)
                status = self.container_manager.get_container_status(container_id, refresh=True)
                container_name = self.container_manager.containers.get(container_id, "unknown")

                # Optionally capture logs (if log_lines > 0)
                logs = None
                if self.log_lines > 0 and status not in (ContainerStatus.RUNNING, ContainerStatus.CREATING):
                    # Only capture logs for non-running containers (more useful)
                    try:
                        logs = self.container_manager.backend.get_workload_logs(container_id, tail=self.log_lines)
                    except Exception:
                        pass  # Logs optional, don't fail health check

                states[container_id] = {
                    "container_id": container_id,
                    "container_name": container_name,
                    "status": status.value,
                    "logs": logs,
                    "checked_at": checked_at,
                }

            except Exception as e:
                # If we can't check a container, report it as error state
                self.logger.warning(f"Failed to check container {container_id[:12]}: {e}")
                states[container_id] = {
                    "container_id": container_id,
                    "container_name": self.container_manager.containers.get(container_id, "unknown"),
                    "status": "error",
                    "logs": None,
                    "checked_at": checked_at,
                    "check_error": str(e),
                }

        return states
