from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    first_name = None
    last_name = None

    class Role(models.TextChoices):
        ORGANIZER = "ORGANIZER", "Organizer"
        JURY = "JURY", "Jury"
        PARTICIPANT = "PARTICIPANT", "Participant"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PARTICIPANT)

    def __str__(self):
        return self.username

    def is_organizer(self):
        return self.role == self.Role.ORGANIZER

    def is_jury(self):
        return self.role == self.Role.JURY

    def is_participant(self):
        return self.role == self.Role.PARTICIPANT

class Contest(models.Model):
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
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    jurys = models.ManyToManyField(User, related_name="judged_contests", blank=True)
    participants = models.ManyToManyField(User, related_name="participated_contests", blank=True)

    def __str__(self):
        return self.name

class Application(models.Model):
    class Type(models.TextChoices):
        JURY = "JURY", "Jury"
        PARTICIPANT = "PARTICIPANT", "Participant"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submitted_apps")
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="contest_apps")
    application_type = models.CharField(max_length=20, choices=Type.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'contest', 'application_type')

    def __str__(self):
        return f"{self.user.username} - {self.contest.name} ({self.application_type})"
