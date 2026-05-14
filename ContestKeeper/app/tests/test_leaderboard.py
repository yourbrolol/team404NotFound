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
    JuryAssignment,
)



from django.core.exceptions import ValidationError
from app.tests.base import BaseSecureTestCase
from django.test import Client
from django.urls import reverse
class LeaderboardLogicTest(BaseSecureTestCase):
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
        # self.client = self.client_class()  # Removed redundant insecure client

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


class LeaderboardHelperFunctionsTest(BaseSecureTestCase):
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
        
        # Create JuryAssignments for all teams and juries
        for team in [self.team_one, self.team_two]:
            for jury in [self.jury_one, self.jury_two]:
                JuryAssignment.objects.create(contest=self.contest, team=team, jury_member=jury)

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

    def test_compute_leaderboard_handles_ties_correctly(self):
        """Test that tied teams get the same rank and is_tied flag"""
        # Both teams get identical scores
        for team in [self.team_one, self.team_two]:
            JuryScore.objects.create(contest=self.contest, team=team, jury_member=self.jury_one, criterion=self.backend, score=Decimal("85.00"))
            JuryScore.objects.create(contest=self.contest, team=team, jury_member=self.jury_two, criterion=self.backend, score=Decimal("85.00"))
            JuryScore.objects.create(contest=self.contest, team=team, jury_member=self.jury_one, criterion=self.ui, score=Decimal("75.00"))
            JuryScore.objects.create(contest=self.contest, team=team, jury_member=self.jury_two, criterion=self.ui, score=Decimal("75.00"))

        leaderboard = compute_leaderboard(self.contest)

        self.assertEqual(len(leaderboard), 2)
        self.assertEqual(leaderboard[0]["rank"], 1)
        self.assertEqual(leaderboard[1]["rank"], 1)
        self.assertTrue(leaderboard[0]["is_tied"])
        self.assertTrue(leaderboard[1]["is_tied"])

    def test_compute_leaderboard_with_missing_scores_shows_partial_results(self):
        """Test leaderboard computation when some scores are missing"""
        # Only score team_one fully
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_one, criterion=self.backend, score=Decimal("90.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_two, criterion=self.backend, score=Decimal("90.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_one, criterion=self.ui, score=Decimal("80.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_two, criterion=self.ui, score=Decimal("80.00"))

        # team_two has no scores
        leaderboard = compute_leaderboard(self.contest)

        self.assertEqual(len(leaderboard), 2)
        self.assertEqual(leaderboard[0]["team"], self.team_one)
        self.assertEqual(leaderboard[0]["total_score"], Decimal("130.00"))
        # Actually: backend avg = (90+90)/2 = 90, weight 1.0 = 90
        # ui avg = (80+80)/2 = 80, weight 0.5 = 40
        # total = 130
        self.assertEqual(leaderboard[0]["total_score"], Decimal("130.00"))
        self.assertEqual(leaderboard[1]["team"], self.team_two)
        self.assertEqual(leaderboard[1]["total_score"], Decimal("0.00"))

    def test_compute_leaderboard_with_sum_aggregation(self):
        """Test leaderboard with SUM aggregation type"""
        sum_criterion = ScoringCriterion.objects.create(
            contest=self.contest,
            name="Sum Criterion",
            max_score=50,
            weight=Decimal("2.00"),
            aggregation_type=ScoringCriterion.AggregationType.SUM,
            order=3,
        )
        
        # The setUp already created jury assignments for all teams/juries
        # Just add scores for the new criterion
        
        # Score team_one: jury_one=20, jury_two=30 -> sum=50, weight=2.0 -> 100
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_one, criterion=sum_criterion, score=Decimal("20.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_two, criterion=sum_criterion, score=Decimal("30.00"))
        
        # team_two: jury_one=10, jury_two=15 -> sum=25, weight=2.0 -> 50
        JuryScore.objects.create(contest=self.contest, team=self.team_two, jury_member=self.jury_one, criterion=sum_criterion, score=Decimal("10.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_two, jury_member=self.jury_two, criterion=sum_criterion, score=Decimal("15.00"))

        leaderboard = compute_leaderboard(self.contest)

        # team_one should have higher score due to sum aggregation
        self.assertEqual(leaderboard[0]["team"], self.team_one)
        self.assertEqual(leaderboard[0]["total_score"], Decimal("100.00"))
        self.assertEqual(leaderboard[1]["team"], self.team_two)
        self.assertEqual(leaderboard[1]["total_score"], Decimal("50.00"))

    def test_compute_leaderboard_with_zero_weights(self):
        """Test leaderboard calculation with zero weight criteria"""
        zero_weight_criterion = ScoringCriterion.objects.create(
            contest=self.contest,
            name="Zero Weight",
            max_score=100,
            weight=Decimal("0.00"),
            aggregation_type=ScoringCriterion.AggregationType.AVERAGE,
            order=3,
        )
        
        # Score the zero weight criterion
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_one, criterion=zero_weight_criterion, score=Decimal("100.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_two, criterion=zero_weight_criterion, score=Decimal("100.00"))
        
        JuryScore.objects.create(contest=self.contest, team=self.team_two, jury_member=self.jury_one, criterion=zero_weight_criterion, score=Decimal("50.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_two, jury_member=self.jury_two, criterion=zero_weight_criterion, score=Decimal("50.00"))

        leaderboard = compute_leaderboard(self.contest)

        # Zero weight criteria should not affect total score
        self.assertEqual(leaderboard[0]["total_score"], leaderboard[1]["total_score"])
        self.assertEqual(leaderboard[0]["total_score"], Decimal("0.00"))

    def test_get_missing_scores_with_partial_scoring(self):
        """Test missing scores detection with some criteria scored"""
        # Score backend for team_one only partially
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_one, criterion=self.backend, score=Decimal("90.00"))
        # Missing: team_one/backend/jury_two, team_one/ui/both, team_two/all

        missing = get_missing_scores(self.contest)

        self.assertIn("Alpha", missing)
        self.assertIn("Backend", missing["Alpha"])
        self.assertIn("judge_b", missing["Alpha"]["Backend"])
        self.assertIn("UI", missing["Alpha"])
        self.assertIn("Beta", missing)
        self.assertIn("Backend", missing["Beta"])
        self.assertIn("UI", missing["Beta"])

    def test_save_leaderboard_with_incomplete_scores_marks_incomplete(self):
        """Test that saving leaderboard with missing scores marks entries as incomplete"""
        # Only partial scoring
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_one, criterion=self.backend, score=Decimal("90.00"))

        entries = save_leaderboard(self.contest)
        phase = ContestEvaluationPhase.objects.get(contest=self.contest)

        self.assertEqual(len(entries), 2)
        self.assertFalse(phase.all_scores_complete)
        self.assertFalse(entries[0].computation_complete)
        self.assertTrue(len(entries[0].missing_scores) > 0)

    def test_compute_leaderboard_empty_contest_returns_empty_list(self):
        """Test leaderboard computation for contest with no teams"""
        empty_contest = Contest.objects.create(
            name="Empty Contest",
            description="No teams",
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1),
            organizer=self.organizer,
            is_draft=False,
        )

        leaderboard = compute_leaderboard(empty_contest)
        self.assertEqual(leaderboard, [])

    def test_export_csv_with_ties_shows_correct_ranks(self):
        """Test CSV export handles tied ranks correctly"""
        # Create tied scores
        for team in [self.team_one, self.team_two]:
            JuryScore.objects.create(contest=self.contest, team=team, jury_member=self.jury_one, criterion=self.backend, score=Decimal("85.00"))
            JuryScore.objects.create(contest=self.contest, team=team, jury_member=self.jury_two, criterion=self.backend, score=Decimal("85.00"))
            JuryScore.objects.create(contest=self.contest, team=team, jury_member=self.jury_one, criterion=self.ui, score=Decimal("75.00"))
            JuryScore.objects.create(contest=self.contest, team=team, jury_member=self.jury_two, criterion=self.ui, score=Decimal("75.00"))

        csv_data = export_csv(self.contest)

        # Both teams should show rank 1
        lines = csv_data.strip().split('\n')
        self.assertEqual(len(lines), 3)  # header + 2 data lines
        self.assertIn("1,Alpha,", lines[1])
        self.assertIn("1,Beta,", lines[2])

    def test_compute_leaderboard_single_jury_single_criterion(self):
        """Test leaderboard with minimal scoring setup"""
        # Remove extra jury and criterion for simpler test
        self.contest.jurys.remove(self.jury_two)
        self.ui.delete()
        
        # Remove extra assignments
        JuryAssignment.objects.filter(jury_member=self.jury_two).delete()
        
        JuryScore.objects.create(contest=self.contest, team=self.team_one, jury_member=self.jury_one, criterion=self.backend, score=Decimal("95.00"))
        JuryScore.objects.create(contest=self.contest, team=self.team_two, jury_member=self.jury_one, criterion=self.backend, score=Decimal("85.00"))

        leaderboard = compute_leaderboard(self.contest)

        self.assertEqual(len(leaderboard), 2)
        self.assertEqual(leaderboard[0]["team"], self.team_one)
        self.assertEqual(leaderboard[0]["total_score"], Decimal("95.00"))
        self.assertEqual(leaderboard[1]["team"], self.team_two)
        self.assertEqual(leaderboard[1]["total_score"], Decimal("85.00"))


