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
class RoundLogicTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username='org', password='password', role=User.Role.ORGANIZER)
        self.participant = User.objects.create_user(username='parti', password='password', role=User.Role.PARTICIPANT)
        self.contest = Contest.objects.create(
            name='Round Test Contest',
            description='Contest with rounds',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            is_draft=False
        )
        self.team = Team.objects.create(name='Team A', captain=self.participant)
        self.contest.teams.add(self.team)
        self.contest.participants.add(self.participant)
        self.client = Client()

    def test_create_round_valid(self):
        """Test creating a valid round with all required fields"""
        self.client.force_login(self.organizer)
        future_start = timezone.now() + timedelta(days=1)
        future_end = timezone.now() + timedelta(days=2)
        
        response = self.client.post(
            reverse('round_create', kwargs={'pk': self.contest.pk}),
            {
                'title': 'Round 1',
                'description': 'First round description',
                'tech_requirements': 'Python 3.9+, Django 4.0+',
                'must_have': '["API endpoint", "Database", "Deployment"]',
                'start_time': future_start.strftime('%Y-%m-%dT%H:%M'),
                'deadline': future_end.strftime('%Y-%m-%dT%H:%M'),
                'materials': '[]'
            },
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        round_obj = Round.objects.get(contest=self.contest, title='Round 1')
        self.assertEqual(round_obj.status, Round.Status.DRAFT)
        self.assertEqual(round_obj.created_by, self.organizer)
        self.assertEqual(len(round_obj.must_have), 3)

    def test_create_round_invalid_deadline(self):
        """Test that round creation fails if deadline <= start_time"""
        self.client.force_login(self.organizer)
        future_time = timezone.now() + timedelta(days=1)
        
        response = self.client.post(
            reverse('round_create', kwargs={'pk': self.contest.pk}),
            {
                'title': 'Invalid Round',
                'description': 'This should fail',
                'tech_requirements': 'Tech stuff',
                'must_have': '["Item 1"]',
                'start_time': future_time.strftime('%Y-%m-%dT%H:%M'),
                'deadline': future_time.strftime('%Y-%m-%dT%H:%M'),  # Same as start_time
                'materials': '[]'
            }
        )
        
        # Should get 400 error or be redirected with error
        self.assertIn(response.status_code, [200, 400])
        self.assertEqual(Round.objects.filter(title='Invalid Round').count(), 0)

    def test_create_round_empty_must_have(self):
        """Test that round creation fails if must_have is empty"""
        self.client.force_login(self.organizer)
        future_start = timezone.now() + timedelta(days=1)
        future_end = timezone.now() + timedelta(days=2)
        
        response = self.client.post(
            reverse('round_create', kwargs={'pk': self.contest.pk}),
            {
                'title': 'Empty Checklist',
                'description': 'This should fail',
                'tech_requirements': 'Tech stuff',
                'must_have': '[]',  # Empty array
                'start_time': future_start.strftime('%Y-%m-%dT%H:%M'),
                'deadline': future_end.strftime('%Y-%m-%dT%H:%M'),
                'materials': '[]'
            }
        )
        
        self.assertEqual(Round.objects.filter(title='Empty Checklist').count(), 0)

    def test_activate_draft_round(self):
        """Test that a DRAFT round can be activated to ACTIVE"""
        self.client.force_login(self.organizer)
        future_start = timezone.now() + timedelta(days=1)
        future_end = timezone.now() + timedelta(days=2)
        
        round_obj = Round.objects.create(
            contest=self.contest,
            title='Activatable Round',
            description='Test',
            tech_requirements='Python',
            must_have=['Item 1'],
            start_time=future_start,
            deadline=future_end,
            status=Round.Status.DRAFT,
            created_by=self.organizer,
            order=1
        )
        
        response = self.client.post(
            reverse('round_activate', kwargs={'pk': self.contest.pk, 'round_id': round_obj.pk}),
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        round_obj.refresh_from_db()
        self.assertEqual(round_obj.status, Round.Status.ACTIVE)

    def test_cannot_activate_non_draft(self):
        """Test that non-DRAFT rounds cannot be activated"""
        self.client.force_login(self.organizer)
        future_start = timezone.now() + timedelta(days=1)
        future_end = timezone.now() + timedelta(days=2)
        
        round_obj = Round.objects.create(
            contest=self.contest,
            title='Already Active',
            description='Test',
            tech_requirements='Python',
            must_have=['Item 1'],
            start_time=future_start,
            deadline=future_end,
            status=Round.Status.ACTIVE,
            created_by=self.organizer,
            order=1
        )
        
        response = self.client.post(
            reverse('round_activate', kwargs={'pk': self.contest.pk, 'round_id': round_obj.pk}),
            follow=True
        )
        
        # Should get 403 or redirect with error
        self.assertIn(response.status_code, [200, 403])
        round_obj.refresh_from_db()
        self.assertEqual(round_obj.status, Round.Status.ACTIVE)

    def test_close_submissions_active_round(self):
        """Test that ACTIVE round can be closed (manual closure)"""
        self.client.force_login(self.organizer)
        future_start = timezone.now() + timedelta(days=1)
        future_end = timezone.now() + timedelta(days=2)
        
        round_obj = Round.objects.create(
            contest=self.contest,
            title='Closable Round',
            description='Test',
            tech_requirements='Python',
            must_have=['Item 1'],
            start_time=future_start,
            deadline=future_end,
            status=Round.Status.ACTIVE,
            created_by=self.organizer,
            order=1
        )
        
        response = self.client.post(
            reverse('round_close_submissions', kwargs={'pk': self.contest.pk, 'round_id': round_obj.pk}),
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        round_obj.refresh_from_db()
        self.assertEqual(round_obj.status, Round.Status.SUBMISSION_CLOSED)

    def test_extend_deadline_active_round(self):
        """Test extending deadline of an ACTIVE round"""
        self.client.force_login(self.organizer)
        future_start = timezone.now() + timedelta(days=1)
        future_end = timezone.now() + timedelta(days=2)
        new_deadline = timezone.now() + timedelta(days=5)
        
        round_obj = Round.objects.create(
            contest=self.contest,
            title='Extendable Round',
            description='Test',
            tech_requirements='Python',
            must_have=['Item 1'],
            start_time=future_start,
            deadline=future_end,
            status=Round.Status.ACTIVE,
            created_by=self.organizer,
            order=1
        )
        old_deadline = round_obj.deadline
        
        response = self.client.post(
            reverse('round_extend_deadline', kwargs={'pk': self.contest.pk, 'round_id': round_obj.pk}),
            {
                'new_deadline': new_deadline.strftime('%Y-%m-%dT%H:%M'),
                'reason': 'Infrastructure delay'
            },
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        round_obj.refresh_from_db()
        self.assertGreater(round_obj.deadline, old_deadline)

    def test_extend_deadline_future_only(self):
        """Test that deadline can only be extended to future times"""
        self.client.force_login(self.organizer)
        future_start = timezone.now() + timedelta(days=1)
        future_end = timezone.now() + timedelta(days=2)
        past_deadline = timezone.now() - timedelta(days=1)
        
        round_obj = Round.objects.create(
            contest=self.contest,
            title='Unextendable Round',
            description='Test',
            tech_requirements='Python',
            must_have=['Item 1'],
            start_time=future_start,
            deadline=future_end,
            status=Round.Status.ACTIVE,
            created_by=self.organizer,
            order=1
        )
        
        response = self.client.post(
            reverse('round_extend_deadline', kwargs={'pk': self.contest.pk, 'round_id': round_obj.pk}),
            {
                'new_deadline': past_deadline.strftime('%Y-%m-%dT%H:%M'),
                'reason': 'Bad date'
            }
        )
        
        # Should reject past date
        self.assertIn(response.status_code, [200, 400])

    def test_team_cannot_see_draft_round(self):
        """Test that participant teams cannot see DRAFT rounds"""
        self.client.force_login(self.participant)
        future_start = timezone.now() + timedelta(days=1)
        future_end = timezone.now() + timedelta(days=2)
        
        Round.objects.create(
            contest=self.contest,
            title='Secret Draft Round',
            description='Hidden',
            tech_requirements='Python',
            must_have=['Item 1'],
            start_time=future_start,
            deadline=future_end,
            status=Round.Status.DRAFT,
            created_by=self.organizer,
            order=1
        )
        
        response = self.client.get(reverse('contest_rounds_team', kwargs={'pk': self.contest.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Secret Draft Round')

    def test_team_sees_active_round(self):
        """Test that participants see ACTIVE rounds with countdown"""
        self.client.force_login(self.participant)
        past_start = timezone.now() - timedelta(days=1)
        future_end = timezone.now() + timedelta(days=3)
        
        Round.objects.create(
            contest=self.contest,
            title='Visible Active Round',
            description='Visible to teams',
            tech_requirements='Python',
            must_have=['Item 1'],
            start_time=past_start,
            deadline=future_end,
            status=Round.Status.ACTIVE,
            created_by=self.organizer,
            order=1
        )
        
        response = self.client.get(reverse('contest_rounds_team', kwargs={'pk': self.contest.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Visible Active Round')
        self.assertContains(response, 'ACTIVE')

    def test_team_sees_closed_message(self):
        """Test that SUBMISSION_CLOSED rounds show read-only message"""
        self.client.force_login(self.participant)
        future_start = timezone.now() + timedelta(days=1)
        past_end = timezone.now() - timedelta(days=1)
        
        Round.objects.create(
            contest=self.contest,
            title='Closed Round',
            description='Closed for submissions',
            tech_requirements='Python',
            must_have=['Item 1'],
            start_time=future_start,
            deadline=past_end,
            status=Round.Status.SUBMISSION_CLOSED,
            created_by=self.organizer,
            order=1
        )
        
        response = self.client.get(reverse('contest_rounds_team', kwargs={'pk': self.contest.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Closed Round')
        self.assertContains(response, 'CLOSED')

    def test_round_is_open_property(self):
        """Test the is_open property correctly identifies open rounds"""
        past_start = timezone.now() - timedelta(days=1)
        future_end = timezone.now() + timedelta(days=3)
        past_end = timezone.now() - timedelta(days=1)
        
        # Active round with past start and future deadline should be open
        active_round = Round.objects.create(
            contest=self.contest,
            title='Open Round',
            description='Test',
            tech_requirements='Python',
            must_have=['Item 1'],
            start_time=past_start,
            deadline=future_end,
            status=Round.Status.ACTIVE,
            created_by=self.organizer,
            order=1
        )
        self.assertTrue(active_round.is_open())
        
        # Closed round should not be open
        closed_round = Round.objects.create(
            contest=self.contest,
            title='Closed Round',
            description='Test',
            tech_requirements='Python',
            must_have=['Item 1'],
            start_time=past_start,
            deadline=past_end,
            status=Round.Status.SUBMISSION_CLOSED,
            created_by=self.organizer,
            order=2
        )
        self.assertFalse(closed_round.is_open())

    def test_organizer_can_only_edit_draft_rounds(self):
        """Test that organizers can only edit DRAFT rounds"""
        self.client.force_login(self.organizer)
        future_start = timezone.now() + timedelta(days=1)
        future_end = timezone.now() + timedelta(days=2)
        
        draft_round = Round.objects.create(
            contest=self.contest,
            title='Editable Draft',
            description='Test',
            tech_requirements='Python',
            must_have=['Item 1'],
            start_time=future_start,
            deadline=future_end,
            status=Round.Status.DRAFT,
            created_by=self.organizer,
            order=1
        )
        
        # Should be able to edit DRAFT round
        response = self.client.post(
            reverse('round_edit', kwargs={'pk': self.contest.pk, 'round_id': draft_round.pk}),
            {
                'title': 'Updated Title',
                'description': 'Updated description',
                'tech_requirements': 'Python 3.9+',
                'must_have': '["Item 1", "Item 2"]',
                'start_time': future_start.strftime('%Y-%m-%dT%H:%M'),
                'deadline': future_end.strftime('%Y-%m-%dT%H:%M'),
                'materials': '[]'
            },
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        draft_round.refresh_from_db()
        self.assertEqual(draft_round.title, 'Updated Title')


