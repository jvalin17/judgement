"""Integration test: play a full game over WebSocket and verify no stuck states.

Tests the exact code path that caused stuck bugs:
  - WebSocket connect after game already started (REST creates + starts)
  - State hydration from connected event (players, round_number, num_cards, etc.)
  - AI auto-play with delays between card_played events
  - Bidding → Playing phase transitions
  - Round transitions (ROUND_COMPLETE → ROUND_STARTED)
  - Trick completion and scoring
  - Game over detection

Stuck detection: any assertion timeout means the game got stuck.
Key invariant: when it's the human's turn, valid_bids or valid_cards MUST be non-empty.

NOTE: Starlette's sync TestClient WebSocket blocks on receive_json() when no
messages are available. Tests must read a known number of events or read until
a known sentinel event (like "hand") rather than trying to drain all messages.
"""

import json
import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.app.main import app
from backend.app.api.rest import set_manager as set_rest_manager
from backend.app.api.websocket import set_manager as set_ws_manager
from backend.app.game_manager import GameManager


# --- Disable event delays for fast tests ---

@pytest.fixture(autouse=True)
def fresh_manager():
    manager = GameManager()
    set_rest_manager(manager)
    set_ws_manager(manager)
    yield manager


client = TestClient(app)


def _create_game(variant="10_to_1"):
    resp = client.post("/api/games", json={
        "variant": variant,
        "must_lose_mode": False,
        "players": [
            {"name": "Human", "is_ai": False},
            {"name": "Bot1", "is_ai": True, "ai_difficulty": "medium"},
            {"name": "Bot2", "is_ai": True, "ai_difficulty": "medium"},
        ],
        "speed": {
            "after_card_played": 0,
            "after_trick_complete": 0,
            "after_round_complete": 0,
        },
    })
    assert resp.status_code == 200
    data = resp.json()
    return data["game_id"], data["player_ids"]["Human"]


# --- Helper: read events until we see a "hand" event ---

def _read_until_hand(ws, collector=None):
    """Read events from ws until a 'hand' event arrives.

    Returns (hand_data, events_seen).
    The server always sends a hand event as the last message after an action
    (via _send_hand_if_my_turn), so this won't block forever.

    Also stops on game_over to avoid blocking when the game ends.
    """
    events = []
    while True:
        evt = ws.receive_json()
        events.append(evt)
        if collector is not None:
            collector.append(evt)
        if evt["type"] == "hand":
            return evt["data"], events
        if evt["type"] == "game_over":
            return None, events


# --- Tests ---


class TestWebSocketConnect:
    """Verify the connected event includes full game state."""

    def test_connected_event_has_round_state(self):
        game_id, player_id = _create_game()

        with client.websocket_connect(f"/ws/{game_id}/{player_id}") as ws:
            # Should receive connected + hand events
            connected = ws.receive_json()
            assert connected["type"] == "connected"
            data = connected["data"]

            assert data["game_id"] == game_id
            assert data["player_id"] == player_id
            assert data["phase"] in ("bidding", "playing")
            assert data["current_player_id"] is not None
            assert len(data["players"]) == 3
            assert data["num_cards"] == 10  # first round of 10_to_1
            assert data["trump_suit"] is not None
            assert data["round_number"] == 1

    def test_auto_sends_hand_on_connect(self):
        game_id, player_id = _create_game()

        with client.websocket_connect(f"/ws/{game_id}/{player_id}") as ws:
            connected = ws.receive_json()
            hand = ws.receive_json()

            assert hand["type"] == "hand"
            assert len(hand["data"]["hand"]) == 10
            # Should have valid_bids or valid_cards depending on whose turn
            is_my_turn = connected["data"]["current_player_id"] == player_id
            if is_my_turn and connected["data"]["phase"] == "bidding":
                assert len(hand["data"]["valid_bids"]) > 0


