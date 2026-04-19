from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from app.leaderboard import compute_leaderboard, export_csv, get_missing_scores, save_leaderboard
from app.models import (
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



from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
class ApplicationLogicTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username='org', password='password', role=User.Role.ORGANIZER)
        self.participant = User.objects.create_user(username='parti', password='password', role=User.Role.PARTICIPANT)
        from django.utils import timezone
        self.contest = Contest.objects.create(
            name='Test Contest',
            description='Test description',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=1),
            organizer=self.organizer,
            is_draft=False
        )
        self.client = Client()

    def test_approve_participant_application(self):
        # Create a participant application
        app = Application.objects.create(
            user=self.participant,
            contest=self.contest,
            application_type=Application.Type.PARTICIPANT,
            status=Application.Status.PENDING
        )
        
        # Approve the application
        self.client.force_login(self.organizer)
        url = reverse('approve_application', kwargs={'pk': app.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)
        app.refresh_from_db()
        self.assertEqual(app.status, Application.Status.APPROVED)
        
        # Check if user is added to contest participants
        self.contest.refresh_from_db()
        self.assertIn(self.participant, self.contest.participants.all())

    def test_apply_invalid_type_fails(self):
        self.client.force_login(self.participant)
        url = reverse('apply_to_contest', kwargs={'pk': self.contest.pk, 'app_type': 'invalid_type'})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Application.objects.count(), 0)


