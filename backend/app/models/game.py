from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel

from .card import Card, Suit
from .player import Player
from .house_rules import CustomDeal, HouseRules, MAX_CUSTOM_PLAYERS


class GamePhase(str, Enum):
    LOBBY = "lobby"
    DEALING = "dealing"
    BIDDING = "bidding"
    PLAYING = "playing"
    ROUND_OVER = "round_over"
    GAME_OVER = "game_over"


class DealingVariant(str, Enum):
    TEN_TO_ONE = "10_to_1"           # 10→1 (10 rounds)
    EIGHT_DOWN_UP = "8_down_up"      # 8→1, 1→8 (16 rounds, max 6 players)
    TEN_DOWN_UP = "10_down_up"       # 10→1, 1→10 (20 rounds)
    EIGHT_DOWN_UP_SHORT = "8_down_up_short"  # 8→4, 4→8 (10 rounds, max 6 players)
    EIGHT_TO_THREE = "8_to_3"            # 8→4 (5 rounds, max 6 players)
    THREE_QUICK = "3_quick"              # 5,3,5 (3 rounds, max 10 players)
    CUSTOM = "custom"                    # host-defined hand sizes (see CustomDeal)


class GameConfig(BaseModel):
    variant: DealingVariant = DealingVariant.TEN_TO_ONE
    must_lose_mode: bool = False
    challenge_mode: bool = False
    house_rules: HouseRules = HouseRules()
    # Only used when variant == CUSTOM. Filled with defaults if missing.
    custom_deal: Optional[CustomDeal] = None

    def resolved_custom_deal(self) -> CustomDeal:
        return self.custom_deal or CustomDeal()

    def is_standard(self) -> bool:
        """True for a preset variant played with classic rules."""
        return self.variant != DealingVariant.CUSTOM and self.house_rules.is_default()


class Bid(BaseModel):
    player_id: str
    amount: int


class TrickPlay(BaseModel):
    player_id: str
    card: Card


class Trick(BaseModel):
    plays: List[TrickPlay] = []
    lead_suit: Optional[Suit] = None
    winner_id: Optional[str] = None


class RoundState(BaseModel):
    round_number: int
    num_cards: int
    trump_suit: Suit
    dealer_id: str
    hands: Dict[str, List[Card]] = {}
    bids: List[Bid] = []
    tricks: List[Trick] = []
    current_trick: Trick = Trick()
    tricks_won: Dict[str, int] = {}
    scores: Dict[str, int] = {}
    # The face-up card that set trump when house rules use "flip".
    trump_card: Optional[Card] = None


class GameFullState(BaseModel):
    game_id: str
    config: GameConfig
    players: List[Player] = []
    phase: GamePhase = GamePhase.LOBBY
    current_round: Optional[RoundState] = None
    cumulative_scores: Dict[str, int] = {}
    current_player_id: Optional[str] = None


def get_round_sequence(variant: DealingVariant) -> list[int]:
    if variant == DealingVariant.TEN_TO_ONE:
        return list(range(10, 0, -1))
    elif variant == DealingVariant.EIGHT_DOWN_UP:
        return list(range(8, 0, -1)) + list(range(1, 9))
    elif variant == DealingVariant.TEN_DOWN_UP:
        return list(range(10, 0, -1)) + list(range(1, 11))
    elif variant == DealingVariant.EIGHT_DOWN_UP_SHORT:
        return list(range(8, 4, -1)) + list(range(5, 9))
    elif variant == DealingVariant.EIGHT_TO_THREE:
        return list(range(8, 3, -1))
    elif variant == DealingVariant.THREE_QUICK:
        return [5, 3, 5]
    elif variant == DealingVariant.CUSTOM:
        # Without a player count, describe the default custom deal at a full
        # table. Real games use GameConfig + build_round_configs instead.
        return CustomDeal().card_sequence(MAX_CUSTOM_PLAYERS)
    raise ValueError(f"Unknown variant: {variant}")


def max_players_for_variant(variant: DealingVariant) -> int:
    if variant == DealingVariant.CUSTOM:
        return MAX_CUSTOM_PLAYERS
    max_cards = max(get_round_sequence(variant))
    return 52 // max_cards


def max_players_for_config(config: GameConfig) -> int:
    """Seat limit for a game, taking a custom deal's minimum hand into account."""
    if config.variant == DealingVariant.CUSTOM:
        return config.resolved_custom_deal().max_players()
    return max_players_for_variant(config.variant)
