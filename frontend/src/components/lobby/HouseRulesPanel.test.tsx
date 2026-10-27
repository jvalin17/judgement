import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { useState } from "react";
import { HouseRulesPanel } from "./HouseRulesPanel";
import { DEFAULT_CUSTOM_DEAL, DEFAULT_HOUSE_RULES, MissedScoring, TrumpMode } from "../../types";
import type { CustomDeal, HouseRules } from "../../types";
import { savePreset } from "../../services/rulePresets";

function Harness({ initial = DEFAULT_HOUSE_RULES, customDeal = null, onLoadCustomDeal, onRules }: {
  initial?: HouseRules;
  customDeal?: CustomDeal | null;
  onLoadCustomDeal?: (deal: CustomDeal) => void;
  onRules?: (rules: HouseRules) => void;
}) {
  const [rules, setRules] = useState(initial);
  return (
    <HouseRulesPanel
      rules={rules}
      onChange={(next) => { setRules(next); onRules?.(next); }}
      customDeal={customDeal}
      onLoadCustomDeal={onLoadCustomDeal}
    />
  );
}

const openPanel = () => fireEvent.click(screen.getByRole("button", { name: /house rules/i }));

describe("HouseRulesPanel", () => {
  beforeEach(() => window.localStorage.clear());

  it("starts collapsed and says classic rules", () => {
    render(<Harness />);
    const header = screen.getByRole("button", { name: /house rules/i });
    expect(header).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByText("Classic rules")).toBeInTheDocument();
    expect(screen.queryByText("Dealer restriction")).not.toBeInTheDocument();
  });

  it("shows the number of changed rules", () => {
    render(<Harness initial={{ ...DEFAULT_HOUSE_RULES, trump_mode: TrumpMode.FLIP, dealer_restriction: false }} />);
    expect(screen.getByText("2 changes")).toBeInTheDocument();
  });

  it("expands to show every rule", () => {
    render(<Harness />);
    openPanel();
    expect(screen.getByRole("button", { name: /house rules/i })).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByLabelText("Dealer restriction")).toBeChecked();
    expect(screen.getByLabelText("Must trump when void")).not.toBeChecked();
    expect(screen.getByLabelText("Made bid")).toBeInTheDocument();
    expect(screen.getByLabelText("Missed bid")).toBeInTheDocument();
  });

  it("switches trump to flip a card", () => {
    const onRules = vi.fn();
    render(<Harness onRules={onRules} />);
    openPanel();
    fireEvent.click(screen.getByRole("button", { name: "Flip a card" }));
    expect(onRules).toHaveBeenLastCalledWith(expect.objectContaining({ trump_mode: TrumpMode.FLIP }));
    expect(screen.getByRole("button", { name: "Flip a card" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText(/first undealt card sets trump/i)).toBeInTheDocument();
  });

  it("toggles the dealer restriction and must-trump rules", () => {
    const onRules = vi.fn();
    render(<Harness onRules={onRules} />);
    openPanel();
    fireEvent.click(screen.getByLabelText("Dealer restriction"));
    expect(onRules).toHaveBeenLastCalledWith(expect.objectContaining({ dealer_restriction: false }));
    fireEvent.click(screen.getByLabelText("Must trump when void"));
    expect(onRules).toHaveBeenLastCalledWith(expect.objectContaining({ must_trump_when_void: true }));
  });

  it("changes missed-bid scoring", () => {
    const onRules = vi.fn();
    render(<Harness onRules={onRules} />);
    openPanel();
    fireEvent.change(screen.getByLabelText("Missed bid"), { target: { value: MissedScoring.PER_TRICK_OFF } });
    expect(onRules).toHaveBeenLastCalledWith(expect.objectContaining({ missed_scoring: MissedScoring.PER_TRICK_OFF }));
  });

  it("resets to classic rules", () => {
    const onRules = vi.fn();
    render(<Harness initial={{ ...DEFAULT_HOUSE_RULES, must_trump_when_void: true }} onRules={onRules} />);
    openPanel();
    fireEvent.click(screen.getByRole("button", { name: /reset to classic/i }));
    expect(onRules).toHaveBeenLastCalledWith(DEFAULT_HOUSE_RULES);
    expect(screen.queryByRole("button", { name: /reset to classic/i })).not.toBeInTheDocument();
  });

  it("saves the current rules as a preset", () => {
    render(<Harness initial={{ ...DEFAULT_HOUSE_RULES, trump_mode: TrumpMode.FLIP }} />);
    openPanel();
    const saveButton = screen.getByRole("button", { name: "Save" });
    expect(saveButton).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Name for these rules"), { target: { value: "Family night" } });
    fireEvent.click(saveButton);
    expect(screen.getByRole("option", { name: "Family night" })).toBeInTheDocument();
    const stored = JSON.parse(window.localStorage.getItem("judgement.rulePresets") ?? "[]");
    expect(stored[0].houseRules.trump_mode).toBe("flip");
  });

  it("loads a preset and its custom deal", () => {
    const deal = { ...DEFAULT_CUSTOM_DEAL, start_cards: 5 };
    savePreset({ name: "Short", houseRules: { ...DEFAULT_HOUSE_RULES, dealer_restriction: false }, customDeal: deal });
    const onRules = vi.fn();
    const onLoadCustomDeal = vi.fn();
    render(<Harness onRules={onRules} onLoadCustomDeal={onLoadCustomDeal} />);
    openPanel();
    fireEvent.change(screen.getByLabelText("Load saved rules"), { target: { value: "Short" } });
    expect(onRules).toHaveBeenLastCalledWith(expect.objectContaining({ dealer_restriction: false }));
    expect(onLoadCustomDeal).toHaveBeenCalledWith(deal);
  });

  it("deletes a selected preset", () => {
    savePreset({ name: "Gone", houseRules: DEFAULT_HOUSE_RULES, customDeal: null });
    render(<Harness />);
    openPanel();
    fireEvent.change(screen.getByLabelText("Load saved rules"), { target: { value: "Gone" } });
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    expect(screen.queryByLabelText("Load saved rules")).not.toBeInTheDocument();
  });
});
