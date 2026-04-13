import { createContext, useContext, useMemo, useEffect } from "react";
import type { ReactNode } from "react";
import type { GameState, Card } from "../types";
import { useGame } from "../hooks/useGame";
import { useWebSocket } from "../hooks/useWebSocket";
import type { ConnectionStatus } from "../services/websocket";

const SESSION_KEY = "judgement_session";

// --- Context shape ---

interface GameContextValue {
  state: GameState;
  connectionStatus: ConnectionStatus;
  actions: GameActions;
}

interface GameActions {
  setGameInfo: (gameId: string, playerId: string) => void;
  resetGame: () => void;
  clearError: () => void;
  connect: () => void;
  disconnect: () => void;
  sendBid: (amount: number) => void;
  sendPlayCard: (card: Card) => void;
  sendGetHand: () => void;
  acknowledgeRoundOver: () => void;
  startTrickCollect: () => void;
  clearTrick: () => void;
}

const GameContext = createContext<GameContextValue | null>(null);

// --- Provider ---

interface GameProviderProps {
  children: ReactNode;
}

export function GameProvider({ children }: GameProviderProps) {
  const {
    state,
    setGameInfo,
    handleServerEvent,
    clearError,
    resetGame,
    acknowledgeRoundOver,
    startTrickCollect,
    clearTrick,
  } = useGame();

  // Restore session from sessionStorage on mount
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(SESSION_KEY);
      if (saved) {
        const { gameId, playerId } = JSON.parse(saved);
        if (gameId && playerId) {
          setGameInfo(gameId, playerId);
        }
      }
    } catch {
      // Ignore parse errors
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Save session to sessionStorage when gameId/playerId change
  useEffect(() => {
    if (state.gameId && state.playerId) {
      sessionStorage.setItem(SESSION_KEY, JSON.stringify({
        gameId: state.gameId,
        playerId: state.playerId,
      }));
    }
  }, [state.gameId, state.playerId]);

  const {
    connectionStatus,
    connect,
    disconnect,
    sendBid,
    sendPlayCard,
    sendGetHand,
  } = useWebSocket({
    gameId: state.gameId,
    playerId: state.playerId,
    onEvent: handleServerEvent,
    autoConnect: true,
  });

  const wrappedResetGame = useMemo(() => () => {
    sessionStorage.removeItem(SESSION_KEY);
    resetGame();
  }, [resetGame]);

  const wrappedDisconnect = useMemo(() => () => {
    sessionStorage.removeItem(SESSION_KEY);
    disconnect();
  }, [disconnect]);

  const actions: GameActions = useMemo(
    () => ({
      setGameInfo,
      resetGame: wrappedResetGame,
      clearError,
      connect,
      disconnect: wrappedDisconnect,
      sendBid,
      sendPlayCard,
      sendGetHand,
      acknowledgeRoundOver,
      startTrickCollect,
      clearTrick,
    }),
    [setGameInfo, wrappedResetGame, clearError, connect, wrappedDisconnect, sendBid, sendPlayCard, sendGetHand, acknowledgeRoundOver, startTrickCollect, clearTrick],
  );

  const contextValue: GameContextValue = useMemo(
    () => ({ state, connectionStatus, actions }),
    [state, connectionStatus, actions],
  );

  return (
    <GameContext.Provider value={contextValue}>
      {children}
    </GameContext.Provider>
  );
}

// --- Hook ---

export function useGameContext(): GameContextValue {
  const context = useContext(GameContext);
  if (!context) {
    throw new Error("useGameContext must be used within a GameProvider");
  }
  return context;
}
