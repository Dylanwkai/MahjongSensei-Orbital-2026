from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import TUTORIAL_MODULES, TutorialProgress


class TutorialProgressModelTests(APITestCase):
    def test_unique_together_user_module(self):
        user = User.objects.create_user(username="alice", password="pw12345!")
        TutorialProgress.objects.create(user=user, module_id="tiles")
        with self.assertRaises(Exception):
            TutorialProgress.objects.create(user=user, module_id="tiles")

    def test_defaults(self):
        user = User.objects.create_user(username="bob", password="pw12345!")
        row = TutorialProgress.objects.create(user=user, module_id="melds")
        self.assertFalse(row.completed)
        self.assertIsNone(row.completed_at)
        self.assertIsNone(row.quiz_score)


class TutorialEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="carol", password="pw12345!")
        self.other = User.objects.create_user(username="dave", password="pw12345!")
        self.modules_url = reverse("tutorial-modules")
        self.progress_url = reverse("tutorial-progress")
        self.complete_url = reverse("tutorial-complete")

    # --- auth ---
    def test_endpoints_require_auth(self):
        for url in (self.modules_url, self.progress_url):
            self.assertEqual(
                self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED
            )
        self.assertEqual(
            self.client.post(self.complete_url, {"module_id": "tiles"}).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # --- modules ---
    def test_modules_list_with_merged_status(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(self.modules_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), len(TUTORIAL_MODULES))
        # default: nothing completed
        for module in resp.data:
            self.assertFalse(module["completed"])
        # ordered by 'order'
        orders = [m["order"] for m in resp.data]
        self.assertEqual(orders, sorted(orders))

    def test_modules_reflects_completion(self):
        self.client.force_authenticate(self.user)
        self.client.post(self.complete_url, {"module_id": "tiles", "quiz_score": 4})
        resp = self.client.get(self.modules_url)
        tiles = next(m for m in resp.data if m["id"] == "tiles")
        self.assertTrue(tiles["completed"])
        self.assertEqual(tiles["quiz_score"], 4)
        self.assertIsNotNone(tiles["completed_at"])

    # --- complete ---
    def test_complete_creates_row(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            self.complete_url, {"module_id": "tiles", "quiz_score": 3}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["completed"])
        self.assertEqual(resp.data["quiz_score"], 3)
        row = TutorialProgress.objects.get(user=self.user, module_id="tiles")
        self.assertTrue(row.completed)
        self.assertIsNotNone(row.completed_at)

    def test_complete_is_idempotent_upsert(self):
        self.client.force_authenticate(self.user)
        self.client.post(self.complete_url, {"module_id": "melds", "quiz_score": 2})
        self.client.post(self.complete_url, {"module_id": "melds", "quiz_score": 5})
        rows = TutorialProgress.objects.filter(user=self.user, module_id="melds")
        self.assertEqual(rows.count(), 1)
        self.assertEqual(rows.first().quiz_score, 5)

    def test_complete_rejects_unknown_module(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(self.complete_url, {"module_id": "nope"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(TutorialProgress.objects.filter(module_id="nope").exists())

    def test_complete_uses_request_user_not_body(self):
        self.client.force_authenticate(self.user)
        # even if a user id is smuggled in the body it must be ignored
        self.client.post(
            self.complete_url,
            {"module_id": "tiles", "quiz_score": 1, "user": self.other.id},
        )
        self.assertTrue(
            TutorialProgress.objects.filter(user=self.user, module_id="tiles").exists()
        )
        self.assertFalse(
            TutorialProgress.objects.filter(user=self.other, module_id="tiles").exists()
        )

    # --- progress isolation ---
    def test_progress_is_per_user(self):
        self.client.force_authenticate(self.user)
        self.client.post(self.complete_url, {"module_id": "tiles", "quiz_score": 4})

        self.client.force_authenticate(self.other)
        resp = self.client.get(self.progress_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 0)
