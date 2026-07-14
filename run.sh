#!/usr/bin/env bash
#
# Start the whole Task Tracker stack with ONE command:
#   ./run.sh
#
# - FastAPI (API + Swagger) on http://127.0.0.1:8000
# - Gradio UI                on http://127.0.0.1:7860
#
# Set SQL_ECHO=1 to print the SQL that SQLModel generates:
#   SQL_ECHO=1 ./run.sh
#
# Press Ctrl-C to stop both.

set -euo pipefail
cd "$(dirname "$0")"

source .venv/bin/activate

# Start the API in the background.
uvicorn app.main:app --port 8000 &
API_PID=$!

# Always stop the API when this script exits (Ctrl-C, error, or UI quit).
trap 'kill "$API_PID" 2>/dev/null || true' EXIT

# Wait until the API is accepting requests before launching the UI.
echo "Waiting for the API on http://127.0.0.1:8000 ..."
until curl -sf http://127.0.0.1:8000/ >/dev/null 2>&1; do
    sleep 0.3
done
echo "API is up. Starting the Gradio UI on http://127.0.0.1:7860 ..."

# Run the UI in the foreground (keeps the script alive).
python ui.py
