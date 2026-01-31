"""Base session manager for managing user sessions."""

import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import TYPE_CHECKING

from podkit.constants import DEFAULT_SESSION_INACTIVITY_TIMEOUT_SECONDS
from podkit.core.manager import BaseContainerManager
from podkit.core.models import ContainerConfig, ContainerStatus, ProcessResult, Session, StartupVerificationConfig
from podkit.utils.paths import get_workspace_path

if TYPE_CHECKING:
    from podkit.core.events import PodkitEventHandler
    from podkit.monitors.health import ContainerHealthMonitor

# Container states that can be recovered by restarting
RECOVERABLE_STATES = {ContainerStatus.CREATING, ContainerStatus.PAUSED, ContainerStatus.EXITED}
# Container states that require removal and recreation
UNRECOVERABLE_STATES = {
    ContainerStatus.RESTARTING,
    ContainerStatus.REMOVING,
    ContainerStatus.DEAD,
    ContainerStatus.ERROR,
}
# STOPPED is intentional closure, not treated as failure


class BaseSessionManager:
    """Base session manager for managing user sessions."""

    def __init__(
        self,
        container_manager: BaseContainerManager,
        default_image: str | None = None,
        logger: logging.Logger | None = None,
        *,
        health_monitor: "ContainerHealthMonitor | None" = None,
        event_handler: "PodkitEventHandler | None" = None,
        session_inactivity_timeout_seconds: int | None = None,
    ):
        """
        Initialize the session manager.

        Args:
            container_manager: Container manager instance.
            default_image: Default Docker image to use for containers.
                          If None, will auto-detect from current container or raise error.
            logger: Optional logger instance. If None, creates a default logger.
                   Accepts any Python logger for flexible integration with external logging systems.
            health_monitor: Optional ContainerHealthMonitor for automatic failure recovery
                          and session cleanup. If provided, monitor will be configured
                          with a handler and started automatically. (keyword-only argument)
            event_handler: Optional PodkitEventHandler instance for lifecycle events.
                          Use for logging, port management, metrics, etc. (keyword-only argument)
            session_inactivity_timeout_seconds: Session inactivity timeout in seconds.
                          If None, uses Session model default (3600 seconds). (keyword-only argument)
        """
        self.container_manager = container_manager
        self.default_image = default_image or self._detect_default_image()
        self.logger = logger or logging.getLogger("podkit.sessions")
        self.sessions: dict[str, Session] = {}
        self.lock = RLock()  # Reentrant lock - allows same thread to acquire multiple times
        self.event_handler = event_handler
        self.session_inactivity_timeout_seconds = session_inactivity_timeout_seconds

        # Optional health monitoring
        self.health_monitor = health_monitor
        if health_monitor:
            # Register single handler that does both:
            # 1. Container failure recovery
            # 2. Session cleanup
            health_monitor.register_handler(self._handle_health_check)

            # Start monitoring
            health_monitor.start()
            self.logger.info(
                f"Container health monitoring enabled "
                f"(interval: {health_monitor.check_interval}s, auto-recovery + session cleanup)"
            )

        self._recover_sessions()

    def _detect_default_image(self) -> str:
        """Detect the default image to use for sandboxes.

        Returns:
            Detected image name.

        Raises:
            RuntimeError: If cannot detect image and none specified.
        """
        detected = self.container_manager.backend.detect_current_image()

        if detected:
            self.logger.warning(f"No default_image specified. Auto-detected from current container: {detected}")
            return detected

        raise RuntimeError(
            "No default_image specified and could not auto-detect "
            "(not running in a container). Please specify an image."
        )

    def _add_session(self, session_key: str, session: Session) -> None:
        """Thread-safe method to add session to dictionary.

        Args:
            session_key: Session key (format: "user_id:session_id").
            session: Session object to add.
        """
        with self.lock:
            self.sessions[session_key] = session

    def _remove_session(self, session_key: str) -> Session | None:
        """Thread-safe method to remove and return session from dictionary.

        Args:
            session_key: Session key (format: "user_id:session_id").

        Returns:
            The removed session, or None if not found.
        """
        with self.lock:
            return self.sessions.pop(session_key, None)

    def _get_all_session_keys(self) -> list[str]:
        """Thread-safe method to get list of all session keys.

        Returns:
            List of session keys currently tracked.
        """
        with self.lock:
            return list(self.sessions.keys())

    def _recover_sessions(self) -> None:
        """Discover and reconnect to existing containers on startup.

        This allows sessions to survive server restarts by reconnecting to
        containers that are still running.
        """
        try:
            discovered = self.container_manager.discover_existing_containers()

            if not discovered:
                self.logger.info("No existing containers to recover")
                return

            self.logger.info(f"Discovering {len(discovered)} existing container(s)...")

            for container_info in discovered:
                try:
                    container_id = container_info["container_id"]
                    user_id = container_info["user_id"]
                    session_id = container_info["session_id"]

                    workspace_path = get_workspace_path(self.container_manager.workspace_base, user_id, session_id)
                    actual_image = container_info.get("image", self.default_image)

                    session = Session(
                        user_id=user_id,
                        session_id=session_id,
                        container_id=container_id,
                        container_name=container_info["container_name"],
                        status=ContainerStatus.RUNNING,
                        config=ContainerConfig(image=actual_image),
                        data_dir=str(workspace_path),
                        session_inactivity_timeout_seconds=self.session_inactivity_timeout_seconds
                        or DEFAULT_SESSION_INACTIVITY_TIMEOUT_SECONDS,
                    )

                    session_key = f"{user_id}:{session_id}"
                    self._add_session(session_key, session)

                    self.logger.info(f"Recovered session: {session_key} (container: {container_id[:12]})")

                except Exception as e:  # pylint: disable=broad-except
                    self.logger.error(f"Failed to recover container {container_info.get('container_id')}: {e}")

            with self.lock:
                session_count = len(self.sessions)
            self.logger.info(f"Session recovery complete. Recovered {session_count} session(s)")

        except Exception as e:  # pylint: disable=broad-except
            self.logger.error(f"Session recovery failed: {e}")

    def create_session(
        self,
        user_id: str,
        session_id: str | None = None,
        config: ContainerConfig | None = None,
    ) -> Session:
        """
        Create a new session.

        Args:
            user_id: ID of the user.
            session_id: ID of the session. If None, a new ID will be generated.
            config: Container configuration. If None, default configuration will be used.

        Returns:
            The created session.

        Raises:
            RuntimeError: If the session creation fails.
        """
        # Hold lock for entire session creation to prevent race conditions
        # Parallel calls with same session_id will wait and return existing session
        with self.lock:
            if session_id is None:
                session_id = str(uuid.uuid4())

            session_key = f"{user_id}:{session_id}"
            if session_key in self.sessions:
                return self.sessions[session_key]

            # Prepare config and paths
            if config is None:
                config = ContainerConfig(image=self.default_image)

            # Note: Config modification happens in container_manager.create_container()
            # via event_handler.on_container_creating() - no need to call it here

            workspace_path = get_workspace_path(self.container_manager.workspace_base, user_id, session_id)
            data_dir = str(workspace_path)

            session = Session(
                user_id=user_id,
                session_id=session_id,
                config=config,
                data_dir=data_dir,
                session_inactivity_timeout_seconds=self.session_inactivity_timeout_seconds
                or DEFAULT_SESSION_INACTIVITY_TIMEOUT_SECONDS,
            )

            container_id = None
            try:
                # Create and start container (with lock - ensures atomic creation)
                container_id, container_name = self.container_manager.create_container(
                    user_id=user_id,
                    session_id=session_id,
                    config=config,
                )

                session.container_id = container_id
                session.container_name = container_name
                session.status = ContainerStatus.RUNNING

                # Start with verification (with lock)
                self.container_manager.start_container(container_id, config)

                # Add to dict
                self.sessions[session_key] = session

                # Notify event handler of successful session creation
                if self.event_handler:
                    self.event_handler.on_session_created(session)

                return session

            except Exception as e:
                # Notify event handler of failure
                if self.event_handler:
                    self.event_handler.on_session_creation_failed(user_id, session_id, e)

                if container_id is not None:
                    try:
                        self.container_manager.remove_container(container_id)
                    except Exception:  # pylint: disable=broad-exception-caught
                        pass

                raise RuntimeError(f"Failed to create session: {e}") from e

    def get_session(self, user_id: str, session_id: str) -> Session | None:
        """
        Get a session.

        Args:
            user_id: ID of the user.
            session_id: ID of the session.

        Returns:
            The session, or None if not found.
        """
        session_key = f"{user_id}:{session_id}"
        with self.lock:
            return self.sessions.get(session_key)

    def get_or_create_session(
        self,
        user_id: str,
        session_id: str,
        config: ContainerConfig | None = None,
    ) -> Session:
        """
        Get an existing session or create a new one.

        This is a convenience method that combines get_session and create_session.
        If a session already exists, it returns the existing session (config is ignored).
        If no session exists, it creates a new one with the provided config.

        Args:
            user_id: ID of the user.
            session_id: ID of the session.
            config: Container configuration for new session. Ignored if session exists.

        Returns:
            The existing or newly created session.
        """
        session = self.get_session(user_id, session_id)
        if session is not None:
            return session
        return self.create_session(user_id, session_id, config)

    def update_session_activity(self, user_id: str, session_id: str) -> None:
        """
        Update the last activity timestamp of a session.

        Args:
            user_id: ID of the user.
            session_id: ID of the session.

        Raises:
            RuntimeError: If the session is not found.
        """
        session_key = f"{user_id}:{session_id}"
        with self.lock:
            session = self.sessions.get(session_key)

        if session is None:
            raise RuntimeError(f"Session not found: {session_key}")

        # Update activity outside lock (safe - doesn't touch dict)
        session.update_activity()

    def _ensure_container_available(self, user_id: str, session_id: str) -> str:
        """Ensure session has a running container, recreate if needed.

        This is called before executing commands or writing files to handle
        sessions marked as ERROR by the health monitor.

        Uses lock for entire operation to prevent race conditions where multiple
        threads might try to recreate the same session's container simultaneously.

        Args:
            user_id: ID of the user.
            session_id: ID of the session.

        Returns:
            Container ID that is ready to use.

        Raises:
            RuntimeError: If container recreation fails.
        """
        with self.lock:
            session_key = f"{user_id}:{session_id}"
            session = self.sessions.get(session_key)
            if session is None:
                raise RuntimeError(f"Session not found: {user_id}:{session_id}")

            # Check if container needs recreation
            if session.container_id is None or session.status == ContainerStatus.ERROR:
                self.logger.info(f"Recreating container for session {user_id}:{session_id}")

                try:
                    # Create new container
                    container_id, container_name = self.container_manager.create_container(
                        user_id=user_id, session_id=session_id, config=session.config
                    )

                    # Update session
                    session.container_id = container_id
                    session.container_name = container_name
                    session.status = ContainerStatus.RUNNING

                    # Clear failure metadata
                    session.metadata.pop("failure_status", None)
                    session.metadata.pop("failure_reason", None)
                    session.metadata.pop("failure_detected_at", None)

                    # Start with verification
                    self.container_manager.start_container(container_id, session.config)

                    self.logger.info(
                        f"Successfully recreated container {container_id[:12]} for session {user_id}:{session_id}"
                    )

                    # Notify event handler of successful recovery
                    if self.event_handler:
                        self.event_handler.on_container_recovered(
                            container_id=container_id,
                            container_name=container_name,
                            user_id=user_id,
                            session_id=session_id,
                        )

                except Exception as e:
                    # Notify event handler of recovery failure
                    if self.event_handler:
                        self.event_handler.on_container_recovery_failed(
                            user_id=user_id,
                            session_id=session_id,
                            reason="recreation_failed",
                            error=e,
                        )
                    raise

            return session.container_id

    def execute_command(
        self,
        user_id: str,
        session_id: str,
        command: str | list[str],
        working_dir: Path | None = None,
        environment: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> ProcessResult:
        """
        Execute a command in a session's container.

        Automatically recreates container if marked as ERROR by health monitor.

        Args:
            user_id: ID of the user.
            session_id: ID of the session.
            command: Command to execute.
            working_dir: Working directory for command execution.
            environment: Environment variables.
            timeout: Timeout in seconds.

        Returns:
            ProcessResult with exit code and output.

        Raises:
            RuntimeError: If the session is not found or command execution fails.
        """
        container_id = self._ensure_container_available(user_id, session_id)

        result = self.container_manager.execute_command(
            container_id=container_id,
            command=command,
            working_dir=working_dir,
            environment=environment,
            timeout=timeout,
        )

        self.update_session_activity(user_id, session_id)
        return result

    def write_file(
        self,
        user_id: str,
        session_id: str,
        container_path: Path | str,
        content: str,
    ) -> Path:
        """
        Write a file to a session's container.

        Implementation depends on container manager's mount strategy:
        - With mounts: File persists on host filesystem
        - Without mounts: File written inside container (ephemeral)

        Args:
            user_id: ID of the user.
            session_id: ID of the session.
            container_path: Path inside the container. Can be:
                - Relative path (e.g., "file.txt") - auto-prepended with /workspace/
                - Absolute path (e.g., "/workspace/file.txt") - used as-is
            content: Content to write.

        Returns:
            The normalized container path where the file was written.

        Raises:
            RuntimeError: If the session is not found or file write fails.
        """
        session = self.get_session(user_id, session_id)
        if session is None:
            raise RuntimeError(f"Session not found: {user_id}:{session_id}")

        # Delegate to container manager - it handles normalization and label lookup
        written_path = self.container_manager.write_file(
            container_id=session.container_id,
            container_path=container_path,
            content=content,
        )

        self.update_session_activity(user_id, session_id)
        return written_path

    def close_session(self, user_id: str, session_id: str) -> None:
        """
        Close a session.

        Args:
            user_id: ID of the user.
            session_id: ID of the session.

        Raises:
            RuntimeError: If the session is not found.
        """
        session_key = f"{user_id}:{session_id}"

        # Remove from dict (minimize lock time)
        session = self._remove_session(session_key)

        if session is None:
            raise RuntimeError(f"Session not found: {session_key}")

        # Notify event handler before closing (container still exists)
        if self.event_handler:
            self.event_handler.on_session_closing(session)

        # Remove container (outside lock - slow operation)
        if session.container_id:
            try:
                self.container_manager.remove_container(session.container_id)
            except Exception:  # pylint: disable=broad-except
                pass

        # Update status (already removed from dict)
        session.status = ContainerStatus.STOPPED

        # Notify event handler after session closed
        if self.event_handler:
            self.event_handler.on_session_closed(session)

    def _handle_health_check(self, container_states: dict[str, dict]) -> None:
        """Handle health check with sophisticated recovery policy.

        Implements smart recovery:
        - RECOVERABLE states (creating, paused, exited): Try restart with verification
        - UNRECOVERABLE states (restarting, removing, dead, error): Remove and mark for recreation

        Args:
            container_states: Dict of {container_id: state_info} for all tracked containers.
        """
        self.logger.debug(f"Health check: {len(container_states)} containers")
        for container_id, state in container_states.items():
            podkit_status = ContainerStatus(state["status"])

            # Skip if running - all good
            if podkit_status == ContainerStatus.RUNNING:
                continue

            # Try recovery for recoverable states
            if podkit_status in RECOVERABLE_STATES:
                recovered = self._attempt_container_recovery(container_id, podkit_status)
                if not recovered:
                    # Recovery failed - remove and mark for recreation
                    self._mark_for_recreation(container_id, state, "restart_failed")
            elif podkit_status in UNRECOVERABLE_STATES:
                # Unrecoverable - remove and mark for recreation immediately
                self._mark_for_recreation(container_id, state, "unrecoverable_state")

        # Periodic session cleanup
        self._cleanup_expired_sessions()

    def _attempt_container_recovery(self, container_id: str, status: ContainerStatus) -> bool:
        """Attempt to recover container by restarting with verification.

        Args:
            container_id: Container ID to recover.
            status: Current container status.

        Returns:
            True if container successfully recovered to RUNNING state.
            False if recovery failed (container should be recreated).
        """
        try:
            self.logger.info(f"Attempting recovery for container {container_id[:12]} (status: {status.value})")

            # Use backend's smart start with verification
            verification_config = StartupVerificationConfig(
                required_consecutive_checks=3,
                check_interval_seconds=1.0,
                max_wait_seconds=5.0,
                capture_logs_on_failure=False,  # We already have logs from health monitor
            )

            # Backend handles start vs unpause automatically
            self.container_manager.backend.start_workload(
                workload_id=container_id, verification_config=verification_config
            )

            self.logger.info(f"Successfully recovered container {container_id[:12]}")

            # Notify event handler of successful recovery
            if self.event_handler:
                with self.lock:
                    container_name = self.container_manager.containers.get(container_id, "unknown")
                    for session in self.sessions.values():
                        if session.container_id == container_id:
                            self.event_handler.on_container_recovered(
                                container_id=container_id,
                                container_name=container_name,
                                user_id=session.user_id,
                                session_id=session.session_id,
                            )

            return True

        except Exception as e:
            self.logger.warning(f"Recovery failed for container {container_id[:12]}: {e}")
            return False

    def _mark_for_recreation(self, container_id: str, state: dict, reason: str) -> None:
        """Mark sessions for recreation and remove bad container.

        Args:
            container_id: Container ID.
            state: Container state info from health monitor.
            reason: Reason for recreation (e.g., "restart_failed", "unrecoverable_state").
        """
        with self.lock:
            # Find sessions using this container
            affected_sessions = []
            for session_key, session in self.sessions.items():
                if session.container_id == container_id:
                    affected_sessions.append((session_key, session))

        # Mark sessions for recreation (outside lock)
        for session_key, session in affected_sessions:
            # Only mark if not already cleared
            if session.container_id is not None:
                session.container_id = None  # Clear so execute_command will recreate
                session.status = ContainerStatus.ERROR
                session.metadata["failure_reason"] = reason
                session.metadata["failure_status"] = state["status"]
                session.metadata["failure_detected_at"] = state["checked_at"]

                self.logger.warning(
                    f"Session {session_key} marked for recreation: {reason} "
                    f"(container: {state['container_name']}, status: {state['status']})"
                )

                # Log container logs at INFO level
                if state.get("logs"):
                    self.logger.info(f"Container {state['container_name']} logs:\n{state['logs']}")

        # Remove the bad container
        if affected_sessions:  # Only if there were affected sessions
            try:
                self.container_manager.remove_container(container_id)
                self.logger.info(f"Removed failed container {container_id[:12]}")
            except Exception as e:
                self.logger.error(f"Failed to remove container {container_id[:12]}: {e}")

    def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions.

        Checks all sessions and closes those that have exceeded their inactivity timeout.
        Called periodically by _handle_health_check().
        """
        session_keys = self._get_all_session_keys()

        for session_key in session_keys:
            try:
                user_id, session_id = session_key.split(":", 1)

                # Get session (thread-safe)
                session = self.get_session(user_id, session_id)
                if not session:
                    continue

                # Check if expired
                if session.is_expired():
                    inactive_seconds = (datetime.now(UTC) - session.last_active_at).total_seconds()
                    self.logger.info(f"Closing expired session: {session_key} (inactive for {inactive_seconds:.0f}s)")

                    # Notify event handler before closing
                    if self.event_handler:
                        self.event_handler.on_session_expired(session)

                    self.close_session(user_id, session_id)

            except Exception as e:
                # Continue with other sessions
                self.logger.warning(f"Failed to cleanup session {session_key}: {e}")

    def cleanup_all(self) -> None:
        """Clean up all sessions and their containers."""
        # Get snapshot (minimize lock time)
        session_keys = self._get_all_session_keys()

        for session_key in session_keys:
            user_id, session_id = session_key.split(":", 1)
            try:
                self.close_session(user_id, session_id)
            except Exception:  # pylint: disable=broad-except
                pass

    def shutdown(self) -> None:
        """Shutdown session manager and stop health monitoring.

        Stops the health monitor if running. Does not close active sessions.
        Call cleanup_all() first if you want to close all sessions.
        """
        if self.health_monitor:
            self.health_monitor.stop()

    def __del__(self) -> None:
        """Ensure health monitor is stopped when session manager is garbage collected."""
        if hasattr(self, "health_monitor") and self.health_monitor:
            self.health_monitor.stop()
