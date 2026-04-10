import { memo } from "react";
import type { Card as CardType, Suit, Rank } from "../../types";
import { Rank as RankValues, SUIT_COLORS, RANK_DISPLAY } from "../../types";
import { PIP_LAYOUTS } from "./pipLayouts";
import type { PipPosition } from "./pipLayouts";
import { SuitSvg } from "./SuitSvg";
import { FaceCardArt } from "./FaceCardArt";
import { useSettings } from "../../context/SettingsContext";
import { CARD_BACK_DESIGN_CLASS } from "./SettingsModal";
import styles from "../../styles/card.module.css";

interface CardProps {
  card: CardType;
  playable?: boolean;
  selected?: boolean;
  dimmed?: boolean;
  small?: boolean;
  onClick?: () => void;
}

export const Card = memo(function Card({ card, playable = false, selected = false, dimmed = false, small = false, onClick }: CardProps) {
  const color = SUIT_COLORS[card.suit];
  const rankLabel = RANK_DISPLAY[card.rank];

  const classNames = [
    styles.card,
    styles[color],
    playable ? styles.playable : "",
    selected ? styles.selected : "",
    dimmed ? styles.dimmed : "",
    small ? styles.small : "",
  ].filter(Boolean).join(" ");

  const cornerSuitSize = small ? 10 : 13;

  return (
    <div className={classNames} onClick={playable ? onClick : undefined} role={playable ? "button" : undefined}>
      <div className={styles.cornerTop}>
        <span className={styles.rank}>{rankLabel}</span>
        <SuitSvg suit={card.suit} size={cornerSuitSize} className={styles.cornerSuit} />
      </div>

      <div className={styles.cardBody}>
        <CardCenter rank={card.rank} suit={card.suit} small={small} />
      </div>

      <div className={styles.cornerBottom}>
        <span className={styles.rank}>{rankLabel}</span>
        <SuitSvg suit={card.suit} size={cornerSuitSize} className={styles.cornerSuit} />
      </div>
    </div>
  );
});

// --- Card center content ---

interface CardCenterProps {
  rank: Rank;
  suit: Suit;
  small: boolean;
}

function CardCenter({ rank, suit, small }: CardCenterProps) {
  if (isNumberRank(rank)) {
    return <PipGrid rank={rank} suit={suit} small={small} />;
  }

  if (isFaceRank(rank)) {
    return <FaceCardDesign rank={rank} suit={suit} />;
  }

  return <AceDesign suit={suit} />;
}

// --- Pip grid for number cards ---

interface PipGridProps {
  rank: Rank;
  suit: Suit;
  small: boolean;
}

function PipGrid({ rank, suit, small }: PipGridProps) {
  const positions = PIP_LAYOUTS[rank as number];
  if (!positions) return <AceDesign suit={suit} />;

  const pipSize = small ? 10 : 14;

  return (
    <div className={styles.pipGrid}>
      {positions.map((position, index) => (
        <Pip key={index} position={position} suit={suit} size={pipSize} />
      ))}
    </div>
  );
}

interface PipProps {
  position: PipPosition;
  suit: Suit;
  size: number;
}

function Pip({ position, suit, size }: PipProps) {
  return (
    <span
      className={styles.pip}
      style={{
        left: `${position.x}%`,
        top: `${position.y}%`,
        transform: position.inverted
          ? "translate(-50%, -50%) rotate(180deg)"
          : "translate(-50%, -50%)",
      }}
    >
      <SuitSvg suit={suit} size={size} />
    </span>
  );
}

// --- Face card design (J, Q, K) — uses SVG portraits ---

interface FaceCardDesignProps {
  rank: Rank;
  suit: Suit;
}

function FaceCardDesign({ rank, suit }: FaceCardDesignProps) {
  return (
    <div className={styles.faceCardCenter}>
      <FaceCardArt rank={rank} suit={suit} />
    </div>
  );
}

// --- Ace design ---

function AceDesign({ suit }: { suit: Suit }) {
  return (
    <span className={styles.aceSymbol}>
      <SuitSvg suit={suit} size={36} />
    </span>
  );
}

// --- Card back ---

interface CardBackProps {
  small?: boolean;
}

export function CardBack({ small = false }: CardBackProps) {
  const { settings } = useSettings();
  const designClass = CARD_BACK_DESIGN_CLASS[settings.cardBack];
  const classNames = [styles.cardBack, designClass, small ? styles.small : ""].filter(Boolean).join(" ");

  return (
    <div className={classNames}>
      <div className={styles.backPattern} />
    </div>
  );
}

// --- Helpers ---

function isNumberRank(rank: Rank): boolean {
  return (rank as number) >= RankValues.TWO && (rank as number) <= RankValues.TEN;
}

function isFaceRank(rank: Rank): boolean {
  return (rank as number) >= RankValues.JACK && (rank as number) <= RankValues.KING;
}
