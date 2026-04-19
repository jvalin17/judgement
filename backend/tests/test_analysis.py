"""Tests for the mascot analysis module: persona loader, fingerprint, and matcher."""
import random

import pytest

from backend.app.analysis.persona_loader import load_personas, get_persona_by_id, DIMENSIONS
from backend.app.analysis.fingerprint import compute_fingerprint, project_round
from backend.app.analysis.persona_match import (
    cosine_similarity, best_personas, pick_persona,
)
from backend.app.models.session import SessionLog, RoundLog
from backend.app.models.game import Bid


# ---- Persona loader tests ----

class TestPersonaLoader:
    def test_loads_without_errors(self):
        personas = load_personas()
        assert len(personas) > 0

    def test_exactly_43_personas(self):
        assert len(load_personas()) == 43

    def test_all_personas_have_6_traits(self):
        for persona in load_personas():
            assert len(persona.traits) == 6
            for dim in DIMENSIONS:
                assert dim in persona.traits

    def test_all_trait_values_in_unit_range(self):
        for persona in load_personas():
            for dim, value in persona.traits.items():
                assert 0.0 <= value <= 1.0, f"{persona.id}.{dim} = {value}"

    def test_all_personas_have_required_fields(self):
        for persona in load_personas():
            assert persona.id
            assert persona.name
            assert persona.tagline
            assert persona.category in ("superhero", "animal", "poker", "cartoon", "pokemon")

    def test_get_persona_by_id_found(self):
        persona = get_persona_by_id("batman")
        assert persona.name == "Batman"

    def test_get_persona_by_id_not_found(self):
        with pytest.raises(KeyError):
            get_persona_by_id("nonexistent")

    def test_categories_all_represented(self):
        categories = {persona.category for persona in load_personas()}
        assert categories == {"superhero", "animal", "poker", "cartoon", "pokemon"}


# ---- Fingerprint tests ----

def _make_session_with_rounds(rounds_data):
    """Helper: create a SessionLog with given round data.
    Each round_data is (num_cards, bids_dict, tricks_won_dict).
    """
    session = SessionLog(game_id="test")
    for index, (num_cards, bids_dict, tricks_won) in enumerate(rounds_data):
        bids = [Bid(player_id=pid, amount=amt) for pid, amt in bids_dict.items()]
        session.rounds.append(RoundLog(
            round_number=index + 1,
            num_cards=num_cards,
            trump_suit="spades",
            dealer_id="p1",
            bids=bids,
            tricks_won=tricks_won,
            scores={},
        ))
    return session


class TestFingerprint:
    def test_high_bid_scores_high_risk(self):
        session = _make_session_with_rounds([
            (7, {"p1": 6, "p2": 2}, {"p1": 6, "p2": 1}),
        ])
        vec = compute_fingerprint(session, "p1")
        assert vec["risk"] > 0.8

    def test_exact_hit_scores_high_planning(self):
        session = _make_session_with_rounds([
            (5, {"p1": 3, "p2": 2}, {"p1": 3, "p2": 2}),
        ])
        vec = compute_fingerprint(session, "p1")
        assert vec["planning"] >= 0.9

    def test_low_bid_scores_low_risk(self):
        session = _make_session_with_rounds([
            (7, {"p1": 1, "p2": 3}, {"p1": 1, "p2": 3}),
        ])
        vec = compute_fingerprint(session, "p1")
        assert vec["risk"] < 0.3

    def test_missed_bid_scores_low_planning(self):
        session = _make_session_with_rounds([
            (10, {"p1": 0, "p2": 5}, {"p1": 5, "p2": 5}),
        ])
        vec = compute_fingerprint(session, "p1")
        assert vec["planning"] < 0.6

    def test_all_values_in_unit_range(self):
        rng = random.Random(42)
        for _ in range(50):
            num_cards = rng.randint(1, 10)
            bids = {"p1": rng.randint(0, num_cards), "p2": rng.randint(0, num_cards)}
            tricks = {"p1": rng.randint(0, num_cards), "p2": num_cards - rng.randint(0, num_cards)}
            session = _make_session_with_rounds([(num_cards, bids, tricks)])
            vec = compute_fingerprint(session, "p1")
            for dim, value in vec.items():
                assert 0.0 <= value <= 1.0, f"{dim} = {value}"

    def test_empty_session_returns_neutral(self):
        session = SessionLog(game_id="test")
        vec = compute_fingerprint(session, "p1")
        for dim in DIMENSIONS:
            assert vec[dim] == 0.5

    def test_multi_round_consistency(self):
        # Player hits bid every time → high consistency
        session = _make_session_with_rounds([
            (5, {"p1": 2, "p2": 3}, {"p1": 2, "p2": 3}),
            (4, {"p1": 1, "p2": 3}, {"p1": 1, "p2": 3}),
            (3, {"p1": 1, "p2": 2}, {"p1": 1, "p2": 2}),
        ])
        vec = compute_fingerprint(session, "p1")
        assert vec["consistency"] > 0.8

    def test_inconsistent_player_lower_consistency(self):
        # Player with wildly varying bid accuracy has lower consistency
        # than a player who always hits exact
        consistent_session = _make_session_with_rounds([
            (5, {"p1": 2, "p2": 3}, {"p1": 2, "p2": 3}),
            (5, {"p1": 3, "p2": 2}, {"p1": 3, "p2": 2}),
            (5, {"p1": 1, "p2": 4}, {"p1": 1, "p2": 4}),
        ])
        inconsistent_session = _make_session_with_rounds([
            (5, {"p1": 0, "p2": 3}, {"p1": 4, "p2": 1}),
            (5, {"p1": 5, "p2": 3}, {"p1": 0, "p2": 5}),
            (5, {"p1": 0, "p2": 3}, {"p1": 3, "p2": 2}),
        ])
        consistent_vec = compute_fingerprint(consistent_session, "p1")
        inconsistent_vec = compute_fingerprint(inconsistent_session, "p1")
        assert consistent_vec["consistency"] > inconsistent_vec["consistency"]


