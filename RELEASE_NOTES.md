# Release Notes

All notable changes to Judgement are listed here. The newest release is at the top. Each section corresponds to a tag on the [Releases page](../../releases).

For the security model behind the update process, see the [Security Guidelines](README.md#security-guidelines) section of the README.

---

## Unreleased

> Bundled into the next tagged release. To install today, build from source (`./scripts/package.sh`) or use **Settings → Check for Updates** inside the installed app.

*Nothing yet.*

---

## v3.0.1

### Fixed
- **macOS Intel support.** Build now runs on Intel runner — the binary works on both Intel and Apple Silicon Macs (via Rosetta).
- **macOS minimum version.** Lowered from Monterey (12) to Catalina (10.15).

---

## v3.0.0 — ML learning, community data, multiplayer, challenge mode

### Added
- **ML learning engine.** AI that learns from game winners and gets stronger over time.
- **Community data sharing.** Share anonymized game decisions to help train better AI. Download community data from other players via Settings.
- **Multiplayer.** Create or join rooms with a code. Lobby browser, quick-join, and host controls.
- **Player personas.** 75 personas across 7 categories. After each game, receive a play style persona based on how you played.
- **Challenge mode.** Toggle in the lobby for players who want full-strength AI.
- **Victory sounds.** Celebratory fanfare when you win, warm tones for runners-up.
- **New dealing variants.** Added 8→4→8 (10 rounds, max 6 players) and 8→4 (5 rounds, max 6 players). Now 6 variants total.
- **Score visible during bidding.** Cumulative score shown alongside the bid selector.
- **Trait bar legend.** Explains what the bars mean on the persona card.

### Changed
- **Opponent display.** Split-circle badge shows won/bid status (e.g. "1/3") and cumulative score at a glance.
- **Persona card moved below scores.** Play style card now appears after the final score list.
- **Scoreboard columns.** Renamed to aviation theme: Pilot, Flights, Landings, Score.

### Fixed
- **Lobby error messages.** Show friendly messages instead of raw JSON when room creation or joining fails.
- **Multiplayer room creation.** Rooms now wait for players instead of starting immediately.
- **8→4 variant crash.** Fixed missing configuration for the new variant.

### Security
- Update endpoint remains localhost-only.
- Community data sharing uploads only anonymized numeric feature vectors. No player names, IDs, or hand data.

---

## v2.0.0

### Added
- **Central rangoli motif on the table.** Decorative kolam pattern in muted antique gold.
- **Custom app icon.** J-card on a violet→magenta tile for Finder, Dock, and app switcher.
- **Settings panel.** Card-back gallery (9 designs), table-color picker (10 colors), animation-speed control, version display, and a "Check for Updates" button.
- **Smarter Hard AI.** Card counting, positional play, trump management, opponent modeling, and a personality system that gives each Hard opponent a unique play style.
- **8→4→8 dealing variant.** 10 rounds, max 6 players.

### Changed
- **Active-player highlight.** Subtle gold border on the active player's card instead of overlapping banners.
- **Table look.** Flat single color (configurable in Settings) with one rangoli design.

### Fixed
- **"Next Round" required two clicks.** Now closes on the first click.
- **In-app updates.** Reliably detects when an update is needed and relaunches the fresh app.
- **Smoother round transitions.** AI errors no longer wedge the game.

---

## v1.0.0 — initial public release

- Single-player against AI (Easy / Medium / Hard).
- Three dealing variants: 10→1, 8→1→8, 10→1→10.
- Must-lose mode (all players are bid-restricted, not just the dealer).
- Standard 52-card deck, follow-suit enforcement, trump rotation (♠ → ♦ → ♣ → ♥).
- Scoring: bid met = +10 / +11 / +N×10; bid missed = same values negated.
- CSS-rendered playing cards, animated dealing and trick collection.
- Live scoreboard, final-results screen with rankings.
- Standalone macOS + Windows desktop app (no browser needed).
- Mobile + desktop responsive layout.

---

## How releases are cut

Today's release process is **tag-driven**:

1. The maintainer pushes a tag matching `v*` (e.g. `v1.0.0`).
2. `.github/workflows/release.yml` builds `Judgement-macOS.tar.gz` and `Judgement-Windows.zip` on hosted runners.
3. A GitHub Release is created for the tag with both artifacts attached and auto-generated changelog.

**Planned change** ([plans/auto_update.md](plans/auto_update.md)): switch to **push-to-`main` triggered** auto-releases with semantic version bumps, and have the in-app updater download those binaries (verified via SHA256) instead of rebuilding from source. This will allow non-developer users to receive updates without ever opening a terminal.
