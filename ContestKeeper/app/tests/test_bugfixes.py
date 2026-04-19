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
class BugfixRegressionTest(TestCase):
    """TASK-01: Regression tests proving each critical bug is fixed."""

    def setUp(self):
        self.organizer = User.objects.create_user(
            username='bugfix_org', password='password', role=User.Role.ORGANIZER
        )
        self.other_user = User.objects.create_user(
            username='bugfix_other', password='password', role=User.Role.PARTICIPANT
        )
        self.captain = User.objects.create_user(
            username='bugfix_cap', password='password', role=User.Role.PARTICIPANT
        )
        self.member = User.objects.create_user(
            username='bugfix_member', password='password', role=User.Role.PARTICIPANT
        )
        self.contest = Contest.objects.create(
            name='Bugfix Contest',
            description='Contest for bugfix tests',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            is_draft=False,
        )
        self.team = Team.objects.create(
            name='Bugfix Team', captain=self.captain, status=Team.Status.ACTIVE
        )
        self.team.participants.add(self.captain, self.member)
        self.contest.teams.add(self.team)
        self.client = Client()

    # ── Bug 1: OrganizerRequiredMixin — permission checked BEFORE view runs ──

    def test_non_organizer_cannot_delete_contest(self):
        """Non-organizer gets 403 and contest is NOT deleted (Bug 1)."""
        self.client.force_login(self.other_user)
        url = reverse('contest_delete', kwargs={'pk': self.contest.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        # Contest must still exist
        self.assertTrue(Contest.objects.filter(pk=self.contest.pk).exists())

    def test_organizer_can_delete_own_contest(self):
        """Organizer can delete their own contest (sanity check for Bug 1 fix)."""
        self.client.force_login(self.organizer)
        url = reverse('contest_delete', kwargs={'pk': self.contest.pk})
        response = self.client.post(url)
        self.assertIn(response.status_code, [200, 302])
        self.assertFalse(Contest.objects.filter(pk=self.contest.pk).exists())

    def test_unauthenticated_user_redirected_from_organizer_view(self):
        """Unauthenticated user is redirected, not shown the view (Bug 1)."""
        url = reverse('contest_delete', kwargs={'pk': self.contest.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('register', response.url)

    # ── Bug 2: TeamActionMixin — kick/block/unblock actually work ──

    def test_team_kick_removes_member(self):
        """Captain can kick a member and the member is actually removed (Bug 2)."""
        self.client.force_login(self.captain)
        url = reverse('team_kick', kwargs={
            'pk': self.contest.pk,
            'ck': self.team.pk,
            'user_id': self.member.pk,
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.team.refresh_from_db()
        self.assertNotIn(self.member, self.team.participants.all())

    def test_team_block_removes_and_blacklists_member(self):
        """Captain can block a member: removes from participants, adds to blacklist,
        rejects pending applications (Bug 2)."""
        # Create a pending application for the member
        Application.objects.create(
            user=self.member,
            team=self.team,
            contest=self.contest,
            application_type=Application.Type.PARTICIPANT,
            status=Application.Status.PENDING,
        )
        self.client.force_login(self.captain)
        url = reverse('team_block', kwargs={
            'pk': self.contest.pk,
            'ck': self.team.pk,
            'user_id': self.member.pk,
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.team.refresh_from_db()
        self.assertNotIn(self.member, self.team.participants.all())
        self.assertIn(self.member, self.team.blacklisted_members.all())
        # Pending application should be rejected
        app = Application.objects.get(user=self.member, team=self.team)
        self.assertEqual(app.status, Application.Status.REJECTED)

    def test_team_unblock_removes_from_blacklist(self):
        """Captain can unblock a member (Bug 2)."""
        self.team.blacklisted_members.add(self.member)
        self.client.force_login(self.captain)
        url = reverse('team_unblock', kwargs={
            'pk': self.contest.pk,
            'ck': self.team.pk,
            'user_id': self.member.pk,
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.team.refresh_from_db()
        self.assertNotIn(self.member, self.team.blacklisted_members.all())

    def test_non_captain_cannot_kick(self):
        """Non-captain gets 403 when trying to kick (Bug 2 permission check)."""
        self.client.force_login(self.other_user)
        url = reverse('team_kick', kwargs={
            'pk': self.contest.pk,
            'ck': self.team.pk,
            'user_id': self.member.pk,
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        # Member should still be in team
        self.assertIn(self.member, self.team.participants.all())

    # ── Bug 4: TeamDetailView — returns 200 with correct context ──

    def test_team_detail_returns_200(self):
        """TeamDetailView renders without crashing (Bug 4: no double get_object)."""
        self.client.force_login(self.captain)
        url = reverse('team_detail', kwargs={
            'pk': self.contest.pk,
            'ck': self.team.pk,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['team'], self.team)
        self.assertEqual(response.context['contest'], self.contest)

    # ── Bug 5: Contest detail shows dynamic status ──

    def test_contest_detail_shows_dynamic_status(self):
        """Contest detail page shows current status, not hardcoded 'Active' (Bug 5)."""
        self.client.force_login(self.organizer)
        url = reverse('contest_detail', kwargs={'pk': self.contest.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        # Should NOT contain the hardcoded 'Active' without a class
        self.assertNotIn('<span class="status-indicator">Active</span>', content)
        # Should contain the dynamic status display
        status_display = self.contest.get_status_display()
        self.assertIn(status_display, content)
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
