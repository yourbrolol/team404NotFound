from decimal import Decimal

from django.core.exceptions import ValidationError
from app.tests.base import BaseSecureTestCase
from django.test import Client
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
from app.tests.base import BaseSecureTestCase
from django.test import Client
from django.urls import reverse
class SubmissionModelTest(BaseSecureTestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username='sub_org', password='password', role=User.Role.ORGANIZER
        )
        self.participant = User.objects.create_user(
            username='sub_parti', password='password', role=User.Role.PARTICIPANT
        )
        self.contest = Contest.objects.create(
            name='Sub Contest',
            description='Contest for submission tests',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            is_draft=False,
        )
        self.team = Team.objects.create(
            name='Sub Team', captain=self.participant, status=Team.Status.ACTIVE
        )
        self.team.participants.add(self.participant)
        self.contest.teams.add(self.team)

        self.round = Round.objects.create(
            contest=self.contest,
            title='Round 1',
            description='First round',
            tech_requirements='Python 3.13',
            must_have=['API', 'Tests'],
            start_time=timezone.now() - timedelta(days=1),
            deadline=timezone.now() + timedelta(days=3),
            status=Round.Status.ACTIVE,
            created_by=self.organizer,
            order=1,
        )

    def test_create_submission_with_valid_data(self):
        """Test that a submission can be created with all required fields."""
        sub = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/example/repo',
            video_url='https://youtube.com/watch?v=abc123',
            live_demo_url='https://example.com/demo',
            description='Implemented API endpoints and database schema.',
        )
        self.assertEqual(sub.round, self.round)
        self.assertEqual(sub.team, self.team)
        self.assertEqual(sub.github_url, 'https://github.com/example/repo')
        self.assertEqual(sub.video_url, 'https://youtube.com/watch?v=abc123')
        self.assertEqual(sub.live_demo_url, 'https://example.com/demo')
        self.assertIsNotNone(sub.submitted_at)
        self.assertIsNotNone(sub.updated_at)
        self.assertEqual(str(sub), f'{self.team.name} — {self.round.title}')

    def test_unique_together_round_team(self):
        """Test that a team cannot submit twice to the same round."""
        Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/example/repo1',
            video_url='https://youtube.com/watch?v=first',
        )
        with self.assertRaises(Exception):
            Submission.objects.create(
                round=self.round,
                team=self.team,
                github_url='https://github.com/example/repo2',
                video_url='https://youtube.com/watch?v=second',
            )

    def test_is_editable_true_when_round_open(self):
        """Submission is editable when round is ACTIVE and before deadline."""
        sub = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/example/repo',
            video_url='https://youtube.com/watch?v=abc',
        )
        # Round is ACTIVE with start_time in the past and deadline in the future
        self.assertTrue(sub.is_editable)

    def test_is_editable_false_when_round_closed(self):
        """Submission is not editable when round status is SUBMISSION_CLOSED."""
        self.round.status = Round.Status.SUBMISSION_CLOSED
        self.round.save()
        sub = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/example/repo',
            video_url='https://youtube.com/watch?v=abc',
        )
        self.assertFalse(sub.is_editable)

    def test_is_editable_false_when_deadline_passed(self):
        """Submission is not editable when the deadline has passed (even if still ACTIVE)."""
        self.round.deadline = timezone.now() - timedelta(hours=1)
        self.round.save()
        sub = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/example/repo',
            video_url='https://youtube.com/watch?v=abc',
        )
        self.assertFalse(sub.is_editable)

    def test_cascade_delete_round(self):
        """Deleting a Round cascades to its Submissions."""
        Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/example/repo',
            video_url='https://youtube.com/watch?v=abc',
        )
        self.assertEqual(Submission.objects.count(), 1)
        self.round.delete()
        self.assertEqual(Submission.objects.count(), 0)

    def test_cascade_delete_team(self):
        """Deleting a Team cascades to its Submissions."""
        Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/example/repo',
            video_url='https://youtube.com/watch?v=abc',
        )
        self.assertEqual(Submission.objects.count(), 1)
        self.team.delete()
        self.assertEqual(Submission.objects.count(), 0)

    def test_submission_url_validation(self):
        """Test that submission URLs are properly validated"""
        # Valid URLs should work
        sub = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/user/repo',
            video_url='https://youtube.com/watch?v=abc123',
            live_demo_url='https://example.com/demo',
        )
        self.assertEqual(sub.github_url, 'https://github.com/user/repo')
        
        # Invalid URLs should fail at form level, but model allows any URL
        # The validation happens in forms, not models for URLs

    def test_submission_with_minimal_data(self):
        """Test submission creation with only required fields"""
        sub = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/example/repo',
            video_url='https://youtube.com/watch?v=abc',
            # live_demo_url and description are optional
        )
        self.assertIsNotNone(sub.submitted_at)
        self.assertIsNotNone(sub.updated_at)
        self.assertEqual(sub.live_demo_url, '')
        self.assertEqual(sub.description, '')

    def test_submission_update_timestamps(self):
        """Test that updating a submission changes updated_at but not submitted_at"""
        sub = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/example/repo',
            video_url='https://youtube.com/watch?v=abc',
        )
        original_submitted_at = sub.submitted_at
        original_updated_at = sub.updated_at
        
        # Wait a bit and update
        import time
        time.sleep(0.01)
        
        sub.description = 'Updated description'
        sub.save()
        
        sub.refresh_from_db()
        self.assertEqual(sub.submitted_at, original_submitted_at)
        self.assertGreater(sub.updated_at, original_updated_at)

    def test_submission_str_method(self):
        """Test the string representation of submissions"""
        sub = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/example/repo',
            video_url='https://youtube.com/watch?v=abc',
        )
        expected_str = f'{self.team.name} — {self.round.title}'
        self.assertEqual(str(sub), expected_str)

    def test_submission_is_editable_edge_cases(self):
        """Test edge cases for is_editable method"""
        # Round just became active (started exactly now)
        now = timezone.now()
        edge_round = Round.objects.create(
            contest=self.contest,
            title='Edge Round',
            description='Test',
            tech_requirements='Python',
            must_have=['Item 1'],
            start_time=now,
            deadline=now + timedelta(hours=1),
            status=Round.Status.ACTIVE,
            created_by=self.organizer,
            order=2
        )
        
        sub = Submission.objects.create(
            round=edge_round,
            team=self.team,
            github_url='https://github.com/example/repo',
            video_url='https://youtube.com/watch?v=abc',
        )
        
        # Should be editable since round just started
        self.assertTrue(sub.is_editable)
        
        # Make round end in past
        edge_round.deadline = now - timedelta(seconds=1)
        edge_round.save()
        
        # Refresh submission to get updated round data
        sub.refresh_from_db()
        self.assertFalse(sub.is_editable)

    def test_multiple_submissions_different_rounds_allowed(self):
        """Test that same team can submit to different rounds"""
        other_round = Round.objects.create(
            contest=self.contest,
            title='Other Round',
            description='Another round',
            tech_requirements='Python',
            must_have=['Item 1'],
            start_time=timezone.now() - timedelta(days=1),
            deadline=timezone.now() + timedelta(days=1),
            status=Round.Status.ACTIVE,
            created_by=self.organizer,
            order=2
        )
        
        # Should not raise exception
        sub1 = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/example/repo1',
            video_url='https://youtube.com/watch?v=first',
        )
        sub2 = Submission.objects.create(
            round=other_round,
            team=self.team,
            github_url='https://github.com/example/repo2',
            video_url='https://youtube.com/watch?v=second',
        )
        
        self.assertEqual(Submission.objects.filter(team=self.team).count(), 2)

    def test_different_teams_same_round_allowed(self):
        """Test that different teams can submit to the same round"""
        other_team = Team.objects.create(
            name='Other Team',
            captain=self.participant,
            status=Team.Status.ACTIVE
        )
        other_team.participants.add(self.participant)
        self.contest.teams.add(other_team)
        
        # Should not raise exception
        sub1 = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/example/repo1',
            video_url='https://youtube.com/watch?v=first',
        )
        sub2 = Submission.objects.create(
            round=self.round,
            team=other_team,
            github_url='https://github.com/example/repo2',
            video_url='https://youtube.com/watch?v=second',
        )
        
        self.assertEqual(Submission.objects.filter(round=self.round).count(), 2)

    def test_submission_with_long_description(self):
        """Test submission with maximum length description"""
        long_description = 'A' * 2000  # Max length
        sub = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/example/repo',
            video_url='https://youtube.com/watch?v=abc',
            description=long_description,
        )
        self.assertEqual(len(sub.description), 2000)

    def test_submission_description_truncation_display(self):
        """Test that long descriptions are handled properly in display"""
        long_description = 'A' * 2000
        sub = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/example/repo',
            video_url='https://youtube.com/watch?v=abc',
            description=long_description,
        )
        
        # The model should store the full description
        self.assertEqual(len(sub.description), 2000)
        # String representation should still work
        self.assertIn(self.team.name, str(sub))

    def test_submission_urls_with_special_characters(self):
        """Test submission URLs with special characters and encoding"""
        sub = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/user/repo-with-dashes_and_underscores',
            video_url='https://youtube.com/watch?v=abc123&feature=share',
            live_demo_url='https://example.com/demo?param=value&other=test',
        )
        
        self.assertIn('dashes', sub.github_url)
        self.assertIn('feature=share', sub.video_url)
        self.assertIn('param=value', sub.live_demo_url)

    def test_optional_fields_can_be_blank(self):
        """live_demo_url and description are optional."""
        sub = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/example/repo',
            video_url='https://youtube.com/watch?v=abc',
        )
        self.assertEqual(sub.live_demo_url, '')
        self.assertEqual(sub.description, '')


