from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.db.models import Count, Q, Sum
from django.db.utils import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
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
    IssueReportSerializer,
    ListIssueReportSerializer,
    ListUserSerializer,
    ListVehicleDriverAssignmentSerializer,
    ListVehicleSerializer,
    PartnerCreateSerializer,
    PartnerListSerializer,
    PartnershipCreateSerializer,
    PartnershipListSerializer,
    RegisterDriverSerializer,
    TokenSerializer,
    UpdateDriverSerializer,
    VehicleDriverAssignmentSerializer,
    VehicleMaintenanceSerializer,
    VehicleSerializer,
    VehicleTechnicianListSerializer,
    VehicleTechnicianSerializer,
)
from api.utils import send_email
from authentication.models import AccessRole, AppUser, Driver, Role
from management.models import Vehicle, VehicleDriverAssignment, VehicleTechnician
from vehicleBudget.models import DocumentCost, VehicleMaintenance
from vehicleHub.models import Document, Fuel, IssueReport, Partner, Partnership


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

    @action(detail=True, methods=["POST"], url_path="update-status/")
    def update_status(self, request, pk=None):
        try:
            user = self.get_object()
            if user.is_active:
                user.is_active = False
                STATUS = "deactivated"
            else:
                user.is_active = True
                STATUS = "activated"
            user.save()
            return Response(
                {"success": True, "response_message": _(f"User {STATUS}.")},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"success": False, "response_message": _("Failed to update status. Try again later.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
                user_serializer.validated_data["password"] = make_password(user_serializer.validated_data["password"])
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

                # create role for the driver
                driver_role = Role.objects.get_or_create(
                    role_group=Role.RoleGroup.DRIVER, role_name="Driver", is_active=True
                )[0]
                AccessRole.objects.get_or_create(
                    user=user,
                    role=driver_role,
                    start_date=timezone.now().date(),
                    end_date=timezone.now().date() + timedelta(days=30),
                )

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


class VehicleViewSet(MultipleSerializerAPIMixin, ModelViewSet):
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
                "response_data": VehicleTechnicianListSerializer(
                    queryset, many=True, context={"request": request}
                ).data,
            }
        )

    @action(detail=False, methods=["GET"], url_path="count/")
    def vehicle_technician_config(self, request, *args, **kwargs):
        try:
            response_data = {
                "success": True,
                "count_": self.get_queryset().count(),
            }
            return Response(response_data)
        except Exception:
            return Response({"success": False, "count_": 0})


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
        except IntegrityError:
            return Response(
                {
                    "success": False,
                    "response_message": _("the specified vehicle is currently assigned to another person."),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"success": False, "response_message": _(f"Failed to assign the given driver because {str(e)}")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VehicleAssignmentsManagementViewSet(MultipleSerializerAPIMixin, viewsets.ModelViewSet):
    queryset = VehicleDriverAssignment.objects.all()
    serializer_class = VehicleDriverAssignmentSerializer
    list_serializer_class = ListVehicleDriverAssignmentSerializer

    lookup_field = "vehicle_id"

    @action(detail=False, methods=["GET"], url_path="count/")
    def assigments_config(self, request, *args, **kwargs):
        response_data = {"success": False, "count_": 0}

        try:
            active = request.query_params.get("active")
            if active == "true":
                response_data = {
                    "success": True,
                    "count_": self.get_queryset()
                    .filter(assignment_status=VehicleDriverAssignment.AssignmentStatus.ACTIVE)
                    .count(),
                }
            elif active == "false":
                response_data = {
                    "success": True,
                    "count_": self.get_queryset()
                    .filter(assignment_status=VehicleDriverAssignment.AssignmentStatus.INACTIVE)
                    .count(),
                }
            else:
                response_data = {
                    "success": True,
                    "count_": self.get_queryset().count(),
                }
            return Response(response_data)
        except Exception:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["POST"], url_path="deactivate/")
    def deactivate(self, request, *args, **kwargs):

        try:
            vehicle_id = kwargs.get("vehicle_id")
            vehicle = Vehicle.objects.get(id=vehicle_id)

            assignments = self.get_queryset().filter(
                vehicle=vehicle, assignment_status=VehicleDriverAssignment.AssignmentStatus.ACTIVE
            )
            if not assignments.exists():
                return Response({"success": False, "response_message": _("Assignments not found.")})
            for assignment in assignments:
                assignment.ends_at = timezone.now().date()
                assignment.assignment_status = VehicleDriverAssignment.AssignmentStatus.INACTIVE
                assignment.save()

            return Response(
                {"success": True, "response_message": _("assignments deactivated!")}, status=status.HTTP_200_OK
            )
        except Vehicle.DoesNotExist:
            return Response(
                {"success": False, "response_message": _("Vehicle does not exist.")}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as error:
            print(error)
            return Response(
                {
                    "success": False,
                    "response_message": _("Failed to deactivate assignments. Contact the administrator."),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomVehicleList(APIView):
    def get_queryset(self):
        return Vehicle.objects.all()

    def get(self, request, *args, **kwargs):
        auth_user = request.user
        ACTIVE = VehicleDriverAssignment.AssignmentStatus.ACTIVE

        response_data = {
            "success": False,
            "response_message": _("An unexpected error occurred. Please Contact the administrator."),
            "response_data": [],
        }
        try:
            vehicle_technician = VehicleTechnician.objects.get(user=auth_user)
            managed_vehicles = Vehicle.objects.filter(
                managing_technician=vehicle_technician, managing_technician__end_date__isnull=False
            )
        except VehicleTechnician.DoesNotExist:
            vehicle_technician = None
            managed_vehicles = None

        try:
            try:
                if auth_user.driver:
                    vehicles = Vehicle.objects.filter(
                        assignment__driver=auth_user.driver, assignment__assignment_status=ACTIVE
                    )
                    response_data["success"] = True
                    response_data["response_message"] = _("Success")
                    response_data["response_data"] = VehicleSerializer(vehicles, many=True).data
                    return JsonResponse(response_data, status=status.HTTP_200_OK)
            except Driver.DoesNotExist:
                pass

            if vehicle_technician:
                response_data["success"] = True
                response_data["response_message"] = _("Success")
                response_data["response_data"] = VehicleSerializer(managed_vehicles, many=True).data
                return Response(response_data, status=status.HTTP_200_OK)

            response_data["response_message"] = _("No vehicles to display.")
            return Response(response_data, status=status.HTTP_200_OK)

        except Driver.DoesNotExist:
            return JsonResponse(response_data, status=status.HTTP_404_NOT_FOUND)

        except Exception as error:
            print("\n\n", error)
            response_data["success"] = False
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


########################
# VEHICLE ISSUE REPORTS
########################


class IssueReportViewSet(MultipleSerializerAPIMixin, ModelViewSet):

    serializer_class = IssueReportSerializer
    list_serializer_class = ListIssueReportSerializer

    def get_queryset(self):
        # we only display reports that have been rejected (they can be reviewed)...
        REJECTED = VehicleMaintenance.Status.REJECTED
        qs = IssueReport.objects.filter(is_fixed=False).filter(
            Q(maintenance__isnull=True) | Q(maintenance__status=REJECTED)
        )
        return qs

    def create(self, request, *args, **kwargs):

        serializer = self.serializer_class(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.validated_data["created_by"] = request.user
            serializer.save()
            return Response(
                {"success": True, "response_message": _("Issue reported.")},
                status=status.HTTP_201_CREATED,
            )

        else:
            for field, messages in serializer.errors.items():
                for message in messages:
                    return Response(
                        {
                            "success": False,
                            "response_message": _(f"{message}"),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            return None

    @action(detail=True, methods=["POST"], url_path="set-cost/")
    def set_cost(self, request, *args, **kwargs):
        try:
            issue_obj = self.get_object()
            if issue_obj.is_fixed:
                return Response(
                    {"success": False, "response_message": _("cannot set cost for a fixed issue")},
                    status=status.HTTP_403_FORBIDDEN,
                )

            issue_cost = request.data.get("issue_cost")
            issue_obj.set_cost(float(issue_cost))

            # update the final costs in the maintenance instance
            PENDING = VehicleMaintenance.Status.PENDING
            pending_maintenances = issue_obj.maintenances.filter(status=PENDING, maintenance_end_date__isnull=False)
            for pending_maintenance in pending_maintenances:
                issue_reports = pending_maintenance.issue_reports.all()
                total = 0
                for report in issue_reports:
                    total += (
                        report.issue_cost if report.issue_cost else 0
                    )  # to avoid value error in the computing process...
                pending_maintenance.payment_amount = total
                pending_maintenance.save()

            return Response({"success": True, "response_message": _("cost set.")}, status=status.HTTP_200_OK)
        except (Exception, ValueError) as e:
            return Response(
                {
                    "success": False,
                    "response_message": _("Failed to set cost. Try again later."),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


########################
# VEHICLE MAINTENANCE
########################


class VehicleMaintenanceViewSet(MultipleSerializerAPIMixin, ModelViewSet):

    queryset = VehicleMaintenance.objects.all()
    serializer_class = VehicleMaintenanceSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.validated_data["created_by"] = request.user
            pending_maintenance = serializer.save()
            pending_maintenance.update_maintenance_cost()
            return Response(
                {
                    "success": True,
                    "response_message": _("Vehicle maintenance created"),
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            for field, messages in serializer.errors.items():
                for message in messages:
                    return Response(
                        {
                            "success": False,
                            "response_message": _(f"{message}"),
                        }
                    )
            return None


class SystemDashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        thirty_days_from_now = today + timedelta(days=30)

        # SYSTEM STATISTICS
        system_stats = {
            "total_vehicles": Vehicle.objects.count(),
            "total_drivers": Driver.objects.count(),
            "total_technicians": VehicleTechnician.objects.count(),
            "active_assignments": VehicleDriverAssignment.objects.filter(
                assignment_status=VehicleDriverAssignment.AssignmentStatus.ACTIVE
            ).count(),
        }

        # USER STATISTICS
        user_stats = {
            "total_users": AppUser.objects.count(),
            "active_users": AppUser.objects.filter(is_active=True).count(),
            "inactive_users": AppUser.inactive.count(),
            "admin_users": AppUser.objects.filter(is_superuser=True).count(),
            # 'role_distribution': Role.objects.annotate(user_count=Count('role')),  #ToDo: to be implemented soon...
            "role_count": Role.objects.count(),
        }

        # VEHICLE STATISTICS
        vehicle_stats = {
            "vehicle_types": Vehicle.objects.values("vehicle_type").annotate(count=Count("vehicle_type")),
            "vehicles_needing_service": Vehicle.objects.filter(
                last_service_date__lt=today - timedelta(days=90)
            ).count(),
            "unassigned_vehicles": Vehicle.objects.filter(assignment__isnull=True).count(),
        }

        # DRIVER STATISTICS
        driver_stats = {
            "license_categories": Driver.objects.values("license_category").annotate(count=Count("license_category")),
            "expiring_licenses": Driver.objects.filter(expiry_date__range=[today, thirty_days_from_now]).count(),
            "active_drivers": Driver.objects.filter(
                assignment__assignment_status=VehicleDriverAssignment.AssignmentStatus.ACTIVE
            )
            .distinct()
            .count(),
        }

        # System Health
        system_health = {
            "database_status": "Connected",
            # 'redis_status': check_redis_connection(),
            "celery_status": check_celery_status(),
        }

        return Response(
            {
                "system_stats": system_stats,
                "user_stats": user_stats,
                "vehicle_stats": vehicle_stats,
                "driver_stats": driver_stats,
                "system_health": system_health,
            }
        )


# def check_redis_connection():
#     try:
#         from django_redis import get_redis_connection
#         redis_conn = get_redis_connection("default")
#         redis_conn.ping()
#         return "Connected"
#     except Exception:
#         return "Disconnected"
#
def check_celery_status():
    try:
        from celery.app.control import Control

        app = Control()
        if app.ping():
            return "Running"
        return "Stopped"
    except Exception:
        return "Error"


class VehicleHistoryViewSet(viewsets.ViewSet):
    """
    ViewSet for handling vehicle history with different aspects
    """

    def get_vehicle(self, pk):
        return get_object_or_404(Vehicle, pk=pk)

    @action(detail=True, methods=["get"], url_path="all-info/")
    def all_info(self, request, pk=None):
        """
        vehicle history information
        """
        vehicle = self.get_vehicle(pk)

        # Basic Info
        # basic_info = ListVehicleSerializer(vehicle, context={"request": request}).data

        basic_info = {
            "id": vehicle.id,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "vehicle_type": vehicle.get_vehicle_type_display(),
            "vin_number": vehicle.vin_number,
            "color": vehicle.color,
            "mileage": vehicle.mileage,
            "license_plate_number": vehicle.license_plate_number,
            "purchase_date": vehicle.purchase_date,
            "last_service_date": vehicle.last_service_date,
        }

        # Driver Assignments
        assignments = vehicle.assignments.all().order_by("-begin_at")
        driver_assignments = [
            {
                "driver": assignment.driver.user.full_name,
                "status": assignment.get_assignment_status_display(),
                "begin_at": assignment.begin_at,
                "ends_at": assignment.ends_at,
            }
            for assignment in assignments
        ]

        # Maintenance Records
        maintenances = VehicleMaintenance.objects.filter(issue_reports__vehicle=vehicle).distinct()
        maintenance_records = [
            {
                "name": maintenance.name,
                "status": maintenance.get_status_display(),
                "begin_date": maintenance.maintenance_begin_date,
                "end_date": maintenance.maintenance_end_date,
                "payment_amount": maintenance.payment_amount,
                "payment_method": maintenance.get_payment_method_display(),
                "partner": maintenance.partner.partnership.name if maintenance.partner else None,
            }
            for maintenance in maintenances
        ]

        # Fuel Consumption
        consumptions = vehicle.fuel_consumptions.all().order_by("-date")
        fuel_consumption = [
            {
                "date": consumption.date,
                "fuel_type": consumption.fuel_type.fuel_type,
                "quantity": str(consumption.quantity),
                "quantity_type": consumption.get_quantity_type_display(),
                "fuel_cost": consumption.fuel_cost,
                "payment_method": consumption.get_payment_method_display(),
                "partner": consumption.partner.partnership.name,
            }
            for consumption in consumptions
        ]

        # Documents
        documents = vehicle.documents.all().order_by("-created_at")
        document_records = [
            {
                "name": document.name,
                "type": document.get_document_type_display(),
                "category": document.get_document_category_display(),
                "is_renewable": document.is_renewable,
                "begin_date": document.exp_begin_date,
                "end_date": document.exp_end_date,
                "issuing_authority": (
                    document.issuing_authority.partnership.name if document.issuing_authority else None
                ),
            }
            for document in documents
        ]

        # Financial Records
        maintenance_costs = VehicleMaintenance.objects.filter(issue_reports__vehicle=vehicle).aggregate(
            total=Sum("payment_amount")
        )
        fuel_costs = vehicle.fuel_consumptions.aggregate(total=Sum("fuel_cost"))
        document_costs = DocumentCost.objects.filter(document__issued_vehicle=vehicle).aggregate(
            total=Sum("payment_amount")
        )
        financial_records = {
            "maintenance_total": maintenance_costs["total"] or 0,
            "fuel_total": fuel_costs["total"] or 0,
            "document_total": document_costs["total"] or 0,
            "total_cost": (maintenance_costs["total"] or 0)
            + (fuel_costs["total"] or 0)
            + (document_costs["total"] or 0),
        }

        # Technicians
        technicians = vehicle.technician.all().order_by("-begin_date")
        technical_management = [
            {
                "technician": technician.user.full_name,
                "begin_date": technician.begin_date,
                "end_date": technician.end_date,
            }
            for technician in technicians
        ]

        # Issue Reports
        issue_reports = vehicle.issue_reports.all().order_by("-created_at")
        issue_report_data = ListIssueReportSerializer(issue_reports, many=True, context={"request": request}).data

        # Stats
        stats = {
            "total_drivers": vehicle.assignments.count(),
            "active_drivers": vehicle.assignments.filter(
                assignment_status=VehicleDriverAssignment.AssignmentStatus.ACTIVE
            ).count(),
            "reported_issues": vehicle.issue_reports.count(),
            "total_maintenances": VehicleMaintenance.objects.filter(issue_reports__vehicle=vehicle).distinct().count(),
            "total_fuel_records": vehicle.fuel_consumptions.count(),
            "total_documents": vehicle.documents.count(),
            "last_maintenance_date": vehicle.last_service_date,
            "current_mileage": vehicle.mileage,
        }

        overall_data = {
            "basic_info": basic_info,
            "driver_assignments": driver_assignments,
            "maintenance_records": maintenance_records,
            "fuel_consumption": fuel_consumption,
            "documents": document_records,
            "financial_records": financial_records,
            "technical_management": technical_management,
            "issue_reports": issue_report_data,
            "stats": stats,
        }

        return Response(overall_data)
