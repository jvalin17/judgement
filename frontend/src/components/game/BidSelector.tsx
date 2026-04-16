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
      <div className={styles.bidHeader}>
        {trumpSymbol && (
          <span className={styles.bidTrump} style={{ color: trumpColor === "red" ? "var(--color-card-red)" : "var(--color-text)" }}>
            {trumpSymbol}
          </span>
        )}
        <span className={styles.bidLabel}>Choose number of hands</span>
        <span className={styles.bidTotal}>{totalBidSoFar}/{numCards}</span>
      </div>

      <BidTable players={players} bids={bids} playerId={playerId} />

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

// --- Bid table: row 1 = player names, row 2 = bids ---

interface BidTableProps {
  players: Player[];
  bids: Bid[];
  playerId: string | null;
}

function BidTable({ players, bids, playerId }: BidTableProps) {
  return (
    <table className={styles.bidTable}>
      <thead>
        <tr>
          {players.map((player) => {
            const isSelf = player.id === playerId;
            const cellClass = [styles.bidTableName, isSelf ? styles.bidTableNameSelf : ""].filter(Boolean).join(" ");
            return (
              <th key={player.id} className={cellClass}>
                <span className={styles.bidTableDot} style={{ backgroundColor: getAvatarColor(player.name) }} />
                <span className={styles.bidTableNameText}>{isSelf ? "You" : player.name}</span>
              </th>
            );
          })}
        </tr>
      </thead>
      <tbody>
        <tr>
          {players.map((player) => {
            const bid = bids.find((entry) => entry.player_id === player.id);
            const isSelf = player.id === playerId;
            const cellClass = [
              styles.bidTableValue,
              bid !== undefined ? styles.bidTableValuePlaced : styles.bidTableValueWaiting,
              isSelf ? styles.bidTableValueSelf : "",
            ].filter(Boolean).join(" ");
            return (
              <td key={player.id} className={cellClass}>
                {bid !== undefined ? bid.amount : (isSelf ? "?" : "—")}
              </td>
            );
          })}
        </tr>
      </tbody>
    </table>
  );
}
