from django.contrib import admin
from django.urls import path, include
from users.views import CreateUserView

urlpatterns = [
    path('register/', CreateUserView.as_view(), name='register'),
    path('api-auth/', include('rest_framework.urls')),  # For browsable API login/logout
]
