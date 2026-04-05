from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    first_name = None
    last_name = None

    class Role(models.TextChoices):
        ORGANIZER = "ORGANIZER", "Organizer"
        JURY = "JURY", "Jury"
        PARTICIPANT = "PARTICIPANT", "Participant"

    username = models.CharField(max_length=20, unique=True)
    bio = models.CharField(max_length=200, blank=True)
    role = models.CharField(choices=Role.choices, default=Role.PARTICIPANT)

    def __str__(self):
        return self.username

    def is_organizer(self):
        return self.role == self.Role.ORGANIZER

    def is_jury(self):
        return self.role == self.Role.JURY

    def is_participant(self):
        return self.role == self.Role.PARTICIPANT

class Team(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
    
    name = models.CharField(max_length=20)
    description = models.TextField(max_length=200, blank=True)
    status = models.CharField(choices=Status.choices, default=Status.DRAFT)
    participants = models.ManyToManyField(User, related_name="participated_teams")
    captain = models.ForeignKey(User, on_delete=models.CASCADE, related_name="captained_teams", null=True, blank=True)
    blacklisted_members = models.ManyToManyField(User, related_name="blacklisted_from_teams", blank=True)
    
    def __str__(self):
        return f"Team {self.name}."

class Contest(models.Model):
    def save(self, *args, **kwargs):
        from django.utils import timezone
        now = timezone.now()
        if self.is_draft:
            self.status = self.Status.DRAFT
        else:
            if self.start_date and self.start_date <= now:
                if self.end_date and self.end_date < now:
                    self.status = self.Status.FINISHED
                else:
                    self.status = self.Status.RUNNING
            else:
                self.status = self.Status.REGISTRATION
        super().save(*args, **kwargs)
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        REGISTRATION = "REGISTRATION", "Registration"
        RUNNING = "RUNNING", "Running"
        FINISHED = "FINISHED", "Finished"

    name = models.CharField(max_length=20)
    description = models.TextField(max_length=200)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_contests", null=True, blank=True)
    status = models.CharField(choices=Status.choices, default=Status.DRAFT)
    is_draft = models.BooleanField(default=True)
    jurys = models.ManyToManyField(User, related_name="judged_contests", blank=True)
    participants = models.ManyToManyField(User, related_name="participated_contests", blank=True)
    teams = models.ManyToManyField(Team, related_name="teams_in_contests", blank=True)

    def __str__(self):
        return self.name

class Application(models.Model):
    class Type(models.TextChoices):
        JURY = "JURY", "Jury"
        TEAM = "TEAM", "Team"
        PARTICIPANT = "PARTICIPANT", "Participant"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submitted_apps")
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="contest_apps", null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_apps", null=True, blank=True)
    application_type = models.CharField(choices=Type.choices)
    status = models.CharField(choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'contest', 'application_type')

    def __str__(self):
        return f"{self.user.username} - {self.contest.name} ({self.application_type})"


class ScoringCriterion(models.Model):
    class AggregationType(models.TextChoices):
        SUM = "SUM", "Sum"
        AVERAGE = "AVERAGE", "Average"

    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="scoring_criteria")
    name = models.CharField(max_length=50)
    max_score = models.FloatField(default=100)
    weight = models.FloatField(default=1.0)
    aggregation_type = models.CharField(max_length=7, choices=AggregationType.choices, default=AggregationType.SUM)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["contest", "order", "name"]
        unique_together = ("contest", "name")

    def __str__(self):
        return f"{self.contest.name} - {self.name}"


class JuryScore(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="jury_scores")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="jury_scores")
    jury_member = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scores_given")
    criterion = models.ForeignKey(ScoringCriterion, on_delete=models.CASCADE, related_name="scores")
    score = models.FloatField(default=0)

    class Meta:
        unique_together = ("contest", "team", "jury_member", "criterion")

    def __str__(self):
        return f"{self.contest.name} / {self.team.name} / {self.criterion.name} by {self.jury_member.username}"


class ContestEvaluationPhase(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "NOT_STARTED", "Not started"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        COMPLETED = "COMPLETED", "Completed"

    class TriggerType(models.TextChoices):
        AUTO = "AUTO", "Automatic"
        MANUAL = "MANUAL", "Manual"

    contest = models.OneToOneField(Contest, on_delete=models.CASCADE, related_name="evaluation_phase")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NOT_STARTED)
    trigger_type = models.CharField(max_length=6, choices=TriggerType.choices, default=TriggerType.AUTO)
    all_scores_complete = models.BooleanField(default=False)
    show_jury_breakdown_to_participants = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.contest.name} evaluation phase"


class LeaderboardEntry(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="leaderboard_entries")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="leaderboard_entries")
    rank = models.PositiveIntegerField(default=0)
    total_score = models.FloatField(default=0)
    is_tied = models.BooleanField(default=False)
    category_scores = models.JSONField(default=dict, blank=True)
    jury_breakdown = models.JSONField(default=dict, blank=True)
    missing_scores = models.JSONField(default=list, blank=True)
    computation_complete = models.BooleanField(default=False)

    class Meta:
        unique_together = ("contest", "team")
        ordering = ["contest", "rank", "team__name"]

    def __str__(self):
        return f"{self.contest.name} - {self.team.name}"

    @property
    def rank_display(self):
        return f"{self.rank}{' (tied)' if self.is_tied else ''}"


class Round(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        SUBMISSION_CLOSED = "SUBMISSION_CLOSED", "Submission Closed"
        EVALUATED = "EVALUATED", "Evaluated"

    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="rounds")
    title = models.CharField(max_length=200)
    description = models.TextField()
    tech_requirements = models.TextField()
    must_have = models.JSONField(default=list, help_text="List of required checklist items")
    start_time = models.DateTimeField()
    deadline = models.DateTimeField()
    materials = models.JSONField(default=list, blank=True, help_text="List of {label, url}")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    order = models.PositiveIntegerField(default=0, help_text="Round number within contest")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_rounds")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["contest", "order", "created_at"]
        unique_together = ("contest", "order")

    def __str__(self):
        return f"{self.contest.name} - Round {self.order}: {self.title}"

    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return self.status == self.Status.ACTIVE and self.start_time <= now

    def is_open(self):
        """Check if the round is open for submissions (ACTIVE status, deadline not passed)"""
        from django.utils import timezone
        now = timezone.now()
        return self.status == self.Status.ACTIVE and self.start_time <= now and self.deadline > now

    def time_remaining(self):
        from django.utils import timezone
        now = timezone.now()
        if self.deadline <= now:
            return None
        return self.deadline - now
