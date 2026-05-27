"""Shared interface for all ML models in the learning engine.

Every model implements the GameModel protocol: predict(features, examples) -> Prediction | None.
Models are interchangeable — SmartHardAI delegates to whichever model it's assigned.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Protocol, runtime_checkable


class Prediction:
    """A prediction with value and confidence score."""
    __slots__ = ("value", "confidence")

    def __init__(self, value: int, confidence: float):
        self.value = value
        self.confidence = confidence


@runtime_checkable
class GameModel(Protocol):
    """Interface all ML models must implement."""

    @property
    def model_name(self) -> str:
        ...

    def predict(
        self,
        features: List[float],
        examples: List[dict],
        context: Optional[Dict] = None,
    ) -> Optional[Prediction]:
        ...
