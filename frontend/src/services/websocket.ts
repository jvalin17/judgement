import type { ServerEvent } from "../types";
import { ClientAction } from "../types";
import type { Card } from "../types";

export type EventHandler = (event: ServerEvent) => void;

const RECONNECT_DELAYS_MS = [1000, 2000, 4000, 8000, 16000];
const MAX_RECONNECT_ATTEMPTS = RECONNECT_DELAYS_MS.length;

export const ConnectionStatus = {
  DISCONNECTED: "disconnected",
  CONNECTING: "connecting",
  CONNECTED: "connected",
  RECONNECTING: "reconnecting",
} as const;

export type ConnectionStatus = (typeof ConnectionStatus)[keyof typeof ConnectionStatus];

export class GameWebSocket {
  private socket: WebSocket | null = null;
  private eventHandler: EventHandler | null = null;
  private statusHandler: ((status: ConnectionStatus) => void) | null = null;
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private intentionalClose = false;

  private gameId: string;
  private playerId: string;

  constructor(gameId: string, playerId: string) {
    this.gameId = gameId;
    this.playerId = playerId;
  }

  // --- Public interface ---

  onEvent(handler: EventHandler): void {
    this.eventHandler = handler;
  }

  onStatusChange(handler: (status: ConnectionStatus) => void): void {
    this.statusHandler = handler;
  }

  connect(): void {
    this.intentionalClose = false;
    this.updateStatus(ConnectionStatus.CONNECTING);
    this.createSocket();
  }

  disconnect(): void {
    this.intentionalClose = true;
    this.cancelReconnect();
    this.closeSocket();
    this.updateStatus(ConnectionStatus.DISCONNECTED);
  }

  sendBid(amount: number): void {
    this.sendMessage({ action: ClientAction.BID, amount });
  }

  sendPlayCard(card: Card): void {
    this.sendMessage({
      action: ClientAction.PLAY,
      suit: card.suit,
      rank: card.rank,
    });
  }

  sendGetHand(): void {
    this.sendMessage({ action: ClientAction.GET_HAND });
  }

  // --- Socket lifecycle ---

  private createSocket(): void {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/${this.gameId}/${this.playerId}`;

    this.socket = new WebSocket(url);
    this.socket.onopen = this.handleOpen.bind(this);
    this.socket.onmessage = this.handleMessage.bind(this);
    this.socket.onclose = this.handleClose.bind(this);
    this.socket.onerror = this.handleError.bind(this);
  }

  private closeSocket(): void {
    if (this.socket) {
      this.socket.onopen = null;
      this.socket.onmessage = null;
      this.socket.onclose = null;
      this.socket.onerror = null;
      this.socket.close();
      this.socket = null;
    }
  }

  // --- Event handlers ---

  private handleOpen(): void {
    this.reconnectAttempt = 0;
    this.updateStatus(ConnectionStatus.CONNECTED);
  }

  private handleMessage(messageEvent: MessageEvent): void {
    const serverEvent = this.parseEvent(messageEvent.data);
    if (serverEvent && this.eventHandler) {
      this.eventHandler(serverEvent);
    }
  }

  private handleClose(): void {
    if (this.intentionalClose) {
      return;
    }
    this.attemptReconnect();
  }

  private handleError(): void {
    this.closeSocket();
  }

  // --- Reconnection ---

  private attemptReconnect(): void {
    if (this.reconnectAttempt >= MAX_RECONNECT_ATTEMPTS) {
      this.updateStatus(ConnectionStatus.DISCONNECTED);
      return;
    }

    this.updateStatus(ConnectionStatus.RECONNECTING);
    const delayMs = RECONNECT_DELAYS_MS[this.reconnectAttempt];
    this.reconnectAttempt += 1;

    this.reconnectTimer = setTimeout(() => {
      this.createSocket();
    }, delayMs);
  }

  private cancelReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  // --- Helpers ---

  private sendMessage(payload: Record<string, unknown>): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(payload));
    }
  }

  private parseEvent(rawData: string): ServerEvent | null {
    try {
      return JSON.parse(rawData) as ServerEvent;
    } catch {
      return null;
    }
  }

  private updateStatus(status: ConnectionStatus): void {
    if (this.statusHandler) {
      this.statusHandler(status);
    }
  }
}
