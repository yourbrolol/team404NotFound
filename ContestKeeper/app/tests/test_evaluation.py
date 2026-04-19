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
        with self.assertRaises(ValidationError):
            JuryScore.objects.create(
                contest=self.contest,
                team=self.team_one,
                jury_member=self.jury_one,
                criterion=self.design,
                score=Decimal("51.00"),
            )

    def test_score_validation_rejects_team_outside_contest(self):
        outsider_team = Team.objects.create(name="Gamma", captain=self.member, status=Team.Status.ACTIVE)
        outsider_team.participants.add(self.member)

        with self.assertRaises(ValidationError):
            JuryScore.objects.create(
                contest=self.contest,
                team=outsider_team,
                jury_member=self.jury_one,
                criterion=self.backend,
                score=Decimal("40.00"),
            )


