from pydantic import BaseModel

from .card import Suit


class RoundConfig(BaseModel):
    """Immutable config for a single round — loaded from JSON, never mutated."""

    round: int
    cards: int
    trump: Suit

    model_config = {"frozen": True}
