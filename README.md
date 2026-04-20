# Judgement (Kachu Phool)

[![Test](https://github.com/jvalin17/judgement/actions/workflows/test.yml/badge.svg)](https://github.com/jvalin17/judgement/actions/workflows/test.yml)

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

**macOS first launch:** macOS may block the app since it's not from the App Store. Right-click the app → **Open** → click **Open** in the dialog. You only need to do this once.

---

## Features

- **Four AI difficulty levels** — Easy (random), Medium (heuristic), Hard (card counting + opponent modeling + personality system), Smart Hard (learns from game winners via kNN)
- **Multiplayer** — create or join rooms with a code, lobby browser, quick-join
- **Challenge mode** — full-strength AI for competitive players (disables adaptive difficulty)
- **Six dealing variants** — 10-to-1, 8 down & up, 10 down & up, 8 short, 8-to-4, 3 quick
- **Turbulence mode** — all players are bid-restricted, not just the dealer
- **Play style persona** — at game end, get matched to one of 75 personas across 7 categories based on an 11-dimension play fingerprint
- **Community data sharing** — share anonymized game decisions to help train better AI, download community data from other players
- **Aviation-themed scoreboard** — Pilot, Flights, Landings, Current, Score columns
- **Score visible during bidding** — cumulative score shown in the bid selector
- **CSS-rendered cards** — no image assets, fully scalable
- **Smooth animations** — dealing, playing, trick collection, celebration effects (confetti, fireworks, rockets, flowers, bubbles, clouds) ranked by final position
- **Desktop app** — standalone macOS/Windows via PyInstaller + pywebview
- **In-app updater** — check for new versions from Settings
- **No telemetry** — zero outbound requests except the manual update check and opt-in community data sharing
- **Victory sound effects** — celebratory fanfare when you win, synthesized via Web Audio API
- **Local learning** — Smart Hard AI learns from your games and gets stronger over time

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
./judgement setup        # Install all dependencies (one-time)
./judgement              # Build frontend + launch the game
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
./judgement dev

# Start frontend dev server (proxies to backend on :8000)
cd frontend && npm run dev

# Run tests
source .venv/bin/activate
python3 -m pytest backend/tests/ -v
cd frontend && npm test
```

| Task | Command |
|------|---------|
| Play the game | `./judgement` |
| First-time setup | `./judgement setup` |
| Dev server | `./judgement dev` |
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
├── judgement                # Unified launcher (play / setup / dev)
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
│   └── tests/              # 307 backend tests
├── frontend/src/
│   ├── components/         # React components
│   ├── hooks/              # useGame, useWebSocket
│   ├── context/            # GameContext, SettingsContext
│   ├── services/           # REST + WebSocket clients
│   └── test/               # 38 frontend tests (Vitest)
├── desktop/                # pywebview launcher
├── assets/                 # App icons (PNG, ICNS, SVG)
├── scripts/                # Build, package, dev tools
└── requirements.txt        # Python dependencies
```

---

## Roadmap

- **Online multiplayer** — play with friends from anywhere, not just the same network
- **Mobile app** — lightweight PWA or native app for phones and tablets
- **Smarter AI** — neural network models trained on community data for more human-like play
- **Public API** — expose the game engine so others can build bots, dashboards, or tournaments

---

## System Requirements

~15 MB download, ~25 MB on disk, ~100 MB RAM. No internet required to play (internet needed only for multiplayer, community data sharing, and update checks).

- **macOS:** 10.13+ (Intel or Apple Silicon)
- **Windows:** 10+
- **Linux:** Python 3.9+ with GTK/WebKit

