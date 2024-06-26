from django.test import TestCase
from django.contrib.auth import get_user_model

from decimal import Decimal
from core import models
from unittest.mock import patch


class ModelTests(TestCase):

    def test_user_created_successfully(self):
        email = "test@example.com"
        password = "password123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
            ["test4@example.com", "test4@example.com"],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email, "sample_password"
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "test")

    def test_create_superuser(self):
        "Test creating superuser"
        user = get_user_model().objects.create_superuser(
            "test@example.com", "test123"
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_recipe_model(self):
        user = get_user_model().objects.create_user(
            "test@example.com", "testpass123"
        )

        recipe = models.Recipe.objects.create(
            user=user,
            title="Sample recipe",
            time_minutes=5,
            price=Decimal("5.5"),
            description="Sample description",
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_tag_model(self):
        user = get_user_model().objects.create_user(
            "test@example.com", "test123"
        )
        tag = models.Tag.objects.create(
            user=user,
            name="test name",
        )
        self.assertEqual(str(tag), tag.name)

    def test_ingredient_model(self):
        user = get_user_model().objects.create_user(
            "test@example.com", "testpass123"
        )
        ingredient = models.Ingredient.objects.create(
            user=user, name="test_name"
        )
        self.assertEqual(str(ingredient), ingredient.name)

    @patch("core.models.uuid.uuid4")
    def test_creating_url_for_image(self, mock_uuid):
        uuid = "test_uuid"
        mock_uuid.return_value = uuid
        file_path = models.get_image_file_path(None, "example.jpg")

        self.assertEqual(file_path, f"uploads/recipes/{uuid}.jpg")
