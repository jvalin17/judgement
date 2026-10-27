import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { SettingsProvider } from "../../context/SettingsContext";
import { GameLobby } from "./GameLobby";
import { DEFAULT_HOUSE_RULES, VARIANT_LIST } from "../../types";

const createGame = vi.fn();
vi.mock("../../services/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../services/api")>();
  return { ...actual, createGame: (...args: unknown[]) => createGame(...args) };
});

function renderLobby() {
  return render(
    <SettingsProvider>
      <GameLobby onGameCreated={vi.fn()} />
    </SettingsProvider>,
  );
}

function selectCustomVariant() {
  const dots = screen.getAllByRole("button", { name: /^Variant \d+$/ });
  fireEvent.click(dots[VARIANT_LIST.indexOf("custom")]);
}

describe("GameLobby house rules", () => {
  beforeEach(() => {
    window.localStorage.clear();
    createGame.mockReset();
    createGame.mockResolvedValue({ game_id: "g1", player_ids: { Ana: "p1" } });
  });

  it("sends classic rules and no custom deal by default", async () => {
    renderLobby();
    fireEvent.change(screen.getByPlaceholderText("Enter your name"), { target: { value: "Ana" } });
    fireEvent.click(screen.getByRole("button", { name: /take off/i }));
    await waitFor(() => expect(createGame).toHaveBeenCalled());
    const request = createGame.mock.calls[0][0];
    expect(request.house_rules).toEqual(DEFAULT_HOUSE_RULES);
    expect(request.custom_deal).toBeNull();
  });

  it("shows the deal editor only for the custom variant", () => {
    renderLobby();
    expect(screen.queryByText("Starting cards")).not.toBeInTheDocument();
    selectCustomVariant();
    expect(screen.getByText("Starting cards")).toBeInTheDocument();
    expect(screen.getByText("7 down to 1")).toBeInTheDocument();
  });

  it("sends the custom deal and house rules", async () => {
    renderLobby();
    fireEvent.change(screen.getByPlaceholderText("Enter your name"), { target: { value: "Ana" } });
    selectCustomVariant();
    fireEvent.click(screen.getByRole("button", { name: "Down & up" }));
    fireEvent.click(screen.getByRole("button", { name: /house rules/i }));
    fireEvent.click(screen.getByLabelText("Must trump when void"));
    fireEvent.click(screen.getByRole("button", { name: /take off/i }));
    await waitFor(() => expect(createGame).toHaveBeenCalled());
    const request = createGame.mock.calls[0][0];
    expect(request.variant).toBe("custom");
    expect(request.custom_deal).toEqual({ start_cards: 7, min_cards: 1, shape: "down_up", repeat_turn: false });
    expect(request.house_rules.must_trump_when_void).toBe(true);
  });
});
