# ML Learning Engine for Hard AI

## Goal

One of the Hard AI bots learns from how game winners play. Pure Python stdlib — no scikit-learn, no DB. Data stored in JSON-lines files.

## Core Idea

After every game, we record every decision (bid + card play) made by the **winning player** along with the game situation at that moment. Over time, this builds a dataset of "what winners do in situation X." The ML bot uses this data to mimic winning patterns.

## Algorithm: Weighted k-Nearest Neighbors (kNN)

**Why kNN:**
- Zero dependencies (just `math`, `json`, `pickle`)
- ~80 lines of core logic
- Naturally improves as more data accumulates
- No training step — it learns instantly as new games finish
- Interpretable: "I'm playing this card because winners in similar spots did the same"

**How it works:**
1. Each decision is stored as a **feature vector** (numbers describing the situation) + **action taken** (bid amount or card played)
2. When the ML bot needs to decide, it computes distance between current situation and all stored winner decisions
3. Picks the action that the closest K similar situations chose (majority vote, weighted by distance)

## What Data to Collect

### Bid decisions (one row per bid by the winner)

```
Features (all numeric):
- num_cards              (1-10)
- num_players            (2-6)
- position_in_bid_order  (0-based)
- trump_count            (int)
- high_trump_count       (J+ in trump)
- ace_count              (int)
- king_count             (int)
- void_count             (suits with 0 cards)
- singleton_count        (suits with 1 card)
- longest_suit_length    (int)
- total_bids_so_far      (sum of earlier bids)
- is_dealer              (0 or 1)

Label:
- bid_amount             (int)
```

### Play decisions (one row per card played by the winner)

```
Features (all numeric):
- tricks_needed          (bid - tricks_won_so_far)
- tricks_won_so_far      (int)
- cards_remaining        (int, cards left in hand)
- position_in_trick      (0=lead, 1, 2, ...)
- is_leading             (0 or 1)
- num_trumps_in_hand     (int)
- num_lead_suit_in_hand  (int, 0 if leading)
- can_win_trick          (0 or 1)
- current_trick_max_rank (int, 0 if leading)
- trump_cards_seen       (int, trumps played so far in round)
- cards_seen_count       (total cards played in round so far)

Label:
- card_index             (index of chosen card among valid cards, sorted by suit+rank)
  → We store relative choice, not absolute card, so patterns generalize
```

### Storage

```
backend/app/ai/ml/
├── data/
│   ├── bid_decisions.jsonl       # One JSON object per line
│   └── play_decisions.jsonl      # One JSON object per line
├── collector.py                  # Records winner decisions after each game
├── features.py                   # Extract feature vectors from RoundContext
└── knn.py                        # kNN prediction logic
```

Files are JSON-lines (`.jsonl`) — append-only, human-readable, no corruption risk on crash.

## Integration

### Where it plugs in

```
ai/
├── hard.py          # Current rule-based Hard AI (unchanged, used as fallback)
├── hard_ml.py       # NEW — wraps kNN, falls back to hard.py when data is sparse
```

`hard_ml.py` implements `AIStrategy`:
- `choose_bid()`: Extract features → kNN lookup on bid data → if enough neighbors (K=5), use kNN result; else fall back to rule-based `HardAI.choose_bid()`
- `choose_card()`: Extract features → kNN lookup on play data → if enough neighbors, use kNN result; else fall back to rule-based `HardAI.choose_card()`

### Which bot uses it

Only **one** AI bot per game uses the ML strategy, chosen at random. In `game_manager._make_strategy()`:
- Randomly pick one Hard AI bot → `HardMLAI` (learning engine)
- All other Hard AI bots → regular `HardAI` (rule-based)

### When data is collected

In `game_manager.py`, on `GAME_OVER` event:
1. Identify the winner
2. Replay the winner's decisions from the round history (already tracked in engine state)
3. For each decision, extract features and append to the `.jsonl` file

### Cold start

On first install, data files are empty → ML bot falls back to rule-based Hard AI for every decision. As games are played, data accumulates and the ML bot gradually takes over decisions where it has enough similar examples.

Optional: ship a pre-seeded data file from ~200 simulated Hard-vs-Hard games so it works from day one.

## Performance

- **Data file size:** ~500 bytes per game (winner makes ~20-40 decisions). After 1000 games: ~500KB.
- **Lookup speed:** Linear scan of all stored decisions. At 1000 games (~30K rows), kNN with distance calc takes <50ms — well within card game response time.
- **If data grows too large (>100K rows):** Downsample oldest entries or keep only most recent N entries.

## Steps

1. `features.py` — feature extraction from RoundContext
2. `knn.py` — kNN classifier (predict bid, predict card)
3. `collector.py` — record winner decisions to .jsonl after game ends
4. `hard_ml.py` — MLHardAI strategy with fallback
5. Wire into game_manager (collector on game_over + ML strategy for one bot)
6. Cold-start: script to simulate games and pre-seed data
7. Tests
