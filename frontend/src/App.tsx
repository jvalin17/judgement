import { useCallback } from "react";
import { GamePhase } from "./types";
import { GameProvider, useGameContext } from "./context/GameContext";
import { SettingsProvider } from "./context/SettingsContext";
import { GameLobby } from "./components/lobby";
import { GameBoard } from "./components/game";
import { FinalResults } from "./components/scoreboard";
import styles from "./styles/app.module.css";

function App() {
  return (
    <SettingsProvider>
      <GameProvider>
        <div className={styles.app}>
          <AppContent />
        </div>
      </GameProvider>
    </SettingsProvider>
  );
}

function AppContent() {
  const { state, actions } = useGameContext();

  const handleGameCreated = useCallback(
    (gameId: string, playerId: string) => {
      actions.setGameInfo(gameId, playerId);
    },
    [actions],
  );

  const handlePlayAgain = useCallback(() => {
    actions.disconnect();
    actions.resetGame();
  }, [actions]);

  return (
    <div className={styles.screenContainer}>
      <CurrentScreen
        phase={state.phase}
        gameId={state.gameId}
        onGameCreated={handleGameCreated}
        onPlayAgain={handlePlayAgain}
      />
    </div>
  );
}

interface CurrentScreenProps {
  phase: GamePhase;
  gameId: string | null;
  onGameCreated: (gameId: string, playerId: string) => void;
  onPlayAgain: () => void;
}

function CurrentScreen({ phase, gameId, onGameCreated, onPlayAgain }: CurrentScreenProps) {
  if (!gameId || phase === GamePhase.LOBBY) {
    return <GameLobby onGameCreated={onGameCreated} />;
  }

  if (phase === GamePhase.GAME_OVER) {
    return <GameOverScreen onPlayAgain={onPlayAgain} />;
  }

  return <GameBoard />;
}

function GameOverScreen({ onPlayAgain }: { onPlayAgain: () => void }) {
  const { state } = useGameContext();

  return (
    <FinalResults
      players={state.players}
      finalScores={state.cumulativeScores}
      onPlayAgain={onPlayAgain}
    />
  );
}

export default App;