class TestWebSocketTwoRounds:
    """Play through 2 complete rounds over WebSocket.

    This is the core integration test. It verifies:
    - Bidding flow (human bids, AI auto-bids)
    - Card play flow (human plays, AI auto-plays)
    - valid_cards is non-empty when it's the human's turn
    - Round transitions happen without getting stuck
    - Each card_played event has player_id and card data
    """

    def test_play_two_rounds(self):
        game_id, player_id = _create_game()

        with client.websocket_connect(f"/ws/{game_id}/{player_id}") as ws:
            # Initial events
            connected = ws.receive_json()
            hand_evt = ws.receive_json()

            assert connected["type"] == "connected"
            assert hand_evt["type"] == "hand"

            rounds_completed = 0
            turns_taken = 0
            cards_played_events = []
            trick_complete_events = []
            all_events = [connected, hand_evt]

            latest_hand = hand_evt["data"]

            while rounds_completed < 2:
                valid_bids = latest_hand.get("valid_bids", [])
                valid_cards = latest_hand.get("valid_cards", [])
                hand_cards = latest_hand.get("hand", [])

                # Act based on phase
                if valid_bids:
                    bid = valid_bids[0]
                    ws.send_json({"action": "bid", "amount": bid})
                elif valid_cards:
                    card = valid_cards[0]
                    ws.send_json({
                        "action": "play",
                        "suit": card["suit"],
                        "rank": card["rank"],
                    })
                else:
                    pytest.fail(
                        f"STUCK: No valid_bids or valid_cards! "
                        f"hand_size={len(hand_cards)}, "
                        f"rounds={rounds_completed}, turns={turns_taken}"
                    )

                turns_taken += 1

                # Read events until we get our next hand update
                hand_data, response_events = _read_until_hand(ws, all_events)

                for evt in response_events:
                    if evt["type"] == "card_played":
                        cards_played_events.append(evt)
                        _assert_card_played_event(evt)
                    elif evt["type"] == "trick_complete":
                        trick_complete_events.append(evt)
                    elif evt["type"] == "round_complete":
                        rounds_completed += 1

                if hand_data is None:
                    # game_over arrived
                    break

                latest_hand = hand_data

                # Safety valve
                assert turns_taken < 100, "Too many turns — likely an infinite loop"

            # Verify we saw card_played events with proper data
            assert len(cards_played_events) > 0, "No card_played events seen"
            assert len(trick_complete_events) > 0, "No trick_complete events seen"

            # Verify round progression
            round_starts = [e for e in all_events if e["type"] == "round_started"]
            assert len(round_starts) >= 1, "No round_started events after first round"

    def test_card_played_events_have_player_names(self):
        """Verify each card_played event has player_id and card,
        so the frontend can show who played what."""
        game_id, player_id = _create_game()

        with client.websocket_connect(f"/ws/{game_id}/{player_id}") as ws:
            connected = ws.receive_json()
            hand_evt = ws.receive_json()
            players = {p["id"]: p["name"] for p in connected["data"]["players"]}
            latest_hand = hand_evt["data"]

            card_events = []
            for _ in range(30):  # enough turns for 1 round
                valid_bids = latest_hand.get("valid_bids", [])
                valid_cards = latest_hand.get("valid_cards", [])

                if valid_bids:
                    ws.send_json({"action": "bid", "amount": valid_bids[0]})
                elif valid_cards:
                    ws.send_json({"action": "play", "suit": valid_cards[0]["suit"], "rank": valid_cards[0]["rank"]})
                else:
                    break

                hand_data, response_events = _read_until_hand(ws)

                for evt in response_events:
                    if evt["type"] == "card_played":
                        card_events.append(evt["data"])
                    elif evt["type"] == "round_complete":
                        break

                if hand_data is None:
                    break
                latest_hand = hand_data

            # Every card_played event must identify the player and the card
            for card_event in card_events:
                assert "player_id" in card_event
                assert card_event["player_id"] in players, (
                    f"Unknown player_id {card_event['player_id']}"
                )
                assert "card" in card_event
                assert "suit" in card_event["card"]
                assert "rank" in card_event["card"]


class TestStuckDetection:
    """Verify the key invariant: when it's the human's turn,
    valid_bids or valid_cards is always non-empty."""

    def test_hand_always_has_valid_actions_on_my_turn(self):
        game_id, player_id = _create_game()

        with client.websocket_connect(f"/ws/{game_id}/{player_id}") as ws:
            connected = ws.receive_json()
            hand_evt = ws.receive_json()
            latest_hand = hand_evt["data"]

            violations = []

            for turn in range(50):
                valid_bids = latest_hand.get("valid_bids", [])
                valid_cards = latest_hand.get("valid_cards", [])
                hand_size = len(latest_hand.get("hand", []))

                # Key invariant check
                if not valid_bids and not valid_cards:
                    violations.append(
                        f"Turn {turn}: empty valid_bids AND valid_cards "
                        f"(hand_size={hand_size})"
                    )
                    break

                if valid_bids:
                    ws.send_json({"action": "bid", "amount": valid_bids[0]})
                else:
                    ws.send_json({"action": "play", "suit": valid_cards[0]["suit"], "rank": valid_cards[0]["rank"]})

                hand_data, response_events = _read_until_hand(ws)

                if hand_data is None:
                    # game_over
                    break

                latest_hand = hand_data

            assert not violations, f"Stuck state detected: {violations}"


# --- Assertion helpers ---


def _assert_card_played_event(event):
    """Verify a card_played event has the expected structure."""
    data = event["data"]
    assert "player_id" in data, "card_played missing player_id"
    assert "card" in data, "card_played missing card"
    card = data["card"]
    assert card["suit"] in ("spades", "diamonds", "clubs", "hearts")
    assert isinstance(card["rank"], int)
    assert 2 <= card["rank"] <= 14
