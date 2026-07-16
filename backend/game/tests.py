from collections import Counter

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .engine import (
    Deck,
    Hand,
    HandEvaluator,
    HandGenerator,
    ScoreCalculator,
    Tile,
    ValuationAlgorithm,
    WinChecker,
)
from .models import Move, Session
from .solo import SEAT_WINDS, SoloGame


def tiles(*specs):
    """Helper: tiles('B', 1, 'B', 2, ...) -> list of Tile objects."""
    suit_map = {"B": "bamboo", "C": "circles", "K": "characters", "H": "honour"}
    out = []
    for index in range(0, len(specs), 2):
        out.append(Tile(suit_map[specs[index]], specs[index + 1]))
    return out


class MahjongEngineTests(TestCase):
    def test_deck_contains_singapore_mahjong_tile_set(self):
        deck = Deck()

        self.assertEqual(len(deck), 148)
        self.assertEqual(len([tile for tile in deck.tiles if tile.is_bonus]), 12)
        self.assertEqual(len([tile for tile in deck.tiles if not tile.is_bonus]), 136)

    def test_random_hand_has_thirteen_playable_tiles(self):
        hand = HandGenerator().generate_random_hand()

        self.assertEqual(len(hand.tiles), 13)
        self.assertTrue(all(not tile.is_bonus for tile in hand.tiles))

    def test_bonus_tiles_are_separated_from_playable_hand(self):
        hand = HandGenerator().generate_random_hand()

        self.assertTrue(all(tile.is_bonus for tile in hand.bonus_tiles))
        self.assertEqual(hand.to_dict()["tile_count"], 13)

    def test_difficulty_controls_closeness_to_winning(self):
        from statistics import mean

        generator = HandGenerator()
        evaluator = HandEvaluator()

        def average_strength(difficulty, samples=120):
            scores = []
            for _ in range(samples):
                hand = generator.generate_random_hand(hand_size=14, difficulty=difficulty)
                self.assertEqual(len(hand.tiles), 14)
                # No more than four of any tile is dealt.
                counts = Counter((t.suit, t.value) for t in hand.tiles)
                self.assertTrue(all(c <= 4 for c in counts.values()))
                scores.append(evaluator.evaluate_hand(hand.tiles))
            return mean(scores)

        easy = average_strength("easy")
        medium = average_strength("medium")
        hard = average_strength("hard")

        # Easier hands are seeded with more complete melds, so they sit closer
        # to a winning shape on average.
        self.assertGreater(easy, medium)
        self.assertGreater(medium, hard)

    def test_tile_serializes_for_api_response(self):
        tile = Tile("bamboo", 3)

        self.assertEqual(
            tile.to_dict(),
            {
                "suit": "bamboo",
                "value": 3,
                "code": "B3",
                "label": "3 bamboo",
                "is_bonus": False,
            },
        )

    def test_evaluator_rewards_complete_sets_and_pairs(self):
        evaluator = HandEvaluator()
        structured_tiles = [
            Tile("bamboo", 1),
            Tile("bamboo", 2),
            Tile("bamboo", 3),
            Tile("circles", 5),
            Tile("circles", 5),
            Tile("circles", 5),
            Tile("characters", 7),
            Tile("characters", 8),
            Tile("characters", 9),
            Tile("honour", "red"),
            Tile("honour", "red"),
        ]
        scattered_tiles = [
            Tile("bamboo", 1),
            Tile("bamboo", 4),
            Tile("bamboo", 7),
            Tile("circles", 2),
            Tile("circles", 5),
            Tile("circles", 8),
            Tile("characters", 1),
            Tile("characters", 4),
            Tile("characters", 7),
            Tile("honour", "red"),
            Tile("honour", "green"),
            Tile("honour", "white"),
        ]

        self.assertGreater(
            evaluator.evaluate_hand(structured_tiles),
            evaluator.evaluate_hand(scattered_tiles),
        )

    def test_valuation_recommends_isolated_discard(self):
        hand = Hand([
            Tile("bamboo", 1),
            Tile("bamboo", 2),
            Tile("bamboo", 3),
            Tile("circles", 5),
            Tile("circles", 5),
            Tile("circles", 5),
            Tile("characters", 7),
            Tile("characters", 8),
            Tile("characters", 9),
            Tile("honour", "red"),
            Tile("honour", "red"),
            Tile("bamboo", 9),
            Tile("circles", 1),
        ])

        recommendation = ValuationAlgorithm().recommend_discard(hand)

        self.assertIn(recommendation["discard"]["code"], ["B9", "C1"])
        self.assertIn("reasoning", recommendation)

    def test_optimal_discards_returns_every_tied_best(self):
        # Three finished melds and a pair, plus three unconnected singletons:
        # discarding any one of those singletons is equally optimal.
        hand = Hand([
            Tile("bamboo", 1),
            Tile("bamboo", 2),
            Tile("bamboo", 3),
            Tile("circles", 4),
            Tile("circles", 5),
            Tile("circles", 6),
            Tile("characters", 7),
            Tile("characters", 8),
            Tile("characters", 9),
            Tile("bamboo", 5),
            Tile("bamboo", 5),
            Tile("honour", "east"),
            Tile("honour", "west"),
            Tile("circles", 1),
        ])

        result = ValuationAlgorithm().optimal_discards(hand)
        codes = sorted(tile["code"] for tile in result["discards"])

        # More than one discard ties for the best score.
        self.assertGreater(len(result["discards"]), 1)
        self.assertEqual(codes, ["C1", "Heast", "Hwest"])
        # The single-recommendation helper returns one of the optimal tiles.
        single = ValuationAlgorithm().recommend_discard(hand)
        self.assertIn(single["discard"]["code"], codes)
        # No tile type is listed twice.
        self.assertEqual(len(codes), len(set(codes)))


class RandomHandApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="demo_user",
            password="demo_password_123",
        )

    def test_random_hand_requires_login(self):
        response = self.client.get("/api/game/random-hand/")

        self.assertEqual(response.status_code, 401)

    def test_logged_in_user_can_generate_random_hand(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/game/random-hand/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["tile_count"], 13)
        self.assertEqual(len(response.data["tiles"]), 13)
        self.assertIn("code", response.data["tiles"][0])


class RecommendDiscardApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="helper_user",
            password="helper_password_123",
        )

    def test_recommend_discard_requires_login(self):
        response = self.client.post(
            "/api/game/recommend-discard/",
            {"tiles": []},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_logged_in_user_can_get_discard_recommendation(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/game/recommend-discard/",
            {
                "tiles": [
                    {"suit": "bamboo", "value": 1},
                    {"suit": "bamboo", "value": 2},
                    {"suit": "bamboo", "value": 3},
                    {"suit": "circles", "value": 5},
                    {"suit": "circles", "value": 5},
                    {"suit": "circles", "value": 5},
                    {"suit": "characters", "value": 7},
                    {"suit": "characters", "value": 8},
                    {"suit": "characters", "value": 9},
                    {"suit": "honour", "value": "red"},
                    {"suit": "honour", "value": "red"},
                    {"suit": "bamboo", "value": 9},
                    {"suit": "circles", "value": 1},
                    {"suit": "circles", "value": 9},
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(response.data["discard"]["code"], ["B9", "C1"])
        self.assertIn("reasoning", response.data)

    def test_recommend_discard_rejects_wrong_tile_count(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/game/recommend-discard/",
            {
                "tiles": [
                    {"suit": "bamboo", "value": 1},
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)


class TrainerApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="trainer_user",
            password="trainer_password_123",
        )
        self.other = User.objects.create_user(
            username="other_user",
            password="other_password_123",
        )

    def test_trainer_new_requires_login(self):
        response = self.client.post("/api/game/trainer/new/")

        self.assertEqual(response.status_code, 401)

    def test_trainer_new_returns_fourteen_tiles_and_logs_move(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post("/api/game/trainer/new/")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data["tiles"]), 14)
        self.assertIn("move_id", response.data)
        # The answer must not be leaked in the challenge response.
        self.assertNotIn("correct_discard", response.data)

        move = Move.objects.get(id=response.data["move_id"])
        self.assertEqual(move.session.user, self.user)
        self.assertEqual(move.session.mode, Session.MODE_TRAINER)
        self.assertIsNone(move.user_discard)

    def test_trainer_submit_scores_and_records_result(self):
        self.client.force_authenticate(user=self.user)

        new_response = self.client.post("/api/game/trainer/new/")
        move_id = new_response.data["move_id"]
        tiles = new_response.data["tiles"]
        discard = tiles[0]

        submit_response = self.client.post(
            "/api/game/trainer/submit/",
            {
                "move_id": move_id,
                "discard": {"suit": discard["suit"], "value": discard["value"]},
            },
            format="json",
        )

        self.assertEqual(submit_response.status_code, 200)
        self.assertIn("is_correct", submit_response.data)
        self.assertIn("correct_discard", submit_response.data)
        self.assertIn("feedback", submit_response.data)

        move = Move.objects.get(id=move_id)
        self.assertIsNotNone(move.user_discard)
        self.assertIsNotNone(move.correct_discard)
        self.assertEqual(move.is_correct, submit_response.data["is_correct"])

    def test_trainer_submit_marks_optimal_discard_correct(self):
        # A near-complete hand with one obvious isolated tile (C1) to drop.
        self.client.force_authenticate(user=self.user)
        session = Session.objects.create(user=self.user, mode=Session.MODE_TRAINER)
        hand = [
            {"suit": "bamboo", "value": 1},
            {"suit": "bamboo", "value": 2},
            {"suit": "bamboo", "value": 3},
            {"suit": "circles", "value": 5},
            {"suit": "circles", "value": 5},
            {"suit": "circles", "value": 5},
            {"suit": "characters", "value": 7},
            {"suit": "characters", "value": 8},
            {"suit": "characters", "value": 9},
            {"suit": "honour", "value": "red"},
            {"suit": "honour", "value": "red"},
            {"suit": "bamboo", "value": 4},
            {"suit": "bamboo", "value": 5},
            {"suit": "circles", "value": 1},
        ]
        move = Move.objects.create(session=session, hand=hand)

        response = self.client.post(
            "/api/game/trainer/submit/",
            {"move_id": move.id, "discard": {"suit": "circles", "value": 1}},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_correct"])

    def test_trainer_submit_rejects_tile_not_in_hand(self):
        self.client.force_authenticate(user=self.user)
        new_response = self.client.post("/api/game/trainer/new/")
        move_id = new_response.data["move_id"]

        # honour 'white' may or may not be present; pick a tile guaranteed absent
        # by using an impossible-but-valid honour only if missing. Instead, drain
        # the hand of a known tile by choosing one and submitting twice.
        response = self.client.post(
            "/api/game/trainer/submit/",
            {"move_id": move_id, "discard": {"suit": "bamboo", "value": 99}},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_trainer_submit_blocks_double_answer(self):
        self.client.force_authenticate(user=self.user)
        new_response = self.client.post("/api/game/trainer/new/")
        move_id = new_response.data["move_id"]
        discard = new_response.data["tiles"][0]
        payload = {
            "move_id": move_id,
            "discard": {"suit": discard["suit"], "value": discard["value"]},
        }

        self.client.post("/api/game/trainer/submit/", payload, format="json")
        second = self.client.post("/api/game/trainer/submit/", payload, format="json")

        self.assertEqual(second.status_code, 400)

    def test_trainer_user_cannot_submit_another_users_move(self):
        self.client.force_authenticate(user=self.user)
        new_response = self.client.post("/api/game/trainer/new/")
        move_id = new_response.data["move_id"]
        discard = new_response.data["tiles"][0]

        self.client.force_authenticate(user=self.other)
        response = self.client.post(
            "/api/game/trainer/submit/",
            {
                "move_id": move_id,
                "discard": {"suit": discard["suit"], "value": discard["value"]},
            },
            format="json",
        )

        self.assertEqual(response.status_code, 404)

    def test_trainer_history_reports_accuracy(self):
        self.client.force_authenticate(user=self.user)
        for _ in range(2):
            new_response = self.client.post("/api/game/trainer/new/")
            discard = new_response.data["tiles"][0]
            self.client.post(
                "/api/game/trainer/submit/",
                {
                    "move_id": new_response.data["move_id"],
                    "discard": {"suit": discard["suit"], "value": discard["value"]},
                },
                format="json",
            )

        response = self.client.get("/api/game/trainer/history/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_attempts"], 2)
        self.assertIn("accuracy", response.data)
        self.assertEqual(len(response.data["attempts"]), 2)


class WinCheckerTests(TestCase):
    def setUp(self):
        self.checker = WinChecker()

    def test_standard_win_with_chows_pongs_and_pair(self):
        # 234B chow, 666C pong, 789K chow, East pong, Red pair = 14 tiles.
        hand = tiles(
            "B", 2, "B", 3, "B", 4,
            "C", 6, "C", 6, "C", 6,
            "K", 7, "K", 8, "K", 9,
            "H", "east", "H", "east", "H", "east",
            "H", "red", "H", "red",
        )
        result = self.checker.check(hand)
        self.assertTrue(result["is_winning"])
        self.assertEqual(result["pattern"], "standard")

    def test_standard_win_all_chows(self):
        # 123B 123B 456C 789K + 5C pair.
        hand = tiles(
            "B", 1, "B", 2, "B", 3,
            "B", 1, "B", 2, "B", 3,
            "C", 4, "C", 5, "C", 6,
            "K", 7, "K", 8, "K", 9,
            "C", 9, "C", 9,
        )
        result = self.checker.check(hand)
        self.assertTrue(result["is_winning"])
        self.assertEqual(result["pattern"], "standard")

    def test_seven_pairs(self):
        hand = tiles(
            "B", 1, "B", 1,
            "B", 5, "B", 5,
            "C", 2, "C", 2,
            "C", 9, "C", 9,
            "K", 3, "K", 3,
            "K", 7, "K", 7,
            "H", "white", "H", "white",
        )
        result = self.checker.check(hand)
        self.assertTrue(result["is_winning"])
        self.assertEqual(result["pattern"], "seven_pairs")

    def test_thirteen_orphans(self):
        # One of every terminal + honour, with East duplicated.
        hand = tiles(
            "B", 1, "B", 9,
            "C", 1, "C", 9,
            "K", 1, "K", 9,
            "H", "east", "H", "south", "H", "west", "H", "north",
            "H", "red", "H", "green", "H", "white",
            "H", "east",
        )
        result = self.checker.check(hand)
        self.assertTrue(result["is_winning"])
        self.assertEqual(result["pattern"], "thirteen_orphans")

    def test_incomplete_hand_is_not_a_win(self):
        # A close-but-not-complete hand (no valid pair + four melds).
        hand = tiles(
            "B", 1, "B", 2, "B", 4,
            "C", 6, "C", 6, "C", 7,
            "K", 7, "K", 8, "K", 9,
            "H", "east", "H", "south", "H", "west",
            "H", "red", "H", "green",
        )
        result = self.checker.check(hand)
        self.assertFalse(result["is_winning"])
        self.assertIsNone(result["pattern"])

    def test_wrong_tile_count_is_not_a_win(self):
        hand = tiles("B", 1, "B", 1)
        self.assertFalse(self.checker.check(hand)["is_winning"])

    def test_honours_cannot_form_a_chow(self):
        # East-South-West is not a meld; this hand should not be a standard win.
        hand = tiles(
            "H", "east", "H", "south", "H", "west",
            "B", 1, "B", 2, "B", 3,
            "C", 4, "C", 5, "C", 6,
            "K", 7, "K", 8, "K", 9,
            "B", 5, "B", 5,
        )
        result = self.checker.check(hand)
        self.assertFalse(result["is_winning"])


class CheckWinApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="win_user",
            password="win_password_123",
        )
        self.winning_payload = {
            "tiles": [
                {"suit": "bamboo", "value": 2},
                {"suit": "bamboo", "value": 3},
                {"suit": "bamboo", "value": 4},
                {"suit": "circles", "value": 6},
                {"suit": "circles", "value": 6},
                {"suit": "circles", "value": 6},
                {"suit": "characters", "value": 7},
                {"suit": "characters", "value": 8},
                {"suit": "characters", "value": 9},
                {"suit": "honour", "value": "east"},
                {"suit": "honour", "value": "east"},
                {"suit": "honour", "value": "east"},
                {"suit": "honour", "value": "red"},
                {"suit": "honour", "value": "red"},
            ]
        }

    def test_check_win_requires_login(self):
        response = self.client.post(
            "/api/game/check-win/", self.winning_payload, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_check_win_detects_winning_hand(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/game/check-win/", self.winning_payload, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_winning"])
        self.assertEqual(response.data["pattern"], "standard")

    def test_check_win_detects_non_winning_hand(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "tiles": [
                {"suit": "bamboo", "value": 1},
                {"suit": "bamboo", "value": 2},
                {"suit": "bamboo", "value": 4},
                {"suit": "circles", "value": 6},
                {"suit": "circles", "value": 6},
                {"suit": "circles", "value": 7},
                {"suit": "characters", "value": 7},
                {"suit": "characters", "value": 8},
                {"suit": "characters", "value": 9},
                {"suit": "honour", "value": "east"},
                {"suit": "honour", "value": "south"},
                {"suit": "honour", "value": "west"},
                {"suit": "honour", "value": "red"},
                {"suit": "honour", "value": "green"},
            ]
        }
        response = self.client.post("/api/game/check-win/", payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["is_winning"])
        self.assertIsNone(response.data["pattern"])

    def test_check_win_rejects_wrong_tile_count(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/game/check-win/",
            {"tiles": [{"suit": "bamboo", "value": 1}]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class KongTests(TestCase):
    def setUp(self):
        self.checker = WinChecker()

    def test_standard_win_with_a_kong_has_fifteen_tiles(self):
        # Kong of 8K, pong of 6C, chow 234B, chow 678B, pair of Red = 15 tiles.
        hand = tiles(
            "K", 8, "K", 8, "K", 8, "K", 8,
            "C", 6, "C", 6, "C", 6,
            "B", 2, "B", 3, "B", 4,
            "B", 6, "B", 7, "B", 8,
            "H", "red", "H", "red",
        )
        result = self.checker.check(hand)
        self.assertTrue(result["is_winning"])
        self.assertEqual(result["pattern"], "standard")
        meld_types = [meld["type"] for meld in result["melds"]]
        self.assertIn("kong", meld_types)

    def test_declare_kong_sets_tiles_aside_and_redraws(self):
        hand = Hand(tiles("B", 5, "B", 5, "B", 5, "B", 5, "C", 1, "C", 2))
        deck = Deck()
        deck.shuffle()
        before = len(hand.tiles)

        replacement = hand.declare_kong("bamboo", 5, deck)

        self.assertIsNotNone(replacement)
        self.assertFalse(replacement.is_bonus)
        self.assertEqual(len(hand.declared_kongs), 1)
        self.assertEqual(len(hand.declared_kongs[0]), 4)
        # Four tiles removed, one replacement drawn.
        self.assertEqual(len(hand.tiles), before - 4 + 1)

    def test_declare_kong_without_four_matching_tiles_raises(self):
        hand = Hand(tiles("B", 5, "B", 5, "B", 5, "C", 1))
        with self.assertRaises(ValueError):
            hand.declare_kong("bamboo", 5, Deck())

    def test_declared_kong_is_a_concealed_locked_meld(self):
        hand = Hand(tiles("B", 5, "B", 5, "B", 5, "B", 5, "C", 1))
        hand.declare_kong("bamboo", 5, Deck())

        self.assertEqual(len(hand.melds), 1)
        self.assertEqual(hand.melds[0].kind, "kong")
        self.assertFalse(hand.melds[0].claimed)  # self-declared = concealed


class ClaimMeldTests(TestCase):
    def test_claim_pong_exposes_and_locks_the_meld(self):
        hand = Hand(tiles("C", 5, "C", 5, "B", 1, "B", 2))
        meld = hand.claim_pong("circles", 5)

        self.assertEqual(meld.kind, "pong")
        self.assertTrue(meld.claimed)          # claimed from a discard
        self.assertFalse(meld.is_concealed)    # so it is exposed
        self.assertEqual(len(meld.tiles), 3)
        self.assertEqual(len(hand.melds), 1)
        # The two matching tiles left the rearrangeable concealed hand.
        self.assertFalse(
            any(t.suit == "circles" and t.value == 5 for t in hand.tiles)
        )

    def test_claim_pong_without_two_matching_tiles_raises(self):
        hand = Hand(tiles("C", 5, "B", 1, "B", 2))
        with self.assertRaises(ValueError):
            hand.claim_pong("circles", 5)

    def test_claim_chow_uses_two_concealed_tiles(self):
        hand = Hand(tiles("B", 3, "B", 4, "C", 1))
        meld = hand.claim_chow("bamboo", 3, claimed_value=5)

        self.assertEqual(meld.kind, "chow")
        self.assertTrue(meld.claimed)
        self.assertEqual([t.value for t in meld.tiles], [3, 4, 5])
        # B3 and B4 were consumed from the concealed hand.
        self.assertEqual(
            [t for t in hand.tiles if t.suit == "bamboo"], []
        )

    def test_claim_kong_from_discard_is_exposed_and_redraws(self):
        hand = Hand(tiles("K", 8, "K", 8, "K", 8, "C", 1))
        deck = Deck()
        deck.shuffle()
        meld = hand.claim_kong("characters", 8, deck)

        self.assertEqual(meld.kind, "kong")
        self.assertTrue(meld.claimed)
        self.assertEqual(len(meld.tiles), 4)
        # 3 tiles removed, 1 replacement drawn (started with C1 + 3x K8 = 4).
        self.assertEqual(len(hand.tiles), 2)

    def test_to_dict_exposes_claimed_flag(self):
        hand = Hand(tiles("C", 5, "C", 5, "B", 1, "B", 1, "B", 1))
        hand.claim_pong("circles", 5)
        data = hand.to_dict()

        self.assertEqual(len(data["melds"]), 1)
        self.assertTrue(data["melds"][0]["claimed"])
        self.assertFalse(data["melds"][0]["concealed"])


class SoloGameTests(TestCase):
    def test_start_deals_four_hands_then_dealer_draws(self):
        game = SoloGame(human_seat="east")
        game.start()

        # Four seated players in wind order, no bonus tiles in concealed hands.
        self.assertEqual([p.seat_wind for p in game.players], list(SEAT_WINDS))
        for player in game.players:
            self.assertTrue(all(not t.is_bonus for t in player.hand.tiles))

        # Everyone is dealt 13; start() advances to the dealer's turn, so the
        # current player has drawn to 14 and is awaiting a discard.
        if game.result is None:
            current = game.current_index
            self.assertEqual(len(game.players[current].hand.tiles), 14)
            for index, player in enumerate(game.players):
                if index != current:
                    self.assertEqual(len(player.hand.tiles), 13)

    def test_human_dealer_starts_with_fourteen_awaiting_discard(self):
        game = SoloGame(human_seat="east")  # East is dealer and human
        game.start()

        # After start, play advances to the human's turn: they've drawn (14)
        # and the game is waiting for their discard.
        if game.result is None:
            self.assertTrue(game.public_state()["is_human_turn"])
            self.assertEqual(game.phase, "discard")
            self.assertEqual(len(game.players[game.human_index()].hand.tiles), 14)

    def test_opponents_hands_hidden_until_game_over(self):
        game = SoloGame(human_seat="east")
        game.start()
        state = game.public_state()

        for player_state in state["players"]:
            if player_state["is_human"]:
                self.assertIsNotNone(player_state["tiles"])
            elif state["result"] is None:
                self.assertIsNone(player_state["tiles"])  # opponents concealed

    def test_full_game_runs_to_completion_without_error(self):
        import random

        random.seed(0)
        game = SoloGame(human_seat="east")
        game.start()

        # Simulate the human always discarding their first tile; the engine
        # plays the AI seats. The game must terminate (win or washout).
        guard = 0
        while game.result is None and guard < 500:
            guard += 1
            if game.phase == "claim":
                game.human_pass_claim()  # dumb human never claims
                continue
            human = game.players[game.human_index()]
            tile = human.hand.tiles[0]
            game.human_discard(tile.suit, tile.value)

        self.assertIsNotNone(game.result)
        self.assertIn(game.result, ("win", "washout"))
        self.assertEqual(game.phase, "over")

    def test_concealed_tiles_never_include_bonus_during_play(self):
        import random

        random.seed(1)
        game = SoloGame(human_seat="east")
        game.start()

        guard = 0
        while game.result is None and guard < 500:
            guard += 1
            for player in game.players:
                self.assertTrue(all(not t.is_bonus for t in player.hand.tiles))
            if game.phase == "claim":
                game.human_pass_claim()
                continue
            human = game.players[game.human_index()]
            tile = human.hand.tiles[0]
            game.human_discard(tile.suit, tile.value)

    def test_washout_triggers_at_sixteen_tile_reserve(self):
        from .solo import WALL_RESERVE

        game = SoloGame(human_seat="east")
        game.start()

        # Leave exactly RESERVE + 1 plain (non-bonus) tiles in the wall.
        game.deck.tiles = [Tile("bamboo", 5) for _ in range(WALL_RESERVE + 1)]
        game.phase = "draw"
        game.result = None

        self.assertIsNotNone(game._draw_current())  # 17 -> draw allowed, 16 left
        self.assertIsNone(game._draw_current())     # 16 reserve -> washout
        self.assertEqual(game.result, "washout")

    def test_self_draw_win_is_detected(self):
        # Force the human into a complete hand, then confirm the engine flags it.
        game = SoloGame(human_seat="east")
        winning = tiles(
            "B", 2, "B", 3, "B", 4,
            "C", 6, "C", 6, "C", 6,
            "K", 7, "K", 8, "K", 9,
            "H", "east", "H", "east", "H", "east",
            "H", "red", "H", "red",
        )
        game.players[0].hand.tiles = winning
        self.assertTrue(game._is_winning(game.players[0]))

    def _filler_13_with(self, *extra):
        """A concealed hand of 13 tiles containing `extra`, padded with distinct
        tiles that form no accidental sets."""
        pad = tiles(
            "B", 1, "B", 2, "B", 4, "B", 5, "B", 6,
            "B", 7, "B", 8, "B", 9, "K", 1, "K", 2, "K", 4,
        )
        hand = list(extra) + pad
        return hand[:13]

    def test_human_can_claim_pong_off_a_discard(self):
        game = SoloGame(human_seat="east")
        game.players[0].hand.tiles = self._filler_13_with(*tiles("C", 3, "C", 3))

        # South (an AI) discards a circles-3 the human holds two of.
        game.current_index = 1
        discard = Tile("circles", 3)
        game.last_discard = discard
        game.discards.append((1, discard))
        game._open_claims()

        self.assertEqual(game.phase, "claim")
        self.assertIn("pong", game.pending_claim["options"]["actions"])

        game.human_claim("pong")
        self.assertEqual(game.current_index, 0)     # turn jumps to the claimer
        self.assertEqual(game.phase, "discard")     # who must now discard
        melds = game.players[0].hand.melds
        self.assertTrue(any(m.kind == "pong" and m.claimed for m in melds))

    def test_chow_is_only_offered_to_the_next_seat(self):
        discard = Tile("circles", 3)

        # North (index 3) discards, so East (the human, index 0) is next and may Chow.
        game = SoloGame(human_seat="east")
        game.players[0].hand.tiles = self._filler_13_with(*tiles("C", 4, "C", 5))
        game.current_index = 3
        game.last_discard = discard
        game.discards.append((3, discard))
        game._open_claims()
        self.assertEqual(game.phase, "claim")
        self.assertIn("chow", game.pending_claim["options"]["actions"])
        self.assertIn(3, game.pending_claim["options"]["chow_runs"])

        game.human_claim("chow", low_value=3)
        self.assertEqual(game.current_index, 0)
        self.assertTrue(any(m.kind == "chow" for m in game.players[0].hand.melds))

        # If South (index 1) discards instead, the human is not next and cannot Chow.
        game2 = SoloGame(human_seat="east")
        game2.players[0].hand.tiles = self._filler_13_with(*tiles("C", 4, "C", 5))
        game2.current_index = 1
        game2.last_discard = discard
        game2.discards.append((1, discard))
        game2._open_claims()
        # No claim was possible, so the turn simply advanced.
        self.assertNotEqual(game2.phase, "claim")

    def test_ai_auto_claims_an_honour_pong(self):
        game = SoloGame(human_seat="east")
        game.players[2].hand.tiles = self._filler_13_with(*tiles("H", "green", "H", "green"))

        # South (index 1) discards a green dragon; West (index 2) wants the Pong.
        game.current_index = 1
        discard = Tile("honour", "green")
        game.last_discard = discard
        game.discards.append((1, discard))
        game._open_claims()

        self.assertNotEqual(game.phase, "claim")   # AI resolves without the human
        self.assertEqual(game.current_index, 2)
        self.assertTrue(any(m.kind == "pong" for m in game.players[2].hand.melds))

    def test_ron_win_on_discard_is_detected_and_scored(self):
        game = SoloGame(human_seat="east", round_wind="east")
        # 234B, 666C, 789K, East pair, Red pair -> waiting on a third East.
        game.players[0].hand.tiles = tiles(
            "B", 2, "B", 3, "B", 4,
            "C", 6, "C", 6, "C", 6,
            "K", 7, "K", 8, "K", 9,
            "H", "east", "H", "east",
            "H", "red", "H", "red",
        )
        game.current_index = 1  # South discards the winning East
        discard = Tile("honour", "east")
        game.last_discard = discard
        game.discards.append((1, discard))
        game._open_claims()

        self.assertEqual(game.phase, "claim")
        self.assertIn("win", game.pending_claim["options"]["actions"])

        game.human_claim("win")
        self.assertEqual(game.result, "win")
        self.assertEqual(game.win_type, "ron")
        self.assertEqual(game.winner_index, 0)
        # East pong scores seat wind + round wind = 2 tai; with no bonus tiles
        # there is nothing extra, so hand and total both come to 2.
        self.assertTrue(game.win_score["is_valid_win"])
        self.assertEqual(game.win_score["hand_tai"], 2)
        self.assertEqual(game.win_score["total_tai"], 2)
        labels = [row["label"] for row in game.win_score["breakdown"]]
        self.assertTrue(any("Seat wind" in label for label in labels))

    def test_self_draw_win_is_scored_in_public_state(self):
        game = SoloGame(human_seat="east", round_wind="east")
        game.players[0].hand.tiles = tiles(
            "B", 2, "B", 3, "B", 4,
            "C", 6, "C", 6, "C", 6,
            "K", 7, "K", 8, "K", 9,
            "H", "east", "H", "east", "H", "east",
            "H", "red", "H", "red",
        )
        game._declare_win(0, "self_draw", Tile("honour", "red"))
        state = game.public_state()
        self.assertIsNotNone(state["win"])
        self.assertEqual(state["win"]["hand_tai"], 2)
        self.assertEqual(state["win"]["win_type"], "self_draw")
        self.assertTrue(len(state["win"]["breakdown"]) >= 1)


class SoloApiTests(TestCase):
    def setUp(self):
        from .views import _SOLO_GAMES

        _SOLO_GAMES.clear()  # in-memory store persists across tests; reset it
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="solo_user", password="solo_password_123"
        )

    def test_solo_endpoints_require_login(self):
        self.assertEqual(self.client.post("/api/game/solo/new/").status_code, 401)
        self.assertEqual(self.client.get("/api/game/solo/state/").status_code, 401)

    def test_state_is_404_before_a_game_starts(self):
        self.client.force_authenticate(user=self.user)
        self.assertEqual(self.client.get("/api/game/solo/state/").status_code, 404)

    def test_new_game_deals_and_returns_state(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/game/solo/new/")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data["players"]), 4)
        # Opponents' concealed tiles stay hidden; the human's are revealed.
        human = next(p for p in response.data["players"] if p["is_human"])
        self.assertIsNotNone(human["tiles"])
        for player in response.data["players"]:
            if not player["is_human"] and response.data["result"] is None:
                self.assertIsNone(player["tiles"])

    def test_human_can_discard_and_state_advances(self):
        self.client.force_authenticate(user=self.user)
        start = self.client.post("/api/game/solo/new/").data
        if start["result"] is not None:
            return  # extremely rare instant end; nothing to discard

        human = next(p for p in start["players"] if p["is_human"])
        tile = human["tiles"][0]
        response = self.client.post(
            "/api/game/solo/discard/",
            {"suit": tile["suit"], "value": tile["value"]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        # After discarding, the engine has run the AI seats and either returned
        # to the human's turn, opened a claim window, or ended the game.
        self.assertTrue(
            response.data["is_human_turn"]
            or response.data["awaiting_claim"]
            or response.data["result"] is not None
        )

    def test_finished_solo_game_updates_profile(self):
        from users.models import Profile

        from .views import _record_solo_result

        Profile.objects.get_or_create(user=self.user)

        # A human win: one game played, one won.
        game = SoloGame(human_seat="east")
        game.result = "win"
        game.winner_index = game.human_index()
        _record_solo_result(self.user, game)

        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.games_played, 1)
        self.assertEqual(profile.games_won, 1)
        self.assertEqual(profile.win_rate, 100.0)

        # Recording the same finished game again must not double count.
        _record_solo_result(self.user, game)
        profile.refresh_from_db()
        self.assertEqual(profile.games_played, 1)

        # A washout counts as a game played but not won.
        washout = SoloGame(human_seat="east")
        washout.result = "washout"
        _record_solo_result(self.user, washout)
        profile.refresh_from_db()
        self.assertEqual(profile.games_played, 2)
        self.assertEqual(profile.games_won, 1)
        self.assertEqual(profile.win_rate, 50.0)


class ScoreCalculatorTests(TestCase):
    def _winning_wind_hand(self):
        # 234B chow, 666C pong, 789K chow, East pong, Red pair.
        return tiles(
            "B", 2, "B", 3, "B", 4,
            "C", 6, "C", 6, "C", 6,
            "K", 7, "K", 8, "K", 9,
            "H", "east", "H", "east", "H", "east",
            "H", "red", "H", "red",
        )

    def test_seat_and_round_wind_pong_each_score_one_tai(self):
        win = WinChecker().check(self._winning_wind_hand())
        score = ScoreCalculator(seat_wind="east", round_wind="east").score(win)

        self.assertTrue(score["is_valid_win"])
        self.assertEqual(score["hand_tai"], 2)  # seat wind + round wind

    def test_flower_alone_meets_the_minimum_tai(self):
        # All chows, no winds/dragons/flush -> 0 hand tai.
        hand = tiles(
            "B", 1, "B", 2, "B", 3,
            "B", 1, "B", 2, "B", 3,
            "C", 4, "C", 5, "C", 6,
            "K", 7, "K", 8, "K", 9,
            "C", 9, "C", 9,
        )
        win = WinChecker().check(hand)
        calc = ScoreCalculator(seat_wind="east", round_wind="east")

        # With no bonus tiles the hand is worth 0 tai and cannot win.
        plain = calc.score(win, [])
        self.assertEqual(plain["hand_tai"], 0)
        self.assertFalse(plain["is_valid_win"])

        # The seat flower adds 1 tai, which now meets the minimum on its own.
        flower = Tile("flower", "red_1", is_bonus=True)  # East's seat flower
        with_flower = calc.score(win, [flower])
        self.assertEqual(with_flower["hand_tai"], 0)
        self.assertEqual(with_flower["bonus_tai"], 1)
        self.assertEqual(with_flower["total_tai"], 1)
        self.assertTrue(with_flower["is_valid_win"])

    def test_full_flush_all_pongs_scores(self):
        # Four bamboo pongs + bamboo pair: full flush + all pongs.
        hand = tiles(
            "B", 1, "B", 1, "B", 1,
            "B", 2, "B", 2, "B", 2,
            "B", 3, "B", 3, "B", 3,
            "B", 4, "B", 4, "B", 4,
            "B", 5, "B", 5,
        )
        win = WinChecker().check(hand)
        score = ScoreCalculator(seat_wind="east", round_wind="east").score(win)

        labels = [item["label"] for item in score["breakdown"]]
        self.assertIn("Full Flush", labels)
        self.assertIn("All Pongs", labels)
        self.assertEqual(score["hand_tai"], 6)
        self.assertTrue(score["is_valid_win"])

    def _pinghu_hand(self):
        # Four chows across two suits plus a characters pair (no flush, no
        # winds): 123B 456B 123C 456C 55K.
        return tiles(
            "B", 1, "B", 2, "B", 3,
            "B", 4, "B", 5, "B", 6,
            "C", 1, "C", 2, "C", 3,
            "C", 4, "C", 5, "C", 6,
            "K", 5, "K", 5,
        )

    def test_pinghu_scores_four_tai_on_self_draw(self):
        win = WinChecker().check(self._pinghu_hand())
        score = ScoreCalculator("east", "east").score(win, [], win_type="self_draw")

        labels = [item["label"] for item in score["breakdown"]]
        self.assertIn("Pinghu", labels)
        self.assertEqual(score["hand_tai"], 4)
        self.assertTrue(score["is_valid_win"])

    def test_pinghu_on_a_discard_needs_a_two_sided_wait(self):
        win = WinChecker().check(self._pinghu_hand())

        # Won on 6 bamboo, completing 456B from a 45 wait (2 or 5... i.e. 3/6):
        # a two-sided wait, so Pinghu stands.
        two_sided = ScoreCalculator("east", "east").score(
            win, [], win_type="ron", winning_tile=Tile("bamboo", 6)
        )
        self.assertIn("Pinghu", [i["label"] for i in two_sided["breakdown"]])
        self.assertEqual(two_sided["hand_tai"], 4)

        # Won on 3 bamboo, completing 123B from a 12 edge wait (only a 3 works):
        # one-sided, so no Pinghu and, with no other tai, not a valid win.
        one_sided = ScoreCalculator("east", "east").score(
            win, [], win_type="ron", winning_tile=Tile("bamboo", 3)
        )
        self.assertNotIn("Pinghu", [i["label"] for i in one_sided["breakdown"]])
        self.assertEqual(one_sided["hand_tai"], 0)
        self.assertFalse(one_sided["is_valid_win"])

    def test_smelly_pinghu_scores_one_tai_and_keeps_flower(self):
        win = WinChecker().check(self._pinghu_hand())
        flower = Tile("flower", "red_1", is_bonus=True)  # East's seat flower
        score = ScoreCalculator("east", "east").score(
            win, [flower], win_type="self_draw"
        )

        labels = [item["label"] for item in score["breakdown"]]
        self.assertIn("Smelly Pinghu", labels)
        self.assertNotIn("Pinghu", labels)
        self.assertEqual(score["hand_tai"], 1)   # smelly pinghu only
        self.assertEqual(score["bonus_tai"], 1)  # the seat flower still counts
        self.assertTrue(score["is_valid_win"])

    def test_pinghu_not_awarded_without_win_context(self):
        # The static score-hand path has no self-draw/Ron context, so Pinghu is
        # not granted (and this clean all-chow hand is otherwise 0 tai).
        win = WinChecker().check(self._pinghu_hand())
        score = ScoreCalculator("east", "east").score(win, [])

        labels = [item["label"] for item in score["breakdown"]]
        self.assertNotIn("Pinghu", labels)
        self.assertNotIn("Smelly Pinghu", labels)
        self.assertFalse(score["is_valid_win"])


class ScoreHandApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="score_user",
            password="score_password_123",
        )
        self.wind_hand = [
            {"suit": "bamboo", "value": 2},
            {"suit": "bamboo", "value": 3},
            {"suit": "bamboo", "value": 4},
            {"suit": "circles", "value": 6},
            {"suit": "circles", "value": 6},
            {"suit": "circles", "value": 6},
            {"suit": "characters", "value": 7},
            {"suit": "characters", "value": 8},
            {"suit": "characters", "value": 9},
            {"suit": "honour", "value": "east"},
            {"suit": "honour", "value": "east"},
            {"suit": "honour", "value": "east"},
            {"suit": "honour", "value": "red"},
            {"suit": "honour", "value": "red"},
        ]

    def test_score_hand_requires_login(self):
        response = self.client.post(
            "/api/game/score-hand/", {"tiles": self.wind_hand}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_score_hand_scores_a_winning_wind_hand(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/game/score-hand/",
            {"tiles": self.wind_hand, "seat_wind": "east", "round_wind": "east"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["win"]["is_winning"])
        self.assertTrue(response.data["score"]["is_valid_win"])
        self.assertGreaterEqual(response.data["score"]["hand_tai"], 2)

    def test_score_hand_rejects_bad_seat_wind(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/game/score-hand/",
            {"tiles": self.wind_hand, "seat_wind": "dragon", "round_wind": "east"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_score_hand_rejects_wrong_tile_count(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/game/score-hand/",
            {"tiles": self.wind_hand[:5]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
