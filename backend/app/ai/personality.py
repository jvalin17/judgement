from __future__ import annotations

import random


class AIPersonality:
    """Weights controlling Hard AI strategic tendencies.

    Each weight is 0.0–1.0. The personality is rolled once per AI instance
    (per game), giving each opponent a consistent style that varies across games.
    """

    def __init__(
        self,
        aggression: float,
        trump_conservation: float,
        opponent_focus: float,
        risk_tolerance: float,
    ):
        self.aggression = aggression
        self.trump_conservation = trump_conservation
        self.opponent_focus = opponent_focus
        self.risk_tolerance = risk_tolerance

    def __repr__(self) -> str:
        return (
            f"AIPersonality(agg={self.aggression:.2f}, trump={self.trump_conservation:.2f}, "
            f"opp={self.opponent_focus:.2f}, risk={self.risk_tolerance:.2f})"
        )


def random_personality() -> AIPersonality:
    """Generate a random personality with weights clustered around expert-level play."""
    return AIPersonality(
        aggression=random.triangular(0.3, 1.0, 0.65),
        trump_conservation=random.triangular(0.3, 1.0, 0.65),
        opponent_focus=random.triangular(0.3, 1.0, 0.65),
        risk_tolerance=random.triangular(0.2, 0.9, 0.55),
    )


# --- Predefined archetypes ---

AGGRESSIVE = AIPersonality(
    aggression=0.9, trump_conservation=0.3, opponent_focus=0.5, risk_tolerance=0.8,
)

CONSERVATIVE = AIPersonality(
    aggression=0.3, trump_conservation=0.9, opponent_focus=0.6, risk_tolerance=0.3,
)

TACTICAL = AIPersonality(
    aggression=0.5, trump_conservation=0.6, opponent_focus=0.9, risk_tolerance=0.5,
)

GAMBLER = AIPersonality(
    aggression=0.8, trump_conservation=0.4, opponent_focus=0.3, risk_tolerance=0.9,
)
