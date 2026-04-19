import { useState, useEffect } from "react";
import type { Player, PersonaAward } from "../../types";
import { Button } from "../common";
import { getSharePreview, shareData, getShareStatus } from "../../services/api";
import type { SharePreviewResponse } from "../../services/api";
import styles from "../../styles/scoreboard.module.css";

interface FinalResultsProps {
  players: Player[];
  finalScores: Record<string, number>;
  awardedPersona: PersonaAward | null;
  playerId: string | null;
  onPlayAgain: () => void;
}

export function FinalResults({ players, finalScores, awardedPersona, playerId, onPlayAgain }: FinalResultsProps) {
  const rankedPlayers = rankPlayersByScore(players, finalScores);
  const winningScore = rankedPlayers.length > 0 ? finalScores[rankedPlayers[0].id] : 0;
  const winners = rankedPlayers.filter((player) => finalScores[player.id] === winningScore);
  const playerRank = getPlayerRank(rankedPlayers, finalScores, playerId);

  return (
    <div className={styles.finalResults}>
      <CelebrationEffect rank={playerRank} />

      <h1 className={styles.gameOverTitle}>Game Over</h1>

      <WinnerDisplay winners={winners} />

      {awardedPersona && <PersonaCard persona={awardedPersona} />}

      <div className={styles.finalScoreList}>
        {rankedPlayers.map((player) => (
          <FinalScoreRow
            key={player.id}
            playerName={player.id === playerId ? "Your score" : player.name}
            score={finalScores[player.id] ?? 0}
            isWinner={finalScores[player.id] === winningScore}
          />
        ))}
      </div>

      <SharePrompt />

      <div className={styles.actions}>
        <Button variant="primary" size="large" onClick={onPlayAgain}>
          Play Again
        </Button>
      </div>
    </div>
  );
}

// --- Helpers ---

