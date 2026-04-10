import type { Rank, Suit } from "../../types";
import { Rank as RankValues, SUIT_COLORS } from "../../types";

interface FaceCardArtProps {
  rank: Rank;
  suit: Suit;
}

/**
 * SVG face card portraits — stylized J/Q/K with suit-colored accents.
 * Each face has a mirrored design like traditional playing cards.
 */
export function FaceCardArt({ rank, suit }: FaceCardArtProps) {
  const color = getSuitHex(suit);

  if ((rank as number) === RankValues.JACK) return <JackArt color={color} />;
  if ((rank as number) === RankValues.QUEEN) return <QueenArt color={color} />;
  return <KingArt color={color} />;
}

function getSuitHex(suit: Suit): string {
  const colorName = SUIT_COLORS[suit];
  const map: Record<string, string> = {
    black: "#1a1a2e",
    red: "#c0392b",
  };
  return map[colorName] ?? "#1a1a2e";
}

function JackArt({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 60 80" width="100%" height="100%">
      {/* Hat */}
      <path d="M18 20 L30 8 L42 20 Z" fill={color} opacity="0.85" />
      <rect x="20" y="20" width="20" height="4" rx="1" fill={color} opacity="0.6" />
      {/* Face */}
      <ellipse cx="30" cy="32" rx="10" ry="11" fill="#f0dcc0" stroke={color} strokeWidth="1" />
      {/* Eyes */}
      <ellipse cx="26" cy="30" rx="1.5" ry="2" fill={color} />
      <ellipse cx="34" cy="30" rx="1.5" ry="2" fill={color} />
      {/* Mouth — slight smile */}
      <path d="M26 36 Q30 39 34 36" fill="none" stroke={color} strokeWidth="0.8" />
      {/* Collar / tunic */}
      <path d="M20 43 L25 40 L30 44 L35 40 L40 43 L42 55 L18 55 Z" fill={color} opacity="0.75" />
      {/* Feather accent */}
      <path d="M30 8 Q35 4 32 12" fill="none" stroke={color} strokeWidth="0.8" opacity="0.6" />
      {/* Decorative line */}
      <line x1="15" y1="56" x2="45" y2="56" stroke={color} strokeWidth="0.5" opacity="0.4" />
      {/* Mirrored lower half (inverted) */}
      <g transform="translate(60, 80) rotate(180)" opacity="0.3">
        <ellipse cx="30" cy="32" rx="8" ry="9" fill="#f0dcc0" stroke={color} strokeWidth="0.5" />
        <path d="M22 43 L26 40 L30 43 L34 40 L38 43 L40 52 L20 52 Z" fill={color} opacity="0.6" />
      </g>
    </svg>
  );
}

function QueenArt({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 60 80" width="100%" height="100%">
      {/* Crown */}
      <path d="M20 18 L23 10 L27 16 L30 7 L33 16 L37 10 L40 18 Z" fill="#daa520" stroke={color} strokeWidth="0.5" />
      {/* Crown jewels */}
      <circle cx="30" cy="10" r="1.5" fill={color} />
      <circle cx="24" cy="13" r="1" fill={color} opacity="0.7" />
      <circle cx="36" cy="13" r="1" fill={color} opacity="0.7" />
      {/* Face */}
      <ellipse cx="30" cy="30" rx="10" ry="11" fill="#f0dcc0" stroke={color} strokeWidth="1" />
      {/* Eyes */}
      <ellipse cx="26" cy="28" rx="1.5" ry="2" fill={color} />
      <ellipse cx="34" cy="28" rx="1.5" ry="2" fill={color} />
      {/* Eyelashes */}
      <path d="M24 26 L26 25" stroke={color} strokeWidth="0.4" />
      <path d="M34 25 L36 26" stroke={color} strokeWidth="0.4" />
      {/* Lips */}
      <path d="M27 34 Q30 37 33 34" fill={color} opacity="0.4" />
      {/* Necklace */}
      <path d="M22 41 Q30 46 38 41" fill="none" stroke="#daa520" strokeWidth="1" />
      <circle cx="30" cy="45" r="2" fill="#daa520" stroke={color} strokeWidth="0.3" />
      {/* Dress */}
      <path d="M18 44 L24 41 L30 47 L36 41 L42 44 L44 58 L16 58 Z" fill={color} opacity="0.7" />
      {/* Decorative line */}
      <line x1="15" y1="59" x2="45" y2="59" stroke={color} strokeWidth="0.5" opacity="0.4" />
      {/* Mirrored lower half */}
      <g transform="translate(60, 80) rotate(180)" opacity="0.3">
        <ellipse cx="30" cy="30" rx="8" ry="9" fill="#f0dcc0" stroke={color} strokeWidth="0.5" />
        <path d="M22 18 L25 12 L28 16 L30 9 L32 16 L35 12 L38 18 Z" fill="#daa520" opacity="0.5" />
        <path d="M20 41 L26 38 L30 43 L34 38 L40 41 L42 52 L18 52 Z" fill={color} opacity="0.5" />
      </g>
    </svg>
  );
}

