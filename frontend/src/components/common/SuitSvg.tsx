import { memo } from "react";
import type { Suit } from "../../types";
import { Suit as SuitValues } from "../../types";

interface SuitSvgProps {
  suit: Suit;
  size?: number;
  className?: string;
}

/**
 * SVG suit symbols with maximally distinct shapes:
 * - Spade: sharp pointed top, narrow angular body, thin stem
 * - Club: three clearly round lobes separated by visible gaps, thick stem
 * - Heart: classic rounded top lobes, pointed bottom
 * - Diamond: tall narrow rhombus
 */
export const SuitSvg = memo(function SuitSvg({ suit, size = 16, className }: SuitSvgProps) {
  return (
    <svg
      viewBox="0 0 100 100"
      width={size}
      height={size}
      className={className}
      style={{ display: "inline-block", verticalAlign: "middle" }}
      aria-label={suit}
    >
      <SuitPath suit={suit} />
    </svg>
  );
});

function SuitPath({ suit }: { suit: Suit }) {
  switch (suit) {
    case SuitValues.SPADES:
      // Sharp angular spade — narrow pointed top, wide flared bottom, thin stem
      return (
        <path
          d="M50 2 C50 2 8 48 8 65 C8 80 22 84 38 76 L44 95 L56 95 L62 76 C78 84 92 80 92 65 C92 48 50 2 50 2Z"
          fill="currentColor"
        />
      );
    case SuitValues.HEARTS:
      return (
        <path
          d="M50 90 C50 90 5 55 5 32 C5 12 22 2 50 30 C78 2 95 12 95 32 C95 55 50 90 50 90Z"
          fill="currentColor"
        />
      );
    case SuitValues.DIAMONDS:
      // Tall narrow diamond
      return (
        <path
          d="M50 2 L88 50 L50 98 L12 50 Z"
          fill="currentColor"
        />
      );
    case SuitValues.CLUBS:
      // Three distinct round lobes with visible gaps between them + wide stem
      // The key: lobes are smaller and spaced apart so gaps are visible even at small sizes
      return (
        <>
          <circle cx="50" cy="22" r="19" fill="currentColor" />
          <circle cx="26" cy="52" r="19" fill="currentColor" />
          <circle cx="74" cy="52" r="19" fill="currentColor" />
          <rect x="40" y="45" width="20" height="50" rx="2" fill="currentColor" />
        </>
      );
  }
}