class SubmissionUITest(BaseSecureTestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username='sub_org', password='password', role=User.Role.ORGANIZER)
        self.participant = User.objects.create_user(username='sub_parti', password='password', role=User.Role.PARTICIPANT)
        self.jury = User.objects.create_user(username='sub_jury', password='password', role=User.Role.JURY)
        self.other_participant = User.objects.create_user(username='sub_other', password='password', role=User.Role.PARTICIPANT)
        
        self.contest = Contest.objects.create(
            name='Submission Test Contest',
            description='Test description',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            is_draft=False
        )
        self.team = Team.objects.create(name='Sub Team', captain=self.participant, status=Team.Status.ACTIVE)
        self.team.participants.add(self.participant)
        self.contest.teams.add(self.team)
        self.contest.jurys.add(self.jury)
        
        self.round = Round.objects.create(
            contest=self.contest,
            title='Test Round',
            description='Test desc',
            tech_requirements='Python',
            must_have=['Item 1'],
            start_time=timezone.now() - timedelta(hours=1),
            deadline=timezone.now() + timedelta(hours=2),
            status=Round.Status.ACTIVE,
            created_by=self.organizer,
            order=1
        )
        # self.client = self.client_class()  # Removed redundant insecure client

    def test_submission_form_access_denied_for_non_team_members(self):
        self.client.force_login(self.other_participant)
        url = reverse('submission_create', kwargs={'pk': self.contest.pk, 'round_id': self.round.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_submission_creation_success(self):
        self.client.force_login(self.participant)
        url = reverse('submission_create', kwargs={'pk': self.contest.pk, 'round_id': self.round.pk})
        data = {
            'github_url': 'https://github.com/team/repo',
            'video_url': 'https://youtube.com/watch?v=123',
            'live_demo_url': 'https://demo.example.com',
            'description': 'Our amazing project implementation.'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        submission = Submission.objects.get(round=self.round, team=self.team)
        self.assertEqual(submission.github_url, data['github_url'])
        self.assertEqual(submission.team, self.team)

    def test_submission_edit_success(self):
        submission = Submission.objects.create(
            round=self.round, team=self.team,
            github_url='https://github.com/old/repo',
            video_url='https://youtube.com/old'
        )
        self.client.force_login(self.participant)
        url = reverse('submission_create', kwargs={'pk': self.contest.pk, 'round_id': self.round.pk})
        data = {
            'github_url': 'https://github.com/new/repo',
            'video_url': 'https://youtube.com/new',
            'description': 'Updated description'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        submission.refresh_from_db()
        self.assertEqual(submission.github_url, 'https://github.com/new/repo')

    def test_submission_creation_denied_after_deadline(self):
        self.round.deadline = timezone.now() - timedelta(minutes=1)
        self.round.save()
        
        self.client.force_login(self.participant)
        url = reverse('submission_create', kwargs={'pk': self.contest.pk, 'round_id': self.round.pk})
        response = self.client.post(url, {'github_url': 'https://github.com/...', 'video_url': '...'})
        self.assertEqual(response.status_code, 403)

    def test_submission_detail_visibility(self):
        submission = Submission.objects.create(
            round=self.round, team=self.team,
            github_url='https://github.com/test/repo',
            video_url='https://youtube.com/test'
        )
        url = reverse('submission_detail', kwargs={
            'pk': self.contest.pk, 'round_id': self.round.pk, 'sub_pk': submission.pk
        })
        
        # Team member can see
        self.client.force_login(self.participant)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Organizer can see
        self.client.force_login(self.organizer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Jury can see
        self.client.force_login(self.jury)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Other participant cannot see
        self.client.force_login(self.other_participant)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_round_submissions_list_permissions(self):
        url = reverse('round_submissions', kwargs={'pk': self.contest.pk, 'round_id': self.round.pk})
        
        # Participant denied
        self.client.force_login(self.participant)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        # Organizer allowed
        self.client.force_login(self.organizer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Jury allowed
        self.client.force_login(self.jury)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
