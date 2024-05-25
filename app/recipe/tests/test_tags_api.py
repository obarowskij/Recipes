from django.test import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer

TAGS_URL = reverse("recipe:tag-list")


def create_user(email="user3@example.com", password="testpass123"):
    return get_user_model().objects.create_user(
        email=email,
        password=password,
    )


def detail_url(id):
    return reverse("recipe:tag-detail", args=[id])


class PublicTagsAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()

        self.client.force_authenticate(user=self.user)

    def test_retrieve_tags(self):
        Tag.objects.create(user=self.user, name="test")
        Tag.objects.create(user=self.user, name="test1")
        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_tags(self):
        new_user = create_user(email="test1@example.com")
        Tag.objects.create(user=new_user, name="test1")
        tag = Tag.objects.create(user=self.user, name="test2")
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tags(self):
        tag = Tag.objects.create(user=self.user, name="test")
        payload = {"name": "patched_name"}
        res = self.client.patch(detail_url(tag.id), payload)
        tag.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["name"], tag.name)

    def test_delete_tags(self):
        tag = Tag.objects.create(user=self.user, name="test")
        serializer = TagSerializer(tag)
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, res.data)
        res = self.client.delete(detail_url(tag.id))
        tags = Tag.objects.filter(user=self.user)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn(tag, tags)

    def test_assigned_tags_only(self):
        tag1 = Tag.objects.create(user=self.user, name="test1")
        tag2 = Tag.objects.create(user=self.user, name="test2")

        rec = Recipe.objects.create(
            user=self.user,
            title="test1",
            time_minutes=10,
            price=Decimal("5.00"),
        )
        rec.tags.add(tag1)
        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_distinct_tags(self):
        tag1 = Tag.objects.create(user=self.user, name="test1")
        Tag.objects.create(user=self.user, name="test2")
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
        rec1.tags.add(tag1)
        rec2.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
