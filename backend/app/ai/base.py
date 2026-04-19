from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from backend.app.models import Card, Suit, Bid
from backend.app.models.game import TrickPlay


class RoundContext:
    """Information visible to an AI player during a round."""

    def __init__(
        self,
        player_id: str,
        trump_suit: Suit,
        num_cards: int,
        num_players: int,
        bids: List[Bid],
        tricks_won: dict,
        cards_played: List[Card],
        current_trick_cards: List[Card],
        trick_history: Optional[List[List[TrickPlay]]] = None,
        current_trick_plays: Optional[List[TrickPlay]] = None,
        play_order: Optional[List[str]] = None,
    ):
        self.player_id = player_id
        self.trump_suit = trump_suit
        self.num_cards = num_cards
        self.num_players = num_players
        self.bids = bids
        self.tricks_won = tricks_won
        self.cards_played = cards_played
        self.current_trick_cards = current_trick_cards
        self.trick_history = trick_history or []
        self.current_trick_plays = current_trick_plays or []
        self.play_order = play_order or []


class AIStrategy(ABC):

    strategy_type: str = "unknown"

    @abstractmethod
    def choose_bid(
        self,
        hand: List[Card],
        valid_bids: List[int],
        context: RoundContext,
    ) -> int:
        """Choose a bid from the list of valid bids."""
        ...

    @abstractmethod
    def choose_card(
        self,
        hand: List[Card],
        valid_cards: List[Card],
        context: RoundContext,
    ) -> Card:
        """Choose a card to play from the list of valid cards."""
        ...
