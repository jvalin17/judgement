from backend.app.models import Card, Suit, Rank, Bid
from backend.app.ai.base import RoundContext
from backend.app.ai.easy import EasyAI
from backend.app.ai.medium import MediumAI
from backend.app.ai.hard import HardAI
from backend.app.ai.hand_evaluator import evaluate_hand


def _make_context(
    player_id="p1",
    trump=Suit.SPADES,
    num_cards=10,
    num_players=3,
    bids=None,
    tricks_won=None,
    cards_played=None,
    current_trick_cards=None,
):
    return RoundContext(
        player_id=player_id,
        trump_suit=trump,
        num_cards=num_cards,
        num_players=num_players,
        bids=bids or [],
        tricks_won=tricks_won or {},
        cards_played=cards_played or [],
        current_trick_cards=current_trick_cards or [],
    )


def _strong_hand(trump=Suit.SPADES):
    return [
        Card(suit=trump, rank=Rank.ACE),
        Card(suit=trump, rank=Rank.KING),
        Card(suit=trump, rank=Rank.QUEEN),
        Card(suit=Suit.HEARTS, rank=Rank.ACE),
        Card(suit=Suit.DIAMONDS, rank=Rank.ACE),
    ]


def _weak_hand(trump=Suit.SPADES):
    return [
        Card(suit=Suit.HEARTS, rank=Rank.TWO),
        Card(suit=Suit.HEARTS, rank=Rank.THREE),
        Card(suit=Suit.DIAMONDS, rank=Rank.TWO),
        Card(suit=Suit.CLUBS, rank=Rank.THREE),
        Card(suit=Suit.CLUBS, rank=Rank.FOUR),
    ]


# ---- Hand Evaluator ----

class TestHandEvaluator:
    def test_strong_hand_high_estimate(self):
        hand = _strong_hand()
        ev = evaluate_hand(hand, Suit.SPADES)
        assert ev.trump_count == 3
        assert ev.aces == 3
        assert ev.estimated_tricks >= 3.0

    def test_weak_hand_low_estimate(self):
        hand = _weak_hand()
        ev = evaluate_hand(hand, Suit.SPADES)
        assert ev.trump_count == 0
        assert ev.aces == 0
        assert ev.estimated_tricks < 1.5

    def test_void_suit_adds_ruffing(self):
        hand = [
            Card(suit=Suit.SPADES, rank=Rank.FIVE),
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
            Card(suit=Suit.HEARTS, rank=Rank.THREE),
        ]
        ev = evaluate_hand(hand, Suit.SPADES)
        # Has trump + void in diamonds and clubs
        assert ev.estimated_tricks > 0


# ---- Easy AI ----

class TestEasyAI:
    def test_always_returns_valid_bid(self):
        ai = EasyAI()
        for _ in range(50):
            valid_bids = [0, 1, 2, 3]
            bid = ai.choose_bid([], valid_bids, _make_context())
            assert bid in valid_bids

    def test_always_returns_valid_card(self):
        ai = EasyAI()
        hand = _strong_hand()
        valid = hand[:3]
        for _ in range(50):
            card = ai.choose_card(hand, valid, _make_context())
            assert card in valid


# ---- Medium AI ----

class TestMediumAI:
    def test_bids_higher_with_strong_hand(self):
        ai = MediumAI()
        valid_bids = list(range(6))
        ctx = _make_context(num_cards=5)

        strong_bids = [
            ai.choose_bid(_strong_hand(), valid_bids, ctx) for _ in range(20)
        ]
        weak_bids = [
            ai.choose_bid(_weak_hand(), valid_bids, ctx) for _ in range(20)
        ]

        avg_strong = sum(strong_bids) / len(strong_bids)
        avg_weak = sum(weak_bids) / len(weak_bids)
        assert avg_strong > avg_weak

    def test_always_returns_valid_bid(self):
        ai = MediumAI()
        valid_bids = [0, 1, 3, 4]  # 2 is forbidden
        for _ in range(20):
            bid = ai.choose_bid(_strong_hand(), valid_bids, _make_context(num_cards=5))
            assert bid in valid_bids

    def test_always_returns_valid_card(self):
        ai = MediumAI()
        hand = _strong_hand()
        valid = hand[:3]
        ctx = _make_context()
        for _ in range(20):
            card = ai.choose_card(hand, valid, ctx)
            assert card in valid

    def test_leads_with_high_card(self):
        ai = MediumAI()
        hand = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
            Card(suit=Suit.CLUBS, rank=Rank.THREE),
        ]
        ctx = _make_context(current_trick_cards=[])
        card = ai.choose_card(hand, hand, ctx)
        # Should prefer leading with the ace
        assert card.rank == Rank.ACE

    def test_tries_to_win_trick(self):
        ai = MediumAI()
        hand = [
            Card(suit=Suit.HEARTS, rank=Rank.KING),
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
        ]
        trick_cards = [Card(suit=Suit.HEARTS, rank=Rank.TEN)]
        ctx = _make_context(current_trick_cards=trick_cards)
        card = ai.choose_card(hand, hand, ctx)
        assert card.rank == Rank.KING


