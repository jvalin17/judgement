from __future__ import annotations

from typing import Dict, List, Optional, Callable

from backend.app.models import (
    Player, PlayerType, AIDifficulty, GameConfig, GamePhase,
)
from backend.app.models.events import GameEvent, EventType
from backend.app.models.session import SessionLog, RoundLog
from backend.app.game.engine import GameEngine
from backend.app.ai.base import AIStrategy, RoundContext
from backend.app.ai.easy import EasyAI
from backend.app.ai.medium import MediumAI
from backend.app.ai.hard import HardAI


STRATEGY_MAP = {
    AIDifficulty.EASY: EasyAI,
    AIDifficulty.MEDIUM: MediumAI,
    AIDifficulty.HARD: HardAI,
}


def _make_strategy(difficulty: AIDifficulty) -> AIStrategy:
    cls = STRATEGY_MAP.get(difficulty, EasyAI)
    return cls()


class GameSpeed:
    """Delays (seconds) between AI actions."""
    def __init__(self, after_card: float = 2.0, after_trick: float = 3.0, after_round: float = 1.5):
        self.after_card_played = after_card
        self.after_trick_complete = after_trick
        self.after_round_complete = after_round


class ManagedGame:
    """Wraps a GameEngine with AI dispatch and session logging."""

    def __init__(self, engine: GameEngine, speed: Optional[GameSpeed] = None):
        self.engine = engine
        self.speed = speed or GameSpeed()
        self.ai_strategies: Dict[str, AIStrategy] = {}
        self.session_log = SessionLog(game_id=engine.state.game_id)
        self._event_callbacks: List[Callable[[GameEvent], None]] = []

        engine.add_observer(self._on_event)

    # --- Event callback management ---

    def add_event_callback(self, callback: Callable[[GameEvent], None]) -> None:
        self._event_callbacks.append(callback)

    def remove_event_callback(self, callback: Callable[[GameEvent], None]) -> None:
        self._event_callbacks.remove(callback)

    # --- Event handling ---

    def _on_event(self, event: GameEvent) -> None:
        self._notify_callbacks(event)
        self._handle_logging(event)
        self._handle_ai_dispatch(event)

    def _notify_callbacks(self, event: GameEvent) -> None:
        for cb in self._event_callbacks:
            cb(event)

    def _handle_logging(self, event: GameEvent) -> None:
        if event.event_type == EventType.ROUND_COMPLETE:
            self._log_round(event)
        elif event.event_type == EventType.GAME_OVER:
            self._log_game_over(event)

    def _handle_ai_dispatch(self, event: GameEvent) -> None:
        if event.event_type == EventType.TURN_CHANGED:
            self._try_ai_turn()

    # --- AI turn dispatch ---

    def _try_ai_turn(self) -> None:
        pid = self.engine.state.current_player_id
        if not pid:
            return
        if not self._is_ai_player(pid):
            return
        strategy = self.ai_strategies.get(pid)
        if not strategy:
            return
        self._execute_ai_action(pid, strategy)

    def _is_ai_player(self, player_id: str) -> bool:
        player = self._find_player(player_id)
        return player is not None and player.player_type == PlayerType.AI

    def _find_player(self, player_id: str) -> Optional[Player]:
        return next(
            (player for player in self.engine.state.players if player.id == player_id),
            None,
        )

    def _execute_ai_action(self, pid: str, strategy: AIStrategy) -> None:
        ctx = self._build_context(pid)
        hand = self.engine.get_player_hand(pid)

        if self.engine.state.phase == GamePhase.BIDDING:
            valid_bids = self.engine.get_valid_bids(pid)
            bid = strategy.choose_bid(hand, valid_bids, ctx)
            self.engine.place_bid(pid, bid)
        elif self.engine.state.phase == GamePhase.PLAYING:
            valid_cards = self.engine.get_valid_cards(pid)
            card = strategy.choose_card(hand, valid_cards, ctx)
            self.engine.play_card(pid, card)

    # --- Context building ---

    def _build_context(self, player_id: str) -> RoundContext:
        return self.engine.get_round_context(player_id)

    # --- Session logging ---

    def _log_round(self, event: GameEvent) -> None:
        summary = self.engine.get_round_summary()
        if not summary:
            return
        self.session_log.rounds.append(RoundLog(
            round_number=summary["round_number"],
            num_cards=summary["num_cards"],
            trump_suit=summary["trump_suit"],
            dealer_id=summary["dealer_id"],
            bids=event.data.get("bids", []),
            tricks_won=summary["tricks_won"],
            scores=event.data.get("round_scores", {}),
        ))

    def _log_game_over(self, event: GameEvent) -> None:
        self.session_log.final_scores = event.data.get("final_scores", {})
        self.session_log.winners = event.data.get("winners", [])


class GameManager:
    """Registry of active games. Creates games and wires AI strategies."""

    def __init__(self):
        self._games: Dict[str, ManagedGame] = {}

    def create_game(self, config: GameConfig, players: List[Player], speed: Optional[GameSpeed] = None) -> ManagedGame:
        engine = GameEngine(config)
        managed = ManagedGame(engine, speed=speed)
        self._register_players(managed, players)
        self._initialize_session_log(managed, config, players)
        self._games[engine.state.game_id] = managed
        return managed

    def _register_players(self, managed: ManagedGame, players: List[Player]) -> None:
        for player in players:
            managed.engine.add_player(player)
            if self._needs_ai_strategy(player):
                managed.ai_strategies[player.id] = _make_strategy(player.ai_difficulty)

    def _needs_ai_strategy(self, player: Player) -> bool:
        return player.player_type == PlayerType.AI and player.ai_difficulty is not None

    def _initialize_session_log(
        self, managed: ManagedGame, config: GameConfig, players: List[Player]
    ) -> None:
        managed.session_log.players = [
            {"id": player.id, "name": player.name, "type": player.player_type.value}
            for player in players
        ]
        managed.session_log.variant = config.variant.value

    def get_game(self, game_id: str) -> Optional[ManagedGame]:
        return self._games.get(game_id)

    def remove_game(self, game_id: str) -> None:
        self._games.pop(game_id, None)

    def list_games(self) -> List[str]:
        return list(self._games.keys())
