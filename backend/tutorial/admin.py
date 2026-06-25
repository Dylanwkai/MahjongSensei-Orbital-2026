from django.contrib import admin

from .models import TutorialProgress


@admin.register(TutorialProgress)
class TutorialProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "module_id", "completed", "quiz_score", "completed_at")
    list_filter = ("completed", "module_id")
    search_fields = ("user__username", "module_id")
