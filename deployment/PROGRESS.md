# Judgement — Online Deployment Progress

This file is the single source of truth for the **online multiplayer deployment** effort. The assistant should re-read this at the start of any future session before doing anything, and update it at the end of each session.

---

## Goal

Run the existing FastAPI + React app on **one always-on internet server** so multiple desktop apps (and browsers) can connect to the same `GameManager` and play together. Persistence of stats / history will come later as a separate phase.

## Constraints (non-negotiable)

- **Strictly $0 / no monthly cost.** Credit card may be entered at signup for identity verification (Oracle), but no charges should occur.
- **Always-on** server (no sleeping free tiers like Render free web services).
- **WebSockets must work** end-to-end (the live game uses `wss://` for play).
- One HTTPS origin serves both the SPA and the API/WS (matches what the code already assumes).

## Decisions made

| Decision | Choice | Notes |
|---------|--------|-------|
| Hosting | **Oracle Cloud Always Free VM** | Genuinely $0 forever. Card required at signup. |
| Region | **US West (San Jose) — `us-sanjose-1`** | User is in Texas; San Jose chosen for ARM Always Free capacity + decent latency. **Home region cannot be changed later.** |
| VM shape (target) | **VM.Standard.A1.Flex (ARM Ampere)**, 1 OCPU + 6 GB RAM | Always Free eligible. Fallback if "out of host capacity": **VM.Standard.E2.1.Micro** (AMD). |
| OS | **Ubuntu 22.04 LTS** | (24.04 acceptable.) |
| Topology | **Single container** with embedded SPA + FastAPI + WebSockets, listening on port 80 (and later 443) | Matches existing `main.py` which serves `frontend/dist`. |
| Domain / TLS | **Defer.** Run on raw public IPv4 over HTTP first, then add HTTPS in Phase D. | Free path planned: DuckDNS subdomain + Cloudflare in front for free TLS. |
| Persistence | **Out of scope for now.** | Postgres (Neon/Supabase free tier) planned for stats phase later. |
| Repo layout | All deployment files live under **`deployment/`** at the repo root. | User explicitly requested a separate folder for deploy artifacts. |

---

## Phases (high-level plan)

- **Phase A — Oracle account + VM creation (USER does, assistant guides).**
- **Phase B — Add deployment files to repo (assistant does).**
- **Phase C — Deploy to the VM (assistant guides, user runs commands).**
- **Phase D — HTTPS + friendly URL ($0).** Deferred.
- **Phase E — Persistence (Postgres + stats).** Deferred.

---

## Progress log (most recent at top)

### Session ending 2026-04-29 ~21:15 CT
- VM created on Oracle Cloud:
  - Region: `us-sanjose-1` (San Jose, single-AD).
  - Shape: **VM.Standard.E2.1.Micro** (AMD Always Free) — Ampere A1.Flex was out of capacity in San Jose, fell back as planned.
  - Image: Ubuntu 24.04.
  - VCN: `judgement-vcn` created via the **VCN Wizard** ("Create VCN with Internet Connectivity"). The inline create-instance form would not let us assign a public IPv4 because the auto-created subnet ended up private; the wizard route fixed it.
  - Public IPv4: **`147.224.12.15`**
  - SSH user: `ubuntu`, key at `$HOME\.ssh\oracle_judgement` on the user's Windows PC.
- VCN security list updated: ingress for TCP 80 and TCP 443 from `0.0.0.0/0` added to the default security list of `judgement-vcn`. Port 22 was already open.
- SSH from the user's Windows laptop to `ubuntu@147.224.12.15` verified working.
- **Phase B done** — added all deployment files under `deployment/`:
  - `Dockerfile` (multi-stage: node:20-alpine builds frontend → python:3.13-slim runs uvicorn with `--proxy-headers --forwarded-allow-ips *`).
  - `.dockerignore`
  - `docker-compose.yml` (host port 80 → container 8000, `restart: unless-stopped`, healthcheck on `/health`, sets `JUDGEMENT_SERVER_MODE=1`).
  - `setup-vm.sh` (idempotent VM bootstrap: installs Docker, opens 80/443 in ufw + iptables, persists iptables, clones repo, builds + starts container).
  - `update.sh` (git pull + rebuild + prune).
  - `DEPLOY.md` (end-to-end runbook + troubleshooting).
- Hardened `backend/app/api/update.py`: added `_server_mode_enabled()` guard on `POST /api/update/apply`. When `JUDGEMENT_SERVER_MODE=1` is set (the case in the container), the endpoint returns 403 regardless of client IP. Closes the proxy-bypass risk noted in the previous session.
- **Stopped here.** Next session: **Phase C — push files to the repo, then deploy on the VM.** See "Next steps" below.

