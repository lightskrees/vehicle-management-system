from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from api.views import TokenPairView

urlpatterns = [
    path('auth/', include('rest_framework.urls')),
    path('token/', TokenPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
