# Judgement (Kachu Phool)

A full-stack, real-time trick-taking card game built with React, TypeScript, FastAPI, and WebSockets. Play solo against AI opponents or online with friends. Available as a web app, standalone desktop app, or Docker container.

Also known as **Kachuful**, **Oh Hell**, or **Estimation** in different regions.

---

## Features

### Gameplay
- **Single-player mode** with three AI difficulty levels (Easy, Medium, Hard)
- **Real-time multiplayer** over WebSockets with lobby system and join codes
- **Four dealing variants** — 10→1, 8→1→8, 10→1→10, 8→5→8
- **Must-lose mode** — optional rule variant where all players are constrained (not just the dealer)
- **Full trick-taking rules** — follow-suit enforcement, trump rotation, bid constraints

### AI Opponents
- **Easy** — random valid moves
- **Medium** — hand evaluation, strategic leads, situational trick-taking
- **Hard** — card counting, positional play, trump management, opponent modeling, personality system with randomized strategy variation per game

### User Interface
- **CSS-rendered playing cards** — no image assets, fully scalable
- **Animated card dealing, playing, and trick collection**
- **Customizable settings** — card back designs, table colors, animation speed
- **Responsive layout** — works on desktop and mobile browsers
- **Live scoreboard** with round-by-round tracking

### Multiplayer
- **Lobby system** — create games, share 6-character join codes
- **Quick Join** — auto-match into an open lobby
- **WebSocket-based** real-time state sync
- **Auto-reconnect** with exponential backoff on disconnect
- **Mixed human/AI games** — fill empty seats with AI players

### Desktop App
- **Standalone macOS/Windows application** via PyInstaller
- **One-command build** — `./scripts/package.sh` handles all dependencies
- **In-app update button** — check for and apply updates without using the terminal
- **Native window** via pywebview (no browser required)

### Infrastructure
- **Dockerized** — single container deployment with `docker build && docker run`
- **Automated test suite** — 210+ tests covering game logic, AI, REST API, WebSocket, and multiplayer integration
- **CI-ready** — `python3 -m pytest backend/tests/ -v`
- **Security scanning** — `python3 scripts/security_scan.py`

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

1. **Quick Play** — start an instant game against AI opponents
2. **Create Game** — set up a lobby, choose a dealing variant, add human or AI players
3. **Join Game** — enter a 6-character join code to play with friends

### Rules

- Standard 52-card deck. Trump suit rotates each round (Spades → Diamonds → Clubs → Hearts)
- Each round: bid how many tricks you expect to win, then play tricks
- Must follow lead suit if able. Highest trump wins, else highest of lead suit
- Bid met: positive points. Missed: negative points
- Dealer cannot bid to make total bids equal the number of cards (ensures someone must miss)

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

## License

MIT
