import { useState, useCallback } from "react";
import {
  VARIANT_LIST,
  VARIANT_CONFIG,
  PlayerType,
  DealingVariant,
  DEFAULT_HOUSE_RULES,
  DEFAULT_CUSTOM_DEAL,
  customDealMaxPlayers,
  customDealSequence,
  describeCustomDeal,
  maxPlayersFor,
} from "../../types";
import type { CustomDeal, HouseRules } from "../../types";
import { useSettings } from "../../context/SettingsContext";
import { createGame, joinGame } from "../../services/api";
import type { PlayerSetup as PlayerSetupRequest } from "../../services/api";
import { SettingsModal } from "../common";
import { PlayerSetup, createDefaultAiPlayer } from "./PlayerSetup";
import { CustomDealEditor } from "./CustomDealEditor";
import { HouseRulesPanel } from "./HouseRulesPanel";
import type { PlayerConfig } from "./PlayerSetup";
import styles from "../../styles/lobby.module.css";

type LobbyView = "main" | "multiplayer";

const VARIANTS = VARIANT_LIST;
const CUSTOM_INDEX = VARIANTS.indexOf(DealingVariant.CUSTOM);

interface VariantCardInfo {
  rounds: string;
  detail: string;
  maxPlayers: number;
}

/** Carousel text for a variant; a custom deal describes its own hand sizes. */
function variantCardInfo(variant: DealingVariant, customDeal: CustomDeal, playerCount: number): VariantCardInfo {
  if (variant !== DealingVariant.CUSTOM) return VARIANT_CONFIG[variant];
  const rounds = customDealSequence(customDeal, playerCount).length;
  return {
    rounds: `Custom \u00B7 ${rounds} ${rounds === 1 ? "round" : "rounds"}`,
    detail: describeCustomDeal(customDeal),
    maxPlayers: customDealMaxPlayers(customDeal),
  };
}

interface GameLobbyProps {
  onGameCreated: (gameId: string, playerId: string) => void;
}

export function GameLobby({ onGameCreated }: GameLobbyProps) {
  const [view, setView] = useState<LobbyView>("main");
  const [showSettings, setShowSettings] = useState(false);

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

      {/* Settings — control tower */}
      <button
        className={styles.settingsButton}
        onClick={() => setShowSettings(true)}
        aria-label="Settings"
      >
        {"\uD83D\uDDFC"}
      </button>
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}

      {view === "main" ? (
        <MainLobby onGameCreated={onGameCreated} onMultiplayer={() => setView("multiplayer")} />
      ) : (
        <MultiplayerPage onGameCreated={onGameCreated} onBack={() => setView("main")} />
      )}
    </div>
  );
}

// ============================================================
// Main lobby — solo play with AI opponents
// ============================================================

interface MainLobbyProps {
  onGameCreated: (gameId: string, playerId: string) => void;
  onMultiplayer: () => void;
}

