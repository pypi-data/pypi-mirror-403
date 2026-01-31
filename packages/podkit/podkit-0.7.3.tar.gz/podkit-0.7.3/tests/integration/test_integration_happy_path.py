"""Integration test for podkit library happy path workflow.

This test validates the entire workflow using ONE container for basic tests,
then creates separate containers for feature-specific scenarios.

NOTE: Tests are numbered to ensure execution order.
"""

import shutil
import time
from pathlib import Path

import docker
import pytest

from podkit import PodkitEventHandler, PortPool, get_docker_session, reset_lifecycle_cache, run_in_docker
from podkit.core.manager import SimpleContainerManager
from podkit.core.models import ContainerConfig, ContainerStatus, Mount, StartupVerificationConfig
from podkit.core.session import BaseSessionManager
from podkit.processes import ProcessManager, ProcessStatus
from podkit.utils.network import get_parent_container_networks
from tests.integration.conftest import create_managers_with_event_handler


@pytest.mark.integration
class TestPodkitIntegrationHappyPath:
    """Integration test for complete podkit library workflow."""

    @pytest.fixture(scope="class")
    def shared_session(self, session_manager, test_user, test_session):
        """Create one session for all tests in this class."""
        session = session_manager.create_session(
            user_id=test_user,
            session_id=test_session,
        )
        yield session
        # Cleanup after all tests (only if session still exists)
        if session_manager.get_session(test_user, test_session):
            session_manager.close_session(test_user, test_session)

    def test_01_basic_operations(self, shared_session, session_manager, container_manager, test_user, test_session):
        """Test basic container operations: command execution and file I/O."""
        # Command execution - Simple command
        result = container_manager.execute_command(
            container_id=shared_session.container_id,
            command=["echo", "hello world"],
        )
        assert result.exit_code == 0
        assert "hello world" in result.stdout
        assert result.stderr == ""

        # Command execution - Custom working directory
        result = container_manager.execute_command(
            container_id=shared_session.container_id,
            command=["pwd"],
            working_dir=Path("/tmp"),
        )
        assert result.exit_code == 0
        assert "/tmp" in result.stdout

        # Command execution - Environment variables
        result = container_manager.execute_command(
            container_id=shared_session.container_id,
            command=["sh", "-c", "echo $TEST_VAR"],
            environment={"TEST_VAR": "test_value"},
        )
        assert result.exit_code == 0
        assert "test_value" in result.stdout

        # Command execution - Shell command with pipes
        result = container_manager.execute_command(
            container_id=shared_session.container_id,
            command=["sh", "-c", "echo 'line1' && echo 'line2'"],
        )
        assert result.exit_code == 0
        assert "line1" in result.stdout
        assert "line2" in result.stdout

        # File operations - Write file using session manager
        write_content = "This is test content\nLine 2\nLine 3"
        container_path = Path("/workspace/test_file.txt")

        session_manager.write_file(
            user_id=test_user,
            session_id=test_session,
            container_path=container_path,
            content=write_content,
        )

        # File operations - Verify file exists and has correct content
        result = container_manager.execute_command(
            container_id=shared_session.container_id,
            command=["cat", str(container_path)],
        )
        assert result.exit_code == 0
        assert result.stdout.strip() == write_content

        # File operations - Create file via shell command
        shell_content = "Created by shell"
        result = container_manager.execute_command(
            container_id=shared_session.container_id,
            command=["sh", "-c", f"echo '{shell_content}' > /workspace/shell_file.txt"],
        )
        assert result.exit_code == 0

        # File operations - Read it back
        result = container_manager.execute_command(
            container_id=shared_session.container_id,
            command=["cat", "/workspace/shell_file.txt"],
        )
        assert result.exit_code == 0
        assert shell_content in result.stdout

    def test_02_path_translation(self, container_manager, test_user, test_session, test_workspace):
        """Test path translation between host and container."""
        container_path = Path("/workspace/test.txt")

        # Convert container path to host path
        host_path = container_manager.to_host_path(container_path, test_user, test_session)
        assert host_path is not None
        assert test_workspace in host_path.parents

        # Convert back to container path
        converted_path = container_manager.to_container_path(host_path, test_user, test_session)
        assert converted_path == container_path

    def test_03_resource_limits(self, shared_session, docker_client):
        """Verify container has resource limits applied."""
        container = docker_client.containers.get(shared_session.container_id)
        host_config = container.attrs["HostConfig"]

        # Verify memory limit
        memory_limit = host_config.get("Memory")
        assert memory_limit is not None
        assert memory_limit > 0

        # Verify CPU limit
        cpu_quota = host_config.get("CpuQuota")
        assert cpu_quota is not None
        assert cpu_quota > 0

    def test_04_session_activity_and_status(
        self, shared_session, session_manager, container_manager, test_user, test_session
    ):
        """Verify session activity tracking and container status."""
        # Check activity tracking
        initial_activity = shared_session.last_active_at
        time.sleep(0.1)
        session_manager.update_session_activity(test_user, test_session)

        updated_session = session_manager.get_session(test_user, test_session)
        assert updated_session.last_active_at > initial_activity

        # Verify session not expired (has recent activity)
        assert not updated_session.is_expired()

        # Check container status
        status = container_manager.get_container_status(shared_session.container_id)
        assert status == ContainerStatus.RUNNING

    def test_05_cleanup_verification(
        self, shared_session, session_manager, container_manager, docker_client, test_user, test_session
    ):
        """Verify cleanup removes container and session."""
        container_id = shared_session.container_id

        # Close session (should remove container)
        session_manager.close_session(test_user, test_session)

        # Verify session removed
        session = session_manager.get_session(test_user, test_session)
        assert session is None

        # Verify container removed from Docker
        with pytest.raises(docker.errors.NotFound):
            docker_client.containers.get(container_id)

        # Verify container removed from manager tracking
        assert container_id not in container_manager.containers

    def test_06_session_recovery_after_manager_restart(
        self, backend, test_config, test_workspace, docker_client, test_user
    ):
        """Test that sessions reconnect to existing containers after manager restart.

        Verifies:
        1. Container survives manager destruction
        2. New manager discovers existing container
        3. Session reconnects automatically
        4. Port bindings are preserved and queryable after restart
        """
        recovery_session_id = f"recovery-{test_user}"
        test_content = "Data survives manager restart"
        test_ports = [5000, 5001, 5002]

        # Phase 1: Create session with first manager
        manager1 = SimpleContainerManager(
            backend=backend,
            container_prefix=f"{test_config['test_prefix']}-recovery",
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        session_manager1 = BaseSessionManager(
            container_manager=manager1,
            default_image=test_config["test_image"],
        )

        # Create config with ports
        config_with_ports = ContainerConfig(
            image=test_config["test_image"],
            ports=test_ports,
        )

        session1 = session_manager1.create_session(
            user_id=test_user,
            session_id=recovery_session_id,
            config=config_with_ports,
        )
        container_id = session1.container_id

        # Verify ports are bound
        port_bindings = backend.get_accessible_ports(container_id)
        assert len(port_bindings) == 3, f"Expected 3 ports, got {len(port_bindings)}"
        assert set(port_bindings.keys()) == set(test_ports), (
            f"Port keys mismatch: {port_bindings.keys()} vs {test_ports}"
        )
        # Verify 1:1 mapping (container port 5000 → host port 5000)
        for port in test_ports:
            assert port_bindings[port] == port, f"Port {port} should map to itself, got {port_bindings[port]}"

        session_manager1.write_file(
            user_id=test_user,
            session_id=recovery_session_id,
            container_path=Path("/workspace/persistent.txt"),
            content=test_content,
        )

        # Verify container is running
        container = docker_client.containers.get(container_id)
        assert container.status == "running"

        # Phase 2: Destroy managers (simulates restart)
        del session_manager1
        del manager1

        # Phase 3: Create new managers - should auto-recover session
        manager2 = SimpleContainerManager(
            backend=backend,
            container_prefix=f"{test_config['test_prefix']}-recovery",
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        session_manager2 = BaseSessionManager(
            container_manager=manager2,
            default_image=test_config["test_image"],
        )

        # Verify session was recovered
        recovered_session = session_manager2.get_session(test_user, recovery_session_id)
        assert recovered_session is not None
        assert recovered_session.container_id == container_id

        # Verify port bindings survived restart
        recovered_ports = backend.get_accessible_ports(container_id)
        assert recovered_ports == port_bindings, "Port bindings should be preserved after recovery"
        assert set(recovered_ports.keys()) == set(test_ports), f"Recovered ports mismatch: {recovered_ports.keys()}"

        # Verify data is still accessible
        result = session_manager2.execute_command(
            user_id=test_user,
            session_id=recovery_session_id,
            command=["cat", "/workspace/persistent.txt"],
        )

        assert result.exit_code == 0
        assert test_content in result.stdout

        # Cleanup
        session_manager2.close_session(test_user, recovery_session_id)
        manager2.cleanup_all()

    def test_07_container_auto_restart_after_timeout(self, backend, test_config, docker_client, test_user):
        """Test that containers auto-restart when they've exited due to timeout."""
        timeout_session_id = f"timeout-{test_user}"

        manager = SimpleContainerManager(
            backend=backend,
            container_prefix=f"{test_config['test_prefix']}-timeout",
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        # Create config with very short container lifetime (reduced from 3s to 2s)
        short_timeout_config = ContainerConfig(
            image=test_config["test_image"],
            container_lifetime_seconds=2,  # Container exits after 2 seconds
        )

        session_manager = BaseSessionManager(
            container_manager=manager,
            default_image=test_config["test_image"],
        )

        session = session_manager.create_session(
            user_id=test_user,
            session_id=timeout_session_id,
            config=short_timeout_config,
        )

        container_id = session.container_id

        # Execute command before timeout
        result = session_manager.execute_command(
            user_id=test_user,
            session_id=timeout_session_id,
            command=["echo", "before timeout"],
        )
        assert result.exit_code == 0

        # Wait for timeout (reduced from 3s to 2.5s)
        time.sleep(2.5)

        # Verify container stopped
        container = docker_client.containers.get(container_id)
        container.reload()
        assert container.status != "running"

        # Execute command again - should auto-restart
        result = session_manager.execute_command(
            user_id=test_user,
            session_id=timeout_session_id,
            command=["echo", "after auto-restart"],
        )

        assert result.exit_code == 0
        assert "after auto-restart" in result.stdout

        # Verify container is running again
        container.reload()
        assert container.status == "running"

        # Cleanup
        session_manager.close_session(test_user, timeout_session_id)
        manager.cleanup_all()

    def test_08_convenience_api_with_context_manager(self, test_config, test_user, docker_client):
        """Test get_docker_session() with mounts and context manager auto-cleanup."""
        mounted_session_id = f"mounted-{test_user}"
        ctx_session_id = f"ctx-{test_user}"
        test_file = "data.txt"
        test_content = "persistent data"

        try:
            # Test with mounts (README Example 3)
            session = get_docker_session(
                user_id=test_user,
                session_id=mounted_session_id,
                workspace=str(test_config["test_workspace"]),
                workspace_host=str(test_config["test_workspace_host"]),
            )

            # Write file using relative path (auto-prepended with /workspace/)
            returned_path = session.write_file(test_file, test_content)
            assert returned_path == Path(f"/workspace/{test_file}")

            # Verify file can be read from container
            result = session.execute_command(["cat", str(returned_path)])
            assert result.exit_code == 0
            assert result.stdout.strip() == test_content

            # Get session info to find actual host path
            session_info = session.get_info()
            session_data_dir = Path(session_info.data_dir)
            expected_host_file = session_data_dir / test_file

            # Verify file persists on host
            assert expected_host_file.exists(), f"Expected file at {expected_host_file}"
            assert expected_host_file.read_text() == test_content

            session.close()

            # File should persist after container removal
            assert expected_host_file.exists(), "File should persist after container removal"

            # Cleanup host file
            expected_host_file.unlink()

            # Test context manager auto-cleanup
            container_id = None
            with get_docker_session(user_id=test_user, session_id=ctx_session_id) as ctx_session:
                container_id = ctx_session.get_info().container_id

                result = ctx_session.execute_command("echo 'test'")
                assert result.exit_code == 0

                # Container exists during context
                container = docker_client.containers.get(container_id)
                assert container.status == "running"

            # Container should be removed after context
            time.sleep(0.5)
            with pytest.raises(docker.errors.NotFound):
                docker_client.containers.get(container_id)

        finally:
            reset_lifecycle_cache()

    def test_09_entrypoint_controls_container_lifetime(self, backend, test_config, docker_client, test_user):
        """Test that entrypoint and command settings control container startup behavior.

        Tests:
        1. entrypoint=None (default) - uses sleep with container_lifetime_seconds
        2. entrypoint=[] - uses sleep infinity
        3. use_image_defaults=True - uses image's default entrypoint/command
        4. config.command explicitly set - uses custom startup command
        """
        entrypoint_session_id = f"entrypoint-test-{test_user}"

        manager = SimpleContainerManager(
            backend=backend,
            container_prefix=f"{test_config['test_prefix']}-entrypoint",
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        session_manager = BaseSessionManager(
            container_manager=manager,
            default_image=test_config["test_image"],
        )

        # Test 1: entrypoint=None (default) - uses sleep <container_lifetime_seconds>
        # Reduced from 3s to 2s
        config_with_timeout = ContainerConfig(
            image=test_config["test_image"],
            container_lifetime_seconds=2,  # 2 second lifetime
        )

        session1 = session_manager.create_session(
            user_id=test_user,
            session_id=f"{entrypoint_session_id}-timeout",
            config=config_with_timeout,
        )

        # Verify container is running
        container1 = docker_client.containers.get(session1.container_id)
        assert container1.status == "running"

        # Check that command is sleep with timeout
        container1.reload()
        container_attrs = container1.attrs
        cmd = container_attrs.get("Config", {}).get("Cmd", [])
        assert "sleep" in cmd
        assert "2" in cmd or 2 in cmd

        # Wait for container to auto-exit (reduced from 4s to 2.5s)
        time.sleep(2.5)
        container1.reload()
        assert container1.status != "running", "Container should have exited after timeout"

        # Test 2: entrypoint=[] - uses sleep infinity (runs indefinitely)
        config_no_timeout = ContainerConfig(
            image=test_config["test_image"],
            entrypoint=[],  # Explicit entrypoint disables auto-timeout
            container_lifetime_seconds=2,  # Should be ignored
        )

        session2 = session_manager.create_session(
            user_id=test_user,
            session_id=f"{entrypoint_session_id}-notimeout",
            config=config_no_timeout,
        )

        # Verify container is running
        container2 = docker_client.containers.get(session2.container_id)
        assert container2.status == "running"

        # Check that command is sleep infinity
        container2.reload()
        container_attrs = container2.attrs
        cmd = container_attrs.get("Config", {}).get("Cmd", [])
        assert "sleep" in cmd
        assert "infinity" in cmd

        # Wait the same time period - container should still be running (reduced from 4s to 2.5s)
        time.sleep(2.5)
        container2.reload()
        assert container2.status == "running", "Container should still be running (sleep infinity)"

        # Test 3: use_image_defaults=True - uses image's default entrypoint and command
        config_image_defaults = ContainerConfig(
            image=test_config["test_image"],
            use_image_defaults=True,
            container_lifetime_seconds=2,  # Should be ignored
        )

        session3 = session_manager.create_session(
            user_id=test_user,
            session_id=f"{entrypoint_session_id}-imagedefaults",
            config=config_image_defaults,
        )

        # Verify container was created and started (may exit immediately depending on image)
        container3 = docker_client.containers.get(session3.container_id)

        # Check that command and entrypoint are NOT overridden (uses image defaults)
        container3.reload()
        container_attrs = container3.attrs
        cmd = container_attrs.get("Config", {}).get("Cmd", [])
        entrypoint = container_attrs.get("Config", {}).get("Entrypoint", [])

        # The key behavior: podkit should NOT override with "sleep" command
        # For python:3.11-alpine, the default is typically ["python3"] or similar
        assert "sleep" not in str(cmd).lower(), f"Should not override command with sleep, got: {cmd}"
        # Also verify entrypoint isn't overridden (if it was set)
        if entrypoint:
            assert "sleep" not in str(entrypoint).lower(), f"Should not override entrypoint, got: {entrypoint}"

        # Note: Container lifecycle depends on image's default command behavior
        # python:3.11-alpine defaults to python3 which exits immediately without input
        # This is expected - we're verifying podkit doesn't override, not container longevity

        # Test 4: config.command explicitly set - uses custom startup command
        # This tests the highest priority path in the command handling logic
        config_custom_command = ContainerConfig(
            image=test_config["test_image"],
            entrypoint=[],  # Use shell
            command=["sh", "-c", "echo 'custom_startup_marker' > /tmp/startup.txt && sleep infinity"],
        )

        session4 = session_manager.create_session(
            user_id=test_user,
            session_id=f"{entrypoint_session_id}-customcmd",
            config=config_custom_command,
        )

        # Verify container is running
        container4 = docker_client.containers.get(session4.container_id)
        assert container4.status == "running"

        # Check that our custom command was used
        container4.reload()
        container_attrs = container4.attrs
        cmd = container_attrs.get("Config", {}).get("Cmd", [])
        assert "custom_startup_marker" in str(cmd), f"Custom command should be set, got: {cmd}"

        # Verify the custom command actually ran by checking the file it created
        result = session_manager.execute_command(
            test_user,
            f"{entrypoint_session_id}-customcmd",
            ["cat", "/tmp/startup.txt"],
        )
        assert result.exit_code == 0, f"Failed to read startup file: {result.stderr}"
        assert "custom_startup_marker" in result.stdout, "Custom startup command should have created the marker file"

        # Cleanup
        session_manager.close_session(test_user, f"{entrypoint_session_id}-timeout")
        session_manager.close_session(test_user, f"{entrypoint_session_id}-notimeout")
        session_manager.close_session(test_user, f"{entrypoint_session_id}-imagedefaults")
        session_manager.close_session(test_user, f"{entrypoint_session_id}-customcmd")
        manager.cleanup_all()

    def test_10_exec_command_timeout(self, backend, test_config, test_user):
        """Test that long-running commands are killed after timeout with exit code 124.

        Verifies:
        1. Command that exceeds timeout is terminated
        2. Returns standard timeout exit code 124
        3. Timeout is enforced (doesn't wait for full command duration)
        4. Container remains usable after timeout
        """
        timeout_test_session_id = f"cmd-timeout-{test_user}"

        manager = SimpleContainerManager(
            backend=backend,
            container_prefix=f"{test_config['test_prefix']}-cmdtimeout",
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        session_manager = BaseSessionManager(
            container_manager=manager,
            default_image=test_config["test_image"],
        )

        try:
            # Create session
            session = session_manager.create_session(
                user_id=test_user,
                session_id=timeout_test_session_id,
            )

            # Test 1: Command that would run for 10 seconds, but timeout after 2
            start_time = time.time()
            result = manager.execute_command(
                container_id=session.container_id,
                command=["sleep", "10"],
                timeout=2,  # Kill after 2 seconds
            )
            elapsed = time.time() - start_time

            # Should complete in ~2 seconds (allow 1s margin for process cleanup)
            assert elapsed < 3, f"Command took {elapsed:.2f}s but should timeout after ~2s"

            # Should return standard timeout exit code
            assert result.exit_code == 124, f"Expected exit code 124 for timeout, got {result.exit_code}"

            # Should have timeout message
            assert "timed out" in result.stderr.lower(), f"Expected timeout message in stderr, got: {result.stderr}"

            # Test 2: Verify container still works after timeout
            result2 = manager.execute_command(
                container_id=session.container_id,
                command=["echo", "still working"],
            )
            assert result2.exit_code == 0
            assert "still working" in result2.stdout

        finally:
            session_manager.close_session(test_user, timeout_test_session_id)
            manager.cleanup_all()

    def test_11_startup_verification(self, backend, test_config, docker_client, test_user):
        """Test startup verification feature detects containers that crash on startup.

        Verifies:
        1. Faulty containers are detected with diagnostic logs and exit codes
        2. Healthy containers pass verification and work normally
        """

        manager = SimpleContainerManager(
            backend=backend,
            container_prefix=f"{test_config['test_prefix']}-startup-verify",
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        session_manager = BaseSessionManager(
            container_manager=manager,
            default_image=test_config["test_image"],
        )

        # Phase 1: Verification detects failing container
        session_id_failing = f"failing-{test_user}"
        config_failing = ContainerConfig(
            image=test_config["test_image"],
            entrypoint=["sh", "-c", "echo 'Fatal error occurred'; exit 1"],
            startup_verification=StartupVerificationConfig(
                required_consecutive_checks=3,
                check_interval_seconds=1.0,
                max_wait_seconds=5.0,
            ),
        )

        try:
            # Should raise RuntimeError with diagnostics
            with pytest.raises(RuntimeError) as exc_info:
                session_manager.create_session(
                    user_id=test_user,
                    session_id=session_id_failing,
                    config=config_failing,
                )

            # Verify error contains diagnostics
            error_msg = str(exc_info.value)
            assert "failed to start" in error_msg.lower()
            assert "exit code" in error_msg.lower()
            assert "Fatal error occurred" in error_msg, "Should capture container logs"

        finally:
            # Cleanup any leftover containers
            manager.cleanup_all()

        # Phase 2: Verification succeeds for healthy container
        session_id_healthy = f"healthy-{test_user}"
        config_healthy = ContainerConfig(
            image=test_config["test_image"],
            entrypoint=["sh", "-c", "sleep 3600"],
            startup_verification=StartupVerificationConfig(
                required_consecutive_checks=3,
                check_interval_seconds=0.5,  # Faster for testing
                max_wait_seconds=5.0,
            ),
        )

        try:
            # Should complete successfully
            session_healthy = session_manager.create_session(
                user_id=test_user,
                session_id=session_id_healthy,
                config=config_healthy,
            )

            # Verify container is running
            container = docker_client.containers.get(session_healthy.container_id)
            assert container.status == "running"

            # Can execute commands
            result = manager.execute_command(
                container_id=session_healthy.container_id,
                command=["echo", "verified"],
            )
            assert result.exit_code == 0
            assert "verified" in result.stdout

        finally:
            session_manager.close_session(test_user, session_id_healthy)
            manager.cleanup_all()

    def test_12_multiple_volumes(self, backend, test_config, docker_client, test_user, test_session):
        """Test multiple volume mounts work correctly.

        Verifies:
        1. Multiple Mount entries are processed correctly
        2. Each volume is accessible at its target path
        3. Files in mounted volumes are readable

        Note: Uses subdirectories of the shared test_workspace for Docker-in-Docker compatibility.
        Note: Read-only volume tests are in test_integration_negative_flows.py.
        """
        manager = SimpleContainerManager(
            backend=backend,
            container_prefix=f"{test_config['test_prefix']}-multi-volumes",
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        session_manager = BaseSessionManager(
            container_manager=manager,
            default_image=test_config["test_image"],
        )

        # Create test directories
        container_path1 = test_config["test_workspace"] / "multi_vol" / test_session / "test1"
        container_path2 = test_config["test_workspace"] / "multi_vol" / test_session / "test2"
        container_path1.mkdir(parents=True, exist_ok=True)
        container_path2.mkdir(parents=True, exist_ok=True)

        # For Docker-in-Docker, use host paths for volume mounts
        host_path1 = test_config["test_workspace_host"] / "multi_vol" / test_session / "test1"
        host_path2 = test_config["test_workspace_host"] / "multi_vol" / test_session / "test2"

        try:
            # Prepare test files
            (container_path1 / "file1.txt").write_text("content from volume 1")
            (container_path2 / "file2.txt").write_text("content from volume 2")

            # Configure with multiple mounts including read-only
            config_with_multiple_volumes = ContainerConfig(
                image=test_config["test_image"],
                volumes=[
                    Mount(type="bind", source=host_path1, target=Path("/mount1")),
                    Mount(type="bind", source=host_path2, target=Path("/mount2")),
                ],
            )

            session = session_manager.create_session(
                user_id=test_user,
                session_id=test_session,
                config=config_with_multiple_volumes,
            )
            container = docker_client.containers.get(session.container_id)
            assert container.status == "running"

            # Verify read-write mounts are accessible
            result1 = session_manager.execute_command(
                user_id=test_user,
                session_id=test_session,
                command=["cat", "/mount1/file1.txt"],
            )
            assert result1.exit_code == 0
            assert "content from volume 1" in result1.stdout

            result2 = session_manager.execute_command(
                user_id=test_user,
                session_id=test_session,
                command=["cat", "/mount2/file2.txt"],
            )
            assert result2.exit_code == 0
            assert "content from volume 2" in result2.stdout

        finally:
            session_manager.close_session(test_user, test_session)
            manager.cleanup_all()
            if container_path1.parent.exists():
                shutil.rmtree(container_path1.parent)

    def test_13_process_management_incremental(self, backend, test_config, test_user):
        """Incremental process management test - building up features one at a time.

        This test builds functionality gradually, adding one feature section at a time.
        Each section validates a specific capability before moving to the next.
        Uses the new ProcessManager implementation.
        """
        session_id = f"process-v2-{test_user}"

        manager = SimpleContainerManager(
            backend=backend,
            container_prefix=f"{test_config['test_prefix']}-processv2",
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        session_manager = BaseSessionManager(
            container_manager=manager,
            default_image=test_config["test_image"],
        )

        try:
            # Create session with explicit entrypoint to prevent early exit
            config = ContainerConfig(
                image=test_config["test_image"],
                entrypoint=[],  # Sleep infinity - prevents early exit
            )

            session = session_manager.create_session(
                user_id=test_user,
                session_id=session_id,
                config=config,
            )

            # Create process manager (using new implementation)
            process_mgr = ProcessManager(
                container_manager=manager,
                container_id=session.container_id,
                user_id=test_user,
                session_id=session_id,
            )

            # ==========================================
            # Phase 1A: Start simple command
            # ==========================================
            print("\n=== Phase 1A: Start simple command ===")
            sleep_proc = process_mgr.start_process("sleep 30")
            assert sleep_proc.pid is not None, "Process should have PID"
            assert process_mgr.is_running(sleep_proc.id), "Process should be running"
            print(f"✓ Phase 1A passed: Started process with PID {sleep_proc.pid}")

            # ==========================================
            # Phase 1C: Multiple processes
            # ==========================================
            print("\n=== Phase 1C: Multiple processes ===")
            proc1 = process_mgr.start_process("sleep 30")
            proc2 = process_mgr.start_process("sleep 30")
            proc3 = process_mgr.start_process("sleep 30")

            processes = process_mgr.list_processes()
            # Should have at least 4: sleep_proc (from 1A), proc1, proc2, proc3
            assert len(processes) >= 4, f"Should track at least 4 processes, got {len(processes)}"

            process_ids = [p.id for p in processes]
            assert sleep_proc.id in process_ids, "Original sleep process should be in list"
            assert proc1.id in process_ids, "Process 1 should be in list"
            assert proc2.id in process_ids, "Process 2 should be in list"
            assert proc3.id in process_ids, "Process 3 should be in list"
            print(f"✓ Phase 1C passed: Managing {len(processes)} processes")

            # ==========================================
            # Phase 2: Combined stdout and stderr capture
            # ==========================================
            print("\n=== Phase 2: Combined stdout and stderr capture ===")
            both_proc = process_mgr.start_process("sh -c 'echo out && echo err >&2 && sleep 1'")
            time.sleep(1.5)  # Wait for command to complete
            logs = process_mgr.get_logs(both_proc.id)
            assert "out" in logs["stdout"], f"Should capture stdout, got: {logs['stdout']}"
            assert "err" in logs["stderr"], f"Should capture stderr, got: {logs['stderr']}"
            print(f"✓ Phase 2F passed: stdout='{logs['stdout'].strip()}', stderr='{logs['stderr'].strip()}'")

            # ==========================================
            # Phase 3: Lifecycle tests (parallelized for efficiency)
            # ==========================================
            print("\n=== Phase 3: Lifecycle tests (completion, failure, exit codes) ===")

            # Start all lifecycle test processes at once
            print("Starting all lifecycle test processes...")
            short_proc = process_mgr.start_process("sleep 0.5")  # 3G: completion
            fail_proc = process_mgr.start_process("sh -c 'exit 5'")  # 3H: failure + exit code
            py_proc = process_mgr.start_process("python3 -c 'import sys; sys.exit(42)'")  # 3J: Python exit code

            # Verify all started as RUNNING
            assert short_proc.status == ProcessStatus.RUNNING, "Completion test should start as RUNNING"
            assert fail_proc.status == ProcessStatus.RUNNING, "Failure test should start as RUNNING"
            assert py_proc.status == ProcessStatus.RUNNING, "Python test should start as RUNNING"

            # Single wait for all processes to complete
            print("Waiting for all processes to complete...")
            time.sleep(1)

            # Check all results
            print("Checking completion detection (3G)...")
            status_complete = process_mgr.get_status(short_proc.id)
            assert status_complete == ProcessStatus.STOPPED, f"Should detect completion, got {status_complete}"
            print("✓ Phase 3G passed: Detected process completion")

            print("Checking failure detection with exit code (3H)...")
            status_fail = process_mgr.get_status(fail_proc.id)
            assert status_fail == ProcessStatus.FAILED, f"Should detect failure, got {status_fail}"
            assert fail_proc.exit_code == 5, f"Should capture exit code 5, got {fail_proc.exit_code}"
            print(f"✓ Phase 3H passed: Detected process failure with exit code {fail_proc.exit_code}")

            print("Checking Python exit code (3J - the critical test!)...")
            status_py = process_mgr.get_status(py_proc.id)
            assert status_py == ProcessStatus.FAILED, f"Exit code 42 should be FAILED, got {status_py}"
            assert py_proc.exit_code == 42, f"Should capture exit code 42, got {py_proc.exit_code}"
            print(f"✓ Phase 3J passed: Captured Python exit code {py_proc.exit_code} correctly!")

            # ==========================================
            # Phase 4K: Environment variables
            # ==========================================
            print("\n=== Phase 4K: Environment variables ===")
            env_proc = process_mgr.start_process(
                "python3 -c 'import os; print(os.getenv(\"TEST_VAR\"))'", environment={"TEST_VAR": "test_value_123"}
            )
            time.sleep(1)  # Wait for completion
            logs = process_mgr.get_logs(env_proc.id)
            assert "test_value_123" in logs["stdout"], f"Environment variable should be in logs, got: {logs['stdout']}"
            print("✓ Phase 4K passed: Environment variable passed correctly")

            # ==========================================
            # Phase 4L: Working directory
            # ==========================================
            print("\n=== Phase 4L: Working directory ===")
            wd_proc = process_mgr.start_process("pwd", working_dir=Path("/tmp"))
            time.sleep(1)  # Wait for completion
            logs = process_mgr.get_logs(wd_proc.id)
            assert "/tmp" in logs["stdout"], f"Should run in /tmp, got: {logs['stdout']}"
            print("✓ Phase 4L passed: Working directory control works")

            # ==========================================
            # Phase 4M: Process naming
            # ==========================================
            print("\n=== Phase 4M: Process naming ===")
            named_proc = process_mgr.start_process("sleep 2", name="test-process")
            assert named_proc.name == "test-process", f"Process name should be set, got {named_proc.name}"
            assert "test-process" in named_proc.display_name, (
                f"display_name should contain name, got {named_proc.display_name}"
            )
            assert named_proc.id[:8] in named_proc.display_name, (
                f"display_name should contain UUID, got {named_proc.display_name}"
            )
            print(f"✓ Phase 4M passed: Process naming works (display_name: {named_proc.display_name})")

            # ==========================================
            # Phase 4N: Graceful shutdown
            # ==========================================
            print("\n=== Phase 4N: Graceful shutdown ===")
            graceful_proc = process_mgr.start_process("sleep 10")
            success = process_mgr.stop_process(graceful_proc.id, timeout=2, force=True)
            assert success, "Should successfully stop process"
            assert not process_mgr.is_running(graceful_proc.id), "Process should not be running"
            print("✓ Phase 4N passed: Graceful shutdown with force fallback works")

            # ==========================================
            # Phase 6Q: Port detection (optional - lsof may not be available)
            # ==========================================
            print("\n=== Phase 6Q: Port detection ===")
            http_proc = process_mgr.start_process("python3 -m http.server 9999", name="http-server")
            time.sleep(1)  # Give server time to start

            # Update status to trigger port detection
            status = process_mgr.get_status(http_proc.id)
            assert status == ProcessStatus.RUNNING, "HTTP server should be running"

            # Port detection is graceful - may or may not work depending on lsof availability
            if http_proc.ports is not None and http_proc.ports:
                assert 9999 in http_proc.ports, f"Port 9999 should be detected, got {http_proc.ports}"
                print(f"✓ Phase 6Q passed: Port detection works (detected ports: {http_proc.ports})")
            else:
                print("✓ Phase 6Q passed: Port detection gracefully handles missing lsof")

            # Cleanup
            process_mgr.stop_process(http_proc.id, force=True)

            print("\n" + "=" * 60)
            print("🎉 ALL PHASES PASSED!")
            print("Phase 1: Core (A, C) ✓")
            print("Phase 2: Observability (stdout/stderr) ✓")
            print("Phase 3: Lifecycle (G, H, J) ✓")
            print("Phase 4: Advanced (K, L, M, N) ✓")
            print("Phase 6: Integration (Q) ✓")
            print("=" * 60)

        finally:
            session_manager.close_session(test_user, session_id)
            manager.cleanup_all()

    def test_14_run_in_docker_convenience_function(self):
        """Test run_in_docker convenience function for one-off executions.

        Verifies:
        1. Simple command execution
        2. File injection before execution
        3. Environment variables
        4. Command timeout with exit code 124
        5. Working directory
        """
        # Test 1: Simple command
        result = run_in_docker("echo hello")
        assert result.exit_code == 0
        assert "hello" in result.stdout

        # Test 2: With files
        result = run_in_docker(
            "python /workspace/script.py",
            files={"/workspace/script.py": "print('from_file')"},
        )
        assert result.exit_code == 0
        assert "from_file" in result.stdout

        # Test 3: Environment variables
        result = run_in_docker(
            ["sh", "-c", "echo $TEST_VAR"],
            environment={"TEST_VAR": "test_value"},
        )
        assert result.exit_code == 0
        assert "test_value" in result.stdout

        # Test 4: Command timeout
        result = run_in_docker("sleep 10", command_timeout=1)
        assert result.exit_code == 124, "Should return exit code 124 on timeout"
        assert "timed out" in result.stderr.lower()

        # Test 5: Working directory
        result = run_in_docker("pwd", working_dir="/tmp")
        assert result.exit_code == 0
        assert "/tmp" in result.stdout

    def test_15_port_pool_and_event_handler_integration(self, backend, test_config):
        """Test PortPool and PodkitEventHandler working together with real containers.

        Verifies:
        1. PortPool allocates ports correctly
        2. PodkitEventHandler receives lifecycle events
        3. Ports are passed to container config
        4. Ports are released when session closes
        5. Multiple sessions get different ports
        """
        # Create port pool with small range for testing
        pool = PortPool(start=7000, end=7019, ports_per_container=3)
        assert pool.available_count == 20

        # Track lifecycle events
        events = []

        class TestEventHandler(PodkitEventHandler):
            """Event handler for testing port allocation lifecycle."""

            def on_container_creating(self, user_id, session_id, config):
                ports = pool.allocate()
                config.ports = ports
                events.append(("creating", user_id, session_id, list(ports)))
                return config

            def on_session_created(self, session):
                events.append(("created", session.user_id, session.session_id))

            def on_session_closing(self, session):
                events.append(("closing", session.user_id, session.session_id))

            def on_session_closed(self, session):
                if session.config.ports:
                    pool.release(session.config.ports)
                events.append(("closed", session.user_id, session.session_id, list(session.config.ports)))

        # Create event handler and managers
        event_handler = TestEventHandler()
        container_manager, session_manager = create_managers_with_event_handler(
            backend, test_config, "hooks", event_handler
        )

        try:
            # Create first session
            config1 = ContainerConfig(image=test_config["test_image"], entrypoint=[])
            session1 = session_manager.create_session("user1", "session1", config1)

            assert session1.config.ports == [7000, 7001, 7002], (
                f"First session should get first ports, got {session1.config.ports}"
            )
            assert pool.available_count == 17, "Pool should have 17 ports after first allocation"

            # Create second session
            config2 = ContainerConfig(image=test_config["test_image"], entrypoint=[])
            session2 = session_manager.create_session("user2", "session2", config2)

            assert session2.config.ports == [7003, 7004, 7005], (
                f"Second session should get next ports, got {session2.config.ports}"
            )
            assert pool.available_count == 14, "Pool should have 14 ports after second allocation"

            # Verify containers are running
            assert container_manager.get_container_status(session1.container_id) == ContainerStatus.RUNNING
            assert container_manager.get_container_status(session2.container_id) == ContainerStatus.RUNNING

            # Close first session - ports should be released
            session_manager.close_session("user1", "session1")
            assert pool.available_count == 17, "Pool should have 17 ports after releasing first session"

            # Create third session - should reuse released ports
            config3 = ContainerConfig(image=test_config["test_image"], entrypoint=[])
            session3 = session_manager.create_session("user3", "session3", config3)

            assert session3.config.ports == [7000, 7001, 7002], (
                f"Third session should reuse released ports, got {session3.config.ports}"
            )
            assert pool.available_count == 14, "Pool should have 14 ports"

            # Close remaining sessions
            session_manager.close_session("user2", "session2")
            session_manager.close_session("user3", "session3")

            assert pool.available_count == 20, "All ports should be released"

            # Verify lifecycle events were captured correctly
            assert len(events) == 12, f"Should have 12 events (3 sessions x 4 events), got {len(events)}"

            # Check event types
            creating_events = [e for e in events if e[0] == "creating"]
            created_events = [e for e in events if e[0] == "created"]
            closing_events = [e for e in events if e[0] == "closing"]
            closed_events = [e for e in events if e[0] == "closed"]

            assert len(creating_events) == 3
            assert len(created_events) == 3
            assert len(closing_events) == 3
            assert len(closed_events) == 3

        finally:
            # Cleanup
            session_manager.cleanup_all()
            container_manager.cleanup_all()

    def test_16_container_networking(self, backend, test_config, docker_client, test_user):
        """Test container networking configuration.

        Verifies:
        1. inherit_parent_networks=True puts child on same network as parent
        2. Explicit networks=[...] attaches container to specified network
        3. Default behavior (no networks, inherit=False) uses default network only
        """
        # Get parent container's networks (the test runner container)
        parent_networks = get_parent_container_networks()
        assert len(parent_networks) > 0, (
            "Test must run inside a container with at least one network. Check docker-compose configuration."
        )

        manager = SimpleContainerManager(
            backend=backend,
            container_prefix=f"{test_config['test_prefix']}-networking",
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        session_manager = BaseSessionManager(
            container_manager=manager,
            default_image=test_config["test_image"],
        )

        test_network = None

        try:
            # ==========================================
            # Part 1: Test inherit_parent_networks=True
            # ==========================================
            config_inherit = ContainerConfig(
                image=test_config["test_image"],
                entrypoint=[],  # Sleep infinity
                inherit_parent_networks=True,
            )

            session_inherit = session_manager.create_session(
                user_id=test_user,
                session_id="inherit-network",
                config=config_inherit,
            )

            # Verify child container is on parent's network
            child_container = docker_client.containers.get(session_inherit.container_id)
            child_networks = list(child_container.attrs["NetworkSettings"]["Networks"].keys())

            # Child should be on at least one of parent's networks
            shared_networks = set(parent_networks) & set(child_networks)
            assert len(shared_networks) > 0, (
                f"Child container should inherit parent's network. "
                f"Parent networks: {parent_networks}, Child networks: {child_networks}"
            )

            session_manager.close_session(test_user, "inherit-network")

            # ==========================================
            # Part 2: Test explicit networks=[...]
            # ==========================================
            # Create a test network
            test_network_name = f"{test_config['test_prefix']}-test-network"
            test_network = docker_client.networks.create(test_network_name, driver="bridge")

            config_explicit = ContainerConfig(
                image=test_config["test_image"],
                entrypoint=[],
                networks=[test_network_name],
            )

            session_explicit = session_manager.create_session(
                user_id=test_user,
                session_id="explicit-network",
                config=config_explicit,
            )

            # Verify container is on the specified network
            explicit_container = docker_client.containers.get(session_explicit.container_id)
            explicit_networks = list(explicit_container.attrs["NetworkSettings"]["Networks"].keys())

            assert test_network_name in explicit_networks, (
                f"Container should be on explicit network '{test_network_name}'. Actual networks: {explicit_networks}"
            )

            session_manager.close_session(test_user, "explicit-network")

            # ==========================================
            # Part 3: Test default behavior (control)
            # ==========================================
            config_default = ContainerConfig(
                image=test_config["test_image"],
                entrypoint=[],
                inherit_parent_networks=False,  # Explicitly disabled
                networks=[],  # No explicit networks
            )

            session_default = session_manager.create_session(
                user_id=test_user,
                session_id="default-network",
                config=config_default,
            )

            # Verify container is NOT on parent's custom network
            default_container = docker_client.containers.get(session_default.container_id)
            default_networks = list(default_container.attrs["NetworkSettings"]["Networks"].keys())

            # Default should only have bridge network, not parent's custom network
            # (unless parent is also on bridge, which is common)
            # The key check: it should NOT have inherited custom networks
            non_default_parent_networks = [n for n in parent_networks if n != "bridge"]
            inherited_custom = set(non_default_parent_networks) & set(default_networks)

            assert len(inherited_custom) == 0, (
                f"Container with inherit_parent_networks=False should not inherit custom networks. "
                f"Parent custom networks: {non_default_parent_networks}, "
                f"Child networks: {default_networks}, "
                f"Unexpected inherited: {inherited_custom}"
            )

            session_manager.close_session(test_user, "default-network")

        finally:
            session_manager.cleanup_all()
            manager.cleanup_all()
            # Cleanup test network
            if test_network:
                try:
                    test_network.remove()
                except Exception:
                    pass

    def test_17_user_configuration(self, backend, test_config, test_user):
        """Test container user configuration.

        Verifies:
        1. user field controls which user runs commands
        2. Default user is root
        3. Non-root user has appropriate restrictions
        """
        manager = SimpleContainerManager(
            backend=backend,
            container_prefix=f"{test_config['test_prefix']}-user-config",
            workspace_base=test_config["test_workspace"],
            workspace_base_host=test_config["test_workspace_host"],
        )

        session_manager = BaseSessionManager(
            container_manager=manager,
            default_image=test_config["test_image"],
        )

        try:
            # ==========================================
            # Part 1: Test non-root user (nobody)
            # ==========================================
            config_nobody = ContainerConfig(
                image=test_config["test_image"],
                entrypoint=[],
                user="nobody",
            )

            session_manager.create_session(
                user_id=test_user,
                session_id="user-nobody",
                config=config_nobody,
            )

            # Verify whoami returns "nobody"
            result_whoami = session_manager.execute_command(test_user, "user-nobody", "whoami")
            assert result_whoami.exit_code == 0, f"whoami failed: {result_whoami.stderr}"
            assert result_whoami.stdout.strip() == "nobody", (
                f"Expected user 'nobody', got '{result_whoami.stdout.strip()}'"
            )

            # Verify id shows non-root (uid != 0)
            result_id = session_manager.execute_command(test_user, "user-nobody", "id -u")
            assert result_id.exit_code == 0, f"id -u failed: {result_id.stderr}"
            uid = int(result_id.stdout.strip())
            assert uid != 0, f"User 'nobody' should have non-zero UID, got {uid}"

            session_manager.close_session(test_user, "user-nobody")

            # ==========================================
            # Part 2: Test default user (root)
            # ==========================================
            config_default = ContainerConfig(
                image=test_config["test_image"],
                entrypoint=[],
                # user not specified - should default to root
            )

            session_manager.create_session(
                user_id=test_user,
                session_id="user-default",
                config=config_default,
            )

            # Verify whoami returns "root"
            result_whoami_root = session_manager.execute_command(test_user, "user-default", "whoami")
            assert result_whoami_root.exit_code == 0, f"whoami failed: {result_whoami_root.stderr}"
            assert result_whoami_root.stdout.strip() == "root", (
                f"Expected default user 'root', got '{result_whoami_root.stdout.strip()}'"
            )

            # Verify id shows root (uid == 0)
            result_id_root = session_manager.execute_command(test_user, "user-default", "id -u")
            assert result_id_root.exit_code == 0, f"id -u failed: {result_id_root.stderr}"
            uid_root = int(result_id_root.stdout.strip())
            assert uid_root == 0, f"Default user should be root (UID 0), got {uid_root}"

            session_manager.close_session(test_user, "user-default")

            # ==========================================
            # Part 3: Test permission restrictions
            # ==========================================
            config_restricted = ContainerConfig(
                image=test_config["test_image"],
                entrypoint=[],
                user="nobody",
            )

            session_manager.create_session(
                user_id=test_user,
                session_id="user-restricted",
                config=config_restricted,
            )

            # Try to write to root-owned directory - should fail
            result_write = session_manager.execute_command(
                test_user, "user-restricted", ["sh", "-c", "echo 'test' > /root/test.txt"]
            )

            # Should fail with permission denied
            assert result_write.exit_code != 0, "Writing to /root/ as 'nobody' should fail with permission denied"

            session_manager.close_session(test_user, "user-restricted")

        finally:
            session_manager.cleanup_all()
            manager.cleanup_all()

    def test_18_named_volume_workspace(self, backend, test_config, docker_client, test_user):
        """Test workspace mounting using Docker named volumes instead of bind mounts.

        This tests the `volume_name` parameter of SimpleContainerManager, which is used
        in containerized deployments where bind mounts aren't available.

        Verifies:
        1. Container starts successfully with named volume workspace
        2. Files can be written to and read from the workspace
        3. Data persists correctly within the volume
        """
        volume_name = f"{test_config['test_prefix']}-named-vol-test"
        session_id = f"named-vol-{test_user}"

        # Create a Docker named volume for testing
        volume = docker_client.volumes.create(name=volume_name)

        try:
            # Create manager using named volume instead of bind mounts
            manager = SimpleContainerManager(
                backend=backend,
                container_prefix=f"{test_config['test_prefix']}-named-vol",
                workspace_base=Path("/data"),  # Path inside the volume
                volume_name=volume_name,  # Use named volume
            )

            session_manager = BaseSessionManager(
                container_manager=manager,
                default_image=test_config["test_image"],
            )

            try:
                # Create session
                config = ContainerConfig(
                    image=test_config["test_image"],
                    entrypoint=[],  # Sleep infinity
                )

                session = session_manager.create_session(
                    user_id=test_user,
                    session_id=session_id,
                    config=config,
                )

                # Verify container is running
                container = docker_client.containers.get(session.container_id)
                assert container.status == "running"

                # Check if volume is mounted
                result_mount = session_manager.execute_command(
                    test_user,
                    session_id,
                    ["sh", "-c", "mount | grep -E 'podkit|volume' || echo 'No volume mounts found'"],
                )
                print(f"\nmount output:\n{result_mount.stdout}")

                result_mnt = session_manager.execute_command(test_user, session_id, ["ls", "-la", "/mnt/"])
                print(f"\n/mnt/ contents:\n{result_mnt.stdout}")

                result_vol_dir = session_manager.execute_command(
                    test_user,
                    session_id,
                    ["sh", "-c", "ls -la /mnt/podkit-workspace/ 2>&1 || echo 'Dir does not exist'"],
                )
                print(f"\n/mnt/podkit-workspace/ contents:\n{result_vol_dir.stdout}")

                result_workspaces = session_manager.execute_command(
                    test_user, session_id, ["sh", "-c", "ls -laR /mnt/podkit-workspace/workspaces/ 2>&1"]
                )
                print(f"\nworkspaces tree:\n{result_workspaces.stdout}")

                # Verify the workspace symlink was created (named volume initialization)
                result_symlink = session_manager.execute_command(
                    test_user,
                    session_id,
                    ["readlink", "/workspace"],
                )
                assert result_symlink.exit_code == 0, f"Symlink check failed: {result_symlink.stderr}"
                assert "/mnt/podkit-workspace/" in result_symlink.stdout, (
                    f"Workspace should be symlinked to volume mount, got: {result_symlink.stdout}"
                )

                # Write a file to the workspace (which uses the named volume)
                test_content = "Hello from named volume test!"
                result_write = session_manager.execute_command(
                    test_user,
                    session_id,
                    ["sh", "-c", f"echo '{test_content}' > /workspace/test_named_vol.txt"],
                )
                print(f"\nwrite exit_code: {result_write.exit_code}, stderr: {result_write.stderr}")
                assert result_write.exit_code == 0, f"Write failed: {result_write.stderr}"

                # Check where the file actually is
                result_find = session_manager.execute_command(
                    test_user,
                    session_id,
                    [
                        "sh",
                        "-c",
                        "find /mnt/podkit-workspace -name 'test_named_vol.txt' 2>/dev/null; "
                        "ls -la /workspace/ 2>&1; ls -la /workspace 2>&1",
                    ],
                )
                print(f"\nafter write - find and ls:\n{result_find.stdout}")

                # Read the file back
                result_read = session_manager.execute_command(
                    test_user,
                    session_id,
                    ["cat", "/workspace/test_named_vol.txt"],
                )
                print(
                    f"\nread exit_code: {result_read.exit_code}, "
                    f"stdout: {result_read.stdout}, stderr: {result_read.stderr}"
                )
                assert result_read.exit_code == 0, f"Read failed: {result_read.stderr}"
                assert test_content in result_read.stdout

                # Verify the workspace directory exists and is writable
                # Note: use /workspace/ (trailing slash) to list contents, not the symlink itself
                result_ls = session_manager.execute_command(
                    test_user,
                    session_id,
                    ["ls", "-la", "/workspace/"],
                )
                print(f"\nfinal ls -la /workspace/:\n{result_ls.stdout}")
                assert result_ls.exit_code == 0
                assert "test_named_vol.txt" in result_ls.stdout

            finally:
                session_manager.cleanup_all()
                manager.cleanup_all()

        finally:
            # Clean up the Docker volume
            volume.remove(force=True)
