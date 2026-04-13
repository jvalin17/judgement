#!/bin/bash
# Start the backend dev server. Kills any existing server on port 8000 first.
cd "$(dirname "$0")/.."
lsof -ti:8000 | xargs kill -9 2>/dev/null
exec python3 -m uvicorn backend.app.main:app --reload --ws websockets --port 8000
