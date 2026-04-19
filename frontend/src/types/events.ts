import type { Card } from "./card";
import type { Bid, Player } from "./game";

export const ServerEventType = {
  CONNECTED: "connected",
  GAME_STARTED: "game_started",
  ROUND_STARTED: "round_started",
  CARDS_DEALT: "cards_dealt",
  BID_PLACED: "bid_placed",
  BIDDING_COMPLETE: "bidding_complete",
  CARD_PLAYED: "card_played",
  TRICK_COMPLETE: "trick_complete",
  ROUND_COMPLETE: "round_complete",
  GAME_OVER: "game_over",
  TURN_CHANGED: "turn_changed",
  INVALID_ACTION: "invalid_action",
  HAND: "hand",
  ERROR: "error",
  PLAYER_JOINED: "player_joined",
  PLAYER_LEFT: "player_left",
  AUTO_START_COUNTDOWN: "auto_start_countdown",
  GAME_STARTING: "game_starting",
  PLAYER_RECONNECTED: "player_reconnected",
  PLAYER_DISCONNECTED: "player_disconnected",
  MASCOT_PERSONA_AWARDED: "mascot_persona_awarded",
} as const;

export type ServerEventType = (typeof ServerEventType)[keyof typeof ServerEventType];

export interface ServerEvent {
  type: ServerEventType;
  data: Record<string, unknown>;
}

export interface ConnectedEventData {
  game_id: string;
  player_id: string;
  phase: string;
  current_player_id: string | null;
  players: Player[];
  round_number?: number;
  num_cards?: number;
  trump_suit?: string;
  dealer_id?: string;
  bids?: Array<{ player_id: string; amount: number }>;
  current_trick?: Array<{ player_id: string; card: Card }>;
  tricks_won?: Record<string, number>;
}

export interface RoundStartedEventData {
  round_number: number;
  num_cards: number;
  trump_suit: string;
  dealer_id: string;
}

export interface CardsDealtEventData {
  hand: Card[];
}

export interface BidPlacedEventData {
  player_id: string;
  amount: number;
}

export interface BiddingCompleteEventData {
  bids: Bid[];
}

export interface CardPlayedEventData {
  player_id: string;
  card: Card;
}

export interface TrickCompleteEventData {
  winner_id: string;
  tricks_won: Record<string, number>;
}

export interface RoundCompleteEventData {
  round_scores: Record<string, number>;
  cumulative_scores: Record<string, number>;
  tricks_won: Record<string, number>;
  bids: Bid[];
}

export interface PersonaAward {
  persona_id: string;
  persona_name: string;
  persona_category: string;
  persona_tagline: string;
  traits: Record<string, number>;
  player_traits: Record<string, number>;
}

export interface GameOverEventData {
  final_scores: Record<string, number>;
  winners: string[];
  persona: PersonaAward | null;
}

export interface TurnChangedEventData {
  player_id: string;
  phase: string;
}

export interface HandEventData {
  hand: Card[];
  valid_cards: Card[];
  valid_bids: number[];
}

export interface ErrorEventData {
  message: string;
}

export interface PlayerJoinedEventData {
  player_id: string;
  player_name: string;
  player_count: number;
}

export interface PlayerLeftEventData {
  player_id: string;
  player_name: string;
  player_count: number;
}

export interface AutoStartCountdownEventData {
  seconds_remaining: number;
}

export interface MascotPersonaAwardedEventData {
  persona_id: string;
  persona_name: string;
  persona_category: string;
  persona_tagline: string;
  traits: Record<string, number>;
  player_traits: Record<string, number>;
}

export const ClientAction = {
  BID: "bid",
  PLAY: "play",
  GET_HAND: "get_hand",
  NEXT_ROUND: "next_round",
} as const;

export type ClientAction = (typeof ClientAction)[keyof typeof ClientAction];
