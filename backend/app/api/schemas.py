from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel

from backend.app.models.player import AIDifficulty
from backend.app.models.game import DealingVariant


class PlayerSetup(BaseModel):
    name: str
    is_ai: bool = False
    ai_difficulty: Optional[AIDifficulty] = None


class CreateGameRequest(BaseModel):
    variant: DealingVariant = DealingVariant.TEN_TO_ONE
    must_lose_mode: bool = False
    players: List[PlayerSetup]


class CreateGameResponse(BaseModel):
    game_id: str
    player_ids: Dict[str, str]  # name -> assigned id


class GameStateResponse(BaseModel):
    game_id: str
    phase: str
    players: List[Dict]
    current_player_id: Optional[str] = None
    trump_suit: Optional[str] = None
    num_cards: Optional[int] = None
    round_number: Optional[int] = None
    dealer_id: Optional[str] = None
    bids: List[Dict] = []
    current_trick: List[Dict] = []
    tricks_won: Dict[str, int] = {}
    cumulative_scores: Dict[str, int] = {}


class PlayerHandResponse(BaseModel):
    hand: List[Dict]
    valid_cards: List[Dict] = []
    valid_bids: List[int] = []


class BidRequest(BaseModel):
    player_id: str
    amount: int


class PlayCardRequest(BaseModel):
    player_id: str
    suit: str
    rank: int


class ActionResponse(BaseModel):
    success: bool
    message: str = ""


class SessionLogResponse(BaseModel):
    game_id: str
    players: List[Dict[str, str]]
    variant: str
    rounds: List[Dict]
    final_scores: Dict[str, int]
    winners: List[str]
