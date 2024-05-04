from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag, Ingredient
from recipe import serializers

# Create your views here.


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by("-id")

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.RecipeSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TagsViewSet(
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user).order_by("-name")


class IngredientsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.IngredientSerializer
    queryset = Tag.objects.all()
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return Ingredient.objects.filter(user=self.request.user).order_by(
            "-name"
        )
