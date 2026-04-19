# Judgement Card Game — Developer Guide

## Quick Reference

```bash
# Run all tests (from project root)
python3 -m pytest backend/tests/ -v

# Run backend server (MUST run from project root, not from backend/)
python3 -m uvicorn backend.app.main:app --reload --ws websockets

# Run frontend dev server (proxies /api and /ws to backend on :8000)
cd frontend && npm run dev

# Build frontend
cd frontend && npm run build

# Python version: 3.9 (use Optional[] not X | None in Pydantic models)
# TypeScript: erasableSyntaxOnly — use `as const` objects, not `enum`

# IMPORTANT: pydantic arch fix (run after any pip install touching pydantic)
# This Mac runs x86_64 Python via Rosetta — pip may pull arm64 wheels.
# If tests fail with "incompatible architecture", run:
python3 -m pip install --force-reinstall pydantic pydantic-core
# Verify: python3 -c "from pydantic import BaseModel"
```

## Architecture Overview

The backend has **four layers** with strict dependency rules:

```
models/        ← Pure data (no logic, no I/O)
game/          ← Game rules engine (depends on models only, ZERO I/O)
ai/            ← AI strategies (depends on models only, ZERO I/O)
api/           ← HTTP/WS transport (depends on everything above)
game_manager   ← Orchestrator (wires game/ + ai/ together)
```

**Key rule:** `game/` and `ai/` have NO dependency on `api/` or `game_manager`. They are pure logic, testable without mocks.

## File Map

### models/ — Data structures (Pydantic)

| File | Contains | Key types |
|------|----------|-----------|
| `card.py` | Card, suits, ranks | `Card`, `Suit`, `Rank`, `TRUMP_ORDER` |
| `player.py` | Player identity | `Player`, `PlayerType`, `AIDifficulty` |
| `game.py` | Game state structures | `GamePhase`, `DealingVariant`, `GameConfig`, `Bid`, `TrickPlay`, `Trick`, `RoundState`, `GameFullState` |
| `round_config.py` | Immutable round config | `RoundConfig` (round, cards, trump) — loaded from JSON |
| `events.py` | Observer event types | `EventType`, `GameEvent`, typed data models + factory functions |
| `session.py` | Game history logging | `SessionLog`, `RoundLog` |

### game/ — Rules engine (pure logic)

| File | Responsibility | Key function/class |
|------|---------------|-------------------|
| `deck.py` | Create, shuffle, deal cards | `create_deck()`, `shuffle_deck()`, `deal()` |
| `trick_resolver.py` | Who wins a trick | `resolve_trick(trick, trump_suit) → winner_id` |
| `scorer.py` | Round scoring | `score_round(bids, tricks_won) → scores` |
| `validators.py` | Bid/play legality | `validate_bid()`, `validate_play()`, `get_valid_cards()`, `get_forbidden_bid()` |
| `round_config_loader.py` | Load round configs from JSON | `load_round_configs(variant) → tuple[RoundConfig]` (cached with `@lru_cache`) |
| `rounds/*.json` | Predefined round definitions | `10_to_1.json`, `8_down_up.json`, `10_down_up.json` — round number, cards, trump per round |
| `round_manager.py` | Single round lifecycle | `RoundManager` — deals, tracks bids/tricks, resolves. Receives `trump_suit` as param (no longer computes it) |
| `engine.py` | Full game state machine | `GameEngine` — LOBBY→BIDDING→PLAYING→ROUND_OVER→GAME_OVER, emits events via factory functions |

**State machine flow:**
```
LOBBY → start_game() → BIDDING → all bids placed → PLAYING → all tricks done → ROUND_OVER → next round or GAME_OVER
```

**Engine is the single source of truth.** All mutations go through `engine.place_bid()` or `engine.play_card()`. The engine validates, updates state, and emits `GameEvent`s via typed factory functions.

**Public engine API** — external code MUST use these instead of accessing `_round_manager`:
- `get_round_context(player_id)` → `RoundContext` for AI decision-making
- `get_round_summary()` → `dict` for WebSocket/logging consumers
- `get_player_hand(player_id)`, `get_valid_bids(player_id)`, `get_valid_cards(player_id)`