function KingArt({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 60 80" width="100%" height="100%">
      {/* Crown — larger, more regal */}
      <path d="M18 20 L20 10 L25 17 L30 5 L35 17 L40 10 L42 20 Z" fill="#daa520" stroke={color} strokeWidth="0.8" />
      <rect x="18" y="20" width="24" height="3" rx="1" fill="#daa520" stroke={color} strokeWidth="0.3" />
      {/* Crown jewels */}
      <circle cx="30" cy="9" r="2" fill="#c0392b" stroke="#daa520" strokeWidth="0.5" />
      <circle cx="22" cy="14" r="1.2" fill={color} />
      <circle cx="38" cy="14" r="1.2" fill={color} />
      {/* Face */}
      <ellipse cx="30" cy="33" rx="10" ry="11" fill="#f0dcc0" stroke={color} strokeWidth="1" />
      {/* Beard */}
      <path d="M22 37 Q25 42 30 44 Q35 42 38 37" fill="#8b7355" opacity="0.5" />
      {/* Eyes — stern */}
      <line x1="24" y1="30" x2="28" y2="30" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      <line x1="32" y1="30" x2="36" y2="30" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      {/* Eyebrows */}
      <path d="M23 28 L28 27" stroke={color} strokeWidth="0.6" />
      <path d="M32 27 L37 28" stroke={color} strokeWidth="0.6" />
      {/* Mustache */}
      <path d="M26 35 Q30 33 34 35" fill={color} opacity="0.3" />
      {/* Robe */}
      <path d="M16 46 L23 42 L30 48 L37 42 L44 46 L46 60 L14 60 Z" fill={color} opacity="0.8" />
      {/* Robe trim */}
      <path d="M18 48 L42 48" stroke="#daa520" strokeWidth="1" opacity="0.6" />
      {/* Scepter hint */}
      <line x1="44" y1="35" x2="46" y2="55" stroke="#daa520" strokeWidth="1.5" opacity="0.5" />
      <circle cx="44" cy="34" r="2.5" fill="#daa520" opacity="0.4" />
      {/* Decorative line */}
      <line x1="13" y1="61" x2="47" y2="61" stroke={color} strokeWidth="0.5" opacity="0.4" />
      {/* Mirrored lower half */}
      <g transform="translate(60, 80) rotate(180)" opacity="0.3">
        <ellipse cx="30" cy="33" rx="8" ry="9" fill="#f0dcc0" stroke={color} strokeWidth="0.5" />
        <path d="M20 20 L22 12 L27 17 L30 7 L33 17 L38 12 L40 20 Z" fill="#daa520" opacity="0.5" />
        <path d="M18 44 L25 40 L30 46 L35 40 L42 44 L44 56 L16 56 Z" fill={color} opacity="0.5" />
      </g>
    </svg>
  );
}
