from django.contrib import admin
from django.urls import path, include
from users.views import RegisterView, ProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('api-auth/', include('rest_framework.urls')),  # For browsable API login/logout
    path('profile/', ProfileView.as_view(), name='profile'),  # Endpoint for user profile
]
