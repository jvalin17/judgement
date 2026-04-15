import { useState, useEffect } from "react";
import { Modal } from "./Modal";
import { useSettings } from "../../context/SettingsContext";
import {
  CardBackDesign,
  TableColor,
  AnimationSpeed,
  TABLE_COLOR_MAP,
  TABLE_COLOR_LABELS,
  CARD_BACK_LABELS,
  ANIMATION_SPEED_LABELS,
} from "../../types";
import { getVersion, checkForUpdate, applyUpdate } from "../../services/api";
import type { VersionInfo, UpdateCheckResponse } from "../../services/api";
import styles from "../../styles/settings.module.css";
import cardStyles from "../../styles/card.module.css";

interface SettingsModalProps {
  onClose: () => void;
}

const CARD_BACK_OPTIONS: CardBackDesign[] = [
  CardBackDesign.CLASSIC_BLUE,
  CardBackDesign.RED_DAMASK,
  CardBackDesign.GREEN_CELTIC,
  CardBackDesign.ROYAL_PURPLE,
  CardBackDesign.GOLD_ORNATE,
];

const TABLE_COLOR_OPTIONS: TableColor[] = [
  TableColor.CLASSIC_GREEN,
  TableColor.NAVY_BLUE,
  TableColor.BURGUNDY,
  TableColor.DARK_WOOD,
  TableColor.SLATE_GRAY,
];

const ANIMATION_SPEED_OPTIONS: AnimationSpeed[] = [
  AnimationSpeed.SLOW,
  AnimationSpeed.MEDIUM,
  AnimationSpeed.FAST,
];

export function SettingsModal({ onClose }: SettingsModalProps) {
  const { settings, updateCardBack, updateTableColor, updateAnimationSpeed } = useSettings();

  return (
    <Modal title="Settings" onClose={onClose}>
      <div className={styles.settingsContent}>
        <CardBackPicker selected={settings.cardBack} onSelect={updateCardBack} />
        <TableColorPicker selected={settings.tableColor} onSelect={updateTableColor} />
        <AnimationSpeedPicker selected={settings.animationSpeed} onSelect={updateAnimationSpeed} />
        <UpdateSection />
      </div>
    </Modal>
  );
}

// --- Card Back Picker ---

interface CardBackPickerProps {
  selected: CardBackDesign;
  onSelect: (design: CardBackDesign) => void;
}

