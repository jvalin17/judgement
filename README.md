# Judgement (Kachu Phool)

[![Test](https://github.com/jvalin17/judgement/actions/workflows/test.yml/badge.svg)](https://github.com/jvalin17/judgement/actions/workflows/test.yml)
[![Full Test Suite](https://github.com/jvalin17/judgement/actions/workflows/test-suite.yml/badge.svg)](https://github.com/jvalin17/judgement/actions/workflows/test-suite.yml)

A trick-taking card game built with React, TypeScript, FastAPI, and WebSockets. Play solo against AI opponents with adaptive difficulty. Available as a standalone desktop app.

Also known as **Kachuful**, **Oh Hell**, or **Estimation** in different regions.

---

## Download & Play

**[Download latest release](https://github.com/jvalin17/judgement/releases/latest)**

| Platform | Download | Install |
|----------|----------|---------|
| **macOS** | [Judgement-macOS.tar.gz](https://github.com/jvalin17/judgement/releases/latest/download/Judgement-macOS.tar.gz) | Extract → move to Applications → double-click |
| **Windows** | [Judgement-Windows.zip](https://github.com/jvalin17/judgement/releases/latest/download/Judgement-Windows.zip) | Extract → run `Judgement.exe` |

No Python, Node.js, or terminal needed. Just download and play.

### What's in the bundle

The download is a self-contained app — everything is bundled:

- **Game engine** — rules, scoring, trick resolution
- **4 AI opponents** — Easy, Medium, Hard, and Smart Hard (learns from your games)
- **75 player personas** — personality matching based on play style
- **Web frontend** — pre-built React app served locally
- **Local server** — FastAPI + WebSockets, runs on your machine only

No data leaves your computer unless you opt into community data sharing or check for updates.

**macOS first launch:** macOS may block the app since it's not from the App Store. Right-click the app → **Open** → click **Open** in the dialog. You only need to do this once.

---

## Features

- **Four AI difficulty levels** — Easy (random), Medium (heuristic), Hard (card counting + opponent modeling + personality system), Smart Hard (learns from game winners via kNN)
- **Multiplayer** — create or join rooms with a code, lobby browser, quick-join
- **Challenge mode** — full-strength AI for competitive players (disables adaptive difficulty)
- **Six dealing variants** — 10-to-1, 8 down & up, 10 down & up, 8 short, 8-to-4, 3 quick
- **Turbulence mode** — guarantees at least one player misses their bid each round
- **Play style persona** — at game end, get matched to one of 75 personas across 7 categories based on an 11-dimension play fingerprint. Persona tier scales with difficulty: Easy unlocks animal personas, Medium adds cartoon and pokemon, Hard/Smart Hard adds achievement and poker, and playing Hard with challenge + turbulence unlocks elite tier (superhero, mythology)
- **Community data sharing** — share anonymized game decisions to help train better AI, download community data from other players
- **Aviation-themed scoreboard** — Pilot, Flights, Landings, Current, Score columns
- **Score visible during bidding** — cumulative score shown in the bid selector
- **Desktop app** — standalone macOS/Windows via PyInstaller + pywebview
- **In-app updater** — check for new versions from Settings
- **Local learning** — Smart Hard AI learns from your games and gets stronger over time
- **627 automated tests** — 143 smoke tests in-repo + 484 in the [full test suite](https://github.com/jvalin17/judgement-tests)

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
| 8 down & up | 16 | 6 |
| 10 down & up | 20 | 5 |
| 8 short | 10 | 6 |
| 8 down to 4 | 5 | 6 |
| 3 quick | 3 | 10 |

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

# Run tests
source .venv/bin/activate
python3 -m pytest backend/tests/ -v
cd frontend && npm test
```

| Task | Command |
|------|---------|
| Play the game | `./scripts/judgement` |
| First-time setup | `./scripts/judgement setup` |
| Dev server | `./scripts/judgement dev` |
| Build standalone app | `./scripts/package.sh` |
| Frontend dev | `cd frontend && npm run dev` |
| Backend tests | `source .venv/bin/activate && python3 -m pytest backend/tests/ -v` |
| Frontend tests | `cd frontend && npm test` |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, CSS Modules |
| Backend | Python 3.9, FastAPI, Pydantic |
| Real-time | WebSockets (uvicorn) |
| AI | Rule-based strategies + kNN learning engine |
| ML | Player fingerprinting, persona matching, community data sharing |
| Desktop | PyInstaller, pywebview |

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
│   │   │   ├── learning/   # kNN model, feature extraction, data collector
│   │   │   └── analysis/   # Play style fingerprinting + persona matching
│   │   ├── api/            # REST + WebSocket + update + data sharing
│   │   ├── game_manager.py # Orchestrator
│   │   └── main.py         # FastAPI entry point
│   └── tests/              # 122 backend smoke tests
├── frontend/src/
│   ├── components/         # React components
│   ├── hooks/              # useGame, useWebSocket
│   ├── context/            # GameContext, SettingsContext
│   ├── services/           # REST + WebSocket clients
│   └── test/               # 21 frontend smoke tests (Vitest)
├── desktop/                # pywebview launcher
├── assets/                 # App icons (PNG, ICNS, SVG)
└── scripts/                # Build, package, launcher, dev tools
    ├── judgement           # Unified launcher (play / setup / dev)
    ├── package.sh          # Build standalone app
    └── run-test-suite.sh   # Run full test suite locally
```

---

## Testing

**Smoke tests** (this repo) — 143 tests that run fast and cover core logic:

```bash
python3 -m pytest backend/tests/ -v        # 122 backend tests
cd frontend && npx vitest run               # 21 frontend tests
```

**[Full test suite](https://github.com/jvalin17/judgement-tests)** — 484 additional tests covering AI strategies, persona matching, all UI components, edge cases, and integration:

```bash
./scripts/run-test-suite.sh                 # Runs both smoke + suite
```

Both run automatically on every push to `main` via GitHub Actions. See badges at the top.

---

## Roadmap

- **Online multiplayer** — play with friends from anywhere, not just the same network
- **Mobile app** — lightweight PWA or native app for phones and tablets
- **Smarter AI** — neural network models trained on community data for more human-like play
- **Public API** — expose the game engine so others can build bots, dashboards, or tournaments

---

## System Requirements

| | Requirement |
|---|---|
| **Download size** | ~15 MB |
| **Disk space** | ~25 MB installed |
| **Memory** | ~100 MB RAM |
| **Internet** | Not required for solo play. Needed for multiplayer, community data sharing, and update checks. |
| **macOS** | 11 Big Sur or later (Apple Silicon). Intel Macs: [build from source](#build-from-source). |
| **Windows** | Windows 10 or later |
| **Linux** | Build from source — Python 3.9+ with GTK/WebKit |

