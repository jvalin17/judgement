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

// --- Multiplayer API ---

export interface JoinGameResponse {
  player_id: string;
  game_id: string;
}

export interface LobbyGameInfo {
  game_id: string;
  host_name: string | null;
  variant: string;
  must_lose_mode: boolean;
  player_count: number;
  max_players: number;
}

export interface LobbyStateResponse {
  game_id: string;
  phase: string;
  variant: string;
  must_lose_mode: boolean;
  players: Array<Record<string, unknown>>;
  host_player_id: string | null;
  max_players: number;
}

export async function joinGame(
  gameId: string,
  playerName: string,
): Promise<JoinGameResponse> {
  const response = await postJson(`${BASE_URL}/${gameId}/join`, {
    player_name: playerName,
  });
  return handleResponse<JoinGameResponse>(response);
}

export async function startGame(
  gameId: string,
  playerId: string,
): Promise<ActionResponse> {
  const response = await postJson(`${BASE_URL}/${gameId}/start?player_id=${playerId}`, {});
  return handleResponse<ActionResponse>(response);
}

export async function getLobbyList(): Promise<{ games: LobbyGameInfo[] }> {
  const response = await fetch("/api/lobby");
  return handleResponse<{ games: LobbyGameInfo[] }>(response);
}

export async function quickJoin(
  playerName: string,
  variant?: string,
): Promise<JoinGameResponse> {
  const body: Record<string, string> = { player_name: playerName };
  if (variant) body.variant = variant;
  const response = await postJson("/api/lobby/quick-join", body);
  return handleResponse<JoinGameResponse>(response);
}

export async function getLobbyState(
  gameId: string,
): Promise<LobbyStateResponse> {
  const response = await fetch(`${BASE_URL}/${gameId}/lobby`);
  return handleResponse<LobbyStateResponse>(response);
}

// --- Update API ---

export interface VersionInfo {
  git_sha: string;
  build_date: string | null;
}

export interface UpdateCheckResponse {
  update_available: boolean;
  current_sha: string;
  latest_sha: string | null;
  latest_message: string | null;
  error: string | null;
}

export async function getVersion(): Promise<VersionInfo> {
  const response = await fetch("/api/update/version");
  return handleResponse<VersionInfo>(response);
}

export async function checkForUpdate(): Promise<UpdateCheckResponse> {
  const response = await fetch("/api/update/check");
  return handleResponse<UpdateCheckResponse>(response);
}

export async function applyUpdate(): Promise<{ success: boolean; message: string }> {
  const response = await postJson("/api/update/apply", {});
  return handleResponse<{ success: boolean; message: string }>(response);
}
