"""Match a player's trait vector to the best persona using weighted multi-factor scoring."""
from __future__ import annotations

import logging
import random
from typing import Dict, List, Optional, Tuple

from backend.app.ml.analysis.persona_loader import Persona, load_personas, get_persona_by_id
from backend.app.ml.constants import DIMENSIONS

logger = logging.getLogger(__name__)


def _evaluate_trigger(trigger: Dict, player_vec: Dict[str, float]) -> bool:
    """Evaluate a single trigger condition against the player's trait vector."""
    trigger_type = trigger.get("type", "")

    if trigger_type == "min":
        return player_vec.get(trigger["dim"], 0.0) >= trigger["threshold"]
    elif trigger_type == "max":
        return player_vec.get(trigger["dim"], 1.0) <= trigger["threshold"]
    elif trigger_type == "range":
        val = player_vec.get(trigger["dim"], 0.5)
        return trigger["lo"] <= val <= trigger["hi"]
    elif trigger_type == "combo":
        return all(
            _evaluate_trigger(condition, player_vec)
            for condition in trigger.get("conditions", [])
        )
    return False


def score_persona(player_vec: Dict[str, float], persona: Persona) -> float:
    """Score how well a player matches a persona using weighted distance + affinity + triggers.

    Returns a score where higher = better match (typically 0.5 to 1.2).
    """
    # Phase 1: Weighted proximity score
    weighted_diffs = []
    total_weight = 0.0
    for dim in DIMENSIONS:
        player_val = player_vec.get(dim, 0.5)
        persona_val = persona.traits.get(dim, 0.5)
        weight = persona.weights.get(dim, 1.0)
        diff = abs(player_val - persona_val)
        weighted_diffs.append(diff * weight)
        total_weight += weight

    if total_weight > 0:
        weighted_avg_diff = sum(weighted_diffs) / total_weight
    else:
        weighted_avg_diff = 0.5

    proximity_score = 1.0 - weighted_avg_diff

    # Phase 2: Directional affinity bonus
    # Reward when both player and persona are extreme in the same direction
    # on the persona's most-weighted dimensions
    affinity_bonus = 0.0
    for dim in persona.key_dims:
        persona_val = persona.traits.get(dim, 0.5)
        player_val = player_vec.get(dim, 0.5)
        if persona_val >= 0.7 and player_val >= 0.7:
            affinity_bonus += 0.05
        elif persona_val <= 0.3 and player_val <= 0.3:
            affinity_bonus += 0.05

    # Phase 3: Achievement trigger bonus
    trigger_bonus = 0.0
    for trigger in persona.triggers:
        if _evaluate_trigger(trigger, player_vec):
            trigger_bonus += trigger.get("bonus", 0.1)

    return proximity_score + affinity_bonus + trigger_bonus


def best_personas(
    player_vec: Dict[str, float],
    recent_ids: Optional[List[str]] = None,
    top_k: int = 7,
) -> List[Tuple[str, float]]:
    """Return top-K personas with category diversity.

    Ensures at least one candidate per category makes it into the pool,
    so players can discover superheroes, mythology, etc. instead of
    always landing on the same few high-similarity categories.
    """
    recent = set(recent_ids or [])
    all_personas = load_personas()

    # Score every persona
    scored_all: List[Tuple[Persona, float]] = []
    for persona in all_personas:
        raw_score = score_persona(player_vec, persona)
        novelty = 0.6 if persona.id in recent else 1.0
        scored_all.append((persona, raw_score * novelty))

    # Pick the best persona from each category first
    best_by_category: Dict[str, Tuple[Persona, float]] = {}
    for persona, score in scored_all:
        cat = persona.category
        if cat not in best_by_category or score > best_by_category[cat][1]:
            best_by_category[cat] = (persona, score)

    # Start with one per category (sorted by score)
    diverse: List[Tuple[str, float]] = [
        (persona.id, score)
        for persona, score in sorted(best_by_category.values(), key=lambda x: -x[1])
    ]

    # Fill remaining slots from the global top scores
    selected_ids = {pair[0] for pair in diverse}
    scored_all.sort(key=lambda x: -x[1])
    for persona, score in scored_all:
        if len(diverse) >= top_k:
            break
        if persona.id not in selected_ids:
            diverse.append((persona.id, score))
            selected_ids.add(persona.id)

    diverse.sort(key=lambda pair: -pair[1])
    return diverse[:top_k]


def pick_persona(
    player_vec: Dict[str, float],
    recent_ids: Optional[List[str]] = None,
    rng: Optional[random.Random] = None,
) -> Persona:
    """Pick a persona from the top matches using weighted random selection.

    The candidate pool is category-diverse (best_personas guarantees at least
    one from each category), so even categories that are harder to match
    have a chance of being selected.
    """
    if rng is None:
        rng = random.Random()

    top = best_personas(player_vec, recent_ids)
    if not top:
        return load_personas()[0]

    ids = [pair[0] for pair in top]
    weights = [max(pair[1], 0.01) for pair in top]

    chosen_id = rng.choices(ids, weights=weights, k=1)[0]
    return get_persona_by_id(chosen_id)
