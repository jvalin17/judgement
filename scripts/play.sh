#!/bin/bash
# One command to build and play Judgement.
# Launches as desktop app (pywebview) if installed, otherwise opens browser.
set -e
cd "$(dirname "$0")/.."

echo "Building frontend..."
cd frontend && npm run build --silent 2>&1 | tail -3
cd ..

lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 0.5

# Check if pywebview is available
if python3 -c "import webview" 2>/dev/null; then
    echo "Launching desktop app..."
    exec python3 desktop/main.py
else
    echo "Starting server on http://localhost:8000 ..."
    # Open browser after a short delay
    (sleep 2 && open "http://localhost:8000" 2>/dev/null || xdg-open "http://localhost:8000" 2>/dev/null) &
    exec python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --ws websockets
fi
