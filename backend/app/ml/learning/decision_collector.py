"""Collects decision data during gameplay with per-decision feedback.

The collector records every player's bid and card-play decisions with
feature vectors, then annotates them with feedback after each trick/round:
- Play decisions: did this card win the trick?
- Bid decisions: did the player hit their bid? How far off?

At game end, all decisions (winners + losers) are flushed with outcome
and feedback metadata. Models learn from this rich signal — a trick-winning
play from a game winner is the strongest positive signal.

Information isolation guarantees:
- Features extracted from player's OWN hand and public game state only
- No other player's hand data is ever included
- Raw card values never stored — only numeric counts and ratios
"""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

from backend.app.models import Card
from backend.app.ai.base import RoundContext
from backend.app.ml.learning.features import extract_bid_features, extract_play_features, card_to_index
from backend.app.ml.learning import neighbor_model

logger = logging.getLogger(__name__)

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def get_bid_data_file() -> str:
    return os.path.join(_DATA_DIR, "bid_decisions.jsonl")


def get_play_data_file() -> str:
    return os.path.join(_DATA_DIR, "play_decisions.jsonl")


class DecisionCollector:
    """Buffers decisions during a game, annotates with feedback, flushes at game end."""

    def __init__(self):
        # player_id -> list of decision dicts
        self._bid_decisions: Dict[str, List[dict]] = {}
        self._play_decisions: Dict[str, List[dict]] = {}
        self._share_consent: Dict[str, bool] = {}
        # Track current round's play decisions for trick feedback
        self._current_round_plays: Dict[str, List[dict]] = {}

    def set_share_consent(self, player_id: str, consented: bool) -> None:
        self._share_consent[player_id] = consented

    def record_bid(
        self,
        player_id: str,
        hand: List[Card],
        context: RoundContext,
        bid_amount: int,
        strategy_type: str = "unknown",
        model_name: str = "",
    ) -> None:
        """Record a bid decision with feature vector and metadata."""
        features = extract_bid_features(hand, context)
        decision = {
            "features": features,
            "label": float(bid_amount),
            "strategy_type": strategy_type,
            "model_name": model_name,
            "round_number": context.round_number,
            "num_cards": context.num_cards,
            # Feedback fields — filled in by annotate_round_end()
            "bid_hit": None,
            "bid_error": None,
        }
        self._bid_decisions.setdefault(player_id, []).append(decision)

    def record_play(
        self,
        player_id: str,
        hand: List[Card],
        valid_cards: List[Card],
        context: RoundContext,
        card_played: Card,
        strategy_type: str = "unknown",
        model_name: str = "",
    ) -> None:
        """Record a card-play decision with feature vector and metadata."""
        features = extract_play_features(hand, valid_cards, context)
        card_index = card_to_index(card_played, valid_cards)
        decision = {
            "features": features,
            "label": float(card_index),
            "strategy_type": strategy_type,
            "model_name": model_name,
            "round_number": context.round_number,
            # Feedback fields — filled in by annotate_trick_result()
            "trick_won": None,
        }
        self._play_decisions.setdefault(player_id, []).append(decision)
        self._current_round_plays.setdefault(player_id, []).append(decision)

    def annotate_trick_result(self, winner_id: str, player_ids: List[str]) -> None:
        """Annotate the most recent play decision for each player in the trick."""
        for player_id in player_ids:
            plays = self._current_round_plays.get(player_id, [])
            if plays:
                plays[-1]["trick_won"] = (player_id == winner_id)

    def annotate_round_end(self, bids: Dict[str, int], tricks_won: Dict[str, int]) -> None:
        """Annotate bid decisions with accuracy feedback, then reset round tracking."""
        for player_id, bid_amount in bids.items():
            actual_tricks = tricks_won.get(player_id, 0)
            bid_hit = (bid_amount == actual_tricks)
            bid_error = actual_tricks - bid_amount

            decisions = self._bid_decisions.get(player_id, [])
            # Find the most recent unannotated bid for this player
            for decision in reversed(decisions):
                if decision["bid_hit"] is None:
                    decision["bid_hit"] = bid_hit
                    decision["bid_error"] = bid_error
                    break

        self._current_round_plays.clear()

    def flush_winner(self, winner_ids: List[str]) -> int:
        return self._flush_with_outcome(winner_ids, "win")

    def flush_losers(self, loser_ids: List[str]) -> int:
        return self._flush_with_outcome(loser_ids, "loss")

    def _flush_with_outcome(self, player_ids: List[str], outcome: str) -> int:
        count = 0
        bid_file = get_bid_data_file()
        play_file = get_play_data_file()

        for player_id in player_ids:
            consented = self._share_consent.get(player_id, False)

            for decision in self._bid_decisions.get(player_id, []):
                metadata = {
                    "strategy_type": decision["strategy_type"],
                    "share_consent": consented,
                    "outcome": outcome,
                    "model_name": decision.get("model_name", ""),
                    "round_number": decision.get("round_number", 0),
                    "num_cards": decision.get("num_cards", 0),
                    "bid_hit": decision.get("bid_hit"),
                    "bid_error": decision.get("bid_error"),
                }
                neighbor_model.append_example(
                    bid_file, decision["features"], decision["label"],
                    metadata=metadata,
                )
                count += 1

            for decision in self._play_decisions.get(player_id, []):
                metadata = {
                    "strategy_type": decision["strategy_type"],
                    "share_consent": consented,
                    "outcome": outcome,
                    "model_name": decision.get("model_name", ""),
                    "round_number": decision.get("round_number", 0),
                    "trick_won": decision.get("trick_won"),
                }
                neighbor_model.append_example(
                    play_file, decision["features"], decision["label"],
                    metadata=metadata,
                )
                count += 1

            bid_count = len(self._bid_decisions.get(player_id, []))
            play_count = len(self._play_decisions.get(player_id, []))
            if bid_count or play_count:
                logger.info(
                    "Flushed %d bid + %d play decisions for %s %s",
                    bid_count, play_count, outcome, player_id,
                )

        return count

    def flush_all(self, winner_ids: List[str], loser_ids: List[str]) -> int:
        count = self.flush_winner(winner_ids)
        count += self.flush_losers(loser_ids)
        self._bid_decisions.clear()
        self._play_decisions.clear()
        self._current_round_plays.clear()
        return count

    def clear(self) -> None:
        self._bid_decisions.clear()
        self._play_decisions.clear()
        self._current_round_plays.clear()
