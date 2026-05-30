from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .engine import HandGenerator


class RandomHandView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hand = HandGenerator().generate_random_hand()
        return Response(hand.to_dict())
