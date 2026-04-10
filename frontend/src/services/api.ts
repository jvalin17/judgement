import type {
  DealingVariant,
  AIDifficulty,
  Card,
  Bid,
  TrickPlay,
  Player,
} from "../types";

// --- Request/Response types ---

export interface PlayerSetup {
  name: string;
  is_ai: boolean;
  ai_difficulty: AIDifficulty | null;
}

export interface CreateGameRequest {
  variant: DealingVariant;
  must_lose_mode: boolean;
  players: PlayerSetup[];
}

export interface CreateGameResponse {
  game_id: string;
  player_ids: Record<string, string>;
}

export interface GameStateResponse {
  game_id: string;
  phase: string;
  players: Player[];
  current_player_id: string | null;
  trump_suit: string | null;
  num_cards: number | null;
  round_number: number | null;
  dealer_id: string | null;
  bids: Bid[];
  current_trick: TrickPlay[];
  tricks_won: Record<string, number>;
  cumulative_scores: Record<string, number>;
}

export interface PlayerHandResponse {
  hand: Card[];
  valid_cards: Card[];
  valid_bids: number[];
}

export interface ActionResponse {
  success: boolean;
  message: string;
}

export interface SessionLogResponse {
  game_id: string;
  players: Array<Record<string, string>>;
  variant: string;
  rounds: Array<Record<string, unknown>>;
  final_scores: Record<string, number>;
  winners: string[];
}

// --- API client ---

const BASE_URL = "/api/games";

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(response.status, body);
  }
  return response.json();
}

function postJson(url: string, body: unknown): Promise<Response> {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

// --- Public API functions ---

export async function createGame(
  request: CreateGameRequest,
): Promise<CreateGameResponse> {
  const response = await postJson(BASE_URL, request);
  return handleResponse<CreateGameResponse>(response);
}

export async function getGameState(
  gameId: string,
): Promise<GameStateResponse> {
  const response = await fetch(`${BASE_URL}/${gameId}`);
  return handleResponse<GameStateResponse>(response);
}

export async function getPlayerHand(
  gameId: string,
  playerId: string,
): Promise<PlayerHandResponse> {
  const response = await fetch(`${BASE_URL}/${gameId}/hand/${playerId}`);
  return handleResponse<PlayerHandResponse>(response);
}

export async function placeBid(
  gameId: string,
  playerId: string,
  amount: number,
): Promise<ActionResponse> {
  const response = await postJson(`${BASE_URL}/${gameId}/bid`, {
    player_id: playerId,
    amount,
  });
  return handleResponse<ActionResponse>(response);
}

export async function playCard(
  gameId: string,
  playerId: string,
  card: Card,
): Promise<ActionResponse> {
  const response = await postJson(`${BASE_URL}/${gameId}/play`, {
    player_id: playerId,
    suit: card.suit,
    rank: card.rank,
  });
  return handleResponse<ActionResponse>(response);
}

export async function getSessionLog(
  gameId: string,
): Promise<SessionLogResponse> {
  const response = await fetch(`${BASE_URL}/${gameId}/session-log`);
  return handleResponse<SessionLogResponse>(response);
}
