import type { Bid } from "../../types";
import { getAvatarColor, getInitials, StatBadge } from "./OpponentArea";
import styles from "../../styles/game.module.css";

interface PlayerInfoProps {
  playerId: string | null;
  playerName: string;
  bids: Bid[];
  tricksWon: Record<string, number>;
  cumulativeScores: Record<string, number>;
  isMyTurn?: boolean;
}

export function PlayerInfo({ playerId, playerName, bids, tricksWon, cumulativeScores, isMyTurn }: PlayerInfoProps) {
  if (!playerId) return null;

  const myBid = findMyBid(bids, playerId);
  const myTricks = tricksWon[playerId] ?? 0;
  const myScore = cumulativeScores[playerId] ?? 0;
  const avatarColor = getAvatarColor(playerName);
  const initials = getInitials(playerName);

  const infoClass = [
    styles.playerInfo,
    isMyTurn ? styles.playerInfoActive : "",
  ].filter(Boolean).join(" ");

  return (
    <div className={infoClass}>
      <div className={styles.playerInfoAvatar} style={{ backgroundColor: avatarColor }}>
        {initials}
      </div>
      <span className={styles.playerInfoName}>{playerName}</span>
      <StatBadge score={myScore} bid={myBid} tricksWon={myTricks} />
    </div>
  );
}

function findMyBid(bids: Bid[], playerId: string): number | null {
  const bid = bids.find((bid) => bid.player_id === playerId);
  return bid ? bid.amount : null;
}
