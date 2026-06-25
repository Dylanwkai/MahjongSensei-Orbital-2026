from rest_framework import serializers

from .models import TutorialProgress


class TutorialProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = TutorialProgress
        fields = [
            "id",
            "module_id",
            "completed",
            "completed_at",
            "quiz_score",
        ]
        read_only_fields = ["id", "completed", "completed_at"]


class ModuleSerializer(serializers.Serializer):
    """Serializes a hardcoded module catalog entry with the current user's
    completion status merged in."""

    id = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    order = serializers.IntegerField()
    completed = serializers.BooleanField()
    completed_at = serializers.DateTimeField(allow_null=True)
    quiz_score = serializers.IntegerField(allow_null=True)


class CompleteModuleSerializer(serializers.Serializer):
    module_id = serializers.CharField()
    quiz_score = serializers.IntegerField(required=False, allow_null=True)
