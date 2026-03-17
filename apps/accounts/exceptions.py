from rest_framework import status
from rest_framework.exceptions import APIException


class EmailConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Email already exists"
    default_code = "email_conflict"
