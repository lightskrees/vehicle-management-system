from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from api.views import (
    AddUserView,
    CustomVehicleList,
    DocumentManagementViewSet,
    DriverListView,
    DriverViewSet,
    FuelViewSet,
    IssueReportViewSet,
    PartnerConfigurationViewSet,
    PartnershipManagementViewSet,
    RegisterDriverApiView,
    SystemDashboardView,
    TokenPairView,
    UserAPIViewSet,
    VehicleAssignmentsManagementViewSet,
    VehicleDriverAssignmentCreationView,
    VehicleMaintenanceViewSet,
    VehicleTechnicianViewSet,
    VehicleViewSet,
)

router = DefaultRouter(trailing_slash=False)
router.register(r"driver", DriverViewSet, basename="driver")
router.register(r"vehicle-technician", VehicleTechnicianViewSet, basename="vehicle-technician")
router.register("vehicle", VehicleViewSet, basename="vehicle")
router.register("registerDriver", RegisterDriverApiView, basename="register-user-driver")
router.register("fuel", FuelViewSet, basename="register-fuel")

# PARTNER MANAGEMENT URLs
router.register("manage/partnerships", PartnershipManagementViewSet, basename="partnership")
router.register(r"manage/partners", PartnerConfigurationViewSet, basename="partners")

# DOCUMENT MANAGEMENT URLs
router.register(r"manage/documents", DocumentManagementViewSet, basename="documents")
router.register(r"manage/users", UserAPIViewSet, basename="manage-users")

# DRIVER-VEHICLE ASSIGNMENTS
router.register(r"manage/assignments", VehicleAssignmentsManagementViewSet, basename="manage-assignments")

# VEHICLE MAINTENANCES
router.register(r"manage/vehicle/maintenances", VehicleMaintenanceViewSet, basename="vehicle-maintenances")


# ISSUE REPORTS
router.register(r"manage/issue-reports", IssueReportViewSet, basename="issue-reports")

urlpatterns = [
    path("user/add-user/", AddUserView.as_view(), name="add_user"),
    path("driver/list/", DriverListView.as_view(), name="driver-list"),
    path("vehicles-access/", CustomVehicleList.as_view(), name="custom-vehicles-list"),
    path(
        "vehicle/driver-assignment/", VehicleDriverAssignmentCreationView.as_view(), name="vehicle-driver-assignment"
    ),
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls")),
    path("login/", TokenPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # path("registerDriver/", RegisterDriverApiView.as_view(), name="register-driver"),
    #######################
    # DASHBOARD VIEW
    #####################
    path("dashboard/", SystemDashboardView.as_view(), name="system-dashboard"),
]
