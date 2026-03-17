from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "first_name", "last_name", "city", "updated_at")
    search_fields = ("user__username", "user__email", "first_name", "last_name")
