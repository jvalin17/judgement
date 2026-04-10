from __future__ import annotations

import asyncio
import json
from typing import Dict, Optional, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.models import Card, Suit, Rank
from backend.app.models.events import EventType, GameEvent
from backend.app.game_manager import GameManager, ManagedGame

# Default delays (seconds) inserted after events so the frontend can show each card.
# These control game pacing — how long the user sees each AI move before the
# next one plays. Configurable per-game via CreateGameRequest.speed.
DEFAULT_DELAY_AFTER_CARD_PLAYED = 2.0
DEFAULT_DELAY_AFTER_TRICK_COMPLETE = 3.0
DEFAULT_DELAY_AFTER_ROUND_COMPLETE = 1.5

router = APIRouter()

_manager: GameManager = GameManager()


def set_manager(manager: GameManager) -> None:
    global _manager
    _manager = manager


# --- Connection tracking ---


class ConnectionManager:
    def __init__(self):
        self._games: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, game_id: str, player_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if game_id not in self._games:
            self._games[game_id] = {}
        self._games[game_id][player_id] = websocket

    def disconnect(self, game_id: str, player_id: str) -> None:
        game_connections = self._games.get(game_id)
        if not game_connections:
            return
        game_connections.pop(player_id, None)
        if not game_connections:
            del self._games[game_id]

    async def send_to_player(self, game_id: str, player_id: str, message: dict) -> None:
        socket = self._get_socket(game_id, player_id)
        if socket:
            await socket.send_json(message)

    async def broadcast(self, game_id: str, message: dict, exclude: Optional[str] = None) -> None:
        game_connections = self._games.get(game_id, {})
        for player_id, socket in game_connections.items():
            if player_id != exclude:
                await socket.send_json(message)

    def get_connected_players(self, game_id: str) -> Set[str]:
        return set(self._games.get(game_id, {}).keys())

    def _get_socket(self, game_id: str, player_id: str) -> Optional[WebSocket]:
        return self._games.get(game_id, {}).get(player_id)


connection_manager = ConnectionManager()


# --- Event flushing ---


async def _flush_pending_events(
    events: list, game_id: str, connections: ConnectionManager, managed: ManagedGame
) -> None:
    """Send queued events to clients with delays between card plays.

    Without delays, AI card plays arrive in one instant burst and the
    frontend never has time to render each card being played.
    """
    while events:
        event = events.pop(0)
        message = {"type": event.event_type.value, "data": event.data}
        if event.player_id:
            await connections.send_to_player(game_id, event.player_id, message)
        else:
            await connections.broadcast(game_id, message)

        delay = _get_event_delay(event.event_type, managed)
        if delay > 0:
            await asyncio.sleep(delay)


def _get_event_delay(event_type: EventType, managed: ManagedGame) -> float:
    speed = managed.speed
    if event_type == EventType.CARD_PLAYED:
        return speed.after_card_played
    if event_type == EventType.TRICK_COMPLETE:
        return speed.after_trick_complete
    if event_type == EventType.ROUND_COMPLETE:
        return speed.after_round_complete
    return 0


# --- Message handlers ---


async def _handle_bid(managed: ManagedGame, player_id: str, message: dict) -> None:
    bid_amount = message.get("amount", 0)
    managed.engine.place_bid(player_id, bid_amount)


async def _handle_play_card(
    managed: ManagedGame, player_id: str, message: dict, websocket: WebSocket
) -> None:
    try:
        card = Card(suit=Suit(message["suit"]), rank=Rank(message["rank"]))
        managed.engine.play_card(player_id, card)
    except (ValueError, KeyError):
        await _send_error(websocket, "Invalid card")


async def _handle_get_hand(
    managed: ManagedGame, player_id: str, websocket: WebSocket
) -> None:
    engine = managed.engine
    hand = engine.get_player_hand(player_id)
    valid_cards = engine.get_valid_cards(player_id)
    valid_bids = engine.get_valid_bids(player_id)
    await websocket.send_json({
        "type": "hand",
        "data": {
            "hand": [card.model_dump() for card in hand],
            "valid_cards": [card.model_dump() for card in valid_cards],
            "valid_bids": valid_bids,
        },
    })


async def _send_error(websocket: WebSocket, reason: str) -> None:
    await websocket.send_json({"type": "error", "data": {"message": reason}})


async def _send_connected(websocket: WebSocket, managed: ManagedGame, game_id: str, player_id: str) -> None:
    engine = managed.engine
    round_data = _build_round_data(managed)
    await websocket.send_json({
        "type": "connected",
        "data": {
            "game_id": game_id,
            "player_id": player_id,
            "phase": engine.state.phase.value,
            "current_player_id": engine.state.current_player_id,
            "players": [player.model_dump() for player in engine.state.players],
            **round_data,
        },
    })
    # Send hand data immediately so the player can act right away
    await _handle_get_hand(managed, player_id, websocket)


def _build_round_data(managed: ManagedGame) -> dict:
    rm = managed.engine._round_manager
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


async def _send_hand_if_my_turn(
    managed: ManagedGame, player_id: str, websocket: WebSocket
) -> None:
    """Auto-send hand data when it's this player's turn.

    This avoids relying on the client to request get_hand via useEffect,
    which can miss turn changes due to React 18 state batching.
    """
    if managed.engine.state.current_player_id == player_id:
        await _handle_get_hand(managed, player_id, websocket)


_ACTION_HANDLERS = {
    "bid": _handle_bid,
    "play": _handle_play_card,
    "get_hand": _handle_get_hand,
}


async def _dispatch_message(
    managed: ManagedGame, player_id: str, raw_text: str, websocket: WebSocket
) -> None:
    message = json.loads(raw_text)
    action = message.get("action")

    if action == "bid":
        await _handle_bid(managed, player_id, message)
    elif action == "play":
        await _handle_play_card(managed, player_id, message, websocket)
    elif action == "get_hand":
        await _handle_get_hand(managed, player_id, websocket)


# --- WebSocket endpoint ---


@router.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_id: str):
    managed = _manager.get_game(game_id)
    if not managed:
        await websocket.close(code=4004, reason="Game not found")
        return

    await connection_manager.connect(game_id, player_id, websocket)

    pending_events: list = []

    def collect_event(event: GameEvent) -> None:
        pending_events.append(event)

    managed.add_event_callback(collect_event)

    try:
        await _send_connected(websocket, managed, game_id, player_id)

        while True:
            raw_text = await websocket.receive_text()
            await _dispatch_message(managed, player_id, raw_text, websocket)
            await _flush_pending_events(pending_events, game_id, connection_manager, managed)
            await _send_hand_if_my_turn(managed, player_id, websocket)

    except WebSocketDisconnect:
        pass
    finally:
        managed.remove_event_callback(collect_event)
        connection_manager.disconnect(game_id, player_id)
