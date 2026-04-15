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

### Desktop App
- **Standalone macOS/Windows application** via PyInstaller
- **One-command build** — `./scripts/package.sh` handles all dependencies
- **In-app update button** — check for and apply updates without using the terminal
- **Native window** via pywebview (no browser required)

### Infrastructure
- **Dockerized** — single container deployment with `docker build && docker run`
- **Automated test suite** — 210+ tests covering game logic, AI, REST API, and WebSocket
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

## Roadmap

- **Online multiplayer** — lobby system with join codes, real-time WebSocket play, auto-reconnect, mixed human/AI games
- **Developer API** — public REST API with API key authentication for building bots, running tournaments, and third-party integrations
- **Leaderboards** — persistent player stats and rankings
- **Custom rules** — configurable scoring, trump selection, and house rules
- **Mobile app** — native iOS/Android versions