function MainLobby({ onGameCreated, onMultiplayer }: MainLobbyProps) {
  const { settings } = useSettings();
  const [playerName, setPlayerName] = useState("");
  const [variantIndex, setVariantIndex] = useState(0);
  const [mustLoseMode, setMustLoseMode] = useState(false);
  const [challengeMode, setChallengeMode] = useState(false);
  const [houseRules, setHouseRules] = useState<HouseRules>(DEFAULT_HOUSE_RULES);
  const [customDeal, setCustomDeal] = useState<CustomDeal>(DEFAULT_CUSTOM_DEAL);
  const [opponents, setOpponents] = useState<PlayerConfig[]>(buildDefaultOpponents);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const variant = VARIANTS[variantIndex];
  const isCustom = variant === DealingVariant.CUSTOM;
  const maxOpponents = maxPlayersFor(variant, customDeal) - 1;
  const effectiveOpponents = opponents.slice(0, maxOpponents);
  const variantInfo = variantCardInfo(variant, customDeal, effectiveOpponents.length + 1);

  const handleLoadCustomDeal = useCallback((deal: CustomDeal) => {
    setCustomDeal(deal);
    setVariantIndex(CUSTOM_INDEX);
  }, []);

  const handlePrevVariant = useCallback(() => {
    setVariantIndex((current) => (current - 1 + VARIANTS.length) % VARIANTS.length);
  }, []);

  const handleNextVariant = useCallback(() => {
    setVariantIndex((current) => (current + 1) % VARIANTS.length);
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
        challenge_mode: challengeMode,
        house_rules: houseRules,
        custom_deal: isCustom ? customDeal : null,
        share_data: settings.shareData,
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
  }, [playerName, effectiveOpponents, variant, isCustom, customDeal, houseRules, mustLoseMode, challengeMode, onGameCreated, settings.shareData]);

  return (
    <div className={styles.lobby}>
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
              onClick={() => setVariantIndex(index)}
              aria-label={`Variant ${index + 1}`}
            />
          ))}
        </div>
      </div>

      {isCustom && (
        <CustomDealEditor
          deal={customDeal}
          onChange={setCustomDeal}
          playerCount={effectiveOpponents.length + 1}
        />
      )}

      {/* Opponents */}
      <PlayerSetup players={effectiveOpponents} maxPlayers={maxOpponents} onChange={setOpponents} />

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
          {mustLoseMode ? "Harder \u2014 someone must lose every round" : "Normal rules"}
        </span>
      </button>

      {/* Challenge/Casual mode lever */}
      <div className={styles.modeLever}>
        <span
          className={`${styles.modeLeverLabel} ${challengeMode ? styles.modeLeverLabelActive : ""}`}
          onClick={() => setChallengeMode(true)}
        >
          🔥 Challenge
        </span>
        <button
          className={`${styles.modeLeverTrack} ${challengeMode ? styles.modeLeverTrackChallenge : ""}`}
          onClick={() => setChallengeMode(!challengeMode)}
          aria-label={challengeMode ? "Switch to casual" : "Switch to challenge"}
        >
          <span className={styles.modeLeverHandle} />
        </button>
        <span
          className={`${styles.modeLeverLabel} ${!challengeMode ? styles.modeLeverLabelActive : ""}`}
          onClick={() => setChallengeMode(false)}
        >
          🎯 Casual
        </span>
      </div>
      <span className={styles.turbulenceHint}>
        {challengeMode ? "AI plays at full strength" : "AI adapts to your level"}
      </span>

      <HouseRulesPanel
        rules={houseRules}
        onChange={setHouseRules}
        customDeal={isCustom ? customDeal : null}
        onLoadCustomDeal={handleLoadCustomDeal}
      />

      {error && <p className={styles.error}>{error}</p>}

      {/* Red airplane start button */}
      <button className={styles.takeoffButton} onClick={handleStartGame} disabled={isCreating}>
        <span className={styles.takeoffPlane}>{"\u2708"}</span>
        <span>{isCreating ? "Boarding..." : "Take Off!"}</span>
      </button>

      {/* Multiplayer link */}
      <button className={styles.joinLink} onClick={onMultiplayer}>
        Play with friends {"\u2192"}
      </button>
    </div>
  );
}

// ============================================================
// Multiplayer page — Create or Join a room
// ============================================================

interface MultiplayerPageProps {
  onGameCreated: (gameId: string, playerId: string) => void;
  onBack: () => void;
}

