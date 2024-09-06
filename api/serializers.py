from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class TokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token_data = super().get_token(user)

        # Add custom claims
        token_data['email'] = user.email

        return token_data

    def validate(self, attrs):
        token_data = super().validate(attrs)

        user_data = {
                "user_id": self.user.id,
                "email": self.user.email
        }
        data = {"user": user_data, **token_data}
        return data
