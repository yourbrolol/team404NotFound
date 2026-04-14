from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class Role(models.TextChoices):
        ORGANIZER = "ORGANIZER", _("Organizer")
        JURY = "JURY", _("Jury")
        PARTICIPANT = "PARTICIPANT", _("Participant")

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

    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Draft")
        ACTIVE = "ACTIVE", _("Active")
    
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
        DRAFT = "DRAFT", _("Draft")
        REGISTRATION = "REGISTRATION", _("Registration")
        RUNNING = "RUNNING", _("Running")
        FINISHED = "FINISHED", _("Finished")

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
        JURY = "JURY", _("Jury")
        TEAM = "TEAM", _("Team")
        PARTICIPANT = "PARTICIPANT", _("Participant")

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        APPROVED = "APPROVED", _("Approved")
        REJECTED = "REJECTED", _("Rejected")

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
        SUM = "SUM", _("Sum")
        AVERAGE = "AVERAGE", _("Average")

    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="scoring_criteria")
    name = models.CharField(max_length=100)
    max_score = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(1)],
    )
    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    aggregation_type = models.CharField(
        max_length=10,
        choices=AggregationType.choices,
        default=AggregationType.AVERAGE,
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("contest", "name")

    def __str__(self):
        return f"{self.contest.name}: {self.name}"


class JuryScore(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="jury_scores")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="jury_scores")
    jury_member = models.ForeignKey(User, on_delete=models.CASCADE, related_name="jury_scores_given")
    criterion = models.ForeignKey(ScoringCriterion, on_delete=models.CASCADE, related_name="jury_scores")
    score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("contest", "team", "jury_member", "criterion")
        ordering = ["contest_id", "team_id", "criterion__order", "jury_member_id"]

    def clean(self):
        errors = {}

        if self.criterion_id and self.contest_id and self.criterion.contest_id != self.contest_id:
            errors["criterion"] = "Criterion must belong to the same contest."

        if self.team_id and self.contest_id and not self.contest.teams.filter(pk=self.team_id).exists():
            errors["team"] = "Team must belong to the selected contest."

        if self.jury_member_id and self.contest_id and not self.contest.jurys.filter(pk=self.jury_member_id).exists():
            errors["jury_member"] = "Jury member must be assigned to the selected contest."

        if self.criterion_id and self.score is not None and self.score > Decimal(str(self.criterion.max_score)):
            errors["score"] = f"Score cannot exceed the criterion maximum of {self.criterion.max_score}."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.jury_member.username} -> {self.team.name} ({self.criterion.name})"


class ContestEvaluationPhase(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "NOT_STARTED", _("Not started")
        IN_PROGRESS = "IN_PROGRESS", _("In progress")
        COMPLETED = "COMPLETED", _("Completed")

    class TriggerType(models.TextChoices):
        AUTO = "AUTO", _("Automatic")
        MANUAL = "MANUAL", _("Manual")

    contest = models.OneToOneField(Contest, on_delete=models.CASCADE, related_name="evaluation_phase")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    trigger_type = models.CharField(max_length=10, choices=TriggerType.choices, default=TriggerType.AUTO)
    all_scores_complete = models.BooleanField(default=False)
    show_jury_breakdown_to_participants = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Evaluation phase for {self.contest.name}"


class LeaderboardEntry(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="leaderboard_entries")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="leaderboard_entries")
    rank = models.PositiveIntegerField()
    total_score = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    is_tied = models.BooleanField(default=False)
    category_scores = models.JSONField(default=dict, blank=True)
    jury_breakdown = models.JSONField(default=dict, blank=True)
    missing_scores = models.JSONField(default=list, blank=True)
    computation_complete = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["rank", "-total_score", "team__name"]
        unique_together = ("contest", "team")

    def __str__(self):
        return f"{self.contest.name} #{self.rank} - {self.team.name}"

    @property
    def rank_display(self):
        return f"{self.rank}{' (tied)' if self.is_tied else ''}"


class Round(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Draft")
        ACTIVE = "ACTIVE", _("Active")
        SUBMISSION_CLOSED = "SUBMISSION_CLOSED", _("Submission Closed")
        EVALUATED = "EVALUATED", _("Evaluated")

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
        from django.utils import timezone

        now = timezone.now()
        return self.status == self.Status.ACTIVE and self.start_time <= now and self.deadline > now

    def time_remaining(self):
        from django.utils import timezone

        now = timezone.now()
        if self.deadline <= now:
            return None
        return self.deadline - now


class Submission(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="submissions")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="submissions")
    github_url = models.URLField(help_text="Link to GitHub repository")
    video_url = models.URLField(help_text="Link to video demo (YouTube, Drive, etc.)")
    live_demo_url = models.URLField(blank=True, help_text="Link to live demo (optional)")
    description = models.TextField(max_length=2000, blank=True, help_text="Short description: what was done, how to run")
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('round', 'team')  # one submission per team per round

    def __str__(self):
        return f"{self.team.name} — {self.round.title}"

    @property
    def is_editable(self):
        """A submission is editable while the round is still open for submissions."""
        return self.round.is_open()


class Notification(models.Model):
    class Type(models.TextChoices):
        REGISTRATION_OPEN = "REGISTRATION_OPEN", _("Registration Open")
        ROUND_STARTED = "ROUND_STARTED", _("Round Started")
        DEADLINE_APPROACHING = "DEADLINE_APPROACHING", _("Deadline Approaching")
        SUBMISSIONS_CLOSED = "SUBMISSIONS_CLOSED", _("Submissions Closed")
        EVALUATION_COMPLETE = "EVALUATION_COMPLETE", _("Evaluation Complete")
        APPLICATION_UPDATE = "APPLICATION_UPDATE", _("Application Update")
        ANNOUNCEMENT = "ANNOUNCEMENT", _("Announcement")

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(choices=Type.choices, max_length=30)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True, help_text="URL to navigate to when clicked")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username}: {self.title}"


class Announcement(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="announcements")
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="authored_announcements")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title


class ScheduleEvent(models.Model):
    class EventType(models.TextChoices):
        ROUND = "ROUND", _("Round")
        DEADLINE = "DEADLINE", _("Deadline")
        WORKSHOP = "WORKSHOP", _("Workshop")
        OTHER = "OTHER", _("Other")

    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="schedule_events")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    event_type = models.CharField(max_length=20, choices=EventType.choices, default=EventType.ROUND)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["start_time", "order"]

    def __str__(self):
        return f"{self.contest.name}: {self.title}"
