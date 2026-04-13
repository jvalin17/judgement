from __future__ import annotations

import uuid
from fastapi import APIRouter, HTTPException

from backend.app.models import Player, PlayerType, GamePhase, GameConfig, Card, Suit, Rank, max_players_for_variant
from backend.app.models.game import DealingVariant
from backend.app.api.schemas import (
    CreateGameRequest, CreateGameResponse,
    GameStateResponse, PlayerHandResponse,
    BidRequest, PlayCardRequest, ActionResponse,
    SessionLogResponse, PlayerSetup,
    JoinGameRequest, JoinGameResponse, LobbyStateResponse,
    LobbyGameInfo, LobbyListResponse, QuickJoinRequest,
)
from backend.app.game_manager import GameManager, ManagedGame

router = APIRouter(prefix="/api/games", tags=["games"])

_manager: GameManager = GameManager()


def get_manager() -> GameManager:
    return _manager


def set_manager(manager: GameManager) -> None:
    global _manager
    _manager = manager


def _require_game(game_id: str) -> ManagedGame:
    managed = _manager.get_game(game_id)
    if not managed:
        raise HTTPException(404, "Game not found")
    return managed


def _parse_card(suit_str: str, rank_val: int) -> Card:
    try:
        return Card(suit=Suit(suit_str), rank=Rank(rank_val))
    except ValueError:
        raise HTTPException(400, "Invalid card")


def _build_player(setup: PlayerSetup) -> tuple[Player, str]:
    pid = str(uuid.uuid4())
    player = Player(
        id=pid,
        name=setup.name,
        player_type=PlayerType.AI if setup.is_ai else PlayerType.HUMAN,
        ai_difficulty=setup.ai_difficulty if setup.is_ai else None,
    )
    return player, pid


def _build_round_state(managed: ManagedGame) -> dict:
    rnd = managed.engine.state.current_round
    if not rnd:
        return {
            "trump_suit": None, "num_cards": None, "round_number": None,
            "dealer_id": None, "bids": [], "current_trick": [], "tricks_won": {},
        }
    return {
        "trump_suit": rnd.trump_suit.value,
        "num_cards": rnd.num_cards,
        "round_number": rnd.round_number,
        "dealer_id": rnd.dealer_id,
        "bids": [bid.model_dump() for bid in rnd.bids],
        "current_trick": [play.model_dump() for play in rnd.current_trick.plays],
        "tricks_won": dict(rnd.tricks_won),
    }


# --- Endpoints ---


@router.post("", response_model=CreateGameResponse)
async def create_game(request: CreateGameRequest):
    min_players = 2 if request.auto_start else 1
    if len(request.players) < min_players:
        raise HTTPException(400, "At least 2 players required")
    if len(request.players) > 6:
        raise HTTPException(400, "Maximum 6 players")

    config = GameConfig(variant=request.variant, must_lose_mode=request.must_lose_mode)
    players = []
    player_ids = {}

    for setup in request.players:
        player, pid = _build_player(setup)
        players.append(player)
        player_ids[setup.name] = pid

    speed = None
    if request.speed:
        from backend.app.game_manager import GameSpeed
        speed = GameSpeed(
            after_card=request.speed.after_card_played,
            after_trick=request.speed.after_trick_complete,
            after_round=request.speed.after_round_complete,
        )
    managed = _manager.create_game(config, players, speed=speed)

    # Track host (first human player)
    first_human = next(
        (player for player in players if player.player_type == PlayerType.HUMAN),
        None,
    )
    if first_human:
        managed.host_player_id = first_human.id

    managed.is_public = request.is_public

    if request.auto_start:
        managed.engine.start_game()

    return CreateGameResponse(game_id=managed.engine.state.game_id, player_ids=player_ids)


@router.get("/{game_id}", response_model=GameStateResponse)
async def get_game_state(game_id: str):
    managed = _require_game(game_id)
    state = managed.engine.state
    round_info = _build_round_state(managed)

    return GameStateResponse(
        game_id=state.game_id,
        phase=state.phase.value,
        players=[player.model_dump() for player in state.players],
        current_player_id=state.current_player_id,
        cumulative_scores=dict(state.cumulative_scores),
        **round_info,
    )


@router.get("/{game_id}/hand/{player_id}", response_model=PlayerHandResponse)
async def get_player_hand(game_id: str, player_id: str):
    managed = _require_game(game_id)
    engine = managed.engine

    return PlayerHandResponse(
        hand=[card.model_dump() for card in engine.get_player_hand(player_id)],
        valid_cards=[card.model_dump() for card in engine.get_valid_cards(player_id)],
        valid_bids=engine.get_valid_bids(player_id),
    )


@router.post("/{game_id}/bid", response_model=ActionResponse)
async def place_bid(game_id: str, request: BidRequest):
    managed = _require_game(game_id)
    success = managed.engine.place_bid(request.player_id, request.amount)
    return ActionResponse(success=success, message="" if success else "Invalid bid")


@router.post("/{game_id}/play", response_model=ActionResponse)
async def play_card(game_id: str, request: PlayCardRequest):
    managed = _require_game(game_id)
    card = _parse_card(request.suit, request.rank)
    success = managed.engine.play_card(request.player_id, card)
    return ActionResponse(success=success, message="" if success else "Invalid card play")


