import { useState, useEffect, useCallback } from "react";
import type { Card as CardType, Bid } from "../../types";
import { GamePhase, isMyTurn } from "../../types";
import { useGameContext } from "../../context/GameContext";
import { RoundInfo } from "./RoundInfo";
import { PlayerSeat } from "./OpponentArea";
import { TrickArea } from "./TrickArea";
import { BidSelector } from "./BidSelector";
import { PlayerHand } from "./PlayerHand";
import { PlayerInfo } from "./PlayerInfo";
import { Scoreboard } from "../scoreboard/Scoreboard";
import { Modal, Button, SettingsModal } from "../common";
import styles from "../../styles/game.module.css";
import settingsStyles from "../../styles/settings.module.css";

// --- Seat position types and constants ---

interface SeatPosition {
  left: string;
  top: string;
}

const SEAT_LAYOUTS: Record<number, SeatPosition[]> = {
  3: [
    { left: "50%", top: "82%" },
    { left: "18%", top: "15%" },
    { left: "82%", top: "15%" },
  ],
  4: [
    { left: "50%", top: "82%" },
    { left: "8%", top: "45%" },
    { left: "50%", top: "8%" },
    { left: "92%", top: "45%" },
  ],
  5: [
    { left: "50%", top: "82%" },
    { left: "10%", top: "58%" },
    { left: "14%", top: "14%" },
    { left: "86%", top: "14%" },
    { left: "90%", top: "58%" },
  ],
  6: [
    { left: "50%", top: "82%" },
    { left: "8%", top: "58%" },
    { left: "12%", top: "12%" },
    { left: "50%", top: "5%" },
    { left: "88%", top: "12%" },
    { left: "92%", top: "58%" },
  ],
};

function getSeatPositions(playerCount: number): SeatPosition[] {
  return SEAT_LAYOUTS[playerCount] ?? SEAT_LAYOUTS[3];
}

// --- Main component ---

