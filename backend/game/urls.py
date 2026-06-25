from django.urls import path

from .views import RandomHandView, RecommendDiscardView

urlpatterns = [
    path('random-hand/', RandomHandView.as_view(), name='random-hand'),
    path('recommend-discard/', RecommendDiscardView.as_view(), name='recommend-discard'),
]
