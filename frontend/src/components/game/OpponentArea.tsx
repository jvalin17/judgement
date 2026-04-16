import type { Player } from "../../types";
import { CardBack } from "../common";
import styles from "../../styles/game.module.css";

interface SeatPosition {
  left: string;
  top: string;
}

interface PlayerSeatProps {
  player: Player;
  position: SeatPosition;
  isCurrentTurn: boolean;
  bid: number | null;
  tricksWon: number;
  score: number;
  cardsRemaining: number;
}

export function PlayerSeat({ player, position, isCurrentTurn, bid, tricksWon, score, cardsRemaining }: PlayerSeatProps) {
  const avatarColor = getAvatarColor(player.name);
  const initials = getInitials(player.name);
  const avatarClass = [styles.avatar, isCurrentTurn ? styles.avatarActive : ""].filter(Boolean).join(" ");
  const cardCount = Math.min(cardsRemaining, 5);
  const fanAngles = getFanAngles(cardCount);

  return (
    <div className={styles.seat} style={{ left: position.left, top: position.top }}>
      <div className={styles.seatCards}>
        {fanAngles.map((angle, index) => (
          <div
            key={index}
            className={styles.seatCard}
            style={{ transform: `translateX(${angle * 2}px) rotate(${angle}deg)` }}
          >
            <CardBack small />
          </div>
        ))}
        {isCurrentTurn && <span className={styles.turnPill}>NOW</span>}
      </div>
      <div className={avatarClass} style={{ backgroundColor: avatarColor }}>
        {initials}
      </div>
      <span className={styles.seatName}>{player.name}</span>
      <StatBadge score={score} bid={bid} tricksWon={tricksWon} />
    </div>
  );
}

// --- Stat badge: split circle showing score | won/bid ---

interface StatBadgeProps {
  score: number;
  bid: number | null;
  tricksWon: number;
}

export function StatBadge({ score, bid, tricksWon }: StatBadgeProps) {
  const bottomText = bid !== null ? `${tricksWon}/${bid}` : "\u2014";

  return (
    <div className={styles.statBadge}>
      <div className={styles.statBadgeTop}>{score}</div>
      <div className={styles.statBadgeDivider} />
      <div className={styles.statBadgeBottom}>{bottomText}</div>
    </div>
  );
}

// --- Avatar helpers ---

const AVATAR_COLORS = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"];

export function getAvatarColor(name: string): string {
  let hash = 0;
  for (let index = 0; index < name.length; index++) {
    hash = name.charCodeAt(index) + ((hash << 5) - hash);
  }
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

export function getInitials(name: string): string {
  return name.slice(0, 2).toUpperCase();
}

function getFanAngles(count: number): number[] {
  if (count <= 1) return [0];
  const spread = 20;
  const step = spread / (count - 1);
  return Array.from({ length: count }, (_, index) => -spread / 2 + step * index);
}
