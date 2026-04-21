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

  const suit = trumpSuit as Suit | null;
  const suitColor = suit ? SUIT_COLORS[suit] : null;
  const isRed = suitColor === "red";
  const cardBg = isRed
    ? "linear-gradient(135deg, #1a3a5c, #2c5f8a)"
    : "linear-gradient(135deg, #f5f0e8, #e8e0d4)";
  const borderColor = isRed ? "#4a7fb5" : "#c0b8a8";
  const symbolColor = isRed ? "var(--color-card-red)" : "var(--color-card-black)";
  const glowColor = isRed ? "rgba(192, 57, 43, 0.4)" : "rgba(100, 100, 100, 0.25)";
  const textColor = isRed ? "#d4e6f5" : "#2c3e50";

  return (
    <div className={styles.roundInfoCard}>
      <div
        className={styles.roundInfoFace}
        style={{
          background: cardBg,
          borderColor: borderColor,
          boxShadow: `0 0 14px 4px ${glowColor}, var(--shadow-card)`,
        }}
      >
        <span className={styles.roundInfoNumber} style={{ color: textColor }}>
          R{roundNumber}
        </span>
        {suit && (
          <span className={styles.roundInfoSuit} style={{ color: symbolColor }}>
            <SuitSvg suit={suit} size={28} />
          </span>
        )}
        {numCards && (
          <span className={styles.roundInfoCards} style={{ color: textColor }}>
            {numCards}
          </span>
        )}
      </div>
      <span className={styles.roundInfoLabel}>TRUMP</span>
    </div>
  );
}
