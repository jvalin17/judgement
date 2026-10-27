from __future__ import annotations

from backend.app.models import Card, Suit, Bid


def get_valid_cards(
    hand: list[Card],
    lead_suit: Suit | None,
    trump_suit: Suit | None = None,
    must_trump_when_void: bool = False,
) -> list[Card]:
    """Cards a player may legally play.

    Always: follow the lead suit if you can. With the must-trump house rule,
    a player who cannot follow suit must play a trump if they hold one.
    """
    if lead_suit is None:
        return list(hand)
    matching = [card for card in hand if card.suit == lead_suit]
    if matching:
        return matching
    if must_trump_when_void and trump_suit is not None:
        trumps = [card for card in hand if card.suit == trump_suit]
        if trumps:
            return trumps
    return list(hand)


def validate_play(
    card: Card,
    hand: list[Card],
    lead_suit: Suit | None,
    trump_suit: Suit | None = None,
    must_trump_when_void: bool = False,
) -> bool:
    if card not in hand:
        return False
    valid = get_valid_cards(hand, lead_suit, trump_suit, must_trump_when_void)
    return card in valid


def get_forbidden_bid(
    player_index_in_bid_order: int,
    num_players: int,
    num_cards: int,
    bids_so_far: list[Bid],
    must_lose_mode: bool,
    dealer_restriction: bool = True,
) -> int | None:
    """Return the bid value that this player is NOT allowed to make, or None."""
    # Only the dealer (last bidder) is ever constrained — total bids != num_cards.
    # This applies in both standard and must-lose (turbulence) mode.
    # The "dealer restriction" house rule can switch it off entirely.
    if not dealer_restriction:
        return None
    is_dealer = player_index_in_bid_order == num_players - 1
    if not is_dealer:
        return None
    total = sum(bid.amount for bid in bids_so_far)
    forbidden = num_cards - total
    if 0 <= forbidden <= num_cards:
        return forbidden
    return None


def validate_bid(
    amount: int,
    player_index_in_bid_order: int,
    num_players: int,
    num_cards: int,
    bids_so_far: list[Bid],
    must_lose_mode: bool,
    dealer_restriction: bool = True,
) -> bool:
    if amount < 0 or amount > num_cards:
        return False
    forbidden = get_forbidden_bid(
        player_index_in_bid_order, num_players, num_cards, bids_so_far, must_lose_mode,
        dealer_restriction,
    )
    if forbidden is not None and amount == forbidden:
        return False
    return True
