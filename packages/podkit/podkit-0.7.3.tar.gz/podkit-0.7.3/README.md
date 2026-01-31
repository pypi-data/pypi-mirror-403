# Podkit - Simple Container Management Library

A Python library for sandboxed execution in Docker containers with backend abstraction

## Features

Podkit implements a clean **three-layer architecture** for flexible container management:

**Layer 1 (Backend)** provides runtime-agnostic infrastructure operations for Docker/Kubernetes with image management and workload execution;

**Layer 2 (ContainerManager)** bridges infrastructure and application logic with container lifecycle management, project-specific mounting strategies, and host-to-container path translation;

**Layer 3 (SessionManager)** delivers the user-facing API with session lifecycle tracking, automatic activity monitoring, and cleanup of expired sessions.

This separation enables backend portability (swap Docker for Podman or Kubernetes without touching business logic), customizable project configurations (different mounting strategies per project), and independent testing of each layer.

## Example 1 (the simplest one)

```python
# Auto-creates session OR reconnects to the existing running/exited container (auto-stopping after 1 min)

from podkit import get_docker_session

result = get_docker_session(user_id="bob", session_id="123").execute_command("pwd")
print(result.stdout)

# No auto-removing in this case, only auto-stopping!
# You may not close the session if you expect running some commands in this session again.
# Otherwise close the session manually, like in example 3.
```

## Example 2 (simple with auto-cleanup)

```python
# auto-cleanup with context manager (container will be removed, slower than example 1)

from podkit import get_docker_session

with get_docker_session(user_id="bob", session_id="123") as session:
    result = session.execute_command("pwd")
    print(result.stdout)

# Perfect when you need one-time execution - run the command and clean up resources right away
```

## Example 3 (with port exposure)

```python
# Expose ports from container to host

from pathlib import Path
from podkit.core.models import ContainerConfig
from podkit import get_docker_session

# Create config with exposed ports
config = ContainerConfig(
    image="nginx:latest",
    ports=[80, 443]  # Expose nginx on host ports 80 and 443
)

session = get_docker_session(
    user_id="bob",
    session_id="web-server",
    config=config
)

# nginx now accessible at http://localhost:80 and https://localhost:443
result = session.execute_command(["nginx", "-g", "daemon off;"])

session.close()
```

## Example 4 (multiple mounts with read-only support)

```python
# Multiple volume mounts via config.volumes (recommended approach)

from podkit import get_docker_session
from podkit.core.models import ContainerConfig, Mount

config = ContainerConfig(
    image="python:3.11-alpine",
    volumes=[
        # Read-only mounts (prevents accidental modifications)
        Mount(source="/shared/datasets", target="/data", read_only=True),
        Mount(source="/shared/configs", target="/etc/configs", read_only=True),
        # Read-write mount for outputs
        Mount(source="/app/outputs", target="/workspace"),
    ],
)

session = get_docker_session(
    user_id="bob",
    session_id="123",
    config=config,
)

# Read from shared data (read-only, safe from accidental changes)
result = session.execute_command(["cat", "/data/dataset.csv"])
print(result.stdout)

# Write results to output directory
session.execute_command(["sh", "-c", "echo 'processing complete' > /workspace/results.txt"])

session.close()
```

Note: Mount source directories must exist on the Docker host before running.


## Example 5 (production-ready configuration)

```python
# Comprehensive example: resource limits, mounts, networks, and environment

from podkit import get_docker_session
from podkit.core.models import ContainerConfig, Mount

config = ContainerConfig(
    image="python:3.11-alpine",
    # Resource limits
    cpu_limit=2.0,              # 2 CPU cores max
    memory_limit="1g",          # 1 GB RAM max
    # Network (must exist: docker network create execution-network)
    networks=["execution-network"],
    # Volume mounts
    volumes=[
        Mount(source="/shared/datasets", target="/data", read_only=True),
        Mount(source="/shared/credentials", target="/creds", read_only=True),
        Mount(source="/app/outputs", target="/outputs"),
    ],
    # Environment variables
    environment={
        "ENV": "production",
        "LOG_LEVEL": "INFO",
        "DATABASE_URL": "postgresql://db.execution-network:5432/tasks",
    },
)

session = get_docker_session(
    user_id="bob",
    session_id="task-123",
    config=config,
)

# Secure, resource-controlled execution with access to shared data
result = session.execute_command([
    "python", "/data/process_data.py",
    "--input", "/data/dataset.csv",
    "--output", "/outputs/results.json",
])

session.close()
```

## Example 5b (workspace system - auto directory creation)

Use the workspace system when you need:
- Automatic directory creation per user/session
- Persistent `write_file()` that writes to host filesystem

```python
# Workspace system creates: {workspace}/workspaces/{user_id}/{session_id}/
# and mounts it to /workspace in the container

from podkit import get_docker_session

session = get_docker_session(
    user_id="bob",
    session_id="task-456",
    workspace="/app/data",        # Podkit creates directories here
    workspace_host="/app/data",   # Docker mounts from here (same for local Docker)
)

# /app/data/workspaces/bob/task-456/ is auto-created and mounted to /workspace
session.write_file("/workspace/output.txt", "results")  # Persists on host!

session.close()
```

Note: The workspace system only works when podkit can create directories on the Docker host
(local Docker or Docker-in-Docker). For remote Docker, use `config.volumes` instead.
See [docs/workspace-mounts.md](docs/workspace-mounts.md) for details.


## Example 6 (full control - for advanced use cases)

