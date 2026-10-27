from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from backend.app.models.card import Suit, TRUMP_ORDER
from backend.app.models.game import DealingVariant, GameConfig
from backend.app.models.house_rules import MAX_CUSTOM_PLAYERS
from backend.app.models.round_config import RoundConfig

_ROUNDS_DIR = Path(__file__).parent / "rounds"

_VARIANT_FILE_MAP = {
    DealingVariant.TEN_TO_ONE: "10_to_1.json",
    DealingVariant.EIGHT_DOWN_UP: "8_down_up.json",
    DealingVariant.TEN_DOWN_UP: "10_down_up.json",
    DealingVariant.EIGHT_DOWN_UP_SHORT: "8_down_up_short.json",
    DealingVariant.EIGHT_TO_THREE: "8_to_3.json",
    DealingVariant.THREE_QUICK: "3_quick.json",
}


@lru_cache(maxsize=None)
def load_round_configs(variant: DealingVariant) -> tuple:
    """Load round configs from JSON. Returns an immutable tuple (safe to cache).

    The custom variant has no file. It returns the default custom deal at a
    full table, matching get_round_sequence(CUSTOM).
    """
    if variant == DealingVariant.CUSTOM:
        return build_custom_round_configs(GameConfig(variant=variant), MAX_CUSTOM_PLAYERS)
    file_path = _ROUNDS_DIR / _VARIANT_FILE_MAP[variant]
    with open(file_path) as config_file:
        raw_rounds = json.load(config_file)
    return tuple(
        RoundConfig(round=entry["round"], cards=entry["cards"], trump=Suit(entry["trump"]))
        for entry in raw_rounds
    )


def build_custom_round_configs(config: GameConfig, num_players: int) -> tuple:
    """Round configs for the custom variant, sized for the actual player count.

    Trump follows the same spades, diamonds, clubs, hearts rotation the
    presets use. Under the "flip" house rule the round manager may replace
    it with the suit of the turned card.
    """
    sequence = config.resolved_custom_deal().card_sequence(num_players)
    return tuple(
        RoundConfig(round=index + 1, cards=cards, trump=TRUMP_ORDER[index % len(TRUMP_ORDER)])
        for index, cards in enumerate(sequence)
    )


def build_round_configs(config: GameConfig, num_players: int) -> tuple:
    """Round configs for a game: preset file, or a custom sequence."""
    if config.variant == DealingVariant.CUSTOM:
        return build_custom_round_configs(config, num_players)
    return load_round_configs(config.variant)
