import { useState, useCallback } from "react";
import { startGame as apiStartGame } from "../../services/api";
import { Button } from "../common";
import styles from "../../styles/waiting.module.css";

interface LobbyPlayer {
  id: string;
  name: string;
  isHost: boolean;
}

interface WaitingRoomProps {
  gameId: string;
  playerId: string;
  isHost: boolean;
  players: LobbyPlayer[];
  autoStartSeconds: number | null;
  maxPlayers: number;
  onLeave: () => void;
}

export function WaitingRoom({
  gameId,
  playerId,
  isHost,
  players,
  autoStartSeconds,
  maxPlayers,
  onLeave,
}: WaitingRoomProps) {
  const [copied, setCopied] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCopyCode = useCallback(() => {
    navigator.clipboard.writeText(gameId).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [gameId]);

  const handleStart = useCallback(async () => {
    setStarting(true);
    setError(null);
    try {
      await apiStartGame(gameId, playerId);
    } catch (startError) {
      setError(startError instanceof Error ? startError.message : "Failed to start");
      setStarting(false);
    }
  }, [gameId, playerId]);

  const emptySlots = maxPlayers - players.length;

  return (
    <div className={styles.waitingRoom}>
      <h2 className={styles.title}>Waiting Room</h2>

      <div className={styles.joinCodeSection}>
        <span className={styles.joinCodeLabel}>Game Code</span>
        <div className={styles.joinCodeRow}>
          <span className={styles.joinCode}>{gameId.slice(0, 8).toUpperCase()}</span>
          <button className={styles.copyButton} onClick={handleCopyCode}>
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
      </div>

      <div className={styles.playerList}>
        {players.map((player) => (
          <div key={player.id} className={styles.playerSlot}>
            <span className={styles.playerAvatar}>
              {player.name.charAt(0).toUpperCase()}
            </span>
            <span className={styles.playerName}>{player.name}</span>
            {player.isHost && <span className={styles.hostBadge}>Host</span>}
          </div>
        ))}
        {Array.from({ length: emptySlots }).map((_, index) => (
          <div key={`empty-${index}`} className={`${styles.playerSlot} ${styles.playerSlotEmpty}`}>
            <span className={styles.playerAvatar}>?</span>
            <span className={styles.playerNameEmpty}>Waiting for player...</span>
          </div>
        ))}
      </div>

      {autoStartSeconds !== null && (
        <div className={styles.countdown}>
          Starting in {autoStartSeconds}s...
        </div>
      )}

      {error && <p className={styles.error}>{error}</p>}

      <div className={styles.actionButtons}>
        {isHost && players.length >= 2 && (
          <Button variant="primary" onClick={handleStart} disabled={starting}>
            {starting ? "Starting..." : "Start Now"}
          </Button>
        )}
        <Button variant="secondary" onClick={onLeave}>Leave</Button>
      </div>
    </div>
  );
}