# ---- Hard AI ----

class TestHardAI:
    def test_always_returns_valid_bid(self):
        ai = HardAI()
        valid_bids = [0, 1, 2, 4, 5]
        for _ in range(20):
            bid = ai.choose_bid(_strong_hand(), valid_bids, _make_context(num_cards=5))
            assert bid in valid_bids

    def test_always_returns_valid_card(self):
        ai = HardAI()
        hand = _strong_hand()
        valid = hand[:3]
        ctx = _make_context()
        for _ in range(20):
            card = ai.choose_card(hand, valid, ctx)
            assert card in valid

    def test_bids_higher_with_strong_hand(self):
        ai = HardAI()
        valid_bids = list(range(6))
        ctx = _make_context(num_cards=5)

        strong_bids = [
            ai.choose_bid(_strong_hand(), valid_bids, ctx) for _ in range(20)
        ]
        weak_bids = [
            ai.choose_bid(_weak_hand(), valid_bids, ctx) for _ in range(20)
        ]

        avg_strong = sum(strong_bids) / len(strong_bids)
        avg_weak = sum(weak_bids) / len(weak_bids)
        assert avg_strong > avg_weak

    def test_card_counting_affects_estimate(self):
        ai = HardAI()
        valid_bids = list(range(6))

        # If ace of spades already played, our king of spades is stronger
        played = [Card(suit=Suit.SPADES, rank=Rank.ACE)]
        ctx = _make_context(num_cards=5, cards_played=played)
        hand = [
            Card(suit=Suit.SPADES, rank=Rank.KING),
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
            Card(suit=Suit.DIAMONDS, rank=Rank.THREE),
        ]
        bid_with_info = ai.choose_bid(hand, valid_bids, ctx)

        ai2 = HardAI()
        ctx_no_info = _make_context(num_cards=5, cards_played=[])
        bid_without_info = ai2.choose_bid(hand, valid_bids, ctx_no_info)

        # With the ace played, king is highest — bid should be >= without info
        assert bid_with_info >= bid_without_info

    def test_plays_lowest_winner(self):
        ai = HardAI()
        hand = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.HEARTS, rank=Rank.KING),
            Card(suit=Suit.HEARTS, rank=Rank.QUEEN),
        ]
        trick_cards = [Card(suit=Suit.HEARTS, rank=Rank.JACK)]
        bids = [Bid(player_id="p1", amount=2)]
        ctx = _make_context(
            current_trick_cards=trick_cards,
            bids=bids,
        )
        card = ai.choose_card(hand, hand, ctx)
        # Should play queen (lowest winner), not ace
        assert card.rank == Rank.QUEEN


# ---- Integration: AI plays full game ----

class TestAIFullGame:
    def test_all_strategies_complete_game(self):
        """Each AI can play through a full game engine round without errors."""
        from backend.app.models import Player, PlayerType, AIDifficulty, GameConfig
        from backend.app.game.engine import GameEngine
        from backend.app.ai.easy import EasyAI
        from backend.app.ai.medium import MediumAI
        from backend.app.ai.hard import HardAI

        strategies = {"easy": EasyAI(), "medium": MediumAI(), "hard": HardAI()}

        for name, strategy in strategies.items():
            engine = GameEngine(GameConfig())
            players = [
                Player(id=f"ai_{name}_{i}", name=f"AI {i}", player_type=PlayerType.AI)
                for i in range(3)
            ]
            for p in players:
                engine.add_player(p)
            engine.start_game()

            # Play through first round (10 cards)
            # Bidding
            while engine.state.phase.value == "bidding":
                pid = engine.state.current_player_id
                valid_bids = engine.get_valid_bids(pid)
                hand = engine.get_player_hand(pid)
                ctx = engine.get_round_context(pid)
                bid = strategy.choose_bid(hand, valid_bids, ctx)
                assert engine.place_bid(pid, bid), f"{name} AI failed to bid"

            # Playing
            while engine.state.phase.value == "playing":
                pid = engine.state.current_player_id
                valid_cards = engine.get_valid_cards(pid)
                hand = engine.get_player_hand(pid)
                ctx = engine.get_round_context(pid)
                card = strategy.choose_card(hand, valid_cards, ctx)
                assert engine.play_card(pid, card), f"{name} AI failed to play"
