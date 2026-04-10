# Judgement Card Game

A full-stack real-time multiplayer card game (Judgement / Kachuful) with AI opponents. Built with FastAPI + WebSockets on the backend and React + TypeScript on the frontend.

Play against AI opponents at three difficulty levels, or with friends in real-time.

---

## Features

### Gameplay
- **Classic Judgement rules** — bid on tricks, follow suit, play trump strategically
- **3 dealing variants** — 10-to-1 (10 rounds), 8-down-up (16 rounds), 10-down-up (20 rounds)
- **3-6 players** — any mix of human and AI opponents
- **Must-lose mode** — optional variant where all players (not just dealer) are constrained on bids
- **Trump rotation** — Spades, Diamonds, Clubs, Hearts cycle predefined per round
- **Scoring** — met bids score positive (0 bid = +10, 1 bid = +11, N bid = N x 10), missed bids score the same magnitude negated

### AI Opponents
- **Easy** — random valid moves
- **Medium** — evaluates hand strength, leads high cards, uses shared trick-play logic
- **Hard** — counts cards, tracks what's been played, strategic bidding and play

### Frontend
- **Poker-table UI** — oval table with players seated around it
- **CSS-rendered playing cards** — no images, fully styled with SVG face card portraits (Jack, Queen, King)
- **Real-time WebSocket updates** — all actions broadcast instantly to all players
- **Trick animations** — cards play one-by-one, winner highlighted for 1 second, then cards collect to winner
- **Animated turn banner** — slides in and auto-fades when it's your turn
- **Compact stat badges** — split-circle showing cumulative score and tricks-won/bid for every player
- **Round-end scoreboard** — modal with full breakdown after each round
- **Final results** — rankings and complete session log at game end
- **Responsive** — mobile-first design, works on phones and desktops
- **Auto-reconnect** — WebSocket reconnects with exponential backoff if connection drops

### Backend
- **Clean layered architecture** — models (pure data) / game (rules) / ai (strategies) / api (transport)
- **State machine engine** — LOBBY → BIDDING → PLAYING → ROUND_OVER → GAME_OVER
- **Observer pattern** — engine emits typed events, consumed by WebSocket, AI orchestrator, and session logger
- **Config-driven rounds** — round definitions loaded from JSON files, cached immutably
- **Typed event payloads** — Pydantic models + factory functions for all 11 event types
- **82 tests** — covering trick resolution, scoring, validation, full game flow, AI, REST API, WebSocket, and config loading

---

## Prerequisites

- **Python 3.9+**
- **Node.js 18+** (with npm)

---

## Running Locally

### 1. Clone the repository

```bash
git clone <repo-url>
cd judgement
```

### 2. Start the backend

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Start the server (--ws websockets is required for WebSocket support)
python3 -m uvicorn app.main:app --reload --ws websockets
```

The backend runs on **http://localhost:8000**.

### 3. Start the frontend (new terminal)

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend runs on **http://localhost:3000** and automatically proxies `/api` and `/ws` requests to the backend on port 8000.

### 4. Play

Open **http://localhost:3000** in your browser. Create a game, add AI players, and start playing.

---

## Running Tests

```bash
# From project root
python3 -m pytest backend/tests/ -v
```

All 82 tests should pass. Tests cover:

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_trick_resolver.py` | 6 | Trick winner logic |
| `test_scorer.py` | 7 | Scoring formula |
| `test_validators.py` | 11 | Bid constraints, follow-suit, must-lose |
| `test_engine.py` | 14 | Full game flow, state transitions |
| `test_ai.py` | 16 | All AI strategies, hand evaluation |
| `test_api_rest.py` | 10 | REST endpoints, AI auto-play |
| `test_round_config.py` | 9 | JSON config loading, bridge tests |
| `test_websocket_game.py` | 5 | WebSocket lifecycle, multi-round play |

---

## Project Structure

```
judgement/
├── backend/
│   ├── app/
│   │   ├── models/          # Pydantic data models (Card, Player, Game, Events)
│   │   ├── game/            # Rules engine (pure logic, no I/O)
│   │   │   ├── engine.py        # Game state machine
│   │   │   ├── round_manager.py # Single-round lifecycle
│   │   │   ├── validators.py    # Bid/play legality
│   │   │   ├── trick_resolver.py# Trick winner resolution
│   │   │   ├── scorer.py        # Round scoring
│   │   │   ├── deck.py          # Card dealing
│   │   │   ├── round_config_loader.py  # JSON config loader
│   │   │   └── rounds/         # Round definition JSON files
│   │   ├── ai/              # AI opponent strategies
│   │   │   ├── easy.py          # Random valid moves
│   │   │   ├── medium.py        # Hand evaluation + lead high
│   │   │   ├── hard.py          # Card counting + strategic play
│   │   │   ├── card_play.py     # Shared card-play utilities
│   │   │   └── hand_evaluator.py# Hand strength analysis
│   │   ├── api/             # HTTP + WebSocket transport
│   │   │   ├── rest.py          # REST endpoints
│   │   │   ├── websocket.py     # Real-time WebSocket handler
│   │   │   └── schemas.py       # Request/response models
│   │   ├── game_manager.py  # Orchestrator (wires engine + AI)
│   │   └── main.py          # FastAPI app entry point
│   ├── tests/               # 82 tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/      # Card, Button, Modal, FaceCardArt, SuitIcon
│   │   │   ├── lobby/       # GameLobby, PlayerSetup, VariantSelector
│   │   │   ├── game/        # GameBoard, TrickArea, BidSelector, PlayerHand, etc.
│   │   │   └── scoreboard/  # Scoreboard, FinalResults
│   │   ├── hooks/           # useGame (reducer), useWebSocket (WS lifecycle)
│   │   ├── context/         # GameContext (state + actions provider)
│   │   ├── services/        # REST client, WebSocket client
│   │   ├── types/           # TypeScript type definitions
│   │   └── styles/          # CSS Modules + global variables
│   └── package.json
└── README.md
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/games` | Create a new game |
| `GET` | `/api/games/{game_id}` | Get game state |
| `GET` | `/api/games/{game_id}/hand/{player_id}` | Get player's hand |
| `POST` | `/api/games/{game_id}/bid` | Place a bid |
| `POST` | `/api/games/{game_id}/play` | Play a card |
| `GET` | `/api/games/{game_id}/session-log/{player_id}` | Get session log |
| `WS` | `/ws/{game_id}/{player_id}` | Real-time game WebSocket |

---

## Architecture

```
Browser (React)                       Server (FastAPI)
┌──────────────┐                     ┌──────────────────────┐
│  Components  │◄── WebSocket ──────►│  WebSocket API       │
│  (GameBoard, │                     │       │              │
│   Lobby,     │◄── REST ──────────►│  REST API            │
│   Scoreboard)│                     │       │              │
└──────┬───────┘                     │  Game Manager        │
       │                             │    ┌────┴─────┐      │
  useGame reducer                    │  Engine    AI        │
  useWebSocket                       │  (state    Strategies│
  GameContext                        │   machine) (3 levels)│
                                     └──────────────────────┘
```

---

## License

MIT
