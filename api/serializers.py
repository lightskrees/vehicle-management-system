from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from authentication.models import AppUser, Driver


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ['email', 'first_name', 'last_name', 'email', 'is_active']


class AddUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ('first_name', 'last_name', 'email', 'password', 'employeeID')


class TokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token_data = super().get_token(user)

        token_data['first_name'] = user.first_name
        token_data['last_name'] = user.last_name
        token_data['username'] = user.email

        return token_data

    def validate(self, attrs):
        token_data = super().validate(attrs)

        user_details = {
            "user_id": self.user.id,
            "username": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        data = {"user": user_details, **token_data}
        return data
