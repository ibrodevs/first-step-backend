from __future__ import annotations

import json
import re

from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken

from .exceptions import EmailConflict
from .models import Profile

User = get_user_model()


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
        if User.objects.filter(username=value).exists() or User.objects.filter(email=value).exists():
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
        user = User.objects.create_user(username=email, email=email, password=password)
        Profile.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = (attrs.get("email") or "").strip().lower()
        password = attrs.get("password")

        user = User.objects.filter(username=email).first() or User.objects.filter(email=email).first()
        if user and not user.is_active:
            raise PermissionDenied("User is inactive")

        authenticated_user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )
        if authenticated_user is None:
            raise AuthenticationFailed("Invalid email or password")

        self.user = authenticated_user

        refresh = RefreshToken.for_user(authenticated_user)
        data = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "token_type": "Bearer",
            "expires_in": int(refresh.access_token.lifetime.total_seconds()),
            "user": {"id": str(authenticated_user.id), "email": authenticated_user.email},
        }

        authenticated_user.last_login = timezone.now()
        authenticated_user.save(update_fields=["last_login"])
        return data


class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class FlexibleStringListField(serializers.ListField):
        child = serializers.CharField()

        def to_internal_value(self, data):
            if data is None or data == "":
                data = []
            elif isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    data = [s.strip() for s in data.split(",") if s.strip()]
            return super().to_internal_value(data)

    avatar_url = serializers.FileField(required=False, allow_null=True)
    skills = FlexibleStringListField(required=False)

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
            "university",
            "skills",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        avatar = data.get("avatar_url")
        if request and isinstance(avatar, str) and avatar and avatar.startswith("/"):
            data["avatar_url"] = request.build_absolute_uri(avatar)
        return data


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
