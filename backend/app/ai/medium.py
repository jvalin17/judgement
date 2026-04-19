from __future__ import annotations

from typing import List

from backend.app.models import Card, Suit, Rank
from backend.app.ai.base import AIStrategy, RoundContext
from backend.app.ai.hand_evaluator import evaluate_hand
from backend.app.ai.card_play import best_winning_card, dump_lowest


class MediumAI(AIStrategy):

    strategy_type = "medium"

    def choose_bid(
        self,
        hand: List[Card],
        valid_bids: List[int],
        context: RoundContext,
    ) -> int:
        evaluation = evaluate_hand(hand, context.trump_suit)
        target = round(evaluation.estimated_tricks)
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
        trick_cards = context.current_trick_cards
        trump = context.trump_suit

        if not trick_cards:
            return self._choose_lead(valid_cards, trump)

        lead_suit = trick_cards[0].suit

        winning_card = best_winning_card(valid_cards, trick_cards, lead_suit, trump)
        if winning_card:
            return winning_card

        return dump_lowest(valid_cards, trump)

    def _choose_lead(self, valid_cards: List[Card], trump: Suit) -> Card:
        non_trump_high = [
            card for card in valid_cards
            if card.suit != trump and card.rank >= Rank.QUEEN
        ]
        if non_trump_high:
            return max(non_trump_high, key=lambda card: card.rank)

        non_trump = [card for card in valid_cards if card.suit != trump]
        if non_trump:
            return min(non_trump, key=lambda card: card.rank)

        return min(valid_cards, key=lambda card: card.rank)
