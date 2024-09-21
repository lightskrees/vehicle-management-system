from django.db.utils import IntegrityError
from django.utils.translation import gettext as _
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView

from api.mixins import MultipleSerializerAPIMixin
from api.serializers import (
    AddUserSerializer,
    DocumentCreateSerializer,
    DocumentListSerializer,
    DriverSerializer,
    PartnerCreateSerializer,
    PartnerListSerializer,
    PartnershipSerializer,
    RegisterDriverSerializer,
    TokenSerializer,
    VehicleDriverAssignmentSerializer,
    VehicleSerializer,
    VehicleTechnicianListSerializer,
    VehicleTechnicianSerializer,
)
from authentication.models import AppUser, Driver
from management.models import Vehicle, VehicleDriverAssignment, VehicleTechnician
from vehicleHub.models import Document, Partner, Partnership


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
    detail_serializer_class = DriverSerializer
    permission_classes = [IsAuthenticated]
    queryset = Driver.objects.all()

    def get_serializer_class(self):
        if self.action == "retrieve" or self.action == "list":
            if hasattr(self, "detail_serializer_class"):
                return self.detail_serializer_class

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
        serializer = self.serializer_class(data=request.data, context=self.get_serializer_context())

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


class VehicleDriverAssignmentCreationView(APIView):

    def get_queryset(self):
        return VehicleDriverAssignment.objects.all()

    def post(self, request, *args, **kwargs):
        try:
            serializer = VehicleDriverAssignmentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "success": True,
                        "response_message": _("Vehicle assigned successfully!"),
                        "response_data": serializer.data,
                    }
                )
            return Response(
                {
                    "success": True,
                    "response_message": serializer.errors,
                }
            )
        except IntegrityError:
            return Response(
                {
                    "success": False,
                    "response_message": _("the specified vehicle is currently assigned to another person."),
                }
            )
        except Exception as e:
            return Response(
                {"success": False, "response_message": _(f"Failed to assign the given driver because {str(e)}")}
            )


class PartnershipManagementViewSet(MultipleSerializerAPIMixin, ModelViewSet):
    queryset = Partnership.objects.filter(status=Partnership.Status.ACTIVE)
    serializer_class = PartnershipSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset:
            return Response({"response_message": _("No partnerships registered yet.")})

        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["POST"], url_path="add-partnership/")
    def add_partnership(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "response_message": _("Partnership added successfully for the company!"),
                }
            )
        return Response({"success": False, "response_message": serializer.errors})

    # def create(self, request, *args, **kwargs):
    #     return self.add_partnership(request, *args, **kwargs)


class PartnerConfigurationViewSet(MultipleSerializerAPIMixin, ModelViewSet):
    queryset = Partner.objects.filter(partnership__status=Partnership.Status.ACTIVE)
    serializer_class = PartnerCreateSerializer
    create_serializer_class = PartnerCreateSerializer
    list_serializer_class = PartnerListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset:
            return Response({"response_message": _("No partners registered yet.")})
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["POST"], url_path="add-partner/")
    def add_partner(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "response_message": _("Partner added successfully for the company!"),
                }
            )
        return Response({"success": False, "response_message": serializer.errors})


class DocumentManagementViewSet(MultipleSerializerAPIMixin, ModelViewSet):
    queryset = Document.objects.all()
    create_serializer_class = DocumentCreateSerializer
    detail_serializer_class = DocumentListSerializer

    @action(detail=False, methods=["POST"], url_path="/add-document/")
    def add_document(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "response_message": _("Document created successfully!"),
                    "response_data": serializer.data,
                }
            )
        return Response({"success": False, "response_message": serializer.errors})

    def create(self, request, *args, **kwargs):
        return self.add_document(request, *args, **kwargs)
