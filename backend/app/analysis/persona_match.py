"""Match a player's trait vector to the closest persona(s) via cosine similarity."""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Tuple

from backend.app.analysis.persona_loader import Persona, load_personas, DIMENSIONS


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Compute cosine similarity between two trait vectors."""
    dot = sum(vec_a.get(dim, 0) * vec_b.get(dim, 0) for dim in DIMENSIONS)
    mag_a = math.sqrt(sum(vec_a.get(dim, 0) ** 2 for dim in DIMENSIONS))
    mag_b = math.sqrt(sum(vec_b.get(dim, 0) ** 2 for dim in DIMENSIONS))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def best_personas(
    player_vec: Dict[str, float],
    recent_ids: Optional[List[str]] = None,
    top_k: int = 3,
) -> List[Tuple[str, float]]:
    """Return top-K personas by similarity, with novelty weighting."""
    recent = set(recent_ids or [])
    scored: List[Tuple[str, float]] = []

    for persona in load_personas():
        sim = cosine_similarity(player_vec, persona.traits)
        novelty = 0.6 if persona.id in recent else 1.0
        scored.append((persona.id, sim * novelty))

    scored.sort(key=lambda pair: -pair[1])
    return scored[:top_k]


def pick_persona(
    player_vec: Dict[str, float],
    recent_ids: Optional[List[str]] = None,
    rng: Optional[random.Random] = None,
) -> Persona:
    """Pick a persona from the top-3 matches using weighted random selection."""
    if rng is None:
        rng = random.Random()

    top3 = best_personas(player_vec, recent_ids)
    if not top3:
        # Fallback — should never happen with a populated corpus
        personas = load_personas()
        return personas[0]

    ids = [pair[0] for pair in top3]
    weights = [max(pair[1], 0.01) for pair in top3]

    chosen_id = rng.choices(ids, weights=weights, k=1)[0]

    for persona in load_personas():
        if persona.id == chosen_id:
            return persona

    # Fallback
    return load_personas()[0]
