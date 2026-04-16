# Release Notes

All notable changes to Judgement are listed here. The newest release is at the top. Each section corresponds to a tag on the [Releases page](../../releases).

For the security model behind the update process, see the [Security Guidelines](README.md#security-guidelines) section of the README.

---

## Unreleased

> Bundled into the next tagged release. To install today, build from source (`./scripts/package.sh`) or use **Settings → Check for Updates** inside the installed app.

### Added
- **Central rangoli motif on the table.** A single, screen-resizing kolam pattern in muted antique gold replaces the previous layered radial gradients.
- **Custom app icon.** Lightweight J-card on a violet→magenta tile, used by Finder, the Dock, and the macOS app switcher.
- **In-app updater hardening.** The updater now correctly rebuilds when the source tree is ahead of the installed bundle, finds `npm` / `node` / `git` even when launched by `launchd`, and relaunches a fresh app instance after the old one exits.
- **Update endpoint is localhost-only.** `POST /api/update/apply` rejects any request not coming from `127.0.0.1` / `::1`. A remote attacker on the same Wi-Fi cannot trigger an update.
- **Settings panel.** Card-back gallery (9 designs), table-color picker (10 colors), animation-speed control, version + build-date display, and a "Check for Updates" button.
- **Hard AI overhaul.** Card counting, positional play, trump management, opponent modeling, and a personality system that gives each Hard opponent a slightly different play style per game.
- **8→4→8 dealing variant.** 10 rounds, max 6 players.

### Changed
- **Active-player highlight.** Replaced the overlapping "YOUR TURN" pill / banner with a subtle gold border on the active player's card. No more elements covering the player's name or hand.
- **Table look.** Flat single color (configurable in Settings) with one rangoli design centered behind the trick area.

### Fixed
- **"Next Round" required two clicks.** The scoreboard modal would briefly reopen after the first click because the acknowledgement state was reset before the next round actually started. Now the modal closes on the first click and stays closed until the next round begins.
- **In-app update silently doing nothing.** When the source tree was already pulled to `HEAD` but the installed bundle was older, `update.sh` exited "Already up to date" without rebuilding. Now it compares the installed bundle's SHA against source `HEAD` and rebuilds on mismatch.
- **In-app update failing with PEP 668.** The update subprocess inherited a stripped `PATH` from `launchd`, which resolved `python3` to Homebrew's externally-managed Python and broke `pip install`. The PATH is now ordered to prefer Xcode CLT's Python 3.9 (which ships pydantic and is not PEP 668-locked).
- **In-app update relaunch.** The app now spawns a detached helper that waits for the old process to exit before launching the fresh bundle, so launchd no longer treats the update as a no-op restart.
- **Round transition timing & AI crash resilience.** Smoother handoffs between rounds; AI errors no longer wedge the game.

### Security
- The `/api/update/apply` endpoint is now restricted to loopback (`127.0.0.1` / `::1`). This is a defence-in-depth fix: even though the desktop app only listens on localhost, an explicit check ensures a misconfigured or future remote-bound deployment cannot expose the updater.
- Removed an unauthorized `LICENSE` file (no license has been chosen for this project yet).

---

## v1.0.0 — initial public release

The first tagged release. Includes:

### Gameplay
- Single-player against AI (Easy / Medium / Hard).
- Three dealing variants: 10→1, 8→1→8, 10→1→10.
- Must-lose mode (all players are bid-restricted, not just the dealer).
- Standard 52-card deck, follow-suit enforcement, trump rotation (♠ → ♦ → ♣ → ♥).
- Scoring: bid met = +10 / +11 / +N×10; bid missed = same values negated.

### UI
- CSS-rendered playing cards (no image assets).
- Animated dealing, playing, trick collection.
- Live round-by-round scoreboard.
- Final-results screen with rankings.
- Mobile + desktop responsive layout.

### Backend
- FastAPI + WebSockets.
- Rules engine with strict layering (`models/` ← `game/` ← `ai/` ← `api/`); `game/` and `ai/` are pure logic with zero I/O.
- AI strategy pattern; `RoundContext` carries only public information so AIs cannot see other players' hands.
- 200+ automated tests (`python3 -m pytest backend/tests/ -v`).

### Desktop & deployment
- Standalone macOS + Windows app via PyInstaller (`./scripts/package.sh`).
- pywebview-based native window (no browser tab).
- GitHub Actions release workflow building macOS + Windows artifacts on tag push.
- Docker single-container deployment.

---

## How releases are cut

Today's release process is **tag-driven**:

1. The maintainer pushes a tag matching `v*` (e.g. `v1.0.0`).
2. `.github/workflows/release.yml` builds `Judgement-macOS.tar.gz` and `Judgement-Windows.zip` on hosted runners.
3. A GitHub Release is created for the tag with both artifacts attached and auto-generated changelog.

**Planned change** ([plans/auto_update.md](plans/auto_update.md)): switch to **push-to-`main` triggered** auto-releases with semantic version bumps, and have the in-app updater download those binaries (verified via SHA256) instead of rebuilding from source. This will allow non-developer users to receive updates without ever opening a terminal.
