from __future__ import annotations

import json
import logging
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

logger = logging.getLogger(__name__)

_STATS_FILE = os.path.join(os.path.dirname(__file__), "ml", "learning", "data", "player_stats.json")

from backend.app.models import (
    Player, PlayerType, AIDifficulty, GameConfig, GamePhase,
    max_players_for_variant,
)
from backend.app.models.events import (
    GameEvent, EventType, PersonaAward,
    player_joined_event, player_left_event, game_starting_event,
    game_over_event,
)
from backend.app.models.session import SessionLog, RoundLog
from backend.app.game.engine import GameEngine
from backend.app.ai.base import AIStrategy, RoundContext
from backend.app.ai.easy import EasyAI
from backend.app.ai.medium import MediumAI
from backend.app.ai.hard import HardAI
from backend.app.ai.smart_hard import SmartHardAI
from backend.app.ml.learning.decision_collector import DecisionCollector


STRATEGY_MAP = {
    AIDifficulty.EASY: EasyAI,
    AIDifficulty.MEDIUM: MediumAI,
    AIDifficulty.HARD: HardAI,
}

AI_SWEETS_NAMES = ("Gulab Jamun", "Jalebi", "Rasgulla", "Barfi", "Ladoo", "Kaju Katli")


def _make_strategy(difficulty: AIDifficulty, use_smart: bool = False) -> AIStrategy:
    if use_smart and difficulty == AIDifficulty.HARD:
        return SmartHardAI()
    cls = STRATEGY_MAP.get(difficulty, EasyAI)
    return cls()


_NERF_MAP: Dict[AIDifficulty, AIDifficulty] = {
    AIDifficulty.HARD: AIDifficulty.MEDIUM,
    AIDifficulty.MEDIUM: AIDifficulty.EASY,
}


