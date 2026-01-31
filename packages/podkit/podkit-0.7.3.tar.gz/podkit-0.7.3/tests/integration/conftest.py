"""Pytest fixtures for podkit integration tests."""

import os
import uuid
from pathlib import Path

import pytest

from podkit.backends.docker import DockerBackend
from podkit.core.manager import SimpleContainerManager
from podkit.core.session import BaseSessionManager


@pytest.fixture(scope="session")
def test_config():
    """Test configuration from environment variables."""
    return {
        "test_image": os.getenv("TEST_IMAGE", "python:3.11-alpine"),
        "test_workspace": Path(os.getenv("TEST_WORKSPACE", "/test_workspace")),
        "test_workspace_host": Path(os.getenv("TEST_WORKSPACE_HOST", os.getenv("TEST_WORKSPACE", "/test_workspace"))),
        "test_prefix": os.getenv("TEST_CONTAINER_PREFIX", "podkit-test"),
        "test_timeout": int(os.getenv("TEST_TIMEOUT", "300")),
    }


@pytest.fixture(scope="session")
def docker_client():
    """Docker client for test verification.

    Uses DockerBackend's connection logic to handle non-default Docker contexts.
    """
    backend = DockerBackend()
    backend.connect()
    yield backend.client
    backend.client.close()


@pytest.fixture(scope="session")
def test_workspace(test_config):
    """Test workspace directory."""
    workspace = test_config["test_workspace"]
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


@pytest.fixture(scope="module")
def backend():
    """Create Docker backend for tests."""
    backend = DockerBackend(logger=None)  # Use default logger for tests
    backend.connect()
    return backend


@pytest.fixture(scope="module")
def container_manager(backend, test_config):
    """Create container manager for tests."""
    manager = SimpleContainerManager(
        backend=backend,
        container_prefix=test_config["test_prefix"],
        workspace_base=test_config["test_workspace"],
        workspace_base_host=test_config["test_workspace_host"],
    )
    yield manager
    # Cleanup after tests
    manager.cleanup_all()


@pytest.fixture(scope="module")
def session_manager(container_manager, test_config):
    """Create session manager for tests."""
    manager = BaseSessionManager(
        container_manager=container_manager,
        default_image=test_config["test_image"],
    )
    yield manager
    # Cleanup after tests
    manager.cleanup_all()


@pytest.fixture(scope="class")
def test_user():
    """Generate unique test user ID."""
    return f"test-user-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="class")
def test_session():
    """Generate unique test session ID."""
    return f"test-session-{uuid.uuid4().hex[:8]}"


def create_managers_with_event_handler(backend, test_config, prefix_suffix, event_handler):
    """Factory function to create container and session managers with custom event handler.

    Args:
        backend: Docker backend instance
        test_config: Test configuration dictionary
        prefix_suffix: Suffix to append to container prefix (e.g., "hooks", "event-failures")
        event_handler: Event handler instance for lifecycle callbacks

    Returns:
        Tuple of (container_manager, session_manager)
    """
    container_manager = SimpleContainerManager(
        backend=backend,
        container_prefix=f"{test_config['test_prefix']}-{prefix_suffix}",
        workspace_base=test_config["test_workspace"],
        workspace_base_host=test_config["test_workspace_host"],
        event_handler=event_handler,
    )

    session_manager = BaseSessionManager(
        container_manager=container_manager,
        default_image=test_config["test_image"],
        event_handler=event_handler,
    )

    return container_manager, session_manager
