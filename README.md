# Judgement

Indian trick-taking card game (also known as Kachuful). Play against AI opponents or with friends online.

## Quick Start

```bash
# First time setup (installs everything, handles Apple Silicon)
./setup

# Play
./play
```

`./play` builds the frontend, starts the server, and opens the game — as a desktop window if [pywebview](https://pywebview.flowrl.com/) is installed, or in your browser otherwise.

### Manual Install (if you prefer)

```bash
pip3 install -r backend/requirements.txt
cd frontend && npm install && cd ..
pip3 install pywebview  # optional, for desktop mode
./play
```

## How to Play

- **Quick Play** — instant game against AI opponents
- **Create Game** — set up a lobby, choose variant and players
- **Join Game** — enter a join code to play with friends

### Game Rules

- Standard 52-card deck. Trump suit rotates each round (Spades, Diamonds, Clubs, Hearts)
- Each round: bid how many tricks you think you'll win, then play
- Must follow lead suit if able. Highest trump wins, else highest of lead suit
- **Scoring:** Hit your bid = positive points. Miss = negative points

### Dealing Variants

| Variant | Rounds | Max Players |
|---------|--------|-------------|
| 10 → 1 | 10 | 5 |
| 8 → 1 → 8 | 16 | 6 |
| 10 → 1 → 10 | 20 | 5 |

## Mobile Testing

The game is mobile-friendly. To test on your phone:

```bash
# Start the server (accessible on local network)
./scripts/build.sh
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --ws websockets
```

Then open `http://<your-computer-ip>:8000` on your phone (same WiFi network).
Find your IP with `ifconfig | grep "inet "` on Mac or `hostname -I` on Linux.

## Development

```bash
# Backend (terminal 1)
./scripts/dev.sh

# Frontend (terminal 2)
cd frontend && npm run dev

# Run tests (190 tests)
python3 -m pytest backend/tests/ -v

# Security scan
python3 scripts/security_scan.py
```

## Deployment

### Single Server

```bash
./scripts/build.sh
./scripts/serve.sh
# Game available at http://localhost:8000
```

### Docker

```bash
docker build -t judgement .
docker run -p 8000:8000 judgement
```

## Tech Stack

- **Backend:** Python 3.9, FastAPI, WebSockets
- **Frontend:** React 19, TypeScript, Vite
- **Desktop:** pywebview (optional)
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
├── scripts/                # dev, build, serve, security scan
└── Dockerfile              # Single container deployment
```
