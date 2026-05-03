# Deploying Judgement to the Oracle VM

End-to-end commands to take a fresh Oracle Ubuntu VM to a running Judgement server.

> Assumes you've completed Phase A (VM created, ports 80/443 open in the VCN security list, SSH key working). See `PROGRESS.md` for context.

---

## 1. SSH into the VM

From PowerShell on your Windows PC:

```powershell
ssh -i $HOME\.ssh\oracle_judgement ubuntu@<PUBLIC_IP>
```

You should land at `ubuntu@judgement-server:~$`.

## 2. First-time setup (one command)

On the VM, run:

```bash
curl -fsSL https://raw.githubusercontent.com/jvalin17/judgement/main/deployment/setup-vm.sh -o setup-vm.sh
bash setup-vm.sh
```

This installs Docker, opens ports 80/443 at the host firewall + iptables level, clones the repo to `~/judgement`, and starts the container.

When it finishes, you should see container status `Up`.

## 3. Verify from your laptop

```powershell
curl http://<PUBLIC_IP>/health
```

Expected response:

```json
{"status":"ok"}
```

Then open `http://<PUBLIC_IP>/` in a browser. You should see the Judgement lobby.

## 4. Updating later

After pushing changes to `main`:

```bash
ssh -i $HOME\.ssh\oracle_judgement ubuntu@<PUBLIC_IP>
bash ~/judgement/deployment/update.sh
```

This pulls latest, rebuilds the image, and restarts the container. Active games are wiped (in-memory `GameManager`).

## 5. Useful operational commands

All run on the VM, from `~/judgement`:

```bash
# Tail logs
docker compose -f deployment/docker-compose.yml logs -f --tail=200

# Restart without rebuilding
docker compose -f deployment/docker-compose.yml restart

# Stop
docker compose -f deployment/docker-compose.yml down

# Container resource use
docker stats judgement --no-stream

# Disk usage of Docker
docker system df
```

## 6. Troubleshooting

**`curl http://<IP>/health` hangs / times out from your laptop**
- VCN security list missing port 80 ingress rule — re-check Step 5 in `PROGRESS.md`.
- Host iptables blocking — re-run the iptables/ufw section of `setup-vm.sh`, or:
  ```bash
  sudo iptables -L INPUT -n --line-numbers | head -20
  ```
  Confirm there's an ACCEPT rule for `tcp dpt:80` BEFORE any REJECT rule.

**Container restarting in a loop**
```bash
docker compose -f deployment/docker-compose.yml logs --tail=100
```
Common causes: missing dependency in `requirements.txt`, code error in `backend/`, or port 80 already bound by something else (`sudo lsof -i :80`).

**`docker: permission denied`**
You haven't logged out/in since `setup-vm.sh` added you to the docker group. Either re-SSH, or prefix commands with `sg docker -c "..."` like the scripts do.

**Frontend loads but WebSocket fails**
Check the browser console. After Phase D, the page is served over HTTPS so the
client auto-uses `wss://`. If WS fails, tail Caddy: `sudo journalctl -u caddy -f`.

## 7. Phase D — HTTPS via DuckDNS + Caddy

Done as of session 2026-05-03. Runbook for re-applying or rebuilding from scratch:

```bash
# On the VM, after the repo is pulled:
DUCKDNS_TOKEN=<your-token> bash ~/judgement/deployment/install-caddy.sh
```

This installs Caddy from the official Cloudsmith repo, drops our `Caddyfile` at
`/etc/caddy/Caddyfile`, kicks off Let's Encrypt cert issuance, and sets up a
systemd timer that pings DuckDNS every 6h to keep the A-record alive.

The container's `docker-compose.yml` was changed from `0.0.0.0:80 → 8000` to
`127.0.0.1:8000 → 8000`. Caddy is now the sole public listener.

Verify:

```bash
sudo systemctl status caddy --no-pager
sudo systemctl list-timers duckdns-update.timer
curl -I https://judgement-game.duckdns.org/health
```

If Caddy fails to issue a cert, check `sudo journalctl -u caddy -n 200`. Common
causes: port 443 still blocked at Oracle VCN level, DNS not yet propagated, or
DuckDNS subdomain points at the wrong IP.

## 8. What's NOT done yet (Phase E)

- Persistence — `GameManager` is in-memory; redeploy = lose active games. Postgres comes in Phase E.
- The in-app updater (`/api/update/apply`) is **disabled** in server mode (env var `JUDGEMENT_SERVER_MODE=1`). Updates here happen via `update.sh` over SSH.