**Round configs** are loaded from JSON files at game start via `load_round_configs()`. Each JSON defines round number, cards to deal, and trump suit. Trump is predefined, not computed at runtime.

### ai/ — AI opponents (Strategy pattern)

| File | Responsibility |
|------|---------------|
| `base.py` | `AIStrategy` ABC: `choose_bid(hand, valid_bids, context)`, `choose_card(hand, valid_cards, context)`. `RoundContext` carries `player_id` + visible game state. |
| `card_play.py` | Shared card-selection utilities: `would_win()`, `best_winning_card()`, `dump_lowest()` |
| `easy.py` | Random valid moves |
| `medium.py` | Hand evaluation, lead high, uses shared card_play for trick logic |
| `hard.py` | Card counting, refined estimation, strategic play, uses shared card_play |
| `smart_hard.py` | `SmartHardAI` — learns from winners via kNN, falls back to HardAI |
| `hand_evaluator.py` | Hand strength evaluation (trumps, aces, voids, ruffing potential) |
| `learning/` | Learning engine: `neighbor_model.py` (kNN), `features.py` (feature extraction), `decision_collector.py` (data collection), `data/` (JSONL training data) |

**`RoundContext`** carries: `player_id`, trump suit, bids placed, tricks won counts, cards played in previous tricks, current trick cards. AI NEVER sees other players' hands.

### api/ — Transport layer

| File | Responsibility |
|------|---------------|
| `schemas.py` | Request/response Pydantic models |
| `rest.py` | REST: `POST /api/games`, `GET /api/games/{id}`, `GET /hand/{pid}`, `POST /bid`, `POST /play`, `GET /session-log` |
| `websocket.py` | WS: `/ws/{game_id}/{player_id}` — actions: `bid`, `play`, `get_hand` |

### game_manager.py — Orchestrator

`GameManager` creates games and holds them in memory. `ManagedGame` wraps an engine and:
1. Registers AI strategies per AI player (based on `AIDifficulty`)
2. Listens for `TURN_CHANGED` events
3. When it's an AI player's turn, builds a `RoundContext` (with `player_id`) and calls `strategy.choose_bid/choose_card`
4. Logs rounds to `SessionLog`

**This is the only place where AI ↔ engine wiring happens.**

## Game Rules (Judgement / Kachuful)

- **Deck:** Standard 52 cards. Rank: 2 (low) → Ace (high)
- **Trump rotation:** Spades → Diamonds → Clubs → Hearts (repeating)
- **Dealer rotation:** Clockwise each round. Left of dealer bids/leads first
- **Dealing variants:**
  - `10_to_1`: 10→1 (10 rounds, max 5 players)
  - `8_down_up`: 8→1→8 (16 rounds, max 6 players)
  - `10_down_up`: 10→1→10 (20 rounds, max 5 players)
- **Bidding:** 0 to num_cards. Dealer can't make total bids = num_cards
- **Must-lose mode:** ALL players constrained (not just dealer)
- **Trick-taking:** Must follow lead suit if able. Highest trump wins, else highest lead suit
- **Scoring:** Bid met: 0→+10, 1→+11, N≥2→+N×10. Missed: same values negated

## Design Patterns

| Pattern | Where | Why |
|---------|-------|-----|
| **State Machine** | `GameEngine` | Clean phase transitions, prevents invalid actions |
| **Strategy** | `ai/` | Swap AI difficulty without touching engine |
| **Observer** | `GameEngine._emit()` | Engine doesn't know about WebSockets or game manager |
| **Config-driven** | `rounds/*.json` | Round rules predefined in JSON, loaded once, cached immutably |
| **Typed Events** | `events.py` factories | Compile-time type safety for event payloads, wire format stays `dict` |

## Testing

