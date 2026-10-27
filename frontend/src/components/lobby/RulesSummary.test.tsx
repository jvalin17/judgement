import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { RulesSummary } from "./RulesSummary";
import { DEFAULT_CUSTOM_DEAL, DEFAULT_HOUSE_RULES, TrumpMode } from "../../types";

describe("RulesSummary", () => {
  it("shows classic rules for a standard game", () => {
    render(<RulesSummary houseRules={DEFAULT_HOUSE_RULES} customDeal={null} playerCount={3} />);
    expect(screen.getByText("Classic rules")).toBeInTheDocument();
  });

  it("lists house rules", () => {
    render(
      <RulesSummary
        houseRules={{ ...DEFAULT_HOUSE_RULES, trump_mode: TrumpMode.FLIP, must_trump_when_void: true }}
        customDeal={null}
        playerCount={3}
      />,
    );
    expect(screen.getByText("Trump: flip a card")).toBeInTheDocument();
    expect(screen.getByText("Must trump when you can't follow suit")).toBeInTheDocument();
    expect(screen.queryByText("Classic rules")).not.toBeInTheDocument();
  });

  it("describes a custom deal for the current players", () => {
    render(<RulesSummary houseRules={DEFAULT_HOUSE_RULES} customDeal={DEFAULT_CUSTOM_DEAL} playerCount={4} />);
    expect(screen.getByText("Hands: 7 down to 1. 7 rounds with 4 players.")).toBeInTheDocument();
  });

  it("warns when more players shrink the hands", () => {
    render(
      <RulesSummary houseRules={DEFAULT_HOUSE_RULES} customDeal={{ ...DEFAULT_CUSTOM_DEAL, start_cards: 10 }} playerCount={6} />,
    );
    expect(screen.getByText("With 6 players, hands start at 8 instead of 10.")).toBeInTheDocument();
  });

  it("previews at least two players while the host waits alone", () => {
    render(<RulesSummary houseRules={DEFAULT_HOUSE_RULES} customDeal={{ ...DEFAULT_CUSTOM_DEAL, start_cards: null }} playerCount={1} />);
    expect(screen.getByText("Hands: Max down to 1. 26 rounds with 2 players.")).toBeInTheDocument();
  });
});
