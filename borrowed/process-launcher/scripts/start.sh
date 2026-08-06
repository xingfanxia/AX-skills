#!/usr/bin/env bash
# Start the Process Launcher
# Run this from a terminal (or tmux) to get full TCC permissions.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating venv..."
    uv venv "$VENV_DIR"
    uv pip install -e "$PROJECT_DIR" --python "$VENV_DIR/bin/python" > /dev/null 2>&1
fi

exec "$VENV_DIR/bin/python" -m process_launcher start --config "$PROJECT_DIR/config/launcher.yaml"
