from collections import Counter

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .engine import (
    ANIMAL_VALUES,
    FLOWER_VALUES,
    HONOUR_VALUES,
    NUMBERED_SUITS,
    WINDS,
    Hand,
    HandEvaluator,
    HandGenerator,
    ScoreCalculator,
    Tile,
    ValuationAlgorithm,
    WinChecker,
)
from users.models import Profile

from .models import Move, Session
from .solo import SoloGame


class RandomHandView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hand = HandGenerator().generate_random_hand()
        return Response(hand.to_dict())


def parse_tile(tile_data):
    suit = tile_data.get("suit")
    value = tile_data.get("value")

    if suit in NUMBERED_SUITS:
        if not isinstance(value, int) or value < 1 or value > 9:
            raise ValueError("Numbered tiles must have an integer value from 1 to 9.")
        return Tile(suit, value)

    if suit == "honour":
        if value not in HONOUR_VALUES:
            raise ValueError("Honour tile value is invalid.")
        return Tile(suit, value)

    raise ValueError("Only suited and honour tiles are allowed in a hand.")


def parse_bonus_tile(tile_data):
    suit = tile_data.get("suit")
    value = tile_data.get("value")

    if suit == "flower" and value in FLOWER_VALUES:
        return Tile("flower", value, is_bonus=True)
    if suit == "animal" and value in ANIMAL_VALUES:
        return Tile("animal", value, is_bonus=True)

    raise ValueError("Bonus tiles must be valid flower or animal tiles.")


class RecommendDiscardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tile_data = request.data.get("tiles", [])

        if not isinstance(tile_data, list):
            return Response(
                {"error": "tiles must be a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(tile_data) != 14:
            return Response(
                {"error": "Hand must contain exactly 14 playable tiles."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tiles = [parse_tile(tile) for tile in tile_data]
        except (AttributeError, ValueError) as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tile_counts = Counter((tile.suit, tile.value) for tile in tiles)
        if any(count > 4 for count in tile_counts.values()):
            return Response(
                {"error": "A hand cannot contain more than 4 copies of the same tile."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hand = Hand(tiles)
        recommendation = ValuationAlgorithm().recommend_discard(hand)

        return Response(recommendation)


class CheckWinView(APIView):
    """POST /api/game/check-win/

    Body: { "tiles": [ {suit, value}, ... ] } with exactly 14 playable tiles.
    Returns whether the hand is already a complete winning hand and, if so,
    which pattern (standard / seven_pairs / thirteen_orphans).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        tile_data = request.data.get("tiles", [])

        if not isinstance(tile_data, list):
            return Response(
                {"error": "tiles must be a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not 14 <= len(tile_data) <= 18:
            return Response(
                {"error": "A winning hand must contain 14 to 18 playable tiles "
                          "(14, plus one extra per Kong)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tiles = [parse_tile(tile) for tile in tile_data]
        except (AttributeError, ValueError) as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tile_counts = Counter((tile.suit, tile.value) for tile in tiles)
        if any(count > 4 for count in tile_counts.values()):
            return Response(
                {"error": "A hand cannot contain more than 4 copies of the same tile."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(WinChecker().check(tiles))


class ScoreHandView(APIView):
    """POST /api/game/score-hand/

    Body: {
        "tiles": [ {suit, value}, ... ],          # 14-18 playable tiles
        "bonus_tiles": [ {suit, value}, ... ],    # optional flowers / animals
        "seat_wind": "east",                       # player's seat (position)
        "round_wind": "east"                       # prevailing wind
    }
    Checks the hand and, if it wins, scores it in tai (with the minimum-tai
    rule applied).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        tile_data = request.data.get("tiles", [])
        bonus_data = request.data.get("bonus_tiles", [])
        seat_wind = request.data.get("seat_wind", "east")
        round_wind = request.data.get("round_wind", "east")

        if not isinstance(tile_data, list) or not isinstance(bonus_data, list):
            return Response(
                {"error": "tiles and bonus_tiles must be lists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not 14 <= len(tile_data) <= 18:
            return Response(
                {"error": "Hand must contain 14 to 18 playable tiles."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if seat_wind not in WINDS or round_wind not in WINDS:
            return Response(
                {"error": "seat_wind and round_wind must be one of east/south/west/north."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tiles = [parse_tile(tile) for tile in tile_data]
            bonus_tiles = [parse_bonus_tile(tile) for tile in bonus_data]
        except (AttributeError, ValueError) as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tile_counts = Counter((tile.suit, tile.value) for tile in tiles)
        if any(count > 4 for count in tile_counts.values()):
            return Response(
                {"error": "A hand cannot contain more than 4 copies of the same tile."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        win = WinChecker().check(tiles)
        score = ScoreCalculator(seat_wind, round_wind).score(win, bonus_tiles)

        return Response({"win": win, "score": score})


# Interactive Trainer endpoints: deal a hand (new), score the user's discard
# and log it (submit), and list past attempts (history).

TRAINER_HAND_SIZE = 14


def tiles_from_dicts(tile_dicts):
    """Rebuild engine Tile objects from stored/posted tile dicts."""
    return [parse_tile(tile) for tile in tile_dicts]


def find_matching_tile(tiles, suit, value):
    """Return the first engine Tile in `tiles` matching suit/value, else None."""
    for tile in tiles:
        if tile.suit == suit and tile.value == value:
            return tile
    return None


TRAINER_DIFFICULTIES = ("easy", "medium", "hard")


class TrainerNewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        difficulty = request.data.get("difficulty") or request.query_params.get(
            "difficulty"
        )
        if difficulty not in TRAINER_DIFFICULTIES:
            difficulty = "medium"
        hand = HandGenerator().generate_random_hand(
            hand_size=TRAINER_HAND_SIZE, difficulty=difficulty
        )

        # Reuse the user's most recent trainer session, or start one. We avoid
        # get_or_create here because a user can legitimately have more than one
        # trainer session (e.g. concurrent "new hand" requests on mount), and
        # get_or_create raises MultipleObjectsReturned in that case.
        session = (
            Session.objects.filter(
                user=request.user,
                mode=Session.MODE_TRAINER,
            )
            .order_by("-created_at")
            .first()
        )
        if session is None:
            session = Session.objects.create(
                user=request.user,
                mode=Session.MODE_TRAINER,
            )

        tile_dicts = [tile.to_dict() for tile in hand.sorted_tiles()]
        bonus_dicts = [tile.to_dict() for tile in hand.bonus_tiles]
        move = Move.objects.create(
            session=session, hand=tile_dicts, difficulty=difficulty
        )

        return Response(
            {
                "move_id": move.id,
                "session_id": session.id,
                "tiles": tile_dicts,
                "bonus_tiles": bonus_dicts,
                "difficulty": difficulty,
            },
            status=status.HTTP_201_CREATED,
        )

    # Allow GET as a convenience for quickly fetching a fresh challenge.
    def get(self, request):
        return self.post(request)


class TrainerSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        move_id = request.data.get("move_id")
        discard_data = request.data.get("discard")

        if move_id is None or not isinstance(discard_data, dict):
            return Response(
                {"error": "move_id and a discard tile are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            move = Move.objects.get(id=move_id, session__user=request.user)
        except Move.DoesNotExist:
            return Response(
                {"error": "Challenge not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if move.is_submitted:
            return Response(
                {"error": "This challenge has already been answered."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            discard_tile = parse_tile(discard_data)
        except (AttributeError, ValueError) as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hand_tiles = tiles_from_dicts(move.hand)
        chosen = find_matching_tile(hand_tiles, discard_tile.suit, discard_tile.value)
        if chosen is None:
            return Response(
                {"error": "That tile is not in the dealt hand."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hand = Hand(hand_tiles)
        valuation = ValuationAlgorithm()
        recommendation = valuation.recommend_discard(hand)
        best_score = recommendation["score"]

        # Several tiles can be equally optimal, so collect all of them.
        optimal_discards = valuation.optimal_discards(hand)["discards"]

        evaluator = HandEvaluator()
        remaining = hand_tiles.copy()
        remaining.remove(chosen)
        user_score = evaluator.evaluate_hand(remaining)

        # A tie with the best score counts as correct, since several discards
        # can be equally good.
        is_correct = user_score == best_score

        move.user_discard = chosen.to_dict()
        move.correct_discard = recommendation["discard"]
        move.user_score = user_score
        move.best_score = best_score
        move.is_correct = is_correct
        move.save()

        optimal_labels = [tile["label"] for tile in optimal_discards]
        if is_correct:
            feedback = "Nice - that's an optimal discard."
        elif len(optimal_labels) == 1:
            feedback = (
                f"Not quite. The optimal discard is {optimal_labels[0]}. "
                + recommendation["reasoning"]
            )
        else:
            feedback = (
                "Not quite. Any of these is optimal: "
                f"{', '.join(optimal_labels)}. " + recommendation["reasoning"]
            )

        return Response(
            {
                "is_correct": is_correct,
                "your_discard": move.user_discard,
                "your_score": user_score,
                "correct_discard": move.correct_discard,
                "optimal_discards": optimal_discards,
                "best_score": best_score,
                "reasoning": recommendation["reasoning"],
                "feedback": feedback,
            }
        )


class TrainerHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        moves = Move.objects.filter(
            session__user=request.user,
            user_discard__isnull=False,
        ).order_by("-created_at")[:50]

        valuation = ValuationAlgorithm()
        attempts = []
        for move in moves:
            # Recompute the full set of optimal discards from the stored hand.
            # The evaluator is deterministic, so this matches what was shown at
            # submit time, and it also backfills older attempts.
            optimal = None
            if move.hand:
                try:
                    optimal = valuation.optimal_discards(
                        Hand(tiles_from_dicts(move.hand))
                    )["discards"]
                except (ValueError, KeyError, AttributeError):
                    optimal = None

            attempts.append(
                {
                    "move_id": move.id,
                    "is_correct": move.is_correct,
                    "difficulty": move.difficulty,
                    "hand": move.hand,
                    "your_discard": move.user_discard,
                    "correct_discard": move.correct_discard,
                    "optimal_discards": optimal,
                    "your_score": move.user_score,
                    "best_score": move.best_score,
                    "created_at": move.created_at,
                }
            )

        total = len(attempts)
        correct = sum(1 for attempt in attempts if attempt["is_correct"])
        accuracy = round(correct / total * 100, 1) if total else 0.0

        return Response(
            {
                "total_attempts": total,
                "correct": correct,
                "accuracy": accuracy,
                "attempts": attempts,
            }
        )


# Solo Play endpoints. The game is stateful so each user's SoloGame is kept in
# an in-memory dict, which means a game is lost if the server restarts. Results
# are not written to the profile yet.

_SOLO_GAMES = {}  # user_id -> SoloGame


def _get_solo_game(request):
    return _SOLO_GAMES.get(request.user.id)


def _record_solo_result(user, game):
    """When a solo game has just finished, count it once towards the player's
    profile: every finished game (win or washout) is a game played, and a win
    for the human seat is a game won."""
    if game is None or game.result is None:
        return
    if getattr(game, "_result_recorded", False):
        return

    profile, _ = Profile.objects.get_or_create(user=user)
    profile.games_played += 1
    if game.result == "win" and game.winner_index == game.human_index():
        profile.games_won += 1
    profile.win_rate = (
        round(profile.games_won / profile.games_played * 100, 1)
        if profile.games_played
        else 0.0
    )
    profile.save()
    game._result_recorded = True


class SoloNewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        game = SoloGame(human_seat="east")
        game.start()
        _SOLO_GAMES[request.user.id] = game
        _record_solo_result(request.user, game)  # in the rare instant-end case
        return Response(game.public_state(), status=status.HTTP_201_CREATED)


class SoloStateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        game = _get_solo_game(request)
        if game is None:
            return Response(
                {"error": "No active game. Start a new one."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(game.public_state())


class SoloDiscardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        game = _get_solo_game(request)
        if game is None:
            return Response(
                {"error": "No active game. Start a new one."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            game.human_discard(request.data.get("suit"), request.data.get("value"))
        except ValueError as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        _record_solo_result(request.user, game)
        return Response(game.public_state())


class SoloKongView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        game = _get_solo_game(request)
        if game is None:
            return Response(
                {"error": "No active game. Start a new one."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            game.human_declare_kong(request.data.get("suit"), request.data.get("value"))
        except ValueError as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        _record_solo_result(request.user, game)
        return Response(game.public_state())


class SoloClaimView(APIView):
    """POST /api/game/solo/claim/

    Body: { "action": "pong"|"kong"|"chow"|"win", "low_value": <int, chow only> }
    Claim the current discard. low_value picks which run to use for a Chow.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        game = _get_solo_game(request)
        if game is None:
            return Response(
                {"error": "No active game. Start a new one."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            game.human_claim(
                request.data.get("action"), low_value=request.data.get("low_value")
            )
        except ValueError as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        _record_solo_result(request.user, game)
        return Response(game.public_state())


class SoloPassView(APIView):
    """POST /api/game/solo/pass/  Pass on the current claim."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        game = _get_solo_game(request)
        if game is None:
            return Response(
                {"error": "No active game. Start a new one."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            game.human_pass_claim()
        except ValueError as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        _record_solo_result(request.user, game)
        return Response(game.public_state())


class SoloHintView(APIView):
    """GET /api/game/solo/hint/

    Suggest a discard for the human's current hand using the same valuation
    engine the AI seats use. Returns the recommended tile plus every equally
    optimal discard.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        game = _get_solo_game(request)
        if game is None:
            return Response(
                {"error": "No active game. Start a new one."},
                status=status.HTTP_404_NOT_FOUND,
            )

        human_index = game.human_index()
        if game.result is not None:
            return Response(
                {"error": "The game is over."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if game.phase != "discard" or game.current_index != human_index:
            return Response(
                {"error": "A hint is only available on your turn to discard."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hand = game.players[human_index].hand
        valuation = ValuationAlgorithm()
        recommendation = valuation.recommend_discard(hand)
        optimal = valuation.optimal_discards(hand)["discards"]

        return Response(
            {
                "discard": recommendation["discard"],
                "optimal_discards": optimal,
                "reasoning": recommendation["reasoning"],
            }
        )
