import { useReducer, useCallback } from "react";
import type {
  GameState,
  Card,
  ServerEvent,
  ConnectedEventData,
  RoundStartedEventData,
  CardsDealtEventData,
  BidPlacedEventData,
  BiddingCompleteEventData,
  CardPlayedEventData,
  TrickCompleteEventData,
  RoundCompleteEventData,
  GameOverEventData,
  TurnChangedEventData,
  HandEventData,
  ErrorEventData,
  PlayerJoinedEventData,
  PlayerLeftEventData,
  AutoStartCountdownEventData,
} from "../types";
import {
  GamePhase,
  INITIAL_GAME_STATE,
  ServerEventType,
} from "../types";

// --- Action types ---

type GameAction =
  | { type: "SET_GAME_INFO"; gameId: string; playerId: string }
  | { type: "SERVER_EVENT"; event: ServerEvent }
  | { type: "SET_ERROR"; error: string }
  | { type: "CLEAR_ERROR" }
  | { type: "RESET" }
  | { type: "ACKNOWLEDGE_ROUND_OVER" }
  | { type: "START_TRICK_COLLECT" }
  | { type: "CLEAR_TRICK" };

// --- Reducer ---

function gameReducer(state: GameState, action: GameAction): GameState {
  switch (action.type) {
    case "SET_GAME_INFO":
      return handleSetGameInfo(state, action.gameId, action.playerId);
    case "SERVER_EVENT":
      return handleServerEvent(state, action.event);
    case "SET_ERROR":
      return { ...state, error: action.error };
    case "CLEAR_ERROR":
      return { ...state, error: null };
    case "RESET":
      return INITIAL_GAME_STATE;
    case "ACKNOWLEDGE_ROUND_OVER":
      return handleAcknowledgeRoundOver(state);
    case "START_TRICK_COLLECT":
      return { ...state, trickCollecting: true };
    case "CLEAR_TRICK":
      return handleClearTrick(state);
    default:
      return state;
  }
}

// --- Game info ---

function handleSetGameInfo(
  state: GameState,
  gameId: string,
  playerId: string,
): GameState {
  // When gameId is set from lobby, transition to WAITING so we show WaitingRoom
  // (WebSocket connected event will refine the phase if game already started)
  const phase = state.phase === GamePhase.LOBBY ? GamePhase.WAITING : state.phase;
  return { ...state, gameId, playerId, phase };
}

// --- Server event dispatch ---

function handleServerEvent(state: GameState, event: ServerEvent): GameState {
  // Buffer events while trick winner is being displayed
  if (state.trickWinner !== null) {
    return {
      ...state,
      pendingEvents: [...state.pendingEvents, event],
    };
  }

  // Buffer events while showing round-end scoreboard
  if (state.phase === GamePhase.ROUND_OVER && !state.roundOverAcknowledged) {
    return {
      ...state,
      pendingEvents: [...state.pendingEvents, event],
    };
  }

  switch (event.type) {
    case ServerEventType.CONNECTED:
      return handleConnected(state, event.data as unknown as ConnectedEventData);
    case ServerEventType.ROUND_STARTED:
      return handleRoundStarted(state, event.data as unknown as RoundStartedEventData);
    case ServerEventType.CARDS_DEALT:
      return handleCardsDealt(state, event.data as unknown as CardsDealtEventData);
    case ServerEventType.BID_PLACED:
      return handleBidPlaced(state, event.data as unknown as BidPlacedEventData);
    case ServerEventType.BIDDING_COMPLETE:
      return handleBiddingComplete(state, event.data as unknown as BiddingCompleteEventData);
    case ServerEventType.CARD_PLAYED:
      return handleCardPlayed(state, event.data as unknown as CardPlayedEventData);
    case ServerEventType.TRICK_COMPLETE:
      return handleTrickComplete(state, event.data as unknown as TrickCompleteEventData);
    case ServerEventType.ROUND_COMPLETE:
      return handleRoundComplete(state, event.data as unknown as RoundCompleteEventData);
    case ServerEventType.GAME_OVER:
      return handleGameOver(state, event.data as unknown as GameOverEventData);
    case ServerEventType.TURN_CHANGED:
      return handleTurnChanged(state, event.data as unknown as TurnChangedEventData);
    case ServerEventType.HAND:
      return handleHand(state, event.data as unknown as HandEventData);
    case ServerEventType.INVALID_ACTION:
    case ServerEventType.ERROR:
      return handleError(state, event.data as unknown as ErrorEventData);
    case ServerEventType.PLAYER_JOINED:
      return handlePlayerJoined(state, event.data as unknown as PlayerJoinedEventData);
    case ServerEventType.PLAYER_LEFT:
      return handlePlayerLeft(state, event.data as unknown as PlayerLeftEventData);
    case ServerEventType.AUTO_START_COUNTDOWN:
      return handleAutoStartCountdown(state, event.data as unknown as AutoStartCountdownEventData);
    case ServerEventType.GAME_STARTING:
      return state; // Game will transition via GAME_STARTED event
    default:
      return state;
  }
}

