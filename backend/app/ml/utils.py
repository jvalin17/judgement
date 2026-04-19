"""Shared ML utilities — math helpers and hand evaluation."""
from __future__ import annotations

from typing import List

from backend.app.models import Card, Suit, Rank


def clamp01(value: float) -> float:
    """Clamp a float to the [0.0, 1.0] range."""
    return max(0.0, min(1.0, value))


# --- Hand evaluation (used by both AI strategies and ML feature extraction) ---


class HandEvaluation:
    """Numeric evaluation of a card hand for bidding decisions."""

    def __init__(
        self,
        trump_count: int,
        high_trump_count: int,
        aces: int,
        kings: int,
        estimated_tricks: float,
        suit_distribution: dict,
    ):
        self.trump_count = trump_count
        self.high_trump_count = high_trump_count
        self.aces = aces
        self.kings = kings
        self.estimated_tricks = estimated_tricks
        self.suit_distribution = suit_distribution


def evaluate_hand(hand: List[Card], trump_suit: Suit) -> HandEvaluation:
    """Evaluate a hand's strength given the trump suit."""
    suit_dist = _count_suit_distribution(hand)
    trump_cards = [card for card in hand if card.suit == trump_suit]

    tricks = 0.0
    tricks += _estimate_trump_tricks(trump_cards)
    tricks += _estimate_non_trump_tricks(hand, trump_suit)
    tricks += _estimate_ruffing_tricks(suit_dist, trump_suit, len(trump_cards))

    return HandEvaluation(
        trump_count=len(trump_cards),
        high_trump_count=len([card for card in trump_cards if card.rank >= Rank.JACK]),
        aces=len([card for card in hand if card.rank == Rank.ACE]),
        kings=len([card for card in hand if card.rank == Rank.KING]),
        estimated_tricks=tricks,
        suit_distribution=suit_dist,
    )


def _count_suit_distribution(hand: List[Card]) -> dict:
    dist: dict = {}
    for card in hand:
        dist[card.suit] = dist.get(card.suit, 0) + 1
    return dist


def _estimate_trump_tricks(trump_cards: List[Card]) -> float:
    tricks = 0.0
    for card in trump_cards:
        if card.rank >= Rank.QUEEN:
            tricks += 0.85
        elif card.rank >= Rank.TEN:
            tricks += 0.5
        else:
            tricks += 0.25
    return tricks


def _estimate_non_trump_tricks(hand: List[Card], trump_suit: Suit) -> float:
    tricks = 0.0
    for card in hand:
        if card.suit == trump_suit:
            continue
        if card.rank == Rank.ACE:
            tricks += 0.75
        elif card.rank == Rank.KING:
            tricks += 0.4
    return tricks


def _estimate_ruffing_tricks(suit_dist: dict, trump_suit: Suit, trump_count: int) -> float:
    if trump_count == 0:
        return 0.0
    tricks = 0.0
    for suit in Suit:
        if suit != trump_suit and suit_dist.get(suit, 0) == 0:
            tricks += 0.3
    return tricks
