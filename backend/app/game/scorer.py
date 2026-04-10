from backend.app.models import Bid


def score_round(bids: list[Bid], tricks_won: dict[str, int]) -> dict[str, int]:
    scores: dict[str, int] = {}
    for bid in bids:
        won = tricks_won.get(bid.player_id, 0)
        if won == bid.amount:
            if bid.amount == 0:
                scores[bid.player_id] = 10
            elif bid.amount == 1:
                scores[bid.player_id] = 11
            else:
                scores[bid.player_id] = bid.amount * 10
        else:
            if bid.amount == 0:
                scores[bid.player_id] = -10
            elif bid.amount == 1:
                scores[bid.player_id] = -11
            else:
                scores[bid.player_id] = -(bid.amount * 10)
    return scores
