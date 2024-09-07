from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from api.views import TokenPairView
from api.views import AddUserView, RegisterDriverView

urlpatterns = [
    path('user/add-user/', AddUserView.as_view(), name='add_user'),
    path('driver/register-driver/', RegisterDriverView.as_view(), name='register_driver'),
    path('auth/', include('rest_framework.urls')),
    path('token/', TokenPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
