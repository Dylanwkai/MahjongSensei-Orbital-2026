from django.urls import path

from .views import (
    RandomHandView,
    RecommendDiscardView,
    TrainerHistoryView,
    TrainerNewView,
    TrainerSubmitView,
)

urlpatterns = [
    path('random-hand/', RandomHandView.as_view(), name='random-hand'),
    path('recommend-discard/', RecommendDiscardView.as_view(), name='recommend-discard'),
    path('trainer/new/', TrainerNewView.as_view(), name='trainer-new'),
    path('trainer/submit/', TrainerSubmitView.as_view(), name='trainer-submit'),
    path('trainer/history/', TrainerHistoryView.as_view(), name='trainer-history'),
]
