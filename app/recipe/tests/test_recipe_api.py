from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

import tempfile
import os
from PIL import Image

RECIPES_URL = reverse("recipe:recipe-list")


def get_recipe(recipe_id):
    return reverse("recipe:recipe-detail", args=[recipe_id])


def get_image(recipe_id):
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def create_user(email, password):
    return get_user_model().objects.create(email=email, password=password)


def create_recipe(user, **params):
    defaults = {
        "title": "sample recipe",
        "time_minutes": 420,
        "price": Decimal("5.55"),
        "description": "Sample desc",
        "link": "http://example.com/recipe.pdf",
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@example.com", "testpass123"
        )
        self.client.force_authenticate(self.user)

    def test_retrieving_recipe(self):
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_recipe_list_limited_to_user(self):
        other_user = get_user_model().objects.create_user(
            "test1@example.com", "testpass123"
        )

        create_recipe(user=self.user)
        create_recipe(user=other_user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        recipe = create_recipe(user=self.user)

        url = get_recipe(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        payload = {
            "title": "test",
            "time_minutes": 5,
            "price": Decimal("5.00"),
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        link = "http://example.com/example.pdf"
        payload = {
            "user": self.user,
            "title": "test",
            "link": link,
        }
        recipe = create_recipe(**payload)
        changes = {"title": "changed title"}
        url = get_recipe(recipe.id)
        res = self.client.patch(url, changes)
        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.user, self.user)
        self.assertEqual(recipe.title, changes["title"])
        self.assertEqual(recipe.link, link)

    def test_full_update(self):
        defaults = {
            "user": self.user,
            "title": "sample recipe",
            "time_minutes": 420,
            "price": Decimal("5.55"),
            "description": "Sample desc",
            "link": "http://example.com/recipe.pdf",
        }
        recipe = create_recipe(**defaults)
        payload = {
            "title": "sample recipe1",
            "time_minutes": 421,
            "price": Decimal("5.56"),
            "description": "Sample desc1",
            "link": "http://example.com/recipe1.pdf",
        }
        url = get_recipe(recipe.id)
        res = self.client.put(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_user_not_changeable(self):
        recipe = create_recipe(user=self.user)
        new_user = create_user("test1@example.com", "test123")
        payload = {"user": new_user}
        url = get_recipe(recipe.id)
        self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        recipe = create_recipe(user=self.user)
        url = get_recipe(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn(recipe, Recipe.objects.all())

    def test_delete_other_user_recipe(self):
        new_user = create_user("test1@example.com", "test123")
        recipe = create_recipe(user=new_user)
        url = get_recipe(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.get(id=recipe.id))

    def test_create_tags(self):
        payload = {
            "title": "test",
            "time_minutes": 30,
            "price": Decimal("5.50"),
            "tags": [{"name": "test1"}, {"name": "test2"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.all()
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            self.assertTrue(
                recipe.tags.filter(name=tag["name"], user=self.user).exists()
            )

    def test_creating_recipe_with_existing_tag(self):
        tag_test = Tag.objects.create(user=self.user, name="test")
        payload = {
            "title": "test",
            "time_minutes": 30,
            "price": Decimal("5.50"),
            "tags": [{"name": "test"}, {"name": "test2"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_test, recipe.tags.all())
        for tag in payload["tags"]:
            self.assertTrue(
                recipe.tags.filter(
                    name=tag["name"],
                    user=self.user,
                ).exists()
            )

    def test_creating_tags_on_patch(self):
        recipe = create_recipe(user=self.user)
        payload = {"tags": [{"name": "test"}]}
        url = get_recipe(recipe.id)
        res = self.client.patch(url, payload, format="json")
        new_tag = Tag.objects.get(user=self.user, name="test")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_tags(self):
        tag1 = Tag.objects.create(user=self.user, name="test1")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag1)

        tag2 = Tag.objects.create(user=self.user, name="test2")
        payload = {"tags": [{"name": "test2"}]}
        url = get_recipe(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag2, recipe.tags.all())
        self.assertNotIn(tag1, recipe.tags.all())

    def test_clearing_tags(self):
        tag = Tag.objects.create(user=self.user, name="test")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)
        payload = {"tags": []}
        url = get_recipe(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_creating_ingredients(self):
        payload = {
            "title": "test",
            "time_minutes": 30,
            "price": Decimal("5.50"),
            "ingredients": [{"name": "test"}, {"name": "test2"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.all()
        self.assertEqual(len(recipes), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload["ingredients"]:
            self.assertTrue(
                Ingredient.objects.get(name=ingredient["name"], user=self.user)
            )

    def test_creating_recipe_with_existing_ingredients(self):
        ingredient = Ingredient.objects.create(user=self.user, name="test")
        payload = {
            "title": "test",
            "time_minutes": 30,
            "price": Decimal("5.50"),
            "ingredients": [{"name": "test"}, {"name": "test2"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        recipes = Recipe.objects.all()
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(Ingredient.objects.all()), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload["ingredients"]:
            self.assertTrue(
                Ingredient.objects.get(user=self.user, name=ingredient["name"])
            )

    def test_updateing_ingredients(self):
        recipe = create_recipe(user=self.user)
        url = get_recipe(recipe.id)
        payload = {"ingredients": [{"name": "test"}]}
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient = Ingredient.objects.get(user=self.user, name="test")
        self.assertIn(ingredient, recipe.ingredients.all())

    def test_update_assign_ingredient(self):
        ingr1 = Ingredient.objects.create(user=self.user, name="test1")
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingr1)

        ingr2 = Ingredient.objects.create(user=self.user, name="test2")
        payload = {"ingredients": [{"name": "test2"}]}
        url = get_recipe(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingr2, recipe.ingredients.all())
        self.assertNotIn(ingr1, recipe.ingredients.all())

    def test_clearing_recipes(self):
        payload = {"ingredients": []}

        ingr1 = Ingredient.objects.create(user=self.user, name="test")
        recipe = create_recipe(user=self.user)

        recipe.ingredients.add(ingr1)
        url = get_recipe(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filtering_by_tags(self):
        r1 = create_recipe(user=self.user, title="recipe1")
        r2 = create_recipe(user=self.user, title="recipe2")
        tag1 = Tag.objects.create(user=self.user, name="tag1")
        tag2 = Tag.objects.create(user=self.user, name="tag2")
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user=self.user, title="recipe3")

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        payload = {"tags": f"{tag1.id}, {tag2.id}"}

        res = self.client.get(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filtering_by_ingredients(self):
        r1 = create_recipe(user=self.user, title="recipe1")
        r2 = create_recipe(user=self.user, title="recipe2")
        in1 = Ingredient.objects.create(user=self.user, name="ing1")
        in2 = Ingredient.objects.create(user=self.user, name="ing2")
        r1.ingredients.add(in1)
        r2.ingredients.add(in2)
        r3 = create_recipe(user=self.user, title="recipe3")

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        payload = {"ingredients": f"{in1.id}, {in2.id}"}

        res = self.client.get(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageRecipeTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@example.com", "testapss123"
        )
        self.client.force_authenticate(user=self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_images(self):
        url = get_image(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_bad_image(self):
        url = get_image(self.recipe.id)
        payload = {"image": "bad_image"}
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
