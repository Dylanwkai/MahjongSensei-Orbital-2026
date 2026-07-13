from django.urls import path

from .views import (
    CheckWinView,
    RandomHandView,
    RecommendDiscardView,
    ScoreHandView,
    SoloClaimView,
    SoloDiscardView,
    SoloHintView,
    SoloKongView,
    SoloNewView,
    SoloPassView,
    SoloStateView,
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
    path('solo/new/', SoloNewView.as_view(), name='solo-new'),
    path('solo/state/', SoloStateView.as_view(), name='solo-state'),
    path('solo/discard/', SoloDiscardView.as_view(), name='solo-discard'),
    path('solo/kong/', SoloKongView.as_view(), name='solo-kong'),
    path('solo/claim/', SoloClaimView.as_view(), name='solo-claim'),
    path('solo/pass/', SoloPassView.as_view(), name='solo-pass'),
    path('solo/hint/', SoloHintView.as_view(), name='solo-hint'),
]
