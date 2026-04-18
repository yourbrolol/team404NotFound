from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Application,
    Contest,
    ContestEvaluationPhase,
    JuryScore,
    LeaderboardEntry,
    Round,
    ScoringCriterion,
    Submission,
    Team,
    User,
)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "role", "is_staff"]
    list_filter = ["role", "is_staff", "is_superuser", "is_active"]
    fieldsets = (
        (None, {"fields": ("username", "email", "first_name", "last_name", "password")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )
    add_fieldsets = (
        (None, {"fields": ("username", "email", "password1", "password2")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")})
    )

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "organization", "captain"]
    search_fields = ["name", "organization"]
    fieldsets = (
        (None, {"fields": ("name", "description", "organization")}),
        ("Social Links", {"fields": ("telegram_link", "discord_link", "website_link")}),
        ("Members", {"fields": ("captain", "participants", "blacklisted_members")}),
    )
    filter_horizontal = ["participants", "blacklisted_members"]

@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ["name", "organizer", "status", "start_date", "end_date"]
    list_filter = ["status", "start_date", "end_date"]
    search_fields = ["name", "description"]
    filter_horizontal = ["jurys", "participants", "teams"]
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

@admin.register(ScoringCriterion)
class ScoringCriterionAdmin(admin.ModelAdmin):
    list_display = ["name", "contest", "max_score", "weight", "aggregation_type", "order"]
    list_filter = ["contest", "aggregation_type"]
    search_fields = ["name", "contest__name"]
    ordering = ["contest", "order", "id"]

@admin.register(JuryScore)
class JuryScoreAdmin(admin.ModelAdmin):
    list_display = ["contest", "team", "criterion", "jury_member", "score", "updated_at"]
    list_filter = ["contest", "criterion", "jury_member"]
    search_fields = ["team__name", "jury_member__username", "criterion__name", "contest__name"]
    readonly_fields = ["created_at", "updated_at"]

@admin.register(ContestEvaluationPhase)
class ContestEvaluationPhaseAdmin(admin.ModelAdmin):
    list_display = ["contest", "status", "trigger_type", "all_scores_complete", "show_jury_breakdown_to_participants", "completed_at"]
    list_filter = ["status", "trigger_type", "all_scores_complete", "show_jury_breakdown_to_participants"]
    search_fields = ["contest__name"]

@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = ["contest", "team", "rank", "total_score", "is_tied", "computation_complete", "updated_at"]
    list_filter = ["contest", "is_tied", "computation_complete"]
    search_fields = ["contest__name", "team__name"]
    readonly_fields = ["updated_at", "category_scores", "jury_breakdown", "missing_scores"]

@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ["title", "contest", "status", "order", "deadline"]
    list_filter = ["status", "contest", "created_at"]
    search_fields = ["title", "description", "contest__name"]
    readonly_fields = ["status", "created_at"]
    fieldsets = (
        (None, {"fields": ("title", "description", "tech_requirements", "contest", "order")}),
        ("Status", {"fields": ("status",)}),
        ("Timeline", {"fields": ("start_time", "deadline", "created_at")}),
        ("Checklist & Materials", {"fields": ("must_have", "materials")}),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.status != "DRAFT":
            readonly.extend(["title", "description", "tech_requirements", "start_time", "must_have"])
        return readonly

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["team", "round", "submitted_at", "updated_at"]
    list_filter = ["round__contest", "round"]
    search_fields = ["team__name", "round__title"]
    readonly_fields = ["submitted_at", "updated_at"]