// --- Individual event handlers ---

function handleConnected(state: GameState, data: ConnectedEventData): GameState {
  // Backend "lobby" phase maps to WAITING in frontend (player already joined)
  const phase = data.phase === "lobby" ? GamePhase.WAITING : data.phase as GamePhase;
  const playerId = state.playerId ?? data.player_id;
  const hostId = (data as unknown as Record<string, unknown>).host_player_id as string | undefined;
  const lobbyPlayers = (data.players ?? []).map((player) => ({
    id: player.id,
    name: player.name,
    isHost: player.id === hostId,
  }));
  return {
    ...state,
    gameId: data.game_id,
    playerId,
    phase,
    isHost: playerId === hostId,
    currentPlayerId: data.current_player_id,
    players: data.players ?? state.players,
    lobbyPlayers,
    roundNumber: data.round_number ?? state.roundNumber,
    numCards: data.num_cards ?? state.numCards,
    trumpSuit: data.trump_suit ?? state.trumpSuit,
    dealerId: data.dealer_id ?? state.dealerId,
    bids: data.bids ?? state.bids,
    currentTrick: data.current_trick ?? state.currentTrick,
    tricksWon: data.tricks_won ?? state.tricksWon,
  };
}

function handleRoundStarted(state: GameState, data: RoundStartedEventData): GameState {
  return {
    ...state,
    phase: GamePhase.BIDDING,
    trumpSuit: data.trump_suit,
    numCards: data.num_cards,
    roundNumber: data.round_number,
    dealerId: data.dealer_id,
    bids: [],
    currentTrick: [],
    tricksWon: {},
    error: null,
  };
}

function handleCardsDealt(state: GameState, data: CardsDealtEventData): GameState {
  return {
    ...state,
    hand: data.hand,
    validCards: [],
    validBids: [],
  };
}

function handleBidPlaced(state: GameState, data: BidPlacedEventData): GameState {
  const newBid = { player_id: data.player_id, amount: data.amount };
  return {
    ...state,
    bids: [...state.bids, newBid],
  };
}

function handleBiddingComplete(state: GameState, data: BiddingCompleteEventData): GameState {
  return {
    ...state,
    phase: GamePhase.PLAYING,
    bids: data.bids,
    validBids: [],
  };
}

function handleCardPlayed(state: GameState, data: CardPlayedEventData): GameState {
  const updatedTrick = [...state.currentTrick, { player_id: data.player_id, card: data.card }];
  const updatedHand = removeCardFromHand(state.hand, data.card, data.player_id, state.playerId);
  const isOwnPlay = data.player_id === state.playerId;
  return {
    ...state,
    currentTrick: updatedTrick,
    hand: updatedHand,
    validCards: isOwnPlay ? [] : state.validCards,
  };
}

function handleTrickComplete(state: GameState, data: TrickCompleteEventData): GameState {
  return {
    ...state,
    tricksWon: data.tricks_won,
    trickWinner: data.winner_id,
    trickCollecting: false,
    // Keep currentTrick visible — it will be cleared by CLEAR_TRICK after animation
  };
}

function handleRoundComplete(state: GameState, data: RoundCompleteEventData): GameState {
  return {
    ...state,
    phase: GamePhase.ROUND_OVER,
    cumulativeScores: data.cumulative_scores,
    tricksWon: data.tricks_won,
    roundScores: data.round_scores,
    hand: [],
    validCards: [],
    validBids: [],
    currentTrick: [],
    trickWinner: null,
    trickCollecting: false,
    pendingEvents: [],
    roundOverAcknowledged: false,
  };
}

