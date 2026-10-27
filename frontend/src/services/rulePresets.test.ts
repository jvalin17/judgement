import { describe, it, expect, beforeEach, vi } from "vitest";
import { DEFAULT_HOUSE_RULES, MadeScoring, TrumpMode, DEFAULT_CUSTOM_DEAL } from "../types";
import { PRESET_STORAGE_KEY, MAX_PRESETS, deletePreset, loadPresets, savePreset } from "./rulePresets";

describe("rulePresets", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it("returns no presets when nothing is saved", () => {
    expect(loadPresets()).toEqual([]);
  });

  it("saves and loads a preset", () => {
    const rules = { ...DEFAULT_HOUSE_RULES, trump_mode: TrumpMode.FLIP };
    savePreset({ name: "Family night", houseRules: rules, customDeal: DEFAULT_CUSTOM_DEAL });
    expect(loadPresets()).toEqual([{ name: "Family night", houseRules: rules, customDeal: DEFAULT_CUSTOM_DEAL }]);
  });

  it("overwrites a preset with the same name ignoring case", () => {
    savePreset({ name: "Mom", houseRules: DEFAULT_HOUSE_RULES, customDeal: null });
    savePreset({ name: "mom", houseRules: { ...DEFAULT_HOUSE_RULES, made_scoring: MadeScoring.TEN_PLUS_BID }, customDeal: null });
    const presets = loadPresets();
    expect(presets).toHaveLength(1);
    expect(presets[0].houseRules.made_scoring).toBe(MadeScoring.TEN_PLUS_BID);
  });

  it("ignores blank names", () => {
    expect(savePreset({ name: "   ", houseRules: DEFAULT_HOUSE_RULES, customDeal: null })).toEqual([]);
  });

  it("keeps at most the newest presets", () => {
    for (let index = 0; index < MAX_PRESETS + 3; index++) {
      savePreset({ name: `P${index}`, houseRules: DEFAULT_HOUSE_RULES, customDeal: null });
    }
    const presets = loadPresets();
    expect(presets).toHaveLength(MAX_PRESETS);
    expect(presets[0].name).toBe(`P${MAX_PRESETS + 2}`);
  });

  it("deletes a preset", () => {
    savePreset({ name: "A", houseRules: DEFAULT_HOUSE_RULES, customDeal: null });
    savePreset({ name: "B", houseRules: DEFAULT_HOUSE_RULES, customDeal: null });
    expect(deletePreset("A").map((preset) => preset.name)).toEqual(["B"]);
  });

  it("survives corrupt storage", () => {
    window.localStorage.setItem(PRESET_STORAGE_KEY, "{not json");
    expect(loadPresets()).toEqual([]);
    window.localStorage.setItem(PRESET_STORAGE_KEY, JSON.stringify([{ nope: true }, "x"]));
    expect(loadPresets()).toEqual([]);
  });

  it("fills in rules missing from older presets", () => {
    window.localStorage.setItem(PRESET_STORAGE_KEY, JSON.stringify([{ name: "Old", houseRules: { trump_mode: "flip" } }]));
    const [preset] = loadPresets();
    expect(preset.houseRules).toEqual({ ...DEFAULT_HOUSE_RULES, trump_mode: "flip" });
    expect(preset.customDeal).toBeNull();
  });

  it("does not throw when storage is blocked", () => {
    vi.spyOn(window.localStorage, "getItem").mockImplementation(() => { throw new Error("blocked"); });
    vi.spyOn(window.localStorage, "setItem").mockImplementation(() => { throw new Error("blocked"); });
    expect(loadPresets()).toEqual([]);
    expect(() => savePreset({ name: "X", houseRules: DEFAULT_HOUSE_RULES, customDeal: null })).not.toThrow();
  });
});
