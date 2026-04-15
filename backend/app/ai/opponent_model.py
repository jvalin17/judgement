from __future__ import annotations

from typing import Dict, List, Set

from backend.app.models import Suit, Bid
from backend.app.models.game import TrickPlay


class OpponentModel:
    """Analyzes trick history to build a picture of each opponent."""

    def __init__(
        self,
        player_id: str,
        trick_history: List[List[TrickPlay]],
        current_trick_plays: List[TrickPlay],
        bids: List[Bid],
        tricks_won: Dict[str, int],
        trump_suit: Suit,
    ):
        self._player_id = player_id
        self._trick_history = trick_history
        self._current_trick_plays = current_trick_plays
        self._bids = bids
        self._tricks_won = tricks_won
        self._trump_suit = trump_suit
        self._voids: Dict[str, Set[Suit]] = self._detect_voids()

    def _detect_voids(self) -> Dict[str, Set[Suit]]:
        """Scan trick history to find suits each player is void in.

        If a player didn't follow the lead suit, they are void in it.
        """
        voids: Dict[str, Set[Suit]] = {}
        for trick_plays in self._trick_history:
            if not trick_plays:
                continue
            lead_suit = trick_plays[0].card.suit
            for play in trick_plays[1:]:
                if play.card.suit != lead_suit:
                    player_voids = voids.setdefault(play.player_id, set())
                    player_voids.add(lead_suit)
        # Also check current trick in progress
        if self._current_trick_plays:
            lead_suit = self._current_trick_plays[0].card.suit
            for play in self._current_trick_plays[1:]:
                if play.card.suit != lead_suit:
                    player_voids = voids.setdefault(play.player_id, set())
                    player_voids.add(lead_suit)
        return voids

    def get_likely_voids(self, opponent_id: str) -> Set[Suit]:
        """Return suits the opponent is likely void in."""
        return self._voids.get(opponent_id, set())

    def opponent_might_be_void(self, opponent_id: str, suit: Suit) -> bool:
        """True if opponent has been observed not following this suit."""
        return suit in self._voids.get(opponent_id, set())

    def get_opponent_needs(self, opponent_id: str) -> int:
        """Return tricks still needed by opponent (positive = hunting, <=0 = satisfied)."""
        bid_amount = self._get_bid(opponent_id)
        if bid_amount is None:
            return 0
        tricks_won = self._tricks_won.get(opponent_id, 0)
        return bid_amount - tricks_won

    def get_dangerous_opponents(self) -> List[str]:
        """Opponents still hunting for tricks (needs > 0)."""
        return [
            bid.player_id
            for bid in self._bids
            if bid.player_id != self._player_id and self.get_opponent_needs(bid.player_id) > 0
        ]

    def get_satisfied_opponents(self) -> List[str]:
        """Opponents who have already met or exceeded their bid."""
        return [
            bid.player_id
            for bid in self._bids
            if bid.player_id != self._player_id and self.get_opponent_needs(bid.player_id) <= 0
        ]

    def _get_bid(self, player_id: str) -> int | None:
        for bid in self._bids:
            if bid.player_id == player_id:
                return bid.amount
        return None
