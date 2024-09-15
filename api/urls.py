from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from api.views import (
    AddUserView,
    DriverListView,
    DriverViewSet,
    TokenPairView,
    VehicleTechnicianViewSet,
    VehicleViewSet,
)

router = DefaultRouter(trailing_slash=False)
router.register(r"driver", DriverViewSet, basename="driver")
router.register(r"vehicle-technician", VehicleTechnicianViewSet, basename="vehicle-technician")
router.register("vehicle", VehicleViewSet, basename="vehicle")

urlpatterns = [
    path("user/add-user/", AddUserView.as_view(), name="add_user"),
    path("driver/list/", DriverListView.as_view(), name="driver-list"),
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls")),
    path("token/", TokenPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
