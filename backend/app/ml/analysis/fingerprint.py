"""Compute a player's trait vector from their game history."""
from __future__ import annotations

import logging
from typing import Dict, List

from backend.app.models.session import RoundLog, SessionLog
from backend.app.ml.constants import DIMENSIONS
from backend.app.ml.utils import clamp01

logger = logging.getLogger(__name__)

# Dimensions computed per-round and then aggregated via exponential decay
_PER_ROUND_DIMS = (
    "risk", "planning", "patience", "aggression", "adaptability", "consistency",
    "boldness", "precision",
)


def project_round(round_log: RoundLog, player_id: str, all_bids_map: Dict[str, int]) -> Dict[str, float]:
    """Project a single round into a trait vector for a player.

    Returns the per-round dimensions (8 dims). Session-level dims
    (resilience, clutch, trajectory) are computed in compute_fingerprint.
    """
    player_bid = all_bids_map.get(player_id, 0)
    player_tricks = round_log.tricks_won.get(player_id, 0)
    num_cards = max(round_log.num_cards, 1)

    # Risk: how aggressively did they bid relative to hand size
    risk = clamp01(player_bid / num_cards)

    # Planning: did they hit their bid exactly?
    bid_error = abs(player_bid - player_tricks)
    planning = clamp01(1.0 - bid_error / num_cards)

    # Patience: low bidders who don't overbid score high
    overbid = max(0, player_bid - player_tricks)
    patience = clamp01(1.0 - overbid / num_cards)

    # Aggression: high bids + winning lots of tricks
    aggression = clamp01((player_bid + player_tricks) / (2 * num_cards))

    # Adaptability: how close is player's bid to the table average
    other_bids = [bid for pid, bid in all_bids_map.items() if pid != player_id]
    if other_bids:
        table_avg = sum(other_bids) / len(other_bids)
        adaptability = clamp01(1.0 - abs(player_bid - table_avg) / num_cards)
    else:
        adaptability = 0.5

    # Consistency: placeholder for single round (needs history)
    consistency = 1.0 if player_bid == player_tricks else 0.5

    # Boldness: bidding high AND delivering
    # bid 5/7 make 5 → 0.71 (bold), bid 5/7 make 4 → 0.57, bid 5/7 make 1 → 0.14 (reckless)
    if player_bid == 0:
        boldness = 0.0
    else:
        delivery_ratio = min(player_tricks / player_bid, 1.0)
        boldness = clamp01((player_bid / num_cards) * delivery_ratio)

    # Precision: exact bid hit weighted by round difficulty
    # Nailing a 10-card round is harder than a 2-card round
    exact_hit = 1.0 if player_bid == player_tricks else 0.0
    precision = exact_hit  # difficulty weighting applied during aggregation

    return {
        "risk": risk,
        "planning": planning,
        "patience": patience,
        "aggression": aggression,
        "adaptability": adaptability,
        "consistency": consistency,
        "boldness": boldness,
        "precision": precision,
    }


def compute_fingerprint(session_log: SessionLog, player_id: str) -> Dict[str, float]:
    """Compute a full-game fingerprint for a player using exponential decay weighting."""
    if not session_log.rounds:
        return {dim: 0.5 for dim in DIMENSIONS}

    alpha = 0.6
    weighted_sums = {dim: 0.0 for dim in _PER_ROUND_DIMS}
    total_weight = 0.0

    # Collect per-round data for session-level computations
    round_hits: List[bool] = []  # did player hit bid exactly?
    round_errors: List[float] = []  # normalized bid errors
    round_num_cards: List[int] = []  # cards per round (for precision weighting)
    max_cards = max((r.num_cards for r in session_log.rounds), default=1)

    round_count = len(session_log.rounds)
    for index, round_log in enumerate(session_log.rounds):
        # Build bids map from round_log.bids
        bids_map = {bid.player_id: bid.amount for bid in round_log.bids}
        if player_id not in bids_map:
            continue

        player_bid = bids_map[player_id]
        player_tricks = round_log.tricks_won.get(player_id, 0)
        num_cards = max(round_log.num_cards, 1)

        hit = player_bid == player_tricks
        round_hits.append(hit)
        round_errors.append(abs(player_bid - player_tricks) / num_cards)
        round_num_cards.append(num_cards)

        # Weight: more recent rounds count more
        recency = round_count - 1 - index  # 0 = most recent
        weight = alpha ** recency

        round_vec = project_round(round_log, player_id, bids_map)

        # Apply difficulty weighting to precision before aggregation
        difficulty_weight = num_cards / max(max_cards, 1)
        round_vec["precision"] *= (0.5 + 0.5 * difficulty_weight)

        for dim in _PER_ROUND_DIMS:
            weighted_sums[dim] += round_vec[dim] * weight
        total_weight += weight

    if total_weight == 0:
        return {dim: 0.5 for dim in DIMENSIONS}

    # --- Aggregate per-round dims ---
    result = {dim: clamp01(weighted_sums[dim] / total_weight) for dim in _PER_ROUND_DIMS}

    # --- Consistency: from bid accuracy variance ---
    if len(round_errors) >= 2:
        mean_error = sum(round_errors) / len(round_errors)
        variance = sum((err - mean_error) ** 2 for err in round_errors) / len(round_errors)
        result["consistency"] = clamp01(1.0 - variance * 4)
    elif round_errors:
        result["consistency"] = clamp01(1.0 - round_errors[0])
    else:
        result["consistency"] = 0.5

    # --- Precision: blend weighted avg with overall hit rate ---
    if round_hits:
        hit_rate = sum(1 for h in round_hits if h) / len(round_hits)
        result["precision"] = clamp01(0.6 * result["precision"] + 0.4 * hit_rate)

    # --- Resilience: recoveries after bad rounds ---
    if len(round_hits) >= 2:
        bad_rounds = [i for i, hit in enumerate(round_hits) if not hit]
        if bad_rounds:
            recoveries = sum(
                1 for i in bad_rounds
                if i + 1 < len(round_hits) and round_hits[i + 1]
            )
            result["resilience"] = clamp01(recoveries / len(bad_rounds))
        else:
            result["resilience"] = 0.5  # never had a bad round
    else:
        result["resilience"] = 0.5

    # --- Clutch: late-game hit rate vs early-game hit rate ---
    if len(round_hits) >= 3:
        late_start = len(round_hits) * 2 // 3
        late_start = max(late_start, 1)  # at least 1 early round
        early_hits = round_hits[:late_start]
        late_hits = round_hits[late_start:]
        if late_hits:
            early_rate = sum(1 for h in early_hits if h) / len(early_hits) if early_hits else 0.5
            late_rate = sum(1 for h in late_hits if h) / len(late_hits)
            result["clutch"] = clamp01(0.5 + (late_rate - early_rate))
        else:
            result["clutch"] = 0.5
    else:
        result["clutch"] = 0.5

    # --- Trajectory: second-half accuracy improvement over first-half ---
    if len(round_errors) >= 2:
        mid = len(round_errors) // 2
        mid = max(mid, 1)
        first_half = round_errors[:mid]
        second_half = round_errors[mid:]
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        # Positive improvement = second half has lower errors
        improvement = first_avg - second_avg
        result["trajectory"] = clamp01(0.5 + improvement * 2)
    else:
        result["trajectory"] = 0.5

    return result
