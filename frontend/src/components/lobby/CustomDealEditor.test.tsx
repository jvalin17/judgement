import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { useState } from "react";
import { CustomDealEditor } from "./CustomDealEditor";
import { DEFAULT_CUSTOM_DEAL, RoundShape } from "../../types";
import type { CustomDeal } from "../../types";

function Harness({ initial = DEFAULT_CUSTOM_DEAL, players = 4, onDeal }: {
  initial?: CustomDeal;
  players?: number;
  onDeal?: (deal: CustomDeal) => void;
}) {
  const [deal, setDeal] = useState(initial);
  return (
    <CustomDealEditor
      deal={deal}
      onChange={(next) => { setDeal(next); onDeal?.(next); }}
      playerCount={players}
    />
  );
}

describe("CustomDealEditor", () => {
  it("previews the rounds for the player count", () => {
    render(<Harness />);
    expect(screen.getByText("With 4 players: 7 · 6 · 5 · 4 · 3 · 2 · 1")).toBeInTheDocument();
    expect(screen.getByText(/7 rounds/)).toBeInTheDocument();
  });

  it("raises and lowers the starting cards", () => {
    const onDeal = vi.fn();
    render(<Harness onDeal={onDeal} />);
    fireEvent.click(screen.getByRole("button", { name: "More: Starting cards" }));
    expect(onDeal).toHaveBeenLastCalledWith(expect.objectContaining({ start_cards: 8 }));
    fireEvent.click(screen.getByRole("button", { name: "Fewer: Starting cards" }));
    expect(onDeal).toHaveBeenLastCalledWith(expect.objectContaining({ start_cards: 7 }));
  });

  it("lowers the fewest cards when the start drops below it", () => {
    const onDeal = vi.fn();
    render(<Harness initial={{ ...DEFAULT_CUSTOM_DEAL, start_cards: 3, min_cards: 3 }} onDeal={onDeal} />);
    fireEvent.click(screen.getByRole("button", { name: "Fewer: Starting cards" }));
    expect(onDeal).toHaveBeenLastCalledWith(expect.objectContaining({ start_cards: 2, min_cards: 2 }));
  });

  it("does not let fewest cards exceed the start", () => {
    render(<Harness initial={{ ...DEFAULT_CUSTOM_DEAL, start_cards: 3, min_cards: 3 }} />);
    expect(screen.getByRole("button", { name: "More: Fewest cards" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Fewer: Starting cards" })).not.toBeDisabled();
  });

  it("switches to the deck maximum", () => {
    const onDeal = vi.fn();
    render(<Harness players={5} onDeal={onDeal} />);
    fireEvent.click(screen.getByRole("button", { name: "Max" }));
    expect(onDeal).toHaveBeenLastCalledWith(expect.objectContaining({ start_cards: null }));
    expect(screen.getByRole("button", { name: "Max" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByLabelText("Starting cards")).toHaveTextContent("10");
    expect(screen.getByRole("button", { name: "More: Starting cards" })).toBeDisabled();
  });

  it("turning Max off keeps the current deck maximum as the start", () => {
    const onDeal = vi.fn();
    render(<Harness initial={{ ...DEFAULT_CUSTOM_DEAL, start_cards: null }} players={6} onDeal={onDeal} />);
    fireEvent.click(screen.getByRole("button", { name: "Max" }));
    expect(onDeal).toHaveBeenLastCalledWith(expect.objectContaining({ start_cards: 8 }));
  });

  it("only offers the repeated turnaround for two-way orders", () => {
    render(<Harness />);
    expect(screen.queryByLabelText(/turnaround round twice/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Down & up" }));
    expect(screen.getByRole("button", { name: "Down & up" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByLabelText(/turnaround round twice/i));
    expect(screen.getByText(/With 4 players: 7 .* 1 · 1 · 2/)).toBeInTheDocument();
  });

  it("explains when the deck forces smaller hands", () => {
    render(<Harness initial={{ ...DEFAULT_CUSTOM_DEAL, start_cards: 10, shape: RoundShape.DOWN }} players={6} />);
    expect(screen.getByText(/Hands start at 8, the most the deck allows/)).toBeInTheDocument();
  });
});
