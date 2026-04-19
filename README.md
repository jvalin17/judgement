# Judgement (Kachu Phool)

[![Test](https://github.com/jvalin17/judgement/actions/workflows/test.yml/badge.svg)](https://github.com/jvalin17/judgement/actions/workflows/test.yml)

A trick-taking card game built with React, TypeScript, FastAPI, and WebSockets. Play solo against AI opponents or with friends in multiplayer. Available as a standalone desktop app.

Also known as **Kachuful**, **Oh Hell**, or **Estimation** in different regions.

---

## Download & Play

### macOS

1. Go to the [Releases](../../releases) page
2. Download `Judgement-macOS.zip`
3. Extract the zip
4. Move `Judgement.app` to your Applications folder
5. Double-click to play

**First launch:** macOS may block the app since it's not from the App Store. Right-click the app, select **Open**, then click **Open** in the dialog. You only need to do this once.

### Windows

1. Go to the [Releases](../../releases) page
2. Download `Judgement-Windows.zip`
3. Extract the zip
4. Run `Judgement.exe`

No Python, Node.js, or terminal needed. Just download and play.

---

## Features

- **Four AI difficulty levels** — Easy (random), Medium (heuristic), Hard (card counting + opponent modeling + personality system), Smart Hard (learns from game winners via kNN)
- **Five dealing variants** — 10-to-1, 8 down & up, 10 down & up, 8 short, 3 quick
- **Multiplayer** — create or join rooms with join codes, mixed human + AI games
- **Must-lose mode** — "Turbulence" toggle where all players are bid-restricted
- **Play style persona** — at game end, get matched to a persona based on your play traits
- **CSS-rendered cards** — no image assets, fully scalable
- **Smooth animations** — dealing, playing, trick collection, confetti + fireworks on game over
- **Desktop app** — standalone macOS/Windows via PyInstaller + pywebview
- **In-app updater** — check for new versions from Settings
- **No telemetry** — zero outbound requests except the manual update check
- **283 automated tests** — game logic, AI, REST API, WebSocket, information isolation
- **Local learning** — the Smart Hard AI learns from your games and gets stronger over time. Each player's AI learns independently on their machine

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
./setup          # Install all dependencies (one-time)
./play           # Build frontend + launch the game
```

### Build standalone app

```bash
./scripts/package.sh
# Output: dist/Judgement.app (macOS) or dist/Judgement/ (Windows)
open dist/Judgement.app
```

### Development

```bash
# Start backend dev server (auto-creates venv if needed)
./start.sh

# Start frontend dev server (hot reload, proxies to backend on :8000)
cd frontend && npm run dev

# Run tests
source .venv/bin/activate
python3 -m pytest backend/tests/ -v
```

| Task | Command |
|------|---------|
| Play the game | `./play` |
| Build standalone app | `./scripts/package.sh` |
| Dev server | `./start.sh` |
| Frontend dev | `cd frontend && npm run dev` |
| Run tests | `source .venv/bin/activate && python3 -m pytest backend/tests/ -v` |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, CSS Modules |
| Backend | Python 3.9, FastAPI, Pydantic |
| Real-time | WebSockets (uvicorn) |
| AI | Rule-based strategies + kNN learning engine |
| Desktop | PyInstaller, pywebview |

---

## Architecture

```
judgement/
├── play                    # One-command launcher
├── setup                   # Dependency installer
├── start.sh                # Dev server (venv-based)
├── backend/
│   ├── app/
│   │   ├── models/         # Pydantic data models
│   │   ├── game/           # Rules engine (pure logic, no I/O)
│   │   ├── ai/             # AI strategies
│   │   │   └── learning/   # kNN model, feature extraction, data collector
│   │   ├── analysis/       # Play style fingerprinting + persona matching
│   │   ├── api/            # REST + WebSocket transport
│   │   ├── game_manager.py # Orchestrator
│   │   └── main.py         # FastAPI entry point
│   └── tests/              # 283 tests
├── frontend/src/
│   ├── components/         # React components
│   ├── hooks/              # useGame, useWebSocket
│   ├── context/            # GameContext provider
│   └── services/           # REST + WebSocket clients
├── desktop/                # pywebview launcher
├── scripts/                # build, package, dev tools
├── Judgement.spec           # PyInstaller config
└── requirements.txt        # Python dependencies
```

---

## System Requirements

~25 MB on disk, ~100 MB RAM. No internet required to play.

- **macOS:** 10.13+ (Intel or Apple Silicon)
- **Windows:** 10+
- **Linux:** Python 3.9+ with GTK/WebKit

---

## License

MIT
