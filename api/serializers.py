from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from authentication.models import AppUser, Driver
from management.models import Vehicle, VehicleDriverAssignment, VehicleTechnician


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ["email", "first_name", "last_name", "email", "is_active"]


class AddUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ("first_name", "last_name", "email", "password", "employeeID")


class DriverSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
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
    # user = serializers.PrimaryKeyRelatedField(queryset=AppUser.objects.all())

    class Meta:
        model = Driver
        fields = ["user", "driving_license_number", "delivery_date", "expiry_date", "driving_license_file"]

    def validate_user(self, value):
        try:
            user = AppUser.objects.get(id=value.id)
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
            return value
        except AppUser.DoesNotExist:
            raise serializers.ValidationError("User account not found.")


class TokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token_data = super().get_token(user)

        token_data["first_name"] = user.first_name
        token_data["last_name"] = user.last_name
        token_data["username"] = user.email

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


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = (
            "make",
            "model",
            "year",
            "vehicle_type",
            "vin_number",
            "vehicle_image",
            "color",
            "license_plate_number",
            "purchase_date",
        )


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
        fields = ("driver", "vehicle", "begin_at", "ends_at")
