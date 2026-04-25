
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
import json

from app.models import (
    Contest, Team, Application, ScoringCriterion, JuryScore, 
    Submission, Round, ContestEvaluationPhase, LeaderboardEntry, 
    Notification, JuryAssignment
)

User = get_user_model()

class FullWorkflowIntegrationTest(TestCase):
    """
    End-to-end integration test (TASK-33) using views and simulated user actions.
    This test follows the "Golden Path" of a contest lifecycle.
    """

    def setUp(self):
        # Create users for different roles
        self.organizer = User.objects.create_user(
            username='org_admin', email='org@test.com', password='password', role=User.Role.ORGANIZER
        )
        self.jury = User.objects.create_user(
            username='jury_member', email='jury@test.com', password='password', role=User.Role.JURY
        )
        self.participant1 = User.objects.create_user(
            username='p1_captain', email='p1@test.com', password='password', role=User.Role.PARTICIPANT
        )
        self.participant2 = User.objects.create_user(
            username='p2_member', email='p2@test.com', password='password', role=User.Role.PARTICIPANT
        )

        # Clients for each user
        self.org_client = Client()
        self.jury_client = Client()
        self.p1_client = Client()
        self.p2_client = Client()

        self.org_client.login(username='org_admin', password='password')
        self.jury_client.login(username='jury_member', password='password')
        self.p1_client.login(username='p1_captain', password='password')
        self.p2_client.login(username='p2_member', password='password')

    def test_complete_contest_workflow(self):
        # 1. Organizer creates a contest
        response = self.org_client.post(reverse('contest_create'), {
            'name': 'Integration Contest',
            'description': 'A full workflow test contest',
            'registration_start': (timezone.now() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
            'registration_end': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'start_date': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'end_date': (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M'),
            'format': 'Multi-Round',
            'is_draft': False
        })
        self.assertEqual(response.status_code, 302)
        contest = Contest.objects.get(name='Integration Contest')
        
        # 2. Organizer adds a scoring criterion
        response = self.org_client.post(reverse('criterion_create', kwargs={'pk': contest.pk}), {
            'name': 'Innovation',
            'max_score': 100,
            'weight': 1.0,
            'aggregation_type': ScoringCriterion.AggregationType.AVERAGE,
            'order': 1
        })
        self.assertEqual(response.status_code, 302)
        contest_criterion = ScoringCriterion.objects.get(contest=contest, name='Innovation')
        
        # 3. Organizer creates a round
        response = self.org_client.post(reverse('round_create', kwargs={'pk': contest.pk}), {
            'title': 'Alpha Round',
            'description': 'Implement a prototype',
            'tech_requirements': 'Python 3.10+, Django 5.0',
            'must_have': json.dumps(['Code', 'Tests', 'Documentation']),
            'start_time': (timezone.now() - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M'),
            'deadline': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'order': 1
        })
        self.assertEqual(response.status_code, 302)
        round_obj = Round.objects.get(contest=contest, title='Alpha Round')
        
        # 4. Participant 1 applies to contest
        response = self.p1_client.post(reverse('apply_to_contest', kwargs={'pk': contest.pk, 'app_type': 'participant'}))
        self.assertEqual(response.status_code, 302)
        app1 = Application.objects.get(user=self.participant1, contest=contest)
        
        # 5. Organizer approves Participant 1
        self.org_client.post(reverse('approve_application', kwargs={'pk': app1.pk}))
        app1.refresh_from_db()
        self.assertEqual(app1.status, Application.Status.APPROVED)
        
        # 6. Participant 1 creates a team
        response = self.p1_client.post(reverse('team_create', kwargs={'pk': contest.pk}), {
            'name': 'Coders United',
            'description': 'The best team',
            'organization': 'Open Source'
        })
        self.assertEqual(response.status_code, 302)
        team = Team.objects.get(name='Coders United')
        self.assertEqual(team.captain, self.participant1)
        
        # Team creation creates a TEAM application for the contest which needs approval
        team_app = Application.objects.get(team=team, contest=contest, application_type=Application.Type.TEAM)
        self.org_client.post(reverse('approve_application', kwargs={'pk': team_app.pk}))
        self.assertTrue(contest.teams.filter(pk=team.pk).exists())
        
        # 7. Participant 2 joins the team
        response = self.p2_client.post(reverse('team_join', kwargs={'pk': contest.pk, 'ck': team.pk}))
        self.assertEqual(response.status_code, 302)
        join_app = Application.objects.get(user=self.participant2, team=team, application_type=Application.Type.PARTICIPANT)
        
        # 8. Captain (Participant 1) approves Participant 2
        response = self.p1_client.post(reverse('approve_application', kwargs={'pk': join_app.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(team.participants.filter(pk=self.participant2.pk).exists())
        
        # 9. Organizer activates the round
        response = self.org_client.post(reverse('round_activate', kwargs={'pk': contest.pk, 'round_id': round_obj.pk}))
        self.assertEqual(response.status_code, 302)
        round_obj.refresh_from_db()
        self.assertEqual(round_obj.status, Round.Status.ACTIVE)
        
        # 10. Captain submits solution
        response = self.p1_client.post(reverse('submission_create', kwargs={'pk': contest.pk, 'round_id': round_obj.pk}), {
            'github_url': 'https://github.com/coders/united',
            'video_url': 'https://vimeo.com/12345',
            'description': 'Initial prototype'
        })
        self.assertEqual(response.status_code, 302)
        submission = Submission.objects.get(team=team, round=round_obj)
        
        # 11. Organizer closes submissions
        self.org_client.post(reverse('round_close_submissions', kwargs={'pk': contest.pk, 'round_id': round_obj.pk}))
        round_obj.refresh_from_db()
        self.assertEqual(round_obj.status, Round.Status.SUBMISSION_CLOSED)
        
        # 12. Organizer assigns Jury
        # We need to make the jury member part of the contest first
        jury_app = Application.objects.create(user=self.jury, contest=contest, application_type=Application.Type.JURY)
        self.org_client.post(reverse('approve_application', kwargs={'pk': jury_app.pk}))
        
        response = self.org_client.post(reverse('assign_jury', kwargs={'pk': contest.pk}), {'min_reviews': 1})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(JuryAssignment.objects.filter(contest=contest, team=team, jury_member=self.jury).exists())
        
        # 13. Jury evaluates the team
        response = self.jury_client.post(reverse('jury_evaluate', kwargs={'pk': contest.pk, 'team_pk': team.pk}), {
            f'criterion_{contest_criterion.id}': 95,
            'round_id': round_obj.pk
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(JuryScore.objects.filter(team=team, criterion=contest_criterion, score=95).exists())
        
        # 14. Organizer recalculates leaderboard
        response = self.org_client.post(reverse('admin_recalculate_leaderboard', kwargs={'pk': contest.pk}))
        self.assertEqual(response.status_code, 302)
        
        # Leaderboard computer usually runs on Recalculate or Finish
        # Let's hit finish to be sure it's public
        self.org_client.post(reverse('admin_finish_evaluation', kwargs={'pk': contest.pk}))
        
        # 15. Verify leaderboard content
        response = self.p1_client.get(reverse('contest_leaderboard', kwargs={'pk': contest.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Coders United')
        self.assertContains(response, '95') # The score
