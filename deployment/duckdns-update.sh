#!/usr/bin/env bash
# Pings DuckDNS so our subdomain's A-record stays alive and pinned to this VM's
# public IP. DuckDNS auto-detects the source IP, so we don't have to hard-code
# 147.224.12.15 — useful if Oracle ever rotates it.
#
# Designed to be run by a systemd timer every 6h. Logs go to journalctl.
#
# Setup is handled by deployment/install-caddy.sh.

set -euo pipefail

DUCKDNS_DOMAIN="judgement-game"
DUCKDNS_TOKEN="${DUCKDNS_TOKEN:-}"

if [[ -z "${DUCKDNS_TOKEN}" ]]; then
	echo "DUCKDNS_TOKEN env var is not set" >&2
	exit 1
fi

response=$(curl -fsS "https://www.duckdns.org/update?domains=${DUCKDNS_DOMAIN}&token=${DUCKDNS_TOKEN}&ip=" || true)

if [[ "${response}" != "OK" ]]; then
	echo "DuckDNS update failed: ${response}" >&2
	exit 1
fi

echo "DuckDNS update OK ($(date -u +%FT%TZ))"