# ---- Cosine similarity tests ----

class TestCosineSimilarity:
    def test_identical_vectors_is_1(self):
        vec = {"risk": 0.5, "planning": 0.7, "patience": 0.3, "aggression": 0.8, "adaptability": 0.6, "consistency": 0.9}
        assert abs(cosine_similarity(vec, vec) - 1.0) < 1e-9

    def test_zero_vector_is_0(self):
        zero = {dim: 0.0 for dim in DIMENSIONS}
        other = {dim: 0.5 for dim in DIMENSIONS}
        assert cosine_similarity(zero, other) == 0.0


# ---- Persona matching tests ----

class TestPersonaMatch:
    def test_batman_vector_matches_batman(self):
        batman_vec = {"risk": 0.4, "planning": 0.95, "patience": 0.8, "aggression": 0.6, "adaptability": 0.7, "consistency": 0.85}
        top3 = best_personas(batman_vec)
        top3_ids = [pair[0] for pair in top3]
        assert "batman" in top3_ids

    def test_turtle_vector_matches_turtle_or_nit(self):
        turtle_vec = {"risk": 0.15, "planning": 0.8, "patience": 0.95, "aggression": 0.2, "adaptability": 0.3, "consistency": 0.95}
        top3 = best_personas(turtle_vec)
        top3_ids = [pair[0] for pair in top3]
        assert "turtle" in top3_ids or "nit" in top3_ids or "snorlax" in top3_ids

    def test_novelty_penalises_recent(self):
        vec = {"risk": 0.6, "planning": 0.7, "patience": 0.7, "aggression": 0.5, "adaptability": 0.9, "consistency": 0.6}
        without_recent = best_personas(vec, recent_ids=[])
        with_recent = best_personas(vec, recent_ids=[without_recent[0][0]])
        # The top persona should change or its score should decrease
        assert with_recent[0][1] <= without_recent[0][1]

    def test_pick_persona_deterministic_with_seed(self):
        vec = {"risk": 0.5, "planning": 0.5, "patience": 0.5, "aggression": 0.5, "adaptability": 0.5, "consistency": 0.5}
        result1 = pick_persona(vec, rng=random.Random(123))
        result2 = pick_persona(vec, rng=random.Random(123))
        assert result1.id == result2.id

    def test_variety_over_multiple_seeds(self):
        vec = {"risk": 0.5, "planning": 0.5, "patience": 0.5, "aggression": 0.5, "adaptability": 0.5, "consistency": 0.5}
        results = set()
        for seed in range(50):
            persona = pick_persona(vec, rng=random.Random(seed))
            results.add(persona.id)
        # With 50 different seeds over a top-3, we should see at least 2 distinct personas
        assert len(results) >= 2

    def test_pick_never_returns_unknown_id(self):
        known_ids = {persona.id for persona in load_personas()}
        rng = random.Random(42)
        for _ in range(100):
            vec = {dim: rng.random() for dim in DIMENSIONS}
            persona = pick_persona(vec, rng=rng)
            assert persona.id in known_ids


# ---- Integration: fingerprint → match ----

