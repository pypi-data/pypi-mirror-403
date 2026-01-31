"""Unified event handler for podkit lifecycle events.

This module provides a single interface for receiving all lifecycle events
from podkit components (container manager, session manager, health monitor,
process manager).
"""

from abc import ABC
from typing import Any

from podkit.core.models import ContainerConfig, Session


class PodkitEventHandler(ABC):
    """Abstract base class for podkit lifecycle event handling.

    Implement this class to receive notifications about lifecycle events
    from all podkit components. All methods have default no-op implementations,
    so you only need to override the ones you care about.

    Event handler is passed to components that emit events:
    - BaseContainerManager: container lifecycle events
    - BaseSessionManager: session lifecycle events
    - ContainerHealthMonitor: health check events
    - ProcessManager: background process events

    Example:
        >>> class MyEventHandler(PodkitEventHandler):
        ...     def __init__(self, logger):
        ...         self.logger = logger
        ...
        ...     def on_container_created(self, container_id, user_id, session_id, config):
        ...         self.logger.info(f"Container created: {container_id}")
        ...
        ...     def on_session_closed(self, session):
        ...         self.logger.info(f"Session closed: {session.session_id}")
        ...
        >>> handler = MyEventHandler(logger)
        >>> container_manager = SimpleContainerManager(..., event_handler=handler)
        >>> session_manager = BaseSessionManager(..., event_handler=handler)
    """

    # =========================================================================
    # Container Lifecycle Events (from BaseContainerManager)
    # =========================================================================

    def on_container_creating(
        self,
        user_id: str,
        session_id: str,
        config: ContainerConfig,
    ) -> ContainerConfig:
        """Called before a container is created.

        Use this to modify the container configuration before creation
        (e.g., allocate ports, add environment variables).

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            config: Container configuration (can be modified).

        Returns:
            The (possibly modified) container configuration.
        """
        return config

    def on_container_created(
        self,
        container_id: str,
        container_name: str,
        user_id: str,
        session_id: str,
        config: ContainerConfig,
    ) -> None:
        """Called after a container is successfully created and started.

        Args:
            container_id: ID of the created container.
            container_name: Name of the container.
            user_id: User identifier.
            session_id: Session identifier.
            config: Container configuration used.
        """

    def on_container_creation_failed(
        self,
        user_id: str,
        session_id: str,
        config: ContainerConfig,
        error: Exception,
    ) -> None:
        """Called when container creation fails.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            config: Container configuration that was attempted.
            error: The exception that caused the failure.
        """

    def on_container_startup_failed(
        self,
        container_id: str,
        container_name: str,
        user_id: str,
        session_id: str,
        exit_code: int | None,
        logs: str,
    ) -> None:
        """Called when container starts but fails startup verification.

        Args:
            container_id: ID of the container.
            container_name: Name of the container.
            user_id: User identifier.
            session_id: Session identifier.
            exit_code: Container exit code if available.
            logs: Last lines of container logs.
        """

    def on_container_stopped(
        self,
        container_id: str,
        container_name: str,
    ) -> None:
        """Called after a container is successfully stopped.

        Args:
            container_id: ID of the stopped container.
            container_name: Name of the container.
        """

    def on_container_stop_failed(
        self,
        container_id: str,
        error: Exception,
    ) -> None:
        """Called when container stop fails.

        Args:
            container_id: ID of the container.
            error: The exception that caused the failure.
        """

    def on_container_removed(
        self,
        container_id: str,
        container_name: str,
    ) -> None:
        """Called after a container is successfully removed.

        Args:
            container_id: ID of the removed container.
            container_name: Name of the container.
        """

    def on_container_removal_failed(
        self,
        container_id: str,
        error: Exception,
    ) -> None:
        """Called when container removal fails.

        Args:
            container_id: ID of the container.
            error: The exception that caused the failure.
        """

    # =========================================================================
    # Session Lifecycle Events (from BaseSessionManager)
    # =========================================================================

    def on_session_created(
        self,
        session: Session,
    ) -> None:
        """Called after a session is successfully created.

        Args:
            session: The created session.
        """

    def on_session_creation_failed(
        self,
        user_id: str,
        session_id: str,
        error: Exception,
    ) -> None:
        """Called when session creation fails.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            error: The exception that caused the failure.
        """

    def on_session_closing(
        self,
        session: Session,
    ) -> None:
        """Called before a session is closed.

        Use this for cleanup tasks that need the container still running.

        Args:
            session: The session being closed.
        """

    def on_session_closed(
        self,
        session: Session,
    ) -> None:
        """Called after a session is closed and container removed.

        Args:
            session: The closed session.
        """

    def on_session_expired(
        self,
        session: Session,
    ) -> None:
        """Called when a session is closed due to inactivity timeout.

        Args:
            session: The expired session.
        """

    # =========================================================================
    # Health Monitor Events (from ContainerHealthMonitor)
    # =========================================================================

    def on_container_health_check_failed(
        self,
        container_id: str,
        container_name: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Called when health monitor detects a container failure.

        Args:
            container_id: ID of the failed container.
            container_name: Name of the container.
            reason: Reason for failure (e.g., "external_stop", "unhealthy").
            details: Additional details about the failure.
        """

    def on_container_recovered(
        self,
        container_id: str,
        container_name: str,
        user_id: str,
        session_id: str,
    ) -> None:
        """Called when a container is successfully recovered after failure.

        Args:
            container_id: ID of the new container.
            container_name: Name of the container.
            user_id: User identifier.
            session_id: Session identifier.
        """

    def on_container_recovery_failed(
        self,
        user_id: str,
        session_id: str,
        reason: str,
        error: Exception | None = None,
    ) -> None:
        """Called when container recovery fails.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            reason: Reason for failure (e.g., "restart_failed", "recreation_failed").
            error: The exception if available.
        """

    # =========================================================================
    # Orphan Cleaner Events (from OrphanContainerCleaner)
    # =========================================================================

    def on_orphan_container_removed(
        self,
        container_id: str,
        container_name: str,
        age_seconds: float,
    ) -> None:
        """Called when an orphaned container is automatically removed.

        Args:
            container_id: ID of the removed container.
            container_name: Name of the container.
            age_seconds: Age of the container in seconds.
        """

    # =========================================================================
    # Process Events (from ProcessManager)
    # =========================================================================

    def on_process_started(
        self,
        process_id: str,
        container_id: str,
        user_id: str,
        session_id: str,
        command: str,
        pid: int | None,
    ) -> None:
        """Called when a background process is started.

        Args:
            process_id: Unique process identifier.
            container_id: ID of the container.
            user_id: User identifier.
            session_id: Session identifier.
            command: The command that was started.
            pid: Process ID inside container.
        """

    def on_process_stopped(
        self,
        process_id: str,
        container_id: str,
        user_id: str,
        session_id: str,
        exit_code: int | None,
    ) -> None:
        """Called when a background process is stopped.

        Args:
            process_id: Unique process identifier.
            container_id: ID of the container.
            user_id: User identifier.
            session_id: Session identifier.
            exit_code: Process exit code if available.
        """

    def on_process_failed(
        self,
        process_id: str,
        container_id: str,
        user_id: str,
        session_id: str,
        error: str,
    ) -> None:
        """Called when a background process fails.

        Args:
            process_id: Unique process identifier.
            container_id: ID of the container.
            user_id: User identifier.
            session_id: Session identifier.
            error: Error description.
        """
