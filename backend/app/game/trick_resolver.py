from backend.app.models import Trick, Suit


def resolve_trick(trick: Trick, trump_suit: Suit) -> str:
    if not trick.plays:
        raise ValueError("Cannot resolve an empty trick")

    lead_suit = trick.plays[0].card.suit
    best_player_id = trick.plays[0].player_id
    best_card = trick.plays[0].card
    best_is_trump = best_card.suit == trump_suit

    for play in trick.plays[1:]:
        card = play.card
        is_trump = card.suit == trump_suit

        if best_is_trump:
            if is_trump and card.rank > best_card.rank:
                best_player_id = play.player_id
                best_card = card
                best_is_trump = True
        else:
            if is_trump:
                best_player_id = play.player_id
                best_card = card
                best_is_trump = True
            elif card.suit == lead_suit and card.rank > best_card.rank:
                best_player_id = play.player_id
                best_card = card

    return best_player_id
