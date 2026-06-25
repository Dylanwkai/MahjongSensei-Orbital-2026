from collections import Counter

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .engine import (
    HONOUR_VALUES,
    NUMBERED_SUITS,
    Hand,
    HandGenerator,
    Tile,
    ValuationAlgorithm,
)


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


class RecommendDiscardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tile_data = request.data.get("tiles", [])

        if not isinstance(tile_data, list):
            return Response(
                {"error": "tiles must be a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(tile_data) != 13:
            return Response(
                {"error": "Hand must contain exactly 13 playable tiles."},
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
