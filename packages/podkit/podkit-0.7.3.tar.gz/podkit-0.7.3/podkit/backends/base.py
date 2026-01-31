"""Abstract base interface for container runtime backends."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from podkit.core.models import ContainerConfig, ContainerStatus, ProcessResult

if TYPE_CHECKING:
    from podkit.core.models import StartupVerificationConfig


class BackendInterface(ABC):
    """
    Abstract interface for container runtime backends.

    This abstraction allows the library to work with different container runtimes
    (Docker, Kubernetes, etc.) without changing business logic.

    Design principle: All container lifecycle operations go through this interface.
    """

    @abstractmethod
    def connect(self) -> None:
        """
        Initialize connection to the backend.

        Raises:
            RuntimeError: If connection fails.
        """
        ...

    @abstractmethod
    def create_workload(
        self,
        name: str,
        config: ContainerConfig,
        mounts: list[dict[str, Any]],
        **kwargs,
    ) -> str:
        """
        Create a workload unit (container, pod, etc.).

        Args:
            name: Unique workload name.
            config: Workload configuration.
            mounts: Volume mount specifications.
            **kwargs: Backend-specific options.

        Returns:
            Workload ID (container ID, pod name, etc.).

        Raises:
            RuntimeError: If creation fails.
        """
        ...

    @abstractmethod
    def start_workload(self, workload_id: str, verification_config: "StartupVerificationConfig | None" = None) -> None:
        """
        Start a workload with optional startup verification.

        Backend should handle different workload states appropriately
        (e.g., unpause if paused, start if stopped).

        Args:
            workload_id: ID of the workload to start.
            verification_config: Optional verification to ensure sustained running state.
                               If None, no verification is performed.

        Raises:
            RuntimeError: If start or verification fails.
        """
        ...

    @abstractmethod
    def stop_workload(self, workload_id: str, timeout: int = 10) -> None:
        """
        Stop a workload without removing it.

        Stops the workload gracefully with the specified timeout.
        The workload remains in the system (stopped state) and can be started again.

        Args:
            workload_id: ID of the workload to stop.
            timeout: Timeout in seconds for graceful stop (default: 10).

        Raises:
            RuntimeError: If stop fails.
        """
        ...

    @abstractmethod
    def execute_command(
        self,
        workload_id: str,
        command: str | list[str],
        working_dir: Path | None = None,
        environment: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> ProcessResult:
        """
        Execute command in workload.

        Args:
            workload_id: ID of the workload.
            command: Command to execute (string or list of strings).
            working_dir: Working directory for command execution.
            environment: Environment variables for the command.
            timeout: Timeout in seconds.

        Returns:
            ProcessResult with exit code and output.

        Raises:
            RuntimeError: If execution fails.
        """
        ...

    @abstractmethod
    def remove_workload(self, workload_id: str, force: bool = True) -> None:
        """
        Remove a workload.

        Args:
            workload_id: ID of the workload to remove.
            force: Force removal even if running.

        Raises:
            RuntimeError: If removal fails.
        """
        ...

    @abstractmethod
    def get_workload_status(self, workload_id: str) -> ContainerStatus:
        """
        Get workload status.

        Args:
            workload_id: ID of the workload.

        Returns:
            Current status.

        Raises:
            RuntimeError: If status check fails.
        """
        ...

    @abstractmethod
    def list_workloads(self, filters: dict[str, str] | None = None) -> list[dict]:
        """
        List workloads matching filters.

        Args:
            filters: Filter criteria (e.g., {"name": "prefix-*"}).

        Returns:
            List of workload information dicts.

        Raises:
            RuntimeError: If listing fails.
        """
        ...

    @abstractmethod
    def get_workload_labels(self, workload_id: str) -> dict[str, str]:
        """
        Get labels/metadata for a workload.

        Args:
            workload_id: ID of the workload.

        Returns:
            Dictionary of labels.

        Raises:
            RuntimeError: If retrieval fails.
        """
        ...

    @abstractmethod
    def reload_workload(self, workload_id: str) -> None:
        """
        Refresh workload state from backend.

        This ensures status checks reflect the most current state.

        Args:
            workload_id: ID of the workload to refresh.

        Raises:
            RuntimeError: If refresh fails.
        """
        ...

    @abstractmethod
    def get_workload_logs(self, workload_id: str, tail: int = 100) -> str:
        """
        Get logs from a workload.

        Args:
            workload_id: ID of the workload.
            tail: Number of lines to retrieve from end of logs.

        Returns:
            Log output as string.

        Raises:
            RuntimeError: If log retrieval fails.
        """
        ...

    @abstractmethod
    def get_workload_exit_code(self, workload_id: str) -> int | None:
        """
        Get exit code of a stopped workload.

        Args:
            workload_id: ID of the workload.

        Returns:
            Exit code if available, None otherwise.

        Raises:
            RuntimeError: If retrieval fails.
        """
        ...

    @abstractmethod
    def get_accessible_ports(self, workload_id: str) -> dict[int, int]:
        """
        Get accessible port mappings for a workload.

        Returns mapping of container_port → externally_accessible_port.

        - Docker: container_port → host_port (accessible via localhost:host_port)
        - Kubernetes: container_port → nodePort or service_port
        - Podman: container_port → host_port

        The accessible_port is what external clients use to connect to
        the container's listening port.

        Args:
            workload_id: ID of the workload.

        Returns:
            Dict mapping container port to externally accessible port.
            Empty dict if no ports exposed or feature not supported.

        Example:
            {80: 8080, 443: 8443}
            # Container listens on 80/443, accessible via 8080/8443

        Raises:
            RuntimeError: If retrieval fails.
        """
        ...

    @abstractmethod
    def detect_current_image(self) -> str | None:
        """
        Detect container image of the current process.

        Useful for auto-detecting default image when running inside a container.

        Returns:
            Image name/tag if running in container and detection succeeds.
            None if not running in container or detection fails.
        """
        ...
