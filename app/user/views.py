from rest_framework import generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from . import serializers


class CreateUserView(generics.CreateAPIView):
<<<<<<< HEAD
    serializer_class = serializers.UserSerializer

class TokenView(ObtainAuthToken):
    serializer_class = serializers.TokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
=======
    serializer_class = UserSerializer
>>>>>>> 5ef188385652ef6a58990bdd5deaa229bdec6a82
