from __future__ import annotations

import random
from typing import List

from backend.app.models import Card
from backend.app.ai.base import AIStrategy, RoundContext


class EasyAI(AIStrategy):

    strategy_type = "easy"

    def choose_bid(
        self,
        hand: List[Card],
        valid_bids: List[int],
        context: RoundContext,
    ) -> int:
        return random.choice(valid_bids)

    def choose_card(
        self,
        hand: List[Card],
        valid_cards: List[Card],
        context: RoundContext,
    ) -> Card:
        return random.choice(valid_cards)
