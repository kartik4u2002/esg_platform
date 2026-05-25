from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.tenancy.serializers import CustomTokenObtainPairSerializer, UserSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/v1/auth/token/

    Authenticate with username & password. Returns JWT access + refresh tokens
    along with embedded user profile data.
    """

    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    """
    POST /api/v1/auth/token/refresh/

    Submit a valid refresh token to receive a new access token.
    """

    pass


class UserProfileView(generics.RetrieveAPIView):
    """
    GET /api/v1/auth/profile/

    Return the authenticated user's profile.
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
