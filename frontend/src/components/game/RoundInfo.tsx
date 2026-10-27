import type { Card, HouseRules, Suit } from "../../types";
import { RANK_DISPLAY, SUIT_COLORS, SUIT_SYMBOLS, summarizeHouseRules } from "../../types";
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
  /** The face-up card that set trump under the "flip a card" house rule. */
  trumpCard?: Card | null;
  houseRules?: HouseRules;
}

export function RoundInfo({
  roundNumber, totalRounds, numCards, trumpSuit, playerCount, mustLoseMode, challengeMode,
  trumpCard = null, houseRules,
}: RoundInfoProps) {
  if (!roundNumber) return null;

  const suit = trumpSuit as Suit | null;
  const suitColor = suit ? SUIT_COLORS[suit] : null;
  const isRed = suitColor === "red";
  const symbolColor = isRed ? "var(--color-card-red)" : "var(--color-card-black)";

  // Top-center is free for 3 and 5 players; occupied for 4 and 6
  const topCenterFree = playerCount === 3 || playerCount === 5;
  const positionClass = topCenterFree ? styles.roundIslandTop : styles.roundIslandBottom;

  const trumpTooltip = trumpCard
    ? `Trump card turned up: ${RANK_DISPLAY[trumpCard.rank]}${SUIT_SYMBOLS[trumpCard.suit]}`
    : "Trump suit";
  const ruleLines = houseRules ? summarizeHouseRules(houseRules) : [];

  const roundTooltip = totalRounds
    ? `Round ${roundNumber} of ${totalRounds}`
    : `Round ${roundNumber}`;

  return (
    <div className={`${styles.roundIsland} ${positionClass}`}>
      {suit && (
        <span className={styles.roundIslandSuit} style={{ color: symbolColor }} title={trumpTooltip}>
          <SuitSvg suit={suit} size={22} />
          {trumpCard && (
            <span className={styles.roundIslandTrumpRank} aria-label={trumpTooltip}>
              {RANK_DISPLAY[trumpCard.rank]}
            </span>
          )}
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
        {ruleLines.length > 0 && (
          <span className={styles.modeIcon} title={`House rules: ${ruleLines.join("; ")}`}>
            {"\uD83D\uDCDC"}
          </span>
        )}
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
