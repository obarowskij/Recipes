from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient

from django.contrib.auth import get_user_model

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse("recipe:ingredient-list")

def create_user(email='test@example.com', password='testpass123'):
    return get_user_model().objects.create_user(email=email, password=password)

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
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.data, serializer.data)
    
    def test_ingredients_limited_to_user(self):
        new_user = create_user()
        tag1 = Ingredient.objects.create(user=self.user, name='test1')
        Ingredient.objects.create(user=new_user, name='test2')
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        serializer = IngredientSerializer(tag1)
        self.assertIn(serializer.data, res.data)