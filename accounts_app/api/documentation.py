from drf_yasg import openapi
from drf_yasg.utils import no_body, swagger_auto_schema

from .serializers import (
    DetailResponseSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    RegistrationSerializer,
)


PUBLIC_SECURITY = []
COOKIE_SECURITY = [{"CookieAuth": []}]
INTERNAL_ERROR = openapi.Response("Internal server error.")

REGISTER_DOCUMENTATION = swagger_auto_schema(
    operation_summary="Register a user",
    operation_description="Create a new Quizly user account.",
    request_body=RegistrationSerializer,
    responses={
        201: DetailResponseSerializer,
        400: openapi.Response("Invalid registration data."),
        500: INTERNAL_ERROR,
    },
    security=PUBLIC_SECURITY,
    tags=["Authentication"],
)

LOGIN_DOCUMENTATION = swagger_auto_schema(
    operation_summary="Log in a user",
    operation_description="Validate credentials and set JWT cookies.",
    request_body=LoginSerializer,
    responses={
        200: LoginResponseSerializer,
        401: openapi.Response("Invalid credentials."),
        500: INTERNAL_ERROR,
    },
    security=PUBLIC_SECURITY,
    tags=["Authentication"],
)

REFRESH_DOCUMENTATION = swagger_auto_schema(
    operation_summary="Refresh the access token",
    operation_description="Issue an access token from the refresh cookie.",
    request_body=no_body,
    responses={
        200: DetailResponseSerializer,
        401: openapi.Response("Invalid refresh token."),
        500: INTERNAL_ERROR,
    },
    security=COOKIE_SECURITY,
    tags=["Authentication"],
)

LOGOUT_DOCUMENTATION = swagger_auto_schema(
    operation_summary="Log out a user",
    operation_description="Blacklist the refresh token and clear JWT cookies.",
    request_body=no_body,
    responses={
        200: DetailResponseSerializer,
        401: openapi.Response("Invalid refresh token."),
        500: INTERNAL_ERROR,
    },
    security=COOKIE_SECURITY,
    tags=["Authentication"],
)
