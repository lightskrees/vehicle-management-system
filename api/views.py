from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView

from api.serializers import TokenSerializer


class TokenPairView(TokenObtainPairView):
    serializer_class = TokenSerializer
