from django.contrib import admin

from .models import Move, Session


class MoveInline(admin.TabularInline):
    model = Move
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "mode", "attempts", "correct_count", "created_at")
    list_filter = ("mode", "created_at")
    search_fields = ("user__username",)
    inlines = [MoveInline]


@admin.register(Move)
class MoveAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "is_correct", "user_score", "best_score", "created_at")
    list_filter = ("is_correct", "created_at")
