import type { Suit } from "../../types";
import { SUIT_COLORS } from "../../types";
import { SuitSvg } from "../common";
import styles from "../../styles/game.module.css";

interface RoundInfoProps {
  roundNumber: number | null;
  numCards: number | null;
  trumpSuit: string | null;
  playerCount: number;
}

export function RoundInfo({ roundNumber, numCards, trumpSuit, playerCount }: RoundInfoProps) {
  if (!roundNumber) return null;

  const suit = trumpSuit as Suit | null;
  const suitColor = suit ? SUIT_COLORS[suit] : null;
  const isRed = suitColor === "red";
  const symbolColor = isRed ? "#e74c3c" : "#ffffff";

  // Top-center is free for 3 and 5 players; occupied for 4 and 6
  const topCenterFree = playerCount === 3 || playerCount === 5;
  const positionClass = topCenterFree ? styles.roundIslandTop : styles.roundIslandBottom;

  return (
    <div className={`${styles.roundIsland} ${positionClass}`}>
      {suit && (
        <span className={styles.roundIslandSuit} style={{ color: symbolColor }}>
          <SuitSvg suit={suit} size={22} />
        </span>
      )}
      <span className={styles.roundIslandText}>
        Round {roundNumber}
      </span>
      <span className={styles.roundIslandDivider} />
      <span className={styles.roundIslandText}>
        {numCards} cards
      </span>
    </div>
  );
}
