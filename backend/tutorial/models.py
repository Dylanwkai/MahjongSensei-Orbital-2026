from django.contrib.auth.models import User
from django.db import models


# Hardcoded catalog of tutorial modules. These do not need their own table —
# the module definitions are static content, and per-user completion is tracked
# by TutorialProgress rows keyed on module_id.
TUTORIAL_MODULES = [
    {
        "id": "tiles",
        "title": "Tile Recognition",
        "description": (
            "Learn to read every tile suit: bamboo, circles, characters, "
            "honours, flowers, and animals."
        ),
        "order": 1,
    },
    {
        "id": "melds",
        "title": "Meld Types",
        "description": "Understand how Pong, Kong, and Chow groups are formed.",
        "order": 2,
    },
    {
        "id": "winning-hands",
        "title": "Winning Hands",
        "description": (
            "Put it together: four melds plus a pair make a standard winning hand."
        ),
        "order": 3,
    },
]

MODULE_IDS = {module["id"] for module in TUTORIAL_MODULES}


class TutorialProgress(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tutorial_progress",
    )
    module_id = models.CharField(max_length=64)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    quiz_score = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "module_id")

    def __str__(self):
        status = "done" if self.completed else "in progress"
        return f"{self.user.username} - {self.module_id} ({status})"
