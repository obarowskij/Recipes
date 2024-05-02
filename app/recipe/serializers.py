from rest_framework.serializers import ModelSerializer
from core.models import Recipe


class RecipeSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "time_minutes",
            "price",
            "link",
        ]
        read_only_fields = ["id"]

class RecipeDetailSerializer(RecipeSerializer):

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
    