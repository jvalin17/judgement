from backend.app.models import Bid, MadeScoring, MissedScoring


def made_bid_points(amount: int, made_scoring: MadeScoring = MadeScoring.CLASSIC) -> int:
    """Points for making a bid exactly."""
    if made_scoring == MadeScoring.TEN_PLUS_BID:
        return 10 + amount
    if amount == 0:
        return 10
    if amount == 1:
        return 11
    return amount * 10


def missed_bid_points(
    amount: int,
    tricks_won: int,
    made_scoring: MadeScoring = MadeScoring.CLASSIC,
    missed_scoring: MissedScoring = MissedScoring.NEGATIVE,
) -> int:
    """Points for missing a bid (zero or negative)."""
    if missed_scoring == MissedScoring.ZERO:
        return 0
    if missed_scoring == MissedScoring.PER_TRICK_OFF:
        return -10 * abs(tricks_won - amount)
    return -made_bid_points(amount, made_scoring)


def score_round(
    bids: list[Bid],
    tricks_won: dict[str, int],
    made_scoring: MadeScoring = MadeScoring.CLASSIC,
    missed_scoring: MissedScoring = MissedScoring.NEGATIVE,
) -> dict[str, int]:
    scores: dict[str, int] = {}
    for bid in bids:
        won = tricks_won.get(bid.player_id, 0)
        if won == bid.amount:
            scores[bid.player_id] = made_bid_points(bid.amount, made_scoring)
        else:
            scores[bid.player_id] = missed_bid_points(bid.amount, won, made_scoring, missed_scoring)
    return scores
