from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Profile


class RegisterApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user_and_profile(self):
        response = self.client.post(
            "/api/users/register/",
            {
                "username": "new_player",
                "password": "strong_password_123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="new_player")
        self.assertTrue(user.check_password("strong_password_123"))
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username="existing_player",
            password="strong_password_123",
        )

        response = self.client.post(
            "/api/users/register/",
            {
                "username": "existing_player",
                "password": "another_password_123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)


class ProfileApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="profile_player",
            password="strong_password_123",
        )
        Profile.objects.create(user=self.user)

    def test_profile_requires_login(self):
        response = self.client.get("/api/users/profile/")

        self.assertEqual(response.status_code, 401)

    def test_logged_in_user_can_view_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/users/profile/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "profile_player")
        self.assertEqual(response.data["games_played"], 0)
        self.assertEqual(response.data["games_won"], 0)
        self.assertEqual(response.data["win_rate"], 0.0)
