from django.contrib.auth.models import User
from django.db import models


class Session(models.Model):
    """A play session for a user, e.g. a Trainer run or (later) a Solo Play game."""

    MODE_TRAINER = "trainer"
    MODE_SOLO = "solo"
    MODE_CHOICES = (
        (MODE_TRAINER, "Trainer"),
        (MODE_SOLO, "Solo Play"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="game_sessions",
    )
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_TRAINER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def attempts(self):
        return self.moves.filter(user_discard__isnull=False).count()

    @property
    def correct_count(self):
        return self.moves.filter(is_correct=True).count()

    def __str__(self):
        return f"{self.user.username} - {self.mode} session #{self.pk}"


class Move(models.Model):
    """A single Trainer round: a generated hand, the user's discard, and the result."""

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="moves",
    )
    hand = models.JSONField()  # list of tile dicts presented to the user
    user_discard = models.JSONField(null=True, blank=True)
    correct_discard = models.JSONField(null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    user_score = models.IntegerField(null=True, blank=True)
    best_score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_submitted(self):
        return self.user_discard is not None

    def __str__(self):
        if not self.is_submitted:
            status = "pending"
        else:
            status = "correct" if self.is_correct else "incorrect"
        return f"Move #{self.pk} ({status})"
