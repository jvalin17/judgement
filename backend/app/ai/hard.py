from __future__ import annotations

from typing import List, Set

from backend.app.models import Card, Suit, Rank
from backend.app.ai.base import AIStrategy, RoundContext
from backend.app.ai.hand_evaluator import evaluate_hand
from backend.app.ai.card_play import would_win, best_winning_card, dump_lowest


class HardAI(AIStrategy):

    def __init__(self):
        self._cards_played: Set[Card] = set()

    def choose_bid(
        self,
        hand: List[Card],
        valid_bids: List[int],
        context: RoundContext,
    ) -> int:
        self._cards_played = set(context.cards_played)
        evaluation = evaluate_hand(hand, context.trump_suit)

        target = self._refined_estimate(hand, context, evaluation)
        target = max(0, min(target, context.num_cards))

        if target in valid_bids:
            return target
        return min(valid_bids, key=lambda bid: abs(bid - target))

    def choose_card(
        self,
        hand: List[Card],
        valid_cards: List[Card],
        context: RoundContext,
    ) -> Card:
        self._cards_played = set(context.cards_played)
        trick_cards = context.current_trick_cards
        trump = context.trump_suit

        my_bid = self._get_my_bid(context)
        my_tricks = context.tricks_won.get(context.player_id, 0)
        tricks_needed = my_bid - my_tricks if my_bid is not None else 0

        if not trick_cards:
            return self._choose_lead(valid_cards, trump, tricks_needed)

        lead_suit = trick_cards[0].suit

        if tricks_needed <= 0:
            return self._try_to_lose(valid_cards, trick_cards, lead_suit, trump)

        winning_card = best_winning_card(valid_cards, trick_cards, lead_suit, trump)
        if winning_card:
            return winning_card

        return dump_lowest(valid_cards, trump)

    def _refined_estimate(self, hand: List[Card], context: RoundContext, evaluation) -> int:
        tricks = 0.0
        for card in hand:
            if card.suit == context.trump_suit:
                outstanding = self._count_outstanding_higher(card, context.trump_suit)
                if outstanding == 0:
                    tricks += 0.95
                elif outstanding <= 1:
                    tricks += 0.65
                elif outstanding <= 2:
                    tricks += 0.35
                else:
                    tricks += 0.15
            else:
                if card.rank == Rank.ACE:
                    suit_count = evaluation.suit_distribution.get(card.suit, 0)
                    tricks += 0.85 if suit_count <= 3 else 0.65
                elif card.rank == Rank.KING:
                    outstanding_aces = self._count_outstanding_specific(card.suit, Rank.ACE)
                    tricks += 0.5 if outstanding_aces == 0 else 0.3
        return round(tricks)

    def _count_outstanding_higher(self, card: Card, suit: Suit) -> int:
        count = 0
        for rank in Rank:
            if rank > card.rank:
                candidate = Card(suit=suit, rank=rank)
                if candidate not in self._cards_played:
                    count += 1
        return count

    def _count_outstanding_specific(self, suit: Suit, rank: Rank) -> int:
        card = Card(suit=suit, rank=rank)
        return 0 if card in self._cards_played else 1

    def _get_my_bid(self, context: RoundContext) -> int | None:
        for bid in context.bids:
            if bid.player_id == context.player_id:
                return bid.amount
        return None

    def _choose_lead(self, valid_cards: List[Card], trump: Suit, tricks_needed: int) -> Card:
        if tricks_needed <= 0:
            return dump_lowest(valid_cards, trump)

        # Lead with guaranteed winners (no outstanding higher cards)
        for card in sorted(valid_cards, key=lambda card: -card.rank):
            if card.suit != trump:
                if self._count_outstanding_higher(card, card.suit) == 0:
                    return card

        # Lead dominant trump
        trump_cards = [card for card in valid_cards if card.suit == trump]
        if trump_cards:
            best_trump = max(trump_cards, key=lambda card: card.rank)
            if self._count_outstanding_higher(best_trump, trump) == 0:
                return best_trump

        # Lead highest non-trump
        non_trump = [card for card in valid_cards if card.suit != trump]
        if non_trump:
            return max(non_trump, key=lambda card: card.rank)
        return min(valid_cards, key=lambda card: card.rank)

    def _try_to_lose(
        self,
        valid_cards: List[Card],
        trick_cards: List[Card],
        lead_suit: Suit,
        trump: Suit,
    ) -> Card:
        losers = [card for card in valid_cards if not would_win(card, trick_cards, lead_suit, trump)]
        if losers:
            return max(losers, key=lambda card: card.rank)
        return min(valid_cards, key=lambda card: card.rank)
