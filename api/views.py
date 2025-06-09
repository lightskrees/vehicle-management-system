from django.contrib.auth.hashers import make_password
from django.db.utils import IntegrityError
from django.utils.translation import gettext as _
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView

from api.mixins import AccessMixin, MultipleSerializerAPIMixin
from api.serializers import (  # ListFuelSerializer,
    AddUserSerializer,
    DocumentCreateSerializer,
    DocumentListSerializer,
    DriverSerializer,
    FuelSerializer,
    ListUserSerializer,
    ListVehicleSerializer,
    PartnerCreateSerializer,
    PartnerListSerializer,
    PartnershipCreateSerializer,
    PartnershipListSerializer,
    RegisterDriverSerializer,
    TokenSerializer,
    UpdateDriverSerializer,
    VehicleDriverAssignmentSerializer,
    VehicleSerializer,
    VehicleTechnicianListSerializer,
    VehicleTechnicianSerializer,
)
from api.utils import send_email
from authentication.models import AppUser, Driver
from management.models import Vehicle, VehicleDriverAssignment, VehicleTechnician
from vehicleHub.models import Document, Fuel, Partner, Partnership


class TokenPairView(TokenObtainPairView):
    serializer_class = TokenSerializer


class AddUserView(GenericAPIView):
    serializer_class = AddUserSerializer
    queryset = AppUser.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer.validated_data["password"] = make_password(serializer.validated_data["password"])
            user = serializer.save()
            try:
                send_email(user, activation_link="google.com")
            except Exception:
                pass  # still under configuration...
            return Response(
                {"success": True, "response_message": "User created successfully!", "response_data": serializer.data}
            )
        return Response({"success": False, "response_message": serializer.errors})


