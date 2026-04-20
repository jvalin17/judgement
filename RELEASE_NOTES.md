# Release Notes

All notable changes to Judgement are listed here. The newest release is at the top. Each section corresponds to a tag on the [Releases page](../../releases).

For the security model behind the update process, see the [Security Guidelines](README.md#security-guidelines) section of the README.

---

## Unreleased

> Bundled into the next tagged release. To install today, build from source (`./scripts/package.sh`) or use **Settings → Check for Updates** inside the installed app.

*Nothing yet.*

---

## v3.0.0 — ML learning, community data, multiplayer, challenge mode

### Added
- **ML learning engine.** kNN-based SmartHardAI that learns from game winners. Decisions are collected during play and winners' strategies are saved to train future AI opponents.
- **Community data sharing.** Share anonymized game decisions via GitHub Releases. Download community data to improve your local AI. Settings panel shows data counts and share/download controls.
- **Multiplayer.** Create or join rooms with a code. Lobby browser, quick-join, and host controls. WebSocket-based real-time play with reconnection support.
- **Player personas.** 75 personas across 7 categories. After each game, human players receive a persona based on their play style fingerprint (11-dimensional trait vector with exponential decay).
- **Challenge mode.** Toggle in the lobby for players who want full-strength AI (disables difficulty nerfing).
- **AI difficulty nerfing.** ~25% of games, AI silently plays one level softer (Hard→Medium, Medium→Easy) to give players more wins. Skipped for the first 2 games. Disabled in challenge mode.
- **Victory sounds.** Web Audio API synthesized fanfare for winners, warm tones for runners-up. No audio files needed.
- **6 dealing variants.** Added 8→4→8 (10 rounds, max 6 players) and 8→4 (5 rounds, max 6 players).
- **Score visible during bidding.** Cumulative score shown in BidSelector and bid table.
- **Trait bar legend.** Explains colored fill (your traits) vs white markers (persona baseline) on the persona card.
- **Frontend test suite.** 47 Vitest + React Testing Library tests covering BidSelector, PlayerHand, Scoreboard, FinalResults, OpponentArea, and variant config.
- **CI gates updates.** In-app updater checks GitHub CI status before offering updates. Shows "being tested" message when CI is failing.

### Changed
- **Opponent area redesign.** Split-circle badge shows won/bid status (e.g. "1/3") in top half and cumulative score in bottom half. Replaces the old initials avatar + separate stat badge.
- **Seat positions.** Opponents no longer overlap the round info bar. Top-row seats pushed down and spread to avoid the trump card display.
- **ML code consolidated.** All machine learning code unified under `backend/app/ml/` (was split across `ai/learning/` and `analysis/`).
- **Persona card moved below scores.** Play style card now appears after the final score list, not before.
- **Scoreboard columns.** Renamed to aviation theme: Pilot, Flights, Landings, Score.
- **310 backend tests, 47 frontend tests** (357 total).

### Fixed
- **Lobby error messages.** Show friendly messages instead of raw JSON when room creation or joining fails.
- **Multiplayer room creation.** Pass `auto_start=false` so rooms wait for players instead of starting immediately.
- **8→4 variant server error.** Missing round sequence and max_players mapping for the new variant.
- **Exhaustive variant tests.** Every `DealingVariant` enum value is now tested for round sequence, max_players, and JSON config consistency.

### Security
- Update endpoint remains localhost-only.
- Community data sharing uploads only anonymized numeric feature vectors. No player names, IDs, or hand data.

---

## v2.0.0

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
