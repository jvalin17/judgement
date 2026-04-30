#!/usr/bin/env bash
# One-time setup on a fresh Ubuntu 22.04 / 24.04 Oracle VM.
# Run as the `ubuntu` user (NOT root). Re-running is safe (idempotent-ish).
#
#   curl -fsSL https://raw.githubusercontent.com/jvalin17/judgement/main/deployment/setup-vm.sh | bash
# OR after cloning:
#   bash deployment/setup-vm.sh

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/jvalin17/judgement.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"
APP_DIR="${APP_DIR:-$HOME/judgement}"

echo "==> Updating apt package index"
sudo apt-get update -y

echo "==> Installing prerequisites (curl, git, ufw)"
sudo apt-get install -y curl git ca-certificates ufw

if ! command -v docker >/dev/null 2>&1; then
    echo "==> Installing Docker via the official convenience script"
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER"
    echo "    (Added $USER to the docker group. You may need to log out and back in for this to take effect.)"
else
    echo "==> Docker already installed: $(docker --version)"
fi

echo "==> Configuring host firewall (ufw) to allow SSH/HTTP/HTTPS"
# Oracle's iptables defaults block these even after the VCN rules are open.
# We open them at the host level too so the container is actually reachable.
sudo ufw allow 22/tcp   || true
sudo ufw allow 80/tcp   || true
sudo ufw allow 443/tcp  || true
sudo ufw --force enable || true

echo "==> Punching ports 80/443 through Oracle's iptables (persists via netfilter-persistent)"
# Oracle Ubuntu images ship with an iptables INPUT chain that REJECTs
# everything except port 22 by default. We have to explicitly accept 80/443
# or no traffic ever reaches Docker, no matter what the VCN says.
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80  -j ACCEPT  || true
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT  || true
sudo apt-get install -y iptables-persistent netfilter-persistent
sudo netfilter-persistent save || true

if [[ ! -d "$APP_DIR/.git" ]]; then
    echo "==> Cloning $REPO_URL (branch $REPO_BRANCH) into $APP_DIR"
    git clone --branch "$REPO_BRANCH" "$REPO_URL" "$APP_DIR"
else
    echo "==> Repo already present at $APP_DIR, fetching $REPO_BRANCH and fast-forwarding"
    git -C "$APP_DIR" fetch origin "$REPO_BRANCH"
    git -C "$APP_DIR" checkout "$REPO_BRANCH"
    git -C "$APP_DIR" pull --ff-only origin "$REPO_BRANCH"
fi

cd "$APP_DIR"

echo "==> Building and starting the container"
# Use sg so this works in the same session even before the user logs out
# and back in to pick up the docker group membership.
sg docker -c "docker compose -f deployment/docker-compose.yml up -d --build"

echo
echo "==> Done."
echo "    Container status:"
sg docker -c "docker compose -f deployment/docker-compose.yml ps"
echo
echo "    Try it from your laptop:  curl http://<this-vm-public-ip>/health"
