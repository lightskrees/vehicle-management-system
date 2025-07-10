from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from api.custom_serializer_fields import RelatedPartnership
from authentication.models import AppUser, Driver
from management.models import Vehicle, VehicleDriverAssignment, VehicleTechnician
from vehicleBudget.models import VehicleMaintenance
from vehicleHub.models import Document, Fuel, IssueReport, Partner, Partnership


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ["email", "first_name", "last_name", "email", "is_active"]


class AddUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["email", "first_name", "last_name", "password", "employeeID"]

    # def create(self, validated_data):
    #     return get_user_model().objects.create_user(**validated_data)


class ListUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ["id", "employeeID", "email", "first_name", "last_name", "password", "is_active"]


class DriverSerializer(serializers.ModelSerializer):
    user = ListUserSerializer(read_only=True)
    have_valid_license = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = [
            "user",
            "driving_license_number",
            "delivery_date",
            "expiry_date",
            "driving_license_file",
            "have_valid_license",
        ]

    def get_have_valid_license(self, obj):
        return obj.have_valid_license()


class RegisterDriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            "user",
            "driving_license_number",
            "delivery_date",
            "expiry_date",
            "license_category",
            "driving_license_file",
        ]


class UpdateDriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            "driving_license_number",
            "delivery_date",
            "expiry_date",
            "license_category",
            "driving_license_file",
        ]


class TokenSerializer(TokenObtainPairSerializer):

    default_error_messages = {
        "no_active_account": _("Votre compte est inactif. Veuillez contacter l' administrateur.")
    }

    @classmethod
    def get_token(cls, user):
        token_data = super().get_token(user)

        token_data["first_name"] = user.first_name
        token_data["last_name"] = user.last_name
        token_data["username"] = user.email

        return token_data

    def validate(self, attrs):
        token_data = super().validate(attrs)

        if not self.user.is_active:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        user_details = {
            "user_id": self.user.id,
            "username": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        data = {"user": user_details, **token_data}
        return data


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            "id",
            "make",
            "model",
            "year",
            "vehicle_type",
            "vin_number",
            "vehicle_image",
            "color",
            "fuel_type",
            "license_plate_number",
            "purchase_date",
        ]


class FuelSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="fuel_type", read_only=True)
    fuel_type = serializers.CharField(write_only=True)

    class Meta:
        model = Fuel
        fields = ["id", "fuel_type", "name"]


# class ListFuelSerializer(serializers.ModelSerializer):
#     fuel_details = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Fuel
#         fields = ["fuel_details"]
#
#     def get_fuel_details(self, obj):
#         return {"value": obj.fuel_type, "title": obj.get_fuel_type_display()}


class ListVehicleSerializer(VehicleSerializer):
    created_by = AddUserSerializer(read_only=True)
    fuel_type = serializers.CharField(source="fuel_type.fuel_type", read_only=True)
    driver = serializers.SerializerMethodField(read_only=True)

    class Meta(VehicleSerializer.Meta):
        fields = VehicleSerializer.Meta.fields + ["created_by", "driver"]

    def get_driver(self, obj):
        try:
            assignment = VehicleDriverAssignment.objects.get(
                vehicle=obj, assignment_status=VehicleDriverAssignment.AssignmentStatus.ACTIVE
            )
        except VehicleDriverAssignment.MultipleObjectsReturned:
            assignment = VehicleDriverAssignment.objects.filter(vehicle=obj).first()
        except VehicleDriverAssignment.DoesNotExist:
            return []

        return DriverSerializer(assignment.driver).data


class VehicleTechnicianSerializer(serializers.ModelSerializer):
    managed_vehicles = serializers.PrimaryKeyRelatedField(queryset=Vehicle.objects.all(), many=True, read_only=False)

    class Meta:
        model = VehicleTechnician
        fields = ("user", "managed_vehicles", "begin_date", "end_date")


class VehicleTechnicianListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    managed_vehicles = VehicleSerializer(many=True, read_only=True)

    class Meta:
        model = VehicleTechnician
        fields = ("user", "managed_vehicles", "begin_date", "end_date")


class VehicleDriverAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleDriverAssignment
        fields = ["driver", "vehicle", "begin_at", "ends_at"]


class ListVehicleDriverAssignmentSerializer(VehicleDriverAssignmentSerializer):
    driver = DriverSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    assignment_status = serializers.CharField(source="get_assignment_status_display", read_only=True)

    class Meta(VehicleDriverAssignmentSerializer.Meta):
        fields = VehicleDriverAssignmentSerializer.Meta.fields + ["assignment_status"]


# =======================
# PARTNER SERIALIZERS
# =======================


