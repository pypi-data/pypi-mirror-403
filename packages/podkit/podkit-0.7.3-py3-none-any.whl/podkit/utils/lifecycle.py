"""Optional lifecycle management utilities for convenient session management.

This module provides convenience functions for common use cases. You can still use
the core SessionManager API directly for more control.
"""

import base64
import logging
import uuid
from pathlib import Path
from threading import Lock
from typing import Any

from podkit.backends.docker import DockerBackend
from podkit.constants import (
    DEFAULT_CONTAINER_IMAGE,
    DEFAULT_CONTAINER_LIFETIME_SECONDS,
    DEFAULT_CONTAINER_PREFIX,
    DEFAULT_CPU_LIMIT,
    DEFAULT_MEMORY_LIMIT,
    DUMMY_WORKSPACE_PATH,
)
from podkit.core.manager import BaseContainerManager
from podkit.core.models import ContainerConfig, ProcessResult, Session
from podkit.core.session import BaseSessionManager
from podkit.utils.mounts import config_volumes_to_mounts, get_standard_workspace_mounts
from podkit.utils.paths import normalize_container_path, write_to_mounted_path

# Global managers cache
_managers_cache: dict[tuple[str, str], tuple[DockerBackend, BaseContainerManager, BaseSessionManager]] = {}
_cache_lock = Lock()


class _NoMountContainerManager(BaseContainerManager):
    """Container manager without filesystem mounts (execution-only)."""

    def get_mounts(self, user_id: str, session_id: str, config: ContainerConfig) -> list[dict[str, Any]]:
        """Return custom volumes from config (no automatic workspace mount)."""
        return config_volumes_to_mounts(config.volumes)

    def write_file(
        self,
        container_id: str,
        container_path: Path | str,
        content: str,
    ) -> Path:
        """
        Write file inside container using shell command (ephemeral).

        Args:
            container_id: ID of the container.
            container_path: Path inside the container. Can be relative or absolute.
            content: Content to write.

        Returns:
            The normalized container path where the file was written.
        """
        path = normalize_container_path(container_path)
        content_b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
        parent_dir = str(path.parent)
        filename = str(path)
        command = f"mkdir -p {parent_dir} && echo '{content_b64}' | base64 -d > {filename}"
        result = self.execute_command(container_id, ["sh", "-c", command])
        if result.exit_code != 0:
            raise RuntimeError(f"Failed to write file {path}: {result.stderr}")
        return path


# pylint: disable=duplicate-code
# Note: get_mounts() and write_file() implementations are intentionally duplicated
# from SimpleContainerManager to maintain independence between convenience API
# (lifecycle.py) and test infrastructure (core/manager.py)
class _MountedContainerManager(BaseContainerManager):
    """Container manager with filesystem mounts for file operations."""

    def __init__(
        self,
        backend,
        container_prefix: str,
        workspace_base: Path,
        workspace_host: Path,
        logger=None,
    ):
        super().__init__(backend, container_prefix, workspace_base, workspace_base_host=workspace_host, logger=logger)

    def get_mounts(self, user_id: str, session_id: str, config: ContainerConfig) -> list[dict[str, Any]]:
        """Get volume mounts for containers."""
        return get_standard_workspace_mounts(
            workspace_base=self.workspace_base,
            user_id=user_id,
            session_id=session_id,
            config=config,
            to_host_path_fn=self.to_host_path,
            volume_name=self.volume_name,
        )

    def write_file(
        self,
        container_id: str,
        container_path: Path | str,
        content: str,
    ) -> Path:
        """Write file to mounted filesystem (persists).

        Looks up user_id and session_id from container labels.

        Returns:
            The normalized container path where the file was written.
        """
        # Look up user_id/session_id from container labels
        labels = self.backend.get_workload_labels(container_id)
        user_id = labels.get("podkit.user_id")
        session_id = labels.get("podkit.session_id")

        if not user_id or not session_id:
            raise RuntimeError(
                f"Container {container_id} missing required labels "
                f"(podkit.user_id={user_id}, podkit.session_id={session_id})"
            )

        return write_to_mounted_path(
            container_path,
            content,
            lambda path: self.to_host_path(path, user_id, session_id),
        )


