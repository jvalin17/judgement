# Judgement (Kachu Phool)

[![Full Test Suite](https://github.com/jvalin17/judgement/actions/workflows/test-suite.yml/badge.svg)](https://github.com/jvalin17/judgement/actions/workflows/test-suite.yml)
[![Production Health](https://github.com/jvalin17/judgement/actions/workflows/health-check.yml/badge.svg)](https://github.com/jvalin17/judgement/actions/workflows/health-check.yml)

A trick-taking card game built with React, TypeScript, FastAPI, and WebSockets. Play solo against AI or online with friends. Available as a standalone desktop app and a live web version.

Also known as **Kachuful**, **Oh Hell**, or **Estimation** in different regions.

---

## Play Online

**https://judgement-game.duckdns.org**

No download or install needed. Play from any browser. Multiplayer supported.

---

## Download Desktop App

**[Download latest release](https://github.com/jvalin17/judgement/releases/latest)**

| Platform | Download | Install |
|----------|----------|---------|
| **macOS** | [Judgement-macOS.tar.gz](https://github.com/jvalin17/judgement/releases/latest/download/Judgement-macOS.tar.gz) | Extract, move to Applications, double-click |
| **Windows** | [Judgement-Windows.zip](https://github.com/jvalin17/judgement/releases/latest/download/Judgement-Windows.zip) | Extract, run `Judgement.exe` |

No Python, Node.js, or terminal needed. Just download and play.

**macOS first launch:** macOS may block the app since it's not from the App Store. Right-click the app, click **Open**, then click **Open** in the dialog. You only need to do this once.

---

## Features

- **Four AI difficulty levels** — Easy (random), Medium (heuristic), Hard (card counting + opponent modeling + personality system), Smart Hard (multi-model ML engine — each bot uses a different algorithm: kNN, Decision Tree, Naive Bayes, or Strategy Classifier, learning from winners and losers with per-decision feedback)
- **Online multiplayer** — play at https://judgement-game.duckdns.org with friends from anywhere
- **Local multiplayer** — create or join rooms with a code, lobby browser, quick-join
- **Challenge mode** — full-strength AI for competitive players (disables adaptive difficulty)
- **Six dealing variants** — 10-to-1, 8 down & up, 10 down & up, 8 short, 8-to-4, 3 quick
- **Turbulence mode** — guarantees at least one player misses their bid each round
- **Play style persona** — at game end, get matched to one of 90 personas across 8 categories based on an 11-dimension play fingerprint. Unlock exclusive prestige personas at higher difficulty tiers
- **Community data sharing** — opt-in to share anonymized game decisions; the server learns from community data and SmartHardAI gets smarter over time
- **Aviation-themed scoreboard** — Pilot, Flights, Landings, Current, Score columns
- **Desktop app** — standalone macOS/Windows via PyInstaller + pywebview
- **In-app updater** — check for new versions from Settings
- **770 automated tests** — all in the [test suite repo](https://github.com/jvalin17/judgement-tests), run on every push and PR via CI
- **Production health monitoring** — daily automated checks for uptime, TLS, security headers

---

## How to Play

1. Enter your name, pick a game mode, and start
2. Each round: cards are dealt, players bid how many tricks they'll win, then play tricks
3. **Must follow lead suit** if able; highest trump wins, else highest of lead suit
4. **Trump rotates** each round: Spades, Diamonds, Clubs, Hearts
5. **Dealer is restricted** — their bid can't make total bids equal the number of cards

### Scoring

| Bid | Result | Points |
|-----|--------|--------|
| 0 | Made | +10 |
| 1 | Made | +11 |
| N (2+) | Made | +N x 10 |
| Any | Missed | Same values, negated |

### Dealing Variants

| Variant | Rounds | Max Players |
|---------|--------|-------------|
| 10 down to 1 | 10 | 5 |
| 8 down & up (8→1→8) | 16 | 6 |
| 10 down & up (10→1→10) | 20 | 5 |
| 8 short (8→5→8) | 8 | 6 |
| 8 down to 4 | 5 | 6 |
| Quick game (5, 3, 5) | 3 | 10 |

---

## Build from Source

Only needed if you want to develop or build the app yourself.

### Prerequisites

- Python 3.9+
- Node.js 18+
- Git

### Setup and play from source

```bash
git clone https://github.com/jvalin17/judgement.git
cd judgement
./scripts/judgement setup        # Install all dependencies (one-time)
./scripts/judgement              # Build frontend + launch the game
```

### Build standalone app

```bash
./scripts/package.sh
# Output: dist/Judgement.app (macOS) or dist/Judgement/ (Windows)
open dist/Judgement.app
```

### Development

```bash
# Start backend dev server (hot reload, auto-creates venv)
./scripts/judgement dev

# Start frontend dev server (proxies to backend on :8000)
cd frontend && npm run dev

# Run tests (requires judgement-tests repo as sibling)
./scripts/run-test-suite.sh
```

| Task | Command |
|------|---------|
| Play the game | `./scripts/judgement` |
| First-time setup | `./scripts/judgement setup` |
| Dev server | `./scripts/judgement dev` |
| Build standalone app | `./scripts/package.sh` |
| Frontend dev | `cd frontend && npm run dev` |
| Run tests | `./scripts/run-test-suite.sh` |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, CSS Modules |
| Backend | Python 3.9, FastAPI, Pydantic |
| Real-time | WebSockets (uvicorn) |
| AI | Rule-based strategies + multi-model ML engine (kNN, Decision Tree, Naive Bayes, Strategy Classifier) |
| ML | Player fingerprinting, persona matching, community data sharing |
| Desktop | PyInstaller, pywebview |
| Deployment | Docker, Caddy (HTTPS), Oracle Cloud VM |

---

## Architecture

```
judgement/
├── backend/
│   ├── app/
│   │   ├── models/         # Pydantic data models
│   │   ├── game/           # Rules engine (pure logic, no I/O)
│   │   ├── ai/             # AI strategies (Easy, Medium, Hard, SmartHard)
│   │   ├── ml/             # Machine learning infrastructure
│   │   │   ├── learning/   # ML models (kNN, Decision Tree, Naive Bayes, Strategy), features, data collector
│   │   │   └── analysis/   # Play style fingerprinting + persona matching
│   │   ├── api/            # REST + WebSocket + update + data sharing
│   │   ├── game_manager.py # Orchestrator
│   │   └── main.py         # FastAPI entry point
│   └── tests/              # See jvalin17/judgement-tests
├── frontend/src/
│   ├── components/         # React components
│   ├── hooks/              # useGame, useWebSocket
│   ├── context/            # GameContext, SettingsContext
│   ├── services/           # REST + WebSocket clients
│   └── test/               # Test helpers
├── deployment/             # Docker, Caddy, VM setup, deploy scripts
├── desktop/                # pywebview launcher
├── assets/                 # App icons (PNG, ICNS, SVG)
└── scripts/                # Build, package, launcher, dev tools
```

---

## Deployment

The live server runs on an Oracle Cloud Always Free VM ($0/month).

- **Docker** single-container deployment with volume for ML data persistence
- **Caddy** reverse proxy with auto-HTTPS via Let's Encrypt
- **DuckDNS** free dynamic DNS at `judgement-game.duckdns.org`
- **CI/CD** — tests run on every push/PR, health checks run daily

See [`deployment/DEPLOY.md`](deployment/DEPLOY.md) for the full runbook.

---

## Testing

All 770 tests live in the **[test suite repo](https://github.com/jvalin17/judgement-tests)** — covering game logic, AI strategies, ML models, persona matching, all UI components, edge cases, and integration flows.

```bash
# Clone test repo as sibling (one-time)
git clone https://github.com/jvalin17/judgement-tests.git ../judgement-tests

# Run all tests locally
./scripts/run-test-suite.sh
```

Runs automatically on every push to `main` and on pull requests via GitHub Actions. See badges at the top.

---

## Roadmap

- **Mobile app** — lightweight PWA or native app for phones and tablets
- **Neural network AI** — deep learning models trained on growing community dataset for even more human-like play
- **Persistence** — save game history and stats to a database (currently in-memory)
- **Public API** — expose the game engine so others can build bots, dashboards, or tournaments

---

## System Requirements

**Online play:** Any modern browser. No install needed.

**Desktop app:**

| | Requirement |
|---|---|
| **Download size** | ~15 MB (macOS), ~17 MB (Windows) |
| **Memory** | ~100 MB RAM |
| **Internet** | Not required for solo play. Needed for online multiplayer, community data sharing, and update checks. |
| **macOS** | 11 Big Sur or later (Apple Silicon). Intel Macs: [build from source](#build-from-source). |
| **Windows** | Windows 10 or later |
| **Linux** | Build from source — Python 3.9+ with GTK/WebKit |
