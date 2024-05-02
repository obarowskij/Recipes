from rest_framework.serializers import ModelSerializer
from core.models import Recipe


class RecipeSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "description",
            "time_minutes",
            "price",
            "link",
        ]
        read_only_fields = ["id"]
