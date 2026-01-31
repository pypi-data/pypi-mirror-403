#!/usr/bin/env bash

set -euo pipefail

source "$(dirname "$0")/config.sh"
source "$(dirname "$0")/install.sh"

cd "$PROJECT_DIR"

echo "Running integration tests in Docker container..."
# Use 'docker compose run' instead of 'up' to avoid watch monitoring crashes
docker compose build test-runner
docker compose run --rm test-runner
