import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import type { GameState, Card } from "../types";
import { INITIAL_GAME_STATE, GamePhase } from "../types";
import { SettingsProvider } from "../context/SettingsContext";
import { createContext, useContext } from "react";

// --- Mock GameContext ---

interface MockGameActions {
  setGameInfo: ReturnType<typeof vi.fn>;
  resetGame: ReturnType<typeof vi.fn>;
  clearError: ReturnType<typeof vi.fn>;
  connect: ReturnType<typeof vi.fn>;
  disconnect: ReturnType<typeof vi.fn>;
  sendBid: ReturnType<typeof vi.fn>;
  sendPlayCard: ReturnType<typeof vi.fn>;
  sendGetHand: ReturnType<typeof vi.fn>;
  acknowledgeRoundOver: ReturnType<typeof vi.fn>;
  startTrickCollect: ReturnType<typeof vi.fn>;
  clearTrick: ReturnType<typeof vi.fn>;
}

interface MockGameContextValue {
  state: GameState;
  connectionStatus: string;
  actions: MockGameActions;
}

const MockGameContext = createContext<MockGameContextValue | null>(null);

export function createMockActions(): MockGameActions {
  return {
    setGameInfo: vi.fn(),
    resetGame: vi.fn(),
    clearError: vi.fn(),
    connect: vi.fn(),
    disconnect: vi.fn(),
    sendBid: vi.fn(),
    sendPlayCard: vi.fn(),
    sendGetHand: vi.fn(),
    acknowledgeRoundOver: vi.fn(),
    startTrickCollect: vi.fn(),
    clearTrick: vi.fn(),
  };
}

export function useMockGameContext() {
  const context = useContext(MockGameContext);
  if (!context) throw new Error("Missing MockGameContext");
  return context;
}

interface RenderOptions {
  state?: Partial<GameState>;
  actions?: Partial<MockGameActions>;
}

export function renderWithProviders(ui: ReactElement, options: RenderOptions = {}) {
  const state = { ...INITIAL_GAME_STATE, ...options.state };
  const actions = { ...createMockActions(), ...options.actions };
  const contextValue: MockGameContextValue = {
    state,
    connectionStatus: "connected",
    actions,
  };

  // Patch the real useGameContext module to return our mock
  return {
    ...render(
      <SettingsProvider>
        <MockGameContext.Provider value={contextValue}>
          {ui}
        </MockGameContext.Provider>
      </SettingsProvider>
    ),
    actions,
    state,
  };
}

// --- Test data factories ---

export function makePlayer(overrides: Partial<{ id: string; name: string; player_type: string; ai_difficulty: string | null }> = {}) {
  return {
    id: overrides.id ?? "p1",
    name: overrides.name ?? "Alice",
    player_type: (overrides.player_type ?? "human") as "human" | "ai",
    ai_difficulty: (overrides.ai_difficulty ?? null) as "easy" | "medium" | "hard" | null,
  };
}

export function makeCard(suit: string, rank: string): Card {
  return { suit, rank } as Card;
}

export { GamePhase, INITIAL_GAME_STATE };
