# Judgement (Kachu Phool)

A full-stack trick-taking card game built with React, TypeScript, FastAPI, and WebSockets. Play solo against AI opponents. Available as a web app, standalone desktop app, or Docker container.

Also known as **Kachuful**, **Oh Hell**, or **Estimation** in different regions.

---

## Features

### Gameplay
- **Single-player mode** with three AI difficulty levels (Easy, Medium, Hard)
- **Four dealing variants** — 10→1, 8→1→8, 10→1→10, 8→5→8
- **Must-lose mode** — optional rule variant where all players are constrained (not just the dealer)
- **Full trick-taking rules** — follow-suit enforcement, trump rotation, bid constraints
- **Quick Play** — jump straight into a game against the default AI lineup with a single click
- **Custom lobby** — pick variant, mix AI difficulties, and tune game options before starting
- **Round-by-round scoreboard** — see bids, tricks won, round delta, and cumulative scores
- **Final results screen** — rankings and full session log when the game ends

### AI Opponents
- **Easy** — random valid moves; good for first-time players
- **Medium** — hand evaluation, strategic leads, situational trick-taking
- **Hard** — card counting, positional play, trump management, opponent modeling, and a personality system that gives each opponent randomized strategy variation per game

### User Interface
- **CSS-rendered playing cards** — no image assets, fully scalable on any screen
- **Smooth animations** for dealing, playing, trick collection, and round transitions
- **Visual table** — green felt with a central rangoli motif that resizes with the window
- **Card back gallery** — Classic Blue, Red Damask, Green Celtic, Royal Purple, Gold Ornate, Black Carbon, Rose Floral, Teal Diamonds, Indigo Stars
- **Table color picker** — 10 themed colors (Classic Green, Navy, Burgundy, Dark Wood, Slate, Emerald, Midnight Black, Teal Ocean, Royal Purple, Coffee Brown)
- **Animation speed control** — Slow / Medium / Fast
- **Subtle turn indicator** — gold border on the active player; no overlapping banners
- **Responsive layout** — desktop and mobile browsers
- **Auto-reconnect** — exponential backoff WebSocket reconnect, plus session restore on tab refresh

### Desktop App
- **Standalone macOS and Windows application** packaged with PyInstaller
- **Native window** via pywebview (no browser tab, no URL bar)
- **Custom app icon** — lightweight J-card on a violet→magenta tile
- **One-command build** — `./scripts/package.sh` installs all deps and produces a ready-to-ship bundle
- **In-app updater** — check for new versions and install them from the Settings panel; no terminal required
- **Settings panel** — toggle cards/tables/animations and view the installed version + build date

