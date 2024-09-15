from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext as _
from rest_framework import mixins, viewsets
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.views import TokenObtainPairView

from api.serializers import (
    AddUserSerializer,
    DriverSerializer,
    RegisterDriverSerializer,
    TokenSerializer,
    VehicleSerializer,
    VehicleTechnicianListSerializer,
    VehicleTechnicianSerializer,
)
from authentication.models import AppUser, Driver
from management.models import Vehicle, VehicleTechnician


class TokenPairView(TokenObtainPairView):
    serializer_class = TokenSerializer


class AddUserView(GenericAPIView):
    serializer_class = AddUserSerializer
    queryset = AppUser.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "response_message": "User created successfully!", "response_data": serializer.data}
            )
        return Response({"success": False, "response_message": serializer.errors})


class DriverListView(ListAPIView):
    serializer_class = DriverSerializer
    queryset = Driver.objects.all()


class DriverViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = RegisterDriverSerializer
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    queryset = Driver.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data["created_by"] = request.user
            serializer.save()
            return Response(
                {
                    "success": True,
                    "response_message": _("Driver registered successfully!"),
                    "response_data": serializer.data,
                }
            )
        return Response(
            {
                "success": False,
                "response_message": serializer.errors,
            }
        )


class VehicleViewSet(mixins.CreateModelMixin, GenericViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "response_message": _("New Vehicle registered!"), "response_data": serializer.data}
            )
        return Response({"success": False, "response_message": serializer.errors})


class VehicleTechnicianViewSet(viewsets.ModelViewSet):
    queryset = VehicleTechnician.objects.all()
    serializer_class = VehicleTechnicianSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context=self.get_serializer())

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "response_message": _("A vehicle technician created successfully!"),
                    "response_data": serializer.data,
                }
            )
        return Response({"success": False, "response_message": serializer.errors})

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset:
            return Response({"response_message": _("No vehicles registered yet.")})

        return Response(
            {
                "success": True,
                "response_message": _("Vehicles found."),
                "response_data": VehicleTechnicianListSerializer(queryset=queryset).data,
            }
        )
