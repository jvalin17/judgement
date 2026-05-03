#!/usr/bin/env bash
# One-time host setup for Phase D (HTTPS).
#
# Run on the Oracle VM after the deployment files are pulled. Idempotent —
# safe to re-run.
#
# What this does:
#   1. Installs Caddy from the official Cloudsmith repo.
#   2. Drops our Caddyfile at /etc/caddy/Caddyfile.
#   3. Reloads Caddy so it auto-issues a Let's Encrypt cert.
#   4. Installs the DuckDNS keepalive systemd service + timer (every 6h).
#   5. Verifies port 443 is open at the host firewall level (ufw + iptables).
#
# Pre-requisites:
#   - DUCKDNS_TOKEN env var set when running this script (only needed first time).
#   - Port 443 already open in Oracle's VCN security list (done in Phase B).
#   - The Judgement container is running (docker compose is fine, it'll be
#     rebound to 127.0.0.1:8000 by the updated docker-compose.yml on next
#     deploy).

set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/judgement}"
DEPLOY_DIR="${REPO_DIR}/deployment"

if [[ -z "${DUCKDNS_TOKEN:-}" ]]; then
	if [[ -f /etc/duckdns-token ]]; then
		# Re-run path: token already saved.
		DUCKDNS_TOKEN="$(sudo cat /etc/duckdns-token)"
	else
		echo "ERROR: DUCKDNS_TOKEN env var not set and /etc/duckdns-token missing." >&2
		echo "First-time install: run as 'DUCKDNS_TOKEN=<your-token> bash install-caddy.sh'" >&2
		exit 1
	fi
fi

echo "==> 1/5 Installing Caddy"
if ! command -v caddy >/dev/null 2>&1; then
	sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
	curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
		| sudo gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
	curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
		| sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
	sudo apt-get update -y
	sudo apt-get install -y caddy
else
	echo "    Caddy already installed: $(caddy version)"
fi

echo "==> 2/5 Installing Caddyfile"
sudo install -m 644 "${DEPLOY_DIR}/Caddyfile" /etc/caddy/Caddyfile

echo "==> 3/5 Reloading Caddy (this triggers Let's Encrypt cert issue on first run)"
sudo systemctl enable --now caddy
sudo systemctl reload caddy || sudo systemctl restart caddy

echo "==> 4/5 Installing DuckDNS keepalive service + timer"
# Save the token where the service can read it (root-only).
echo "${DUCKDNS_TOKEN}" | sudo tee /etc/duckdns-token >/dev/null
sudo chmod 600 /etc/duckdns-token
sudo chown root:root /etc/duckdns-token

# Copy the update script to a system path.
sudo install -m 755 "${DEPLOY_DIR}/duckdns-update.sh" /usr/local/bin/duckdns-update.sh

# Service unit.
sudo tee /etc/systemd/system/duckdns-update.service >/dev/null <<'UNIT'
[Unit]
Description=DuckDNS dynamic DNS update for Judgement
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
EnvironmentFile=-/etc/default/duckdns-update
ExecStart=/bin/bash -c 'DUCKDNS_TOKEN=$(cat /etc/duckdns-token) /usr/local/bin/duckdns-update.sh'
UNIT

# Timer unit — every 6 hours, and once on boot.
sudo tee /etc/systemd/system/duckdns-update.timer >/dev/null <<'UNIT'
[Unit]
Description=Run DuckDNS update every 6 hours

[Timer]
OnBootSec=2min
OnUnitActiveSec=6h
Unit=duckdns-update.service
Persistent=true

[Install]
WantedBy=timers.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now duckdns-update.timer
sudo systemctl start duckdns-update.service || true

echo "==> 5/5 Ensuring host firewall allows 443"
if command -v ufw >/dev/null 2>&1; then
	sudo ufw allow 443/tcp || true
fi
# Oracle's default iptables drops 443 — make sure we explicitly allow it and persist.
if ! sudo iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null; then
	sudo iptables -I INPUT 6 -p tcp --dport 443 -j ACCEPT
fi
if command -v netfilter-persistent >/dev/null 2>&1; then
	sudo netfilter-persistent save || true
fi

echo
echo "==> Done. Verify with:"
echo "    sudo systemctl status caddy --no-pager"
echo "    sudo systemctl list-timers duckdns-update.timer"
echo "    curl -I https://judgement-game.duckdns.org/health"
