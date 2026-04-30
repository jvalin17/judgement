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
Check the browser console. The current setup uses `ws://` (since we're on plain HTTP). HTTPS/WSS comes in Phase D.

## 7. What's NOT done yet (Phase D / E)

- HTTPS — currently plain HTTP. Browsers will warn about insecure connection. Cloudflare in front (free) will fix this in Phase D.
- Persistence — `GameManager` is in-memory; redeploy = lose active games. Postgres comes in Phase E.
- The in-app updater (`/api/update/apply`) is **disabled** in server mode (env var `JUDGEMENT_SERVER_MODE=1`). Updates here happen via `update.sh` over SSH.
