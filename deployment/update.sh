#!/usr/bin/env bash
# Pull the latest code and rebuild the running container.
# Run on the VM:  bash ~/judgement/deployment/update.sh

set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/judgement}"

cd "$APP_DIR"

echo "==> Pulling latest from git"
git pull --ff-only

echo "==> Rebuilding and restarting container"
# `sg docker` so this still works if the user hasn't re-logged-in since setup.
sg docker -c "docker compose -f deployment/docker-compose.yml up -d --build"

echo "==> Pruning old images to save disk"
sg docker -c "docker image prune -f"

echo
echo "==> Done. Status:"
sg docker -c "docker compose -f deployment/docker-compose.yml ps"
