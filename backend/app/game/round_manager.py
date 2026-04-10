from __future__ import annotations

from backend.app.models import (
    Card, Suit, Bid, TrickPlay, Trick, RoundState, Player,
)
from backend.app.game.deck import create_deck, shuffle_deck, deal
from backend.app.game.trick_resolver import resolve_trick
from backend.app.game.scorer import score_round
from backend.app.game.validators import get_valid_cards, validate_play, validate_bid


class RoundManager:
    def __init__(
        self,
        round_number: int,
        num_cards: int,
        trump_suit: Suit,
        players: list[Player],
        dealer_index: int,
        must_lose_mode: bool,
    ):
        self.players = players
        self.num_cards = num_cards
        self.dealer_index = dealer_index
        self.must_lose_mode = must_lose_mode

        player_order = self._build_player_order(dealer_index)
        hands = self._deal_hands(player_order)

        self.bid_order = player_order
        self.play_order = list(player_order)

        self.state = RoundState(
            round_number=round_number,
            num_cards=num_cards,
            trump_suit=trump_suit,
            dealer_id=players[dealer_index].id,
            hands=hands,
            tricks_won={player.id: 0 for player in players},
        )

    # --- Setup helpers ---

    def _build_player_order(self, dealer_index: int) -> list[str]:
        """Build clockwise order starting from left of dealer."""
        first_seat = (dealer_index + 1) % len(self.players)
        return [
            self.players[(first_seat + offset) % len(self.players)].id
            for offset in range(len(self.players))
        ]

    def _deal_hands(self, player_order: list[str]) -> dict[str, list[Card]]:
        deck = shuffle_deck(create_deck())
        hands_list = deal(deck, len(self.players), self.num_cards)
        return {player_id: hands_list[index] for index, player_id in enumerate(player_order)}

    # --- State queries ---

    @property
    def bidding_complete(self) -> bool:
        return len(self.state.bids) == len(self.players)

    @property
    def round_complete(self) -> bool:
        return len(self.state.tricks) == self.num_cards

    @property
    def current_bidder_id(self) -> str | None:
        if self.bidding_complete:
            return None
        return self.bid_order[len(self.state.bids)]

    @property
    def current_player_id(self) -> str | None:
        if not self.bidding_complete:
            return self.current_bidder_id
        if self.round_complete:
            return None
        return self._current_trick_player_id()

    def _current_trick_player_id(self) -> str | None:
        num_plays = len(self.state.current_trick.plays)
        if num_plays >= len(self.players):
            return None
        return self.play_order[num_plays]

    # --- Actions ---

    def place_bid(self, player_id: str, amount: int) -> bool:
        if not self._is_valid_bidder(player_id):
            return False
        if not self._is_valid_bid_amount(amount):
            return False
        self.state.bids.append(Bid(player_id=player_id, amount=amount))
        return True

    def _is_valid_bidder(self, player_id: str) -> bool:
        return player_id == self.current_bidder_id

    def _is_valid_bid_amount(self, amount: int) -> bool:
        bid_index = len(self.state.bids)
        return validate_bid(
            amount, bid_index, len(self.players),
            self.num_cards, self.state.bids, self.must_lose_mode,
        )

    def play_card(self, player_id: str, card: Card) -> bool:
        if not self._is_valid_player(player_id):
            return False
        if not self._is_valid_card_play(player_id, card):
            return False
        self._record_card_play(player_id, card)
        return True

    def _is_valid_player(self, player_id: str) -> bool:
        return self.current_player_id == player_id

    def _is_valid_card_play(self, player_id: str, card: Card) -> bool:
        hand = self.state.hands.get(player_id, [])
        lead_suit = self.state.current_trick.lead_suit
        return validate_play(card, hand, lead_suit)

    def _record_card_play(self, player_id: str, card: Card) -> None:
        if not self.state.current_trick.plays:
            self.state.current_trick.lead_suit = card.suit
        self.state.current_trick.plays.append(
            TrickPlay(player_id=player_id, card=card)
        )
        self.state.hands[player_id].remove(card)

    # --- Trick resolution ---

    def try_resolve_trick(self) -> str | None:
        if not self._is_trick_complete():
            return None
        winner_id = self._resolve_current_trick()
        self._archive_trick(winner_id)
        self._set_next_lead(winner_id)
        return winner_id

    def _is_trick_complete(self) -> bool:
        return len(self.state.current_trick.plays) >= len(self.players)

    def _resolve_current_trick(self) -> str:
        return resolve_trick(self.state.current_trick, self.state.trump_suit)

    def _archive_trick(self, winner_id: str) -> None:
        self.state.current_trick.winner_id = winner_id
        self.state.tricks_won[winner_id] = self.state.tricks_won.get(winner_id, 0) + 1
        self.state.tricks.append(self.state.current_trick)
        self.state.current_trick = Trick()

    def _set_next_lead(self, winner_id: str) -> None:
        winner_seat = next(
            index for index, player in enumerate(self.players) if player.id == winner_id
        )
        self.play_order = [
            self.players[(winner_seat + offset) % len(self.players)].id
            for offset in range(len(self.players))
        ]

    # --- Scoring ---

    def calculate_scores(self) -> dict[str, int]:
        scores = score_round(self.state.bids, self.state.tricks_won)
        self.state.scores = scores
        return scores