### Security & Reliability
- **Update endpoint locked to localhost** — `/api/update/apply` rejects non-loopback requests, so a remote attacker on the same network cannot trigger an update
- **No telemetry** — the app never phones home; the only outbound request is the update check to GitHub, and only when you click it
- **Dependency scanner** — `python3 scripts/security_scan.py` runs `pip-audit` + `npm audit` against current lockfiles
- **AI information isolation** — AI players only see public game state (bids, tricks played, current trick), never other players' hands
- See [Security Guidelines](#security-guidelines) below for the full trust model

### Infrastructure
- **Dockerized** — single container deployment with `docker build && docker run`
- **Automated test suite** — 210+ tests covering game logic, AI, REST API, and WebSocket
- **CI-ready** — `python3 -m pytest backend/tests/ -v`
- **GitHub Actions release pipeline** — tag-triggered build of macOS + Windows artifacts, attached to a GitHub Release
- **Configuration via JSON** — round definitions live in `backend/app/game/rounds/*.json` and are loaded once, cached immutably

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, CSS Modules |
| Backend | Python 3.9, FastAPI, Pydantic |
| Real-time | WebSockets (uvicorn) |
| AI Engine | Rule-based strategies with personality system |
| Desktop | PyInstaller, pywebview |
| Deployment | Docker, shell scripts |

---

## Download & Install

### Prerequisites

- **Python** 3.9+ — [python.org/downloads](https://www.python.org/downloads/)
- **Node.js** 18+ — [nodejs.org](https://nodejs.org/)
- **OS:** macOS, Windows, Linux

### Option 1: Download a Release (recommended)

Go to the [Releases](../../releases) page and download the latest build for your OS:

- **macOS:** Download `Judgement-macOS.tar.gz`, extract, and move `Judgement.app` to Applications
- **Windows:** Download `Judgement-Windows.zip`, extract, and run `Judgement.exe`
- **Linux:** Use [Option 3: Run from Source](#option-3-run-from-source)

No Python or Node.js needed — just download and play.

### Option 2: Build Desktop App from Source

```bash
git clone <repo-url> && cd judgement
./scripts/package.sh     # Installs deps automatically, builds the app
```

- **macOS:** `open dist/Judgement.app` (or copy to `/Applications/`)
- **Windows:** Run `dist/Judgement/Judgement.exe`

To update to the latest version:

```bash
./scripts/update.sh      # Pulls latest, rebuilds, installs to /Applications/
```

Or use the **in-app update button** under Settings — no terminal needed.

### Option 3: Run from Source

```bash
git clone <repo-url> && cd judgement
./setup    # One-time: installs all dependencies
./play     # Build frontend, start server, open game
```

Opens as a desktop window if [pywebview](https://pywebview.flowrl.com/) is available, otherwise opens in your browser at `http://localhost:8000`.

---

## Usage

| Task | Command |
|------|---------|
| First time setup | `./setup` |
| Play the game | `./play` |
| Build standalone app | `./scripts/package.sh` |
| Update & reinstall | `./scripts/update.sh` |
| Run tests | `python3 -m pytest backend/tests/ -v` |
| Dev server (backend) | `./scripts/dev.sh` |
| Dev server (frontend) | `cd frontend && npm run dev` |
| Build frontend only | `cd frontend && npm run build` |
| Production server | `./scripts/build.sh && ./scripts/serve.sh` |
| Security scan | `python3 scripts/security_scan.py` |
| Docker | `docker build -t judgement . && docker run -p 8000:8000 judgement` |

---

## How to Play

### Getting Started

1. **Quick Play** — start an instant game against AI opponents. Choose your name, pick a difficulty, and you're playing in seconds.
2. **Create Game** — set up a lobby, choose a dealing variant, and add AI players of varying difficulty.

### Game Flow

Each game consists of multiple rounds. In each round:

1. **Deal** — Cards are dealt face-down. The number of cards changes each round depending on the variant.
2. **Bid** — Starting from the player left of the dealer, each player bids how many tricks they think they can win (0 to the number of cards in hand). The dealer bids last and is restricted — they cannot make the total bids equal the number of cards, so at least one player is guaranteed to miss their bid.
3. **Play Tricks** — The player left of the dealer leads the first trick. Each player plays one card clockwise. You **must follow the lead suit** if you have it. If you don't, you can play any card (including trump).
4. **Trick Winner** — The highest trump card wins. If no trump was played, the highest card of the lead suit wins. The winner leads the next trick.
5. **Scoring** — After all tricks are played, points are awarded based on whether you hit your bid.
6. **Next Round** — Review the scoreboard, then continue to the next round. The dealer rotates clockwise and the number of cards changes.

### Trump Suit

The trump suit rotates in a fixed order each round: **Spades → Diamonds → Clubs → Hearts**, then repeats. Trump cards beat any non-trump card, regardless of rank.

### Card Ranking

Cards rank from lowest to highest: **2, 3, 4, 5, 6, 7, 8, 9, 10, Jack, Queen, King, Ace**

### Rules Summary

- Standard 52-card deck
- Must follow lead suit if able
- Highest trump wins the trick; if no trump, highest of lead suit wins
- Dealer's bid is restricted (total bids cannot equal number of cards)
- **Must-lose mode** (optional): All players are restricted, not just the dealer

### Dealing Variants

| Variant | Rounds | Max Players | Description |
|---------|--------|-------------|-------------|
| 10 → 1 | 10 | 5 | Countdown from 10 cards to 1 |
| 8 → 1 → 8 | 16 | 6 | Down from 8, back up to 8 |
| 10 → 1 → 10 | 20 | 5 | Full down-and-up cycle |
| 8 → 5 → 8 | 8 | 6 | Short game, mid-range hands |

### Scoring

| Bid | Result | Points |
|-----|--------|--------|
| 0 | Made | +10 |
| 1 | Made | +11 |
| N (2+) | Made | +N x 10 |
| Any | Missed | Same values, negated |

### Strategy Tips

- **Bidding 0 is powerful** — you earn +10 points for making it, and in rounds with fewer cards it's often the safest bet
- **Count trumps** — know how many trumps are out. If you hold the Ace of trump, it's almost guaranteed to win
- **Watch the bids** — if total bids exceed the number of cards, play aggressively. If they're under, play conservatively
- **Create voids** — being out of a suit lets you trump in, which is valuable for winning tricks you need
- **Dump high cards early** when you're trying to lose — they become liabilities as the round progresses

---

## Architecture

```
judgement/
├── play                    # One-command launcher
├── setup                   # One-time dependency installer
├── backend/
│   ├── app/
│   │   ├── models/         # Pydantic data models (Card, Player, GameState)
│   │   ├── game/           # Rules engine — pure logic, no I/O
│   │   ├── ai/             # AI strategies (Strategy pattern)
│   │   ├── api/            # REST + WebSocket transport
│   │   ├── game_manager.py # Orchestrator (wires game + AI)
│   │   └── main.py         # FastAPI entry point
│   └── tests/              # 210+ tests
├── frontend/src/
│   ├── components/         # React components (lobby, game board, scoreboard)
│   ├── hooks/              # useGame (state reducer), useWebSocket
│   ├── context/            # GameContext provider
│   ├── services/           # REST + WebSocket clients
│   └── styles/             # CSS Modules with animations
├── desktop/                # pywebview desktop launcher
├── scripts/                # dev, build, serve, package, update, security scan
└── Dockerfile              # Single container deployment
```

### Design Patterns

| Pattern | Where | Purpose |
|---------|-------|---------|
| State Machine | `GameEngine` | Phase transitions: LOBBY → BIDDING → PLAYING → ROUND_OVER → GAME_OVER |
| Strategy | `ai/` | Swappable AI difficulty without touching the engine |
| Observer | `GameEngine._emit()` | Decouples engine from WebSocket/API transport |
| Config-driven | `rounds/*.json` | Round definitions loaded from JSON, cached immutably |
| Typed Events | `events.py` | Type-safe event payloads with factory functions |

---

## Security Guidelines

This section documents the security model of the app, what it protects against, what it does **not** protect against, and how to report issues.

### Trust model

When you install or update Judgement, you are trusting:

1. **GitHub as the publisher.** All release artifacts are downloaded from `github.com` over TLS, validated by your operating system's certificate store. There is no other delivery channel.
2. **The GitHub Actions workflow in this repo.** Builds happen in CI from the source you can read at `.github/workflows/release.yml`. No binaries are built on a private machine and uploaded by hand.
3. **The release tag you choose to install.** Each release lists the exact commit it was built from. The desktop app reports its installed version under Settings.

### What the app protects against

- **Remote update triggering.** `/api/update/apply` only accepts requests from `127.0.0.1` / `::1`. An attacker on the same Wi-Fi cannot force an update.
- **Tampering in transit.** All update checks and downloads use HTTPS to `api.github.com`. The OS validates GitHub's certificate.
- **Unwanted network chatter.** No analytics, no crash reporting, no "phone home" call. The only outbound request is the manual update check, and only after you click it.
- **AI cheating.** AI strategies receive a `RoundContext` containing only publicly visible information (trump suit, bids, tricks played, current trick, the AI's own hand). They never see other players' hands.

### What the app does NOT protect against (be aware)

- **Compromise of the GitHub repo.** If an attacker pushes malicious code to `main`, CI will dutifully build and publish it. Mitigations the maintainer should keep in place: 2FA on the GitHub account, branch protection on `main`, signed commits, and required reviews on PRs.
- **macOS Gatekeeper warnings.** This project does not pay for an Apple Developer ID. The first time you open the app from a fresh download, macOS will warn "unidentified developer". You must right-click → Open to confirm. Subsequent launches are silent. There is currently no way around this without code signing.
- **Compromise of your own machine.** Anything already running as your user can read or replace the app on disk. Standard OS hygiene applies.
- **Old, vulnerable installs.** If you stop updating, you stop receiving fixes. Use the in-app updater periodically.

### Recommendations for users

- **Download only from the official GitHub Releases page.** Do not trust a third party that has zipped up "Judgement" and posted it elsewhere.
- **Verify the version after install.** Open Settings → check the displayed version against the latest tag on GitHub.
- **Keep the app updated.** Click "Check for Updates" in Settings periodically. There is no auto-update on launch — it is always your decision to apply.

### Recommendations for the maintainer

- **Enable 2FA + signed commits** on the GitHub account that owns this repo.
- **Branch-protect `main`** and require PR review before merge.
- **Run `python3 scripts/security_scan.py`** before tagging a release. It runs `pip-audit` (Python deps) and `npm audit` (Node deps) and exits non-zero on known vulnerabilities.
- **Pin GitHub Actions** to commit SHAs (not floating tags) for sensitive steps in `.github/workflows/release.yml`.

### Reporting a vulnerability

If you find a security issue, please **do not** open a public GitHub issue. Email the maintainer or open a private security advisory through GitHub's "Security" tab on the repository. Include:

- A description of the issue and its impact
- Steps to reproduce
- The version of Judgement you were running

You will receive an acknowledgement and a timeline for the fix.

---

## Release Notes

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for the full changelog. Every published release on the [Releases page](../../releases) also lists the changes since the previous tag.

---

## Roadmap

- **Auto-updater v2** — replace the current rebuild-from-source updater with a download-and-replace flow that fetches signed-by-SHA256 binaries from GitHub Releases. See [`plans/auto_update.md`](plans/auto_update.md) for the full design.
- **Online multiplayer** — lobby system with join codes, real-time WebSocket play, auto-reconnect, mixed human/AI games
- **Developer API** — public REST API with API key authentication for building bots, running tournaments, and third-party integrations
- **Leaderboards** — persistent player stats and rankings
- **Custom rules** — configurable scoring, trump selection, and house rules
- **Mobile app** — native iOS/Android versions
