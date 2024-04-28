from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client


class TestAdmin(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="testpass123"
        )
        self.client.force_login(self.admin)
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="testpass321",
            name="testName",
        )

    def test_user_list(self):
        url = reverse("admin:core_user_changelist")
        res = self.client.get(url)

        self.assertContains(res, self.user.email)
        self.assertContains(res, self.user.name)

    def test_user_change(self):
        url = reverse("admin:core_user_change", args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_add_user(self):
        url = reverse("admin:core_user_add")
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
