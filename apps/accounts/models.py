from __future__ import annotations

from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar_url = models.FileField(upload_to="avatars/", blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=120, blank=True)
    about = models.TextField(max_length=1000, blank=True)
    university = models.CharField(max_length=200, blank=True)
    skills = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Profile({self.user_id})"
