// House rules and custom hand sizes. Mirrors backend/app/models/house_rules.py.
// Every default reproduces the classic game.

export const DECK_SIZE = 52;
export const MAX_CUSTOM_PLAYERS = 6;
export const MAX_CUSTOM_START = DECK_SIZE / 2;

export const TrumpMode = {
  ROTATION: "rotation",
  FLIP: "flip",
} as const;
export type TrumpMode = (typeof TrumpMode)[keyof typeof TrumpMode];

export const MadeScoring = {
  CLASSIC: "classic",
  TEN_PLUS_BID: "ten_plus_bid",
} as const;
export type MadeScoring = (typeof MadeScoring)[keyof typeof MadeScoring];

export const MissedScoring = {
  NEGATIVE: "negative",
  ZERO: "zero",
  PER_TRICK_OFF: "per_trick_off",
} as const;
export type MissedScoring = (typeof MissedScoring)[keyof typeof MissedScoring];

export const RoundShape = {
  DOWN: "down",
  UP: "up",
  DOWN_UP: "down_up",
  UP_DOWN: "up_down",
} as const;
export type RoundShape = (typeof RoundShape)[keyof typeof RoundShape];

export interface HouseRules {
  trump_mode: TrumpMode;
  dealer_restriction: boolean;
  must_trump_when_void: boolean;
  made_scoring: MadeScoring;
  missed_scoring: MissedScoring;
}

export interface CustomDeal {
  /** null means "as many as the deck allows for the number of players". */
  start_cards: number | null;
  min_cards: number;
  shape: RoundShape;
  repeat_turn: boolean;
}

export const DEFAULT_HOUSE_RULES: HouseRules = {
  trump_mode: TrumpMode.ROTATION,
  dealer_restriction: true,
  must_trump_when_void: false,
  made_scoring: MadeScoring.CLASSIC,
  missed_scoring: MissedScoring.NEGATIVE,
};

export const DEFAULT_CUSTOM_DEAL: CustomDeal = {
  start_cards: 7,
  min_cards: 1,
  shape: RoundShape.DOWN,
  repeat_turn: false,
};

export const TRUMP_MODE_LABELS: Record<TrumpMode, string> = {
  [TrumpMode.ROTATION]: "Rotate suits",
  [TrumpMode.FLIP]: "Flip a card",
};

export const MADE_SCORING_LABELS: Record<MadeScoring, string> = {
  [MadeScoring.CLASSIC]: "Classic (10, 11, bid × 10)",
  [MadeScoring.TEN_PLUS_BID]: "10 + bid",
};

export const MISSED_SCORING_LABELS: Record<MissedScoring, string> = {
  [MissedScoring.NEGATIVE]: "Lose what you'd have won",
  [MissedScoring.ZERO]: "Zero points",
  [MissedScoring.PER_TRICK_OFF]: "−10 per trick off",
};

export const ROUND_SHAPE_LABELS: Record<RoundShape, string> = {
  [RoundShape.DOWN]: "Down",
  [RoundShape.UP]: "Up",
  [RoundShape.DOWN_UP]: "Down & up",
  [RoundShape.UP_DOWN]: "Up & down",
};

export function isDefaultHouseRules(rules: HouseRules): boolean {
  return (Object.keys(DEFAULT_HOUSE_RULES) as Array<keyof HouseRules>).every(
    (key) => rules[key] === DEFAULT_HOUSE_RULES[key],
  );
}

/** Most players a custom deal can seat; every hand needs at least min_cards. */
export function customDealMaxPlayers(deal: CustomDeal): number {
  return Math.max(2, Math.min(MAX_CUSTOM_PLAYERS, Math.floor(DECK_SIZE / deal.min_cards)));
}

/** Starting hand size for this many players, reduced to fit the deck. */
export function resolveStartCards(deal: CustomDeal, numPlayers: number): number {
  const deckMax = Math.floor(DECK_SIZE / Math.max(numPlayers, 1));
  return deal.start_cards === null ? deckMax : Math.min(deal.start_cards, deckMax);
}

/** Hand size for every round, for this many players. */
export function customDealSequence(deal: CustomDeal, numPlayers: number): number[] {
  const high = resolveStartCards(deal, numPlayers);
  const low = Math.min(deal.min_cards, high);
  const descending: number[] = [];
  for (let cards = high; cards >= low; cards--) descending.push(cards);
  const ascending = [...descending].reverse();
  switch (deal.shape) {
    case RoundShape.DOWN:
      return descending;
    case RoundShape.UP:
      return ascending;
    case RoundShape.DOWN_UP:
      return [...descending, ...(deal.repeat_turn ? ascending : ascending.slice(1))];
    case RoundShape.UP_DOWN:
      return [...ascending, ...(deal.repeat_turn ? descending : descending.slice(1))];
  }
}

/** Short description of a deal's shape, e.g. "7 down to 1, back to 7". */
export function describeCustomDeal(deal: CustomDeal): string {
  const start = deal.start_cards === null ? "Max" : String(deal.start_cards);
  const low = deal.start_cards === null ? deal.min_cards : Math.min(deal.min_cards, deal.start_cards);
  switch (deal.shape) {
    case RoundShape.DOWN:
      return `${start} down to ${low}`;
    case RoundShape.UP:
      return `${low} up to ${start}`;
    case RoundShape.DOWN_UP:
      return `${start} down to ${low}, back to ${start}`;
    case RoundShape.UP_DOWN:
      return `${low} up to ${start}, back to ${low}`;
  }
}

/** Human-readable list of every rule that differs from the classic game. */
export function summarizeHouseRules(rules: HouseRules): string[] {
  const lines: string[] = [];
  if (rules.trump_mode === TrumpMode.FLIP) lines.push("Trump: flip a card");
  if (!rules.dealer_restriction) lines.push("Dealer can make bids add up");
  if (rules.must_trump_when_void) lines.push("Must trump when you can't follow suit");
  if (rules.made_scoring !== MadeScoring.CLASSIC) {
    lines.push(`Made bid: ${MADE_SCORING_LABELS[rules.made_scoring]}`);
  }
  if (rules.missed_scoring !== MissedScoring.NEGATIVE) {
    lines.push(`Missed bid: ${MISSED_SCORING_LABELS[rules.missed_scoring]}`);
  }
  return lines;
}
