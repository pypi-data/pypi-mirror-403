"""Path translation utilities for container and host filesystems."""

from collections.abc import Callable
from pathlib import Path

from podkit.constants import CONTAINER_WORKSPACE_PATH, WORKSPACE_SUBDIRECTORY


def normalize_container_path(container_path: Path | str) -> Path:
    """
    Normalize a container path by auto-prepending /workspace/ for relative paths.

    Args:
        container_path: Path inside the container. Can be relative or absolute.

    Returns:
        Absolute container path with /workspace/ prepended for relative paths.

    Example:
        >>> normalize_container_path("file.txt")
        Path("/workspace/file.txt")
        >>> normalize_container_path("/workspace/file.txt")
        Path("/workspace/file.txt")
        >>> normalize_container_path("/tmp/file.txt")
        Path("/tmp/file.txt")
    """
    path = Path(container_path)
    if not path.is_absolute():
        path = Path(CONTAINER_WORKSPACE_PATH) / path
    return path


def container_to_host_path(
    container_path: Path,
    workspace_base: Path,
    container_workspace: Path = Path(CONTAINER_WORKSPACE_PATH),
) -> Path:
    """
    Convert a container path to a host path.

    Args:
        container_path: Path inside the container.
        workspace_base: Base workspace directory on the host.
        container_workspace: Workspace path inside the container (default: /workspace).

    Returns:
        Path on the host filesystem.

    Raises:
        ValueError: If container_path is not within the container workspace.

    Example:
        >>> container_to_host_path(
        ...     Path("/workspace/test.txt"),
        ...     Path("/home/user/.podkit/test/user1/session1"),
        ...     Path("/workspace")
        ... )
        Path("/home/user/.podkit/test/user1/session1/test.txt")
    """
    container_path = Path(container_path)
    workspace_base = Path(workspace_base)
    container_workspace = Path(container_workspace)

    try:
        relative_path = container_path.relative_to(container_workspace)
    except ValueError as e:
        raise ValueError(
            f"Container path '{container_path}' must be within container workspace '{container_workspace}'"
        ) from e

    host_path = workspace_base / relative_path
    return host_path


def host_to_container_path(
    host_path: Path,
    workspace_base: Path,
    container_workspace: Path = Path(CONTAINER_WORKSPACE_PATH),
) -> Path:
    """
    Convert a host path to a container path.

    Args:
        host_path: Path on the host filesystem.
        workspace_base: Base workspace directory on the host.
        container_workspace: Workspace path inside the container (default: /workspace).

    Returns:
        Path inside the container.

    Raises:
        ValueError: If host_path is not within the workspace base.

    Example:
        >>> host_to_container_path(
        ...     Path("/home/user/.podkit/test/user1/session1/test.txt"),
        ...     Path("/home/user/.podkit/test/user1/session1"),
        ...     Path("/workspace")
        ... )
        Path("/workspace/test.txt")
    """
    host_path = Path(host_path)
    workspace_base = Path(workspace_base)
    container_workspace = Path(container_workspace)

    try:
        relative_path = host_path.relative_to(workspace_base)
    except ValueError as e:
        raise ValueError(f"Host path '{host_path}' must be within workspace base '{workspace_base}'") from e

    container_path = container_workspace / relative_path
    return container_path


def get_workspace_path(
    workspace_base: Path,
    user_id: str,
    session_id: str,
) -> Path:
    """
    Get the workspace path for a specific user and session.

    Args:
        workspace_base: Base workspace directory.
        user_id: User identifier.
        session_id: Session identifier.

    Returns:
        Path to the user's session workspace.

    Example:
        >>> get_workspace_path(Path("/var/lib/podkit"), "user1", "session1")
        Path("/var/lib/podkit/workspaces/user1/session1")
    """
    return workspace_base / WORKSPACE_SUBDIRECTORY / user_id / session_id


def write_to_mounted_path(
    container_path: Path | str,
    content: str,
    to_host_path_fn: Callable[[Path], Path],
) -> Path:
    """Helper to write file to mounted filesystem with path normalization.

    Args:
        container_path: Path inside the container. Can be relative or absolute.
        content: Content to write.
        to_host_path_fn: Function that converts container path to host path.
            Should accept a Path and return a Path.

    Returns:
        The normalized container path where the file was written.
    """
    path = normalize_container_path(container_path)
    host_path = to_host_path_fn(path)
    host_path.parent.mkdir(parents=True, exist_ok=True)
    with open(host_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return path
