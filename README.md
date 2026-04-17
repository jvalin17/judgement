# Judgement (Kachu Phool)

[![Test](https://github.com/jvalin17/judgement/actions/workflows/test.yml/badge.svg)](https://github.com/jvalin17/judgement/actions/workflows/test.yml)

A trick-taking card game built with React, TypeScript, FastAPI, and WebSockets. Play solo against AI opponents. Available as a web app, standalone desktop app, or Docker container.

Also known as **Kachuful**, **Oh Hell**, or **Estimation** in different regions.

---

## Features

- **Three AI difficulty levels** — Easy (random), Medium (strategic), Hard (card counting, opponent modeling, personality system)
- **Four dealing variants** — 10→1, 8→1→8, 10→1→10, 8→5→8
- **Quick Play** — one click to start, or create a custom lobby with mixed AI difficulties
- **Must-lose mode** — optional rule where all players are bid-restricted, not just the dealer
- **CSS-rendered cards** — no image assets, fully scalable, with 9 card-back designs and 10 table colors
- **Smooth animations** — dealing, playing, trick collection, round transitions (speed configurable)
- **Desktop app** — standalone macOS/Windows via PyInstaller + pywebview (no embedded browser, ~45 MB)
- **In-app updater** — check for new versions from the Settings panel, no terminal needed
- **No telemetry** — zero outbound requests except the manual update check
- **210+ automated tests** — game logic, AI, REST API, WebSocket, with CI on every push
- **Docker** — single container deployment

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, CSS Modules |
| Backend | Python 3.9, FastAPI, Pydantic |
| Real-time | WebSockets (uvicorn) |
| AI | Rule-based strategies with personality system |
| Desktop | PyInstaller, pywebview |

---

## Download & Install

### Download a Release (recommended)

Go to the [Releases](../../releases) page:

- **macOS:** Download `Judgement-macOS.tar.gz`, extract, move `Judgement.app` to Applications
- **Windows:** Download `Judgement-Windows.zip`, extract, run `Judgement.exe`

No Python or Node.js needed — just download and play.

### Build from Source

Requires Python 3.9+ and Node.js 18+.

```bash
git clone <repo-url> && cd judgement
./scripts/package.sh          # Build desktop app
# or
./setup && ./play             # Run from source
```

---

## Usage

| Task | Command |
|------|---------|
| Play the game | `./play` |
| Build standalone app | `./scripts/package.sh` |
| Run tests | `python3 -m pytest backend/tests/ -v` |
| Dev server (backend) | `./scripts/dev.sh` |
| Dev server (frontend) | `cd frontend && npm run dev` |
| Docker | `docker build -t judgement . && docker run -p 8000:8000 judgement` |

---

## How to Play

1. **Quick Play** or **Create Game** from the lobby
2. Each round: cards are dealt, players bid how many tricks they'll win, then play tricks
3. **Must follow lead suit** if able; highest trump wins, else highest of lead suit
4. **Trump rotates** each round: Spades → Diamonds → Clubs → Hearts
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
| 10 → 1 | 10 | 5 |
| 8 → 1 → 8 | 16 | 6 |
| 10 → 1 → 10 | 20 | 5 |
| 8 → 5 → 8 | 8 | 6 |

---

## Architecture

```
judgement/
├── play                    # One-command launcher
├── setup                   # Dependency installer
├── backend/
│   ├── app/
│   │   ├── models/         # Pydantic data models
│   │   ├── game/           # Rules engine (pure logic, no I/O)
│   │   ├── ai/             # AI strategies (Strategy pattern)
│   │   ├── api/            # REST + WebSocket transport
│   │   ├── game_manager.py # Orchestrator
│   │   └── main.py         # FastAPI entry point
│   └── tests/              # 210+ tests
├── frontend/src/
│   ├── components/         # React components
│   ├── hooks/              # useGame, useWebSocket
│   ├── context/            # GameContext provider
│   └── services/           # REST + WebSocket clients
├── desktop/                # pywebview launcher
├── scripts/                # dev, build, package, update
└── Dockerfile
```

---

## System Requirements

~45 MB on disk, ~100 MB RAM, negligible CPU. No internet required to play. macOS 10.13+, Windows 10+, or Linux with Python 3.9+ and GTK/WebKit.

---

## Release Notes

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for the full changelog.

---

## Roadmap

- **Auto-updater v2** — download prebuilt binaries instead of rebuilding from source
- **Online multiplayer** — lobby system with join codes, mixed human/AI games
- **Developer API** — REST API for bots, tournaments, and integrations
- **Leaderboards** — persistent player stats and rankings
- **Custom rules** — configurable scoring, trump selection, house rules
- **Mobile app** — native iOS/Android
