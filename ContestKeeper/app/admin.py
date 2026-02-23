from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Contest, User, Application

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


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ["name", "status", "organizer", "start_date", "end_date"]
    list_filter = ["status", "start_date", "end_date"]
    search_fields = ["name", "description"]
    filter_horizontal = ["jurys", "participants"]
    fieldsets = (
        (None, {"fields": ("name", "description", "status")}),
        ("Dates", {"fields": ("start_date", "end_date")}),
        ("Roles", {"fields": ("organizer", "jurys", "participants")}),
    )

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["user", "contest", "status"]
    list_filter = ["status", "contest"]
    search_fields = ["user__username", "contest__name"]