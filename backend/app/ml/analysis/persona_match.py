"""Match a player's trait vector to the best persona using weighted multi-factor scoring."""
from __future__ import annotations

import logging
import random
from typing import Dict, List, Optional, Set, Tuple

from backend.app.ml.analysis.persona_loader import Persona, load_personas, get_persona_by_id
from backend.app.ml.constants import DIMENSIONS

logger = logging.getLogger(__name__)

# --- Persona tiers ---
# Categories are unlocked based on game difficulty settings.
# Harder games reward more prestigious persona categories.

TIER_ELITE = {"superhero", "mythology"}          # Hard + turbulence + challenge
TIER_COMPETITIVE = {"achievement", "poker"}       # Hard/SmartHard or challenge
TIER_STANDARD = {"cartoon", "pokemon"}            # Medium bots
TIER_CASUAL = {"animal"}                          # Easy bots

ALL_CATEGORIES = TIER_ELITE | TIER_COMPETITIVE | TIER_STANDARD | TIER_CASUAL

TIERS_BY_LEVEL = {
    "elite": TIER_ELITE | TIER_COMPETITIVE | TIER_STANDARD | TIER_CASUAL,
    "competitive": TIER_COMPETITIVE | TIER_STANDARD | TIER_CASUAL,
    "standard": TIER_STANDARD | TIER_CASUAL,
    "casual": TIER_CASUAL,
}


def compute_tier(
    max_ai_difficulty: str,
    challenge_mode: bool,
    must_lose_mode: bool,
) -> str:
    """Determine persona tier from game settings.

    Args:
        max_ai_difficulty: highest AI difficulty in the game ("easy", "medium", "hard", "smart_hard")
        challenge_mode: whether challenge mode is enabled
        must_lose_mode: whether turbulence mode is enabled
    """
    is_hard = max_ai_difficulty in ("hard", "smart_hard")

    if is_hard and must_lose_mode and challenge_mode:
        return "elite"
    if is_hard or challenge_mode:
        return "competitive"
    if max_ai_difficulty == "medium":
        return "standard"
    return "casual"


# --- Scoring ---


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
    allowed_categories: Optional[Set[str]] = None,
) -> List[Tuple[str, float]]:
    """Return top-K personas with category diversity, filtered by allowed categories.

    Ensures at least one candidate per allowed category makes it into the pool.
    """
    recent = set(recent_ids or [])
    allowed = allowed_categories or ALL_CATEGORIES
    all_personas = [p for p in load_personas() if p.category in allowed]

    if not all_personas:
        all_personas = load_personas()

    # Score every persona
    scored_all: List[Tuple[Persona, float]] = []
    for persona in all_personas:
        raw_score = score_persona(player_vec, persona)
        novelty = 0.3 if persona.id in recent else 1.0
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
    tier: str = "elite",
) -> Persona:
    """Pick a persona from the top matches using weighted random selection.

    The tier controls which categories are available:
    - elite: all categories (superhero, mythology, achievement, poker, cartoon, pokemon, animal)
    - competitive: achievement, poker, cartoon, pokemon, animal
    - standard: cartoon, pokemon, animal
    - casual: animal only
    """
    if rng is None:
        rng = random.Random()

    allowed = TIERS_BY_LEVEL.get(tier, ALL_CATEGORIES)
    top = best_personas(player_vec, recent_ids, allowed_categories=allowed)
    if not top:
        return load_personas()[0]

    ids = [pair[0] for pair in top]
    scores = [max(pair[1], 0.01) for pair in top]

    # Add jitter so close scores don't always pick the same persona.
    # The jitter (up to 15% of score) breaks ties while still favoring
    # genuinely better matches.
    jittered = [score * (1.0 + rng.uniform(-0.15, 0.15)) for score in scores]

    chosen_id = rng.choices(ids, weights=jittered, k=1)[0]
    return get_persona_by_id(chosen_id)
