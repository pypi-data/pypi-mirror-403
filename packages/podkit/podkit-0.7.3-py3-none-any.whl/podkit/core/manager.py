"""Base container manager for managing container lifecycle."""

import logging
import re
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, Any

from podkit.backends.base import BackendInterface
from podkit.constants import CONTAINER_WORKSPACE_PATH
from podkit.core.models import ContainerConfig, ContainerStatus, ProcessResult
from podkit.utils.mounts import get_standard_workspace_mounts, get_volume_init_command
from podkit.utils.paths import (
    container_to_host_path,
    get_workspace_path,
    host_to_container_path,
    write_to_mounted_path,
)

if TYPE_CHECKING:
    from podkit.core.events import PodkitEventHandler


class BaseContainerManager(ABC):
    """
    Base container manager that works with any backend.

    Projects extend this class and inject their chosen backend.
    """

    def __init__(
        self,
        backend: BackendInterface,
        container_prefix: str,
        workspace_base: Path,
        workspace_base_host: Path | None = None,
        volume_name: str | None = None,
        event_handler: "PodkitEventHandler | None" = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize container manager.

        Args:
            backend: Backend implementation (Docker, K8s, etc.).
            container_prefix: Prefix for container names (e.g., "sandbox", "biomni").
            workspace_base: Base workspace directory for all sessions.
            workspace_base_host: Actual host path that Docker can access (for nested containers).
                                If None, assumes workspace_base is directly accessible by Docker.
            volume_name: Optional Docker volume name. If provided, uses named volume with subpath
                        instead of bind mounts. Useful for containerized deployments where the
                        parent container mounts a named volume (e.g., `data-volume:/data`) and
                        child containers need to access subdirectories of that volume.
            event_handler: Optional event handler for lifecycle events.
            logger: Optional logger instance. If None, creates a default logger.
                   Accepts any Python logger for flexible integration with external logging systems.
        """
        self.backend = backend
        self.container_prefix = container_prefix
        self.workspace_base = Path(workspace_base)
        self.workspace_base_host = Path(workspace_base_host) if workspace_base_host else self.workspace_base
        self.volume_name = volume_name
        self.event_handler = event_handler
        self.logger = logger or logging.getLogger(f"podkit.{container_prefix}")
        self.lock = Lock()
        self.containers: dict[str, str] = {}  # {workload_id: workload_name}

        self.backend.connect()

    def _track_container(self, container_id: str, container_name: str) -> None:
        """Thread-safe method to add container to tracking dictionary.

        Args:
            container_id: Container ID to track.
            container_name: Container name.
        """
        with self.lock:
            self.containers[container_id] = container_name

    def _untrack_container(self, container_id: str) -> bool:
        """Thread-safe method to remove container from tracking dictionary.

        Args:
            container_id: Container ID to untrack.

        Returns:
            True if container was tracked (and removed), False otherwise.
        """
        with self.lock:
            if container_id in self.containers:
                del self.containers[container_id]
                return True
            return False

    def _is_tracked(self, container_id: str) -> bool:
        """Thread-safe method to check if container is tracked.

        Args:
            container_id: Container ID to check.

        Returns:
            True if container is tracked, False otherwise.
        """
        with self.lock:
            return container_id in self.containers

    def get_tracked_containers(self) -> list[str]:
        """Get list of tracked container IDs.

        Returns:
            List of container IDs currently tracked.
        """
        with self.lock:
            return list(self.containers.keys())

    def create_container(
        self,
        user_id: str,
        session_id: str,
        config: ContainerConfig,
        *,
        container_name: str | None = None,
    ) -> tuple[str, str]:
        """
        Create a new container.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            config: Container configuration.
            container_name: Optional container name. If None, generates automatically.

        Returns:
            Tuple of (container_id, container_name).

        Raises:
            RuntimeError: If container creation fails.
        """
        # Allow event handler to modify config before creation
        if self.event_handler:
            config = self.event_handler.on_container_creating(user_id, session_id, config)

        if container_name is None:
            user_session_slug = "-".join(re.sub(r"[^a-z0-9]", "", _id.lower()) for _id in (session_id, user_id))
            container_name = f"{self.container_prefix}-{user_session_slug}-{uuid.uuid4().hex[:4]}"

        mounts = self.get_mounts(user_id, session_id, config)

        # Add labels for session recovery
        labels = {
            "podkit.user_id": user_id,
            "podkit.session_id": session_id,
            "podkit.manager": self.container_prefix,
            "podkit.image": config.image,
        }

        try:
            # Create via backend with labels (outside lock - this may be slow)
            container_id = self.backend.create_workload(
                name=container_name,
                config=config,
                mounts=mounts,
                labels=labels,
            )

            # Add to tracking (minimize lock time)
            self._track_container(container_id, container_name)

            # Notify event handler of successful creation
            if self.event_handler:
                self.event_handler.on_container_created(container_id, container_name, user_id, session_id, config)

            return container_id, container_name

        except Exception as e:
            # Notify event handler of failure
            if self.event_handler:
                self.event_handler.on_container_creation_failed(user_id, session_id, config, e)
            raise

    @abstractmethod
    def get_mounts(
        self,
        user_id: str,
        session_id: str,
        config: ContainerConfig,
    ) -> list[dict[str, Any]]:
        """
        Get volume mounts for container.

        Project-specific implementation (sandbox vs biomni have different needs).

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            config: Container configuration.

        Returns:
            List of mount specifications in Docker format.
        """
        ...

    def start_container(self, container_id: str, config: ContainerConfig | None = None) -> None:
        """
        Start a container with optional startup verification.

        Backend automatically handles paused vs stopped states.

        Args:
            container_id: ID of the container to start.
            config: Optional config for verification settings.
                   If None or no startup_verification, verification is skipped.

        Raises:
            RuntimeError: If container start fails or verification fails.
        """
        # Delegate to backend - it handles start/unpause + verification
        verification_config = config.startup_verification if config else None

        try:
            self.backend.start_workload(container_id, verification_config)
        except Exception:
            # Notify event handler of startup failure
            if self.event_handler:
                with self.lock:
                    container_name = self.containers.get(container_id, "unknown")

                # Get additional info for the callback
                labels = self.backend.get_workload_labels(container_id)
                user_id = labels.get("podkit.user_id", "unknown")
                session_id = labels.get("podkit.session_id", "unknown")
                exit_code = self.backend.get_workload_exit_code(container_id)
                logs = self.backend.get_workload_logs(container_id, tail=100)

                self.event_handler.on_container_startup_failed(
                    container_id=container_id,
                    container_name=container_name,
                    user_id=user_id,
                    session_id=session_id,
                    exit_code=exit_code,
                    logs=logs,
                )

            # Re-raise the exception
            raise

    def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """
        Stop a container without removing it.

        Idempotent - no error if container is already stopped.

        Args:
            container_id: ID of the container to stop.
            timeout: Timeout in seconds for graceful stop (default: 10).

        Raises:
            RuntimeError: If container stop fails.
        """
        with self.lock:
            container_name = self.containers.get(container_id, "unknown")

        try:
            self.backend.stop_workload(container_id, timeout=timeout)

            if self.event_handler:
                self.event_handler.on_container_stopped(container_id, container_name)

        except Exception as e:
            if self.event_handler:
                self.event_handler.on_container_stop_failed(container_id, e)
            raise

    def remove_container(self, container_id: str) -> None:
        """
        Remove a container.

        Args:
            container_id: ID of the container to remove.

        Raises:
            RuntimeError: If container removal fails.
        """
        # Get container name before removal (for event handler)
        with self.lock:
            container_name = self.containers.get(container_id, "unknown")

        try:
            # Remove from backend (outside lock - slow operation)
            self.backend.remove_workload(container_id)

            # Remove from tracking (minimize lock time)
            self._untrack_container(container_id)

            # Notify event handler of successful removal
            if self.event_handler:
                self.event_handler.on_container_removed(container_id, container_name)

        except Exception as e:
            # Notify event handler of failure
            if self.event_handler:
                self.event_handler.on_container_removal_failed(container_id, e)
            raise

    def execute_command(
        self,
        container_id: str,
        command: str | list[str],
        working_dir: Path | None = None,
        environment: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> ProcessResult:
        """
        Execute command in container.

        Args:
            container_id: ID of the container.
            command: Command to execute.
            working_dir: Working directory for command execution.
            environment: Environment variables.
            timeout: Timeout in seconds.

        Returns:
            ProcessResult with exit code and output.

        Raises:
            RuntimeError: If command execution fails.
        """
        return self.backend.execute_command(
            workload_id=container_id,
            command=command,
            working_dir=working_dir,
            environment=environment,
            timeout=timeout,
        )

    @abstractmethod
    def write_file(
        self,
        container_id: str,
        container_path: Path | str,
        content: str,
    ) -> Path:
        """
        Write a file for a container.

        Implementation depends on mount strategy:
        - With mounts: Write to host filesystem (persists), looks up user_id/session_id from container labels
        - Without mounts: Write inside container via command (ephemeral)

        Args:
            container_id: ID of the container.
            container_path: Path inside the container where file should appear. Can be:
                           - Relative path (e.g., "file.txt") - auto-prepended with /workspace/
                           - Absolute path (e.g., "/workspace/file.txt") - used as-is
            content: Content to write.

        Returns:
            The normalized container path where the file was written.

        Raises:
            RuntimeError: If file write fails or container labels are missing.
        """
        ...

    def get_container_status(self, container_id: str, refresh: bool = True) -> ContainerStatus:
        """
        Get container status.

        Args:
            container_id: ID of the container.
            refresh: If True, refresh container state before checking status (default: True).
                    If False, use cached state (faster but may be stale).

        Returns:
            Current container status.
        """
        if refresh:
            self.backend.reload_workload(container_id)
        return self.backend.get_workload_status(container_id)

    def to_host_path(
        self,
        container_path: Path,
        user_id: str,
        session_id: str,
        real_host: bool = False,
    ) -> Path:
        """
        Convert a container path to a host path.

        Args:
            container_path: Path inside the container.
            user_id: User identifier.
            session_id: Session identifier.
            real_host: If False, return path valid for current process (default).
                      If True, return path on underlying host that Docker daemon can access.
                      Only makes a difference when running inside a container.

        Returns:
            Path on the host filesystem.

        Raises:
            ValueError: If path conversion fails.
        """
        workspace_path = get_workspace_path(self.workspace_base, user_id, session_id)
        host_path = container_to_host_path(
            container_path=Path(container_path),
            workspace_base=workspace_path,
            container_workspace=Path(CONTAINER_WORKSPACE_PATH),
        )

        # For nested Docker: translate from process-local path to actual host path
        if real_host and self.workspace_base_host != self.workspace_base:
            try:
                relative_path = host_path.relative_to(self.workspace_base)
                host_path = self.workspace_base_host / relative_path
            except ValueError as e:
                raise ValueError(
                    f"Host path must be under workspace_base '{self.workspace_base}', got '{host_path}' instead"
                ) from e

        return host_path

    def to_container_path(
        self,
        host_path: Path,
        user_id: str,
        session_id: str,
    ) -> Path:
        """
        Convert a host path to a container path.

        Args:
            host_path: Path on the host filesystem.
            user_id: User identifier.
            session_id: Session identifier.

        Returns:
            Path inside the container.

        Raises:
            ValueError: If path conversion fails.
        """
        workspace_path = get_workspace_path(self.workspace_base, user_id, session_id)
        return host_to_container_path(
            host_path=Path(host_path),
            workspace_base=workspace_path,
            container_workspace=Path(CONTAINER_WORKSPACE_PATH),
        )

    def discover_existing_containers(self) -> list[dict[str, str]]:
        """Discover existing containers managed by this manager.

        Discovered containers are automatically added to internal tracking.

        Returns:
            List of dicts with keys: container_id, container_name, user_id, session_id, image
        """
        try:
            containers = self.backend.list_workloads(filters={"name": f"{self.container_prefix}-"})

            discovered = []
            for container_info in containers:
                container_id = container_info["id"]
                container_name = container_info["name"]

                labels = self.backend.get_workload_labels(container_id)

                user_id = labels.get("podkit.user_id")
                session_id = labels.get("podkit.session_id")
                image = labels.get("podkit.image")

                if user_id and session_id:
                    # Add to tracking dict so cleanup_all() can find it
                    self._track_container(container_id, container_name)

                    discovered.append(
                        {
                            "container_id": container_id,
                            "container_name": container_name,
                            "user_id": user_id,
                            "session_id": session_id,
                            "image": image,
                        }
                    )

            return discovered
        except Exception:  # pylint: disable=broad-except
            return []

    def cleanup_all(self) -> None:
        """Clean up all tracked containers."""
        # Get snapshot (minimize lock time)
        container_ids = self.get_tracked_containers()

        for container_id in container_ids:
            try:
                self.remove_container(container_id)
            except Exception:  # pylint: disable=broad-except
                # Continue even if one fails
                pass


class SimpleContainerManager(BaseContainerManager):
    """
    Simple implementation of container manager.

    This is used for integration tests and provides a basic mount strategy.
    """

    def get_mounts(
        self,
        user_id: str,
        session_id: str,
        config: ContainerConfig,
    ) -> list[dict[str, Any]]:
        """
        Get volume mounts for test containers.

        Creates a workspace mount for the user's session.

        Note: For nested Docker containers, we need to use paths that Docker
        on the host can access. Uses to_host_path(real_host=True) from base class.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            config: Container configuration.

        Returns:
            List of mount specifications.
        """
        return get_standard_workspace_mounts(
            workspace_base=self.workspace_base,
            user_id=user_id,
            session_id=session_id,
            config=config,
            to_host_path_fn=self.to_host_path,
            volume_name=self.volume_name,
        )

    def start_container(self, container_id: str, config: ContainerConfig | None = None) -> None:
        """
        Start a container with optional startup verification.

        For named volumes, initializes the workspace by creating the session
        directory and symlinking /workspace to it.

        Args:
            container_id: ID of the container to start.
            config: Optional config for verification settings.

        Raises:
            RuntimeError: If container start fails or verification fails.
        """
        # Start the container using base class
        super().start_container(container_id, config)

        # For named volumes, initialize the workspace inside the container
        if self.volume_name:
            labels = self.backend.get_workload_labels(container_id)
            user_id = labels.get("podkit.user_id")
            session_id = labels.get("podkit.session_id")

            if user_id and session_id:
                init_cmd = get_volume_init_command(user_id, session_id)
                result = self.execute_command(container_id, init_cmd)
                if result.exit_code != 0:
                    raise RuntimeError(f"Failed to initialize workspace in named volume: {result.stderr}")

    def write_file(
        self,
        container_id: str,
        container_path: Path | str,
        content: str,
    ) -> Path:
        """
        Write file to mounted filesystem (persists after container removal).

        Looks up user_id and session_id from container labels to determine
        the correct host path for the file.

        Args:
            container_id: ID of the container.
            container_path: Path inside the container. Can be relative or absolute.
            content: Content to write.

        Returns:
            The normalized container path where the file was written.

        Raises:
            RuntimeError: If file write fails or container labels are missing.
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
