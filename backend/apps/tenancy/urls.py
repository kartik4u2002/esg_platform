from django.urls import path

from apps.tenancy.views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    UserProfileView,
)

app_name = 'tenancy'

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
]
