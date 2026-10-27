import { useId } from "react";
import {
  MAX_CUSTOM_START,
  RoundShape,
  ROUND_SHAPE_LABELS,
  customDealSequence,
  resolveStartCards,
} from "../../types";
import type { CustomDeal } from "../../types";
import styles from "../../styles/lobby.module.css";

interface CustomDealEditorProps {
  deal: CustomDeal;
  onChange: (deal: CustomDeal) => void;
  /** Players currently set up, used for the preview. */
  playerCount: number;
}

const SHAPES: RoundShape[] = [RoundShape.DOWN, RoundShape.UP, RoundShape.DOWN_UP, RoundShape.UP_DOWN];

export function CustomDealEditor({ deal, onChange, playerCount }: CustomDealEditorProps) {
  const repeatId = useId();
  const isAuto = deal.start_cards === null;
  const startCeiling = isAuto ? MAX_CUSTOM_START : (deal.start_cards ?? MAX_CUSTOM_START);

  const setStart = (start: number | null) => {
    const clamped = start === null ? null : Math.max(1, Math.min(MAX_CUSTOM_START, start));
    const minCards = clamped === null ? deal.min_cards : Math.min(deal.min_cards, clamped);
    onChange({ ...deal, start_cards: clamped, min_cards: minCards });
  };

  const setMin = (minCards: number) => {
    onChange({ ...deal, min_cards: Math.max(1, Math.min(startCeiling, minCards)) });
  };

  const showRepeat = deal.shape === RoundShape.DOWN_UP || deal.shape === RoundShape.UP_DOWN;
  const sequence = customDealSequence(deal, playerCount);
  const effectiveStart = resolveStartCards(deal, playerCount);
  const wasReduced = !isAuto && deal.start_cards !== null && effectiveStart < deal.start_cards;

  return (
    <div className={styles.rulesCard}>
      <div className={styles.ruleRow}>
        <span className={styles.ruleLabel}>Starting cards</span>
        <div className={styles.ruleControls}>
          <button
            type="button"
            className={`${styles.chip} ${isAuto ? styles.chipActive : ""}`}
            aria-pressed={isAuto}
            onClick={() => setStart(isAuto ? effectiveStart : null)}
            title="As many cards as the deck allows for the number of players"
          >
            Max
          </button>
          <Stepper
            label="Starting cards"
            value={isAuto ? effectiveStart : (deal.start_cards ?? 1)}
            min={1}
            max={MAX_CUSTOM_START}
            disabled={isAuto}
            onChange={setStart}
          />
        </div>
      </div>

      <div className={styles.ruleRow}>
        <span className={styles.ruleLabel}>Fewest cards</span>
        <Stepper
          label="Fewest cards"
          value={deal.min_cards}
          min={1}
          max={startCeiling}
          onChange={setMin}
        />
      </div>

      <div className={styles.ruleBlock}>
        <span className={styles.ruleLabel}>Order</span>
        <div className={styles.segmented} role="group" aria-label="Round order">
          {SHAPES.map((shape) => (
            <button
              key={shape}
              type="button"
              className={`${styles.segment} ${deal.shape === shape ? styles.segmentActive : ""}`}
              aria-pressed={deal.shape === shape}
              onClick={() => onChange({ ...deal, shape })}
            >
              {ROUND_SHAPE_LABELS[shape]}
            </button>
          ))}
        </div>
      </div>

      {showRepeat && (
        <label className={styles.checkRow} htmlFor={repeatId}>
          <input
            id={repeatId}
            type="checkbox"
            checked={deal.repeat_turn}
            onChange={(event) => onChange({ ...deal, repeat_turn: event.target.checked })}
          />
          <span>Play the turnaround round twice</span>
        </label>
      )}

      <div className={styles.dealPreview} aria-live="polite">
        <span className={styles.dealPreviewLine}>
          With {playerCount} players: {sequence.join(" · ")}
        </span>
        <span className={styles.ruleHint}>
          {sequence.length} {sequence.length === 1 ? "round" : "rounds"}
          {wasReduced && `. Hands start at ${effectiveStart}, the most the deck allows.`}
        </span>
      </div>
    </div>
  );
}

interface StepperProps {
  label: string;
  value: number;
  min: number;
  max: number;
  disabled?: boolean;
  onChange: (value: number) => void;
}

function Stepper({ label, value, min, max, disabled = false, onChange }: StepperProps) {
  return (
    <div className={styles.stepper}>
      <button
        type="button"
        className={styles.stepperButton}
        onClick={() => onChange(value - 1)}
        disabled={disabled || value <= min}
        aria-label={`Fewer: ${label}`}
      >
        {"−"}
      </button>
      <span className={styles.stepperValue} aria-label={label} aria-live="polite">
        {value}
      </span>
      <button
        type="button"
        className={styles.stepperButton}
        onClick={() => onChange(value + 1)}
        disabled={disabled || value >= max}
        aria-label={`More: ${label}`}
      >
        +
      </button>
    </div>
  );
}
