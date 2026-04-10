import styles from "../../styles/game.module.css";

interface BidSelectorProps {
  validBids: number[];
  numCards: number | null;
  onBid: (amount: number) => void;
}

export function BidSelector({ validBids, numCards, onBid }: BidSelectorProps) {
  const maxBid = numCards ?? 0;

  return (
    <div className={styles.bidSelector}>
      <span className={styles.bidPrompt}>Bid</span>
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