### Session ending 2026-04-28 ~22:50 CT
- Confirmed Python 3.13 is installed locally via `py` launcher (the bare `python` command on Windows still resolves to the MS Store stub — keep using `py` or the venv's `python.exe`).
- Local game runs successfully:
  - venv created at `c:\Professional\ai\judgement\.venv`
  - `pip install -r backend\requirements.txt` succeeded
  - `npm install` and `npm run build` in `frontend\` succeeded
  - `uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --ws websockets` runs and `/health` returns OK
- User attempted Oracle Cloud signup. Account took ~15 min to provision (expected). Initial "invalid username/password" was because the identity domain wasn't live yet.
- User signed in successfully after waiting and completing **2-step MFA** setup (TOTP via authenticator app — required by Oracle; recovery/backup codes should be stored safely by user).
- **Stopped here.** Next session: pick up at **Step 4 — Create the VM** (see "Next steps" below).

---

## Where we are right now

- ✅ Local dev environment verified working.
- ✅ Oracle Cloud account created and user can sign in.
- ✅ Region locked to **US West (San Jose)** as the home region.
- ⏳ MFA / 2-step verification: enabled. User should confirm backup codes are saved.
- ✅ SSH keypair generated on the user's Windows PC at `$HOME\.ssh\oracle_judgement`.
- ✅ VM created — shape `VM.Standard.E2.1.Micro`, public IP **`147.224.12.15`**, user `ubuntu`.
- ✅ Ports 80 / 443 opened in VCN security list (default SL of `judgement-vcn`).
- ✅ SSH into VM verified.
- ✅ Deployment files added to repo under `deployment/` (Phase B).
- ✅ Updater route hardened with `JUDGEMENT_SERVER_MODE` guard.
- ⬜ Deployment files committed and pushed to GitHub.
- ⬜ App deployed and reachable on `http://147.224.12.15/`.

---

## Next steps (resume here)

### Phase C — Deploy the app on the VM

> Steps C1–C3 below are what to do **right now** to get the server live. Steps 2–6 from the original plan (keypair, VM creation, security list, SSH test) are done — kept below for historical reference.

#### C1 — Commit and push the deployment files

On the user's Windows PC:

```powershell
cd c:\Professional\ai\judgement
git add deployment/ backend/app/api/update.py
git commit -m "Add Oracle VM deployment (Dockerfile, compose, scripts, runbook); harden updater"
git push origin main
```

#### C2 — Bootstrap the VM

SSH in and run the one-liner setup:

```powershell
ssh -i $HOME\.ssh\oracle_judgement ubuntu@147.224.12.15
```

Then on the VM:

```bash
curl -fsSL https://raw.githubusercontent.com/jvalin17/judgement/main/deployment/setup-vm.sh -o setup-vm.sh
bash setup-vm.sh
```

This installs Docker, opens 80/443 at the host firewall + iptables level (Oracle's default iptables blocks them), clones the repo, builds the image, and starts the container. Expect 3–6 minutes on first build (npm install + pip install + tsc/vite).

When it finishes, the script prints `docker compose ps` showing the container as `Up`.

#### C3 — Verify

From the user's Windows PC:

```powershell
curl http://147.224.12.15/health
```

Expected: `{"status":"ok"}`.

Then open `http://147.224.12.15/` in a browser. Should show the Judgement lobby. Try a 2-player game across two browsers / two devices to confirm WebSockets work end-to-end.

#### C4 — Updating the running server later

After pushing changes to `main`:

```powershell
ssh -i $HOME\.ssh\oracle_judgement ubuntu@147.224.12.15 "bash ~/judgement/deployment/update.sh"
```

(Reminder: this wipes active games — `GameManager` is in-memory.)

---

### Historical / completed setup steps (for reference)

#### Step 2 (DONE) — Generate SSH keypair on Windows

In PowerShell:

```powershell
mkdir $HOME\.ssh -ErrorAction SilentlyContinue
ssh-keygen -t ed25519 -f $HOME\.ssh\oracle_judgement -N '""'
Get-Content $HOME\.ssh\oracle_judgement.pub
```

- Private key: `C:\Users\<you>\.ssh\oracle_judgement` (NEVER share or commit).
- Public key: `C:\Users\<you>\.ssh\oracle_judgement.pub` (paste into Oracle when creating the VM).

### Step 3 — Confirm region in Oracle Console

Top-right of the console should show **US West (San Jose)**. Everything else must be created in that region.

### Step 4 — Create the VM (Compute Instance)

Console → **hamburger menu** → **Compute** → **Instances** → **Create instance**.

- **Name:** `judgement-server`
- **Compartment:** root tenancy compartment is fine for now.
- **Image:** Edit → Canonical Ubuntu → **Ubuntu 22.04** (or 24.04). Select.
- **Shape:** Edit → **Ampere** tab → **VM.Standard.A1.Flex** → 1 OCPU, 6 GB RAM. Select.
  - If "Out of host capacity": try a different Availability Domain (AD-1/AD-2/AD-3). If still no luck, fall back to **VM.Standard.E2.1.Micro** (AMD Always Free).
- **Networking:**
  - Create new VCN: `judgement-vcn`
  - Create new public subnet (default).
  - **Assign a public IPv4 address** — must be checked.
- **SSH keys:** Paste public keys → paste contents of `oracle_judgement.pub`.
- **Boot volume:** defaults are Always Free eligible.
- Click **Create**. Wait ~1–2 min for **RUNNING** state.

Record:
- **Public IPv4:** `__________________`
- **OS user:** `ubuntu`

### Step 5 — Open ports 80 and 443 in VCN security list

Instance page → Primary VNIC → click Subnet → Security Lists → **Default Security List for judgement-vcn** → **Add Ingress Rules**:

| Source CIDR | Protocol | Dest port | Description |
|-------------|----------|-----------|-------------|
| `0.0.0.0/0` | TCP | 80 | HTTP |
| `0.0.0.0/0` | TCP | 443 | HTTPS |

Port 22 (SSH) is open by default.

### Step 6 — SSH test

From PowerShell on the user's Windows PC:

```powershell
ssh -i $HOME\.ssh\oracle_judgement ubuntu@<PUBLIC_IP>
```

Accept fingerprint on first connect. Should land at `ubuntu@judgement-server:~$`. Type `exit` to leave.

### Step 7 — Hand back to assistant

Once Steps 4–6 are done, paste the **public IPv4** here and confirm SSH works. Assistant then proceeds with **Phase B**:
- Create deployment files in the `deployment/` folder:
  - `Dockerfile` (multi-stage: Node builds frontend → Python image runs uvicorn).
  - `.dockerignore`
  - `docker-compose.yml` (restart policy + port mapping)
  - `setup-vm.sh` (run once on the VM: install Docker, fetch repo, start container)
  - `update.sh` (pull latest + restart)
  - `DEPLOY.md` (exact end-to-end commands)
- Tighten the in-app updater route (`backend/app/api/update.py`) — its localhost check (`client.host == 127.0.0.1`) becomes meaningless behind any reverse proxy. Either disable it in "server mode" via env flag or require an explicit auth token.
- Then walk the user through Phase C deployment.

---

## Things to remember / gotchas

- **`python` on Windows = MS Store stub.** Always use the venv's `python.exe` or the `py` launcher.
- **In-memory `GameManager`.** Any container restart / redeploy wipes active games. Acceptable for friends; mention before each deploy.
- **ARM (Ampere) capacity in Oracle is volatile.** If denied, retry a different AD or fall back to AMD Always Free shape.
- **Oracle reclaims idle Always Free resources.** Real friend-traffic prevents this; long-idle VMs can be stopped. Plan a periodic ping (e.g. UptimeRobot free) once deployed.
- **Updater route security:** the existing `_is_localhost(request)` check in `backend/app/api/update.py` is unsafe behind a proxy — must be addressed before going public.
- **Oracle home region is permanent** — already locked to `us-sanjose-1`.
- **MFA backup codes:** user must save these somewhere safe (password manager). Losing the auth device without backup codes can lock the account.

---

## Quick reference

- **Oracle region:** US West (San Jose) — `us-sanjose-1`
- **Planned VM name:** `judgement-server`
- **Planned VCN:** `judgement-vcn`
- **OS user (Ubuntu image):** `ubuntu`
- **SSH key path (Windows):** `$HOME\.ssh\oracle_judgement` (private) / `.pub` (public)
- **Local dev URL:** http://127.0.0.1:8000
- **Local run command:**

```powershell
cd c:\Professional\ai\judgement
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --ws websockets
```

---

## Update protocol

At the **end of every session**, append a new entry to "Progress log" (most recent at top) with:
- Date/time stopping point.
- What was completed in this session.
- Where to resume next session (link to a step in this file).

At the **start of every session**, the assistant must read this file first.
