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

// --- Card back design to CSS class mapping ---

export const CARD_BACK_DESIGN_CLASS: Record<CardBackDesign, string> = {
  [CardBackDesign.CLASSIC_BLUE]: cardStyles.backClassicBlue ?? "",
  [CardBackDesign.RED_DAMASK]: cardStyles.backRedDamask ?? "",
  [CardBackDesign.GREEN_CELTIC]: cardStyles.backGreenCeltic ?? "",
  [CardBackDesign.ROYAL_PURPLE]: cardStyles.backRoyalPurple ?? "",
  [CardBackDesign.GOLD_ORNATE]: cardStyles.backGoldOrnate ?? "",
};
