from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel

from .game import Bid


class RoundLog(BaseModel):
    round_number: int
    num_cards: int
    trump_suit: str
    dealer_id: str
    bids: List[Bid] = []
    tricks_won: Dict[str, int] = {}
    scores: Dict[str, int] = {}


class SessionLog(BaseModel):
    game_id: str
    players: List[Dict[str, str]] = []
    variant: str = ""
    rounds: List[RoundLog] = []
    final_scores: Dict[str, int] = {}
    winners: List[str] = []
