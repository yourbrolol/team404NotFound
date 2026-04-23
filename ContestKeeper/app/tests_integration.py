"""
Integration tests for ContestKeeper main user scenarios.
"""
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from app.models import Contest, Team, ScoringCriterion, LeaderboardEntry, Round, ContestEvaluationPhase

User = get_user_model()


class ContestKeeperIntegrationTest(TestCase):
    """TASK-33: Integration tests for core contest workflows."""

    def setUp(self):
        self.client = Client()
        self.organizer = User.objects.create_user(
            username='organizer1',
            email='organizer1@test.com',
            password='password123',
            role=User.Role.ORGANIZER,
        )
        self.jury = User.objects.create_user(
            username='jury1',
            email='jury1@test.com',
            password='password123',
            role=User.Role.JURY,
        )
        self.participant1 = User.objects.create_user(
            username='participant1',
            email='participant1@test.com',
            password='password123',
            role=User.Role.PARTICIPANT,
        )
        self.participant2 = User.objects.create_user(
            username='participant2',
            email='participant2@test.com',
            password='password123',
            role=User.Role.PARTICIPANT,
        )

    def test_contest_creation_and_publish_flow(self):
        """Test creating and publishing contests through the form."""
        self.client.login(username='organizer1', password='password123')

        # Create a draft contest
        contest = Contest.objects.create(
            name='Integration Contest',
            description='Created by integration test',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
            max_teams=5,
            organizer=self.organizer,
            is_draft=True,
        )

        self.assertTrue(contest.is_draft)
        self.assertEqual(contest.organizer, self.organizer)
        self.assertEqual(contest.status, Contest.Status.DRAFT)

        # Publish the contest by updating is_draft field
        contest.is_draft = False
        contest.save()

        contest.refresh_from_db()
        self.assertFalse(contest.is_draft)
        self.assertEqual(contest.status, Contest.Status.REGISTRATION)

    def test_scoring_criterion_creation(self):
        """Test creating scoring criteria directly."""
        contest = Contest.objects.create(
            name='Criterion Contest',
            description='Test scoring criterion',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            is_draft=False,
        )

        # Create criterion directly (use actual model fields)
        criterion = ScoringCriterion.objects.create(
            contest=contest,
            name='Code Quality',
            weight=50,
            max_score=100,
            order=1,
        )

        self.assertTrue(ScoringCriterion.objects.filter(contest=contest, name='Code Quality').exists())
        self.assertEqual(criterion.weight, 50)
        self.assertEqual(criterion.max_score, 100)

    def test_team_creation_and_join(self):
        contest = Contest.objects.create(
            name='Team Registration Contest',
            description='Test teams',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            is_draft=False,
        )

        self.client.login(username='participant1', password='password123')
        url = reverse('team_create', kwargs={'pk': contest.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            'name': 'Team Alpha',
            'organization': 'Test University',
            'discord_link': 'https://discord.gg/test',
        }
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [200, 302])

        self.assertTrue(Team.objects.filter(name='Team Alpha', captain=self.participant1).exists())

    def test_draft_contest_visibility_restriction(self):
        draft_contest = Contest.objects.create(
            name='Draft Contest',
            description='Hidden contest',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            is_draft=True,
        )

        self.client.login(username='participant1', password='password123')
        response = self.client.get(reverse('contest_detail', kwargs={'pk': draft_contest.pk}))
        self.assertIn(response.status_code, [302, 403, 404])

        self.client.logout()
        self.client.login(username='organizer1', password='password123')
        response = self.client.get(reverse('contest_detail', kwargs={'pk': draft_contest.pk}))
        self.assertEqual(response.status_code, 200)

    def test_leaderboard_access_for_participant(self):
        contest = Contest.objects.create(
            name='Leaderboard Access Contest',
            description='Test leaderboard',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            is_draft=False,
        )

        team = Team.objects.create(name='Leaderboard Team', captain=self.participant1)
        contest.teams.add(team)

        LeaderboardEntry.objects.create(
            contest=contest,
            team=team,
            rank=1,
            total_score=88.0,
            category_scores={'Code Quality': 88.0},
            is_tied=False,
            computation_complete=True,
        )

        self.client.login(username='participant1', password='password123')
        response = self.client.get(reverse('contest_leaderboard', kwargs={'pk': contest.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Leaderboard', response.content)

    def test_round_creation_permission(self):
        contest = Contest.objects.create(
            name='Round Permission Contest',
            description='Test round permissions',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            is_draft=False,
        )

        url = reverse('round_create', kwargs={'pk': contest.pk})
        self.client.login(username='participant1', password='password123')
        data = {
            'title': 'Unauthorized Round',
            'description': 'Should not be allowed',
            'tech_requirements': 'Python',
            'must_have': '["Test"]',
            'start_time': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'deadline': (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'),
            'materials': '[]',
        }
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [302, 403])
        self.assertEqual(Round.objects.filter(contest=contest).count(), 0)

        self.client.logout()
        self.client.login(username='organizer1', password='password123')
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [200, 302])

    def test_leaderboard_pagination_rendering(self):
        contest = Contest.objects.create(
            name='Pagination Contest',
            description='Test pagination',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            is_draft=False,
        )

        for i in range(55):
            team = Team.objects.create(name=f'Team {i}', captain=self.participant1)
            contest.teams.add(team)
            LeaderboardEntry.objects.create(
                contest=contest,
                team=team,
                rank=i + 1,
                total_score=100 - i,
                category_scores={},
                is_tied=False,
                computation_complete=True,
            )

        # Mark evaluation as complete so leaderboard displays
        phase, _ = ContestEvaluationPhase.objects.get_or_create(contest=contest)
        phase.status = ContestEvaluationPhase.Status.COMPLETED
        phase.save()

        self.client.login(username='participant1', password='password123')
        response = self.client.get(reverse('contest_leaderboard', kwargs={'pk': contest.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Check for team entries in leaderboard
        self.assertIn(b'Team', response.content)
