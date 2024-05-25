from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient, Recipe

from django.contrib.auth import get_user_model

from recipe.serializers import IngredientSerializer
from decimal import Decimal

INGREDIENTS_URL = reverse("recipe:ingredient-list")


def create_user(email="test@example.com", password="testpass123"):
    return get_user_model().objects.create_user(email=email, password=password)


def get_ingredient_url(id):
    return reverse("recipe:ingredient-detail", args=[id])


class PublicIngredientsTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="admin@example.com")
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredients(self):
        Ingredient.objects.create(user=self.user, name="test1")
        Ingredient.objects.create(user=self.user, name="test2")
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        new_user = create_user()
        tag1 = Ingredient.objects.create(user=self.user, name="test1")
        Ingredient.objects.create(user=new_user, name="test2")
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        serializer = IngredientSerializer(tag1)
        self.assertIn(serializer.data, res.data)

    def test_update_ingredient(self):
        ingredient = Ingredient.objects.create(user=self.user, name="test")
        payload = {"name": "test1"}
        url = get_ingredient_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        ingredient = Ingredient.objects.create(user=self.user, name="test")
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

        url = get_ingredient_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        ingredient = Ingredient.objects.filter(user=self.user).exists()

        self.assertFalse(ingredient)

    def test_assigned_ingredients_only(self):
        ing1 = Ingredient.objects.create(user=self.user, name="test1")
        ing2 = Ingredient.objects.create(user=self.user, name="test2")

        rec = Recipe.objects.create(
            user=self.user,
            title="test1",
            time_minutes=10,
            price=Decimal("5.00"),
        )
        rec.ingredients.add(ing1)
        s1 = IngredientSerializer(ing1)
        s2 = IngredientSerializer(ing2)
        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_distinct_ingredients(self):
        ing1 = Ingredient.objects.create(user=self.user, name="test1")
        Ingredient.objects.create(user=self.user, name="test2")
        rec1 = Recipe.objects.create(
            user=self.user,
            title="test1",
            time_minutes=10,
            price=Decimal("5.00"),
        )
        rec2 = Recipe.objects.create(
            user=self.user,
            title="test2",
            time_minutes=10,
            price=Decimal("5.00"),
        )
        rec1.ingredients.add(ing1)
        rec2.ingredients.add(ing1)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
