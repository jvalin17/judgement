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
# --env-file loads secrets (JUDGEMENT_GITHUB_TOKEN) from deployment/.env
ENV_FLAG=""
if [ -f deployment/.env ]; then
    ENV_FLAG="--env-file deployment/.env"
fi
# Pass git SHA and build date so the container knows its version
export GIT_SHA="$(git rev-parse --short HEAD)"
export BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
sg docker -c "GIT_SHA=$GIT_SHA BUILD_DATE=$BUILD_DATE docker compose -f deployment/docker-compose.yml $ENV_FLAG up -d --build"

echo "==> Pruning old images to save disk"
sg docker -c "docker image prune -f"

echo
echo "==> Done. Status:"
sg docker -c "docker compose -f deployment/docker-compose.yml ps"
