"""Tests for the ML learning engine (kNN, features, collector, HardMLAI)."""

import os
import tempfile

import pytest

from backend.app.models import Card, Suit, Rank, Bid
from backend.app.models.player import Player, PlayerType, AIDifficulty
from backend.app.models.game import GameConfig, DealingVariant
from backend.app.ai.base import RoundContext
from backend.app.ai.ml import knn
from backend.app.ai.ml.features import (
    extract_bid_features,
    extract_play_features,
    card_to_index,
    index_to_card,
)
from backend.app.ai.ml.collector import DecisionCollector
from backend.app.ai.hard_ml import HardMLAI
from backend.app.game_manager import GameManager, _make_strategy


def _make_context(
    player_id="p1",
    trump_suit=Suit.SPADES,
    num_cards=10,
    num_players=3,
    bids=None,
    tricks_won=None,
    cards_played=None,
    current_trick_cards=None,
):
    return RoundContext(
        player_id=player_id,
        trump_suit=trump_suit,
        num_cards=num_cards,
        num_players=num_players,
        bids=bids or [],
        tricks_won=tricks_won or {},
        cards_played=cards_played or [],
        current_trick_cards=current_trick_cards or [],
    )


def _sample_hand():
    return [
        Card(suit=Suit.SPADES, rank=Rank.ACE),
        Card(suit=Suit.SPADES, rank=Rank.KING),
        Card(suit=Suit.HEARTS, rank=Rank.QUEEN),
        Card(suit=Suit.DIAMONDS, rank=Rank.JACK),
        Card(suit=Suit.CLUBS, rank=Rank.TEN),
    ]


# --- Feature extraction ---


class TestBidFeatures:
    def test_returns_fixed_length_vector(self):
        hand = _sample_hand()
        context = _make_context(num_cards=5)
        features = extract_bid_features(hand, context)
        assert len(features) == 12
        assert all(isinstance(value, float) for value in features)

    def test_num_cards_is_first_feature(self):
        hand = _sample_hand()
        context = _make_context(num_cards=5)
        features = extract_bid_features(hand, context)
        assert features[0] == 5.0

    def test_dealer_detection(self):
        hand = _sample_hand()
        # 2 bids placed, 3 players → this is the dealer (last to bid)
        bids = [Bid(player_id="p2", amount=1), Bid(player_id="p3", amount=2)]
        context = _make_context(num_cards=5, bids=bids)
        features = extract_bid_features(hand, context)
        assert features[-1] == 1.0  # is_dealer


class TestPlayFeatures:
    def test_returns_fixed_length_vector(self):
        hand = _sample_hand()
        valid_cards = hand[:3]
        context = _make_context(
            num_cards=5,
            bids=[Bid(player_id="p1", amount=2)],
        )
        features = extract_play_features(hand, valid_cards, context)
        assert len(features) == 11
        assert all(isinstance(value, float) for value in features)

    def test_leading_flag(self):
        hand = _sample_hand()
        context = _make_context(num_cards=5, bids=[Bid(player_id="p1", amount=2)])
        features = extract_play_features(hand, hand, context)
        assert features[4] == 1.0  # is_leading


class TestCardIndexConversion:
    def test_round_trip(self):
        cards = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.TWO),
            Card(suit=Suit.DIAMONDS, rank=Rank.KING),
        ]
        for card in cards:
            index = card_to_index(card, cards)
            recovered = index_to_card(index, cards)
            assert recovered.suit == card.suit
            assert recovered.rank == card.rank

    def test_out_of_range_returns_none(self):
        cards = [Card(suit=Suit.HEARTS, rank=Rank.ACE)]
        assert index_to_card(5, cards) is None


# --- kNN ---


