from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .leaderboard import compute_leaderboard, export_csv, get_missing_scores, save_leaderboard
from .models import (
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


class SubmissionModelTest(TestCase):
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


class SubmissionUITest(TestCase):
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
        self.client = Client()

    def test_submission_form_access_denied_for_non_team_members(self):
        self.client.force_login(self.other_participant)
        url = reverse('submission_create', kwargs={'pk': self.contest.pk, 'round_id': self.round.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

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
