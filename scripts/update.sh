#!/usr/bin/env bash
# Update Judgement — pull latest changes, rebuild, and reinstall.
set -e
cd "$(dirname "$0")/.."

echo "=== Updating Judgement ==="
echo ""

# --- Pull latest ---
echo "Pulling latest changes..."
BEFORE=$(git rev-parse HEAD)
git pull --ff-only
AFTER=$(git rev-parse HEAD)

if [ "$BEFORE" = "$AFTER" ]; then
    echo "Already up to date."
    if [ -t 0 ]; then
        read -p "Rebuild anyway? [y/N] " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Nothing to do."
            exit 0
        fi
    else
        echo "No changes, skipping rebuild."
        exit 0
    fi
else
    echo ""
    echo "New commits:"
    git log --oneline "$BEFORE".."$AFTER"
    echo ""
fi

# --- Rebuild ---
echo "Rebuilding..."
./scripts/package.sh

# --- Install ---
APP_SRC="dist/Judgement.app"
APP_DEST="/Applications/Judgement.app"

if [ -d "$APP_SRC" ]; then
    echo ""
    echo "Installing to /Applications/..."
    rm -rf "$APP_DEST"
    cp -r "$APP_SRC" "$APP_DEST"
    echo "Installed: $APP_DEST"
    echo ""
    echo "=== Update Complete ==="
    echo "Run: open /Applications/Judgement.app"
fi
