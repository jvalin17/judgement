from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, Optional, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

from backend.app.models import Card, Suit, Rank
from backend.app.models.events import EventType, GameEvent
from backend.app.game_manager import GameManager, ManagedGame

router = APIRouter()

_manager: GameManager = GameManager()


def set_manager(manager: GameManager) -> None:
    global _manager
    _manager = manager


# --- Connection tracking ---


class ConnectionManager:
    def __init__(self):
        self._games: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, game_id: str, player_id: str, websocket: WebSocket) -> Optional[WebSocket]:
        """Accept and register a WebSocket. Returns the old socket if replacing."""
        await websocket.accept()
        if game_id not in self._games:
            self._games[game_id] = {}
        old_socket = self._games[game_id].get(player_id)
        self._games[game_id][player_id] = websocket
        return old_socket

    def disconnect(self, game_id: str, player_id: str, websocket: WebSocket) -> None:
        """Only remove if the stored socket matches (prevents stale disconnect)."""
        game_connections = self._games.get(game_id)
        if not game_connections:
            return
        stored = game_connections.get(player_id)
        if stored is websocket:
            game_connections.pop(player_id, None)
        if not game_connections:
            del self._games[game_id]

    def get_connected_players(self, game_id: str) -> Set[str]:
        return set(self._games.get(game_id, {}).keys())


connection_manager = ConnectionManager()


# --- Event delay logic ---


def _get_event_delay(event_type: EventType, managed: ManagedGame) -> float:
    speed = managed.speed
    if event_type == EventType.CARD_PLAYED:
        return speed.after_card_played
    if event_type == EventType.TRICK_COMPLETE:
        return speed.after_trick_complete
    if event_type == EventType.ROUND_COMPLETE:
        return speed.after_round_complete
    if event_type == EventType.BIDDING_COMPLETE:
        return speed.after_bidding_complete
    return 0


# --- Message handlers ---


async def _handle_bid(managed: ManagedGame, player_id: str, message: dict) -> None:
    bid_amount = message.get("amount", 0)
    # Record human decision BEFORE the engine processes it (hand changes after)
    managed.record_human_bid(player_id, bid_amount)
    managed.engine.place_bid(player_id, bid_amount)


async def _handle_play_card(
    managed: ManagedGame, player_id: str, message: dict, websocket: WebSocket
) -> None:
    try:
        card = Card(suit=Suit(message["suit"]), rank=Rank(message["rank"]))
        # Record human decision BEFORE the engine processes it (hand changes after)
        managed.record_human_play(player_id, card)
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
    round_data = managed.engine.get_round_summary()
    await websocket.send_json({
        "type": "connected",
        "data": {
            "game_id": game_id,
            "player_id": player_id,
            "phase": engine.state.phase.value,
            "current_player_id": engine.state.current_player_id,
            "players": [player.model_dump() for player in engine.state.players],
            "host_player_id": managed.host_player_id,
            "must_lose_mode": engine.state.config.must_lose_mode,
            "challenge_mode": engine.state.config.challenge_mode,
            "total_rounds": len(engine._round_configs) if engine._round_configs else None,
            **round_data,
        },
    })
    # Send hand data immediately so the player can act right away
    await _handle_get_hand(managed, player_id, websocket)


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
    elif action == "next_round":
        managed.engine.continue_game()


# --- Writer / Reader tasks ---


async def _writer_task(
    queue: asyncio.Queue,
    websocket: WebSocket,
    player_id: str,
    managed: ManagedGame,
) -> None:
    """Continuously drain the event queue and send to this client."""
    while True:
        event: GameEvent = await queue.get()
        # Filter targeted events: only send if meant for this player or broadcast
        if event.player_id and event.player_id != player_id:
            continue

        message = {"type": event.event_type.value, "data": event.data}
        if event.event_type.value == "game_over":
            logger.info(
                "Sending game_over to %s: persona=%s",
                player_id,
                "present" if event.data.get("persona") else "None",
            )
        await websocket.send_json(message)

        delay = _get_event_delay(event.event_type, managed)
        if delay > 0:
            await asyncio.sleep(delay)

        # After events that change whose turn it is, auto-send hand data
        if event.event_type == EventType.TURN_CHANGED:
            if managed.engine.state.current_player_id == player_id:
                await _handle_get_hand(managed, player_id, websocket)


async def _reader_task(
    websocket: WebSocket,
    managed: ManagedGame,
    player_id: str,
) -> None:
    """Handle incoming client messages independently of event delivery."""
    while True:
        raw_text = await websocket.receive_text()
        await _dispatch_message(managed, player_id, raw_text, websocket)


# --- WebSocket endpoint ---


@router.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_id: str):
    managed = _manager.get_game(game_id)
    if not managed:
        await websocket.close(code=4004, reason="Game not found")
        return

    old_socket = await connection_manager.connect(game_id, player_id, websocket)
    if old_socket:
        # Close old connection gracefully (reconnection scenario)
        try:
            await old_socket.close(code=4001, reason="Replaced by new connection")
        except Exception:
            pass

    queue: asyncio.Queue = asyncio.Queue()

    def collect_event(event: GameEvent) -> None:
        queue.put_nowait(event)

    managed.add_event_callback(collect_event)

    try:
        await _send_connected(websocket, managed, game_id, player_id)

        writer = asyncio.create_task(_writer_task(queue, websocket, player_id, managed))
        reader = asyncio.create_task(_reader_task(websocket, managed, player_id))

        done, pending = await asyncio.wait(
            [writer, reader],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

    except WebSocketDisconnect:
        pass
    finally:
        managed.remove_event_callback(collect_event)
        connection_manager.disconnect(game_id, player_id, websocket)
