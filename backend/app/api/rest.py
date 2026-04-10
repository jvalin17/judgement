from __future__ import annotations

import uuid
from fastapi import APIRouter, HTTPException

from backend.app.models import Player, PlayerType, GameConfig, Card, Suit, Rank
from backend.app.api.schemas import (
    CreateGameRequest, CreateGameResponse,
    GameStateResponse, PlayerHandResponse,
    BidRequest, PlayCardRequest, ActionResponse,
    SessionLogResponse, PlayerSetup,
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
    if len(request.players) < 2:
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

    managed = _manager.create_game(config, players)
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
