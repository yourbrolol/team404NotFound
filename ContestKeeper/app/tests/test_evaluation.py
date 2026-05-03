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
    JuryAssignment,
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
class EvaluationModelsTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="password", role=User.Role.ORGANIZER)
        self.jury_one = User.objects.create_user(username="jury1", password="password", role=User.Role.JURY)
        self.jury_two = User.objects.create_user(username="jury2", password="password", role=User.Role.JURY)
        self.captain_one = User.objects.create_user(username="captain1", password="password")
        self.captain_two = User.objects.create_user(username="captain2", password="password")
        self.member = User.objects.create_user(username="member1", password="password")

        self.team_one = Team.objects.create(name="Alpha", captain=self.captain_one, status=Team.Status.ACTIVE)
        self.team_one.participants.add(self.captain_one, self.member)
        self.team_two = Team.objects.create(name="Beta", captain=self.captain_two, status=Team.Status.ACTIVE)
        self.team_two.participants.add(self.captain_two)

        self.contest = Contest.objects.create(
            name="EvalCup",
            description="Contest with scoring",
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2),
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
        self.design = ScoringCriterion.objects.create(
            contest=self.contest,
            name="Design",
            max_score=50,
            weight=Decimal("2.00"),
            aggregation_type=ScoringCriterion.AggregationType.SUM,
            order=2,
        )

    def test_create_scoring_models(self):
        # Create JuryAssignment first
        from app.models import JuryAssignment
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team_one,
            jury_member=self.jury_one
        )
        
        score = JuryScore.objects.create(
            contest=self.contest,
            team=self.team_one,
            jury_member=self.jury_one,
            criterion=self.backend,
            score=Decimal("87.50"),
        )

        phase = ContestEvaluationPhase.objects.create(contest=self.contest)

        self.assertEqual(score.score, Decimal("87.50"))
        self.assertEqual(phase.status, ContestEvaluationPhase.Status.NOT_STARTED)
        self.assertEqual(str(self.backend), "EvalCup: Backend")

    def test_score_validation_rejects_score_above_maximum(self):
        # Create JuryAssignment first
        from app.models import JuryAssignment
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team_one,
            jury_member=self.jury_one
        )
        
        with self.assertRaises(ValidationError):
            JuryScore.objects.create(
                contest=self.contest,
                team=self.team_one,
                jury_member=self.jury_one,
                criterion=self.design,
                score=Decimal("51.00"),
            )

    def test_score_validation_rejects_team_outside_contest(self):
        # Create JuryAssignment for a team not in contest (will still fail for team validation)
        from app.models import JuryAssignment
        
        outsider_team = Team.objects.create(name="Gamma", captain=self.member, status=Team.Status.ACTIVE)
        outsider_team.participants.add(self.member)
        
        # This will fail on team validation, not assignment

        with self.assertRaises(ValidationError):
            JuryScore.objects.create(
                contest=self.contest,
                team=outsider_team,
                jury_member=self.jury_one,
                criterion=self.backend,
                score=Decimal("40.00"),
            )

    def test_score_validation_rejects_jury_not_assigned_to_team(self):
        """Test that scores cannot be given by jury members not assigned to the team"""
        # Create JuryAssignment for jury_one -> team_one, but try to score jury_two -> team_one
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team_one,
            jury_member=self.jury_one
        )
        
        with self.assertRaises(ValidationError) as cm:
            JuryScore.objects.create(
                contest=self.contest,
                team=self.team_one,
                jury_member=self.jury_two,  # jury_two is not assigned to team_one
                criterion=self.backend,
                score=Decimal("50.00"),
            )
        
        self.assertIn("jury_member", cm.exception.message_dict)
        self.assertIn("not assigned", str(cm.exception))

    def test_score_validation_rejects_negative_score(self):
        """Test that negative scores are rejected"""
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team_one,
            jury_member=self.jury_one
        )
        
        with self.assertRaises(ValidationError) as cm:
            JuryScore.objects.create(
                contest=self.contest,
                team=self.team_one,
                jury_member=self.jury_one,
                criterion=self.backend,
                score=Decimal("-5.00"),
            )
        
        self.assertIn("score", cm.exception.message_dict)

    def test_score_validation_rejects_criterion_from_different_contest(self):
        """Test that criteria from other contests are rejected"""
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team_one,
            jury_member=self.jury_one
        )
        
        # Create another contest with its own criterion
        other_contest = Contest.objects.create(
            name="Other Contest",
            description="Different contest",
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1),
            organizer=self.organizer,
            is_draft=False,
        )
        other_criterion = ScoringCriterion.objects.create(
            contest=other_contest,
            name="Other Criterion",
            max_score=100,
            weight=Decimal("1.00"),
            aggregation_type=ScoringCriterion.AggregationType.AVERAGE,
            order=1,
        )
        
        with self.assertRaises(ValidationError) as cm:
            JuryScore.objects.create(
                contest=self.contest,
                team=self.team_one,
                jury_member=self.jury_one,
                criterion=other_criterion,  # Wrong contest's criterion
                score=Decimal("50.00"),
            )
        
        self.assertIn("criterion", cm.exception.message_dict)
        self.assertIn("same contest", str(cm.exception))

    def test_score_validation_rejects_jury_not_in_contest(self):
        """Test that jury members not assigned to the contest are rejected"""
        outsider_jury = User.objects.create_user(username="outsider_jury", password="password", role=User.Role.JURY)
        
        with self.assertRaises(ValidationError) as cm:
            JuryScore.objects.create(
                contest=self.contest,
                team=self.team_one,
                jury_member=outsider_jury,  # Not in contest.jurys
                criterion=self.backend,
                score=Decimal("50.00"),
            )
        
        self.assertIn("jury_member", cm.exception.message_dict)
        self.assertIn("not assigned to this team", str(cm.exception))

    def test_score_validation_allows_zero_score(self):
        """Test that zero scores are allowed"""
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team_one,
            jury_member=self.jury_one
        )
        
        score = JuryScore.objects.create(
            contest=self.contest,
            team=self.team_one,
            jury_member=self.jury_one,
            criterion=self.backend,
            score=Decimal("0.00"),
        )
        
        self.assertEqual(score.score, Decimal("0.00"))

    def test_score_validation_allows_decimal_scores(self):
        """Test that decimal scores are allowed"""
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team_one,
            jury_member=self.jury_one
        )
        
        score = JuryScore.objects.create(
            contest=self.contest,
            team=self.team_one,
            jury_member=self.jury_one,
            criterion=self.backend,
            score=Decimal("87.54"),
        )
        
        self.assertEqual(score.score, Decimal("87.54"))

    def test_score_validation_rejects_score_exactly_at_max_plus_epsilon(self):
        """Test that scores slightly above max are rejected"""
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team_one,
            jury_member=self.jury_one
        )
        
        with self.assertRaises(ValidationError) as cm:
            JuryScore.objects.create(
                contest=self.contest,
                team=self.team_one,
                jury_member=self.jury_one,
                criterion=self.design,  # max_score = 50
                score=Decimal("50.01"),
            )
        
        self.assertIn("score", cm.exception.message_dict)
        self.assertIn("cannot exceed", str(cm.exception))

    def test_jury_assignment_unique_constraint(self):
        """Test that jury assignments are unique per contest/team/jury"""
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team_one,
            jury_member=self.jury_one
        )
        
        with self.assertRaises(Exception):  # IntegrityError or ValidationError
            JuryAssignment.objects.create(
                contest=self.contest,
                team=self.team_one,
                jury_member=self.jury_one  # Same combination
            )

    def test_jury_assignment_different_teams_same_jury_allowed(self):
        """Test that same jury can be assigned to different teams"""
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team_one,
            jury_member=self.jury_one
        )
        
        # Should not raise exception
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team_two,
            jury_member=self.jury_one
        )
        
        self.assertEqual(JuryAssignment.objects.filter(jury_member=self.jury_one).count(), 2)

    def test_scoring_criterion_unique_name_per_contest(self):
        """Test that criterion names must be unique within a contest"""
        with self.assertRaises(Exception):  # IntegrityError
            ScoringCriterion.objects.create(
                contest=self.contest,
                name="Backend",  # Same as existing
                max_score=100,
                weight=Decimal("1.00"),
                aggregation_type=ScoringCriterion.AggregationType.AVERAGE,
                order=2,
            )

    def test_scoring_criterion_same_name_different_contest_allowed(self):
        """Test that same criterion name can exist in different contests"""
        other_contest = Contest.objects.create(
            name="Other Contest",
            description="Different contest",
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1),
            organizer=self.organizer,
            is_draft=False,
        )
        
        # Should not raise exception
        criterion = ScoringCriterion.objects.create(
            contest=other_contest,
            name="Backend",  # Same name as in self.contest
            max_score=100,
            weight=Decimal("1.00"),
            aggregation_type=ScoringCriterion.AggregationType.AVERAGE,
            order=1,
        )
        
        self.assertEqual(criterion.name, "Backend")
        self.assertEqual(criterion.contest, other_contest)


