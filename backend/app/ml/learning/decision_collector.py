"""Collects decision data during gameplay and persists winner decisions.

The collector records every player's bid and card-play decisions with
feature vectors and strategy type, then at game end writes only the
winner's decisions to the data files.

Information isolation guarantees:
- Features are extracted from the player's OWN hand and public game state only.
- No other player's hand data is ever included in the features.
- Raw card values are never stored — only numeric counts and ratios.
- The strategy_type field tracks which strategy made the decision
  (e.g. "easy", "medium", "hard", "smart_hard", "human").
"""

from __future__ import annotations

import logging
import os
from typing import Dict, List

from backend.app.models import Card
from backend.app.ai.base import RoundContext
from backend.app.ml.learning.features import extract_bid_features, extract_play_features, card_to_index
from backend.app.ml.learning import neighbor_model

logger = logging.getLogger(__name__)

# Default data directory — relative to this file
_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def get_bid_data_file() -> str:
    return os.path.join(_DATA_DIR, "bid_decisions.jsonl")


def get_play_data_file() -> str:
    return os.path.join(_DATA_DIR, "play_decisions.jsonl")


class DecisionCollector:
    """Buffers decisions during a game, flushes winner's data at game end."""

    def __init__(self):
        # player_id -> list of (features, label, strategy_type) tuples
        self._bid_decisions: Dict[str, List[tuple]] = {}
        self._play_decisions: Dict[str, List[tuple]] = {}
        # player_id -> whether they opted in to community data sharing
        self._share_consent: Dict[str, bool] = {}

    def set_share_consent(self, player_id: str, consented: bool) -> None:
        """Mark whether a player has opted in to community data sharing."""
        self._share_consent[player_id] = consented

    def record_bid(
        self,
        player_id: str,
        hand: List[Card],
        context: RoundContext,
        bid_amount: int,
        strategy_type: str = "unknown",
    ) -> None:
        """Record a bid decision with its feature vector and strategy type."""
        features = extract_bid_features(hand, context)
        if player_id not in self._bid_decisions:
            self._bid_decisions[player_id] = []
        self._bid_decisions[player_id].append((features, float(bid_amount), strategy_type))

    def record_play(
        self,
        player_id: str,
        hand: List[Card],
        valid_cards: List[Card],
        context: RoundContext,
        card_played: Card,
        strategy_type: str = "unknown",
    ) -> None:
        """Record a card-play decision with its feature vector and strategy type."""
        features = extract_play_features(hand, valid_cards, context)
        card_index = card_to_index(card_played, valid_cards)
        if player_id not in self._play_decisions:
            self._play_decisions[player_id] = []
        self._play_decisions[player_id].append((features, float(card_index), strategy_type))

    def flush_winner(self, winner_ids: List[str]) -> int:
        """Write the winner's decisions to data files. Returns examples written."""
        count = 0
        bid_file = get_bid_data_file()
        play_file = get_play_data_file()

        for winner_id in winner_ids:
            bid_count = len(self._bid_decisions.get(winner_id, []))
            play_count = len(self._play_decisions.get(winner_id, []))
            consented = self._share_consent.get(winner_id, False)

            for features, label, strategy_type in self._bid_decisions.get(winner_id, []):
                neighbor_model.append_example(
                    bid_file, features, label,
                    metadata={"strategy_type": strategy_type, "share_consent": consented},
                )
                count += 1
            for features, label, strategy_type in self._play_decisions.get(winner_id, []):
                neighbor_model.append_example(
                    play_file, features, label,
                    metadata={"strategy_type": strategy_type, "share_consent": consented},
                )
                count += 1

            if bid_count or play_count:
                logger.info(
                    "Flushed %d bid + %d play decisions for winner %s",
                    bid_count, play_count, winner_id,
                )

        self._bid_decisions.clear()
        self._play_decisions.clear()
        return count

    def clear(self) -> None:
        """Discard all buffered decisions."""
        self._bid_decisions.clear()
        self._play_decisions.clear()
