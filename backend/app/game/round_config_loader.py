from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from backend.app.models.card import Suit
from backend.app.models.game import DealingVariant
from backend.app.models.round_config import RoundConfig

_ROUNDS_DIR = Path(__file__).parent / "rounds"

_VARIANT_FILE_MAP = {
    DealingVariant.TEN_TO_ONE: "10_to_1.json",
    DealingVariant.EIGHT_DOWN_UP: "8_down_up.json",
    DealingVariant.TEN_DOWN_UP: "10_down_up.json",
    DealingVariant.EIGHT_DOWN_UP_SHORT: "8_down_up_short.json",
    DealingVariant.THREE_QUICK: "3_quick.json",
}


@lru_cache(maxsize=None)
def load_round_configs(variant: DealingVariant) -> tuple:
    """Load round configs from JSON. Returns an immutable tuple (safe to cache)."""
    file_path = _ROUNDS_DIR / _VARIANT_FILE_MAP[variant]
    with open(file_path) as config_file:
        raw_rounds = json.load(config_file)
    return tuple(
        RoundConfig(round=entry["round"], cards=entry["cards"], trump=Suit(entry["trump"]))
        for entry in raw_rounds
    )
