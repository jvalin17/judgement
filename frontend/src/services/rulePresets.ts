// Saved house-rule presets ("Mom's rules"), stored per browser.
// Storage can be missing or blocked (private windows, previews), so every
// access is guarded and failures simply mean "no saved presets".
import type { HouseRules, CustomDeal } from "../types";
import { DEFAULT_HOUSE_RULES } from "../types";

export interface RulePreset {
  name: string;
  houseRules: HouseRules;
  /** Saved only when the preset was made with the custom deal selected. */
  customDeal: CustomDeal | null;
}

export const PRESET_STORAGE_KEY = "judgement.rulePresets";
export const MAX_PRESETS = 12;
export const MAX_PRESET_NAME = 24;

function isPreset(value: unknown): value is RulePreset {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.name === "string" &&
    !!candidate.houseRules &&
    typeof candidate.houseRules === "object"
  );
}

export function loadPresets(): RulePreset[] {
  try {
    const raw = window.localStorage.getItem(PRESET_STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isPreset).map((preset) => ({
      name: preset.name,
      // Fill in any rule added after the preset was saved.
      houseRules: { ...DEFAULT_HOUSE_RULES, ...preset.houseRules },
      customDeal: preset.customDeal ?? null,
    }));
  } catch {
    return [];
  }
}

function writePresets(presets: RulePreset[]): boolean {
  try {
    window.localStorage.setItem(PRESET_STORAGE_KEY, JSON.stringify(presets));
    return true;
  } catch {
    return false;
  }
}

/** Save or overwrite a preset by name (case-insensitive). Returns the new list. */
export function savePreset(preset: RulePreset): RulePreset[] {
  const name = preset.name.trim().slice(0, MAX_PRESET_NAME);
  if (!name) return loadPresets();
  const others = loadPresets().filter((existing) => existing.name.toLowerCase() !== name.toLowerCase());
  const next = [{ ...preset, name }, ...others].slice(0, MAX_PRESETS);
  writePresets(next);
  return next;
}

export function deletePreset(name: string): RulePreset[] {
  const next = loadPresets().filter((preset) => preset.name !== name);
  writePresets(next);
  return next;
}
