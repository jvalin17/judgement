#!/usr/bin/env bash
# Update Judgement — pull latest changes, rebuild, and reinstall.
set -e
cd "$(dirname "$0")/.."

echo "=== Updating Judgement ==="
echo ""

# --- Pull latest ---
echo "Pulling latest changes..."
BEFORE=$(git rev-parse --short HEAD)
git pull --ff-only
AFTER=$(git rev-parse --short HEAD)

# --- Detect if installed app is in sync with source ---
# The previous logic only rebuilt when `git pull` fetched new commits, so if
# someone had already pulled manually (source HEAD ahead of installed app),
# the script would exit "No changes" and the stale app would never refresh.
# Fix: also rebuild when the installed bundle's SHA != source HEAD.
INSTALLED_VERSION="/Applications/Judgement.app/Contents/Resources/backend/app/version_info.json"
INSTALLED_SHA=""
if [ -f "$INSTALLED_VERSION" ]; then
    INSTALLED_SHA=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('git_sha',''))" "$INSTALLED_VERSION" 2>/dev/null || true)
fi

if [ "$BEFORE" != "$AFTER" ]; then
    echo ""
    echo "New commits pulled:"
    git log --oneline "$BEFORE".."$AFTER"
    echo ""
elif [ -n "$INSTALLED_SHA" ] && [ "$INSTALLED_SHA" != "$AFTER" ]; then
    echo "Source already at $AFTER, but installed app is at $INSTALLED_SHA. Rebuilding to sync..."
elif [ -z "$INSTALLED_SHA" ]; then
    echo "No installed app detected at /Applications/Judgement.app — building fresh."
else
    echo "Already up to date (source $AFTER == installed $INSTALLED_SHA)."
    if [ -t 0 ]; then
        read -p "Rebuild anyway? [y/N] " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Nothing to do."
            exit 0
        fi
    else
        echo "Nothing to rebuild."
        exit 0
    fi
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
