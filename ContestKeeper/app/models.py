from django.db import models
from django.contrib.auth.models import AbstractUser

class Contest(models.Model):
    name = models.CharField(max_length=20)
    description = models.TextField(max_length=200)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

class User(AbstractUser):
    first_name = None
    last_name = None

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        JUDGE = "JUDGE", "Judge"
        PARTICIPANT = "PARTICIPANT", "Participant"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PARTICIPANT)

    def __str__(self):
        return self.username

    def is_admin(self):
        return self.role == self.Role.ADMIN

    def is_judge(self):
        return self.role == self.Role.JUDGE

    def is_participant(self):
        return self.role == self.Role.PARTICIPANT