```
backend/tests/
├── test_trick_resolver.py          #  6 tests — trick winner logic
├── test_scorer.py                  #  7 tests — scoring formula
├── test_validators.py              # 11 tests — bid constraints, follow-suit
├── test_engine.py                  # 14 tests — full game flow, state transitions
├── test_ai.py                      # 16 tests — all strategies valid, hand eval, integration
├── test_api_rest.py                # 37 tests — REST endpoints, lobby, quick-join, AI auto-play
├── test_round_config.py            #  9 tests — JSON config loading, bridge tests vs runtime
├── test_websocket_game.py          # 10 tests — WS connect, two-round play, stuck detect, reconnect, persona on wire
├── test_multiplayer_integration.py #  6 tests — lobby→start→play full rounds, session log
├── test_edge_cases.py              # 17 tests — invalid inputs, duplicate names, error handling
├── test_analysis.py                # 30 tests — persona loader, fingerprint, cosine similarity, persona match
└── test_smart_ai.py                # 23 tests — features, neighbor model, collector, SmartHardAI, integration
                                     268 total
```

## Common Tasks

**Add a new AI difficulty:** Create `backend/app/ai/mythical.py` implementing `AIStrategy`, use shared helpers from `card_play.py`, add to `game_manager._make_strategy()`, add enum value to `models/player.py:AIDifficulty`.

**Add a new API endpoint:** Add schema to `api/schemas.py`, add route to `api/rest.py`, add test to `tests/test_api_rest.py`.

**Change scoring rules:** Edit `game/scorer.py:score_round()`, update `tests/test_scorer.py`.

**Change bid constraints:** Edit `game/validators.py:get_forbidden_bid()`, update `tests/test_validators.py`.

**Add persistence:** Create `persistence/repository.py` with save/load for `SessionLog`. Wire into `ManagedGame._log_game_over()` in `game_manager.py`.

## Code Style

- **Modularity:** Every method does one thing. Long methods are split into small, named helpers (e.g. `_check_bidding_complete()`, `_emit_round_started()`).
- **Descriptive variables:** No single-letter variables. Use `card`, `player`, `bid`, `suit`, `offset` — not `c`, `p`, `b`, `s`, `i`.
- **Shared logic:** Card-play helpers (`would_win`, `best_winning_card`, `dump_lowest`) live in `ai/card_play.py` and are reused by MediumAI and HardAI. Do not duplicate these.

## Frontend Architecture

### Setup: Vite + React + TypeScript

```bash
cd frontend && npm run dev    # Dev server on :3000, proxies /api and /ws to :8000
cd frontend && npm run build  # Production build
```

### File Map

| Directory | Contents |
|-----------|----------|
| `types/card.ts` | `Suit`, `Rank`, `Card`, display helpers (`SUIT_SYMBOLS`, `RANK_DISPLAY`, `cardDisplayName`) |
| `types/game.ts` | `GamePhase`, `DealingVariant`, `Player`, `Bid`, `TrickPlay`, `GameState`, `INITIAL_GAME_STATE`, variant labels/limits |
| `types/events.ts` | `ServerEventType`, `ClientAction`, typed event data interfaces for all WebSocket messages |
| `services/api.ts` | REST client — `createGame()`, `getGameState()`, `getPlayerHand()`, `placeBid()`, `playCard()`, `getSessionLog()` |
| `services/websocket.ts` | `GameWebSocket` class — connect/disconnect, auto-reconnect with exponential backoff, `sendBid()`, `sendPlayCard()`, `sendGetHand()` |
| `hooks/useGame.ts` | `useGame()` — game state reducer with handlers for every server event type |
| `hooks/useWebSocket.ts` | `useWebSocket()` — manages WebSocket lifecycle, exposes `connectionStatus` and action senders |
| `context/GameContext.tsx` | `GameProvider` + `useGameContext()` — wires state + WebSocket together, single source of truth for components |
| `styles/global.css` | CSS variables (card table green theme), reset, mobile-first base styles |

### Components

| Directory | Components | Responsibility |
|-----------|------------|----------------|
| `common/` | `Card`, `CardBack`, `SuitIcon`, `Button`, `Modal` | Base UI primitives, CSS-rendered playing cards |
| `lobby/` | `GameLobby`, `PlayerSetup`, `VariantSelector` | Game creation: variant, players, must-lose toggle |
| `game/` | `GameBoard`, `RoundInfo`, `OpponentArea`, `TrickArea`, `BidSelector`, `PlayerHand`, `PlayerInfo` | Main gameplay: bidding, trick-taking, hand display |
| `scoreboard/` | `Scoreboard`, `FinalResults` | Round scores table, game-over with rankings |

