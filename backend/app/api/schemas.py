from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel

from backend.app.models.player import AIDifficulty
from backend.app.models.game import DealingVariant


class PlayerSetup(BaseModel):
    name: str
    is_ai: bool = False
    ai_difficulty: Optional[AIDifficulty] = None


class GameSpeed(BaseModel):
    """Delays (seconds) between AI actions. Controls game pacing."""
    after_card_played: float = 2.0
    after_trick_complete: float = 3.0
    after_round_complete: float = 1.5
    after_bidding_complete: float = 1.5


class CreateGameRequest(BaseModel):
    variant: DealingVariant = DealingVariant.TEN_TO_ONE
    must_lose_mode: bool = False
    challenge_mode: bool = False
    players: List[PlayerSetup]
    speed: Optional[GameSpeed] = None
    auto_start: bool = True
    is_public: bool = False
    share_data: bool = False


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


class JoinGameRequest(BaseModel):
    player_name: str
    share_data: bool = False


class AddBotRequest(BaseModel):
    player_id: str  # caller — must be the host
    difficulty: AIDifficulty = AIDifficulty.MEDIUM
    name: Optional[str] = None  # if None, auto-pick from sweets list


class JoinGameResponse(BaseModel):
    player_id: str
    game_id: str


class LobbyStateResponse(BaseModel):
    game_id: str
    phase: str
    variant: str
    must_lose_mode: bool
    players: List[Dict]
    host_player_id: Optional[str] = None
    max_players: int


class LobbyGameInfo(BaseModel):
    game_id: str
    host_name: Optional[str] = None
    variant: str
    must_lose_mode: bool
    player_count: int
    max_players: int


class LobbyListResponse(BaseModel):
    games: List[LobbyGameInfo]


class QuickJoinRequest(BaseModel):
    player_name: str
    variant: Optional[str] = None
    auto_play: bool = True
