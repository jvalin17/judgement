import {
  customDealSequence,
  describeCustomDeal,
  resolveStartCards,
  summarizeHouseRules,
} from "../../types";
import type { CustomDeal, HouseRules } from "../../types";
import styles from "../../styles/waiting.module.css";

interface RulesSummaryProps {
  houseRules: HouseRules;
  /** Present only for the custom dealing variant. */
  customDeal: CustomDeal | null;
  playerCount: number;
}

/** Read-only list of this game's rules, shown to everyone before it starts. */
export function RulesSummary({ houseRules, customDeal, playerCount }: RulesSummaryProps) {
  const ruleLines = summarizeHouseRules(houseRules);
  const players = Math.max(playerCount, 2);
  const sequence = customDeal ? customDealSequence(customDeal, players) : [];
  const effectiveStart = customDeal ? resolveStartCards(customDeal, players) : 0;
  const reduced = customDeal !== null && customDeal.start_cards !== null && effectiveStart < customDeal.start_cards;

  return (
    <div className={styles.rulesSummary} aria-label="Game rules">
      <span className={styles.rulesSummaryTitle}>{"📜"} Rules</span>
      <ul className={styles.rulesList}>
        {customDeal && (
          <li>
            Hands: {describeCustomDeal(customDeal)}. {sequence.length}{" "}
            {sequence.length === 1 ? "round" : "rounds"} with {players} players.
          </li>
        )}
        {reduced && (
          <li className={styles.rulesNotice}>
            With {players} players, hands start at {effectiveStart} instead of {customDeal?.start_cards}.
          </li>
        )}
        {ruleLines.length === 0 ? <li>Classic rules</li> : ruleLines.map((line) => <li key={line}>{line}</li>)}
      </ul>
    </div>
  );
}
