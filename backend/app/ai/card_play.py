from __future__ import annotations

from typing import List, Optional

from backend.app.models import Card, Suit


def would_win(card: Card, trick_cards: List[Card], lead_suit: Suit, trump: Suit) -> bool:
    has_trump = any(played.suit == trump for played in trick_cards)
    if card.suit == trump:
        if has_trump:
            best_trump_rank = max(played.rank for played in trick_cards if played.suit == trump)
            return card.rank > best_trump_rank
        return True
    elif card.suit == lead_suit:
        if has_trump:
            return False
        best_lead_rank = max(played.rank for played in trick_cards if played.suit == lead_suit)
        return card.rank > best_lead_rank
    return False


def best_winning_card(
    valid_cards: List[Card],
    trick_cards: List[Card],
    lead_suit: Suit,
    trump: Suit,
) -> Optional[Card]:
    winners = [card for card in valid_cards if would_win(card, trick_cards, lead_suit, trump)]
    if not winners:
        return None
    return min(winners, key=lambda card: (0 if card.suit == lead_suit else 1, card.rank))


def dump_lowest(valid_cards: List[Card], trump: Suit) -> Card:
    non_trump = [card for card in valid_cards if card.suit != trump]
    if non_trump:
        return min(non_trump, key=lambda card: card.rank)
    return min(valid_cards, key=lambda card: card.rank)
