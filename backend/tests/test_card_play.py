"""Tests for shared AI card-play helpers.

These functions are used by MediumAI and HardAI — correctness bugs here
affect all non-trivial AI decision-making.
"""

from backend.app.models import Card, Suit, Rank
from backend.app.ai.card_play import would_win, best_winning_card, dump_lowest


# ---- would_win ----

class TestWouldWin:
    def test_trump_beats_lead_suit(self):
        trick = [Card(suit=Suit.HEARTS, rank=Rank.ACE)]
        card = Card(suit=Suit.SPADES, rank=Rank.TWO)
        assert would_win(card, trick, lead_suit=Suit.HEARTS, trump=Suit.SPADES)

    def test_higher_trump_beats_lower_trump(self):
        trick = [Card(suit=Suit.SPADES, rank=Rank.FIVE)]
        card = Card(suit=Suit.SPADES, rank=Rank.SIX)
        assert would_win(card, trick, lead_suit=Suit.HEARTS, trump=Suit.SPADES)

    def test_lower_trump_loses_to_higher_trump(self):
        trick = [Card(suit=Suit.SPADES, rank=Rank.KING)]
        card = Card(suit=Suit.SPADES, rank=Rank.TWO)
        assert not would_win(card, trick, lead_suit=Suit.HEARTS, trump=Suit.SPADES)

    def test_lead_suit_beats_lower_lead_suit(self):
        trick = [Card(suit=Suit.HEARTS, rank=Rank.FIVE)]
        card = Card(suit=Suit.HEARTS, rank=Rank.ACE)
        assert would_win(card, trick, lead_suit=Suit.HEARTS, trump=Suit.SPADES)

    def test_lead_suit_loses_to_trump_in_trick(self):
        trick = [Card(suit=Suit.SPADES, rank=Rank.TWO)]
        card = Card(suit=Suit.HEARTS, rank=Rank.ACE)
        assert not would_win(card, trick, lead_suit=Suit.HEARTS, trump=Suit.SPADES)

    def test_off_suit_never_wins(self):
        trick = [Card(suit=Suit.HEARTS, rank=Rank.TWO)]
        card = Card(suit=Suit.DIAMONDS, rank=Rank.ACE)
        assert not would_win(card, trick, lead_suit=Suit.HEARTS, trump=Suit.SPADES)

    def test_trump_wins_against_multiple_lead_cards(self):
        trick = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.HEARTS, rank=Rank.KING),
        ]
        card = Card(suit=Suit.SPADES, rank=Rank.TWO)
        assert would_win(card, trick, lead_suit=Suit.HEARTS, trump=Suit.SPADES)

    def test_lead_suit_lower_than_best_loses(self):
        trick = [Card(suit=Suit.HEARTS, rank=Rank.KING)]
        card = Card(suit=Suit.HEARTS, rank=Rank.QUEEN)
        assert not would_win(card, trick, lead_suit=Suit.HEARTS, trump=Suit.SPADES)


# ---- best_winning_card ----

class TestBestWinningCard:
    def test_returns_none_when_no_winner(self):
        trick = [Card(suit=Suit.SPADES, rank=Rank.ACE)]
        valid = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.DIAMONDS, rank=Rank.KING),
        ]
        result = best_winning_card(valid, trick, lead_suit=Suit.SPADES, trump=Suit.SPADES)
        assert result is None

    def test_prefers_lead_suit_over_trump(self):
        trick = [Card(suit=Suit.HEARTS, rank=Rank.FIVE)]
        valid = [
            Card(suit=Suit.HEARTS, rank=Rank.KING),
            Card(suit=Suit.SPADES, rank=Rank.TWO),  # trump
        ]
        result = best_winning_card(valid, trick, lead_suit=Suit.HEARTS, trump=Suit.SPADES)
        assert result.suit == Suit.HEARTS

    def test_picks_lowest_winner(self):
        trick = [Card(suit=Suit.HEARTS, rank=Rank.FIVE)]
        valid = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.HEARTS, rank=Rank.SIX),
            Card(suit=Suit.HEARTS, rank=Rank.KING),
        ]
        result = best_winning_card(valid, trick, lead_suit=Suit.HEARTS, trump=Suit.SPADES)
        assert result.rank == Rank.SIX

    def test_picks_lowest_trump_when_only_trumps_win(self):
        trick = [Card(suit=Suit.HEARTS, rank=Rank.ACE)]
        valid = [
            Card(suit=Suit.SPADES, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.TWO),
        ]
        result = best_winning_card(valid, trick, lead_suit=Suit.HEARTS, trump=Suit.SPADES)
        assert result.rank == Rank.TWO


# ---- dump_lowest ----

class TestDumpLowest:
    def test_prefers_non_trump(self):
        trump = Suit.SPADES
        cards = [
            Card(suit=Suit.SPADES, rank=Rank.TWO),
            Card(suit=Suit.HEARTS, rank=Rank.THREE),
        ]
        result = dump_lowest(cards, trump)
        assert result.suit == Suit.HEARTS

    def test_dumps_lowest_non_trump(self):
        trump = Suit.SPADES
        cards = [
            Card(suit=Suit.HEARTS, rank=Rank.KING),
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
            Card(suit=Suit.DIAMONDS, rank=Rank.FIVE),
        ]
        result = dump_lowest(cards, trump)
        assert result == Card(suit=Suit.HEARTS, rank=Rank.TWO)

    def test_dumps_lowest_trump_when_all_trump(self):
        trump = Suit.SPADES
        cards = [
            Card(suit=Suit.SPADES, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.THREE),
            Card(suit=Suit.SPADES, rank=Rank.KING),
        ]
        result = dump_lowest(cards, trump)
        assert result.rank == Rank.THREE