function CardBackPicker({ selected, onSelect }: CardBackPickerProps) {
  return (
    <div className={styles.settingsSection}>
      <span className={styles.sectionTitle}>Card Back Design</span>
      <div className={styles.cardBackGrid}>
        {CARD_BACK_OPTIONS.map((design) => {
          const optionClass = [
            styles.cardBackOption,
            selected === design ? styles.selected : "",
          ].filter(Boolean).join(" ");

          return (
            <div key={design} className={optionClass} onClick={() => onSelect(design)}>
              <CardBackMiniPreview design={design} />
              <span className={styles.cardBackLabel}>{CARD_BACK_LABELS[design]}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CardBackMiniPreview({ design }: { design: CardBackDesign }) {
  const designClass = CARD_BACK_DESIGN_CLASS[design];
  const previewClass = [styles.cardBackPreview, cardStyles.cardBack, designClass]
    .filter(Boolean).join(" ");

  return (
    <div className={previewClass} style={{ width: 44, height: 64 }}>
      <div className={cardStyles.backPattern} />
    </div>
  );
}

// --- Table Color Picker ---

interface TableColorPickerProps {
  selected: TableColor;
  onSelect: (color: TableColor) => void;
}

function TableColorPicker({ selected, onSelect }: TableColorPickerProps) {
  return (
    <div className={styles.settingsSection}>
      <span className={styles.sectionTitle}>Table Color</span>
      <div className={styles.colorGrid}>
        {TABLE_COLOR_OPTIONS.map((color) => {
          const optionClass = [
            styles.colorOption,
            selected === color ? styles.selected : "",
          ].filter(Boolean).join(" ");

          const colorValues = TABLE_COLOR_MAP[color];

          return (
            <div key={color} className={optionClass} onClick={() => onSelect(color)}>
              <div
                className={styles.colorSwatch}
                style={{
                  background: `radial-gradient(circle at 35% 35%, ${colorValues.light}, ${colorValues.base}, ${colorValues.dark})`,
                }}
              />
              <span className={styles.colorLabel}>{TABLE_COLOR_LABELS[color]}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// --- Animation Speed Picker ---

interface AnimationSpeedPickerProps {
  selected: AnimationSpeed;
  onSelect: (speed: AnimationSpeed) => void;
}

function AnimationSpeedPicker({ selected, onSelect }: AnimationSpeedPickerProps) {
  return (
    <div className={styles.settingsSection}>
      <span className={styles.sectionTitle}>Animation Speed</span>
      <div className={styles.speedGroup}>
        {ANIMATION_SPEED_OPTIONS.map((speed) => {
          const optionClass = [
            styles.speedOption,
            selected === speed ? styles.selected : "",
          ].filter(Boolean).join(" ");

          return (
            <div key={speed} className={optionClass} onClick={() => onSelect(speed)}>
              {ANIMATION_SPEED_LABELS[speed]}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// --- Update Section ---

type UpdateStatus = "idle" | "checking" | "up-to-date" | "update-available" | "updating" | "error";

function UpdateSection() {
  const [status, setStatus] = useState<UpdateStatus>("idle");
  const [version, setVersion] = useState<VersionInfo | null>(null);
  const [updateInfo, setUpdateInfo] = useState<UpdateCheckResponse | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    getVersion().then(setVersion).catch(() => {});
  }, []);

  const handleCheck = async () => {
    setStatus("checking");
    setMessage("");
    try {
      const result = await checkForUpdate();
      setUpdateInfo(result);
      if (result.error) {
        setStatus("error");
        setMessage(result.error);
      } else if (result.update_available) {
        setStatus("update-available");
      } else {
        setStatus("up-to-date");
      }
    } catch {
      setStatus("error");
      setMessage("Could not reach server");
    }
  };

  const handleUpdate = async () => {
    setStatus("updating");
    setMessage("Updating... the app will restart shortly.");
    try {
      const result = await applyUpdate();
      if (!result.success) {
        setStatus("error");
        setMessage(result.message);
      }
    } catch {
      setStatus("error");
      setMessage("Update failed");
    }
  };

  const buttonLabel = {
    idle: "Check for Updates",
    checking: "Checking...",
    "up-to-date": "Up to Date",
    "update-available": "Update Now",
    updating: "Updating...",
    error: "Retry",
  }[status];

  const isDisabled = status === "checking" || status === "updating";

  const handleClick = () => {
    if (status === "update-available") {
      handleUpdate();
    } else {
      handleCheck();
    }
  };

  return (
    <div className={styles.settingsSection} style={{ borderTop: "1px solid var(--color-surface-light)", paddingTop: "var(--space-lg)" }}>
      <span className={styles.sectionTitle}>Updates</span>
      <button
        className={styles.updateButton}
        onClick={handleClick}
        disabled={isDisabled}
      >
        {buttonLabel}
      </button>
      {status === "up-to-date" && (
        <div className={styles.updateStatus} style={{ color: "var(--color-success)" }}>
          You're on the latest version
        </div>
      )}
      {status === "update-available" && updateInfo && (
        <div className={styles.updateStatus}>
          New version available: {updateInfo.latest_sha}
          {updateInfo.latest_message && <> — {updateInfo.latest_message}</>}
        </div>
      )}
      {status === "updating" && (
        <div className={styles.updateStatus} style={{ color: "var(--color-accent)" }}>
          {message}
        </div>
      )}
      {status === "error" && message && (
        <div className={styles.updateStatus} style={{ color: "var(--color-danger)" }}>
          {message}
        </div>
      )}
      {version && (
        <div className={styles.versionInfo}>
          Version: {version.git_sha}{version.build_date ? ` · Built ${version.build_date.split("T")[0]}` : ""}
        </div>
      )}
    </div>
  );
}

// --- Card back design to CSS class mapping ---

export const CARD_BACK_DESIGN_CLASS: Record<CardBackDesign, string> = {
  [CardBackDesign.CLASSIC_BLUE]: cardStyles.backClassicBlue ?? "",
  [CardBackDesign.RED_DAMASK]: cardStyles.backRedDamask ?? "",
  [CardBackDesign.GREEN_CELTIC]: cardStyles.backGreenCeltic ?? "",
  [CardBackDesign.ROYAL_PURPLE]: cardStyles.backRoyalPurple ?? "",
  [CardBackDesign.GOLD_ORNATE]: cardStyles.backGoldOrnate ?? "",
};
