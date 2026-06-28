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


# ---------------------------------------------------------------------------
# Interactive Trainer (Feature 3)
#
# Flow:
#   1. POST /api/game/trainer/new/    -> generates a 14-tile hand, logs a pending
#      Move, and returns the tiles + move_id (without revealing the answer).
#   2. POST /api/game/trainer/submit/ -> the user picks a discard; the server
#      scores it against ValuationAlgorithm, records the result on the Move,
#      and returns immediate feedback.
#   3. GET  /api/game/trainer/history/ -> the user's past attempts.
# ---------------------------------------------------------------------------

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


class TrainerNewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        hand = HandGenerator().generate_random_hand(hand_size=TRAINER_HAND_SIZE)

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
        move = Move.objects.create(session=session, hand=tile_dicts)

        return Response(
            {
                "move_id": move.id,
                "session_id": session.id,
                "tiles": tile_dicts,
                "bonus_tiles": bonus_dicts,
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
        recommendation = ValuationAlgorithm().recommend_discard(hand)
        best_score = recommendation["score"]

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

        if is_correct:
            feedback = "Nice — that's an optimal discard."
        else:
            feedback = (
                f"Not quite. Discarding {recommendation['discard']['label']} keeps a "
                "stronger hand. " + recommendation["reasoning"]
            )

        return Response(
            {
                "is_correct": is_correct,
                "your_discard": move.user_discard,
                "your_score": user_score,
                "correct_discard": move.correct_discard,
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

        attempts = [
            {
                "move_id": move.id,
                "is_correct": move.is_correct,
                "your_discard": move.user_discard,
                "correct_discard": move.correct_discard,
                "your_score": move.user_score,
                "best_score": move.best_score,
                "created_at": move.created_at,
            }
            for move in moves
        ]

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


# ---------------------------------------------------------------------------
# Solo Play (Feature 4) — Steps 1-4.
#
# The game is stateful, so the SoloGame object is kept server-side, keyed by
# user, in a simple in-memory store. This is a prototype convenience: games are
# lost if the server restarts, and results are NOT yet written to the profile /
# stats (intentionally left unlinked for now).
# ---------------------------------------------------------------------------

_SOLO_GAMES = {}  # user_id -> SoloGame


def _get_solo_game(request):
    return _SOLO_GAMES.get(request.user.id)


class SoloNewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        game = SoloGame(human_seat="east")
        game.start()
        _SOLO_GAMES[request.user.id] = game
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
        return Response(game.public_state())
