"""Network utilities for container management."""

import logging
import os

try:
    import docker

    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

logger = logging.getLogger(__name__)


def is_running_in_docker_container() -> bool:
    """Check if the current process is running inside a Docker container.

    Uses the hostname-based detection: Docker containers have hostname = container ID.
    Attempts to query the Docker API with the system hostname as a container ID.

    Returns:
        True if running inside a Docker container, False otherwise.
    """
    if not DOCKER_AVAILABLE:
        logger.debug("Docker SDK not available - assuming not in container")
        return False

    try:
        # Get system hostname (which equals container ID in Docker)
        hostname = os.uname().nodename

        client = docker.from_env()
        client.containers.get(hostname)

        return True

    except docker.errors.NotFound:
        return False
    except Exception as e:
        logger.debug(f"Could not determine if running in container: {e}")
        return False


def get_parent_container_networks() -> list[str]:
    """Discover networks of the parent container.

    This utility is useful when running podkit inside a Docker container
    and you want child containers to have the same network access as the parent.

    Common use case: MCP server runs in Docker with restricted networking (proxy/firewall).
    Child containers need same network configuration to reach external services.

    Returns:
        List of network names if running inside a Docker container.
        Empty list if not running in a container or if discovery fails.

    Example:
        >>> networks = get_parent_container_networks()
        >>> if networks:
        ...     print(f"Parent uses networks: {networks}")
        ... else:
        ...     print("Not running in container or discovery failed")
    """
    if not is_running_in_docker_container():
        logger.debug("Not running in a Docker container")
        return []

    try:
        # Get our container ID (which is the hostname)
        hostname = os.uname().nodename

        client = docker.from_env()
        container = client.containers.get(hostname)

        networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
        network_names = list(networks.keys())

        if network_names:
            logger.info(f"Discovered parent container networks: {network_names}")
        else:
            logger.debug("Parent container has no networks")

        return network_names

    except Exception as e:
        logger.debug(f"Could not discover parent container networks: {e}")
        return []
