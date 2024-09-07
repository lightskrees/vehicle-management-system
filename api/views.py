from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from api.serializers import TokenSerializer, AddUserSerializer, RegisterDriverSerializer, DriverSerializer
from authentication.models import AppUser, Driver


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
                "response_data": serializer.data
            }
            )
        return Response(
            {
                'success': False,
                'response_message': serializer.errors
            }
        )


class DriverListView(ListAPIView):
    serializer_class = DriverSerializer
    queryset = Driver.objects.all()


class RegisterDriverView(GenericAPIView):
    serializer_class = RegisterDriverSerializer
    queryset = Driver.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['created_by'] = request.user
            serializer.save()
            return Response(
                {
                    'success': True,
                    'response_message': 'Driver registered successfully!',
                    'response_data': serializer.data
                }
            )
        return Response(
            {
                'success': False,
                'response_message': serializer.errors,
            }
        )
