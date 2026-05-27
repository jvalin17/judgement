"""Smart Hard AI that learns from game data.

Delegates predictions to a pluggable ML model (kNN, Decision Tree,
Naive Bayes, or Strategy Classifier). Falls back to rule-based HardAI
when the model has insufficient data or low confidence.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from backend.app.models import Card
from backend.app.ai.base import AIStrategy, RoundContext
from backend.app.ai.hard import HardAI
from backend.app.ml.learning.features import extract_bid_features, extract_play_features, index_to_card
from backend.app.ml.learning.decision_collector import get_bid_data_file, get_play_data_file
from backend.app.ml.data_store import get_default_store

logger = logging.getLogger(__name__)


class SmartHardAI(AIStrategy):
    """Hard AI that learns from data via a pluggable model, with rule-based fallback."""

    strategy_type = "smart_hard"

    def __init__(self, model=None):
        if model is None:
            from backend.app.ml.learning.neighbor_model import CardGameKNN
            model = CardGameKNN()
        self._model = model
        self._fallback = HardAI()
        logger.info("SmartHardAI initialized with model: %s", self._model.model_name)

    def choose_bid(
        self,
        hand: List[Card],
        valid_bids: List[int],
        context: RoundContext,
    ) -> int:
        features = extract_bid_features(hand, context)
        examples = get_default_store().load_examples(get_bid_data_file())

        prediction = self._model.predict(features, examples, context={
            "mode": "bid",
            "valid_bids": valid_bids,
            "round_context": context,
        })

        if prediction is not None:
            predicted = prediction.value
            if predicted in valid_bids:
                return predicted
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
        examples = get_default_store().load_examples(get_play_data_file())

        prediction = self._model.predict(features, examples, context={
            "mode": "play",
            "hand": hand,
            "valid_cards": valid_cards,
            "round_context": context,
        })

        if prediction is not None:
            predicted_index = max(0, min(prediction.value, len(valid_cards) - 1))
            card = index_to_card(predicted_index, valid_cards)
            if card is not None:
                return card

        return self._fallback.choose_card(hand, valid_cards, context)