class UserAPIViewSet(
    MultipleSerializerAPIMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = AppUser.objects.all()
    serializer_class = ListUserSerializer
    update_serializer_class = AddUserSerializer

    @action(detail=False, methods=["GET"], url_path="count/")
    def users_config(self, request, *args, **kwargs):
        active = request.query_params.get("active")
        response_data = {
            "success": False,
            "users_count": 0,
        }
        if active == "true":
            response_data["success"] = True
            response_data["users_count"] = self.get_queryset().filter(is_active=True).count()
        elif active == "false":
            response_data["success"] = True
            response_data["users_count"] = AppUser.inactive.all().count()
        return Response(response_data)


class DriverListView(ListAPIView):
    serializer_class = DriverSerializer
    queryset = Driver.objects.all()


class DriverViewSet(ModelViewSet):
    serializer_class = RegisterDriverSerializer
    detail_serializer_class = DriverSerializer
    permission_classes = [IsAuthenticated]
    queryset = Driver.objects.all()

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            if hasattr(self, "detail_serializer_class"):
                return self.detail_serializer_class
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        # Validate and create the AppUser first
        user_data = request.data.get("user")
        # user_serializer = AddUserSerializer(data=user_data)  # Use a serializer for AppUser validation
        # if user_serializer.is_valid():
        #     user = user_serializer.save()  # Create the user
        # else:
        #     return Response(
        #         {
        #             "success": False,
        #             "response_message": _("User data is invalid."),
        #             "errors": user_serializer.errors,
        #         },
        #         status=400,
        #     )

        # Process the driver creation
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)  # Pass the user and created_by fields
            return Response(
                {
                    "success": True,
                    "response_message": _("Driver registered successfully!"),
                    "response_data": serializer.data,
                },
                status=201,
            )
        else:
            for field, messages in serializer.errors.items():
                for message in messages:
                    return Response(
                        {
                            "success": False,
                            "response_message": _(f"{message}"),
                            "response_data": None,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

    @action(detail=False, methods=["GET"], url_path="count/")
    def drivers_config(self, request, *args, **kwargs):
        try:
            response_data = {
                "success": True,
                "count_": self.get_queryset().count(),
            }
            return Response(response_data)
        except Exception:
            return Response({"success": False, "count_": 0})


class RegisterDriverApiView(ModelViewSet, MultipleSerializerAPIMixin):
    permission_classes = [IsAuthenticated]
    queryset = Driver.objects.all()
    update_serializer_class = UpdateDriverSerializer
    serializer_class = DriverSerializer

    def create(self, request, *args, **kwargs):
        # Extract user data
        try:
            user_data = {
                "email": request.data.get("email"),
                "first_name": request.data.get("first_name"),
                "last_name": request.data.get("last_name"),
                "password": request.data.get("password"),
                "employeeID": request.data.get("employeeID"),
            }

            # Extract driver info
            driver_info = {
                "driving_license_number": request.data.get("driving_license_number"),
                "delivery_date": request.data.get("delivery_date"),
                "expiry_date": request.data.get("expiry_date"),
                "license_category": request.data.get("license_category"),
            }

            # Extract driving license file
            driving_license_file = request.FILES.get("driving_license_file")

            # Validate and save the user
            user_serializer = AddUserSerializer(data=user_data)
            if user_serializer.is_valid():
                user = user_serializer.save()
            else:
                for field, messages in user_serializer.errors.items():
                    for message in messages:
                        return Response(
                            {
                                "success": False,
                                "response_message": _(f"{message}"),
                                "response_data": None,
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

            # Add the user to driver_info
            driver_info["user"] = user.id
            driver_info["driving_license_file"] = driving_license_file

            # Validate and save the driver
            driver_serializer = RegisterDriverSerializer(data=driver_info)
            if driver_serializer.is_valid():
                driver = driver_serializer.save(created_by=request.user)
                return Response(
                    {
                        "success": True,
                        "response_message": _("Driver registered successfully!"),
                        "response_data": DriverSerializer(driver).data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                # Delete user if driver creation fails
                user.delete()
                for field, messages in driver_serializer.errors.items():
                    for message in messages:

                        return Response(
                            {
                                "success": False,
                                "response_message": _(f"{message}"),
                                "errors": driver_serializer.errors,
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                return None
        except Exception as error:
            return Response(
                {
                    "success": False,
                    "response_message": _("An error occurred in the process. Please contact the administrator."),
                    "response_data": str(error),
                }
            )

    def update(self, request, *args, **kwargs):
        # Extract user data
        try:

            # Extract driver info
            driver_info = {
                "driving_license_number": request.data.get("driving_license_number"),
                "delivery_date": request.data.get("delivery_date"),
                "expiry_date": request.data.get("expiry_date"),
                "license_category": request.data.get("license_category"),
            }

            # Extract driving license file
            driving_license_file = request.FILES.get("driving_license_file")

            # Add driver_info
            driver_info["driving_license_file"] = driving_license_file

            # Validate and save the driver
            driver_object = self.get_object()
            driver_serializer = UpdateDriverSerializer(driver_object, data=driver_info, partial=True)
            if driver_serializer.is_valid():
                driver = driver_serializer.save(created_by=request.user)
                return Response(
                    {
                        "success": True,
                        "response_message": _("Driver information updated"),
                        "response_data": DriverSerializer(driver).data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                # Delete user if driver creation fails
                for field, messages in driver_serializer.errors.items():
                    for message in messages:

                        return Response(
                            {
                                "success": False,
                                "response_message": _(f"{message}"),
                                "errors": driver_serializer.errors,
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                return None
        except Exception as error:
            return Response(
                {
                    "success": False,
                    "response_message": _("An error occurred in the process. Please contact the administrator."),
                    "response_data": str(error),
                }
            )


class FuelViewSet(viewsets.ModelViewSet):
    serializer_class = FuelSerializer
    queryset = Fuel.objects.all()


class VehicleViewSet(ModelViewSet, MultipleSerializerAPIMixin):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    list_serializer_class = ListVehicleSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            data["created_by"] = request.user
            serializer.save()
            return Response(
                {"success": True, "response_message": _("New Vehicle registered!"), "response_data": serializer.data}
            )
        else:
            for field, messages in serializer.errors.items():
                for message in messages:
                    return Response(
                        {
                            "success": False,
                            "response_message": _(f"{message}"),
                            "response_data": None,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        return None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset:
            return Response(
                {
                    "success": False,
                    "response_message": _("No Vehicles registered!"),
                }
            )
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["GET"], url_path="count/")
    def vehicle_config(self, request, *args, **kwargs):
        try:
            response_data = {
                "success": True,
                "count_": self.get_queryset().count(),
            }
            return Response(response_data)
        except Exception:
            return Response({"success": False, "count_": 0})


class VehicleTechnicianViewSet(ModelViewSet):
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
    serializer_class = PartnershipCreateSerializer
    list_serializer_class = PartnershipListSerializer

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
    serializer_class = DocumentCreateSerializer
    list_serializer_class = DocumentListSerializer
    # access_required = "trying.access"
    permission_denied_message = "You do not have required access to add documents."

    @action(detail=False, methods=["POST"], url_path="add-document/")
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
        return Response(
            {
                "success": False,
                "response_message": _("Failed to add document. Try again later."),
                "response_data": serializer.errors,
            }
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset:
            return Response({"response_message": _("No documents registered yet.")})

        return super().list(request, *args, **kwargs)
