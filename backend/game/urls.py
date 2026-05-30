from django.urls import path

from .views import RandomHandView

urlpatterns = [
    path('random-hand/', RandomHandView.as_view(), name='random-hand'),
]
