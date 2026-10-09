#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
  PYTHON="$SCRIPT_DIR/.venv/bin/python"
else
  PYTHON=python3
fi

export SERVER_HOST=0.0.0.0
export SERVER_PORT=8000
export TLS_ENABLED=false

echo "Starting presentation demo server..."
echo "Open http://localhost:8000 on this laptop."
echo "Other laptops should open http://$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1):8000"
echo "Press Ctrl+C to stop."

exec "$PYTHON" run_server.py
