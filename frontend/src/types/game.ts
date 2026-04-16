import type { Card } from "./card";
import type { ServerEvent } from "./events";

// INTENTIONAL BREAK for CI validation — will revert
export enum DeliberateBreak { Foo = "foo" }

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
};

export const VARIANT_LABELS: Record<DealingVariant, string> = {
  [DealingVariant.TEN_TO_ONE]: "10 → 1 (10 rounds)",
  [DealingVariant.EIGHT_DOWN_UP]: "8 → 1 → 8 (16 rounds)",
  [DealingVariant.TEN_DOWN_UP]: "10 → 1 → 10 (20 rounds)",
  [DealingVariant.EIGHT_DOWN_UP_SHORT]: "8 → 5 → 8 (8 rounds)",
};

export const VARIANT_MAX_PLAYERS: Record<DealingVariant, number> = {
  [DealingVariant.TEN_TO_ONE]: 5,
  [DealingVariant.EIGHT_DOWN_UP]: 6,
  [DealingVariant.TEN_DOWN_UP]: 5,
  [DealingVariant.EIGHT_DOWN_UP_SHORT]: 6,
};

export function isMyTurn(state: GameState): boolean {
  return state.currentPlayerId === state.playerId;
}
