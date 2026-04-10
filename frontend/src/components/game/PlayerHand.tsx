import type { Card as CardType } from "../../types";
import { isSameCard } from "../../types";
import { Card } from "../common";
import styles from "../../styles/game.module.css";

interface PlayerHandProps {
  hand: CardType[];
  validCards: CardType[];
  isMyTurn: boolean;
  onPlayCard: (card: CardType) => void;
}

export function PlayerHand({ hand, validCards, isMyTurn, onPlayCard }: PlayerHandProps) {
  return (
    <div className={styles.handArea}>
      <div className={styles.handCards}>
        {hand.map((card) => {
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
