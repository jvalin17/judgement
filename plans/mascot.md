# Mascot — persona-matched commentary that varies every time

## What this is

A small character on the screen who, at moments the player notices, says one short line about *something specific* the player did, **and** anchors it to a recognisable persona ("Foxlike.", "That's a Batman move.", "Pure Calling Station — and it paid off.").

Two layers of output:

1. **Per-round mascot line** — after each round, one short observation about the player's last round, optionally tagged with a persona reference. Examples:
   > "Held the trump Ace till trick 7. Foxlike — patient, opportunistic."
   > "Bid 5 with no aces. Loose-Aggressive but it landed."
   > "Voided clubs by trick 3. Black-Widow play."

2. **End-of-game persona card** — when the game ends, a small modal: *"Your play style this game: The Fox"* with a one-liner and the traits that earned it. Different game → different persona, even with similar play, because the matcher picks weighted-randomly from the top-K matches.

Both layers draw from a single **persona corpus** (a "document vector" library) that includes superheroes, animals, and classic poker archetypes. Each persona has a trait vector. Each round we project the player's behaviour into the same trait space and match by similarity.

This is the "document vector or something" the user asked for, implemented as a small JSON corpus + cosine-similarity matcher — no LLM, no learned embeddings, no inference. Pure rule-based, deterministic given a seed, fully unit-testable.

## Constraints (from user)

1. **Keep it simple.** No LLM, no real ML. Rule-based scoring + a static persona corpus.
2. **Different strengths every time.** Same player playing the same way for ten rounds should hear ten different observations / persona references. Same play style across multiple games should still surface different personas.
3. **Cover a wide trait space.** Risk taker, gambler, sorted, planner, patient, aggressive, opportunistic, comeback artist, etc.
4. **Use recognisable archetypes.** Superheroes, animals — characters players can mentally picture. Not "Player Type 7C".
5. **Player-only.** The mascot talks about the human player.
6. **Read-only.** Cannot affect gameplay. Cannot leak hints.

## High-level design

```
┌──────────────────┐  round_complete  ┌────────────────────────┐
│  GameEngine      │ ───────────────> │ analysis.fingerprint   │
│  (RoundLog +     │                  │  player → trait vector │
│   game state)    │                  │  (this round + history)│
└──────────────────┘                  └──────────┬─────────────┘
                                                 │ trait vector
                                                 ▼
┌────────────────────┐  axes & scores  ┌────────────────────────┐
│ analysis.evaluator │ <───────────────│ analysis.persona_match │
│ scores axes for    │                 │  cosine sim vs corpus  │
│ this round         │                 │  pick from top-K       │
└─────────┬──────────┘                 └──────────┬─────────────┘
          │                                       │ persona_id
          ▼                                       ▼
┌────────────────────────────────────────────────────────────────┐
│              analysis.commentary                               │
│  combine: 1 axis observation + persona-flavoured suffix        │
│  draw phrasing from persona-specific or generic line pool      │
└─────────────────────────┬──────────────────────────────────────┘
                          ▼
┌────────────────────────────────────────────────────────────────┐
│  WebSocket event MASCOT_MESSAGE → frontend <Mascot> bubble     │
└────────────────────────────────────────────────────────────────┘

At game_complete:
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│  Final persona = matcher run on full-game fingerprint          │
│  → MASCOT_PERSONA_AWARDED event → end-of-game card             │
└────────────────────────────────────────────────────────────────┘
```

## The persona corpus

A static JSON file at `backend/app/analysis/personas.source.json` containing ~43 personas across **five categories**: superheroes (Marvel), animal totems, poker archetypes, cartoon / Indian icons, and iconic Pokémon. Each persona has a 6-dimension trait vector and a small phrasing pool. The source JSON is **compiled into a compact packed form** for shipping (see §"Compact encoding" below).

### The 6 trait dimensions (the "vector space")

These are the only things both the personas and the player are scored on. Picked because they map cleanly to Judgement's mechanics:

| Dim | What it means | How a player scores high on it |
|-----|---------------|--------------------------------|
| `risk` | Willingness to bid above safe range | Bids ≥ ⌈cards/2⌉ frequently; bids non-zero on weak hands |
| `planning` | Long-horizon thinking | Hits exact bid often; manages trump release across the round |
| `patience` | Holds power cards back | Doesn't dump trump Ace early; voids before trumping |
| `aggression` | Plays high cards / leads suits | Leads with Aces/Kings; ruffs whenever legal |
| `adaptability` | Adjusts to game state | Bids low when table over-bids, high when table under-bids |
| `consistency` | Hits bid reliably | Variance of (bid − tricks) across rounds is low |

All values 0.0–1.0. Player projection uses the same dims, computed from `RoundLog` history (see §"Player fingerprint" below).

### Persona categories

**Superhero personas** (6, recognisable to most players):

| Persona | risk | plan | pat | agg | adapt | cons | One-liner trait |
|---------|------|------|-----|-----|-------|------|-----------------|
| Batman | 0.4 | 0.95 | 0.8 | 0.6 | 0.7 | 0.85 | The strategist who plans every move |
| Iron Man | 0.85 | 0.7 | 0.3 | 0.9 | 0.6 | 0.5 | Brilliant, brash, inventive |
| Spider-Man | 0.6 | 0.5 | 0.4 | 0.7 | 0.95 | 0.5 | Quick, curious, improvises mid-trick |
| Captain America | 0.3 | 0.7 | 0.7 | 0.5 | 0.4 | 0.95 | Loyal to the plan, bid hits like clockwork |
| Black Widow | 0.5 | 0.85 | 0.85 | 0.4 | 0.9 | 0.75 | Reads the room, plays the long game |
| Thor | 0.9 | 0.4 | 0.3 | 0.95 | 0.4 | 0.4 | Hammers down trump cards, no subtlety |

**Animal totem personas** (12, broad coverage):

