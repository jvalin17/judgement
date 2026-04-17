import { useState, useCallback } from "react";
import type { DealingVariant } from "../../types";
import { VARIANT_MAX_PLAYERS, VARIANT_LABELS, DealingVariant as DV, PlayerType } from "../../types";
import { createGame } from "../../services/api";
import type { PlayerSetup as PlayerSetupRequest } from "../../services/api";
import { Button, SettingsModal } from "../common";
import { PlayerSetup, createDefaultAiPlayer } from "./PlayerSetup";
import { JoinGameForm } from "./JoinGameForm";
import type { PlayerConfig } from "./PlayerSetup";
import styles from "../../styles/lobby.module.css";
import settingsStyles from "../../styles/settings.module.css";

const VARIANTS: DealingVariant[] = [
  DV.TEN_TO_ONE,
  DV.EIGHT_DOWN_UP,
  DV.TEN_DOWN_UP,
  DV.EIGHT_DOWN_UP_SHORT,
];

interface GameLobbyProps {
  onGameCreated: (gameId: string, playerId: string) => void;
}

export function GameLobby({ onGameCreated }: GameLobbyProps) {
  const [showSettings, setShowSettings] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [playerName, setPlayerName] = useState("");
  const [variant, setVariant] = useState<DealingVariant>("10_to_1");
  const [mustLoseMode, setMustLoseMode] = useState(false);
  const [opponents, setOpponents] = useState<PlayerConfig[]>(buildDefaultOpponents);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const maxPlayers = VARIANT_MAX_PLAYERS[variant];
  const maxOpponents = maxPlayers - 1;

  const handleVariantChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const newVariant = event.target.value as DealingVariant;
    setVariant(newVariant);
    const newMax = VARIANT_MAX_PLAYERS[newVariant] - 1;
    setOpponents((current) => current.slice(0, newMax));
  }, []);

  const handleOpponentsChange = useCallback((players: PlayerConfig[]) => {
    setOpponents(players.slice(0, maxOpponents));
  }, [maxOpponents]);

  const handleStartGame = useCallback(async () => {
    if (!playerName.trim()) {
      setError("Enter your name to start");
      return;
    }

    const allPlayers: PlayerConfig[] = [
      { name: playerName.trim(), playerType: PlayerType.HUMAN, aiDifficulty: "hard" as PlayerConfig["aiDifficulty"] },
      ...opponents,
    ];

    if (allPlayers.length < 2) {
      setError("Add at least one opponent");
      return;
    }

    const names = allPlayers.map((player) => player.name.trim().toLowerCase());
    if (new Set(names).size !== names.length) {
      setError("Player names must be unique");
      return;
    }

    setError(null);
    setIsCreating(true);

    try {
      const request = {
        variant,
        must_lose_mode: mustLoseMode,
        players: allPlayers.map((player): PlayerSetupRequest => ({
          name: player.name.trim(),
          is_ai: player.playerType === PlayerType.AI,
          ai_difficulty: player.playerType === PlayerType.AI ? player.aiDifficulty : null,
        })),
      };
      const response = await createGame(request);
      const playerId = response.player_ids[playerName.trim()];
      onGameCreated(response.game_id, playerId);
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Failed to create game");
    } finally {
      setIsCreating(false);
    }
  }, [playerName, opponents, variant, mustLoseMode, onGameCreated]);

  const switchClass = [styles.toggleSwitch, mustLoseMode ? styles.active : ""]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={styles.lobby}>
      <button
        className={settingsStyles.gearButton}
        onClick={() => setShowSettings(true)}
        aria-label="Settings"
      >
        &#9881;
      </button>
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}

      <h1 className={styles.title}>Judgement</h1>
      <p className={styles.subtitle}>Indian trick-taking card game</p>

      <div className={styles.section}>
        <span className={styles.sectionLabel}>Your Name</span>
        <input
          className={styles.textInput}
          type="text"
          placeholder="Enter your name"
          value={playerName}
          onChange={(event) => setPlayerName(event.target.value)}
          maxLength={20}
          autoFocus
        />
      </div>

      <div className={styles.section}>
        <span className={styles.sectionLabel}>Rounds</span>
        <select
          className={styles.variantSelect}
          value={variant}
          onChange={handleVariantChange}
        >
          {VARIANTS.map((variantOption) => (
            <option key={variantOption} value={variantOption}>
              {VARIANT_LABELS[variantOption]}
            </option>
          ))}
        </select>
      </div>

      <PlayerSetup players={opponents} maxPlayers={maxOpponents} onChange={handleOpponentsChange} />

      <button
        className={styles.advancedToggle}
        onClick={() => setShowAdvanced(!showAdvanced)}
      >
        {showAdvanced ? "\u25BE" : "\u25B8"} Advanced options
      </button>

      {showAdvanced && (
        <div className={styles.advancedSection}>
          <div className={styles.toggle}>
            <div>
              <span>Must-Lose Mode</span>
              <p className={styles.advancedHint}>All players are constrained (not just dealer)</p>
            </div>
            <div className={switchClass} onClick={() => setMustLoseMode(!mustLoseMode)} role="switch" aria-checked={mustLoseMode}>
              <div className={styles.toggleKnob} />
            </div>
          </div>
          <JoinGameForm onJoined={onGameCreated} />
        </div>
      )}

      {error && <p className={styles.error}>{error}</p>}

      <div className={styles.actions}>
        <Button variant="primary" size="large" fullWidth onClick={handleStartGame} disabled={isCreating}>
          {isCreating ? "Creating..." : "Start Game"}
        </Button>
      </div>
    </div>
  );
}

function buildDefaultOpponents(): PlayerConfig[] {
  return [createDefaultAiPlayer(1), createDefaultAiPlayer(2)];
}