function handleGameOver(state: GameState, data: GameOverEventData): GameState {
  return {
    ...state,
    phase: GamePhase.GAME_OVER,
    cumulativeScores: data.final_scores,
  };
}

function handleTurnChanged(state: GameState, data: TurnChangedEventData): GameState {
  return {
    ...state,
    currentPlayerId: data.player_id,
    phase: data.phase as GamePhase,
  };
}

function handleHand(state: GameState, data: HandEventData): GameState {
  return {
    ...state,
    hand: data.hand,
    validCards: data.valid_cards,
    validBids: data.valid_bids,
  };
}

function handlePlayerJoined(state: GameState, data: PlayerJoinedEventData): GameState {
  const alreadyExists = state.lobbyPlayers.some((p) => p.id === data.player_id);
  if (alreadyExists) return state;
  return {
    ...state,
    lobbyPlayers: [...state.lobbyPlayers, { id: data.player_id, name: data.player_name, isHost: false }],
  };
}

function handlePlayerLeft(state: GameState, data: PlayerLeftEventData): GameState {
  return {
    ...state,
    lobbyPlayers: state.lobbyPlayers.filter((p) => p.id !== data.player_id),
    autoStartSeconds: data.player_count < 2 ? null : state.autoStartSeconds,
  };
}

function handleAutoStartCountdown(state: GameState, data: AutoStartCountdownEventData): GameState {
  return {
    ...state,
    autoStartSeconds: data.seconds_remaining,
  };
}

function handleError(state: GameState, data: ErrorEventData): GameState {
  const errorData = data as ErrorEventData & { reason?: string };
  const message = errorData.message ?? errorData.reason ?? "Unknown error";
  return {
    ...state,
    error: String(message),
  };
}

function handleClearTrick(state: GameState): GameState {
  let newState: GameState = {
    ...state,
    currentTrick: [],
    trickWinner: null,
    trickCollecting: false,
    pendingEvents: [],
  };
  // Replay buffered events. Some may re-buffer (e.g. round-over buffering)
  // so we keep whatever pendingEvents accumulate during replay.
  for (const event of state.pendingEvents) {
    newState = handleServerEvent(newState, event);
  }
  return newState;
}

function handleAcknowledgeRoundOver(state: GameState): GameState {
  let newState = { ...state, roundOverAcknowledged: true };
  for (const event of state.pendingEvents) {
    newState = handleServerEvent(newState, event);
  }
  return {
    ...newState,
    pendingEvents: [],
    roundOverAcknowledged: false,
  };
}

// --- Helpers ---

function removeCardFromHand(
  hand: Card[],
  playedCard: Card,
  playedById: string,
  myPlayerId: string | null,
): Card[] {
  if (playedById !== myPlayerId) {
    return hand;
  }
  const cardIndex = hand.findIndex(
    (card) => card.suit === playedCard.suit && card.rank === playedCard.rank,
  );
  if (cardIndex === -1) {
    return hand;
  }
  return [...hand.slice(0, cardIndex), ...hand.slice(cardIndex + 1)];
}

// --- Hook ---

export function useGame() {
  const [state, dispatch] = useReducer(gameReducer, INITIAL_GAME_STATE);

  const setGameInfo = useCallback((gameId: string, playerId: string) => {
    dispatch({ type: "SET_GAME_INFO", gameId, playerId });
  }, []);

  const handleServerEvent = useCallback((event: ServerEvent) => {
    dispatch({ type: "SERVER_EVENT", event });
  }, []);

  const setError = useCallback((error: string) => {
    dispatch({ type: "SET_ERROR", error });
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: "CLEAR_ERROR" });
  }, []);

  const resetGame = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  const acknowledgeRoundOver = useCallback(() => {
    dispatch({ type: "ACKNOWLEDGE_ROUND_OVER" });
  }, []);

  const startTrickCollect = useCallback(() => {
    dispatch({ type: "START_TRICK_COLLECT" });
  }, []);

  const clearTrick = useCallback(() => {
    dispatch({ type: "CLEAR_TRICK" });
  }, []);

  return {
    state,
    setGameInfo,
    handleServerEvent,
    setError,
    clearError,
    resetGame,
    acknowledgeRoundOver,
    startTrickCollect,
    clearTrick,
  };
}
