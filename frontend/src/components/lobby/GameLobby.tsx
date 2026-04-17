import { useState, useCallback } from "react";
import type { DealingVariant } from "../../types";
import { VARIANT_MAX_PLAYERS, DealingVariant as DV, PlayerType } from "../../types";
import { createGame } from "../../services/api";
import type { PlayerSetup as PlayerSetupRequest } from "../../services/api";
import { SettingsModal } from "../common";
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

const VARIANT_DESCRIPTIONS: Record<DealingVariant, { rounds: string; detail: string; maxPlayers: number }> = {
  [DV.TEN_TO_ONE]: { rounds: "10 rounds", detail: "10 down to 1", maxPlayers: 5 },
  [DV.EIGHT_DOWN_UP]: { rounds: "16 rounds", detail: "8 down to 1, back to 8", maxPlayers: 6 },
  [DV.TEN_DOWN_UP]: { rounds: "20 rounds", detail: "10 down to 1, back to 10", maxPlayers: 5 },
  [DV.EIGHT_DOWN_UP_SHORT]: { rounds: "8 rounds", detail: "8 down to 5, back to 8", maxPlayers: 6 },
};

interface GameLobbyProps {
  onGameCreated: (gameId: string, playerId: string) => void;
}

export function GameLobby({ onGameCreated }: GameLobbyProps) {
  const [showSettings, setShowSettings] = useState(false);
  const [showJoin, setShowJoin] = useState(false);

  const [playerName, setPlayerName] = useState("");
  const [variantIndex, setVariantIndex] = useState(0);
  const [mustLoseMode, setMustLoseMode] = useState(false);
  const [opponents, setOpponents] = useState<PlayerConfig[]>(buildDefaultOpponents);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const variant = VARIANTS[variantIndex];
  const variantInfo = VARIANT_DESCRIPTIONS[variant];
  const maxOpponents = VARIANT_MAX_PLAYERS[variant] - 1;

  const handlePrevVariant = useCallback(() => {
    setVariantIndex((current) => (current - 1 + VARIANTS.length) % VARIANTS.length);
  }, []);

  const handleNextVariant = useCallback(() => {
    setVariantIndex((current) => (current + 1) % VARIANTS.length);
  }, []);

  const handleVariantDot = useCallback((index: number) => {
    setVariantIndex(index);
  }, []);

  // Trim opponents when variant changes to a lower max
  const effectiveOpponents = opponents.slice(0, maxOpponents);

  const handleOpponentsChange = useCallback((players: PlayerConfig[]) => {
    setOpponents(players);
  }, []);

  const handleStartGame = useCallback(async () => {
    if (!playerName.trim()) {
      setError("Enter your name to take off!");
      return;
    }

    const allPlayers: PlayerConfig[] = [
      { name: playerName.trim(), playerType: PlayerType.HUMAN, aiDifficulty: "hard" as PlayerConfig["aiDifficulty"] },
      ...effectiveOpponents,
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
  }, [playerName, effectiveOpponents, variant, mustLoseMode, onGameCreated]);

  return (
    <div className={styles.skyPage}>
      {/* Animated clouds */}
      <div className={styles.cloudsLayer}>
        <div className={`${styles.cloud} ${styles.cloud1}`} />
        <div className={`${styles.cloud} ${styles.cloud2}`} />
        <div className={`${styles.cloud} ${styles.cloud3}`} />
        <div className={`${styles.cloud} ${styles.cloud4}`} />
        <div className={`${styles.cloud} ${styles.cloud5}`} />
      </div>

      {/* Floating suit symbols */}
      <div className={styles.floatingSuits}>
        <span className={`${styles.suitSymbol} ${styles.suit1}`}>{"\u2660"}</span>
        <span className={`${styles.suitSymbol} ${styles.suit2}`}>{"\u2665"}</span>
        <span className={`${styles.suitSymbol} ${styles.suit3}`}>{"\u2666"}</span>
        <span className={`${styles.suitSymbol} ${styles.suit4}`}>{"\u2663"}</span>
      </div>

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

        {/* Name input */}
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

        {/* Variant carousel */}
        <div className={styles.section}>
          <span className={styles.sectionLabel}>Game Mode</span>
          <div className={styles.carousel}>
            <button className={styles.carouselArrow} onClick={handlePrevVariant} aria-label="Previous variant">
              {"\u2039"}
            </button>
            <div className={styles.carouselCard}>
              <div className={styles.carouselRounds}>{variantInfo.rounds}</div>
              <div className={styles.carouselDetail}>{variantInfo.detail}</div>
              <div className={styles.carouselPlayers}>up to {variantInfo.maxPlayers} players</div>
            </div>
            <button className={styles.carouselArrow} onClick={handleNextVariant} aria-label="Next variant">
              {"\u203A"}
            </button>
          </div>
          <div className={styles.carouselDots}>
            {VARIANTS.map((_, index) => (
              <button
                key={index}
                className={`${styles.dot} ${index === variantIndex ? styles.dotActive : ""}`}
                onClick={() => handleVariantDot(index)}
                aria-label={`Variant ${index + 1}`}
              />
            ))}
          </div>
        </div>

        {/* Opponents */}
        <PlayerSetup players={effectiveOpponents} maxPlayers={maxOpponents} onChange={handleOpponentsChange} />

        {/* Turbulence toggle */}
        <button
          className={`${styles.turbulenceToggle} ${mustLoseMode ? styles.turbulenceActive : ""}`}
          onClick={() => setMustLoseMode(!mustLoseMode)}
        >
          <span className={styles.turbulenceIcon}>{mustLoseMode ? "\u26A0\uFE0F" : "\u2708\uFE0F"}</span>
          <span className={styles.turbulenceText}>
            {mustLoseMode ? "Turbulence!" : "Smooth Skies"}
          </span>
          <span className={styles.turbulenceHint}>
            {mustLoseMode ? "All players constrained" : "Only dealer constrained"}
          </span>
        </button>

        {error && <p className={styles.error}>{error}</p>}

        {/* Red airplane start button */}
        <button
          className={styles.takeoffButton}
          onClick={handleStartGame}
          disabled={isCreating}
        >
          <span className={styles.takeoffPlane}>{"\u2708"}</span>
          <span>{isCreating ? "Boarding..." : "Take Off!"}</span>
        </button>

        {/* Join game link */}
        <button
          className={styles.joinLink}
          onClick={() => setShowJoin(!showJoin)}
        >
          {showJoin ? "Back to create" : "Have a game code? Join here"}
        </button>

        {showJoin && (
          <div className={styles.joinSection}>
            <JoinGameForm onJoined={onGameCreated} />
          </div>
        )}
      </div>
    </div>
  );
}

function buildDefaultOpponents(): PlayerConfig[] {
  return [createDefaultAiPlayer(1), createDefaultAiPlayer(2)];
}
