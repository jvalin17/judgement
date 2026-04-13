import type { TrickPlay, Player } from "../../types";
import { Card } from "../common";
import styles from "../../styles/game.module.css";
import animStyles from "../../styles/animations.module.css";

interface SeatPosition {
  left: string;
  top: string;
}

interface TrickAreaProps {
  currentTrick: TrickPlay[];
  players: Player[];
  orderedPlayers: Player[];
  seatPositions: SeatPosition[];
  trickWinner: string | null;
  trickCollecting: boolean;
}

export function TrickArea({
  currentTrick, players, orderedPlayers, seatPositions,
  trickWinner, trickCollecting,
}: TrickAreaProps) {
  if (currentTrick.length === 0 && !trickWinner) {
    return (
      <div className={styles.trickArea}>
        <span className={styles.emptyTrick}>Waiting for play...</span>
      </div>
    );
  }

  const winnerName = trickWinner ? findPlayerName(players, trickWinner) : null;
  const pileClass = [
    styles.trickPile,
    trickWinner ? styles.trickHasWinner : "",
    trickCollecting ? animStyles.collectTrick : "",
  ].filter(Boolean).join(" ");

  return (
    <div className={styles.trickArea}>
      <div className={pileClass}>
        {trickWinner && !trickCollecting && (
          <div className={styles.trickWinnerLabel}>
            {winnerName} wins!
          </div>
        )}
        {currentTrick.map((play, index) => {
          const isWinner = trickWinner === play.player_id;
          const origin = getSeatOrigin(play.player_id, orderedPlayers, seatPositions);
          const isNew = index === currentTrick.length - 1 && !trickWinner;
          return (
            <TrickCardSlot
              key={play.player_id}
              play={play}
              playerName={findPlayerName(players, play.player_id)}
              isWinner={isWinner}
              originX={origin.x}
              originY={origin.y}
              isNew={isNew}
            />
          );
        })}
      </div>
    </div>
  );
}

// --- Compute origin offset for fly-in animation ---

function getSeatOrigin(
  playerId: string,
  orderedPlayers: Player[],
  seatPositions: SeatPosition[],
): { x: number; y: number } {
  const seatIndex = orderedPlayers.findIndex((player) => player.id === playerId);
  if (seatIndex < 0 || seatIndex >= seatPositions.length) {
    return { x: 0, y: 60 }; // fallback: slide from bottom
  }
  const seat = seatPositions[seatIndex];
  // Seat positions are percentages. Trick area is at ~50%, 45%.
  // Convert to pixel-ish offsets relative to center.
  const seatX = parseFloat(seat.left) - 50;
  const seatY = parseFloat(seat.top) - 45;
  // Scale to reasonable animation distance (not full screen)
  const scale = 2.5;
  return { x: seatX * scale, y: seatY * scale };
}

// --- Single card slot in the trick ---

interface TrickCardSlotProps {
  play: TrickPlay;
  playerName: string;
  isWinner: boolean;
  originX: number;
  originY: number;
  isNew: boolean;
}

function TrickCardSlot({ play, playerName, isWinner, originX, originY, isNew }: TrickCardSlotProps) {
  const slotClass = [
    styles.trickCardSlot,
    isWinner ? styles.trickCardWinner : "",
    isNew ? styles.trickCardFlyIn : "",
  ].filter(Boolean).join(" ");

  const flyStyle = isNew ? {
    "--fly-from-x": `${originX}px`,
    "--fly-from-y": `${originY}px`,
  } as React.CSSProperties : undefined;

  return (
    <div className={slotClass} style={flyStyle}>
      <span className={styles.trickPlayerName}>{playerName}</span>
      <Card card={play.card} />
    </div>
  );
}

// --- Helpers ---

function findPlayerName(players: Player[], playerId: string): string {
  const player = players.find((player) => player.id === playerId);
  return player?.name ?? "Unknown";
}
