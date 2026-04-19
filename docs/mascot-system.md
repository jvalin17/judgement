# Mascot / Persona System — Design & Implementation

## Overview

At the end of every game, each **human** player receives a "play style" persona — a character (animal, Pokemon, cartoon, superhero, or poker archetype) that best matches how they played. The persona card appears on the Game Over screen with trait comparison bars.

The system is fully **offline** — all 43 persona definitions are bundled in a single JSON file. No internet connectivity is needed.

## Architecture

```
Player finishes game
        │
        ▼
┌─────────────────────┐
│  SessionLog (rounds) │  ← accumulated during gameplay by game_manager
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  compute_fingerprint │  ← analysis/fingerprint.py
│  (6-dimension vector)│
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  pick_persona        │  ← analysis/persona_match.py
│  (cosine similarity) │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Embedded in         │
│  GAME_OVER event     │  ← game_manager._handle_game_over()
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  PersonaCard on      │
│  FinalResults screen │  ← frontend/src/components/scoreboard/FinalResults.tsx
└─────────────────────┘
```

## The 6 Trait Dimensions

Every player and every persona is described by a vector of 6 values, each in the range [0.0, 1.0]:

| Dimension       | What it measures                                                |
|-----------------|-----------------------------------------------------------------|
| **Risk**        | How aggressively does the player bid relative to their hand?    |
| **Planning**    | How accurately does the player hit their bid?                   |
| **Patience**    | Does the player bid conservatively (low) or reach for the moon? |
| **Aggression**  | How much does the player overbid relative to hand strength?     |
| **Adaptability**| How different are the player's bids across rounds?              |
| **Consistency** | How consistently does the player hit their bid across rounds?   |

## Backend Files

### `backend/app/analysis/personas.json`

The corpus of 43 personas across 5 categories:

- **Superhero** (8): Batman, Spider-Man, Shaktimaan, Krrish, Iron Man, Superman, Black Panther, Doga
- **Animal** (9): Fox, Owl, Shark, Turtle, Eagle, Chameleon, Elephant, Ant, Wolf
- **Poker** (8): Maniac, TAG, LAG, Nit, Grinder, Bluffer, Shark, Calling Station
- **Cartoon** (9): Dexter, Bugs Bunny, Tom, Jerry, Scooby-Doo, Johnny Bravo, Courage, Captain Haddock, Doraemon
- **Pokemon** (9): Pikachu, Mewtwo, Snorlax, Eevee, Gengar, Charizard, Alakazam, Dragonite, Ditto

Each persona has:
```json
{
  "id": "batman",
  "category": "superhero",
  "name": "Batman",
  "tagline": "The strategist who plans every move",
  "traits": [0.4, 0.95, 0.8, 0.6, 0.7, 0.85]
}
```

Traits array maps to: `[risk, planning, patience, aggression, adaptability, consistency]`

### `backend/app/analysis/persona_loader.py`

- `load_personas()` → loads and caches (via `@lru_cache`) all 43 personas from JSON
- `get_persona_by_id(persona_id)` → lookup by ID, raises `KeyError` if not found
- `Persona` class with `id`, `category`, `name`, `tagline`, `traits` (dict)
- `DIMENSIONS` = `["risk", "planning", "patience", "aggression", "adaptability", "consistency"]`

### `backend/app/analysis/fingerprint.py`

Computes a player's trait vector from their `SessionLog`.

**`compute_fingerprint(session_log, player_id) → Dict[str, float]`**

For each round, `project_round()` computes per-dimension scores:

- **Risk**: `bid / num_cards` — bidding 6 out of 7 cards = high risk
- **Planning**: `1 - |bid - tricks_won| / num_cards` — hitting your bid exactly = perfect planning
- **Patience**: `1 - bid / num_cards` — bidding 0 = maximum patience
- **Aggression**: `bid / max(hand_avg, 0.01)` — overbidding relative to table average
- **Adaptability**: standard deviation of bids across rounds (normalized)
- **Consistency**: `1 - variance(bid_errors)` across all rounds

Multi-round aggregation uses **exponential decay weighting** (alpha = 0.6) so recent rounds count more than early ones.

Empty sessions return a neutral vector (all 0.5).

### `backend/app/analysis/persona_match.py`

**`cosine_similarity(vec_a, vec_b) → float`**

Standard cosine similarity between two trait vectors. Returns 0.0 for zero vectors.

**`best_personas(player_vec, recent_ids=[], top_k=3) → List[Tuple[str, float]]`**

1. Computes cosine similarity between player vector and all 43 persona vectors
2. Applies a novelty penalty (0.9x multiplier) for recently-seen personas
3. Returns top-k (persona_id, score) pairs sorted by score descending

**`pick_persona(player_vec, recent_ids=[], rng=None) → Persona`**

