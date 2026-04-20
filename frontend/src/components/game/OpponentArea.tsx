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
  const bidDisplay = bid !== null ? `${tricksWon}/${bid}` : "\u2014";
  const ringProgress = getRingProgress(bid, tricksWon);
  const ringColor = getRingColor(bid, tricksWon);
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
      <div className={styles.avatarRing}>
        <ProgressRing
          progress={ringProgress}
          color={ringColor}
          isActive={isCurrentTurn}
          bgColor={avatarColor}
        />
        <span className={styles.avatarBidStatus}>{bidDisplay}</span>
        <span className={styles.scoreBadge}>{score}</span>
      </div>
      <span className={styles.seatName}>{player.name}</span>
    </div>
  );
}

// --- Progress ring SVG ---

const RING_SIZE = 52;
const RING_STROKE = 3.5;
const RING_RADIUS = (RING_SIZE - RING_STROKE) / 2;
const RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS;

interface ProgressRingProps {
  progress: number;
  color: string;
  isActive: boolean;
  bgColor: string;
}

function ProgressRing({ progress, color, isActive, bgColor }: ProgressRingProps) {
  const offset = RING_CIRCUMFERENCE * (1 - progress);

  return (
    <svg className={styles.ringOverlay} viewBox={`0 0 ${RING_SIZE} ${RING_SIZE}`}>
      {/* Filled circle background */}
      <circle
        cx={RING_SIZE / 2}
        cy={RING_SIZE / 2}
        r={RING_RADIUS - RING_STROKE / 2}
        fill={bgColor}
      />
      {/* Track */}
      <circle
        cx={RING_SIZE / 2}
        cy={RING_SIZE / 2}
        r={RING_RADIUS}
        fill="none"
        stroke="rgba(255,255,255,0.15)"
        strokeWidth={RING_STROKE}
      />
      {/* Progress arc */}
      {progress > 0 && (
        <circle
          cx={RING_SIZE / 2}
          cy={RING_SIZE / 2}
          r={RING_RADIUS}
          fill="none"
          stroke={color}
          strokeWidth={RING_STROKE}
          strokeDasharray={RING_CIRCUMFERENCE}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${RING_SIZE / 2} ${RING_SIZE / 2})`}
          className={styles.ringArc}
        />
      )}
      {/* Active glow ring */}
      {isActive && (
        <circle
          cx={RING_SIZE / 2}
          cy={RING_SIZE / 2}
          r={RING_RADIUS + 1}
          fill="none"
          stroke="#ffd54a"
          strokeWidth={1.5}
          opacity={0.7}
        />
      )}
    </svg>
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

// --- Ring progress helpers ---

function getRingProgress(bid: number | null, tricksWon: number): number {
  if (bid === null || bid === 0) return tricksWon > 0 ? 1 : 0;
  return Math.min(tricksWon / bid, 1);
}

function getRingColor(bid: number | null, tricksWon: number): string {
  if (bid === null) return "rgba(255,255,255,0.3)";
  if (tricksWon > bid) return "#e74c3c"; // over-bid: red
  if (tricksWon === bid) return "#2ecc71"; // exact: green
  return "#3498db"; // in progress: blue
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