@router.get("/{game_id}/session-log", response_model=SessionLogResponse)
async def get_session_log(game_id: str):
    managed = _require_game(game_id)
    log = managed.session_log
    return SessionLogResponse(
        game_id=log.game_id,
        players=log.players,
        variant=log.variant,
        rounds=[round_log.model_dump() for round_log in log.rounds],
        final_scores=log.final_scores,
        winners=log.winners,
    )


# --- Join / Start / Lobby endpoints ---


@router.post("/{game_id}/join", response_model=JoinGameResponse)
async def join_game(game_id: str, request: JoinGameRequest):
    managed = _require_game(game_id)
    engine = managed.engine

    if engine.state.phase != GamePhase.LOBBY:
        raise HTTPException(400, "Game already started")

    max_p = max_players_for_variant(engine.state.config.variant)
    if len(engine.state.players) >= max_p:
        raise HTTPException(400, "Game is full")

    name_lower = request.player_name.strip().lower()
    if any(player.name.lower() == name_lower for player in engine.state.players):
        raise HTTPException(400, "Name already taken")

    pid = str(uuid.uuid4())
    player = Player(
        id=pid,
        name=request.player_name.strip(),
        player_type=PlayerType.HUMAN,
    )
    success = engine.add_player(player)
    if not success:
        raise HTTPException(400, "Could not join game")

    return JoinGameResponse(player_id=pid, game_id=engine.state.game_id)


@router.post("/{game_id}/start", response_model=ActionResponse)
async def start_game(game_id: str, player_id: str):
    managed = _require_game(game_id)
    engine = managed.engine

    if engine.state.phase != GamePhase.LOBBY:
        raise HTTPException(400, "Game already started")

    if managed.host_player_id and managed.host_player_id != player_id:
        raise HTTPException(403, "Only the host can start the game")

    if len(engine.state.players) < 2:
        raise HTTPException(400, "Need at least 2 players")

    success = engine.start_game()
    return ActionResponse(success=success, message="" if success else "Could not start game")


@router.get("/{game_id}/lobby", response_model=LobbyStateResponse)
async def get_lobby_state(game_id: str):
    managed = _require_game(game_id)
    engine = managed.engine
    config = engine.state.config

    return LobbyStateResponse(
        game_id=engine.state.game_id,
        phase=engine.state.phase.value,
        variant=config.variant.value,
        must_lose_mode=config.must_lose_mode,
        players=[player.model_dump() for player in engine.state.players],
        host_player_id=managed.host_player_id,
        max_players=max_players_for_variant(config.variant),
    )


# --- Lobby listing / quick-join ---


# Use a separate router for /api/lobby (not nested under /api/games/{id})
lobby_router = APIRouter(prefix="/api/lobby", tags=["lobby"])


@lobby_router.get("", response_model=LobbyListResponse)
async def list_lobbies():
    lobbies = _manager.list_public_lobbies()
    games = []
    for managed in lobbies:
        engine = managed.engine
        config = engine.state.config
        host = next(
            (p for p in engine.state.players if p.id == managed.host_player_id),
            None,
        )
        games.append(LobbyGameInfo(
            game_id=engine.state.game_id,
            host_name=host.name if host else None,
            variant=config.variant.value,
            must_lose_mode=config.must_lose_mode,
            player_count=len(engine.state.players),
            max_players=max_players_for_variant(config.variant),
        ))
    # Sort: most players first, then oldest
    games.sort(key=lambda g: (-g.player_count, g.game_id))
    return LobbyListResponse(games=games)


@lobby_router.post("/quick-join", response_model=JoinGameResponse)
async def quick_join(request: QuickJoinRequest):
    lobbies = _manager.list_public_lobbies()

    # Filter by variant if specified
    if request.variant:
        lobbies = [
            managed for managed in lobbies
            if managed.engine.state.config.variant.value == request.variant
        ]

    # Sort: most players first, then oldest
    lobbies.sort(
        key=lambda m: (-len(m.engine.state.players), m.created_at)
    )

    # Try to join an existing lobby
    for managed in lobbies:
        engine = managed.engine
        name_lower = request.player_name.strip().lower()
        name_taken = any(p.name.lower() == name_lower for p in engine.state.players)
        max_p = max_players_for_variant(engine.state.config.variant)
        is_full = len(engine.state.players) >= max_p

        if not name_taken and not is_full:
            pid = str(uuid.uuid4())
            player = Player(
                id=pid,
                name=request.player_name.strip(),
                player_type=PlayerType.HUMAN,
            )
            success = _manager.add_human_player(engine.state.game_id, player)
            if success:
                return JoinGameResponse(player_id=pid, game_id=engine.state.game_id)

    # No suitable lobby found — create a new one
    variant = DealingVariant(request.variant) if request.variant else DealingVariant.TEN_TO_ONE
    config = GameConfig(variant=variant, must_lose_mode=False)
    pid = str(uuid.uuid4())
    player = Player(
        id=pid,
        name=request.player_name.strip(),
        player_type=PlayerType.HUMAN,
    )
    managed = _manager.create_game(config, [player])
    managed.is_public = True
    managed.host_player_id = pid

    if request.auto_play:
        # Fill with AI and start immediately so the player can play right away
        _manager.fill_with_ai(managed.engine.state.game_id)
        managed.engine.start_game()

    return JoinGameResponse(player_id=pid, game_id=managed.engine.state.game_id)
