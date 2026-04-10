import { memo } from "react";
import type { Suit } from "../../types";
import { Suit as SuitValues, SUIT_COLORS } from "../../types";

interface SuitSvgProps {
  suit: Suit;
  size?: number;
  className?: string;
}

/**
 * SVG suit symbols — distinct, crisp at any size.
 * Spade: pointed with stem. Club: three lobes with stem. Heart: classic. Diamond: rotated square.
 */
export const SuitSvg = memo(function SuitSvg({ suit, size = 16, className }: SuitSvgProps) {
  const color = SUIT_COLORS[suit] === "red" ? "currentColor" : "currentColor";
  return (
    <svg
      viewBox="0 0 100 100"
      width={size}
      height={size}
      className={className}
      style={{ display: "inline-block", verticalAlign: "middle" }}
      aria-label={suit}
    >
      <SuitPath suit={suit} color={color} />
    </svg>
  );
});

function SuitPath({ suit, color }: { suit: Suit; color: string }) {
  switch (suit) {
    case SuitValues.SPADES:
      return (
        <path
          d="M50 5 C50 5 10 45 10 62 C10 78 25 85 40 78 C38 88 35 95 25 95 L75 95 C65 95 62 88 60 78 C75 85 90 78 90 62 C90 45 50 5 50 5Z"
          fill={color}
        />
      );
    case SuitValues.HEARTS:
      return (
        <path
          d="M50 88 C50 88 10 55 10 35 C10 15 30 8 50 28 C70 8 90 15 90 35 C90 55 50 88 50 88Z"
          fill={color}
        />
      );
    case SuitValues.DIAMONDS:
      return (
        <path
          d="M50 5 L85 50 L50 95 L15 50 Z"
          fill={color}
        />
      );
    case SuitValues.CLUBS:
      return (
        <>
          {/* Top lobe */}
          <circle cx="50" cy="28" r="20" fill={color} />
          {/* Bottom-left lobe */}
          <circle cx="30" cy="52" r="20" fill={color} />
          {/* Bottom-right lobe */}
          <circle cx="70" cy="52" r="20" fill={color} />
          {/* Stem */}
          <path d="M43 60 L43 95 L57 95 L57 60 Z" fill={color} />
        </>
      );
  }
}
