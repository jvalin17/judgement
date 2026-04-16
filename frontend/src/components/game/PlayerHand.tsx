import type { Card as CardType } from "../../types";
import { isSameCard, Suit } from "../../types";
import { Card } from "../common";
import styles from "../../styles/game.module.css";

const SUIT_ORDER: Record<string, number> = {
  [Suit.SPADES]: 0,
  [Suit.DIAMONDS]: 1,
  [Suit.CLUBS]: 2,
  [Suit.HEARTS]: 3,
};

function sortHand(cards: CardType[]): CardType[] {
  return [...cards].sort((a, b) => {
    const suitDiff = SUIT_ORDER[a.suit] - SUIT_ORDER[b.suit];
    if (suitDiff !== 0) return suitDiff;
    return a.rank - b.rank;
  });
}

interface PlayerHandProps {
  hand: CardType[];
  validCards: CardType[];
  isMyTurn: boolean;
  onPlayCard: (card: CardType) => void;
}

export function PlayerHand({ hand, validCards, isMyTurn, onPlayCard }: PlayerHandProps) {
  const sorted = sortHand(hand);
  return (
    <div className={styles.handArea}>
      <div className={styles.handCards}>
        {sorted.map((card) => {
          const isPlayable = isMyTurn && isCardPlayable(card, validCards);
          const isDimmed = isMyTurn && !isPlayable;
          return (
            <Card
              key={cardKey(card)}
              card={card}
              playable={isPlayable}
              dimmed={isDimmed}
              onClick={() => isPlayable && onPlayCard(card)}
            />
          );
        })}
        {isMyTurn && <span className={styles.handTurnHourglass}>{"\u23F3"}</span>}
      </div>
    </div>
  );
}

function isCardPlayable(card: CardType, validCards: CardType[]): boolean {
  return validCards.some((validCard) => isSameCard(card, validCard));
}

function cardKey(card: CardType): string {
  return `${card.suit}-${card.rank}`;
}
