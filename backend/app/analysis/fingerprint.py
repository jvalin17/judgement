"""Compute a player's trait vector from their game history."""
from __future__ import annotations

from typing import Dict, List

from backend.app.models.session import RoundLog, SessionLog


DIMENSIONS = ("risk", "planning", "patience", "aggression", "adaptability", "consistency")


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def project_round(round_log: RoundLog, player_id: str, all_bids_map: Dict[str, int]) -> Dict[str, float]:
    """Project a single round into a 6-dimension trait vector for a player."""
    player_bid = all_bids_map.get(player_id, 0)
    player_tricks = round_log.tricks_won.get(player_id, 0)
    num_cards = max(round_log.num_cards, 1)

    # Risk: how aggressively did they bid relative to hand size
    risk = _clamp01(player_bid / num_cards)

    # Planning: did they hit their bid exactly?
    bid_error = abs(player_bid - player_tricks)
    planning = _clamp01(1.0 - bid_error / num_cards)

    # Patience: low bidders who don't overbid score high
    overbid = max(0, player_bid - player_tricks)
    patience = _clamp01(1.0 - overbid / num_cards)

    # Aggression: high bids + winning lots of tricks
    aggression = _clamp01((player_bid + player_tricks) / (2 * num_cards))

    # Adaptability: how close is player's bid to the table average
    other_bids = [bid for pid, bid in all_bids_map.items() if pid != player_id]
    if other_bids:
        table_avg = sum(other_bids) / len(other_bids)
        adaptability = _clamp01(1.0 - abs(player_bid - table_avg) / num_cards)
    else:
        adaptability = 0.5

    # Consistency: placeholder for single round (needs history)
    consistency = 1.0 if player_bid == player_tricks else 0.5

    return {
        "risk": risk,
        "planning": planning,
        "patience": patience,
        "aggression": aggression,
        "adaptability": adaptability,
        "consistency": consistency,
    }


def compute_fingerprint(session_log: SessionLog, player_id: str) -> Dict[str, float]:
    """Compute a full-game fingerprint for a player using exponential decay weighting."""
    if not session_log.rounds:
        return {dim: 0.5 for dim in DIMENSIONS}

    alpha = 0.6
    weighted_sums = {dim: 0.0 for dim in DIMENSIONS}
    total_weight = 0.0

    round_count = len(session_log.rounds)
    for index, round_log in enumerate(session_log.rounds):
        # Build bids map from round_log.bids
        bids_map = {bid.player_id: bid.amount for bid in round_log.bids}
        if player_id not in bids_map:
            continue

        # Weight: more recent rounds count more
        recency = round_count - 1 - index  # 0 = most recent
        weight = alpha ** recency

        round_vec = project_round(round_log, player_id, bids_map)
        for dim in DIMENSIONS:
            weighted_sums[dim] += round_vec[dim] * weight
        total_weight += weight

    if total_weight == 0:
        return {dim: 0.5 for dim in DIMENSIONS}

    # Compute consistency from bid accuracy variance across all rounds
    bid_errors: List[float] = []
    for round_log in session_log.rounds:
        bids_map = {bid.player_id: bid.amount for bid in round_log.bids}
        player_bid = bids_map.get(player_id)
        if player_bid is None:
            continue
        player_tricks = round_log.tricks_won.get(player_id, 0)
        num_cards = max(round_log.num_cards, 1)
        bid_errors.append(abs(player_bid - player_tricks) / num_cards)

    if len(bid_errors) >= 2:
        mean_error = sum(bid_errors) / len(bid_errors)
        variance = sum((err - mean_error) ** 2 for err in bid_errors) / len(bid_errors)
        consistency = _clamp01(1.0 - variance * 4)  # scale so variance 0.25 → 0
    elif bid_errors:
        consistency = _clamp01(1.0 - bid_errors[0])
    else:
        consistency = 0.5

    result = {dim: _clamp01(weighted_sums[dim] / total_weight) for dim in DIMENSIONS}
    result["consistency"] = consistency
    return result
