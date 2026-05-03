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

### Session 2026-05-03 — Mobile fit / safe-area pass (pre-Phase-D)
- User reported the app doesn't auto-scale on iPhone — UI cut off on both iPhone 14 and iPhone 17, in both portrait and landscape, both lobby and game board.
- Root causes identified by reading layout CSS:
  1. `index.html` had no `viewport-fit=cover` and no safe-area awareness, so positioned chrome (round pill at `top:10px`, `bottom:10px`; `topButtons`; settings button at `top:12px`) sat under the Dynamic Island / home indicator on notched iPhones.
  2. `.gameBoard` is `height: 100dvh; overflow: hidden` with everything absolutely positioned. On a short landscape phone (~390px tall), the bid bar (`bottom: card-height + 56px = 160px`) plus the trick area at `top: 45%` plus the hand pinned to `bottom: 0` overflow and get clipped.
  3. `.handCards` had `overflow: visible` with negatively-margined cards — 7+ cards × 72px - 10px overlap ≈ 444px clipped on a 390px phone with no scroll fallback.
  4. No landscape-specific compression for short viewports.
- Changes (all CSS / one HTML):
  - `frontend/index.html`: viewport now `width=device-width, initial-scale=1.0, viewport-fit=cover, maximum-scale=1.0, user-scalable=no`. Added `theme-color`, `apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style=black-translucent`.
  - `frontend/src/styles/global.css`: added `--safe-top/right/bottom/left` vars sourced from `env(safe-area-inset-*)` with `0px` fallback; added `overscroll-behavior: none` and `-webkit-tap-highlight-color: transparent` on `body`.
  - `frontend/src/styles/game.module.css`: padded `roundIslandTop/Bottom`, `bidBar`, `playerInfo`, `handArea` by safe-area insets; added `touch-action: manipulation` on `.gameBoard`. Made `.handCards` `overflow-x: auto` (with hidden scrollbar) so an oversized hand scrolls horizontally instead of clipping. Added a `@media (orientation: landscape) and (max-height: 500px)` block that shrinks `--card-width/height` to 56/80, lifts the trick area, tightens the bid bar / player info, and a portrait `max-height: 700px` block that pulls the bottom stack closer to the cards.
  - `frontend/src/styles/settings.module.css`: `.topButtons` (× and gear) padded by safe-area top/right.
  - `frontend/src/styles/lobby.module.css`: `.lobby` padding wraps each side with `safe-area-inset-*`; `.settingsButton` (control tower) offset by safe-area.
  - `frontend/src/styles/waiting.module.css`: `.waitingRoom` padded by safe-area on all four sides.
  - `frontend/src/styles/common.module.css`: `.modalOverlay` padded by safe-area; `.modal` switched from `90vh` to `90dvh` so it uses the dynamic viewport (no clip when iOS toolbars expand).
- `npm run build` clean. No lint errors.
- Next: commit, push to `deploy/oracle-vm`, run `update.sh` on the VM, retest on iPhone 14 + 17 (portrait & landscape). Then resume Phase D (HTTPS via DuckDNS + Caddy).

### Session 2026-04-30 (late) — iPhone 17 hang re-diagnosed, Phase D unblocks it
- User corrected earlier assumption: **both** iPhone 14 (works) and iPhone 17 (broken) are on iOS 26 / Safari 26. So OS version isn't the differentiator. Rules out the "iOS 26 broke ws://" theory.
- Other observations: iPhone 17 in Safari, no Lockdown Mode, no Private Relay (no iCloud+), no VPN/DNS profile, same Wi-Fi as iPhone 14. When iPhone 17 joins a room created on iPhone 14, the host (iPhone 14) sees the joiner appear → REST `/join` works fine → server emitted `player_joined`. But iPhone 17 itself sees an empty roster (not even self).
- **Diagnostic added**: connection-status badge in `WaitingRoom.tsx` (commit `3511eed`). Shows Connecting / Connected / Reconnecting / Disconnected pill above the join code, sourced from existing `connectionStatus` in `GameContext`. Wired through `App.tsx` → `WaitingRoomScreen`. Useful long-term too.
- **Cache headers fix** (commit `09a51af`): added explicit `Cache-Control` on the FastAPI side — `no-cache, must-revalidate` on `index.html` and SPA fallbacks, `public, max-age=1y, immutable` on `/assets/*` (safe because Vite content-hashes them). Verified live: `curl -D - http://147.224.12.15/` → no-cache, `/assets/index-*.js` → immutable. Future deploys are picked up on first navigation; no more "is this a cache issue?" rabbit holes.
- **Result on iPhone 17 after cache clear:** pill says "Connecting" forever, roster stays empty. So the WebSocket truly never opens — Safari (or some per-device WebKit policy on iPhone 17) is silently blocking `ws://` to a bare-IP origin. iPhone 14 on the same OS doesn't hit it.
- Earlier "skip persistence and do Phase D" path was the right one after all — TLS fixes this for free because `services/websocket.ts:81` already auto-uses `wss:` when `window.location.protocol === "https:"`. No frontend change needed once we have HTTPS.
- **Stopped here.** Next session resume point: pick a Phase D approach (see below).

