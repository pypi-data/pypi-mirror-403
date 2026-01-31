#!/bin/bash -eu
set -o pipefail
set -x

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Check if the fix parameter is provided
FIX_MODE=false
if [[ $# -gt 0 && "$1" == "--fix" ]]; then
    FIX_MODE=true
fi

# Run linter
cd "$PROJECT_DIR"
if [ "$FIX_MODE" = true ]; then
    echo "Running linters in fix mode..."
    uv run ruff format ./podkit/ ./tests/
    uv run ruff check --fix ./podkit/ ./tests/
else
    echo "Running linters in check mode..."
    uv run ruff format --check ./podkit/ ./tests/
    uv run ruff check ./podkit/ ./tests/
fi
uv run pylint ./podkit/ ./tests/