Note: This example shows the low-level API for maximum control. For most use cases, use `get_docker_session()` instead.

```python
from pathlib import Path

from podkit.backends.docker import DockerBackend
from podkit.core.manager import BaseContainerManager
from podkit.core.models import ContainerConfig
from podkit.core.session import BaseSessionManager
from podkit.monitors.health import ContainerHealthMonitor
from podkit.utils.paths import get_workspace_path, write_to_mounted_path

# You must provide concrete ContainerManager implementation
# BaseContainerManager requires implementing get_mounts() and write_file()
class MyContainerManager(BaseContainerManager):
    """Custom container manager with project-specific mount logic."""

    def get_mounts(self, user_id: str, session_id: str, config: ContainerConfig):
        """Define how exactly to mount volumes."""

        workspace_path = get_workspace_path(self.workspace_base, user_id, session_id)
        workspace_path.mkdir(parents=True, exist_ok=True)

        return [{
            "Type": "bind",
            "Source": str(workspace_path),
            "Target": "/workspace",
        }]

    def write_file(self, container_id, container_path, content, user_id, session_id):
        """Write file to mounted filesystem (persists)."""

        return write_to_mounted_path(
            container_path,
            content,
            lambda path: self.to_host_path(path, user_id, session_id),
        )

backend = DockerBackend()
backend.connect()

container_manager = MyContainerManager(
    backend=backend,
    container_prefix="podkit",
    workspace_base=Path("/tmp/podkit_workspace"),
)

# Setup health monitoring for production deployments (optional but recommended)
# The monitor runs in a background thread and provides automatic recovery
health_monitor = ContainerHealthMonitor(
    container_manager=container_manager,
    check_interval=30,      # Check container health every 30 seconds
    log_lines=50            # Capture last 50 log lines for failed containers
)

# Pass health_monitor to session manager - it will register handler and start automatically
session_manager = BaseSessionManager(
    container_manager=container_manager,
    default_image="python:3.11-alpine",
    health_monitor=health_monitor,  # Auto-starts monitoring with recovery handler
)
# Health monitor now runs in background providing:
# - Automatic container recovery (restart if possible, recreate if needed)
# - Session cleanup (removes expired sessions)
# - Smart failure handling (marks sessions for recreation on next use)

# Configuration with auto-shutdown (entrypoint=None, default behavior)
# Container runs for 5 minutes then auto-exits (via sleep command)
sandbox_config = ContainerConfig(
    image="python:3.11-alpine",
    container_lifetime_seconds=300,  # Container auto-exits after 5 minutes
    cpu_limit=1.0,
    memory_limit="512m",
    environment={
        "PYTHONUNBUFFERED": "1",
        "LOG_LEVEL": "DEBUG",
    },
)

session = session_manager.create_session(
    user_id="user",
    session_id="session",
    config=sandbox_config,
)

# Execute commands - if container exited (timeout), it auto-restarts
result = session_manager.execute_command(
    user_id="user",
    session_id="session",
    command=["sh", "-c", "echo 'Hello'"],
)
print(result.stdout)

session_manager.write_file(
    user_id="user",
    session_id="session",
    container_path=Path("/workspace/file.txt"),
    content="Hello from podkit",
)

# Configuration without auto-shutdown (explicit entrypoint disables it)
# When entrypoint=[] is set, container uses "sleep infinity" and runs until manually closed
# Note: container_lifetime_seconds is IGNORED when explicit entrypoint is set
no_timeout_config = ContainerConfig(
    image="python:3.11-alpine",
    entrypoint=[],  # Explicit empty entrypoint = sleep infinity, no auto-shutdown
)

session2 = session_manager.create_session(
    user_id="user2",
    session_id="session2",
    config=no_timeout_config,
)
# This container runs indefinitely until manually closed (below)
# Session may still expire due to inactivity (controlled by session_inactivity_timeout_seconds)

# Cleanup
session_manager.close_session("user", "session")
session_manager.close_session("user2", "session2")
```

## Container Image Requirements

When using **ProcessManager** ([`podkit/processes/manager.py`](podkit/processes/manager.py)) to manage background processes, your container images must include specific system utilities:

### Required Dependencies

- **`procps`** - Provides full-featured `ps` command with process state inspection
  - Used for checking process status and detecting zombie processes
  - Note: Busybox `ps` (default in Alpine) doesn't support required flags
- **`coreutils`** - Standard Unix utilities (`mkdir`, `cat`, `tail`, etc.)
- **`sh`** - Shell for executing commands (typically pre-installed)

### Optional Dependencies

- **`lsof`** - Enables automatic port detection for running processes
  - If missing, port detection is gracefully skipped

### Installation Examples

**Alpine Linux:**
```dockerfile
RUN apk add --no-cache procps coreutils lsof
```

**Debian/Ubuntu:**
```dockerfile
RUN apt-get update && apt-get install -y procps coreutils lsof && rm -rf /var/lib/apt/lists/*
```

**Note:** If you're only using basic container operations (command execution, file I/O) without ProcessManager, these dependencies are not required.

## Development Setup

### Prerequisites

- Docker
- uv

### Installation

```bash
./scripts/install.sh
```

## Running Tests

### Integration Tests (Recommended)

Run tests in Docker container (most realistic):

```bash
./scripts/test.sh
```

This will:
1. Build the test runner container with all dependencies
2. Mount the Docker socket and test workspace
3. Run pytest with the integration tests
4. Clean up automatically
