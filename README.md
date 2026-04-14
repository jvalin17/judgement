# Judgement

Indian trick-taking card game (also known as Kachuful). Play against AI opponents or with friends online.

## System Requirements

- **Python** 3.9+
- **Node.js** 18+
- **OS:** macOS, Windows, Linux

## Install & Play

```bash
./setup    # One-time: installs all dependencies
./play     # Build frontend, start server, open game
```

Opens as a desktop window if [pywebview](https://pywebview.flowrl.com/) is available, otherwise opens in your browser at `http://localhost:8000`.

### Standalone Desktop App (no dependencies needed to run)

```bash
./scripts/package.sh    # Build Judgement.app (macOS) or Judgement.exe (Windows)
open dist/Judgement.app  # Double-click to play — no Python/Node needed
```

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
- **Create Game** — set up a lobby, choose variant and players
- **Join Game** — enter a join code to play with friends

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
│   └── tests/              # 190 tests
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