class TestFingerprintToMatch:
    def test_aggressive_player_gets_high_risk_persona(self):
        # High bid, misses often → high risk profile
        session = _make_session_with_rounds([
            (7, {"p1": 6, "p2": 2}, {"p1": 3, "p2": 4}),
            (5, {"p1": 5, "p2": 1}, {"p1": 2, "p2": 3}),
            (8, {"p1": 7, "p2": 3}, {"p1": 4, "p2": 4}),
        ])
        vec = compute_fingerprint(session, "p1")
        assert vec["risk"] > 0.7
        assert vec["aggression"] > 0.5
        # Verify persona match produces a result (any valid persona)
        top3 = best_personas(vec)
        assert len(top3) == 3
        known_ids = {p.id for p in load_personas()}
        assert all(pid in known_ids for pid, _ in top3)

    def test_conservative_player_gets_conservative_persona(self):
        session = _make_session_with_rounds([
            (7, {"p1": 1, "p2": 4}, {"p1": 1, "p2": 3}),
            (5, {"p1": 0, "p2": 3}, {"p1": 0, "p2": 2}),
            (8, {"p1": 1, "p2": 5}, {"p1": 1, "p2": 3}),
        ])
        vec = compute_fingerprint(session, "p1")
        top3 = best_personas(vec)
        top3_ids = [pair[0] for pair in top3]
        conservative_personas = {"turtle", "nit", "elephant", "snorlax", "ant", "owl", "shaktimaan"}
        assert any(pid in conservative_personas for pid in top3_ids)

    def test_game_over_event_includes_persona(self):
        """Verify the game_over event factory can include persona data."""
        from backend.app.models.events import game_over_event, PersonaAward
        persona = PersonaAward(
            persona_id="fox",
            persona_name="The Fox",
            persona_category="animal",
            persona_tagline="Cunning",
            traits={"risk": 0.6},
            player_traits={"risk": 0.5},
        )
        event = game_over_event(
            final_scores={"p1": 20},
            winners=["p1"],
            persona=persona,
        )
        assert event.event_type.value == "game_over"
        assert event.data["persona"]["persona_id"] == "fox"
        assert event.data["persona"]["persona_name"] == "The Fox"
        assert event.data["persona"]["player_traits"]["risk"] == 0.5

    def test_game_over_event_without_persona(self):
        """Verify game_over event works without persona (AI-only game)."""
        from backend.app.models.events import game_over_event
        event = game_over_event(final_scores={"p1": 20}, winners=["p1"])
        assert event.data["persona"] is None


class TestMascotIntegration:
    """Integration test: play a full game and verify persona is in GAME_OVER event."""

    def test_full_game_emits_persona_in_game_over(self):
        import random as stdlib_random
        from backend.app.models import Player, PlayerType, AIDifficulty, GameConfig, DealingVariant
        from backend.app.models.events import EventType
        from backend.app.game_manager import GameManager

        manager = GameManager()
        config = GameConfig(variant=DealingVariant.THREE_QUICK)
        players = [
            Player(id="human1", name="Alice", player_type=PlayerType.HUMAN),
            Player(id="ai1", name="Bot", player_type=PlayerType.AI, ai_difficulty=AIDifficulty.EASY),
        ]

        collected_events = []
        managed = manager.create_game(config, players)
        managed.add_event_callback(lambda e: collected_events.append(e))
        managed.engine.start_game()

        rng = stdlib_random.Random(42)
        max_iterations = 500
        iteration = 0
        while managed.engine.state.phase.value != "game_over" and iteration < max_iterations:
            iteration += 1
            phase = managed.engine.state.phase.value
            pid = managed.engine.state.current_player_id
            if phase == "round_over":
                managed.engine.continue_game()
                continue
            if not pid or pid.startswith("ai"):
                continue
            if phase == "bidding":
                valid = managed.engine.get_valid_bids(pid)
                managed.engine.place_bid(pid, rng.choice(valid))
            elif phase == "playing":
                valid = managed.engine.get_valid_cards(pid)
                managed.engine.play_card(pid, rng.choice(valid))

        # Find GAME_OVER events targeted at the human player
        game_over_events = [
            e for e in collected_events
            if e.event_type == EventType.GAME_OVER and e.player_id == "human1"
        ]
        assert len(game_over_events) == 1, f"Expected 1 GAME_OVER for human, got {len(game_over_events)}"

        event = game_over_events[0]
        persona = event.data.get("persona")
        assert persona is not None, "Persona should be included in GAME_OVER event"
        assert "persona_name" in persona
        assert "persona_tagline" in persona
        assert "traits" in persona
        assert "player_traits" in persona
        assert len(persona["player_traits"]) == 6

    def test_ai_only_game_has_no_persona(self):
        from backend.app.models import Player, PlayerType, AIDifficulty, GameConfig, DealingVariant
        from backend.app.models.events import EventType
        from backend.app.game_manager import GameManager

        manager = GameManager()
        config = GameConfig(variant=DealingVariant.THREE_QUICK)
        players = [
            Player(id="ai1", name="Bot1", player_type=PlayerType.AI, ai_difficulty=AIDifficulty.EASY),
            Player(id="ai2", name="Bot2", player_type=PlayerType.AI, ai_difficulty=AIDifficulty.EASY),
        ]

        collected_events = []
        managed = manager.create_game(config, players)
        managed.add_event_callback(lambda e: collected_events.append(e))
        managed.engine.start_game()

        max_iterations = 500
        iteration = 0
        while managed.engine.state.phase.value != "game_over" and iteration < max_iterations:
            iteration += 1
            if managed.engine.state.phase.value == "round_over":
                managed.engine.continue_game()

        game_over_events = [e for e in collected_events if e.event_type == EventType.GAME_OVER]
        assert len(game_over_events) == 2  # One per AI player
        for event in game_over_events:
            assert event.data.get("persona") is None
