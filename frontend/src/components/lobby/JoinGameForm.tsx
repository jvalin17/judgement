import { useState, useCallback } from "react";
import { joinGame } from "../../services/api";
import { Button } from "../common";
import styles from "../../styles/lobby.module.css";

interface JoinGameFormProps {
  onJoined: (gameId: string, playerId: string) => void;
}

export function JoinGameForm({ onJoined }: JoinGameFormProps) {
  const [gameCode, setGameCode] = useState("");
  const [playerName, setPlayerName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [joining, setJoining] = useState(false);

  const handleSubmit = useCallback(async () => {
    if (!gameCode.trim()) {
      setError("Enter a game code");
      return;
    }
    if (!playerName.trim()) {
      setError("Enter your name");
      return;
    }

    setError(null);
    setJoining(true);

    try {
      const response = await joinGame(gameCode.trim(), playerName.trim());
      onJoined(response.game_id, response.player_id);
    } catch (joinError) {
      setError(joinError instanceof Error ? joinError.message : "Failed to join");
    } finally {
      setJoining(false);
    }
  }, [gameCode, playerName, onJoined]);

  return (
    <div className={styles.section}>
      <input
        className={styles.textInput}
        type="text"
        placeholder="Game code"
        value={gameCode}
        onChange={(event) => setGameCode(event.target.value)}
      />
      <input
        className={styles.textInput}
        type="text"
        placeholder="Your name"
        value={playerName}
        onChange={(event) => setPlayerName(event.target.value)}
        maxLength={20}
      />
      {error && <p className={styles.error}>{error}</p>}
      <Button variant="primary" fullWidth onClick={handleSubmit} disabled={joining}>
        {joining ? "Joining..." : "Join Game"}
      </Button>
    </div>
  );
}