### Session 2026-04-30 — iPhone 17 hang diagnosed, deferred
- User report: game works on iPhone 14, but on iPhone 17 (iOS 26 / Safari 26) the screen gets stuck at "Waiting Room" and never transitions to bidding. Same Wi-Fi as the iPhone 14, Private Relay off, happens for both host and joiner roles, also for single-player vs bots.
- Likely root cause: **Safari 26 refuses (or silently fails) `ws://` WebSocket connections from a top-level `http://<bare-IP>` page.** Page loads fine (plain HTTP fetch + REST works → WaitingRoom renders), but `new WebSocket("ws://147.224.12.15/ws/...")` in `frontend/src/services/websocket.ts:81-85` never reaches `onopen`, so no `round_started` event ever arrives. iPhone 14 (iOS 17/18) is grandfathered into the looser behavior. Single-player hanging at waiting room is consistent because the same code path requires the WS for `round_started`.
- Why we didn't fully confirm: would need Safari Web Inspector via a Mac + USB. Diagnosis is well-grounded enough; the fix is the same either way.
- Fix (deferred): **Phase D — HTTPS.** Once the site serves over `https://` with a real cert, the WS code already picks `wss:` automatically (`window.location.protocol === "https:"` check in `services/websocket.ts:81`). No frontend code change needed.
- Decision: skip for now, continue to Phase E (persistence). User accepts iPhone 17 users hitting the site via iPhone 14 / desktop browser until Phase D is done.
- Open item: when we do Phase D, retest on iPhone 17 first thing — it should "just work" with `wss://`.

### Session 2026-04-30 — Bot dropdown readability fix
- User reported the difficulty `<select>` popup showed blank entries until hovered (only the selected default "Medium" was visible).
- First attempt set `option { background: var(--color-surface); color: var(--color-text); }` — didn't help.
- Root cause: theme's `--color-surface` is `rgba(0,0,0,0.2)` (semi-transparent, designed to composite over the dark gradient body). The native `<option>` popup is rendered by the OS on a white backdrop, so the transparent surface composited to white and the near-white `--color-text` (`#ecf0f1`) text became invisible. The OS hover highlight is opaque, which is why hovering "fixed" it.
- Fix in `frontend/src/styles/waiting.module.css`: hardcoded opaque colors on `.botSelect option` — `background-color: #2c3e50` (matches `--color-primary`) and `color: #ecf0f1`. No JS changes.
- Built, committed, pushed to `deploy/oracle-vm`, redeployed via `update.sh` on the VM. User hard-refreshed and confirmed all three difficulties are now readable.
- Next: awaiting next issue from user's list.

### Session 2026-04-30 — Add Bot in multiplayer waiting room
- New feature: host can add AI players to a multiplayer room before starting, mirroring the single-player setup flow.
- Backend:
  - `GameManager.add_ai_player(game_id, difficulty, name=None)` — creates the Player, calls `engine.add_player`, registers the strategy in `ai_strategies` (without this the bot would sit idle on its turn), and broadcasts `player_joined` via the same callback path used for humans.
  - Auto-picks names from `AI_SWEETS_NAMES`, falls back to `Bot N` if all sweets are taken.
  - New endpoint `POST /api/games/{game_id}/add-bot` — host-only (checks `host_player_id`), lobby-only, capacity-checked. New schema `AddBotRequest { player_id, difficulty, name? }`.
- Frontend:
  - `addBot(gameId, playerId, difficulty)` in `services/api.ts`.
  - `WaitingRoom.tsx`: when `isHost && emptySlots > 0`, renders a difficulty dropdown (Easy / Medium / Hard, default Medium) + "Add Bot" button. On click, POSTs to `/add-bot`; the server's `player_joined` event flows through the existing WS handler, so the new bot appears in every connected client's roster automatically (no extra reducer wiring).
  - CSS additions (`.botRow`, `.botLabel`, `.botSelect`) styled to match the dashed empty-slot aesthetic.
