from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Contest, User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "role", "is_staff"]
    list_filter = ["role", "is_staff", "is_active"]
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"fields": ("username", "email", "password1", "password2")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
    )


admin.site.register(Contest)
