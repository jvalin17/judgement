"""Extract numeric feature vectors from game state for ML predictions."""

from __future__ import annotations

from typing import List, Optional

from backend.app.models import Card, Suit, Rank
from backend.app.ai.base import RoundContext
from backend.app.ai.hand_evaluator import evaluate_hand
from backend.app.ai.card_play import would_win


def extract_bid_features(
    hand: List[Card],
    context: RoundContext,
) -> List[float]:
    """Extract features for a bidding decision.

    Returns a fixed-length numeric vector describing the hand and situation.
    """
    trump = context.trump_suit
    evaluation = evaluate_hand(hand, trump)

    trump_count = evaluation.trump_count
    high_trump_count = evaluation.high_trump_count
    ace_count = evaluation.aces
    king_count = evaluation.kings
    suit_dist = evaluation.suit_distribution

    void_count = sum(1 for suit in Suit if suit != trump and suit_dist.get(suit, 0) == 0)
    singleton_count = sum(1 for suit in Suit if suit != trump and suit_dist.get(suit, 0) == 1)
    longest_suit = max(suit_dist.values()) if suit_dist else 0
    total_bids_so_far = sum(bid.amount for bid in context.bids)
    is_dealer = 1.0 if len(context.bids) == context.num_players - 1 else 0.0

    return [
        float(context.num_cards),
        float(context.num_players),
        float(len(context.bids)),       # position in bid order
        float(trump_count),
        float(high_trump_count),
        float(ace_count),
        float(king_count),
        float(void_count),
        float(singleton_count),
        float(longest_suit),
        float(total_bids_so_far),
        is_dealer,
    ]


def extract_play_features(
    hand: List[Card],
    valid_cards: List[Card],
    context: RoundContext,
) -> List[float]:
    """Extract features for a card-play decision.

    Returns a fixed-length numeric vector describing the game situation.
    """
    trump = context.trump_suit
    trick_cards = context.current_trick_cards
    is_leading = len(trick_cards) == 0
    lead_suit = trick_cards[0].suit if trick_cards else None

    my_bid = _get_my_bid(context)
    my_tricks = context.tricks_won.get(context.player_id, 0)
    tricks_needed = (my_bid - my_tricks) if my_bid is not None else 0

    num_trumps = sum(1 for card in hand if card.suit == trump)
    num_lead_suit = 0
    if lead_suit and not is_leading:
        num_lead_suit = sum(1 for card in hand if card.suit == lead_suit)

    can_win = any(would_win(card, trick_cards, lead_suit, trump) for card in valid_cards) if trick_cards else 1
    current_max_rank = max((card.rank for card in trick_cards), default=0)

    trump_cards_seen = sum(1 for card in context.cards_played if card.suit == trump)
    total_cards_seen = len(context.cards_played)

    return [
        float(tricks_needed),
        float(my_tricks),
        float(len(hand)),               # cards remaining
        float(len(trick_cards)),         # position in trick
        1.0 if is_leading else 0.0,
        float(num_trumps),
        float(num_lead_suit),
        1.0 if can_win else 0.0,
        float(current_max_rank),
        float(trump_cards_seen),
        float(total_cards_seen),
    ]


def card_to_index(card: Card, valid_cards: List[Card]) -> int:
    """Convert a card choice to an index in the sorted valid cards list.

    Cards are sorted by (suit value, rank value) so the index is stable
    regardless of hand order.
    """
    sorted_cards = sorted(valid_cards, key=lambda c: (c.suit, c.rank))
    for index, candidate in enumerate(sorted_cards):
        if candidate.suit == card.suit and candidate.rank == card.rank:
            return index
    return 0


def index_to_card(index: int, valid_cards: List[Card]) -> Optional[Card]:
    """Convert an index back to a card from the valid cards list."""
    sorted_cards = sorted(valid_cards, key=lambda c: (c.suit, c.rank))
    if 0 <= index < len(sorted_cards):
        return sorted_cards[index]
    return None


def _get_my_bid(context: RoundContext) -> Optional[int]:
    for bid in context.bids:
        if bid.player_id == context.player_id:
            return bid.amount
    return None
