#!/bin/bash
# Run production server (serves both API and frontend on one port).
# Build frontend first: ./scripts/build.sh
cd "$(dirname "$0")/.."
lsof -ti:8000 | xargs kill -9 2>/dev/null
exec python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --ws websockets