| Persona | risk | plan | pat | agg | adapt | cons | One-liner trait |
|---------|------|------|-----|-----|-------|------|-----------------|
| Fox | 0.6 | 0.7 | 0.7 | 0.5 | 0.9 | 0.6 | Cunning, opportunistic, sets traps |
| Owl | 0.3 | 0.95 | 0.85 | 0.4 | 0.7 | 0.85 | Wise, observant, plays on knowledge |
| Wolf | 0.5 | 0.7 | 0.5 | 0.7 | 0.6 | 0.7 | Loyal pack thinker, leads when it matters |
| Elephant | 0.3 | 0.85 | 0.95 | 0.4 | 0.4 | 0.9 | Never forgets a card played |
| Turtle | 0.2 | 0.8 | 0.95 | 0.2 | 0.3 | 0.95 | Steady, patient, low-bid specialist |
| Eagle | 0.5 | 0.85 | 0.6 | 0.7 | 0.7 | 0.7 | Sees the whole table at once |
| Hawk | 0.6 | 0.7 | 0.4 | 0.85 | 0.5 | 0.6 | Sharp focus, decisive strikes |
| Lion | 0.85 | 0.5 | 0.4 | 0.95 | 0.4 | 0.5 | Brave, leads from the front, takes risks |
| Dolphin | 0.6 | 0.5 | 0.4 | 0.6 | 0.95 | 0.5 | Playful, sociable, reads opponents |
| Raven | 0.7 | 0.7 | 0.7 | 0.5 | 0.85 | 0.6 | Trickster — bluffs and bait bids |
| Ant | 0.2 | 0.85 | 0.85 | 0.3 | 0.4 | 0.95 | Disciplined, methodical, group-minded |
| Bee | 0.4 | 0.95 | 0.6 | 0.5 | 0.6 | 0.9 | Organised, busy, every card has a job |

**Card-game archetype personas** (6, lifted from poker — players will recognise):

| Persona | risk | plan | pat | agg | adapt | cons | One-liner trait |
|---------|------|------|-----|-----|-------|------|-----------------|
| Tight-Aggressive (TAG) | 0.5 | 0.85 | 0.75 | 0.85 | 0.7 | 0.85 | Disciplined picker, attacks when in |
| Loose-Aggressive (LAG) | 0.85 | 0.6 | 0.3 | 0.95 | 0.7 | 0.5 | Plays everything, bets everything |
| Tight-Passive (Nit) | 0.15 | 0.8 | 0.95 | 0.2 | 0.3 | 0.9 | Bids low, plays safe, waits for premium |
| Loose-Passive (Calling Station) | 0.6 | 0.3 | 0.4 | 0.3 | 0.4 | 0.4 | In every trick, rarely commits |
| Maniac | 0.95 | 0.2 | 0.1 | 0.95 | 0.5 | 0.3 | Chaos agent — high variance, big swings |
| Grinder | 0.4 | 0.85 | 0.8 | 0.6 | 0.6 | 0.95 | Quietly racks up small wins each round |

**Cartoon & Indian-icon personas** (9, recognisable to most Indian audiences):