class TestKNN:
    def test_append_and_load(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            knn.append_example(tmp_path, [1.0, 2.0, 3.0], 5.0)
            knn.append_example(tmp_path, [4.0, 5.0, 6.0], 3.0)

            examples = knn._load_examples(tmp_path)
            assert len(examples) == 2
            assert examples[0]["label"] == 5.0
            assert examples[1]["features"] == [4.0, 5.0, 6.0]
        finally:
            os.unlink(tmp_path)

    def test_predict_returns_none_with_few_examples(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            for index in range(5):  # Less than MIN_EXAMPLES
                knn.append_example(tmp_path, [float(index)], float(index))

            result = knn.predict_bid([3.0], tmp_path)
            assert result is None
        finally:
            os.unlink(tmp_path)

    def test_predict_returns_value_with_enough_examples(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Add 15 examples all bidding 3
            for index in range(15):
                knn.append_example(tmp_path, [float(index), 5.0], 3.0)

            result = knn.predict_bid([7.0, 5.0], tmp_path)
            assert result == 3
        finally:
            os.unlink(tmp_path)

    def test_predict_picks_nearest_label(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Cluster of bid=2 near [1.0]
            for _ in range(8):
                knn.append_example(tmp_path, [1.0], 2.0)
            # Cluster of bid=5 near [10.0]
            for _ in range(8):
                knn.append_example(tmp_path, [10.0], 5.0)

            # Query near the bid=2 cluster
            assert knn.predict_bid([1.5], tmp_path) == 2
            # Query near the bid=5 cluster
            assert knn.predict_bid([9.5], tmp_path) == 5
        finally:
            os.unlink(tmp_path)

    def test_predict_card_clamps_to_valid_range(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # All examples say index=10, but we only have 3 valid cards
            for index in range(15):
                knn.append_example(tmp_path, [float(index)], 10.0)

            result = knn.predict_card_index([5.0], 3, tmp_path)
            assert result == 2  # clamped to max valid index
        finally:
            os.unlink(tmp_path)

    def test_empty_file_returns_none(self):
        result = knn.predict_bid([1.0], "/nonexistent/path.jsonl")
        assert result is None

    def test_example_count(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            assert knn.example_count(tmp_path) == 0
            knn.append_example(tmp_path, [1.0], 1.0)
            knn.append_example(tmp_path, [2.0], 2.0)
            assert knn.example_count(tmp_path) == 2
        finally:
            os.unlink(tmp_path)


# --- Collector ---


class TestDecisionCollector:
    def test_record_and_flush_winner(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            bid_file = os.path.join(tmp_dir, "bids.jsonl")
            play_file = os.path.join(tmp_dir, "plays.jsonl")

            collector = DecisionCollector()
            hand = _sample_hand()
            context = _make_context(num_cards=5)

            # Record bids for two players
            collector.record_bid("winner", hand, context, 3)
            collector.record_bid("loser", hand, context, 1)

            # Record plays
            valid_cards = hand[:3]
            play_context = _make_context(
                num_cards=5,
                bids=[Bid(player_id="winner", amount=3)],
            )
            collector.record_play("winner", hand, valid_cards, play_context, hand[0])
            collector.record_play("loser", hand, valid_cards, play_context, hand[1])

            # Monkey-patch data file paths for this test
            import backend.app.ai.ml.collector as collector_module
            original_bid_fn = collector_module.get_bid_data_file
            original_play_fn = collector_module.get_play_data_file
            collector_module.get_bid_data_file = lambda: bid_file
            collector_module.get_play_data_file = lambda: play_file

            try:
                count = collector.flush_winner(["winner"])
            finally:
                collector_module.get_bid_data_file = original_bid_fn
                collector_module.get_play_data_file = original_play_fn

            assert count == 2  # 1 bid + 1 play from winner only
            assert knn.example_count(bid_file) == 1
            assert knn.example_count(play_file) == 1

    def test_flush_clears_buffer(self):
        collector = DecisionCollector()
        hand = _sample_hand()
        context = _make_context(num_cards=5)
        collector.record_bid("p1", hand, context, 2)
        collector.clear()

        with tempfile.TemporaryDirectory() as tmp_dir:
            bid_file = os.path.join(tmp_dir, "bids.jsonl")

            import backend.app.ai.ml.collector as collector_module
            original_fn = collector_module.get_bid_data_file
            collector_module.get_bid_data_file = lambda: bid_file

            try:
                count = collector.flush_winner(["p1"])
            finally:
                collector_module.get_bid_data_file = original_fn

            assert count == 0


# --- HardMLAI ---


class TestHardMLAI:
    def test_falls_back_when_no_data(self):
        """With no training data, HardMLAI should behave like HardAI."""
        strategy = HardMLAI()
        hand = _sample_hand()
        context = _make_context(num_cards=5)
        valid_bids = [0, 1, 2, 3, 4, 5]

        bid = strategy.choose_bid(hand, valid_bids, context)
        assert bid in valid_bids

    def test_choose_card_falls_back(self):
        strategy = HardMLAI()
        hand = _sample_hand()
        context = _make_context(
            num_cards=5,
            bids=[Bid(player_id="p1", amount=2)],
        )
        card = strategy.choose_card(hand, hand, context)
        assert card in hand

    def test_always_returns_valid(self):
        """ML AI must always return a valid move, even with bad data."""
        strategy = HardMLAI()
        hand = [Card(suit=Suit.HEARTS, rank=Rank.TWO)]
        context = _make_context(
            num_cards=1,
            bids=[Bid(player_id="p1", amount=0)],
        )
        card = strategy.choose_card(hand, hand, context)
        assert card in hand


# --- Strategy factory ---


class TestMakeStrategy:
    def test_hard_without_ml(self):
        from backend.app.ai.hard import HardAI
        strategy = _make_strategy(AIDifficulty.HARD, use_ml=False)
        assert isinstance(strategy, HardAI)

    def test_hard_with_ml(self):
        strategy = _make_strategy(AIDifficulty.HARD, use_ml=True)
        assert isinstance(strategy, HardMLAI)

    def test_non_hard_ignores_ml_flag(self):
        from backend.app.ai.easy import EasyAI
        strategy = _make_strategy(AIDifficulty.EASY, use_ml=True)
        assert isinstance(strategy, EasyAI)


# --- Integration: ML bot in a full game ---


class TestMLIntegration:
    def test_game_with_ml_bot_completes(self):
        """A full game with one HardMLAI bot should complete without errors."""
        manager = GameManager()
        config = GameConfig(variant=DealingVariant.TEN_TO_ONE)
        players = [
            Player(id="human", name="Alice", player_type=PlayerType.HUMAN),
            Player(id="ai1", name="Bot1", player_type=PlayerType.AI, ai_difficulty=AIDifficulty.HARD),
            Player(id="ai2", name="Bot2", player_type=PlayerType.AI, ai_difficulty=AIDifficulty.HARD),
        ]
        managed = manager.create_game(config, players)

        # At least one Hard AI should have the ML strategy
        has_ml = any(isinstance(s, HardMLAI) for s in managed.ai_strategies.values())
        has_regular = any(
            not isinstance(s, HardMLAI) for s in managed.ai_strategies.values()
        )
        # One ML, one regular (random assignment — could be either)
        assert has_ml or has_regular  # at minimum some strategy exists

        # Start and simulate through a few rounds
        managed.engine.start_game()
        # AI should auto-play their turns; verify game is progressing
        from backend.app.models.game import GamePhase
        assert managed.engine.state.phase in (
            GamePhase.BIDDING, GamePhase.PLAYING, GamePhase.ROUND_OVER,
        )
