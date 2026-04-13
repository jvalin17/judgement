import { useState, useCallback } from "react";
import type { DealingVariant } from "../../types";
import { quickJoin } from "../../services/api";
import { Button } from "../common";
import { VariantSelector } from "./VariantSelector";
import styles from "../../styles/lobby.module.css";

interface QuickPlayFormProps {
  onJoined: (gameId: string, playerId: string) => void;
}

export function QuickPlayForm({ onJoined }: QuickPlayFormProps) {
  const [playerName, setPlayerName] = useState("");
  const [variant, setVariant] = useState<DealingVariant>("10_to_1");
  const [error, setError] = useState<string | null>(null);
  const [finding, setFinding] = useState(false);

  const handleFind = useCallback(async () => {
    if (!playerName.trim()) {
      setError("Enter your name");
      return;
    }

    setError(null);
    setFinding(true);

    try {
      const response = await quickJoin(playerName.trim(), variant);
      onJoined(response.game_id, response.player_id);
    } catch (findError) {
      setError(findError instanceof Error ? findError.message : "Failed to find game");
    } finally {
      setFinding(false);
    }
  }, [playerName, variant, onJoined]);

  return (
    <div className={styles.section}>
      <input
        className={styles.textInput}
        type="text"
        placeholder="Your name"
        value={playerName}
        onChange={(event) => setPlayerName(event.target.value)}
        maxLength={20}
      />
      <VariantSelector selected={variant} onChange={setVariant} />
      {error && <p className={styles.error}>{error}</p>}
      <Button variant="primary" fullWidth onClick={handleFind} disabled={finding}>
        {finding ? "Finding..." : "Find Game"}
      </Button>
    </div>
  );
}
