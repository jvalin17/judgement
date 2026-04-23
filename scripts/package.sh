#!/usr/bin/env bash
# Package Judgement as a standalone desktop app using PyInstaller.
# Produces: dist/Judgement.app (macOS) or dist/Judgement/ (Windows/Linux)
#
# Uses Judgement.spec as single source of truth for all modules and data files.
set -e
cd "$(dirname "$0")/.."

echo "=== Packaging Judgement ==="
echo ""

# --- Detect platform ---
OS="$(uname -s)"
NATIVE_ARCH="$(uname -m)"
if [ "$OS" = "Darwin" ] && sysctl -n hw.optional.arm64 2>/dev/null | grep -q 1; then
    NATIVE_ARCH="arm64"
fi
echo "Platform: $OS $NATIVE_ARCH"

# --- Setup venv ---
if [ ! -d ".venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r backend/requirements.txt --quiet
    pip install pyinstaller pywebview --quiet
else
    source .venv/bin/activate
fi

# Ensure build tools are installed
pip install pyinstaller pywebview --quiet 2>/dev/null

# Verify pydantic
if ! python3 -c "from pydantic_core import __version__" 2>/dev/null; then
    echo "Fixing pydantic architecture..."
    pip install --force-reinstall pydantic pydantic-core --quiet
fi

# --- Build frontend ---
echo ""
echo "Building frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install --silent
fi
npm run build --silent
cd ..

if [ ! -f "frontend/dist/index.html" ]; then
    echo "ERROR: frontend build failed."
    exit 1
fi

# --- Write version info ---
echo ""
echo "Writing version info..."
GIT_SHA=$(git rev-parse --short HEAD)
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SOURCE_DIR=$(pwd)
cat > backend/app/version_info.json <<VEOF
{"git_sha": "$GIT_SHA", "build_date": "$BUILD_DATE", "source_dir": "$SOURCE_DIR"}
VEOF
echo "  Version: $GIT_SHA ($BUILD_DATE)"

# --- Generate icon if missing ---
if [ ! -f "assets/icon.icns" ] && [ -f "assets/icon.svg" ]; then
    echo "Generating app icon..."
    ./scripts/build_icons.sh
fi

# --- Run PyInstaller using the spec file ---
echo ""
echo "Running PyInstaller..."
python3 -m PyInstaller Judgement.spec --clean -y --log-level WARN 2>&1 | grep -E "completed|ERROR" | tail -5

# --- Verify ---
echo ""
echo "=== Build Complete ==="

if [ "$OS" = "Darwin" ]; then
    APP_PATH="dist/Judgement.app"
    if [ -d "$APP_PATH" ]; then
        SIZE=$(du -sh "$APP_PATH" | cut -f1)
        echo "Output: $APP_PATH ($SIZE)"
        echo ""
        echo "To run:     open dist/Judgement.app"
        echo "To install: cp -r dist/Judgement.app /Applications/"
        echo "To share:   zip -r Judgement-macOS.zip dist/Judgement.app"
    else
        echo "ERROR: Build failed — dist/Judgement.app not found"
        exit 1
    fi
else
    EXE_PATH="dist/Judgement/Judgement"
    if [ -f "$EXE_PATH" ] || [ -f "${EXE_PATH}.exe" ]; then
        echo "Output: dist/Judgement/"
        echo "To run: dist/Judgement/Judgement"
    else
        echo "ERROR: Build failed"
        exit 1
    fi
fi
echo ""