1. Gets top-3 personas from `best_personas()`
2. Uses weighted random selection (scores as weights) to pick one
3. Returns the full `Persona` object

This adds variety — the same player won't always get the exact same persona.

## How It Gets Triggered

### Backend: `game_manager.py`

When the engine emits a `GAME_OVER` event, the game manager **intercepts** it:

```python
def _on_event(self, event: GameEvent) -> None:
    if event.event_type == EventType.GAME_OVER:
        self._handle_game_over(event)
        return  # original event is NOT forwarded
    ...
```

`_handle_game_over()` creates **per-player enriched events**:

```python
def _handle_game_over(self, event: GameEvent) -> None:
    self._log_game_over(event)
    for player in self.engine.state.players:
        persona_award = self._compute_persona(player.id) if player.player_type == PlayerType.HUMAN else None
        enriched = game_over_event(
            final_scores=..., winners=..., persona=persona_award,
        )
        enriched.player_id = player.id  # target specific player
        self._notify_callbacks(enriched)
```

Key design decisions:
- **Persona is embedded in the GAME_OVER event**, not sent as a separate event. This avoids timing/buffering issues where a separate event could get lost in the frontend event queue.
- **Each player gets their own GAME_OVER event** with `player_id` set, so the WebSocket writer only delivers it to the right player.
- **AI players get `persona: null`** — only human players get persona computation.
- `_compute_persona()` wraps everything in try/except to prevent persona errors from breaking the game-over flow.

### Backend: Event model

```python
# models/events.py
class PersonaAward(BaseModel):
    persona_id: str
    persona_name: str
    persona_category: str
    persona_tagline: str
    traits: Dict[str, float]        # persona's ideal trait vector
    player_traits: Dict[str, float] # player's computed trait vector

class GameOverData(BaseModel):
    final_scores: Dict[str, int]
    winners: List[str]
    persona: Optional[PersonaAward] = None
```

### WebSocket delivery

The `_writer_task` in `websocket.py` filters events by `player_id`:
```python
if event.player_id and event.player_id != player_id:
    continue  # skip events not for this player
```

So each human only receives their own persona, and AI GAME_OVER events (with `persona: null`) only go to AI connections (which don't exist in practice).

### Frontend: State management

**`useGame.ts`** — the reducer handles GAME_OVER:
```typescript
function handleGameOver(state: GameState, data: GameOverEventData): GameState {
  return {
    ...state,
    phase: GamePhase.GAME_OVER,
    cumulativeScores: data.final_scores,
    awardedPersona: data.persona ?? null,
  };
}
```

**`GameState`** has `awardedPersona: PersonaAward | null`

**`App.tsx`** switches to `FinalResults` when phase is `GAME_OVER`, passing `state.awardedPersona`.

### Frontend: PersonaCard component

**`FinalResults.tsx`** renders the persona card between the winner display and score list:

```tsx
{awardedPersona && <PersonaCard persona={awardedPersona} />}
```

The `PersonaCard` shows:
- "Your Play Style" header
- Persona name (e.g., "Batman") in accent color
- Category label (e.g., "Superhero")
- Tagline in italic
- 6 trait bars comparing player values vs persona values
  - Orange gradient bar = player's actual trait value
  - White marker = persona's ideal trait value

### Frontend: Celebration animations

**Confetti** (150 pieces):
- 3 waves of 50 pieces each
- 12 colors, 3 shapes (rectangle, circle, triangle)
- Seeded PRNG for deterministic rendering
- CSS `confettiFall` animation with sway

**Fireworks** (8 bursts, 12 sparks each):
- Positioned randomly across top half of screen
- Each spark explodes outward using CSS custom properties (`--spark-x`, `--spark-y`)
- Staggered delays for sequential bursts

Both use module-level constants (not React state) to avoid re-render issues.

## Data Flow Summary

```
1. During game: game_manager logs each round to SessionLog
2. Game ends: engine emits GAME_OVER
3. game_manager intercepts → computes fingerprint from SessionLog
4. Fingerprint matched to best persona via cosine similarity
5. PersonaAward embedded in enriched GAME_OVER event
6. WebSocket delivers per-player event to frontend
7. Reducer stores awardedPersona in GameState
8. FinalResults renders PersonaCard with trait bars
```

## Test Coverage

| Test file | What it covers | Count |
|-----------|---------------|-------|
| `test_analysis.py` | Persona loader, fingerprint, cosine sim, matching, integration | 30 |
| `test_websocket_game.py` | GAME_OVER WebSocket message has persona data on the wire | 1 |

Key integration tests:
- `test_full_game_emits_persona_in_game_over` — plays a full 3-round game, verifies GAME_OVER event callback has persona with all 6 traits
- `test_ai_only_game_has_no_persona` — verifies AI-only games have `persona: null`
- `test_game_over_has_persona_on_wire` — verifies the actual WebSocket JSON message sent to the client contains persona data
