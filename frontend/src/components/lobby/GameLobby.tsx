import { useState, useCallback } from "react";
import type { DealingVariant } from "../../types";
import { VARIANT_MAX_PLAYERS, PlayerType } from "../../types";
import { createGame } from "../../services/api";
import type { PlayerSetup as PlayerSetupRequest } from "../../services/api";
import { Button, SettingsModal } from "../common";
import { VariantSelector } from "./VariantSelector";
import { PlayerSetup, createDefaultHumanPlayer, createDefaultAiPlayer } from "./PlayerSetup";
import { JoinGameForm } from "./JoinGameForm";
import { QuickPlayForm } from "./QuickPlayForm";
import type { PlayerConfig } from "./PlayerSetup";
import styles from "../../styles/lobby.module.css";
import settingsStyles from "../../styles/settings.module.css";

type LobbyTab = "create" | "join" | "quick";

interface GameLobbyProps {
  onGameCreated: (gameId: string, playerId: string) => void;
}

export function GameLobby({ onGameCreated }: GameLobbyProps) {
  const [activeTab, setActiveTab] = useState<LobbyTab>("create");
  const [showSettings, setShowSettings] = useState(false);

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

      <div className={styles.tabBar}>
        <button
          className={`${styles.tab} ${activeTab === "create" ? styles.tabActive : ""}`}
          onClick={() => setActiveTab("create")}
        >
          Create
        </button>
        <button
          className={`${styles.tab} ${activeTab === "join" ? styles.tabActive : ""}`}
          onClick={() => setActiveTab("join")}
        >
          Join
        </button>
        <button
          className={`${styles.tab} ${activeTab === "quick" ? styles.tabActive : ""}`}
          onClick={() => setActiveTab("quick")}
        >
          Quick Play
        </button>
      </div>

      {activeTab === "create" && <CreateGameTab onGameCreated={onGameCreated} />}
      {activeTab === "join" && <JoinGameForm onJoined={onGameCreated} />}
      {activeTab === "quick" && <QuickPlayForm onJoined={onGameCreated} />}
    </div>
  );
}

// --- Create game tab (existing flow, slightly modified) ---

interface CreateGameTabProps {
  onGameCreated: (gameId: string, playerId: string) => void;
}

function CreateGameTab({ onGameCreated }: CreateGameTabProps) {
  const [variant, setVariant] = useState<DealingVariant>("10_to_1");
  const [mustLoseMode, setMustLoseMode] = useState(false);
  const [players, setPlayers] = useState<PlayerConfig[]>(buildDefaultPlayers);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const maxPlayers = VARIANT_MAX_PLAYERS[variant];

  const handleVariantChange = useCallback((newVariant: DealingVariant) => {
    setVariant(newVariant);
    const newMax = VARIANT_MAX_PLAYERS[newVariant];
    setPlayers((current) => current.slice(0, newMax));
  }, []);

  const handleCreateGame = useCallback(async () => {
    const validationError = validatePlayers(players);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);
    setIsCreating(true);

    try {
      const humanPlayer = findHumanPlayer(players);
      const request = buildCreateRequest(variant, mustLoseMode, players);
      const response = await createGame(request);
      const playerId = humanPlayer ? response.player_ids[humanPlayer.name] : "";
      onGameCreated(response.game_id, playerId);
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Failed to create game");
    } finally {
      setIsCreating(false);
    }
  }, [players, variant, mustLoseMode, onGameCreated]);

  return (
    <>
      <VariantSelector selected={variant} onChange={handleVariantChange} />
      <MustLoseToggle enabled={mustLoseMode} onToggle={setMustLoseMode} />
      <PlayerSetup players={players} maxPlayers={maxPlayers} onChange={setPlayers} />
      {error && <p className={styles.error}>{error}</p>}
      <div className={styles.actions}>
        <Button variant="primary" size="large" fullWidth onClick={handleCreateGame} disabled={isCreating}>
          {isCreating ? "Creating..." : "Start Game"}
        </Button>
      </div>
    </>
  );
}

// --- Must-lose toggle ---

interface MustLoseToggleProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
}

function MustLoseToggle({ enabled, onToggle }: MustLoseToggleProps) {
  const switchClass = [styles.toggleSwitch, enabled ? styles.active : ""]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={styles.section}>
      <div className={styles.toggle}>
        <span>Must-Lose Mode</span>
        <div className={switchClass} onClick={() => onToggle(!enabled)} role="switch" aria-checked={enabled}>
          <div className={styles.toggleKnob} />
        </div>
      </div>
    </div>
  );
}

// --- Helpers ---

function buildDefaultPlayers(): PlayerConfig[] {
  return [createDefaultHumanPlayer(), createDefaultAiPlayer(1), createDefaultAiPlayer(2)];
}

function validatePlayers(players: PlayerConfig[]): string | null {
  if (players.length < 2) return "At least 2 players required";

  const humanPlayers = players.filter((player) => player.playerType === PlayerType.HUMAN);
  for (const human of humanPlayers) {
    if (!human.name.trim()) return "All human players need a name";
  }

  const names = players.map((player) => player.name.trim().toLowerCase());
  const uniqueNames = new Set(names);
  if (uniqueNames.size !== names.length) return "Player names must be unique";

  return null;
}

function findHumanPlayer(players: PlayerConfig[]): PlayerConfig | undefined {
  return players.find((player) => player.playerType === PlayerType.HUMAN);
}

function buildCreateRequest(
  variant: DealingVariant,
  mustLoseMode: boolean,
  players: PlayerConfig[],
): { variant: DealingVariant; must_lose_mode: boolean; players: PlayerSetupRequest[] } {
  return {
    variant,
    must_lose_mode: mustLoseMode,
    players: players.map((player) => ({
      name: player.name.trim(),
      is_ai: player.playerType === PlayerType.AI,
      ai_difficulty: player.playerType === PlayerType.AI ? player.aiDifficulty : null,
    })),
  };
}
