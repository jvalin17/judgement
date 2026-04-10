"""Tests for round config JSON files and loader.

Bridge tests verify that the JSON configs produce the exact same (cards, trump)
sequence as the current runtime computation (get_round_sequence + TRUMP_ORDER).
"""

from backend.app.models.card import Suit, TRUMP_ORDER
from backend.app.models.game import DealingVariant, get_round_sequence
from backend.app.models.round_config import RoundConfig
from backend.app.game.round_config_loader import load_round_configs


# --- Count tests ---


def test_10_to_1_has_10_rounds():
    configs = load_round_configs(DealingVariant.TEN_TO_ONE)
    assert len(configs) == 10


def test_8_down_up_has_16_rounds():
    configs = load_round_configs(DealingVariant.EIGHT_DOWN_UP)
    assert len(configs) == 16


def test_10_down_up_has_20_rounds():
    configs = load_round_configs(DealingVariant.TEN_DOWN_UP)
    assert len(configs) == 20


# --- Immutability ---


def test_configs_are_frozen():
    configs = load_round_configs(DealingVariant.TEN_TO_ONE)
    assert isinstance(configs, tuple)
    config = configs[0]
    assert isinstance(config, RoundConfig)
    try:
        config.cards = 99
        assert False, "Should have raised"
    except Exception:
        pass


# --- Caching ---


def test_same_object_returned_on_repeated_calls():
    first = load_round_configs(DealingVariant.TEN_TO_ONE)
    second = load_round_configs(DealingVariant.TEN_TO_ONE)
    assert first is second


# --- Bridge tests: JSON matches runtime computation ---


def _expected_sequence(variant: DealingVariant):
    """Build expected (cards, trump) from the current runtime functions."""
    card_counts = get_round_sequence(variant)
    return [
        (cards, TRUMP_ORDER[(round_index) % len(TRUMP_ORDER)])
        for round_index, cards in enumerate(card_counts)
    ]


def test_bridge_10_to_1():
    configs = load_round_configs(DealingVariant.TEN_TO_ONE)
    expected = _expected_sequence(DealingVariant.TEN_TO_ONE)
    for config, (expected_cards, expected_trump) in zip(configs, expected):
        assert config.cards == expected_cards, f"Round {config.round}: cards mismatch"
        assert config.trump == expected_trump, f"Round {config.round}: trump mismatch"


def test_bridge_8_down_up():
    configs = load_round_configs(DealingVariant.EIGHT_DOWN_UP)
    expected = _expected_sequence(DealingVariant.EIGHT_DOWN_UP)
    for config, (expected_cards, expected_trump) in zip(configs, expected):
        assert config.cards == expected_cards, f"Round {config.round}: cards mismatch"
        assert config.trump == expected_trump, f"Round {config.round}: trump mismatch"


def test_bridge_10_down_up():
    configs = load_round_configs(DealingVariant.TEN_DOWN_UP)
    expected = _expected_sequence(DealingVariant.TEN_DOWN_UP)
    for config, (expected_cards, expected_trump) in zip(configs, expected):
        assert config.cards == expected_cards, f"Round {config.round}: cards mismatch"
        assert config.trump == expected_trump, f"Round {config.round}: trump mismatch"


# --- Round numbering ---


def test_round_numbers_are_sequential():
    for variant in DealingVariant:
        configs = load_round_configs(variant)
        for index, config in enumerate(configs):
            assert config.round == index + 1, f"{variant}: round {config.round} at index {index}"
