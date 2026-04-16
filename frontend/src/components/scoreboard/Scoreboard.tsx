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
  const leaderIds = findLeaderIds(players, cumulativeScores);
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
              isLeader={leaderIds.has(player.id)}
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
  isLeader: boolean;
}

function ScoreRow({ player, bid, tricks, score, roundScore, isCurrentPlayer, isLeader }: ScoreRowProps) {
  const rowClass = isLeader ? styles.leaderRow : "";
  return (
    <tr className={rowClass}>
      <td className={styles.playerNameCell}>
        {isLeader && <span className={styles.leaderBadge} title="Leader">★</span>}
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

function findLeaderIds(players: Player[], cumulativeScores: Record<string, number>): Set<string> {
  if (players.length === 0) return new Set();
  let topScore = -Infinity;
  for (const player of players) {
    const score = cumulativeScores[player.id] ?? 0;
    if (score > topScore) topScore = score;
  }
  const leaders = new Set<string>();
  for (const player of players) {
    if ((cumulativeScores[player.id] ?? 0) === topScore) leaders.add(player.id);
  }
  return leaders;
}

function findPlayerBid(bids: Bid[], playerId: string): number | null {
  const bid = bids.find((bid) => bid.player_id === playerId);
  return bid ? bid.amount : null;
}
