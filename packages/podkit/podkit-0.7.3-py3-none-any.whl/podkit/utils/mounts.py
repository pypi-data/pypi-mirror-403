"""Shared mount configuration utilities for container managers."""

from pathlib import Path
from typing import Any

from podkit.constants import CONTAINER_WORKSPACE_PATH, WORKSPACE_SUBDIRECTORY
from podkit.core.models import ContainerConfig, Mount
from podkit.utils.paths import get_workspace_path

# Mount point for named volumes (before symlinking to /workspace)
NAMED_VOLUME_MOUNT_PATH = "/mnt/podkit-workspace"


def config_volumes_to_mounts(volumes: list[Mount] | None) -> list[dict[str, Any]]:
    """Convert config.volumes to Docker mount format.

    Args:
        volumes: List of Mount objects from ContainerConfig.volumes.

    Returns:
        List of mount specifications in Docker format.
    """
    mounts = []
    for volume in volumes or []:
        mount_dict = {
            "Type": volume.type,
            "Source": str(volume.source),
            "Target": str(volume.target),
        }
        if volume.read_only:
            mount_dict["ReadOnly"] = True
        mounts.append(mount_dict)
    return mounts


def get_volume_workspace_subpath(user_id: str, session_id: str) -> str:
    """Get the workspace subpath for a user/session within a named volume.

    Args:
        user_id: User identifier.
        session_id: Session identifier.

    Returns:
        Subpath like "workspaces/user1/session1".
    """
    return f"{WORKSPACE_SUBDIRECTORY}/{user_id}/{session_id}"


def get_volume_init_command(user_id: str, session_id: str) -> list[str]:
    """Get the command to initialize workspace inside a named volume.

    Creates the session directory and symlinks /workspace to it.

    Args:
        user_id: User identifier.
        session_id: Session identifier.

    Returns:
        Shell command to run inside container after start.
    """
    subpath = get_volume_workspace_subpath(user_id, session_id)
    workspace_dir = f"{NAMED_VOLUME_MOUNT_PATH}/{subpath}"
    target = CONTAINER_WORKSPACE_PATH
    return [
        "sh",
        "-c",
        f"mkdir -p {workspace_dir} && rm -rf {target} && ln -s {workspace_dir} {target}",
    ]


def get_standard_workspace_mounts(
    workspace_base: Path,
    user_id: str,
    session_id: str,
    config: ContainerConfig,
    to_host_path_fn,
    volume_name: str | None = None,
) -> list[dict[str, Any]]:
    """Generate standard workspace mounts for a container.

    This is the common mount strategy used by both SimpleContainerManager
    and _MountedContainerManager. It creates a workspace mount and adds
    any custom volumes from the config.

    Supports two mount types:
    - Bind mounts (default): Direct host path mounting
    - Named volumes: For containerized deployments using Docker volumes.
      The volume is mounted at a temporary path and symlinked to /workspace
      after container start (via get_volume_init_command).

    Args:
        workspace_base: Base workspace directory.
        user_id: User identifier.
        session_id: Session identifier.
        config: Container configuration with optional custom volumes.
        to_host_path_fn: Function to convert container path to host path.
            Should accept (container_path, user_id, session_id, real_host=True).
        volume_name: Optional Docker volume name. If provided, mounts the volume
            at a temporary path. Caller must run get_volume_init_command() after
            container start to set up /workspace symlink.

    Returns:
        List of mount specifications in Docker format.

    Example (bind mount):
        >>> mounts = get_standard_workspace_mounts(
        ...     workspace_base=Path("/tmp/workspace"),
        ...     user_id="user1",
        ...     session_id="session1",
        ...     config=ContainerConfig(image="python:3.11-alpine"),
        ...     to_host_path_fn=manager.to_host_path
        ... )

    Example (named volume):
        >>> mounts = get_standard_workspace_mounts(
        ...     workspace_base=Path("/data"),
        ...     user_id="user1",
        ...     session_id="session1",
        ...     config=ContainerConfig(image="python:3.11-alpine"),
        ...     to_host_path_fn=manager.to_host_path,
        ...     volume_name="my-data-volume"
        ... )
        >>> # After container start, run:
        >>> init_cmd = get_volume_init_command("user1", "session1")
    """
    if volume_name:
        # Named volume - mount entire volume at temporary path
        # Caller must run get_volume_init_command() after start to set up /workspace
        workspace_mount = {
            "Type": "volume",
            "Source": volume_name,
            "Target": NAMED_VOLUME_MOUNT_PATH,
        }
    else:
        # Bind mount - direct host path mounting
        workspace_path = get_workspace_path(workspace_base, user_id, session_id)
        workspace_path.mkdir(parents=True, exist_ok=True)

        # real_host=True gets the actual host path Docker can access
        host_workspace_path = to_host_path_fn(Path(CONTAINER_WORKSPACE_PATH), user_id, session_id, real_host=True)
        workspace_mount = {
            "Type": "bind",
            "Source": str(host_workspace_path),
            "Target": CONTAINER_WORKSPACE_PATH,
        }

    mounts = [workspace_mount]
    mounts.extend(config_volumes_to_mounts(config.volumes))

    return mounts
