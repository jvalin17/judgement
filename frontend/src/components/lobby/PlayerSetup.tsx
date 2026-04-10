import { AIDifficulty, PlayerType } from "../../types";
import styles from "../../styles/lobby.module.css";

export interface PlayerConfig {
  name: string;
  playerType: PlayerType;
  aiDifficulty: AIDifficulty;
}

interface PlayerSetupProps {
  players: PlayerConfig[];
  maxPlayers: number;
  onChange: (players: PlayerConfig[]) => void;
}

export function PlayerSetup({ players, maxPlayers, onChange }: PlayerSetupProps) {
  function handleNameChange(index: number, name: string) {
    const updated = [...players];
    updated[index] = { ...updated[index], name };
    onChange(updated);
  }

  function handleTypeChange(index: number, playerType: PlayerType) {
    const updated = [...players];
    updated[index] = {
      ...updated[index],
      playerType,
      name: playerType === PlayerType.AI ? generateAiName(index, updated) : updated[index].name,
    };
    onChange(updated);
  }

  function handleDifficultyChange(index: number, aiDifficulty: AIDifficulty) {
    const updated = [...players];
    updated[index] = { ...updated[index], aiDifficulty };
    onChange(updated);
  }

  function handleAddPlayer() {
    if (players.length >= maxPlayers) return;
    const newPlayer = createDefaultAiPlayer(players.length);
    onChange([...players, newPlayer]);
  }

  function handleRemovePlayer(index: number) {
    if (players.length <= 2) return;
    onChange(players.filter((_, playerIndex) => playerIndex !== index));
  }

  return (
    <div className={styles.section}>
      <span className={styles.sectionLabel}>Players ({players.length}/{maxPlayers})</span>
      <div className={styles.playerList}>
        {players.map((player, index) => (
          <PlayerRow
            key={index}
            index={index}
            player={player}
            canRemove={players.length > 2}
            onNameChange={(name) => handleNameChange(index, name)}
            onTypeChange={(type) => handleTypeChange(index, type)}
            onDifficultyChange={(difficulty) => handleDifficultyChange(index, difficulty)}
            onRemove={() => handleRemovePlayer(index)}
          />
        ))}
      </div>
      {players.length < maxPlayers && (
        <button className={styles.addPlayerButton} onClick={handleAddPlayer}>
          + Add Player
        </button>
      )}
    </div>
  );
}

interface PlayerRowProps {
  index: number;
  player: PlayerConfig;
  canRemove: boolean;
  onNameChange: (name: string) => void;
  onTypeChange: (type: PlayerType) => void;
  onDifficultyChange: (difficulty: AIDifficulty) => void;
  onRemove: () => void;
}

function PlayerRow({
  index,
  player,
  canRemove,
  onNameChange,
  onTypeChange,
  onDifficultyChange,
  onRemove,
}: PlayerRowProps) {
  const isAi = player.playerType === PlayerType.AI;

  return (
    <div className={styles.playerRow}>
      <span className={styles.playerIndex}>{index + 1}</span>
      <input
        className={styles.playerName}
        type="text"
        value={player.name}
        onChange={(event) => onNameChange(event.target.value)}
        placeholder={`Player ${index + 1}`}
        readOnly={isAi}
      />
      <select
        className={styles.playerTypeSelect}
        value={player.playerType}
        onChange={(event) => onTypeChange(event.target.value as PlayerType)}
      >
        <option value={PlayerType.HUMAN}>Human</option>
        <option value={PlayerType.AI}>AI</option>
      </select>
      {isAi && (
        <select
          className={styles.difficultySelect}
          value={player.aiDifficulty}
          onChange={(event) => onDifficultyChange(event.target.value as AIDifficulty)}
        >
          <option value={AIDifficulty.EASY}>Easy</option>
          <option value={AIDifficulty.MEDIUM}>Medium</option>
          <option value={AIDifficulty.HARD}>Hard</option>
        </select>
      )}
      {canRemove && (
        <button className={styles.removeButton} onClick={onRemove} aria-label="Remove player">
          ✕
        </button>
      )}
    </div>
  );
}

// --- Helpers ---

const AI_DESSERT_NAMES = ["Tiramisu", "Cannoli", "Eclair", "Macaron", "Pavlova"];

function generateAiName(index: number, players: PlayerConfig[]): string {
  const usedNames = new Set(players.map((player) => player.name));
  const availableName = AI_DESSERT_NAMES.find((name) => !usedNames.has(name));
  return availableName ?? `Bot ${index + 1}`;
}

export function createDefaultAiPlayer(index: number): PlayerConfig {
  return {
    name: AI_DESSERT_NAMES[index] ?? `Bot ${index + 1}`,
    playerType: PlayerType.AI,
    aiDifficulty: AIDifficulty.MEDIUM,
  };
}

export function createDefaultHumanPlayer(): PlayerConfig {
  return {
    name: "",
    playerType: PlayerType.HUMAN,
    aiDifficulty: AIDifficulty.MEDIUM,
  };
}
