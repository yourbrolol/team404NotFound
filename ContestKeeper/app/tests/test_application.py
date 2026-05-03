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

    def test_apply_participant_twice_fails(self):
        """Test that participant applications are disabled"""
        self.client.force_login(self.participant)
        url = reverse('apply_to_contest', kwargs={'pk': self.contest.pk, 'app_type': 'participant'})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Application.objects.count(), 0)

    def test_apply_jury_twice_fails(self):
        """Test that applying as jury twice gets the existing application"""
        jury_user = User.objects.create_user(username='jury_app', password='password', role=User.Role.JURY)
        
        # First application
        Application.objects.create(
            user=jury_user,
            contest=self.contest,
            application_type=Application.Type.JURY,
            status=Application.Status.PENDING
        )
        
        # Try second application - get_or_create should get existing
        self.client.force_login(jury_user)
        url = reverse('apply_to_contest', kwargs={'pk': self.contest.pk, 'app_type': 'jury'})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertEqual(Application.objects.filter(user=jury_user, contest=self.contest).count(), 1)

    def test_apply_as_participant_when_already_jury_fails(self):
        """Test that a user cannot apply as participant if already applied as jury"""
        jury_user = User.objects.create_user(username='jury_part', password='password', role=User.Role.JURY)
        
        # First application as jury
        Application.objects.create(
            user=jury_user,
            contest=self.contest,
            application_type=Application.Type.JURY,
            status=Application.Status.PENDING
        )
        
        # Try application as participant
        self.client.force_login(jury_user)
        url = reverse('apply_to_contest', kwargs={'pk': self.contest.pk, 'app_type': 'participant'})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Application.objects.filter(user=jury_user, contest=self.contest).count(), 1)

    def test_apply_as_jury_when_already_participant_fails(self):
        """Test that participant applications are disabled but jury applications work"""
        # First try participant application (disabled)
        self.client.force_login(self.participant)
        url = reverse('apply_to_contest', kwargs={'pk': self.contest.pk, 'app_type': 'participant'})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 403)
        
        # Now try jury application (should work)
        jury_user = User.objects.create_user(username='jury_part', password='password', role=User.Role.JURY)
        self.client.force_login(jury_user)
        url = reverse('apply_to_contest', kwargs={'pk': self.contest.pk, 'app_type': 'jury'})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Application.objects.filter(user=jury_user, contest=self.contest).count(), 1)

    def test_approve_application_wrong_organizer_fails(self):
        """Test that only the contest organizer can approve applications"""
        other_organizer = User.objects.create_user(username='other_org', password='password', role=User.Role.ORGANIZER)
        
        app = Application.objects.create(
            user=self.participant,
            contest=self.contest,
            application_type=Application.Type.PARTICIPANT,
            status=Application.Status.PENDING
        )
        
        # Try to approve with wrong organizer
        self.client.force_login(other_organizer)
        url = reverse('approve_application', kwargs={'pk': app.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)  # Redirect
        app.refresh_from_db()
        self.assertEqual(app.status, Application.Status.PENDING)  # No change

    def test_approve_already_approved_application_no_change(self):
        """Test that approving an already approved application doesn't change anything"""
        app = Application.objects.create(
            user=self.participant,
            contest=self.contest,
            application_type=Application.Type.PARTICIPANT,
            status=Application.Status.APPROVED
        )
        
        self.client.force_login(self.organizer)
        url = reverse('approve_application', kwargs={'pk': app.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)
        app.refresh_from_db()
        self.assertEqual(app.status, Application.Status.APPROVED)

    def test_approve_rejected_application_no_change(self):
        """Test that approving a rejected application changes status to approved"""
        app = Application.objects.create(
            user=self.participant,
            contest=self.contest,
            application_type=Application.Type.PARTICIPANT,
            status=Application.Status.REJECTED
        )
        
        self.client.force_login(self.organizer)
        url = reverse('approve_application', kwargs={'pk': app.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)
        app.refresh_from_db()
        self.assertEqual(app.status, Application.Status.APPROVED)  # Status changes

    def test_apply_to_draft_contest_fails(self):
        """Test that applications to draft contests are not allowed"""
        draft_contest = Contest.objects.create(
            name='Draft Contest',
            description='Draft description',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=1),
            organizer=self.organizer,
            is_draft=True
        )
        
        self.client.force_login(self.participant)
        url = reverse('apply_to_contest', kwargs={'pk': draft_contest.pk, 'app_type': 'participant'})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Application.objects.count(), 0)

    def test_apply_as_organizer_fails(self):
        """Test that organizers cannot apply to their own contests"""
        self.client.force_login(self.organizer)
        url = reverse('apply_to_contest', kwargs={'pk': self.contest.pk, 'app_type': 'participant'})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Application.objects.count(), 0)

    def test_apply_with_invalid_contest_id_fails(self):
        """Test that applying to non-existent contest fails"""
        self.client.force_login(self.participant)
        url = reverse('apply_to_contest', kwargs={'pk': 99999, 'app_type': 'participant'})
        response = self.client.post(url)  # POST request
        
        self.assertEqual(response.status_code, 404)


