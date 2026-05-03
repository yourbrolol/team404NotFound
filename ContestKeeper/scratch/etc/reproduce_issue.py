import os
import django
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ContestKeeper.settings")
django.setup()

from app.models import User, Contest, Team, Round, Submission

class JuryVisibilityTest(TestCase):
    def setUp(self):
        self.password = "pass123"
        # Create a user with role PARTICIPANT
        self.jury_user = User.objects.create_user(
            username="test_jury",
            password=self.password,
            role=User.Role.PARTICIPANT
        )
        self.organizer = User.objects.create_user(
            username="organizer",
            password=self.password,
            role=User.Role.ORGANIZER
        )
        
        now = timezone.now()
        self.contest = Contest.objects.create(
            name="Test Contest",
            start_date=now,
            end_date=now + timedelta(days=1),
            organizer=self.organizer,
            is_draft=False
        )
        # Add user to contest.jurys relationship
        self.contest.jurys.add(self.jury_user)
        
        self.team = Team.objects.create(name="Test Team")
        self.contest.teams.add(self.team)
        
        self.round = Round.objects.create(
            contest=self.contest,
            title="Round 1",
            start_time=now,
            deadline=now + timedelta(hours=1),
            status=Round.Status.ACTIVE,
            order=1
        )
        
        self.submission = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url="https://github.com",
            video_url="https://youtube.com"
        )
        
    def test_jury_button_visibility(self):
        client = Client()
        client.login(username="test_jury", password=self.password)
        
        url = reverse('submission_detail', kwargs={
            'pk': self.contest.pk,
            'round_id': self.round.pk,
            'sub_pk': self.submission.pk
        })
        
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Check if "Evaluate" button is present
        # In the template: {% if user.is_jury or user.is_organizer %}
        # Since user.role is PARTICIPANT, is_jury() returns False.
        # But they ARE in contest.jurys.
        
        self.assertNotContains(response, 'Evaluate')
        print("Confirmed: 'Evaluate' button NOT found for jury with PARTICIPANT role.")

if __name__ == "__main__":
    from django.core.management import call_command
    call_command('test', 'JuryVisibilityTest')
