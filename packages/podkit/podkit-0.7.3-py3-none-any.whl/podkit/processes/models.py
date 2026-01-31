"""Data models for process management."""

from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class ProcessStatus(str, Enum):
    """Status of a managed process."""

    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class Process(BaseModel):
    """Managed background process in a container.

    Represents a long-running process started via ProcessManager,
    including its lifecycle state, logs, and runtime information.
    """

    id: str = Field(description="Unique process identifier")
    name: str | None = Field(None, description="Optional user-friendly name for the process")
    container_id: str = Field(description="Container where process runs")
    command: str = Field(description="Command that was executed")
    working_dir: Path = Field(description="Working directory")
    status: ProcessStatus = Field(default=ProcessStatus.STARTING, description="Current process status")
    pid: int | None = Field(None, description="Process ID inside container")
    start_time: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When process was started")
    stop_time: datetime | None = Field(None, description="When process stopped/failed")
    exit_code: int | None = Field(None, description="Exit code if process terminated")
    ports: list[int] = Field(default_factory=list, description="Detected listening ports")
    environment: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    log_dir: Path = Field(description="Directory for log files (container path)")

    @property
    def display_name(self) -> str:
        """Get display name for logging and debugging.

        Returns the user-provided name if available, otherwise a short UUID.

        Returns:
            User-friendly display name.

        Example:
            >>> process = Process(id="abc123...", name="api-server", ...)
            >>> process.display_name
            "api-server (abc123ab)"

            >>> process = Process(id="xyz789...", name=None, ...)
            >>> process.display_name
            "xyz789xy"
        """
        if self.name:
            return f"{self.name} ({self.id[:8]})"
        return self.id[:8]

    @property
    def stdout_log(self) -> Path:
        """Path to stdout log file (container path)."""
        return self.log_dir / f"{self.id}.out.log"

    @property
    def stderr_log(self) -> Path:
        """Path to stderr log file (container path)."""
        return self.log_dir / f"{self.id}.err.log"

    @property
    def pid_file(self) -> Path:
        """Path to PID file (container path)."""
        return self.log_dir / f"{self.id}.pid"

    @property
    def exit_code_file(self) -> Path:
        """Path to exit code file (container path)."""
        return self.log_dir / f"{self.id}.exit"
