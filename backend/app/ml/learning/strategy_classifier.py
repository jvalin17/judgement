"""Strategy classifier — predicts a play strategy, then executes it with rules.

Instead of predicting an exact bid or card index, this model predicts
a high-level strategy label (e.g., "bid_conservative", "dump_lowest")
and then uses rule-based logic to execute that strategy. This generalizes
better because "dump lowest" is always the right concept regardless of
which specific card is lowest.

Thinks ahead like chess: evaluates the game situation, picks the best
strategic approach, then executes precisely.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from backend.app.ml.learning.model_base import Prediction
from backend.app.ml.learning.naive_bayes import NaiveBayesModel

logger = logging.getLogger(__name__)

# --- Strategy labels ---

BID_ZERO = 0
BID_CONSERVATIVE = 1
BID_MODERATE = 2
BID_AGGRESSIVE = 3

PLAY_DUMP_LOWEST = 0
PLAY_FOLLOW_LOW = 1
PLAY_FOLLOW_HIGH = 2
PLAY_TRUMP = 3
PLAY_HIGHEST = 4

CONFIDENCE_THRESHOLD = 0.3


class StrategyClassifier:
    """Predicts strategy labels, then uses rules to pick the exact move."""

    @property
    def model_name(self) -> str:
        return "strategy"

    def __init__(self):
        self._bid_model = NaiveBayesModel()
        self._play_model = NaiveBayesModel()

    def predict(
        self,
        features: List[float],
        examples: List[dict],
        context: Optional[Dict] = None,
    ) -> Optional[Prediction]:
        if not context:
            return None

        mode = context.get("mode")
        if mode == "bid":
            return self._predict_bid(features, examples, context)
        elif mode == "play":
            return self._predict_play(features, examples, context)
        return None

    def _predict_bid(
        self,
        features: List[float],
        examples: List[dict],
        context: Dict,
    ) -> Optional[Prediction]:
        # Convert examples to strategy-labeled data
        strategy_examples = []
        for ex in examples:
            if ex.get("outcome", "win") != "win":
                continue
            num_cards = ex["features"][0] if ex["features"] else 5
            strategy_label = _bid_to_strategy(ex["label"], num_cards)
            strategy_examples.append({
                "features": ex["features"],
                "label": float(strategy_label),
                "outcome": "win",
            })

        prediction = self._bid_model.predict(features, strategy_examples)
        if prediction is None:
            return None

        # Execute the strategy
        strategy = prediction.value
        valid_bids = context.get("valid_bids", [])
        round_context = context.get("round_context")

        bid = _execute_bid_strategy(strategy, features, valid_bids, round_context)
        if bid is None:
            return None
        return Prediction(value=bid, confidence=prediction.confidence)

    def _predict_play(
        self,
        features: List[float],
        examples: List[dict],
        context: Dict,
    ) -> Optional[Prediction]:
        # Convert examples to strategy-labeled data
        strategy_examples = []
        for ex in examples:
            if ex.get("outcome", "win") != "win":
                continue
            num_valid = len(ex["features"])  # approximate
            strategy_label = _play_index_to_strategy(ex["label"], ex["features"])
            strategy_examples.append({
                "features": ex["features"],
                "label": float(strategy_label),
                "outcome": "win",
            })

        prediction = self._play_model.predict(features, strategy_examples)
        if prediction is None:
            return None

        # Execute the strategy
        strategy = prediction.value
        hand = context.get("hand", [])
        valid_cards = context.get("valid_cards", [])
        round_context = context.get("round_context")

        card_index = _execute_play_strategy(strategy, hand, valid_cards, round_context)
        if card_index is None:
            return None
        return Prediction(value=card_index, confidence=prediction.confidence)


# --- Label conversion: numeric → strategy ---

def _bid_to_strategy(bid_label: float, num_cards: float) -> int:
    """Convert a numeric bid to a strategy label."""
    bid = round(bid_label)
    num = max(num_cards, 1)
    if bid == 0:
        return BID_ZERO
    ratio = bid / num
    if ratio <= 0.3:
        return BID_CONSERVATIVE
    if ratio <= 0.6:
        return BID_MODERATE
    return BID_AGGRESSIVE


def _play_index_to_strategy(card_index: float, features: List[float]) -> int:
    """Convert a card index + features to a strategy label.

    Uses features to infer what the player was doing:
    - tricks_needed (features[0]): positive = need wins, zero/negative = need to dump
    - is_leading (features[4]): 1.0 if leading
    - can_win (features[7]): 1.0 if a winning card exists
    """
    index = round(card_index)
    tricks_needed = features[0] if len(features) > 0 else 0
    is_leading = features[4] if len(features) > 4 else 0
    can_win = features[7] if len(features) > 7 else 0
    num_trumps = features[5] if len(features) > 5 else 0

    if tricks_needed <= 0:
        return PLAY_DUMP_LOWEST
    if can_win and num_trumps > 0 and index > 0:
        return PLAY_TRUMP
    if index == 0:
        return PLAY_FOLLOW_LOW
    if can_win:
        return PLAY_FOLLOW_HIGH
    return PLAY_DUMP_LOWEST


# --- Strategy execution ---

def _execute_bid_strategy(
    strategy: int,
    features: List[float],
    valid_bids: List[int],
    round_context,
) -> Optional[int]:
    """Convert a strategy label to an actual bid."""
    if not valid_bids:
        return None

    num_cards = features[0] if features else 5
    trump_count = features[3] if len(features) > 3 else 0
    high_trump = features[4] if len(features) > 4 else 0
    aces = features[5] if len(features) > 5 else 0

    if strategy == BID_ZERO:
        bid = 0
    elif strategy == BID_CONSERVATIVE:
        estimated = trump_count * 0.5 + aces * 0.6
        bid = max(0, round(estimated * 0.7))
    elif strategy == BID_MODERATE:
        estimated = trump_count * 0.7 + high_trump * 0.3 + aces * 0.8
        bid = round(estimated)
    else:  # BID_AGGRESSIVE
        estimated = trump_count * 0.8 + high_trump * 0.5 + aces * 0.9
        bid = round(estimated * 1.2)

    # Clamp to nearest valid bid
    if bid in valid_bids:
        return bid
    return min(valid_bids, key=lambda b: abs(b - bid))


def _execute_play_strategy(
    strategy: int,
    hand: List,
    valid_cards: List,
    round_context,
) -> Optional[int]:
    """Convert a strategy label to a card index in sorted valid cards."""
    if not valid_cards:
        return None

    from backend.app.models import Suit
    sorted_cards = sorted(valid_cards, key=lambda c: (c.suit, c.rank))

    trump = round_context.trump_suit if round_context else None
    trick_cards = round_context.current_trick_cards if round_context else []
    lead_suit = trick_cards[0].suit if trick_cards else None

    if strategy == PLAY_DUMP_LOWEST:
        # Dump lowest non-trump, or lowest overall
        non_trump = [c for c in sorted_cards if c.suit != trump] if trump else sorted_cards
        target = non_trump[0] if non_trump else sorted_cards[0]
        return sorted_cards.index(target)

    elif strategy == PLAY_FOLLOW_LOW:
        # Lowest card of lead suit, or lowest overall
        if lead_suit:
            lead_cards = [c for c in sorted_cards if c.suit == lead_suit]
            if lead_cards:
                return sorted_cards.index(lead_cards[0])
        return 0

    elif strategy == PLAY_FOLLOW_HIGH:
        # Highest card of lead suit, or highest overall
        if lead_suit:
            lead_cards = [c for c in sorted_cards if c.suit == lead_suit]
            if lead_cards:
                return sorted_cards.index(lead_cards[-1])
        return len(sorted_cards) - 1

    elif strategy == PLAY_TRUMP:
        # Lowest trump that wins, or lowest trump
        trumps = [c for c in sorted_cards if c.suit == trump] if trump else []
        if trumps:
            return sorted_cards.index(trumps[0])
        return len(sorted_cards) - 1

    elif strategy == PLAY_HIGHEST:
        return len(sorted_cards) - 1

    return 0
