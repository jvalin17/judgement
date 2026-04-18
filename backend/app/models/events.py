from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class EventType(str, Enum):
    GAME_STARTED = "game_started"
    ROUND_STARTED = "round_started"
    CARDS_DEALT = "cards_dealt"
    BID_PLACED = "bid_placed"
    BIDDING_COMPLETE = "bidding_complete"
    CARD_PLAYED = "card_played"
    TRICK_COMPLETE = "trick_complete"
    ROUND_COMPLETE = "round_complete"
    GAME_OVER = "game_over"
    TURN_CHANGED = "turn_changed"
    INVALID_ACTION = "invalid_action"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    AUTO_START_COUNTDOWN = "auto_start_countdown"
    GAME_STARTING = "game_starting"
    PLAYER_RECONNECTED = "player_reconnected"
    PLAYER_DISCONNECTED = "player_disconnected"
    MASCOT_PERSONA_AWARDED = "mascot_persona_awarded"


class GameEvent(BaseModel):
    event_type: EventType
    data: Dict[str, Any] = {}
    player_id: Optional[str] = None  # target player (None = broadcast)


# --- Typed event data models ---


class GameStartedData(BaseModel):
    players: List[dict]
    variant: str


class RoundStartedData(BaseModel):
    round_number: int
    num_cards: int
    trump_suit: str
    dealer_id: str


class CardsDealtData(BaseModel):
    hand: List[dict]


class BidPlacedData(BaseModel):
    player_id: str
    amount: int


class BiddingCompleteData(BaseModel):
    bids: List[dict]


class CardPlayedData(BaseModel):
    player_id: str
    card: dict


class TrickCompleteData(BaseModel):
    winner_id: str
    tricks_won: Dict[str, int]


class RoundCompleteData(BaseModel):
    round_scores: Dict[str, int]
    cumulative_scores: Dict[str, int]
    tricks_won: Dict[str, int]
    bids: List[dict]


class GameOverData(BaseModel):
    final_scores: Dict[str, int]
    winners: List[str]


class TurnChangedData(BaseModel):
    player_id: str
    phase: str


class InvalidActionData(BaseModel):
    reason: str


# --- Factory functions ---


def game_started_event(players: List[dict], variant: str) -> GameEvent:
    data = GameStartedData(players=players, variant=variant)
    return GameEvent(event_type=EventType.GAME_STARTED, data=data.model_dump())


def round_started_event(
    round_number: int, num_cards: int, trump_suit: str, dealer_id: str,
) -> GameEvent:
    data = RoundStartedData(
        round_number=round_number, num_cards=num_cards,
        trump_suit=trump_suit, dealer_id=dealer_id,
    )
    return GameEvent(event_type=EventType.ROUND_STARTED, data=data.model_dump())


def cards_dealt_event(hand: List[dict], player_id: str) -> GameEvent:
    data = CardsDealtData(hand=hand)
    return GameEvent(
        event_type=EventType.CARDS_DEALT, data=data.model_dump(), player_id=player_id,
    )


def bid_placed_event(player_id: str, amount: int) -> GameEvent:
    data = BidPlacedData(player_id=player_id, amount=amount)
    return GameEvent(event_type=EventType.BID_PLACED, data=data.model_dump())


def bidding_complete_event(bids: List[dict]) -> GameEvent:
    data = BiddingCompleteData(bids=bids)
    return GameEvent(event_type=EventType.BIDDING_COMPLETE, data=data.model_dump())


def card_played_event(player_id: str, card: dict) -> GameEvent:
    data = CardPlayedData(player_id=player_id, card=card)
    return GameEvent(event_type=EventType.CARD_PLAYED, data=data.model_dump())


def trick_complete_event(winner_id: str, tricks_won: Dict[str, int]) -> GameEvent:
    data = TrickCompleteData(winner_id=winner_id, tricks_won=tricks_won)
    return GameEvent(event_type=EventType.TRICK_COMPLETE, data=data.model_dump())


def round_complete_event(
    round_scores: Dict[str, int], cumulative_scores: Dict[str, int],
    tricks_won: Dict[str, int], bids: List[dict],
) -> GameEvent:
    data = RoundCompleteData(
        round_scores=round_scores, cumulative_scores=cumulative_scores,
        tricks_won=tricks_won, bids=bids,
    )
    return GameEvent(event_type=EventType.ROUND_COMPLETE, data=data.model_dump())


def game_over_event(final_scores: Dict[str, int], winners: List[str]) -> GameEvent:
    data = GameOverData(final_scores=final_scores, winners=winners)
    return GameEvent(event_type=EventType.GAME_OVER, data=data.model_dump())


def turn_changed_event(player_id: str, phase: str) -> GameEvent:
    data = TurnChangedData(player_id=player_id, phase=phase)
    return GameEvent(event_type=EventType.TURN_CHANGED, data=data.model_dump())


def invalid_action_event(reason: str, player_id: str) -> GameEvent:
    data = InvalidActionData(reason=reason)
    return GameEvent(
        event_type=EventType.INVALID_ACTION, data=data.model_dump(), player_id=player_id,
    )


# --- Lobby event data models ---


class PlayerJoinedData(BaseModel):
    player_id: str
    player_name: str
    player_count: int


class PlayerLeftData(BaseModel):
    player_id: str
    player_name: str
    player_count: int


class AutoStartCountdownData(BaseModel):
    seconds_remaining: int


# --- Lobby event factories ---


def player_joined_event(player_id: str, player_name: str, player_count: int) -> GameEvent:
    data = PlayerJoinedData(player_id=player_id, player_name=player_name, player_count=player_count)
    return GameEvent(event_type=EventType.PLAYER_JOINED, data=data.model_dump())


def player_left_event(player_id: str, player_name: str, player_count: int) -> GameEvent:
    data = PlayerLeftData(player_id=player_id, player_name=player_name, player_count=player_count)
    return GameEvent(event_type=EventType.PLAYER_LEFT, data=data.model_dump())


def auto_start_countdown_event(seconds_remaining: int) -> GameEvent:
    data = AutoStartCountdownData(seconds_remaining=seconds_remaining)
    return GameEvent(event_type=EventType.AUTO_START_COUNTDOWN, data=data.model_dump())


def game_starting_event() -> GameEvent:
    return GameEvent(event_type=EventType.GAME_STARTING, data={})


def player_reconnected_event(player_id: str, player_name: str) -> GameEvent:
    return GameEvent(
        event_type=EventType.PLAYER_RECONNECTED,
        data={"player_id": player_id, "player_name": player_name},
    )


def player_disconnected_event(player_id: str, player_name: str) -> GameEvent:
    return GameEvent(
        event_type=EventType.PLAYER_DISCONNECTED,
        data={"player_id": player_id, "player_name": player_name},
    )


# --- Mascot event data models ---


class MascotPersonaAwardedData(BaseModel):
    persona_id: str
    persona_name: str
    persona_category: str
    persona_tagline: str
    traits: Dict[str, float]
    player_traits: Dict[str, float]


def mascot_persona_awarded_event(
    player_id: str,
    persona_id: str,
    persona_name: str,
    persona_category: str,
    persona_tagline: str,
    traits: Dict[str, float],
    player_traits: Dict[str, float],
) -> GameEvent:
    data = MascotPersonaAwardedData(
        persona_id=persona_id,
        persona_name=persona_name,
        persona_category=persona_category,
        persona_tagline=persona_tagline,
        traits=traits,
        player_traits=player_traits,
    )
    return GameEvent(
        event_type=EventType.MASCOT_PERSONA_AWARDED,
        data=data.model_dump(),
        player_id=player_id,
    )
