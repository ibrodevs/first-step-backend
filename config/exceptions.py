from __future__ import annotations

from typing import Any

from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def _normalize_validation(detail: Any) -> dict[str, list[str]]:
    if isinstance(detail, dict):
        return {
            str(field): [str(msg) for msg in (messages if isinstance(messages, list) else [messages])]
            for field, messages in detail.items()
        }
    if isinstance(detail, list):
        return {"non_field_errors": [str(m) for m in detail]}
    return {"non_field_errors": [str(detail)]}


def api_exception_handler(exc: Exception, context: dict) -> Response:
    drf_response = exception_handler(exc, context)

    if drf_response is None:
        if isinstance(exc, Http404):
            payload = {"error": {"code": "not_found", "message": "Not found"}}
            return Response(payload, status=status.HTTP_404_NOT_FOUND)
        payload = {"error": {"code": "server_error", "message": "Internal server error"}}
        return Response(payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    code = "error"
    message = "Request failed"
    fields = None

    if isinstance(exc, exceptions.ValidationError):
        code = "validation_error"
        message = "Validation failed"
        fields = _normalize_validation(drf_response.data)
    elif isinstance(exc, exceptions.AuthenticationFailed):
        code = "auth_failed"
        message = "Invalid credentials"
    elif isinstance(exc, exceptions.NotAuthenticated):
        code = "not_authenticated"
        message = "Authentication credentials were not provided."
    elif isinstance(exc, exceptions.PermissionDenied):
        code = "permission_denied"
        message = str(getattr(exc, "detail", "Permission denied"))
    elif isinstance(exc, exceptions.NotFound):
        code = "not_found"
        message = "Not found"
    elif isinstance(exc, exceptions.Throttled):
        code = "throttled"
        message = "Request was throttled"
    elif isinstance(exc, exceptions.APIException):
        code = getattr(exc, "default_code", "error")
        message = str(getattr(exc, "detail", "Request failed"))

    error: dict[str, Any] = {"code": code, "message": message}
    if fields is not None:
        error["fields"] = fields

    return Response({"error": error}, status=drf_response.status_code)
