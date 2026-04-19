"""Smart Hard AI that learns from game winners.

Uses k-Nearest Neighbors to predict bids and card plays based on
accumulated data from past game winners. Falls back to rule-based
HardAI when insufficient data exists.
"""

from __future__ import annotations

from typing import List, Optional

from backend.app.models import Card
from backend.app.ai.base import AIStrategy, RoundContext
from backend.app.ai.hard import HardAI
from backend.app.ai.learning.features import extract_bid_features, extract_play_features, index_to_card
from backend.app.ai.learning.decision_collector import get_bid_data_file, get_play_data_file
from backend.app.ai.learning import neighbor_model


class SmartHardAI(AIStrategy):
    """Hard AI that learns from winners via kNN, with rule-based fallback."""

    def __init__(self):
        self._fallback = HardAI()

    def choose_bid(
        self,
        hand: List[Card],
        valid_bids: List[int],
        context: RoundContext,
    ) -> int:
        features = extract_bid_features(hand, context)
        predicted = neighbor_model.predict_bid(features, get_bid_data_file())

        if predicted is not None and predicted in valid_bids:
            return predicted

        # If prediction is close to a valid bid, use closest valid
        if predicted is not None:
            closest = min(valid_bids, key=lambda bid: abs(bid - predicted))
            return closest

        return self._fallback.choose_bid(hand, valid_bids, context)

    def choose_card(
        self,
        hand: List[Card],
        valid_cards: List[Card],
        context: RoundContext,
    ) -> Card:
        features = extract_play_features(hand, valid_cards, context)
        predicted_index = neighbor_model.predict_card_index(
            features, len(valid_cards), get_play_data_file(),
        )

        if predicted_index is not None:
            card = index_to_card(predicted_index, valid_cards)
            if card is not None:
                return card

        return self._fallback.choose_card(hand, valid_cards, context)
