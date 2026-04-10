import type { Card as CardType, Suit, Rank } from "../../types";
import { Rank as RankValues, SUIT_SYMBOLS, SUIT_COLORS, RANK_DISPLAY } from "../../types";
import { PIP_LAYOUTS } from "./pipLayouts";
import type { PipPosition } from "./pipLayouts";
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

export function Card({ card, playable = false, selected = false, dimmed = false, small = false, onClick }: CardProps) {
  const color = SUIT_COLORS[card.suit];
  const suitSymbol = SUIT_SYMBOLS[card.suit];
  const rankLabel = RANK_DISPLAY[card.rank];

  const classNames = [
    styles.card,
    styles[color],
    playable ? styles.playable : "",
    selected ? styles.selected : "",
    dimmed ? styles.dimmed : "",
    small ? styles.small : "",
  ].filter(Boolean).join(" ");

  return (
    <div className={classNames} onClick={playable ? onClick : undefined} role={playable ? "button" : undefined}>
      <div className={styles.cornerTop}>
        <span className={styles.rank}>{rankLabel}</span>
        <span className={styles.cornerSuit}>{suitSymbol}</span>
      </div>

      <div className={styles.cardBody}>
        <CardCenter rank={card.rank} suit={card.suit} small={small} />
      </div>

      <div className={styles.cornerBottom}>
        <span className={styles.rank}>{rankLabel}</span>
        <span className={styles.cornerSuit}>{suitSymbol}</span>
      </div>
    </div>
  );
}

// --- Card center content ---

interface CardCenterProps {
  rank: Rank;
  suit: Suit;
  small: boolean;
}

function CardCenter({ rank, suit, small }: CardCenterProps) {
  const suitSymbol = SUIT_SYMBOLS[suit];

  if (isNumberRank(rank)) {
    return <PipGrid rank={rank} suitSymbol={suitSymbol} small={small} />;
  }

  if (isFaceRank(rank)) {
    return <FaceCardDesign rank={rank} suit={suit} />;
  }

  return <AceDesign suitSymbol={suitSymbol} />;
}

// --- Pip grid for number cards ---

interface PipGridProps {
  rank: Rank;
  suitSymbol: string;
  small: boolean;
}

function PipGrid({ rank, suitSymbol, small }: PipGridProps) {
  const positions = PIP_LAYOUTS[rank as number];
  if (!positions) return <span className={styles.aceSymbol}>{suitSymbol}</span>;

  return (
    <div className={styles.pipGrid}>
      {positions.map((position, index) => (
        <Pip key={index} position={position} symbol={suitSymbol} small={small} />
      ))}
    </div>
  );
}

interface PipProps {
  position: PipPosition;
  symbol: string;
  small: boolean;
}

function Pip({ position, symbol, small }: PipProps) {
  const pipClass = [styles.pip, small ? styles.pipSmall : ""].filter(Boolean).join(" ");

  return (
    <span
      className={pipClass}
      style={{
        left: `${position.x}%`,
        top: `${position.y}%`,
        transform: position.inverted
          ? "translate(-50%, -50%) rotate(180deg)"
          : "translate(-50%, -50%)",
      }}
    >
      {symbol}
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

interface AceDesignProps {
  suitSymbol: string;
}

function AceDesign({ suitSymbol }: AceDesignProps) {
  return <span className={styles.aceSymbol}>{suitSymbol}</span>;
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
