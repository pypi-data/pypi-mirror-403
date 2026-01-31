"""Process lifecycle management for containers.

This module provides tools for managing multiple background processes
within containers, including lifecycle management and health monitoring.

Example usage:
    from podkit.processes import ProcessManager, ProcessMonitor

    # Create container-scoped process manager
    manager = ProcessManager(container_manager, container_id)

    # Start background process
    process = manager.start_process(
        command="python -m http.server 8000",
        working_dir="/workspace"
    )

    # Monitor processes in background
    monitor = ProcessMonitor(manager, check_interval=30)
    monitor.start()
"""

from podkit.processes.manager import ProcessManager
from podkit.processes.models import Process, ProcessStatus
from podkit.processes.monitor import ProcessMonitor

__all__ = [
    "ProcessManager",
    "ProcessMonitor",
    "Process",
    "ProcessStatus",
]
