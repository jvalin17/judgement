from __future__ import annotations

from typing import Callable
import uuid

from backend.app.models import (
    Player, GamePhase, GameConfig, GameFullState, Card,
    max_players_for_variant,
)
from backend.app.models.events import (
    EventType, GameEvent,
    game_started_event, round_started_event, cards_dealt_event,
    bid_placed_event, bidding_complete_event, card_played_event,
    trick_complete_event, round_complete_event, game_over_event,
    turn_changed_event, invalid_action_event,
)
from backend.app.ai.base import RoundContext
from backend.app.game.round_manager import RoundManager
from backend.app.game.round_config_loader import load_round_configs
from backend.app.game.validators import get_forbidden_bid, get_valid_cards as _get_valid_cards


class GameEngine:
    def __init__(self, config: GameConfig | None = None):
        self.state = GameFullState(
            game_id=str(uuid.uuid4()),
            config=config or GameConfig(),
        )
        self._round_manager: RoundManager | None = None
        self._round_configs: tuple = ()
        self._current_round_index: int = 0
        self._dealer_index: int = 0
        self._observers: list[Callable[[GameEvent], None]] = []

    # --- Observer pattern ---

    def add_observer(self, callback: Callable[[GameEvent], None]) -> None:
        self._observers.append(callback)

    def _emit(self, event: GameEvent) -> None:
        for observer in self._observers:
            observer(event)

    def _emit_turn(self) -> None:
        if self.state.current_player_id:
            self._emit(turn_changed_event(
                player_id=self.state.current_player_id,
                phase=self.state.phase.value,
            ))

    def _sync_current_player(self) -> None:
        if self._round_manager:
            self.state.current_player_id = self._round_manager.current_player_id

    # --- Player management ---

    def add_player(self, player: Player) -> bool:
        if not self._can_add_player(player):
            return False
        self.state.players.append(player)
        self.state.cumulative_scores[player.id] = 0
        return True

    def _can_add_player(self, player: Player) -> bool:
        if self.state.phase != GamePhase.LOBBY:
            return False
        max_p = max_players_for_variant(self.state.config.variant)
        if len(self.state.players) >= max_p:
            return False
        if any(existing.id == player.id for existing in self.state.players):
            return False
        return True

    # --- Game lifecycle ---

    def start_game(self) -> bool:
        if not self._can_start():
            return False
        self._initialize_game()
        self._start_round()
        return True

    def _can_start(self) -> bool:
        return (
            self.state.phase == GamePhase.LOBBY
            and len(self.state.players) >= 2
        )

    def _initialize_game(self) -> None:
        self._round_configs = load_round_configs(self.state.config.variant)
        self._current_round_index = 0
        self._dealer_index = 0
        self._emit(game_started_event(
            players=[player.model_dump() for player in self.state.players],
            variant=self.state.config.variant.value,
        ))

    # --- Round lifecycle ---

    def _start_round(self) -> None:
        self._create_round_manager()
        self._emit_round_started()
        self._deal_hands_to_players()
        self._sync_current_player()
        self._emit_turn()

    def _create_round_manager(self) -> None:
        config = self._round_configs[self._current_round_index]
        self._round_manager = RoundManager(
            round_number=config.round,
            num_cards=config.cards,
            trump_suit=config.trump,
            players=self.state.players,
            dealer_index=self._dealer_index,
            must_lose_mode=self.state.config.must_lose_mode,
        )
        self.state.current_round = self._round_manager.state
        self.state.phase = GamePhase.BIDDING

    def _emit_round_started(self) -> None:
        rm = self._round_manager
        self._emit(round_started_event(
            round_number=rm.state.round_number,
            num_cards=rm.num_cards,
            trump_suit=rm.state.trump_suit.value,
            dealer_id=rm.state.dealer_id,
        ))

    def _deal_hands_to_players(self) -> None:
        for player in self.state.players:
            hand = self._round_manager.state.hands.get(player.id, [])
            self._emit(cards_dealt_event(
                hand=[card.model_dump() for card in hand],
                player_id=player.id,
            ))

    def _end_round(self) -> None:
        self._score_round()
        self._emit_round_complete()
        # Do NOT auto-advance. Wait for continue_game() to be called
        # so the frontend can show the scoreboard first.

    def continue_game(self) -> bool:
        """Advance from ROUND_OVER to the next round (or game over).

        Called by the transport layer after the client acknowledges the scoreboard.
        """
        if self.state.phase != GamePhase.ROUND_OVER:
            return False
        self._advance_to_next_round()
        return True

    def _score_round(self) -> None:
        scores = self._round_manager.calculate_scores()
        for pid, score in scores.items():
            self.state.cumulative_scores[pid] = (
                self.state.cumulative_scores.get(pid, 0) + score
            )
        self.state.phase = GamePhase.ROUND_OVER

    def _emit_round_complete(self) -> None:
        rm = self._round_manager
        self._emit(round_complete_event(
            round_scores=dict(rm.state.scores),
            cumulative_scores=dict(self.state.cumulative_scores),
            tricks_won=dict(rm.state.tricks_won),
            bids=[bid.model_dump() for bid in rm.state.bids],
        ))

    def _advance_to_next_round(self) -> None:
        self._current_round_index += 1
        self._dealer_index = (self._dealer_index + 1) % len(self.state.players)
        if self._current_round_index >= len(self._round_configs):
            self._end_game()
        else:
            self._start_round()

    def _end_game(self) -> None:
        winners = self._determine_winners()
        self.state.phase = GamePhase.GAME_OVER
        self.state.current_player_id = None
        self._emit(game_over_event(
            final_scores=dict(self.state.cumulative_scores),
            winners=winners,
        ))

    def _determine_winners(self) -> list[str]:
        max_score = max(self.state.cumulative_scores.values())
        return [
            pid for pid, score in self.state.cumulative_scores.items()
            if score == max_score
        ]

    # --- Player actions ---

    def place_bid(self, player_id: str, amount: int) -> bool:
        if not self._is_bidding_phase():
            return False
        if not self._round_manager.place_bid(player_id, amount):
            self._emit_invalid_action(player_id, "Invalid bid")
            return False
        self._emit_bid_placed(player_id, amount)
        self._check_bidding_complete()
        self._sync_current_player()
        self._emit_turn()
        return True

    def _is_bidding_phase(self) -> bool:
        return self.state.phase == GamePhase.BIDDING and self._round_manager is not None

    def _emit_bid_placed(self, player_id: str, amount: int) -> None:
        self._emit(bid_placed_event(player_id=player_id, amount=amount))

    def _check_bidding_complete(self) -> None:
        if self._round_manager.bidding_complete:
            self.state.phase = GamePhase.PLAYING
            self._emit(bidding_complete_event(
                bids=[bid.model_dump() for bid in self._round_manager.state.bids],
            ))

    def play_card(self, player_id: str, card: Card) -> bool:
        if not self._is_playing_phase():
            return False
        if not self._round_manager.play_card(player_id, card):
            self._emit_invalid_action(player_id, "Invalid card play")
            return False
        self._emit_card_played(player_id, card)
        self._check_trick_complete()
        return True

    def _is_playing_phase(self) -> bool:
        return self.state.phase == GamePhase.PLAYING and self._round_manager is not None

    def _emit_card_played(self, player_id: str, card: Card) -> None:
        self._emit(card_played_event(player_id=player_id, card=card.model_dump()))

    def _check_trick_complete(self) -> None:
        winner_id = self._round_manager.try_resolve_trick()
        if winner_id:
            self._emit_trick_complete(winner_id)
            if self._round_manager.round_complete:
                self._end_round()
                return
        self._sync_current_player()
        self._emit_turn()

    def _emit_trick_complete(self, winner_id: str) -> None:
        self._emit(trick_complete_event(
            winner_id=winner_id,
            tricks_won=dict(self._round_manager.state.tricks_won),
        ))

    def _emit_invalid_action(self, player_id: str, reason: str) -> None:
        self._emit(invalid_action_event(reason=reason, player_id=player_id))

    # --- Query methods ---

    def get_player_hand(self, player_id: str) -> list[Card]:
        if not self._round_manager:
            return []
        return list(self._round_manager.state.hands.get(player_id, []))

    def get_valid_bids(self, player_id: str) -> list[int]:
        if not self._is_bidding_phase():
            return []
        if self._round_manager.current_bidder_id != player_id:
            return []
        return self._compute_valid_bids()

    def _compute_valid_bids(self) -> list[int]:
        rm = self._round_manager
        forbidden = get_forbidden_bid(
            len(rm.state.bids),
            len(self.state.players),
            rm.num_cards,
            rm.state.bids,
            self.state.config.must_lose_mode,
        )
        return [
            bid_amount for bid_amount in range(rm.num_cards + 1)
            if forbidden is None or bid_amount != forbidden
        ]

    def get_valid_cards(self, player_id: str) -> list[Card]:
        if not self._is_playing_phase():
            return []
        hand = self._round_manager.state.hands.get(player_id, [])
        lead_suit = self._round_manager.state.current_trick.lead_suit
        return _get_valid_cards(hand, lead_suit)

    def get_round_context(self, player_id: str) -> RoundContext:
        """Build an AI-visible context for the current round."""
        rm = self._round_manager
        if not rm:
            return RoundContext(
                player_id=player_id,
                trump_suit=None, num_cards=0, num_players=0,
                bids=[], tricks_won={}, cards_played=[], current_trick_cards=[],
            )
        completed_cards = [
            play.card for trick in rm.state.tricks for play in trick.plays
        ]
        current_cards = [play.card for play in rm.state.current_trick.plays]
        trick_history = [
            list(trick.plays) for trick in rm.state.tricks
        ]
        current_trick_plays = list(rm.state.current_trick.plays)
        return RoundContext(
            player_id=player_id,
            trump_suit=rm.state.trump_suit,
            num_cards=rm.num_cards,
            num_players=len(self.state.players),
            bids=list(rm.state.bids),
            tricks_won=dict(rm.state.tricks_won),
            cards_played=completed_cards + current_cards,
            current_trick_cards=current_cards,
            trick_history=trick_history,
            current_trick_plays=current_trick_plays,
            play_order=list(rm.play_order),
            cumulative_scores=dict(self.state.cumulative_scores),
            round_number=rm.state.round_number,
            total_rounds=len(self._round_configs),
        )

    def get_round_summary(self) -> dict:
        """Return round state for WebSocket/logging consumers."""
        rm = self._round_manager
        if not rm:
            return {}
        return {
            "round_number": rm.state.round_number,
            "num_cards": rm.num_cards,
            "trump_suit": rm.state.trump_suit.value,
            "dealer_id": rm.state.dealer_id,
            "bids": [bid.model_dump() for bid in rm.state.bids],
            "current_trick": [play.model_dump() for play in rm.state.current_trick.plays],
            "tricks_won": dict(rm.state.tricks_won),
        }
