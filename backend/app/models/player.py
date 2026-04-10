from enum import Enum
from typing import Optional
from pydantic import BaseModel


class PlayerType(str, Enum):
    HUMAN = "human"
    AI = "ai"


class AIDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Player(BaseModel):
    id: str
    name: str
    player_type: PlayerType
    ai_difficulty: Optional[AIDifficulty] = None
