from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from api.serializers import TokenSerializer, AddUserSerializer
from authentication.models import AppUser


class TokenPairView(TokenObtainPairView):
    serializer_class = TokenSerializer


class AddUserView(GenericAPIView):
    serializer_class = AddUserSerializer
    queryset = AppUser.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'response_message': 'User created successfully!',
                "created_user": serializer.data
            }
            )
        return Response(
            {
                'success': False,
                'response_message': serializer.errors
            }
        )
