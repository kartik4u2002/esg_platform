from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.tenancy.models import Organization, User


class OrganizationSerializer(serializers.ModelSerializer):
    """Read-only serializer for Organization."""

    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'is_active', 'created_at']
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User profile data."""

    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'organization']
        read_only_fields = ['id', 'username', 'email', 'role', 'organization']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends the default JWT token serializer to embed extra claims
    (user_id, email, role, organization_id) in the token and include
    user data in the response body.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Custom claims
        token['user_id'] = str(user.id)
        token['email'] = user.email
        token['role'] = user.role
        token['organization_id'] = str(user.organization_id) if user.organization_id else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user info to the response body alongside access/refresh tokens
        data['user'] = UserSerializer(self.user).data
        return data


class LoginSerializer(serializers.Serializer):
    """Serializer for the login request body (documentation purposes)."""

    username = serializers.CharField(required=True, help_text='Username or email')
    password = serializers.CharField(required=True, style={'input_type': 'password'})
