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
class LeaderboardLogicTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username='org', password='password', role=User.Role.ORGANIZER)
        self.jury = User.objects.create_user(username='jury', password='password', role=User.Role.JURY)
        self.participant = User.objects.create_user(username='parti', password='password', role=User.Role.PARTICIPANT)
        from django.utils import timezone
        self.contest = Contest.objects.create(
            name='Leaderboard Contest',
            description='Contest description',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=1),
            organizer=self.organizer,
            is_draft=False
        )
        self.team = Team.objects.create(name='Team A', status=Team.Status.ACTIVE)
        self.contest.teams.add(self.team)
        self.contest.jurys.add(self.jury)
        self.criterion = ScoringCriterion.objects.create(
            contest=self.contest,
            name='Quality',
            max_score=10,
            weight=1.0,
            aggregation_type=ScoringCriterion.AggregationType.SUM,
            order=1,
        )
        self.client = Client()

    def test_contest_leaderboard_not_available_before_completion(self):
        self.client.force_login(self.organizer)
        response = self.client.get(reverse('contest_leaderboard', kwargs={'pk': self.contest.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Leaderboard is not yet available. Evaluation is still in progress.')

    def test_finish_evaluation_creates_leaderboard_with_missing_scores(self):
        self.client.force_login(self.organizer)
        response = self.client.post(reverse('admin_finish_evaluation', kwargs={'pk': self.contest.pk}))
        self.assertEqual(response.status_code, 302)

        phase = ContestEvaluationPhase.objects.get(contest=self.contest)
        self.assertEqual(phase.status, ContestEvaluationPhase.Status.COMPLETED)
        self.assertEqual(phase.trigger_type, ContestEvaluationPhase.TriggerType.MANUAL)
        self.assertFalse(phase.all_scores_complete)

        entry = LeaderboardEntry.objects.get(contest=self.contest, team=self.team)
        self.assertFalse(entry.computation_complete)
        self.assertGreaterEqual(len(entry.missing_scores), 1)
        self.assertEqual(entry.missing_scores[0]['jury_username'], self.jury.username)


class LeaderboardHelperFunctionsTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="org_lb", password="password", role=User.Role.ORGANIZER)
        self.jury_one = User.objects.create_user(username="judge_a", password="password", role=User.Role.JURY)
        self.jury_two = User.objects.create_user(username="judge_b", password="password", role=User.Role.JURY)
        self.captain_one = User.objects.create_user(username="alpha_cap", password="password")
        self.captain_two = User.objects.create_user(username="beta_cap", password="password")

        self.team_one = Team.objects.create(name="Alpha", captain=self.captain_one, status=Team.Status.ACTIVE)
        self.team_one.participants.add(self.captain_one)
        self.team_two = Team.objects.create(name="Beta", captain=self.captain_two, status=Team.Status.ACTIVE)
        self.team_two.participants.add(self.captain_two)

        self.contest = Contest.objects.create(
            name="LeaderCup",
            description="Leaderboard contest",
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=3),
            organizer=self.organizer,
            is_draft=False,
        )
        self.contest.teams.add(self.team_one, self.team_two)
        self.contest.jurys.add(self.jury_one, self.jury_two)

        self.backend = ScoringCriterion.objects.create(
            contest=self.contest,
            name="Backend",
            max_score=100,
            weight=Decimal("1.00"),
            aggregation_type=ScoringCriterion.AggregationType.AVERAGE,
            order=1,
        )
        self.ui = ScoringCriterion.objects.create(
            contest=self.contest,
            name="UI",
            max_score=100,
            weight=Decimal("0.50"),
            aggregation_type=ScoringCriterion.AggregationType.AVERAGE,
            order=2,
        )

    def test_compute_leaderboard_orders_teams_by_weighted_score(self):
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_one, criterion=self.backend, score=Decimal("90.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_two, criterion=self.backend, score=Decimal("80.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_one, criterion=self.ui, score=Decimal("70.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_two, criterion=self.ui, score=Decimal("90.00"))

        JuryScore.objects.create(contest=self.contest, team=self.team_two, jury_member=self.jury_one, criterion=self.backend, score=Decimal("60.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_two, jury_member=self.jury_two, criterion=self.backend, score=Decimal("70.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_two, jury_member=self.jury_one, criterion=self.ui, score=Decimal("50.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_two, jury_member=self.jury_two, criterion=self.ui, score=Decimal("50.00"))

        leaderboard = compute_leaderboard(self.contest)

        self.assertEqual(leaderboard[0]["team"], self.team_one)
        self.assertEqual(leaderboard[0]["rank"], 1)
        self.assertEqual(leaderboard[0]["total_score"], Decimal("125.00"))
        self.assertEqual(leaderboard[1]["total_score"], Decimal("90.00"))

    def test_get_missing_scores_reports_unscored_slots(self):
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_one, criterion=self.backend, score=Decimal("95.00"))

        missing = get_missing_scores(self.contest)

        self.assertIn("Alpha", missing)
        self.assertIn("Backend", missing["Alpha"])
        self.assertIn("judge_b", missing["Alpha"]["Backend"])
        self.assertIn("UI", missing["Alpha"])

    def test_save_leaderboard_persists_entries_and_marks_phase_complete(self):
        for team, backend_one, backend_two, ui_one, ui_two in (
            (self.team_one, "90.00", "90.00", "80.00", "80.00"),
            (self.team_two, "90.00", "90.00", "80.00", "80.00"),
        ):
            JuryScore.objects.create(contest=self.contest, team=team, jury_member=self.jury_one, criterion=self.backend, score=Decimal(backend_one))
            JuryScore.objects.create(contest=self.contest, team=team, jury_member=self.jury_two, criterion=self.backend, score=Decimal(backend_two))
            JuryScore.objects.create(contest=self.contest, team=team, jury_member=self.jury_one, criterion=self.ui, score=Decimal(ui_one))
            JuryScore.objects.create(contest=self.contest, team=team, jury_member=self.jury_two, criterion=self.ui, score=Decimal(ui_two))

        entries = save_leaderboard(self.contest)
        phase = ContestEvaluationPhase.objects.get(contest=self.contest)

        self.assertEqual(len(entries), 2)
        self.assertEqual(self.contest.leaderboard_entries.count(), 2)
        self.assertTrue(phase.all_scores_complete)
        self.assertEqual(phase.status, ContestEvaluationPhase.Status.COMPLETED)
        self.assertTrue(all(entry.is_tied for entry in entries))

    def test_export_csv_returns_ranked_rows(self):
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_one, criterion=self.backend, score=Decimal("88.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_two, criterion=self.backend, score=Decimal("88.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_one, criterion=self.ui, score=Decimal("92.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_two, criterion=self.ui, score=Decimal("92.00"))

        csv_data = export_csv(self.contest)

        self.assertIn("rank,team,total_score", csv_data)
        self.assertIn("Alpha", csv_data)


