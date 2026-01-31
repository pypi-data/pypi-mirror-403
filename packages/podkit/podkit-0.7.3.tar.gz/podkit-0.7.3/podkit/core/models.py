"""Core data models for podkit container management library."""

from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from podkit.constants import (
    DEFAULT_CONTAINER_LIFETIME_SECONDS,
    DEFAULT_CPU_LIMIT,
    DEFAULT_MEMORY_LIMIT,
    DEFAULT_SESSION_INACTIVITY_TIMEOUT_SECONDS,
    DEFAULT_USER,
    DEFAULT_WORKING_DIR,
)


class ContainerStatus(str, Enum):
    """Status of a container workload."""

    CREATING = "creating"
    RUNNING = "running"
    PAUSED = "paused"
    EXITED = "exited"  # Docker reports this
    STOPPED = "stopped"  # podkit uses this for intentional closure
    RESTARTING = "restarting"
    REMOVING = "removing"
    DEAD = "dead"
    ERROR = "error"  # podkit: container not found or check failed


class Mount(BaseModel):
    """Custom volume mount."""

    type: str = Field(default="bind", description="Mount type")
    source: Path = Field(description="Source path on the host")
    target: Path = Field(description="Target path inside the container")
    read_only: bool = Field(default=False, description="Mount as read-only")


class StartupVerificationConfig(BaseModel):
    """Configuration for container startup verification."""

    required_consecutive_checks: int = Field(
        3, description="Number of consecutive 'running' checks required for success"
    )
    check_interval_seconds: float = Field(1.0, description="Seconds to wait between status checks")
    max_wait_seconds: float = Field(5.0, description="Maximum seconds to wait for verification (total timeout)")
    capture_logs_on_failure: bool = Field(True, description="Capture container logs if startup fails")
    log_tail_lines: int = Field(100, description="Number of log lines to capture on failure")


class ContainerConfig(BaseModel):
    """Configuration for a container workload."""

    image: str | None = Field(
        None,
        description="Container image to use. If None, uses default image (python:3.11-alpine) "
        "unless inherit_parent_image is True.",
    )
    inherit_parent_image: bool = Field(
        False,
        description="Auto-detect and use parent container's image. "
        "Useful for spawning child containers with the same image as the orchestrator. "
        "Only works when running inside a container. Ignored if image is explicitly set.",
    )
    cpu_limit: float = Field(DEFAULT_CPU_LIMIT, description="CPU limit in cores")
    memory_limit: str = Field(DEFAULT_MEMORY_LIMIT, description="Memory limit (e.g., '4g', '512m')")
    container_lifetime_seconds: int = Field(
        DEFAULT_CONTAINER_LIFETIME_SECONDS,
        description="Container lifetime in seconds before auto-exit (default: 60 seconds). "
        "Only applies when entrypoint is None and use_image_defaults is False. "
        "Ignored when explicit entrypoint is set or use_image_defaults is True.",
    )
    environment: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    working_dir: str = Field(DEFAULT_WORKING_DIR, description="Working directory inside the container")
    user: str = Field(DEFAULT_USER, description="User to run commands as")
    use_image_defaults: bool = Field(
        False,
        description="Use image's default entrypoint and command without modification. "
        "When True, podkit will not override entrypoint or command, allowing the image to run as designed. "
        "Takes precedence over entrypoint and command fields.",
    )
    entrypoint: list[str] | None = Field(
        None,
        description="Override container entrypoint (None = auto-managed unless use_image_defaults is True). "
        "Ignored when use_image_defaults is True.",
    )
    command: list[str] | None = Field(
        None,
        description=(
            "Override container command (None = auto-managed based on entrypoint unless "
            "use_image_defaults is True). Use to specify custom startup command instead of "
            "default sleep behavior. Ignored when use_image_defaults is True."
        ),
    )
    volumes: list[Mount] = Field(default_factory=list, description="Volume bindings for the container")
    ports: list[int] = Field(
        default_factory=list,
        description="Ports to expose from container to host. Docker binds container port to same host port.",
    )
    networks: list[str] = Field(
        default_factory=list,
        description="Explicit list of networks to attach container to. Takes precedence over inherit_parent_networks.",
    )
    inherit_parent_networks: bool = Field(
        False,
        description="Auto-discover and use parent container's networks. "
        "Ignored if 'networks' is non-empty or not running in a container.",
    )
    tty: bool = Field(False, description="Allocate a pseudo-TTY for interactive features")
    stdin_open: bool = Field(False, description="Keep STDIN open even if not attached")
    auto_remove: bool = Field(
        False,
        description="Automatically remove container when it exits. "
        "Useful for ephemeral containers that should not leave behind stopped containers.",
    )
    startup_verification: StartupVerificationConfig | None = Field(
        None, description="Optional startup verification. If None, container starts without verification checks."
    )


class ProcessResult(BaseModel):
    """Result of a process execution."""

    exit_code: int = Field(description="Process exit code")
    stdout: str = Field(description="Standard output")
    stderr: str = Field(description="Standard error")


class Session(BaseModel):
    """User session information with container association."""

    user_id: str = Field(description="ID of the user")
    session_id: str = Field(description="ID of the session")
    container_id: str | None = Field(None, description="ID of the associated container")
    container_name: str | None = Field(None, description="Name of the associated container")
    status: ContainerStatus = Field(ContainerStatus.CREATING, description="Status of the container")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Time when the session was created",
    )
    last_active_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Time of last activity",
    )
    config: ContainerConfig = Field(description="Container configuration")
    data_dir: str = Field(description="Path to the session data directory")
    session_inactivity_timeout_seconds: int = Field(
        DEFAULT_SESSION_INACTIVITY_TIMEOUT_SECONDS,
        description="Session inactivity timeout in seconds (default: 3600 = 60 minutes)",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def is_expired(self, timeout_seconds: int | None = None) -> bool:
        """Check if the session has expired due to inactivity.

        Args:
            timeout_seconds: Inactivity timeout in seconds. If None, use session_inactivity_timeout_seconds.

        Returns:
            True if the session has expired, False otherwise.
        """
        if timeout_seconds is None:
            timeout_seconds = self.session_inactivity_timeout_seconds

        now = datetime.now(UTC)
        elapsed_seconds = (now - self.last_active_at).total_seconds()

        return elapsed_seconds > timeout_seconds

    def update_activity(self) -> None:
        """Update the last activity timestamp to current time."""
        self.last_active_at = datetime.now(UTC)
