import { describe, it, expect } from "vitest";
import {
  DEFAULT_CUSTOM_DEAL,
  DEFAULT_HOUSE_RULES,
  MadeScoring,
  MissedScoring,
  RoundShape,
  TrumpMode,
  customDealMaxPlayers,
  customDealSequence,
  describeCustomDeal,
  isDefaultHouseRules,
  resolveStartCards,
  summarizeHouseRules,
} from "./houseRules";
import type { CustomDeal } from "./houseRules";
import { DealingVariant, VARIANT_CONFIG, maxPlayersFor } from "./game";

const deal = (overrides: Partial<CustomDeal> = {}): CustomDeal => ({ ...DEFAULT_CUSTOM_DEAL, ...overrides });

// These cases mirror backend/tests/test_house_rules.py so both sides agree.
describe("customDealSequence", () => {
  it("runs down from the start to one", () => {
    expect(customDealSequence(deal({ start_cards: 7 }), 4)).toEqual([7, 6, 5, 4, 3, 2, 1]);
  });

  it("runs up from the minimum to the start", () => {
    expect(customDealSequence(deal({ start_cards: 5, min_cards: 2, shape: RoundShape.UP }), 4)).toEqual([2, 3, 4, 5]);
  });

  it("plays the turnaround once by default", () => {
    expect(customDealSequence(deal({ start_cards: 3, shape: RoundShape.DOWN_UP }), 4)).toEqual([3, 2, 1, 2, 3]);
  });

  it("plays the turnaround twice with repeat_turn", () => {
    expect(customDealSequence(deal({ start_cards: 3, shape: RoundShape.DOWN_UP, repeat_turn: true }), 4))
      .toEqual([3, 2, 1, 1, 2, 3]);
  });

  it("turns at the top for up and down", () => {
    expect(customDealSequence(deal({ start_cards: 4, min_cards: 2, shape: RoundShape.UP_DOWN }), 4)).toEqual([2, 3, 4, 3, 2]);
  });

  it("reduces the start to fit the deck", () => {
    expect(customDealSequence(deal({ start_cards: 10 }), 6)[0]).toBe(8);
  });

  it("collapses to one round when the minimum is above the reduced start", () => {
    expect(customDealSequence(deal({ start_cards: 10, min_cards: 9 }), 6)).toEqual([8]);
  });
});

describe("resolveStartCards", () => {
  it("uses the deck maximum when start is null", () => {
    expect(resolveStartCards(deal({ start_cards: null }), 4)).toBe(13);
    expect(resolveStartCards(deal({ start_cards: null }), 6)).toBe(8);
  });

  it("keeps an explicit start that fits", () => {
    expect(resolveStartCards(deal({ start_cards: 7 }), 6)).toBe(7);
  });
});

describe("customDealMaxPlayers", () => {
  it("depends on the minimum hand size", () => {
    expect(customDealMaxPlayers(deal({ min_cards: 1 }))).toBe(6);
    expect(customDealMaxPlayers(deal({ min_cards: 9 }))).toBe(5);
    expect(customDealMaxPlayers(deal({ min_cards: 26 }))).toBe(2);
  });
});

describe("maxPlayersFor", () => {
  it("uses the custom deal for the custom variant", () => {
    expect(maxPlayersFor(DealingVariant.CUSTOM, deal({ min_cards: 11 }))).toBe(4);
  });

  it("uses the preset table for other variants", () => {
    expect(maxPlayersFor(DealingVariant.TEN_TO_ONE, deal())).toBe(VARIANT_CONFIG[DealingVariant.TEN_TO_ONE].maxPlayers);
  });
});

describe("describeCustomDeal", () => {
  it("describes each shape", () => {
    expect(describeCustomDeal(deal({ start_cards: 7 }))).toBe("7 down to 1");
    expect(describeCustomDeal(deal({ start_cards: 7, min_cards: 3, shape: RoundShape.UP }))).toBe("3 up to 7");
    expect(describeCustomDeal(deal({ start_cards: 7, shape: RoundShape.DOWN_UP }))).toBe("7 down to 1, back to 7");
    expect(describeCustomDeal(deal({ start_cards: 5, min_cards: 2, shape: RoundShape.UP_DOWN }))).toBe("2 up to 5, back to 2");
  });

  it("says Max for an automatic start", () => {
    expect(describeCustomDeal(deal({ start_cards: null }))).toBe("Max down to 1");
  });
});

describe("house rules summary", () => {
  it("is empty for classic rules", () => {
    expect(summarizeHouseRules(DEFAULT_HOUSE_RULES)).toEqual([]);
    expect(isDefaultHouseRules(DEFAULT_HOUSE_RULES)).toBe(true);
  });

  it("lists every changed rule", () => {
    const rules = {
      trump_mode: TrumpMode.FLIP,
      dealer_restriction: false,
      must_trump_when_void: true,
      made_scoring: MadeScoring.TEN_PLUS_BID,
      missed_scoring: MissedScoring.ZERO,
    };
    const lines = summarizeHouseRules(rules);
    expect(lines).toHaveLength(5);
    expect(lines).toContain("Trump: flip a card");
    expect(lines).toContain("Made bid: 10 + bid");
    expect(lines).toContain("Missed bid: Zero points");
    expect(isDefaultHouseRules(rules)).toBe(false);
  });
});
