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
