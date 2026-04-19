from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel

from .card import Card, Suit
from .player import Player


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
    THREE_QUICK = "3_quick"              # 5,3,5 (3 rounds, max 10 players)


class GameConfig(BaseModel):
    variant: DealingVariant = DealingVariant.TEN_TO_ONE
    must_lose_mode: bool = False


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
    elif variant == DealingVariant.THREE_QUICK:
        return [5, 3, 5]
    raise ValueError(f"Unknown variant: {variant}")


def max_players_for_variant(variant: DealingVariant) -> int:
    max_cards = max(get_round_sequence(variant))
    return 52 // max_cards