- Per user choices: per-bot difficulty picker, auto-named, no remove button, no "fill all" button.
- Verified locally: smoke test created a game, added Hard + Easy bots, both got strategies, both `player_joined` events fired, game started successfully into bidding phase. Frontend `tsc -b && vite build` clean. No lints.
- Next: commit, push to `deploy/oracle-vm`, redeploy on VM, two-browser test.

### Session 2026-04-30 — Player list desync fix verified live
- Re-read progress, confirmed the `useGame.ts` fix (`handlePlayerJoined` / `handlePlayerLeft` mirror into both `lobbyPlayers` and `players`) was already committed (`1452a91`) and pushed to `deploy/oracle-vm`.
- Ran `deployment/update.sh` on the VM — `Already up to date`, all layers cached, container restarted cleanly. `/health` → `{"status":"ok"}`.
- User verified two-browser end-to-end: host now sees joiners in waiting room AND in-game. Multiplayer lobby + player-list bugs both closed.
- Next: user has more issues to fix before moving to Phase D / E. Awaiting list.

### Session ending 2026-04-29 ~22:25 CT — Player list desync after game start
- After deploying the previous fix, joiners now appear in the host's *waiting room* but disappear once the game starts: host sees themselves only, joiners see everyone correctly.
- Root cause: the frontend keeps two parallel player lists in `useGame.ts` reducer state — `lobbyPlayers` (drives `WaitingRoom`) and `players` (drives `GameBoard`, `BidSelector`, scoreboard). The `player_joined` event handler only updated `lobbyPlayers`, not `players`. Joiners receive the `connected` event on their WS open which seeds `state.players` with the full roster, so they look fine. The host opened their WS when they were alone, so `state.players` froze at `[host]` and never grew.
- Fix in `frontend/src/hooks/useGame.ts handlePlayerJoined`: also append the new player to `state.players` (with `player_type=HUMAN`, `ai_difficulty=null`). Symmetrically, `handlePlayerLeft` now removes from both lists.
- **Stopped here.** Next: commit, push, redeploy on the VM, retest with two browsers — host should see joiners in the waiting room AND in the game itself.

### Session ending 2026-04-29 ~22:10 CT — Multiplayer lobby bug fix
- User report: when host creates a "Play with Friends" room and a second player joins via room code, the host doesn't see the joiner appear in the waiting room, and there's no way to start the game.
- Root cause: `POST /api/games/{game_id}/join` in `backend/app/api/rest.py` was calling `engine.add_player(player)` directly, bypassing `GameManager.add_human_player()`. The latter is the only thing that emits a `player_joined` event. Without that event, the host's WebSocket never broadcasts the new joiner, `lobbyPlayers` stays at length 1, and `WaitingRoom.tsx` (which renders the "Start Now" button only when `isHost && players.length >= 2`) never shows the start button. So both reported symptoms (no joiner visible + game never starts) trace to one missing event.
- Fix (`backend/app/api/rest.py` `join_game`): replaced `engine.add_player(player)` with `_manager.add_human_player(engine.state.game_id, player)`. One-line change, no schema change. The frontend already has the `player_joined` handler wired up correctly (`useGame.ts handlePlayerJoined`) and `WaitingRoom` will show the "Start Now" button as soon as the joiner appears.
- Quick-join (`/api/lobby/quick-join`) was already going through the manager — not affected.
- **Stopped here.** Next: commit, push to `deploy/oracle-vm`, redeploy on the VM, retest with two browsers.

### Session ending 2026-04-29 ~21:55 CT — SERVER IS LIVE 🎉
- Pushed `deployment/` + updater hardening to a new branch `deploy/oracle-vm` on `jvalin17/judgement`. (User `anurag012` was added as a collaborator with write access by the repo owner.)
- Bootstrapped the VM with `setup-vm.sh` (passing `REPO_BRANCH=deploy/oracle-vm`). Everything ran cleanly except the Docker image build, which initially failed at `npm ci` with `EUSAGE — Missing: @emnapi/core@1.10.0 from lock file`.
  - Root cause: local Node was 22.22 / npm 11.6, Dockerfile pinned `node:20-alpine`. The lockfile generated by npm 11 included entries that npm 10 considered missing.
  - Fix: bumped Dockerfile to `node:22-alpine` AND regenerated `frontend/package-lock.json` from a clean `node_modules` to guarantee consistency. Committed both.
