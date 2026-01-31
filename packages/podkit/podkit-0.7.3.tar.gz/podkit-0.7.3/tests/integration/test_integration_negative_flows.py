"""Integration tests for podkit library negative flows and error scenarios.

This test validates error handling and failure scenarios:
1. Read-only volume mount restrictions
2. Invalid operations and expected failures
3. Permission and access control

NOTE: Tests are numbered to ensure execution order.
"""

import shutil
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from podkit.core.events import PodkitEventHandler
from podkit.core.manager import SimpleContainerManager
from podkit.core.models import ContainerConfig, ContainerStatus, Mount, ProcessResult
from podkit.core.session import BaseSessionManager
from podkit.monitors.health import ContainerHealthMonitor
from podkit.monitors.orphans import OrphanContainerCleaner
from tests.integration.conftest import create_managers_with_event_handler


def assert_read_only_error(result: ProcessResult):
    """Assert that read-only volumes prevent write operations."""
    assert result.exit_code == 1
    assert "read-only file system" in result.stderr.lower() or "read-only file system" in result.stdout.lower()


@pytest.mark.integration
class TestPodkitIntegrationNegativeFlows:
    """Integration tests for error handling and failure scenarios."""

    def test_01_readonly_volume_prevents_writes(self, backend, test_config, docker_client, test_user, test_session):
        """Test that read-only volumes prevent write operations.

        Verifies:
        1. Files in read-only volumes can be read
        2. Attempts to write to existing files in read-only volumes fail
        3. Attempts to create new files in read-only volumes fail
        4. Attempts to delete files in read-only volumes fail
        5. Docker mount is actually marked as read-only

        Note: Uses subdirectories of the shared test_workspace for Docker-in-Docker compatibility.
        """
        manager = SimpleContainerManager(
            backend=backend,
            container_prefix=f"{test_config['test_prefix']}-readonly-vol",
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        session_manager = BaseSessionManager(
            default_image=test_config["test_image"],
            container_manager=manager,
        )

        container_path = test_config["test_workspace"] / "readonly_vol" / test_session
        container_path.mkdir(parents=True, exist_ok=True)

        # For Docker-in-Docker, use host path for volume mount
        host_path = test_config["test_workspace_host"] / "readonly_vol" / test_session

        try:
            test_file = container_path / "readonly_file.txt"
            test_file.write_text("This file is read-only")

            # Create config with read-only volume
            config_with_readonly_volume = ContainerConfig(
                container_lifetime_seconds=3000,
                image=test_config["test_image"],
                volumes=[
                    Mount(type="bind", source=host_path, target=Path("/readonly"), read_only=True),
                ],
            )

            session = session_manager.create_session(
                user_id=test_user,
                session_id=test_session,
                config=config_with_readonly_volume,
            )
            container = docker_client.containers.get(session.container_id)
            assert container.status == "running"

            # Test 1: Verify file can be read from read-only volume
            result_read = session_manager.execute_command(
                user_id=test_user,
                session_id=test_session,
                command=["cat", "/readonly/readonly_file.txt"],
            )
            assert result_read.exit_code == 0
            assert "This file is read-only" in result_read.stdout

            # Test 2: Verify writing to existing file in read-only volume fails
            result_write = session_manager.execute_command(
                user_id=test_user,
                session_id=test_session,
                command=["sh", "-c", "echo 'new content' > /readonly/readonly_file.txt"],
            )
            assert_read_only_error(result_write)

            # Test 3: Verify creating new file in read-only volume fails
            result_create = session_manager.execute_command(
                user_id=test_user,
                session_id=test_session,
                command=["sh", "-c", "echo 'new file' > /readonly/new_file.txt"],
            )
            assert_read_only_error(result_create)

            # Test 4: Verify deleting file in read-only volume fails
            result_delete = session_manager.execute_command(
                user_id=test_user,
                session_id=test_session,
                command=["rm", "/readonly/readonly_file.txt"],
            )
            assert_read_only_error(result_delete)

            # Test 5: Verify original file still exists and unchanged
            result_verify = session_manager.execute_command(
                user_id=test_user,
                session_id=test_session,
                command=["cat", "/readonly/readonly_file.txt"],
            )
            assert result_verify.exit_code == 0
            assert "This file is read-only" in result_verify.stdout

            # Test 6: Verify the mount is actually marked as read-only in Docker
            container_attrs = container.attrs
            mounts = container_attrs.get("Mounts", [])
            readonly_mount = next((m for m in mounts if m.get("Destination") == "/readonly"), None)
            assert readonly_mount is not None, "Read-only mount not found"
            assert readonly_mount.get("RW") is False, "Mount should be marked as read-only (RW=False)"

        finally:
            session_manager.close_session(test_user, test_session)
            manager.cleanup_all()
            if container_path.parent.exists():
                shutil.rmtree(container_path.parent)

    def test_02_health_monitor_recovery_and_cleanup(self, backend, test_config, docker_client, test_user, test_session):
        """Test health monitor detects failures, attempts recovery, and handles cleanup.

        Verifies:
        1. Health monitor detects externally stopped containers
        2. RECOVERABLE states (exited): Try restart with verification
        3. If restart succeeds: Keep container
        4. UNRECOVERABLE states (dead): Remove and mark for recreation
        5. execute_command auto-recreates when needed
        6. Expired sessions auto-cleaned up
        """
        manager = SimpleContainerManager(
            backend=backend,
            container_prefix=f"{test_config['test_prefix']}-health",
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        # Create health monitor with fast checks
        health_monitor = ContainerHealthMonitor(
            container_manager=manager,
            check_interval=2,  # Fast checks for testing
            log_lines=50,
        )

        session_manager = BaseSessionManager(
            default_image=test_config["test_image"],
            container_manager=manager,
            health_monitor=health_monitor,  # Enable monitoring
        )

        try:
            # Test 1: Create session and verify it works
            config = ContainerConfig(
                image=test_config["test_image"],
                container_lifetime_seconds=3000,
            )
            session = session_manager.create_session(test_user, test_session, config)
            result1 = session_manager.execute_command(test_user, test_session, ["echo", "before_stop"])
            assert result1.exit_code == 0
            assert "before_stop" in result1.stdout

            original_container_id = session.container_id
            assert original_container_id is not None

            # Test 2: Stop container externally (simulates failure)
            container = docker_client.containers.get(original_container_id)
            container.stop()

            # Wait for health monitor to detect and attempt recovery
            time.sleep(4)  # 2s check interval + buffer

            # Test 3: Verify recovery was attempted (container should be restarted)
            container.reload()
            # Container should be running again (recovery successful for EXITED state)
            assert container.status == "running"

            # Session should still have same container (restart succeeded)
            session = session_manager.get_session(test_user, test_session)
            assert session.container_id == original_container_id

            # Test 4: Execute command should work (container was recovered)
            result2 = session_manager.execute_command(test_user, test_session, ["echo", "after_recovery"])
            assert result2.exit_code == 0
            assert "after_recovery" in result2.stdout

            # Test 5: Test UNRECOVERABLE state - kill container (makes it "dead")
            container.kill()
            time.sleep(4)  # Wait for detection

            # Health monitor should remove UNRECOVERABLE container and mark session
            session_before_recreation = session_manager.get_session(test_user, test_session)
            # Session should be marked ERROR with cleared container_id
            assert (
                session_before_recreation.container_id is None
                or session_before_recreation.status == ContainerStatus.ERROR
            )
            # Verify failure metadata captured (BEFORE recreation clears it)
            assert (
                "failure_status" in session_before_recreation.metadata
                or "failure_reason" in session_before_recreation.metadata
            )

            # Test 6: execute_command should auto-recreate
            result3 = session_manager.execute_command(test_user, test_session, ["echo", "recreated"])
            assert result3.exit_code == 0
            assert "recreated" in result3.stdout

            # Verify NEW container was created (different ID)
            session_after_recreation = session_manager.get_session(test_user, test_session)
            new_container_id = session_after_recreation.container_id
            assert new_container_id is not None
            assert new_container_id != original_container_id  # Must be different!
            # Metadata cleared after successful recreation
            assert session_after_recreation.status == ContainerStatus.RUNNING

            # Test 7: Session cleanup - create session and make it expire
            short_session_id = f"{test_session}_short"
            session2 = session_manager.create_session(test_user, short_session_id)
            assert session2 is not None

            # Get the session from manager's dict to modify it
            session2_from_dict = session_manager.get_session(test_user, short_session_id)
            assert session2_from_dict is not None

            # Manually set short timeout and old last_active_at to simulate expiration
            session2_from_dict.session_inactivity_timeout_seconds = 2  # 2 second timeout
            session2_from_dict.last_active_at = datetime.now(UTC) - timedelta(seconds=5)  # 5 seconds ago

            # Verify session is expired
            assert session2_from_dict.is_expired()

            # Wait for monitor check (multiple cycles to be safe)
            time.sleep(6)  # 3x check interval to ensure cleanup runs

            # Verify session cleaned up
            session2_after = session_manager.get_session(test_user, short_session_id)
            assert session2_after is None  # Should be auto-removed

        finally:
            health_monitor.stop()
            session_manager.cleanup_all()
            manager.cleanup_all()

    def test_03_orphan_cleaner_only_removes_matching_prefix(self, backend, test_config, docker_client):
        """Test that OrphanContainerCleaner ONLY removes containers with matching prefix.

        THIS IS A CRITICAL SAFETY TEST.

        Verifies:
        1. Cleaner removes stopped containers with matching prefix
        2. Cleaner does NOT touch containers with different prefix
        3. Cleaner does NOT touch running containers (even with matching prefix)

        If this test fails, the cleaner could accidentally kill production containers!
        """
        # Use two distinct prefixes
        target_prefix = f"{test_config['test_prefix']}-orphan-target"
        safe_prefix = f"{test_config['test_prefix']}-orphan-safe"

        # Create two managers with different prefixes
        target_manager = SimpleContainerManager(
            backend=backend,
            container_prefix=target_prefix,
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        safe_manager = SimpleContainerManager(
            backend=backend,
            container_prefix=safe_prefix,
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        # Track cleanup events via event handler
        cleanup_events = []

        class TestOrphanHandler(PodkitEventHandler):
            """Event handler to track orphan cleanup events."""

            def on_orphan_container_removed(self, container_id, container_name, age_seconds):
                cleanup_events.append(
                    {
                        "container_id": container_id,
                        "container_name": container_name,
                        "age_seconds": age_seconds,
                    }
                )

        orphan_handler = TestOrphanHandler()

        try:
            # Create containers with TARGET prefix (will be cleaned)
            config = ContainerConfig(
                image=test_config["test_image"],
                entrypoint=[],  # Sleep infinity
            )

            target_container_id, _target_container_name = target_manager.create_container(
                user_id="orphan-test",
                session_id="target1",
                config=config,
            )
            target_manager.start_container(target_container_id, config)

            # Create containers with SAFE prefix (must NOT be cleaned)
            safe_container_id, _safe_container_name = safe_manager.create_container(
                user_id="orphan-test",
                session_id="safe1",
                config=config,
            )
            safe_manager.start_container(safe_container_id, config)

            # Verify both containers are running
            assert target_manager.get_container_status(target_container_id) == ContainerStatus.RUNNING
            assert safe_manager.get_container_status(safe_container_id) == ContainerStatus.RUNNING

            # Stop both containers (simulating orphaned state)
            backend.stop_workload(target_container_id, timeout=1)
            backend.stop_workload(safe_container_id, timeout=1)

            # Verify both are stopped
            target_status = target_manager.get_container_status(target_container_id)
            safe_status = safe_manager.get_container_status(safe_container_id)
            assert target_status in (ContainerStatus.EXITED, ContainerStatus.STOPPED)
            assert safe_status in (ContainerStatus.EXITED, ContainerStatus.STOPPED)

            # Create cleaner that ONLY targets the target_prefix
            cleaner = OrphanContainerCleaner(
                backend=backend,
                container_prefix=target_prefix,
                check_interval=1,  # Fast for testing
                max_age_seconds=0,  # Remove immediately (for testing)
                event_handler=orphan_handler,
            )

            # Run ONE cleanup cycle manually (don't start the thread)
            cleaner._cleanup_orphans()  # pylint: disable=protected-access

            # CRITICAL ASSERTIONS:

            # 1. Target container should be removed
            assert len(cleanup_events) == 1, f"Should clean exactly 1 container, got {len(cleanup_events)}"
            assert target_prefix in cleanup_events[0]["container_name"], (
                f"Cleaned container should have target prefix, got {cleanup_events[0]['container_name']}"
            )

            # 2. Verify target container is actually gone
            target_containers = backend.list_workloads(filters={"name": f"^{target_prefix}-"})
            assert len(target_containers) == 0, (
                f"Target container should be removed, but found: {[c['name'] for c in target_containers]}"
            )

            # 3. CRITICAL: Safe container must still exist!
            safe_containers = backend.list_workloads(filters={"name": f"^{safe_prefix}-"})
            assert len(safe_containers) == 1, (
                f"Safe container MUST still exist! Found: {len(safe_containers)} containers"
            )
            assert safe_containers[0]["id"] == safe_container_id, "Safe container ID should match"

            # 4. Verify safe container was NOT in cleanup events
            for event in cleanup_events:
                assert safe_prefix not in event["container_name"], (
                    f"CRITICAL: Safe container was cleaned! This would kill production! Event: {event}"
                )

        finally:
            # Cleanup both managers
            try:
                target_manager.cleanup_all()
            except Exception:
                pass
            try:
                safe_manager.cleanup_all()
            except Exception:
                pass

    def test_04_orphan_cleaner_does_not_remove_running_containers(self, backend, test_config, docker_client):
        """Test that OrphanContainerCleaner does NOT remove running containers.

        Even if a container matches the prefix, it should not be removed if running.
        """
        prefix = f"{test_config['test_prefix']}-orphan-running"

        manager = SimpleContainerManager(
            backend=backend,
            container_prefix=prefix,
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        cleanup_events = []

        class TestOrphanHandler(PodkitEventHandler):
            """Event handler to track orphan cleanup events."""

            def on_orphan_container_removed(self, container_id, container_name, age_seconds):
                cleanup_events.append(container_name)

        orphan_handler = TestOrphanHandler()

        try:
            # Create and start a container (keep it running)
            config = ContainerConfig(
                image=test_config["test_image"],
                entrypoint=[],  # Sleep infinity
            )

            container_id, _container_name = manager.create_container(
                user_id="orphan-test",
                session_id="running1",
                config=config,
            )
            manager.start_container(container_id, config)

            # Verify it's running
            assert manager.get_container_status(container_id) == ContainerStatus.RUNNING

            # Create cleaner with max_age_seconds=0 (would remove immediately if stopped)
            cleaner = OrphanContainerCleaner(
                backend=backend,
                container_prefix=prefix,
                check_interval=1,
                max_age_seconds=0,
                event_handler=orphan_handler,
            )

            # Run cleanup
            cleaner._cleanup_orphans()  # pylint: disable=protected-access

            # Container should NOT be cleaned (it's running)
            assert len(cleanup_events) == 0, f"Running container should NOT be cleaned, but got: {cleanup_events}"

            # Container should still exist and be running
            assert manager.get_container_status(container_id) == ContainerStatus.RUNNING

        finally:
            manager.cleanup_all()

    def test_05_orphan_cleaner_thread_lifecycle(self, backend, test_config, docker_client):
        """Test OrphanContainerCleaner background thread behavior.

        Verifies:
        1. start() launches background thread that runs cleanup periodically
        2. Cleanup happens automatically without manual _cleanup_orphans() call
        3. stop() terminates the thread
        4. Calling start()/stop() multiple times is safe (idempotent)
        """
        prefix = f"{test_config['test_prefix']}-orphan-thread"

        manager = SimpleContainerManager(
            backend=backend,
            container_prefix=prefix,
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        cleanup_events = []

        class TestOrphanHandler(PodkitEventHandler):
            """Event handler to track orphan cleanup events."""

            def on_orphan_container_removed(self, container_id, container_name, age_seconds):
                cleanup_events.append(
                    {
                        "container_id": container_id,
                        "container_name": container_name,
                    }
                )

        orphan_handler = TestOrphanHandler()
        cleaner = None

        try:
            # Create and stop a container (orphan candidate)
            config = ContainerConfig(
                image=test_config["test_image"],
                entrypoint=[],
            )

            container_id, _container_name = manager.create_container(
                user_id="orphan-thread-test",
                session_id="test1",
                config=config,
            )
            manager.start_container(container_id, config)

            # Stop the container to make it an orphan candidate
            backend.stop_workload(container_id, timeout=1)

            # Verify container is stopped
            status = manager.get_container_status(container_id)
            assert status in (ContainerStatus.EXITED, ContainerStatus.STOPPED), (
                f"Container should be stopped, got {status}"
            )

            # Create cleaner with short interval for testing
            cleaner = OrphanContainerCleaner(
                backend=backend,
                container_prefix=prefix,
                check_interval=1,  # 1 second interval
                max_age_seconds=0,  # Remove immediately
                event_handler=orphan_handler,
            )

            # Verify thread is not running yet
            assert not cleaner.running, "Cleaner should not be running before start()"

            # ==========================================
            # Part 1: Test start() launches thread
            # ==========================================
            cleaner.start()
            assert cleaner.running, "Cleaner should be running after start()"

            # Wait for automatic cleanup (thread should run within interval)
            # Give it 3 seconds (3x the interval) to be safe
            time.sleep(3)

            # Verify container was automatically cleaned (without manual _cleanup_orphans())
            assert len(cleanup_events) >= 1, (
                f"Thread should have automatically cleaned orphan container, but got {len(cleanup_events)} events"
            )
            assert cleanup_events[0]["container_id"] == container_id, "Cleaned container ID should match"

            # Verify container is actually gone
            containers = backend.list_workloads(filters={"name": f"^{prefix}-"})
            assert len(containers) == 0, (
                f"Container should be removed by thread, but found: {[c['name'] for c in containers]}"
            )

            # ==========================================
            # Part 2: Test stop() terminates thread
            # ==========================================
            cleaner.stop()
            assert not cleaner.running, "Cleaner should not be running after stop()"

            # ==========================================
            # Part 3: Test idempotency
            # ==========================================
            # start() twice should be safe
            cleaner.start()
            cleaner.start()  # Second call should be no-op
            assert cleaner.running, "Cleaner should still be running"

            # stop() twice should be safe
            cleaner.stop()
            cleaner.stop()  # Second call should be no-op
            assert not cleaner.running, "Cleaner should be stopped"

        finally:
            if cleaner and cleaner.running:
                cleaner.stop()
            manager.cleanup_all()

    def test_06_event_handler_failure_callbacks(self, backend, test_config):
        """Test that failure event handler callbacks are invoked correctly.

        Verifies:
        1. on_container_creation_failed() called when container creation fails
        2. on_session_creation_failed() called when session creation fails

        Note: Several other failure callbacks are defined in PodkitEventHandler but
        not yet implemented in the codebase (on_container_startup_failed,
        on_session_expired, on_container_stopped, etc.). This test covers the
        callbacks that ARE currently implemented.
        """
        # Track events
        events = []

        class TestEventHandler(PodkitEventHandler):
            """Event handler for testing failure callbacks."""

            def on_container_creation_failed(self, user_id, session_id, config, error):
                events.append(
                    {
                        "type": "container_creation_failed",
                        "user_id": user_id,
                        "session_id": session_id,
                        "error": str(error),
                    }
                )

            def on_session_creation_failed(self, user_id, session_id, error):
                events.append(
                    {
                        "type": "session_creation_failed",
                        "user_id": user_id,
                        "session_id": session_id,
                        "error": str(error),
                    }
                )

        event_handler = TestEventHandler()
        container_manager, session_manager = create_managers_with_event_handler(
            backend, test_config, "event-failures", event_handler
        )

        try:
            # ==========================================
            # Test: Invalid image triggers failure callbacks
            # ==========================================
            invalid_config = ContainerConfig(
                image="nonexistent-image-that-does-not-exist:invalid-tag-12345",
                entrypoint=[],
            )

            # Attempt to create session with invalid image - should fail
            creation_failed = False
            try:
                session_manager.create_session(
                    user_id="failure-test-user",
                    session_id="failure-test-session",
                    config=invalid_config,
                )
            except Exception:
                creation_failed = True

            # Verify creation failed
            assert creation_failed, "Session creation should have failed with invalid image"

            # Verify failure callbacks were invoked
            assert len(events) >= 1, f"At least one failure callback should be invoked, got {len(events)}"

            # Check for container_creation_failed event
            container_failures = [e for e in events if e["type"] == "container_creation_failed"]
            assert len(container_failures) >= 1, f"on_container_creation_failed should be called. Events: {events}"

            container_failure = container_failures[0]
            assert container_failure["user_id"] == "failure-test-user"
            assert container_failure["session_id"] == "failure-test-session"
            assert (
                "nonexistent-image" in container_failure["error"].lower()
                or "not found" in container_failure["error"].lower()
            ), f"Error should mention the invalid image. Got: {container_failure['error']}"

            # Check for session_creation_failed event
            session_failures = [e for e in events if e["type"] == "session_creation_failed"]
            assert len(session_failures) >= 1, f"on_session_creation_failed should be called. Events: {events}"

            session_failure = session_failures[0]
            assert session_failure["user_id"] == "failure-test-user"
            assert session_failure["session_id"] == "failure-test-session"

        finally:
            container_manager.cleanup_all()
