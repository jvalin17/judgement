"""Tests for house rules and the custom dealing variant.

Written in the judgement-tests style so they can move to that repo as-is.
Run from the repo root with: python3 -m pytest backend/tests/ -v
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.models import (
    Bid, Card, Suit, Rank, Player, PlayerType, AIDifficulty,
    GameConfig, DealingVariant, GamePhase,
    HouseRules, CustomDeal, TrumpMode, MadeScoring, MissedScoring, RoundShape,
    max_players_for_config, max_players_for_variant,
)
from backend.app.game.engine import GameEngine
from backend.app.game.round_manager import RoundManager
from backend.app.game.round_config_loader import build_round_configs, load_round_configs
from backend.app.game.scorer import score_round, made_bid_points, missed_bid_points
from backend.app.game.validators import get_forbidden_bid, get_valid_cards, validate_bid, validate_play
from backend.app.game_manager import GameManager, ManagedGame


def _players(count: int) -> list[Player]:
    return [
        Player(id=f"p{index + 1}", name=f"P{index + 1}", player_type=PlayerType.HUMAN)
        for index in range(count)
    ]


def _engine(config: GameConfig, player_count: int) -> GameEngine:
    engine = GameEngine(config)
    for player in _players(player_count):
        assert engine.add_player(player)
    return engine


def _card(suit: Suit, rank: Rank) -> Card:
    return Card(suit=suit, rank=rank)


# --- CustomDeal: hand-size sequences ---


def test_custom_deal_down_runs_from_start_to_one():
    deal = CustomDeal(start_cards=7)
    assert deal.card_sequence(4) == [7, 6, 5, 4, 3, 2, 1]


def test_custom_deal_up_runs_from_min_to_start():
    deal = CustomDeal(start_cards=5, min_cards=2, shape=RoundShape.UP)
    assert deal.card_sequence(4) == [2, 3, 4, 5]


def test_custom_deal_down_up_plays_turnaround_once_by_default():
    deal = CustomDeal(start_cards=3, shape=RoundShape.DOWN_UP)
    assert deal.card_sequence(4) == [3, 2, 1, 2, 3]


def test_custom_deal_down_up_repeat_turn_plays_turnaround_twice():
    deal = CustomDeal(start_cards=3, shape=RoundShape.DOWN_UP, repeat_turn=True)
    assert deal.card_sequence(4) == [3, 2, 1, 1, 2, 3]


def test_custom_deal_up_down_turns_at_the_top():
    deal = CustomDeal(start_cards=4, min_cards=2, shape=RoundShape.UP_DOWN)
    assert deal.card_sequence(4) == [2, 3, 4, 3, 2]


def test_custom_deal_up_down_repeat_turn_plays_top_twice():
    deal = CustomDeal(start_cards=3, min_cards=2, shape=RoundShape.UP_DOWN, repeat_turn=True)
    assert deal.card_sequence(4) == [2, 3, 3, 2]


def test_custom_deal_auto_start_uses_max_for_player_count():
    deal = CustomDeal(start_cards=None)
    assert deal.resolve_start(4) == 13
    assert deal.resolve_start(5) == 10
    assert deal.resolve_start(6) == 8


def test_custom_deal_reduces_start_when_deck_is_too_small():
    """10 cards each needs 60 cards for 6 players, so hands start at 8."""
    deal = CustomDeal(start_cards=10)
    assert deal.resolve_start(5) == 10
    assert deal.resolve_start(6) == 8
    assert deal.card_sequence(6)[0] == 8


def test_custom_deal_min_above_reduced_start_collapses_to_one_round():
    deal = CustomDeal(start_cards=10, min_cards=9)
    assert deal.card_sequence(6) == [8]


def test_custom_deal_single_size_round():
    deal = CustomDeal(start_cards=5, min_cards=5, shape=RoundShape.DOWN_UP)
    assert deal.card_sequence(4) == [5]


def test_custom_deal_max_players_depends_on_min_cards():
    assert CustomDeal(min_cards=1).max_players() == 6
    assert CustomDeal(min_cards=9).max_players() == 5
    assert CustomDeal(min_cards=26).max_players() == 2


@pytest.mark.parametrize("field,value", [
    ("start_cards", 0), ("start_cards", 27), ("min_cards", 0), ("min_cards", 27),
])
def test_custom_deal_rejects_out_of_range_values(field, value):
    with pytest.raises(ValidationError):
        CustomDeal(**{field: value})


def test_custom_deal_rejects_unknown_shape():
    with pytest.raises(ValidationError):
        CustomDeal(shape="sideways")


# --- Round configs ---


def test_build_round_configs_custom_uses_rotation_trump():
    config = GameConfig(variant=DealingVariant.CUSTOM, custom_deal=CustomDeal(start_cards=5))
    rounds = build_round_configs(config, 4)
    assert [r.cards for r in rounds] == [5, 4, 3, 2, 1]
    assert [r.trump for r in rounds] == [Suit.SPADES, Suit.DIAMONDS, Suit.CLUBS, Suit.HEARTS, Suit.SPADES]
    assert [r.round for r in rounds] == [1, 2, 3, 4, 5]


def test_build_round_configs_preset_matches_json():
    config = GameConfig(variant=DealingVariant.EIGHT_TO_THREE)
    assert build_round_configs(config, 4) == load_round_configs(DealingVariant.EIGHT_TO_THREE)


def test_build_round_configs_custom_without_deal_uses_defaults():
    config = GameConfig(variant=DealingVariant.CUSTOM)
    assert [r.cards for r in build_round_configs(config, 4)] == list(range(13, 0, -1))


def test_max_players_for_config_custom_uses_min_cards():
    config = GameConfig(variant=DealingVariant.CUSTOM, custom_deal=CustomDeal(min_cards=11))
    assert max_players_for_config(config) == 4


def test_max_players_for_config_preset_unchanged():
    for variant in DealingVariant:
        if variant == DealingVariant.CUSTOM:
            continue
        assert max_players_for_config(GameConfig(variant=variant)) == max_players_for_variant(variant)


# --- HouseRules flags ---


def test_house_rules_defaults_are_classic():
    rules = HouseRules()
    assert rules.trump_mode == TrumpMode.ROTATION
    assert rules.dealer_restriction is True
    assert rules.must_trump_when_void is False
    assert rules.made_scoring == MadeScoring.CLASSIC
    assert rules.missed_scoring == MissedScoring.NEGATIVE
    assert rules.is_default()


def test_game_config_is_standard_only_for_presets_with_classic_rules():
    assert GameConfig().is_standard()
    assert not GameConfig(variant=DealingVariant.CUSTOM).is_standard()
    assert not GameConfig(house_rules=HouseRules(trump_mode=TrumpMode.FLIP)).is_standard()


@pytest.mark.parametrize("rules,compatible", [
    (HouseRules(), True),
    (HouseRules(trump_mode=TrumpMode.FLIP), True),
    (HouseRules(dealer_restriction=False), False),
    (HouseRules(must_trump_when_void=True), False),
    (HouseRules(made_scoring=MadeScoring.TEN_PLUS_BID), False),
    (HouseRules(missed_scoring=MissedScoring.ZERO), False),
    (HouseRules(missed_scoring=MissedScoring.PER_TRICK_OFF), False),
])
def test_house_rules_training_compatibility(rules, compatible):
    assert rules.is_training_compatible() is compatible


# --- Scoring ---


def test_score_round_defaults_match_classic_scoring():
    bids = [Bid(player_id="a", amount=0), Bid(player_id="b", amount=1), Bid(player_id="c", amount=3)]
    assert score_round(bids, {"a": 0, "b": 1, "c": 3}) == {"a": 10, "b": 11, "c": 30}
    assert score_round(bids, {"a": 1, "b": 0, "c": 2}) == {"a": -10, "b": -11, "c": -30}


def test_made_bid_points_ten_plus_bid():
    assert [made_bid_points(n, MadeScoring.TEN_PLUS_BID) for n in (0, 1, 2, 5)] == [10, 11, 12, 15]


def test_missed_bid_points_negative_follows_made_formula():
    assert missed_bid_points(3, 1, MadeScoring.TEN_PLUS_BID, MissedScoring.NEGATIVE) == -13
    assert missed_bid_points(3, 1, MadeScoring.CLASSIC, MissedScoring.NEGATIVE) == -30


def test_missed_bid_points_zero():
    assert missed_bid_points(4, 0, MadeScoring.CLASSIC, MissedScoring.ZERO) == 0


def test_missed_bid_points_per_trick_off_counts_both_directions():
    assert missed_bid_points(2, 5, MadeScoring.CLASSIC, MissedScoring.PER_TRICK_OFF) == -30
    assert missed_bid_points(4, 1, MadeScoring.CLASSIC, MissedScoring.PER_TRICK_OFF) == -30
    assert missed_bid_points(0, 1, MadeScoring.CLASSIC, MissedScoring.PER_TRICK_OFF) == -10


def test_score_round_with_house_scoring():
    bids = [Bid(player_id="a", amount=2), Bid(player_id="b", amount=3)]
    scores = score_round(bids, {"a": 2, "b": 1}, MadeScoring.TEN_PLUS_BID, MissedScoring.PER_TRICK_OFF)
    assert scores == {"a": 12, "b": -20}


# --- Validators ---


def test_dealer_restriction_off_allows_any_dealer_bid():
    bids = [Bid(player_id="a", amount=1), Bid(player_id="b", amount=1)]
    assert get_forbidden_bid(2, 3, 3, bids, False, dealer_restriction=False) is None
    assert validate_bid(1, 2, 3, 3, bids, False, dealer_restriction=False)


def test_dealer_restriction_on_by_default():
    bids = [Bid(player_id="a", amount=1), Bid(player_id="b", amount=1)]
    assert get_forbidden_bid(2, 3, 3, bids, False) == 1
    assert not validate_bid(1, 2, 3, 3, bids, False)


def test_must_trump_forces_trump_when_void_in_lead():
    hand = [_card(Suit.SPADES, Rank.TWO), _card(Suit.CLUBS, Rank.ACE), _card(Suit.SPADES, Rank.KING)]
    valid = get_valid_cards(hand, Suit.HEARTS, Suit.SPADES, must_trump_when_void=True)
    assert set(valid) == {_card(Suit.SPADES, Rank.TWO), _card(Suit.SPADES, Rank.KING)}


def test_must_trump_off_allows_any_card_when_void():
    hand = [_card(Suit.SPADES, Rank.TWO), _card(Suit.CLUBS, Rank.ACE)]
    assert set(get_valid_cards(hand, Suit.HEARTS, Suit.SPADES)) == set(hand)


def test_must_trump_still_requires_following_suit_first():
    hand = [_card(Suit.HEARTS, Rank.THREE), _card(Suit.SPADES, Rank.ACE)]
    valid = get_valid_cards(hand, Suit.HEARTS, Suit.SPADES, must_trump_when_void=True)
    assert valid == [_card(Suit.HEARTS, Rank.THREE)]


def test_must_trump_without_trumps_allows_any_card():
    hand = [_card(Suit.CLUBS, Rank.THREE), _card(Suit.DIAMONDS, Rank.ACE)]
    valid = get_valid_cards(hand, Suit.HEARTS, Suit.SPADES, must_trump_when_void=True)
    assert set(valid) == set(hand)


def test_validate_play_rejects_discard_under_must_trump():
    hand = [_card(Suit.SPADES, Rank.TWO), _card(Suit.CLUBS, Rank.ACE)]
    assert not validate_play(_card(Suit.CLUBS, Rank.ACE), hand, Suit.HEARTS, Suit.SPADES, True)
    assert validate_play(_card(Suit.SPADES, Rank.TWO), hand, Suit.HEARTS, Suit.SPADES, True)


# --- Round manager: trump flip ---


def test_flip_trump_uses_first_undealt_card():
    rm = RoundManager(
        round_number=1, num_cards=5, trump_suit=Suit.SPADES, players=_players(4),
        dealer_index=0, must_lose_mode=False, house_rules=HouseRules(trump_mode=TrumpMode.FLIP),
    )
    assert rm.state.trump_card is not None
    assert rm.state.trump_suit == rm.state.trump_card.suit
    dealt = [card for hand in rm.state.hands.values() for card in hand]
    assert rm.state.trump_card not in dealt


def test_flip_trump_falls_back_to_rotation_when_all_cards_dealt():
    rm = RoundManager(
        round_number=1, num_cards=13, trump_suit=Suit.CLUBS, players=_players(4),
        dealer_index=0, must_lose_mode=False, house_rules=HouseRules(trump_mode=TrumpMode.FLIP),
    )
    assert rm.state.trump_card is None
    assert rm.state.trump_suit == Suit.CLUBS


def test_rotation_trump_has_no_trump_card():
    rm = RoundManager(
        round_number=1, num_cards=5, trump_suit=Suit.HEARTS, players=_players(4),
        dealer_index=0, must_lose_mode=False,
    )
    assert rm.state.trump_card is None
    assert rm.state.trump_suit == Suit.HEARTS


def test_round_manager_uses_house_scoring():
    rm = RoundManager(
        round_number=1, num_cards=1, trump_suit=Suit.SPADES, players=_players(2),
        dealer_index=0, must_lose_mode=False,
        house_rules=HouseRules(made_scoring=MadeScoring.TEN_PLUS_BID, missed_scoring=MissedScoring.ZERO),
    )
    rm.state.bids = [Bid(player_id="p1", amount=1), Bid(player_id="p2", amount=1)]
    rm.state.tricks_won = {"p1": 1, "p2": 0}
    assert rm.calculate_scores() == {"p1": 11, "p2": 0}


# --- Engine integration ---


def test_engine_custom_game_sizes_rounds_for_player_count():
    config = GameConfig(variant=DealingVariant.CUSTOM, custom_deal=CustomDeal(start_cards=10))
    engine = _engine(config, 6)
    assert engine.start_game()
    assert engine.state.current_round.num_cards == 8
    assert len(engine._round_configs) == 8
    for hand in engine.state.current_round.hands.values():
        assert len(hand) == 8


def test_engine_rejects_players_beyond_custom_deal_limit():
    config = GameConfig(variant=DealingVariant.CUSTOM, custom_deal=CustomDeal(min_cards=11))
    engine = _engine(config, 4)
    assert not engine.add_player(Player(id="p5", name="P5", player_type=PlayerType.HUMAN))


def test_engine_dealer_restriction_off_offers_every_bid():
    config = GameConfig(house_rules=HouseRules(dealer_restriction=False))
    engine = _engine(config, 3)
    engine.start_game()
    num_cards = engine.state.current_round.num_cards
    for _ in range(2):
        engine.place_bid(engine.state.current_player_id, 1)
    dealer = engine.state.current_player_id
    assert engine.get_valid_bids(dealer) == list(range(num_cards + 1))
    assert engine.place_bid(dealer, num_cards - 2)


def test_engine_flip_trump_reported_in_round_started_event():
    events = []
    config = GameConfig(house_rules=HouseRules(trump_mode=TrumpMode.FLIP))
    engine = _engine(config, 3)
    engine.add_observer(events.append)
    engine.start_game()
    started = next(e for e in events if e.event_type.value == "round_started")
    card = started.data["trump_card"]
    assert card is not None
    assert started.data["trump_suit"] == card["suit"]
    assert engine.get_round_summary()["trump_card"] == card


def test_engine_must_trump_restricts_valid_cards():
    config = GameConfig(house_rules=HouseRules(must_trump_when_void=True))
    engine = _engine(config, 2)
    engine.start_game()
    rm = engine._round_manager
    trump = rm.state.trump_suit
    lead_suit = next(s for s in Suit if s != trump)
    off_suit = next(s for s in Suit if s not in (trump, lead_suit))
    leader, follower = rm.play_order
    rm.state.hands[leader] = [_card(lead_suit, Rank.FIVE)] + rm.state.hands[leader][1:]
    rm.state.hands[follower] = [_card(trump, Rank.TWO), _card(off_suit, Rank.ACE)] + [
        c for c in rm.state.hands[follower][2:] if c.suit not in (lead_suit, trump)
    ]
    for _ in range(2):
        assert engine.place_bid(engine.state.current_player_id, 0)
    assert engine.state.phase == GamePhase.PLAYING
    assert engine.play_card(leader, _card(lead_suit, Rank.FIVE))
    valid = engine.get_valid_cards(follower)
    assert valid and all(card.suit == trump for card in valid)
    assert not engine.play_card(follower, _card(off_suit, Rank.ACE))


def test_engine_full_custom_game_with_bots_completes():
    """Bots must play legally under every house rule at once."""
    config = GameConfig(
        variant=DealingVariant.CUSTOM,
        custom_deal=CustomDeal(start_cards=4, min_cards=2, shape=RoundShape.DOWN_UP),
        house_rules=HouseRules(
            trump_mode=TrumpMode.FLIP, dealer_restriction=False, must_trump_when_void=True,
            made_scoring=MadeScoring.TEN_PLUS_BID, missed_scoring=MissedScoring.PER_TRICK_OFF,
        ),
    )
    bots = [
        Player(id=f"b{i}", name=f"Bot{i}", player_type=PlayerType.AI, ai_difficulty=difficulty)
        for i, difficulty in enumerate([AIDifficulty.EASY, AIDifficulty.MEDIUM, AIDifficulty.HARD, AIDifficulty.MEDIUM])
    ]
    manager = GameManager()
    managed = manager.create_game(config, bots)
    assert managed.engine.start_game()
    for _ in range(200):
        if managed.engine.state.phase == GamePhase.GAME_OVER:
            break
        if managed.engine.state.phase == GamePhase.ROUND_OVER:
            managed.engine.continue_game()
    assert managed.engine.state.phase == GamePhase.GAME_OVER
    assert len(managed.session_log.rounds) == 5


# --- ML training data guard ---


def _finish_game(managed: ManagedGame) -> None:
    from backend.app.models.events import game_over_event
    managed._flush_winner_decisions(game_over_event(final_scores={}, winners=[]))


def test_nonstandard_scoring_games_skip_training_data(monkeypatch):
    managed = GameManager().create_game(
        GameConfig(house_rules=HouseRules(missed_scoring=MissedScoring.ZERO)), _players(2),
    )
    calls = []
    monkeypatch.setattr(managed.decision_collector, "flush_all", lambda *a: calls.append(a) or 0)
    _finish_game(managed)
    assert calls == []


def test_classic_rule_games_still_flush_training_data(monkeypatch):
    managed = GameManager().create_game(
        GameConfig(house_rules=HouseRules(trump_mode=TrumpMode.FLIP)), _players(2),
    )
    calls = []
    monkeypatch.setattr(managed.decision_collector, "flush_all", lambda *a: calls.append(a) or 0)
    _finish_game(managed)
    assert len(calls) == 1


# --- REST API ---


@pytest.fixture
def client():
    from backend.app.main import app
    from backend.app.api.rest import set_manager
    set_manager(GameManager())
    return TestClient(app)


def _host_only(name="Host"):
    return [{"name": name, "is_ai": False}]


def test_api_create_custom_game_stores_rules(client):
    response = client.post("/api/games", json={
        "variant": "custom",
        "custom_deal": {"start_cards": 7, "min_cards": 2, "shape": "down_up"},
        "house_rules": {"trump_mode": "flip", "made_scoring": "ten_plus_bid"},
        "players": _host_only(),
        "auto_start": False,
    })
    assert response.status_code == 200
    lobby = client.get(f"/api/games/{response.json()['game_id']}/lobby").json()
    assert lobby["variant"] == "custom"
    assert lobby["custom_deal"] == {"start_cards": 7, "min_cards": 2, "shape": "down_up", "repeat_turn": False}
    assert lobby["house_rules"]["trump_mode"] == "flip"
    assert lobby["house_rules"]["made_scoring"] == "ten_plus_bid"
    assert lobby["house_rules"]["dealer_restriction"] is True
    assert lobby["max_players"] == 6


def test_api_custom_game_without_deal_stores_defaults(client):
    response = client.post("/api/games", json={
        "variant": "custom", "players": _host_only(), "auto_start": False,
    })
    lobby = client.get(f"/api/games/{response.json()['game_id']}/lobby").json()
    assert lobby["custom_deal"] == {"start_cards": None, "min_cards": 1, "shape": "down", "repeat_turn": False}


def test_api_preset_ignores_custom_deal(client):
    response = client.post("/api/games", json={
        "variant": "10_to_1", "custom_deal": {"start_cards": 3},
        "players": _host_only(), "auto_start": False,
    })
    lobby = client.get(f"/api/games/{response.json()['game_id']}/lobby").json()
    assert lobby["custom_deal"] is None


def test_api_defaults_when_house_rules_omitted(client):
    response = client.post("/api/games", json={"players": _host_only(), "auto_start": False})
    lobby = client.get(f"/api/games/{response.json()['game_id']}/lobby").json()
    assert lobby["house_rules"] == HouseRules().model_dump(mode="json")


def test_api_rejects_invalid_house_rule_value(client):
    response = client.post("/api/games", json={
        "house_rules": {"made_scoring": "double"}, "players": _host_only(), "auto_start": False,
    })
    assert response.status_code == 422


def test_api_rejects_more_players_than_custom_deal_seats(client):
    players = [{"name": f"P{i}", "is_ai": i > 0, "ai_difficulty": "easy" if i else None} for i in range(5)]
    response = client.post("/api/games", json={
        "variant": "custom", "custom_deal": {"min_cards": 11}, "players": players,
    })
    assert response.status_code == 400
    assert "at most 4" in response.json()["detail"]


def test_api_join_respects_custom_deal_seat_limit(client):
    game = client.post("/api/games", json={
        "variant": "custom", "custom_deal": {"min_cards": 26},
        "players": _host_only(), "auto_start": False,
    }).json()
    assert client.post(f"/api/games/{game['game_id']}/join", json={"player_name": "Two"}).status_code == 200
    full = client.post(f"/api/games/{game['game_id']}/join", json={"player_name": "Three"})
    assert full.status_code == 400


def test_api_lobby_list_includes_rules(client):
    client.post("/api/games", json={
        "house_rules": {"dealer_restriction": False}, "players": _host_only(),
        "auto_start": False, "is_public": True,
    })
    games = client.get("/api/lobby").json()["games"]
    assert games[0]["house_rules"]["dealer_restriction"] is False


def test_api_quick_join_skips_house_rule_lobbies(client):
    custom = client.post("/api/games", json={
        "house_rules": {"missed_scoring": "zero"}, "players": _host_only(),
        "auto_start": False, "is_public": True,
    }).json()
    joined = client.post("/api/lobby/quick-join", json={"player_name": "Stranger", "auto_play": False}).json()
    assert joined["game_id"] != custom["game_id"]


def test_api_quick_join_still_matches_standard_lobbies(client):
    standard = client.post("/api/games", json={
        "players": _host_only(), "auto_start": False, "is_public": True,
    }).json()
    joined = client.post("/api/lobby/quick-join", json={"player_name": "Stranger", "auto_play": False}).json()
    assert joined["game_id"] == standard["game_id"]


def test_api_quick_join_rejects_custom_variant(client):
    response = client.post("/api/lobby/quick-join", json={"player_name": "Stranger", "variant": "custom"})
    assert response.status_code == 400
