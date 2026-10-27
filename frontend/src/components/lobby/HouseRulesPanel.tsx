import { useId, useState } from "react";
import {
  DEFAULT_HOUSE_RULES,
  MADE_SCORING_LABELS,
  MISSED_SCORING_LABELS,
  MadeScoring,
  MissedScoring,
  TRUMP_MODE_LABELS,
  TrumpMode,
  summarizeHouseRules,
} from "../../types";
import type { CustomDeal, HouseRules } from "../../types";
import { MAX_PRESET_NAME, deletePreset, loadPresets, savePreset } from "../../services/rulePresets";
import type { RulePreset } from "../../services/rulePresets";
import styles from "../../styles/lobby.module.css";

interface HouseRulesPanelProps {
  rules: HouseRules;
  onChange: (rules: HouseRules) => void;
  /** The custom deal in use, or null when a preset variant is selected. */
  customDeal: CustomDeal | null;
  /** Called when a saved preset that includes a custom deal is loaded. */
  onLoadCustomDeal?: (deal: CustomDeal) => void;
}

const TRUMP_MODES: TrumpMode[] = [TrumpMode.ROTATION, TrumpMode.FLIP];
const MADE_OPTIONS: MadeScoring[] = [MadeScoring.CLASSIC, MadeScoring.TEN_PLUS_BID];
const MISSED_OPTIONS: MissedScoring[] = [MissedScoring.NEGATIVE, MissedScoring.ZERO, MissedScoring.PER_TRICK_OFF];

export function HouseRulesPanel({ rules, onChange, customDeal, onLoadCustomDeal }: HouseRulesPanelProps) {
  const panelId = useId();
  const [open, setOpen] = useState(false);
  const changes = summarizeHouseRules(rules);
  const summary = changes.length === 0
    ? "Classic rules"
    : `${changes.length} ${changes.length === 1 ? "change" : "changes"}`;

  const update = <K extends keyof HouseRules>(key: K, value: HouseRules[K]) => {
    onChange({ ...rules, [key]: value });
  };

  return (
    <div className={styles.rulesPanel}>
      <button
        type="button"
        className={styles.rulesHeader}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen(!open)}
      >
        <span className={styles.rulesHeaderTitle}>{"📜"} House Rules</span>
        <span className={styles.rulesHeaderSummary}>{summary}</span>
        <span className={styles.rulesChevron} aria-hidden="true">{open ? "▴" : "▾"}</span>
      </button>

      {open && (
        <div id={panelId} className={styles.rulesCard}>
          <div className={styles.ruleBlock}>
            <span className={styles.ruleLabel}>Trump</span>
            <div className={styles.segmented} role="group" aria-label="Trump">
              {TRUMP_MODES.map((mode) => (
                <button
                  key={mode}
                  type="button"
                  className={`${styles.segment} ${rules.trump_mode === mode ? styles.segmentActive : ""}`}
                  aria-pressed={rules.trump_mode === mode}
                  onClick={() => update("trump_mode", mode)}
                >
                  {TRUMP_MODE_LABELS[mode]}
                </button>
              ))}
            </div>
            <span className={styles.ruleHint}>
              {rules.trump_mode === TrumpMode.FLIP
                ? "The first undealt card sets trump. If every card is dealt, suits rotate."
                : "Spades, diamonds, clubs, hearts, then repeat."}
            </span>
          </div>

          <ToggleRow
            label="Dealer restriction"
            hint="The dealer can't bid so the total equals the cards dealt."
            checked={rules.dealer_restriction}
            onChange={(checked) => update("dealer_restriction", checked)}
          />
          <ToggleRow
            label="Must trump when void"
            hint="If you can't follow suit, you must play a trump if you have one."
            checked={rules.must_trump_when_void}
            onChange={(checked) => update("must_trump_when_void", checked)}
          />

          <SelectRow
            label="Made bid"
            value={rules.made_scoring}
            options={MADE_OPTIONS}
            labels={MADE_SCORING_LABELS}
            onChange={(value) => update("made_scoring", value)}
          />
          <SelectRow
            label="Missed bid"
            value={rules.missed_scoring}
            options={MISSED_OPTIONS}
            labels={MISSED_SCORING_LABELS}
            onChange={(value) => update("missed_scoring", value)}
          />

          {changes.length > 0 && (
            <button type="button" className={styles.linkButton} onClick={() => onChange(DEFAULT_HOUSE_RULES)}>
              Reset to classic rules
            </button>
          )}

          <PresetControls
            rules={rules}
            customDeal={customDeal}
            onLoad={(preset) => {
              onChange(preset.houseRules);
              if (preset.customDeal && onLoadCustomDeal) onLoadCustomDeal(preset.customDeal);
            }}
          />
        </div>
      )}
    </div>
  );
}

