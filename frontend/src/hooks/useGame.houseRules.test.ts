import { renderHook, act } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { useGame } from "./useGame";
import { DEFAULT_HOUSE_RULES, ServerEventType } from "../types";
import type { ServerEvent } from "../types";

function makeEvent(type: string, data: Record<string, unknown>): ServerEvent {
  return { type: type as ServerEvent["type"], data };
}

describe("useGame house rules", () => {
  it("defaults to classic rules", () => {
    const { result } = renderHook(() => useGame());
    expect(result.current.state.houseRules).toEqual(DEFAULT_HOUSE_RULES);
    expect(result.current.state.customDeal).toBeNull();
    expect(result.current.state.maxPlayers).toBeNull();
  });

  it("CONNECTED stores the game's rules and seat limit", () => {
    const { result } = renderHook(() => useGame());
    act(() => result.current.setGameInfo("g1", "p1"));
    const houseRules = { ...DEFAULT_HOUSE_RULES, trump_mode: "flip" };
    const customDeal = { start_cards: 7, min_cards: 1, shape: "down", repeat_turn: false };
    act(() =>
      result.current.handleServerEvent(
        makeEvent(ServerEventType.CONNECTED, {
          game_id: "g1", player_id: "p1", phase: "lobby", current_player_id: null, players: [],
          variant: "custom", house_rules: houseRules, custom_deal: customDeal, max_players: 4,
        }),
      ),
    );
    expect(result.current.state.variant).toBe("custom");
    expect(result.current.state.houseRules).toEqual(houseRules);
    expect(result.current.state.customDeal).toEqual(customDeal);
    expect(result.current.state.maxPlayers).toBe(4);
  });

  it("ROUND_STARTED records and clears the flipped trump card", () => {
    const { result } = renderHook(() => useGame());
    act(() => result.current.setGameInfo("g1", "p1"));
    const roundStarted = (trumpCard: unknown) =>
      makeEvent(ServerEventType.ROUND_STARTED, {
        round_number: 1, num_cards: 5, trump_suit: "clubs", dealer_id: "p1", trump_card: trumpCard,
      });
    act(() => result.current.handleServerEvent(roundStarted({ suit: "clubs", rank: 9 })));
    expect(result.current.state.trumpCard).toEqual({ suit: "clubs", rank: 9 });
    act(() => result.current.handleServerEvent(roundStarted(null)));
    expect(result.current.state.trumpCard).toBeNull();
  });
});
