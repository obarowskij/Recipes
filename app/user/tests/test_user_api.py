# Tests for user API.
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_user_created_succesfully(self):
        payload = {
            "email": "test1@example.com",
            "password": "testpass123",
            "name": "test",
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_not_created_email_exists(self):
        payload = {
            "email": "test1@example.com",
            "password": "testpass123",
            "name": "test",
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        payload = {
            "email": "test1@example.com",
            "password": "123",
            "name": "test",
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        with self.assertRaises(get_user_model().DoesNotExist) as context:
            get_user_model().objects.get(email=payload["email"])
        self.assertEqual(
            str(context.exception), "User matching query does not exist."
        )

    def test_token_created_succesfully(self):
        payload = {
            "name": "Test name",
            "email": "test@example.com",
            "password": "testpass123",
        }
        for_token = {
            "email": payload["email"],
            "password": payload["password"],
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, for_token)
        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_token_not_created_bad_credentials(self):
        payload = {
            "name": "Test name",
            "email": "test@example.com",
            "password": "testpass123",
        }
        create_user(**payload)
        for_token = {
            "email": payload["email"],
            "password": "badpass123",
        }
        res = self.client.post(TOKEN_URL, for_token)
        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_not_created_empty_password(self):
        payload = {
            "name": "Test name",
            "email": "test@example.com",
            "password": "testpass123",
        }
        create_user(**payload)
        for_token = {
            "email": payload["email"],
            "password": "",
        }
        res = self.client.post(TOKEN_URL, for_token)
        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_not_authorized(self):
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        payload = {
            "email": "test@example.com",
            "password": "testpass",
            "name": "test",
        }
        self.user = create_user(**payload)
        self.client.force_authenticate(user=self.user)

    def test_user_retrieved_succesfully(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data,
            {
                "email": self.user.email,
                "name": self.user.name,
            },
        )

    def test_post_not_allowed(self):
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_user_patch_method(self):
        payload = {
            "name": "newName",
            "password": "newpass",
        }
        res = self.client.patch(ME_URL, payload)
        self.assertEqual(self.user.name, payload["name"])
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
