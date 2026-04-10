import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api.rest import set_manager
from backend.app.game_manager import GameManager


@pytest.fixture(autouse=True)
def fresh_manager():
    manager = GameManager()
    set_manager(manager)
    yield manager


client = TestClient(app)


def _create_game(players=None, variant="10_to_1", must_lose=False):
    if players is None:
        players = [
            {"name": "Alice", "is_ai": False},
            {"name": "Bot1", "is_ai": True, "ai_difficulty": "easy"},
            {"name": "Bot2", "is_ai": True, "ai_difficulty": "medium"},
        ]
    return client.post("/api/games", json={
        "variant": variant,
        "must_lose_mode": must_lose,
        "players": players,
    })


class TestCreateGame:
    def test_create_game_success(self):
        resp = _create_game()
        assert resp.status_code == 200
        data = resp.json()
        assert "game_id" in data
        assert "Alice" in data["player_ids"]
        assert "Bot1" in data["player_ids"]

    def test_create_game_too_few_players(self):
        resp = _create_game(players=[{"name": "Solo"}])
        assert resp.status_code == 400

    def test_create_game_must_lose(self):
        resp = _create_game(must_lose=True)
        assert resp.status_code == 200


class TestGetGameState:
    def test_get_state(self):
        create_resp = _create_game()
        game_id = create_resp.json()["game_id"]

        resp = client.get(f"/api/games/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["game_id"] == game_id
        # AI players should have already bid (easy + medium), Alice's turn
        assert data["phase"] in ("bidding", "playing", "round_over")

    def test_get_nonexistent_game(self):
        resp = client.get("/api/games/nonexistent")
        assert resp.status_code == 404


class TestGetPlayerHand:
    def test_get_hand(self):
        create_resp = _create_game()
        data = create_resp.json()
        game_id = data["game_id"]
        alice_id = data["player_ids"]["Alice"]

        resp = client.get(f"/api/games/{game_id}/hand/{alice_id}")
        assert resp.status_code == 200
        hand_data = resp.json()
        assert "hand" in hand_data
        assert len(hand_data["hand"]) == 10  # first round is 10 cards


class TestBidAndPlay:
    def test_full_human_turn(self):
        create_resp = _create_game()
        data = create_resp.json()
        game_id = data["game_id"]
        alice_id = data["player_ids"]["Alice"]

        # Get state to see if it's Alice's turn to bid
        state = client.get(f"/api/games/{game_id}").json()

        if state["phase"] == "bidding" and state["current_player_id"] == alice_id:
            # Get valid bids
            hand_resp = client.get(f"/api/games/{game_id}/hand/{alice_id}").json()
            valid_bids = hand_resp["valid_bids"]
            assert len(valid_bids) > 0

            # Place bid
            bid_resp = client.post(f"/api/games/{game_id}/bid", json={
                "player_id": alice_id,
                "amount": valid_bids[0],
            })
            assert bid_resp.json()["success"] is True

        # After bidding, check if it's playing phase and Alice's turn
        state = client.get(f"/api/games/{game_id}").json()
        if state["phase"] == "playing" and state["current_player_id"] == alice_id:
            hand_resp = client.get(f"/api/games/{game_id}/hand/{alice_id}").json()
            valid_cards = hand_resp["valid_cards"]
            assert len(valid_cards) > 0

            card = valid_cards[0]
            play_resp = client.post(f"/api/games/{game_id}/play", json={
                "player_id": alice_id,
                "suit": card["suit"],
                "rank": card["rank"],
            })
            assert play_resp.json()["success"] is True

    def test_invalid_bid(self):
        create_resp = _create_game()
        data = create_resp.json()
        game_id = data["game_id"]
        alice_id = data["player_ids"]["Alice"]

        # Try bidding out of turn or invalid amount
        resp = client.post(f"/api/games/{game_id}/bid", json={
            "player_id": "nonexistent",
            "amount": 99,
        })
        assert resp.json()["success"] is False


class TestSessionLog:
    def test_session_log_exists(self):
        create_resp = _create_game()
        game_id = create_resp.json()["game_id"]

        resp = client.get(f"/api/games/{game_id}/session-log")
        assert resp.status_code == 200
        log = resp.json()
        assert log["game_id"] == game_id
        assert len(log["players"]) == 3


class TestAIAutoPlay:
    def test_ai_plays_automatically(self):
        """When game starts with AI players, they bid/play on their own turns."""
        create_resp = _create_game()
        data = create_resp.json()
        game_id = data["game_id"]
        alice_id = data["player_ids"]["Alice"]

        state = client.get(f"/api/games/{game_id}").json()
        # AI should have already taken their turns, so either it's Alice's turn
        # or AI has played through everything
        if state["current_player_id"] == alice_id:
            # Good — AI played, now waiting for human
            assert state["phase"] in ("bidding", "playing")
        else:
            # AI might still be going in a later phase
            assert state["phase"] in ("bidding", "playing", "round_over", "game_over")
