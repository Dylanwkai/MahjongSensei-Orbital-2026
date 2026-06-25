from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MODULE_IDS, TUTORIAL_MODULES, TutorialProgress
from .serializers import (
    CompleteModuleSerializer,
    ModuleSerializer,
    TutorialProgressSerializer,
)


class ModuleListView(APIView):
    """GET /api/tutorial/modules/

    Returns the hardcoded module catalog with the current user's completion
    status merged in.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        progress_by_module = {
            row.module_id: row
            for row in TutorialProgress.objects.filter(user=request.user)
        }

        modules = []
        for module in sorted(TUTORIAL_MODULES, key=lambda m: m["order"]):
            row = progress_by_module.get(module["id"])
            modules.append(
                {
                    "id": module["id"],
                    "title": module["title"],
                    "description": module["description"],
                    "order": module["order"],
                    "completed": bool(row and row.completed),
                    "completed_at": row.completed_at if row else None,
                    "quiz_score": row.quiz_score if row else None,
                }
            )

        return Response(ModuleSerializer(modules, many=True).data)


class ProgressView(APIView):
    """GET /api/tutorial/progress/

    Returns this user's TutorialProgress rows.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = TutorialProgress.objects.filter(user=request.user).order_by("module_id")
        return Response(TutorialProgressSerializer(rows, many=True).data)


class CompleteModuleView(APIView):
    """POST /api/tutorial/complete/

    Body: { "module_id": "tiles", "quiz_score": 4 }
    Upserts a completed TutorialProgress row for (request.user, module_id).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CompleteModuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        module_id = serializer.validated_data["module_id"]
        quiz_score = serializer.validated_data.get("quiz_score")

        if module_id not in MODULE_IDS:
            return Response(
                {"error": f"Unknown module_id: {module_id}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        row, _created = TutorialProgress.objects.update_or_create(
            user=request.user,
            module_id=module_id,
            defaults={
                "completed": True,
                "completed_at": timezone.now(),
                "quiz_score": quiz_score,
            },
        )

        return Response(
            TutorialProgressSerializer(row).data,
            status=status.HTTP_200_OK,
        )
