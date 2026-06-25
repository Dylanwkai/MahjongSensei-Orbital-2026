from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .engine import Deck, Hand, HandEvaluator, HandGenerator, Tile, ValuationAlgorithm
from .models import Move, Session


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
