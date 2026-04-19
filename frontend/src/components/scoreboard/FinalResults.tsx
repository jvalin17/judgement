import type { Player, PersonaAward } from "../../types";
import { Button } from "../common";
import styles from "../../styles/scoreboard.module.css";

interface FinalResultsProps {
  players: Player[];
  finalScores: Record<string, number>;
  awardedPersona: PersonaAward | null;
  onPlayAgain: () => void;
}

export function FinalResults({ players, finalScores, awardedPersona, onPlayAgain }: FinalResultsProps) {
  const rankedPlayers = rankPlayersByScore(players, finalScores);
  const winningScore = rankedPlayers.length > 0 ? finalScores[rankedPlayers[0].id] : 0;
  const winners = rankedPlayers.filter((player) => finalScores[player.id] === winningScore);

  return (
    <div className={styles.finalResults}>
      <Confetti />
      <Fireworks />

      <h1 className={styles.gameOverTitle}>Game Over</h1>

      <WinnerDisplay winners={winners} />

      {awardedPersona && <PersonaCard persona={awardedPersona} />}

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

const CONFETTI_COLORS = [
  "#e67e22", "#f1c40f", "#e74c3c", "#2ecc71", "#3498db", "#9b59b6",
  "#ff6b6b", "#ffd93d", "#6bcb77", "#4d96ff", "#ff922b", "#cc5de8",
];
const CONFETTI_COUNT = 150;

function seededRandom(seed: number): number {
  const x = Math.sin(seed * 9301 + 49297) * 49297;
  return x - Math.floor(x);
}

const CONFETTI_PIECES = Array.from({ length: CONFETTI_COUNT }, (_, index) => {
  const wave = Math.floor(index / 50); // 3 waves of 50
  return {
    id: index,
    left: seededRandom(index * 7 + 1) * 100,
    delay: wave * 0.8 + seededRandom(index * 7 + 2) * 1.5,
    duration: 2 + seededRandom(index * 7 + 3) * 4,
    color: CONFETTI_COLORS[index % CONFETTI_COLORS.length],
    size: 6 + seededRandom(index * 7 + 4) * 12,
    rotation: seededRandom(index * 7 + 5) * 360,
    shape: index % 3, // 0=rect, 1=circle, 2=triangle
    swayAmount: 20 + seededRandom(index * 7 + 6) * 60,
  };
});

function Confetti() {
  return (
    <div className={styles.confettiContainer} aria-hidden="true">
      {CONFETTI_PIECES.map((piece) => (
        <div
          key={piece.id}
          className={`${styles.confettiPiece} ${piece.shape === 1 ? styles.confettiCircle : piece.shape === 2 ? styles.confettiTriangle : ""}`}
          style={{
            left: `${piece.left}%`,
            animationDelay: `${piece.delay}s`,
            animationDuration: `${piece.duration}s`,
            backgroundColor: piece.shape === 2 ? "transparent" : piece.color,
            borderBottomColor: piece.shape === 2 ? piece.color : undefined,
            width: `${piece.size}px`,
            height: piece.shape === 1 ? `${piece.size}px` : `${piece.size * 0.6}px`,
            ["--sway" as string]: `${piece.swayAmount}px`,
          }}
        />
      ))}
    </div>
  );
}

// --- Fireworks ---

const FIREWORK_COLORS = ["#e67e22", "#f1c40f", "#e74c3c", "#2ecc71", "#3498db", "#9b59b6", "#ff6b6b", "#ffd93d"];
const FIREWORK_COUNT = 8;
const SPARKS_PER_FIREWORK = 12;

const FIREWORKS_DATA = Array.from({ length: FIREWORK_COUNT }, (_, fwIndex) => ({
  id: fwIndex,
  left: 10 + seededRandom(fwIndex * 11 + 100) * 80,
  top: 10 + seededRandom(fwIndex * 11 + 101) * 40,
  delay: seededRandom(fwIndex * 11 + 102) * 3,
  color: FIREWORK_COLORS[fwIndex % FIREWORK_COLORS.length],
  sparks: Array.from({ length: SPARKS_PER_FIREWORK }, (__, sparkIndex) => {
    const angle = (sparkIndex / SPARKS_PER_FIREWORK) * 360;
    const distance = 30 + seededRandom(fwIndex * 100 + sparkIndex * 7 + 200) * 50;
    return {
      id: sparkIndex,
      angle,
      distance,
    };
  }),
}));

function Fireworks() {
  return (
    <div className={styles.confettiContainer} aria-hidden="true">
      {FIREWORKS_DATA.map((fw) => (
        <div
          key={fw.id}
          className={styles.fireworkBurst}
          style={{
            left: `${fw.left}%`,
            top: `${fw.top}%`,
            animationDelay: `${fw.delay}s`,
          }}
        >
          {fw.sparks.map((spark) => (
            <div
              key={spark.id}
              className={styles.fireworkSpark}
              style={{
                backgroundColor: fw.color,
                ["--spark-x" as string]: `${Math.cos((spark.angle * Math.PI) / 180) * spark.distance}px`,
                ["--spark-y" as string]: `${Math.sin((spark.angle * Math.PI) / 180) * spark.distance}px`,
                animationDelay: `${fw.delay}s`,
              }}
            />
          ))}
        </div>
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
  persona: PersonaAward;
}

function PersonaCard({ persona }: PersonaCardProps) {
  const categoryLabel = CATEGORY_LABELS[persona.persona_category] ?? persona.persona_category;

  return (
    <div className={styles.personaCard}>
      <div className={styles.personaHeader}>
        <span className={styles.personaStyleLabel}>Your Play Style</span>
        <h2 className={styles.personaName}>{persona.persona_name}</h2>
        <span className={styles.personaCategory}>{categoryLabel}</span>
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
