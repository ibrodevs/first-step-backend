from __future__ import annotations

import logging
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile, User
from .serializers import ChangePasswordSerializer, LoginSerializer, ProfileSerializer, RegisterSerializer

logger = logging.getLogger(__name__)


class LoginThrottle(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("register success email=%s", user.email)
        return Response(
            {"id": str(user.id), "email": user.email, "created_at": user.date_joined.isoformat().replace("+00:00", "Z")},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        logger.info("login success email=%s", serializer.user.email)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            raise ValidationError({"refresh": ["This field is required."]})

        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except Exception:
            raise ValidationError({"refresh": ["Invalid refresh token."]})

        logger.info("logout success user_id=%s", request.user.id)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    forbidden_fields = {"id", "email", "is_active", "is_staff", "is_superuser"}

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def update(self, request, *args, **kwargs):
        forbidden = sorted(set(request.data.keys()) & self.forbidden_fields)
        if forbidden:
            raise ValidationError({field: ["This field cannot be updated."] for field in forbidden})
        return super().update(request, *args, **kwargs)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            raise ValidationError({"old_password": ["Old password is incorrect."]})

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        try:
            from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

            tokens = OutstandingToken.objects.filter(user=user)
            BlacklistedToken.objects.bulk_create(
                [BlacklistedToken(token=t) for t in tokens if not hasattr(t, "blacklistedtoken")],
                ignore_conflicts=True,
            )
        except Exception:
            pass

        logger.info("password changed user_id=%s", user.id)
        return Response(status=status.HTTP_200_OK)
