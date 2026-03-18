from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Contest, User, Application, Team

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "role", "is_staff"]
    list_filter = ["role", "is_staff", "is_superuser", "is_active"]
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )
    add_fieldsets = (
        (None, {"fields": ("username", "email", "password1", "password2")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")})
    )

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]

@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ["name", "organizer", "status", "start_date", "end_date"]
    list_filter = ["status", "start_date", "end_date"]
    search_fields = ["name", "description"]
    filter_horizontal = ["jurys", "participants"]
    fieldsets = (
        (None, {"fields": ("name", "description", "status")}),
        ("Dates", {"fields": ("start_date", "end_date")}),
        ("Roles", {"fields": ("organizer", "jurys", "participants", "teams")})
    )

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["user", "contest", "application_type", "status"]
    list_filter = ["user", "application_type", "created_at", "status", "contest"]
    search_fields = ["user__username", "contest__name"]
    readonly_fields = ["created_at"]
    fieldsets = (
        (None, {"fields": ("user", "team", "contest", "application_type", "status")}),
        ("Dates", {"fields": ["created_at"]})
    )