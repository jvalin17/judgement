from backend.app.models import Card, Suit, Rank, Bid
from backend.app.game.validators import (
    get_valid_cards, validate_play, validate_bid, get_forbidden_bid,
)


# --- get_valid_cards ---

def test_no_lead_suit_all_valid():
    hand = [Card(suit=Suit.HEARTS, rank=Rank.ACE), Card(suit=Suit.CLUBS, rank=Rank.TWO)]
    assert get_valid_cards(hand, None) == hand


def test_must_follow_suit():
    hand = [
        Card(suit=Suit.HEARTS, rank=Rank.ACE),
        Card(suit=Suit.CLUBS, rank=Rank.TWO),
        Card(suit=Suit.HEARTS, rank=Rank.THREE),
    ]
    valid = get_valid_cards(hand, Suit.HEARTS)
    assert len(valid) == 2
    assert all(c.suit == Suit.HEARTS for c in valid)


def test_no_matching_suit_all_valid():
    hand = [Card(suit=Suit.CLUBS, rank=Rank.ACE), Card(suit=Suit.DIAMONDS, rank=Rank.TWO)]
    valid = get_valid_cards(hand, Suit.HEARTS)
    assert valid == hand


# --- validate_play ---

def test_play_valid_card():
    hand = [Card(suit=Suit.HEARTS, rank=Rank.ACE)]
    assert validate_play(Card(suit=Suit.HEARTS, rank=Rank.ACE), hand, None)


def test_play_card_not_in_hand():
    hand = [Card(suit=Suit.HEARTS, rank=Rank.ACE)]
    assert not validate_play(Card(suit=Suit.CLUBS, rank=Rank.TWO), hand, None)


def test_play_wrong_suit_when_has_matching():
    hand = [
        Card(suit=Suit.HEARTS, rank=Rank.ACE),
        Card(suit=Suit.CLUBS, rank=Rank.TWO),
    ]
    assert not validate_play(Card(suit=Suit.CLUBS, rank=Rank.TWO), hand, Suit.HEARTS)


# --- validate_bid ---

def test_valid_bid_non_dealer():
    assert validate_bid(3, 0, 3, 5, [], False)


def test_bid_out_of_range():
    assert not validate_bid(-1, 0, 3, 5, [], False)
    assert not validate_bid(6, 0, 3, 5, [], False)


def test_dealer_forbidden_bid():
    bids = [Bid(player_id="p1", amount=2), Bid(player_id="p2", amount=1)]
    # Dealer is index 2 (last of 3 players), 5 cards, total so far = 3, forbidden = 2
    assert not validate_bid(2, 2, 3, 5, bids, False)
    assert validate_bid(1, 2, 3, 5, bids, False)


def test_non_dealer_not_constrained_standard():
    bids = [Bid(player_id="p1", amount=3)]
    # Player index 1 is not dealer (index 2 is), so they can bid anything valid
    assert validate_bid(2, 1, 3, 5, bids, False)


# --- must-lose mode ---

def test_must_lose_first_player_constrained():
    # 5 cards, no bids yet, forbidden = 5 - 0 = 5
    assert not validate_bid(5, 0, 3, 5, [], True)
    assert validate_bid(4, 0, 3, 5, [], True)


def test_must_lose_middle_player_constrained():
    bids = [Bid(player_id="p1", amount=2)]
    # 5 cards, total = 2, forbidden = 3
    assert not validate_bid(3, 1, 3, 5, bids, True)
    assert validate_bid(2, 1, 3, 5, bids, True)


# --- get_forbidden_bid ---

def test_forbidden_bid_standard_non_dealer():
    assert get_forbidden_bid(0, 3, 5, [], False) is None


def test_forbidden_bid_standard_dealer():
    bids = [Bid(player_id="p1", amount=2), Bid(player_id="p2", amount=1)]
    assert get_forbidden_bid(2, 3, 5, bids, False) == 2


def test_forbidden_bid_must_lose():
    bids = [Bid(player_id="p1", amount=1)]
    assert get_forbidden_bid(1, 3, 5, bids, True) == 4
