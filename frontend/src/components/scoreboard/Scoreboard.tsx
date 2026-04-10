import type { Player, Bid } from "../../types";
import styles from "../../styles/scoreboard.module.css";

interface ScoreboardProps {
  players: Player[];
  bids: Bid[];
  tricksWon: Record<string, number>;
  cumulativeScores: Record<string, number>;
  roundScores?: Record<string, number>;
  currentPlayerId: string | null;
}

export function Scoreboard({
  players,
  bids,
  tricksWon,
  cumulativeScores,
  roundScores,
  currentPlayerId,
}: ScoreboardProps) {
  return (
    <div className={styles.scoreboard}>
      <table className={styles.scoreTable}>
        <thead>
          <tr>
            <th>Player</th>
            <th>Bid</th>
            <th>Tricks</th>
            {roundScores && <th>Round</th>}
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {players.map((player) => (
            <ScoreRow
              key={player.id}
              player={player}
              bid={findPlayerBid(bids, player.id)}
              tricks={tricksWon[player.id] ?? 0}
              score={cumulativeScores[player.id] ?? 0}
              roundScore={roundScores ? (roundScores[player.id] ?? 0) : undefined}
              isCurrentPlayer={player.id === currentPlayerId}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface ScoreRowProps {
  player: Player;
  bid: number | null;
  tricks: number;
  score: number;
  roundScore?: number;
  isCurrentPlayer: boolean;
}

function ScoreRow({ player, bid, tricks, score, roundScore, isCurrentPlayer }: ScoreRowProps) {
  return (
    <tr>
      <td className={styles.playerNameCell}>
        {isCurrentPlayer ? <span className={styles.highlight}>{player.name}</span> : player.name}
      </td>
      <td>{bid !== null ? bid : "—"}</td>
      <td>{tricks}</td>
      {roundScore !== undefined && (
        <td className={roundScore > 0 ? styles.positive : styles.negative}>
          {roundScore > 0 ? "+" : ""}{roundScore}
        </td>
      )}
      <td className={styles.highlight}>{score}</td>
    </tr>
  );
}

function findPlayerBid(bids: Bid[], playerId: string): number | null {
  const bid = bids.find((bid) => bid.player_id === playerId);
  return bid ? bid.amount : null;
}
