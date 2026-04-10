import type { Suit } from "../../types";
import { SUIT_SYMBOLS, SUIT_COLORS } from "../../types";

interface SuitIconProps {
  suit: Suit;
  size?: "sm" | "md" | "lg";
}

const SIZE_MAP = {
  sm: "1rem",
  md: "1.5rem",
  lg: "2rem",
};

export function SuitIcon({ suit, size = "md" }: SuitIconProps) {
  return (
    <span
      style={{ color: SUIT_COLORS[suit], fontSize: SIZE_MAP[size] }}
      aria-label={suit}
    >
      {SUIT_SYMBOLS[suit]}
    </span>
  );
}
