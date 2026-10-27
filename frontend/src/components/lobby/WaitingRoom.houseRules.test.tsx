import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { WaitingRoom } from "./WaitingRoom";
import { ConnectionStatus } from "../../services/websocket";
import { DEFAULT_CUSTOM_DEAL, DEFAULT_HOUSE_RULES } from "../../types";

const baseProps = {
  gameId: "abcdef1234",
  playerId: "p1",
  isHost: false,
  players: [{ id: "p1", name: "Ana", isHost: true }, { id: "p2", name: "Raj", isHost: false }],
  autoStartSeconds: null,
  connectionStatus: ConnectionStatus.CONNECTED,
  onLeave: vi.fn(),
};

describe("WaitingRoom house rules", () => {
  it("shows classic rules when none are given", () => {
    render(<WaitingRoom {...baseProps} maxPlayers={5} />);
    expect(screen.getByText("Classic rules")).toBeInTheDocument();
  });

  it("shows the custom deal and house rules to every player", () => {
    render(
      <WaitingRoom
        {...baseProps}
        maxPlayers={6}
        houseRules={{ ...DEFAULT_HOUSE_RULES, dealer_restriction: false }}
        customDeal={DEFAULT_CUSTOM_DEAL}
      />,
    );
    expect(screen.getByText("Hands: 7 down to 1. 7 rounds with 2 players.")).toBeInTheDocument();
    expect(screen.getByText("Dealer can make bids add up")).toBeInTheDocument();
  });

  it("uses the game's seat limit for empty slots", () => {
    render(<WaitingRoom {...baseProps} maxPlayers={4} />);
    expect(screen.getAllByText("Waiting for player...")).toHaveLength(2);
  });

  it("never shows negative empty slots", () => {
    render(<WaitingRoom {...baseProps} maxPlayers={1} />);
    expect(screen.queryByText("Waiting for player...")).not.toBeInTheDocument();
  });
});
