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
  const isRed = suitColor === "red";
  const cardBg = isRed
    ? "linear-gradient(135deg, #1a3a5c, #2c5f8a)"
    : "linear-gradient(135deg, #f5f0e8, #e8e0d4)";
  const borderColor = isRed ? "#4a7fb5" : "#c0b8a8";
  const symbolColor = isRed ? "var(--color-card-red)" : "var(--color-card-black)";
  const glowColor = isRed ? "rgba(192, 57, 43, 0.5)" : "rgba(100, 100, 100, 0.3)";

  return (
    <div className={styles.trumpDisplay}>
      <div
        className={styles.trumpCard}
        style={{
          background: cardBg,
          borderColor: borderColor,
          boxShadow: `0 0 12px 3px ${glowColor}, var(--shadow-card)`,
        }}
      >
        <span className={styles.trumpSymbol} style={{ color: symbolColor }}>
          <SuitSvg suit={suit} size={20} />
        </span>
      </div>
      <span className={styles.trumpLabel}>TRUMP</span>
    </div>
  );
}
