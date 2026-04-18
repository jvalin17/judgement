import type { Player, MascotPersonaAwardedEventData } from "../../types";
import { Button } from "../common";
import styles from "../../styles/scoreboard.module.css";

interface FinalResultsProps {
  players: Player[];
  finalScores: Record<string, number>;
  awardedPersona: MascotPersonaAwardedEventData | null;
  onPlayAgain: () => void;
}

export function FinalResults({ players, finalScores, awardedPersona, onPlayAgain }: FinalResultsProps) {
  const rankedPlayers = rankPlayersByScore(players, finalScores);
  const winningScore = rankedPlayers.length > 0 ? finalScores[rankedPlayers[0].id] : 0;
  const winners = rankedPlayers.filter((player) => finalScores[player.id] === winningScore);

  return (
    <div className={styles.finalResults}>
      <Confetti />

      <h1 className={styles.gameOverTitle}>Game Over</h1>

      <WinnerDisplay winners={winners} />

      <div className={styles.finalScoreList}>
        {rankedPlayers.map((player) => (
          <FinalScoreRow
            key={player.id}
            playerName={player.name}
            score={finalScores[player.id] ?? 0}
            isWinner={finalScores[player.id] === winningScore}
          />
        ))}
      </div>

      {awardedPersona && <PersonaCard persona={awardedPersona} />}

      <div className={styles.actions}>
        <Button variant="primary" size="large" onClick={onPlayAgain}>
          Play Again
        </Button>
      </div>
    </div>
  );
}

interface WinnerDisplayProps {
  winners: Player[];
}

function WinnerDisplay({ winners }: WinnerDisplayProps) {
  const winnerNames = winners.map((winner) => winner.name).join(" & ");

  return (
    <div className={styles.winnerSection}>
      <span className={styles.winnerLabel}>{winners.length > 1 ? "Winners" : "Winner"}</span>
      <span className={styles.winnerName}>{winnerNames}</span>
    </div>
  );
}

interface FinalScoreRowProps {
  playerName: string;
  score: number;
  isWinner: boolean;
}

function FinalScoreRow({ playerName, score, isWinner }: FinalScoreRowProps) {
  const rowClass = [styles.finalScoreRow, isWinner ? styles.winner : ""].filter(Boolean).join(" ");

  return (
    <div className={rowClass}>
      <span className={styles.finalScoreName}>{playerName}</span>
      <span className={styles.finalScoreValue}>{score}</span>
    </div>
  );
}

function rankPlayersByScore(players: Player[], scores: Record<string, number>): Player[] {
  return [...players].sort((playerA, playerB) => (scores[playerB.id] ?? 0) - (scores[playerA.id] ?? 0));
}

// --- Confetti ---

const CONFETTI_COLORS = ["#e67e22", "#f1c40f", "#e74c3c", "#2ecc71", "#3498db", "#9b59b6"];
const CONFETTI_COUNT = 60;

function seededRandom(seed: number): number {
  const x = Math.sin(seed * 9301 + 49297) * 49297;
  return x - Math.floor(x);
}

const CONFETTI_PIECES = Array.from({ length: CONFETTI_COUNT }, (_, index) => ({
  id: index,
  left: seededRandom(index * 7 + 1) * 100,
  delay: seededRandom(index * 7 + 2) * 2,
  duration: 2 + seededRandom(index * 7 + 3) * 3,
  color: CONFETTI_COLORS[index % CONFETTI_COLORS.length],
  size: 4 + seededRandom(index * 7 + 4) * 8,
  rotation: seededRandom(index * 7 + 5) * 360,
}));

function Confetti() {

  return (
    <div className={styles.confettiContainer} aria-hidden="true">
      {CONFETTI_PIECES.map((piece) => (
        <div
          key={piece.id}
          className={styles.confettiPiece}
          style={{
            left: `${piece.left}%`,
            animationDelay: `${piece.delay}s`,
            animationDuration: `${piece.duration}s`,
            backgroundColor: piece.color,
            width: `${piece.size}px`,
            height: `${piece.size * 0.6}px`,
            transform: `rotate(${piece.rotation}deg)`,
          }}
        />
      ))}
    </div>
  );
}

// --- Persona Card ---

const DIMENSION_LABELS: Record<string, string> = {
  risk: "Risk",
  planning: "Planning",
  patience: "Patience",
  aggression: "Aggression",
  adaptability: "Adaptability",
  consistency: "Consistency",
};

const CATEGORY_LABELS: Record<string, string> = {
  superhero: "Superhero",
  animal: "Animal Totem",
  poker: "Poker Archetype",
  cartoon: "Cartoon Icon",
  pokemon: "Pokemon",
};

interface PersonaCardProps {
  persona: MascotPersonaAwardedEventData;
}

function PersonaCard({ persona }: PersonaCardProps) {
  const categoryLabel = CATEGORY_LABELS[persona.persona_category] ?? persona.persona_category;

  return (
    <div className={styles.personaCard}>
      <div className={styles.personaHeader}>
        <span className={styles.personaCategory}>{categoryLabel}</span>
        <h2 className={styles.personaName}>{persona.persona_name}</h2>
        <p className={styles.personaTagline}>{persona.persona_tagline}</p>
      </div>
      <div className={styles.traitBars}>
        {Object.entries(DIMENSION_LABELS).map(([dim, label]) => (
          <TraitBar
            key={dim}
            label={label}
            playerValue={persona.player_traits[dim] ?? 0}
            personaValue={persona.traits[dim] ?? 0}
          />
        ))}
      </div>
    </div>
  );
}

interface TraitBarProps {
  label: string;
  playerValue: number;
  personaValue: number;
}

function TraitBar({ label, playerValue, personaValue }: TraitBarProps) {
  return (
    <div className={styles.traitRow}>
      <span className={styles.traitLabel}>{label}</span>
      <div className={styles.traitBarTrack}>
        <div
          className={styles.traitBarFillPlayer}
          style={{ width: `${playerValue * 100}%` }}
        />
        <div
          className={styles.traitBarMarker}
          style={{ left: `${personaValue * 100}%` }}
          title={`${label} persona target`}
        />
      </div>
    </div>
  );
}
