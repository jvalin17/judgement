import { createContext, useContext, useState, useCallback, useEffect } from "react";
import type { ReactNode } from "react";
import type { GameSettings, CardBackDesign, TableColor, AnimationSpeed } from "../types";
import {
  DEFAULT_SETTINGS,
  TABLE_COLOR_MAP,
  ANIMATION_SPEED_MAP,
} from "../types";

interface SettingsContextValue {
  settings: GameSettings;
  updateCardBack: (design: CardBackDesign) => void;
  updateTableColor: (color: TableColor) => void;
  updateAnimationSpeed: (speed: AnimationSpeed) => void;
  updateShareData: (enabled: boolean) => void;
}

const SettingsContext = createContext<SettingsContextValue | null>(null);

interface SettingsProviderProps {
  children: ReactNode;
}

const STORAGE_KEY = "judgement-settings";

function loadPersistedSettings(): GameSettings {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      return { ...DEFAULT_SETTINGS, ...parsed };
    }
  } catch {
    // Ignore corrupted storage
  }
  return DEFAULT_SETTINGS;
}

export function SettingsProvider({ children }: SettingsProviderProps) {
  const [settings, setSettings] = useState<GameSettings>(loadPersistedSettings);

  // Apply CSS variables whenever settings change
  useEffect(() => {
    const root = document.documentElement.style;
    const colors = TABLE_COLOR_MAP[settings.tableColor];
    root.setProperty("--color-table", colors.base);
    root.setProperty("--color-table-dark", colors.dark);
    root.setProperty("--color-table-light", colors.light);

    const speeds = ANIMATION_SPEED_MAP[settings.animationSpeed];
    root.setProperty("--transition-fast", `${speeds.fast}ms ease`);
    root.setProperty("--transition-base", `${speeds.base}ms ease`);
    root.setProperty("--transition-slow", `${speeds.slow}ms ease`);
  }, [settings.tableColor, settings.animationSpeed]);

  const updateCardBack = useCallback((design: CardBackDesign) => {
    setSettings((prev) => ({ ...prev, cardBack: design }));
  }, []);

  const updateTableColor = useCallback((color: TableColor) => {
    setSettings((prev) => ({ ...prev, tableColor: color }));
  }, []);

  const updateAnimationSpeed = useCallback((speed: AnimationSpeed) => {
    setSettings((prev) => ({ ...prev, animationSpeed: speed }));
  }, []);

  const updateShareData = useCallback((enabled: boolean) => {
    setSettings((prev) => ({ ...prev, shareData: enabled }));
  }, []);

  // Persist settings to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }, [settings]);

  return (
    <SettingsContext.Provider value={{ settings, updateCardBack, updateTableColor, updateAnimationSpeed, updateShareData }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings(): SettingsContextValue {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return context;
}