- Re-ran `docker compose up -d --build` on the VM — built and started successfully.
- Verified:
  - `docker compose ps` → `judgement` Up.
  - `curl http://127.0.0.1/health` on VM → `{"status":"ok"}`.
  - `curl http://147.224.12.15/health` from laptop → `{"status":"ok"}`.
  - `http://147.224.12.15/` loads the Judgement SPA in a browser.
- ⏳ End-to-end WebSocket multiplayer test (two clients across two devices) — handed off to user to verify.
- Side note on Windows tooling: `npm` directly errors with "running scripts is disabled"; use `npm.cmd` from PowerShell or `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. PowerShell `curl` is `Invoke-WebRequest` and prompts to parse content; use `curl.exe` for plain output.

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

## RESUME HERE (next session, 2026-05-01)

We paused mid-discussion of **Phase D (HTTPS)**. Context:

- Persistence work (Phase E, Supabase) was about to start, but user reported the iPhone 17 hang.
- Diagnosis: WebSocket on iPhone 17 never opens (`ws://` to bare-IP `147.224.12.15` blocked silently by Safari, even though iPhone 14 on same iOS 26 / same Wi-Fi works). Connection badge stays at "Connecting".
- Conclusion: do **Phase D first**, then Phase E. Phase D gives us `wss://`, which fixes iPhone 17 with zero frontend changes.

**The pending question** I asked the user before we paused — they should answer this first thing tomorrow:

> Domain strategy for Phase D? Options:
> 1. **DuckDNS + Caddy on the VM (Let's Encrypt auto-issue).** ~20 min, $0, end-to-end TLS, no third-party CDN. **My recommendation.**
> 2. **DuckDNS + Cloudflare Flexible mode.** Cloudflare proxies HTTPS → HTTP on the last hop. Adds CDN benefits, slightly fiddlier DNS setup.
> 3. **Buy a cheap .com via Cloudflare Registrar** (~$10/yr at cost). Cleanest URL, breaks the strict $0 constraint.

**My pick if user defers:** Option 1 (DuckDNS + Caddy). Reasoning:
- Strict $0, no extra account beyond one-click DuckDNS login.
- Caddy auto-issues + auto-renews Let's Encrypt certs with literally one config line. Battle-tested for WebSockets on free-tier VMs.
- End-to-end TLS without manually managing certs.
- Avoids Cloudflare's WS frame-size and idle-timeout quirks (100s default — would need tuning for our long-lived game sessions).
- Plays cleanly with Phase E later (Supabase auth wants HTTPS origin).

**Plan if we go Option 1:**
1. User claims a DuckDNS subdomain (e.g. `judgement-anurag.duckdns.org`) and pastes the token here.
2. Open port 443 on Oracle VCN security list (port 80 already open).
3. On the VM: install Caddy, write a `/etc/caddy/Caddyfile` with `judgement-anurag.duckdns.org { reverse_proxy localhost:8000 }`. Caddy auto-issues + renews the cert. Update `docker-compose.yml` to bind to `127.0.0.1:8000` instead of `0.0.0.0:80` so only Caddy is publicly exposed.
4. Add a tiny systemd timer (or Caddy module) to refresh the DuckDNS A-record every 6h pointing at `147.224.12.15` (the IP doesn't change, but DuckDNS requires periodic updates to keep the subdomain alive).
5. Test on iPhone 17 first — pill should show "Connected" (now via wss://), game should start normally.
6. Update PROGRESS.md, mark Phase D done, then start Phase E (Supabase persistence — see plan below in earlier section).

**Phase E status:** plan already agreed with user (name-only identity, persist stats + history + accounts + ML data, Supabase Postgres free tier, three-commit rollout). User needs to create the Supabase project and paste the pooler connection string back. **Not blocked by Phase D** — could proceed in parallel, but doing Phase D first is cleaner for the iPhone 17 unblock + future auth.

**Open / parked items not lost:**
- iPhone 17 multiplayer hang (this whole thread). Will be retested as Phase D's first verification step.
- Connection-status badge in WaitingRoom — already shipped, but we may want to add the same indicator to the in-game header (currently only shown during waiting room). Defer until requested.

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
- ✅ Deployment files committed and pushed to GitHub (branch `deploy/oracle-vm`).
- ✅ App deployed and reachable on `http://147.224.12.15/` (browser confirmed).
- ✅ End-to-end WebSocket multiplayer test across two devices — verified working 2026-04-30.
- ⬜ Phase D — HTTPS via Cloudflare (deferred).
- ⬜ Phase E — Postgres persistence + stats (deferred).

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
