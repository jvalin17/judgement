import { memo } from "react";
import type { Suit } from "../../types";
import { Suit as SuitValues } from "../../types";

interface SuitSvgProps {
  suit: Suit;
  size?: number;
  className?: string;
}

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
      // Classic spade: pointed top, curved body, two small flares at base, thin stem
      return (
        <>
          <path
            d="M50 4 C50 4 6 42 6 62 C6 78 20 82 36 72 C38 82 40 92 40 92 L60 92 C60 92 62 82 64 72 C80 82 94 78 94 62 C94 42 50 4 50 4Z"
            fill="currentColor"
          />
          {/* Cut out between flares and stem to make the base shape clearer */}
          <ellipse cx="50" cy="78" rx="10" ry="6" fill="currentColor" />
        </>
      );
    case SuitValues.HEARTS:
      return (
        <path
          d="M50 88 C50 88 5 55 5 32 C5 12 20 2 35 2 C45 2 50 12 50 22 C50 12 55 2 65 2 C80 2 95 12 95 32 C95 55 50 88 50 88Z"
          fill="currentColor"
        />
      );
    case SuitValues.DIAMONDS:
      return (
        <path
          d="M50 2 C50 2 88 46 88 50 C88 54 50 98 50 98 C50 98 12 54 12 50 C12 46 50 2 50 2Z"
          fill="currentColor"
        />
      );
    case SuitValues.CLUBS:
      // Trefoil: three distinct circles arranged as a triangle, connected by a narrow stem
      return (
        <>
          {/* Top lobe */}
          <circle cx="50" cy="20" r="18" fill="currentColor" />
          {/* Bottom-left lobe */}
          <circle cx="28" cy="50" r="18" fill="currentColor" />
          {/* Bottom-right lobe */}
          <circle cx="72" cy="50" r="18" fill="currentColor" />
          {/* Center fill between lobes */}
          <path d="M42 30 L58 30 L68 44 L50 55 L32 44 Z" fill="currentColor" />
          {/* Stem */}
          <path d="M44 55 L44 92 L56 92 L56 55 Z" fill="currentColor" />
          {/* Small flares at base of stem */}
          <path d="M34 92 L44 80 L44 92 Z" fill="currentColor" />
          <path d="M66 92 L56 80 L56 92 Z" fill="currentColor" />
        </>
      );
  }
}
