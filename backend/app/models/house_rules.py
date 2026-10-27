"""House rules: per-game options a host picks before the game starts.

Two independent pieces live here:

- ``HouseRules`` changes how a round is played and scored (trump selection,
  dealer restriction, must-trump, scoring formulas). It applies to every
  dealing variant, including the built-in presets.
- ``CustomDeal`` describes the hand-size sequence for the ``custom`` dealing
  variant (starting cards, minimum, shape). The actual number of cards is
  resolved at game start, once the player count is known.

All defaults reproduce the classic game exactly, so a config that omits
these fields behaves the same as before house rules existed.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

DECK_SIZE = 52
MAX_CUSTOM_PLAYERS = 6  # table layout supports up to 6 seats
MAX_CUSTOM_START = DECK_SIZE // 2  # 26 cards each for a 2-player game


class TrumpMode(str, Enum):
    ROTATION = "rotation"  # spades, diamonds, clubs, hearts, repeat
    FLIP = "flip"          # turn the top undealt card; its suit is trump


class MadeScoring(str, Enum):
    CLASSIC = "classic"            # 0 -> 10, 1 -> 11, N -> N x 10
    TEN_PLUS_BID = "ten_plus_bid"  # 10 + bid


class MissedScoring(str, Enum):
    NEGATIVE = "negative"            # lose what you would have scored
    ZERO = "zero"                    # no points either way
    PER_TRICK_OFF = "per_trick_off"  # -10 for each trick you were off by


class HouseRules(BaseModel):
    trump_mode: TrumpMode = TrumpMode.ROTATION
    dealer_restriction: bool = True
    must_trump_when_void: bool = False
    made_scoring: MadeScoring = MadeScoring.CLASSIC
    missed_scoring: MissedScoring = MissedScoring.NEGATIVE

    model_config = {"frozen": True}

    def is_default(self) -> bool:
        return self == HouseRules()

    def is_training_compatible(self) -> bool:
        """True when decisions from this game are safe to train the ML bots on.

        Bots learn bidding and play from classic incentives. Different
        scoring, a relaxed dealer bid, or forced trumping change what a good
        decision looks like, so those games are kept out of the training
        data. Trump selection does not change incentives.
        """
        return (
            self.dealer_restriction
            and not self.must_trump_when_void
            and self.made_scoring == MadeScoring.CLASSIC
            and self.missed_scoring == MissedScoring.NEGATIVE
        )


class RoundShape(str, Enum):
    DOWN = "down"        # start -> min
    UP = "up"            # min -> start
    DOWN_UP = "down_up"  # start -> min -> start
    UP_DOWN = "up_down"  # min -> start -> min


class CustomDeal(BaseModel):
    # None means "as many as the deck allows for the number of players".
    start_cards: Optional[int] = Field(default=None, ge=1, le=MAX_CUSTOM_START)
    min_cards: int = Field(default=1, ge=1, le=MAX_CUSTOM_START)
    shape: RoundShape = RoundShape.DOWN
    # Play the turnaround round twice (e.g. 3,2,1,1,2,3 instead of 3,2,1,2,3).
    repeat_turn: bool = False

    model_config = {"frozen": True}

    def max_players(self) -> int:
        """Most players this deal can seat; every hand needs at least min_cards."""
        return max(2, min(MAX_CUSTOM_PLAYERS, DECK_SIZE // self.min_cards))

    def resolve_start(self, num_players: int) -> int:
        """Starting hand size for this many players, reduced to fit the deck."""
        deck_max = DECK_SIZE // max(num_players, 1)
        if self.start_cards is None:
            return deck_max
        return min(self.start_cards, deck_max)

    def card_sequence(self, num_players: int) -> List[int]:
        """Hand size for every round, for this many players."""
        high = self.resolve_start(num_players)
        low = min(self.min_cards, high)
        descending = list(range(high, low - 1, -1))
        ascending = list(reversed(descending))
        if self.shape == RoundShape.DOWN:
            return descending
        if self.shape == RoundShape.UP:
            return ascending
        if self.shape == RoundShape.DOWN_UP:
            tail = ascending if self.repeat_turn else ascending[1:]
            return descending + tail
        tail = descending if self.repeat_turn else descending[1:]
        return ascending + tail