| Persona | risk | plan | pat | agg | adapt | cons | One-liner trait |
|---------|------|------|-----|-----|-------|------|-----------------|
| Chhota Bheem | 0.5 | 0.5 | 0.6 | 0.85 | 0.6 | 0.85 | Laddoo-strong, leads from the front |
| Krrish | 0.6 | 0.7 | 0.7 | 0.8 | 0.7 | 0.85 | Lightning-fast, balanced hero |
| Shaktimaan | 0.3 | 0.95 | 0.95 | 0.6 | 0.6 | 0.95 | Yogic restraint, perfect discipline |
| Dexter (Dexter's Laboratory) | 0.4 | 0.95 | 0.5 | 0.6 | 0.5 | 0.85 | Boy genius — over-engineers every trick |
| Bugs Bunny | 0.55 | 0.85 | 0.8 | 0.5 | 0.95 | 0.8 | Calm trickster, "Eh, what's up doc" energy |
| Tom (Tom & Jerry) | 0.6 | 0.8 | 0.4 | 0.85 | 0.4 | 0.5 | Elaborate schemes, doesn't always close |
| Jerry (Tom & Jerry) | 0.5 | 0.8 | 0.6 | 0.5 | 0.95 | 0.85 | Tiny, quick, escapes any trap |
| Scooby Doo | 0.2 | 0.3 | 0.4 | 0.3 | 0.7 | 0.4 | Reluctant but somehow wins |
| Johnny Bravo | 0.85 | 0.2 | 0.2 | 0.95 | 0.3 | 0.4 | All flex, all bid, no plan |

**Iconic Pokémon personas** (10, instantly recognisable — Pokédex behaviour + community MBTI mappings):

| Persona | risk | plan | pat | agg | adapt | cons | One-liner trait |
|---------|------|------|-----|-----|-------|------|-----------------|
| Pikachu | 0.55 | 0.5 | 0.4 | 0.7 | 0.9 | 0.6 | Curious, plucky, shocks when cornered |
| Charizard | 0.85 | 0.5 | 0.3 | 0.95 | 0.5 | 0.5 | Fiery, proud, loves a new challenge |
| Snorlax | 0.2 | 0.4 | 0.95 | 0.2 | 0.3 | 0.9 | Unmovable, waits for the perfect bite |
| Mewtwo | 0.5 | 0.98 | 0.9 | 0.7 | 0.6 | 0.9 | Coldly intelligent, calculated every trick |
| Gengar | 0.7 | 0.75 | 0.8 | 0.6 | 0.9 | 0.6 | Mischief in the shadows, springs the trap |
| Eevee | 0.5 | 0.4 | 0.5 | 0.5 | 0.98 | 0.5 | Adapts to whatever the table needs |
| Psyduck | 0.5 | 0.2 | 0.3 | 0.4 | 0.3 | 0.25 | Flails — then accidentally wins the trick |
| Jigglypuff | 0.7 | 0.4 | 0.4 | 0.6 | 0.7 | 0.4 | Wants the spotlight, bids loud |
| Alakazam | 0.6 | 0.95 | 0.7 | 0.6 | 0.85 | 0.85 | Reads the whole table at once |
| Dragonite | 0.5 | 0.7 | 0.85 | 0.6 | 0.6 | 0.9 | Scary on paper, gentle in execution |

**Total: 43 personas.** Easy to grow later without code changes — just add to JSON. Future expansions to consider: Bahubali, Krishna (mythological trickster god), Mighty Raju, more 90s Cartoon Network roster (Powerpuff Girls, Courage), more Indian comics (Nagraj, Super Commando Dhruva), more Pokémon (Machamp, Ditto, Lucario, Gardevoir).

## Player fingerprint

Each `RoundLog` is converted into a contribution vector on the same 6 dimensions. Across multiple rounds we keep a rolling weighted average (recent rounds count more — exponential decay with α=0.6).

Per-round projection rules (initial, easy to tweak):

```python
def project_round(round_log) -> dict[str, float]:
    bid, tricks, cards = round_log.bid, round_log.tricks_won, round_log.num_cards

    risk         = clamp01(bid / max(cards, 1))                    # high bid = high risk
    planning     = 1.0 if bid == tricks else 0.5 - abs(bid-tricks)/cards
    patience     = trump_release_lateness(round_log)               # 0..1
    aggression   = leads_high_count(round_log) / max(tricks, 1)
    adaptability = 1.0 - abs(player_bid - table_avg_bid) / cards   # bidding with the table
    consistency  = 1.0 - rolling_bid_error_variance(history)

    return {risk, planning, patience, aggression, adaptability, consistency}
```

Helpers (`trump_release_lateness`, `leads_high_count`) live in the same module and are tested independently.

## Persona matching

```python
def best_personas(player_vec, history_window) -> list[str]:
    scores = []
    for persona in PERSONAS:
        sim = cosine(player_vec, persona.traits)
        novelty = novelty_factor(persona.id, history_window)   # 1.5/1.0/0.6
        scores.append((persona.id, sim * novelty))
    scores.sort(key=lambda x: -x[1])
    return scores[:3]                                           # top 3

def pick_persona(player_vec, history_window, rng) -> str:
    top3 = best_personas(player_vec, history_window)
    return weighted_choice(top3, rng)                           # weighted by score
```

Same novelty + sample-don't-max strategy from the original plan: ensures the same player profile across 10 rounds rotates through ≥6 distinct personas.

End-of-game persona uses the **whole-game** fingerprint and a **fresh** novelty buffer (so the final card isn't constrained by per-round picks). This typically lands on a more "settled" persona that summarises the game.

## Per-round commentary structure

A round-end mascot line is composed of two parts:

```
{axis_observation}{separator}{persona_flavour}
```

Examples:

| Axis hit | Persona picked | Final line |
|----------|----------------|------------|
| `held_trump_late` | Fox | "Sat on the trump Ace till trick 7. Foxlike." |
| `bid_zero_made` | Turtle | "Bid zero, took zero. Pure Turtle." |
| `bid_aggressive_made` | Thor | "Bid 6 on a 7-card hand and made it. Thor moment." |
| `void_created` | Black Widow | "Voided clubs by trick 3. Classic Widow setup." |
| `comeback_round` | Spider-Man | "Best round on the table. Spider-Man pivot." |

When the persona has a **specialised line** for that axis (in `lines[axis_id]`), use that directly:

> Persona: Owl, axis: `held_trump_late`
> Persona's specialised line: "Owls watch. You watched the trump Ace until trick 7."

Falls back to `lines.general` + axis observation when no specialised line exists.

## Persona JSON schema

```json
{
  "id": "fox",
  "category": "animal",
  "name": "The Fox",
  "tagline": "Cunning, opportunistic, sets traps",
  "traits": {
    "risk": 0.6, "planning": 0.7, "patience": 0.7,
    "aggression": 0.5, "adaptability": 0.9, "consistency": 0.6
  },
  "lines": {
    "general": [
      "Foxlike.",
      "That's a Fox move.",
      "Cunning."
    ],
    "void_created": [
      "Foxlike — voided {suit} to spring a ruff.",
      "Set the trap by trick {trick}. Pure Fox."
    ],
    "bid_zero_made": [
      "Invisible all round. Foxlike."
    ]
  },
  "art": "fox.svg"
}
```

The `lines` map is sparse — most personas only specialise on the 2–3 axes that fit them best. The fallback chain is: `lines[axis_id]` → `lines.general` → "" (omit persona suffix).

## Compact encoding

Per the user's request — keep a **compact encoded version in resources** so the shipped bundle stays small and load is instant. Two-file design:

| File | Purpose | Shape |
|------|---------|-------|
| `backend/app/analysis/personas.source.json` | Human-edited source of truth | Pretty-printed, commented via `_note` fields, full phrasing pools |
| `backend/app/analysis/personas.pack.json` | Shipped artefact; what `persona_loader.py` actually reads at runtime | Minified, traits quantised to `int 0–100`, shared-string table for repeated phrasings |

Runtime loader always reads `personas.pack.json`. The `.source.json` never ships to end users (add to PyInstaller exclude list + `.gitignore` untouched — source is checked in, pack is regenerated by CI).

### Packed schema

```jsonc
{
  "v": 1,                         // bump when the schema changes
  "dims": ["risk","planning","patience","aggression","adaptability","consistency"],
  "phrases": [                    // deduped string pool
    "Foxlike.", "That's a Fox move.", "Cunning.",
    "Owls watch.", "...", "..."
  ],
  "personas": [
    {
      "id": "fox",
      "c": "animal",              // category short code
      "n": "The Fox",
      "t": "Cunning, opportunistic",
      "v": [60,70,70,50,90,60],   // traits × 100, int
      "l": {"g": [0,1,2], "void_created": [27,28]},  // line pools → indexes into phrases[]
      "a": "fox.svg"
    }
  ]
}
```

Quantising traits to `int 0–100` costs < 0.005 cosine error (empirically verified in tests) and halves the file size vs floats. Deduping phrases saves another ~20–30% because "Foxlike." / "Owl energy." / axis-specific words recur across personas.

### Build step

`scripts/pack_personas.py` reads the source JSON, validates the schema, dedupes phrases, quantises traits, and writes the pack. Invoked:

1. **Manually** during development whenever the source changes: `python3 scripts/pack_personas.py`
2. **Automatically** by `scripts/package.sh` before PyInstaller bundles the app, so the pack is always current in releases
3. **In CI** as a step in `.github/workflows/release.yml` — fails the build if the checked-in pack is out of sync with the source (`git diff --exit-code` on the pack)

### Expected size

Rough estimate for 43 personas with ~5 general + ~6 axis-specific lines each:

| Format | Approx size |
|--------|-------------|
| `personas.source.json` (pretty) | ~55 KB |
| `personas.pack.json` (minified, quantised, deduped) | **~18 KB** |
| `personas.pack.msgpack` (if we ever need further shrink) | ~12 KB |

18 KB is well under any reasonable budget — for comparison the app icon alone is ~80 KB. But the packed format also makes the loader trivially fast (single `json.load` + list-index lookups, no validation at runtime) and makes the shipped resources readable by a security auditor without Python deps.

## Components

```
backend/app/analysis/
├── __init__.py
├── personas.source.json   # Editable source of truth (43 personas, dev only)
├── personas.pack.json     # Shipped artefact: quantised ints + deduped phrase pool
├── persona_loader.py      # Reads .pack.json, exposed via @lru_cache
├── fingerprint.py         # project_round(), update_fingerprint()
├── persona_match.py       # cosine sim, novelty, weighted pick
├── axes.py                # The axis catalog from the original plan
├── evaluator.py           # Run all axes vs RoundLog → list[Observation]
├── commentary.py          # Compose final string from (axis, persona)
└── observer.py            # MascotObserver hooked into ManagedGame

scripts/
└── pack_personas.py       # Builds personas.pack.json from personas.source.json
```

(Same layering rules as `ai/` — pure logic, depends only on `models/`.)

## Events + plumbing

Two new event types in `backend/app/models/events.py`:

- `MASCOT_MESSAGE` — emitted after each `ROUND_COMPLETE`, targeted at one player.
  ```
  data: { text, axis_id, persona_id, round_number }
  ```
- `MASCOT_PERSONA_AWARDED` — emitted after `GAME_OVER`, targeted at one player.
  ```
  data: { persona_id, persona_name, persona_tagline, traits, top_axes_hit }
  ```

Frontend `types/events.ts` adds matching `ServerEventType` entries and typed data interfaces. WebSocket targeting (already in place — `event.player_id` filter) handles delivery.

## Frontend

```
frontend/src/components/mascot/
├── Mascot.tsx              # Corner character + speech bubble
├── PersonaCard.tsx         # End-of-game persona reveal
├── mascot.module.css
└── personas/               # SVGs — one per category to start, expand later
    ├── fox.svg                      # animal
    ├── batman_silhouette.svg        # Marvel
    ├── tag.svg                      # poker archetype
    ├── chhota_bheem.svg             # cartoon/Indian
    ├── pikachu_silhouette.svg       # Pokémon
    └── _default.svg                 # placeholder for un-art'd personas
```

Behaviour:

- `<Mascot>` lives in a fixed corner of `GameBoard`. Default art is the placeholder J card; persona art swaps in only when present in `personas/`.
- On `MASCOT_MESSAGE`, fade in the bubble with the line, hold ~5s, fade out.
- Queue messages — never overlap.
- On `MASCOT_PERSONA_AWARDED`, render `<PersonaCard>` on the FinalResults screen below the rankings, with persona name, tagline, the 6-trait bar chart of the player's vector vs the persona's, and the line pool sample.

Settings toggle in `SettingsModal.tsx`: **"Show mascot commentary"** (default on). Stored in localStorage.

## Innovation guarantees

The user's "every time it should try to give different strengths" requirement is met by **three independent variability sources**:

1. **Axis variety** — 12 axes, ring-buffered to avoid recent repeats (from original plan).
2. **Persona variety** — 43 personas spanning 5 categories (Marvel heroes, animal totems, poker archetypes, cartoon/Indian icons, iconic Pokémon), novelty-weighted, sampled from top-3.
3. **Phrasing variety** — 3–5 phrasings per (persona × axis) combination + 3–5 generic per persona.

Combinatorial output ceiling: 12 axes × ~3 candidate personas/round × ~3 phrasings ≈ **100+ unique lines** before the player ever hears a repeat. Across an entire 20-round game, even an extremely consistent player will hear ≥12 distinct personas referenced. The 5-category mix (heroes / animals / poker / cartoons / Pokémon) makes the *texture* of the references vary too — one round you're Foxlike, the next you're Dexter, then Tight-Aggressive, then Chhota Bheem, then Mewtwo-cold.

The persona corpus is **data, not code**. Adding new superheroes/animals/archetypes is a JSON edit + an SVG. No code change.

## Prerequisite: CI pipeline

Before starting any of the 4 PRs below, we land `.github/workflows/test.yml` so every PR below gets a green-tick gate. See [`plans/ci_pipeline.md`](ci_pipeline.md) — it's a single small PR.

## Detailed file-by-file code changes (per PR)

This section is the contract for each PR: every file touched, every test added, and the regression tests that must pass at the end of the PR. The 4-PR split lets us ship the bottom of the stack (pure logic, zero user-visible change) and prove CI before any UI work.

### PR 1 — Fingerprint + persona corpus + matcher

Pure additive, no wire-level changes, no engine integration. Everything is unit-testable from fixtures.

**New files:**

| Path | Purpose |
|------|---------|
| `backend/app/analysis/__init__.py` | Package marker (empty) |
| `backend/app/analysis/personas.source.json` | The 43-persona corpus, pretty-printed, full lines pools |
| `backend/app/analysis/personas.pack.json` | Generated compact form (committed — CI drift-checks it) |
| `backend/app/analysis/persona_loader.py` | `@lru_cache`'d `load_personas() → tuple[Persona, ...]`. Loads `personas.pack.json`, hydrates Pydantic models, asserts schema `v: 1` |
| `backend/app/analysis/fingerprint.py` | `project_round(round_log) → dict[str,float]`, `RollingFingerprint(alpha=0.6).update(vec)` |
| `backend/app/analysis/persona_match.py` | `cosine(a,b)`, `novelty_factor(id, buf)`, `best_personas(vec, buf) → list[tuple[str,float]]`, `pick_persona(vec, buf, rng) → str` |
| `scripts/pack_personas.py` | CLI: reads source, dedupes phrases, quantises traits, emits pack |
| `backend/tests/test_fingerprint.py` | ~8 tests (see below) |
| `backend/tests/test_persona_loader.py` | ~5 tests |
| `backend/tests/test_persona_match.py` | ~8 tests |
| `backend/tests/test_pack_personas.py` | ~3 tests |

**Modified files:** none. (This is why PR 1 is safe — zero risk of regressing existing gameplay.)

**Unit tests in detail:**

- `test_fingerprint.py`
  - `test_high_bid_round_scores_high_risk` — bid 6 on 7 cards → risk > 0.8
  - `test_exact_hit_scores_high_planning` — bid == tricks → planning ≥ 0.9
  - `test_late_trump_release_scores_high_patience` — trump Ace played trick 6 of 7 → patience > 0.8
  - `test_bidding_with_table_scores_high_adaptability` — player bid within 1 of table average → adaptability > 0.8
  - `test_rolling_fingerprint_decays_old_rounds` — feed 5 rounds; round-5 influence > round-1 by factor ~α^4
  - `test_single_round_has_neutral_consistency` — first round → consistency = 0.5
  - `test_all_fingerprint_values_are_in_unit_range` — fuzz 200 random rounds; every dim ∈ [0, 1]
  - `test_missed_bid_by_large_margin_scores_low_planning` — bid 0, took 5 → planning < 0.2

- `test_persona_loader.py`
  - `test_pack_loads_without_errors`
  - `test_exactly_43_personas_present`
  - `test_every_persona_has_6_trait_values_in_unit_range`
  - `test_every_persona_has_non_empty_general_lines`
  - `test_schema_version_is_1` (guards against silent schema drift)

- `test_persona_match.py`
  - `test_cosine_of_identical_vectors_is_1`
  - `test_cosine_of_orthogonal_vectors_is_0`
  - `test_batman_fingerprint_puts_batman_in_top_3` — craft a vector near Batman's trait row, assert `"batman"` appears in `best_personas()[:3]`
  - `test_turtle_fingerprint_matches_turtle_or_nit` — low-risk low-aggression vector → top-3 contains Turtle or Nit (both cluster there)
  - `test_novelty_factor_penalises_recent_personas` — buffer = {"fox"} → `novelty_factor("fox", buf) < novelty_factor("owl", buf)`
  - `test_pick_persona_is_deterministic_with_seeded_rng` — same seed, same vec, same result
  - `test_ten_identical_calls_yield_at_least_6_distinct_personas` — the user's "different strengths every time" guarantee, enforced as a test
  - `test_pick_persona_never_returns_unknown_id` — fuzz over 1000 random vectors; every result is in the loaded corpus

- `test_pack_personas.py`
  - `test_source_to_pack_round_trip_preserves_cosine_within_0_005` — build pack from source in-memory, load both, compare cosine of every persona pair; max diff < 0.005
  - `test_pack_dedupes_repeated_phrases` — source has "Cunning." twice; pack's `phrases[]` contains it once
  - `test_pack_is_under_30kb` — hard ceiling (current target ~18 KB)

**Regression tests (must still pass):**

All 210+ existing tests run unchanged — PR 1 adds files, never modifies. CI enforces this; no manual check required.

**Acceptance criteria for PR 1:**
- All 24 new tests green
- All existing tests green
- `personas.pack.json` is checked in and `python3 scripts/pack_personas.py && git diff --exit-code` is clean

---

### PR 2 — Axes + evaluator + commentary composition

Adds the round-observation layer + the commentary composer. Still no engine integration yet — everything is fixture-driven.

**New files:**

| Path | Purpose |
|------|---------|
| `backend/app/analysis/axes.py` | 12 axis functions, each `(round_log, engine_snapshot) → Optional[Observation]` |
| `backend/app/analysis/evaluator.py` | `Evaluator(ring_size=3).evaluate(round_log, snapshot) → list[Observation]`, sorted by strength, filtered by ring buffer |
| `backend/app/analysis/commentary.py` | `compose(observation, persona, rng) → MascotLine` |
| `backend/tests/test_axes.py` | ~12 tests, one per axis |
| `backend/tests/test_evaluator.py` | ~4 tests |
| `backend/tests/test_commentary.py` | ~6 tests |

**Modified files:**

| Path | Change |
|------|--------|
| `backend/app/models/events.py` | Add `MASCOT_MESSAGE` and `MASCOT_PERSONA_AWARDED` to `EventType`; add `mascot_message_event()` and `mascot_persona_awarded_event()` factories with typed data models |

**Unit tests in detail:**

- `test_axes.py` — one test per axis, plus negative cases:
  - `test_held_trump_late` — trump Ace played trick 7/7 → axis fires with strength proportional to delay
  - `test_bid_zero_made` — bid 0, won 0 → fires
  - `test_bid_aggressive_made` — bid ≥ ⌈cards/2⌉ and made → fires
  - `test_void_created` — player didn't play suit S after trick 2 → fires for suit S
  - `test_comeback_round` — player's round score is highest at the table → fires
  - `test_perfect_bid_streak` — 3 exact-bid rounds in a row → fires on the 3rd
  - `test_risky_bluff_bid_made` — bid > ⌈cards/2⌉ on hand with no trump/Aces, and made → fires
  - `test_calling_station_played_every_trick_won_few` — played in N/N tricks, won ≤1 → fires
  - `test_grinder_round` — exactly hit a small bid (1–2) with no drama → fires
  - `test_ruff_at_first_opportunity` — trumped the first suit you were void in → fires
  - `test_high_card_in_lost_trick` — played King or Ace in a trick you lost → fires
  - `test_no_axes_fire_on_blank_round` — empty round log returns `[]`

- `test_evaluator.py`
  - `test_evaluator_returns_all_firing_axes`
  - `test_evaluator_ring_buffer_suppresses_recent_axis` — same axis fires 4 rounds in a row; ring buffer of 3 means round 4 returns without it
  - `test_evaluator_sorts_observations_by_strength_desc`
  - `test_evaluator_empty_round_returns_empty_list`

- `test_commentary.py`
  - `test_specialised_line_used_when_persona_has_one_for_axis`
  - `test_general_fallback_used_when_no_specialised_line`
  - `test_no_persona_suffix_when_persona_has_no_general_lines_either` (defensive, shouldn't happen in real data)
  - `test_observation_metadata_preserved_in_output` — `axis_id` + `persona_id` round-trip into the emitted line's metadata fields
  - `test_deterministic_with_seeded_rng`
  - `test_phrasing_variety_over_50_runs` — 50 calls with identical inputs & changing seeds → ≥3 distinct phrasings

**Regression tests (must still pass):**

- All PR 1 tests (24) green.
- All pre-existing 210+ tests green.
- **`backend/app/models/events.py` stability check**: existing event types must retain their string values — add `test_event_type_string_values_are_stable` that freezes the current 20 EventType string values, guards against an accidental renumbering when new enum members are inserted.
- **Event factory contract check**: existing factories (`round_started_event`, `card_played_event`, etc.) produce identical output for identical inputs as before the PR. Add a fingerprint test that hashes a known event's JSON.

**Acceptance criteria for PR 2:**
- 22 new tests green
- Stability test on event string values green
- Existing event factory fingerprints unchanged

---

### PR 3 — Observer integration + WebSocket plumbing

This is the riskiest PR because it hooks into the live engine event stream. Regression discipline is critical here.

**New files:**

| Path | Purpose |
|------|---------|
| `backend/app/analysis/observer.py` | `MascotObserver(player_id, rng_seed)` — holds a `RollingFingerprint`, a `PersonaHistoryBuffer`, an `Evaluator`. Method `on_round_complete(round_log, snapshot) → Optional[GameEvent]`. Method `on_game_over(session_log) → GameEvent` |
| `backend/tests/test_mascot_observer.py` | ~6 tests |
| `backend/tests/test_mascot_websocket.py` | ~4 tests |
| `backend/tests/test_mascot_regression.py` | ~5 tests — **dedicated regression suite** for this PR |

**Modified files:**

| Path | Change |
|------|--------|
| `backend/app/game_manager.py` | `ManagedGame.__init__` accepts `enable_mascot: bool = True`. If enabled, build a `MascotObserver` per human player. Subscribe to `ROUND_COMPLETE` and `GAME_OVER` events; forward observer output via the same engine `_emit` path. Observer errors are caught + logged, **never propagate into engine state**. |
| `backend/app/api/websocket.py` | Add routing rule: events with `target_player_id` set are delivered only to that WS client. Existing broadcast behaviour unchanged for untargeted events. |
| `backend/app/models/events.py` | `GameEvent` gets an optional `target_player_id: Optional[str]`. Existing events continue to set it `None` → broadcast behaviour preserved. |

**Unit tests in detail:**

- `test_mascot_observer.py`
  - `test_observer_emits_mascot_message_on_round_complete`
  - `test_observer_emits_persona_awarded_on_game_over`
  - `test_observer_skipped_for_ai_only_games` — no human → no events at all
  - `test_observer_receives_full_round_log_not_just_state` — can reconstruct axis signals
  - `test_observer_disabled_flag_emits_nothing`
  - `test_observer_exception_is_logged_and_does_not_raise` — inject a faulty axis; observer returns `None`, engine continues

- `test_mascot_websocket.py`
  - `test_mascot_message_reaches_target_player_only`
  - `test_mascot_message_not_broadcast_to_opponents`
  - `test_persona_awarded_reaches_target_player_only`
  - `test_targeted_event_coexists_with_broadcast_events` — both flow correctly in same round

**Dedicated regression suite (`test_mascot_regression.py`):**

These catch the "observer broke the engine" class of bug, which is the main risk of PR 3.

- `test_existing_engine_tests_all_pass_with_observer_enabled` — parametrise a handful of `test_engine.py` scenarios to also run with `enable_mascot=True`. State transitions + scores identical.
- `test_no_extra_events_visible_to_ai_strategy_layer` — `RoundContext` built after a round with observer enabled does NOT include mascot events in `cards_played` or anywhere else. Information isolation holds.
- `test_event_ordering_is_preserved` — run a seeded 3-round game with and without the observer; assert the non-mascot event sequence is byte-identical.
- `test_golden_game_replay` — a fixed-seed 5-round game produces the same final scoreboard with mascot on vs off.
- `test_round_end_overhead_under_10ms` — micro-benchmark `on_round_complete` 100× on a representative round; fail if median exceeds 10ms on the CI runner. Guards against O(N²) creeping in as the corpus grows.

**Regression tests from prior PRs (must still pass):**
- All 24 PR 1 tests
- All 22 PR 2 tests
- The 210+ pre-existing tests

**Acceptance criteria for PR 3:**
- 15 new tests green (6 observer + 4 WS + 5 regression)
- Full existing suite green
- Golden-replay test proves the feature is invisible when disabled

---

### PR 4 — Frontend Mascot + PersonaCard + settings toggle + starter art

Only user-visible PR. Backend contract is frozen by end of PR 3, so this PR can't regress gameplay.

**New files:**

| Path | Purpose |
|------|---------|
| `frontend/src/components/mascot/Mascot.tsx` | Fixed-corner character with speech-bubble queue |
| `frontend/src/components/mascot/PersonaCard.tsx` | End-of-game persona reveal |
| `frontend/src/components/mascot/mascot.module.css` | Styling |
| `frontend/src/components/mascot/personas/fox.svg` | Animal starter |
| `frontend/src/components/mascot/personas/batman_silhouette.svg` | Marvel starter |
| `frontend/src/components/mascot/personas/tag.svg` | Poker starter |
| `frontend/src/components/mascot/personas/chhota_bheem.svg` | Cartoon/Indian starter |
| `frontend/src/components/mascot/personas/pikachu_silhouette.svg` | Pokémon starter |
| `frontend/src/components/mascot/personas/_default.svg` | Fallback for un-art'd personas |
| `frontend/src/hooks/useMascot.ts` | Queue management (dequeue after bubble fade-out) |

**Modified files:**

| Path | Change |
|------|--------|
| `frontend/src/types/events.ts` | Add `MASCOT_MESSAGE` + `MASCOT_PERSONA_AWARDED` to `ServerEventType`; add `MascotMessageEventData` + `MascotPersonaAwardedEventData` interfaces |
| `frontend/src/types/game.ts` | Add `mascotQueue: MascotMessage[]` and `awardedPersona: PersonaAward \| null` to `GameState` + `INITIAL_GAME_STATE` |
| `frontend/src/hooks/useGame.ts` | Two new handlers + `DEQUEUE_MASCOT` action (consumes the head of `mascotQueue` after bubble fade) |
| `frontend/src/components/game/GameBoard.tsx` | Render `<Mascot>` in a fixed corner |
| `frontend/src/components/scoreboard/FinalResults.tsx` | Render `<PersonaCard>` below rankings when `awardedPersona` is set |
| `frontend/src/components/settings/SettingsModal.tsx` | "Show mascot commentary" toggle (default on, localStorage key `mascot.enabled`) |

**Tests:**

Frontend currently has no test runner installed (package.json has `lint`, `build`, no `test`). Two options:

- **Option A (chosen default):** Rely on TypeScript + lint in CI + manual QA for this PR. Keep the PR small. Defer Vitest to a later PR if we hit a regression this doesn't catch.
- **Option B:** Add Vitest + @testing-library/react in this PR. Adds ~60 lines to `package.json`, one config file, and ~20 lines to `test.yml`. Enables:
  - `Mascot.test.tsx` — bubble shows on event, hides after 5s, queues overlapping events
  - `PersonaCard.test.tsx` — renders persona name + tagline + trait bars from props
  - `useMascot.test.ts` — queue dequeue order
  - `useGame.test.ts` — new event handlers update state correctly

Recommendation: ship Option A in PR 4, open a follow-up PR for Vitest. Keeps the user-visible milestone small.

**Regression tests (must still pass):**

- All 15 PR 3 tests
- All 22 PR 2 tests
- All 24 PR 1 tests
- All 210+ pre-existing tests
- `cd frontend && npm run build` succeeds (tsc + vite build, enforced in CI)
- `cd frontend && npm run lint` succeeds
- Manual: run `./play`, disable mascot in settings, play one round — UI is pixel-identical to pre-PR aside from the settings toggle row

**Acceptance criteria for PR 4:**
- Backend suite fully green
- Frontend typecheck + lint green
- Demo video or screenshot confirming the corner mascot + end-of-game persona card work end-to-end with all 5 starter SVGs loading
- Settings toggle genuinely hides the mascot and suppresses future events (stored in localStorage, sent as a flag in the WS join message so backend can skip emitting — belt-and-braces)

## Master regression checklist (run at end of each PR)

```
python3 -m pytest backend/tests/ -v       # must be green (210+ pre-existing + new per-PR)
cd frontend && npm run build              # typecheck + build passes
cd frontend && npm run lint               # no new lint errors
python3 scripts/security_scan.py          # no new advisories (sanity, not gating)
```

CI enforces 1–3 automatically. Item 4 is an optional pre-merge check until we wire it into CI separately.

## Order of work summary

1. **CI first** — `plans/ci_pipeline.md`. Single small PR landing `.github/workflows/test.yml`. Prerequisite for all 4 mascot PRs.
2. **PR 1** — Fingerprint + persona corpus + matcher (pure logic, zero visible change).
3. **PR 2** — Axes + evaluator + commentary (pure logic + event type additions).
4. **PR 3** — Observer integration + WebSocket plumbing (the only PR that touches live engine).
5. **PR 4** — Frontend Mascot + PersonaCard + settings toggle + starter art (user-visible).

Each PR is independently shippable and reviewable. PR 4 is the only one that produces visible UI. Detailed file-by-file contracts are in the "Detailed file-by-file code changes" section above.

## Decisions still open (flag for review)

- **Persona art style.** Hand-drawn cartoon, flat geometric, line-art icons, or pixel-art? Default suggestion: flat geometric in the same gold/violet palette as the app icon, so they fit the rangoli table.
- **Persona category mix.** Should the matcher prefer animal personas (broader appeal), superhero personas (more recognisable), or weight equally? Default: equal weight via cosine similarity alone.
- **Tone of persona references.** Reverent ("Pure Batman."), playful ("Foxy."), academic ("Tight-Aggressive profile detected."). Default: terse-playful, short sentences with a period.
- **Should we expose the trait vector to the player?** End-of-game persona card could include the bar chart, or hide it. Default: show — players love seeing their stats.
- **Bilingual?** Indian audience may prefer Hindi/Hinglish phrasings ("Sher ji — bid hit on a 7-card hand."). Out of scope for v1; wire up via a `locale` field in JSON later.
- **Naughty mode?** Optional toggle where the mascot also calls out *bad* play ("Threw the King under a losing trick. Calling Station."). Default: encouraging only; toggle off-by-default if added.
- **Mid-game persona drift card.** Show a small toast when the matched persona changes ("You started Batman, now you're Loose-Aggressive — what changed?"). Tempting but probably noise; flag for v2.

## Out of scope (v1)

- LLM-generated commentary
- Multi-language support
- Mascot reacting mid-trick (only at round/game boundaries)
- Player-selectable mascot character
- Persona unlock progression / collection mechanics
- Audio
- Persisting persona awards across games (no DB yet)

## Future / roadmap (v2+)

These are deliberately deferred but the v1 design leaves room for them:

- **LLM-authored persona lines.** Replace the static `lines[*]` phrase pools with on-the-fly generation from a small local LLM (e.g. a quantised Llama running via `llama.cpp` embedded in the desktop bundle, or an optional hosted call behind a user-provided API key). The trait-vector matcher stays; only the phrase-generation step changes. This lets the mascot reference *specific* cards/tricks ("That King of spades you dumped at trick 4…") without us hand-authoring every template.
- **LLM-generated new personas.** On-demand persona expansion: "Invent a persona that matches this trait vector." Output is validated against the same JSON schema and appended to a user-local persona corpus, so power users can grow the library themselves.
- **DB-backed persona history & achievements.** Once persistence lands (see the `SessionLog` "Add persistence" task), store each game's awarded persona per player. Enables:
  - A "collection" screen — "You've been matched with 12 of 43 personas"
  - Stats — "Your most common persona is The Fox (40%)"
  - Rivalries — in future multiplayer, compare persona profiles across friends
- **Vector-DB-backed corpus.** Migrate `personas.pack.json` into a proper embedding store (e.g. SQLite + `sqlite-vec`) if the corpus grows past a few hundred personas. At that scale, cosine-over-array becomes measurable; vector indexes make it O(log N).
- **Player-trained persona drift.** Learn per-player baseline trait vectors and match against *deltas* from their own baseline rather than absolute values. Surfaces "You played more aggressive than usual today" style observations.
- **Community persona packs.** Signed community-contributed persona packs installable from Settings (anime packs, sports-legend packs, regional-folklore packs). Requires signature verification and a moderation story.

## Sources used while designing the persona corpus

- Poker player typology (TAG, LAG, Nit, Calling Station, Maniac): [888poker — Top 9 Poker Player Personalities](https://www.888poker.com/magazine/top-9-poker-player-personalities), [Pokerology — 6 Poker Playing Styles](https://www.pokerology.com/lessons/poker-playing-styles/)
- Superhero MBTI archetypes (Batman INTJ, Iron Man ENTP, Black Widow ISTP, Wonder Woman ENFJ, Captain America ISFJ): [So Syncd — 16 Personality Types as Superheroes](https://www.sosyncd.com/16-personality-types-superheroes/), [BrainManager — Avengers Personality Types](https://brainmanager.io/blog/trending/avengers-personality-types), [Medium — MCU character archetypes](https://victormb.medium.com/marvels-the-avengers-2012-character-archetypes-in-the-movie-ed1d271b937d)
- Animal totem traits (Fox cunning, Owl wise, Wolf loyal, Elephant memory, Turtle patient, Eagle vision, Hawk focus, Lion brave, Dolphin playful, Raven trickster, Ant disciplined, Bee organised): [SpiritAnimal.info — Ultimate Guide](https://www.spiritanimal.info/), [Spiritual Wayfarer — Animal Totem List](https://spiritualwayfarer.com/complete-animal-totem-list/), [CenterSpirited — Animal Symbolism](https://centerspirited.com/animal-symbolism/symbology-and-meanings/)
- Indian superheroes & cartoon characters (Chhota Bheem, Krrish, Shaktimaan, Mighty Raju): [Wikipedia — Chhota Bheem](https://en.wikipedia.org/wiki/Chhota_Bheem), [Wikipedia — Shaktimaan](https://en.wikipedia.org/wiki/Shaktimaan), [Wikipedia — Krrish](https://en.wikipedia.org/wiki/Krrish)
- Western cartoon character archetypes (Dexter's Lab, Bugs Bunny, Tom & Jerry, Scooby Doo, Johnny Bravo): [CBR — Cartoon Network character psychology](https://www.cbr.com/), [Wikipedia — Looney Tunes](https://en.wikipedia.org/wiki/Looney_Tunes)
- Pokémon personality traits (Pikachu ENFP, Charizard ENTJ, Mewtwo INTJ, Gengar mischief, Snorlax immovable, Eevee adaptable, Psyduck chaotic, Jigglypuff attention-seeking, Alakazam intelligent, Dragonite gentle-powerhouse): [So Syncd — 16 Personality Types as Pokémon](https://www.sosyncd.com/16-personality-types-pokemon/), [Boo.world — Pokémon Personality Types](https://boo.world/database/anime/pokemon-personality-types), [CBR — Pokémon With The Biggest Personalities](https://www.cbr.com/most-fun-loving-pokemon/), [Bulbapedia — Snorlax](https://bulbapedia.bulbagarden.net/wiki/Snorlax_(Pok%C3%A9mon)), [Pokémon.com — Gengar Pokédex](https://www.pokemon.com/us/pokedex/gengar)
