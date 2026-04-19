#!/bin/bash
# Start the Judgement game server using the project venv

set -e
cd "$(dirname "$0")"

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip --quiet
  pip install -r requirements.txt --quiet
  echo "Dependencies installed."
else
  source .venv/bin/activate
fi

# Kill any existing server on port 8000
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true

echo "Starting server at http://localhost:8000"
python3 -m uvicorn backend.app.main:app --reload --ws websockets
