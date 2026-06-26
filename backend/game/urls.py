from django.urls import path

from .views import (
    CheckWinView,
    RandomHandView,
    RecommendDiscardView,
    ScoreHandView,
    TrainerHistoryView,
    TrainerNewView,
    TrainerSubmitView,
)

urlpatterns = [
    path('random-hand/', RandomHandView.as_view(), name='random-hand'),
    path('recommend-discard/', RecommendDiscardView.as_view(), name='recommend-discard'),
    path('check-win/', CheckWinView.as_view(), name='check-win'),
    path('score-hand/', ScoreHandView.as_view(), name='score-hand'),
    path('trainer/new/', TrainerNewView.as_view(), name='trainer-new'),
    path('trainer/submit/', TrainerSubmitView.as_view(), name='trainer-submit'),
    path('trainer/history/', TrainerHistoryView.as_view(), name='trainer-history'),
]
