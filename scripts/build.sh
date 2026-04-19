#!/bin/bash
# Build Judgement.app — complete, ready-to-distribute macOS app
#
# Usage: ./scripts/build.sh
# Output: dist/Judgement.app (double-click to run)

set -e
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

echo "=== Building Judgement.app ==="

# 1. Setup Python venv
if [ ! -d ".venv" ]; then
  echo "[1/4] Creating virtual environment..."
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip --quiet
  pip install -r requirements.txt --quiet
  pip install pyinstaller pywebview --quiet
else
  source .venv/bin/activate
  echo "[1/4] Virtual environment ready"
fi

# Ensure build tools are installed
pip install pyinstaller pywebview --quiet 2>/dev/null

# 2. Build frontend
echo "[2/4] Building frontend..."
cd "$ROOT/frontend"
npm ci --silent 2>/dev/null || npm install --silent
npm run build --silent
cd "$ROOT"

# 3. Build app bundle
echo "[3/4] Packaging app..."
python3 -m PyInstaller Judgement.spec --clean -y --log-level WARN 2>&1 | grep -E "INFO|ERROR|WARNING" | tail -5

# 4. Verify
if [ -d "dist/Judgement.app" ]; then
  SIZE=$(du -sh "dist/Judgement.app" | cut -f1)
  echo "[4/4] Done! dist/Judgement.app ($SIZE)"
  echo ""
  echo "To run:  open dist/Judgement.app"
  echo "To share: zip -r Judgement.zip dist/Judgement.app"
else
  echo "[4/4] ERROR: Build failed — dist/Judgement.app not found"
  exit 1
fi
