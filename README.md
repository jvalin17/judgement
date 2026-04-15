# Judgement

Indian trick-taking card game (also known as Kachuful). Play solo against AI or online with friends.

- **Single player** — instant game against easy/medium/hard AI
- **Multiplayer** — create a lobby, share the join code, play over WebSocket
- **Desktop app** — standalone macOS/Windows app via PyInstaller

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
./setup                  # Install build dependencies
./scripts/package.sh     # Build the app
```

Then install:
- **macOS:** Copy `dist/Judgement.app` to your Applications folder, or run `open dist/Judgement.app`
- **Windows:** Run `dist/Judgement/Judgement.exe`
- **Linux:** Run `dist/Judgement/Judgement`

### Option 3: Run from Source

```bash
git clone <repo-url> && cd judgement
./setup    # One-time: installs all dependencies
./play     # Build frontend, start server, open game
```

Opens as a desktop window if [pywebview](https://pywebview.flowrl.com/) is available, otherwise opens in your browser at `http://localhost:8000`.

## Common Workflows

| Task | Command |
|------|---------|
| First time setup | `./setup` |
| Play the game | `./play` |
| Build standalone app | `./scripts/package.sh` |
| Run tests | `python3 -m pytest backend/tests/ -v` |
| Dev server (backend) | `./scripts/dev.sh` |
| Dev server (frontend) | `cd frontend && npm run dev` |
| Build frontend only | `cd frontend && npm run build` |
| Production server | `./scripts/build.sh && ./scripts/serve.sh` |
| Security scan | `python3 scripts/security_scan.py` |
| Docker | `docker build -t judgement . && docker run -p 8000:8000 judgement` |

## How to Play

- **Quick Play** — instant game against AI opponents
- **Create Game** — set up a lobby, choose variant, add human/AI players
- **Join Game** — enter a 6-character join code to play with friends
- **Multiplayer** — real-time WebSocket play, auto-reconnect on disconnect

### Rules

- Standard 52-card deck. Trump suit rotates each round
- Each round: bid how many tricks you'll win, then play
- Must follow lead suit if able. Highest trump wins, else highest of lead suit
- Hit your bid = positive points. Miss = negative points

### Dealing Variants

| Variant | Rounds | Max Players |
|---------|--------|-------------|
| 10 → 1 | 10 | 5 |
| 8 → 1 → 8 | 16 | 6 |
| 10 → 1 → 10 | 20 | 5 |
| 8 → 5 → 8 | 8 | 6 |

## Tech Stack

- **Backend:** Python 3.9, FastAPI, WebSockets
- **Frontend:** React 19, TypeScript, Vite
- **Desktop:** pywebview (optional) / PyInstaller (standalone)
- **AI:** Three difficulty levels (easy, medium, hard)

## Project Structure

```
judgement/
├── play                    # One-command launcher
├── setup                   # One-time dependency installer
├── backend/
│   ├── app/
│   │   ├── models/         # Pydantic data models
│   │   ├── game/           # Rules engine (pure logic, no I/O)
│   │   ├── ai/             # AI strategies (easy, medium, hard)
│   │   ├── api/            # REST + WebSocket transport
│   │   ├── game_manager.py # Orchestrator
│   │   └── main.py         # FastAPI entry point
│   └── tests/              # 210 tests
├── frontend/src/
│   ├── components/         # React components
│   ├── hooks/              # useGame, useWebSocket
│   ├── context/            # GameContext provider
│   ├── services/           # REST + WebSocket clients
│   └── styles/             # CSS Modules
├── desktop/                # pywebview desktop launcher
├── scripts/                # dev, build, serve, package, security scan
└── Dockerfile              # Single container deployment
```
