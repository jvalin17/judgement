import { VARIANT_LIST, VARIANT_LABELS } from "../../types";
import type { DealingVariant } from "../../types";
import styles from "../../styles/lobby.module.css";

interface VariantSelectorProps {
  selected: DealingVariant;
  onChange: (variant: DealingVariant) => void;
}

const VARIANTS = VARIANT_LIST;

export function VariantSelector({ selected, onChange }: VariantSelectorProps) {
  return (
    <div className={styles.section}>
      <span className={styles.sectionLabel}>Dealing Variant</span>
      <div className={styles.variantGroup}>
        {VARIANTS.map((variant) => (
          <VariantOption
            key={variant}
            variant={variant}
            isSelected={variant === selected}
            onSelect={onChange}
          />
        ))}
      </div>
    </div>
  );
}

interface VariantOptionProps {
  variant: DealingVariant;
  isSelected: boolean;
  onSelect: (variant: DealingVariant) => void;
}

function VariantOption({ variant, isSelected, onSelect }: VariantOptionProps) {
  const className = [styles.variantOption, isSelected ? styles.selected : ""]
    .filter(Boolean)
    .join(" ");

  return (
    <label className={className}>
      <input
        type="radio"
        name="variant"
        className={styles.variantRadio}
        checked={isSelected}
        onChange={() => onSelect(variant)}
      />
      <span className={styles.variantLabel}>{VARIANT_LABELS[variant]}</span>
    </label>
  );
}
