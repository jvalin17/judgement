import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { RoundInfo } from "./RoundInfo";
import { DEFAULT_HOUSE_RULES, MissedScoring } from "../../types";
import type { Card } from "../../types";

const baseProps = {
  roundNumber: 2,
  totalRounds: 7,
  numCards: 6,
  trumpSuit: "hearts",
  playerCount: 4,
  mustLoseMode: false,
  challengeMode: false,
};

describe("RoundInfo house rules", () => {
  it("shows the rank of a flipped trump card", () => {
    const trumpCard = { suit: "hearts", rank: 13 } as Card;
    render(<RoundInfo {...baseProps} trumpCard={trumpCard} />);
    expect(screen.getByLabelText("Trump card turned up: K♥")).toHaveTextContent("K");
  });

  it("shows no rank for rotation trump", () => {
    render(<RoundInfo {...baseProps} />);
    expect(screen.queryByLabelText(/Trump card turned up/)).not.toBeInTheDocument();
  });

  it("shows a house rules icon when rules differ", () => {
    render(<RoundInfo {...baseProps} houseRules={{ ...DEFAULT_HOUSE_RULES, missed_scoring: MissedScoring.ZERO }} />);
    expect(screen.getByTitle("House rules: Missed bid: Zero points")).toBeInTheDocument();
  });

  it("hides the house rules icon for classic rules", () => {
    render(<RoundInfo {...baseProps} houseRules={DEFAULT_HOUSE_RULES} />);
    expect(screen.queryByTitle(/House rules/)).not.toBeInTheDocument();
  });
});
