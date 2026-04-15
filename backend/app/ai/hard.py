from __future__ import annotations

from typing import List, Optional, Set

from backend.app.models import Card, Suit, Rank
from backend.app.ai.base import AIStrategy, RoundContext
from backend.app.ai.hand_evaluator import evaluate_hand
from backend.app.ai.card_play import would_win, best_winning_card, dump_lowest, lowest_winning_trump
from backend.app.ai.personality import AIPersonality, random_personality
from backend.app.ai.opponent_model import OpponentModel


class HardAI(AIStrategy):

    def __init__(self, personality: Optional[AIPersonality] = None):
        self._cards_played: Set[Card] = set()
        self._personality = personality or random_personality()
        self._opponent_model: Optional[OpponentModel] = None

    # --- Public API ---

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
        self._opponent_model = OpponentModel(
            player_id=context.player_id,
            trick_history=context.trick_history,
            current_trick_plays=context.current_trick_plays,
            bids=context.bids,
            tricks_won=context.tricks_won,
            trump_suit=context.trump_suit,
        )
        trick_cards = context.current_trick_cards
        trump = context.trump_suit

        my_bid = self._get_my_bid(context)
        my_tricks = context.tricks_won.get(context.player_id, 0)
        tricks_needed = my_bid - my_tricks if my_bid is not None else 0
        cards_remaining = len(hand)
        is_endgame = cards_remaining <= 3

        if not trick_cards:
            return self._choose_lead(valid_cards, hand, trump, tricks_needed, cards_remaining, context)

        lead_suit = trick_cards[0].suit
        position = len(trick_cards)
        is_last = position >= context.num_players - 1

        if tricks_needed <= 0:
            return self._try_to_lose_smart(valid_cards, trick_cards, lead_suit, trump, is_last, is_endgame)

        if is_last:
            return self._choose_last(valid_cards, trick_cards, lead_suit, trump, tricks_needed, is_endgame)

        return self._choose_middle(valid_cards, trick_cards, lead_suit, trump, tricks_needed, cards_remaining)

    # --- Bid estimation ---

    def _refined_estimate(self, hand: List[Card], context: RoundContext, evaluation) -> int:
        tricks = 0.0
        trump = context.trump_suit
        trump_count = sum(1 for card in hand if card.suit == trump)

        for card in hand:
            if card.suit == trump:
                outstanding = self._count_outstanding_higher(card, trump)
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

        # Ruffing potential: void in a suit + trumps to ruff with
        for suit in Suit:
            if suit != trump and evaluation.suit_distribution.get(suit, 0) == 0:
                if trump_count >= 2:
                    tricks += 0.5
                elif trump_count >= 1:
                    tricks += 0.3

        # Position-aware: check if opponents are over/under-bidding
        total_bids = sum(bid.amount for bid in context.bids)
        if total_bids > context.num_cards:
            tricks -= 0.3  # opponents over-bid, be conservative
        elif total_bids < context.num_cards * 0.6 and len(context.bids) > 1:
            tricks += 0.2  # opponents under-bid, be slightly aggressive

        # Personality influence
        tricks += (self._personality.aggression - 0.5) * 0.5

        # Small hand penalty: with 1-3 cards, non-ace non-trump is very risky
        if context.num_cards <= 3:
            for card in hand:
                if card.suit != trump and card.rank != Rank.ACE:
                    tricks -= 0.1

        return round(tricks)

    # --- Leading ---

    def _choose_lead(
        self,
        valid_cards: List[Card],
        hand: List[Card],
        trump: Suit,
        tricks_needed: int,
        cards_remaining: int,
        context: RoundContext,
    ) -> Card:
        if tricks_needed <= 0:
            return self._lead_to_lose(valid_cards, trump)

        trump_cards = [card for card in valid_cards if card.suit == trump]
        non_trump = [card for card in valid_cards if card.suit != trump]

        # 1. Guaranteed non-trump winners (Ace with nothing higher outstanding)
        guaranteed_winners = []
        for card in sorted(non_trump, key=lambda card: -card.rank):
            if self._count_outstanding_higher(card, card.suit) == 0:
                guaranteed_winners.append(card)
        if guaranteed_winners:
            return guaranteed_winners[0]

        # 2. Trump lead to draw out opponents' trumps
        if self._should_lead_trump(trump_cards, trump, tricks_needed, cards_remaining):
            # Lead LOW trump to force opponents to spend their high trumps
            return min(trump_cards, key=lambda card: card.rank)

        # 3. Guaranteed trump winner — but conserve if personality says so
        if trump_cards:
            best_trump = max(trump_cards, key=lambda card: card.rank)
            if self._count_outstanding_higher(best_trump, trump) == 0:
                # With high trump conservation and other options, save trump for later
                if self._personality.trump_conservation > 0.7 and non_trump and tricks_needed > 1:
                    pass  # skip to non-trump fallback
                else:
                    return best_trump

        # 4. Short suit lead to create void for future ruffing
        if non_trump and trump_cards and cards_remaining > 2:
            suit_counts = {}
            for card in hand:
                if card.suit != trump:
                    suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1
            short_suit_cards = [
                card for card in non_trump
                if suit_counts.get(card.suit, 0) <= 2
            ]
            if short_suit_cards:
                return min(short_suit_cards, key=lambda card: card.rank)

        # 5. Fallback: highest non-trump, or lowest trump
        if non_trump:
            return max(non_trump, key=lambda card: card.rank)
        return min(valid_cards, key=lambda card: card.rank)

    def _lead_to_lose(self, valid_cards: List[Card], trump: Suit) -> Card:
        """Lead a card most likely to lose the trick."""
        non_trump = [card for card in valid_cards if card.suit != trump]
        if non_trump:
            # Lead lowest non-trump from longest suit (harder for opponents to void)
            suit_counts = {}
            for card in non_trump:
                suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1
            return min(non_trump, key=lambda card: (card.rank, -suit_counts.get(card.suit, 0)))
        return min(valid_cards, key=lambda card: card.rank)

    def _should_lead_trump(
        self,
        my_trumps: List[Card],
        trump: Suit,
        tricks_needed: int,
        cards_remaining: int,
    ) -> bool:
        """Decide whether to lead trump to draw out opponents' trumps."""
        if len(my_trumps) < 2 or tricks_needed <= 0:
            return False

        remaining_trumps = self._count_remaining_trumps(trump, my_trumps)

        # If we have more trumps than are outstanding, we have trump control
        # Lead low trump to strip opponents' trumps, then cash high ones later
        if len(my_trumps) > remaining_trumps and cards_remaining > 2:
            return True

        # With high aggression, lead trump more often when we have length
        if self._personality.aggression > 0.7 and len(my_trumps) >= 3:
            return True

        return False

    # --- Last position (perfect information) ---

    def _choose_last(
        self,
        valid_cards: List[Card],
        trick_cards: List[Card],
        lead_suit: Suit,
        trump: Suit,
        tricks_needed: int,
        is_endgame: bool,
    ) -> Card:
        # Playing last — we know exactly what beats what
        winners = [card for card in valid_cards if would_win(card, trick_cards, lead_suit, trump)]

        if winners and tricks_needed > 0:
            # Take with the cheapest winner — save strong cards for later
            return min(winners, key=lambda card: (0 if card.suit == lead_suit else 1, card.rank))

        if not winners:
            return self._dump_strategically(valid_cards, trump)

        # We can win but don't need to — dump instead
        return self._dump_strategically(valid_cards, trump)

    # --- Middle position (opponents still to play after us) ---

    def _choose_middle(
        self,
        valid_cards: List[Card],
        trick_cards: List[Card],
        lead_suit: Suit,
        trump: Suit,
        tricks_needed: int,
        cards_remaining: int,
    ) -> Card:
        winners = [card for card in valid_cards if would_win(card, trick_cards, lead_suit, trump)]

        if not winners:
            return self._dump_strategically(valid_cards, trump)

        # Guaranteed winner: no outstanding higher cards can beat us
        guaranteed = []
        for card in winners:
            effective_suit = trump if card.suit == trump else lead_suit
            if self._count_outstanding_higher(card, effective_suit) == 0:
                guaranteed.append(card)

        if guaranteed:
            return min(guaranteed, key=lambda card: (0 if card.suit == lead_suit else 1, card.rank))

        # Marginal winner: personality decides
        if self._personality.risk_tolerance > 0.6 or cards_remaining <= 2:
            # Risk-tolerant or endgame: play the cheapest winner and hope
            return min(winners, key=lambda card: (0 if card.suit == lead_suit else 1, card.rank))

        # Conservative: trump conservation — don't waste trump on uncertain tricks
        non_trump_winners = [card for card in winners if card.suit != lead_suit and card.suit != trump]
        suit_winners = [card for card in winners if card.suit == lead_suit]

        if suit_winners:
            return min(suit_winners, key=lambda card: card.rank)
        if non_trump_winners:
            return min(non_trump_winners, key=lambda card: card.rank)

        # Only trump winners available
        if self._personality.trump_conservation > 0.7 and tricks_needed > 1:
            # Save trump for later tricks
            return self._dump_strategically(valid_cards, trump)

        return min(winners, key=lambda card: card.rank)

    # --- Smart losing ---

    def _try_to_lose_smart(
        self,
        valid_cards: List[Card],
        trick_cards: List[Card],
        lead_suit: Suit,
        trump: Suit,
        is_last: bool,
        is_endgame: bool,
    ) -> Card:
        losers = [card for card in valid_cards if not would_win(card, trick_cards, lead_suit, trump)]

        if losers:
            return self._pick_best_loser(losers, trump)

        # All cards win — play the lowest to minimize damage
        return min(valid_cards, key=lambda card: card.rank)

    def _pick_best_loser(self, losers: List[Card], trump: Suit) -> Card:
        """Choose the best card to play when trying to lose.

        Priority: void creation (dump from shortest suit) > shed high cards from long suits.
        """
        non_trump_losers = [card for card in losers if card.suit != trump]
        trump_losers = [card for card in losers if card.suit == trump]

        if non_trump_losers:
            # Dump from shortest non-trump suit to create voids for future ruffing
            suit_counts = {}
            for card in non_trump_losers:
                suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1

            min_suit_count = min(suit_counts.values())
            short_suit_losers = [
                card for card in non_trump_losers
                if suit_counts[card.suit] == min_suit_count
            ]
            # From the shortest suit, play the highest card (shed the most dangerous card)
            return max(short_suit_losers, key=lambda card: card.rank)

        # Only trump losers — play the highest (shed dangerous trump)
        return max(trump_losers, key=lambda card: card.rank)

    def _dump_strategically(self, valid_cards: List[Card], trump: Suit) -> Card:
        """Dump a card when we can't or don't want to win.

        Prefer voiding a short suit, then shedding high non-trumps, then lowest trump.
        """
        non_trump = [card for card in valid_cards if card.suit != trump]

        if non_trump:
            suit_counts = {}
            for card in non_trump:
                suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1

            # Dump from shortest suit (create voids), highest card first
            min_count = min(suit_counts.values())
            short_suit = [card for card in non_trump if suit_counts[card.suit] == min_count]
            return max(short_suit, key=lambda card: card.rank) if short_suit else min(non_trump, key=lambda card: card.rank)

        return min(valid_cards, key=lambda card: card.rank)

    # --- Card counting helpers ---

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

    def _count_remaining_trumps(self, trump: Suit, my_trumps: List[Card]) -> int:
        """Count trump cards still held by opponents (not played, not in our hand)."""
        count = 0
        my_trump_set = set(my_trumps)
        for rank in Rank:
            card = Card(suit=trump, rank=rank)
            if card not in self._cards_played and card not in my_trump_set:
                count += 1
        return count

    def _get_my_bid(self, context: RoundContext) -> Optional[int]:
        for bid in context.bids:
            if bid.player_id == context.player_id:
                return bid.amount
        return None
