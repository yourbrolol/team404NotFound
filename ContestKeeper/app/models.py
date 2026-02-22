from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    first_name = None
    last_name = None

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        ORGANIZER = "ORGANIZER", "Organizer"
        JURY = "JURY", "Jury"
        PARTICIPANT = "PARTICIPANT", "Participant"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PARTICIPANT)

    def __str__(self):
        return self.username

    def is_admin(self):
        return self.role == self.Role.ADMIN

    def is_organizer(self):
        return self.role == self.Role.ORGANIZER

    def is_jury(self):
        return self.role == self.Role.JURY

    def is_participant(self):
        return self.role == self.Role.PARTICIPANT

class Contest(models.Model):
    name = models.CharField(max_length=20)
    description = models.TextField(max_length=200)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_contests", null=True, blank=True)
    jury = models.ManyToManyField(User, related_name="judged_contests", blank=True)
    participants = models.ManyToManyField(User, related_name="participated_contests", blank=True)

    def __str__(self):
        return self.name