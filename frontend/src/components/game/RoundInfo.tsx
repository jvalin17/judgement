import type { Suit } from "../../types";
import { SUIT_COLORS } from "../../types";
import { SuitSvg } from "../common";
import styles from "../../styles/game.module.css";

interface RoundInfoProps {
  roundNumber: number | null;
  numCards: number | null;
  trumpSuit: string | null;
}

export function RoundInfo({ roundNumber, numCards, trumpSuit }: RoundInfoProps) {
  if (!roundNumber) return null;

  return (
    <div className={styles.topBar}>
      <div className={styles.roundDetails}>
        <span className={styles.roundLabel}>Round {roundNumber}</span>
        {numCards && <span className={styles.cardsLabel}>{numCards} cards</span>}
      </div>
      {trumpSuit && <TrumpCard suit={trumpSuit as Suit} />}
    </div>
  );
}

interface TrumpCardProps {
  suit: Suit;
}

function TrumpCard({ suit }: TrumpCardProps) {
  const suitColor = SUIT_COLORS[suit];
  const glowColor = suitColor === "red" ? "rgba(192, 57, 43, 0.5)" : "rgba(100, 130, 180, 0.5)";

  return (
    <div className={styles.trumpDisplay}>
      <div className={styles.trumpCard} style={{ boxShadow: `0 0 12px 3px ${glowColor}, var(--shadow-card)` }}>
        <span className={styles.trumpSymbol} style={{ color: suitColor === "red" ? "var(--color-card-red)" : "#e8e0d4" }}>
          <SuitSvg suit={suit} size={28} />
        </span>
      </div>
      <span className={styles.trumpLabel}>TRUMP</span>
    </div>
  );
}
