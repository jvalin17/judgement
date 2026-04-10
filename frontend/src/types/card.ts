export const Suit = {
  SPADES: "spades",
  DIAMONDS: "diamonds",
  CLUBS: "clubs",
  HEARTS: "hearts",
} as const;

export type Suit = (typeof Suit)[keyof typeof Suit];

export const Rank = {
  TWO: 2,
  THREE: 3,
  FOUR: 4,
  FIVE: 5,
  SIX: 6,
  SEVEN: 7,
  EIGHT: 8,
  NINE: 9,
  TEN: 10,
  JACK: 11,
  QUEEN: 12,
  KING: 13,
  ACE: 14,
} as const;

export type Rank = (typeof Rank)[keyof typeof Rank];

export interface Card {
  suit: Suit;
  rank: Rank;
}

export const SUIT_SYMBOLS: Record<Suit, string> = {
  [Suit.SPADES]: "♠",
  [Suit.DIAMONDS]: "♦",
  [Suit.CLUBS]: "♣",
  [Suit.HEARTS]: "♥",
};

export const SUIT_COLORS: Record<Suit, string> = {
  [Suit.SPADES]: "black",
  [Suit.HEARTS]: "red",
  [Suit.DIAMONDS]: "red",
  [Suit.CLUBS]: "black",
};

export const RANK_DISPLAY: Record<Rank, string> = {
  [Rank.TWO]: "2",
  [Rank.THREE]: "3",
  [Rank.FOUR]: "4",
  [Rank.FIVE]: "5",
  [Rank.SIX]: "6",
  [Rank.SEVEN]: "7",
  [Rank.EIGHT]: "8",
  [Rank.NINE]: "9",
  [Rank.TEN]: "10",
  [Rank.JACK]: "J",
  [Rank.QUEEN]: "Q",
  [Rank.KING]: "K",
  [Rank.ACE]: "A",
};

export const TRUMP_ORDER: Suit[] = [
  Suit.SPADES,
  Suit.DIAMONDS,
  Suit.CLUBS,
  Suit.HEARTS,
];

export function isSameCard(cardA: Card, cardB: Card): boolean {
  return cardA.suit === cardB.suit && cardA.rank === cardB.rank;
}

export function cardDisplayName(card: Card): string {
  return `${RANK_DISPLAY[card.rank]}${SUIT_SYMBOLS[card.suit]}`;
}
