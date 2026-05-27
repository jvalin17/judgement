from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from backend.app.ml.constants import DIMENSIONS

logger = logging.getLogger(__name__)


class Persona:
    """A single persona from the corpus."""

    __slots__ = ("id", "category", "name", "tagline", "fact", "traits", "weights", "triggers")

    def __init__(
        self, persona_id: str, category: str, name: str, tagline: str,
        traits: Dict[str, float],
        weights: Optional[Dict[str, float]] = None,
        triggers: Optional[List[Dict]] = None,
        fact: Optional[str] = None,
    ):
        self.id = persona_id
        self.category = category
        self.name = name
        self.tagline = tagline
        self.fact = fact or ""
        self.traits = traits
        self.weights = weights or {dim: 1.0 for dim in traits}
        self.triggers = triggers or []

    @property
    def key_dims(self) -> List[str]:
        """Top 3 dimensions by weight — used for affinity bonus."""
        sorted_dims = sorted(self.weights.items(), key=lambda item: -item[1])
        return [dim for dim, _ in sorted_dims[:3]]


@lru_cache(maxsize=1)
def load_personas() -> Tuple[Persona, ...]:
    """Load all personas from the bundled JSON corpus."""
    corpus_path = Path(__file__).parent / "personas.json"
    with open(corpus_path, "r") as fh:
        data = json.load(fh)

    assert data["version"] == 2, f"Unsupported corpus version: {data['version']}"

    personas: List[Persona] = []
    for entry in data["personas"]:
        traits = dict(zip(DIMENSIONS, entry["traits"]))
        weights_list = entry.get("weights")
        weights = dict(zip(DIMENSIONS, weights_list)) if weights_list else None
        triggers = entry.get("triggers", [])
        personas.append(Persona(
            persona_id=entry["id"],
            category=entry["category"],
            name=entry["name"],
            tagline=entry["tagline"],
            traits=traits,
            weights=weights,
            triggers=triggers,
            fact=entry.get("fact", ""),
        ))
    logger.debug("Loaded %d personas from %s", len(personas), corpus_path)
    return tuple(personas)


def get_persona_by_id(persona_id: str) -> Persona:
    """Look up a single persona by ID. Raises KeyError if not found."""
    for persona in load_personas():
        if persona.id == persona_id:
            return persona
    raise KeyError(f"Unknown persona: {persona_id}")
