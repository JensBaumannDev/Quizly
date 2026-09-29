from django.contrib.auth.models import User
from rest_framework import serializers


class RegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "confirmed_password"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def validate(self, attributes):
        if attributes["password"] != attributes["confirmed_password"]:
            raise serializers.ValidationError({"confirmed_password": "Passwords do not match."})
        return attributes

    def create(self, validated_data):
        validated_data.pop("confirmed_password")
        return User.objects.create_user(**validated_data)
