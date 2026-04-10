import { createContext, useContext, useMemo } from "react";
import type { ReactNode } from "react";
import type { GameState, Card } from "../types";
import { useGame } from "../hooks/useGame";
import { useWebSocket } from "../hooks/useWebSocket";
import type { ConnectionStatus } from "../services/websocket";

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

  const actions: GameActions = useMemo(
    () => ({
      setGameInfo,
      resetGame,
      clearError,
      connect,
      disconnect,
      sendBid,
      sendPlayCard,
      sendGetHand,
      acknowledgeRoundOver,
      startTrickCollect,
      clearTrick,
    }),
    [setGameInfo, resetGame, clearError, connect, disconnect, sendBid, sendPlayCard, sendGetHand, acknowledgeRoundOver, startTrickCollect, clearTrick],
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
