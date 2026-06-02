#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

".venv/bin/pip" install -r requirements.txt

PORT="${1:-8503}"
while lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; do
  PORT=$((PORT + 1))
done

echo "Starting Research Agent UI at http://localhost:${PORT}"
exec ".venv/bin/streamlit" run app.py \
  --browser.gatherUsageStats false \
  --server.port "$PORT"
