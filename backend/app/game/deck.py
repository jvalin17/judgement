from __future__ import annotations

import os
import random

from backend.app.models import Card, Suit, Rank


def create_deck() -> list[Card]:
    return [Card(suit=suit, rank=rank) for suit in Suit for rank in Rank]


def shuffle_deck(deck: list[Card], rng: random.Random | None = None) -> list[Card]:
    """Shuffle with OS-level entropy so back-to-back games never correlate.

    When no explicit RNG is passed (normal gameplay), we seed a fresh
    Random instance from os.urandom each time.  This breaks any dependence
    on Python's global Mersenne Twister state and guarantees that two
    consecutive shuffles share no sequential relationship.

    Tests can still pass a seeded ``rng`` for reproducibility.
    """
    shuffled = list(deck)
    if rng:
        rng.shuffle(shuffled)
    else:
        secure_rng = random.Random(os.urandom(32))
        secure_rng.shuffle(shuffled)
    return shuffled


def deal(deck: list[Card], num_players: int, cards_per_player: int) -> list[list[Card]]:
    hands: list[list[Card]] = []
    for player_index in range(num_players):
        start = player_index * cards_per_player
        hands.append(deck[start : start + cards_per_player])
    return hands
