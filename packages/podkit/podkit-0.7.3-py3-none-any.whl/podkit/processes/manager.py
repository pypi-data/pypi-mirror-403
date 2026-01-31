"""Process manager for managing background processes in containers.

Redesigned implementation that fixes exit code capture issues.
Built incrementally and validated through test_14.
"""

import logging
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import TYPE_CHECKING

from podkit.core.manager import BaseContainerManager
from podkit.processes.models import Process, ProcessStatus

if TYPE_CHECKING:
    from podkit.core.events import PodkitEventHandler


class ProcessManager:
    """Manages multiple background processes within a single container.

    This is a container-scoped manager - create one instance per container.
    Uses simple shell commands to run processes in background, captures PIDs,
    redirects output to log files, and provides lifecycle management.

    Example:
        manager = ProcessManager(
            container_manager=container_manager,
            container_id=container_id,
            user_id=user_id,
            session_id=session_id,
        )

        # Start background process with optional name
        process = manager.start_process(
            command="python -m http.server 8000",
            name="web-server",  # Optional user-friendly name
            working_dir=Path("/workspace")
        )

        # Check status
        status = manager.get_status(process.id)

        # Get logs
        logs = manager.get_logs(process.id, tail=100)

        # Stop process
        manager.stop_process(process.id)
    """

    def __init__(
        self,
        container_manager: BaseContainerManager,
        container_id: str,
        user_id: str,
        session_id: str,
        default_log_dir: Path = Path("/workspace/logs"),
        event_handler: "PodkitEventHandler | None" = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize container-scoped process manager.

        Args:
            container_manager: Podkit container manager instance.
            container_id: Container ID to manage processes in.
            user_id: User ID for session (required for mounted filesystem operations).
            session_id: Session ID (required for mounted filesystem operations).
            default_log_dir: Default directory for process logs (container path).
            event_handler: Optional event handler for process lifecycle events.
            logger: Optional logger instance (accepts any Python logger).
        """
        self.container_manager = container_manager
        self.container_id = container_id
        self.user_id = user_id
        self.session_id = session_id
        self.default_log_dir = default_log_dir
        self.event_handler = event_handler
        self.logger = logger or logging.getLogger("podkit.processes")
        self.processes: dict[str, Process] = {}
        self.lock = RLock()  # Reentrant lock - allows same thread to acquire multiple times

    def start_process(
        self,
        command: str,
        name: str | None = None,
        working_dir: Path | None = None,
        environment: dict[str, str] | None = None,
        log_dir: Path | None = None,
    ) -> Process:
        """Start a background process in the container.

        Uses simple shell backgrounding to run process, captures PID,
        redirects output to log files. Returns immediately.

        Args:
            command: Command to execute in background.
            name: Optional user-friendly name for the process (helps with debugging).
            working_dir: Working directory for the process (default: /workspace).
            environment: Environment variables for the process.
            log_dir: Directory for log files (default: /workspace/logs).

        Returns:
            Process object with ID, PID, and status.

        Raises:
            RuntimeError: If process start fails.

        Example:
            >>> process = manager.start_process(
            ...     command="python server.py",
            ...     name="api-server"
            ... )
            >>> print(process.display_name)
            "api-server (abc12345)"
        """
        process_id = str(uuid.uuid4())
        working_dir = working_dir or Path("/workspace")
        log_dir = log_dir or self.default_log_dir
        environment = environment or {}

        try:
            self.container_manager.execute_command(
                self.container_id,
                ["mkdir", "-p", str(log_dir)],
            )
        except Exception as e:
            raise RuntimeError(f"Failed to create log directory: {e}") from e

        process = Process(
            id=process_id,
            name=name,
            container_id=self.container_id,
            command=command,
            working_dir=working_dir,
            log_dir=log_dir,
            environment=environment,
        )

        self.logger.info(f"Starting process {process.display_name}: {command}")

        # Strategy: Use sh -c with nohup, redirect to files, background with &
        # Write PID directly to file
        pid_file = log_dir / f"{process_id}.pid"
        stdout_log = log_dir / f"{process_id}.out.log"
        stderr_log = log_dir / f"{process_id}.err.log"
        exit_code_file = log_dir / f"{process_id}.exit"

        export_stmts = ""
        if environment:
            for key, value in environment.items():
                # Escape single quotes for shell safety
                escaped_value = value.replace("'", "'\\''")
                export_stmts += f"export {key}='{escaped_value}'; "

        # Build command: run in background, capture PID and exit code
        # Use a subshell to:
        # 1. Export environment variables
        # 2. Run the command with output redirected
        # 3. Capture its exit code immediately after completion
        # 4. Write exit code to file
        # The subshell itself runs in background, we track its PID
        startup_cmd = [
            "sh",
            "-c",
            f"cd {working_dir} && ({export_stmts}{command} > {stdout_log} 2> {stderr_log}; "
            f"echo $? > {exit_code_file}) & echo $! > {pid_file}",
        ]

        try:
            result = self.container_manager.execute_command(
                self.container_id,
                startup_cmd,
            )

            if result.exit_code != 0:
                raise RuntimeError(f"Failed to start process: exit_code={result.exit_code}, stderr={result.stderr}")

            # Poll for PID file with retries (more robust than fixed sleep)
            max_attempts = 10
            attempt_delay = 0.05  # Start with 50ms
            pid_result = None

            for attempt in range(max_attempts):
                time.sleep(attempt_delay)
                pid_result = self.container_manager.execute_command(
                    self.container_id,
                    ["cat", str(pid_file)],
                )
                if pid_result.exit_code == 0 and pid_result.stdout.strip():
                    break
                attempt_delay = min(attempt_delay * 1.5, 0.5)  # Exponential backoff, max 500ms
                self.logger.debug(f"PID file not ready, attempt {attempt + 1}/{max_attempts}")

            if pid_result and pid_result.exit_code == 0 and pid_result.stdout.strip():
                process.pid = int(pid_result.stdout.strip())
                process.status = ProcessStatus.RUNNING
                self.logger.info(f"Started process {process.display_name} with PID {process.pid}")

                # Notify event handler of successful start
                if self.event_handler:
                    self.event_handler.on_process_started(
                        process_id=process_id,
                        container_id=self.container_id,
                        user_id=self.user_id,
                        session_id=self.session_id,
                        command=command,
                        pid=process.pid,
                    )
            else:
                process.status = ProcessStatus.FAILED
                self.logger.error(f"Failed to read PID for process {process.display_name}")

                # Notify event handler of failure
                if self.event_handler:
                    self.event_handler.on_process_failed(
                        process_id=process_id,
                        container_id=self.container_id,
                        user_id=self.user_id,
                        session_id=self.session_id,
                        error="Failed to read PID file",
                    )

            with self.lock:
                self.processes[process_id] = process

            return process

        except Exception as e:
            with self.lock:
                if process_id in self.processes:
                    del self.processes[process_id]
            raise RuntimeError(f"Failed to start process: {e}") from e

    def is_running(self, process_id: str) -> bool:
        """Check if process is still running.

        Uses ps to check if PID exists and is not a zombie.
        Zombies are processes that have terminated but haven't been reaped yet.

        Args:
            process_id: Process ID.

        Returns:
            True if process is running, False otherwise.

        Raises:
            ValueError: If process_id not found.
        """
        with self.lock:
            if process_id not in self.processes:
                raise RuntimeError(f"Process {process_id} not found")

            process = self.processes[process_id]
            pid = process.pid

        if pid is None:
            return False

        # Check process state to exclude zombies (state Z or Z+)
        result = self.container_manager.execute_command(
            self.container_id,
            ["ps", "-p", str(pid), "-o", "state="],
        )

        if result.exit_code != 0:
            return False

        # Process is running if it exists and is not a zombie
        state = result.stdout.strip()
        is_running = bool(state) and not state.startswith("Z")

        self.logger.debug(f"Process {pid} state: '{state}', is_running: {is_running}")
        return is_running

    def stop_process(self, process_id: str, timeout: int = 2, force: bool = True) -> bool:
        """Stop a running process.

        Sends SIGTERM, waits for timeout seconds, then SIGKILL if still running.

        Args:
            process_id: Process ID to stop.
            timeout: Seconds to wait before force kill (default: 2).
            force: If True, send SIGKILL if SIGTERM fails (default: True).

        Returns:
            True if successfully stopped, False otherwise.

        Raises:
            ValueError: If process_id not found.
        """
        with self.lock:
            if process_id not in self.processes:
                raise RuntimeError(f"Process {process_id} not found")

            process = self.processes[process_id]
            pid = process.pid
            display_name = process.display_name

        if pid is None:
            self.logger.warning(f"Process {display_name} has no PID")
            return False

        self.logger.info(f"Stopping process {display_name} (PID: {pid})")

        try:
            # Debug: check what processes exist
            ps_result = self.container_manager.execute_command(
                self.container_id,
                ["ps", "-ef"],
            )
            self.logger.debug(f"Process list before kill:\n{ps_result.stdout}")

            result = self.container_manager.execute_command(
                self.container_id,
                ["kill", str(pid)],
            )

            self.logger.debug(f"kill command result: exit_code={result.exit_code}, stderr='{result.stderr}'")

            if result.exit_code != 0:
                self.logger.warning(f"Failed to send SIGTERM to process {display_name}: {result.stderr}")
                # Try SIGKILL as fallback
                kill_result = self.container_manager.execute_command(
                    self.container_id,
                    ["kill", "-9", str(pid)],
                )
                self.logger.debug(f"kill -9 result: exit_code={kill_result.exit_code}, stderr='{kill_result.stderr}'")
                if kill_result.exit_code != 0:
                    return False

            for i in range(int(timeout * 5)):  # Check 5 times per second
                time.sleep(0.2)
                running = self.is_running(process_id)
                self.logger.debug(f"Check {i + 1}: is_running={running}")
                if not running:
                    self.logger.info(f"Successfully stopped process {display_name}")

                    # Notify event handler
                    if self.event_handler:
                        self.event_handler.on_process_stopped(
                            process_id=process_id,
                            container_id=self.container_id,
                            user_id=self.user_id,
                            session_id=self.session_id,
                            exit_code=None,  # Exit code not available when killed
                        )

                    return True

            if force:
                self.logger.info(f"Force killing process {display_name}")
                kill9_result = self.container_manager.execute_command(
                    self.container_id,
                    ["kill", "-9", str(pid)],
                )
                self.logger.debug(
                    f"Final kill -9 result: exit_code={kill9_result.exit_code}, stderr='{kill9_result.stderr}'"
                )
                time.sleep(0.5)

                # Debug: check what processes exist now
                ps_result2 = self.container_manager.execute_command(
                    self.container_id,
                    ["ps", "-ef"],
                )
                self.logger.debug(f"Process list after kill -9:\n{ps_result2.stdout}")

                running_final = self.is_running(process_id)
                self.logger.debug(f"Final check: is_running={running_final}")
                if not running_final:
                    self.logger.info(f"Successfully force-killed process {display_name}")

                    # Notify event handler
                    if self.event_handler:
                        self.event_handler.on_process_stopped(
                            process_id=process_id,
                            container_id=self.container_id,
                            user_id=self.user_id,
                            session_id=self.session_id,
                            exit_code=None,  # Exit code not available when force-killed
                        )

                    return True

            self.logger.warning(f"Process {display_name} still running after all attempts")
            return False

        except Exception as e:
            self.logger.error(f"Error stopping process {display_name}: {e}")
            return False

    def list_processes(self) -> list[Process]:
        """List all managed processes.

        Returns:
            List of all processes managed by this manager.
        """
        with self.lock:
            return list(self.processes.values())

    def get_status(self, process_id: str) -> ProcessStatus:
        """Get current status of a process.

        Checks if process is still running via ps command.
        Updates process status and detects failures.
        Captures exit code when process terminates.

        Args:
            process_id: Process ID.

        Returns:
            Current process status.

        Raises:
            ValueError: If process_id not found.
        """
        with self.lock:
            if process_id not in self.processes:
                raise RuntimeError(f"Process {process_id} not found")

            process = self.processes[process_id]

            # Don't check if already in terminal state
            if process.status in (ProcessStatus.STOPPED, ProcessStatus.FAILED):
                return process.status

            try:
                if self.is_running(process_id):
                    process.status = ProcessStatus.RUNNING
                    self._update_ports(process_id)
                else:
                    process.stop_time = datetime.now(UTC)

                    exit_code = self._read_exit_code(process.exit_code_file)
                    if exit_code is not None:
                        process.exit_code = exit_code
                        if exit_code == 0:
                            process.status = ProcessStatus.STOPPED
                            self.logger.info(f"Process {process.display_name} completed successfully (exit 0)")

                            # Notify event handler of normal completion
                            if self.event_handler:
                                self.event_handler.on_process_stopped(
                                    process_id=process_id,
                                    container_id=self.container_id,
                                    user_id=self.user_id,
                                    session_id=self.session_id,
                                    exit_code=exit_code,
                                )
                        else:
                            process.status = ProcessStatus.FAILED
                            self.logger.info(f"Process {process.display_name} failed (exit {exit_code})")

                            # Notify event handler of failure
                            if self.event_handler:
                                self.event_handler.on_process_failed(
                                    process_id=process_id,
                                    container_id=self.container_id,
                                    user_id=self.user_id,
                                    session_id=self.session_id,
                                    error=f"Process exited with code {exit_code}",
                                )
                    else:
                        # No exit code available, assume stopped normally
                        process.status = ProcessStatus.STOPPED
                        self.logger.info(f"Process {process.display_name} completed (no exit code)")

                        # Notify event handler
                        if self.event_handler:
                            self.event_handler.on_process_stopped(
                                process_id=process_id,
                                container_id=self.container_id,
                                user_id=self.user_id,
                                session_id=self.session_id,
                                exit_code=None,
                            )

            except Exception as e:
                # Container likely removed
                self.logger.debug(f"Process check failed: {e}")
                process.status = ProcessStatus.FAILED
                process.stop_time = datetime.now(UTC)

                # Notify event handler of failure
                if self.event_handler:
                    self.event_handler.on_process_failed(
                        process_id=process_id,
                        container_id=self.container_id,
                        user_id=self.user_id,
                        session_id=self.session_id,
                        error=f"Process check failed: {e}",
                    )

            return process.status

    def get_logs(self, process_id: str, tail: int = 100) -> dict[str, str]:
        """Retrieve process logs.

        Args:
            process_id: Process ID.
            tail: Number of lines to retrieve from end (default: 100).

        Returns:
            Dict with 'stdout' and 'stderr' keys containing log content.

        Raises:
            ValueError: If process_id not found.
        """
        with self.lock:
            if process_id not in self.processes:
                raise RuntimeError(f"Process {process_id} not found")

            process = self.processes[process_id]
            stdout_log = process.stdout_log
            stderr_log = process.stderr_log
            display_name = process.display_name

        stdout = ""
        stderr = ""

        try:
            stdout_result = self.container_manager.execute_command(
                self.container_id,
                ["tail", "-n", str(tail), str(stdout_log)],
            )
            if stdout_result.exit_code == 0:
                stdout = stdout_result.stdout
        except Exception as e:
            self.logger.debug(f"Failed to read stdout for {display_name}: {e}")

        try:
            stderr_result = self.container_manager.execute_command(
                self.container_id,
                ["tail", "-n", str(tail), str(stderr_log)],
            )
            if stderr_result.exit_code == 0:
                stderr = stderr_result.stdout
        except Exception as e:
            self.logger.debug(f"Failed to read stderr for {display_name}: {e}")

        return {
            "stdout": stdout,
            "stderr": stderr,
        }

    def _read_exit_code(self, exit_file: Path) -> int | None:
        """Read exit code from file.

        Returns None if file doesn't exist or can't be parsed.
        """
        try:
            result = self.container_manager.execute_command(
                self.container_id,
                ["cat", str(exit_file)],
            )

            if result.exit_code == 0 and result.stdout.strip():
                return int(result.stdout.strip())
        except (ValueError, Exception) as e:
            self.logger.debug(f"Failed to read exit code from {exit_file}: {e}")

        return None

    def _update_ports(self, process_id: str) -> None:
        """Detect which ports process is listening on.

        Uses lsof to detect listening ports. Checks both the tracked PID
        and its children, since the tracked PID is often a wrapper subshell
        with the actual command running as a child process.

        Args:
            process_id: Process ID.
        """
        with self.lock:
            if process_id not in self.processes:
                return

            process = self.processes[process_id]
            pid = process.pid
            display_name = process.display_name

        if pid is None:
            return

        try:
            # Check both the tracked PID and its children for listening ports.
            # The tracked PID is often a wrapper subshell, with the actual
            # command (e.g., node server.js) running as a child process.
            result = self.container_manager.execute_command(
                self.container_id,
                [
                    "sh",
                    "-c",
                    f'PIDS="{pid} $(pgrep -P {pid} 2>/dev/null)"; '
                    f"for pid in $PIDS; do "
                    f"lsof -Pan -p $pid -i 2>/dev/null | grep LISTEN | "
                    f"awk '{{print $9}}' | sed -E 's/.*:([0-9]+).*/\\1/'; "
                    f"done | sort -u",
                ],
            )

            if result.exit_code == 0 and result.stdout.strip():
                ports = []
                for line in result.stdout.strip().split("\n"):
                    try:
                        if line:
                            ports.append(int(line))
                    except ValueError:
                        pass

                if ports:
                    with self.lock:
                        # Re-check process still exists before updating
                        if process_id in self.processes:
                            self.processes[process_id].ports = ports
                    self.logger.debug(f"Process {display_name} listening on ports: {ports}")

        except Exception as e:
            # Non-critical - silently continue
            self.logger.debug(f"Failed to detect ports for process {display_name}: {e}")
