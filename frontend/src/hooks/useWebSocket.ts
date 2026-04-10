import { useRef, useCallback, useEffect, useState } from "react";
import { GameWebSocket, ConnectionStatus } from "../services/websocket";
import type { EventHandler } from "../services/websocket";

interface UseWebSocketOptions {
  gameId: string | null;
  playerId: string | null;
  onEvent: EventHandler;
  autoConnect?: boolean;
}

interface UseWebSocketResult {
  connectionStatus: ConnectionStatus;
  connect: () => void;
  disconnect: () => void;
  sendBid: (amount: number) => void;
  sendPlayCard: (card: { suit: string; rank: number }) => void;
  sendGetHand: () => void;
}

export function useWebSocket({
  gameId,
  playerId,
  onEvent,
  autoConnect = true,
}: UseWebSocketOptions): UseWebSocketResult {
  const socketRef = useRef<GameWebSocket | null>(null);
  const onEventRef = useRef(onEvent);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);

  onEventRef.current = onEvent;

  // --- Connection management ---

  const createAndConnect = useCallback(() => {
    if (!gameId || !playerId) return;

    cleanupExistingSocket(socketRef.current);

    const socket = new GameWebSocket(gameId, playerId);
    socket.onEvent((event) => onEventRef.current(event));
    socket.onStatusChange(setConnectionStatus);
    socket.connect();

    socketRef.current = socket;
  }, [gameId, playerId]);

  const disconnect = useCallback(() => {
    cleanupExistingSocket(socketRef.current);
    socketRef.current = null;
    setConnectionStatus(ConnectionStatus.DISCONNECTED);
  }, []);

  // --- Auto-connect on mount / params change ---

  useEffect(() => {
    if (autoConnect && gameId && playerId) {
      createAndConnect();
    }

    return () => {
      cleanupExistingSocket(socketRef.current);
      socketRef.current = null;
    };
  }, [gameId, playerId, autoConnect, createAndConnect]);

  // --- Actions ---

  const sendBid = useCallback((amount: number) => {
    socketRef.current?.sendBid(amount);
  }, []);

  const sendPlayCard = useCallback((card: { suit: string; rank: number }) => {
    socketRef.current?.sendPlayCard(card as { suit: string; rank: number } & { suit: import("../types").Suit; rank: import("../types").Rank });
  }, []);

  const sendGetHand = useCallback(() => {
    socketRef.current?.sendGetHand();
  }, []);

  return {
    connectionStatus,
    connect: createAndConnect,
    disconnect,
    sendBid,
    sendPlayCard,
    sendGetHand,
  };
}

// --- Helpers ---

function cleanupExistingSocket(socket: GameWebSocket | null): void {
  if (socket) {
    socket.disconnect();
  }
}
