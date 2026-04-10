from __future__ import annotations

import random

from backend.app.models import Card, Suit, Rank


def create_deck() -> list[Card]:
    return [Card(suit=suit, rank=rank) for suit in Suit for rank in Rank]


def shuffle_deck(deck: list[Card], rng: random.Random | None = None) -> list[Card]:
    shuffled = list(deck)
    if rng:
        rng.shuffle(shuffled)
    else:
        random.shuffle(shuffled)
    return shuffled


def deal(deck: list[Card], num_players: int, cards_per_player: int) -> list[list[Card]]:
    hands: list[list[Card]] = []
    for player_index in range(num_players):
        start = player_index * cards_per_player
        hands.append(deck[start : start + cards_per_player])
    return hands