interface ToggleRowProps {
  label: string;
  hint: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function ToggleRow({ label, hint, checked, onChange }: ToggleRowProps) {
  const id = useId();
  return (
    <div className={styles.ruleBlock}>
      <label className={styles.checkRow} htmlFor={id}>
        <input id={id} type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
        <span className={styles.ruleLabel}>{label}</span>
      </label>
      <span className={styles.ruleHint}>{hint}</span>
    </div>
  );
}

interface SelectRowProps<T extends string> {
  label: string;
  value: T;
  options: T[];
  labels: Record<T, string>;
  onChange: (value: T) => void;
}

function SelectRow<T extends string>({ label, value, options, labels, onChange }: SelectRowProps<T>) {
  const id = useId();
  return (
    <div className={styles.ruleRow}>
      <label className={styles.ruleLabel} htmlFor={id}>{label}</label>
      <select
        id={id}
        className={styles.ruleSelect}
        value={value}
        onChange={(event) => onChange(event.target.value as T)}
      >
        {options.map((option) => (
          <option key={option} value={option}>{labels[option]}</option>
        ))}
      </select>
    </div>
  );
}

interface PresetControlsProps {
  rules: HouseRules;
  customDeal: CustomDeal | null;
  onLoad: (preset: RulePreset) => void;
}

function PresetControls({ rules, customDeal, onLoad }: PresetControlsProps) {
  const selectId = useId();
  const nameId = useId();
  const [presets, setPresets] = useState<RulePreset[]>(loadPresets);
  const [selected, setSelected] = useState("");
  const [name, setName] = useState("");

  const handleSave = () => {
    const trimmed = name.trim();
    if (!trimmed) return;
    setPresets(savePreset({ name: trimmed, houseRules: rules, customDeal }));
    setSelected(trimmed.slice(0, MAX_PRESET_NAME));
    setName("");
  };

  const handleSelect = (presetName: string) => {
    setSelected(presetName);
    const preset = presets.find((candidate) => candidate.name === presetName);
    if (preset) onLoad(preset);
  };

  const handleDelete = () => {
    setPresets(deletePreset(selected));
    setSelected("");
  };

  return (
    <div className={styles.presetBox}>
      <span className={styles.ruleLabel}>Saved rules</span>
      {presets.length > 0 && (
        <div className={styles.presetRow}>
          <label className={styles.visuallyHidden} htmlFor={selectId}>Load saved rules</label>
          <select
            id={selectId}
            className={styles.ruleSelect}
            value={selected}
            onChange={(event) => handleSelect(event.target.value)}
          >
            <option value="">Load saved rules…</option>
            {presets.map((preset) => (
              <option key={preset.name} value={preset.name}>{preset.name}</option>
            ))}
          </select>
          {selected && (
            <button type="button" className={styles.linkButton} onClick={handleDelete}>
              Delete
            </button>
          )}
        </div>
      )}
      <div className={styles.presetRow}>
        <label className={styles.visuallyHidden} htmlFor={nameId}>Name for these rules</label>
        <input
          id={nameId}
          className={styles.presetInput}
          type="text"
          placeholder="Name these rules, e.g. Family night"
          value={name}
          maxLength={MAX_PRESET_NAME}
          onChange={(event) => setName(event.target.value)}
          onKeyDown={(event) => { if (event.key === "Enter") handleSave(); }}
        />
        <button type="button" className={styles.chip} onClick={handleSave} disabled={!name.trim()}>
          Save
        </button>
      </div>
      <span className={styles.ruleHint}>Saved on this device only.</span>
    </div>
  );
}
