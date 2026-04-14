import type { Bid, Player } from "../../types";
import { SUIT_SYMBOLS, SUIT_COLORS } from "../../types";
import { getAvatarColor } from "./OpponentArea";
import styles from "../../styles/game.module.css";

interface BidSelectorProps {
  validBids: number[];
  numCards: number | null;
  onBid: (amount: number) => void;
  bids: Bid[];
  players: Player[];
  playerId: string | null;
  trumpSuit: string | null;
}

export function BidSelector({ validBids, numCards, onBid, bids, players, playerId, trumpSuit }: BidSelectorProps) {
  const maxBid = numCards ?? 0;
  const totalBidSoFar = bids.reduce((sum, bid) => sum + bid.amount, 0);
  const trumpSymbol = trumpSuit ? SUIT_SYMBOLS[trumpSuit as keyof typeof SUIT_SYMBOLS] : null;
  const trumpColor = trumpSuit ? SUIT_COLORS[trumpSuit as keyof typeof SUIT_COLORS] : undefined;

  return (
    <div className={styles.bidBar}>
      {/* Trump + round info */}
      <div className={styles.bidInfo}>
        {trumpSymbol && (
          <span className={styles.bidTrump} style={{ color: trumpColor === "red" ? "var(--color-card-red)" : "var(--color-text)" }}>
            {trumpSymbol}
          </span>
        )}
        <span className={styles.bidRoundInfo}>{numCards} cards</span>
      </div>

      {/* Other players' bids */}
      {players.length > 1 && (
        <div className={styles.bidHistory}>
          {players.filter((player) => player.id !== playerId).map((player) => {
            const bid = bids.find((bid) => bid.player_id === player.id);
            return (
              <div key={player.id} className={styles.bidHistoryChip}>
                <span
                  className={styles.bidHistoryDot}
                  style={{ backgroundColor: getAvatarColor(player.name) }}
                />
                <span className={styles.bidHistoryName}>{player.name}</span>
                {bid ? (
                  <span className={styles.bidHistoryValue}>{bid.amount}</span>
                ) : (
                  <span className={styles.bidHistoryWaiting}>-</span>
                )}
              </div>
            );
          })}
          {bids.length > 0 && (
            <span className={styles.bidTotal}>({totalBidSoFar}/{numCards})</span>
          )}
        </div>
      )}

      {/* Bid buttons */}
      <div className={styles.bidOptions}>
        {Array.from({ length: maxBid + 1 }, (_, bidValue) => (
          <button
            key={bidValue}
            className={styles.bidButton}
            disabled={!validBids.includes(bidValue)}
            onClick={() => onBid(bidValue)}
          >
            {bidValue}
          </button>
        ))}
      </div>
    </div>
  );
}
