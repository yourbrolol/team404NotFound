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
class HomeViewTaskTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.organizer = User.objects.create_user(username="home_org", password="password", role=User.Role.ORGANIZER)
        self.participant = User.objects.create_user(username="home_participant", password="password", role=User.Role.PARTICIPANT)
        now = timezone.now()

        self.registration_contest = Contest.objects.create(
            name="Reg Cup",
            description="Registration contest",
            start_date=now + timedelta(days=2),
            end_date=now + timedelta(days=4),
            organizer=self.organizer,
            is_draft=False,
        )
        self.running_contest = Contest.objects.create(
            name="Run Cup",
            description="Running contest",
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=2),
            organizer=self.organizer,
            is_draft=False,
        )
        self.finished_contest = Contest.objects.create(
            name="Done Cup",
            description="Finished contest",
            start_date=now - timedelta(days=5),
            end_date=now - timedelta(days=1),
            organizer=self.organizer,
            is_draft=False,
        )
        self.draft_contest = Contest.objects.create(
            name="Draft Cup",
            description="Draft contest",
            start_date=now + timedelta(days=5),
            end_date=now + timedelta(days=6),
            organizer=self.organizer,
            is_draft=True,
        )

    def test_home_shows_all_non_draft_contests(self):
        self.client.force_login(self.participant)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reg Cup")
        self.assertContains(response, "Run Cup")
        self.assertContains(response, "Done Cup")
        self.assertNotContains(response, "Draft Cup")

    def test_home_status_filter_limits_contests(self):
        self.client.force_login(self.participant)
        response = self.client.get(reverse("home"), {"status": Contest.Status.REGISTRATION})

        self.assertContains(response, "Reg Cup")
        self.assertNotContains(response, "Run Cup")
        self.assertNotContains(response, "Done Cup")

    def test_home_invalid_status_filter_falls_back_to_all(self):
        self.client.force_login(self.participant)
        response = self.client.get(reverse("home"), {"status": "NOT_A_REAL_STATUS"})

        self.assertContains(response, "Reg Cup")
        self.assertContains(response, "Run Cup")
        self.assertContains(response, "Done Cup")

    def test_home_quick_access_appears_for_participant_with_active_contest(self):
        team = Team.objects.create(name="Rocket", captain=self.participant, status=Team.Status.ACTIVE)
        team.participants.add(self.participant)
        self.running_contest.teams.add(team)
        Round.objects.create(
            contest=self.running_contest,
            title="Speed Round",
            description="Round description",
            tech_requirements="Python",
            must_have=["API"],
            start_time=timezone.now() - timedelta(hours=2),
            deadline=timezone.now() + timedelta(hours=5),
            status=Round.Status.ACTIVE,
            order=1,
            created_by=self.organizer,
        )

        self.client.force_login(self.participant)
        response = self.client.get(reverse("home"))

        self.assertContains(response, "Your current contest")
        self.assertContains(response, "Rocket")
        self.assertContains(response, "Speed Round")
        self.assertContains(response, "Open Current Round")

    def test_home_quick_access_hidden_when_participant_has_no_team(self):
        self.client.force_login(self.participant)
        response = self.client.get(reverse("home"))

        self.assertNotContains(response, "Your current contest")


class ProfileViewTaskTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.organizer = User.objects.create_user(username="profile_org", password="password", role=User.Role.ORGANIZER)
        self.jury = User.objects.create_user(username="profile_jury", password="password", role=User.Role.JURY)
        self.participant = User.objects.create_user(username="profile_participant", password="password", role=User.Role.PARTICIPANT)
        self.member = User.objects.create_user(username="profile_member", password="password", role=User.Role.PARTICIPANT)
        now = timezone.now()

        self.contest = Contest.objects.create(
            name="Profile Contest",
            description="Contest for profile tests",
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=1),
            organizer=self.organizer,
            is_draft=False,
        )
        self.team = Team.objects.create(name="Winners", captain=self.participant, status=Team.Status.ACTIVE)
        self.team.participants.add(self.participant, self.member)
        self.contest.teams.add(self.team)
        self.contest.jurys.add(self.jury)

        self.criterion = ScoringCriterion.objects.create(
            contest=self.contest,
            name="Backend",
            max_score=100,
            weight=Decimal("1.00"),
            aggregation_type=ScoringCriterion.AggregationType.AVERAGE,
            order=1,
        )

    def test_profile_for_participant_shows_teams_and_leaderboard_history(self):
        LeaderboardEntry.objects.create(
            contest=self.contest,
            team=self.team,
            rank=1,
            total_score=Decimal("95.00"),
            is_tied=False,
            category_scores={"Backend": "95.00"},
        )

        self.client.force_login(self.participant)
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Teams")
        self.assertContains(response, "Winners")
        self.assertContains(response, "Captain")
        self.assertContains(response, "Leaderboard History")
        self.assertContains(response, "95.00")

    def test_profile_for_jury_shows_pending_and_completed_reviews(self):
        JuryScore.objects.create(
            contest=self.contest,
            team=self.team,
            jury_member=self.jury,
            criterion=self.criterion,
            score=Decimal("88.00"),
        )
        second_team = Team.objects.create(name="Challengers", captain=self.member, status=Team.Status.ACTIVE)
        second_team.participants.add(self.member)
        self.contest.teams.add(second_team)

        self.client.force_login(self.jury)
        response = self.client.get(reverse("profile"))

        self.assertContains(response, "Pending Reviews")
        self.assertContains(response, "Challengers")
        self.assertContains(response, "Completed Reviews")
        self.assertContains(response, "88.00")

    def test_profile_for_organizer_shows_managed_contests(self):
        self.client.force_login(self.organizer)
        response = self.client.get(reverse("profile"))

        self.assertContains(response, "My Contests")
        self.assertContains(response, "Profile Contest")
        self.assertContains(response, "Running")

    def test_profile_empty_states_render_for_user_without_related_data(self):
        empty_participant = User.objects.create_user(username="lonely_user", password="password", role=User.Role.PARTICIPANT)

        self.client.force_login(empty_participant)
        response = self.client.get(reverse("profile"))

        self.assertContains(response, "You are not part of any teams yet.")
        self.assertContains(response, "No leaderboard results available yet.")