function getPlayerRank(
  rankedPlayers: Player[],
  scores: Record<string, number>,
  playerId: string | null,
): number {
  if (!playerId) return rankedPlayers.length;
  let rank = 1;
  let prevScore: number | null = null;
  for (const player of rankedPlayers) {
    const score = scores[player.id] ?? 0;
    if (prevScore !== null && score < prevScore) {
      rank = rankedPlayers.indexOf(player) + 1;
    }
    if (player.id === playerId) return rank;
    prevScore = score;
  }
  return rankedPlayers.length;
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

// --- Celebration effects based on player rank ---

function CelebrationEffect({ rank }: { rank: number }) {
  switch (rank) {
    case 1:
      return <ChampionCelebration />;
    case 2:
      return <SilverCelebration />;
    case 3:
      return <FlowersCelebration />;
    case 4:
      return <BubblesCelebration />;
    default:
      return <CloudsCelebration />;
  }
}

// --- 1st Place: Grand fireworks + rockets + sparkles + confetti ---

function ChampionCelebration() {
  return (
    <>
      <Confetti count={200} />
      <Fireworks count={14} />
      <Rockets />
      <Sparkles />
    </>
  );
}

// --- 2nd Place: Standard confetti + fireworks (original) ---

function SilverCelebration() {
  return (
    <>
      <Confetti count={120} />
      <Fireworks count={6} />
    </>
  );
}

// --- 3rd Place: Falling flowers ---

function FlowersCelebration() {
  return (
    <div className={styles.confettiContainer} aria-hidden="true">
      {FLOWERS_DATA.map((flower) => (
        <div
          key={flower.id}
          className={styles.flowerPiece}
          style={{
            left: `${flower.left}%`,
            animationDelay: `${flower.delay}s`,
            animationDuration: `${flower.duration}s`,
            fontSize: `${flower.size}px`,
            ["--sway" as string]: `${flower.swayAmount}px`,
          }}
        >
          {flower.emoji}
        </div>
      ))}
    </div>
  );
}

const FLOWER_EMOJIS = ["\u{1F338}", "\u{1F33A}", "\u{1F33B}", "\u{1F33C}", "\u{1F33E}", "\u{1F340}", "\u{1F337}", "\u{2728}"];
const FLOWERS_DATA = Array.from({ length: 60 }, (_, index) => ({
  id: index,
  left: seededRandom(index * 7 + 500) * 100,
  delay: Math.floor(index / 20) * 1.2 + seededRandom(index * 7 + 501) * 2,
  duration: 3 + seededRandom(index * 7 + 502) * 4,
  size: 16 + seededRandom(index * 7 + 503) * 16,
  swayAmount: 30 + seededRandom(index * 7 + 504) * 50,
  emoji: FLOWER_EMOJIS[index % FLOWER_EMOJIS.length],
}));

// --- 4th Place: Rising bubbles ---

function BubblesCelebration() {
  return (
    <div className={styles.confettiContainer} aria-hidden="true">
      {BUBBLES_DATA.map((bubble) => (
        <div
          key={bubble.id}
          className={styles.bubble}
          style={{
            left: `${bubble.left}%`,
            animationDelay: `${bubble.delay}s`,
            animationDuration: `${bubble.duration}s`,
            width: `${bubble.size}px`,
            height: `${bubble.size}px`,
            ["--sway" as string]: `${bubble.swayAmount}px`,
          }}
        />
      ))}
    </div>
  );
}

const BUBBLES_DATA = Array.from({ length: 40 }, (_, index) => ({
  id: index,
  left: seededRandom(index * 7 + 600) * 100,
  delay: seededRandom(index * 7 + 601) * 4,
  duration: 4 + seededRandom(index * 7 + 602) * 5,
  size: 10 + seededRandom(index * 7 + 603) * 30,
  swayAmount: 20 + seededRandom(index * 7 + 604) * 40,
}));

// --- 5th Place: Drifting clouds ---

function CloudsCelebration() {
  return (
    <div className={styles.confettiContainer} aria-hidden="true">
      {CLOUDS_DATA.map((cloud) => (
        <div
          key={cloud.id}
          className={styles.cloud}
          style={{
            top: `${cloud.top}%`,
            animationDelay: `${cloud.delay}s`,
            animationDuration: `${cloud.duration}s`,
            opacity: cloud.opacity,
            fontSize: `${cloud.size}px`,
          }}
        >
          {"\u2601\uFE0F"}
        </div>
      ))}
    </div>
  );
}

const CLOUDS_DATA = Array.from({ length: 12 }, (_, index) => ({
  id: index,
  top: 10 + seededRandom(index * 7 + 700) * 60,
  delay: seededRandom(index * 7 + 701) * 5,
  duration: 8 + seededRandom(index * 7 + 702) * 8,
  size: 30 + seededRandom(index * 7 + 703) * 30,
  opacity: 0.3 + seededRandom(index * 7 + 704) * 0.4,
}));

// --- Confetti (shared, parameterized) ---

const CONFETTI_COLORS = [
  "#e67e22", "#f1c40f", "#e74c3c", "#2ecc71", "#3498db", "#9b59b6",
  "#ff6b6b", "#ffd93d", "#6bcb77", "#4d96ff", "#ff922b", "#cc5de8",
];

function seededRandom(seed: number): number {
  const x = Math.sin(seed * 9301 + 49297) * 49297;
  return x - Math.floor(x);
}

function generateConfetti(count: number): ConfettiPiece[] {
  return Array.from({ length: count }, (_, index) => {
    const wave = Math.floor(index / 50);
    return {
      id: index,
      left: seededRandom(index * 7 + 1) * 100,
      delay: wave * 0.8 + seededRandom(index * 7 + 2) * 1.5,
      duration: 2 + seededRandom(index * 7 + 3) * 4,
      color: CONFETTI_COLORS[index % CONFETTI_COLORS.length],
      size: 6 + seededRandom(index * 7 + 4) * 12,
      rotation: seededRandom(index * 7 + 5) * 360,
      shape: index % 3,
      swayAmount: 20 + seededRandom(index * 7 + 6) * 60,
    };
  });
}

interface ConfettiPiece {
  id: number;
  left: number;
  delay: number;
  duration: number;
  color: string;
  size: number;
  rotation: number;
  shape: number;
  swayAmount: number;
}

// Pre-compute for each level
const CONFETTI_200 = generateConfetti(200);
const CONFETTI_120 = generateConfetti(120);

function Confetti({ count }: { count: number }) {
  const pieces = count >= 200 ? CONFETTI_200 : CONFETTI_120;

  return (
    <div className={styles.confettiContainer} aria-hidden="true">
      {pieces.map((piece) => (
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

// --- Fireworks (shared, parameterized) ---

const FIREWORK_COLORS = ["#e67e22", "#f1c40f", "#e74c3c", "#2ecc71", "#3498db", "#9b59b6", "#ff6b6b", "#ffd93d"];
const SPARKS_PER_FIREWORK = 12;

function generateFireworks(count: number) {
  return Array.from({ length: count }, (_, fwIndex) => ({
    id: fwIndex,
    left: 10 + seededRandom(fwIndex * 11 + 100) * 80,
    top: 10 + seededRandom(fwIndex * 11 + 101) * 40,
    delay: seededRandom(fwIndex * 11 + 102) * 3,
    color: FIREWORK_COLORS[fwIndex % FIREWORK_COLORS.length],
    sparks: Array.from({ length: SPARKS_PER_FIREWORK }, (__, sparkIndex) => {
      const angle = (sparkIndex / SPARKS_PER_FIREWORK) * 360;
      const distance = 30 + seededRandom(fwIndex * 100 + sparkIndex * 7 + 200) * 50;
      return { id: sparkIndex, angle, distance };
    }),
  }));
}

const FIREWORKS_14 = generateFireworks(14);
const FIREWORKS_6 = generateFireworks(6);

function Fireworks({ count }: { count: number }) {
  const data = count >= 14 ? FIREWORKS_14 : FIREWORKS_6;

  return (
    <div className={styles.confettiContainer} aria-hidden="true">
      {data.map((fw) => (
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

// --- Rockets (1st place only) ---

const ROCKETS_DATA = Array.from({ length: 6 }, (_, index) => ({
  id: index,
  left: 10 + seededRandom(index * 11 + 300) * 80,
  delay: 0.5 + seededRandom(index * 11 + 301) * 3,
}));

function Rockets() {
  return (
    <div className={styles.confettiContainer} aria-hidden="true">
      {ROCKETS_DATA.map((rocket) => (
        <div
          key={rocket.id}
          className={styles.rocket}
          style={{
            left: `${rocket.left}%`,
            animationDelay: `${rocket.delay}s`,
          }}
        >
          {"\u{1F680}"}
        </div>
      ))}
    </div>
  );
}

// --- Sparkles (1st place only) ---

const SPARKLES_DATA = Array.from({ length: 20 }, (_, index) => ({
  id: index,
  left: seededRandom(index * 7 + 400) * 100,
  top: seededRandom(index * 7 + 401) * 70,
  delay: seededRandom(index * 7 + 402) * 4,
  size: 12 + seededRandom(index * 7 + 403) * 20,
}));

function Sparkles() {
  return (
    <div className={styles.confettiContainer} aria-hidden="true">
      {SPARKLES_DATA.map((sparkle) => (
        <div
          key={sparkle.id}
          className={styles.sparkle}
          style={{
            left: `${sparkle.left}%`,
            top: `${sparkle.top}%`,
            animationDelay: `${sparkle.delay}s`,
            fontSize: `${sparkle.size}px`,
          }}
        >
          {"\u2728"}
        </div>
      ))}
    </div>
  );
}

// --- Share Prompt ---

function SharePrompt() {
  const [dismissed, setDismissed] = useState(false);
  const [preview, setPreview] = useState<SharePreviewResponse | null>(null);
  const [showPopup, setShowPopup] = useState(false);
  const [shareState, setShareState] = useState<"idle" | "sharing" | "done" | "error">("idle");
  const [shareMessage, setShareMessage] = useState("");

  useEffect(() => {
    const skipShare = localStorage.getItem("judgement_skip_share") === "true";
    if (skipShare) {
      setDismissed(true);
      return;
    }
    getSharePreview().then(setPreview).catch(() => {});
  }, []);

  if (dismissed || !preview || preview.total === 0) return null;

  const handleShare = async () => {
    setShareState("sharing");
    try {
      const result = await shareData();
      if (!result.success) {
        setShareState("error");
        setShareMessage(result.message);
        return;
      }
      // Poll status until upload finishes (runs in background thread)
      for (let attempt = 0; attempt < 20; attempt++) {
        await new Promise((r) => setTimeout(r, 1500));
        const status = await getShareStatus();
        if (status.state === "success") {
          setShareState("done");
          setShareMessage(status.message || "Thanks for sharing!");
          return;
        }
        if (status.state === "error") {
          setShareState("error");
          setShareMessage(status.message);
          return;
        }
      }
      setShareState("done");
      setShareMessage("Thanks for sharing!");
    } catch {
      setShareState("error");
      setShareMessage("Could not connect to server");
    }
  };

  const handleDismiss = () => {
    setShowPopup(false);
    setDismissed(true);
  };

  const handleNeverAsk = () => {
    localStorage.setItem("judgement_skip_share", "true");
    setShowPopup(false);
    setDismissed(true);
  };

  if (shareState === "done") {
    return (
      <div className={styles.sharePrompt}>
        <span className={styles.shareMessage}>{shareMessage}</span>
      </div>
    );
  }

  return (
    <>
      <div className={styles.sharePrompt}>
        <button className={styles.shareButton} onClick={() => setShowPopup(true)}>
          Share Game Data
        </button>
        <span className={styles.shareDescription}>Help improve the AI</span>
      </div>

      {showPopup && (
        <div className={styles.shareOverlay} onClick={() => setShowPopup(false)}>
          <div className={styles.sharePopup} onClick={(e) => e.stopPropagation()}>
            <span className={styles.shareTitle}>Share Game Data</span>

            <span className={styles.shareDescription}>
              Help the community train stronger AI by sharing anonymized game decisions.
            </span>

            <div className={styles.shareDetails}>
              <div className={styles.shareDetailRow}>
                <span className={styles.shareDetailLabel}>Bid decisions</span>
                <span className={styles.shareDetailValue}>{preview.bid_decisions}</span>
              </div>
              <div className={styles.shareDetailRow}>
                <span className={styles.shareDetailLabel}>Play decisions</span>
                <span className={styles.shareDetailValue}>{preview.play_decisions}</span>
              </div>
              <div className={styles.shareDetailRow}>
                <span className={styles.shareDetailLabel}>Your decisions</span>
                <span className={styles.shareDetailValue}>{preview.human_bid_decisions + preview.human_play_decisions}</span>
              </div>
              <div className={styles.shareDetailRow}>
                <span className={styles.shareDetailLabel}>Total examples</span>
                <span className={styles.shareDetailValue}>{preview.total}</span>
              </div>
            </div>

            <div className={styles.shareFinePrint}>
              Only numeric features are shared — no names, no cards, no personal data.
              Data comes from game winners only.
            </div>

            {shareState === "error" && (
              <span className={styles.shareError}>{shareMessage}</span>
            )}

            <div className={styles.sharePopupActions}>
              <button className={styles.shareDismiss} onClick={handleDismiss}>Not now</button>
              <button className={styles.shareDismiss} onClick={handleNeverAsk}>Don't ask again</button>
              <button
                className={styles.shareButton}
                onClick={handleShare}
                disabled={shareState === "sharing"}
              >
                {shareState === "sharing" ? "Sharing..." : "Share"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
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
  boldness: "Boldness",
  precision: "Precision",
  resilience: "Resilience",
  clutch: "Clutch",
  trajectory: "Trajectory",
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
