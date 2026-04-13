import type { TrickPlay, Player } from "../../types";
import { Card } from "../common";
import styles from "../../styles/game.module.css";
import animStyles from "../../styles/animations.module.css";

interface TrickAreaProps {
  currentTrick: TrickPlay[];
  players: Player[];
  trickWinner: string | null;
  trickCollecting: boolean;
}

export function TrickArea({ currentTrick, players, trickWinner, trickCollecting }: TrickAreaProps) {
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
        {currentTrick.map((play) => {
          const isWinner = trickWinner === play.player_id;
          return (
            <TrickCardSlot
              key={play.player_id}
              play={play}
              playerName={findPlayerName(players, play.player_id)}
              isWinner={isWinner}
            />
          );
        })}
      </div>
    </div>
  );
}

// --- Single card slot in the trick ---

interface TrickCardSlotProps {
  play: TrickPlay;
  playerName: string;
  isWinner: boolean;
}

function TrickCardSlot({ play, playerName, isWinner }: TrickCardSlotProps) {
  const slotClass = [
    styles.trickCardSlot,
    isWinner ? styles.trickCardWinner : "",
  ].filter(Boolean).join(" ");

  return (
    <div className={slotClass}>
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