export function GameBoard() {
  const { state, actions } = useGameContext();
  const [showSettings, setShowSettings] = useState(false);
  const [showExitConfirm, setShowExitConfirm] = useState(false);

  const handleExit = useCallback(() => {
    actions.disconnect();
    actions.resetGame();
  }, [actions]);

  const myTurn = isMyTurn(state);
  const allPlayers = state.players;
  const opponents = allPlayers.filter((player) => player.id !== state.playerId);
  const seatPositions = getSeatPositions(allPlayers.length);

  const humanPlayer = allPlayers.find((player) => player.id === state.playerId);
  const orderedPlayers = humanPlayer ? [humanPlayer, ...opponents] : allPlayers;

  const showRoundOverScoreboard = state.phase === GamePhase.ROUND_OVER && !state.roundOverAcknowledged;

  // --- Trick winner display timer ---
  // When a trick winner is set: pause to show winner, then animate collect, then clear
  useEffect(() => {
    if (!state.trickWinner) return;

    // Phase 1: Show winner label for 1.5s
    const collectTimer = setTimeout(() => {
      actions.startTrickCollect();
    }, 1500);

    // Phase 2: After collect animation (0.6s), clear the trick
    const clearTimer = setTimeout(() => {
      actions.clearTrick();
    }, 2100);

    return () => {
      clearTimeout(collectTimer);
      clearTimeout(clearTimer);
    };
  }, [state.trickWinner, actions]);

  useEffect(() => {
    if (myTurn) {
      actions.sendGetHand();
    }
  }, [myTurn, state.currentPlayerId, actions]);

  const handleBid = useCallback((amount: number) => {
    actions.sendBid(amount);
  }, [actions]);

  const handlePlayCard = useCallback((card: CardType) => {
    actions.sendPlayCard(card);
  }, [actions]);

  const showBidSelector = state.phase === GamePhase.BIDDING && myTurn && state.validBids.length > 0;
  const showPlayArea = state.phase === GamePhase.PLAYING;

  return (
    <div className={styles.gameBoard}>
      <div className={styles.tableOval} />

      <div className={settingsStyles.topButtons}>
        <button
          className={settingsStyles.exitButton}
          onClick={() => setShowExitConfirm(true)}
          aria-label="Exit game"
        >
          &times;
        </button>
        <button
          className={settingsStyles.gearButton}
          onClick={() => setShowSettings(true)}
          aria-label="Settings"
        >
          &#9881;
        </button>
      </div>
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}

      {showExitConfirm && (
        <Modal title="Leave Game?">
          <p style={{ textAlign: "center", color: "var(--color-text-muted)", margin: "0 0 16px" }}>
            Your progress in this game will be lost.
          </p>
          <div style={{ display: "flex", gap: "12px", justifyContent: "center" }}>
            <Button variant="secondary" onClick={() => setShowExitConfirm(false)}>Cancel</Button>
            <Button variant="danger" onClick={handleExit}>Leave</Button>
          </div>
        </Modal>
      )}

      <RoundInfo
        roundNumber={state.roundNumber}
        numCards={state.numCards}
        trumpSuit={state.trumpSuit}
      />

      {orderedPlayers.slice(1).map((player, index) => {
        const seatIndex = index + 1;
        const position = seatPositions[seatIndex];
        if (!position) return null;
        return (
          <PlayerSeat
            key={player.id}
            player={player}
            position={position}
            isCurrentTurn={player.id === state.currentPlayerId}
            bid={findBidForPlayer(state.bids, player.id)}
            tricksWon={state.tricksWon[player.id] ?? 0}
            score={state.cumulativeScores[player.id] ?? 0}
            cardsRemaining={state.hand.length}
          />
        );
      })}

      {showPlayArea && (
        <TrickArea
          currentTrick={state.currentTrick}
          players={state.players}
          orderedPlayers={orderedPlayers}
          seatPositions={seatPositions}
          trickWinner={state.trickWinner}
          trickCollecting={state.trickCollecting}
        />
      )}

      <StatusMessage state={state} myTurn={myTurn} />

      {state.error && <div className={styles.errorBar}>{state.error}</div>}

      {showBidSelector ? (
        <BidSelector
          validBids={state.validBids}
          numCards={state.numCards}
          onBid={handleBid}
          bids={state.bids}
          players={state.players}
          playerId={state.playerId}
          trumpSuit={state.trumpSuit}
        />
      ) : (
        <PlayerInfo
          playerId={state.playerId}
          playerName={humanPlayer?.name ?? "You"}
          bids={state.bids}
          tricksWon={state.tricksWon}
          cumulativeScores={state.cumulativeScores}
          isMyTurn={myTurn}
        />
      )}

      <PlayerHand
        hand={state.hand}
        validCards={state.validCards}
        isMyTurn={myTurn && state.phase === GamePhase.PLAYING}
        onPlayCard={handlePlayCard}
      />

      {showRoundOverScoreboard && (
        <Modal title={`Round ${state.roundNumber} Complete`}>
          <Scoreboard
            players={state.players}
            bids={state.bids}
            tricksWon={state.tricksWon}
            cumulativeScores={state.cumulativeScores}
            roundScores={state.roundScores}
            currentPlayerId={state.playerId}
          />
          <div style={{ marginTop: "16px", textAlign: "center" }}>
            <Button variant="primary" onClick={() => actions.acknowledgeRoundOver()}>
              Next Round
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
}

// --- Status message ---

interface StatusMessageProps {
  state: { phase: GamePhase; currentPlayerId: string | null; playerId: string | null; players: Array<{ id: string; name: string }> };
  myTurn: boolean;
}

function StatusMessage({ state, myTurn }: StatusMessageProps) {
  // Show animated banner for "your turn"
  if (myTurn && (state.phase === GamePhase.BIDDING || state.phase === GamePhase.PLAYING)) {
    const action = state.phase === GamePhase.BIDDING ? "bid" : "play";
    return <TurnBanner key={`${state.currentPlayerId}-${state.phase}`} action={action} />;
  }

  // Quiet status for waiting on others
  const message = buildWaitingMessage(state);
  if (!message) return null;

  return <div className={styles.statusBar}>{message}</div>;
}

function TurnBanner({ action }: { action: string }) {
  return (
    <div className={styles.turnBanner}>
      Your turn to {action}!
    </div>
  );
}

function buildWaitingMessage(
  state: { phase: GamePhase; currentPlayerId: string | null; playerId: string | null; players: Array<{ id: string; name: string }> },
): string {
  if (state.phase === GamePhase.BIDDING) {
    return `Waiting for ${findCurrentPlayerName(state)} to bid...`;
  }
  if (state.phase === GamePhase.PLAYING) {
    return `Waiting for ${findCurrentPlayerName(state)}...`;
  }
  return "";
}

function findCurrentPlayerName(state: { currentPlayerId: string | null; players: Array<{ id: string; name: string }> }): string {
  const player = state.players.find((player) => player.id === state.currentPlayerId);
  return player?.name ?? "opponent";
}

// --- Helpers ---

function findBidForPlayer(bids: Bid[], playerId: string): number | null {
  const bid = bids.find((bid) => bid.player_id === playerId);
  return bid ? bid.amount : null;
}
