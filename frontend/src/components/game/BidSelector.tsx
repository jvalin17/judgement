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
    <div className={styles.bidOverlay}>
      <div className={styles.bidPopup}>
        <div className={styles.bidPopupTitle}>
          Place Your Bid
          {trumpSymbol && (
            <span className={styles.bidTrump} style={{ color: trumpColor === "red" ? "var(--color-card-red)" : "var(--color-text-muted)" }}>
              {" "}Trump: {trumpSymbol}
            </span>
          )}
        </div>

        <div className={styles.bidRoundInfo}>
          Round {numCards} cards
        </div>

        {/* Bid history — show all players and their bids */}
        <div className={styles.bidHistory}>
          {players.map((player) => {
            const bid = bids.find((bid) => bid.player_id === player.id);
            const isMe = player.id === playerId;
            return (
              <div key={player.id} className={styles.bidHistoryRow}>
                <span className={`${styles.bidHistoryName} ${isMe ? styles.bidHistoryYou : ""}`}>
                  <span
                    className={styles.bidHistoryDot}
                    style={{ backgroundColor: getAvatarColor(player.name) }}
                  />
                  {isMe ? `${player.name} (you)` : player.name}
                </span>
                {bid ? (
                  <span className={styles.bidHistoryValue}>{bid.amount}</span>
                ) : isMe ? (
                  <span className={styles.bidHistoryWaiting}>your turn</span>
                ) : (
                  <span className={styles.bidHistoryWaiting}>waiting</span>
                )}
              </div>
            );
          })}
        </div>

        <div className={styles.bidDivider} />

        {/* Bid buttons */}
        <div className={styles.bidPrompt}>Choose your bid</div>
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

        {bids.length > 0 && (
          <div className={styles.bidTotal}>
            Total bids so far: {totalBidSoFar} / {numCards}
          </div>
        )}
      </div>
    </div>
  );
}
