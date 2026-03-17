from __future__ import annotations

import re

from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .exceptions import EmailConflict
from .models import Profile, User


_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).+$")


def validate_simple_password(value: str) -> str:
    if len(value) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters.")
    if not _PASSWORD_RE.match(value):
        raise serializers.ValidationError("Password must contain letters and digits.")
    return value


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate_email(self, value: str) -> str:
        value = value.strip().lower()
        if User.objects.filter(email=value).exists():
            raise EmailConflict()
        return value

    def validate_password(self, value: str) -> str:
        return validate_simple_password(value)

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError({"password_confirm": ["Passwords do not match."]})
        return attrs

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]
        user = User.objects.create_user(email=email, password=password)
        Profile.objects.create(user=user)
        return user


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = (attrs.get("email") or "").strip().lower()
        password = attrs.get("password")

        user = User.objects.filter(email=email).first()
        if user and not user.is_active:
            raise PermissionDenied("User is inactive")

        self.user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )
        if self.user is None:
            raise AuthenticationFailed("Invalid email or password")

        refresh = self.get_token(self.user)

        data = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "token_type": "Bearer",
            "expires_in": int(refresh.access_token.lifetime.total_seconds()),
            "user": {"id": str(self.user.id), "email": self.user.email},
        }
        self.user.last_login = timezone.now()
        self.user.save(update_fields=["last_login"])
        return data


class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "avatar_url",
            "birth_date",
            "city",
            "about",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_new_password(self, value: str) -> str:
        return validate_simple_password(value)

    def validate(self, attrs):
        if attrs.get("new_password") != attrs.get("new_password_confirm"):
            raise serializers.ValidationError({"new_password_confirm": ["Passwords do not match."]})
        return attrs
