from enum import Enum, IntEnum
from pydantic import BaseModel


class Suit(str, Enum):
    SPADES = "spades"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"
    HEARTS = "hearts"


class Rank(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


class Card(BaseModel):
    suit: Suit
    rank: Rank

    model_config = {"frozen": True}

    def __hash__(self) -> int:
        return hash((self.suit, self.rank))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.suit == other.suit and self.rank == other.rank

    def __str__(self) -> str:
        rank_names = {11: "J", 12: "Q", 13: "K", 14: "A"}
        rank_str = rank_names.get(self.rank, str(self.rank.value))
        suit_symbols = {
            Suit.SPADES: "♠",
            Suit.DIAMONDS: "♦",
            Suit.CLUBS: "♣",
            Suit.HEARTS: "♥",
        }
        return f"{rank_str}{suit_symbols[self.suit]}"


TRUMP_ORDER: list[Suit] = [Suit.SPADES, Suit.DIAMONDS, Suit.CLUBS, Suit.HEARTS]
