"""Constants and default values for podkit library."""

# Using python:3.11-alpine for stability and small image size
DEFAULT_CONTAINER_IMAGE = "python:3.11-alpine"
DEFAULT_CPU_LIMIT = 1.0
DEFAULT_MEMORY_LIMIT = "512m"
DEFAULT_CONTAINER_LIFETIME_SECONDS = 60
DEFAULT_SESSION_INACTIVITY_TIMEOUT_SECONDS = 3600
DEFAULT_WORKING_DIR = "/workspace"
DEFAULT_USER = "root"

CONTAINER_WORKSPACE_PATH = "/workspace"
DUMMY_WORKSPACE_PATH = "/tmp/podkit_dummy"
WORKSPACE_SUBDIRECTORY = "workspaces"

DEFAULT_CONTAINER_PREFIX = "podkit"

DOCKER_CPU_QUOTA_MULTIPLIER = 100000  # Microseconds per second
DOCKER_STOP_TIMEOUT = 1

# Health monitoring
DEFAULT_HEALTH_CHECK_INTERVAL = 30  # seconds
DEFAULT_HEALTH_CHECK_LOG_LINES = 50  # lines to capture for diagnostics