def _load_game_count() -> int:
    try:
        with open(_STATS_FILE) as fh:
            return json.load(fh).get("game_count", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def _increment_game_count() -> int:
    count = _load_game_count() + 1
    os.makedirs(os.path.dirname(_STATS_FILE), exist_ok=True)
    with open(_STATS_FILE, "w") as fh:
        json.dump({"game_count": count}, fh)
    return count


def _should_nerf_ai() -> bool:
    """~25% chance, but never on the first 2 games (let the player learn)."""
    count = _increment_game_count()
    if count <= 2:
        return False
    return random.random() < 0.25


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
        self.host_player_id: Optional[str] = None
        self.is_public: bool = False
        self.created_at: datetime = datetime.utcnow()
        self._event_callbacks: List[Callable[[GameEvent], None]] = []
        self.decision_collector = DecisionCollector()

        engine.add_observer(self._on_event)

    # --- Event callback management ---

    def add_event_callback(self, callback: Callable[[GameEvent], None]) -> None:
        self._event_callbacks.append(callback)

    def remove_event_callback(self, callback: Callable[[GameEvent], None]) -> None:
        self._event_callbacks.remove(callback)

    # --- Event handling ---

    def _on_event(self, event: GameEvent) -> None:
        if event.event_type == EventType.GAME_OVER:
            self._handle_game_over(event)
            return
        self._notify_callbacks(event)
        self._handle_logging(event)
        self._handle_ai_dispatch(event)

    def _notify_callbacks(self, event: GameEvent) -> None:
        for cb in self._event_callbacks:
            cb(event)

    def _handle_game_over(self, event: GameEvent) -> None:
        """Handle GAME_OVER: log, compute personas, enrich event, then broadcast."""
        self._log_game_over(event)
        self._flush_winner_decisions(event)

        logger.info("GAME_OVER: winners=%s, computing personas for humans", event.data.get("winners"))
        logger.info("Session log has %d rounds", len(self.session_log.rounds))

        # Compute persona for each human player and send enriched per-player events
        for player in self.engine.state.players:
            persona_award = self._compute_persona(player.id) if player.player_type == PlayerType.HUMAN else None
            logger.info(
                "Player %s (%s): persona=%s",
                player.id, player.player_type.value,
                persona_award.persona_name if persona_award else "None",
            )
            enriched = game_over_event(
                final_scores=event.data.get("final_scores", {}),
                winners=event.data.get("winners", []),
                persona=persona_award,
            )
            enriched.player_id = player.id
            self._notify_callbacks(enriched)

    def _compute_persona(self, player_id: str) -> Optional[PersonaAward]:
        """Compute a persona award for a player. Returns None on failure."""
        try:
            from backend.app.ml.analysis.fingerprint import compute_fingerprint
            from backend.app.ml.analysis.persona_match import pick_persona

            player_traits = compute_fingerprint(self.session_log, player_id)
            logger.info("Fingerprint for %s: %s", player_id, player_traits)
            persona = pick_persona(player_traits)
            logger.info("Matched persona: %s (%s)", persona.name, persona.category)
            return PersonaAward(
                persona_id=persona.id,
                persona_name=persona.name,
                persona_category=persona.category,
                persona_tagline=persona.tagline,
                traits=persona.traits,
                player_traits=player_traits,
            )
        except Exception as exc:
            logger.error("Persona computation failed for %s: %s", player_id, exc, exc_info=True)
            return None

    def _handle_logging(self, event: GameEvent) -> None:
        if event.event_type == EventType.ROUND_COMPLETE:
            self._log_round(event)

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

    def _get_strategy_type(self, player_id: str) -> str:
        """Get a readable strategy type name for a player."""
        strategy = self.ai_strategies.get(player_id)
        if strategy is None:
            return "human"
        return strategy.strategy_type

    def _execute_ai_action(self, pid: str, strategy: AIStrategy) -> None:
        ctx = self._build_context(pid)
        hand = self.engine.get_player_hand(pid)
        strategy_type = self._get_strategy_type(pid)

        try:
            if self.engine.state.phase == GamePhase.BIDDING:
                valid_bids = self.engine.get_valid_bids(pid)
                bid = strategy.choose_bid(hand, valid_bids, ctx)
                self.decision_collector.record_bid(pid, hand, ctx, bid, strategy_type)
                self.engine.place_bid(pid, bid)
            elif self.engine.state.phase == GamePhase.PLAYING:
                valid_cards = self.engine.get_valid_cards(pid)
                card = strategy.choose_card(hand, valid_cards, ctx)
                self.decision_collector.record_play(pid, hand, valid_cards, ctx, card, strategy_type)
                self.engine.play_card(pid, card)
        except Exception:
            # Fallback: pick a random valid move so the game doesn't get stuck
            if self.engine.state.phase == GamePhase.BIDDING:
                valid_bids = self.engine.get_valid_bids(pid)
                if valid_bids:
                    self.engine.place_bid(pid, random.choice(valid_bids))
            elif self.engine.state.phase == GamePhase.PLAYING:
                valid_cards = self.engine.get_valid_cards(pid)
                if valid_cards:
                    self.engine.play_card(pid, random.choice(valid_cards))

    # --- Human decision recording ---

    def record_human_bid(self, player_id: str, bid_amount: int) -> None:
        """Record a human player's bid decision for learning.

        Must be called BEFORE engine.place_bid() so the hand state
        is still pre-action. Only uses the player's own hand and
        public game state — never accesses other players' cards.
        """
        hand = self.engine.get_player_hand(player_id)
        ctx = self._build_context(player_id)
        self.decision_collector.record_bid(player_id, hand, ctx, bid_amount, "human")

    def record_human_play(self, player_id: str, card: 'Card') -> None:
        """Record a human player's card-play decision for learning.

        Must be called BEFORE engine.play_card() so the hand state
        is still pre-action. Only uses the player's own hand and
        public game state — never accesses other players' cards.
        """
        hand = self.engine.get_player_hand(player_id)
        valid_cards = self.engine.get_valid_cards(player_id)
        ctx = self._build_context(player_id)
        self.decision_collector.record_play(player_id, hand, valid_cards, ctx, card, "human")

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

    def _flush_winner_decisions(self, event: GameEvent) -> None:
        winner_ids = event.data.get("winners", [])
        if winner_ids:
            self.decision_collector.flush_winner(winner_ids)


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
        # Pick one random Hard AI bot to use the ML strategy
        hard_ai_players = [
            player for player in players
            if self._needs_ai_strategy(player) and player.ai_difficulty == AIDifficulty.HARD
        ]
        smart_player_id = random.choice(hard_ai_players).id if hard_ai_players else None

        # Occasionally nerf AI difficulty so the player can win
        nerf = _should_nerf_ai()
        if nerf:
            logger.info("Difficulty nerf active this game — AI playing softer")

        for player in players:
            managed.engine.add_player(player)
            if self._needs_ai_strategy(player):
                effective_difficulty = player.ai_difficulty
                if nerf and effective_difficulty in _NERF_MAP:
                    effective_difficulty = _NERF_MAP[effective_difficulty]
                use_smart = (not nerf) and player.id == smart_player_id
                managed.ai_strategies[player.id] = _make_strategy(effective_difficulty, use_smart=use_smart)

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

    def add_human_player(self, game_id: str, player: Player) -> bool:
        managed = self._games.get(game_id)
        if not managed:
            return False
        success = managed.engine.add_player(player)
        if success:
            event = player_joined_event(
                player_id=player.id,
                player_name=player.name,
                player_count=len(managed.engine.state.players),
            )
            managed._notify_callbacks(event)
        return success

    def start_game(self, game_id: str) -> bool:
        managed = self._games.get(game_id)
        if not managed:
            return False
        event = game_starting_event()
        managed._notify_callbacks(event)
        return managed.engine.start_game()

    def fill_with_ai(self, game_id: str) -> None:
        """Fill remaining slots with medium AI players."""
        managed = self._games.get(game_id)
        if not managed:
            return
        engine = managed.engine
        max_p = max_players_for_variant(engine.state.config.variant)
        current_count = len(engine.state.players)
        used_names = {player.name for player in engine.state.players}
        for index in range(current_count, max_p):
            ai_name = next(
                (name for name in AI_SWEETS_NAMES if name not in used_names),
                f"Bot {index + 1}",
            )
            used_names.add(ai_name)
            ai_player = Player(
                id=f"ai-backfill-{index}",
                name=ai_name,
                player_type=PlayerType.AI,
                ai_difficulty=AIDifficulty.MEDIUM,
            )
            if engine.add_player(ai_player):
                managed.ai_strategies[ai_player.id] = _make_strategy(AIDifficulty.MEDIUM)

    def get_game(self, game_id: str) -> Optional[ManagedGame]:
        # Exact match first
        exact = self._games.get(game_id)
        if exact:
            return exact
        # Prefix match (for short join codes) — case insensitive
        game_id_lower = game_id.lower()
        matches = [
            managed for gid, managed in self._games.items()
            if gid.lower().startswith(game_id_lower)
        ]
        if len(matches) == 1:
            return matches[0]
        return None

    def remove_game(self, game_id: str) -> None:
        self._games.pop(game_id, None)

    def list_games(self) -> List[str]:
        return list(self._games.keys())

    def list_public_lobbies(self) -> List[ManagedGame]:
        return [
            managed for managed in self._games.values()
            if managed.is_public and managed.engine.state.phase == GamePhase.LOBBY
        ]
