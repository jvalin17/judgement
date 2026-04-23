import type { Suit } from "../../types";
import { SUIT_COLORS } from "../../types";
import { SuitSvg } from "../common";
import styles from "../../styles/game.module.css";

interface RoundInfoProps {
  roundNumber: number | null;
  totalRounds: number | null;
  numCards: number | null;
  trumpSuit: string | null;
  playerCount: number;
  mustLoseMode: boolean;
  challengeMode: boolean;
}

export function RoundInfo({ roundNumber, totalRounds, numCards, trumpSuit, playerCount, mustLoseMode, challengeMode }: RoundInfoProps) {
  if (!roundNumber) return null;

  const suit = trumpSuit as Suit | null;
  const suitColor = suit ? SUIT_COLORS[suit] : null;
  const isRed = suitColor === "red";
  const symbolColor = isRed ? "var(--color-card-red)" : "var(--color-card-black)";

  // Top-center is free for 3 and 5 players; occupied for 4 and 6
  const topCenterFree = playerCount === 3 || playerCount === 5;
  const positionClass = topCenterFree ? styles.roundIslandTop : styles.roundIslandBottom;

  const roundTooltip = totalRounds
    ? `Round ${roundNumber} of ${totalRounds}`
    : `Round ${roundNumber}`;

  return (
    <div className={`${styles.roundIsland} ${positionClass}`}>
      {suit && (
        <span className={styles.roundIslandSuit} style={{ color: symbolColor }}>
          <SuitSvg suit={suit} size={22} />
        </span>
      )}
      <span className={styles.roundIslandText} title={roundTooltip}>
        Round {roundNumber}
      </span>
      <span className={styles.roundIslandDivider} />
      <span className={styles.roundIslandText}>
        {numCards} cards
      </span>
      <span className={styles.roundIslandDivider} />
      <span className={styles.roundIslandModes}>
        {mustLoseMode && (
          <span className={styles.modeIcon} title="Turbulence — someone must lose every round">
            ⚠️
          </span>
        )}
        {challengeMode ? (
          <span className={styles.modeIcon} title="Challenge — AI plays at full strength">
            🔥
          </span>
        ) : (
          <span className={styles.modeIcon} title="Casual — AI adapts to your level">
            🎯
          </span>
        )}
      </span>
    </div>
  );
}
