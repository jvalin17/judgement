"""Collects decision data during gameplay and persists winner decisions.

The collector observes game events, records every player's bid and card-play
decisions with feature vectors, then at game end writes only the winner's
decisions to the data files.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from backend.app.models import Card, Suit
from backend.app.ai.base import RoundContext
from backend.app.ai.learning.features import extract_bid_features, extract_play_features, card_to_index
from backend.app.ai.learning import neighbor_model

# Default data directory — relative to this file
_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def get_bid_data_file() -> str:
    return os.path.join(_DATA_DIR, "bid_decisions.jsonl")


def get_play_data_file() -> str:
    return os.path.join(_DATA_DIR, "play_decisions.jsonl")


class DecisionCollector:
    """Buffers decisions during a game, flushes winner's data at game end."""

    def __init__(self):
        # player_id -> list of (features, label) tuples
        self._bid_decisions: Dict[str, List[tuple]] = {}
        self._play_decisions: Dict[str, List[tuple]] = {}

    def record_bid(
        self,
        player_id: str,
        hand: List[Card],
        context: RoundContext,
        bid_amount: int,
    ) -> None:
        """Record a bid decision with its feature vector."""
        features = extract_bid_features(hand, context)
        if player_id not in self._bid_decisions:
            self._bid_decisions[player_id] = []
        self._bid_decisions[player_id].append((features, float(bid_amount)))

    def record_play(
        self,
        player_id: str,
        hand: List[Card],
        valid_cards: List[Card],
        context: RoundContext,
        card_played: Card,
    ) -> None:
        """Record a card-play decision with its feature vector."""
        features = extract_play_features(hand, valid_cards, context)
        card_index = card_to_index(card_played, valid_cards)
        if player_id not in self._play_decisions:
            self._play_decisions[player_id] = []
        self._play_decisions[player_id].append((features, float(card_index)))

    def flush_winner(self, winner_ids: List[str]) -> int:
        """Write the winner's decisions to data files.

        Returns the number of examples written.
        """
        count = 0
        bid_file = get_bid_data_file()
        play_file = get_play_data_file()

        for winner_id in winner_ids:
            for features, label in self._bid_decisions.get(winner_id, []):
                neighbor_model.append_example(bid_file, features, label)
                count += 1
            for features, label in self._play_decisions.get(winner_id, []):
                neighbor_model.append_example(play_file, features, label)
                count += 1

        self._bid_decisions.clear()
        self._play_decisions.clear()
        return count

    def clear(self) -> None:
        """Discard all buffered decisions."""
        self._bid_decisions.clear()
        self._play_decisions.clear()
