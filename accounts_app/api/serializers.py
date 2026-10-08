from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidCredentials(APIException):
    """Represent a generic authentication failure."""

    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Invalid credentials."


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate registration data and create a user account."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        """Configure the user model fields used for registration."""

        model = User
        fields = ["username", "email", "password", "confirmed_password"]

    def validate_email(self, value):
        """Reject email addresses that are already registered."""

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def validate(self, attributes):
        """Ensure that both supplied passwords match."""

        if attributes["password"] != attributes["confirmed_password"]:
            raise serializers.ValidationError(
                {"confirmed_password": "Passwords do not match."}
            )
        return attributes

    def create(self, validated_data):
        """Create a user without persisting the confirmation password."""

        validated_data.pop("confirmed_password")
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Validate credentials and provide the authenticated user."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attributes):
        """Authenticate the supplied username and password."""

        user = authenticate(
            username=attributes["username"],
            password=attributes["password"],
        )
        if user is None:
            raise InvalidCredentials
        attributes["user"] = user
        return attributes


class UserResponseSerializer(serializers.ModelSerializer):
    """Serialize public user data for authentication responses."""

    class Meta:
        """Configure public user response fields."""

        model = User
        fields = ["id", "username", "email"]


class DetailResponseSerializer(serializers.Serializer):
    """Serialize a response containing a detail message."""

    detail = serializers.CharField()


class LoginResponseSerializer(DetailResponseSerializer):
    """Serialize login details together with public user data."""

    user = UserResponseSerializer()
