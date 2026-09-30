from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, RegistrationSerializer
from .utils import build_user_data, get_refresh_token, set_access_cookie, set_auth_cookies


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "User created successfully!"}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = RefreshToken.for_user(serializer.validated_data["user"])
        response_data = {"detail": "Login successfully!", "user": build_user_data(serializer.validated_data["user"])}
        response = Response(response_data, status=status.HTTP_200_OK)
        set_auth_cookies(response, refresh_token)
        return response


class RefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = get_refresh_token(request)
        if refresh_token is None:
            response_data = {"detail": "Invalid refresh token."}
            return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)
        response = Response({"detail": "Token refreshed"}, status=status.HTTP_200_OK)
        set_access_cookie(response, refresh_token.access_token)
        return response