class SessionProxy:
    """
    Convenience wrapper for session operations.

    Remembers user_id and session_id so you don't have to pass them repeatedly.

    Example:
        session = get_docker_session(user_id="bob", session_id="123")
        result = session.execute_command("ls -lah")
        session.write_file(Path("/workspace/test.txt"), "Hello")
        session.close()
    """

    def __init__(self, session_manager: BaseSessionManager, user_id: str, session_id: str):
        """
        Initialize session proxy.

        Args:
            session_manager: The underlying session manager.
            user_id: User identifier.
            session_id: Session identifier.
        """
        self._manager = session_manager
        self._user_id = user_id
        self._session_id = session_id

    @property
    def user_id(self) -> str:
        """Get user ID."""
        return self._user_id

    @property
    def session_id(self) -> str:
        """Get session ID."""
        return self._session_id

    def execute_command(
        self,
        command: str | list[str],
        working_dir: Path | None = None,
        environment: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> ProcessResult:
        """
        Execute command in this session's container.

        Args:
            command: Command to execute.
            working_dir: Optional working directory.
            environment: Optional environment variables.
            timeout: Optional timeout in seconds.

        Returns:
            ProcessResult with exit code and output.

        Raises:
            RuntimeError: If the session is not found or command execution fails.
        """
        return self._manager.execute_command(
            self._user_id,
            self._session_id,
            command,
            working_dir,
            environment,
            timeout,
        )

    def write_file(self, container_path: Path | str, content: str) -> Path:
        """
        Write a file to this session's container.

        Behavior depends on how session was created:
        - With workspace: File persists on host filesystem
        - Without workspace: File written inside container (ephemeral)

        Args:
            container_path: Path inside the container. Can be:
                - Relative path (e.g., "file.txt") - auto-prepended with /workspace/
                - Absolute path (e.g., "/workspace/file.txt") - used as-is
            content: Content to write.

        Returns:
            The normalized container path where the file was written.

        Raises:
            RuntimeError: If the session is not found or file write fails.
        """
        # Delegate to session manager - it will pass to container manager for normalization
        return self._manager.write_file(
            self._user_id,
            self._session_id,
            container_path,
            content,
        )

    def close(self) -> None:
        """
        Close this session and cleanup resources.

        Raises:
            RuntimeError: If the session is not found.
        """
        self._manager.close_session(self._user_id, self._session_id)

    def get_info(self) -> Session | None:
        """
        Get information about this session.

        Returns:
            Session object or None if not found.
        """
        return self._manager.get_session(self._user_id, self._session_id)

    def __enter__(self):
        """Support context manager protocol."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Auto-close on context manager exit."""
        try:
            self.close()
        except Exception:  # pylint: disable=broad-except
            pass  # Best-effort cleanup


def get_docker_session(
    *,
    user_id: str,
    session_id: str,
    config: ContainerConfig | None = None,
    workspace: Path | str | None = None,
    workspace_host: Path | str | None = None,
    container_prefix: str = DEFAULT_CONTAINER_PREFIX,
    image_name: str = DEFAULT_CONTAINER_IMAGE,
    logger: logging.Logger | None = None,
) -> SessionProxy:
    """
    Get or create a Docker session with automatic manager setup.

    This is a convenience function that handles manager lifecycle internally.
    If you need more control, use BaseSessionManager directly.

    There are two ways to mount volumes:

    1. Custom volumes via config.volumes (RECOMMENDED)
       - Explicit, predictable paths
       - Works with local and remote Docker
       - You control the exact mount points

    2. Workspace system via workspace/workspace_host params
       - Auto-creates directory structure: {workspace}/workspaces/{user_id}/{session_id}
       - Enables persistent write_file() to host filesystem
       - Only works when podkit can mkdir on the Docker host (local Docker or DinD)

    Usage Pattern 1 - Custom volumes (recommended):
        session = get_docker_session(
            user_id="bob",
            session_id="123",
            config=ContainerConfig(
                image="python:3.11-alpine",
                volumes=[
                    Mount(source="/host/data", target="/data", read_only=True),
                    Mount(source="/host/output", target="/output"),
                ],
            ),
        )
        result = session.execute_command(["ls", "/data"])
        session.close()

    Usage Pattern 2 - No mounts (ephemeral execution):
        session = get_docker_session(user_id="bob", session_id="123")
        session.write_file("/tmp/script.py", "print('Hello')")  # Ephemeral
        result = session.execute_command("python /tmp/script.py")
        session.close()

    Usage Pattern 3 - Workspace system (local Docker only):
        session = get_docker_session(
            user_id="bob",
            session_id="123",
            workspace="/app/data",        # Where podkit runs mkdir
            workspace_host="/app/data",   # What Docker mounts (same for local Docker)
        )
        # Creates: /app/data/workspaces/bob/123/ on host
        # Mounts to: /workspace in container
        session.write_file("/workspace/test.txt", "content")  # Persists on host
        session.close()

    Usage Pattern 4 - Context manager (auto-cleanup):
        with get_docker_session(user_id="bob", session_id="123") as session:
            result = session.execute_command("ls -lah")

    Args:
        user_id: User identifier (used in workspace path if workspace system enabled).
        session_id: Session identifier (used in workspace path if workspace system enabled).
        config: Container configuration. Use config.volumes for custom mounts.
            If None, creates defaults with auto-shutdown after 60 seconds.
        workspace: Base path where podkit creates workspace directories.
            When set, podkit runs: mkdir -p {workspace}/workspaces/{user_id}/{session_id}
            This path must be writable by the machine running podkit.
            If None, workspace system is disabled (use config.volumes instead).
        workspace_host: The path Docker uses for bind mounts.
            - For local Docker: same as workspace
            - For Docker-in-Docker: the host path that maps to workspace
            Required when workspace is provided.
        container_prefix: Container name prefix (default: "podkit").
        image_name: Default image if config not provided (default: "python:3.11-alpine").
        logger: Optional logger instance.

    Returns:
        SessionProxy for convenient operations.

    Raises:
        RuntimeError: If Docker is not available or session creation fails.
        ValueError: If workspace provided but workspace_host is not.

    Note:
        For remote Docker (Docker daemon on different machine), use config.volumes
        instead of workspace/workspace_host. The workspace system requires podkit
        to create directories on the Docker host, which isn't possible with remote Docker.
    """
    # Validate workspace parameters
    has_mounts = workspace is not None
    if has_mounts and workspace_host is None:
        raise ValueError("workspace_host is required when workspace is provided")

    # Determine cache key
    if has_mounts:
        cache_key = (f"mounted:{workspace}", container_prefix)
    else:
        cache_key = ("no-mounts", container_prefix)

    with _cache_lock:
        if cache_key not in _managers_cache:
            backend = DockerBackend(logger=logger)
            backend.connect()

            if has_mounts:
                container_manager = _MountedContainerManager(
                    backend=backend,
                    container_prefix=container_prefix,
                    workspace_base=Path(workspace),
                    workspace_host=Path(workspace_host),
                    logger=logger,
                )
            else:
                container_manager = _NoMountContainerManager(
                    backend=backend,
                    container_prefix=container_prefix,
                    workspace_base=Path(DUMMY_WORKSPACE_PATH),
                    logger=logger,
                )

            session_manager = BaseSessionManager(
                container_manager=container_manager,
                default_image=image_name,
                logger=logger,
            )

            _managers_cache[cache_key] = (backend, container_manager, session_manager)

        _, _, session_manager = _managers_cache[cache_key]

    existing_session = session_manager.get_session(user_id, session_id)

    if existing_session is None:
        if config is None:
            config = ContainerConfig(
                image=image_name,
                # entrypoint=None means use container_lifetime_seconds for auto-shutdown
                container_lifetime_seconds=DEFAULT_CONTAINER_LIFETIME_SECONDS,
            )

        session_manager.create_session(
            user_id=user_id,
            session_id=session_id,
            config=config,
        )

    return SessionProxy(session_manager, user_id, session_id)


def reset_lifecycle_cache() -> None:
    """
    Reset the internal manager cache.

    Useful for testing or when you need to recreate managers.
    Cleanup all sessions before calling this.
    """
    with _cache_lock:
        for _, _, session_manager in _managers_cache.values():
            try:
                session_manager.cleanup_all()
            except Exception:  # pylint: disable=broad-except
                pass

        _managers_cache.clear()


def run_in_docker(
    command: str | list[str],
    *,
    image: str = DEFAULT_CONTAINER_IMAGE,
    command_timeout: int | None = None,
    memory_limit: str = DEFAULT_MEMORY_LIMIT,
    cpu_limit: float = DEFAULT_CPU_LIMIT,
    files: dict[str, str] | None = None,
    environment: dict[str, str] | None = None,
    working_dir: Path | None = None,
) -> ProcessResult:
    """Run a command in a temporary Docker container.

    This is a convenience function for one-off command executions.
    The container is automatically created and cleaned up.

    For persistent sessions or more control, use get_docker_session() instead.

    Args:
        command: Command to execute (string or list of strings).
        image: Docker image to use (default: python:3.11-alpine).
        command_timeout: Maximum seconds to wait for command completion.
            If None (default), waits indefinitely until command finishes.
            Returns exit code 124 if timeout is reached.
        memory_limit: Container memory limit (default: 512m).
        cpu_limit: Container CPU limit in cores (default: 1.0).
        files: Dict of {container_path: content} to write before execution.
        environment: Environment variables for the command.
        working_dir: Working directory for command execution.

    Returns:
        ProcessResult with exit_code, stdout, and stderr.

    Example:
        >>> result = run_in_docker("echo hello")
        >>> print(result.stdout)
        hello

        >>> result = run_in_docker(
        ...     "python /workspace/script.py",
        ...     files={"/workspace/script.py": "print('hello')"},
        ... )

        >>> result = run_in_docker(
        ...     "python long_job.py",
        ...     command_timeout=30,  # Kill if not done in 30s
        ... )
        >>> if result.exit_code == 124:
        ...     print("Command timed out")
    """
    config = ContainerConfig(
        image=image,
        memory_limit=memory_limit,
        cpu_limit=cpu_limit,
        entrypoint=[],  # Use sleep infinity - container runs until we're done
    )

    with get_docker_session(
        user_id="_run_in_docker",
        session_id=uuid.uuid4().hex,
        config=config,
    ) as session:
        if files:
            for path, content in files.items():
                session.write_file(path, content)

        return session.execute_command(
            command,
            timeout=command_timeout,
            environment=environment,
            working_dir=working_dir,
        )