function MultiplayerPage({ onGameCreated, onBack }: MultiplayerPageProps) {
  const { settings } = useSettings();
  const [hostName, setHostName] = useState("");
  const [createVariantIndex, setCreateVariantIndex] = useState(0);
  const [createMustLose, setCreateMustLose] = useState(false);
  const [createRules, setCreateRules] = useState<HouseRules>(DEFAULT_HOUSE_RULES);
  const [createDeal, setCreateDeal] = useState<CustomDeal>(DEFAULT_CUSTOM_DEAL);
  const [createError, setCreateError] = useState<string | null>(null);
  const [isCreatingRoom, setIsCreatingRoom] = useState(false);

  const [joinCode, setJoinCode] = useState("");
  const [joinName, setJoinName] = useState("");
  const [joinError, setJoinError] = useState<string | null>(null);
  const [isJoining, setIsJoining] = useState(false);

  const createVariant = VARIANTS[createVariantIndex];
  const createIsCustom = createVariant === DealingVariant.CUSTOM;
  // Friends join later, so preview the deal at a full table.
  const createPreviewPlayers = customDealMaxPlayers(createDeal);
  const createVariantInfo = variantCardInfo(createVariant, createDeal, createPreviewPlayers);

  const handleLoadCreateDeal = useCallback((deal: CustomDeal) => {
    setCreateDeal(deal);
    setCreateVariantIndex(CUSTOM_INDEX);
  }, []);

  const handleCreateRoom = useCallback(async () => {
    if (!hostName.trim()) {
      setCreateError("Enter your name");
      return;
    }
    setCreateError(null);
    setIsCreatingRoom(true);
    try {
      const request = {
        variant: createVariant,
        must_lose_mode: createMustLose,
        house_rules: createRules,
        custom_deal: createIsCustom ? createDeal : null,
        share_data: settings.shareData,
        players: [{ name: hostName.trim(), is_ai: false, ai_difficulty: null }] as PlayerSetupRequest[],
        auto_start: false,
      };
      const response = await createGame(request);
      const playerId = response.player_ids[hostName.trim()];
      onGameCreated(response.game_id, playerId);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to create room");
    } finally {
      setIsCreatingRoom(false);
    }
  }, [hostName, createVariant, createIsCustom, createDeal, createRules, createMustLose, onGameCreated, settings.shareData]);

  const handleJoinRoom = useCallback(async () => {
    if (!joinCode.trim()) {
      setJoinError("Enter a room code");
      return;
    }
    if (!joinName.trim()) {
      setJoinError("Enter your name");
      return;
    }
    setJoinError(null);
    setIsJoining(true);
    try {
      const response = await joinGame(joinCode.trim(), joinName.trim(), settings.shareData);
      onGameCreated(response.game_id, response.player_id);
    } catch (err) {
      setJoinError(err instanceof Error ? err.message : "Failed to join room");
    } finally {
      setIsJoining(false);
    }
  }, [joinCode, joinName, onGameCreated]);

  return (
    <div className={styles.lobby}>
      <button className={styles.backButton} onClick={onBack}>
        {"\u2190"} Back
      </button>

      <h1 className={styles.title}>Play with Friends</h1>
      <p className={styles.subtitle}>Create a room or join with a code</p>

      {/* --- Create a Room --- */}
      <div className={styles.glassCard}>
        <h2 className={styles.cardHeading}>Create a Room</h2>

        <div className={styles.section}>
          <span className={styles.sectionLabel}>Your Name</span>
          <input
            className={styles.textInput}
            type="text"
            placeholder="Enter your name"
            value={hostName}
            onChange={(event) => setHostName(event.target.value)}
            maxLength={20}
            autoFocus
          />
        </div>

        <div className={styles.section}>
          <span className={styles.sectionLabel}>Game Mode</span>
          <div className={styles.carousel}>
            <button
              className={styles.carouselArrow}
              onClick={() => setCreateVariantIndex((i) => (i - 1 + VARIANTS.length) % VARIANTS.length)}
            >
              {"\u2039"}
            </button>
            <div className={styles.carouselCard}>
              <div className={styles.carouselRounds}>{createVariantInfo.rounds}</div>
              <div className={styles.carouselDetail}>{createVariantInfo.detail}</div>
              <div className={styles.carouselPlayers}>up to {createVariantInfo.maxPlayers} players</div>
            </div>
            <button
              className={styles.carouselArrow}
              onClick={() => setCreateVariantIndex((i) => (i + 1) % VARIANTS.length)}
            >
              {"\u203A"}
            </button>
          </div>
        </div>

        {createIsCustom && (
          <CustomDealEditor deal={createDeal} onChange={setCreateDeal} playerCount={createPreviewPlayers} />
        )}

        <button
          className={`${styles.turbulenceToggle} ${createMustLose ? styles.turbulenceActive : ""}`}
          onClick={() => setCreateMustLose(!createMustLose)}
        >
          <span className={styles.turbulenceIcon}>{createMustLose ? "\u26A0\uFE0F" : "\u2708\uFE0F"}</span>
          <span className={styles.turbulenceText}>
            {createMustLose ? "Turbulence!" : "Smooth Skies"}
          </span>
          <span className={styles.turbulenceHint}>
            {createMustLose ? "Harder \u2014 someone must lose every round" : "Normal rules"}
          </span>
        </button>

        <HouseRulesPanel
          rules={createRules}
          onChange={setCreateRules}
          customDeal={createIsCustom ? createDeal : null}
          onLoadCustomDeal={handleLoadCreateDeal}
        />

        {createError && <p className={styles.error}>{createError}</p>}

        <button className={styles.skyButton} onClick={handleCreateRoom} disabled={isCreatingRoom}>
          {isCreatingRoom ? "Creating..." : "Get Room Code"}
        </button>
      </div>

      {/* --- Divider --- */}
      <div className={styles.divider}>
        <span className={styles.dividerText}>or</span>
      </div>

      {/* --- Join a Room --- */}
      <div className={styles.glassCard}>
        <h2 className={styles.cardHeading}>Join a Room</h2>

        <div className={styles.section}>
          <span className={styles.sectionLabel}>Room Code</span>
          <input
            className={styles.textInput}
            type="text"
            placeholder="Enter room code"
            value={joinCode}
            onChange={(event) => setJoinCode(event.target.value)}
          />
        </div>

        <div className={styles.section}>
          <span className={styles.sectionLabel}>Your Name</span>
          <input
            className={styles.textInput}
            type="text"
            placeholder="Enter your name"
            value={joinName}
            onChange={(event) => setJoinName(event.target.value)}
            maxLength={20}
          />
        </div>

        {joinError && <p className={styles.error}>{joinError}</p>}

        <button className={styles.skyButton} onClick={handleJoinRoom} disabled={isJoining}>
          {isJoining ? "Joining..." : "Board Flight"}
        </button>
      </div>
    </div>
  );
}

// --- Helpers ---

function buildDefaultOpponents(): PlayerConfig[] {
  return [createDefaultAiPlayer(1), createDefaultAiPlayer(2)];
}
