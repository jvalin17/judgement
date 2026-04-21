export const CardBackDesign = {
  CLASSIC_BLUE: "classic_blue",
  COCKPIT_NAVY: "cockpit_navy",
  RUNWAY_GRAY: "runway_gray",
  FIRST_CLASS: "first_class",
  RED_EYE: "red_eye",
  ALTITUDE_WHITE: "altitude_white",
  SUNSET_HORIZON: "sunset_horizon",
  RADAR_GREEN: "radar_green",
  BLACKBOX: "blackbox",
} as const;
export type CardBackDesign = (typeof CardBackDesign)[keyof typeof CardBackDesign];

export const TableColor = {
  CLASSIC_GREEN: "classic_green",
  NAVY_BLUE: "navy_blue",
  BURGUNDY: "burgundy",
  DARK_WOOD: "dark_wood",
  SLATE_GRAY: "slate_gray",
  EMERALD: "emerald",
  MIDNIGHT_BLACK: "midnight_black",
  TEAL_OCEAN: "teal_ocean",
  ROYAL_PURPLE: "royal_purple",
  COFFEE_BROWN: "coffee_brown",
} as const;
export type TableColor = (typeof TableColor)[keyof typeof TableColor];

export const AnimationSpeed = {
  SLOW: "slow",
  MEDIUM: "medium",
  FAST: "fast",
} as const;
export type AnimationSpeed = (typeof AnimationSpeed)[keyof typeof AnimationSpeed];

export interface GameSettings {
  cardBack: CardBackDesign;
  tableColor: TableColor;
  animationSpeed: AnimationSpeed;
}

export const DEFAULT_SETTINGS: GameSettings = {
  cardBack: CardBackDesign.CLASSIC_BLUE,
  tableColor: TableColor.CLASSIC_GREEN,
  animationSpeed: AnimationSpeed.SLOW,
};

export const TABLE_COLOR_MAP: Record<TableColor, { base: string; dark: string; light: string }> = {
  [TableColor.CLASSIC_GREEN]: { base: "#1a6b3c", dark: "#145530", light: "#1f7f47" },
  [TableColor.NAVY_BLUE]: { base: "#1a3a5c", dark: "#0f2540", light: "#254d72" },
  [TableColor.BURGUNDY]: { base: "#5c1a2a", dark: "#401020", light: "#722535" },
  [TableColor.DARK_WOOD]: { base: "#3e2a1a", dark: "#2a1c10", light: "#4f3622" },
  [TableColor.SLATE_GRAY]: { base: "#3a3f47", dark: "#2a2e34", light: "#4a5058" },
  [TableColor.EMERALD]: { base: "#0f8a4a", dark: "#0a6638", light: "#15a85a" },
  [TableColor.MIDNIGHT_BLACK]: { base: "#15171c", dark: "#0a0c10", light: "#21242c" },
  [TableColor.TEAL_OCEAN]: { base: "#0e5a6a", dark: "#08404c", light: "#147384" },
  [TableColor.ROYAL_PURPLE]: { base: "#3d1a5c", dark: "#2a1040", light: "#4f2474" },
  [TableColor.COFFEE_BROWN]: { base: "#5a3a24", dark: "#3e2818", light: "#714a30" },
};

export const TABLE_COLOR_LABELS: Record<TableColor, string> = {
  [TableColor.CLASSIC_GREEN]: "Classic Green",
  [TableColor.NAVY_BLUE]: "Navy Blue",
  [TableColor.BURGUNDY]: "Burgundy",
  [TableColor.DARK_WOOD]: "Dark Wood",
  [TableColor.SLATE_GRAY]: "Slate Gray",
  [TableColor.EMERALD]: "Emerald",
  [TableColor.MIDNIGHT_BLACK]: "Midnight",
  [TableColor.TEAL_OCEAN]: "Teal Ocean",
  [TableColor.ROYAL_PURPLE]: "Royal Purple",
  [TableColor.COFFEE_BROWN]: "Coffee Brown",
};

export const CARD_BACK_LABELS: Record<CardBackDesign, string> = {
  [CardBackDesign.CLASSIC_BLUE]: "Classic Blue",
  [CardBackDesign.COCKPIT_NAVY]: "Cockpit Navy",
  [CardBackDesign.RUNWAY_GRAY]: "Runway",
  [CardBackDesign.FIRST_CLASS]: "First Class",
  [CardBackDesign.RED_EYE]: "Red Eye",
  [CardBackDesign.ALTITUDE_WHITE]: "Altitude",
  [CardBackDesign.SUNSET_HORIZON]: "Horizon",
  [CardBackDesign.RADAR_GREEN]: "Radar",
  [CardBackDesign.BLACKBOX]: "Black Box",
};

export const ANIMATION_SPEED_MAP: Record<AnimationSpeed, { fast: number; base: number; slow: number }> = {
  [AnimationSpeed.SLOW]: { fast: 400, base: 800, slow: 1200 },
  [AnimationSpeed.MEDIUM]: { fast: 250, base: 500, slow: 800 },
  [AnimationSpeed.FAST]: { fast: 100, base: 200, slow: 350 },
};

export const ANIMATION_SPEED_LABELS: Record<AnimationSpeed, string> = {
  [AnimationSpeed.SLOW]: "Slow",
  [AnimationSpeed.MEDIUM]: "Medium",
  [AnimationSpeed.FAST]: "Fast",
};
