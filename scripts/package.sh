#!/usr/bin/env bash
# Package Judgement as a standalone desktop app using PyInstaller.
# Produces: dist/Judgement.app (macOS) or dist/Judgement.exe (Windows)
set -e
cd "$(dirname "$0")/.."

echo "=== Packaging Judgement ==="
echo ""

# --- Detect platform ---
OS="$(uname -s)"
NATIVE_ARCH="$(uname -m)"
if [ "$OS" = "Darwin" ] && sysctl -n hw.optional.arm64 2>/dev/null | grep -q 1; then
    NATIVE_ARCH="arm64"
    PYTHON="arch -arm64 python3"
    PIP="arch -arm64 pip3"
else
    PYTHON="python3"
    PIP="pip3"
fi

echo "Platform: $OS $NATIVE_ARCH"

# --- Install Python dependencies ---
echo "Installing Python dependencies..."
$PIP install -r backend/requirements.txt -q

if ! $PYTHON -c "import PyInstaller" 2>/dev/null; then
    echo "Installing PyInstaller..."
    $PIP install pyinstaller
fi

if ! $PYTHON -c "import webview" 2>/dev/null; then
    echo "Installing pywebview..."
    $PIP install pywebview
fi

# --- Build frontend ---
echo ""
echo "Building frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi
npm run build
cd ..

# --- Verify frontend dist ---
if [ ! -f "frontend/dist/index.html" ]; then
    echo "ERROR: frontend/dist/index.html not found. Frontend build failed."
    exit 1
fi

# --- Run PyInstaller ---
echo ""
echo "Running PyInstaller..."

# Clean previous builds
rm -rf build/Judgement dist/Judgement dist/Judgement.app

$PYTHON -m PyInstaller \
    --name "Judgement" \
    --windowed \
    --onedir \
    --noconfirm \
    --clean \
    --add-data "frontend/dist:frontend/dist" \
    --add-data "backend/app/game/rounds:backend/app/game/rounds" \
    --hidden-import "backend" \
    --hidden-import "backend.app" \
    --hidden-import "backend.app.main" \
    --hidden-import "backend.app.api" \
    --hidden-import "backend.app.api.rest" \
    --hidden-import "backend.app.api.websocket" \
    --hidden-import "backend.app.api.schemas" \
    --hidden-import "backend.app.models" \
    --hidden-import "backend.app.models.card" \
    --hidden-import "backend.app.models.player" \
    --hidden-import "backend.app.models.game" \
    --hidden-import "backend.app.models.events" \
    --hidden-import "backend.app.models.session" \
    --hidden-import "backend.app.models.round_config" \
    --hidden-import "backend.app.game" \
    --hidden-import "backend.app.game.engine" \
    --hidden-import "backend.app.game.deck" \
    --hidden-import "backend.app.game.scorer" \
    --hidden-import "backend.app.game.trick_resolver" \
    --hidden-import "backend.app.game.validators" \
    --hidden-import "backend.app.game.round_manager" \
    --hidden-import "backend.app.game.round_config_loader" \
    --hidden-import "backend.app.ai" \
    --hidden-import "backend.app.ai.base" \
    --hidden-import "backend.app.ai.easy" \
    --hidden-import "backend.app.ai.medium" \
    --hidden-import "backend.app.ai.hard" \
    --hidden-import "backend.app.ai.card_play" \
    --hidden-import "backend.app.ai.hand_evaluator" \
    --hidden-import "backend.app.game_manager" \
    --hidden-import "uvicorn" \
    --hidden-import "uvicorn.logging" \
    --hidden-import "uvicorn.loops" \
    --hidden-import "uvicorn.loops.auto" \
    --hidden-import "uvicorn.protocols" \
    --hidden-import "uvicorn.protocols.http" \
    --hidden-import "uvicorn.protocols.http.auto" \
    --hidden-import "uvicorn.protocols.websockets" \
    --hidden-import "uvicorn.protocols.websockets.auto" \
    --hidden-import "uvicorn.lifespan" \
    --hidden-import "uvicorn.lifespan.on" \
    --hidden-import "websockets" \
    --hidden-import "websockets.legacy" \
    --hidden-import "websockets.legacy.server" \
    desktop/main.py

echo ""
echo "=== Build Complete ==="

if [ "$OS" = "Darwin" ]; then
    APP_PATH="dist/Judgement.app"
    if [ -d "$APP_PATH" ]; then
        SIZE=$(du -sh "$APP_PATH" | cut -f1)
        echo "Output: $APP_PATH ($SIZE)"
        echo ""
        echo "To run:  open dist/Judgement.app"
        echo "To install: cp -r dist/Judgement.app /Applications/"
    fi
else
    EXE_PATH="dist/Judgement/Judgement"
    if [ -f "$EXE_PATH" ] || [ -f "${EXE_PATH}.exe" ]; then
        echo "Output: dist/Judgement/"
        echo "To run: dist/Judgement/Judgement"
    fi
fi
echo ""
