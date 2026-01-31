"""Process health monitoring with background thread."""

import logging
import time
from collections.abc import Callable

from podkit.monitors.base import BaseThreadMonitor
from podkit.processes.manager import ProcessManager
from podkit.processes.models import ProcessStatus


class ProcessMonitor(BaseThreadMonitor):
    """Background monitor for process health.

    Runs in a separate thread, periodically checks process status,
    and invokes callbacks when failures are detected. This allows
    monitoring without blocking or keeping sessions alive.

    Example:
        monitor = ProcessMonitor(process_manager, check_interval=30)

        # Register failure handler
        def handle_failure(process_id, details):
            print(f"Process {process_id} failed: {details}")

        monitor.register_failure_handler(handle_failure)
        monitor.start()
    """

    def __init__(
        self,
        process_manager: ProcessManager,
        check_interval: int = 30,
        logger: logging.Logger | None = None,
    ):
        """Initialize process monitor.

        Args:
            process_manager: Process manager to monitor.
            check_interval: Seconds between health checks (default: 30).
            logger: Optional logger instance.
        """
        super().__init__(logger or logging.getLogger("podkit.processes.monitor"))
        self.process_manager = process_manager
        self.check_interval = check_interval
        self.failure_handlers: list[Callable[[str, dict], None]] = []

    def start(self) -> None:
        """Start monitoring thread.

        Creates a daemon thread that runs the monitoring loop.
        Safe to call multiple times (no-op if already running).
        """
        super().start()
        if self.running:  # Only log if actually started
            self.logger.info(f"Started process monitor (interval: {self.check_interval}s)")

    def stop(self, timeout: int = 5) -> None:
        """Stop monitoring thread.

        Args:
            timeout: Maximum seconds to wait for thread to stop (default: 5).
        """
        was_running = self.running
        super().stop(timeout=timeout)
        if was_running:  # Only log if actually stopped
            self.logger.info("Stopped process monitor")

    def register_failure_handler(
        self,
        handler: Callable[[str, dict], None],
    ) -> None:
        """Register callback for process failures.

        Handler will be called with (process_id, failure_details) when
        a process failure is detected. Multiple handlers can be registered.

        Args:
            handler: Callback function taking (process_id: str, details: dict).
                    Handler should not raise exceptions.
        """
        self.failure_handlers.append(handler)
        self.logger.debug(f"Registered failure handler: {handler.__name__}")

    def _monitor_loop(self) -> None:
        """Main monitoring loop.

        Runs continuously while self.running is True. Catches all exceptions
        to prevent the monitoring thread from crashing.
        """
        while self.running:
            try:
                failures = self._check_all_processes()

                for process_id, details in failures.items():
                    for handler in self.failure_handlers:
                        try:
                            handler(process_id, details)
                        except Exception as e:
                            # Don't let handler errors crash the monitor
                            process = self.process_manager.processes.get(process_id)
                            display = process.display_name if process else process_id[:8]
                            self.logger.error(f"Failure handler error for process {display}: {e}", exc_info=True)

            except Exception as e:
                # Don't crash the monitoring thread
                self.logger.error(f"Monitor loop error: {e}", exc_info=True)

            time.sleep(self.check_interval)

    def _check_all_processes(self) -> dict[str, dict]:
        """Check status of all processes and detect failures.

        Returns:
            Dict mapping process_id -> failure_details for failed processes.
            Empty dict if no failures detected.
        """
        failures = {}

        processes = list(self.process_manager.processes.items())

        for process_id, process in processes:
            old_status = process.status

            # Skip if already in terminal state
            if old_status in (ProcessStatus.STOPPED, ProcessStatus.FAILED):
                continue

            try:
                new_status = self.process_manager.get_status(process_id)

                if new_status == ProcessStatus.FAILED:
                    logs = self._get_logs_safe(process_id, tail=50)
                    failures[process_id] = {
                        "old_status": old_status.value,
                        "new_status": new_status.value,
                        "exit_code": process.exit_code,
                        "command": process.command,
                        "logs": logs,
                    }
                    self.logger.warning(f"Process {process.display_name} failed (exit: {process.exit_code})")

                # Detect unexpected RUNNING → STOPPED transitions
                elif old_status == ProcessStatus.RUNNING and new_status == ProcessStatus.STOPPED:
                    logs = self._get_logs_safe(process_id, tail=50)
                    failures[process_id] = {
                        "old_status": old_status.value,
                        "new_status": new_status.value,
                        "exit_code": process.exit_code,
                        "command": process.command,
                        "unexpected_stop": True,
                        "logs": logs,
                    }
                    self.logger.warning(f"Process {process.display_name} stopped unexpectedly")

            except Exception as e:
                # Continue checking other processes
                self.logger.warning(f"Failed to check process {process.display_name}: {e}")

        return failures

    def _get_logs_safe(self, process_id: str, tail: int) -> dict[str, str]:
        """Safely retrieve process logs.

        Returns empty dict if logs can't be retrieved (e.g., container removed).
        """
        try:
            return self.process_manager.get_logs(process_id, tail=tail)
        except Exception as e:
            process = self.process_manager.processes.get(process_id)
            display = process.display_name if process else process_id[:8]
            self.logger.debug(f"Failed to retrieve logs for {display}: {e}")
            return {"stdout": "", "stderr": ""}
