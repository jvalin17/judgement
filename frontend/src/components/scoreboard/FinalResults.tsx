import type { Player } from "../../types";
import { Button } from "../common";
import styles from "../../styles/scoreboard.module.css";

interface FinalResultsProps {
  players: Player[];
  finalScores: Record<string, number>;
  onPlayAgain: () => void;
}

export function FinalResults({ players, finalScores, onPlayAgain }: FinalResultsProps) {
  const rankedPlayers = rankPlayersByScore(players, finalScores);
  const winningScore = rankedPlayers.length > 0 ? finalScores[rankedPlayers[0].id] : 0;
  const winners = rankedPlayers.filter((player) => finalScores[player.id] === winningScore);

  return (
    <div className={styles.finalResults}>
      <h1 className={styles.gameOverTitle}>Game Over</h1>

      <WinnerDisplay winners={winners} />

      <div className={styles.finalScoreList}>
        {rankedPlayers.map((player) => (
          <FinalScoreRow
            key={player.id}
            playerName={player.name}
            score={finalScores[player.id] ?? 0}
            isWinner={finalScores[player.id] === winningScore}
          />
        ))}
      </div>

      <div className={styles.actions}>
        <Button variant="primary" size="large" onClick={onPlayAgain}>
          Play Again
        </Button>
      </div>
    </div>
  );
}

interface WinnerDisplayProps {
  winners: Player[];
}

function WinnerDisplay({ winners }: WinnerDisplayProps) {
  const winnerNames = winners.map((winner) => winner.name).join(" & ");

  return (
    <div className={styles.winnerSection}>
      <span className={styles.winnerLabel}>{winners.length > 1 ? "Winners" : "Winner"}</span>
      <span className={styles.winnerName}>{winnerNames}</span>
    </div>
  );
}

interface FinalScoreRowProps {
  playerName: string;
  score: number;
  isWinner: boolean;
}

function FinalScoreRow({ playerName, score, isWinner }: FinalScoreRowProps) {
  const rowClass = [styles.finalScoreRow, isWinner ? styles.winner : ""].filter(Boolean).join(" ");

  return (
    <div className={rowClass}>
      <span className={styles.finalScoreName}>{playerName}</span>
      <span className={styles.finalScoreValue}>{score}</span>
    </div>
  );
}

function rankPlayersByScore(players: Player[], scores: Record<string, number>): Player[] {
  return [...players].sort((playerA, playerB) => (scores[playerB.id] ?? 0) - (scores[playerA.id] ?? 0));
}