class PartnershipCreateSerializer(serializers.ModelSerializer):
    end_date = serializers.DateField(required=False)

    class Meta:
        model = Partnership
        fields = ["id", "name", "start_date", "end_date", "description"]


class PartnershipListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partnership
        fields = ["id", "name", "start_date", "end_date", "description", "is_permanent_partner"]


class PartnerListSerializer(serializers.ModelSerializer):
    partnership = PartnershipListSerializer(read_only=True)

    class Meta:
        model = Partner
        fields = "__all__"


class PartnerCreateSerializer(serializers.ModelSerializer):
    partnership = RelatedPartnership(queryset=Partnership.objects.filter(status=Partnership.Status.ACTIVE))

    class Meta:
        model = Partner
        fields = ["partnership", "email", "address", "website", "phone_number", "companyNIF"]


# =======================
# DOCUMENT SERIALIZERS
# =======================


class DocumentCreateSerializer(serializers.ModelSerializer):
    issued_driver = serializers.PrimaryKeyRelatedField(queryset=Driver.objects.all(), allow_null=True, required=False)
    issued_vehicle = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(), allow_null=True, required=False
    )
    issuing_authority = serializers.PrimaryKeyRelatedField(
        queryset=Partner.objects.all(), allow_null=True, required=False
    )
    exp_begin_date = serializers.DateField(required=False)
    exp_end_date = serializers.DateField(required=False)

    class Meta:
        model = Document
        fields = [
            "name",
            "document_type",
            "document_category",
            "issued_vehicle",
            "issued_driver",
            "is_renewable",
            "validity_period",
            "renewal_frequency",
            "issuing_authority",
            "exp_begin_date",
            "exp_end_date",
        ]


# ===============================
# VEHICLE MAINTENANCE SERIALIZERS
# ================================


class VehicleMaintenanceSerializer(serializers.ModelSerializer):
    issue_reports = serializers.PrimaryKeyRelatedField(
        queryset=IssueReport.objects.filter(is_fixed=False), many=True, read_only=False
    )
    partner = serializers.PrimaryKeyRelatedField(queryset=Partner.objects.all(), allow_null=True, required=False)

    class Meta:
        model = VehicleMaintenance
        fields = ["name", "issue_reports", "maintenance_begin_date", "partner"]


class DocumentListSerializer(serializers.ModelSerializer):
    issued_driver = DriverSerializer(read_only=True)
    issued_vehicle = VehicleSerializer(read_only=True)
    issuing_authority = PartnerListSerializer(read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "name",
            "document_type",
            "document_category",
            "issued_to",
            "issued_vehicle",
            "issued_driver",
            "is_renewable",
            "validity_period",
            "renewal_frequency",
            "issuing_authority",
            "exp_begin_date",
            "exp_end_date",
        ]


class IssueReportSerializer(serializers.ModelSerializer):
    name = serializers.CharField(allow_null=True, required=False)
    vehicle = serializers.PrimaryKeyRelatedField(queryset=Vehicle.objects.all(), read_only=False)

    class Meta:
        model = IssueReport
        fields = ["name", "vehicle", "issue_cost", "priority", "description"]

    # def validate_vehicle(self, obj):
    #
    #     ACTIVE = VehicleDriverAssignment.AssignmentStatus.ACTIVE
    #     try:
    #         request = self.context.get("request")
    #         user = request.user
    #
    #         if user.driver:
    #             vehicles = Vehicle.objects.filter(assignment__driver=user.driver, assignment__assignment_status=ACTIVE)
    #             if vehicles.exists():
    #                 vehicles.get(id=self.vehicle)
    #                 return self.vehicle
    #             raise serializers.ValidationError("You do not have access to report that vehicle")
    #         elif user.technician:
    #             vehicles = Vehicle.objects.filter(managing_technician=user.technician)
    #             if vehicles.exists():
    #                 vehicles.get(id=self.vehicle)
    #                 return self.vehicle
    #             raise serializers.ValidationError("You do not have access to report that vehicle")
    #
    #         raise serializers.ValidationError("You do not have access to report that vehicle")
    #
    #     except (Vehicle.DoesNotExist, Driver.DoesNotExist):
    #         raise serializers.ValidationError("Could not report that vehicle. Try again later.")


class ListIssueReportSerializer(IssueReportSerializer):
    vehicle = VehicleSerializer(read_only=True)

    class Meta(IssueReportSerializer.Meta):
        model = IssueReport
        fields = ["id"] + IssueReportSerializer.Meta.fields

    def validate_name(self, obj):
        if not self.name:
            self.name = "Issue Report"
        return self.name