### Styles

| File | Purpose |
|------|---------|
| `global.css` | CSS variables, reset, base theme |
| `card.module.css` | Playing card + card back styles |
| `common.module.css` | Button + Modal styles |
| `lobby.module.css` | Lobby form, player rows, variant selector |
| `game.module.css` | Board grid, trick area, bid selector, hand layout |
| `scoreboard.module.css` | Score table, final results |
| `animations.module.css` | Card deal, slide, collect, fade, stagger animations |

### Key patterns

- **No enums:** TypeScript `erasableSyntaxOnly` is enabled. Use `const` objects + union types instead of `enum`.
- **No `public` parameter properties:** Use explicit field declarations in classes.
- **State via reducer:** All game state flows through `useGame` reducer. Server events dispatch through `handleServerEvent` → individual handler functions.
- **WebSocket reconnect:** Exponential backoff (1s → 2s → 4s → 8s → 16s), max 5 attempts.
- **Proxy:** Vite dev server proxies `/api/*` and `/ws/*` to backend on `:8000`.
- **Component modularity:** Each component is a single function. Helper logic (finding bids, building status messages) lives as standalone functions below the component.
- **Screen routing:** `App.tsx` switches between Lobby, GameBoard, and FinalResults based on `GamePhase`.

## Gotchas

- **Python 3.9:** Use `Optional[X]` and `List[X]` in Pydantic models, not `X | None` or `list[X]`. `from __future__ import annotations` helps in non-Pydantic files but Pydantic evaluates annotations at runtime.
- **Imports:** All game logic imports use `backend.app.models` / `backend.app.game` (absolute from project root). Tests run from project root with `python3 -m pytest`.
- **AI information isolation:** `RoundContext` is the AI's view of the world. It carries `player_id` so AI can look up its own bid/tricks. Never pass other players' hands. Use `engine.get_round_context(pid)` to build it.
- **game_manager.py is the wiring layer:** If AI isn't playing automatically, the bug is in `ManagedGame._try_ai_turn()`.
- **No `_round_manager` access outside engine:** All external consumers must use `get_round_context()` or `get_round_summary()`. The `_round_manager` is an internal implementation detail.
- **Event factories:** Always use factory functions from `events.py` (e.g. `round_started_event(...)`) instead of constructing `GameEvent(...)` with inline dicts. This gives type safety at the producer side.
- **No persistence yet:** `SessionLog` is built in memory but not saved to disk. See "Add persistence" in Common Tasks.
- **Frontend enums:** Do NOT use TypeScript `enum`. The project has `erasableSyntaxOnly: true`. Use `as const` objects with union types.
- **uvicorn WebSocket:** Must run with `--ws websockets` flag or WebSocket connections return 404.
- **uvicorn start directory:** Must start from **project root** with `python3 -m uvicorn backend.app.main:app`, NOT from `backend/` with `app.main:app`. Starting from the wrong directory causes `lobby_router` and other routers to silently fail to register — all `/api/lobby/*` routes return 404. The `--reload` flag also won't detect changes if the module path doesn't match. If you see `{"detail":"Not Found"}` on lobby/quick-join endpoints, this is almost certainly the cause.
- **Port already in use:** If uvicorn fails with `[Errno 48] Address already in use`, kill the old process first: `lsof -ti:8000 | xargs kill -9`. This happens when a previous server process gets stuck.
- **pydantic_core arch mismatch:** This Mac runs Python 3.9 under Rosetta (x86_64) but `pip install` may pull arm64 wheels for pydantic_core. If you see `ImportError: dlopen ... incompatible architecture (have 'arm64', need 'x86_64')`, fix with: `python3 -m pip install --force-reinstall pydantic pydantic-core`. **Always verify pydantic imports work before running tests:** `python3 -c "from pydantic import BaseModel"`. This MUST be done after any `pip install` that touches pydantic.
