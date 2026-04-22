import type { Card } from "./card";
import type { ServerEvent, PersonaAward } from "./events";

export const GamePhase = {
  LOBBY: "lobby",
  WAITING: "waiting",
  DEALING: "dealing",
  BIDDING: "bidding",
  PLAYING: "playing",
  ROUND_OVER: "round_over",
  GAME_OVER: "game_over",
} as const;

export type GamePhase = (typeof GamePhase)[keyof typeof GamePhase];

export const DealingVariant = {
  TEN_TO_ONE: "10_to_1",
  EIGHT_DOWN_UP: "8_down_up",
  TEN_DOWN_UP: "10_down_up",
  EIGHT_DOWN_UP_SHORT: "8_down_up_short",
  EIGHT_TO_THREE: "8_to_3",
  THREE_QUICK: "3_quick",
} as const;

export type DealingVariant = (typeof DealingVariant)[keyof typeof DealingVariant];

export const PlayerType = {
  HUMAN: "human",
  AI: "ai",
} as const;

export type PlayerType = (typeof PlayerType)[keyof typeof PlayerType];

export const AIDifficulty = {
  EASY: "easy",
  MEDIUM: "medium",
  HARD: "hard",
} as const;

export type AIDifficulty = (typeof AIDifficulty)[keyof typeof AIDifficulty];

export interface Player {
  id: string;
  name: string;
  player_type: PlayerType;
  ai_difficulty: AIDifficulty | null;
}

export interface Bid {
  player_id: string;
  amount: number;
}

export interface TrickPlay {
  player_id: string;
  card: Card;
}

export interface GameState {
  gameId: string | null;
  playerId: string | null;
  phase: GamePhase;
  players: Player[];
  currentPlayerId: string | null;
  trumpSuit: string | null;
  numCards: number | null;
  roundNumber: number | null;
  dealerId: string | null;
  bids: Bid[];
  currentTrick: TrickPlay[];
  tricksWon: Record<string, number>;
  cumulativeScores: Record<string, number>;
  hand: Card[];
  validCards: Card[];
  validBids: number[];
  error: string | null;
  pendingEvents: ServerEvent[];
  roundOverAcknowledged: boolean;
  roundScores: Record<string, number>;
  trickWinner: string | null;
  trickCollecting: boolean;
  lobbyPlayers: Array<{ id: string; name: string; isHost: boolean }>;
  autoStartSeconds: number | null;
  isHost: boolean;
  awardedPersona: PersonaAward | null;
  mustLoseMode: boolean;
  challengeMode: boolean;
}

export interface RoundSummary {
  roundNumber: number;
  numCards: number;
  trumpSuit: string;
  dealerId: string;
  bids: Bid[];
  tricksWon: Record<string, number>;
  scores: Record<string, number>;
}

export const INITIAL_GAME_STATE: GameState = {
  gameId: null,
  playerId: null,
  phase: GamePhase.LOBBY,
  players: [],
  currentPlayerId: null,
  trumpSuit: null,
  numCards: null,
  roundNumber: null,
  dealerId: null,
  bids: [],
  currentTrick: [],
  tricksWon: {},
  cumulativeScores: {},
  hand: [],
  validCards: [],
  validBids: [],
  error: null,
  pendingEvents: [],
  roundOverAcknowledged: false,
  roundScores: {},
  trickWinner: null,
  trickCollecting: false,
  lobbyPlayers: [],
  autoStartSeconds: null,
  isHost: false,
  awardedPersona: null,
  mustLoseMode: false,
  challengeMode: false,
};

export interface VariantConfig {
  label: string;
  rounds: string;
  detail: string;
  maxPlayers: number;
}

export const VARIANT_CONFIG: Record<DealingVariant, VariantConfig> = {
  [DealingVariant.TEN_TO_ONE]:          { label: "10 down to 1 — 10 rounds",          rounds: "10 rounds", detail: "10 down to 1",             maxPlayers: 5  },
  [DealingVariant.EIGHT_DOWN_UP]:       { label: "8 down to 1, back to 8 — 16 rounds", rounds: "16 rounds", detail: "8 down to 1, back to 8",   maxPlayers: 6  },
  [DealingVariant.TEN_DOWN_UP]:         { label: "10 down to 1, back to 10 — 20 rounds", rounds: "20 rounds", detail: "10 down to 1, back to 10", maxPlayers: 5  },
  [DealingVariant.EIGHT_DOWN_UP_SHORT]: { label: "8 down to 5, back to 8 — 8 rounds",  rounds: "8 rounds",  detail: "8 down to 5, back to 8",   maxPlayers: 6  },
  [DealingVariant.EIGHT_TO_THREE]:     { label: "8 down to 4 — 5 rounds",            rounds: "5 rounds",  detail: "8 down to 4",               maxPlayers: 6  },
  [DealingVariant.THREE_QUICK]:         { label: "Quick game — 3 rounds",              rounds: "3 rounds",  detail: "Quick game: 5, 3, 5 cards", maxPlayers: 10 },
};

export const VARIANT_LIST: DealingVariant[] = Object.keys(VARIANT_CONFIG) as DealingVariant[];

// Convenience accessors for backward compatibility
export const VARIANT_LABELS: Record<DealingVariant, string> =
  Object.fromEntries(VARIANT_LIST.map((v) => [v, VARIANT_CONFIG[v].label])) as Record<DealingVariant, string>;

export const VARIANT_MAX_PLAYERS: Record<DealingVariant, number> =
  Object.fromEntries(VARIANT_LIST.map((v) => [v, VARIANT_CONFIG[v].maxPlayers])) as Record<DealingVariant, number>;

export function isMyTurn(state: GameState): boolean {
  return state.currentPlayerId === state.playerId;
}
