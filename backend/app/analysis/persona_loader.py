from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple


class Persona:
    """A single persona from the corpus."""

    __slots__ = ("id", "category", "name", "tagline", "traits")

    def __init__(
        self, persona_id: str, category: str, name: str, tagline: str,
        traits: Dict[str, float],
    ):
        self.id = persona_id
        self.category = category
        self.name = name
        self.tagline = tagline
        self.traits = traits


DIMENSIONS = ("risk", "planning", "patience", "aggression", "adaptability", "consistency")


@lru_cache(maxsize=1)
def load_personas() -> Tuple[Persona, ...]:
    """Load all personas from the bundled JSON corpus."""
    corpus_path = Path(__file__).parent / "personas.json"
    with open(corpus_path, "r") as fh:
        data = json.load(fh)

    assert data["version"] == 1, f"Unsupported corpus version: {data['version']}"

    personas: List[Persona] = []
    for entry in data["personas"]:
        traits = dict(zip(DIMENSIONS, entry["traits"]))
        personas.append(Persona(
            persona_id=entry["id"],
            category=entry["category"],
            name=entry["name"],
            tagline=entry["tagline"],
            traits=traits,
        ))
    return tuple(personas)


def get_persona_by_id(persona_id: str) -> Persona:
    """Look up a single persona by ID. Raises KeyError if not found."""
    for persona in load_personas():
        if persona.id == persona_id:
            return persona
    raise KeyError(f"Unknown persona: {persona_id}")
