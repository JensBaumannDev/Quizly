from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .documentation import (
    LOGIN_DOCUMENTATION,
    LOGOUT_DOCUMENTATION,
    REFRESH_DOCUMENTATION,
    REGISTER_DOCUMENTATION,
)
from .serializers import LoginSerializer, RegistrationSerializer
from .utils import (
    build_user_data,
    clear_auth_cookies,
    get_refresh_token,
    set_access_cookie,
    set_auth_cookies,
)


class RegisterView(APIView):
    """Create new user accounts."""

    permission_classes = [AllowAny]

    @REGISTER_DOCUMENTATION
    def post(self, request):
        """Validate registration data and create a user."""

        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_data = {"detail": "User created successfully!"}
        return Response(response_data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Authenticate users and issue JWT cookies."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @LOGIN_DOCUMENTATION
    def post(self, request):
        """Validate credentials and return authenticated user data."""

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = RefreshToken.for_user(serializer.validated_data["user"])
        response_data = {
            "detail": "Login successfully!",
            "user": build_user_data(serializer.validated_data["user"]),
        }
        response = Response(response_data, status=status.HTTP_200_OK)
        set_auth_cookies(response, refresh_token)
        return response


class RefreshView(APIView):
    """Issue a new access token from a valid refresh cookie."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @REFRESH_DOCUMENTATION
    def post(self, request):
        """Refresh the access cookie or reject an invalid token."""

        refresh_token = get_refresh_token(request)
        if refresh_token is None:
            response_data = {"detail": "Invalid refresh token."}
            return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)
        response = Response({"detail": "Token refreshed"}, status=status.HTTP_200_OK)
        set_access_cookie(response, refresh_token.access_token)
        return response


class LogoutView(APIView):
    """Blacklist refresh tokens and clear authentication cookies."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @LOGOUT_DOCUMENTATION
    def post(self, request):
        """Invalidate the refresh token and log the user out."""
        refresh_token = get_refresh_token(request)
        if refresh_token is None:
            response_data = {"detail": "Invalid refresh token."}
            return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)
        refresh_token.blacklist()
        response_data = {
            "detail": "Log-Out successfully! All Tokens will be deleted. "
            "Refresh token is now invalid."
        }
        response = Response(response_data, status=status.HTTP_200_OK)
        clear_auth_cookies(response)
        return response
